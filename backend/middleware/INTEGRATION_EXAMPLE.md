# Integration Example: Adding Admin Authentication to Existing Endpoints

This document shows how to integrate the admin authentication middleware into existing FastAPI endpoints.

## Example: Protecting Template Management Endpoints

### Before (No Authentication)

```python
@app.post("/api/templates/create")
@limiter.limit("20/minute")
async def create_template(request: Request, template_request: CreateTemplateRequest):
    """Create a new template from an existing document"""
    if not TEMPLATE_MANAGER_AVAILABLE:
        raise HTTPException(status_code=501, detail="Template management service not available.")

    try:
        template = app.state.template_manager.create_template(
            document_id=template_request.document_id,
            category=template_request.category,
            notes=template_request.notes
        )
        return {"success": True, "template": template}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### After (With Admin Authentication)

```python
from fastapi import Depends
from middleware.auth import get_admin_user

@app.post("/api/templates/create")
@limiter.limit("20/minute")
async def create_template(
    request: Request,
    template_request: CreateTemplateRequest,
    admin_user=Depends(get_admin_user)  # Add this dependency
):
    """Create a new template from an existing document (Admin only)"""
    if not TEMPLATE_MANAGER_AVAILABLE:
        raise HTTPException(status_code=501, detail="Template management service not available.")

    try:
        log_info(
            f"Creating template from document {template_request.document_id} by admin",
            "TEMPLATES"
        )
        template = app.state.template_manager.create_template(
            document_id=template_request.document_id,
            category=template_request.category,
            notes=template_request.notes
        )
        return {"success": True, "template": template}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Recommended Endpoints to Protect

Based on the existing `main.py`, here are the endpoints that should require admin authentication:

### 1. Template Management (Admin Only)
```python
# CREATE template
@app.post("/api/templates/create")
async def create_template(..., admin_user=Depends(get_admin_user)):

# APPROVE template
@app.post("/api/templates/{template_id}/approve")
async def approve_template(..., admin_user=Depends(get_admin_user)):

# DELETE template
@app.delete("/api/templates/{template_id}")
async def delete_template(..., admin_user=Depends(get_admin_user)):
```

### 2. Bulk Operations (Admin Only)
```python
# Categorize all documents (expensive operation)
@app.post("/api/documents/categorize-all")
async def categorize_all(request: Request, admin_user=Depends(get_admin_user)):
```

### 3. Public Endpoints (No Authentication Required)
```python
# These should remain public:
@app.get("/api/templates")  # List templates - users need to see available templates
@app.get("/api/templates/{template_id}")  # View template details
@app.post("/api/chat")  # Chat endpoint - core functionality
@app.get("/api/documents")  # List documents
@app.post("/api/documents/compliance-check")  # Compliance checking
```

### 4. Upload/Delete Operations (Consider Case-by-Case)
```python
# Option A: Make admin-only for production
@app.post("/api/documents/upload")
async def upload_documents(..., admin_user=Depends(get_admin_user)):

@app.delete("/api/documents/{doc_id}")
async def delete_document(..., admin_user=Depends(get_admin_user)):

# Option B: Keep public for development, add admin requirement later
@app.post("/api/documents/upload")
async def upload_documents(...):  # Public for now
```

## Complete Example: Updated Template Endpoints

Here's how the template endpoints section of `main.py` would look with authentication:

