import os
import json
import sqlite3
import httpx
import tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, File, UploadFile
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from database import init_database, migrate_database, migrate_redlining_tables, migrate_visual_annotation_tables
from services.document_manager import DocumentManager
from services.document_parser import parse_file
from logger import log_buffer, log_info, log_success, log_error, log_warning

# Template management services (will be initialized if available)
try:
    from services.template_manager import TemplateManager
    TEMPLATE_MANAGER_AVAILABLE = True
except ImportError:
    TEMPLATE_MANAGER_AVAILABLE = False
    log_warning("TemplateManager not available - template endpoints will return 501", "STARTUP")

try:
    from services.clause_extractor import ClauseExtractor
    CLAUSE_EXTRACTOR_AVAILABLE = True
except ImportError:
    CLAUSE_EXTRACTOR_AVAILABLE = False
    log_warning("ClauseExtractor not available - clause extraction endpoints will return 501", "STARTUP")

try:
    from services.redlining_service import RedliningService
    REDLINING_SERVICE_AVAILABLE = True
except ImportError:
    REDLINING_SERVICE_AVAILABLE = False
    log_warning("RedliningService not available - redlining endpoints will return 501", "STARTUP")

try:
    from services.redlining_service_progressive import ProgressiveRedliningService
    from sse_starlette.sse import EventSourceResponse
    PROGRESSIVE_REDLINING_AVAILABLE = True
except ImportError:
    PROGRESSIVE_REDLINING_AVAILABLE = False
    log_warning("ProgressiveRedliningService not available - progressive redlining endpoints will return 501", "STARTUP")

# Load environment variables
load_dotenv()

app = FastAPI(title="Contracts AI Backend")

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# CORS setup - Use environment variable for allowed origins
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
origins = [origin.strip() for origin in allowed_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods including OPTIONS
    allow_headers=["*"],  # Allow all headers
)

class ChatRequest(BaseModel):
    model: str = "mistral"
    messages: List[Dict[str, str]]
    stream: bool = False

    @validator('messages')
    def validate_messages(cls, v):
        if not v:
            raise ValueError("Messages cannot be empty")
        if len(v) > 100:
            raise ValueError("Too many messages (max 100)")
        for msg in v:
            if 'content' in msg and len(msg['content']) > 10000:
                raise ValueError("Message content too long (max 10000 characters)")
        return v

class CreateTemplateRequest(BaseModel):
    document_id: str
    category: str
    notes: Optional[str] = None

    @validator('document_id')
    def validate_document_id(cls, v):
        if not v or not v.strip():
            raise ValueError("document_id cannot be empty")
        return v.strip()

    @validator('category')
    def validate_category(cls, v):
        if not v or not v.strip():
            raise ValueError("category cannot be empty")
        return v.strip()

class ApproveTemplateRequest(BaseModel):
    approved_by: str

    @validator('approved_by')
    def validate_approved_by(cls, v):
        if not v or not v.strip():
            raise ValueError("approved_by cannot be empty")
        return v.strip()

class StartRedliningRequest(BaseModel):
    document_id: str
    category: Optional[str] = None

    @validator('document_id')
    def validate_document_id(cls, v):
        if not v or not v.strip():
            raise ValueError("document_id cannot be empty")
        return v.strip()

class UpdateChangeActionRequest(BaseModel):
    action: str

    @validator('action')
    def validate_action(cls, v):
        if v not in ['accepted', 'rejected', 'pending']:
            raise ValueError("action must be 'accepted', 'rejected', or 'pending'")
        return v

@app.on_event("startup")
async def startup_event():
    """Initialize database and document manager on startup"""
    log_info("Initializing database schema...", "STARTUP")
    # Run migration first to add new columns to existing tables
    migrate_database()
    # Migrate redlining tables
    migrate_redlining_tables()
    # Migrate visual annotation tables
    migrate_visual_annotation_tables()
    # Then ensure all tables exist
    init_database()
    log_success("Database ready", "STARTUP")

    log_info("Initializing document manager...", "STARTUP")
    app.state.doc_manager = DocumentManager()
    log_success("Document manager ready", "STARTUP")

    # Initialize template manager if available
    if TEMPLATE_MANAGER_AVAILABLE:
        log_info("Initializing template manager...", "STARTUP")
        app.state.template_manager = TemplateManager()
        log_success("Template manager ready", "STARTUP")

    # Initialize clause extractor if available
    if CLAUSE_EXTRACTOR_AVAILABLE:
        log_info("Initializing clause extractor...", "STARTUP")
        app.state.clause_extractor = ClauseExtractor()
        log_success("Clause extractor ready", "STARTUP")

    # Initialize redlining service if available
    if REDLINING_SERVICE_AVAILABLE:
        log_info("Initializing redlining service...", "STARTUP")
        app.state.redlining_service = RedliningService()
        log_success("Redlining service ready", "STARTUP")

    # Initialize progressive redlining service if available
    if PROGRESSIVE_REDLINING_AVAILABLE:
        log_info("Initializing progressive redlining service...", "STARTUP")
        app.state.progressive_redlining_service = ProgressiveRedliningService()
        log_success("Progressive redlining service ready", "STARTUP")

