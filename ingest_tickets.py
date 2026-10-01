"""
Ingests resolved tickets from data/tickets.db into the 'tickets' Chroma collection.
Safe to re-run: it replaces the collection each time.
Run after adding new tickets: python ingest_tickets.py
"""
import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
import sqlite3
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from config import CHROMA_DIR, EMBED_MODEL, TICKETS_COLLECTION, TICKETS_DB_PATH


def load_ticket_documents(db_path) -> list[Document]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM tickets WHERE status = 'resolved'"
    ).fetchall()
    conn.close()

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


def main():
    print("Loading ticket documents from SQLite...")
    docs = load_ticket_documents(TICKETS_DB_PATH)
    print(f"  {len(docs)} resolved tickets loaded.")

    print("Initialising embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    vectorstore = Chroma(
        collection_name=TICKETS_COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )

    # Empty the collection first so re-running replaces the data instead of duplicating it
    existing_ids = vectorstore.get()["ids"]
    if existing_ids:
        print(f"  Removing {len(existing_ids)} existing vectors...")
        vectorstore.delete(ids=existing_ids)

    print(f"Embedding and storing in Chroma collection '{TICKETS_COLLECTION}'...")
    vectorstore.add_documents(docs)
    print(f"  Done. {vectorstore._collection.count()} vectors stored.")


if __name__ == "__main__":
    main()
