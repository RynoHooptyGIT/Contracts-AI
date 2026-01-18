import sqlite3
from pathlib import Path
import os

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "/app/data/documents.db"))

def get_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_PATH)

def init_database():
    """Initialize SQLite database with schema"""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'processing'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            text TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            embedding_id INTEGER NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)

    conn.commit()
    conn.close()