@app.get("/")
async def root():
    return {"message": "Contracts AI Backend Running"}

@app.get("/api/logs")
async def get_logs(count: int = 50):
    """Get recent log messages"""
    try:
        logs = log_buffer.get_recent(count)
        return {"success": True, "logs": logs}
    except Exception as e:
        log_error(f"Failed to retrieve logs: {str(e)}", "LOGS")
        raise HTTPException(status_code=500, detail="Failed to retrieve logs")

@app.get("/api/logs/stream")
async def stream_logs(request: Request):
    """Stream logs using Server-Sent Events"""
    from fastapi.responses import StreamingResponse
    import asyncio
    import json

    async def event_generator():
        last_count = 0
        try:
            log_info("Client connected to log stream", "LOGS")

            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    log_info("Client disconnected from log stream", "LOGS")
                    break

                # Get all logs and send only new ones
                all_logs = log_buffer.get_recent(200)
                current_count = len(all_logs)

                if current_count > last_count:
                    # Send new logs
                    new_logs = all_logs[last_count:]
                    for log_entry in new_logs:
                        yield f"data: {json.dumps(log_entry)}\n\n"
                    last_count = current_count

                await asyncio.sleep(0.5)  # Poll every 500ms
        except Exception as e:
            log_error(f"Log stream error: {str(e)}", "LOGS")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/api/documents/upload")
@limiter.limit("30/minute")
async def upload_documents(request: Request, file: UploadFile = File(...)):
    """Upload ZIP file (batch) or individual document (PDF/DOCX/TXT) for RAG ingestion"""
    log_info(f"Received upload request: {file.filename}", "UPLOAD")

    # Determine file type
    filename_lower = file.filename.lower()
    is_zip = filename_lower.endswith('.zip')
    is_single_doc = filename_lower.endswith(('.pdf', '.docx', '.txt'))

    if not (is_zip or is_single_doc):
        log_warning(f"Rejected unsupported file type: {file.filename}", "UPLOAD")
        raise HTTPException(status_code=400, detail="Only ZIP, PDF, DOCX, and TXT files are supported")

    # Read file content
    content = await file.read()

    # Handle ZIP file (batch upload)
    if is_zip:
        log_info(f"Processing ZIP file: {file.filename}", "UPLOAD")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            results = app.state.doc_manager.ingest_zip(tmp_path)
            log_success(f"Processed {results['processed']} files, {results['failed']} failed", "UPLOAD")
            return {
                "success": True,
                "message": f"Processed {results['processed']} files successfully, {results['failed']} failed",
                "details": results
            }
        except Exception as e:
            log_error(f"ZIP processing failed: {str(e)}", "UPLOAD")
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
        finally:
            Path(tmp_path).unlink(missing_ok=True)
            log_info("Cleaned up temporary ZIP file", "UPLOAD")

    # Handle single document file
    else:
        log_info(f"Processing single document: {file.filename}", "UPLOAD")
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            doc_id = app.state.doc_manager.process_file(tmp_path)
            log_success(f"Processed document: {file.filename}", "UPLOAD")
            return {
                "success": True,
                "message": f"Document uploaded successfully",
                "details": {
                    "processed": 1,
                    "failed": 0,
                    "documents": [{
                        "id": doc_id,
                        "filename": file.filename,
                        "file_type": suffix
                    }]
                }
            }
        except Exception as e:
            log_error(f"Document processing failed: {str(e)}", "UPLOAD")
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
        finally:
            Path(tmp_path).unlink(missing_ok=True)
            log_info("Cleaned up temporary file", "UPLOAD")

@app.get("/api/documents")
async def list_documents():
    """Get all uploaded documents"""
    try:
        log_info("Fetching document list", "DOCUMENTS")
        documents = app.state.doc_manager.list_documents()
        log_success(f"Retrieved {len(documents)} documents", "DOCUMENTS")
        return {
            "success": True,
            "count": len(documents),
            "documents": documents
        }
    except Exception as e:
        log_error(f"Failed to list documents: {str(e)}", "DOCUMENTS")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@app.get("/api/documents/metrics")
