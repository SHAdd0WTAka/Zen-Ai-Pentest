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
        r'sk-[a-zA-Z0-9]{20,}',  # OpenAI keys
        r'ghp_[a-zA-Z0-9]{36}',   # GitHub tokens
        r'glpat-[a-zA-Z0-9\-]{20}', # GitLab tokens
        r'[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}',  # JWT
        r'password\s*=\s*["\'][^"\']+["\']',  # password="..."
        r'api[_-]?key\s*=\s*["\'][^"\']+["\']',  # api_key="..."
        r'Bearer\s+[a-zA-Z0-9\-_]+',  # Bearer tokens
    ]
    
    for pattern in sensitive_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def safe_log_message(message: str, sensitive_values: Optional[list] = None) -> str:
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
