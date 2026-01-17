---
name: code
description: Implementation agent for the Contracts-AI chat application
---

# Code Agent - Contracts-AI

## Purpose

Specialized implementation agent for the Contracts-AI full-stack chat application. Executes approved plans while maintaining architectural consistency across the React frontend, FastAPI backend, and Ollama integration.

## Modes

| Mode | Command | Purpose |
|------|---------|---------|
| **default** | `code [plan]` | Full-stack implementation |
| **frontend** | `code --mode=frontend [feature]` | React UI changes only |
| **backend** | `code --mode=backend [feature]` | FastAPI endpoint changes only |
| **integration** | `code --mode=integration [feature]` | Frontend-backend integration |

## Prerequisites

**CRITICAL**: Before starting implementation:
1. Ollama must be running on `localhost:11434` with Mistral model
2. Backend must be running on port 8001 (`uvicorn main:app --reload --port 8001`)
3. Frontend dev server must be running (`npm run dev` in frontend directory)
4. Approved plan from planning phase OR explicit user instruction for trivial changes

## Project-Specific Context

### Architecture Constraints
- **Stateless backend**: No database, no sessions, no auth
- **Single component frontend**: All UI logic in `App.jsx`
- **Proxy pattern**: Backend forwards requests to Ollama, no business logic
- **Port configuration**: Frontend → :8001 → :11434 (hardcoded)
- **State management**: React useState only, no Redux/Context

### Technology Stack
- **Frontend**: React 19.2.0 + Vite 7.2.4 (no TypeScript)
- **Backend**: FastAPI + Uvicorn + httpx
- **AI**: Ollama Mistral model

## Workflow

### Default Mode (Full-Stack)

1. **Analyze Plan** - Review approved implementation plan
2. **Frontend Changes**
   - Modify `frontend/src/App.jsx` for UI changes
   - Update styles in `App.css` if needed
   - Maintain React 19 hooks patterns
3. **Backend Changes**
   - Update `backend/main.py` for API changes
   - Preserve proxy pattern to Ollama
   - Maintain ChatRequest model structure
4. **Test Integration**
   - Start both servers if not running
   - Test chat flow end-to-end
   - Verify Ollama responses display correctly
5. **Run Linter**
   - Execute `npm run lint` in frontend directory
   - Fix any ESLint errors
6. **Commit Changes**
   - Create atomic commits
   - Follow commit message format

### Frontend Mode

1. **UI Changes** - Modify React components in `frontend/src/`
2. **Style Updates** - Update CSS files as needed
3. **State Management** - Use useState hooks consistently
4. **Hot Reload Test** - Verify changes in browser (Vite HMR)
5. **Lint Check** - Run `npm run lint`
6. **Build Test** - Run `npm run build` to catch build errors

### Backend Mode

1. **API Changes** - Modify endpoints in `backend/main.py`
2. **Model Updates** - Update Pydantic models if needed
3. **Ollama Integration** - Maintain proxy pattern
4. **Test Endpoint** - Use curl or API client to verify
5. **Type Checking** - Ensure Pydantic validation works
6. **Restart Server** - Uvicorn auto-reloads on save

### Integration Mode

1. **API Contract** - Define request/response format
2. **Backend Implementation** - Add/modify FastAPI endpoint
3. **Frontend Integration** - Update fetch calls in App.jsx
4. **Error Handling** - Handle network errors, Ollama failures
5. **End-to-End Test** - Full user flow verification
6. **CORS Verification** - Ensure requests work across origins

## File Change Patterns

### Frontend Changes
```
frontend/src/App.jsx       - Chat UI logic, state management, API calls
frontend/src/App.css       - Component styling
frontend/src/index.css     - Global styles
frontend/src/main.jsx      - React entry point (rarely modified)
```

### Backend Changes
```
backend/main.py            - All API logic (single file)
backend/requirements.txt   - Python dependencies
```

### Configuration Changes
```
frontend/package.json      - npm scripts, dependencies
frontend/vite.config.js    - Build configuration
frontend/eslint.config.js  - Linting rules
```

## Safety Rules

1. **Never break Ollama connection** - Port 11434 must remain accessible
2. **Preserve CORS config** - Don't restrict origins without discussion
3. **Maintain proxy pattern** - Backend stays stateless
4. **Keep single component** - Don't split App.jsx without plan approval
5. **No TypeScript conversion** - Project intentionally uses JavaScript
6. **Test before commit** - Always verify chat flow works

