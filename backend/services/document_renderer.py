"""
HTML Document Renderer
Converts PDF/DOCX to HTML while preserving formatting
Sanitizes output to prevent XSS attacks
"""

import mammoth
import pdfplumber
from bs4 import BeautifulSoup
import bleach
import uuid
import re
from pathlib import Path

# Allowed HTML tags and attributes (whitelist for security)
ALLOWED_TAGS = [
    'p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br',
    'strong', 'em', 'u', 'ol', 'ul', 'li', 'table', 'tr', 'td', 'th'
]
ALLOWED_ATTRIBUTES = {
    '*': ['class', 'data-clause-id', 'data-clause-type', 'data-clause-index']
}

class DocumentRenderer:
    def __init__(self, db):
        self.db = db

    async def render_to_html(self, document_id: str) -> dict:
        """
        Convert document to HTML with preserved formatting
        Sanitizes HTML to prevent XSS attacks

        Returns:
            {
                "html_content": "<div>...</div>",
                "css_content": "body { font-family: ... }",
                "clause_markers": [{"clause_id": "...", "start": 0, "end": 150}]
            }
        """
        # Check cache first
        cached = self.db.execute(
            "SELECT html_content, css_content FROM rendered_documents WHERE document_id = ?",
            (document_id,)
        ).fetchone()

        if cached:
            return {
                "html_content": cached[0],
                "css_content": cached[1],
                "clause_markers": self._get_clause_markers(document_id)
            }

        # Get document info
        doc = self.db.execute(
            "SELECT filename, filepath FROM documents WHERE id = ?",
            (document_id,)
        ).fetchone()

        if not doc:
            raise ValueError(f"Document not found: {document_id}")

        filename, filepath = doc

        # Convert to HTML based on file type
        if filename.endswith('.docx'):
            html, css = self._convert_docx_to_html(filepath)
        elif filename.endswith('.pdf'):
            html, css = self._convert_pdf_to_html(filepath)
        else:
            raise ValueError(f"Unsupported file type: {filename}")

        # SECURITY: Sanitize HTML to prevent XSS
        html = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)

        # Add clause boundary markers
        html = self._add_clause_markers(document_id, html)

        # Cache result
        cache_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT OR REPLACE INTO rendered_documents (id, document_id, html_content, css_content) VALUES (?, ?, ?, ?)",
            (cache_id, document_id, html, css)
        )
        self.db.commit()

        return {
            "html_content": html,
            "css_content": css,
            "clause_markers": self._get_clause_markers(document_id)
        }

    def _convert_docx_to_html(self, filepath: str) -> tuple[str, str]:
        """Use mammoth library to convert DOCX to HTML"""
        with open(filepath, "rb") as docx_file:
            result = mammoth.convert_to_html(docx_file)
            html = result.value

            # Extract inline styles to separate CSS
            soup = BeautifulSoup(html, 'html.parser')
            css = self._extract_css_from_html(soup)

            return html, css

    def _convert_pdf_to_html(self, filepath: str) -> tuple[str, str]:
        """Use pdfplumber to extract text and structure from PDF"""
        html_parts = []

        with pdfplumber.open(filepath) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract text
                text = page.extract_text()

                if text:
                    # Structure text as HTML paragraphs
                    paragraphs = text.split('\n\n')
                    for para in paragraphs:
                        if para.strip():
                            # Detect headings (all caps or short lines)
                            if self._is_heading(para):
                                html_parts.append(f'<h3>{para.strip()}</h3>')
                            else:
                                html_parts.append(f'<p>{para.strip()}</p>')

        html = f"<div class='document'>{''.join(html_parts)}</div>"
        css = self._generate_default_css()

        return html, css

    def _is_heading(self, text: str) -> bool:
        """Detect if text is likely a heading"""
        # Heuristic: All caps, short length, or ends with colon
        if len(text.strip()) < 100 and (
            text.isupper() or
            text.strip().endswith(':') or
            len(text.split()) <= 5
        ):
            return True
        return False

    def _extract_css_from_html(self, soup: BeautifulSoup) -> str:
        """Extract inline styles and convert to CSS"""
        # Default CSS for DOCX-converted HTML
        css = """
        .document {
            font-family: 'Times New Roman', Times, serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #000;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }
        p {
            margin: 0.5rem 0;
        }
        h1, h2, h3, h4, h5, h6 {
            margin: 1rem 0 0.5rem 0;
            font-weight: bold;
        }
        """
        return css.strip()

    def _generate_default_css(self) -> str:
        """Generate default CSS for PDF-converted HTML"""
        return """
        .document {
            font-family: 'Times New Roman', Times, serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #000;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }
        p {
            margin: 0.75rem 0;
        }
        h3 {
            margin: 1.5rem 0 0.75rem 0;
            font-weight: bold;
            font-size: 14pt;
        }
        """

    def _add_clause_markers(self, document_id: str, html: str) -> str:
        """
        Add data attributes to HTML elements to mark clause boundaries

        Example: <p data-clause-id="clause-123" data-clause-type="Payment" data-clause-index="0">...</p>
        """
        # Get all clauses for this document
        clauses = self.db.execute(
            """SELECT id, clause_type, clause_index, clause_text, start_char, end_char
               FROM document_clauses
               WHERE document_id = ?
               ORDER BY clause_index""",
            (document_id,)
        ).fetchall()

        if not clauses:
            # No clauses extracted yet, return HTML as-is
            return html

        soup = BeautifulSoup(html, 'html.parser')

        # Get all text content to map clauses
        full_text = soup.get_text()

        # For each clause, find the corresponding HTML element(s)
        for clause_id, clause_type, clause_index, clause_text, start_char, end_char in clauses:
            # Find where this clause text appears in the HTML
            clause_text_clean = clause_text.strip()

            # Try to find matching paragraph
            for p in soup.find_all(['p', 'div']):
                p_text = p.get_text().strip()
                if clause_text_clean in p_text or p_text in clause_text_clean:
                    # Add clause markers to this element
                    p['data-clause-id'] = clause_id
                    p['data-clause-type'] = clause_type
                    p['data-clause-index'] = str(clause_index)
                    break

        return str(soup)

    def _get_clause_markers(self, document_id: str) -> list[dict]:
        """Get clause ID and position mappings"""
        clauses = self.db.execute(
            """SELECT id, clause_type, clause_title, start_char, end_char, clause_index
               FROM document_clauses
               WHERE document_id = ?
               ORDER BY clause_index""",
            (document_id,)
        ).fetchall()

        return [
            {
                "clause_id": row[0],
                "clause_type": row[1],
                "clause_title": row[2] or f"Clause {row[5] + 1}",
                "start": row[3],
                "end": row[4],
                "index": row[5]
            }
            for row in clauses
        ]
