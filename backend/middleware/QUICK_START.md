# Quick Start: Admin Authentication

## 1. Setup (30 seconds)

Add to your `.env` file:

```bash
# Generate a secure token
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env
ADMIN_TOKEN=your-generated-token-here
```

## 2. Protect an Endpoint (1 line of code)

```python
from fastapi import Depends
from middleware.auth import get_admin_user

@app.post("/api/admin-endpoint")
async def admin_endpoint(admin_user=Depends(get_admin_user)):
    # Your code here - only accessible with valid admin token
    return {"message": "Admin access granted"}
```

## 3. Make Authenticated Requests

### cURL
```bash
curl -X POST http://localhost:8000/api/admin-endpoint \
  -H "Authorization: Bearer your-token-here"
```

### JavaScript
```javascript
fetch('/api/admin-endpoint', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

### Python
```python
import requests

headers = {'Authorization': f'Bearer {token}'}
requests.post('http://localhost:8000/api/admin-endpoint', headers=headers)
```

## 4. Test It

```bash
# Without token (should return 401)
curl http://localhost:8000/api/admin-endpoint

# With token (should succeed)
curl -H "Authorization: Bearer your-token-here" \
  http://localhost:8000/api/admin-endpoint
```

## That's it!

See `README.md` for detailed documentation.
See `INTEGRATION_EXAMPLE.md` for full integration examples.
