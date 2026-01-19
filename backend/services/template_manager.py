import sqlite3
import uuid
import os
from typing import Dict, List, Optional
from datetime import datetime


class TemplateManager:
    def __init__(self):
        # Database path from environment
        db_path = os.getenv("DATABASE_PATH", "/app/data/documents.db")
        self.db_path = db_path

    def _get_connection(self):
        """Get SQLite database connection"""
        return sqlite3.connect(self.db_path)

    def create_template(self, document_id: str, category: str, notes: str = None) -> Dict:
        """
        Create a new golden template from an existing document.

        Args:
            document_id: ID of the document to use as template
            category: Template category (e.g., "NDAs", "Employment Agreements")
            notes: Optional notes about the template

        Returns:
            Dictionary containing template details

        Raises:
            ValueError: If document does not exist
            Exception: If database operation fails
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Validate document exists
            cursor.execute("SELECT id FROM documents WHERE id = ?", (document_id,))
            if not cursor.fetchone():
                raise ValueError(f"Document with id {document_id} does not exist")

            # Generate unique template ID
            template_id = str(uuid.uuid4())

            # Insert into golden_templates table
            cursor.execute("""
                INSERT INTO golden_templates
                (id, document_id, category, notes, is_approved, is_active)
                VALUES (?, ?, ?, ?, 0, 1)
            """, (template_id, document_id, category, notes))

            conn.commit()

            # Fetch and return the created template
            cursor.execute("""
                SELECT id, document_id, category, notes, is_approved, is_active,
                       approved_by, approved_at, created_at
                FROM golden_templates
                WHERE id = ?
            """, (template_id,))

            row = cursor.fetchone()
            return {
                "id": row[0],
                "document_id": row[1],
                "category": row[2],
                "notes": row[3],
                "is_approved": bool(row[4]),
                "is_active": bool(row[5]),
                "approved_by": row[6],
                "approved_at": row[7],
                "created_at": row[8]
            }

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def approve_template(self, template_id: str, approved_by: str) -> Dict:
        """
        Approve a template and deactivate any other active approved templates for the same category.

        Args:
            template_id: ID of the template to approve
            approved_by: Username or ID of the person approving the template

        Returns:
            Dictionary containing updated template details

        Raises:
            ValueError: If template does not exist
            Exception: If database operation fails
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Get template by ID
            cursor.execute("""
                SELECT id, category
                FROM golden_templates
                WHERE id = ?
            """, (template_id,))

            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Template with id {template_id} does not exist")

            category = result[1]

            # Deactivate any other active approved templates for the same category
            cursor.execute("""
                UPDATE golden_templates
                SET is_active = 0
                WHERE category = ? AND is_approved = 1 AND is_active = 1 AND id != ?
            """, (category, template_id))

            # Update template: is_approved=1, approved_by, approved_at=CURRENT_TIMESTAMP
            cursor.execute("""
                UPDATE golden_templates
                SET is_approved = 1,
                    approved_by = ?,
                    approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (approved_by, template_id))

            conn.commit()

            # Fetch and return the updated template
            cursor.execute("""
                SELECT id, document_id, category, notes, is_approved, is_active,
                       approved_by, approved_at, created_at
                FROM golden_templates
                WHERE id = ?
            """, (template_id,))

            row = cursor.fetchone()
            return {
                "id": row[0],
                "document_id": row[1],
                "category": row[2],
                "notes": row[3],
                "is_approved": bool(row[4]),
                "is_active": bool(row[5]),
                "approved_by": row[6],
                "approved_at": row[7],
                "created_at": row[8]
            }

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_template(self, template_id: str) -> Optional[Dict]:
        """
        Get a template by its ID.

        Args:
            template_id: ID of the template to retrieve

        Returns:
            Dictionary containing template details, or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, document_id, category, notes, is_approved, is_active,
                       approved_by, approved_at, created_at
                FROM golden_templates
                WHERE id = ?
            """, (template_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return {
                "id": row[0],
                "document_id": row[1],
                "category": row[2],
                "notes": row[3],
                "is_approved": bool(row[4]),
                "is_active": bool(row[5]),
                "approved_by": row[6],
                "approved_at": row[7],
                "created_at": row[8]
            }

        except Exception as e:
            raise e
        finally:
            conn.close()

    def get_active_template(self, category: str) -> Optional[Dict]:
        """
        Get the active approved template for a specific category.

        Args:
            category: Template category to search for

        Returns:
            Dictionary containing template details or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, document_id, category, notes, is_approved, is_active,
                       approved_by, approved_at, created_at
                FROM golden_templates
                WHERE category = ? AND is_active = 1 AND is_approved = 1
            """, (category,))

            row = cursor.fetchone()
            if not row:
                return None

            return {
                "id": row[0],
                "document_id": row[1],
                "category": row[2],
                "notes": row[3],
                "is_approved": bool(row[4]),
                "is_active": bool(row[5]),
                "approved_by": row[6],
                "approved_at": row[7],
                "created_at": row[8]
            }

        finally:
            conn.close()

    def list_templates(self, category: str = None, include_inactive: bool = False) -> List[Dict]:
        """
        List templates with optional filtering.

        Args:
            category: Optional category filter
            include_inactive: Whether to include inactive templates (default: False)

        Returns:
            List of template dictionaries ordered by created_at DESC
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Build query with optional filters
            query = """
                SELECT id, document_id, category, notes, is_approved, is_active,
                       approved_by, approved_at, created_at
                FROM golden_templates
                WHERE 1=1
            """
            params = []

            if category is not None:
                query += " AND category = ?"
                params.append(category)

            if not include_inactive:
                query += " AND is_active = 1"

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)

            templates = []
            for row in cursor.fetchall():
                templates.append({
                    "id": row[0],
                    "document_id": row[1],
                    "category": row[2],
                    "notes": row[3],
                    "is_approved": bool(row[4]),
                    "is_active": bool(row[5]),
                    "approved_by": row[6],
                    "approved_at": row[7],
                    "created_at": row[8]
                })

            return templates

        finally:
            conn.close()

    def deactivate_template(self, template_id: str) -> Dict:
        """
        Deactivate a template.

        Args:
            template_id: ID of the template to deactivate

        Returns:
            Dictionary containing updated template details

        Raises:
            ValueError: If template does not exist
            Exception: If database operation fails
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Check if template exists
            cursor.execute("SELECT id FROM golden_templates WHERE id = ?", (template_id,))
            if not cursor.fetchone():
                raise ValueError(f"Template with id {template_id} does not exist")

            # Update template to deactivate
            cursor.execute("""
                UPDATE golden_templates
                SET is_active = 0
                WHERE id = ?
            """, (template_id,))

            conn.commit()

            # Fetch and return the updated template
            cursor.execute("""
                SELECT id, document_id, category, notes, is_approved, is_active,
                       approved_by, approved_at, created_at
                FROM golden_templates
                WHERE id = ?
            """, (template_id,))

            row = cursor.fetchone()
            return {
                "id": row[0],
                "document_id": row[1],
                "category": row[2],
                "notes": row[3],
                "is_approved": bool(row[4]),
                "is_active": bool(row[5]),
                "approved_by": row[6],
                "approved_at": row[7],
                "created_at": row[8]
            }

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_template_usage(self, template_id: str) -> Dict:
        """
        Get usage statistics for a template.

        Args:
            template_id: ID of the template to check

        Returns:
            Dictionary containing template_id and usage_count
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT COUNT(*)
                FROM redlining_sessions
                WHERE template_id = ?
            """, (template_id,))

            count = cursor.fetchone()[0]

            return {
                "template_id": template_id,
                "usage_count": count
            }

        finally:
            conn.close()
