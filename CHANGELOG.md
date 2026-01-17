# Changelog

All notable changes to the Contracts-AI project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup with React 19.2.0 frontend and FastAPI backend
- Ollama Mistral integration for AI chat functionality
- Chat interface with message history display
- Real-time message streaming from Ollama
- CLAUDE.md for AI agent guidance
- Documentation agent for pre-commit documentation validation
- Code agent specification for implementation workflows
- Pre-commit hooks for documentation consistency
- Documentation templates for features and API endpoints

### Changed

### Fixed

### Removed

### Security

---

## [0.1.0] - 2025-01-15

### Added
- Initial release
- Basic chat functionality with Mistral model
- Frontend: React + Vite development environment
- Backend: FastAPI with CORS support
- Proxy pattern to forward requests to local Ollama instance

### Technical Details
- Frontend runs on port 5173 (Vite default)
- Backend runs on port 8001
- Ollama required on localhost:11434

---

## Template for New Entries

```markdown
## [Version] - YYYY-MM-DD

### Added
- New feature description ([#issue-number] if applicable)

### Changed
- Changed functionality description

### Fixed
- Bug fix description ([#issue-number] if applicable)

### Removed
- Removed functionality description

### Security
- Security-related changes
```

---

**Note**: This changelog is automatically checked by the documentation agent before commits.
Update this file whenever you make notable changes to the project.
