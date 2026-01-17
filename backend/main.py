import os
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Dict, Any
from dotenv import load_dotenv
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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
    allow_methods=["POST", "GET"],
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

@app.get("/")
async def root():
    return {"message": "Contracts AI Backend Running"}

@app.post("/api/chat")
@limiter.limit("20/minute")
async def chat(request: Request, chat_request: ChatRequest):
    ollama_url = "http://localhost:11434/api/chat"

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
