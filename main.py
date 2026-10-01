"""
CLI entry point for the telecom RAG chatbot.
Usage: python main.py
"""
import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import sqlite_compat  # noqa: F401  (must come before chromadb is imported)
from dotenv import load_dotenv
from rag_chain import build_chain
from setup_vector_store import ensure_vector_store

load_dotenv()


def main():
    print("=== Telecom Customer Care Chatbot (RAG) ===")
    print("Type your question and press Enter. Type 'quit' to exit.\n")

    ensure_vector_store()
    chain = build_chain()

    while True:
        question = input("Customer: ").strip()
        if not question:
            continue
        if question.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break

        print("\nAssistant: ", end="", flush=True)
        for chunk in chain.stream(question):
            print(chunk, end="", flush=True)
        print("\n")


if __name__ == "__main__":
    main()
