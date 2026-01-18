import zipfile
import uuid
import sqlite3
from pathlib import Path
from typing import Dict, List
import os
from .document_parser import parse_file, chunk_text
from .embedding_service import EmbeddingService
from .vector_store import FAISSVectorStore

class DocumentManager:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = FAISSVectorStore()

        # Use environment variable for upload directory
        upload_dir = os.getenv("UPLOAD_DIR", "/app/data/documents")
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # Database path from environment
        db_path = os.getenv("DATABASE_PATH", "/app/data/documents.db")
        self.db_path = db_path

    def _get_connection(self):
        """Get SQLite database connection"""
        return sqlite3.connect(self.db_path)

    def ingest_zip(self, zip_path: str) -> Dict:
        """Process ZIP file: extract, parse, embed, store"""
        results = {"processed": 0, "failed": 0, "documents": [], "errors": []}

        # Extract ZIP to temporary directory
        extract_dir = self.upload_dir / f"extract_{uuid.uuid4().hex}"
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except Exception as e:
            results["errors"].append(f"Failed to extract ZIP: {str(e)}")
            return results

        # Process each file in extracted directory
        supported_extensions = ['.txt', '.md', '.pdf', '.docx']

        for file_path in extract_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    doc_id = self.process_file(str(file_path))
                    results["processed"] += 1
                    results["documents"].append({
                        "id": doc_id,
                        "filename": file_path.name,
                        "file_type": file_path.suffix
                    })
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"{file_path.name}: {str(e)}")

        # Save vector index to disk
        self.vector_store.save()

        return results

    def process_file(self, filepath: str) -> str:
        """Process single file: parse, chunk, embed, store"""
        path = Path(filepath)

        # Parse text from file
        text = parse_file(filepath)

        # Chunk text
        chunks = chunk_text(text)

        # Generate embeddings
        embeddings = self.embedding_service.generate_embeddings(chunks)

        # Store vectors in FAISS
        embedding_ids = self.vector_store.add_vectors(embeddings)

        # Store metadata in SQLite
        doc_id = str(uuid.uuid4())
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Insert document record
            cursor.execute("""
                INSERT INTO documents (id, filename, filepath, file_type, file_size, status)
                VALUES (?, ?, ?, ?, ?, 'indexed')
            """, (doc_id, path.name, filepath, path.suffix, path.stat().st_size))

            # Insert chunk records
            for idx, (chunk, emb_id) in enumerate(zip(chunks, embedding_ids)):
                chunk_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO chunks (id, document_id, text, chunk_index, embedding_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (chunk_id, doc_id, chunk, idx, emb_id))

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

        return doc_id

    def search_documents(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for relevant document chunks using vector similarity"""
        # Generate query embedding
        query_embedding = self.embedding_service.generate_query_embedding(query)

        # Search FAISS index
        results = self.vector_store.search(query_embedding, top_k)

        # Retrieve chunk text from SQLite
        conn = self._get_connection()
        cursor = conn.cursor()

        retrieved_chunks = []
        for embedding_id, distance in results:
            cursor.execute("""
                SELECT c.text, c.chunk_index, d.filename
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE c.embedding_id = ?
            """, (embedding_id,))

            row = cursor.fetchone()
            if row:
                # Convert L2 distance to similarity score
                similarity = float(1 / (1 + distance))
                retrieved_chunks.append({
                    "text": row[0],
                    "chunk_index": row[1],
                    "filename": row[2],
                    "similarity": similarity
                })

        conn.close()
        return retrieved_chunks

    def list_documents(self) -> List[Dict]:
        """Get all uploaded documents"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, filename, file_type, file_size, uploaded_at, status
            FROM documents
            ORDER BY uploaded_at DESC
        """)

        docs = cursor.fetchall()
        conn.close()

        return [
            {
                "id": doc[0],
                "filename": doc[1],
                "file_type": doc[2],
                "file_size": doc[3],
                "uploaded_at": doc[4],
                "status": doc[5]
            }
            for doc in docs
        ]

    def delete_document(self, doc_id: str) -> bool:
        """Delete document and associated chunks"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Delete chunks first (foreign key constraint)
            cursor.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))

            # Delete document
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

            conn.commit()

            # Note: We don't remove from FAISS index as it would require rebuilding
            # This is acceptable as orphaned vectors just won't be returned in searches

            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
