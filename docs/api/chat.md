# API: Chat Endpoint

## Endpoint

```
POST /api/chat
```

## Description

The chat endpoint proxies conversation requests to the local Ollama instance. It accepts a conversation history and returns the AI model's response. This endpoint maintains no state - all conversation context must be provided in each request.

## Authentication

**Required**: No (current implementation has no authentication)

## Request

### Headers

```
Content-Type: application/json
```

### Body Schema

```json
{
  "model": "string - AI model name (default: mistral)",
  "messages": "array - Conversation history with role and content",
  "stream": "boolean - Enable streaming responses (default: false)"
}
```

### Pydantic Model

```python
class ChatRequest(BaseModel):
    model: str = "mistral"
    messages: List[Dict[str, str]]
    stream: bool = False
```

### Example Request

```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "messages": [
      {"role": "user", "content": "Hello!"},
      {"role": "assistant", "content": "Hello! How can I help you?"},
      {"role": "user", "content": "What is a contract?"}
    ],
    "stream": false
  }'
```

## Response

### Success Response (200 OK)

```json
{
  "model": "mistral",
  "created_at": "2026-01-17T12:00:00.000000Z",
  "message": {
    "role": "assistant",
    "content": "A contract is a legally binding agreement between two or more parties..."
  },
  "done": true,
  "total_duration": 1500000000,
  "load_duration": 100000000,
  "prompt_eval_count": 25,
  "prompt_eval_duration": 400000000,
  "eval_count": 150,
  "eval_duration": 1000000000
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | Model that generated the response |
| `created_at` | string | ISO timestamp of response creation |
| `message` | object | Response message with role and content |
| `message.role` | string | Always "assistant" |
| `message.content` | string | AI-generated response text |
| `done` | boolean | Whether generation is complete |
| `total_duration` | number | Total time in nanoseconds |
| `load_duration` | number | Model load time in nanoseconds |
| `prompt_eval_count` | number | Number of tokens in prompt |
| `prompt_eval_duration` | number | Prompt evaluation time |
| `eval_count` | number | Number of tokens in response |
| `eval_duration` | number | Response generation time |

### Error Responses

#### 400 Bad Request

```json
{
  "detail": "Invalid request format or missing required fields"
}
```

**Causes**:
- Missing `messages` field
- Invalid message format
- Empty messages array

#### 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "loc": ["body", "messages"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Causes**: Pydantic validation error (wrong data types, missing fields)

#### 500 Internal Server Error

```json
{
  "detail": "Connection error to Ollama: [Errno 61] Connection refused"
}
```

**Causes**:
- Ollama not running on localhost:11434
- Ollama service crashed
- Network connectivity issues
- Model not available

## Implementation Details

### File Location

- **Backend**: `backend/main.py`
- **Function**: `chat()`
- **Lines**: 32-50

### Ollama Integration

**Calls Ollama**: Yes

**Ollama Endpoint**: `http://localhost:11434/api/chat`

**Request to Ollama**: Passes through the entire ChatRequest model

```python
response = await client.post(
    ollama_url,
    json=request.model_dump(),
    timeout=60.0
)
```

### Code Implementation

```python
@app.post("/api/chat")
async def chat(request: ChatRequest):
    ollama_url = "http://localhost:11434/api/chat"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                ollama_url,
                json=request.model_dump(),
                timeout=60.0
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Ollama Error: {response.text}"
                )

            return response.json()

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Connection error to Ollama: {str(exc)}"
        )
```

## Flow Diagram

```
Frontend (App.jsx)
    ↓
    POST /api/chat
    {model, messages, stream}
    ↓
FastAPI Backend (main.py)
    ↓
    Validate with Pydantic (ChatRequest)
    ↓
    Proxy to Ollama
    POST http://localhost:11434/api/chat
    ↓
Ollama API (Mistral Model)
    ↓
    Generate Response
    ↓
Response: Ollama → Backend → Frontend
```

## Error Handling