async def get_metrics():
    """Get document database metrics"""
    try:
        log_info("Fetching system metrics", "METRICS")
        metrics = app.state.doc_manager.get_metrics()
        log_success("Metrics retrieved successfully", "METRICS")
        return metrics
    except Exception as e:
        log_error(f"Failed to get metrics: {str(e)}", "METRICS")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@app.delete("/api/documents/{doc_id}")
@limiter.limit("10/minute")
async def delete_document(request: Request, doc_id: str):
    """Delete a document and its associated chunks"""
    try:
        log_info(f"Deleting document: {doc_id}", "DOCUMENTS")
        success = app.state.doc_manager.delete_document(doc_id)
        if success:
            log_success(f"Document deleted: {doc_id}", "DOCUMENTS")
            return {"success": True, "message": "Document deleted successfully"}
        else:
            log_warning(f"Document not found: {doc_id}", "DOCUMENTS")
            raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Failed to delete document {doc_id}: {str(e)}", "DOCUMENTS")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@app.get("/api/documents/insights")
async def get_insights():
    """Get comprehensive insights for Document Insights Panel"""
    try:
        log_info("Fetching document insights", "INSIGHTS")
        insights = app.state.doc_manager.get_insights()
        log_success("Insights retrieved successfully", "INSIGHTS")
        return insights
    except Exception as e:
        log_error(f"Failed to get insights: {str(e)}", "INSIGHTS")
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")

@app.post("/api/documents/compliance-check")
@limiter.limit("5/minute")
async def compliance_check(request: Request, file: UploadFile = File(...)):
    """Upload a contract for compliance checking against existing documents"""
    log_info(f"Received compliance check request: {file.filename}", "COMPLIANCE")

    # Validate file type (PDF, DOCX, TXT only)
    allowed_extensions = ['.pdf', '.docx', '.txt', '.md']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        log_warning(f"Rejected file type: {file.filename}", "COMPLIANCE")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Save uploaded file temporarily
    log_info(f"Saving uploaded file for compliance check: {file.filename}", "COMPLIANCE")
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # Parse and check compliance
    try:
        log_info(f"Parsing contract: {file.filename}", "COMPLIANCE")
        contract_text = parse_file(tmp_path)

        log_info("Running compliance check", "COMPLIANCE")
        compliance_report = app.state.doc_manager.check_compliance(contract_text)
        log_success(
            f"Compliance check complete: {compliance_report['compliance_score']}",
            "COMPLIANCE"
        )

        return {
            "success": True,
            "filename": file.filename,
            **compliance_report
        }
    except Exception as e:
        log_error(f"Compliance check failed: {str(e)}", "COMPLIANCE")
        raise HTTPException(status_code=500, detail=f"Compliance check failed: {str(e)}")
    finally:
        # Clean up temporary file
        Path(tmp_path).unlink(missing_ok=True)
        log_info("Cleaned up temporary file", "COMPLIANCE")

@app.post("/api/documents/categorize-all")
@limiter.limit("1/hour")
async def categorize_all(request: Request):
    """Admin endpoint to categorize all documents (expensive operation)"""
    try:
        log_info("Starting batch categorization of all documents", "CATEGORIZE")
        results = app.state.doc_manager.categorize_all_documents()
        log_success(
            f"Categorization complete: {results['categorized']} success, {results['failed']} failed",
            "CATEGORIZE"
        )
        return {
            "success": True,
            "message": "Categorization completed",
            **results
        }
    except Exception as e:
        log_error(f"Batch categorization failed: {str(e)}", "CATEGORIZE")
        raise HTTPException(status_code=500, detail=f"Categorization failed: {str(e)}")

@app.get("/api/documents/search-history")
async def get_search_history(limit: int = 10):
    """Get popular/recent search queries for suggested questions"""
    try:
        log_info(f"Fetching search history (limit: {limit})", "HISTORY")
        history = app.state.doc_manager.get_search_history(limit)
        log_success(f"Retrieved {len(history)} search queries", "HISTORY")
        return {
            "success": True,
            "queries": history
        }
    except Exception as e:
        log_error(f"Failed to get search history: {str(e)}", "HISTORY")
        raise HTTPException(status_code=500, detail=f"Failed to get search history: {str(e)}")

