"""
Progressive Redlining Service - Streams clause comparisons in real-time
Supports Server-Sent Events (SSE) for incremental UI updates
Each clause is analyzed and streamed as it completes, allowing for progressive document annotation
"""
import asyncio
import sqlite3
import uuid
import httpx
import json
from typing import AsyncGenerator, Dict, List, Optional, Tuple
from datetime import datetime
import os
from logger import log_info, log_warning, log_error, log_success
from .template_matcher import TemplateMatcher
from .clause_extractor import ClauseExtractor
from .embedding_service import EmbeddingService
import numpy as np


# LLM Prompts (enhanced with RAG support)
DEVIATION_ANALYSIS_PROMPT = '''You are a legal contract analyzer. Compare these two contract clauses and identify all differences.

GOLDEN TEMPLATE CLAUSE (Standard):
Title: {template_title}
Type: {template_type}
Text: {template_text}

NEW CONTRACT CLAUSE:
Title: {new_title}
Type: {new_type}
Text: {new_text}

{rag_context}

Analyze and identify:
1. Material differences (changes that affect legal rights/obligations)
2. Missing provisions (important terms present in template but not in new clause)
3. Added provisions (new terms not in template)
4. Term changes (amounts, dates, durations, parties)
5. Risk level: Low, Medium, High, or Critical

Consider:
- Does the new clause weaken protections?
- Are financial terms less favorable?
- Are timeframes extended in a risky way?
- Are obligations vague or unclear?
- How does this clause compare to the similar examples above (if provided)?

Respond ONLY in valid JSON format with no additional text:
{{
  "material_differences": ["Payment period changed from net-30 to net-60"],
  "missing_provisions": ["Late fee provision", "Interest on overdue amounts"],
  "added_provisions": ["Early payment discount"],
  "term_changes": {{
    "payment_period": {{"template": "net-30", "new": "net-60"}},
    "amount": {{"template": "$50,000", "new": "$45,000"}}
  }},
  "risk_level": "Medium",
  "risk_rationale": "Extended payment period increases financial risk. Reduced amount is favorable but may indicate reduced scope.",
  "summary": "Payment terms modified with extended period and reduced amount"
}}
'''

INDIVIDUAL_CHANGES_PROMPT = '''You are a legal contract analyzer. Compare these two contract clauses and identify SPECIFIC text-level changes.

TEMPLATE CLAUSE (standard):
{template_text}

NEW CONTRACT CLAUSE:
{new_text}

For each difference, identify:
1. Type: "addition" (text added in new), "deletion" (text removed from template), or "modification" (text changed)
2. Original text (what was in template, or empty string for additions)
3. Suggested text (what should replace it based on template, or empty string for deletions)
4. Start position (character offset in NEW clause where change occurs, 0 if deletion)
5. End position (character offset in NEW clause where change ends, 0 if deletion)
6. Risk level: Low, Medium, High
7. Brief rationale (why this change matters)

BE SPECIFIC - identify individual words/phrases, not entire paragraphs.

Respond ONLY in valid JSON format:
{{
  "changes": [
    {{
      "change_type": "modification",
      "original_text": "30 days",
      "suggested_text": "net-30 days",
      "start_offset": 45,
      "end_offset": 52,
      "risk_level": "Low",
      "rationale": "Added clarity with 'net-' prefix"
    }},
    {{
      "change_type": "deletion",
      "original_text": "late fee provision",
      "suggested_text": "",
      "start_offset": 0,
      "end_offset": 0,
      "risk_level": "High",
      "rationale": "Missing late fee provision increases financial risk"
    }}
  ]
}}'''


