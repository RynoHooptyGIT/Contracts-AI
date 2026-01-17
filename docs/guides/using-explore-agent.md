# Using the Explore Agent

Complete guide to using the Explore Agent for codebase exploration, debugging, and code search in Contracts-AI.

## Overview

The Explore Agent is a read-only analysis tool that helps you:
- 🔍 **Understand** how features work
- 🐛 **Debug** issues with root cause analysis
- 🔎 **Search** code semantically
- 📊 **Trace** data flow through the application
- 🔌 **Explore** API endpoints and integrations

## Quick Start

### Basic Exploration

```bash
explore "chat interface"
```

This will analyze the chat interface and provide:
- Component overview
- State management details
- Event handlers
- API integration points

### Debug an Issue

```bash
explore --mode=debug "messages not appearing"
```

The agent will:
- Trace the execution path
- Identify where the failure occurs
- Provide root cause analysis
- Recommend a fix approach

### Search for Code

```bash
explore --mode=search "error handling"
```

Returns all error handling code with:
- File locations and line numbers
- Code snippets with context
- Pattern analysis

### Trace Data Flow

```bash
explore --mode=flow "message submission"
```

Provides complete trace from:
- User action (button click)
- Through frontend processing
- Via backend proxy
- To Ollama and back

## Modes Explained

### 1. Default Mode (General Exploration)

**Purpose**: Understand how something works

**When to Use**:
- Learning the codebase
- Understanding a feature
- Onboarding new developers
- Planning changes

**Example Queries**:
```bash
explore "authentication flow"          # When auth is added
explore "chat interface"               # Understand main feature
explore "Ollama integration"           # Learn how AI works
explore "state management"             # Understand React state
```

**Output Includes**:
- File structure and organization
- Key components and functions
- Data flow diagrams
- Code patterns used
- Potential issues

### 2. Debug Mode

**Purpose**: Find and fix bugs

**When to Use**:
- Something is broken
- Need root cause analysis
- Investigating errors
- Reproducing issues

**Example Queries**:
```bash
explore --mode=debug "messages not sending"
explore --mode=debug "Ollama connection fails"
explore --mode=debug "input not clearing"
explore --mode=debug "chat history disappears"
```

**Output Includes**:
- Issue description
- Root cause with evidence
- Code references (file:line)
- Recommended fix
- Test plan

### 3. Search Mode

**Purpose**: Find code by semantic description

**When to Use**:
- Looking for specific functionality
- Don't know exact file/function name
- Finding all instances of a pattern
- Code review

**Example Queries**:
```bash
explore --mode=search "API calls"
explore --mode=search "error handling"
explore --mode=search "state updates"
explore --mode=search "fetch requests"
```

**Output Includes**:
- Ranked matches
- Code snippets with context
- File and line numbers
- Pattern analysis
- Related code

### 4. Flow Mode

**Purpose**: Trace data through the application

**When to Use**:
- Understanding end-to-end flow
- Debugging complex interactions
- Learning architecture
- Documenting features

**Example Queries**:
```bash
explore --mode=flow "message submission"
explore --mode=flow "error handling"
explore --mode=flow "state management during chat"
```

**Output Includes**:
- Step-by-step trace
- Visual flow diagram
- State changes
- Code references
- Potential bottlenecks

### 5. API Mode

**Purpose**: Explore API endpoints

**When to Use**:
- Understanding backend integration
- Debugging API issues
- Documenting endpoints
- Planning API changes

**Example Queries**:
```bash
explore --mode=api "/api/chat"
explore --mode=api "Ollama proxy"
explore --mode=api "CORS configuration"
```

**Output Includes**:
- Endpoint details
- Request/response models
- Integration points
- Error handling
- Frontend usage

## Real-World Examples

### Example 1: Understanding the Chat Feature

**Scenario**: New developer wants to understand how chat works

**Command**:
```bash
explore "chat interface"
```

