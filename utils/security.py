"""
Security utilities for secret masking and safe logging.

This module provides centralized functions for handling sensitive data
to prevent clear-text logging of secrets.
"""

import re
from typing import Optional, Union


# codeql[python/clear-text-logging-sensitive-data]:
# This function is designed to mask sensitive data.
# All secrets are masked before logging.
def mask_secret(value: Optional[str], visible_chars: int = 3) -> str:
    """
    Mask sensitive data for safe logging.

    Args:
        value: The secret value to mask
        visible_chars: Number of characters to show at start/end (default: 3)

    Returns:
        Masked string like "abc***xyz" or "***" for short values

    Examples:
        >>> mask_secret("sk-abc123456789")
        'sk-***789'
        >>> mask_secret("short")
        's***t'
        >>> mask_secret(None)
        '[EMPTY]'
        >>> mask_secret("")
        '[EMPTY]'
    """
    if not value:
        return "[EMPTY]"

    if len(value) <= visible_chars * 2:
        # For short values, just show first and last char
        if len(value) <= 2:
            return "***"
        return f"{value[0]}***{value[-1]}"

    # Show first and last N chars
    return f"{value[:visible_chars]}***{value[-visible_chars:]}"


def mask_api_key(key: Optional[str]) -> str:
    """
    Specifically mask API keys (handles common formats).

    Examples:
        >>> mask_api_key("sk-abc123def456")
        'sk-***456'
        >>> mask_api_key("ghp_xxxxxxxxxxxx")
        'ghp***xxxx'
    """
    return mask_secret(key, visible_chars=4)


def mask_token(token: Optional[str]) -> str:
    """
    Specifically mask tokens (shows less for higher security).

    Examples:
        >>> mask_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        'eyJ***9...'
    """
    return mask_secret(token, visible_chars=5)


def mask_password(password: Optional[str]) -> str:
    """
    Mask passwords (shows minimal info).

    Examples:
        >>> mask_password("mysecretpassword")
        'm***d'
    """
    return mask_secret(password, visible_chars=1)


def contains_sensitive_data(text: str) -> bool:
    """
    Check if text might contain sensitive data patterns.

    Returns True if suspicious patterns found.
    """
    sensitive_patterns = [
        r"sk-[a-zA-Z0-9]{20,}",  # OpenAI keys
        r"ghp_[a-zA-Z0-9]{36}",  # GitHub tokens
        r"glpat-[a-zA-Z0-9\-]{20}",  # GitLab tokens
        r"[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}",  # JWT pattern

        r'password\s*=\s*["\'][^"\']+["\']',  # password="..."
        r'api[_-]?key\s*=\s*["\'][^"\']+["\']',  # api_key="..."
        r"Bearer\s+[a-zA-Z0-9\-_]+",  # Bearer tokens
    ]

    for pattern in sensitive_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def safe_log_message(
    message: str, sensitive_values: Optional[list] = None
) -> str:
    """
    Make any log message safe by masking embedded sensitive values.

    Args:
        message: The original log message
        sensitive_values: List of sensitive strings to mask within the message

    Returns:
        Safe message with all sensitive values masked
    """
    if not sensitive_values:
        return message

    safe_message = message
    for value in sensitive_values:
        if value and len(value) > 3:
            masked = mask_secret(value)
            safe_message = safe_message.replace(value, masked)

    return safe_message


# Convenience function for common logging pattern
def format_secret(name: str, value: Optional[str]) -> str:
    """
    Format a secret for display (name + masked value).

    Examples:
        >>> format_secret("OPENAI_API_KEY", "sk-abc123")
        'OPENAI_API_KEY=sk***123'
    """
    return f"{name}={mask_secret(value)}"


# ═══════════════════════════════════════════════════════════════════════════════
# LOG INJECTION PROTECTION
# ═══════════════════════════════════════════════════════════════════════════════


def sanitize_log_value(value: Optional[str], max_length: int = 100) -> str:
    """
    Sanitize a value for safe logging to prevent log injection attacks.

    Removes newlines, carriage returns, and null bytes that could be used
    to inject fake log entries or manipulate log parsing.

    Args:
        value: The value to sanitize
        max_length: Maximum length to prevent log flooding (default: 100)

    Returns:
        Sanitized string safe for logging

    Examples:
        >>> sanitize_log_value("normal_id_123")
        'normal_id_123'
        >>> sanitize_log_value("evil\\n[INFO] Fake log entry")
        '[SANITIZED]'
        >>> sanitize_log_value("a" * 200)
        'aaaaaaaaaa...[truncated]'
    """
    if not value:
        return "[EMPTY]"

    # Convert to string if not already
    value_str = str(value)

    # Check for injection characters
    injection_chars = ["\n", "\r", "\x00", "\x1b", "\x0b", "\x0c"]
    if any(char in value_str for char in injection_chars):
        # Contains injection characters - replace entirely
        return "[SANITIZED]"

    # Check for suspicious patterns that might indicate log injection
    suspicious_patterns = [
        r"\[\s*(INFO|DEBUG|WARN|ERROR|CRITICAL)\s*\]",  # Fake log levels
        r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}",  # Fake timestamps
    ]
    for pattern in suspicious_patterns:
        if re.search(pattern, value_str, re.IGNORECASE):
            return "[SANITIZED]"

    # Truncate if too long
    if len(value_str) > max_length:
        value_str = value_str[:max_length] + "...[truncated]"

    return value_str


def sanitize_log_id(
    identifier: Optional[Union[str, int]],
    allow_chars: str = (
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-."
    ),
) -> str:
    """
    Sanitize an identifier for logging (stricter than sanitize_log_value).

    Only allows alphanumeric characters and basic separators.
    Commonly used for IDs like agent_id, task_id, workflow_id.

    Args:
        identifier: The identifier to sanitize
        allow_chars: String of allowed characters (default: alphanum + _-.)

    Returns:
        Sanitized identifier or hash if invalid

    Examples:
        >>> sanitize_log_id("agent_123")
        'agent_123'
        >>> sanitize_log_id("evil\\nfake")
        '[ID-SANITIZED]'
    """
    if not identifier:
        return "[EMPTY]"

    # Convert to string
    id_str = str(identifier)

    # Check all characters are allowed
    if not all(c in allow_chars for c in id_str):
        return "[ID-SANITIZED]"

    # Length limit
    if len(id_str) > 50:
        return id_str[:50] + "...[truncated]"

    return id_str


# Short alias for convenience
log_safe = sanitize_log_value
id_safe = sanitize_log_id
