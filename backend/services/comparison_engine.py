"""
Comparison engine for clause-by-clause contract analysis
Matches clauses between new contracts and golden templates using RAG
Identifies: matched, modified, missing, and extra clauses
Calculates risk scores and generates LLM-powered deviation summaries
"""
import sqlite3
import httpx
import json
import uuid
from typing import Dict, List, Optional, Tuple
import os
from logger import log_info, log_warning, log_error, log_success
from .embedding_service import EmbeddingService
from .vector_store import FAISSVectorStore


# LLM Prompt Template for deviation analysis
DEVIATION_ANALYSIS_PROMPT = '''You are a legal contract analyzer. Compare these two contract clauses and identify all differences.

GOLDEN TEMPLATE CLAUSE (Standard):
Title: {template_title}
Type: {template_type}
Text: {template_text}

NEW CONTRACT CLAUSE:
Title: {new_title}
Type: {new_type}
Text: {new_text}

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


class ComparisonEngine:
    """Service for comparing contracts to golden templates clause-by-clause"""

    def __init__(self):
        # Database path from environment
        db_path = os.getenv("DATABASE_PATH", "/app/data/documents.db")
        self.db_path = db_path

        # Ollama configuration
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
        self.model_name = os.getenv("OLLAMA_MODEL", "mistral:latest")

        # Comparison configuration
        self.clause_similarity_threshold = 0.6  # Minimum similarity to match clauses
        self.top_k_matches = 3  # Consider top-3 similar clauses

        # Initialize embedding and vector store services
        self.embedding_service = EmbeddingService()
        self.vector_store = FAISSVectorStore()

    def _get_connection(self):
        """Get SQLite database connection"""
        return sqlite3.connect(self.db_path)

    def compare_documents(self, new_document_id: str, template_document_id: str) -> Dict:
        """
        Compare a new contract against a golden template clause-by-clause

        Args:
            new_document_id: The uploaded contract document ID
            template_document_id: The golden template document ID

        Returns:
            Dictionary with comparison results:
            {
                "matched": [...],  # Clauses that match well
                "modified": [...], # Clauses with differences
                "missing": [...],  # Template clauses not found in new contract
                "extra": [...]     # New clauses not in template
            }
        """
        log_info(f"Comparing documents: new={new_document_id[:8]}, template={template_document_id[:8]}", "COMPARISON_ENGINE")

        # Get clauses from both documents
        new_clauses = self._get_document_clauses(new_document_id)
        template_clauses = self._get_document_clauses(template_document_id)

        if not new_clauses:
            log_warning(f"No clauses found for new document: {new_document_id}", "COMPARISON_ENGINE")
            return {"matched": [], "modified": [], "missing": template_clauses, "extra": []}

        if not template_clauses:
            log_warning(f"No clauses found for template: {template_document_id}", "COMPARISON_ENGINE")
            return {"matched": [], "modified": [], "missing": [], "extra": new_clauses}

        log_info(f"Comparing {len(new_clauses)} new clauses against {len(template_clauses)} template clauses", "COMPARISON_ENGINE")

        # Match clauses using semantic similarity
        matched_pairs = []
        unmatched_new = []
        unmatched_template = list(template_clauses)  # Start with all template clauses

        for new_clause in new_clauses:
            best_match, similarity = self._find_best_matching_clause(new_clause, unmatched_template)

            if best_match and similarity >= self.clause_similarity_threshold:
                # Found a good match
                matched_pairs.append({
                    "new_clause": new_clause,
                    "template_clause": best_match,
                    "similarity": similarity
                })
                unmatched_template.remove(best_match)
            else:
                # No good match found - this is an extra clause
                unmatched_new.append(new_clause)

        log_info(f"Matched {len(matched_pairs)} clause pairs, {len(unmatched_new)} extra, {len(unmatched_template)} missing", "COMPARISON_ENGINE")

        # Analyze matched pairs for deviations
        matched_clauses = []
        modified_clauses = []

        for pair in matched_pairs:
            if pair["similarity"] >= 0.9:
                # Very high similarity - consider it matched
                matched_clauses.append({
                    "new_clause": pair["new_clause"],
                    "template_clause": pair["template_clause"],
                    "similarity": pair["similarity"],
                    "comparison_type": "matched"
                })
            else:
                # Some differences - needs deviation analysis
                try:
                    deviation = self._analyze_deviation(pair["new_clause"], pair["template_clause"])
                    modified_clauses.append({
                        "new_clause": pair["new_clause"],
                        "template_clause": pair["template_clause"],
                        "similarity": pair["similarity"],
                        "comparison_type": "modified",
                        "deviation": deviation
                    })
                except Exception as e:
                    log_error(f"Failed to analyze deviation: {str(e)}", "COMPARISON_ENGINE")
                    # Still include it as modified but without deviation details
                    modified_clauses.append({
                        "new_clause": pair["new_clause"],
                        "template_clause": pair["template_clause"],
                        "similarity": pair["similarity"],
                        "comparison_type": "modified",
                        "deviation": {
                            "risk_level": "Unknown",
                            "summary": "Failed to analyze deviation"
                        }
                    })

        log_success(f"Comparison complete: {len(matched_clauses)} matched, {len(modified_clauses)} modified", "COMPARISON_ENGINE")

        return {
            "matched": matched_clauses,
            "modified": modified_clauses,
            "missing": [{"clause": c, "comparison_type": "missing"} for c in unmatched_template],
            "extra": [{"clause": c, "comparison_type": "extra"} for c in unmatched_new]
        }

    def _get_document_clauses(self, document_id: str) -> List[Dict]:
        """
        Retrieve all clauses for a document

        Args:
            document_id: The document ID

        Returns:
            List of clause dictionaries
        """
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
                # Parse terms JSON
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
            log_error(f"Failed to retrieve clauses: {str(e)}", "COMPARISON_ENGINE")
            return []
        finally:
            conn.close()

    def _find_best_matching_clause(self, query_clause: Dict, candidate_clauses: List[Dict]) -> Tuple[Optional[Dict], float]:
        """
        Find the best matching clause from candidates using semantic similarity

        Args:
            query_clause: The clause to match
            candidate_clauses: List of candidate clauses to match against

        Returns:
            Tuple of (best_match_clause, similarity_score)
        """
        if not candidate_clauses:
            return None, 0.0

        # Generate embedding for query clause text
        query_text = f"{query_clause['title']}: {query_clause['text']}"
        query_embedding = self.embedding_service.generate_query_embedding(query_text)

        # Calculate similarity with each candidate
        best_match = None
        best_similarity = 0.0

        for candidate in candidate_clauses:
            # Generate embedding for candidate
            candidate_text = f"{candidate['title']}: {candidate['text']}"
            candidate_embedding = self.embedding_service.generate_query_embedding(candidate_text)

            # Calculate cosine similarity (using dot product since vectors are normalized)
            import numpy as np
            similarity = float(np.dot(query_embedding, candidate_embedding))

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = candidate

        return best_match, best_similarity

    def _analyze_deviation(self, new_clause: Dict, template_clause: Dict) -> Dict:
        """
        Use LLM to analyze differences between two clauses

        Args:
            new_clause: The clause from new contract
            template_clause: The clause from golden template

        Returns:
            Dictionary with deviation analysis results
        """
        log_info(f"Analyzing deviation for clause: {new_clause['title']}", "COMPARISON_ENGINE")

        # Prepare prompt
        prompt = DEVIATION_ANALYSIS_PROMPT.format(
            template_title=template_clause["title"],
            template_type=template_clause["type"],
            template_text=template_clause["text"],
            new_title=new_clause["title"],
            new_type=new_clause["type"],
            new_text=new_clause["text"]
        )

        # Call LLM
        try:
            with httpx.Client() as client:
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.2  # Lower temperature for structured output
                    }
                }

                response = client.post(
                    self.ollama_url,
                    json=payload,
                    timeout=60.0
                )

                if response.status_code != 200:
                    raise Exception(f"Ollama returned status {response.status_code}: {response.text}")

                result = response.json()

                # Extract content
                if "message" in result and "content" in result["message"]:
                    content = result["message"]["content"]
                else:
                    raise Exception(f"Unexpected response format: {result}")

                # Parse JSON from content
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                deviation = json.loads(content)

                log_success(f"Deviation analysis complete: {deviation['risk_level']}", "COMPARISON_ENGINE")
                return deviation

        except json.JSONDecodeError as e:
            log_error(f"Failed to parse LLM JSON response: {str(e)}", "COMPARISON_ENGINE")
            raise Exception(f"Failed to parse deviation analysis: {str(e)}")

        except Exception as e:
            log_error(f"LLM call error: {str(e)}", "COMPARISON_ENGINE")
            raise

    def calculate_overall_risk_score(self, comparison_results: Dict) -> float:
        """
        Calculate overall risk score for a comparison (0.0 to 1.0)

        Args:
            comparison_results: Results from compare_documents()

        Returns:
            Risk score where 0.0 is low risk and 1.0 is critical risk
        """
        risk_levels = {
            "Low": 0.2,
            "Medium": 0.5,
            "High": 0.8,
            "Critical": 1.0,
            "Unknown": 0.5
        }

        total_clauses = (
            len(comparison_results["matched"]) +
            len(comparison_results["modified"]) +
            len(comparison_results["missing"]) +
            len(comparison_results["extra"])
        )

        if total_clauses == 0:
            return 0.0

        risk_sum = 0.0

        # Matched clauses: low risk
        risk_sum += len(comparison_results["matched"]) * 0.1

        # Modified clauses: use deviation risk level
        for item in comparison_results["modified"]:
            if "deviation" in item and "risk_level" in item["deviation"]:
                risk_sum += risk_levels.get(item["deviation"]["risk_level"], 0.5)
            else:
                risk_sum += 0.5  # Unknown risk

        # Missing clauses: high risk (template provisions missing)
        risk_sum += len(comparison_results["missing"]) * 0.8

        # Extra clauses: medium risk (new provisions not in template)
        risk_sum += len(comparison_results["extra"]) * 0.5

        overall_risk = risk_sum / total_clauses
        log_info(f"Overall risk score: {overall_risk:.2f}", "COMPARISON_ENGINE")

        return overall_risk

    def get_critical_deviations(self, comparison_results: Dict) -> List[Dict]:
        """
        Extract all high and critical risk deviations from comparison results

        Args:
            comparison_results: Results from compare_documents()

        Returns:
            List of critical deviation dictionaries
        """
        critical = []

        # Check modified clauses
        for item in comparison_results["modified"]:
            if "deviation" in item and "risk_level" in item["deviation"]:
                risk_level = item["deviation"]["risk_level"]
                if risk_level in ["High", "Critical"]:
                    critical.append({
                        "type": "modified",
                        "clause_title": item["new_clause"]["title"],
                        "risk_level": risk_level,
                        "summary": item["deviation"].get("summary", ""),
                        "rationale": item["deviation"].get("risk_rationale", "")
                    })

        # Missing clauses are always high risk
        for item in comparison_results["missing"]:
            critical.append({
                "type": "missing",
                "clause_title": item["clause"]["title"],
                "risk_level": "High",
                "summary": f"Missing clause: {item['clause']['title']}",
                "rationale": "This clause is present in the golden template but missing from the new contract"
            })

        log_info(f"Found {len(critical)} critical deviations", "COMPARISON_ENGINE")
        return critical
