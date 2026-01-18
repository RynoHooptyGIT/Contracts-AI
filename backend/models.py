from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DocumentUploadResponse(BaseModel):
    processed: int
    failed: int
    documents: List[str]

class DocumentInfo(BaseModel):
    id: str
    filename: str
    file_type: str
    uploaded_at: str
    status: str

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]

class RetrievedChunk(BaseModel):
    text: str
    chunk_index: int
    filename: str
    similarity: float

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

class SearchResponse(BaseModel):
    chunks: List[RetrievedChunk]
