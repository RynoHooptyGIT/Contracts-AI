# Contracts-AI

> AI-powered contract analysis system with RAG (Retrieval Augmented Generation), Docker containerization, and Ollama Mistral integration.

[![GitHub](https://img.shields.io/github/license/RynoHooptyGIT/Contracts-AI)](LICENSE)
[![React](https://img.shields.io/badge/React-19.2.0-blue)](https://react.dev())
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Mistral-orange)](https://ollama.ai/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)](https://www.docker.com/)

## Overview

Contracts-AI is a full-stack AI application that combines conversational AI with document-based question answering. Using RAG (Retrieval Augmented Generation), the system can analyze uploaded contracts and provide accurate, context-aware responses based on actual document content. The entire stack is containerized with Docker for easy deployment.

## Features

- 🚀 **RAG System** - Upload documents and ask questions based on their content
- 📄 **Multi-Format Support** - Process TXT, MD, PDF, and DOCX files
- 🔍 **Semantic Search** - FAISS vector similarity search for relevant context retrieval
- 🐳 **Docker Containerization** - Complete multi-container architecture
- 💬 **Real-time Chat Interface** - Interactive chat with AI-powered responses
- 🤖 **Mistral AI Integration** - Powered by Ollama's Mistral model
- ⚡ **Fast & Modern Stack** - React 19 + Vite + FastAPI
- 🔒 **Production-Ready Security** - Rate limiting, input validation, security headers
- 📚 **Comprehensive Documentation** - Auto-generated docs with pre-commit validation
- 🛠️ **Developer-Friendly** - Hot reload, ESLint, and automated workflows

## Tech Stack

### Frontend
- **React 19.2.0** - Modern UI library
- **Vite 7.2.4** - Next-generation build tool
- **Nginx** - Production web server
- **ESLint** - Code quality enforcement

### Backend
- **FastAPI** - High-performance Python web framework
- **Uvicorn** - ASGI server
- **httpx** - Async HTTP client
- **Pydantic** - Data validation
- **SQLite** - Document metadata storage

### RAG (Retrieval Augmented Generation)
- **Sentence-Transformers** - all-MiniLM-L6-v2 embedding model (384 dimensions)
- **FAISS** - Facebook AI Similarity Search for vector operations
- **PyPDF2** - PDF document parsing
- **python-docx** - Word document parsing

### AI
- **Ollama** - Local LLM inference
- **Mistral** - Open-source AI model

### Infrastructure
- **Docker** - Containerization
- **docker-compose** - Multi-container orchestration

## Prerequisites

Before running this application, ensure you have:

- **Docker** and **docker-compose** installed
- That's it! All other dependencies are containerized.

### Install Docker

```bash
# macOS
brew install --cask docker

# Or download from https://www.docker.com/products/docker-desktop
```

## Quick Start (Docker - Recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/RynoHooptyGIT/Contracts-AI.git
cd Contracts-AI
```

### 2. Build and Start Containers

```bash
# Build all containers (first time only)
docker-compose build

# Start all services (backend, frontend, ollama)
docker-compose up
```

### 3. Pull Mistral Model

In a new terminal, pull the Mistral model into the Ollama container:

```bash
docker exec contracts-ai-ollama ollama pull mistral
```

### 4. Open Application

Navigate to `http://localhost:5173` in your browser.

### 5. Upload Documents (Optional)

1. Click "📁 Manage Documents" in the header
2. Upload a ZIP file containing your contracts (TXT, MD, PDF, DOCX)
3. Wait for processing to complete
4. Enable "Use Document Context (RAG)" checkbox
5. Ask questions about your documents!

### Stopping the Application

```bash
docker-compose down          # Stop containers
docker-compose down -v       # Stop and remove volumes (clean slate)
```

## Local Development (Without Docker)

For local development without Docker:

<details>
<summary>Click to expand local setup instructions</summary>

### Prerequisites
- **Node.js** (v18 or higher)
- **Python 3** (v3.11 or higher)
- **Ollama** installed and running locally

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Start backend
uvicorn main:app --reload --port 8001
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Start Ollama

```bash
# macOS
brew install ollama
ollama serve

# Pull Mistral model
ollama pull mistral
```

</details>

## Development

### Project Structure

```
Contracts-AI/
├── backend/                      # FastAPI backend
│   ├── main.py                  # Main application file
│   ├── database.py              # SQLite schema & connection
│   ├── models.py                # Pydantic models for RAG
│   ├── services/                # RAG services
│   │   ├── document_parser.py   # File parsing & chunking
│   │   ├── embedding_service.py # Sentence-Transformers embeddings
│   │   ├── vector_store.py      # FAISS vector operations
│   │   └── document_manager.py  # Ingestion orchestration
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Backend container config
│   └── .env.example             # Environment template
├── frontend/                    # React frontend
│   ├── src/
│   │   ├── App.jsx              # Main chat component
│   │   ├── App.css              # Component styles
│   │   ├── components/          # React components
│   │   │   ├── DocumentUpload.jsx    # ZIP upload UI
│   │   │   ├── DocumentUpload.css
│   │   │   ├── DocumentList.jsx      # Document grid view
│   │   │   └── DocumentList.css
│   │   └── main.jsx             # React entry point
│   ├── package.json             # Node dependencies
│   ├── nginx.conf               # Nginx configuration
│   ├── Dockerfile               # Frontend container config
│   └── vite.config.js           # Vite configuration
├── docs/                        # Documentation
│   ├── api/                     # API endpoint docs
│   ├── features/                # Feature documentation
│   ├── guides/                  # Development guides
│   └── templates/               # Doc templates
├── .claude/                     # Claude Code agents
│   ├── agents/                  # Agent specifications
│   └── hooks/                   # Git hooks
├── docker-compose.yml           # Multi-container orchestration
├── CLAUDE.md                    # AI agent guidance
├── CHANGELOG.md                 # Version history
└── README.md                    # This file
```

### Available Scripts

**Docker** (Recommended):
```bash
docker-compose build              # Build all containers
docker-compose up                 # Start all services
docker-compose up -d              # Start in detached mode
docker-compose down               # Stop containers
docker-compose down -v            # Stop and remove volumes
docker-compose logs -f backend    # View backend logs
docker-compose logs -f frontend   # View frontend logs
docker exec -it contracts-ai-backend /bin/bash   # Access backend shell
```

**Frontend** (Local Development):
```bash
npm run dev      # Start development server
npm run build    # Create production build
npm run lint     # Run ESLint
npm run preview  # Preview production build
```

**Backend** (Local Development):
```bash
uvicorn main:app --reload --port 8001  # Start with auto-reload
```

### Documentation System

This project includes an automated documentation system that runs before every commit:

```bash
# Install pre-commit hook (one-time setup)
cp .claude/hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

The hook automatically:
- Validates documentation completeness
- Checks for missing CHANGELOG entries
- Creates documentation structure
- Reminds about code comments

See [Documentation Workflow Guide](docs/guides/documentation-workflow.md) for details.

## Architecture

### High-Level Data Flow

**Document Ingestion (RAG Pipeline)**:
```
User uploads ZIP → Frontend (5173)
    ↓
POST /api/documents/upload
    ↓
Backend extracts & processes (8001)
    ↓
Parse files (TXT/MD/PDF/DOCX)
    ↓
Chunk text (500 words, 50 overlap)
    ↓
Generate embeddings (Sentence-Transformers)
    ↓
Store in FAISS + SQLite
```

**Chat with RAG**:
```
User question → Frontend (5173)
    ↓
POST /api/chat?use_rag=true
    ↓
Backend (8001):
  1. Generate query embedding
  2. Search FAISS for top-K similar chunks
  3. Build augmented prompt with context
  4. Send to Ollama (11434)
    ↓
Mistral generates response
    ↓
Response → Backend → Frontend → User
```

**Docker Architecture**:
```
┌─────────────────────────────────────────────┐
│          contracts-ai-network (bridge)       │
│                                             │
│  ┌──────────────┐  ┌──────────────┐        │
│  │   Frontend   │  │   Backend    │        │
│  │  (React)     │  │  (FastAPI)   │        │
│  │  Port: 5173  │  │  Port: 8001  │        │
│  └──────────────┘  └──────────────┘        │
│         │                  │                │
│         └─────────┬────────┘                │
│                   │                         │
│            ┌──────────────┐                 │
│            │   Ollama     │                 │
│            │  (Mistral)   │                 │
│            │  Port: 11434 │                 │
│            └──────────────┘                 │
│                                             │
│  Volumes:                                   │
│  • backend_data (docs, SQLite, FAISS)       │
│  • ollama_models (Mistral model)            │
└─────────────────────────────────────────────┘
```

### Key Architectural Decisions

- **Stateless Backend**: All state persisted in Docker volumes
- **RAG Pattern**: Vector similarity search augments LLM prompts with document context
- **Singleton Embedding Model**: Loaded once on startup, reused for all embeddings
- **Containerization**: Full Docker isolation for reproducibility
- **React State**: Uses `useState` hooks for UI state management
- **Document Storage**: SQLite for metadata, FAISS for vectors, filesystem for raw files
- **Error Resilience**: RAG failures gracefully degrade to standard chat

For detailed architecture information, see [CLAUDE.md](CLAUDE.md).

## API Documentation

### POST /api/chat

Send a chat message and receive AI response (with optional RAG).

**Query Parameters**:
- `use_rag` (boolean, default: true) - Enable RAG context retrieval
- `top_k` (integer, default: 3) - Number of document chunks to retrieve

**Request**:
```json
{
  "model": "mistral",
  "messages": [
    {"role": "user", "content": "What are the payment terms?"}
  ],
  "stream": false
}
```

**Response**:
```json
{
  "model": "mistral",
  "message": {
    "role": "assistant",
    "content": "Based on the uploaded contract..."
  },
  "done": true
}
```

### POST /api/documents/upload

Upload a ZIP file containing documents for RAG ingestion.

**Rate Limit**: 5 requests/minute

**Request**:
- Content-Type: `multipart/form-data`
- Body: ZIP file

**Response**:
```json
{
  "success": true,
  "message": "Processed 5 files successfully, 0 failed",
  "details": {
    "processed": 5,
    "failed": 0,
    "documents": [
      {"id": "uuid", "filename": "contract.pdf", "file_type": ".pdf"}
    ]
  }
}
```

### GET /api/documents

List all uploaded documents.

**Response**:
```json
{
  "success": true,
  "count": 5,
  "documents": [
    {
      "id": "uuid",
      "filename": "contract.pdf",
      "file_type": ".pdf",
      "file_size": 1024000,
      "uploaded_at": "2026-01-17T12:00:00",
      "status": "indexed"
    }
  ]
}
```

### DELETE /api/documents/{doc_id}

Delete a document and its associated chunks.

**Rate Limit**: 10 requests/minute

**Response**:
```json
{
  "success": true,
  "message": "Document deleted successfully"
}
```

See [API Documentation](docs/api/) for complete details.

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - AI agent guidance and project overview
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes
- **[Documentation Guide](docs/guides/documentation-workflow.md)** - How to document features
- **[API Reference](docs/api/)** - API endpoint documentation
- **[Feature Docs](docs/features/)** - Feature documentation

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Update documentation (templates in `docs/templates/`)
5. Update `CHANGELOG.md`
6. Commit your changes (pre-commit hook will validate)
7. Push to your branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Troubleshooting

### Ollama Connection Error

**Error**: `Connection error to Ollama: [Errno 61] Connection refused`

**Solution**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve

# Verify Mistral model is available
ollama list | grep mistral
```

### Frontend Can't Connect to Backend

**Error**: Network error when sending messages

**Solution**:
- Ensure backend is running on port 8001
- Check browser console for CORS errors
- Verify fetch URL in `App.jsx` matches backend port

### ESLint Errors

**Solution**:
```bash
cd frontend
npm run lint
```

Fix any reported issues or update `.eslintrc` if needed.

## Roadmap

### Completed ✅
- [x] Add rate limiting (production) - v0.2.0
- [x] Docker containerization - v0.3.0
- [x] RAG system with document upload - v0.3.0
- [x] Security headers and input validation - v0.2.0

### In Progress 🚧
- [ ] Add markdown rendering for AI responses
- [ ] Display streaming responses in real-time
- [ ] Implement dark mode

### Planned 📋
- [ ] Add chat history persistence (local storage)
- [ ] Implement message export functionality
- [ ] Add model selection UI (switch between models)
- [ ] Document preview/view endpoint
- [ ] Semantic chunking (beyond word count)
- [ ] Support for more file types (CSV, JSON, HTML)
- [ ] Citation tracking in responses
- [ ] Hybrid search (keyword + semantic)
- [ ] Add authentication (production)
- [ ] Deploy to cloud platform (AWS ECS / Google Cloud Run)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Ollama](https://ollama.ai/) - Local LLM inference platform
- [Mistral AI](https://mistral.ai/) - Open-source AI model
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [Vite](https://vitejs.dev/) - Build tool

## Support

For issues, questions, or suggestions:
- Open an [issue](https://github.com/RynoHooptyGIT/Contracts-AI/issues)
- See [documentation](docs/)
- Check [CLAUDE.md](CLAUDE.md) for development guidance

---

**Built with ❤️ using React, FastAPI, and Ollama**

Co-Authored-By: Claude Sonnet 4.5