```python
from fastapi import Depends
from middleware.auth import get_admin_user

# ... other imports and setup ...

@app.post("/api/templates/create")
@limiter.limit("20/minute")
async def create_template(
    request: Request,
    template_request: CreateTemplateRequest,
    admin_user=Depends(get_admin_user)
):
    """Create a new template from an existing document (Admin only)"""
    if not TEMPLATE_MANAGER_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Template management service not available."
        )

    try:
        log_info(
            f"Admin creating template from document {template_request.document_id}",
            "TEMPLATES"
        )
        template = app.state.template_manager.create_template(
            document_id=template_request.document_id,
            category=template_request.category,
            notes=template_request.notes
        )
        log_success(f"Template created: {template.get('id', 'unknown')}", "TEMPLATES")
        return {"success": True, "template": template}
    except ValueError as e:
        log_warning(f"Invalid template creation request: {str(e)}", "TEMPLATES")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Failed to create template: {str(e)}", "TEMPLATES")
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")


@app.post("/api/templates/{template_id}/approve")
@limiter.limit("20/minute")
async def approve_template(
    request: Request,
    template_id: str,
    approve_request: ApproveTemplateRequest,
    admin_user=Depends(get_admin_user)
):
    """Approve a template for use (Admin only)"""
    if not TEMPLATE_MANAGER_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Template management service not available."
        )

    try:
        log_info(f"Admin approving template {template_id}", "TEMPLATES")
        template = app.state.template_manager.approve_template(
            template_id=template_id,
            approved_by=approve_request.approved_by
        )
        if not template:
            log_warning(f"Template not found: {template_id}", "TEMPLATES")
            raise HTTPException(status_code=404, detail="Template not found")
        log_success(f"Template approved: {template_id}", "TEMPLATES")
        return {"success": True, "template": template}
    except HTTPException:
        raise
    except ValueError as e:
        log_warning(f"Invalid template approval request: {str(e)}", "TEMPLATES")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Failed to approve template {template_id}: {str(e)}", "TEMPLATES")
        raise HTTPException(status_code=500, detail=f"Failed to approve template: {str(e)}")


@app.delete("/api/templates/{template_id}")
@limiter.limit("20/minute")
async def delete_template(
    request: Request,
    template_id: str,
    admin_user=Depends(get_admin_user)
):
    """Deactivate a template (soft delete) (Admin only)"""
    if not TEMPLATE_MANAGER_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Template management service not available."
        )

    try:
        log_info(f"Admin deactivating template: {template_id}", "TEMPLATES")
        success = app.state.template_manager.deactivate_template(template_id)
        if not success:
            log_warning(f"Template not found: {template_id}", "TEMPLATES")
            raise HTTPException(status_code=404, detail="Template not found")
        log_success(f"Template deactivated: {template_id}", "TEMPLATES")
        return {"success": True, "message": "Template deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Failed to deactivate template {template_id}: {str(e)}", "TEMPLATES")
        raise HTTPException(status_code=500, detail=f"Failed to deactivate template: {str(e)}")


# Public endpoints (no authentication required)
@app.get("/api/templates")
async def list_templates(category: Optional[str] = None, include_inactive: bool = False):
    """List all templates with optional filtering (Public)"""
    # ... existing implementation ...


@app.get("/api/templates/{template_id}")
async def get_template(template_id: str):
    """Get a specific template by ID with usage statistics (Public)"""
    # ... existing implementation ...
```

## Testing with Authentication

### 1. Set Up Environment

```bash
# In your .env file
ADMIN_TOKEN=dev-admin-token-12345
```

### 2. Test Protected Endpoint

```bash
# This should fail (401 Unauthorized)
curl -X POST http://localhost:8000/api/templates/create \
  -H "Content-Type: application/json" \
  -d '{"document_id": "doc123", "category": "NDA"}'

# This should succeed
curl -X POST http://localhost:8000/api/templates/create \
  -H "Authorization: Bearer dev-admin-token-12345" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "doc123", "category": "NDA"}'
```

### 3. Test Public Endpoint

```bash
# This should still work without token
curl http://localhost:8000/api/templates
```

## Error Handling

The authentication middleware provides clear error messages:

```json
// Missing token
{
  "detail": "Missing authentication credentials"
}

// Invalid format
{
  "detail": "Invalid authentication format. Expected: 'Bearer {token}'"
}

// Invalid token
{
  "detail": "Invalid or expired authentication credentials"
}
```

## Next Steps

1. **Update main.py**: Add `admin_user=Depends(get_admin_user)` to protected endpoints
2. **Update .env**: Set a secure ADMIN_TOKEN
3. **Test endpoints**: Verify authentication works correctly
4. **Update frontend**: Add token to admin requests
5. **Document**: Update API documentation to indicate which endpoints require admin access

## Frontend Integration

When making authenticated requests from the frontend:

```typescript
// Store admin token securely (e.g., in localStorage or secure cookie)
const adminToken = localStorage.getItem('adminToken');

// Add to requests
const response = await fetch('/api/templates/create', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${adminToken}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    document_id: 'doc123',
    category: 'NDA',
  }),
});

if (response.status === 401) {
  // Handle unauthorized - redirect to login or show error
  console.error('Authentication required');
}
```

## Security Reminders

1. **Never commit tokens**: Add `.env` to `.gitignore`
2. **Use HTTPS in production**: Tokens should never be sent over HTTP
3. **Rotate tokens regularly**: Change admin token periodically
4. **Plan for upgrade**: This is Phase 1 - plan to implement JWT/user management later
5. **Audit logs**: Track who performs admin actions (add to logging)
