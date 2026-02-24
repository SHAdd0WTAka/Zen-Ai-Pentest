"""
Zen AI Pentest - Core Module
Multi-LLM Penetration Testing Intelligence System - Core Components

Performance Optimizations:
- Lazy loading of heavy modules
- Deferred imports for optional components
- Conditional initialization based on environment

Author: SHAdd0WTAka
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "SHAdd0WTAka"
__description__ = "Multi-LLM Penetration Testing Intelligence System"

# =============================================================================
# Lazy Import Utilities
# =============================================================================

import importlib
import sys
from typing import TYPE_CHECKING, Any


class _LazyModule:
    """Lazy module loader - delays import until first access"""

    def __init__(self, name: str):
        self._name = name
        self._module = None

    def _load(self):
        if self._module is None:
            self._module = importlib.import_module(self._name)
        return self._module

    def __getattr__(self, name: str) -> Any:
        return getattr(self._load(), name)

    def __dir__(self) -> list:
        return dir(self._load())


# =============================================================================
# AsyncIO Fix for Windows Python 3.13+ (Issue #10)
# Muss vor allen anderen Imports geladen werden
# =============================================================================

try:
    from .asyncio_fix import patch_asyncio_for_windows

    patch_asyncio_for_windows()
except ImportError:
    pass  # Not critical


# =============================================================================
# Core Exports (Lazy Loaded)
# =============================================================================

# These are wrapped in lazy loaders to improve import performance
# The actual modules are only imported when accessed

_cache_module = None
_database_module = None
_orchestrator_module = None
_models_module = None
_performance_module = None


def _get_cache_module():
    global _cache_module
    if _cache_module is None:
        from . import cache as _cache_module
    return _cache_module


def _get_database_module():
    global _database_module
    if _database_module is None:
        from . import database as _database_module
    return _database_module


def _get_orchestrator_module():
    global _orchestrator_module
    if _orchestrator_module is None:
        from . import orchestrator as _orchestrator_module
    return _orchestrator_module


def _get_models_module():
    global _models_module
    if _models_module is None:
        from . import models as _models_module
    return _models_module


def _get_performance_module():
    global _performance_module
    if _performance_module is None:
        from . import performance as _performance_module
    return _performance_module


# =============================================================================
# Public API with Lazy Loading
# =============================================================================


# Cache API
class CacheProxy:
    """Proxy for cache module with lazy loading"""

    def __getattr__(self, name: str):
        return getattr(_get_cache_module(), name)


# Database API
class DatabaseProxy:
    """Proxy for database module with lazy loading"""

    def __getattr__(self, name: str):
        return getattr(_get_database_module(), name)


# Performance API
class PerformanceProxy:
    """Proxy for performance module with lazy loading"""

    def __getattr__(self, name: str):
        return getattr(_get_performance_module(), name)


# Create proxy instances
cache = CacheProxy()
database = DatabaseProxy()
performance = PerformanceProxy()


# =============================================================================
# Eager Exports (Small, commonly used)
# =============================================================================

# Health Check System - commonly used
# Exported eagerly as they're small and frequently accessed
try:
    from .health_check import (
        HealthCheckConfig,
        HealthCheckResult,
        HealthCheckRunner,
        HealthReport,
        HealthStatus,
        SeverityLevel,
        run_health_check,
    )

    _health_check_available = True
except ImportError:
    _health_check_available = False
    # Define stubs to avoid import errors
    HealthCheckConfig = None
    HealthCheckResult = None
    HealthCheckRunner = None
    HealthReport = None
    HealthStatus = None
    SeverityLevel = None
    run_health_check = None


# =============================================================================
# Conditional/Lazy Exports
# =============================================================================


def __getattr__(name: str) -> Any:
    """Lazy load heavy modules on first access"""

    # Orchestrator exports
    if name in (
        "ZenOrchestrator",
        "BaseBackend",
        "QualityLevel",
        "LLMResponse",
    ):
        mod = _get_orchestrator_module()
        return getattr(mod, name)

    # Model exports
    if name in (
        "APIKeyConfig",
        "ScanConfig",
        "Finding",
        "ScanResult",
        "LLMRequest",
        "LLMResponse",
        "SubdomainInfo",
        "DomainRecon",
        "HealthStatus",
        "PaginatedResponse",
        "ReportConfig",
    ):
        mod = _get_models_module()
        return getattr(mod, name)

    # Performance exports
    if name in (
        "timed",
        "timed_block",
        "memoize",
        "ttl_cache",
        "LazyImport",
        "LazyLoader",
        "PerformanceTimer",
        "PerformanceMiddleware",
        "gather_with_concurrency",
        "run_in_thread",
    ):
        mod = _get_performance_module()
        return getattr(mod, name)

    # Cache exports
    if name in (
        "CacheBackend",
        "MemoryCache",
        "SQLiteCache",
        "RedisCache",
        "MultiTierCache",
        "CacheStats",
        "cached",
    ):
        mod = _get_cache_module()
        return getattr(mod, name)

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# =============================================================================
# __all__ Definition
# =============================================================================

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__description__",
    # Proxy modules
    "cache",
    "database",
    "performance",
    # Health Check (conditionally available)
    "HealthCheckConfig",
    "HealthCheckResult",
    "HealthCheckRunner",
    "HealthReport",
    "HealthStatus",
    "SeverityLevel",
    "run_health_check",
    # Lazy-loaded: Orchestrator
    "ZenOrchestrator",
    "BaseBackend",
    "QualityLevel",
    "LLMResponse",
    # Lazy-loaded: Models
    "APIKeyConfig",
    "ScanConfig",
    "Finding",
    "ScanResult",
    "LLMRequest",
    "SubdomainInfo",
    "DomainRecon",
    "PaginatedResponse",
    "ReportConfig",
    # Lazy-loaded: Performance
    "timed",
    "timed_block",
    "memoize",
    "ttl_cache",
    "LazyImport",
    "LazyLoader",
    "PerformanceTimer",
    "PerformanceMiddleware",
    "gather_with_concurrency",
    "run_in_thread",
    # Lazy-loaded: Cache
    "CacheBackend",
    "MemoryCache",
    "SQLiteCache",
    "RedisCache",
    "MultiTierCache",
    "CacheStats",
    "cached",
]

# Add health check to __all__ only if available
if _health_check_available:
    __all__.extend(
        [
            "HealthCheckConfig",
            "HealthCheckResult",
            "HealthCheckRunner",
            "HealthReport",
            "HealthStatus",
            "SeverityLevel",
            "run_health_check",
        ]
    )
