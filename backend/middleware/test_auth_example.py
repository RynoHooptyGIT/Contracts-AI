"""
Example test file for admin authentication middleware.

This demonstrates how to test the authentication functionality.
Run with: pytest middleware/test_auth_example.py

Note: This is an example. Full test suite should be added later.
"""

import os
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException, Request


def test_admin_auth_initialization():
    """Test AdminAuth initializes correctly with environment variable."""
    with patch.dict(os.environ, {"ADMIN_TOKEN": "test-token-123"}):
        from middleware.auth import AdminAuth

        auth = AdminAuth()
        assert auth.admin_token == "test-token-123"


def test_admin_auth_missing_token():
    """Test AdminAuth raises error when ADMIN_TOKEN is not set."""
    with patch.dict(os.environ, {}, clear=True):
        from middleware.auth import AdminAuth

        with pytest.raises(ValueError, match="ADMIN_TOKEN environment variable is not set"):
            AdminAuth()


def test_verify_admin_token_valid():
    """Test token verification with valid token."""
    with patch.dict(os.environ, {"ADMIN_TOKEN": "correct-token"}):
        from middleware.auth import AdminAuth

        auth = AdminAuth()
        assert auth.verify_admin_token("correct-token") is True


def test_verify_admin_token_invalid():
    """Test token verification with invalid token."""
    with patch.dict(os.environ, {"ADMIN_TOKEN": "correct-token"}):
        from middleware.auth import AdminAuth

        auth = AdminAuth()
        assert auth.verify_admin_token("wrong-token") is False
        assert auth.verify_admin_token("") is False
        assert auth.verify_admin_token(None) is False


def test_require_admin_missing_header():
    """Test require_admin raises 401 when Authorization header is missing."""
    with patch.dict(os.environ, {"ADMIN_TOKEN": "test-token"}):
        from middleware.auth import AdminAuth

        auth = AdminAuth()
        mock_request = Mock(spec=Request)
        mock_request.headers = {}

        with pytest.raises(HTTPException) as exc_info:
            auth.require_admin(mock_request)

        assert exc_info.value.status_code == 401
        assert "Missing authentication credentials" in exc_info.value.detail


def test_require_admin_invalid_format():
    """Test require_admin raises 401 when Authorization format is invalid."""
    with patch.dict(os.environ, {"ADMIN_TOKEN": "test-token"}):
        from middleware.auth import AdminAuth

        auth = AdminAuth()
        mock_request = Mock(spec=Request)

        # Test various invalid formats
        invalid_headers = [
            "test-token",  # Missing "Bearer"
            "Bearer",  # Missing token
            "Basic test-token",  # Wrong auth type
            "Bearer token1 token2 extra",  # Too many parts
        ]

        for invalid_header in invalid_headers:
            mock_request.headers = {"Authorization": invalid_header}
            with pytest.raises(HTTPException) as exc_info:
                auth.require_admin(mock_request)

            assert exc_info.value.status_code == 401


def test_require_admin_invalid_token():
    """Test require_admin raises 401 when token is invalid."""
    with patch.dict(os.environ, {"ADMIN_TOKEN": "correct-token"}):
        from middleware.auth import AdminAuth

        auth = AdminAuth()
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer wrong-token"}

        with pytest.raises(HTTPException) as exc_info:
            auth.require_admin(mock_request)

        assert exc_info.value.status_code == 401
        assert "Invalid or expired authentication credentials" in exc_info.value.detail


def test_require_admin_success():
    """Test require_admin succeeds with valid token."""
    with patch.dict(os.environ, {"ADMIN_TOKEN": "correct-token"}):
        from middleware.auth import AdminAuth

        auth = AdminAuth()
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer correct-token"}

        # Should not raise any exception
        auth.require_admin(mock_request)