class ProgressiveRedliningService:
    """
    Progressive redlining service with real-time streaming support

    This service processes contract clauses one-by-one and yields events
    for Server-Sent Events (SSE) streaming to the frontend, enabling
    real-time document annotation as analysis progresses.
    """

    def __init__(self, doc_manager=None):
        # Database path from environment
        db_path = os.getenv("DATABASE_PATH", "/app/data/documents.db")
        self.db_path = db_path

        # Ollama configuration
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
        self.model_name = os.getenv("OLLAMA_MODEL", "mistral:latest")

        # Comparison configuration
        self.clause_similarity_threshold = 0.6  # Minimum similarity to match clauses

        # Initialize dependent services
        self.template_matcher = TemplateMatcher()
        self.clause_extractor = ClauseExtractor()
        self.embedding_service = EmbeddingService()

        # RAG support - document manager for semantic search
        self.doc_manager = doc_manager
        self.use_rag = doc_manager is not None

    def _get_connection(self):
        """Get SQLite database connection"""
        return sqlite3.connect(self.db_path)

    async def start_progressive_session(self, document_id: str, category: Optional[str] = None) -> Dict:
        """
        Start progressive analysis session - returns immediately with session_id
        Actual analysis happens in background via analyze_progressive()

        Args:
            document_id: The uploaded document ID
            category: Optional category for template matching

        Returns:
            {
                "session_id": "uuid",
                "status": "processing",
                "uploaded_document_id": "uuid",
                "template_id": "uuid",
                "template_document_id": "uuid"
            }
        """
        log_info(f"Starting progressive redlining session for document: {document_id}", "PROGRESSIVE_REDLINING")

        try:
            # Step 1: Extract clauses from uploaded document (synchronous for now)
            new_clauses = self.clause_extractor.get_document_clauses(document_id)
            if not new_clauses:
                log_info("Clauses not found, extracting...", "PROGRESSIVE_REDLINING")
                new_clauses = self.clause_extractor.extract_clauses(document_id)

            if not new_clauses:
                raise Exception("Failed to extract clauses from document")

            log_success(f"Extracted {len(new_clauses)} clauses from document", "PROGRESSIVE_REDLINING")

            # Step 2: Find best matching template
            template_match = self.template_matcher.find_best_template(document_id, category)

            if not template_match:
                log_warning("No matching template found", "PROGRESSIVE_REDLINING")
                session_id = self._create_session(document_id, None, None, category, status="no_template")
                return {
                    "session_id": session_id,
                    "status": "no_template",
                    "message": "No matching golden template found",
                    "uploaded_document_id": document_id
                }

            template_id = template_match["template_id"]
            template_document_id = template_match["template"]["document_id"]
            match_score = template_match["similarity_score"]

            log_success(f"Found matching template {template_id[:8]} with score {match_score:.3f}", "PROGRESSIVE_REDLINING")

            # Step 3: Extract clauses from template
            template_clauses = self.clause_extractor.get_document_clauses(template_document_id)
            if not template_clauses:
                log_info("Template clauses not found, extracting...", "PROGRESSIVE_REDLINING")
                template_clauses = self.clause_extractor.extract_clauses(template_document_id)

            if not template_clauses:
                raise Exception("Failed to extract clauses from template")

            log_success(f"Extracted {len(template_clauses)} clauses from template", "PROGRESSIVE_REDLINING")

            # Step 4: Create session with status="processing"
            session_id = self._create_session(
                document_id,
                template_id,
                match_score,
                category,
                status="processing"
            )

            log_success(f"Created progressive session: {session_id}", "PROGRESSIVE_REDLINING")

            # Return immediately - analysis happens via analyze_progressive()
            return {
                "session_id": session_id,
                "status": "processing",
                "uploaded_document_id": document_id,
                "template_id": template_id,
                "template_document_id": template_document_id
            }

        except Exception as e:
            log_error(f"Failed to start progressive session: {str(e)}", "PROGRESSIVE_REDLINING")
            raise

    async def analyze_progressive(
        self,
        session_id: str,
        document_id: str,
        template_document_id: str
    ) -> AsyncGenerator[Dict, None]:
        """
        Progressive analysis - yields events for each clause comparison
        This is the core streaming function that enables real-time UI updates

        Yields:
            {
                "event": "clause_compared",
                "data": {
                    "clause_id": "uuid",
                    "comparison_type": "matched|modified|missing|extra",
                    "risk_level": "Low|Medium|High",
                    "changes": [...],  # Individual annotation changes
                    "progress": { "current": 5, "total": 15 }
                }
            }

        Final event:
            {
                "event": "complete",
                "data": {
                    "session_id": "uuid",
                    "overall_risk_score": 0.65,
                    "deviation_count": 12,
                    "summary": { "matched": 10, "modified": 3, "missing": 2, "extra": 0 }
                }
            }
        """
        log_info(f"Starting progressive analysis for session: {session_id}", "PROGRESSIVE_REDLINING")

        try:
            # Get clauses for both documents
            new_clauses = self._get_document_clauses(document_id)
            template_clauses = self._get_document_clauses(template_document_id)

            if not new_clauses or not template_clauses:
                raise Exception("Failed to retrieve clauses for comparison")

            log_info(f"Comparing {len(new_clauses)} new clauses against {len(template_clauses)} template clauses", "PROGRESSIVE_REDLINING")

            # Match clauses using semantic similarity (synchronous)
            clause_pairs = self._match_clauses(new_clauses, template_clauses)

            total_clauses = (
                len(clause_pairs["matched"]) +
                len(clause_pairs["modified"]) +
                len(clause_pairs["missing"]) +
                len(clause_pairs["extra"])
            )
            current = 0
            summary = {"matched": 0, "modified": 0, "missing": 0, "extra": 0}
            all_risk_scores = []

            # Process matched clauses
            for new_clause, template_clause, similarity in clause_pairs["matched"]:
                current += 1

                # Store clause comparison
                comparison_id = self._store_clause_comparison(
                    session_id, new_clause["id"], template_clause["id"],
                    "matched", similarity, "Low", ""
                )

                # No changes for matched clauses
                changes = []

                yield {
                    "event": "clause_compared",
                    "data": {
                        "clause_id": new_clause["id"],
                        "comparison_type": "matched",
                        "risk_level": "Low",
                        "changes": changes,
                        "progress": {"current": current, "total": total_clauses}
                    }
                }

                summary["matched"] += 1
                all_risk_scores.append(0.1)  # Low risk

                await asyncio.sleep(0.1)  # Small delay for smooth streaming

            # Process modified clauses (with LLM-powered deviation analysis + RAG)
            for new_clause, template_clause, similarity in clause_pairs["modified"]:
                current += 1

                try:
                    # Get RAG context for better analysis
                    rag_context = self._get_rag_context_for_clause(new_clause, top_k=2)

                    # Analyze deviations using async LLM call with RAG context
                    deviation = await self._analyze_deviation_async(new_clause, template_clause, rag_context)
                    risk_level = deviation.get("risk_level", "Medium")
                    deviation_summary = deviation.get("summary", "")

                    # Generate individual changes using async LLM call
                    individual_changes = await self._generate_individual_changes_async(
                        new_clause, template_clause
                    )

                except Exception as e:
                    log_error(f"Failed to analyze clause {new_clause['title']}: {str(e)}", "PROGRESSIVE_REDLINING")
                    # Fallback to basic comparison
                    risk_level = "Medium"
                    deviation_summary = "Analysis failed"
                    individual_changes = [{
                        "change_type": "modification",
                        "original_text": template_clause["text"],
                        "suggested_text": new_clause["text"],
                        "start_offset": 0,
                        "end_offset": len(new_clause["text"]),
                        "risk_level": "Medium",
                        "rationale": "Clause modified (detailed analysis unavailable)"
                    }]

                # Store clause comparison
                comparison_id = self._store_clause_comparison(
                    session_id, new_clause["id"], template_clause["id"],
                    "modified", similarity, risk_level, deviation_summary
                )

                # Store individual changes
                stored_changes = self._store_individual_changes(comparison_id, individual_changes)

                yield {
                    "event": "clause_compared",
                    "data": {
                        "clause_id": new_clause["id"],
                        "comparison_type": "modified",
                        "risk_level": risk_level,
                        "changes": stored_changes,
                        "progress": {"current": current, "total": total_clauses}
                    }
                }

                summary["modified"] += 1
                all_risk_scores.append(self._risk_level_to_score(risk_level))

                await asyncio.sleep(0.3)  # Longer delay for LLM processing

            # Process missing clauses
            for template_clause in clause_pairs["missing"]:
                current += 1
                risk_level = "High"  # Missing clauses are high risk

                # Store clause comparison
                comparison_id = self._store_clause_comparison(
                    session_id, None, template_clause["id"],
                    "missing", 0.0, risk_level, "Clause missing from uploaded document"
                )

                # Create single change for missing clause
                changes = [{
                    "change_type": "missing_clause",
                    "original_text": "",
                    "suggested_text": template_clause["text"],
                    "start_offset": 0,
                    "end_offset": 0,
                    "risk_level": risk_level,
                    "rationale": f"This {template_clause['type']} clause is required but missing from the uploaded document."
                }]
                stored_changes = self._store_individual_changes(comparison_id, changes)

                yield {
                    "event": "clause_compared",
                    "data": {
                        "clause_id": template_clause["id"],
                        "comparison_type": "missing",
                        "risk_level": risk_level,
                        "changes": stored_changes,
                        "progress": {"current": current, "total": total_clauses}
                    }
                }

                summary["missing"] += 1
                all_risk_scores.append(0.8)  # High risk

                await asyncio.sleep(0.1)

            # Process extra clauses (with RAG context to assess if they're standard)
            for new_clause in clause_pairs["extra"]:
                current += 1

                # Use RAG to find similar clauses from other documents
                rag_context = self._get_rag_context_for_clause(new_clause, top_k=3)

                # Assess risk level using RAG context
                risk_level = "Medium"  # Default
                rationale = f"This {new_clause['type']} clause does not appear in the template."

                if rag_context:
                    # If we found similar clauses in other documents, this might be standard
                    rationale += " However, similar clauses were found in other contracts (see analysis)."

                # Store clause comparison
                comparison_id = self._store_clause_comparison(
                    session_id, new_clause["id"], None,
                    "extra", 0.0, risk_level, "Extra clause not in template"
                )

                # Create single change for extra clause with RAG insight
                changes = [{
                    "change_type": "extra_clause",
                    "original_text": new_clause["text"],
                    "suggested_text": "",
                    "start_offset": 0,
                    "end_offset": len(new_clause["text"]),
                    "risk_level": risk_level,
                    "rationale": rationale,
                    "rag_context": rag_context[:500] if rag_context else None  # Include snippet for reference
                }]
                stored_changes = self._store_individual_changes(comparison_id, changes)

                yield {
                    "event": "clause_compared",
                    "data": {
                        "clause_id": new_clause["id"],
                        "comparison_type": "extra",
                        "risk_level": risk_level,
                        "changes": stored_changes,
                        "progress": {"current": current, "total": total_clauses}
                    }
                }

                summary["extra"] += 1
                all_risk_scores.append(0.5)  # Medium risk

                await asyncio.sleep(0.1)

            # Calculate overall risk score
            overall_risk_score = sum(all_risk_scores) / len(all_risk_scores) if all_risk_scores else 0.0
            deviation_count = summary["modified"] + summary["missing"] + summary["extra"]

            # Update session status to completed
            self._update_session_completion(session_id, overall_risk_score, deviation_count)

            log_success(f"Progressive analysis complete: {deviation_count} deviations, risk {overall_risk_score:.2f}", "PROGRESSIVE_REDLINING")

            # Yield final completion event
            yield {
                "event": "complete",
                "data": {
                    "session_id": session_id,
                    "overall_risk_score": overall_risk_score,
                    "deviation_count": deviation_count,
                    "summary": summary
                }
            }

        except Exception as e:
            log_error(f"Progressive analysis failed: {str(e)}", "PROGRESSIVE_REDLINING")

            # Yield error event
            yield {
                "event": "error",
                "data": {
                    "message": str(e)
                }
            }

            # Update session status to failed
            self._update_session_status(session_id, "failed")

    # ========== Database Helper Methods ==========

    def _create_session(
        self,
        document_id: str,
        template_id: Optional[str],
        match_score: Optional[float],
        category: Optional[str],
        risk_score: float = 0.0,
        deviation_count: int = 0,
        status: str = "processing"
    ) -> str:
        """Create a new redlining session in the database"""
        session_id = str(uuid.uuid4())
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO redlining_sessions (
                    id, uploaded_document_id, template_id,
                    template_match_score, category, status,
                    overall_risk_score, deviation_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                document_id,
                template_id,
                match_score,
                category,
                status,
                risk_score,
                deviation_count
            ))

            conn.commit()
            return session_id

        except Exception as e:
            conn.rollback()
            log_error(f"Failed to create session: {str(e)}", "PROGRESSIVE_REDLINING")
            raise
        finally:
            conn.close()

    def _store_clause_comparison(
        self,
        session_id: str,
        new_clause_id: Optional[str],
        template_clause_id: Optional[str],
        comparison_type: str,
        similarity: float,
        risk_level: str,
        deviation_summary: str
    ) -> str:
        """Store a clause comparison in the database"""
        comparison_id = str(uuid.uuid4())
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO clause_comparisons (
                    id, session_id, new_clause_id, template_clause_id,
                    comparison_type, similarity_score, risk_level, deviation_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                comparison_id,
                session_id,
                new_clause_id,
                template_clause_id,
                comparison_type,
                similarity,
                risk_level,
                deviation_summary
            ))

            conn.commit()
            return comparison_id

        except Exception as e:
            conn.rollback()
            log_error(f"Failed to store comparison: {str(e)}", "PROGRESSIVE_REDLINING")
            raise
        finally:
            conn.close()

    def _store_individual_changes(self, comparison_id: str, changes: List[Dict]) -> List[Dict]:
        """Store individual annotation changes in the database and return them with IDs"""
        conn = self._get_connection()
        cursor = conn.cursor()
        stored_changes = []

        try:
            for change in changes:
                change_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO annotation_changes (
                        id, comparison_id, change_type, original_text,
                        suggested_text, start_offset, end_offset,
                        risk_level, rationale, user_action
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    change_id,
                    comparison_id,
                    change.get("change_type"),
                    change.get("original_text"),
                    change.get("suggested_text"),
                    change.get("start_offset", 0),
                    change.get("end_offset", 0),
                    change.get("risk_level", "Low"),
                    change.get("rationale", ""),
                    "pending"
                ))

                # Add change ID to return object
                stored_change = change.copy()
                stored_change["id"] = change_id
                stored_changes.append(stored_change)

            conn.commit()
            return stored_changes

        except Exception as e:
            conn.rollback()
            log_error(f"Failed to store individual changes: {str(e)}", "PROGRESSIVE_REDLINING")
            raise
        finally:
            conn.close()

    def _update_session_completion(self, session_id: str, risk_score: float, deviation_count: int):
        """Update session to completed status with final metrics"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE redlining_sessions
                SET status = 'completed',
                    overall_risk_score = ?,
                    deviation_count = ?,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (risk_score, deviation_count, session_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            log_error(f"Failed to update session completion: {str(e)}", "PROGRESSIVE_REDLINING")
            raise
        finally:
            conn.close()

    def _update_session_status(self, session_id: str, status: str):
        """Update session status"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE redlining_sessions
                SET status = ?
                WHERE id = ?
            """, (status, session_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            log_error(f"Failed to update session status: {str(e)}", "PROGRESSIVE_REDLINING")
        finally:
            conn.close()

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session details"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, uploaded_document_id, template_id,
                       template_match_score, category, status,
                       overall_risk_score, deviation_count,
                       created_at, completed_at
                FROM redlining_sessions
                WHERE id = ?
            """, (session_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return {
                "id": row[0],
                "uploaded_document_id": row[1],
                "template_id": row[2],
                "template_match_score": row[3],
                "category": row[4],
                "status": row[5],
                "overall_risk_score": row[6],
                "deviation_count": row[7],
                "created_at": row[8],
                "completed_at": row[9]
            }

        except Exception as e:
            log_error(f"Failed to retrieve session: {str(e)}", "PROGRESSIVE_REDLINING")
            return None
        finally:
            conn.close()

    # ========== Clause Matching Methods ==========

    def _get_document_clauses(self, document_id: str) -> List[Dict]:
        """Retrieve all clauses for a document"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, document_id, clause_type, clause_title,
                       clause_text, clause_index, extracted_terms
                FROM document_clauses
                WHERE document_id = ?
                ORDER BY clause_index ASC
            """, (document_id,))

            rows = cursor.fetchall()

            clauses = []
            for row in rows:
                try:
                    terms = json.loads(row[6]) if row[6] else {}
                except json.JSONDecodeError:
                    terms = {}

                clauses.append({
                    "id": row[0],
                    "document_id": row[1],
                    "type": row[2],
                    "title": row[3],
                    "text": row[4],
                    "index": row[5],
                    "terms": terms
                })

            return clauses

        except Exception as e:
            log_error(f"Failed to retrieve clauses: {str(e)}", "PROGRESSIVE_REDLINING")
            return []
        finally:
            conn.close()

    def _match_clauses(self, new_clauses: List[Dict], template_clauses: List[Dict]) -> Dict:
        """
        Match clauses using semantic similarity

        Returns:
            {
                "matched": [(new_clause, template_clause, similarity), ...],
                "modified": [(new_clause, template_clause, similarity), ...],
                "missing": [template_clause, ...],
                "extra": [new_clause, ...]
            }
        """
        matched_pairs = []
        modified_pairs = []
        unmatched_new = []
        unmatched_template = list(template_clauses)

        for new_clause in new_clauses:
            best_match, similarity = self._find_best_matching_clause(new_clause, unmatched_template)

            if best_match and similarity >= self.clause_similarity_threshold:
                if similarity >= 0.9:
                    # Very high similarity - consider it matched
                    matched_pairs.append((new_clause, best_match, similarity))
                else:
                    # Some differences - needs analysis
                    modified_pairs.append((new_clause, best_match, similarity))

                unmatched_template.remove(best_match)
            else:
                # No good match - extra clause
                unmatched_new.append(new_clause)

        return {
            "matched": matched_pairs,
            "modified": modified_pairs,
            "missing": unmatched_template,
            "extra": unmatched_new
        }

    def _find_best_matching_clause(self, query_clause: Dict, candidate_clauses: List[Dict]) -> Tuple[Optional[Dict], float]:
        """Find the best matching clause using semantic similarity"""
        if not candidate_clauses:
            return None, 0.0

        # Generate embedding for query clause
        query_text = f"{query_clause['title']}: {query_clause['text']}"
        query_embedding = self.embedding_service.generate_query_embedding(query_text)

        # Find best match
        best_match = None
        best_similarity = 0.0

        for candidate in candidate_clauses:
            candidate_text = f"{candidate['title']}: {candidate['text']}"
            candidate_embedding = self.embedding_service.generate_query_embedding(candidate_text)

            # Cosine similarity (dot product for normalized vectors)
            similarity = float(np.dot(query_embedding, candidate_embedding))

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = candidate

        return best_match, best_similarity

    # ========== RAG Helper Methods ==========

    def _get_rag_context_for_clause(self, clause: Dict, top_k: int = 3) -> str:
        """
        Search the vector store for similar clauses to provide context

        Args:
            clause: The clause to find similar examples for
            top_k: Number of similar clauses to retrieve

        Returns:
            Formatted string with similar clause examples from other documents
        """
        if not self.use_rag:
            return ""

        try:
            # Create query from clause title and text
            query = f"{clause['title']}: {clause['text'][:300]}"

            # Search for similar clauses
            similar_chunks = self.doc_manager.search_documents(query, top_k=top_k)

            if not similar_chunks:
                return ""

            # Format the context
            context_parts = []
            for i, chunk in enumerate(similar_chunks, 1):
                context_parts.append(
                    f"Example {i} (from {chunk['filename']}):\n{chunk['text']}"
                )

            rag_context = "\n\n".join(context_parts)
            log_info(f"Found {len(similar_chunks)} similar clauses for RAG context", "PROGRESSIVE_REDLINING")

            return rag_context

        except Exception as e:
            log_warning(f"Failed to get RAG context: {str(e)}", "PROGRESSIVE_REDLINING")
            return ""

    # ========== Async LLM Methods ==========

    async def _analyze_deviation_async(self, new_clause: Dict, template_clause: Dict, rag_context: str = "") -> Dict:
        """Use LLM to analyze deviation between two clauses (async version with optional RAG context)"""
        log_info(f"Analyzing deviation for clause: {new_clause['title']}", "PROGRESSIVE_REDLINING")

        # Format RAG context section
        rag_section = ""
        if rag_context:
            rag_section = f"\nSIMILAR CLAUSES FROM OTHER CONTRACTS (for reference):\n{rag_context}\n"

        prompt = DEVIATION_ANALYSIS_PROMPT.format(
            template_title=template_clause["title"],
            template_type=template_clause["type"],
            template_text=template_clause["text"],
            new_title=new_clause["title"],
            new_type=new_clause["type"],
            new_text=new_clause["text"],
            rag_context=rag_section
        )

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": 0.2}
                }

                response = await client.post(
                    self.ollama_url,
                    json=payload,
                    timeout=60.0
                )

                if response.status_code != 200:
                    raise Exception(f"Ollama returned status {response.status_code}")

                result = response.json()
                content = result["message"]["content"]

                # Clean JSON from markdown code blocks
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                deviation = json.loads(content)
                log_success(f"Deviation analysis complete: {deviation['risk_level']}", "PROGRESSIVE_REDLINING")

                return deviation

        except Exception as e:
            log_error(f"Deviation analysis failed: {str(e)}", "PROGRESSIVE_REDLINING")
            raise

    async def _generate_individual_changes_async(self, new_clause: Dict, template_clause: Dict) -> List[Dict]:
        """Use LLM to generate individual text-level changes (async version)"""
        log_info(f"Generating individual changes for: {new_clause['title']}", "PROGRESSIVE_REDLINING")

        prompt = INDIVIDUAL_CHANGES_PROMPT.format(
            template_text=template_clause["text"],
            new_text=new_clause["text"]
        )

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": 0.1}
                }

                response = await client.post(
                    self.ollama_url,
                    json=payload,
                    timeout=90.0
                )

                if response.status_code != 200:
                    raise Exception(f"Ollama returned status {response.status_code}")

                result = response.json()
                content = result["message"]["content"]

                # Clean JSON from markdown code blocks
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                parsed = json.loads(content)
                changes = parsed.get("changes", [])

                log_success(f"Generated {len(changes)} individual changes", "PROGRESSIVE_REDLINING")
                return changes

        except Exception as e:
            log_error(f"Individual changes generation failed: {str(e)}", "PROGRESSIVE_REDLINING")
            raise

    # ========== Helper Methods ==========

    def _risk_level_to_score(self, risk_level: str) -> float:
        """Convert risk level string to numeric score"""
        risk_map = {
            "Low": 0.2,
            "Medium": 0.5,
            "High": 0.8,
            "Critical": 1.0
        }
        return risk_map.get(risk_level, 0.5)
