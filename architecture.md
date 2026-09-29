# Architecture — RAG Telecom Customer Care Chatbot

This document describes the system architecture and design of the telecom support chatbot: its components, how data flows through it, and the design decisions behind it.

> Diagrams use [Mermaid](https://mermaid.js.org/). They render on GitHub and in VS Code (with the *Markdown Preview Mermaid Support* extension).

---

## 1. System Overview

The chatbot is a **Retrieval-Augmented Generation (RAG)** application. Instead of relying only on what a Large Language Model (LLM) already knows, it first **retrieves** relevant facts from the company's own knowledge sources and then asks the LLM to **generate** an answer grounded in those facts.

The system has two independent pipelines:

| Pipeline | When it runs | What it does |
|---|---|---|
| **Offline ingestion pipeline** | Once, and whenever source data changes | Reads raw knowledge (CSV, SQLite, PDF), converts it to vector embeddings, stores them in ChromaDB |
| **Online query pipeline** | Every time a user asks a question | Embeds the question, retrieves matching knowledge, builds a prompt, calls the LLM, streams the answer back |

### High-level architecture

```mermaid
flowchart LR
    subgraph Sources["📂 Knowledge Sources (data/)"]
        CSV["faq.csv<br/>25 FAQ entries"]
        DB[("tickets.db<br/>SQLite · 20 tickets")]
        PDF["telecom_guide.pdf<br/>9-page reference guide"]
    end

    subgraph Ingest["⚙️ Offline Ingestion Layer"]
        IF["ingest_faq.py"]
        IT["ingest_tickets.py"]
        IP["ingest_pdf.py"]
    end

    EMB["🧠 Embedding Model<br/>all-MiniLM-L6-v2<br/>(local, HuggingFace)"]

    subgraph Store["🗄️ Vector Store — ChromaDB (chroma_store/)"]
        C1[("faq")]
        C2[("tickets")]
        C3[("guides")]
    end

    subgraph App["🚀 Online Application Layer"]
        UI["app.py<br/>Streamlit Web UI"]
        CLI["main.py<br/>Terminal CLI"]
        CHAIN["rag_chain.py<br/>RAG Chain"]
        RET["retriever.py<br/>Merged Retriever"]
    end

    LLM["☁️ LLM<br/>Qwen3.8-27B on Groq"]
    USER(("👤 Customer"))

    CSV --> IF --> C1
    DB --> IT --> C2
    PDF --> IP --> C3
    IF & IT & IP -.uses.-> EMB

    USER <--> UI
    USER <--> CLI
    UI --> CHAIN
    CLI --> CHAIN
    CHAIN --> RET
    RET -.uses.-> EMB
    RET --> C1 & C2 & C3
    CHAIN <--> LLM
```

---

## 2. Layered Architecture

Like most production systems, the project is organised into layers, each with one responsibility. A layer only talks to the layer directly below it.

```mermaid
flowchart TB
    L1["<b>Presentation Layer</b><br/>app.py (Streamlit) · main.py (CLI)<br/><i>Collects questions, displays streamed answers, keeps chat history</i>"]
    L2["<b>Orchestration Layer</b><br/>rag_chain.py<br/><i>Wires retriever → prompt → LLM → parser into one pipeline</i>"]
    L3["<b>Retrieval Layer</b><br/>retriever.py<br/><i>Semantic search over three collections, merges results</i>"]
    L4["<b>Storage Layer</b><br/>ChromaDB (chroma_store/)<br/><i>Persists vectors + text + metadata</i>"]
    L5["<b>Ingestion Layer</b><br/>ingest_faq.py · ingest_tickets.py · ingest_pdf.py<br/><i>Load → transform → embed → store</i>"]
    L6["<b>Source Data Layer</b><br/>faq.csv · tickets.db · telecom_guide.pdf<br/>seed_tickets.py · generate_pdf.py"]
    EXT["<b>External Services</b><br/>Groq API (LLM) · HuggingFace Hub (model download)"]

    L1 --> L2 --> L3 --> L4
    L6 --> L5 --> L4
    L2 -.-> EXT
    L5 -.-> EXT
```

| Layer | Files | Responsibility | Technology |
|---|---|---|---|
| Presentation | `app.py`, `main.py` | User interaction | Streamlit, Python `input()` |
| Orchestration | `rag_chain.py` | Pipeline composition, prompt engineering | LangChain LCEL |
| Retrieval | `retriever.py` | Similarity search & result merging | LangChain + Chroma |
| Storage | `chroma_store/` | Vector persistence | ChromaDB (SQLite-backed) |
| Ingestion | `ingest_*.py` | ETL into vector store | pandas, sqlite3, PyPDF, text splitters |
| Source data | `data/` | Raw knowledge | CSV, SQLite, PDF (fpdf2) |
| External | — | Inference & model hosting | Groq, HuggingFace |

---

## 3. Offline Ingestion Pipeline

Each knowledge source has its own ingestion script following the classic **ETL (Extract → Transform → Load)** pattern.

```mermaid
flowchart LR
    subgraph FAQ["FAQ pipeline"]
        direction LR
        A1["Extract<br/>pandas.read_csv"] --> A2["Transform<br/>'Q: … A: …'<br/>1 row = 1 doc"] --> A3["Embed<br/>MiniLM → 384-dim"] --> A4[("Load<br/>Chroma 'faq'")]
    end
    subgraph TK["Tickets pipeline"]
        direction LR
        B1["Extract<br/>SQL: status='resolved'"] --> B2["Transform<br/>Issue + Description + Resolution<br/>1 ticket = 1 doc"] --> B3["Embed<br/>MiniLM → 384-dim"] --> B4[("Load<br/>Chroma 'tickets'")]
    end
    subgraph GD["Guide pipeline"]
        direction LR
        C1["Extract<br/>PyPDFLoader (per page)"] --> C2["Transform<br/>RecursiveCharacterTextSplitter<br/>600 chars · 100 overlap"] --> C3["Embed<br/>MiniLM → 384-dim"] --> C4[("Load<br/>Chroma 'guides'")]
    end
```

### Chunking strategy per source

| Source | Chunking | Why |
|---|---|---|
| FAQ | None — one row is one document | Each Q&A is short and self-contained |
| Tickets | None — one ticket is one document | A ticket's issue and resolution must stay together to be useful |
| PDF guide | 600-char chunks, 100-char overlap, split on `\n\n` → `\n` → `.` → space | Pages are long; small chunks give precise matches, and overlap prevents a sentence being cut in half across chunks |

### Metadata stored with each vector

| Collection | Metadata fields |
|---|---|
| `faq` | `source="faq"`, `category`, `faq_id` |
| `tickets` | `source="ticket"`, `ticket_id`, `category`, `status` |
| `guides` | `source="guide"`, `chunk_index`, `page`, plus PDF loader fields |

The `source` field is later used to label each piece of context in the prompt (e.g. `[FAQ]`, `[TICKET]`, `[GUIDE]`).

---

## 4. Online Query Pipeline (Request Lifecycle)

This sequence shows what happens from the moment a customer presses Enter until the answer appears.

```mermaid
sequenceDiagram
    autonumber
    actor U as Customer
    participant UI as app.py / main.py
    participant CH as RAG Chain (rag_chain.py)
    participant R as Merged Retriever (retriever.py)
    participant E as Embedding Model (local)
    participant V as ChromaDB
    participant L as Qwen3.8-27B (Groq)

    U->>UI: "Why is my bill higher this month?"
    UI->>CH: chain.stream(question)
    CH->>R: retrieve(question)
    R->>E: embed(question)
    E-->>R: 384-dim query vector
    par Top-3 from each collection
        R->>V: search 'faq' (k=3)
        R->>V: search 'tickets' (k=3)
        R->>V: search 'guides' (k=3)
    end
    V-->>R: 9 most similar documents
    R-->>CH: list[Document]
    CH->>CH: _format_docs → "[FAQ] … --- [TICKET] … --- [GUIDE] …"
    CH->>CH: Fill ChatPromptTemplate (system + context + question)
    CH->>L: HTTPS request (temperature=0, streaming)
    loop token stream
        L-->>CH: token
        CH-->>UI: text chunk (StrOutputParser)
        UI-->>U: renders incrementally
    end
    UI->>UI: Save Q&A to session history
```

> Note: in the current code the three collection searches run one after another; they are drawn as `par` because they are independent and could be parallelised.

### The RAG chain (LangChain Expression Language)

```mermaid
flowchart LR
    Q["question (str)"] --> SPLIT{{"parallel map"}}
    SPLIT -->|context| RET["retriever"] --> FMT["_format_docs"]
    SPLIT -->|question| PASS["RunnablePassthrough"]
    FMT --> P["ChatPromptTemplate"]
    PASS --> P
    P --> LLM["ChatGroq<br/>qwen/qwen3.8-27b<br/>temp=0 · retries=2"]
    LLM --> OUT["StrOutputParser"] --> A["answer (streamed str)"]
```

Code equivalent (`rag_chain.py`):

```python
chain = (
    {"context": retriever | _format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
```

---

## 5. Deployment View

Everything runs on a single machine except LLM inference.

```mermaid
flowchart TB
    subgraph Local["💻 Local machine / single server"]
        direction TB
        ST["Streamlit server :8501<br/>(or CLI process)"]
        PY["Python 3.11 runtime<br/>LangChain · sentence-transformers · PyTorch (CPU)"]
        FS[("Disk<br/>chroma_store/ · data/ · HF model cache")]
        ENV[".env<br/>GROQ_API_KEY · HF_TOKEN"]
        ST --- PY --- FS
        PY -.reads.-> ENV
    end
    B["🌐 Browser"] <-->|HTTP| ST
    PY <-->|HTTPS · API key| GROQ["☁️ Groq Cloud<br/>LLM inference"]
    PY -->|first run only| HF["☁️ HuggingFace Hub<br/>model download"]
```

| Concern | Where it lives |
|---|---|
| Secrets | `.env` (git-ignored); template in `.env.example` |
| Vector data | `chroma_store/` — a local SQLite file plus binary index folders |
| Embedding model | Downloaded once to the HuggingFace cache, then runs locally on CPU |
| LLM | Remote — Groq API |
| Dependencies | `pyproject.toml` + `uv.lock` (managed by `uv`) |

---

## 6. Key Design Decisions

| # | Decision | Rationale | Trade-off |
|---|---|---|---|
| 1 | **RAG instead of fine-tuning** | Knowledge can be updated by re-running an ingest script — no model retraining | Answer quality depends on retrieval quality |
| 2 | **Three separate collections** instead of one | Guarantees every answer sees FAQ, ticket *and* guide context; prevents the numerous PDF chunks from crowding out FAQs | Always returns 9 docs, even if some are irrelevant |
| 3 | **Fixed k=3 per collection** | Simple, predictable prompt size | No relevance threshold or re-ranking |
| 4 | **Local embeddings (MiniLM-L6-v2)** | Free, fast on CPU, no data leaves the machine at embed time | Smaller model → lower semantic accuracy than large API embedders |
| 5 | **Hosted LLM on Groq** | Very fast inference, no GPU needed locally | Requires internet + API key; question and context are sent to a third party |
| 6 | **`temperature=0`** | Deterministic, factual support answers | Less varied phrasing |
| 7 | **Grounding prompt ("use ONLY the context")** with 611 fallback | Reduces hallucination; safe escalation path | May refuse questions it could have answered generally |
| 8 | **Streaming output** | Better perceived latency | Slightly more complex UI code |
| 9 | **Only `resolved` tickets ingested** | Escalated/unresolved tickets have no reliable fix to recommend | Loses signal from open cases |
| 10 | **Shared chain via `@st.cache_resource`** | Embedding model and DB connections are loaded once per server, not per message | Changes to the vector store require an app restart |
| 11 | **Two front-ends over one chain** | UI and CLI reuse identical logic (`build_chain()`) | — |

---

## 7. Non-Functional Characteristics

| Quality | Current state |
|---|---|
| **Latency** | Retrieval is local and fast (ms); total time dominated by Groq generation, hidden by streaming |
| **Scalability** | Single-process; ChromaDB embedded mode. Suitable for a demo / small team |
| **Reliability** | LLM calls retry up to 2 times; no fallback model |
| **Security** | API keys in `.env`; no user authentication; no input sanitisation or PII filtering |
| **Observability** | Console prints during ingestion only; no logging/tracing at query time |
| **Memory** | Chat history is shown in the UI but **not** sent to the LLM — each question is answered independently |

---

## 8. Known Limitations & Evolution Path

**Current limitations**

- Re-running an ingest script **appends** to the existing collection (no document IDs / no reset), creating duplicate vectors. Delete `chroma_store/` before a full re-ingest.
- The system prompt mentions only *two* sources (FAQ, tickets) though three are retrieved.
- No conversation memory — follow-up questions like "and how do I fix that?" lose context.
- No evaluation suite to measure answer quality.

**How a production version would evolve**

```mermaid
flowchart LR
    subgraph Today
        T1["Streamlit"] --> T2["LangChain chain"] --> T3[("Embedded Chroma")]
        T2 --> T4["Groq"]
    end
    subgraph Production
        P0["Web / mobile / WhatsApp"] --> GW["API Gateway + Auth"]
        GW --> API["FastAPI service<br/>(stateless, N replicas)"]
        API --> CACHE[("Redis<br/>sessions + cache")]
        API --> VDB[("Managed vector DB<br/>Chroma server / pgvector / Pinecone")]
        API --> RR["Re-ranker"]
        API --> LLMGW["LLM gateway<br/>primary + fallback"]
        API --> OBS["Logging · tracing · evals<br/>(LangSmith / OpenTelemetry)"]
        ETL["Scheduled ingestion jobs<br/>(Airflow / cron) with upserts"] --> VDB
        CRM[("Live ticketing system / CRM")] --> ETL
    end
    Today ==> Production
```

| Area | Improvement |
|---|---|
| Ingestion | Deterministic IDs + upsert; scheduled sync from the live ticketing system |
| Retrieval | Hybrid search (keyword + vector), similarity threshold, cross-encoder re-ranking |
| Conversation | Pass chat history and rewrite follow-up questions into standalone queries |
| Answers | Show source citations (ticket ID, FAQ ID, guide page) to the user |
| Service | Split UI from a FastAPI backend; containerise with Docker |
| Safety | PII redaction, prompt-injection guards, rate limiting, authentication |
| Quality | Offline evaluation set (question → expected answer) run on every change |
