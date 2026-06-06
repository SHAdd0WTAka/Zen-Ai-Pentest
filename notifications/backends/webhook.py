"""
Generic Webhook Notification Backend for Zen-AI-Pentest

Supports custom webhook URLs with configurable headers and payload format.
Includes SSRF protection to prevent internal network access.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

# SSRF Protection: Block private IP ranges and internal hosts
BLOCKED_HOSTS: Tuple[str, ...] = (
    "localhost",
    "127.0.0.1",
    "::1",
    "0.0.0.0",  # nosec B104
)

BLOCKED_NETWORKS = [
    ("10.0.0.0", "10.255.255.255"),  # 10.0.0.0/8
    ("172.16.0.0", "172.31.255.255"),  # 172.16.0.0/12
    ("192.168.0.0", "192.168.255.255"),  # 192.168.0.0/16
    ("169.254.0.0", "169.254.255.255"),  # Link-local
    ("127.0.0.0", "127.255.255.255"),  # Loopback
]


class WebhookValidationError(Exception):
    """Raised when webhook URL fails validation"""

    pass


class WebhookBackend:
    """Generic Webhook Backend with SSRF protection and retry support"""

    def __init__(
        self,
        webhook_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
        max_retries: int = 3,
        verify_ssl: bool = True,
        allowed_hosts: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize Webhook backend.

        Args:
            webhook_url: Target webhook URL
            headers: Custom headers to include
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            verify_ssl: Verify SSL certificates
            allowed_hosts: Additional allowed host patterns (regex)

        Raises:
            WebhookValidationError: If URL fails SSRF validation
        """
        self._validate_url(webhook_url)
        self.webhook_url = webhook_url
        self.headers = headers or {}
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        self.allowed_hosts = allowed_hosts or []

    def _validate_url(self, url: str) -> None:
        """
        Validate URL for SSRF protection.

        Raises:
            WebhookValidationError: If URL is not allowed
        """
        if not url:
            raise WebhookValidationError("URL is required")

        parsed = urlparse(url)

        # Require HTTPS
        if parsed.scheme != "https":
            raise WebhookValidationError("Only HTTPS URLs are allowed for security reasons")

        if not parsed.hostname:
            raise WebhookValidationError("Invalid URL: no hostname found")

        hostname = parsed.hostname.lower()

        # Check blocked hosts
        if hostname in BLOCKED_HOSTS:
            raise WebhookValidationError(f"Host '{hostname}' is not allowed for security reasons")

        # Check blocked networks (simple string check for common cases)
        if hostname.startswith(
            (
                "10.",
                "192.168.",
                "172.16.",
                "172.17.",
                "172.18.",
                "172.19.",
                "172.20.",
                "172.21.",
                "172.22.",
                "172.23.",
                "172.24.",
                "172.25.",
                "172.26.",
                "172.27.",
                "172.28.",
                "172.29.",
                "172.30.",
                "172.31.",
                "127.",
                "0.",
                "169.254.",
            )
        ):
            raise WebhookValidationError("Private IP ranges are not allowed for security reasons")

    def send(
        self,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Send webhook notification.

        Args:
            payload: JSON payload to send
            headers: Additional headers for this request

        Returns:
            Dict with success status
        """
        # Merge headers
        request_headers = dict(self.headers)
        if headers:
            request_headers.update(headers)

        # Ensure Content-Type is set
        if "Content-Type" not in request_headers:
            request_headers["Content-Type"] = "application/json"

        # Add signature if secret is configured
        if "X-Webhook-Secret" in request_headers:
            import hashlib
            import hmac

            secret = request_headers.pop("X-Webhook-Secret")
            payload_bytes = json.dumps(payload).encode()
            signature = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
            request_headers["X-Signature"] = f"sha256={signature}"

        return self._send_with_retry(payload, request_headers)

    def send_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        custom_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send event notification.

        Args:
            event_type: Type of event
            data: Event data
            custom_payload: Optional custom payload structure

        Returns:
            Dict with success status
        """
        if custom_payload:
            payload = custom_payload
        else:
            # Standard event payload
            payload = {
                "event": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "source": "zen-ai-pentest",
                "data": data,
            }

        return self.send(payload)

    def _send_with_retry(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """Send with retry logic"""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                )

                # 2xx success
                if 200 <= response.status_code < 300:
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "attempt": attempt + 1,
                        "response": response.text[:500] if response.text else None,
                    }
                elif response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(f"Webhook rate limited, retrying after {retry_after}s")
                    import time

                    time.sleep(retry_after)
                    last_error = f"Rate limited (HTTP {response.status_code})"
                else:
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.warning(f"Webhook request failed: {last_error}")

            except requests.RequestException as e:
                last_error = str(e)
                logger.warning(f"Webhook request error (attempt {attempt + 1}): {e}")

            # Exponential backoff
            if attempt < self.max_retries - 1:
                import time

                time.sleep(2**attempt)

        return {
            "success": False,
            "error": last_error,
            "attempts": self.max_retries,
        }

    def test(self) -> Dict[str, Any]:
        """Test the webhook connection"""
        payload = {
            "event": "test",
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "source": "zen-ai-pentest",
            "message": "This is a test notification from Zen-AI-Pentest",
            "data": {
                "test": True,
                "notification_type": "webhook_test",
            },
        }

        return self.send(payload)


class WebhookBackendFactory:
    """Factory for creating webhook backends with different configurations"""

    @staticmethod
    def create_discord_compat(webhook_url: str, **kwargs) -> WebhookBackend:
        """Create webhook backend with Discord-compatible payload"""
        headers = kwargs.pop("headers", {})
        headers.setdefault("Content-Type", "application/json")
        return WebhookBackend(webhook_url, headers=headers, **kwargs)

    @staticmethod
    def create_slack_compat(webhook_url: str, **kwargs) -> WebhookBackend:
        """Create webhook backend with Slack-compatible payload"""
        headers = kwargs.pop("headers", {})
        headers.setdefault("Content-Type", "application/json")
        return WebhookBackend(webhook_url, headers=headers, **kwargs)

    @staticmethod
    def create_with_signature(webhook_url: str, secret: str, **kwargs) -> WebhookBackend:
        """Create webhook backend with HMAC signature"""
        headers = kwargs.pop("headers", {})
        headers["X-Webhook-Secret"] = secret
        return WebhookBackend(webhook_url, headers=headers, **kwargs)