def test_get_admin_user_success():
    """Test get_admin_user dependency returns admin user dict."""
    with patch.dict(os.environ, {"ADMIN_TOKEN": "test-token"}):
        from middleware.auth import get_admin_user

        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer test-token"}

        admin_user = get_admin_user(mock_request)

        assert admin_user["role"] == "admin"
        assert admin_user["authenticated"] is True


def test_get_admin_user_unauthorized():
    """Test get_admin_user raises HTTPException for unauthorized access."""
    with patch.dict(os.environ, {"ADMIN_TOKEN": "test-token"}):
        from middleware.auth import get_admin_user

        mock_request = Mock(spec=Request)
        mock_request.headers = {}

        with pytest.raises(HTTPException) as exc_info:
            get_admin_user(mock_request)

        assert exc_info.value.status_code == 401


def test_case_insensitive_bearer():
    """Test that 'Bearer' keyword is case-insensitive."""
    with patch.dict(os.environ, {"ADMIN_TOKEN": "test-token"}):
        from middleware.auth import AdminAuth

        auth = AdminAuth()
        mock_request = Mock(spec=Request)

        # Test different cases of "Bearer"
        for bearer_variant in ["Bearer", "bearer", "BEARER", "BeArEr"]:
            mock_request.headers = {"Authorization": f"{bearer_variant} test-token"}
            # Should not raise exception
            auth.require_admin(mock_request)


# Integration test example
@pytest.mark.asyncio
async def test_fastapi_endpoint_integration():
    """
    Example integration test showing how authentication works with FastAPI endpoints.

    This would require FastAPI test client setup.
    """
    from fastapi import FastAPI, Depends
    from fastapi.testclient import TestClient

    with patch.dict(os.environ, {"ADMIN_TOKEN": "test-admin-token"}):
        from middleware.auth import get_admin_user

        app = FastAPI()

        @app.get("/protected")
        async def protected_endpoint(admin_user=Depends(get_admin_user)):
            return {"message": "Success", "admin": admin_user}

        @app.get("/public")
        async def public_endpoint():
            return {"message": "Public access"}

        client = TestClient(app)

        # Test protected endpoint without token
        response = client.get("/protected")
        assert response.status_code == 401

        # Test protected endpoint with invalid token
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer wrong-token"}
        )
        assert response.status_code == 401

        # Test protected endpoint with valid token
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer test-admin-token"}
        )
        assert response.status_code == 200
        assert response.json()["admin"]["role"] == "admin"

        # Test public endpoint (should always work)
        response = client.get("/public")
        assert response.status_code == 200


if __name__ == "__main__":
    """Run basic tests without pytest."""
    print("Running basic authentication tests...")

    # Set up test environment
    os.environ["ADMIN_TOKEN"] = "test-token-123"

    # Import after setting environment
    from middleware.auth import AdminAuth, get_admin_user

    # Test 1: Initialization
    print("Test 1: AdminAuth initialization... ", end="")
    auth = AdminAuth()
    assert auth.admin_token == "test-token-123"
    print("PASSED")

    # Test 2: Valid token
    print("Test 2: Valid token verification... ", end="")
    assert auth.verify_admin_token("test-token-123") is True
    print("PASSED")

    # Test 3: Invalid token
    print("Test 3: Invalid token verification... ", end="")
    assert auth.verify_admin_token("wrong-token") is False
    print("PASSED")

    # Test 4: Missing header
    print("Test 4: Missing Authorization header... ", end="")
    mock_request = Mock(spec=Request)
    mock_request.headers = {}
    try:
        auth.require_admin(mock_request)
        print("FAILED - Should have raised HTTPException")
    except HTTPException as e:
        assert e.status_code == 401
        print("PASSED")

    # Test 5: Valid authentication
    print("Test 5: Valid authentication... ", end="")
    mock_request.headers = {"Authorization": "Bearer test-token-123"}
    auth.require_admin(mock_request)  # Should not raise
    print("PASSED")

    print("\nAll basic tests passed!")
