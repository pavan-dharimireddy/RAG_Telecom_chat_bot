"""
Builds the RAG chain:
  merged retriever → prompt → Qwen3.8-27B on Groq → string output
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
from langchain_groq import ChatGroq

from config import LLM_MODEL, LLM_TEMPERATURE
from retriever import build_retriever

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


def _format_docs(docs: list[Document]) -> str:
    sections = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown").upper()
        sections.append(f"[{source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(sections)


def build_chain():
    retriever = build_retriever()

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ])

    llm = ChatGroq(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        max_tokens=None,
        reasoning_format="parsed",
        timeout=None,
        max_retries=2,
    )

    chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain
