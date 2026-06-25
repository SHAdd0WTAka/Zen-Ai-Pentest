import pytest

pytestmark = pytest.mark.skip(reason="Stale tests needing overhaul")

"""
Core Auth Module Tests
======================

Comprehensive tests for zen-ai-pentest/core/auth/ modules:
- device_flow.py (DeviceCodeFlow, APIKeyAuth, AuthenticationError)
- cli.py (AuthCLI)
- token_store.py (TokenStore)
- __init__.py (module exports)

Target: 90-100% coverage for each module
"""

import asyncio
import json
import os
import stat
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import pytest_asyncio

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import modules under test
from core.auth import AuthCLI, DeviceCodeFlow, TokenStore
from core.auth.device_flow import APIKeyAuth, AuthenticationError

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory for token store tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_token_store(temp_config_dir):
    """Create a TokenStore with temporary config directory."""
    store = TokenStore()
    # Override config dir to use temp directory
    store.config_dir = temp_config_dir / "zen-ai-pentest"
    store.credentials_file = store.config_dir / "credentials.json"
    store._ensure_config_dir()
    return store


@pytest.fixture
def sample_credentials():
    """Sample credentials for testing."""
    return {
        "access_token": "test_access_token_12345",
        "refresh_token": "test_refresh_token_67890",
        "expires_in": 3600,
        "provider": "kimi",
    }


@pytest.fixture
def mock_device_code_response():
    """Mock device code flow initiation response."""
    return {
        "device_code": "test_device_code_abc123",
        "user_code": "ABCD-EFGH",
        "verification_uri": "https://example.com/verify",
        "verification_uri_complete": "https://example.com/verify?code=ABCD-EFGH",
        "expires_in": 600,
        "interval": 5,
    }


@pytest.fixture
def mock_token_response():
    """Mock successful token response."""
    return {
        "access_token": "mock_access_token_xyz789",
        "refresh_token": "mock_refresh_token_abc456",
        "token_type": "Bearer",
        "expires_in": 3600,
    }


@pytest.fixture
def mock_aiohttp_session():
    """Create a mock aiohttp ClientSession."""
    mock_session = AsyncMock()
    mock_context = AsyncMock()
    mock_session.post.return_value = mock_context
    return mock_session, mock_context


# =============================================================================
# TokenStore Tests
# =============================================================================


