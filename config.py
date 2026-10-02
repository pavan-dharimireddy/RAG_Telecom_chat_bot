"""
Central settings for the whole project.
Every script imports from here, so a value only ever needs changing in one place.
"""
from pathlib import Path

# Project folder (where this file lives). All paths are built from it,
# so the scripts work no matter which folder they are run from.
BASE_DIR = Path(__file__).resolve().parent

# ── Data sources ─────────────────────────────────────────────────────────────
DATA_DIR        = BASE_DIR / "data"
FAQ_CSV_PATH    = DATA_DIR / "faq.csv"
TICKETS_DB_PATH = DATA_DIR / "tickets.db"
GUIDE_PDF_PATH  = DATA_DIR / "telecom_guide.pdf"

# ── Vector store ─────────────────────────────────────────────────────────────
CHROMA_DIR         = str(BASE_DIR / "chroma_store")
FAQ_COLLECTION     = "faq"
TICKETS_COLLECTION = "tickets"
GUIDES_COLLECTION  = "guides"

# ── Embedding model (must be the same for ingestion and retrieval) ───────────
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ── PDF chunking ─────────────────────────────────────────────────────────────
CHUNK_SIZE    = 600
CHUNK_OVERLAP = 100

# ── Retrieval: results fetched from each collection per question ─────────────
K_FAQ     = 3
K_TICKETS = 3
K_GUIDES  = 3

# ── LLM ──────────────────────────────────────────────────────────────────────
# Previous provider: Qwen on Groq (Groq returns "403 Access denied" from Streamlit Community Cloud)
# LLM_MODEL       = "qwen/qwen3.8-27b"
LLM_MODEL       = "gemini-3.5-flash"
LLM_TEMPERATURE = 0