**Expected Output**:
```markdown
# Exploration Report: Chat Interface

## Scope Analyzed
- Frontend: frontend/src/App.jsx
- Backend: backend/main.py

## Key Findings

### Component Overview
**File**: `frontend/src/App.jsx` (Lines 1-120)
- **Purpose**: Main chat UI with message history and input
- **State**:
  - messages: Array of chat messages
  - input: Current input field value
  - isLoading: Boolean for request state
- **Functions**:
  - handleSubmit(): Sends message to backend
  - Message rendering in JSX

### Data Flow
```
User types message
    ↓ input state updated
User clicks Send
    ↓ handleSubmit() called
    ↓ API POST to /api/chat
Backend receives request
    ↓ Validates with Pydantic
    ↓ Proxies to Ollama
Ollama generates response
    ↓ Returns to backend
    ↓ Returns to frontend
Frontend updates messages state
    ↓ UI re-renders
```

### Recommendations
- Consider adding loading indicator in UI
- Add retry logic for failed requests
- Persist chat history to local storage
```

### Example 2: Debugging Message Not Clearing

**Scenario**: Bug where input field doesn't clear after sending

**Command**:
```bash
explore --mode=debug "input not clearing after send"
```

**Expected Output**:
```markdown
# Debug Report: Input Not Clearing After Send

## Issue Description
Input field retains user's message after clicking Send instead of clearing.

## Root Cause
**File**: `frontend/src/App.jsx` (Line 52)
**Cause**: setInput('') is called before the fetch completes, but there's a potential race condition or missing await.

## Evidence Trail

### Step 1: handleSubmit Function
**File**: `frontend/src/App.jsx:45-70`
```javascript
const handleSubmit = async () => {
  if (!input.trim()) return;

  setIsLoading(true);
  setInput('');  // ← Clears input immediately

  // ... API call
}
```

**Analysis**: The setInput('') is called correctly, but check if there's re-rendering issue.

## Recommended Fix
Check if input state is being reset elsewhere or if there's a controlled input issue.

### Test Plan
1. Add console.log before and after setInput('')
2. Verify input prop is bound correctly: value={input}
3. Check onChange handler updates state properly
```

### Example 3: Finding Error Handling

**Scenario**: Need to review all error handling in the app

**Command**:
```bash
explore --mode=search "error handling"
```

**Expected Output**:
```markdown
# Search Results: Error Handling

## Matches Found: 3

### 1. Frontend API Error Handling
**File**: `frontend/src/App.jsx`
**Lines**: 55-57
**Relevance**: High

```javascript
} catch (error) {
  console.error('Error sending message:', error);
}
```

**Context**: Catches API call failures but only logs to console. No user-facing error message.

### 2. Backend Ollama Connection Error
**File**: `backend/main.py`
**Lines**: 49-50
**Relevance**: High

```python
except httpx.RequestError as exc:
    raise HTTPException(status_code=500, detail=f"Connection error to Ollama: {str(exc)}")
```

**Context**: Returns 500 error when Ollama is unavailable.

### 3. Backend Response Error
**File**: `backend/main.py`
**Lines**: 44-45
**Relevance**: High

```python
if response.status_code != 200:
    raise HTTPException(status_code=response.status_code, detail=f"Ollama Error: {response.text}")
```

**Context**: Handles non-200 responses from Ollama.

## Pattern Analysis
- Frontend: try/catch with console.error
- Backend: HTTPException with descriptive messages
- Missing: User-facing error messages in frontend
```

### Example 4: Tracing Message Flow

**Scenario**: Want to understand complete message flow

**Command**:
```bash
explore --mode=flow "message from input to response"
```

**Expected Output**:
```markdown
# Data Flow Trace: Message Submission

## Flow Overview
Complete journey of a user message from input field to AI response display.

## Detailed Trace

### 1. User Types Message
**Location**: `frontend/src/App.jsx:80`
```javascript
<input value={input} onChange={(e) => setInput(e.target.value)} />
```
**State Change**: `input` state updates on every keystroke

### 2. User Clicks Send
**Location**: `frontend/src/App.jsx:85`
```javascript
<button onClick={handleSubmit}>Send</button>
```
**Trigger**: handleSubmit function executes

### 3. Input Cleared & Loading Set
**Location**: `frontend/src/App.jsx:46-47`
```javascript
setIsLoading(true);
setInput('');
```
**State Changes**:
- `isLoading`: false → true
- `input`: "message" → ""

[... continues with full trace ...]

## Flow Diagram
[Visual diagram of complete flow]

## State Changes Summary
1. input: "" → "message" → ""
2. isLoading: false → true → false
3. messages: [...old] → [...old, user, ai]
```

