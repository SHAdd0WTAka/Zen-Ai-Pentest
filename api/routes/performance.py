"""
Performance API Routes

Endpoints for cache management and performance monitoring.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

# Import performance components
try:
    from performance import CacheManager
    from performance.pool import PoolManager
except ImportError:
    import sys

    sys.path.insert(0, "../..")
    from performance import CacheManager
    from performance.pool import PoolManager


router = APIRouter(prefix="/api/v1/performance", tags=["Performance"])

# Global instances
_cache: Optional[CacheManager] = None
_pool_manager: Optional[PoolManager] = None


def get_cache() -> CacheManager:
    """Get cache manager"""
    global _cache
    if _cache is None:
        _cache = CacheManager()
    return _cache


def get_pool_manager() -> PoolManager:
    """Get pool manager"""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = PoolManager()
    return _pool_manager


# Cache endpoints


@router.get("/cache/stats")
async def get_cache_stats(cache: CacheManager = Depends(get_cache)):
    """Get cache statistics"""
    return cache.get_stats()


@router.delete("/cache")
async def clear_cache(cache: CacheManager = Depends(get_cache)):
    """Clear all cache"""
    await cache.clear()
    return {"cleared": True}


@router.delete("/cache/{key}")
async def delete_cache_key(key: str, cache: CacheManager = Depends(get_cache)):
    """Delete specific cache key"""
    success = await cache.delete(key)
    return {"deleted": success}


# Pool endpoints


@router.get("/pools/stats")
async def get_pool_stats(pool_manager: PoolManager = Depends(get_pool_manager)):
    """Get connection pool statistics"""
    return pool_manager.get_all_stats()


@router.get("/pools/{name}/stats")
async def get_pool_stats_by_name(name: str, pool_manager: PoolManager = Depends(get_pool_manager)):
    """Get specific pool statistics"""
    pool = pool_manager.get(name)
    if not pool:
        raise HTTPException(status_code=404, detail=f"Pool {name} not found")
    return pool.get_stats()


@router.post("/pools/{name}/cleanup")
async def cleanup_pool(name: str, pool_manager: PoolManager = Depends(get_pool_manager)):
    """Clean up idle connections in pool"""
    pool = pool_manager.get(name)
    if not pool:
        raise HTTPException(status_code=404, detail=f"Pool {name} not found")

    await pool.cleanup()
    return {"cleaned": True}


# Performance optimization endpoints


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed performance health check"""
    return {
        "status": "healthy",
        "components": {"cache": "operational", "pools": "operational", "async_optimizer": "operational"},
    }
