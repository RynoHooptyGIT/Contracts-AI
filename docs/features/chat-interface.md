# Feature: Chat Interface

## Overview

The chat interface provides a conversational UI for interacting with the Mistral AI model through Ollama. Users can send messages and receive AI-generated responses in real-time, with full conversation history displayed in the interface.

## Implementation

### Frontend Changes

- **File**: `frontend/src/App.jsx`
- **Changes**:
  - Message input field with submit functionality
  - Message history display with role-based styling
  - Auto-scroll to latest message
  - Loading state while waiting for responses
  - Error handling for failed requests

### State Management

```javascript
const [messages, setMessages] = useState([]);
const [input, setInput] = useState('');
const [isLoading, setIsLoading] = useState(false);
```

- `messages`: Array of chat messages with `role` and `content`
- `input`: Current text in the input field
- `isLoading`: Boolean indicating if a request is in progress

### Backend Changes

- **File**: `backend/main.py`
- **Endpoint**: `POST /api/chat`
- **Function**: `chat(request: ChatRequest)`
- **Purpose**: Proxies chat requests to Ollama API

## User Experience

### How to Use

1. User opens the application at `http://localhost:5173`
2. User types a message in the input field at the bottom
3. User clicks "Send" button or presses Enter
4. Message appears in the chat history
5. AI response appears below the user's message
6. User can continue the conversation

### UI Layout

```
┌─────────────────────────────────┐
│     Contracts AI Chat           │
├─────────────────────────────────┤
│                                 │
│  User: Hello                    │
│                                 │
│  AI: Hello! How can I help you  │
│      today?                     │
│                                 │
│  User: Tell me about contracts  │
│                                 │
│  AI: [Response about contracts] │
│                                 │
│     ↓ Auto-scrolls to here      │
├─────────────────────────────────┤
│ [Input field: Type message...] │
│                      [Send]     │
└─────────────────────────────────┘
```

## Technical Details

### Message Format

Messages are stored in the following structure:

```javascript
{
  role: "user" | "assistant",
  content: "Message text here"
}
```

### API Integration

The frontend sends requests to the backend:

```javascript
const response = await fetch('http://localhost:8001/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: 'mistral',
    messages: [...allMessages, newUserMessage]
  })
});
```

### Request Flow

```
User Input → State Update → API Call → Backend Proxy → Ollama → Response → State Update → UI Render
```

### Error Handling

```javascript
try {
  // API call
} catch (error) {
  console.error('Error sending message:', error);
  // Error is logged to console
  // TODO: Add user-friendly error display in UI
}
```

## Testing

### Manual Testing Checklist

- [x] Chat interface loads correctly
- [x] User can type in input field
- [x] Clicking Send sends the message
- [x] User message appears in chat history
- [x] AI response appears after user message
- [x] Input field clears after sending
- [x] Chat auto-scrolls to latest message
- [x] Loading state prevents duplicate sends
- [x] Multiple messages can be sent in sequence

### Test Cases

1. **Send First Message**
   - **Input**: "Hello"
   - **Expected**: Message appears, AI responds with greeting
   - **Result**: ✅ Pass

2. **Send Follow-up Message**
   - **Input**: "Tell me more"
   - **Expected**: Context from previous message is maintained
   - **Result**: ✅ Pass

3. **Send Empty Message**
   - **Input**: "" (empty string)
   - **Expected**: Nothing happens, message not sent
   - **Result**: ⚠️ Currently allowed - consider adding validation

4. **Ollama Unavailable**
   - **Setup**: Stop Ollama service
   - **Expected**: Error message displayed to user
   - **Result**: ⚠️ Error logged to console - needs UI feedback

## Dependencies

- **Ollama**: Must be running on `localhost:11434`
- **Model**: Mistral (must be pulled: `ollama pull mistral`)
- **Browser**: Modern browser with ES6+ support
- **Network**: Backend must be accessible on `localhost:8001`

## Configuration

### Port Configuration

Hardcoded in `frontend/src/App.jsx`:
```javascript
const response = await fetch('http://localhost:8001/api/chat', {
  // ...
});
```

To change the backend URL, modify this line.

### Model Selection

Currently fixed to "mistral":
```javascript
body: JSON.stringify({
  model: 'mistral',  // Hardcoded model name
  messages: messages
})
```

## Known Limitations

- No conversation persistence (messages lost on page refresh)
- No export functionality for chat history
- No model selection UI (fixed to Mistral)
- No streaming responses (full response after completion)
- Limited error feedback to user (errors only in console)
- No message editing or deletion
- No file upload support
- No markdown rendering in responses

## Future Enhancements

- [ ] Add local storage to persist chat history
- [ ] Implement export chat history feature
- [ ] Add model selection dropdown (Mistral, Llama2, etc.)
- [ ] Display loading indicator while waiting for response
- [ ] Show user-friendly error messages in UI
- [ ] Add markdown rendering for formatted AI responses
- [ ] Implement streaming for real-time response display
- [ ] Add clear chat button
- [ ] Support message editing
- [ ] Add dark mode toggle

## Related Documentation

- [Chat API Documentation](../api/chat.md)
- [CLAUDE.md Architecture](../../CLAUDE.md#architecture)

---

**Created**: 2026-01-17
**Author**: Contracts-AI Team
**Status**: ✅ Implemented
**Version**: 0.1.0
