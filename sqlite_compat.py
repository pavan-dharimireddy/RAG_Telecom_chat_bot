"""
ChromaDB needs SQLite 3.35 or newer. Some Linux servers ship an older system SQLite,
which makes ChromaDB refuse to start. In that case only, swap in the newer SQLite
bundled with the pysqlite3-binary package. Elsewhere this module does nothing.

Import it before anything that imports chromadb (langchain_chroma, chromadb).
"""
import sqlite3
import sys

MIN_SQLITE_VERSION = (3, 35, 0)

if sqlite3.sqlite_version_info < MIN_SQLITE_VERSION:
    import pysqlite3

    sys.modules["sqlite3"] = pysqlite3