@app.post("/api/templates/create")
@limiter.limit("20/minute")
async def create_template(request: Request, template_request: CreateTemplateRequest):
    """Create a new template from an existing document"""
    if not TEMPLATE_MANAGER_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Template management service not available. Please ensure template_manager.py is implemented."
        )

    try:
        log_info(
            f"Creating template from document {template_request.document_id} (category: {template_request.category})",
            "TEMPLATES"
        )
        template = app.state.template_manager.create_template(
            document_id=template_request.document_id,
            category=template_request.category,
            notes=template_request.notes
        )
        log_success(f"Template created: {template.get('id', 'unknown')}", "TEMPLATES")
        return {
            "success": True,
            "template": template
        }
    except ValueError as e:
        log_warning(f"Invalid template creation request: {str(e)}", "TEMPLATES")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Failed to create template: {str(e)}", "TEMPLATES")
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")

@app.post("/api/templates/{template_id}/approve")
@limiter.limit("20/minute")
async def approve_template(request: Request, template_id: str, approve_request: ApproveTemplateRequest):
    """Approve a template for use"""
    if not TEMPLATE_MANAGER_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Template management service not available. Please ensure template_manager.py is implemented."
        )

    try:
        log_info(f"Approving template {template_id} by {approve_request.approved_by}", "TEMPLATES")
        template = app.state.template_manager.approve_template(
            template_id=template_id,
            approved_by=approve_request.approved_by
        )
        if not template:
            log_warning(f"Template not found: {template_id}", "TEMPLATES")
            raise HTTPException(status_code=404, detail="Template not found")
        log_success(f"Template approved: {template_id}", "TEMPLATES")
        return {
            "success": True,
            "template": template
        }
    except HTTPException:
        raise
    except ValueError as e:
        log_warning(f"Invalid template approval request: {str(e)}", "TEMPLATES")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Failed to approve template {template_id}: {str(e)}", "TEMPLATES")
        raise HTTPException(status_code=500, detail=f"Failed to approve template: {str(e)}")

@app.get("/api/templates")
async def list_templates(category: Optional[str] = None, include_inactive: bool = False):
    """List all templates with optional filtering"""
    if not TEMPLATE_MANAGER_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Template management service not available. Please ensure template_manager.py is implemented."
        )

    try:
        log_info(
            f"Listing templates (category: {category or 'all'}, include_inactive: {include_inactive})",
            "TEMPLATES"
        )
        templates = app.state.template_manager.list_templates(
            category=category,
            include_inactive=include_inactive
        )
        log_success(f"Retrieved {len(templates)} templates", "TEMPLATES")
        return {
            "success": True,
            "count": len(templates),
            "templates": templates
        }
    except Exception as e:
        log_error(f"Failed to list templates: {str(e)}", "TEMPLATES")
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")

@app.get("/api/templates/{template_id}")
async def get_template(template_id: str):
    """Get a specific template by ID with usage statistics"""
    if not TEMPLATE_MANAGER_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Template management service not available. Please ensure template_manager.py is implemented."
        )

    try:
        log_info(f"Fetching template: {template_id}", "TEMPLATES")
        template = app.state.template_manager.get_template(template_id)
        if not template:
            log_warning(f"Template not found: {template_id}", "TEMPLATES")
            raise HTTPException(status_code=404, detail="Template not found")

        # Get usage statistics
        try:
            usage = app.state.template_manager.get_template_usage(template_id)
            template['usage'] = usage
        except Exception as usage_err:
            log_warning(f"Failed to get usage stats for template {template_id}: {str(usage_err)}", "TEMPLATES")
            template['usage'] = None

        log_success(f"Retrieved template: {template_id}", "TEMPLATES")
        return {
            "success": True,
            "template": template
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Failed to get template {template_id}: {str(e)}", "TEMPLATES")
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")

@app.delete("/api/templates/{template_id}")
@limiter.limit("20/minute")
async def delete_template(request: Request, template_id: str):
    """Deactivate a template (soft delete)"""
    if not TEMPLATE_MANAGER_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Template management service not available. Please ensure template_manager.py is implemented."
        )

    try:
        log_info(f"Deactivating template: {template_id}", "TEMPLATES")
        success = app.state.template_manager.deactivate_template(template_id)
        if not success:
            log_warning(f"Template not found: {template_id}", "TEMPLATES")
            raise HTTPException(status_code=404, detail="Template not found")
        log_success(f"Template deactivated: {template_id}", "TEMPLATES")
        return {
            "success": True,
            "message": "Template deactivated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Failed to deactivate template {template_id}: {str(e)}", "TEMPLATES")
        raise HTTPException(status_code=500, detail=f"Failed to deactivate template: {str(e)}")

