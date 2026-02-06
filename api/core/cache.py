"""
API Cache Module

Provides caching with Redis support (production) and in-memory fallback (development).
"""
import os
import json
import logging
from typing import Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.info("Redis not available, using in-memory cache")

# In-memory cache fallback
_memory_cache: dict = {}
_memory_cache_expiry: dict = {}

# Redis client (initialized lazily)
_redis_client = None


def get_redis_client() -> Optional[Any]:
    """Get or create Redis client"""
    global _redis_client
    
    if not REDIS_AVAILABLE or _redis_client is not None:
        return _redis_client
    
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            health_check_interval=30
        )
        # Test connection
        _redis_client.ping()
        logger.info(f"Connected to Redis at {redis_url}")
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Using in-memory cache.")
        _redis_client = None
        return None


def init_cache() -> None:
    """Initialize cache"""
    _memory_cache.clear()
    _memory_cache_expiry.clear()
    
    # Try to connect to Redis
    client = get_redis_client()
    if client:
        logger.info("Cache initialized with Redis backend")
    else:
        logger.info("Cache initialized with in-memory backend")


def close_cache() -> None:
    """Close cache connections"""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None
    _memory_cache.clear()
    _memory_cache_expiry.clear()


def _is_memory_key_expired(key: str) -> bool:
    """Check if an in-memory key has expired"""
    if key not in _memory_cache_expiry:
        return False
    return datetime.utcnow() > _memory_cache_expiry[key]


def _cleanup_expired_memory_keys():
    """Remove expired keys from memory cache"""
    expired_keys = [
        key for key in _memory_cache_expiry
        if _is_memory_key_expired(key)
    ]
    for key in expired_keys:
        _memory_cache.pop(key, None)
        _memory_cache_expiry.pop(key, None)


def get_cache(key: str) -> Optional[Any]:
    """
    Get value from cache.
    
    Tries Redis first, falls back to in-memory cache.
    """
    # Try Redis first
    client = get_redis_client()
    if client:
        try:
            value = client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
        except Exception as e:
            logger.debug(f"Redis get error: {e}")
    
    # Fall back to memory cache
    _cleanup_expired_memory_keys()
    
    if key in _memory_cache and not _is_memory_key_expired(key):
        return _memory_cache[key]
    
    return None


def set_cache(key: str, value: Any, ttl: int = 300) -> None:
    """
    Set value in cache.
    
    Args:
        key: Cache key
        value: Value to cache (must be JSON serializable)
        ttl: Time to live in seconds (default: 5 minutes)
    """
    # Try Redis first
    client = get_redis_client()
    if client:
        try:
            serialized = json.dumps(value) if not isinstance(value, (str, bytes)) else value
            client.setex(key, ttl, serialized)
            return
        except Exception as e:
            logger.debug(f"Redis set error: {e}")
    
    # Fall back to memory cache
    _memory_cache[key] = value
    _memory_cache_expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)


def delete_cache(key: str) -> bool:
    """Delete key from cache"""
    deleted = False
    
    # Try Redis
    client = get_redis_client()
    if client:
        try:
            deleted = client.delete(key) > 0
        except Exception as e:
            logger.debug(f"Redis delete error: {e}")
    
    # Also remove from memory cache
    if key in _memory_cache:
        del _memory_cache[key]
        _memory_cache_expiry.pop(key, None)
        deleted = True
    
    return deleted


def clear_cache(pattern: str = "*") -> int:
    """
    Clear cache keys matching pattern.
    
    Args:
        pattern: Key pattern to match (Redis glob-style)
        
    Returns:
        Number of keys cleared
    """
    count = 0
    
    # Try Redis
    client = get_redis_client()
    if client:
        try:
            keys = client.keys(pattern)
            if keys:
                count = client.delete(*keys)
        except Exception as e:
            logger.debug(f"Redis clear error: {e}")
    
    # Clear matching memory cache keys
    if pattern == "*":
        count += len(_memory_cache)
        _memory_cache.clear()
        _memory_cache_expiry.clear()
    else:
        # Simple pattern matching for memory cache
        import fnmatch
        keys_to_remove = [
            key for key in _memory_cache
            if fnmatch.fnmatch(key, pattern)
        ]
        for key in keys_to_remove:
            del _memory_cache[key]
            _memory_cache_expiry.pop(key, None)
            count += 1
    
    return count


def get_cache_info() -> dict:
    """Get cache statistics and info"""
    info = {
        "backend": "redis" if get_redis_client() else "memory",
        "memory_keys": len(_memory_cache),
    }
    
    client = get_redis_client()
    if client:
        try:
            redis_info = client.info()
            info["redis_version"] = redis_info.get("redis_version")
            info["redis_keys"] = client.dbsize()
            info["used_memory_human"] = redis_info.get("used_memory_human")
        except Exception as e:
            info["redis_error"] = str(e)
    
    return info


# Decorator for caching function results
def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Cache TTL in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Build cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_value = get_cache(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            set_cache(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test cache
    init_cache()
    
    set_cache("test", {"foo": "bar"}, ttl=60)
    print(f"Get cache: {get_cache('test')}")
    
    print(f"Cache info: {get_cache_info()}")
    
    delete_cache("test")
    print(f"After delete: {get_cache('test')}")