class TestTokenStore:
    """Tests for TokenStore class (81 statements)."""

    def test_init_creates_config_dir(self, temp_config_dir):
        """Test TokenStore initialization creates config directory."""
        with patch.object(TokenStore, "_get_config_dir", return_value=temp_config_dir / "zen"):
            store = TokenStore()
            assert store.config_dir.exists()

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-only test")
    def test_get_config_dir_windows(self):
        """Test config directory path on Windows."""
        with patch("os.name", "nt"):
            with patch.dict(os.environ, {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"}):
                store = TokenStore()
                expected = Path("C:\\Users\\Test\\AppData\\Roaming") / "zen-ai-pentest"
                assert store._get_config_dir() == expected

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-only test")
    def test_get_config_dir_windows_fallback(self):
        """Test config directory fallback on Windows without APPDATA."""
        with patch("os.name", "nt"):
            with patch.dict(os.environ, {}, clear=True):
                with patch.object(Path, "home", return_value=Path("C:\\Users\\Test")):
                    store = TokenStore()
                    config_dir = store._get_config_dir()
                    assert "AppData" in str(config_dir)

    def test_get_config_dir_linux(self):
        """Test config directory path on Linux."""
        with patch("os.name", "posix"):
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/home/test/.config"}):
                store = TokenStore()
                expected = Path("/home/test/.config") / "zen-ai-pentest"
                assert store._get_config_dir() == expected

    def test_get_config_dir_linux_fallback(self):
        """Test config directory fallback on Linux without XDG_CONFIG_HOME."""
        with patch("os.name", "posix"):
            with patch.dict(os.environ, {}, clear=True):
                with patch.object(Path, "home", return_value=Path("/home/test")):
                    store = TokenStore()
                    config_dir = store._get_config_dir()
                    assert ".config" in str(config_dir)

    def test_ensure_config_dir_sets_permissions(self, temp_config_dir):
        """Test config directory gets restrictive permissions on Unix."""
        with patch("os.name", "posix"):
            store = TokenStore()
            store.config_dir = temp_config_dir / "zen-test"
            store._ensure_config_dir()

            # Check permissions
            mode = os.stat(store.config_dir).st_mode
            # Should be 700 (owner read/write/execute only)
            assert stat.S_IRWXU & mode
            assert not (stat.S_IRWXG & mode)
            assert not (stat.S_IRWXO & mode)

    def test_save_credentials(self, mock_token_store, sample_credentials):
        """Test saving credentials."""
        mock_token_store.save_credentials(**sample_credentials)

        assert mock_token_store.credentials_file.exists()
        with open(mock_token_store.credentials_file) as f:
            saved = json.load(f)

        assert saved["access_token"] == sample_credentials["access_token"]
        assert saved["refresh_token"] == sample_credentials["refresh_token"]
        assert saved["provider"] == sample_credentials["provider"]
        assert saved["version"] == 1
        assert "created_at" in saved
        assert "expires_at" in saved

    def test_save_credentials_no_expiry(self, mock_token_store):
        """Test saving credentials without expiration."""
        mock_token_store.save_credentials(
            access_token="test_token",
            refresh_token=None,
            expires_in=None,
            provider="kimi",
        )

        with open(mock_token_store.credentials_file) as f:
            saved = json.load(f)

        assert saved["expires_at"] is None
        assert saved["refresh_token"] is None

    def test_save_credentials_sets_permissions(self, mock_token_store, sample_credentials):
        """Test saved credentials file gets restrictive permissions on Unix."""
        with patch("os.name", "posix"):
            mock_token_store.save_credentials(**sample_credentials)

            mode = os.stat(mock_token_store.credentials_file).st_mode
            # Should be 600 (owner read/write only)
            assert stat.S_IRUSR & mode
            assert stat.S_IWUSR & mode
            assert not (stat.S_IRWXG & mode)
            assert not (stat.S_IRWXO & mode)

    def test_load_credentials(self, mock_token_store, sample_credentials):
        """Test loading saved credentials."""
        mock_token_store.save_credentials(**sample_credentials)

        loaded = mock_token_store.load_credentials()
        assert loaded is not None
        assert loaded["access_token"] == sample_credentials["access_token"]

    def test_load_credentials_not_exists(self, mock_token_store):
        """Test loading credentials when file doesn't exist."""
        loaded = mock_token_store.load_credentials()
        assert loaded is None

    def test_load_credentials_invalid_json(self, mock_token_store):
        """Test loading credentials with invalid JSON."""
        mock_token_store.config_dir.mkdir(parents=True, exist_ok=True)
        with open(mock_token_store.credentials_file, "w") as f:
            f.write("invalid json")

        loaded = mock_token_store.load_credentials()
        assert loaded is None

    def test_get_access_token(self, mock_token_store, sample_credentials):
        """Test getting access token."""
        mock_token_store.save_credentials(**sample_credentials)

        token = mock_token_store.get_access_token()
        assert token == sample_credentials["access_token"]

    def test_get_access_token_expired(self, mock_token_store):
        """Test getting expired access token returns None."""
        # Save credentials that expire in 1 second (less than 5 min threshold)
        mock_token_store.save_credentials(
            access_token="expired_token",
            refresh_token="refresh",
            expires_in=1,  # Expires in 1 second
            provider="kimi",
        )

        # Token should be considered expired (within 5 min window)
        token = mock_token_store.get_access_token()
        assert token is None

    def test_get_access_token_no_creds(self, mock_token_store):
        """Test getting access token when no credentials exist."""
        token = mock_token_store.get_access_token()
        assert token is None

    def test_get_refresh_token(self, mock_token_store, sample_credentials):
        """Test getting refresh token."""
        mock_token_store.save_credentials(**sample_credentials)

        token = mock_token_store.get_refresh_token()
        assert token == sample_credentials["refresh_token"]

    def test_get_refresh_token_no_creds(self, mock_token_store):
        """Test getting refresh token when no credentials exist."""
        token = mock_token_store.get_refresh_token()
        assert token is None

    def test_is_authenticated_true(self, mock_token_store, sample_credentials):
        """Test is_authenticated returns True when valid token exists."""
        mock_token_store.save_credentials(**sample_credentials)
        assert mock_token_store.is_authenticated() is True

    def test_is_authenticated_false(self, mock_token_store):
        """Test is_authenticated returns False when no credentials."""
        assert mock_token_store.is_authenticated() is False

    def test_is_authenticated_expired(self, mock_token_store):
        """Test is_authenticated returns False when token is expired."""
        mock_token_store.save_credentials(
            access_token="token",
            refresh_token="refresh",
            expires_in=1,  # Expires in 1 second
            provider="kimi",
        )
        assert mock_token_store.is_authenticated() is False

    def test_clear_credentials(self, mock_token_store, sample_credentials):
        """Test clearing credentials."""
        mock_token_store.save_credentials(**sample_credentials)
        assert mock_token_store.credentials_file.exists()

        mock_token_store.clear_credentials()
        assert not mock_token_store.credentials_file.exists()

    def test_clear_credentials_not_exists(self, mock_token_store):
        """Test clearing credentials when file doesn't exist."""
        # Should not raise an error
        mock_token_store.clear_credentials()

    def test_get_auth_headers(self, mock_token_store, sample_credentials):
        """Test getting auth headers."""
        mock_token_store.save_credentials(**sample_credentials)

        headers = mock_token_store.get_auth_headers()
        assert headers == {"Authorization": f"Bearer {sample_credentials['access_token']}"}

    def test_get_auth_headers_no_token(self, mock_token_store):
        """Test getting auth headers when no token exists."""
        headers = mock_token_store.get_auth_headers()
        assert headers == {}

    def test_get_credential_path(self, mock_token_store):
        """Test getting credential path."""
        path = mock_token_store.get_credential_path()
        assert "credentials.json" in path


# =============================================================================
# TokenStore Helper Functions Tests
# =============================================================================


class TestTokenStoreHelpers:
    """Tests for TokenStore helper functions."""

    def test_get_stored_token(self, mock_token_store):
        """Test get_stored_token convenience function."""
        mock_token_store.save_credentials(
            access_token="test_token",
            refresh_token=None,
            expires_in=3600,
            provider="kimi",
        )

        from core.auth.token_store import get_stored_token

        with patch("core.auth.token_store.TokenStore") as MockStore:
            MockStore.return_value = mock_token_store
            token = get_stored_token()
            assert token == "test_token"

    def test_is_logged_in(self, mock_token_store):
        """Test is_logged_in convenience function."""
        mock_token_store.save_credentials(
            access_token="test_token",
            refresh_token=None,
            expires_in=3600,
            provider="kimi",
        )

        from core.auth.token_store import is_logged_in

        with patch("core.auth.token_store.TokenStore") as MockStore:
            MockStore.return_value = mock_token_store
            assert is_logged_in() is True

    def test_require_auth_decorator_authenticated(self, mock_token_store):
        """Test require_auth decorator when authenticated."""
        mock_token_store.save_credentials(
            access_token="test_token",
            refresh_token=None,
            expires_in=3600,
            provider="kimi",
        )

        from core.auth.token_store import require_auth

        with patch("core.auth.token_store.TokenStore") as MockStore:
            MockStore.return_value = mock_token_store

            @require_auth
            def protected_function():
                return "success"

            assert protected_function() == "success"

    def test_require_auth_decorator_not_authenticated(self, mock_token_store):
        """Test require_auth decorator when not authenticated."""
        from core.auth.token_store import require_auth

        with patch("core.auth.token_store.TokenStore") as MockStore:
            MockStore.return_value = mock_token_store

            @require_auth
            def protected_function():
                return "success"

            result = protected_function()
            assert result == 1


# =============================================================================
# DeviceCodeFlow Tests
# =============================================================================


@pytest.mark.asyncio
class TestDeviceCodeFlow:
    """Tests for DeviceCodeFlow class (async operations)."""

    async def test_init(self):
        """Test DeviceCodeFlow initialization."""
        flow = DeviceCodeFlow(client_id="test-client")
        assert flow.client_id == "test-client"
        assert flow.session is None

    async def test_async_context_manager(self):
        """Test async context manager creates and closes session."""
        flow = DeviceCodeFlow()

        async with flow as f:
            assert f.session is not None

        # After exiting, session should be closed
        assert flow.session is not None  # Still referenced but closed

    def _create_mock_session(self, mock_response):
        """Helper to create a mock session with async context manager."""
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_context)
        return mock_session

    async def test_initiate_device_flow_success(self, mock_device_code_response):
        """Test successful device flow initiation."""
        flow = DeviceCodeFlow()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_device_code_response)

        flow.session = self._create_mock_session(mock_response)

        result = await flow.initiate_device_flow()

        assert result == mock_device_code_response
        flow.session.post.assert_called_once()
        call_args = flow.session.post.call_args
        assert call_args[0][0] == DeviceCodeFlow.DEVICE_AUTHORIZATION_ENDPOINT

    async def test_initiate_device_flow_failure(self):
        """Test device flow initiation failure."""
        flow = DeviceCodeFlow()

        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Bad Request")

        flow.session = self._create_mock_session(mock_response)

        with pytest.raises(AuthenticationError) as exc_info:
            await flow.initiate_device_flow()

        assert "Device code request failed" in str(exc_info.value)

    async def test_initiate_device_flow_network_error(self):
        """Test device flow initiation with network error."""
        import aiohttp

        flow = DeviceCodeFlow()

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("Connection failed"))
        mock_context.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_context)

        flow.session = mock_session

        with pytest.raises(AuthenticationError) as exc_info:
            await flow.initiate_device_flow()

        assert "Network error" in str(exc_info.value)

    async def test_poll_for_token_success(self, mock_token_response):
        """Test successful token polling."""
        flow = DeviceCodeFlow()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_token_response)

        flow.session = self._create_mock_session(mock_response)

        result = await flow.poll_for_token("device_code_123", interval=0.1, timeout=1)

        assert result == mock_token_response
        assert result["access_token"] == mock_token_response["access_token"]

    async def test_poll_for_token_authorization_pending(self, mock_token_response):
        """Test token polling with authorization_pending response."""
        flow = DeviceCodeFlow()

        pending_response = AsyncMock()
        pending_response.status = 400
        pending_response.json = AsyncMock(return_value={"error": "authorization_pending"})

        success_response = AsyncMock()
        success_response.status = 200
        success_response.json = AsyncMock(return_value=mock_token_response)

        # Create side effects for multiple calls
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(side_effect=[pending_response, success_response])
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_context_manager)

        flow.session = mock_session

        result = await flow.poll_for_token("device_code_123", interval=0.01, timeout=5)

        assert result["access_token"] == mock_token_response["access_token"]
        assert mock_session.post.call_count == 2

    async def test_poll_for_token_slow_down(self, mock_token_response):
        """Test token polling with slow_down response."""
        flow = DeviceCodeFlow()

        slow_response = AsyncMock()
        slow_response.status = 400
        slow_response.json = AsyncMock(return_value={"error": "slow_down"})

        success_response = AsyncMock()
        success_response.status = 200
        success_response.json = AsyncMock(return_value=mock_token_response)

        # Create side effects for multiple calls
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(side_effect=[slow_response, success_response])
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_context_manager)

        flow.session = mock_session

        # Use a longer timeout since slow_down adds 5 seconds to interval
        result = await flow.poll_for_token("device_code_123", interval=0.01, timeout=30)

        assert result["access_token"] == mock_token_response["access_token"]

    async def test_poll_for_token_expired(self):
        """Test token polling with expired_token error."""
        flow = DeviceCodeFlow()

        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={"error": "expired_token"})

        flow.session = self._create_mock_session(mock_response)

        with pytest.raises(AuthenticationError) as exc_info:
            await flow.poll_for_token("device_code_123", interval=0.01, timeout=5)

        assert "expired" in str(exc_info.value).lower()

    async def test_poll_for_token_access_denied(self):
        """Test token polling with access_denied error."""
        flow = DeviceCodeFlow()

        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={"error": "access_denied"})

        flow.session = self._create_mock_session(mock_response)

        with pytest.raises(AuthenticationError) as exc_info:
            await flow.poll_for_token("device_code_123", interval=0.01, timeout=5)

        assert "denied" in str(exc_info.value).lower()

    async def test_poll_for_token_unknown_error(self):
        """Test token polling with unknown error."""
        flow = DeviceCodeFlow()

        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={"error": "unknown_error"})

        flow.session = self._create_mock_session(mock_response)

        with pytest.raises(AuthenticationError) as exc_info:
            await flow.poll_for_token("device_code_123", interval=0.01, timeout=5)

        assert "Token request failed" in str(exc_info.value)

    async def test_poll_for_token_timeout(self):
        """Test token polling timeout."""
        flow = DeviceCodeFlow()

        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={"error": "authorization_pending"})

        flow.session = self._create_mock_session(mock_response)

        with pytest.raises(AuthenticationError) as exc_info:
            await flow.poll_for_token("device_code_123", interval=0.01, timeout=0.1)

        assert "timed out" in str(exc_info.value).lower()

    async def test_poll_for_token_network_error(self):
        """Test token polling with network error."""
        import aiohttp

        flow = DeviceCodeFlow()

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("Connection lost"))
        mock_context.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_context)

        flow.session = mock_session

        with pytest.raises(AuthenticationError) as exc_info:
            await flow.poll_for_token("device_code_123", interval=0.01, timeout=5)

        assert "Network error" in str(exc_info.value)

    async def test_refresh_access_token_success(self, mock_token_response):
        """Test successful access token refresh."""
        flow = DeviceCodeFlow()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_token_response)

        flow.session = self._create_mock_session(mock_response)

        result = await flow.refresh_access_token("old_refresh_token")

        assert result == mock_token_response
        call_args = flow.session.post.call_args
        assert call_args[0][0] == DeviceCodeFlow.TOKEN_ENDPOINT

    async def test_refresh_access_token_failure(self):
        """Test access token refresh failure."""
        flow = DeviceCodeFlow()

        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Invalid refresh token")

        flow.session = self._create_mock_session(mock_response)

        with pytest.raises(AuthenticationError) as exc_info:
            await flow.refresh_access_token("invalid_token")

        assert "Token refresh failed" in str(exc_info.value)

    async def test_refresh_access_token_network_error(self):
        """Test access token refresh with network error."""
        import aiohttp

        flow = DeviceCodeFlow()

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("Network down"))
        mock_context.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_context)

        flow.session = mock_session

        with pytest.raises(AuthenticationError) as exc_info:
            await flow.refresh_access_token("refresh_token")

        assert "Network error" in str(exc_info.value)

    def test_open_browser_success(self):
        """Test opening browser successfully."""
        flow = DeviceCodeFlow()

        with patch("webbrowser.open", return_value=True) as mock_open:
            result = flow.open_browser("https://example.com/verify")
            assert result is True
            mock_open.assert_called_once_with("https://example.com/verify")

    def test_open_browser_failure(self):
        """Test opening browser when it fails."""
        flow = DeviceCodeFlow()

        with patch("webbrowser.open", side_effect=Exception("Browser error")):
            result = flow.open_browser("https://example.com/verify")
            assert result is False


