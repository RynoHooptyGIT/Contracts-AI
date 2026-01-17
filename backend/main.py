import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI(title="Contracts AI Backend")

# CORS setup
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    model: str = "mistral"
    messages: List[Dict[str, str]]
    stream: bool = False

@app.get("/")
async def root():
    return {"message": "Contracts AI Backend Running"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    ollama_url = "http://localhost:11434/api/chat"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                ollama_url,
                json=request.model_dump(),
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"Ollama Error: {response.text}")
            
            return response.json()
            
    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f"Connection error to Ollama: {str(exc)}")
