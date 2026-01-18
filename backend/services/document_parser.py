from pathlib import Path
from typing import List
import PyPDF2
from docx import Document

def parse_file(filepath: str) -> str:
    """Extract text from file based on extension"""
    path = Path(filepath)
    ext = path.suffix.lower()

    if ext in ['.txt', '.md']:
        return path.read_text(encoding='utf-8', errors='ignore')

    elif ext == '.pdf':
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return '\n\n'.join(page.extract_text() for page in reader.pages)

    elif ext == '.docx':
        doc = Document(filepath)
        return '\n\n'.join(paragraph.text for paragraph in doc.paragraphs)

    else:
        raise ValueError(f"Unsupported file type: {ext}")

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks by word count"""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks if chunks else [text]  # Return original if no chunks created
