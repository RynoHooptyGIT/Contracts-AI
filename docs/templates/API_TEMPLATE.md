# API: [Endpoint Name]

> **Template Usage**: Copy this file to `docs/api/[endpoint-name].md` and fill in the sections below.

## Endpoint

```
POST /api/[endpoint-name]
```

## Description

[Detailed description of what this endpoint does]

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
  "field1": "string - Description of field1",
  "field2": "boolean - Description of field2",
  "field3": "array - Description of field3"
}
```

### Pydantic Model

```python
class RequestModel(BaseModel):
    field1: str
    field2: bool = False
    field3: List[str] = []
```

### Example Request

```bash
curl -X POST http://localhost:8001/api/[endpoint-name] \
  -H "Content-Type: application/json" \
  -d '{
    "field1": "example value",
    "field2": true,
    "field3": ["item1", "item2"]
  }'
```

## Response

### Success Response (200 OK)

```json
{
  "field1": "string - Description",
  "field2": "object - Description",
  "status": "success"
}
```

### Error Responses

#### 400 Bad Request

```json
{
  "detail": "Invalid request format or missing required fields"
}
```

#### 500 Internal Server Error

```json
{
  "detail": "Connection error to Ollama: [error details]"
}
```

## Implementation Details

### File Location

- **Backend**: `backend/main.py`
- **Function**: `[function_name]()`

### Ollama Integration

**Calls Ollama**: Yes / No

**Ollama Endpoint**: `http://localhost:11434/api/[ollama-endpoint]`

**Request to Ollama**:
```json
{
  "field": "value"
}
```

### Code Snippet

```python
@app.post("/api/[endpoint-name]")
async def endpoint_function(request: RequestModel):
    """
    [Function documentation]
    """
    # Implementation details
    pass
```

## Flow Diagram

```
Frontend (App.jsx)
    ↓
    POST /api/[endpoint-name]
    ↓
FastAPI Backend (main.py)
    ↓
    [Proxy to Ollama / Direct response]
    ↓
Ollama (if applicable)
    ↓
Response → Backend → Frontend
```

## Error Handling

| Error Case | Status Code | Response |
|------------|-------------|----------|
| Missing required field | 400 | `{"detail": "Field X is required"}` |
| Ollama unavailable | 500 | `{"detail": "Connection error to Ollama"}` |
| Invalid data type | 422 | Pydantic validation error |

## Testing

### Manual Testing

```bash
# Test successful request
curl -X POST http://localhost:8001/api/[endpoint-name] \
  -H "Content-Type: application/json" \
  -d '{"field1": "test"}'

# Test error case - missing field
curl -X POST http://localhost:8001/api/[endpoint-name] \
  -H "Content-Type: application/json" \
  -d '{}'

# Test error case - invalid type
curl -X POST http://localhost:8001/api/[endpoint-name] \
  -H "Content-Type: application/json" \
  -d '{"field1": 123}'
```

### Expected Behavior

1. ✅ Valid request returns 200 with expected data
2. ✅ Invalid request returns 400/422 with error details
3. ✅ Ollama failure returns 500 with clear message

## Rate Limiting

**Current**: None
**Recommended**: [If applicable]

## Caching

**Current**: None
**Recommended**: [If applicable]

## Performance

- **Expected Response Time**: < 2s (depends on Ollama)
- **Timeout**: 60 seconds (configured in httpx client)

## Security Considerations

- [CORS enabled for all origins - development only]
- [No authentication required - consider for production]
- [Input validation via Pydantic]

## CORS Configuration

```python
origins = ["*"]  # All origins allowed
```

## Dependencies

- **Ollama**: [Required for this endpoint / Not required]
- **Model**: Mistral (default)
- **Python Packages**: httpx, pydantic

## Usage in Frontend

### Fetch Example

```javascript
const response = await fetch('http://localhost:8001/api/[endpoint-name]', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    field1: value1,
    field2: value2
  })
});

const data = await response.json();
```

### Error Handling

```javascript
try {
  const response = await fetch(/* ... */);
  if (!response.ok) {
    throw new Error('API request failed');
  }
  const data = await response.json();
} catch (error) {
  console.error('Error:', error);
  // Handle error in UI
}
```

## Related Documentation

- [Link to feature documentation]
- [Link to frontend implementation]

## Changelog

- **[Date]**: Initial implementation
- **[Date]**: [Change description]

---

**Created**: [Date]
**Last Updated**: [Date]
**Status**: ✅ Active / 🚧 Beta / ⚠️ Deprecated
