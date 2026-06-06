"""GitHub App authentication utilities."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx
import jwt

logger = logging.getLogger(__name__)


class GitHubAuth:
    """Handles GitHub App JWT and Installation Token management."""

    def __init__(self, app_id: str, private_key: str):
        """Initialize GitHub authentication.

        Args:
            app_id: GitHub App ID
            private_key: GitHub App private key (PEM format)
        """
        self.app_id = app_id
        self.private_key = private_key
        self._token_cache: Dict[int, Dict[str, Any]] = {}

    def generate_jwt(self) -> str:
        """Generate JWT for GitHub App authentication.

        Returns:
            JWT token string
        """
        now = datetime.now(timezone.utc)
        payload = {"iat": now, "exp": now + timedelta(minutes=10), "iss": self.app_id}

        return jwt.encode(payload, self.private_key, algorithm="RS256")

    async def get_installation_token(self, installation_id: int, repositories: Optional[list] = None) -> str:
        """Get access token for an installation.

        Args:
            installation_id: GitHub App installation ID
            repositories: Optional list of repository names to scope token to

        Returns:
            Installation access token
        """
        # Check cache
        if installation_id in self._token_cache:
            cached = self._token_cache[installation_id]
            if cached["expires_at"] > datetime.now(timezone.utc) + timedelta(minutes=5):
                logger.debug(f"Using cached token for installation {installation_id}")
                return cached["token"]

        # Generate new token
        jwt_token = self.generate_jwt()

        url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        headers = {"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github.v3+json"}

        data = {}
        if repositories:
            data["repositories"] = repositories

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()

                result = response.json()
                token = result["token"]
                expires_at = datetime.fromisoformat(result["expires_at"].replace("Z", "+00:00"))

                # Cache token
                self._token_cache[installation_id] = {"token": token, "expires_at": expires_at}

                logger.info(f"Generated new token for installation {installation_id}")
                return token

            except httpx.HTTPError as e:
                logger.error(f"Failed to get installation token: {e}")
                raise

    async def verify_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify GitHub webhook signature.

        Args:
            payload: Raw request body
            signature: X-Hub-Signature-256 header value
            secret: Webhook secret

        Returns:
            True if signature is valid
        """
        import hashlib
        import hmac

        expected_signature = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        return hmac.compare_digest(expected_signature, signature)
