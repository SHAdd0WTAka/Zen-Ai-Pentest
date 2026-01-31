"""API Cache Module (Stub)"""
from typing import Any, Optional


_cache: dict = {}


def init_cache() -> None:
    """Initialize cache (stub)"""
    _cache.clear()


def close_cache() -> None:
    """Close cache (stub)"""
    _cache.clear()


def get_cache(key: str) -> Optional[Any]:
    """Get value from cache (stub)"""
    return _cache.get(key)


def set_cache(key: str, value: Any, ttl: int = 300) -> None:
    """Set value in cache (stub)"""
    _cache[key] = value