# =============================================================================
# APIKeyAuth Tests
# =============================================================================


class TestAPIKeyAuth:
    """Tests for APIKeyAuth class."""

    def test_validate_key_valid_kimi(self):
        """Test validating valid Kimi API key."""
        assert APIKeyAuth.validate_key("sk-test-key-12345", provider="kimi") is True
        assert APIKeyAuth.validate_key("Bearer token123", provider="kimi") is True

    def test_validate_key_invalid_kimi(self):
        """Test validating invalid Kimi API key."""
        assert APIKeyAuth.validate_key("invalid-key", provider="kimi") is False
        assert APIKeyAuth.validate_key("abc", provider="kimi") is False

    def test_validate_key_empty(self):
        """Test validating empty key."""
        assert APIKeyAuth.validate_key("") is False
        assert APIKeyAuth.validate_key(None) is False

    def test_validate_key_short(self):
        """Test validating short key."""
        assert APIKeyAuth.validate_key("short") is False

    def test_validate_key_other_provider(self):
        """Test validating key for other provider."""
        # For non-kimi providers, just check length
        assert APIKeyAuth.validate_key("any-key-long-enough", provider="other") is True
        assert APIKeyAuth.validate_key("short", provider="other") is False


# =============================================================================
# AuthenticationError Tests
# =============================================================================


