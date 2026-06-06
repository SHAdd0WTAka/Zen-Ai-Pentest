"""
🔐 ZEN-ALPHA Secure Authentication Integration
Combines LocalPortManager (Reverse Proxy) + Device Auth Bridge (OAuth)

Features:
- No hardcoded API keys (Device Auth Bridge)
- Reverse proxy for metadata protection (LocalPortManager)
- Browser-based login flow
- Automatic token refresh
"""

import base64
import hashlib
import secrets
import sys
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))

# Import Device Auth Bridge
from kimi_auth_bridge import KimiAuthBridge

# Import LocalPortManager
from localportmanager import LocalPortManager


@dataclass
class SecureSession:
    """Secure session with device-bound authentication"""

    session_id: str
    device_id: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    user_agent: str = ""
    ip_address: str = ""
    created_at: datetime = None
    last_used: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.last_used is None:
            self.last_used = datetime.now(timezone.utc)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Convert datetime to ISO format
        for key in ["expires_at", "created_at", "last_used"]:
            if data[key]:
                data[key] = data[key].isoformat()
        return data


class SecureAuthManager:
    """
    Manages secure authentication combining:
    - LocalPortManager (metadata protection)
    - Device Auth Bridge (OAuth without hardcoded keys)
    """

    def __init__(
        self,
        proxy_port: int = 1355,
        api_port: int = 8000,
        session_timeout: int = 3600,  # 1 hour
    ):
        self.proxy_port = proxy_port
        self.api_port = api_port
        self.session_timeout = session_timeout

        # Initialize components
        self.port_manager = LocalPortManager(proxy_port=proxy_port)
        self.auth_bridge = KimiAuthBridge()

        # Session storage
        self.sessions: Dict[str, SecureSession] = {}
        self._lock = threading.Lock()

        # Device ID (unique per installation)
        self.device_id = self._get_or_create_device_id()

    def _get_or_create_device_id(self) -> str:
        """Get or create unique device ID"""
        device_id_file = Path.home() / ".zen-alpha" / "device.id"
        device_id_file.parent.mkdir(parents=True, exist_ok=True)

        if device_id_file.exists():
            return device_id_file.read_text().strip()

        # Generate new device ID
        device_id = secrets.token_urlsafe(32)
        device_id_file.write_text(device_id)
        return device_id

    def setup_reverse_proxy(self) -> bool:
        """
        Setup LocalPortManager as reverse proxy
        Protects metadata by routing through localhost
        """
        try:
            # Register the API backend
            self.port_manager.register_service(
                name="zen-alpha-api",
                command="python -m uvicorn api.main:app --port {port}",
                auto_start=True,
            )

            print("✅ Reverse proxy configured:")
            print(f"   → API accessible at: http://zen-alpha-api.localhost:{self.proxy_port}")
            print("   → Protected from direct metadata exposure")

            return True

        except Exception as e:
            print(f"⚠️  Reverse proxy setup failed: {e}")
            print("   Falling back to direct API access")
            return False

    def check_device_auth(self) -> Tuple[bool, Optional[str]]:
        """
        Check if device is authenticated via Kimi CLI
        Returns: (is_authenticated, token_preview)
        """
        if not self.auth_bridge.is_authenticated():
            return False, None

        self.auth_bridge.get_access_token()
        preview = self.auth_bridge.get_token_preview()

        return True, preview

    def initiate_browser_login(self) -> Dict[str, Any]:
        """
        Initiates browser-based login flow
        Returns login URL and session info
        """
        # Generate PKCE parameters
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().rstrip("=")

        state = secrets.token_urlsafe(32)

        # Create local callback server
        callback_port = self._find_free_port()

        # Build authorization URL
        auth_params = {
            "response_type": "code",
            "client_id": "kimi_cli",
            "redirect_uri": f"http://localhost:{callback_port}/callback",
            "scope": "read write",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "device_id": self.device_id,
        }

        # Note: Actual URL would be from Kimi's OAuth server
        # This is a placeholder for the flow
        auth_url = f"https://kimi.com/oauth/authorize?{urlencode(auth_params)}"

        return {
            "auth_url": auth_url,
            "callback_port": callback_port,
            "state": state,
            "code_verifier": code_verifier,
            "device_id": self.device_id,
        }

    def _find_free_port(self, start: int = 5000, end: int = 6000) -> int:
        """Find a free port for callback server"""
        import socket

        for port in range(start, end):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("127.0.0.1", port))
                    return port
            except OSError:
                continue
        raise RuntimeError("No free port found")

    def create_session(self, access_token: str, user_agent: str = "", ip_address: str = "") -> SecureSession:
        """Create new secure session"""
        with self._lock:
            session = SecureSession(
                session_id=secrets.token_urlsafe(32),
                device_id=self.device_id,
                access_token=access_token,
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=self.session_timeout),
                user_agent=user_agent,
                ip_address=ip_address,
            )
            self.sessions[session.session_id] = session
            return session

    def validate_session(self, session_id: str) -> Optional[SecureSession]:
        """Validate and return session if valid"""
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return None

            if session.is_expired():
                del self.sessions[session_id]
                return None

            session.last_used = datetime.now(timezone.utc)
            return session

    def revoke_session(self, session_id: str) -> bool:
        """Revoke a session"""
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False

    def get_active_sessions(self) -> list:
        """Get all active sessions"""
        with self._lock:
            # Clean expired sessions
            now = datetime.now(timezone.utc)
            expired = [sid for sid, s in self.sessions.items() if s.expires_at and s.expires_at < now]
            for sid in expired:
                del self.sessions[sid]

            return [s.to_dict() for s in self.sessions.values()]

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        if not self.auth_bridge.is_authenticated():
            return {}

        return self.auth_bridge.get_auth_headers()

    def cleanup(self):
        """Cleanup resources"""
        # Clear all sessions
        with self._lock:
            self.sessions.clear()

        # Stop reverse proxy if running
        try:
            self.port_manager.stop_all_services()
        except Exception:
            pass


