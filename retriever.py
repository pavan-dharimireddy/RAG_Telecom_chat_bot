"""
Builds a merged retriever across all three Chroma collections:
  - faq     : FAQ entries (no chunking — 1 row = 1 doc)
  - tickets : resolved support tickets (no chunking — 1 ticket = 1 doc)
  - guides  : PDF guide chunks (RecursiveCharacterTextSplitter applied at ingest)
"""
import sqlite_compat  # noqa: F401  (must come before chromadb is imported)
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnableLambda
from langchain_core.documents import Document

from config import (
    CHROMA_DIR, EMBED_MODEL,
    FAQ_COLLECTION, TICKETS_COLLECTION, GUIDES_COLLECTION,
    K_FAQ, K_TICKETS, K_GUIDES,
)


def build_retriever(
    k_faq: int = K_FAQ,
    k_tickets: int = K_TICKETS,
    k_guides: int = K_GUIDES,
) -> RunnableLambda:
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    faq_store = Chroma(
        collection_name=FAQ_COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )
    tickets_store = Chroma(
        collection_name=TICKETS_COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )
    guides_store = Chroma(
        collection_name=GUIDES_COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )

    faq_retriever     = faq_store.as_retriever(search_kwargs={"k": k_faq})
    tickets_retriever = tickets_store.as_retriever(search_kwargs={"k": k_tickets})
    guides_retriever  = guides_store.as_retriever(search_kwargs={"k": k_guides})

    def retrieve(query: str) -> list[Document]:
        return (
            faq_retriever.invoke(query)
            + tickets_retriever.invoke(query)
            + guides_retriever.invoke(query)
        )

    return RunnableLambda(retrieve)