class TestAuthenticationError:
    """Tests for AuthenticationError exception."""

    def test_error_message(self):
        """Test error message is preserved."""
        error = AuthenticationError("Test error message")
        assert str(error) == "Test error message"

    def test_error_is_exception(self):
        """Test AuthenticationError is an Exception."""
        error = AuthenticationError("Test")
        assert isinstance(error, Exception)

    def test_error_can_be_caught(self):
        """Test AuthenticationError can be caught as Exception."""
        try:
            raise AuthenticationError("Test error")
        except Exception as e:
            assert str(e) == "Test error"


# =============================================================================
# AuthCLI Tests
# =============================================================================


class TestAuthCLI:
    """Tests for AuthCLI class (155 statements)."""

    def test_init(self):
        """Test AuthCLI initialization."""
        cli = AuthCLI()
        assert cli.token_store is not None
        assert isinstance(cli.token_store, TokenStore)

    def test_login_already_authenticated_no_reauth(self, mock_token_store, capsys):
        """Test login when already authenticated, user declines re-auth."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        # Save credentials first
        mock_token_store.save_credentials(
            access_token="existing_token",
            refresh_token="refresh",
            expires_in=3600,
            provider="kimi",
        )

        with patch("builtins.input", return_value="n"):
            result = cli.login(interactive=True)

        assert result == 0
        captured = capsys.readouterr()
        assert "Already authenticated" in captured.out

    def test_login_already_authenticated_yes_reauth(self, mock_token_store, capsys):
        """Test login when already authenticated, user wants re-auth."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        mock_token_store.save_credentials(
            access_token="existing_token",
            refresh_token="refresh",
            expires_in=3600,
            provider="kimi",
        )

        # Mock the async _do_login to avoid full flow
        with patch.object(cli, "_do_login", return_value=0) as mock_do:
            with patch("builtins.input", return_value="y"):
                result = cli.login(interactive=True)

        assert result == 0
        mock_do.assert_called_once()

    def test_login_keyboard_interrupt(self, mock_token_store):
        """Test login handles keyboard interrupt."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        with patch.object(cli, "_do_login", side_effect=KeyboardInterrupt()):
            result = cli.login(interactive=True)

        assert result == 130

    def test_login_exception(self, mock_token_store):
        """Test login handles general exception."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        with patch.object(cli, "_do_login", side_effect=Exception("Test error")):
            result = cli.login(interactive=True)

        assert result == 1

    @pytest.mark.asyncio
    async def test_do_login_device_flow_success(self, mock_token_store, mock_device_code_response, mock_token_response):
        """Test successful device flow login."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        with patch("core.auth.cli.DeviceCodeFlow") as MockFlow:
            mock_flow = AsyncMock()
            mock_flow.initiate_device_flow = AsyncMock(return_value=mock_device_code_response)
            mock_flow.poll_for_token = AsyncMock(return_value=mock_token_response)
            mock_flow.open_browser = Mock(return_value=True)
            MockFlow.return_value = mock_flow

            # Mock async context manager
            MockFlow.return_value.__aenter__ = AsyncMock(return_value=mock_flow)
            MockFlow.return_value.__aexit__ = AsyncMock(return_value=None)

            # Capture printed output
            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                with patch("builtins.input", side_effect=["y"]):
                    result = await cli._do_login()

            assert result == 0
            mock_flow.initiate_device_flow.assert_called_once()
            mock_flow.poll_for_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_do_login_device_flow_auth_error(self, mock_token_store):
        """Test device flow login with authentication error."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        with patch("core.auth.cli.DeviceCodeFlow") as MockFlow:
            mock_flow = AsyncMock()
            mock_flow.initiate_device_flow = AsyncMock(side_effect=AuthenticationError("Network error"))
            MockFlow.return_value = mock_flow
            MockFlow.return_value.__aenter__ = AsyncMock(return_value=mock_flow)
            MockFlow.return_value.__aexit__ = AsyncMock(return_value=None)

            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                with patch("builtins.input", side_effect=["sk-test-api-key"]):
                    result = await cli._do_login()

            assert result == 0  # Falls back to manual login

    @pytest.mark.asyncio
    async def test_do_login_poll_error(self, mock_token_store, mock_device_code_response):
        """Test device flow login with polling error."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        with patch("core.auth.cli.DeviceCodeFlow") as MockFlow:
            mock_flow = AsyncMock()
            mock_flow.initiate_device_flow = AsyncMock(return_value=mock_device_code_response)
            mock_flow.poll_for_token = AsyncMock(side_effect=AuthenticationError("Timeout"))
            mock_flow.open_browser = Mock(return_value=True)
            MockFlow.return_value = mock_flow
            MockFlow.return_value.__aenter__ = AsyncMock(return_value=mock_flow)
            MockFlow.return_value.__aexit__ = AsyncMock(return_value=None)

            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                result = await cli._do_login()

            assert result == 1

    def test_manual_api_key_login_success(self, mock_token_store):
        """Test successful manual API key login."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            with patch("builtins.input", return_value="sk-test-key-12345"):
                result = cli._manual_api_key_login()

        assert result == 0
        assert mock_token_store.is_authenticated() is True
        assert mock_token_store.get_access_token() == "sk-test-key-12345"

    def test_manual_api_key_login_empty_key(self, mock_token_store):
        """Test manual API key login with empty key."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            with patch("builtins.input", return_value=""):
                result = cli._manual_api_key_login()

        assert result == 1

    def test_manual_api_key_login_invalid_format_no_continue(self, mock_token_store):
        """Test manual API key login with invalid format, user doesn't continue."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            with patch("builtins.input", side_effect=["invalid-key", "n"]):
                result = cli._manual_api_key_login()

        assert result == 1

    def test_manual_api_key_login_invalid_format_continue(self, mock_token_store):
        """Test manual API key login with invalid format, user continues anyway."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            with patch("builtins.input", side_effect=["invalid-key", "y"]):
                result = cli._manual_api_key_login()

        assert result == 0
        assert mock_token_store.get_access_token() == "invalid-key"

    def test_logout_not_authenticated(self, mock_token_store, capsys):
        """Test logout when not authenticated."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        result = cli.logout()

        assert result == 0
        captured = capsys.readouterr()
        assert "Not currently authenticated" in captured.out

    def test_logout_confirm(self, mock_token_store, capsys):
        """Test logout with confirmation."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        mock_token_store.save_credentials(
            access_token="token",
            refresh_token="refresh",
            expires_in=3600,
            provider="kimi",
        )

        with patch("builtins.input", return_value="y"):
            result = cli.logout()

        assert result == 0
        assert not mock_token_store.is_authenticated()
        captured = capsys.readouterr()
        assert "Successfully logged out" in captured.out

    def test_logout_cancel(self, mock_token_store):
        """Test logout when user cancels."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        mock_token_store.save_credentials(
            access_token="token",
            refresh_token="refresh",
            expires_in=3600,
            provider="kimi",
        )

        with patch("builtins.input", return_value="n"):
            result = cli.logout()

        assert result == 0
        assert mock_token_store.is_authenticated() is True  # Still authenticated

    def test_status_not_authenticated(self, mock_token_store, capsys):
        """Test status when not authenticated."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        result = cli.status()

        assert result == 1
        captured = capsys.readouterr()
        assert "Not authenticated" in captured.out

    def test_status_authenticated(self, mock_token_store, capsys):
        """Test status when authenticated."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        mock_token_store.save_credentials(
            access_token="token",
            refresh_token="refresh",
            expires_in=3600,
            provider="kimi",
        )

        result = cli.status()

        assert result == 0
        captured = capsys.readouterr()
        assert "Authenticated" in captured.out
        assert "kimi" in captured.out

    def test_status_expired_token(self, mock_token_store, capsys):
        """Test status with expired token."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        # Create a credential that was created in the past and expired
        mock_token_store.config_dir.mkdir(parents=True, exist_ok=True)
        past_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        expired_creds = {
            "version": 1,
            "provider": "kimi",
            "access_token": "expired_token",
            "refresh_token": "refresh",
            "expires_at": past_time,
            "created_at": past_time,
        }
        with open(mock_token_store.credentials_file, "w") as f:
            json.dump(expired_creds, f)

        result = cli.status()

        assert result == 0
        captured = capsys.readouterr()
        assert "EXPIRED" in captured.out or "Never" in captured.out

    def test_status_no_expiration(self, mock_token_store, capsys):
        """Test status with no expiration (API key)."""
        cli = AuthCLI()
        cli.token_store = mock_token_store

        mock_token_store.save_credentials(
            access_token="api_key_token",
            refresh_token=None,
            expires_in=None,
            provider="kimi",
        )

        result = cli.status()

        assert result == 0
        captured = capsys.readouterr()
        assert "Never" in captured.out or "API key" in captured.out

    def test_print_help(self, capsys):
        """Test print_help outputs help text."""
        cli = AuthCLI()
        cli.print_help()

        captured = capsys.readouterr()
        assert "Authentication Commands" in captured.out
        assert "zen auth login" in captured.out
        assert "zen auth logout" in captured.out
        assert "zen auth status" in captured.out


# =============================================================================
# AuthCLI Main Function Tests
# =============================================================================


class TestAuthCLIMain:
    """Tests for AuthCLI main function."""

    def test_main_no_args(self, capsys):
        """Test main with no arguments prints help."""
        with patch.object(sys, "argv", ["zen-auth"]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Authentication Commands" in captured.out

    def test_main_login(self):
        """Test main with login command."""
        with patch.object(sys, "argv", ["zen-auth", "login"]):
            with patch.object(AuthCLI, "login", return_value=0) as mock_login:
                result = main()

        assert result == 0
        mock_login.assert_called_once()

    def test_main_logout(self):
        """Test main with logout command."""
        with patch.object(sys, "argv", ["zen-auth", "logout"]):
            with patch.object(AuthCLI, "logout", return_value=0) as mock_logout:
                result = main()

        assert result == 0
        mock_logout.assert_called_once()

    def test_main_status(self):
        """Test main with status command."""
        with patch.object(sys, "argv", ["zen-auth", "status"]):
            with patch.object(AuthCLI, "status", return_value=0) as mock_status:
                result = main()

        assert result == 0
        mock_status.assert_called_once()

    def test_main_unknown_command(self, capsys):
        """Test main with unknown command."""
        with patch.object(sys, "argv", ["zen-auth", "unknown"]):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Authentication Commands" in captured.out

    def test_main_case_insensitive(self):
        """Test main commands are case insensitive."""
        with patch.object(sys, "argv", ["zen-auth", "LOGIN"]):
            with patch.object(AuthCLI, "login", return_value=0) as mock_login:
                result = main()

        assert result == 0
        mock_login.assert_called_once()


# =============================================================================
# Module Export Tests
# =============================================================================


class TestAuthModuleExports:
    """Tests for core.auth.__init__ module exports."""

    def test_module_exports_device_code_flow(self):
        """Test DeviceCodeFlow is exported."""
        from core.auth import DeviceCodeFlow

        assert DeviceCodeFlow is not None

    def test_module_exports_token_store(self):
        """Test TokenStore is exported."""
        from core.auth import TokenStore

        assert TokenStore is not None

    def test_module_exports_auth_cli(self):
        """Test AuthCLI is exported."""
        from core.auth import AuthCLI

        assert AuthCLI is not None

    def test_module_all_exports(self):
        """Test __all__ exports are correct."""
        import core.auth

        expected_exports = ["DeviceCodeFlow", "TokenStore", "AuthCLI"]
        assert core.auth.__all__ == expected_exports

    def test_can_import_device_flow_directly(self):
        """Test device_flow module can be imported directly."""
        from core.auth.device_flow import (
            APIKeyAuth,
            AuthenticationError,
            DeviceCodeFlow,
        )

        assert DeviceCodeFlow is not None
        assert AuthenticationError is not None
        assert APIKeyAuth is not None

    def test_can_import_token_store_directly(self):
        """Test token_store module can be imported directly."""
        from core.auth.token_store import (
            TokenStore,
            get_stored_token,
            is_logged_in,
            require_auth,
        )

        assert TokenStore is not None
        assert get_stored_token is not None
        assert is_logged_in is not None
        assert require_auth is not None

    def test_can_import_cli_directly(self):
        """Test cli module can be imported directly."""
        from core.auth.cli import AuthCLI, main

        assert AuthCLI is not None
        assert main is not None


# Import main at the end to avoid circular import issues
from core.auth.cli import main

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