## Common Use Cases

### Onboarding
```bash
# Get overview of entire application
explore "application architecture"

# Understand specific features
explore "chat interface"
explore "backend API"
```

### Bug Fixing
```bash
# Debug specific issue
explore --mode=debug "messages not sending"
explore --mode=debug "Ollama connection fails"

# Find related code
explore --mode=search "message handling"
```

### Feature Development
```bash
# Understand existing patterns
explore --mode=flow "message submission"

# Find integration points
explore --mode=api "/api/chat"

# Check for similar code
explore --mode=search "state management"
```

### Code Review
```bash
# Check error handling
explore --mode=search "error handling"

# Review API endpoints
explore --mode=api "/api/chat"

# Understand data flow
explore --mode=flow "chat feature"
```

## Tips for Best Results

### 1. Be Specific
❌ Bad: `explore "code"`
✅ Good: `explore "message handling in chat interface"`

### 2. Use Appropriate Mode
- Understanding → default mode
- Bug fixing → debug mode
- Finding code → search mode
- Tracing execution → flow mode

### 3. Start Broad, Then Narrow
```bash
# First, get overview
explore "chat feature"

# Then, dig deeper
explore --mode=flow "message submission"

# Finally, specific details
explore --mode=api "/api/chat"
```

### 4. Combine with Other Agents

```bash
# 1. Explore to understand
explore "chat interface"

# 2. Plan changes
# (Use plan agent)

# 3. Implement
# (Use code agent)

# 4. Document
# (Documentation agent runs automatically)
```

## Output Interpretation

### Understanding Exploration Reports

**File References**:
- `frontend/src/App.jsx:45` = File path + line number
- `backend/main.py:32-50` = File path + line range

**Code Snippets**:
- Always include surrounding context
- Line numbers match actual file
- Highlights relevant portions

**Flow Diagrams**:
- Show execution order top to bottom
- Include file:line references
- Note state changes

**Recommendations**:
- Potential improvements
- Issues to address
- Areas needing attention

## Troubleshooting

### Explore Agent Not Finding Code

**Problem**: Search returns no results

**Solutions**:
- Check spelling of search terms
- Use broader search terms
- Try different mode (search vs default)
- Verify files exist in repository

### Unclear Output

**Problem**: Report doesn't answer your question

**Solutions**:
- Rephrase query more specifically
- Try different exploration mode
- Break into smaller queries
- Ask for specific file or function

### Too Much Information

**Problem**: Report is overwhelming

**Solutions**:
- Narrow scope of query
- Focus on specific file or function
- Use search mode for targeted results
- Review summary sections first

## Advanced Techniques

### Combining Modes

```bash
# First, search for functionality
explore --mode=search "error handling"

# Then, trace how it works
explore --mode=flow "error handling"

# Finally, debug if issues found
explore --mode=debug "error not showing to user"
```

### Using with Git

```bash
# Explore recent changes
git log --oneline -10
explore "changes in last commit"

# Understand specific commit
git show abc123
explore --mode=debug "issue from commit abc123"
```

### Documentation Reference

After exploration, create documentation:
```bash
# Explore the feature
explore "export chat history"

# Document findings
cp docs/templates/FEATURE_TEMPLATE.md docs/features/export.md
# Fill in based on exploration results
```

## Next Steps

After using the explore agent:

1. **For Learning**: Review the generated report and code references
2. **For Debugging**: Use recommended fix approach with code agent
3. **For Planning**: Create implementation plan based on findings
4. **For Documentation**: Update docs with discovered information

## See Also

- [Explore Agent Specification](../../.claude/agents/explore.md)
- [Code Agent Guide](../../.claude/agents/code.md)
- [Documentation Agent](../../.claude/agents/documentation.md)
- [CLAUDE.md](../../CLAUDE.md)

---

**Last Updated**: 2026-01-17
