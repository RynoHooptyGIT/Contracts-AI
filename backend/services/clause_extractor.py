"""
LLM-powered clause extraction service using Ollama
"""
import json
import uuid
import time
import sqlite3
import httpx
from typing import Dict, List, Optional
from pathlib import Path
import os
from logger import log_info, log_warning, log_error, log_success

# LLM Prompt Template for clause extraction
CLAUSE_EXTRACTION_PROMPT = '''You are a legal contract analyzer. Extract all distinct clauses from this contract.

For each clause provide:
1. Title (e.g., "Payment Terms")
2. Type: must be one of: Payment, Liability, Termination, Confidentiality, IP, Dispute, Warranty, Indemnification, Other
3. Full clause text
4. Key terms (amounts, dates, durations, parties) as a dict
5. Position index (1, 2, 3...)

Contract Text:
{contract_text}

Respond ONLY in valid JSON format with no additional text:
{{
  "clauses": [
    {{
      "title": "Payment Terms",
      "type": "Payment",
      "text": "Payment shall be made within thirty (30) days...",
      "terms": {{"period": "30 days", "amount": "$50,000"}},
      "index": 1
    }}
  ]
}}
'''


class ClauseExtractor:
    """Service for extracting and managing clauses from legal documents using LLM"""

    def __init__(self):
        # Database path from environment
        db_path = os.getenv("DATABASE_PATH", "/app/data/documents.db")
        self.db_path = db_path

        # Ollama configuration
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
        self.model_name = os.getenv("OLLAMA_MODEL", "mistral:latest")

        # Chunking configuration for large documents
        self.max_chunk_size = 25000  # Max characters per chunk (safe for 8k token models)
        self.chunk_overlap = 2000    # Overlap between chunks to catch clauses spanning boundaries

    def _get_connection(self):
        """Get SQLite database connection"""
        return sqlite3.connect(self.db_path)

    def _get_document_text(self, document_id: str) -> Optional[str]:
        """
        Retrieve the full text of a document by concatenating all chunks

        Args:
            document_id: The document ID to retrieve

        Returns:
            Full document text or None if document not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get all chunks for this document, ordered by chunk_index
            cursor.execute("""
                SELECT text FROM chunks
                WHERE document_id = ?
                ORDER BY chunk_index ASC
            """, (document_id,))

            chunks = cursor.fetchall()
            conn.close()

            if not chunks:
                log_warning(f"No chunks found for document: {document_id}", "CLAUSE_EXTRACTOR")
                return None

            # Concatenate all chunks
            full_text = "\n\n".join([chunk[0] for chunk in chunks])
            log_info(f"Retrieved document text ({len(full_text)} chars)", "CLAUSE_EXTRACTOR")
            return full_text

        except Exception as e:
            log_error(f"Failed to retrieve document text: {str(e)}", "CLAUSE_EXTRACTOR")
            return None

    def _call_llm(self, prompt: str, max_retries: int = 3) -> Dict:
        """
        Call Ollama LLM with retry logic and structured output parsing

        Args:
            prompt: The prompt to send to the LLM
            max_retries: Maximum number of retry attempts

        Returns:
            Parsed JSON response from LLM

        Raises:
            Exception: If all retry attempts fail
        """
        retry_delays = [1, 2, 4]  # Exponential backoff delays in seconds

        for attempt in range(max_retries):
            try:
                log_info(f"Calling Ollama LLM (attempt {attempt + 1}/{max_retries})", "CLAUSE_EXTRACTOR")

                # Prepare request payload matching the chat format from main.py
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

                # Make synchronous HTTP request to Ollama
                with httpx.Client() as client:
                    response = client.post(
                        self.ollama_url,
                        json=payload,
                        timeout=60.0
                    )

                    if response.status_code != 200:
                        raise Exception(f"Ollama returned status {response.status_code}: {response.text}")

                    # Parse response
                    result = response.json()

                    # Extract the message content from Ollama's response format
                    if "message" in result and "content" in result["message"]:
                        content = result["message"]["content"]
                    else:
                        raise Exception(f"Unexpected response format: {result}")

                    # Parse JSON from the content
                    # Handle cases where LLM might include markdown code blocks
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.startswith("```"):
                        content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()

                    parsed_result = json.loads(content)

                    # Validate the response structure
                    if "clauses" not in parsed_result:
                        raise Exception("Response missing 'clauses' field")

                    if not isinstance(parsed_result["clauses"], list):
                        raise Exception("'clauses' field must be a list")

                    log_success(f"LLM call successful, extracted {len(parsed_result['clauses'])} clauses", "CLAUSE_EXTRACTOR")
                    return parsed_result

            except json.JSONDecodeError as e:
                log_error(f"Failed to parse JSON response: {str(e)}", "CLAUSE_EXTRACTOR")
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    log_info(f"Retrying in {delay} seconds...", "CLAUSE_EXTRACTOR")
                    time.sleep(delay)
                else:
                    raise Exception(f"Failed to parse LLM JSON response after {max_retries} attempts: {str(e)}")

            except httpx.RequestError as e:
                log_error(f"HTTP request error: {str(e)}", "CLAUSE_EXTRACTOR")
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    log_info(f"Retrying in {delay} seconds...", "CLAUSE_EXTRACTOR")
                    time.sleep(delay)
                else:
                    raise Exception(f"Failed to connect to Ollama after {max_retries} attempts: {str(e)}")

            except Exception as e:
                log_error(f"LLM call error: {str(e)}", "CLAUSE_EXTRACTOR")
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    log_info(f"Retrying in {delay} seconds...", "CLAUSE_EXTRACTOR")
                    time.sleep(delay)
                else:
                    raise

        raise Exception(f"Failed to call LLM after {max_retries} attempts")

    def _split_into_chunks(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks for processing large documents

        Args:
            text: The full document text

        Returns:
            List of text chunks with overlap
        """
        if len(text) <= self.max_chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.max_chunk_size

            # If not the last chunk, try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings in the last 500 chars of chunk
                last_period = text[end-500:end].rfind('.')
                last_newline = text[end-500:end].rfind('\n\n')
                break_point = max(last_period, last_newline)

                if break_point != -1:
                    end = end - 500 + break_point + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap for next chunk
            start = end - self.chunk_overlap

        log_info(f"Split document into {len(chunks)} chunks", "CLAUSE_EXTRACTOR")
        return chunks

    def _deduplicate_clauses(self, all_clauses: List[Dict]) -> List[Dict]:
        """
        Deduplicate clauses that may appear in overlapping chunks

        Uses similarity of title and first 200 chars of text to identify duplicates.
        Keeps the clause with more complete text.

        Args:
            all_clauses: List of all extracted clauses (may contain duplicates)

        Returns:
            Deduplicated list of clauses
        """
        if len(all_clauses) <= 1:
            return all_clauses

        unique_clauses = []
        seen_signatures = set()

        # Sort by index to preserve order
        sorted_clauses = sorted(all_clauses, key=lambda c: c.get("index", 0))

        for clause in sorted_clauses:
            # Create signature from title and beginning of text
            title = clause.get("title", "").lower().strip()
            text = clause.get("text", "")
            text_start = text[:200].lower().strip()

            signature = f"{title}||{text_start}"

            # Check if similar clause already exists
            is_duplicate = False
            for existing_sig in seen_signatures:
                existing_title, existing_text_start = existing_sig.split("||", 1)

                # Consider duplicate if title matches and text starts are very similar
                if title == existing_title:
                    # Calculate simple character overlap
                    min_len = min(len(text_start), len(existing_text_start))
                    if min_len > 0:
                        matching_chars = sum(1 for i in range(min_len) if text_start[i] == existing_text_start[i])
                        similarity = matching_chars / min_len

                        if similarity > 0.8:  # 80% character match threshold
                            is_duplicate = True
                            break

            if not is_duplicate:
                unique_clauses.append(clause)
                seen_signatures.add(signature)

        removed_count = len(all_clauses) - len(unique_clauses)
        if removed_count > 0:
            log_info(f"Removed {removed_count} duplicate clauses", "CLAUSE_EXTRACTOR")

        return unique_clauses

    def extract_clauses(self, document_id: str) -> List[Dict]:
        """
        Extract clauses from a document using LLM and store them in the database.
        Handles large documents by processing in chunks with overlap.

        Args:
            document_id: The document ID to extract clauses from

        Returns:
            List of extracted clause dictionaries

        Raises:
            Exception: If extraction fails
        """
        log_info(f"Starting clause extraction for document: {document_id}", "CLAUSE_EXTRACTOR")

        # Get document text
        document_text = self._get_document_text(document_id)
        if not document_text:
            raise Exception(f"Could not retrieve text for document: {document_id}")

        # Split into chunks if document is large
        text_chunks = self._split_into_chunks(document_text)
        log_info(f"Processing {len(text_chunks)} text chunks", "CLAUSE_EXTRACTOR")

        # Extract clauses from each chunk
        all_clauses = []
        clause_index_offset = 0

        for chunk_num, chunk_text in enumerate(text_chunks, 1):
            try:
                log_info(f"Processing chunk {chunk_num}/{len(text_chunks)} ({len(chunk_text)} chars)", "CLAUSE_EXTRACTOR")

                # Prepare prompt for this chunk
                prompt = CLAUSE_EXTRACTION_PROMPT.format(contract_text=chunk_text)

                # Call LLM
                llm_response = self._call_llm(prompt)

                # Extract clauses from response
                chunk_clauses = llm_response.get("clauses", [])

                # Adjust clause indices to account for previous chunks
                for clause in chunk_clauses:
                    clause["index"] = clause.get("index", 0) + clause_index_offset
                    all_clauses.append(clause)

                # Update offset for next chunk
                if chunk_clauses:
                    max_index = max(c.get("index", 0) for c in chunk_clauses)
                    clause_index_offset = max_index

                log_success(f"Extracted {len(chunk_clauses)} clauses from chunk {chunk_num}", "CLAUSE_EXTRACTOR")

            except Exception as e:
                log_error(f"Failed to extract clauses from chunk {chunk_num}: {str(e)}", "CLAUSE_EXTRACTOR")
                # Continue with other chunks even if one fails
                continue

        if not all_clauses:
            log_warning(f"No clauses extracted from document: {document_id}", "CLAUSE_EXTRACTOR")
            return []

        # Deduplicate clauses from overlapping chunks
        unique_clauses = self._deduplicate_clauses(all_clauses)
        log_info(f"Total unique clauses after deduplication: {len(unique_clauses)}", "CLAUSE_EXTRACTOR")

        # Store clauses in database
        conn = self._get_connection()
        cursor = conn.cursor()

        stored_clauses = []

        try:
            for clause in unique_clauses:
                clause_id = str(uuid.uuid4())

                # Validate required fields
                title = clause.get("title", "Untitled Clause")
                clause_type = clause.get("type", "Other")
                text = clause.get("text", "")
                index = clause.get("index", 0)
                terms = clause.get("terms", {})

                # Serialize terms to JSON string
                terms_json = json.dumps(terms)

                # Insert into document_clauses table
                cursor.execute("""
                    INSERT INTO document_clauses (
                        id, document_id, clause_type, clause_title,
                        clause_text, clause_index, extracted_terms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (clause_id, document_id, clause_type, title, text, index, terms_json))

                stored_clauses.append({
                    "id": clause_id,
                    "document_id": document_id,
                    "title": title,
                    "type": clause_type,
                    "text": text,
                    "terms": terms,
                    "index": index
                })

            conn.commit()
            log_success(f"Stored {len(stored_clauses)} clauses for document: {document_id}", "CLAUSE_EXTRACTOR")

        except Exception as e:
            conn.rollback()
            log_error(f"Failed to store clauses: {str(e)}", "CLAUSE_EXTRACTOR")
            raise
        finally:
            conn.close()

        return stored_clauses

    def get_document_clauses(self, document_id: str) -> List[Dict]:
        """
        Retrieve all clauses for a document from the database

        Args:
            document_id: The document ID to retrieve clauses for

        Returns:
            List of clause dictionaries ordered by clause_index
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, document_id, clause_type, clause_title,
                       clause_text, clause_index, extracted_terms
                FROM document_clauses
                WHERE document_id = ?
                ORDER BY clause_index ASC
            """, (document_id,))

            rows = cursor.fetchall()
            conn.close()

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

            log_info(f"Retrieved {len(clauses)} clauses for document: {document_id}", "CLAUSE_EXTRACTOR")
            return clauses

        except Exception as e:
            log_error(f"Failed to retrieve clauses: {str(e)}", "CLAUSE_EXTRACTOR")
            return []
