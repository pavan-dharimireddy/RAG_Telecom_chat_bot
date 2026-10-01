# RAG Telecom Chatbot

> Based on the RAG tutorial by Dhaval Patel (codebasics). Extended with architecture docs and project notes.

A Retrieval-Augmented Generation (RAG) customer care chatbot for telecom support. It answers questions about mobile connectivity, billing, SIM issues, and roaming by retrieving relevant context from three knowledge sources and generating responses with Qwen3.8-27B via Groq.

## Architecture

```
User question
     │
     ▼
Merged Retriever (top-k from each store)
  ├── ChromaDB · faq        (FAQ entries from CSV)
  ├── ChromaDB · tickets    (resolved support tickets from SQLite)
  └── ChromaDB · guides     (PDF guide chunks)
     │
     ▼
ChatPromptTemplate → Qwen3.8-27B (Groq) → Answer
```

**Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (runs locally via HuggingFace)  
**LLM:** `qwen/qwen3.8-27b` served by [Groq](https://groq.com)

For detailed diagrams and design decisions see [architecture.md](architecture.md). For a beginner-friendly, line-by-line guide to every script see [notes.md](notes.md).

## Project Structure

```
rag-telecom-chatbot/
├── app.py              # Streamlit web UI
├── main.py             # CLI entry point
├── config.py           # All settings in one place (paths, models, chunking, k values)
├── rag_chain.py        # Builds the LangChain RAG chain
├── retriever.py        # Merges the three Chroma retrievers
├── ingest_faq.py       # Loads data/faq.csv → Chroma 'faq' collection
├── ingest_tickets.py   # Loads data/tickets.db → Chroma 'tickets' collection
├── ingest_pdf.py       # Cleans + chunks data/telecom_guide.pdf → Chroma 'guides' collection
├── setup_vector_store.py  # Builds any empty collection automatically on start-up
├── sqlite_compat.py    # Swaps in a newer SQLite on old Linux servers (no-op elsewhere)
├── data/
│   ├── faq.csv             # FAQ question/answer pairs
│   ├── tickets.db          # SQLite database of resolved support tickets
│   ├── telecom_guide.pdf   # Telecom user guide (chunked at ingest)
│   ├── seed_tickets.py     # Script to seed the tickets database
│   └── generate_pdf.py     # Script to generate the telecom guide PDF
├── chroma_store/       # Persisted Chroma vector database (built automatically, git-ignored)
├── architecture.md     # System architecture & design diagrams
├── notes.md            # Beginner-friendly guide to every script
├── pyproject.toml
├── uv.lock
├── requirements.txt    # pip / hosting-platform install list (exported from uv.lock)
├── LICENSE
└── .env.example
```

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A [Groq API key](https://console.groq.com)
- A [HuggingFace token](https://huggingface.co/settings/tokens) (optional: the embedding model is public; a token only raises download rate limits)

## Setup

**1. Clone and install dependencies**

```bash
git clone https://github.com/pavan-dharimireddy/RAG_Telecom_chat_bot.git
cd RAG_Telecom_chat_bot
uv sync                            # or: pip install -r requirements.txt
```

PyTorch is pinned to the **CPU-only** build (see `[tool.uv.sources]` in `pyproject.toml`), which avoids several GB of GPU libraries the app doesn't use.

**2. Configure environment variables**

```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:

```
GROQ_API_KEY=your_groq_api_key_here
HF_TOKEN=your_huggingface_token_here
```

**3. Build the vector store (optional)**

You can skip this step: on start-up, `app.py` and `main.py` call `ensure_vector_store()` from [setup_vector_store.py](setup_vector_store.py), which runs the ingest script for any collection that is missing or empty. On a fresh machine or server the first start therefore takes about a minute longer.

To build it up front instead:

```bash
python setup_vector_store.py     # fills any empty collection
# or run the scripts individually:
python ingest_faq.py
python ingest_tickets.py
python ingest_pdf.py
```

Each ingest script embeds the source data and persists it to `chroma_store/`. The automatic check only fills **empty** collections, so after changing source data, re-run the matching ingest script yourself. Re-run a script whenever its source data changes. Re-running is safe: each script empties its collection before loading, so it never creates duplicates. Restart the Streamlit app afterwards to pick up the new data.

## Running the App

**Streamlit web UI**

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. The sidebar has one-click sample questions and a button to clear the conversation history.

**CLI**

```bash
python main.py
```

Interactive prompt — type a question and press Enter. Type `quit` to exit.

## Configuration

All tunable settings live in [config.py](config.py): data file paths, the Chroma folder and collection names, the embedding model, PDF chunk size/overlap, results per collection (`K_FAQ`, `K_TICKETS`, `K_GUIDES`) and the LLM model/temperature. Paths are built from the project folder, so the scripts work from any working directory.

> The embedding model must be the same for ingestion and retrieval; keeping it in one place guarantees that. If you change `EMBED_MODEL`, re-run all three ingest scripts.

## Data Sources

| Collection | Source file | Granularity |
|---|---|---|
| `faq` | `data/faq.csv` | 1 document per FAQ row |
| `tickets` | `data/tickets.db` | 1 document per resolved ticket |
| `guides` | `data/telecom_guide.pdf` | Repeated page header/footer removed, then chunks of 600 chars with 100-char overlap |

The retriever fetches the top 3 results from each collection (9 context documents total) for every query.

## Regenerating Seed Data

```bash
# Seed the SQLite ticket database
python data/seed_tickets.py

# Regenerate the PDF guide
python data/generate_pdf.py
```

After regenerating, re-run the corresponding ingest script.

## Deployment notes

The app is set up to run on hosting platforms such as Hugging Face Spaces or Streamlit Community Cloud:

- **No database in git:** `chroma_store/` is built automatically on first start.
- **Install list:** platforms install from `requirements.txt`. Its first line (`--find-links https://download.pytorch.org/whl/cpu/torch/`) makes `pip`/`uv` fetch the CPU-only PyTorch build. `uv export` does not write that line, so re-add it after regenerating the file with:
  ```bash
  uv export --format requirements-txt --no-hashes --no-dev --no-emit-project -o requirements.txt
  ```
- **Old SQLite on Linux:** ChromaDB needs SQLite 3.35+. On Linux, `pysqlite3-binary` is installed and [sqlite_compat.py](sqlite_compat.py) switches to it only if the system SQLite is older.
- **Secrets:** set `GROQ_API_KEY` in the platform's secrets settings (never commit `.env`).

## License

Released under the [MIT License](LICENSE). The original tutorial code is by Dhaval Patel (codebasics).
