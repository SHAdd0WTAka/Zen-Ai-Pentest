"""
Smart tests for api/main.py module.

Tests cover:
1. Module importability
2. FastAPI app creation
3. Lifespan management
4. Token verification
5. Route registration
"""

from unittest.mock import MagicMock, patch

import pytest


class TestMainImportable:
    """Test that main module can be imported."""

    def test_module_importable(self):
        """Test that main module can be imported."""
        with patch.dict(
            "sys.modules",
            {
                "database.models": MagicMock(),
                "database.crud": MagicMock(),
            },
        ):
            import api.main as main

            assert main is not None

    def test_app_available(self):
        """Test that FastAPI app is available."""
        with patch.dict(
            "sys.modules",
            {
                "database.models": MagicMock(),
                "database.crud": MagicMock(),
            },
        ):
            from api.main import app

            assert app is not None


class TestFastAPIApp:
    """Test FastAPI application."""

    def test_app_title(self):
        """Test FastAPI app title."""
        with patch.dict(
            "sys.modules",
            {
                "database.models": MagicMock(),
                "database.crud": MagicMock(),
            },
        ):
            from api.main import app

            assert app.title == "Zen-AI-Pentest API"

    def test_app_version(self):
        """Test FastAPI app version."""
        with patch.dict(
            "sys.modules",
            {
                "database.models": MagicMock(),
                "database.crud": MagicMock(),
            },
        ):
            from api.main import app

            assert app.version == "2.2.0"

    def test_app_has_routes(self):
        """Test that app has routes."""
        with patch.dict(
            "sys.modules",
            {
                "database.models": MagicMock(),
                "database.crud": MagicMock(),
            },
        ):
            from api.main import app

            assert len(app.routes) > 0


class TestTokenVerification:
    """Test token verification in main."""

    @pytest.mark.asyncio
    async def test_verify_token_no_credentials(self):
        """Test verify_token with no credentials."""
        from fastapi import HTTPException

        with patch.dict(
            "sys.modules",
            {
                "database.models": MagicMock(),
                "database.crud": MagicMock(),
            },
        ):
            from api.main import verify_token

            with pytest.raises(HTTPException) as exc_info:
                await verify_token(None)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_token_empty_credentials(self):
        """Test verify_token with empty credentials."""
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials

        with patch.dict(
            "sys.modules",
            {
                "database.models": MagicMock(),
                "database.crud": MagicMock(),
            },
        ):
            from api.main import verify_token

            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="")
            with pytest.raises(HTTPException) as exc_info:
                await verify_token(credentials)
            assert exc_info.value.status_code == 401


class TestOptionalAuth:
    """Test optional authentication."""

    @pytest.mark.asyncio
    async def test_optional_auth_no_header(self):
        """Test optional_auth with no auth header."""
        from unittest.mock import MagicMock

        with patch.dict(
            "sys.modules",
            {
                "database.models": MagicMock(),
                "database.crud": MagicMock(),
            },
        ):
            from api.main import optional_auth

            request = MagicMock()
            request.headers.get.return_value = None
            result = await optional_auth(request)
            assert result is None

    @pytest.mark.asyncio
    async def test_optional_auth_invalid_scheme(self):
        """Test optional_auth with invalid scheme."""
        from unittest.mock import MagicMock

        with patch.dict(
            "sys.modules",
            {
                "database.models": MagicMock(),
                "database.crud": MagicMock(),
            },
        ):
            from api.main import optional_auth

            request = MagicMock()
            request.headers.get.return_value = "Basic token123"
            result = await optional_auth(request)
            assert result is None


class TestLifespan:
    """Test lifespan management."""

    @pytest.mark.asyncio
    async def test_lifespan_startup(self):
        """Test lifespan startup."""
        with patch.dict(
            "sys.modules",
            {
                "database.models": MagicMock(),
                "database.crud": MagicMock(),
            },
        ):
            from fastapi import FastAPI

            from api.main import lifespan

            app = FastAPI()
            async with lifespan(app):
                pass  # Startup and shutdown


class TestEmptyInput:
    """Test handling of empty input."""

    def test_empty_target_in_scan(self):
        """Test handling empty target in scan creation."""
        from pydantic import ValidationError

        with patch.dict(
            "sys.modules",
            {
                "database.models": MagicMock(),
                "database.crud": MagicMock(),
            },
        ):
            from api.schemas import ScanCreate

            with pytest.raises(ValidationError):
                ScanCreate(name="Test", target="", scan_type="nmap")


class TestInvalidOutput:
    """Test handling of invalid output."""

    @pytest.mark.asyncio
    async def test_verify_token_malformed(self):
        """Test verify_token with malformed token."""
        from fastapi.security import HTTPAuthorizationCredentials

        with patch.dict(
            "sys.modules",
            {
                "database.models": MagicMock(),
                "database.crud": MagicMock(),
            },
        ):
            from fastapi import HTTPException

            from api.main import verify_token

            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="malformed.token.here")
            with pytest.raises(HTTPException) as exc_info:
                await verify_token(credentials)
            assert exc_info.value.status_code == 401
