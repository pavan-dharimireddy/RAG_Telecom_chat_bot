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
   - [config.py](#53-configpy--the-settings-file)
   - [ingest_faq.py](#54-ingest_faqpy--teaches-the-bot-the-faqs)
   - [ingest_tickets.py](#55-ingest_ticketspy--teaches-the-bot-past-cases)
   - [ingest_pdf.py](#56-ingest_pdfpy--teaches-the-bot-the-manual)
   - [retriever.py](#57-retrieverpy--the-librarian)
   - [rag_chain.py](#58-rag_chainpy--the-brain)
   - [app.py](#59-apppy--the-website)
   - [main.py](#510-mainpy--the-terminal-version)
   - [setup_vector_store.py](#511-setup_vector_storepy--builds-the-database-automatically)
   - [sqlite_compat.py](#512-sqlite_compatpy--the-sqlite-safety-fix)
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
| **LLM** (Large Language Model) | The AI that writes human-like text. Here: Google's **Gemini 3.5 Flash** (originally Qwen on Groq; see [5.8](#58-rag_chainpy--the-brain)). |
| **Embedding** | Turning a sentence into a list of 384 numbers(dimensions) that captures its *meaning*. Sentences with similar meaning get similar numbers — "internet is slow" and "data speed is poor" end up close together even though they share no words. |
| **Embedding model** | The tool that makes embeddings. Here: **all-MiniLM-L6-v2**, a small free model that runs on your own computer. |
| **Vector database** | A database that stores embeddings and can quickly find "the ones most similar to this question". Here: **ChromaDB**. |
| **Collection** | A named group of documents inside the vector database, like a separate table or drawer. We have three: `faq`, `tickets`, `guides`. (They are not folders with those names; see "Where are the collections stored?" below.) |
| **Chunking** | Cutting a long document into small pieces so searches can find the exact relevant paragraph. |
| **Ingestion** | The one-time process of reading the documents, embedding them, and saving them to the vector database. |
| **Prompt** | The instructions + context + question sent to the AI. |
| **LangChain** | A Python library that connects all these pieces (database, prompt, AI) into a pipeline. |
| **Streamlit** | A Python library that turns a script into a website with almost no web-development code. |

### Common questions about embeddings

**Q: Does every embedding create only 384 vectors?**

No. Every piece of text(chunk) becomes **one** vector, and that one vector is a list of **384 numbers(dimensions)**.

- **Vector** = one list of numbers that represents one piece of text.
- **384** = how many numbers are in that list.

| Text | What it becomes |
|---|---|
| "Why is my internet slow?" | 1 vector → `[0.021, -0.113, 0.047, …]` (384 numbers) |
| One FAQ entry | 1 vector (384 numbers) |
| One chunk of the PDF manual | 1 vector (384 numbers) |

A short question and a long paragraph both come out as exactly 384 numbers. The length of the list never changes.

**Q: So how many vectors are stored in the database?**

One for every piece of text we saved:

- `faq`: 25 vectors (one per FAQ)
- `tickets`: 19 vectors (one per solved ticket)
- `guides`: one per chunk of the PDF

Each of those vectors is 384 numbers long.

**Q: What are "dimensions"? Is that the same as the 384 numbers?**

Yes. Here, **"384 dimensions" and "384 numbers" mean the same thing.** "Dimensions" is just the technical word for how many numbers are in each vector.

Think of describing where something is:

| Describing… | Dimensions | Numbers needed |
|---|---|---|
| A point on a ruler | 1 | `[5]` |
| A place on a map (left-right, up-down) | 2 | `[5, 3]` |
| A spot in a room (left-right, up-down, front-back) | 3 | `[5, 3, 2]` |
| The **meaning** of a sentence (this project) | 384 | `[0.021, -0.113, …]` (384 of them) |

A map needs 2 numbers to pin a location. Meaning is far richer than a location, so the model uses 384 numbers to pin a sentence in a "meaning space". Sentences that mean similar things land close together. That's how the bot finds the right FAQs and tickets even when the customer uses different words.

**Q: Why exactly 384? Can it be different?**

The number is fixed by the embedding model you choose. This project's model (`all-MiniLM-L6-v2`) always gives 384. Other models give other sizes:

| Model | Numbers per vector |
|---|---|
| all-MiniLM-L6-v2 (this project) | 384 |
| all-mpnet-base-v2 | 768 |
| OpenAI text-embedding-3-small | 1536 |
| OpenAI text-embedding-3-large | 3072 |

More numbers can capture meaning in finer detail, but they take more storage and make searches slower. 384 is a good balance for a small project.

**Q: Why must the same model be used everywhere?**

The customer's question is turned into 384 numbers by the same model, then compared with the stored vectors. If the stored documents used one model and the question used another, it would be like comparing a map location with a room location: the numbers wouldn't line up. That's why the model name is defined **once**, as `EMBED_MODEL` in [config.py](config.py), and both the ingest scripts and [retriever.py](retriever.py) read it from there.

### Common questions about vector databases

**Q: What does a vector database actually do?**

It stores the vectors (the 384-number lists) together with the original text, and very quickly answers one question: *"Which stored texts are closest in meaning to this one?"*

A normal database (like Excel or SQL) finds rows by **exact** match, e.g. `category = "billing"`. A vector database finds rows by **similar meaning**, e.g. "internet is slow" also finds "poor data speed".

**Q: Where are the collections stored? I can't find a `faq`, `tickets` or `guides` folder.**

That's expected. A collection is a **named group inside the database**, not a folder you can see with that name. ChromaDB gives each collection a random ID and uses it internally. Inside `chroma_store/` you'll find:

```
chroma_store/
├── chroma.sqlite3                          ← the "master file"
├── 4f898b0d-b921-4760-b42d-4f7741bf4fbc/   ← search index for 'faq'
├── 2521d5de-a9af-493e-bac1-b9e20fe7e1a2/   ← search index for 'tickets'
└── 3e1ecf31-2237-4a74-a752-11c7e6fb59d3/   ← search index for 'guides'
```

*(The long IDs will be different on your computer; they are generated randomly. They also change if you delete `chroma_store/` and rebuild it.)*

Each ID-named folder holds a fast search index of that collection's vectors (files like `data_level0.bin` and `header.bin`), arranged so the closest matches are found quickly.

So the names `faq`, `tickets` and `guides` live *inside* `chroma.sqlite3`, and each one points to one of the ID-named folders. You never open these files by hand; the code opens a collection by name, e.g. `Chroma(collection_name=FAQ_COLLECTION, ...)` in [retriever.py](retriever.py), where `FAQ_COLLECTION` is `"faq"` (set in [config.py](config.py)).

**Q: How can I see which ID folder belongs to which collection, and how much is in each?**

Run this from the project folder. It only reads the database and doesn't change anything:

```bash
python -c "import chromadb; c = chromadb.PersistentClient('chroma_store'); [print(col.name, '->', col.count(), 'vectors') for col in c.list_collections()]"
```

Expected result (the order may vary):

```
faq -> 25 vectors
guides -> 36 vectors
tickets -> 19 vectors
```

These numbers should match your data: 25 FAQs, 19 solved tickets, and 36 PDF chunks.

**Q: This project uses ChromaDB. Are there other vector databases?**

Yes, many. They all do the same core job; they differ in size, hosting and extra features.

| Vector database | Type | Best for | Notes |
|---|---|---|---|
| **ChromaDB** *(this project)* | Open source · runs inside your app or as a server | Learning, prototypes, small apps | Easiest to start with; saves to a local folder (`chroma_store/`) |
| **Qdrant** | Open source · self-hosted or managed cloud | Production apps needing speed and filtering | Written in Rust; very fast; strong filtering by metadata (e.g. "only billing tickets") |
| **Pinecone** | Fully managed cloud service (paid, free tier) | Teams that don't want to run servers | No setup; scales automatically; data lives on Pinecone's servers |
| **Weaviate** | Open source · self-hosted or managed cloud | Hybrid search (keywords + meaning) | Built-in modules can create embeddings for you |
| **Milvus / Zilliz** | Open source (Milvus) · managed cloud (Zilliz) | Very large data (billions of vectors) | Built for big-company scale |
| **FAISS** | Open-source library by Meta (not a full database) | Fast in-memory search, research | Extremely fast, but no built-in storage server or metadata filtering |
| **pgvector** | Extension for PostgreSQL | Teams already using PostgreSQL | Keep normal data and vectors in one database |
| **Elasticsearch / OpenSearch** | Search engines with vector support | Companies already using them for text search | Good at combining keyword and vector search |
| **Redis** | In-memory database with vector search | Very low-latency apps | Very fast because data lives in memory |
| **MongoDB Atlas Vector Search** | Vector search inside MongoDB's cloud | Teams already using MongoDB | Vectors stored next to normal documents |

**Q: When would you switch to something like Qdrant or Pinecone?**

| Situation | Better choice |
|---|---|
| Millions of documents, many users at once | Qdrant, Milvus, Pinecone |
| Don't want to manage any servers | Pinecone, Qdrant Cloud, Weaviate Cloud |
| Already have a PostgreSQL database | pgvector |
| Need heavy filtering ("only roaming tickets from 2025") | Qdrant, Weaviate |
| Just learning or prototyping | ChromaDB (current choice), FAISS |

**Q: How hard is it to switch?**

Fairly easy, thanks to LangChain. Each database has a LangChain package (e.g. `langchain-qdrant`, `langchain-pinecone`), so you mainly change the `Chroma(...)` lines in the ingest scripts and [retriever.py](retriever.py), then re-run the ingest scripts. The embedding model, prompt and app stay the same.

### Common questions about chunking

**Q: What is chunking?**

Chunking means **cutting documents into smaller pieces before saving them** in the vector database. Each piece (a "chunk") gets its own vector, and search returns whole chunks.

Think of highlighting a textbook before an exam. You don't memorise the whole book as one blob; you mark the paragraphs so you can find the right one fast. Chunking decides **where those boundaries go**.

**Q: Why is chunking done correctly so important?**

Because the AI can only answer from the chunks the search hands it. Bad chunks lead to bad answers, even with a great AI model.

| If chunks are… | What goes wrong | Example |
|---|---|---|
| **Too big** (a whole page) | One chunk mixes many topics, so its meaning gets blurry and it matches poorly. The AI also has to read lots of irrelevant text. | A page about "SIM cards" also covers eSIM, PIN codes and SIM swaps. A question about PIN codes gets the whole page. |
| **Too small** (one sentence) | Pieces lose their context. | A chunk saying "Toggle it off and on again" without saying *what* to toggle. |
| **Cut in the wrong place** | A step, a sentence, or a problem and its solution get split apart. | A ticket's *problem* in one chunk and its *resolution* in another: the bot finds the problem but not the fix. |
| **Just right** | Each chunk covers one idea, completely. | One FAQ Q&A; one ticket with its fix; one paragraph about APN settings. |

**Rule of thumb:** a good chunk should make sense if you read it on its own.

**Q: How does this project chunk each file?**

Each file type is treated differently, because each has a different natural shape:

| File | Script | Chunking method | 1 chunk = | Chunks | Size of each chunk (characters) | Why this choice |
|---|---|---|---|---|---|---|
| `faq.csv` | [ingest_faq.py](ingest_faq.py) | **No splitting**: one row, one chunk | One question + its answer | 25 | 184 – 315 (avg 250) | Each Q&A is already short and complete. Splitting would separate the question from its answer. |
| `tickets.db` | [ingest_tickets.py](ingest_tickets.py) | **No splitting**: one record, one chunk (issue + description + resolution joined together) | One solved support case | 19 | 277 – 424 (avg 351) | The problem and its fix must stay together. That pairing is what makes a ticket useful. |
| `telecom_guide.pdf` | [ingest_pdf.py](ingest_pdf.py) | **Clean, then recursive character splitting**, 600 characters max, 100 overlap | About one paragraph of the manual | 36 (from 9 pages) | 121 – 596 (avg 502) | Pages are long and cover several topics, so they're cut into paragraph-sized pieces. |

**How the PDF is cut, step by step:**

1. The PDF is read **page by page**. Chunks never cross from one page to the next.
2. **Each page is cleaned first:** the header line (*"Telecom Technical Reference Guide - Internal Use Only"*) and the page-number footer (*"Page 2"*, *"Page 3"*…) are removed. They appear on every page but say nothing about the topic.
3. The splitter tries to keep each chunk under **600 characters**, cutting at the "nicest" place it can find, in this order of preference:
   1. a blank line (`\n\n`), which is the end of a paragraph
   2. a line break (`\n`)
   3. a full stop (`.`), the end of a sentence
   4. a space, which at least doesn't cut a word in half
4. **Overlap:** up to **100 characters** at the end of one chunk may be repeated at the start of the next, so an idea sitting on the border isn't lost. In this PDF, 12 of the 35 neighbouring chunk pairs share overlapping text, for example the sentence *"detect duplicates via idempotency keys; if not, the agent must manually reverse the extra charge."* appears at the end of one chunk and the start of the next. The others split cleanly at a paragraph or line break, so no overlap was needed.

**Why the cleaning step matters (a real example from this project):** the first version of `ingest_pdf.py` didn't clean the pages, so the header and footer were read as normal text, and **9 of the 37 chunks** contained them. It didn't break anything, but it was noise that slightly blurred those chunks' meaning. Removing them before chunking brought that to **0**, and the total to 36 chunks. Lesson: **look at your chunks.** Repeated headers, footers, page numbers and copyright lines are common in PDFs and are easy to miss.

**Q: What are the different types of chunking?**

| Type | How it works | Good for | Downsides |
|---|---|---|---|
| **No chunking (one record = one chunk)** *(used for FAQ and tickets)* | Each row, record or item is saved as it is | Short, self-contained items: FAQs, tickets, product listings | Doesn't work for long documents |
| **Fixed-size** | Cut every N characters (or words/tokens), no matter what | Quick experiments | Cuts mid-sentence or even mid-word |
| **Recursive character** *(used for the PDF)* | Try to cut at paragraphs, then lines, then sentences, then spaces, staying under a size limit | General-purpose text. The most common default. | Doesn't understand meaning, only punctuation and line breaks |
| **Sentence-based** | Cut only at sentence ends, grouping a few sentences per chunk | Articles, emails, chat logs | Sentence lengths vary a lot, so chunk sizes are uneven |
| **Structure-aware (document-based)** | Follow the document's own structure: headings, sections, Markdown titles, HTML tags, code functions | Manuals, wikis, web pages, code | Needs clean structure in the source |
| **Semantic** | Use an embedding model to find where the **topic changes**, and cut there | Long documents with mixed topics | Slower and more expensive (it embeds everything while chunking) |
| **Token-based** | Measure size in **tokens** (what the AI counts) instead of characters | Staying exactly within model limits | Needs a tokenizer; otherwise the same weaknesses as fixed-size |
| **Parent–child (small-to-big)** | Search on small chunks for precision, but give the AI the larger "parent" section it came from | When you need both precise matches and full context | More complex to build and store |
| **Agentic / LLM-based** | Ask an AI model to decide the boundaries | Messy or unusual documents | Slowest and costliest; results can vary |

**Q: What are chunk size and overlap, and how do I choose them?**

| Setting | Meaning | This project | Typical range |
|---|---|---|---|
| **Chunk size** | Maximum length of one chunk | 600 characters (about 100 words) | 300–1,500 characters |
| **Chunk overlap** | Text repeated between neighbouring chunks | 100 characters (about 15%) | 10–20% of chunk size |

- **Smaller chunks** give more precise matches but less context in each.
- **Bigger chunks** carry more context, but they're less precise and use more of the AI's space.
- **The embedding model has a limit too.** `all-MiniLM-L6-v2` only reads about the first 256 tokens (roughly 1,000 characters) of any text and ignores the rest. So chunks much bigger than that would be only partly understood. 600 characters sits safely inside the limit.

There's no perfect number. The practical approach is to try a few sizes, ask real test questions, and keep the setting that returns the most useful chunks.

**Q: How would I change the chunking in this project?**

Edit these two lines in [config.py](config.py), then re-run `python ingest_pdf.py` and restart the app:

```python
CHUNK_SIZE    = 600
CHUNK_OVERLAP = 100
```

The FAQ and ticket scripts don't need chunking settings, because each item is already the right size.

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
├── config.py            ← ⚙️ All settings in one place (paths, models, chunking, k)
├── rag_chain.py         ← 🧠 Connects: search → prompt → AI → answer
├── retriever.py         ← 🔎 Searches the three knowledge collections
│
├── ingest_faq.py        ← 📥 Loads FAQs into the vector database
├── ingest_tickets.py    ← 📥 Loads past tickets into the vector database
├── ingest_pdf.py        ← 📥 Loads the PDF manual into the vector database
├── setup_vector_store.py ← 🔧 Builds any empty collection automatically on start-up
├── sqlite_compat.py     ← 🩹 SQLite fix for old Linux servers (does nothing elsewhere)
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
├── requirements.txt     ← Same list in the format hosting platforms read
├── uv.lock              ← Exact pinned versions of those libraries
├── README.md            ← Quick-start instructions
├── LICENSE              ← MIT licence: how others may reuse the code
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
| Change how many results are searched | `config.py` → `K_FAQ`, `K_TICKETS`, `K_GUIDES` |
| Change the PDF chunk size / overlap | `config.py` → `CHUNK_SIZE`, `CHUNK_OVERLAP`, then re-run `ingest_pdf.py` |
| Change the embedding model | `config.py` → `EMBED_MODEL`, then re-run **all three** ingest scripts |
| Change the website's look / sample questions | `app.py` |
| Change the AI model | `config.py` → `LLM_MODEL` |

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

### 5.3 `config.py` — the settings file

**In plain words:** One file that holds **every setting** the project uses: where files are, which AI models to use, how to chunk the PDF, how many search results to fetch. Every other script reads its settings from here.

**Not run directly.** The ingest scripts, `retriever.py` and `rag_chain.py` all import from it.

**Why it exists:** before `config.py`, the same settings were copy-pasted into several files. For example, the embedding model name was written in **4 places**. If someone changed it in one file and forgot another, the stored documents and the customer's questions would be turned into numbers by **different models**, and search would quietly return poor results with **no error message**. Now each setting is written **once**, so that mistake can't happen.

**An analogy:** it's like a thermostat for a whole house instead of a separate dial in every room. Change the temperature once, and every room follows.

#### Line-by-line walkthrough of `config.py`

> Line numbers match [config.py](config.py).

**Part 1: Description and import (lines 1–5)**

```python
"""
Central settings for the whole project.
Every script imports from here, so a value only ever needs changing in one place.
"""
from pathlib import Path
```

| Line | Code | What it does |
|---|---|---|
| 1–4 | Docstring | Says what the file is for. |
| 5 | `from pathlib import Path` | Loads Python's built-in tool for working with **file and folder paths**. It handles `\` (Windows) vs `/` (Mac/Linux) automatically. |

**Part 2: The project folder (lines 7–9)**

```python
# Project folder (where this file lives). All paths are built from it,
# so the scripts work no matter which folder they are run from.
BASE_DIR = Path(__file__).resolve().parent
```

| Line | Code | What it does |
|---|---|---|
| 7–8 | Comment | Explains why the line below matters. |
| 9 | `BASE_DIR = Path(__file__).resolve().parent` | Works out the **full address of the project folder**. `__file__` is the location of this file (`config.py`), `.resolve()` turns it into a complete address like `C:\Users\…\rag_telecom_chatbot\config.py`, and `.parent` steps up to the folder that contains it. |

**Why this matters:** previously the scripts used short paths like `"data/faq.csv"`, which Python looks for **relative to wherever you ran the command from**. Running `python rag_telecom_chatbot/ingest_faq.py` from the parent folder would fail to find the data, or create a new, empty `chroma_store/` in the wrong place. Building every path from `BASE_DIR` means the scripts always find the right files, wherever they're started from.

**Part 3: Data sources (lines 12–15)**

```python
DATA_DIR        = BASE_DIR / "data"
FAQ_CSV_PATH    = DATA_DIR / "faq.csv"
TICKETS_DB_PATH = DATA_DIR / "tickets.db"
GUIDE_PDF_PATH  = DATA_DIR / "telecom_guide.pdf"
```

| Line | Setting | What it does |
|---|---|---|
| 12 | `DATA_DIR` | The `data/` folder. With `Path`, the `/` symbol **joins** folder names (it isn't division). |
| 13 | `FAQ_CSV_PATH` | Full path to the FAQ spreadsheet. Used by `ingest_faq.py`. |
| 14 | `TICKETS_DB_PATH` | Full path to the ticket database. Used by `ingest_tickets.py`. |
| 15 | `GUIDE_PDF_PATH` | Full path to the PDF manual. Used by `ingest_pdf.py`. |

The lines starting with `# ──` are just comments drawn as section dividers, to make the file easy to scan.

**Part 4: Vector store (lines 18–21)**

```python
CHROMA_DIR         = str(BASE_DIR / "chroma_store")
FAQ_COLLECTION     = "faq"
TICKETS_COLLECTION = "tickets"
GUIDES_COLLECTION  = "guides"
```

| Line | Setting | What it does |
|---|---|---|
| 18 | `CHROMA_DIR` | Full path to the `chroma_store/` database folder. Wrapped in `str(...)` because ChromaDB expects the path as plain text. |
| 19–21 | `FAQ_COLLECTION`, `TICKETS_COLLECTION`, `GUIDES_COLLECTION` | The three collection names. Each ingest script **writes** to one; `retriever.py` **reads** all three. Defining them here guarantees writer and reader use the same names. |

**Part 5: Embedding model (line 24)**

```python
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
```

| Line | Setting | What it does |
|---|---|---|
| 24 | `EMBED_MODEL` | The model that turns text into 384 numbers. **The most important setting to keep in one place**, because ingestion and search must use the same one. ⚠️ If you change it, re-run all three ingest scripts so the stored vectors are rebuilt with the new model. |

**Part 6: PDF chunking (lines 27–28)**

```python
CHUNK_SIZE    = 600
CHUNK_OVERLAP = 100
```

| Line | Setting | What it does |
|---|---|---|
| 27 | `CHUNK_SIZE` | Maximum characters per PDF chunk. |
| 28 | `CHUNK_OVERLAP` | Characters shared between neighbouring chunks. Change either, then re-run `python ingest_pdf.py`. See [Common questions about chunking](#common-questions-about-chunking). |

**Part 7: Retrieval (lines 31–33)**

```python
K_FAQ     = 3
K_TICKETS = 3
K_GUIDES  = 3
```

| Line | Setting | What it does |
|---|---|---|
| 31–33 | `K_FAQ`, `K_TICKETS`, `K_GUIDES` | How many results to fetch from each collection per question (3 + 3 + 3 = 9). Used as the defaults in `build_retriever()`. No re-ingest needed; just restart the app. |

**Part 8: The AI model (lines 36–39)**

```python
# Previous provider: Qwen on Groq (Groq returns "403 Access denied" from Streamlit Community Cloud)
# LLM_MODEL       = "qwen/qwen3.8-27b"
LLM_MODEL       = "gemini-3.5-flash"
LLM_TEMPERATURE = 0
```

| Line | Setting | What it does |
|---|---|---|
| 36–37 | Comments | The old Groq model, kept as a comment so it's easy to switch back (see [5.8](#58-rag_chainpy--the-brain)). |
| 38 | `LLM_MODEL` | Which Gemini model writes the answers. |
| 39 | `LLM_TEMPERATURE` | The "randomness dial": 0 = consistent, factual answers. |

#### Which script uses which setting

| Setting | `ingest_faq.py` | `ingest_tickets.py` | `ingest_pdf.py` | `retriever.py` | `rag_chain.py` |
|---|---|---|---|---|---|
| `CHROMA_DIR` | ✅ | ✅ | ✅ | ✅ | |
| `EMBED_MODEL` | ✅ | ✅ | ✅ | ✅ | |
| `FAQ_COLLECTION` / `FAQ_CSV_PATH` | ✅ | | | ✅ (collection) | |
| `TICKETS_COLLECTION` / `TICKETS_DB_PATH` | | ✅ | | ✅ (collection) | |
| `GUIDES_COLLECTION` / `GUIDE_PDF_PATH` | | | ✅ | ✅ (collection) | |
| `CHUNK_SIZE`, `CHUNK_OVERLAP` | | | ✅ | | |
| `K_FAQ`, `K_TICKETS`, `K_GUIDES` | | | | ✅ | |
| `LLM_MODEL`, `LLM_TEMPERATURE` | | | | | ✅ |

#### After changing a setting, what do I need to re-run?

| You changed… | Then… |
|---|---|
| `EMBED_MODEL` | Re-run **all three** ingest scripts, then restart the app |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | Re-run `python ingest_pdf.py`, then restart the app |
| A data path or collection name | Re-run the matching ingest script, then restart the app |
| `K_FAQ` / `K_TICKETS` / `K_GUIDES` | Just restart the app |
| `LLM_MODEL` / `LLM_TEMPERATURE` | Just restart the app |

---

### 5.4 `ingest_faq.py` — teaches the bot the FAQs

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
4. **Empty the collection** `faq` if it already has data, so running the script again **replaces** the FAQs instead of adding a second copy.
5. **Embed and save** all documents into ChromaDB collection `faq` inside `chroma_store/`.
6. Prints how many vectors are stored.

**Design note:** FAQs are **not** cut into smaller pieces — each Q&A is already short and complete.

**Expected output**
```
Loading FAQ documents...
  25 FAQ entries loaded.
Initialising embedding model...
  Removing 25 existing vectors...        ← only appears when re-running
Embedding and storing in Chroma collection 'faq'...
  Done. 25 vectors stored.
```

#### Line-by-line walkthrough of `ingest_faq.py`

> Line numbers match [ingest_faq.py](ingest_faq.py). The other two ingest scripts follow the **same structure**, so reading this one carefully makes the next two easy.

**Part 1: Description (lines 1–5)**

```python
"""
Ingests data/faq.csv into the 'faq' Chroma collection.
Safe to re-run: it replaces the collection each time.
Run whenever the CSV changes: python ingest_faq.py
"""
```

| Line | What it does |
|---|---|
| 1–5 | A **docstring**: a note for humans at the top of the file saying what the script does and how to run it. Python ignores it when running. |

**Part 2: Imports, the tools this script borrows (lines 6–12)**

```python
import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
import sqlite_compat  # noqa: F401  (must come before chromadb is imported)
import pandas as pd
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
```

| Line | Code | What it does |
|---|---|---|
| 6 | `import os` | Loads Python's built-in "operating system" toolkit, used for file paths and settings. |
| 7 | `os.environ["TRANSFORMERS_VERBOSITY"] = "error"` | Tells the AI-model library to **only print real errors**, not dozens of info/warning lines. It's set *before* the libraries below are loaded so they pick it up. Purely cosmetic: it keeps the output clean. |
| 8 | `import sqlite_compat  # noqa: …` | Loads the project's small **SQLite safety fix** ([sqlite_compat.py](sqlite_compat.py), see [section 5.12](#512-sqlite_compatpy--the-sqlite-safety-fix)). ChromaDB needs a recent version of SQLite; on the rare server that has an older one, this swaps in a newer copy. On your PC it does nothing. It must come **before** any line that loads ChromaDB (line 11). The `# noqa: F401` comment tells code checkers "yes, this import looks unused, but it's on purpose". |
| 9 | `import pandas as pd` | Loads **pandas**, a library for reading spreadsheet-like data (CSV files). `as pd` is just a short nickname. |
| 10 | `from langchain_core.documents import Document` | Loads LangChain's **Document** type: a standard "box" holding a piece of text (`page_content`) plus labels about it (`metadata`). |
| 11 | `from langchain_chroma import Chroma` | Loads the connector to the **ChromaDB** vector database. |
| 12 | `from langchain_huggingface import HuggingFaceEmbeddings` | Loads the tool that runs the **embedding model** (turns text into 384 numbers). |

**Part 3: Settings, borrowed from `config.py` (line 14)**

```python
from config import CHROMA_DIR, EMBED_MODEL, FAQ_COLLECTION, FAQ_CSV_PATH
```

| Line | Code | What it does |
|---|---|---|
| 14 | `from config import …` | Brings in four settings from the project's central settings file, [config.py](config.py) (see [section 5.3](#53-configpy--the-settings-file)): |
| | `CHROMA_DIR` | The folder where the vector database is saved (`chroma_store/`). |
| | `EMBED_MODEL` | Which embedding model to use. Because every script imports it from the **same place**, ingestion and search can never accidentally use different models. |
| | `FAQ_COLLECTION` | The name of the collection to fill: `"faq"`. |
| | `FAQ_CSV_PATH` | The full path to `data/faq.csv`. |

Names in CAPITALS are a Python convention meaning "this is a setting; it doesn't change while the program runs". The blank line before this import separates outside libraries (lines 9–12) from the project's own files.

**Part 4: Reading the CSV into Documents (lines 17–26)**

```python
def load_faq_documents(csv_path) -> list[Document]:
    df = pd.read_csv(csv_path)
    docs = []
    for _, row in df.iterrows():
        content = f"Q: {row['question']}\nA: {row['answer']}"
        docs.append(Document(
            page_content=content,
            metadata={"source": "faq", "category": row["category"], "faq_id": str(row["id"])},
        ))
    return docs
```

| Line | Code | What it does |
|---|---|---|
| 17 | `def load_faq_documents(csv_path) -> list[Document]:` | Defines a reusable **function**. It takes a file path and gives back a list of Documents. The `-> list[Document]` part is a **type hint**: a note for readers and code editors about what comes back, not a rule Python enforces. |
| 18 | `df = pd.read_csv(csv_path)` | Reads the whole CSV into a **DataFrame** (`df`), basically a spreadsheet in memory with columns `id`, `question`, `answer`, `category`. |
| 19 | `docs = []` | Creates an empty list to collect the Documents. |
| 20 | `for _, row in df.iterrows():` | Loops over the spreadsheet **one row at a time**. `iterrows()` gives (row number, row); the `_` means "I don't need the row number". |
| 21 | `content = f"Q: {row['question']}\nA: {row['answer']}"` | Builds the text that will be embedded and searched. The `f"..."` (f-string) inserts values into `{ }`; `\n` is a line break. Result: `Q: How do I check my data balance?` / `A: Dial *123#…` |
| 22–25 | `docs.append(Document(...))` | Wraps the text in a Document and adds it to the list. |
| 23 | `page_content=content` | The text itself: what gets embedded and later shown to the AI. |
| 24 | `metadata={...}` | Labels stored alongside (not embedded): `source: "faq"` (used later to print `[FAQ]` in the prompt), the row's `category` (e.g. `"data"`), and `faq_id` (the row's ID, converted to text with `str()` because Chroma metadata must be simple text/number values). |
| 26 | `return docs` | Hands the finished list (25 Documents) back to whoever called the function. |

**Part 5: The main program (lines 29–51)**

```python
def main():
    print("Loading FAQ documents...")
    docs = load_faq_documents(FAQ_CSV_PATH)
    print(f"  {len(docs)} FAQ entries loaded.")
```

| Line | Code | What it does |
|---|---|---|
| 29 | `def main():` | Defines the main function: the script's to-do list, in order. |
| 30 | `print("Loading FAQ documents...")` | Progress message. |
| 31 | `docs = load_faq_documents(FAQ_CSV_PATH)` | Calls the function above. `docs` now holds 25 Documents. |
| 32 | `print(f"  {len(docs)} FAQ entries loaded.")` | `len(docs)` counts the items → prints `25 FAQ entries loaded.` |

```python
    print("Initialising embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
```

| Line | Code | What it does |
|---|---|---|
| 34 | `print(...)` | Progress message. |
| 35 | `embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)` | Loads the MiniLM embedding model. The first time ever, it **downloads** it (~88 MB) from Hugging Face; after that it loads from your computer's cache. Nothing is embedded yet; this just gets the tool ready. |

```python
    vectorstore = Chroma(
        collection_name=FAQ_COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )
```

| Line | Code | What it does |
|---|---|---|
| 37–41 | `vectorstore = Chroma(...)` | **Opens** the `faq` collection in `chroma_store/`. If the folder or collection doesn't exist yet, Chroma **creates** it. |
| 38 | `collection_name=FAQ_COLLECTION` | Which collection: `"faq"`. |
| 39 | `embedding_function=embeddings` | Tells Chroma which model to use whenever it needs to turn text into vectors. |
| 40 | `persist_directory=CHROMA_DIR` | Save to disk in `chroma_store/` (so the data survives after the script ends). |

```python
    # Empty the collection first so re-running replaces the data instead of duplicating it
    existing_ids = vectorstore.get()["ids"]
    if existing_ids:
        print(f"  Removing {len(existing_ids)} existing vectors...")
        vectorstore.delete(ids=existing_ids)
```

| Line | Code | What it does |
|---|---|---|
| 43 | `# Empty the collection…` | A **comment** (starts with `#`): a note for humans, ignored by Python. |
| 44 | `existing_ids = vectorstore.get()["ids"]` | Asks Chroma for everything already in the collection and keeps only the list of **IDs** (every stored item has a unique ID). On a first run this list is empty. |
| 45 | `if existing_ids:` | "If the list is not empty…" (an empty list counts as *false* in Python). |
| 46 | `print(f"  Removing … existing vectors...")` | Says how many old items will be removed. |
| 47 | `vectorstore.delete(ids=existing_ids)` | **Deletes** all old items. This is what prevents duplicates when the script runs again. |

```python
    print(f"Embedding and storing in Chroma collection '{FAQ_COLLECTION}'...")
    vectorstore.add_documents(docs)
    print(f"  Done. {vectorstore._collection.count()} vectors stored.")
```

| Line | Code | What it does |
|---|---|---|
| 49 | `print(...)` | Progress message. |
| 50 | `vectorstore.add_documents(docs)` | **The key step.** For each of the 25 Documents, Chroma (1) runs the embedding model to turn the text into 384 numbers, (2) gives it a new random ID, and (3) saves the vector, text and metadata to disk. |
| 51 | `vectorstore._collection.count()` | Counts what's now in the collection, as a final check. Should print `25`. (The `_` at the start of `_collection` marks it as an "internal" part of the library; it works, but it isn't an official feature.) |

**Part 6: The start button (lines 54–55)**

```python
if __name__ == "__main__":
    main()
```

| Line | What it does |
|---|---|
| 54–55 | "If this file was **run directly** (`python ingest_faq.py`), call `main()`." If another file only *imports* this one (to reuse `load_faq_documents`, for example), `main()` does **not** run automatically. This is a standard Python pattern. |

---

### 5.5 `ingest_tickets.py` — teaches the bot past cases

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
3. **Empty** the `tickets` collection if it already has data (so re-running replaces rather than duplicates).
4. **Embed and save** to the `tickets` collection.

**Design note:** The problem and its solution are kept in **one** document so that when a customer describes a similar problem, the bot also sees how it was solved.

#### Line-by-line walkthrough of `ingest_tickets.py`

> Line numbers match [ingest_tickets.py](ingest_tickets.py). This script has the same shape as `ingest_faq.py`. The **new** parts are reading from a SQLite database (lines 9 and 17–23) and building a three-part text (lines 28–32).

**Part 1: Description (lines 1–5)**

| Line | What it does |
|---|---|
| 1–5 | Docstring: says this script loads **resolved** tickets from `data/tickets.db` into the `tickets` collection, and is safe to re-run. |

**Part 2: Imports (lines 6–12)**

```python
import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
import sqlite_compat  # noqa: F401  (must come before chromadb is imported)
import sqlite3
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
```

| Line | Code | What it does |
|---|---|---|
| 6–7 | `import os` + verbosity setting | Same as the FAQ script: file-path tools, and quieter library output. |
| 8 | `import sqlite_compat …` | The SQLite safety fix, same as in the FAQ script. |
| 9 | `import sqlite3` | **New.** Python's built-in tool for reading **SQLite** database files (`.db`). No installation needed; it comes with Python. |
| 10–12 | `Document`, `Chroma`, `HuggingFaceEmbeddings` | Same as the FAQ script. |

**Part 3: Settings, borrowed from `config.py` (line 14)**

```python
from config import CHROMA_DIR, EMBED_MODEL, TICKETS_COLLECTION, TICKETS_DB_PATH
```

| Line | Code | What it does |
|---|---|---|
| 14 | `from config import …` | Same idea as the FAQ script: four settings from [config.py](config.py). |
| | `CHROMA_DIR`, `EMBED_MODEL` | The same database folder and the same embedding model as every other script. |
| | `TICKETS_COLLECTION` | Fill the `tickets` collection this time. |
| | `TICKETS_DB_PATH` | The full path to `data/tickets.db`. |

**Part 4: Reading tickets from the database (lines 17–23)**

```python
def load_ticket_documents(db_path) -> list[Document]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM tickets WHERE status = 'resolved'"
    ).fetchall()
    conn.close()
```

| Line | Code | What it does |
|---|---|---|
| 17 | `def load_ticket_documents(db_path) -> list[Document]:` | Defines a function that takes the database path and returns a list of Documents. |
| 18 | `conn = sqlite3.connect(db_path)` | **Opens a connection** to the database file, like opening a spreadsheet file before reading it. |
| 19 | `conn.row_factory = sqlite3.Row` | Makes each result row readable **by column name** (`row['description']`) instead of only by position (`row[4]`). Easier to read and less error-prone. |
| 20–22 | `rows = conn.execute("SELECT …").fetchall()` | Runs a **SQL query**, a question asked to the database: *"give me every column (`*`) from the `tickets` table, but only rows where status is `resolved`."* `fetchall()` collects all the matching rows into a list. Result: 19 rows (the 1 `escalated` ticket is skipped because it has no confirmed fix to recommend). |
| 23 | `conn.close()` | **Closes** the database connection. Good practice: it frees the file as soon as we're done with it. |

**Part 5: Turning each ticket into a Document (lines 25–42)**

```python
    docs = []
    for row in rows:
        # Combine issue description + resolution into a single searchable text block
        content = (
            f"Issue: {row['issue_type']}\n"
            f"Description: {row['description']}\n"
            f"Resolution: {row['resolution']}"
        )
        docs.append(Document(
            page_content=content,
            metadata={
                "source":    "ticket",
                "ticket_id": row["ticket_id"],
                "category":  row["category"],
                "status":    row["status"],
            },
        ))
    return docs
```

| Line | Code | What it does |
|---|---|---|
| 25 | `docs = []` | Empty list to collect Documents. |
| 26 | `for row in rows:` | Go through the tickets one at a time. |
| 27 | `# Combine …` | Comment explaining the next step. |
| 28–32 | `content = ( f"Issue: …\n" f"Description: …\n" f"Resolution: …" )` | Builds **one text block** from three columns. Python automatically joins strings written next to each other inside `( )`. Result:<br>`Issue: Unexpected roaming charges`<br>`Description: Customer returned from a trip to Spain…`<br>`Resolution: …bundle was activated 3 hours after…`<br>Keeping the problem **and** its fix together is the whole point: a customer describing the problem will also bring back the solution. |
| 33–41 | `docs.append(Document(...))` | Wraps the text in a Document and adds it to the list. |
| 34 | `page_content=content` | The text to embed and search. |
| 35–40 | `metadata={...}` | Labels: `source: "ticket"` (shows as `[TICKET]` in the AI's prompt), `ticket_id` (e.g. `TK-004`), `category` (e.g. `roaming`), and `status` (always `resolved` here). Notice `ticket_id`, `category` and `status` are **not** in the searchable text; they're kept only as labels. |
| 42 | `return docs` | Returns 19 Documents. |

**Part 6: Main program (lines 45–67)**

This is **identical** to the FAQ script's main program; only the messages and the variable names differ:

| Lines | What happens | Same as FAQ lines |
|---|---|---|
| 46–48 | Print progress, call `load_ticket_documents(TICKETS_DB_PATH)`, print `19 resolved tickets loaded.` | 30–32 |
| 50–51 | Load the embedding model | 34–35 |
| 53–57 | Open (or create) the `tickets` collection in `chroma_store/` | 37–41 |
| 59–63 | Delete any existing tickets in the collection, so a re-run never duplicates | 43–47 |
| 65–67 | Embed and save all 19 tickets, then print the final count | 49–51 |

**Part 7: Start button (lines 70–71)**

| Lines | What it does |
|---|---|
| 70–71 | `if __name__ == "__main__": main()`: run `main()` only when the file is run directly. |

---

### 5.6 `ingest_pdf.py` — teaches the bot the manual

**In plain words:** Reads the PDF manual, removes the repeated text printed on every page (header and page number), cuts it into small overlapping paragraphs, and saves each paragraph to the `guides` collection.

```bash
python ingest_pdf.py
```

**What it does, step by step**

1. **Load** the PDF page by page with `PyPDFLoader`.
2. **Clean** each page: remove the header line *"Telecom Technical Reference Guide - Internal Use Only"* and the footer *"Page 2"*, *"Page 3"*… These appear on every page and carry no meaning, so leaving them in would add noise to the chunks.
3. **Chunk** the pages with `RecursiveCharacterTextSplitter`:
   - `CHUNK_SIZE = 600` characters (roughly one paragraph)
   - `CHUNK_OVERLAP = 100` characters shared between neighbouring chunks
   - Tries to split at paragraph breaks first, then line breaks, then sentence ends, then spaces, so it avoids cutting words or sentences in half.
4. **Tag** each chunk with `source="guide"` and a `chunk_index` number.
5. **Empty** the `guides` collection if it already has data (so re-running replaces rather than duplicates).
6. **Embed and save** to the `guides` collection: 36 chunks from 9 pages.

**Why chunk?** A whole page covers many topics. If the customer asks about APN settings, we want the *one paragraph* about APNs, not a full page where APNs are one line among many.

**Why overlap?** If an important sentence sits on the border between two chunks, the overlap makes sure it appears whole in at least one of them.

**Why clean first?** Before cleaning was added, 9 of the 37 chunks contained the header or a "Page N" footer. Those words have nothing to do with the chunk's topic, so they slightly blurred its "meaning numbers". After cleaning, 0 chunks contain them (and there's one chunk fewer: 36).

**Expected output**
```
Loading PDF...
  9 pages loaded.
Removing page headers and footers...
Chunking (size=600, overlap=100)...
  36 chunks produced.
Initialising embedding model...
  Removing 36 existing vectors...        ← only appears when re-running
Embedding and storing in Chroma collection 'guides'...
  Done. 36 vectors stored.
```

#### Line-by-line walkthrough of `ingest_pdf.py`

> Line numbers match [ingest_pdf.py](ingest_pdf.py). Unlike the other two scripts, this one has **no separate loading function**: everything happens inside `main()`. The **new** parts are the cleaning rules (lines 22–32), loading the PDF (lines 37–38), cleaning each page (lines 41–43), **chunking** (lines 45–51) and tagging the chunks (lines 53–56).

**Part 1: Description (lines 1–7)**

| Line | What it does |
|---|---|
| 1–7 | Docstring: loads `data/telecom_guide.pdf` into the `guides` collection, removes the repeated header/footer, splits it into chunks with `RecursiveCharacterTextSplitter`, and is safe to re-run. |

**Part 2: Imports (lines 8–20)**

```python
import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
import sqlite_compat  # noqa: F401  (must come before chromadb is imported)
import re

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from config import (
    CHROMA_DIR, EMBED_MODEL, GUIDES_COLLECTION, GUIDE_PDF_PATH, CHUNK_SIZE, CHUNK_OVERLAP,
)
```

| Line | Code | What it does |
|---|---|---|
| 8–9 | `import os` + verbosity setting | Same as the other scripts. |
| 10 | `import sqlite_compat …` | The SQLite safety fix, same as in the other scripts. |
| 11 | `import re` | **New.** Python's built-in **regular expressions** tool, for finding text that follows a pattern (like "the word Page, a space, then any number"). Used to spot the header and footer lines. |
| 13 | `from langchain_community.document_loaders import PyPDFLoader` | **New.** A ready-made tool that opens a PDF and pulls out its text, **one Document per page**. (It uses the `pypdf` library underneath.) |
| 14 | `from langchain_text_splitters import RecursiveCharacterTextSplitter` | **New.** The **chunking** tool: it cuts long text into smaller pieces at sensible places. |
| 15–16 | `Chroma`, `HuggingFaceEmbeddings` | Same as the other scripts. Note `Document` isn't imported here: the PDF loader creates Documents itself. |
| 18–20 | `from config import ( … )` | Six settings from [config.py](config.py): the database folder, the embedding model, the `guides` collection name, the PDF's path, and the two **chunking settings** `CHUNK_SIZE` (600) and `CHUNK_OVERLAP` (100). The brackets `( )` simply let one import statement continue over several lines. |

**Part 3: The cleaning rules (lines 22–24)**

```python
# Text printed on every page by data/generate_pdf.py; it carries no meaning, so it is removed
HEADER_PATTERN = re.compile(r"^Telecom Technical Reference Guide\s+-\s+Internal Use Only$")
FOOTER_PATTERN = re.compile(r"^Page \d+$")
```

| Line | Code | What it does |
|---|---|---|
| 22 | `# Text printed on every page…` | Comment explaining why these patterns exist. |
| 23 | `HEADER_PATTERN = re.compile(r"…")` | A pattern that matches **exactly** the header line. `re.compile` prepares the pattern once so it can be reused quickly. Pattern symbols: `^` = start of the line, `$` = end of the line (so only a line that is *nothing but* the header matches), `\s+` = one or more spaces (the PDF has two spaces before the dash, so this makes it tolerant). The `r` before the quotes means "raw text": backslashes are kept as they are. |
| 24 | `FOOTER_PATTERN = re.compile(r"^Page \d+$")` | Matches lines like `Page 2` or `Page 10`. `\d+` = one or more digits. Because of `^` and `$`, a sentence that merely *contains* "page 2" is **not** removed, only a line that is exactly "Page" + a number. |

**Part 4: The cleaning function (lines 27–32)**

```python
def clean_page_text(text: str) -> str:
    lines = [
        line for line in text.splitlines()
        if not HEADER_PATTERN.match(line.strip()) and not FOOTER_PATTERN.match(line.strip())
    ]
    return "\n".join(lines).strip()
```

| Line | Code | What it does |
|---|---|---|
| 27 | `def clean_page_text(text: str) -> str:` | A function that takes one page's text and returns the cleaned text. |
| 28–31 | `lines = [ … ]` | A **list comprehension**: a compact way to build a list by filtering another one. Read it as: *"for every line in the page, keep it **if** it's not the header **and** not a footer."* |
| 29 | `line for line in text.splitlines()` | `splitlines()` cuts the page into individual lines. |
| 30 | `if not HEADER_PATTERN.match(line.strip()) and not FOOTER_PATTERN.match(line.strip())` | The filter. `.strip()` removes spaces at the start and end of the line before checking, so stray spaces don't stop a match. |
| 32 | `return "\n".join(lines).strip()` | Glues the kept lines back together with line breaks (blank lines between paragraphs are kept, so the chunker can still split at paragraph ends), and trims empty space at the very start and end. |

**Example:** the second page of the PDF, before and after cleaning:

```
BEFORE                                                AFTER
Telecom Technical Reference Guide  - Internal Use Only    1. Introduction to Mobile Networks
1. Introduction to Mobile Networks                        Mobile networks have evolved through…
Mobile networks have evolved through…                     …
…                                                         bands to balance coverage and capacity.
bands to balance coverage and capacity.
Page 2
```

**Part 5: Loading the PDF (lines 35–39)**

```python
def main():
    print("Loading PDF...")
    loader = PyPDFLoader(str(GUIDE_PDF_PATH))
    pages = loader.load()
    print(f"  {len(pages)} pages loaded.")
```

| Line | Code | What it does |
|---|---|---|
| 35 | `def main():` | Start of the main program. |
| 36 | `print(...)` | Progress message. |
| 37 | `loader = PyPDFLoader(str(GUIDE_PDF_PATH))` | Prepares a loader pointed at the PDF. Nothing is read yet. `str(...)` converts the path from `config.py` (a `Path` object) into plain text, which is what this loader expects. |
| 38 | `pages = loader.load()` | **Reads the PDF.** Returns a list of 9 Documents, **one per page**. Each one's `page_content` is that page's text, and its `metadata` is filled in automatically, e.g. `{'source': '…/data/telecom_guide.pdf', 'page': 1, 'page_label': '2', 'total_pages': 9, 'producer': 'PyPDF', …}`. Note `page` counts from **0**, so the title page is `page: 0`. |
| 39 | `print(f"  {len(pages)} pages loaded.")` | Prints `9 pages loaded.` |

**Part 6: Cleaning each page (lines 41–43)**

```python
    print("Removing page headers and footers...")
    for page in pages:
        page.page_content = clean_page_text(page.page_content)
```

| Line | Code | What it does |
|---|---|---|
| 41 | `print(...)` | Progress message. |
| 42 | `for page in pages:` | Go through the 9 pages one by one. |
| 43 | `page.page_content = clean_page_text(page.page_content)` | Replaces each page's text with its cleaned version. The page's metadata (page number etc.) is untouched. This happens **before** chunking, so no chunk ever contains the header or footer. |

**Part 7: Chunking (lines 45–51)**

```python
    print(f"Chunking (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " "],
    )
    chunks = splitter.split_documents(pages)
```

| Line | Code | What it does |
|---|---|---|
| 45 | `print(...)` | Prints `Chunking (size=600, overlap=100)...` |
| 46–50 | `splitter = RecursiveCharacterTextSplitter(...)` | Creates the chunking tool with our rules. Nothing is cut yet. |
| 47 | `chunk_size=CHUNK_SIZE` | Each chunk at most 600 characters. |
| 48 | `chunk_overlap=CHUNK_OVERLAP` | Up to 100 characters of overlap. |
| 49 | `separators=["\n\n", "\n", ".", " "]` | **Where it's allowed to cut, in order of preference:** a blank line (end of paragraph), then a line break, then a full stop, then a space. "Recursive" means: try the first; if a piece is still too long, try the next one on that piece, and so on. |
| 51 | `chunks = splitter.split_documents(pages)` | **Does the cutting.** Each page is split separately, so a chunk never crosses two pages. Each chunk **inherits** its page's metadata (`page`, `source`, …). Result: 36 chunks from 9 pages. |

**Part 8: Labelling the chunks (lines 53–58)**

```python
    # Tag each chunk so we know it came from the guide
    for i, chunk in enumerate(chunks):
        chunk.metadata["source"] = "guide"
        chunk.metadata["chunk_index"] = i

    print(f"  {len(chunks)} chunks produced.")
```

| Line | Code | What it does |
|---|---|---|
| 53 | `# Tag each chunk…` | Comment. |
| 54 | `for i, chunk in enumerate(chunks):` | Loops over the chunks. `enumerate` also gives a running number `i` (0, 1, 2, …). |
| 55 | `chunk.metadata["source"] = "guide"` | **Overwrites** the loader's `source` (which was the PDF's file path) with the simple label `"guide"`. This matches the other collections' style (`faq`, `ticket`) and is what shows as `[GUIDE]` in the AI's prompt. |
| 56 | `chunk.metadata["chunk_index"] = i` | Gives each chunk its position number (0–35), so you can tell which chunks were neighbours in the original document. |
| 58 | `print(...)` | Prints `36 chunks produced.` |

**Part 9: Embedding and saving (lines 60–77)**

Identical to the FAQ script's lines 34–51; only the collection name is `GUIDES_COLLECTION` and the list being saved is called `chunks` instead of `docs`:

| Lines | What happens | Same as FAQ lines |
|---|---|---|
| 60–61 | Load the embedding model | 34–35 |
| 63–67 | Open (or create) the `guides` collection in `chroma_store/` | 37–41 |
| 69–73 | Delete any existing chunks in the collection, so a re-run never duplicates | 43–47 |
| 75–77 | `vectorstore.add_documents(chunks)`: embed all 36 chunks into vectors and save them, then print the final count | 49–51 |

**Part 10: Start button (lines 80–81)**

| Lines | What it does |
|---|---|
| 80–81 | `if __name__ == "__main__": main()`: run `main()` only when the file is run directly. |

#### The three ingest scripts side by side

| Step | `ingest_faq.py` | `ingest_tickets.py` | `ingest_pdf.py` |
|---|---|---|---|
| Settings from | `config.py` | `config.py` | `config.py` |
| Read the source | `pd.read_csv` | `sqlite3` + SQL query | `PyPDFLoader` |
| Filter | — (all rows) | Only `status = 'resolved'` | — (all pages) |
| Clean | — | — | Remove page header + "Page N" footer |
| Build text | `Q: … A: …` | `Issue: … Description: … Resolution: …` | Cleaned page text |
| Chunking | None (1 row = 1 chunk) | None (1 ticket = 1 chunk) | Recursive, 600 / 100 |
| `source` label | `faq` | `ticket` | `guide` |
| Extra labels | `category`, `faq_id` | `ticket_id`, `category`, `status` | `chunk_index`, `page`, + PDF info |
| Empty old data | ✅ | ✅ | ✅ |
| Embed + save | `add_documents(docs)` | `add_documents(docs)` | `add_documents(chunks)` |
| Final count | 25 | 19 | 36 |

---

### 5.7 `retriever.py` — the librarian

**In plain words:** Given a customer's question, it searches all three collections and returns the **3 best matches from each** — 9 snippets in total.

**Not run directly** — it is used by `rag_chain.py`.

**Key contents**

| Item | Value / purpose |
|---|---|
| `CHROMA_DIR`, `EMBED_MODEL`, collection names, `K_*` | Imported from [config.py](config.py). Because the ingest scripts import the same values, the model and folder **always match** what was used during ingestion |
| `build_retriever(k_faq=3, k_tickets=3, k_guides=3)` | Main function (defaults come from `K_FAQ`, `K_TICKETS`, `K_GUIDES`) |

**What `build_retriever()` does**

1. Loads the embedding model.
2. Opens the three existing collections (`faq`, `tickets`, `guides`).
3. Makes a "retriever" for each that returns the top *k* most similar documents.
4. Defines `retrieve(query)`, which runs all three searches and joins the results into one list: FAQ results first, then tickets, then guide chunks.
5. Wraps it in a `RunnableLambda` so it can plug into a LangChain pipeline.

**Why three separate searches instead of one big one?** The PDF produces many chunks. In one combined search, those chunks could push FAQs and tickets out of the top results. Searching each separately guarantees the AI always sees a policy answer (FAQ), a real-world fix (ticket), and technical background (guide).

#### Line-by-line walkthrough of `retriever.py`

> Line numbers match [retriever.py](retriever.py). The ingest scripts **write** to the database; this file **reads** from it. It reuses many of the same building blocks (`Chroma`, `HuggingFaceEmbeddings`), so the [ingest_faq.py walkthrough](#line-by-line-walkthrough-of-ingest_faqpy) is helpful background.

**Part 1: Description (lines 1–6)**

```python
"""
Builds a merged retriever across all three Chroma collections:
  - faq     : FAQ entries (no chunking — 1 row = 1 doc)
  - tickets : resolved support tickets (no chunking — 1 ticket = 1 doc)
  - guides  : PDF guide chunks (RecursiveCharacterTextSplitter applied at ingest)
"""
```

| Line | What it does |
|---|---|
| 1–6 | Docstring: says this file builds **one combined search** across the three collections, and reminds the reader how each collection was chunked. |

**Part 2: Imports (lines 7–11)**

```python
import sqlite_compat  # noqa: F401  (must come before chromadb is imported)
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnableLambda
from langchain_core.documents import Document
```

| Line | Code | What it does |
|---|---|---|
| 7 | `import sqlite_compat …` | The SQLite safety fix ([section 5.12](#512-sqlite_compatpy--the-sqlite-safety-fix)). It must come before line 8, which loads ChromaDB. |
| 8 | `from langchain_chroma import Chroma` | Connector to the ChromaDB vector database. |
| 9 | `from langchain_huggingface import HuggingFaceEmbeddings` | The embedding model tool. It's needed here too, because the **customer's question** must be turned into 384 numbers before it can be compared with the stored vectors. |
| 10 | `from langchain_core.runnables import RunnableLambda` | **New.** A wrapper that turns an ordinary Python function into a LangChain "**Runnable**": a building block that can be chained with others using the `\|` symbol in [rag_chain.py](rag_chain.py). |
| 11 | `from langchain_core.documents import Document` | The Document type. Here it's used only in a type hint (line 47), to say the function returns a list of Documents. |

Notice this file does **not** set `TRANSFORMERS_VERBOSITY`. It doesn't need to, because `app.py` and `main.py` set it before importing this file.

**Part 3: Settings, borrowed from `config.py` (lines 13–17)**

```python
from config import (
    CHROMA_DIR, EMBED_MODEL,
    FAQ_COLLECTION, TICKETS_COLLECTION, GUIDES_COLLECTION,
    K_FAQ, K_TICKETS, K_GUIDES,
)
```

| Line | Code | What it does |
|---|---|---|
| 13–17 | `from config import ( … )` | Brings in eight settings from [config.py](config.py). The brackets let the import continue over several lines. |
| 14 | `CHROMA_DIR`, `EMBED_MODEL` | Where to find the database, and which embedding model to use for questions. Both come from the **same place** the ingest scripts use, so the folder is always the one they wrote to, and the model always matches. (If the models differed, the question's numbers and the stored numbers wouldn't be comparable, and search would quietly return poor results with **no error message**. Keeping it in `config.py` prevents that.) |
| 15 | `FAQ_COLLECTION`, `TICKETS_COLLECTION`, `GUIDES_COLLECTION` | The three collection names: `"faq"`, `"tickets"`, `"guides"`. |
| 16 | `K_FAQ`, `K_TICKETS`, `K_GUIDES` | How many results to fetch from each collection (3 each). |

**Part 4: The function header and its settings (lines 20–24)**

```python
def build_retriever(
    k_faq: int = K_FAQ,
    k_tickets: int = K_TICKETS,
    k_guides: int = K_GUIDES,
) -> RunnableLambda:
```

| Line | Code | What it does |
|---|---|---|
| 20 | `def build_retriever(` | Defines the main function. It doesn't search anything itself; it **builds and returns** a search tool. |
| 21 | `k_faq: int = K_FAQ` | How many FAQ results to return per question. `= K_FAQ` sets the **default value** (3, from `config.py`): used unless the caller asks for a different number, e.g. `build_retriever(k_faq=5)`. |
| 22 | `k_tickets: int = K_TICKETS` | How many ticket results (default 3). |
| 23 | `k_guides: int = K_GUIDES` | How many PDF-chunk results (default 3). |
| 24 | `) -> RunnableLambda:` | Type hint: the function returns a `RunnableLambda` (a pluggable search block). |

**Part 5: Load the embedding model (line 25)**

```python
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
```

| Line | What it does |
|---|---|
| 25 | Loads the MiniLM model from your computer's cache. It's loaded **once** and shared by all three collections below, which saves memory and time. |

**Part 6: Open the three collections (lines 27–41)**

```python
    faq_store = Chroma(
        collection_name=FAQ_COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )
    tickets_store = Chroma(collection_name=TICKETS_COLLECTION, ...)
    guides_store  = Chroma(collection_name=GUIDES_COLLECTION, ...)
```

| Lines | Code | What it does |
|---|---|---|
| 27–31 | `faq_store = Chroma(collection_name=FAQ_COLLECTION, ...)` | Opens the `faq` collection. |
| 32–36 | `tickets_store = Chroma(collection_name=TICKETS_COLLECTION, ...)` | Opens the `tickets` collection. |
| 37–41 | `guides_store = Chroma(collection_name=GUIDES_COLLECTION, ...)` | Opens the `guides` collection. |
| each | `embedding_function=embeddings` | Tells each collection to use the shared model to turn questions into vectors. |
| each | `persist_directory=CHROMA_DIR` | Read from `chroma_store/` on disk. |

⚠️ If you haven't run the ingest scripts yet, Chroma doesn't complain. It quietly **creates empty collections**, so every search returns nothing and the bot answers "I don't have enough information". That's why the ingest scripts must be run first.

**Part 7: Turn each collection into a "retriever" (lines 43–45)**

```python
    faq_retriever     = faq_store.as_retriever(search_kwargs={"k": k_faq})
    tickets_retriever = tickets_store.as_retriever(search_kwargs={"k": k_tickets})
    guides_retriever  = guides_store.as_retriever(search_kwargs={"k": k_guides})
```

| Line | Code | What it does |
|---|---|---|
| 43 | `faq_store.as_retriever(search_kwargs={"k": k_faq})` | Wraps the FAQ collection in a **retriever**: a simple object with one job, *"give me a question, I'll give back the k most similar documents"*. `search_kwargs` passes search settings; here, `k = 3`. |
| 44 | `tickets_retriever = ...` | Same for tickets. |
| 45 | `guides_retriever = ...` | Same for PDF chunks. |

The extra spaces before `=` on these lines are just to line them up neatly; Python ignores them.

**How "most similar" is measured:** the search mode is **similarity** (the default). Chroma measures the **distance** between the question's vector and each stored vector: **smaller distance = closer meaning**. A real example for *"Why is my mobile internet so slow?"* in the `tickets` collection:

| Rank | Distance | Ticket | Relevant? |
|---|---|---|---|
| 1 | 0.714 | TK-008 · Extremely slow 4G speeds (below 1 Mbps) | ✅ Very |
| 2 | 1.112 | TK-001 · No internet access | ✅ Somewhat |
| 3 | 1.331 | TK-018 · Number port taking too long | ❌ Not really |

This shows an important limitation: **the retriever always returns exactly k results, even when some are weak matches.** There's no "only if it's similar enough" cut-off. The AI then has to ignore the irrelevant ones, which is one reason the prompt tells it to answer from the context *only when it's sufficient*.

**Part 8: The search function itself (lines 47–52)**

```python
    def retrieve(query: str) -> list[Document]:
        return (
            faq_retriever.invoke(query)
            + tickets_retriever.invoke(query)
            + guides_retriever.invoke(query)
        )
```

| Line | Code | What it does |
|---|---|---|
| 47 | `def retrieve(query: str) -> list[Document]:` | Defines the function that does the actual searching. It takes the customer's question (text) and returns a list of Documents. It's defined **inside** `build_retriever`, so it can use the three retrievers created above. (A function that remembers variables from the function around it is called a **closure**.) |
| 48 | `return (` | Return the result of the expression in brackets. |
| 49 | `faq_retriever.invoke(query)` | **Runs the FAQ search.** `.invoke()` is LangChain's standard "run this" command. Behind the scenes: turn the question into 384 numbers → find the 3 nearest FAQ vectors → return them as Documents (text + metadata). |
| 50 | `+ tickets_retriever.invoke(query)` | Runs the ticket search and **joins** its 3 results onto the list (`+` on two lists sticks them together). |
| 51 | `+ guides_retriever.invoke(query)` | Runs the guide search and joins its 3 results. |
| 52 | `)` | Final result: **one list of 9 Documents**, always in the order FAQ ×3 → tickets ×3 → guides ×3. |

The three searches run **one after another**, not at the same time. Each one also converts the question into numbers **separately**, so the same question is embedded 3 times. With a small local model this takes only milliseconds, but it's an easy optimisation if the project grows.

**Part 9: Return the finished search tool (line 54)**

```python
    return RunnableLambda(retrieve)
```

| Line | What it does |
|---|---|
| 54 | Wraps `retrieve` in a `RunnableLambda` and hands it back. Now it can be dropped into the LangChain pipeline in [rag_chain.py](rag_chain.py) like any other building block: `retriever \| _format_docs`. It also gains standard methods such as `.invoke(question)`. |

#### How `retriever.py` is used

```python
# in rag_chain.py
retriever = build_retriever()          # build the search tool once (loads model, opens DB)
docs = retriever.invoke("Why is my bill higher this month?")   # search: returns 9 Documents
```

| When | What runs | How often |
|---|---|---|
| App starts | `build_retriever()`: load model, open 3 collections, create 3 retrievers | **Once** (the website caches it) |
| Each customer question | `retrieve(question)`: embed question, search 3 collections, join results | **Every question** |

**Changing the number of results:** change `K_FAQ`, `K_TICKETS`, `K_GUIDES` in [config.py](config.py), or call `build_retriever(k_faq=2, k_tickets=4, k_guides=3)` from [rag_chain.py](rag_chain.py). More results give the AI more context but more noise; fewer are more focused but may miss something.

---

### 5.8 `rag_chain.py` — the brain

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
| 3 | `ChatGoogleGenerativeAI` | Send to the AI model (Gemini) |
| 4 | `StrOutputParser` | Extract plain text from the AI's response |

**AI settings (`ChatGoogleGenerativeAI`)**

| Setting | Value | Meaning |
|---|---|---|
| `model` | `gemini-3.5-flash` | Which AI model to use |
| `temperature` | `0` | No creativity/randomness — consistent, factual answers |
| `max_retries` | `2` | Retry twice if the network call fails |

The original **Groq** settings are still in the file as comments, for switching back.

#### Line-by-line walkthrough of `rag_chain.py`

> Line numbers match [rag_chain.py](rag_chain.py). This is the file where **R**etrieval, **A**ugmentation (adding the found text to the prompt) and **G**eneration (the AI writing the answer) come together, the three letters of "RAG".

**Part 1: Description (lines 1–4)**

```python
"""
Builds the RAG chain:
  merged retriever → prompt → Gemini (Google) → string output
"""
```

| Line | What it does |
|---|---|
| 1–4 | Docstring: a one-line map of the pipeline this file builds. Search → prompt → AI → plain text. |

**Part 2: Imports (lines 5–13)**

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
# from langchain_groq import ChatGroq  # previous provider, see build_chain()
from langchain_google_genai import ChatGoogleGenerativeAI

from config import LLM_MODEL, LLM_TEMPERATURE
from retriever import build_retriever
```

| Line | Code | What it does |
|---|---|---|
| 5 | `ChatPromptTemplate` | A **fill-in-the-blanks message template** for chat AIs. You write the message once with blanks like `{context}` and `{question}`, and it fills them in for every new question. |
| 6 | `StrOutputParser` | Takes the AI's reply (which arrives as a message object with extra details) and pulls out **just the text**. |
| 7 | `RunnablePassthrough` | A building block that **passes its input through unchanged**. It's used to carry the customer's question forward to the prompt. |
| 8 | `Document` | The Document type, used only in a type hint on line 32. |
| 9 | `# from langchain_groq import ChatGroq` | The old connector to **Groq**, commented out (Python ignores lines starting with `#`). Kept for switching back. |
| 10 | `from langchain_google_genai import ChatGoogleGenerativeAI` | The connector to **Google Gemini**, the AI that now writes the answers. |
| 12 | `from config import LLM_MODEL, LLM_TEMPERATURE` | Brings in the AI model name and temperature from [config.py](config.py). The blank line before it is a Python convention: outside libraries first, then the project's own files. |
| 13 | `from retriever import build_retriever` | Imports our own search tool from [retriever.py](retriever.py). |

**Part 3: The system prompt, the bot's instructions (lines 15–29)**

```python
SYSTEM_PROMPT = """You are a helpful and professional telecom customer care assistant.
Your job is to help customers resolve technical issues with their mobile service.

Use ONLY the context below to answer the customer's question.
The context comes from three sources, each labelled in square brackets:
- [FAQ] entries (general policy and how-to information)
- [TICKET] past support tickets (real resolved cases with step-by-step resolutions)
- [GUIDE] excerpts from the telecom technical reference guide (background and troubleshooting procedures)

If the context does not contain enough information to answer confidently, say so clearly \
and suggest the customer call 611 or use the MyTelecom app.

Context:
{context}
"""
```

A **system prompt** is the hidden instruction sheet given to the AI before the customer's question. The customer never sees it, but it shapes every answer.

| Line(s) | Text | What it does |
|---|---|---|
| 15 | `SYSTEM_PROMPT = """…` | Stores the instructions in a setting. Triple quotes `"""` allow text spanning many lines. |
| 15–16 | "You are a helpful and professional telecom customer care assistant…" | Gives the AI a **role** and a **goal**, which sets its tone and focus. |
| 18 | "Use **ONLY** the context below…" | **Grounding**: tells the AI not to rely on its general knowledge. This is the main defence against made-up answers (hallucinations). |
| 19–22 | "The context comes from three sources, each labelled in square brackets: [FAQ]… [TICKET]… [GUIDE]…" | Explains what kinds of information it will receive, and uses the **same labels** that `_format_docs` puts on each snippet, so the AI knows how to treat each one: FAQs for policy, tickets for proven fixes, the guide for technical background. (An earlier version listed only FAQ and tickets, even though guide chunks were always sent. The AI still read them, but it wasn't told what they were.) |
| 24–25 | "If the context does not contain enough information… call 611 or use the MyTelecom app." | A **safe fallback**: when unsure, admit it and point to a human channel instead of guessing. The `\` at the end of line 24 joins lines 24 and 22 into one line of text. |
| 27–28 | `Context:` `{context}` | **The blank to fill in.** At run time, the 9 search results replace `{context}`. |

**Part 4: Formatting the search results (lines 32–37)**

```python
def _format_docs(docs: list[Document]) -> str:
    sections = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown").upper()
        sections.append(f"[{source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(sections)
```

The retriever returns a list of 9 Document objects, but the prompt needs **plain text**. This function converts one into the other.

| Line | Code | What it does |
|---|---|---|
| 32 | `def _format_docs(docs: list[Document]) -> str:` | Takes a list of Documents and returns one string. The `_` at the start of the name is a Python convention meaning "**internal helper**, only meant to be used inside this file". |
| 33 | `sections = []` | Empty list to collect each formatted snippet. |
| 34 | `for doc in docs:` | Go through the 9 Documents one by one. |
| 35 | `source = doc.metadata.get("source", "unknown").upper()` | Reads the `source` label set by the ingest scripts (`faq`, `ticket` or `guide`). `.get(..., "unknown")` uses `"unknown"` if the label is missing, instead of crashing. `.upper()` makes it capitals: `FAQ`, `TICKET`, `GUIDE`. |
| 36 | `sections.append(f"[{source}]\n{doc.page_content}")` | Builds one labelled snippet: the label in square brackets, a line break, then the text. |
| 37 | `return "\n\n---\n\n".join(sections)` | Glues all snippets into one block, with a `---` divider and blank lines between them, so the AI can clearly see where one snippet ends and the next begins. |

**Real output** for the question *"How do I enable Wi-Fi calling?"* (first part shown; the full block is about 3,300 characters):

```
[FAQ]
Q: How do I enable Wi-Fi calling?
A: Go to Settings > Phone > Wi-Fi Calling and toggle it on. Wi-Fi calling lets you make and
receive calls over a Wi-Fi network when cellular signal is weak. Your plan must include this
feature; if not, call 611 to add it.

---

[FAQ]
Q: Why am I unable to make international calls?
A: International calling must be enabled on your account...

---
...  (then 3 [TICKET] snippets and 3 [GUIDE] snippets)
```

**Part 5: Building the chain (lines 40–41)**

```python
def build_chain():
    retriever = build_retriever()
```

| Line | Code | What it does |
|---|---|---|
| 40 | `def build_chain():` | The main function. `app.py` and `main.py` call it **once** at start-up to get a ready-to-use chatbot pipeline. |
| 41 | `retriever = build_retriever()` | Creates the search tool from [retriever.py](retriever.py) (loads the embedding model, opens the 3 collections). Uses the default 3 results per collection. |

**Part 6: The prompt template (lines 43–46)**

```python
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ])
```

Chat AIs receive a conversation as a list of messages, each with a **role**:

| Line | Code | What it does |
|---|---|---|
| 43 | `ChatPromptTemplate.from_messages([...])` | Creates the template from a list of (role, text) pairs. |
| 44 | `("system", SYSTEM_PROMPT)` | **Message 1, role "system"**: the instructions + the context (blank `{context}`). The AI treats this as its rules. |
| 45 | `("human", "{question}")` | **Message 2, role "human"**: the customer's question (blank `{question}`). |

When filled in for the Wi-Fi example, the AI receives 2 messages: a system message of about **3,800 characters** (instructions + 9 snippets) and a human message of **30 characters** (the question). Almost all of what the AI reads is the retrieved context.

**Part 7: The AI model settings (lines 48–65)**

```python
    # Previous provider: Qwen on Groq. Groq returns "403 Access denied" from Streamlit Community
    # Cloud's servers, so it was replaced by Gemini. To switch back: uncomment this block and the
    # ChatGroq import, comment out the Gemini block, set LLM_MODEL in config.py and GROQ_API_KEY.
    # llm = ChatGroq(
    #     model=LLM_MODEL,
    #     temperature=LLM_TEMPERATURE,
    #     max_tokens=None,
    #     reasoning_format="parsed",
    #     timeout=None,
    #     max_retries=2,
    # )

    # Reads the key from the GEMINI_API_KEY (or GOOGLE_API_KEY) environment variable
    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        max_retries=2,
    )
```

`llm` stands for **Large Language Model**. This creates the connection to the AI; nothing is sent yet.

**The commented-out Groq block (lines 48–58):** the project originally used **Qwen on Groq**. When the app was deployed to Streamlit Community Cloud, Groq refused every request with *"403 Access denied"* because it blocks that platform's servers, so the AI was switched to **Google Gemini**. The old code is kept as **comments** (lines starting with `#`, which Python ignores) rather than deleted, so it's easy to see what changed and to switch back. Lines 48–50 explain how.

| Line | Setting | What it does |
|---|---|---|
| 60 | `# Reads the key from …` | Comment: where the API key comes from. |
| 61 | `ChatGoogleGenerativeAI(...)` | Connects to Google's **Gemini** API. It automatically reads your key from the **`GEMINI_API_KEY`** (or `GOOGLE_API_KEY`) environment variable, loaded from `.env` by `app.py` / `main.py`, or from **Secrets** on Streamlit Cloud. If the key is missing, this is where it fails. |
| 62 | `model=LLM_MODEL` | Which Gemini model to use. Set in [config.py](config.py) to `"gemini-3.5-flash"`: a fast, free-tier-friendly model. (The newest `gemini-3.8-flash` was tried first but often returned *"503 high demand"*.) |
| 63 | `temperature=LLM_TEMPERATURE` | Set to `0` in [config.py](config.py). **Randomness dial.** 0 = always pick the most likely next word → consistent, factual answers. Higher values (e.g. 0.7) give more varied, creative wording. Support answers should be predictable, so 0 is right here. |
| 64 | `max_retries=2` | If the request fails (network glitch, Gemini briefly busy), try **2 more times** before giving up. |

**Groq vs Gemini settings:** Groq's `reasoning_format="parsed"` isn't needed here. Gemini keeps its internal "thinking" out of the answer text by default. `max_tokens=None` and `timeout=None` were Groq's defaults anyway, so they're simply left out.

**Part 8: Connecting everything into one pipeline (lines 67–73)**

```python
    chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain
```

This is the heart of the file. It's written in **LCEL** (LangChain Expression Language). The `|` symbol (called a "pipe") means **"send the output of the left side into the right side"**, like an assembly line.

| Line | Code | What it does |
|---|---|---|
| 68 | `{"context": …, "question": …}` | A **two-lane step**. The customer's question goes into *both* lanes at the same time, and the result is a dictionary with two named items. LangChain automatically turns `{ }` into a parallel step. |
| 68 | `"context": retriever \| _format_docs` | **Lane 1:** question → search (9 Documents) → format into one labelled text block. Result is stored as `context`. |
| 68 | `"question": RunnablePassthrough()` | **Lane 2:** the question passes through **unchanged** and is stored as `question`. Needed because the prompt has a `{question}` blank to fill, too. |
| 69 | `\| prompt` | Takes `{context, question}` and **fills the blanks** in the template → 2 ready chat messages. |
| 70 | `\| llm` | Sends the messages to **Gemini** → receives the AI's reply. |
| 71 | `\| StrOutputParser()` | Pulls out **just the answer text** from the reply (dropping the separate reasoning and other details). |
| 73 | `return chain` | Hands the finished pipeline back to `app.py` / `main.py`. |

**The whole journey of one question:**

```
"How do I enable Wi-Fi calling?"
        │
        ├──► Lane 1: retriever ──► 9 Documents ──► _format_docs ──► "[FAQ]\nQ: How do I enable…\n---\n…"   = context
        └──► Lane 2: RunnablePassthrough ─────────────────────────► "How do I enable Wi-Fi calling?"         = question
        │
        ▼
   prompt     → [system: instructions + context]  [human: question]
        ▼
   llm        → Gemini writes the answer (on Google's servers)
        ▼
   StrOutputParser → "To enable Wi-Fi calling, go to Settings > Phone > Wi-Fi Calling…"
```

#### How `rag_chain.py` is used

```python
chain = build_chain()                        # once, at start-up
chain.invoke("How do I enable Wi-Fi calling?")   # → full answer, all at once
chain.stream("How do I enable Wi-Fi calling?")   # → answer arrives word by word
```

Both `app.py` and `main.py` use **`.stream()`**. The search and prompt-filling steps finish first (in a fraction of a second); then the AI's words are passed through to the screen **as they're generated**, so the customer sees the answer start appearing almost immediately instead of waiting for the whole reply.

| When | What runs | How often |
|---|---|---|
| App starts | `build_chain()`: build retriever, template, AI connection, and pipeline | **Once** |
| Each question | `chain.stream(question)`: search → format → fill prompt → AI → text | **Every question** |

**Common changes:**

| To change… | Edit |
|---|---|
| The bot's tone, rules or fallback message | `SYSTEM_PROMPT` (lines 15–29) |
| How snippets are labelled for the AI | `_format_docs` (lines 32–37) |
| The AI model | `LLM_MODEL` in [config.py](config.py) |
| How creative the answers are | `LLM_TEMPERATURE` in [config.py](config.py) |
| How many search results the AI sees | `K_FAQ`, `K_TICKETS`, `K_GUIDES` in [config.py](config.py) |

#### Common questions about `rag_chain.py`

**Q: On line 41, `retriever = build_retriever()`, we don't pass the question. Why?**

Because that line **builds** the search tool; it doesn't **use** it yet. There are two separate moments:

| Moment | Code | What happens | Question involved? |
|---|---|---|---|
| **1. Build** (once, at start-up) | `retriever = build_retriever()` (line 41) | Loads the embedding model, opens the 3 collections, creates the 3 retrievers, and returns the `retrieve` function wrapped in a `RunnableLambda` | ❌ No |
| **2. Use** (every question) | `chain.stream(question)` in `app.py` / `main.py` | The question flows through the pipeline and reaches the retriever | ✅ Yes |

**An analogy:** line 41 is like **installing a coffee machine**: plugging it in, filling the water and beans. You don't need a coffee order to install it. Each customer's question is **pressing the button**, which can happen many times on the same machine.

**Why it's designed this way:** building is **slow** (loading the model and opening the database takes a few seconds), while searching is **fast** (milliseconds). By building once and reusing it for every question, the app avoids reloading everything on each message. That's also why `app.py` caches the chain with `@st.cache_resource`.

You can see both moments by hand in a Python shell:

```python
from retriever import build_retriever
retriever = build_retriever()                                 # build (no question)
docs = retriever.invoke("How do I enable Wi-Fi calling?")     # use (question goes in here)
```

**Q: So where does the question actually enter?**

Follow it through three files:

```python
# ① app.py: the question enters the chain
response = st.write_stream(chain.stream(question))
```

```python
# ② rag_chain.py, line 68: LangChain hands the question to the retriever automatically
{"context": retriever | _format_docs, "question": RunnablePassthrough()}
```

```python
# ③ retriever.py, lines 47–52: the question arrives here as `query`
def retrieve(query: str) -> list[Document]:
    return (
        faq_retriever.invoke(query)
        + tickets_retriever.invoke(query)
        + guides_retriever.invoke(query)
    )
```

**Q: On line 68, how does the question get in automatically when nothing seems to accept it as an argument?**

It *is* accepted as an argument: `query` in `retrieve(query: str)` in [retriever.py](retriever.py). You just never see the call, because **LangChain makes the call for you**.

**Line 55 doesn't run anything; it only describes the steps.**

```python
chain = (
    {"context": retriever | _format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
```

When Python runs this, **no searching happens and no question exists yet**. The `|` symbols just build a **recipe**, a list of steps saved inside the `chain` object:

```
chain = [ step 1: {context: retriever → _format_docs, question: passthrough},
          step 2: prompt,
          step 3: llm,
          step 4: StrOutputParser ]
```

It's like writing a function with no input yet. Line 55 is the **definition**, not the **call**.

**The question arrives later, when the chain is called:**

```python
chain.invoke("How do I enable Wi-Fi calling?")    # or chain.stream(...)
```

That's the moment the question is passed as an argument, to the **chain**. The chain then walks through its saved steps and passes the input to each one:

```python
# What LangChain does inside chain.invoke(question), simplified:

# Step 1: the { } dictionary. Give the SAME input to every lane.
context  = _format_docs( retriever.invoke(question) )   # ← here! the retriever gets the question
question = question                                     # RunnablePassthrough: return input unchanged
step1_output = {"context": context, "question": question}

# Step 2 onward: each step's output becomes the next step's input
messages = prompt.invoke(step1_output)
reply    = llm.invoke(messages)
answer   = StrOutputParser().invoke(reply)
return answer
```

And `retriever.invoke(question)` is what finally calls `retrieve(query)`, with `query = "How do I enable Wi-Fi calling?"`.

**The same chain written without LangChain** would be just this:

```python
def chain(question):                                  # ← the question IS an argument
    context  = _format_docs(retrieve(question))       # lane 1
    messages = fill_prompt(context, question)         # lane 2 + prompt
    reply    = call_gemini(messages)                  # llm
    return reply.text                                 # StrOutputParser
```

Line 55 is LangChain's shorthand for this function. Instead of writing `retrieve(question)` yourself, you list the steps, and LangChain writes the "pass the input along" part for you.

**Q: How does `|` know to do this?**

Every LangChain building block (`retriever`, `prompt`, `llm`, the parser) is a **Runnable**, which makes two promises:

1. It has an `.invoke(input)` method.
2. `a | b` creates a new Runnable whose `.invoke(x)` means **`b.invoke(a.invoke(x))`**: run `a`, then feed its result to `b`.

A `{ }` dictionary inside a chain is automatically turned into a **parallel step**, whose `.invoke(x)` gives **the same `x` to every value in the dictionary**. That's why both `retriever` and `RunnablePassthrough()` receive the question.

This is also why [retriever.py](retriever.py) wraps `retrieve` in `RunnableLambda`. A plain Python function doesn't have `.invoke()` and can't take part in `|`. Wrapping it turns it into a Runnable, so LangChain knows how to call it with the input.

**In one line:**

> **Line 55 defines the steps. `chain.stream(question)` in `app.py` provides the question. LangChain calls `retrieve(query)` with it.**

**Q: So is this the right understanding? `build_retriever()` sets up ChromaDB and returns `retrieve()`, and later `retriever | _format_docs` calls `retrieve()` through `retriever.invoke(query)`?**

Yes, that's correct, with two small refinements.

**Step 1: `retriever = build_retriever()` (line 41, once at start-up)**

- Loads the embedding model.
- Opens the three ChromaDB collections (`faq`, `tickets`, `guides`).
- Creates the three small retrievers.
- **Defines** `retrieve()` but doesn't run it.
- Returns `RunnableLambda(retrieve)`, which is stored in the variable `retriever`.

So `retriever` is a **wrapper holding the `retrieve` function**.

> **Refinement 1: "connection" to ChromaDB.** ChromaDB here isn't a separate server you connect to over a network. It runs **inside your Python program** and reads the files in `chroma_store/`. So "opens the database files" is more accurate than "establishes a connection". The effect is the same: it's ready to search.

**Step 2: `{"context": retriever | _format_docs, ...}` (line 68)**

This only **records** that "the retriever comes first, then `_format_docs`". Nothing runs yet.

**Step 3: When a question arrives, `chain.stream(question)`**

```
chain.stream("How do I enable Wi-Fi calling?")
   └─► LangChain calls  retriever.invoke("How do I enable Wi-Fi calling?")
          └─► RunnableLambda calls  retrieve("How do I enable Wi-Fi calling?")
                 └─► faq_retriever.invoke(...) + tickets_retriever.invoke(...) + guides_retriever.invoke(...)
                        └─► returns 9 Documents
   └─► LangChain calls  _format_docs(those 9 Documents)  →  context text
```

> **Refinement 2: who calls `.invoke()`?** *You* never write `retriever.invoke(query)` in this project. **LangChain** calls it automatically when the chain runs. Your code only provides the question to `chain.stream(...)`.

**Q: `build_retriever()` finished running at start-up. How does `retrieve()` still reach the three retrievers later?**

`retrieve()` uses `faq_retriever`, `tickets_retriever` and `guides_retriever` every time a question comes in, even though the function that created them (`build_retriever`) has already finished. That works because `retrieve` was defined **inside** `build_retriever`, so it **remembers** those variables. This is called a **closure**.

**An analogy:** think of it as a backpack. When `retrieve` is created, it packs the three retrievers and carries them everywhere, even after `build_retriever()` is done.

**In one line:**

> **`build_retriever()` prepares everything once and returns `retrieve` in a wrapper. On each question, LangChain calls `retriever.invoke(question)`, which runs `retrieve(question)` using the three retrievers it remembered.**

---

### 5.9 `app.py` — the website

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

1. Hides noisy library warnings (`TRANSFORMERS_VERBOSITY=error`), applies the SQLite safety fix (`import sqlite_compat`, see [5.12](#512-sqlite_compatpy--the-sqlite-safety-fix)), and loads API keys from `.env`.
2. `get_chain()` runs **once** and is cached (`@st.cache_resource`), so the embedding model isn't reloaded on every message. It:
   - calls `ensure_vector_store()` ([5.11](#511-setup_vector_storepy--builds-the-database-automatically)), which builds any empty collection. On a brand-new server this takes about a minute, and the page shows *"Preparing the knowledge base (first start only)…"* meanwhile;
   - then builds the RAG chain with `build_chain()`.
3. Uses `st.session_state` to remember:
   - `messages` — the chat history shown on screen
   - `pending_question` — a question chosen by clicking a sample button
4. Redraws all previous messages.
5. Takes the new question from either the text box or a clicked sample button.
6. Shows the question, then calls `chain.stream(question)` and displays the answer **word by word** as it arrives (`st.write_stream`).
7. Saves both the question and answer to the history.

**Note:** The history is only for display. The AI does **not** see previous messages, so every question is answered on its own.

---

### 5.10 `main.py` — the terminal version

**In plain words:** The same chatbot without a website — you type in the terminal and read the answer there. Handy for quick testing.

```bash
python main.py
```

**How it works**

1. Loads API keys, applies the SQLite safety fix, and calls `ensure_vector_store()` to build any empty collection.
2. Builds the chain once.
3. Loops forever:
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

### 5.11 `setup_vector_store.py` — builds the database automatically

**In plain words:** A safety check that runs when the chatbot starts. It looks at the vector database, and if any of the three collections is missing or empty, it runs that collection's ingest script **once**, automatically. After that, startup is instant.

**Why it exists:** `chroma_store/` is git-ignored, so when the project is put on a new computer or a **web server**, the database doesn't come with it. Without this check, the bot would start with an empty database and answer "I don't have enough information" to every question until someone remembered to run the three ingest scripts by hand. Now the app builds what's missing on its own.

**When it runs:**

| Situation | What happens |
|---|---|
| `app.py`: first question after the server starts | Checks the database; builds any empty collection (about a minute the very first time), then answers |
| `main.py`: on start | Same check before the first `Customer:` prompt |
| Run by hand: `python setup_vector_store.py` | Same check, then prints `Vector store is ready.` A handy one-command alternative to running the three ingest scripts |
| Database already complete | Nothing is rebuilt; the check takes a fraction of a second |

**Real output on a fresh setup (no `chroma_store/` folder):**

```
Collection 'faq' is empty, building it now...
Loading FAQ documents...
  25 FAQ entries loaded.
...
Collection 'tickets' is empty, building it now...
...
Collection 'guides' is empty, building it now...
...
  Done. 36 vectors stored.
```

> It only fills **empty** collections. If you *changed* the data (e.g. edited `faq.csv`), the collection isn't empty, so nothing happens: run that ingest script yourself, as before.

#### Line-by-line walkthrough of `setup_vector_store.py`

> Line numbers match [setup_vector_store.py](setup_vector_store.py).

**Part 1: Description (lines 1–8)**

| Line | What it does |
|---|---|
| 1–8 | Docstring: explains why the check is needed (`chroma_store/` isn't in git), who calls it, and how to run it by hand. |

**Part 2: Imports (lines 9–15)**

```python
import sqlite_compat  # noqa: F401  (must come before chromadb is imported)
import chromadb

import ingest_faq
import ingest_tickets
import ingest_pdf
from config import CHROMA_DIR, FAQ_COLLECTION, TICKETS_COLLECTION, GUIDES_COLLECTION
```

| Line | Code | What it does |
|---|---|---|
| 9 | `import sqlite_compat …` | The SQLite safety fix ([section 5.12](#512-sqlite_compatpy--the-sqlite-safety-fix)); must come before ChromaDB is loaded on the next line. |
| 10 | `import chromadb` | ChromaDB itself, used **directly** here (not through LangChain), because we only need to ask "how many items are in each collection?" |
| 12–14 | `import ingest_faq` … `import ingest_pdf` | Loads the three ingest scripts **as modules**, so their `main()` functions can be called from here. Because of the `if __name__ == "__main__":` line at the bottom of each, importing them does **not** start an ingest; it only makes their functions available. |
| 15 | `from config import …` | The database folder and the three collection names. |

**Part 3: Which script fills which collection (lines 17–21)**

```python
INGESTERS = {
    FAQ_COLLECTION: ingest_faq.main,
    TICKETS_COLLECTION: ingest_tickets.main,
    GUIDES_COLLECTION: ingest_pdf.main,
}
```

| Line | Code | What it does |
|---|---|---|
| 17–21 | `INGESTERS = { … }` | A **dictionary** (a lookup table) pairing each collection name with the function that builds it: `"faq"` → `ingest_faq.main`, and so on. Note there are **no brackets** after `main`: we're storing the function itself, to call later, not calling it now. |

**Part 4: The check (lines 24–31)**

```python
def ensure_vector_store() -> None:
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    sizes = {collection.name: collection.count() for collection in client.list_collections()}

    for name, ingest in INGESTERS.items():
        if sizes.get(name, 0) == 0:
            print(f"Collection '{name}' is empty, building it now...")
            ingest()
```

| Line | Code | What it does |
|---|---|---|
| 24 | `def ensure_vector_store() -> None:` | The function `app.py` and `main.py` call. `-> None` means it doesn't return anything; its job is the side effect of filling the database. |
| 25 | `client = chromadb.PersistentClient(path=CHROMA_DIR)` | Opens the database folder. If `chroma_store/` doesn't exist yet, ChromaDB creates it. |
| 26 | `sizes = {collection.name: collection.count() for …}` | Builds a lookup of **how many items each existing collection holds**, e.g. `{'faq': 25, 'tickets': 19, 'guides': 36}`. On a fresh server this is just `{}`. (This compact `{… for …}` form is a **dictionary comprehension**.) |
| 28 | `for name, ingest in INGESTERS.items():` | Goes through the three collections one by one, getting each name and its ingest function. |
| 29 | `if sizes.get(name, 0) == 0:` | `.get(name, 0)` returns the collection's size, or `0` if it doesn't exist. So this is true for both **missing** and **empty** collections. (An empty collection can exist if the app was started once before ingesting, because ChromaDB quietly creates empty collections when they're opened.) |
| 30 | `print(...)` | Says which collection is being built. |
| 31 | `ingest()` | Calls that collection's ingest function, e.g. `ingest_faq.main()`: exactly the same as running `python ingest_faq.py`. |

**Part 5: Running it by hand (lines 34–36)**

| Line | What it does |
|---|---|
| 34–36 | When run directly (`python setup_vector_store.py`), do the check and print `Vector store is ready.` |

---

### 5.12 `sqlite_compat.py` — the SQLite safety fix

**In plain words:** A tiny file that protects against one specific server problem. ChromaDB stores its data using **SQLite** (a small database engine built into Python), and it needs **version 3.35 or newer**. Some older Linux servers come with an older SQLite, and on those ChromaDB refuses to start with an error like *"Your system has an unsupported version of sqlite3"*. This file checks the version and, **only if it's too old**, swaps in a newer SQLite that comes with the `pysqlite3-binary` package.

| Where it runs | SQLite version | What this file does |
|---|---|---|
| Your Windows PC | 3.50 | Nothing |
| Most modern servers | 3.40+ | Nothing |
| An old Linux server | e.g. 3.31 | Swaps in the newer SQLite from `pysqlite3-binary` |

`pysqlite3-binary` is listed in `pyproject.toml` and `requirements.txt` for **Linux only**, because that's the only place it's ever needed (and the only place it has ready-made installs).

**Where it's imported:** at the top of every file that loads ChromaDB (the three ingest scripts, `retriever.py`, `setup_vector_store.py`) and of the two entry points (`app.py`, `main.py`). It must always come **before** ChromaDB is loaded, because ChromaDB checks the SQLite version the moment it starts.

#### Line-by-line walkthrough of `sqlite_compat.py`

> Line numbers match [sqlite_compat.py](sqlite_compat.py).

```python
import sqlite3
import sys

MIN_SQLITE_VERSION = (3, 35, 0)

if sqlite3.sqlite_version_info < MIN_SQLITE_VERSION:
    import pysqlite3

    sys.modules["sqlite3"] = pysqlite3
```

| Line | Code | What it does |
|---|---|---|
| 1–7 | Docstring | Explains the problem, the fix, and the rule "import this before ChromaDB". |
| 8 | `import sqlite3` | Loads Python's built-in SQLite, to check its version. |
| 9 | `import sys` | Loads Python's "system" toolkit. Here we need `sys.modules`: Python's list of **already-loaded modules**. |
| 11 | `MIN_SQLITE_VERSION = (3, 35, 0)` | The oldest version ChromaDB accepts, written as (major, minor, patch). |
| 13 | `if sqlite3.sqlite_version_info < MIN_SQLITE_VERSION:` | Compares the real version, e.g. `(3, 50, 4)`, with the minimum. Python compares these number by number, so `(3, 31, 1) < (3, 35, 0)` is true and `(3, 50, 4) < (3, 35, 0)` is false. |
| 14 | `import pysqlite3` | Only on an old server: loads the newer SQLite from `pysqlite3-binary`. |
| 16 | `sys.modules["sqlite3"] = pysqlite3` | **The swap.** It tells Python: "from now on, whenever any code asks for `sqlite3`, hand it `pysqlite3` instead." When ChromaDB loads a moment later and asks for `sqlite3`, it gets the newer version without knowing anything changed. |

**Why `# noqa: F401` appears on every import of it:** the scripts never *use* anything from `sqlite_compat` by name. Importing it is enough, because its code runs once on import. Code checkers would flag it as an "unused import" (rule F401); `# noqa: F401` tells them it's on purpose.

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
| `pyproject.toml` | Project name, Python version (3.11+), and list of libraries. Also pins PyTorch to the **CPU-only** build (`[tool.uv.sources]`) |
| `uv.lock` | Exact versions of every library, so everyone installs the same thing |
| `requirements.txt` | The same exact versions, in the classic format that `pip` and most hosting platforms read. Generated from `uv.lock` with `uv export`. Its first line points `pip` to PyTorch's CPU-only downloads; `uv export` doesn't write that line, so **add it back** whenever you regenerate the file |
| `.gitignore` | Tells git which files to never upload (e.g. `.env`, `.venv/`, `chroma_store/`) |
| `config.py` | The project's **own settings**: paths, collection names, embedding and AI model, chunk size, results per collection. See [section 5.3](#53-configpy--the-settings-file) |
| `LICENSE` | The MIT licence: anyone may use, copy and modify the code, as long as they keep the copyright notice. Without a licence file, others legally can't reuse public code |

**Required keys in `.env`**

| Key | Where to get it | Used for |
|---|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com → **Get API key** (free) | Calling the AI model (Gemini) |
| ~~`GROQ_API_KEY`~~ | https://console.groq.com | Previous AI provider; only needed if you switch back to Groq |
| `HF_TOKEN` | https://huggingface.co/settings/tokens | Downloading the embedding model (optional, see below) |

**Q: Is `HF_TOKEN` really required?**

Not really. The embedding model (`all-MiniLM-L6-v2`) is public, so it downloads without a token. The token only helps you avoid **download rate limits**.

**Q: What is a "rate limit"?**

Hugging Face lets anyone download public models for free, but it limits how much each visitor can download in a given period. This limit is called a **rate limit**. It stops one person or bot from overloading their servers.

| | Without a token | With a token (`HF_TOKEN`) |
|---|---|---|
| Who Hugging Face thinks you are | An anonymous visitor | A logged-in user |
| Download limit | Smaller | Bigger |
| Risk of being blocked | Higher. You may briefly see an error like `429 Too Many Requests` | Much lower |

**An analogy:** a public library lets anyone walk in and read. A guest can borrow only 2 books at a time; a member with a library card can borrow 10. The book (the model) is free either way. The card (the token) just raises your borrowing limit.

**Q: Does this project need it?**

Hardly. The model is small (about 88 MB) and is downloaded only **once**. After that it's saved on your computer (in `C:\Users\<you>\.cache\huggingface\hub\`) and runs locally, so you'd almost never hit the anonymous limit. The token is a safety net. It matters more when:

- downloading many models, or very large ones
- working on a shared network (office, college, cloud server), where many people share the same limit

**Libraries used (from `pyproject.toml`)**

| Library | Role |
|---|---|
| `langchain`, `langchain-core` | Pipeline framework |
| `langchain-google-genai` | Connects LangChain to Google's Gemini AI |
| `langchain-groq` | Connects LangChain to Groq's AI (previous provider, kept for switching back) |
| `langchain-chroma`, `chromadb` | Vector database |
| `langchain-huggingface`, `sentence-transformers`, `torch` | Embedding model. `torch` (PyTorch) is pinned to the small **CPU-only** build, since the GPU build adds several GB this app never uses |
| `pysqlite3-binary` | A newer SQLite, installed **on Linux servers only**, used by `sqlite_compat.py` if the server's own SQLite is too old for ChromaDB |
| `langchain-community`, `pypdf` | PDF loading |
| `langchain-text-splitters` | Chunking |
| `pandas` | Reading the CSV |
| `fpdf2` | Generating the PDF |
| `streamlit` | Web interface |
| `python-dotenv` | Reading `.env` |

---

## 8. How to run it (step by step)

```bash
# 1. Install libraries (any one of these)
uv sync
pip install -r requirements.txt
pip install -e .

# 2. Add your keys
cp .env.example .env         # then edit .env

# 3. Build the knowledge base (optional: the app does this automatically on first start)
python setup_vector_store.py

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
| 6 | Gemini | Gemini reads everything and writes an answer, e.g. explaining that charges before the bundle was activated are billed at standard rates and that the customer can request a review/goodwill credit. |
| 7 | `app.py` | The answer appears word by word and is saved to the chat history. |

---

## 10. Common tasks

**Add a new FAQ**
1. Add a row to `data/faq.csv` (`id,question,answer,category`).
2. `python ingest_faq.py`
3. Restart the app (see note below).

**Add a new ticket**
1. Add a tuple to `TICKETS` in `data/seed_tickets.py`.
2. `python data/seed_tickets.py`
3. `python ingest_tickets.py`
4. Restart the app.

**Change the bot's tone or rules** → edit `SYSTEM_PROMPT` in `rag_chain.py`, then restart the app.

**Give the AI more or less context** → change `K_FAQ`, `K_TICKETS`, `K_GUIDES` in `config.py`, then restart the app.

**Change any other setting** (models, chunk size, paths) → edit `config.py`. See ["After changing a setting, what do I need to re-run?"](#after-changing-a-setting-what-do-i-need-to-re-run).

> ✅ **Re-running is safe:** each ingest script first empties its own collection and then loads the data fresh, so running a script twice never creates duplicates. You only need to re-run the script whose data changed.
>
> 🔁 **Restart the app afterwards:** the website keeps the database connection cached, so stop and restart `streamlit run app.py` to see the new data.
>
> 🧹 **Full reset:** to start completely from scratch, delete the `chroma_store/` folder and run all three ingest scripts.

---

## 11. Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| Bot says it doesn't have enough information for everything | `chroma_store/` is empty or missing | Normally fixed automatically on start-up. If it persists, run `python setup_vector_store.py` and restart the app |
| `GEMINI_API_KEY` / authentication error | `.env` missing or wrong key | Check `.env` exists and the key name is exactly `GEMINI_API_KEY` (capitals matter on Linux) |
| `503 UNAVAILABLE … high demand` from Gemini | That model is overloaded on Google's side | Temporary. Retry, or use a less busy model in `LLM_MODEL` (e.g. `gemini-3.5-flash`) |
| Very slow first start (or first question) | Embedding model downloading and/or the database being built for the first time | Wait (about a minute); both are kept for next time |
| `unsupported version of sqlite3` from ChromaDB | Old SQLite on a Linux server, and `pysqlite3-binary` isn't installed | Install from `requirements.txt` (it includes `pysqlite3-binary` on Linux) |
| Same snippet appears several times in answers | Database was built with an older version of the ingest scripts, which added copies on every run | Delete `chroma_store/` and run the three ingest scripts once (current scripts no longer duplicate) |
| Changes to data not reflected in the website | Chain is cached | Re-ingest, then stop and restart `streamlit run app.py` |
| `ModuleNotFoundError` | Libraries not installed / wrong environment | Run `uv sync` and activate `.venv` |
| `ModuleNotFoundError: No module named 'config'` | A script was copied or moved away from the project folder | Keep all the `.py` scripts together in the project folder; they all import `config.py` |

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
