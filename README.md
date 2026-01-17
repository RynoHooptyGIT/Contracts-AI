# Contracts-AI

> AI-powered chat application using React, FastAPI, and Ollama Mistral for intelligent contract assistance.

[![GitHub](https://img.shields.io/github/license/RynoHooptyGIT/Contracts-AI)](LICENSE)
[![React](https://img.shields.io/badge/React-19.2.0-blue)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Mistral-orange)](https://ollama.ai/)

## Overview

Contracts-AI is a full-stack AI chat application that provides a conversational interface powered by the Mistral AI model through Ollama. The application features a clean React frontend and a FastAPI backend that proxies requests to a local Ollama instance.

## Features

- 💬 **Real-time Chat Interface** - Interactive chat with AI-powered responses
- 🤖 **Mistral AI Integration** - Powered by Ollama's Mistral model
- ⚡ **Fast & Modern Stack** - React 19 + Vite for lightning-fast development
- 🔄 **Stateless Architecture** - Simple proxy pattern for reliable performance
- 📚 **Comprehensive Documentation** - Auto-generated docs with pre-commit validation
- 🛠️ **Developer-Friendly** - Hot reload, ESLint, and automated workflows

## Tech Stack

### Frontend
- **React 19.2.0** - Modern UI library
- **Vite 7.2.4** - Next-generation build tool
- **ESLint** - Code quality enforcement

### Backend
- **FastAPI** - High-performance Python web framework
- **Uvicorn** - ASGI server
- **httpx** - Async HTTP client
- **Pydantic** - Data validation

### AI
- **Ollama** - Local LLM inference
- **Mistral** - Open-source AI model

## Prerequisites

Before running this application, ensure you have:

- **Node.js** (v18 or higher)
- **Python 3** (v3.8 or higher)
- **Ollama** installed and running
- **Mistral model** pulled in Ollama

### Install Ollama and Mistral

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama service
ollama serve

# Pull Mistral model (in a new terminal)
ollama pull mistral
```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/RynoHooptyGIT/Contracts-AI.git
cd Contracts-AI
```

### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server (port 8001)
uvicorn main:app --reload --port 8001
```

### 3. Setup Frontend

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start development server (port 5173)
npm run dev
```

### 4. Open Application

Navigate to `http://localhost:5173` in your browser and start chatting!

## Development

### Project Structure

```
Contracts-AI/
├── backend/                # FastAPI backend
│   ├── main.py            # Main application file
│   ├── requirements.txt   # Python dependencies
│   └── venv/              # Virtual environment
├── frontend/              # React frontend
│   ├── src/
│   │   ├── App.jsx        # Main chat component
│   │   ├── App.css        # Component styles
│   │   └── main.jsx       # React entry point
│   ├── package.json       # Node dependencies
│   └── vite.config.js     # Vite configuration
├── docs/                  # Documentation
│   ├── api/               # API endpoint docs
│   ├── features/          # Feature documentation
│   ├── guides/            # Development guides
│   └── templates/         # Doc templates
├── .claude/               # Claude Code agents
│   ├── agents/            # Agent specifications
│   └── hooks/             # Git hooks
├── CLAUDE.md              # AI agent guidance
├── CHANGELOG.md           # Version history
└── README.md              # This file
```

### Available Scripts

**Frontend**:
```bash
npm run dev      # Start development server
npm run build    # Create production build
npm run lint     # Run ESLint
npm run preview  # Preview production build
```

**Backend**:
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

```
User Input → React Frontend (5173)
    ↓
    POST /api/chat
    ↓
FastAPI Backend (8001)
    ↓
    Proxy to Ollama
    ↓
Ollama API (11434) → Mistral Model
    ↓
Response: Ollama → Backend → Frontend → User
```

### Key Architectural Decisions

- **Stateless Backend**: No database, sessions, or authentication
- **Proxy Pattern**: Backend simply forwards requests to Ollama
- **Single Component**: All UI logic in `App.jsx` for simplicity
- **React State**: Uses `useState` hooks, no external state management
- **Port Configuration**: Frontend → :8001 → :11434 (hardcoded)

For detailed architecture information, see [CLAUDE.md](CLAUDE.md).

## API Documentation

### POST /api/chat

Send a chat message and receive AI response.

**Request**:
```json
{
  "model": "mistral",
  "messages": [
    {"role": "user", "content": "Hello!"}
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
    "content": "Hello! How can I help you today?"
  },
  "done": true
}
```

See [API Documentation](docs/api/chat.md) for complete details.

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

- [ ] Add chat history persistence (local storage)
- [ ] Implement message export functionality
- [ ] Add model selection UI (switch between models)
- [ ] Display streaming responses in real-time
- [ ] Add markdown rendering for AI responses
- [ ] Implement dark mode
- [ ] Add authentication (production)
- [ ] Add rate limiting (production)
- [ ] Deploy to cloud platform

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
