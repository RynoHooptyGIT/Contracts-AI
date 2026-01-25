#!/bin/bash
cd /Users/ryan.hooley@bmcjax.com/Documents/VS\ Projects/Contracts-AI/backend
source venv/bin/activate
export OLLAMA_MODEL="qwen2.5:3b"
export DATABASE_PATH="data/documents.db"
export FAISS_INDEX_PATH="data/faiss_index"
export UPLOAD_DIR="data/documents"
uvicorn main:app --reload --port 8001
