import zipfile
import uuid
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
import os
from datetime import datetime, timedelta
from .document_parser import parse_file, chunk_text
from .embedding_service import EmbeddingService
from .vector_store import FAISSVectorStore
from .categorizer import categorize_document as categorize_doc, extract_entities_from_chunks as extract_entities

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

    def get_metrics(self) -> Dict:
        """Get database and system metrics"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Total documents
            cursor.execute("SELECT COUNT(*) FROM documents")
            total_documents = cursor.fetchone()[0]

            # Total chunks
            cursor.execute("SELECT COUNT(*) FROM chunks")
            total_chunks = cursor.fetchone()[0]

            # Total storage
            cursor.execute("SELECT SUM(file_size) FROM documents")
            storage_result = cursor.fetchone()[0]
            storage_used = storage_result if storage_result is not None else 0

            # File types breakdown
            cursor.execute("""
                SELECT file_type, COUNT(*)
                FROM documents
                GROUP BY file_type
                ORDER BY COUNT(*) DESC
            """)
            file_types_raw = cursor.fetchall()
            file_types = {ft[0]: ft[1] for ft in file_types_raw}

            # Vector dimensions (constant for all-MiniLM-L6-v2)
            vector_dimensions = 384

            return {
                "totalDocuments": total_documents,
                "totalChunks": total_chunks,
                "storageUsed": storage_used,
                "fileTypes": file_types,
                "vectorDimensions": vector_dimensions
            }
        finally:
            conn.close()

    def categorize_document(self, doc_id: str) -> str:
        """
        Categorize a single document using hybrid approach.

        Args:
            doc_id: Document ID to categorize

        Returns:
            Category name
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Get document filename
            cursor.execute("SELECT filename FROM documents WHERE id = ?", (doc_id,))
            result = cursor.fetchone()
            if not result:
                return "Uncategorized"

            filename = result[0]

            # Get first 3 chunks for content analysis
            cursor.execute("""
                SELECT text FROM chunks
                WHERE document_id = ?
                ORDER BY chunk_index
                LIMIT 3
            """, (doc_id,))

            chunks = [row[0] for row in cursor.fetchall()]

            # Use categorizer service
            category = categorize_doc(filename, chunks if chunks else None)

            # Update document category in database
            cursor.execute("UPDATE documents SET category = ? WHERE id = ?", (category, doc_id))
            conn.commit()

            return category
        finally:
            conn.close()

    def categorize_all_documents(self) -> Dict:
        """
        Batch categorization for all documents.

        Returns:
            Statistics about categorization process
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Get all documents that need categorization
            cursor.execute("SELECT id FROM documents")
            doc_ids = [row[0] for row in cursor.fetchall()]

            categorized = 0
            failed = 0
            categories_count = {}

            for doc_id in doc_ids:
                try:
                    category = self.categorize_document(doc_id)
                    categorized += 1
                    categories_count[category] = categories_count.get(category, 0) + 1
                except Exception as e:
                    print(f"Failed to categorize document {doc_id}: {str(e)}")
                    failed += 1

            return {
                "categorized": categorized,
                "failed": failed,
                "categories": categories_count
            }
        finally:
            conn.close()

    def get_insights(self) -> Dict:
        """
        Aggregate all data for Document Insights Panel.

        Returns comprehensive insights including stats, categories, activity, entities
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Quick Stats
            cursor.execute("SELECT COUNT(*) FROM documents")
            total_documents = cursor.fetchone()[0]

            cursor.execute("SELECT uploaded_at FROM documents ORDER BY uploaded_at DESC LIMIT 1")
            last_upload_result = cursor.fetchone()
            last_upload = last_upload_result[0] if last_upload_result else None

            cursor.execute("SELECT SUM(file_size) FROM documents")
            storage_result = cursor.fetchone()[0]
            storage_used = storage_result if storage_result is not None else 0

            # File Types
            cursor.execute("""
                SELECT file_type, COUNT(*)
                FROM documents
                GROUP BY file_type
                ORDER BY COUNT(*) DESC
            """)
            file_types = {ft[0]: ft[1] for ft in cursor.fetchall()}

            # Categories
            cursor.execute("""
                SELECT category, COUNT(*)
                FROM documents
                GROUP BY category
                ORDER BY COUNT(*) DESC
            """)
            categories = {cat[0]: cat[1] for cat in cursor.fetchall()}

            # Recent Activity (last 7 days)
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("""
                SELECT COUNT(*)
                FROM documents
                WHERE uploaded_at >= ?
            """, (seven_days_ago,))
            recent_uploads = cursor.fetchone()[0]

            # Most active day in last 7 days
            cursor.execute("""
                SELECT DATE(uploaded_at) as upload_date, COUNT(*) as count
                FROM documents
                WHERE uploaded_at >= ?
                GROUP BY upload_date
                ORDER BY count DESC
                LIMIT 1
            """, (seven_days_ago,))
            most_active_result = cursor.fetchone()
            most_active_day = {
                "date": most_active_result[0] if most_active_result else None,
                "count": most_active_result[1] if most_active_result else 0
            }

            # Common Entities (top 10)
            cursor.execute("""
                SELECT entity_type, entity_value, SUM(frequency) as total_freq
                FROM document_entities
                WHERE entity_type = 'company'
                GROUP BY entity_type, entity_value
                ORDER BY total_freq DESC
                LIMIT 10
            """)
            common_entities = [
                {"type": row[0], "value": row[1], "frequency": row[2]}
                for row in cursor.fetchall()
            ]

            # Suggested Questions (based on categories)
            suggested_questions = self._generate_suggested_questions(categories)

            return {
                "quickStats": {
                    "totalDocuments": total_documents,
                    "lastUpload": last_upload,
                    "storageUsed": storage_used,
                    "recentUploads": recent_uploads
                },
                "fileTypes": file_types,
                "categories": categories,
                "recentActivity": {
                    "last7Days": recent_uploads,
                    "mostActiveDay": most_active_day
                },
                "commonEntities": common_entities,
                "suggestedQuestions": suggested_questions
            }
        finally:
            conn.close()

    def _generate_suggested_questions(self, categories: Dict[str, int]) -> List[str]:
        """Generate context-aware suggested questions based on document categories"""
        questions = []

        # Category-specific questions
        if categories.get("NDAs", 0) > 0:
            questions.append("What are the key terms in our NDAs?")
            questions.append("Find NDAs with specific confidentiality periods")

        if categories.get("Employment Agreements", 0) > 0:
            questions.append("Compare compensation structures across employment contracts")
            questions.append("What are common non-compete clauses?")

        if categories.get("Vendor Contracts", 0) > 0:
            questions.append("Compare vendor payment terms")
            questions.append("What are typical vendor liability caps?")

        if categories.get("Master Service Agreements", 0) > 0:
            questions.append("What MSAs require statements of work?")

        # General questions (always available)
        questions.append("Find contracts expiring in the next 90 days")
        questions.append("Search for termination clauses")

        return questions[:6]  # Limit to 6 questions

    def extract_and_cache_entities(self, doc_id: str) -> List[Dict]:
        """
        Extract entities from document chunks and cache in database.

        Args:
            doc_id: Document ID

        Returns:
            List of extracted entities
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Check if entities already cached
            cursor.execute("SELECT COUNT(*) FROM document_entities WHERE document_id = ?", (doc_id,))
            if cursor.fetchone()[0] > 0:
                # Return cached entities
                cursor.execute("""
                    SELECT entity_type, entity_value, frequency
                    FROM document_entities
                    WHERE document_id = ?
                """, (doc_id,))
                return [
                    {"type": row[0], "value": row[1], "frequency": row[2]}
                    for row in cursor.fetchall()
                ]

            # Get chunks for entity extraction
            cursor.execute("""
                SELECT text FROM chunks
                WHERE document_id = ?
                ORDER BY chunk_index
                LIMIT 5
            """, (doc_id,))
            chunks = [row[0] for row in cursor.fetchall()]

            if not chunks:
                return []

            # Extract entities
            entities = extract_entities(chunks)

            # Cache in database
            for entity in entities:
                entity_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO document_entities (id, document_id, entity_type, entity_value, frequency)
                    VALUES (?, ?, ?, ?, ?)
                """, (entity_id, doc_id, entity["type"], entity["value"], entity["frequency"]))

            conn.commit()
            return entities
        finally:
            conn.close()

    def check_compliance(self, new_contract_text: str) -> Dict:
        """
        Check compliance of new contract against existing contracts.

        Uses RAG to find similar contracts and compare clause presence.

        Args:
            new_contract_text: Text of contract to check

        Returns:
            Compliance report with score, similar contracts, missing clauses, unusual terms
        """
        # Find top 5 similar contracts using RAG
        similar_results = self.search_documents(new_contract_text, top_k=5)

        # Standard clause keywords to check for
        standard_clauses = {
            "Termination": ["termination", "terminate", "cancellation"],
            "Payment Terms": ["payment", "invoice", "net-30", "net-60", "compensation"],
            "Liability": ["liability", "indemnification", "liability cap"],
            "Confidentiality": ["confidential", "non-disclosure", "proprietary"],
            "Dispute Resolution": ["dispute", "arbitration", "mediation", "jurisdiction"],
            "Force Majeure": ["force majeure", "act of god", "unforeseeable"]
        }

        # Check which clauses are present in new contract
        new_contract_lower = new_contract_text.lower()
        present_clauses = []
        missing_clauses = []

        for clause_name, keywords in standard_clauses.items():
            found = any(keyword in new_contract_lower for keyword in keywords)
            if found:
                present_clauses.append(clause_name)
            else:
                missing_clauses.append(clause_name)

        # Calculate compliance score (based on standard clauses present)
        compliance_score = len(present_clauses) / len(standard_clauses)

        # Extract unusual terms (basic implementation - checks for uncommon payment periods)
        unusual_terms = []
        if "net-90" in new_contract_lower or "net 90" in new_contract_lower:
            unusual_terms.append("Payment term net-90 (standard is typically net-30)")

        # Recommendations
        recommendations = []
        if missing_clauses:
            recommendations.append(f"Consider adding: {', '.join(missing_clauses)}")
        if compliance_score < 0.7:
            recommendations.append("Contract is missing several standard clauses")
        if not unusual_terms:
            recommendations.append("Contract terms appear standard")

        return {
            "compliance_score": round(compliance_score, 2),
            "similar_contracts": [
                {"filename": r["filename"], "similarity": r["similarity"]}
                for r in similar_results
            ],
            "present_clauses": present_clauses,
            "missing_clauses": missing_clauses,
            "unusual_terms": unusual_terms,
            "recommendations": recommendations
        }

    def get_search_history(self, limit: int = 10) -> List[Dict]:
        """
        Retrieve popular/recent searches for suggested questions.

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of queries with counts
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT query, COUNT(*) as count
                FROM query_history
                GROUP BY query
                ORDER BY count DESC
                LIMIT ?
            """, (limit,))

            return [
                {"query": row[0], "count": row[1]}
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    def log_query(self, query: str, result_count: int, used_rag: bool):
        """
        Log a query to query_history for analytics.

        Args:
            query: The search query
            result_count: Number of results returned
            used_rag: Whether RAG was used
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO query_history (id, query, result_count, used_rag)
                VALUES (?, ?, ?, ?)
            """, (query_id, query, result_count, used_rag))
            conn.commit()
        finally:
            conn.close()
