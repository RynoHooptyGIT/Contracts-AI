"""
Admin Authentication Middleware - Phase 1 Implementation

IMPORTANT: This is a basic Phase 1 implementation using simple token-based authentication.
This approach is suitable for initial development but MUST be enhanced before production use.

Future enhancements should include:
- JWT-based authentication with expiration
- Role-based access control (RBAC)
- Password hashing and user management
- Session management
- Multi-factor authentication (MFA)
- Audit logging for authentication events

Current approach: Simple bearer token validation against environment variable.
"""

import os
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AdminAuth:
    """
    Basic admin authentication handler for Phase 1.

    Uses a simple token comparison for admin authentication.
    This is intentionally minimal for Phase 1 and should be enhanced later.
    """

    def __init__(self):
        """Initialize AdminAuth with token from environment."""
        self.admin_token = os.getenv("ADMIN_TOKEN")
        if not self.admin_token:
            raise ValueError(
                "ADMIN_TOKEN environment variable is not set. "
                "Please configure it in your .env file for admin authentication."
            )

    def verify_admin_token(self, token: str) -> bool:
        """
        Verify if the provided token matches the admin token.

        Args:
            token: The bearer token to verify

        Returns:
            bool: True if token is valid, False otherwise

        Note:
            This is a simple string comparison. Future versions should use
            secure token validation with JWT or similar mechanisms.
        """
        if not token:
            return False

        # Simple comparison for Phase 1
        # TODO: Replace with JWT validation in Phase 2+
        return token == self.admin_token

    def require_admin(self, request: Request) -> None:
        """
        Validate admin authentication from request.

        Args:
            request: FastAPI Request object

        Raises:
            HTTPException: 401 if authentication fails

        Note:
            This method extracts the Authorization header and validates the bearer token.
        """
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Parse Bearer token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication format. Expected: 'Bearer {token}'",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = parts[1]

        # Verify token
        if not self.verify_admin_token(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


# Global admin auth instance
_admin_auth = None


def get_admin_auth() -> AdminAuth:
    """
    Get or create the global AdminAuth instance.

    Returns:
        AdminAuth: The singleton admin authentication handler
    """
    global _admin_auth
    if _admin_auth is None:
        _admin_auth = AdminAuth()
    return _admin_auth


# FastAPI Dependency Functions


def get_admin_user(request: Request) -> dict:
    """
    FastAPI dependency for admin authentication.

    This dependency can be used with FastAPI's Depends() to protect endpoints.

    Args:
        request: FastAPI Request object

    Returns:
        dict: Admin user information (currently just a placeholder)

    Raises:
        HTTPException: 401 if authentication fails

    Example:
        ```python
        from middleware.auth import get_admin_user
        from fastapi import Depends

        @app.post("/api/admin-only-endpoint")
        async def admin_endpoint(admin_user=Depends(get_admin_user)):
            # Only accessible with valid admin token
            return {"message": "Admin access granted"}
        ```

    Usage:
        Client should send requests with:
        ```
        Authorization: Bearer {ADMIN_TOKEN}
        ```
    """
    auth = get_admin_auth()
    auth.require_admin(request)

    # For Phase 1, return a simple admin user dict
    # TODO: In Phase 2+, return actual user details from JWT or database
    return {
        "role": "admin",
        "authenticated": True,
        # Future: add user_id, username, permissions, etc.
    }


# Optional: HTTP Bearer security scheme for OpenAPI documentation
# This makes the authentication requirement visible in FastAPI's auto-generated docs
bearer_scheme = HTTPBearer(
    scheme_name="Admin Bearer Token",
    description="Admin authentication using bearer token. Set ADMIN_TOKEN in environment variables.",
    auto_error=False  # We handle errors manually in get_admin_user
)


def get_admin_user_with_scheme(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = None
) -> dict:
    """
    Alternative FastAPI dependency that uses HTTPBearer scheme for better OpenAPI docs.

    This version provides better API documentation but functions identically to get_admin_user.

    Args:
        request: FastAPI Request object
        credentials: Auto-extracted by HTTPBearer (optional)

    Returns:
        dict: Admin user information

    Raises:
        HTTPException: 401 if authentication fails

    Example:
        ```python
        from middleware.auth import get_admin_user_with_scheme, bearer_scheme
        from fastapi import Depends

        @app.post("/api/admin-endpoint")
        async def admin_endpoint(
            admin_user=Depends(get_admin_user_with_scheme),
            token: HTTPAuthorizationCredentials = Depends(bearer_scheme)
        ):
            return {"message": "Admin access granted"}
        ```
    """
    auth = get_admin_auth()

    # If credentials provided via bearer_scheme, validate them
    if credentials:
        if not auth.verify_admin_token(credentials.credentials):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    else:
        # Fallback to manual header extraction
        auth.require_admin(request)

    return {
        "role": "admin",
        "authenticated": True,
    }
