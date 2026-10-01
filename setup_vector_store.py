"""
Makes sure the vector store is ready before the chatbot answers questions.
chroma_store/ is not in git, so on a fresh server it starts empty: any collection
that is missing or empty is built by running its ingest script once.

Called automatically by app.py and main.py. Can also be run directly to fill
any empty collections: python setup_vector_store.py
"""
import sqlite_compat  # noqa: F401  (must come before chromadb is imported)
import chromadb

import ingest_faq
import ingest_tickets
import ingest_pdf
from config import CHROMA_DIR, FAQ_COLLECTION, TICKETS_COLLECTION, GUIDES_COLLECTION

INGESTERS = {
    FAQ_COLLECTION: ingest_faq.main,
    TICKETS_COLLECTION: ingest_tickets.main,
    GUIDES_COLLECTION: ingest_pdf.main,
}


def ensure_vector_store() -> None:
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    sizes = {collection.name: collection.count() for collection in client.list_collections()}

    for name, ingest in INGESTERS.items():
        if sizes.get(name, 0) == 0:
            print(f"Collection '{name}' is empty, building it now...")
            ingest()


if __name__ == "__main__":
    ensure_vector_store()
    print("Vector store is ready.")