@app.post("/api/documents/{document_id}/extract-clauses")
@limiter.limit("20/minute")
async def extract_clauses(request: Request, document_id: str):
    """Extract clauses from a document"""
    if not CLAUSE_EXTRACTOR_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Clause extraction service not available. Please ensure clause_extractor.py is implemented."
        )

    try:
        log_info(f"Extracting clauses from document: {document_id}", "CLAUSES")
        clauses = app.state.clause_extractor.extract_clauses(document_id)
        log_success(f"Extracted {len(clauses)} clauses from document {document_id}", "CLAUSES")
        return {
            "success": True,
            "document_id": document_id,
            "clause_count": len(clauses),
            "clauses": clauses
        }
    except ValueError as e:
        log_warning(f"Invalid clause extraction request: {str(e)}", "CLAUSES")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Failed to extract clauses from document {document_id}: {str(e)}", "CLAUSES")
        raise HTTPException(status_code=500, detail=f"Failed to extract clauses: {str(e)}")

@app.get("/api/documents/{document_id}")
async def get_document_info(document_id: str):
    """Get document metadata by ID"""
    try:
        conn = sqlite3.connect(os.getenv("DATABASE_PATH", "/app/data/documents.db"))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, filename, filepath, file_type, uploaded_at, category
            FROM documents
            WHERE id = ?
        """, (document_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "id": row[0],
            "filename": row[1],
            "filepath": row[2],
            "file_type": row[3],
            "uploaded_at": row[4],
            "category": row[5]
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Failed to fetch document {document_id}: {str(e)}", "DOCUMENTS")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{document_id}/render-html")
@limiter.limit("30/minute")
async def render_document_html(request: Request, document_id: str):
    """
    Render document as HTML with preserved formatting and clause markers
    Sanitizes HTML to prevent XSS attacks
    """
    try:
        log_info(f"Rendering document {document_id} to HTML", "RENDERER")

        # Import DocumentRenderer here to avoid startup errors if service not available
        from services.document_renderer import DocumentRenderer

        # Get database connection from DocumentManager
        db_conn = app.state.doc_manager._get_connection()
        renderer = DocumentRenderer(db_conn)
        result = await renderer.render_to_html(document_id)

        log_success(f"Rendered document {document_id} successfully", "RENDERER")
        return {
            "success": True,
            "document_id": document_id,
            "html_content": result["html_content"],
            "css_content": result["css_content"],
            "clause_markers": result["clause_markers"]
        }
    except ValueError as e:
        log_warning(f"Invalid document render request: {str(e)}", "RENDERER")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Failed to render document {document_id}: {str(e)}", "RENDERER")
        raise HTTPException(status_code=500, detail=f"Failed to render document: {str(e)}")

# ==================== Redlining Session Endpoints ====================

@app.post("/api/redlining/start")
@limiter.limit("10/minute")
async def start_redlining_session(request: Request, redlining_request: StartRedliningRequest):
    """Start a new redlining session for an uploaded contract"""
    if not REDLINING_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Redlining service not available. Please ensure redlining_service.py is implemented."
        )

    try:
        log_info(
            f"Starting redlining session for document {redlining_request.document_id} (category: {redlining_request.category})",
            "REDLINING"
        )
        result = app.state.redlining_service.start_redlining_session(
            document_id=redlining_request.document_id,
            category=redlining_request.category
        )
        log_success(f"Redlining session created: {result.get('session_id', 'unknown')}", "REDLINING")
        return {
            "success": True,
            **result
        }
    except ValueError as e:
        log_warning(f"Invalid redlining request: {str(e)}", "REDLINING")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Failed to start redlining session: {str(e)}", "REDLINING")
        raise HTTPException(status_code=500, detail=f"Failed to start redlining session: {str(e)}")

@app.post("/api/redlining/start-progressive")
@limiter.limit("10/minute")
async def start_progressive_redlining(request: Request, redlining_request: StartRedliningRequest):
    """
    Start progressive redlining session - returns immediately with session_id
    Analysis happens in background and streams via SSE endpoint
    """
    if not PROGRESSIVE_REDLINING_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Progressive redlining service not available. Please ensure sse-starlette is installed."
        )

    try:
        log_info(
            f"Starting progressive redlining for document {redlining_request.document_id} (category: {redlining_request.category})",
            "PROGRESSIVE_REDLINING"
        )

        # Start session (returns immediately)
        result = await app.state.progressive_redlining_service.start_progressive_session(
            document_id=redlining_request.document_id,
            category=redlining_request.category
        )

        log_success(f"Progressive session created: {result.get('session_id', 'unknown')}", "PROGRESSIVE_REDLINING")

        return {
            "success": True,
            **result
        }

    except ValueError as e:
        log_warning(f"Invalid progressive redlining request: {str(e)}", "PROGRESSIVE_REDLINING")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Failed to start progressive redlining: {str(e)}", "PROGRESSIVE_REDLINING")
        raise HTTPException(status_code=500, detail=f"Failed to start progressive redlining: {str(e)}")

@app.get("/api/redlining/session/{session_id}/stream")
async def stream_redlining_progress(session_id: str):
    """
    Server-Sent Events (SSE) stream for progressive clause analysis
    Streams events as each clause is compared in real-time
    """
    if not PROGRESSIVE_REDLINING_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Progressive redlining service not available. Please ensure sse-starlette is installed."
        )

    async def event_generator():
        """Generate SSE events from progressive analysis"""
        try:
            log_info(f"Starting SSE stream for session: {session_id}", "PROGRESSIVE_REDLINING")

            # Get session info
            session = app.state.progressive_redlining_service.get_session(session_id)
            if not session:
                yield {
                    "event": "error",
                    "data": json.dumps({"message": "Session not found"})
                }
                return

            document_id = session["uploaded_document_id"]
            template_document_id = session.get("template_id")

            # Handle "no_template" status
            if session["status"] == "no_template":
                yield {
                    "event": "error",
                    "data": json.dumps({"message": "No template found for session"})
                }
                return

            # Get template document ID from template_id if needed
            if not template_document_id:
                yield {
                    "event": "error",
                    "data": json.dumps({"message": "No template document found"})
                }
                return

            # For now, we need to get the template document ID from the template
            # This is a bit of a hack - we should store template_document_id in session
            # But for MVP, we'll fetch it from the database
            conn = sqlite3.connect(os.getenv("DATABASE_PATH", "/app/data/documents.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT document_id FROM golden_templates WHERE id = ?", (template_document_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                yield {
                    "event": "error",
                    "data": json.dumps({"message": "Template document not found"})
                }
                return

            template_doc_id = row[0]

            # Stream progressive analysis
            log_info(f"Streaming analysis for document {document_id} vs template {template_doc_id}", "PROGRESSIVE_REDLINING")
            async for event in app.state.progressive_redlining_service.analyze_progressive(
                session_id, document_id, template_doc_id
            ):
                yield {
                    "event": event["event"],
                    "data": json.dumps(event["data"])
                }

            log_success(f"SSE stream completed for session: {session_id}", "PROGRESSIVE_REDLINING")

        except Exception as e:
            log_error(f"SSE stream error: {str(e)}", "PROGRESSIVE_REDLINING")
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)})
            }

    return EventSourceResponse(event_generator())

@app.get("/api/redlining/session/{session_id}")
async def get_redlining_session(session_id: str):
    """Get redlining session details with full comparison results"""
    if not REDLINING_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Redlining service not available. Please ensure redlining_service.py is implemented."
        )

    try:
        log_info(f"Fetching redlining session: {session_id}", "REDLINING")
        session = app.state.redlining_service.get_session(session_id)
        if not session:
            log_warning(f"Redlining session not found: {session_id}", "REDLINING")
            raise HTTPException(status_code=404, detail="Session not found")
        log_success(f"Retrieved redlining session: {session_id}", "REDLINING")
        return {
            "success": True,
            "session": session
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Failed to get redlining session {session_id}: {str(e)}", "REDLINING")
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")

@app.get("/api/redlining/session/{session_id}/comparisons")
async def get_session_comparisons(session_id: str):
    """Get all clause comparisons for a redlining session"""
    if not REDLINING_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Redlining service not available. Please ensure redlining_service.py is implemented."
        )

    try:
        log_info(f"Fetching comparisons for session: {session_id}", "REDLINING")
        comparisons = app.state.redlining_service.get_session_comparisons(session_id)
        log_success(f"Retrieved {len(comparisons)} comparisons for session {session_id}", "REDLINING")
        return {
            "success": True,
            "session_id": session_id,
            "comparison_count": len(comparisons),
            "comparisons": comparisons
        }
    except Exception as e:
        log_error(f"Failed to get comparisons for session {session_id}: {str(e)}", "REDLINING")
        raise HTTPException(status_code=500, detail=f"Failed to get comparisons: {str(e)}")

@app.get("/api/redlining/session/{session_id}/individual-changes")
async def get_session_individual_changes(session_id: str):
    """Get all individual text-level changes for a redlining session"""
    if not REDLINING_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Redlining service not available. Please ensure redlining_service.py is implemented."
        )

    try:
        log_info(f"Fetching individual changes for session: {session_id}", "REDLINING")

        # Query annotation_changes table joined with clause_comparisons
        db_conn = app.state.doc_manager._get_connection()
        cursor = db_conn.cursor()

        cursor.execute("""
            SELECT ac.id, ac.comparison_id, ac.change_type, ac.original_text,
                   ac.suggested_text, ac.start_offset, ac.end_offset,
                   ac.risk_level, ac.rationale, ac.user_action,
                   cc.comparison_type, cc.new_clause_id, cc.template_clause_id
            FROM annotation_changes ac
            JOIN clause_comparisons cc ON ac.comparison_id = cc.id
            WHERE cc.session_id = ?
            ORDER BY cc.comparison_type, ac.risk_level DESC
        """, (session_id,))

        rows = cursor.fetchall()
        db_conn.close()

        changes = []
        for row in rows:
            changes.append({
                "id": row[0],
                "comparison_id": row[1],
                "change_type": row[2],
                "original_text": row[3],
                "suggested_text": row[4],
                "start_offset": row[5],
                "end_offset": row[6],
                "risk_level": row[7],
                "rationale": row[8],
                "user_action": row[9],
                "clause_comparison_type": row[10],
                "new_clause_id": row[11],
                "template_clause_id": row[12]
            })

        log_success(f"Retrieved {len(changes)} individual changes for session {session_id}", "REDLINING")
        return {
            "success": True,
            "session_id": session_id,
            "change_count": len(changes),
            "changes": changes
        }
    except Exception as e:
        log_error(f"Failed to get individual changes for session {session_id}: {str(e)}", "REDLINING")
        raise HTTPException(status_code=500, detail=f"Failed to get changes: {str(e)}")

@app.patch("/api/redlining/changes/{change_id}/action")
@limiter.limit("100/minute")
async def update_change_action(request: Request, change_id: str, action_request: UpdateChangeActionRequest):
    """
    Update user action on an individual change

    Args:
        change_id: The annotation change ID
        action_request: Contains 'action' field ('accepted', 'rejected', or 'pending')

    Returns:
        Updated change object
    """
    try:
        log_info(f"Updating change {change_id} action to: {action_request.action}", "REDLINING")

        # Update the annotation_changes table
        db_conn = app.state.doc_manager._get_connection()
        cursor = db_conn.cursor()

        # First, verify the change exists
        cursor.execute("SELECT id FROM annotation_changes WHERE id = ?", (change_id,))
        if not cursor.fetchone():
            db_conn.close()
            log_warning(f"Change not found: {change_id}", "REDLINING")
            raise HTTPException(status_code=404, detail="Change not found")

        # Update the user_action field
        cursor.execute("""
            UPDATE annotation_changes
            SET user_action = ?
            WHERE id = ?
        """, (action_request.action, change_id))

        db_conn.commit()

        # Fetch the updated change
        cursor.execute("""
            SELECT id, comparison_id, change_type, original_text,
                   suggested_text, start_offset, end_offset,
                   risk_level, rationale, user_action
            FROM annotation_changes
            WHERE id = ?
        """, (change_id,))

        row = cursor.fetchone()
        db_conn.close()

        if not row:
            log_error(f"Change not found after update: {change_id}", "REDLINING")
            raise HTTPException(status_code=500, detail="Failed to retrieve updated change")

        updated_change = {
            "id": row[0],
            "comparison_id": row[1],
            "change_type": row[2],
            "original_text": row[3],
            "suggested_text": row[4],
            "start_offset": row[5],
            "end_offset": row[6],
            "risk_level": row[7],
            "rationale": row[8],
            "user_action": row[9]
        }

        log_success(f"Updated change {change_id} action to {action_request.action}", "REDLINING")
        return {
            "success": True,
            "change": updated_change
        }

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Failed to update change action: {str(e)}", "REDLINING")
        raise HTTPException(status_code=500, detail=f"Failed to update change: {str(e)}")

@app.post("/api/redlining/session/{session_id}/export")
@limiter.limit("10/minute")
async def export_redlined_document(request: Request, session_id: str):
    """
    Export redlined document as DOCX with track changes

    Returns: DOCX file download with accepted/rejected changes
    """
    try:
        log_info(f"Starting DOCX export for session: {session_id}", "REDLINING")

        from services.docx_exporter import DocxExporter

        # Initialize exporter
        db_path = os.getenv("DATABASE_PATH", "/app/data/documents.db")
        exporter = DocxExporter(db_path=db_path)

        # Generate DOCX with track changes
        docx_bytes = exporter.export_with_track_changes(session_id)

        # Generate filename
        filename = exporter.get_export_filename(session_id)

        log_success(f"DOCX export completed for session {session_id}", "REDLINING")

        # Return as downloadable file
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except ValueError as e:
        log_warning(f"Session not found for export: {session_id}", "REDLINING")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log_error(f"Failed to export DOCX for session {session_id}: {str(e)}", "REDLINING")
        raise HTTPException(status_code=500, detail=f"Failed to export document: {str(e)}")

@app.delete("/api/redlining/session/{session_id}")
@limiter.limit("10/minute")
async def delete_redlining_session(request: Request, session_id: str):
    """Delete a redlining session and all associated data"""
    if not REDLINING_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Redlining service not available. Please ensure redlining_service.py is implemented."
        )

    try:
        log_info(f"Deleting redlining session: {session_id}", "REDLINING")
        success = app.state.redlining_service.delete_session(session_id)
        if not success:
            log_warning(f"Redlining session not found: {session_id}", "REDLINING")
            raise HTTPException(status_code=404, detail="Session not found")
        log_success(f"Redlining session deleted: {session_id}", "REDLINING")
        return {
            "success": True,
            "message": "Session deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Failed to delete redlining session {session_id}: {str(e)}", "REDLINING")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

@app.post("/api/chat")
@limiter.limit("20/minute")
async def chat(request: Request, chat_request: ChatRequest, use_rag: bool = True, top_k: int = 3):
    """Chat endpoint with optional RAG (Retrieval Augmented Generation)"""
    log_info(f"Chat request received (RAG: {use_rag})", "CHAT")

    # Get Ollama URL from environment or use default
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")

    # If RAG is enabled, retrieve relevant context
    if use_rag and chat_request.messages:
        try:
            # Get the last user message as the query
            last_message = chat_request.messages[-1].get("content", "")

            if last_message:
                log_info(f"Searching documents for: {last_message[:50]}...", "RAG")
                # Search for relevant document chunks
                retrieved_chunks = app.state.doc_manager.search_documents(last_message, top_k)

                # Log query to query_history for analytics
                try:
                    app.state.doc_manager.log_query(
                        query=last_message,
                        result_count=len(retrieved_chunks),
                        used_rag=True
                    )
                except Exception as log_err:
                    log_warning(f"Failed to log query: {str(log_err)}", "RAG")

                # If we found relevant context, augment the prompt
                if retrieved_chunks:
                    log_success(f"Found {len(retrieved_chunks)} relevant chunks", "RAG")
                    # Build context string from retrieved chunks
                    context = "\n\n".join([
                        f"[From {chunk['filename']}]\n{chunk['text']}"
                        for chunk in retrieved_chunks
                    ])

                    # Create system prompt with context
                    system_prompt = f"""You are a helpful assistant specializing in contract analysis. Answer the user's question using the following context from uploaded documents.

