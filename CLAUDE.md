# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Contracts-AI** is a full-stack AI chat application that provides a conversational interface powered by the Mistral AI model through Ollama. The project uses a monorepo structure with separate frontend and backend implementations.

**Technology Stack**:
- **Frontend**: React 19.2.0 + Vite 7.2.4
- **Backend**: FastAPI (Python) with Uvicorn
- **AI**: Ollama with Mistral model (localhost:11434)

## Development Setup

### Prerequisites

**Critical**: Ollama must be running on `localhost:11434` with the Mistral model available before starting development.

**Backend Requirements**:
- Python 3
- Virtual environment (`backend/venv/`)
- Dependencies from `backend/requirements.txt`

**Frontend Requirements**:
- Node.js and npm
- Dependencies from `frontend/package.json`

### Running the Application

**Backend** (from repository root):
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload --port 8001
```

**Frontend** (from repository root):
```bash
cd frontend
npm run dev      # Start development server (default port 5173)
npm run build    # Create production build
npm run lint     # Run ESLint
npm run preview  # Preview production build locally
```

Both backend and frontend must run simultaneously for the application to work.

## Architecture

### High-Level Data Flow

```
User Input → React Chat UI (port 5173)
    ↓
    POST /api/chat
    ↓
FastAPI Backend (port 8001)
    ↓
    Proxy to Ollama
    ↓
Ollama API (localhost:11434)
    ↓
Response: Ollama → Backend → Frontend → User
```

### Key Architectural Decisions

1. **Stateless Backend**: The FastAPI backend ([backend/main.py](backend/main.py)) is a simple proxy with a single `/api/chat` endpoint. It forwards requests to Ollama and returns responses.

2. **No Persistence**: Chat history is maintained only in frontend state (React useState). There is no database, no session management, and no authentication.

3. **CORS Configuration**: The backend allows all origins (`origins = ["*"]`) for development purposes.

4. **Request Format**: The ChatRequest model expects:
   ```python
   {
     "model": "mistral",  # default model
     "messages": [{"role": "user", "content": "..."}],
     "stream": false
   }
   ```

5. **Simple Frontend**: The entire chat interface is in [frontend/src/App.jsx](frontend/src/App.jsx) using React hooks for state management.

## Critical Files

- [backend/main.py](backend/main.py) - Complete FastAPI backend (51 lines)
- [frontend/src/App.jsx](frontend/src/App.jsx) - Main chat interface component
- [frontend/package.json](frontend/package.json) - Build scripts and dependencies
- [frontend/vite.config.js](frontend/vite.config.js) - Vite bundler configuration
- [backend/requirements.txt](backend/requirements.txt) - Python dependencies

## Development Notes

- **Port Configuration**: Frontend expects backend on port 8001 (hardcoded in App.jsx)
- **No TypeScript**: The project uses plain JavaScript despite React type definitions being available
- **Single Component**: The entire frontend UI is in one component (App.jsx)
- **Virtual Environment**: Backend uses a local venv; activate it before running uvicorn
- **Ollama Dependency**: The application will fail if Ollama is not running or if the Mistral model is not available
