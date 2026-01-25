"""
Template matching service using RAG (FAISS vector similarity)
Finds the best matching golden template for an uploaded contract
"""
import sqlite3
from typing import Dict, List, Optional
import os
from logger import log_info, log_warning, log_error, log_success
from .embedding_service import EmbeddingService
from .vector_store import FAISSVectorStore


class TemplateMatcher:
    """Service for matching contracts to golden templates using semantic similarity"""

    def __init__(self):
        # Database path from environment
        db_path = os.getenv("DATABASE_PATH", "/app/data/documents.db")
        self.db_path = db_path

        # Initialize embedding and vector store services
        self.embedding_service = EmbeddingService()
        self.vector_store = FAISSVectorStore()

        # Matching configuration
        self.min_similarity_threshold = 0.3  # Minimum similarity to consider a match
        self.top_k_chunks = 10  # Number of chunks to compare per template

    def _get_connection(self):
        """Get SQLite database connection"""
        return sqlite3.connect(self.db_path)

    def find_best_template(self, document_id: str, category: Optional[str] = None) -> Optional[Dict]:
        """
        Find the best matching golden template for a document

        Args:
            document_id: The document ID to match
            category: Optional category to filter templates (e.g., "NDA", "Employment")

        Returns:
            Dictionary with best matching template and similarity score, or None if no good match
        """
        log_info(f"Finding best template for document: {document_id}", "TEMPLATE_MATCHER")

        # Get document text for comparison
        document_text = self._get_document_text(document_id)
        if not document_text:
            log_error(f"Could not retrieve text for document: {document_id}", "TEMPLATE_MATCHER")
            return None

        # Get all active approved templates (optionally filtered by category)
        templates = self._get_active_templates(category)
        if not templates:
            log_warning(f"No active templates found for category: {category}", "TEMPLATE_MATCHER")
            return None

        log_info(f"Comparing against {len(templates)} templates", "TEMPLATE_MATCHER")

        # Calculate similarity for each template
        template_scores = []
        for template in templates:
            try:
                similarity_score = self._calculate_similarity(document_text, template['document_id'])
                template_scores.append({
                    "template": template,
                    "similarity_score": similarity_score
                })
                log_info(f"Template {template['id'][:8]} ({template['category']}): {similarity_score:.3f}", "TEMPLATE_MATCHER")
            except Exception as e:
                log_error(f"Failed to calculate similarity for template {template['id']}: {str(e)}", "TEMPLATE_MATCHER")
                continue

        if not template_scores:
            log_warning("No template scores calculated", "TEMPLATE_MATCHER")
            return None

        # Sort by similarity score (highest first)
        template_scores.sort(key=lambda x: x['similarity_score'], reverse=True)

        # Get best match
        best_match = template_scores[0]

        # Check if best match meets minimum threshold
        if best_match['similarity_score'] < self.min_similarity_threshold:
            log_warning(f"Best match score {best_match['similarity_score']:.3f} below threshold {self.min_similarity_threshold}", "TEMPLATE_MATCHER")
            return None

        log_success(f"Found best template: {best_match['template']['id'][:8]} with score {best_match['similarity_score']:.3f}", "TEMPLATE_MATCHER")

        return {
            "template_id": best_match['template']['id'],
            "template": best_match['template'],
            "similarity_score": best_match['similarity_score'],
            "alternatives": [
                {
                    "template_id": match['template']['id'],
                    "category": match['template']['category'],
                    "similarity_score": match['similarity_score']
                }
                for match in template_scores[1:4]  # Include top 3 alternatives
                if match['similarity_score'] >= self.min_similarity_threshold
            ]
        }

    def find_top_templates(self, document_id: str, category: Optional[str] = None, top_n: int = 3) -> List[Dict]:
        """
        Find the top N matching golden templates for a document

        Args:
            document_id: The document ID to match
            category: Optional category to filter templates (e.g., "NDA", "Employment")
            top_n: Number of top templates to return (default: 3)

        Returns:
            List of top N templates with similarity scores, or empty list if no matches
        """
        log_info(f"Finding top {top_n} templates for document: {document_id}", "TEMPLATE_MATCHER")

        # Get document text for comparison
        document_text = self._get_document_text(document_id)
        if not document_text:
            log_error(f"Could not retrieve text for document: {document_id}", "TEMPLATE_MATCHER")
            return []

        # Get all active approved templates (optionally filtered by category)
        templates = self._get_active_templates(category)
        if not templates:
            log_warning(f"No active templates found for category: {category}", "TEMPLATE_MATCHER")
            return []

        log_info(f"Comparing against {len(templates)} templates", "TEMPLATE_MATCHER")

        # Calculate similarity for each template
        template_scores = []
        for template in templates:
            try:
                similarity_score = self._calculate_similarity(document_text, template['document_id'])
                template_scores.append({
                    "id": template['id'],
                    "document_id": template['document_id'],
                    "category": template['category'],
                    "similarity_score": similarity_score,
                    "notes": template.get('notes', ''),
                    "approved_by": template.get('approved_by', ''),
                    "approved_at": template.get('approved_at', '')
                })
                log_info(f"Template {template['id'][:8]} ({template['category']}): {similarity_score:.3f}", "TEMPLATE_MATCHER")
            except Exception as e:
                log_error(f"Failed to calculate similarity for template {template['id']}: {str(e)}", "TEMPLATE_MATCHER")
                continue

        if not template_scores:
            log_warning("No template scores calculated", "TEMPLATE_MATCHER")
            return []

        # Sort by similarity score (highest first)
        template_scores.sort(key=lambda x: x['similarity_score'], reverse=True)

        # Filter to templates above threshold and limit to top_n
        top_templates = [
            template for template in template_scores
            if template['similarity_score'] >= self.min_similarity_threshold
        ][:top_n]

        if top_templates:
            log_success(f"Found {len(top_templates)} templates above threshold {self.min_similarity_threshold}", "TEMPLATE_MATCHER")
            for i, template in enumerate(top_templates, 1):
                log_info(f"  #{i}: {template['id'][:8]} ({template['category']}) - {template['similarity_score']:.3f}", "TEMPLATE_MATCHER")
        else:
            log_warning(f"No templates above threshold {self.min_similarity_threshold}", "TEMPLATE_MATCHER")

        return top_templates

    def _get_active_templates(self, category: Optional[str] = None) -> List[Dict]:
        """
        Get all active approved golden templates

        Args:
            category: Optional category filter

        Returns:
            List of template dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if category:
                cursor.execute("""
                    SELECT id, document_id, category, notes, approved_by, approved_at
                    FROM golden_templates
                    WHERE is_active = 1 AND is_approved = 1 AND category = ?
                    ORDER BY created_at DESC
                """, (category,))
            else:
                cursor.execute("""
                    SELECT id, document_id, category, notes, approved_by, approved_at
                    FROM golden_templates
                    WHERE is_active = 1 AND is_approved = 1
                    ORDER BY category, created_at DESC
                """)

            rows = cursor.fetchall()
            templates = []

            for row in rows:
                templates.append({
                    "id": row[0],
                    "document_id": row[1],
                    "category": row[2],
                    "notes": row[3],
                    "approved_by": row[4],
                    "approved_at": row[5]
                })

            return templates

        except Exception as e:
            log_error(f"Failed to retrieve templates: {str(e)}", "TEMPLATE_MATCHER")
            return []
        finally:
            conn.close()

    def _get_document_text(self, document_id: str) -> Optional[str]:
        """
        Retrieve document text by concatenating chunks

        Args:
            document_id: The document ID

        Returns:
            Full document text or None
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT text FROM chunks
                WHERE document_id = ?
                ORDER BY chunk_index ASC
            """, (document_id,))

            chunks = cursor.fetchall()
            if not chunks:
                return None

            # Concatenate chunks with spacing
            return "\n\n".join([chunk[0] for chunk in chunks])

        except Exception as e:
            log_error(f"Failed to retrieve document text: {str(e)}", "TEMPLATE_MATCHER")
            return None
        finally:
            conn.close()

    def _calculate_similarity(self, query_text: str, template_document_id: str) -> float:
        """
        Calculate similarity between query document and template using RAG

        Args:
            query_text: Text of the document to match
            template_document_id: Document ID of the template

        Returns:
            Aggregate similarity score (0.0 to 1.0)
        """
        # Generate embedding for a representative sample of the query document
        # Use first 3000 characters to avoid embedding size limits
        query_sample = query_text[:3000]
        query_embedding = self.embedding_service.generate_query_embedding(query_sample)

        # Search FAISS index for similar chunks
        results = self.vector_store.search(query_embedding, self.top_k_chunks * 2)  # Get more results to filter

        # Filter results to only include chunks from the template document
        conn = self._get_connection()
        cursor = conn.cursor()

        template_similarities = []
        for embedding_id, distance in results:
            cursor.execute("""
                SELECT document_id
                FROM chunks
                WHERE embedding_id = ?
            """, (embedding_id,))

            row = cursor.fetchone()
            if row and row[0] == template_document_id:
                # Convert L2 distance to similarity score (same formula as document_manager)
                similarity = float(1 / (1 + distance))
                template_similarities.append(similarity)

                # Stop once we have enough matches
                if len(template_similarities) >= self.top_k_chunks:
                    break

        conn.close()

        if not template_similarities:
            return 0.0

        # Calculate aggregate similarity score
        # Use weighted average: higher weight for top matches
        weights = [1.0 / (i + 1) for i in range(len(template_similarities))]
        weighted_sum = sum(s * w for s, w in zip(template_similarities, weights))
        weight_total = sum(weights)

        aggregate_score = weighted_sum / weight_total if weight_total > 0 else 0.0

        return aggregate_score

    def match_all_templates(self, document_id: str) -> List[Dict]:
        """
        Calculate similarity scores for all active templates

        Args:
            document_id: The document ID to match

        Returns:
            List of all templates with similarity scores, sorted by score
        """
        log_info(f"Calculating similarity for all templates: {document_id}", "TEMPLATE_MATCHER")

        document_text = self._get_document_text(document_id)
        if not document_text:
            return []

        templates = self._get_active_templates()
        if not templates:
            return []

        template_scores = []
        for template in templates:
            try:
                similarity_score = self._calculate_similarity(document_text, template['document_id'])
                template_scores.append({
                    **template,
                    "similarity_score": similarity_score
                })
            except Exception as e:
                log_error(f"Failed to calculate similarity for template {template['id']}: {str(e)}", "TEMPLATE_MATCHER")
                continue

        # Sort by similarity score (highest first)
        template_scores.sort(key=lambda x: x['similarity_score'], reverse=True)

        log_success(f"Calculated {len(template_scores)} template similarities", "TEMPLATE_MATCHER")
        return template_scores
