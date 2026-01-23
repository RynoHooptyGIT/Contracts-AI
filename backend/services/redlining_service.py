"""
Redlining service - Orchestrates the full contract redlining workflow
Manages sessions, coordinates template matching, clause extraction, and comparison
"""
import sqlite3
import uuid
from typing import Dict, List, Optional
from datetime import datetime
import os
from logger import log_info, log_warning, log_error, log_success
from .template_matcher import TemplateMatcher
from .clause_extractor import ClauseExtractor
from .comparison_engine import ComparisonEngine


class RedliningService:
    """Service for managing contract redlining sessions"""

    def __init__(self):
        # Database path from environment
        db_path = os.getenv("DATABASE_PATH", "/app/data/documents.db")
        self.db_path = db_path

        # Initialize dependent services
        self.template_matcher = TemplateMatcher()
        self.clause_extractor = ClauseExtractor()
        self.comparison_engine = ComparisonEngine()

    def _get_connection(self):
        """Get SQLite database connection"""
        return sqlite3.connect(self.db_path)

    def start_redlining_session(self, document_id: str, category: Optional[str] = None) -> Dict:
        """
        Start a new redlining session for an uploaded contract

        Workflow:
        1. Extract clauses from uploaded document (if not already done)
        2. Match against golden templates
        3. Extract clauses from best template (if not already done)
        4. Compare clause-by-clause
        5. Store results in redlining_sessions and clause_comparisons tables

        Args:
            document_id: The uploaded document ID
            category: Optional category filter for template matching

        Returns:
            Session dictionary with session_id and initial status
        """
        log_info(f"Starting redlining session for document: {document_id}", "REDLINING_SERVICE")

        try:
            # Step 1: Extract clauses from uploaded document
            log_info("Step 1: Extracting clauses from uploaded document", "REDLINING_SERVICE")

            # Check if clauses already extracted
            new_clauses = self.clause_extractor.get_document_clauses(document_id)
            if not new_clauses:
                log_info("Clauses not found, extracting...", "REDLINING_SERVICE")
                new_clauses = self.clause_extractor.extract_clauses(document_id)

            if not new_clauses:
                raise Exception("Failed to extract clauses from document")

            log_success(f"Extracted {len(new_clauses)} clauses from document", "REDLINING_SERVICE")

            # Step 2: Find best matching template
            log_info("Step 2: Finding best matching template", "REDLINING_SERVICE")
            template_match = self.template_matcher.find_best_template(document_id, category)

            if not template_match:
                log_warning("No matching template found", "REDLINING_SERVICE")
                # Create session without template
                session_id = self._create_session(document_id, None, None, category)
                return {
                    "session_id": session_id,
                    "status": "no_template",
                    "message": "No matching golden template found for this document"
                }

            template_id = template_match["template_id"]
            template_document_id = template_match["template"]["document_id"]
            match_score = template_match["similarity_score"]

            log_success(f"Found matching template {template_id[:8]} with score {match_score:.3f}", "REDLINING_SERVICE")

            # Step 3: Extract clauses from template
            log_info("Step 3: Extracting clauses from template", "REDLINING_SERVICE")

            # Check if clauses already extracted
            template_clauses = self.clause_extractor.get_document_clauses(template_document_id)
            if not template_clauses:
                log_info("Template clauses not found, extracting...", "REDLINING_SERVICE")
                template_clauses = self.clause_extractor.extract_clauses(template_document_id)

            if not template_clauses:
                raise Exception("Failed to extract clauses from template")

            log_success(f"Extracted {len(template_clauses)} clauses from template", "REDLINING_SERVICE")

            # Step 4: Compare documents
            log_info("Step 4: Comparing documents clause-by-clause", "REDLINING_SERVICE")
            comparison = self.comparison_engine.compare_documents(document_id, template_document_id)

            # Calculate overall risk score
            risk_score = self.comparison_engine.calculate_overall_risk_score(comparison)

            # Count total deviations
            deviation_count = len(comparison["modified"]) + len(comparison["missing"]) + len(comparison["extra"])

            log_success(f"Comparison complete: {deviation_count} deviations, risk score {risk_score:.2f}", "REDLINING_SERVICE")

            # Step 5: Create session and store results
            log_info("Step 5: Storing session results", "REDLINING_SERVICE")
            session_id = self._create_session(
                document_id,
                template_id,
                match_score,
                category,
                risk_score,
                deviation_count
            )

            # Store comparison results
            self._store_comparison_results(session_id, comparison)

            log_success(f"Redlining session created: {session_id}", "REDLINING_SERVICE")

            return {
                "session_id": session_id,
                "status": "completed",
                "template_id": template_id,
                "template_match_score": match_score,
                "overall_risk_score": risk_score,
                "deviation_count": deviation_count,
                "summary": {
                    "matched": len(comparison["matched"]),
                    "modified": len(comparison["modified"]),
                    "missing": len(comparison["missing"]),
                    "extra": len(comparison["extra"])
                }
            }

        except Exception as e:
            log_error(f"Failed to start redlining session: {str(e)}", "REDLINING_SERVICE")
            raise

    def _create_session(
        self,
        document_id: str,
        template_id: Optional[str],
        match_score: Optional[float],
        category: Optional[str],
        risk_score: float = 0.0,
        deviation_count: int = 0
    ) -> str:
        """
        Create a new redlining session in the database

        Args:
            document_id: The uploaded document ID
            template_id: The matched template ID (None if no template)
            match_score: Template match similarity score
            category: Contract category
            risk_score: Overall risk score (0.0 to 1.0)
            deviation_count: Number of deviations found

        Returns:
            Session ID (UUID)
        """
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
                "completed",
                risk_score,
                deviation_count
            ))

            conn.commit()
            log_info(f"Created session: {session_id}", "REDLINING_SERVICE")
            return session_id

        except Exception as e:
            conn.rollback()
            log_error(f"Failed to create session: {str(e)}", "REDLINING_SERVICE")
            raise
        finally:
            conn.close()

    def _store_comparison_results(self, session_id: str, comparison: Dict):
        """
        Store clause comparison results in the database

        Args:
            session_id: The session ID
            comparison: Comparison results from ComparisonEngine
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Store matched clauses
            for item in comparison["matched"]:
                comparison_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO clause_comparisons (
                        id, session_id, new_clause_id, template_clause_id,
                        comparison_type, similarity_score, risk_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    comparison_id,
                    session_id,
                    item["new_clause"]["id"],
                    item["template_clause"]["id"],
                    "matched",
                    item["similarity"],
                    "Low"
                ))

            # Store modified clauses
            for item in comparison["modified"]:
                comparison_id = str(uuid.uuid4())
                deviation = item.get("deviation", {})
                risk_level = deviation.get("risk_level", "Unknown")
                summary = deviation.get("summary", "")

                cursor.execute("""
                    INSERT INTO clause_comparisons (
                        id, session_id, new_clause_id, template_clause_id,
                        comparison_type, similarity_score, risk_level,
                        deviation_summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    comparison_id,
                    session_id,
                    item["new_clause"]["id"],
                    item["template_clause"]["id"],
                    "modified",
                    item["similarity"],
                    risk_level,
                    summary
                ))

            # Store missing clauses
            for item in comparison["missing"]:
                comparison_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO clause_comparisons (
                        id, session_id, new_clause_id, template_clause_id,
                        comparison_type, similarity_score, risk_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    comparison_id,
                    session_id,
                    None,  # No new clause
                    item["clause"]["id"],
                    "missing",
                    0.0,
                    "High"
                ))

            # Store extra clauses
            for item in comparison["extra"]:
                comparison_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO clause_comparisons (
                        id, session_id, new_clause_id, template_clause_id,
                        comparison_type, similarity_score, risk_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    comparison_id,
                    session_id,
                    item["clause"]["id"],
                    None,  # No template clause
                    "extra",
                    0.0,
                    "Medium"
                ))

            conn.commit()
            log_info(f"Stored comparison results for session: {session_id}", "REDLINING_SERVICE")

        except Exception as e:
            conn.rollback()
            log_error(f"Failed to store comparison results: {str(e)}", "REDLINING_SERVICE")
            raise
        finally:
            conn.close()

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve session details with full comparison results

        Args:
            session_id: The session ID

        Returns:
            Session dictionary with all details, or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Get session info
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

            session = {
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

            # Get comparison results
            session["comparisons"] = self.get_session_comparisons(session_id)

            return session

        except Exception as e:
            log_error(f"Failed to retrieve session: {str(e)}", "REDLINING_SERVICE")
            return None
        finally:
            conn.close()

    def get_session_comparisons(self, session_id: str) -> List[Dict]:
        """
        Retrieve all clause comparisons for a session

        Args:
            session_id: The session ID

        Returns:
            List of comparison dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, session_id, new_clause_id, template_clause_id,
                       comparison_type, similarity_score, risk_level,
                       deviation_summary, created_at
                FROM clause_comparisons
                WHERE session_id = ?
                ORDER BY comparison_type, risk_level DESC
            """, (session_id,))

            rows = cursor.fetchall()

            comparisons = []
            for row in rows:
                comparisons.append({
                    "id": row[0],
                    "session_id": row[1],
                    "new_clause_id": row[2],
                    "template_clause_id": row[3],
                    "comparison_type": row[4],
                    "similarity_score": row[5],
                    "risk_level": row[6],
                    "deviation_summary": row[7],
                    "created_at": row[8]
                })

            return comparisons

        except Exception as e:
            log_error(f"Failed to retrieve comparisons: {str(e)}", "REDLINING_SERVICE")
            return []
        finally:
            conn.close()

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a redlining session and all associated data

        Args:
            session_id: The session ID

        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Delete comparisons first (foreign key constraint)
            cursor.execute("DELETE FROM clause_comparisons WHERE session_id = ?", (session_id,))

            # Delete session
            cursor.execute("DELETE FROM redlining_sessions WHERE id = ?", (session_id,))

            conn.commit()
            log_info(f"Deleted session: {session_id}", "REDLINING_SERVICE")
            return True

        except Exception as e:
            conn.rollback()
            log_error(f"Failed to delete session: {str(e)}", "REDLINING_SERVICE")
            return False
        finally:
            conn.close()