CONTEXT FROM DOCUMENTS:
{context}

INSTRUCTIONS:
- Answer based primarily on the provided context
- If the context doesn't contain relevant information, say so and provide a general answer if appropriate
- Cite which document(s) you're referencing in your answer
- Be precise and reference specific details from the documents"""

                    # Add system prompt to the beginning of messages
                    chat_request.messages.insert(0, {"role": "system", "content": system_prompt})
                else:
                    log_warning("No relevant documents found for query", "RAG")

        except Exception as e:
            # Log error but don't fail the request - continue without RAG
            log_error(f"RAG retrieval error: {str(e)}", "RAG")

    # Call Ollama with (potentially augmented) messages
    try:
        log_info("Sending request to Ollama", "CHAT")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                ollama_url,
                json=chat_request.model_dump(),
                timeout=180.0  # 3 minutes for CPU-based inference with RAG
            )

            if response.status_code != 200:
                log_error(f"Ollama error: {response.status_code}", "CHAT")
                raise HTTPException(status_code=response.status_code, detail=f"Ollama Error: {response.text}")

            log_success("Response received from Ollama", "CHAT")
            return response.json()

    except httpx.RequestError as exc:
        log_error(f"Ollama connection error: {str(exc)}", "CHAT")
        raise HTTPException(status_code=500, detail=f"Connection error to Ollama: {str(exc)}")
