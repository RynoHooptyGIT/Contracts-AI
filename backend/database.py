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
            status TEXT DEFAULT 'processing',
            category TEXT DEFAULT 'Uncategorized'
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
            id TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            result_count INTEGER,
            used_rag BOOLEAN
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_entities (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_value TEXT NOT NULL,
            frequency INTEGER DEFAULT 1,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)

    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON documents(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_timestamp ON query_history(timestamp DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON document_entities(entity_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_value ON document_entities(entity_value)")

    conn.commit()
    conn.close()

def migrate_database():
    """Migrate existing database to add new columns and tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Check if category column exists in documents table
    cursor.execute("PRAGMA table_info(documents)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'category' not in columns:
        cursor.execute("ALTER TABLE documents ADD COLUMN category TEXT DEFAULT 'Uncategorized'")
        print("Added category column to documents table")

    # Create new tables if they don't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
            id TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            result_count INTEGER,
            used_rag BOOLEAN
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_entities (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_value TEXT NOT NULL,
            frequency INTEGER DEFAULT 1,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON documents(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_timestamp ON query_history(timestamp DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON document_entities(entity_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_value ON document_entities(entity_value)")

    conn.commit()
    conn.close()
    print("Database migration completed successfully")

def migrate_redlining_tables():
    """Migrate database to add contract redlining system tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # 1. Create golden_templates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS golden_templates (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            category TEXT NOT NULL,
            version TEXT,
            parent_template_id TEXT,
            is_approved BOOLEAN DEFAULT 0,
            approved_by TEXT,
            approved_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id),
            FOREIGN KEY (parent_template_id) REFERENCES golden_templates(id)
        )
    """)

    # 2. Create document_clauses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_clauses (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            clause_type TEXT NOT NULL,
            clause_title TEXT,
            clause_text TEXT NOT NULL,
            clause_index INTEGER NOT NULL,
            start_char INTEGER,
            end_char INTEGER,
            extracted_terms TEXT,
            chunk_ids TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)

    # 3. Create redlining_sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS redlining_sessions (
            id TEXT PRIMARY KEY,
            uploaded_document_id TEXT NOT NULL,
            template_id TEXT NOT NULL,
            template_match_score REAL,
            category TEXT,
            status TEXT DEFAULT 'pending',
            overall_risk_score REAL,
            deviation_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (uploaded_document_id) REFERENCES documents(id),
            FOREIGN KEY (template_id) REFERENCES golden_templates(id)
        )
    """)

    # 4. Create clause_comparisons table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clause_comparisons (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            new_clause_id TEXT,
            template_clause_id TEXT,
            comparison_type TEXT NOT NULL,
            similarity_score REAL,
            risk_level TEXT,
            deviation_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES redlining_sessions(id),
            FOREIGN KEY (new_clause_id) REFERENCES document_clauses(id),
            FOREIGN KEY (template_clause_id) REFERENCES document_clauses(id)
        )
    """)

    # 5. Create ai_suggestions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_suggestions (
            id TEXT PRIMARY KEY,
            comparison_id TEXT NOT NULL,
            suggestion_type TEXT NOT NULL,
            suggested_text TEXT,
            rationale TEXT,
            confidence_score REAL,
            example_sources TEXT,
            user_action TEXT,
            edited_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (comparison_id) REFERENCES clause_comparisons(id)
        )
    """)

    # Create indexes for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_templates_category
        ON golden_templates(category, is_active)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_clauses_document
        ON document_clauses(document_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_status
        ON redlining_sessions(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_comparisons_session
        ON clause_comparisons(session_id)
    """)

    conn.commit()
    conn.close()
    print("Contract redlining tables migration completed successfully")

def migrate_visual_annotation_tables():
    """Migrate database to add visual annotation system tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # 1. Create annotation_changes table (individual text-level changes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS annotation_changes (
            id TEXT PRIMARY KEY,
            comparison_id TEXT NOT NULL,
            change_type TEXT NOT NULL,
            original_text TEXT,
            suggested_text TEXT,
            start_offset INTEGER,
            end_offset INTEGER,
            risk_level TEXT,
            rationale TEXT,
            user_action TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (comparison_id) REFERENCES clause_comparisons(id)
        )
    """)

    # 2. Create rendered_documents table (HTML rendering cache)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rendered_documents (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL UNIQUE,
            html_content TEXT NOT NULL,
            css_content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)

    # Create indexes for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_changes_comparison
        ON annotation_changes(comparison_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_changes_action
        ON annotation_changes(user_action)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_rendered_document
        ON rendered_documents(document_id)
    """)

    conn.commit()
    conn.close()
    print("Visual annotation tables migration completed successfully")
