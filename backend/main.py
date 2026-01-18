import os
import httpx
import tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from database import init_database
from services.document_manager import DocumentManager

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
    allow_methods=["POST", "GET", "DELETE"],
    allow_headers=["Content-Type"],
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

@app.on_event("startup")
async def startup_event():
    """Initialize database and document manager on startup"""
    init_database()
    app.state.doc_manager = DocumentManager()

@app.get("/")
async def root():
    return {"message": "Contracts AI Backend Running"}

@app.post("/api/documents/upload")
@limiter.limit("5/minute")
async def upload_documents(request: Request, file: UploadFile = File(...)):
    """Upload ZIP file containing documents for RAG ingestion"""
    # Validate file type
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported")

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # Process ZIP file
    try:
        results = app.state.doc_manager.ingest_zip(tmp_path)
        return {
            "success": True,
            "message": f"Processed {results['processed']} files successfully, {results['failed']} failed",
            "details": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        # Clean up temporary file
        Path(tmp_path).unlink(missing_ok=True)

@app.get("/api/documents")
async def list_documents():
    """Get all uploaded documents"""
    try:
        documents = app.state.doc_manager.list_documents()
        return {
            "success": True,
            "count": len(documents),
            "documents": documents
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@app.delete("/api/documents/{doc_id}")
@limiter.limit("10/minute")
async def delete_document(request: Request, doc_id: str):
    """Delete a document and its associated chunks"""
    try:
        success = app.state.doc_manager.delete_document(doc_id)
        if success:
            return {"success": True, "message": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@app.post("/api/chat")
@limiter.limit("20/minute")
async def chat(request: Request, chat_request: ChatRequest, use_rag: bool = True, top_k: int = 3):
    """Chat endpoint with optional RAG (Retrieval Augmented Generation)"""
    # Get Ollama URL from environment or use default
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")

    # If RAG is enabled, retrieve relevant context
    if use_rag and chat_request.messages:
        try:
            # Get the last user message as the query
            last_message = chat_request.messages[-1].get("content", "")

            if last_message:
                # Search for relevant document chunks
                retrieved_chunks = app.state.doc_manager.search_documents(last_message, top_k)

                # If we found relevant context, augment the prompt
                if retrieved_chunks:
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

        except Exception as e:
            # Log error but don't fail the request - continue without RAG
            print(f"RAG retrieval error: {str(e)}")

    # Call Ollama with (potentially augmented) messages
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                ollama_url,
                json=chat_request.model_dump(),
                timeout=60.0
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"Ollama Error: {response.text}")

            return response.json()

    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f"Connection error to Ollama: {str(exc)}")