# FastAPI Integration
class SecureAuthMiddleware:
    """FastAPI middleware for secure authentication"""

    def __init__(self, auth_manager: SecureAuthManager):
        self.auth_manager = auth_manager

    async def __call__(self, request, call_next):
        from fastapi.responses import JSONResponse

        # Skip auth for public endpoints
        public_paths = [
            "/health",
            "/auth/login",
            "/auth/callback",
            "/docs",
            "/openapi.json",
        ]
        if any(request.url.path.startswith(p) for p in public_paths):
            return await call_next(request)

        # Check session cookie
        session_id = request.cookies.get("zen_session")
        if not session_id:
            return JSONResponse(
                status_code=401,
                content={"error": "No session", "login_url": "/auth/login"},
            )

        # Validate session
        session = self.auth_manager.validate_session(session_id)
        if not session:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or expired session"},
            )

        # Add session to request state
        request.state.session = session

        return await call_next(request)


# Singleton instance
_secure_auth_manager: Optional[SecureAuthManager] = None


def get_secure_auth_manager() -> SecureAuthManager:
    """Get or create singleton SecureAuthManager"""
    global _secure_auth_manager
    if _secure_auth_manager is None:
        _secure_auth_manager = SecureAuthManager()
    return _secure_auth_manager


if __name__ == "__main__":
    # Demo usage
    print("🔐 ZEN-ALPHA Secure Authentication")
    print("=" * 50)

    auth = get_secure_auth_manager()

    # Check device auth
    is_auth, preview = auth.check_device_auth()
    print(f"\nDevice Auth Status: {'✅ Authenticated' if is_auth else '❌ Not authenticated'}")
    if preview:
        print(f"Token Preview: {preview}")

    # Setup reverse proxy
    print("\nSetting up reverse proxy...")
    auth.setup_reverse_proxy()

    print("\n✨ Ready for secure operations!")