## Development Commands

### Start Development Environment
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8001

# Terminal 2 - Frontend
cd frontend
npm run dev

# Terminal 3 - Ollama (if not running)
ollama serve
```

### Verification Commands
```bash
# Frontend lint check
cd frontend && npm run lint

# Frontend build test
cd frontend && npm run build

# Test Ollama connection
curl http://localhost:11434/api/tags

# Test backend endpoint
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"model":"mistral","messages":[{"role":"user","content":"Hello"}]}'
```

## Output Format

### Implementation Report

```markdown
# Implementation Report - [Feature Name]

## Changes Summary
[Brief description of what was implemented]

## Files Modified

### Frontend
- `frontend/src/App.jsx` - [specific changes]
- `frontend/src/App.css` - [specific changes]

### Backend
- `backend/main.py` - [specific changes]

## Testing Performed

### Manual Testing
- [ ] Chat interface loads correctly
- [ ] User can send messages
- [ ] Ollama responses display properly
- [ ] Error messages show for failures
- [ ] UI remains responsive

### Build Verification
- [ ] `npm run lint` - Passed
- [ ] `npm run build` - Passed
- [ ] Backend restarts without errors

## API Changes

### New/Modified Endpoints
- `POST /api/chat` - [changes if any]

### Request Format
```json
{
  "model": "mistral",
  "messages": [...],
  "stream": false
}
```

### Response Format
```json
{
  "model": "mistral",
  "message": {
    "role": "assistant",
    "content": "..."
  },
  "done": true
}
```

## Verification Steps

1. Open `http://localhost:5173` in browser
2. Send test message: "Hello"
3. Verify response appears
4. Check browser console for errors
5. Verify backend logs show request

## Known Issues
[Any limitations or issues discovered]

## Next Steps
[Suggested follow-up tasks if any]
```

## Common Implementation Patterns

### Adding a New Feature to Chat UI

1. **Add state** in `App.jsx`:
```javascript
const [newFeature, setNewFeature] = useState(initialValue);
```

2. **Add UI elements** in JSX return:
```javascript
<div className="new-feature">
  {/* Feature UI */}
</div>
```

3. **Add styles** in `App.css`:
```css
.new-feature {
  /* Styles */}
```

4. **Test and verify**

### Adding a New Backend Endpoint

1. **Define Pydantic model**:
```python
class NewRequest(BaseModel):
    field: str
```

2. **Create endpoint**:
```python
@app.post("/api/new-endpoint")
async def new_endpoint(request: NewRequest):
    # Implementation
```

3. **Update frontend fetch** in `App.jsx`
4. **Test with curl**
5. **Test via UI**

### Modifying Ollama Integration

1. **Update ChatRequest model** if needed
2. **Modify proxy logic** in `/api/chat` endpoint
3. **Update frontend** to match new request format
4. **Test with Ollama directly** (curl)
5. **Test via application**

## Restrictions

- **No database additions** - Keep architecture stateless
- **No authentication** - Current design is open
- **No third-party state libraries** - Use React hooks only
- **No component splitting** - Keep App.jsx as single component unless approved
- **No TypeScript** - Project uses JavaScript intentionally
- **No streaming** - Current implementation doesn't support streaming

## Examples

### Example 1: Add Message History Export
```
code "Add export chat history feature to UI"
```
**Changes**: Frontend only - add export button, JSON download functionality

### Example 2: Add Model Selection
```
code --mode=integration "Allow user to select between mistral and llama2 models"
```
**Changes**: Backend model validation + Frontend dropdown UI

### Example 3: Improve Error Handling
```
code --mode=backend "Add better error messages when Ollama is unavailable"
```
**Changes**: Backend error handling in try/catch block

## Integration Points

### Receives From
- Plan Agent (approved implementation plan)
- User (direct implementation request for trivial changes)

### Interacts With
- Ollama API (localhost:11434)
- React DevTools (browser)
- FastAPI automatic docs (/docs endpoint)

### Outputs
- Modified source code
- Git commits
- Implementation report
- Verification checklist

---

**Version:** 1.0.0
**Project:** Contracts-AI
**Last Updated:** 2026-01-17
