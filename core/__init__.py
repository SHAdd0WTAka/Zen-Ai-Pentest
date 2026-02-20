"""
Zen AI Pentest - Multi-LLM Penetration Testing Intelligence System
Author: SHAdd0WTAka
Version: 1.0.0
"""

# AsyncIO Fix für Windows Python 3.13+ (Issue #10)
# Muss vor allen anderen Imports geladen werden
try:
    from .asyncio_fix import patch_asyncio_for_windows

    patch_asyncio_for_windows()
except ImportError:
    pass  # Not critical

__version__ = "1.0.0"
__author__ = "SHAdd0WTAka"
__description__ = "Multi-LLM Penetration Testing Intelligence System"

# Export Health Check System
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
except ImportError:
    pass  # Health check dependencies may not be installed

__all__ = [
    "HealthCheckConfig",
    "HealthCheckResult",
    "HealthCheckRunner",
    "HealthReport",
    "HealthStatus",
    "SeverityLevel",
    "run_health_check",
]
