"""
Ingests data/faq.csv into the 'faq' Chroma collection.
Safe to re-run: it replaces the collection each time.
Run whenever the CSV changes: python ingest_faq.py
"""
import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
import pandas as pd
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from config import CHROMA_DIR, EMBED_MODEL, FAQ_COLLECTION, FAQ_CSV_PATH


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


def main():
    print("Loading FAQ documents...")
    docs = load_faq_documents(FAQ_CSV_PATH)
    print(f"  {len(docs)} FAQ entries loaded.")

    print("Initialising embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    vectorstore = Chroma(
        collection_name=FAQ_COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )

    # Empty the collection first so re-running replaces the data instead of duplicating it
    existing_ids = vectorstore.get()["ids"]
    if existing_ids:
        print(f"  Removing {len(existing_ids)} existing vectors...")
        vectorstore.delete(ids=existing_ids)

    print(f"Embedding and storing in Chroma collection '{FAQ_COLLECTION}'...")
    vectorstore.add_documents(docs)
    print(f"  Done. {vectorstore._collection.count()} vectors stored.")


if __name__ == "__main__":
    main()
