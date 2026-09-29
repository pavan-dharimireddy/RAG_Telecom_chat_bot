# Project Notes — RAG Telecom Customer Care Chatbot

A plain-English guide to this project: what it is, why it exists, and what every file does.
No prior AI knowledge is needed. Technical details are included for developers, but each section starts with a simple explanation.

For diagrams and system design, see [architecture.md](architecture.md).

---

## Table of Contents

1. [What is this project?](#1-what-is-this-project)
2. [Key ideas explained simply](#2-key-ideas-explained-simply)
3. [The big picture in 5 steps](#3-the-big-picture-in-5-steps)
4. [Folder map](#4-folder-map)
5. [Script-by-script guide](#5-script-by-script-guide)
   - [data/generate_pdf.py](#51-datagenerate_pdfpy--creates-the-reference-manual)
   - [data/seed_tickets.py](#52-dataseed_ticketspy--creates-the-past-support-cases)
   - [ingest_faq.py](#53-ingest_faqpy--teaches-the-bot-the-faqs)
   - [ingest_tickets.py](#54-ingest_ticketspy--teaches-the-bot-past-cases)
   - [ingest_pdf.py](#55-ingest_pdfpy--teaches-the-bot-the-manual)
   - [retriever.py](#56-retrieverpy--the-librarian)
   - [rag_chain.py](#57-rag_chainpy--the-brain)
   - [app.py](#58-apppy--the-website)
   - [main.py](#59-mainpy--the-terminal-version)
6. [Data files](#6-data-files)
7. [Configuration files](#7-configuration-files)
8. [How to run it (step by step)](#8-how-to-run-it-step-by-step)
9. [A question's journey — worked example](#9-a-questions-journey--worked-example)
10. [Common tasks](#10-common-tasks)
11. [Troubleshooting](#11-troubleshooting)
12. [Glossary](#12-glossary)

---

## 1. What is this project?

**In one sentence:** It is a chatbot that answers mobile-phone customer support questions (slow internet, billing, SIM problems, roaming…) using the telecom company's own documents instead of guessing.

**Real-world analogy:** Imagine a new support agent on their first day. They don't know everything, but they have three things on their desk:

| On the desk | In this project |
|---|---|
| 📋 A sheet of Frequently Asked Questions | `data/faq.csv` |
| 🗂️ A drawer of old support cases and how they were solved | `data/tickets.db` |
| 📘 A technical reference manual | `data/telecom_guide.pdf` |

When a customer asks something, the agent quickly flips through all three, picks out the most relevant pages, and then writes a helpful reply based on what they found. **That is exactly what this chatbot does**, just in a couple of seconds.

**Why not just use ChatGPT-style AI directly?** A general AI doesn't know *this* company's policies, prices, or past fixes, and it may confidently make things up. By handing it the right company documents first, its answers become accurate and specific.

---

## 2. Key ideas explained simply

| Term | Simple meaning |
|---|---|
| **RAG** (Retrieval-Augmented Generation) | "Look it up first, then answer." Retrieve relevant documents → give them to the AI → AI generates the answer. |
| **LLM** (Large Language Model) | The AI that writes human-like text. Here: **Qwen3.8-27B**, running on **Groq**'s servers. |
| **Embedding** | Turning a sentence into a list of 384 numbers that captures its *meaning*. Sentences with similar meaning get similar numbers — "internet is slow" and "data speed is poor" end up close together even though they share no words. |
| **Embedding model** | The tool that makes embeddings. Here: **all-MiniLM-L6-v2**, a small free model that runs on your own computer. |
| **Vector database** | A database that stores embeddings and can quickly find "the ones most similar to this question". Here: **ChromaDB**. |
| **Collection** | A named folder inside the vector database. We have three: `faq`, `tickets`, `guides`. |
| **Chunking** | Cutting a long document into small pieces so searches can find the exact relevant paragraph. |
| **Ingestion** | The one-time process of reading the documents, embedding them, and saving them to the vector database. |
| **Prompt** | The instructions + context + question sent to the AI. |
| **LangChain** | A Python library that connects all these pieces (database, prompt, AI) into a pipeline. |
| **Streamlit** | A Python library that turns a script into a website with almost no web-development code. |

---

## 3. The big picture in 5 steps

The project has two phases: **preparing the knowledge** (done once) and **answering questions** (done every time).

```
PHASE A — PREPARE (run once)                 PHASE B — ANSWER (every question)
─────────────────────────────                ──────────────────────────────────
                                             
 1. Create the raw data                        4. Customer asks a question
    generate_pdf.py → telecom_guide.pdf           (website app.py or terminal main.py)
    seed_tickets.py → tickets.db                        │
    (faq.csv is written by hand)                        ▼
          │                                    5. retriever.py finds the 9 most
          ▼                                       relevant snippets (3 from each
 2. Convert it to "meaning numbers"               collection) → rag_chain.py sends
    ingest_faq.py                                 them + the question to the AI →
    ingest_tickets.py                             answer is streamed back
    ingest_pdf.py
          │
          ▼
 3. Saved in chroma_store/  ◄──────────────── read by step 5
```

---

## 4. Folder map

```
rag_telecom_chatbot/
│
├── app.py               ← 🌐 The chatbot website (start here to use it)
├── main.py              ← 💻 Same chatbot, in the terminal
├── rag_chain.py         ← 🧠 Connects: search → prompt → AI → answer
├── retriever.py         ← 🔎 Searches the three knowledge collections
│
├── ingest_faq.py        ← 📥 Loads FAQs into the vector database
├── ingest_tickets.py    ← 📥 Loads past tickets into the vector database
├── ingest_pdf.py        ← 📥 Loads the PDF manual into the vector database
│
├── data/
│   ├── faq.csv              ← 25 question/answer pairs
│   ├── tickets.db           ← 20 past support tickets (SQLite database)
│   ├── telecom_guide.pdf    ← 9-page technical reference manual
│   ├── seed_tickets.py      ← 🏭 Script that creates tickets.db
│   └── generate_pdf.py      ← 🏭 Script that creates telecom_guide.pdf
│
├── chroma_store/        ← 🗄️ The vector database (created by ingest scripts)
│
├── .env                 ← 🔑 Your secret API keys (never share / commit)
├── .env.example         ← Template showing which keys are needed
├── pyproject.toml       ← List of Python libraries the project needs
├── uv.lock              ← Exact pinned versions of those libraries
├── README.md            ← Quick-start instructions
├── architecture.md      ← System design & diagrams
└── notes.md             ← This file
```

**Which files should I touch?**

| If you want to… | Edit this |
|---|---|
| Change how the bot talks / its rules | `rag_chain.py` → `SYSTEM_PROMPT` |
| Add or edit FAQs | `data/faq.csv`, then re-run `ingest_faq.py` |
| Add past cases | `data/seed_tickets.py`, run it, then re-run `ingest_tickets.py` |
| Change the manual | `data/generate_pdf.py`, run it, then re-run `ingest_pdf.py` |
| Change how many results are searched | `retriever.py` → `k_faq`, `k_tickets`, `k_guides` |
| Change the website's look / sample questions | `app.py` |
| Change the AI model | `rag_chain.py` → `ChatGroq(model=...)` |

---

## 5. Script-by-script guide

Scripts are listed in the order they are used.

### 5.1 `data/generate_pdf.py` — creates the reference manual

**In plain words:** A "printing press" that writes a professional-looking PDF manual about mobile networks. It exists so the project has a realistic long document to practise on.

**When to run:** Only if you change the manual's content. The PDF is already included.

```bash
python data/generate_pdf.py
```

**What it does, step by step**

1. Holds the manual's text in a list called `SECTIONS` (title + body for each chapter).
2. Defines a `PDF` class (based on the `fpdf2` library) that adds a grey header — *"Telecom Technical Reference Guide – Internal Use Only"* — and a page number footer on every page.
3. `build_pdf()` creates a title page ("Telecom Technical Reference Guide · Version 3.2"), then adds one page per section with a blue heading and underline.
4. Saves the file to `data/telecom_guide.pdf`.

**The 8 chapters in the manual**

| # | Chapter | Covers |
|---|---|---|
| 1 | Introduction to Mobile Networks | 2G → 5G, frequency bands |
| 2 | Troubleshooting Connectivity Issues | 6-step diagnosis (signal, airplane mode, APN, SIM, outages) |
| 3 | Data Plans and Fair Use Policy | Data caps, throttling |
| 4 | International Roaming | How roaming and bundles work |
| 5 | SIM Card Technology | Physical SIM, eSIM, provisioning |
| 6 | VoLTE, VoWiFi, Advanced Voice | HD calls, Wi-Fi calling |
| 7 | Billing System & Common Disputes | Why bills change, disputes |
| 8 | Network Security & Fraud Prevention | SIM-swap fraud, scams |

**Output:** `data/telecom_guide.pdf` (9 pages: title + 8 chapters).

---

### 5.2 `data/seed_tickets.py` — creates the past support cases

**In plain words:** Builds a small database of 20 made-up but realistic customer complaints and how each was solved. This simulates the history a real company's ticketing system would have.

**When to run:** Only if you change the tickets. `tickets.db` is already included.

```bash
python data/seed_tickets.py
```

**What it does, step by step**

1. Holds 20 tickets in a Python list `TICKETS`. Each ticket is a tuple of: ticket ID, category, issue type, description, resolution, status.
2. Connects to (or creates) the SQLite file `data/tickets.db`.
3. **Deletes** the old `tickets` table if it exists (so running it twice doesn't duplicate data) and creates a fresh one.
4. Inserts all 20 tickets and saves.

**Table structure (`tickets`)**

| Column | Example | Meaning |
|---|---|---|
| `id` | 1 | Auto-number |
| `ticket_id` | TK-004 | Human-readable case number |
| `category` | roaming | Topic |
| `issue_type` | Unexpected roaming charges | Short title |
| `description` | "Customer returned from Spain…" | What the customer reported |
| `resolution` | "Bundle was activated 3 hours late… offered 50% credit" | How support fixed it |
| `status` | resolved / escalated | 19 resolved, 1 escalated |

---

### 5.3 `ingest_faq.py` — teaches the bot the FAQs

**In plain words:** Reads the FAQ spreadsheet, turns each question-and-answer into "meaning numbers" (embeddings), and saves them in the `faq` collection of the vector database.

```bash
python ingest_faq.py
```

**What it does, step by step**

1. **Read** `data/faq.csv` with `pandas`.
2. **Reshape** each row into one text block:
   ```
   Q: How do I check my current data balance?
   A: Dial *123# from your mobile or log in to the MyTelecom app…
   ```
   plus labels (metadata): `source="faq"`, `category`, `faq_id`.
3. **Load the embedding model** `all-MiniLM-L6-v2` (downloaded automatically the first time).
4. **Embed and save** all documents into ChromaDB collection `faq` inside `chroma_store/`.
5. Prints how many vectors are stored.

**Design note:** FAQs are **not** cut into smaller pieces — each Q&A is already short and complete.

**Expected output**
```
Loading FAQ documents...
  25 FAQ entries loaded.
Initialising embedding model...
Embedding and storing in Chroma collection 'faq'...
  Done. 25 vectors stored.
```

---

### 5.4 `ingest_tickets.py` — teaches the bot past cases

**In plain words:** Opens the tickets database, takes only the cases that were **successfully solved**, and saves them to the `tickets` collection.

```bash
python ingest_tickets.py
```

**What it does, step by step**

1. **Query** SQLite: `SELECT * FROM tickets WHERE status = 'resolved'` → 19 tickets (the escalated one is skipped because it has no confirmed fix).
2. **Combine** each ticket's fields into one text block:
   ```
   Issue: Unexpected roaming charges
   Description: Customer returned from a trip to Spain…
   Resolution: Investigated and found the roaming bundle was activated 3 hours after…
   ```
   plus metadata: `source="ticket"`, `ticket_id`, `category`, `status`.
3. **Embed and save** to the `tickets` collection.

**Design note:** The problem and its solution are kept in **one** document so that when a customer describes a similar problem, the bot also sees how it was solved.

---

### 5.5 `ingest_pdf.py` — teaches the bot the manual

**In plain words:** Reads the PDF manual, cuts it into small overlapping paragraphs, and saves each paragraph to the `guides` collection.

```bash
python ingest_pdf.py
```

**What it does, step by step**

1. **Load** the PDF page by page with `PyPDFLoader`.
2. **Chunk** the pages with `RecursiveCharacterTextSplitter`:
   - `CHUNK_SIZE = 600` characters (roughly one paragraph)
   - `CHUNK_OVERLAP = 100` characters shared between neighbouring chunks
   - Tries to split at paragraph breaks first, then line breaks, then sentence ends, then spaces — so it avoids cutting words or sentences in half.
3. **Tag** each chunk with `source="guide"` and a `chunk_index` number.
4. **Embed and save** to the `guides` collection.

**Why chunk?** A whole page covers many topics. If the customer asks about APN settings, we want the *one paragraph* about APNs — not a full page where APNs are one line among many.

**Why overlap?** If an important sentence sits on the border between two chunks, the overlap makes sure it appears whole in at least one of them.

---

### 5.6 `retriever.py` — the librarian

**In plain words:** Given a customer's question, it searches all three collections and returns the **3 best matches from each** — 9 snippets in total.

**Not run directly** — it is used by `rag_chain.py`.

**Key contents**

| Item | Value / purpose |
|---|---|
| `CHROMA_DIR` | `"chroma_store"` — where the database lives |
| `EMBED_MODEL` | `"sentence-transformers/all-MiniLM-L6-v2"` — **must match** the model used during ingestion, otherwise the "meaning numbers" won't be comparable |
| `build_retriever(k_faq=3, k_tickets=3, k_guides=3)` | Main function |

**What `build_retriever()` does**

1. Loads the embedding model.
2. Opens the three existing collections (`faq`, `tickets`, `guides`).
3. Makes a "retriever" for each that returns the top *k* most similar documents.
4. Defines `retrieve(query)`, which runs all three searches and joins the results into one list: FAQ results first, then tickets, then guide chunks.
5. Wraps it in a `RunnableLambda` so it can plug into a LangChain pipeline.

**Why three separate searches instead of one big one?** The PDF produces many chunks. In one combined search, those chunks could push FAQs and tickets out of the top results. Searching each separately guarantees the AI always sees a policy answer (FAQ), a real-world fix (ticket), and technical background (guide).

---

### 5.7 `rag_chain.py` — the brain

**In plain words:** The assembly line that turns a question into an answer: **search → format → build prompt → ask AI → clean up text**.

**Not run directly** — used by `app.py` and `main.py` via `build_chain()`.

**Key contents**

**1. `SYSTEM_PROMPT` — the bot's job description.** It tells the AI:
- You are a helpful, professional telecom customer care assistant.
- Use **ONLY** the context provided (to prevent made-up answers).
- If the context isn't enough, say so and suggest calling **611** or using the **MyTelecom app**.
- The retrieved context is inserted at `{context}`.

**2. `_format_docs(docs)` — makes the snippets readable for the AI.** Each snippet gets a label showing where it came from, separated by `---`:
```
[FAQ]
Q: Why is my bill higher than usual?
A: ...

---

[TICKET]
Issue: Double charged for monthly plan
...
```

**3. `build_chain()` — wires everything together.**

| Stage | Component | Job |
|---|---|---|
| 1 | `retriever \| _format_docs` | Find 9 snippets and format them as text |
| 1 (in parallel) | `RunnablePassthrough()` | Pass the original question through unchanged |
| 2 | `ChatPromptTemplate` | Fill the system prompt with context + add the question |
| 3 | `ChatGroq` | Send to the AI model |
| 4 | `StrOutputParser` | Extract plain text from the AI's response |

**AI settings (`ChatGroq`)**

| Setting | Value | Meaning |
|---|---|---|
| `model` | `qwen/qwen3.8-27b` | Which AI model to use |
| `temperature` | `0` | No creativity/randomness — consistent, factual answers |
| `max_tokens` | `None` | No artificial length limit |
| `reasoning_format` | `"parsed"` | The model's internal "thinking" is separated out so only the final answer is shown |
| `max_retries` | `2` | Retry twice if the network call fails |

---

### 5.8 `app.py` — the website

**In plain words:** The friendly chat web page customers use. It looks like a messaging app.

```bash
streamlit run app.py
```
Then open http://localhost:8501.

**What you see**

| Area | Contents |
|---|---|
| **Sidebar** | Title "📡 Telecom Support", 8 clickable sample questions, a "🗑️ Clear conversation" button |
| **Main area** | "Customer Care Assistant" title, the conversation history, and a text box: *"Describe your issue…"* |

**How it works, step by step**

1. Hides noisy library warnings (`TRANSFORMERS_VERBOSITY=error`) and loads API keys from `.env`.
2. `get_chain()` builds the RAG chain **once** and caches it (`@st.cache_resource`) — so the embedding model isn't reloaded on every message.
3. Uses `st.session_state` to remember:
   - `messages` — the chat history shown on screen
   - `pending_question` — a question chosen by clicking a sample button
4. Redraws all previous messages.
5. Takes the new question from either the text box or a clicked sample button.
6. Shows the question, then calls `chain.stream(question)` and displays the answer **word by word** as it arrives (`st.write_stream`).
7. Saves both the question and answer to the history.

**Note:** The history is only for display. The AI does **not** see previous messages, so every question is answered on its own.

---

### 5.9 `main.py` — the terminal version

**In plain words:** The same chatbot without a website — you type in the terminal and read the answer there. Handy for quick testing.

```bash
python main.py
```

**How it works**

1. Loads API keys and builds the chain once.
2. Loops forever:
   - Shows `Customer: ` and waits for input.
   - Ignores empty lines.
   - Exits on `quit`, `exit` or `q`.
   - Otherwise prints `Assistant: ` and streams the answer piece by piece.

**Example session**
```
=== Telecom Customer Care Chatbot (RAG) ===
Type your question and press Enter. Type 'quit' to exit.

Customer: How do I enable Wi-Fi calling?

Assistant: To enable Wi-Fi calling, go to Settings > ...

Customer: quit
Goodbye!
```

---

## 6. Data files

| File | Format | Contents | Created by |
|---|---|---|---|
| `data/faq.csv` | Spreadsheet (CSV) | 25 FAQs with columns `id, question, answer, category`. Categories: billing (5), connectivity (4), sim (4), voice (4), data (3), roaming (3), account (1), device (1) | Written by hand |
| `data/tickets.db` | SQLite database | 20 tickets (19 resolved, 1 escalated) | `seed_tickets.py` |
| `data/telecom_guide.pdf` | PDF | 9-page technical manual | `generate_pdf.py` |
| `chroma_store/` | ChromaDB (SQLite + index folders) | All embeddings for the 3 collections | The 3 ingest scripts |

---

## 7. Configuration files

| File | Purpose |
|---|---|
| `.env` | Your private keys. **Never commit or share this.** |
| `.env.example` | Template — copy it to `.env` and fill in values |
| `pyproject.toml` | Project name, Python version (3.11+), and list of libraries |
| `uv.lock` | Exact versions of every library, so everyone installs the same thing |
| `.gitignore` | Tells git which files to never upload (e.g. `.env`, `.venv/`) |

**Required keys in `.env`**

| Key | Where to get it | Used for |
|---|---|---|
| `GROQ_API_KEY` | https://console.groq.com | Calling the AI model |
| `HF_TOKEN` | https://huggingface.co/settings/tokens | Downloading the embedding model |

**Libraries used (from `pyproject.toml`)**

| Library | Role |
|---|---|
| `langchain`, `langchain-core` | Pipeline framework |
| `langchain-groq` | Connects LangChain to Groq's AI |
| `langchain-chroma`, `chromadb` | Vector database |
| `langchain-huggingface`, `sentence-transformers`, `torchvision` | Embedding model |
| `langchain-community`, `pypdf` | PDF loading |
| `langchain-text-splitters` | Chunking |
| `pandas` | Reading the CSV |
| `fpdf2` | Generating the PDF |
| `streamlit` | Web interface |
| `python-dotenv` | Reading `.env` |

---

## 8. How to run it (step by step)

```bash
# 1. Install libraries
uv sync                      # or: pip install -e .

# 2. Add your keys
cp .env.example .env         # then edit .env

# 3. Build the knowledge base (one time)
python ingest_faq.py
python ingest_tickets.py
python ingest_pdf.py

# 4. Chat!
streamlit run app.py         # website
# or
python main.py               # terminal
```

---

## 9. A question's journey — worked example

**Customer asks:** *"I was charged for roaming but had a bundle active"*

| Step | Where | What happens |
|---|---|---|
| 1 | `app.py` | Customer clicks the sample question. It's shown in the chat. |
| 2 | `rag_chain.py` | `chain.stream(question)` starts the pipeline. |
| 3 | `retriever.py` | The question is converted to 384 numbers by MiniLM. |
| 4 | ChromaDB | Finds the closest matches: FAQs about roaming bundles, **ticket TK-004** (bundle activated 3 hours late → 50% credit), and the guide's roaming chapter. |
| 5 | `rag_chain.py` | 9 snippets are labelled `[FAQ]`, `[TICKET]`, `[GUIDE]` and placed in the prompt along with the rules and the question. |
| 6 | Groq | Qwen reads everything and writes an answer, e.g. explaining that charges before the bundle was activated are billed at standard rates and that the customer can request a review/goodwill credit. |
| 7 | `app.py` | The answer appears word by word and is saved to the chat history. |

---

## 10. Common tasks

**Add a new FAQ**
1. Add a row to `data/faq.csv` (`id,question,answer,category`).
2. Delete the `chroma_store/` folder *(see note below)*.
3. Re-run all three ingest scripts.

**Add a new ticket**
1. Add a tuple to `TICKETS` in `data/seed_tickets.py`.
2. `python data/seed_tickets.py`
3. Delete `chroma_store/` and re-run all three ingest scripts.

**Change the bot's tone or rules** → edit `SYSTEM_PROMPT` in `rag_chain.py`, then restart the app.

**Give the AI more or less context** → change `k_faq`, `k_tickets`, `k_guides` in `retriever.py`.

> ⚠️ **Important:** The ingest scripts **add** documents to the database; they don't replace existing ones. Running an ingest script twice creates duplicates. To refresh cleanly, delete the `chroma_store/` folder and run all three ingest scripts again.

---

## 11. Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| Bot says it doesn't have enough information for everything | `chroma_store/` is empty or missing | Run the three ingest scripts |
| `GROQ_API_KEY` / authentication error | `.env` missing or wrong key | Check `.env` exists and the key is valid |
| Very slow first start | Embedding model downloading | Wait; it's cached after the first run |
| Same snippet appears several times in answers | Ingest scripts were run more than once | Delete `chroma_store/` and re-ingest |
| Changes to data not reflected in the website | Chain is cached | Re-ingest, then stop and restart `streamlit run app.py` |
| `ModuleNotFoundError` | Libraries not installed / wrong environment | Run `uv sync` and activate `.venv` |

---

## 12. Glossary

| Term | Meaning |
|---|---|
| **APN** | Access Point Name — phone settings that tell it how to connect to mobile data |
| **Chunk** | A small piece of a longer document |
| **Collection** | A named group of documents in ChromaDB |
| **Context** | The retrieved snippets given to the AI alongside the question |
| **Embedding / vector** | A list of numbers representing a text's meaning |
| **eSIM** | A digital SIM built into the phone |
| **Grounding** | Forcing the AI to base its answer on provided documents |
| **Hallucination** | When an AI confidently states something false |
| **k** | How many top results to fetch from a search |
| **Metadata** | Labels attached to a document (source, category, ID) |
| **Roaming** | Using your phone on another country's network |
| **Semantic search** | Searching by meaning rather than exact words |
| **Streaming** | Showing the answer piece by piece as it's generated |
| **Temperature** | AI randomness setting; 0 = most consistent |
| **Token** | A small piece of text (about ¾ of a word) that AI models read and write |
| **VoLTE / VoWiFi** | Voice calls over 4G / over Wi-Fi |
