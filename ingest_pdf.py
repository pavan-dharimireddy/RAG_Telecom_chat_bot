"""
Ingests data/telecom_guide.pdf into the 'guides' Chroma collection.
Removes the repeated page header/footer, then applies RecursiveCharacterTextSplitter
to break the long document into chunks.
Safe to re-run: it replaces the collection each time.
Run after regenerating the PDF: python ingest_pdf.py
"""
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

# Text printed on every page by data/generate_pdf.py; it carries no meaning, so it is removed
HEADER_PATTERN = re.compile(r"^Telecom Technical Reference Guide\s+-\s+Internal Use Only$")
FOOTER_PATTERN = re.compile(r"^Page \d+$")


def clean_page_text(text: str) -> str:
    lines = [
        line for line in text.splitlines()
        if not HEADER_PATTERN.match(line.strip()) and not FOOTER_PATTERN.match(line.strip())
    ]
    return "\n".join(lines).strip()


def main():
    print("Loading PDF...")
    loader = PyPDFLoader(str(GUIDE_PDF_PATH))
    pages = loader.load()
    print(f"  {len(pages)} pages loaded.")

    print("Removing page headers and footers...")
    for page in pages:
        page.page_content = clean_page_text(page.page_content)

    print(f"Chunking (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " "],
    )
    chunks = splitter.split_documents(pages)

    # Tag each chunk so we know it came from the guide
    for i, chunk in enumerate(chunks):
        chunk.metadata["source"] = "guide"
        chunk.metadata["chunk_index"] = i

    print(f"  {len(chunks)} chunks produced.")

    print("Initialising embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    vectorstore = Chroma(
        collection_name=GUIDES_COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )

    # Empty the collection first so re-running replaces the data instead of duplicating it
    existing_ids = vectorstore.get()["ids"]
    if existing_ids:
        print(f"  Removing {len(existing_ids)} existing vectors...")
        vectorstore.delete(ids=existing_ids)

    print(f"Embedding and storing in Chroma collection '{GUIDES_COLLECTION}'...")
    vectorstore.add_documents(chunks)
    print(f"  Done. {vectorstore._collection.count()} vectors stored.")


if __name__ == "__main__":
    main()