| Error Case | Status Code | Response | User Action |
|------------|-------------|----------|-------------|
| Missing messages field | 422 | Pydantic validation error | Fix request format |
| Invalid data type | 422 | Pydantic validation error | Correct data types |
| Ollama unavailable | 500 | Connection error | Start Ollama service |
| Ollama returns error | 400/500 | Ollama error message | Check Ollama logs |
| Timeout (>60s) | 500 | Timeout error | Check Ollama performance |

## Testing

### Manual Testing

**Test Successful Request**:
```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

**Expected**: 200 OK with AI response

---

**Test Missing Messages Field**:
```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral"
  }'
```

**Expected**: 422 Unprocessable Entity

---

**Test Invalid Data Type**:
```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "messages": "not an array"
  }'
```

**Expected**: 422 Unprocessable Entity

---

**Test Ollama Unavailable**:
```bash
# Stop Ollama first
# Then run:
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "messages": [{"role": "user", "content": "test"}]
  }'
```

**Expected**: 500 Internal Server Error with connection error message

### Expected Behavior

1. ✅ Valid request returns 200 with AI-generated response
2. ✅ Invalid request returns 422 with validation details
3. ✅ Ollama unavailable returns 500 with clear error message
4. ✅ Timeout after 60 seconds with timeout error

## Performance

- **Expected Response Time**: 1-5 seconds (depends on prompt complexity and Ollama performance)
- **Timeout**: 60 seconds (configured in httpx client)
- **Ollama Processing**: Varies based on:
  - Prompt length
  - Response length
  - System resources
  - Model size

## Rate Limiting

**Current**: None

**Recommended for Production**:
- Rate limit per IP: 60 requests/minute
- Rate limit per user (when auth added): 100 requests/minute

## Caching

**Current**: None (stateless proxy)

**Not Recommended**: Caching would reduce AI response quality as context matters

## Security Considerations

- **CORS**: Currently allows all origins (`origins = ["*"]`)
  - ⚠️ **Production**: Restrict to specific frontend origin
- **No Authentication**: Anyone with network access can use the API
  - ⚠️ **Production**: Add API key or session-based auth
- **Input Validation**: Pydantic handles basic validation
  - ✅ Type checking
  - ✅ Required fields
  - ⚠️ No content filtering or sanitization
- **No Rate Limiting**: Susceptible to abuse
  - ⚠️ **Production**: Implement rate limiting
- **Timeout Protection**: 60-second timeout prevents hanging requests
  - ✅ Protects against slow Ollama responses

## CORS Configuration

```python
origins = [
    "*",  # All origins allowed - DEVELOPMENT ONLY
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production Recommendation**:
```python
origins = [
    "https://yourdomain.com",
    "https://app.yourdomain.com"
]
```

## Dependencies

- **Ollama**: Required, must be running on localhost:11434
- **Model**: Mistral (or other model specified in request)
- **Python Packages**:
  - `fastapi` - Web framework
  - `httpx` - Async HTTP client
  - `pydantic` - Request validation

## Usage in Frontend

### Fetch Example

```javascript
const sendMessage = async (userMessage) => {
  const response = await fetch('http://localhost:8001/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'mistral',
      messages: [
        ...previousMessages,
        { role: 'user', content: userMessage }
      ],
      stream: false
    })
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const data = await response.json();
  return data.message.content;
};
```

### Error Handling

```javascript
try {
  const response = await fetch('http://localhost:8001/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody)
  });

  if (!response.ok) {
    const error = await response.json();
    console.error('API Error:', error.detail);
    // Display error to user
    return;
  }

  const data = await response.json();
  // Process successful response
} catch (error) {
  console.error('Network Error:', error);
  // Display network error to user
}
```

## Related Documentation

- [Chat Interface Feature](../features/chat-interface.md)
- [CLAUDE.md - Architecture](../../CLAUDE.md#architecture)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)

## Changelog

- **2026-01-17**: Initial implementation with Mistral model
  - Basic proxy functionality
  - 60-second timeout
  - Error handling for Ollama connection
  - Pydantic validation

---

**Created**: 2026-01-17
**Last Updated**: 2026-01-17
**Status**: ✅ Active
**Version**: 0.1.0
