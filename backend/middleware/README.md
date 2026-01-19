# Authentication Middleware

## Overview

This directory contains authentication and authorization middleware for the Contracts AI backend.

## Phase 1: Basic Admin Authentication

The current implementation (`auth.py`) provides simple token-based authentication for admin endpoints. This is suitable for Phase 1 development but should be enhanced before production deployment.

### Features

- **Simple Bearer Token Authentication**: Uses a single admin token from environment variables
- **FastAPI Dependency Integration**: Easy to add authentication to any endpoint
- **Clear Error Messages**: Provides helpful 401 responses for unauthorized access
- **OpenAPI Documentation Support**: Generates proper API documentation

### Setup

1. **Set Admin Token in Environment**

   Add to your `.env` file:
   ```bash
   ADMIN_TOKEN=your-secure-admin-token-here
   ```

   Generate a secure token:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Import and Use in Endpoints**

   ```python
   from fastapi import Depends
   from middleware.auth import get_admin_user

   @app.post("/api/admin-only-endpoint")
   async def admin_endpoint(admin_user=Depends(get_admin_user)):
       # Only accessible with valid admin token
       return {"message": "Admin access granted"}
   ```

### Usage Examples

#### Basic Admin Endpoint Protection

```python
from fastapi import APIRouter, Depends
from middleware.auth import get_admin_user

router = APIRouter()

@router.post("/api/templates/create")
async def create_template(
    template_data: dict,
    admin_user=Depends(get_admin_user)
):
    # admin_user is only populated if authentication succeeds
    return {"success": True, "admin": admin_user["role"]}
```

#### Making Authenticated Requests

From a client (e.g., curl, JavaScript, Python):

```bash
# Using curl
curl -X POST http://localhost:8000/api/admin-endpoint \
  -H "Authorization: Bearer your-admin-token-here" \
  -H "Content-Type: application/json" \
  -d '{"data": "value"}'
```

```javascript
// Using JavaScript fetch
const response = await fetch('http://localhost:8000/api/admin-endpoint', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${adminToken}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ data: 'value' }),
});
```

```python
# Using Python requests
import requests

headers = {
    'Authorization': f'Bearer {admin_token}',
    'Content-Type': 'application/json',
}

response = requests.post(
    'http://localhost:8000/api/admin-endpoint',
    headers=headers,
    json={'data': 'value'}
)
```

### API Responses

#### Success (200)
```json
{
  "message": "Admin access granted",
  "data": "..."
}
```

#### Missing Authorization Header (401)
```json
{
  "detail": "Missing authentication credentials"
}
```

#### Invalid Token Format (401)
```json
{
  "detail": "Invalid authentication format. Expected: 'Bearer {token}'"
}
```

#### Invalid Token (401)
```json
{
  "detail": "Invalid or expired authentication credentials"
}
```

### Security Considerations

**Current Implementation (Phase 1):**
- Simple token comparison
- No expiration
- No user roles or permissions
- No audit logging
- Token stored in plain environment variable

**Recommended Enhancements for Production:**

1. **JWT-Based Authentication**
   - Token expiration and refresh
   - Claims-based authorization
   - Revocation support

2. **User Management**
   - Multiple admin users
   - Password hashing (bcrypt/argon2)
   - User database

3. **Role-Based Access Control (RBAC)**
   - Different permission levels
   - Granular endpoint access
   - Resource-based authorization

4. **Additional Security**
   - Multi-factor authentication (MFA)
   - Rate limiting per user
   - Audit logging for auth events
   - IP allowlisting
   - Session management

5. **Secure Token Storage**
   - Use secrets manager (AWS Secrets Manager, HashiCorp Vault)
   - Rotate tokens regularly
   - Encrypt tokens at rest

### Testing Authentication

You can test the authentication locally:

```python
# test_auth.py
import requests

BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "your-admin-token-here"

# Test without token (should fail)
response = requests.post(f"{BASE_URL}/api/templates/create")
print(f"No token: {response.status_code}")  # Should be 401

# Test with invalid token (should fail)
headers = {"Authorization": "Bearer invalid-token"}
response = requests.post(f"{BASE_URL}/api/templates/create", headers=headers)
print(f"Invalid token: {response.status_code}")  # Should be 401

# Test with valid token (should succeed)
headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
response = requests.post(f"{BASE_URL}/api/templates/create", headers=headers)
print(f"Valid token: {response.status_code}")  # Should be 200 or appropriate response
```

### Migration Path to Enhanced Authentication

When ready to upgrade to a more robust authentication system:

1. **Phase 2: JWT Authentication**
   - Replace `AdminAuth.verify_admin_token()` with JWT validation
   - Add token expiration and refresh logic
   - Keep the same `get_admin_user` interface for backward compatibility

2. **Phase 3: User Management**
   - Add user database table
   - Implement login/logout endpoints
   - Add password hashing

3. **Phase 4: RBAC**
   - Add roles and permissions table
   - Create permission checking dependencies
   - Implement fine-grained access control

The current dependency structure (`get_admin_user`) is designed to be easily extended without breaking existing endpoints.

## Files

- `auth.py` - Main authentication implementation
- `__init__.py` - Package initialization and exports
- `README.md` - This documentation file

## Future Enhancements

Track authentication improvements in your project management system:

- [ ] Implement JWT-based authentication
- [ ] Add user database and management
- [ ] Implement RBAC system
- [ ] Add audit logging for authentication events
- [ ] Implement rate limiting per user
- [ ] Add multi-factor authentication (MFA)
- [ ] Integrate with external identity providers (OAuth, SAML)
- [ ] Add session management
- [ ] Implement password reset flow
- [ ] Add IP allowlisting for additional security
