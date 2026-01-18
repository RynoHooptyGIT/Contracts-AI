FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PDF/DOCX parsing and compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download embedding model during build (cache layer for faster rebuilds)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data/documents /app/data/faiss_index

# Expose port
EXPOSE 8001

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
