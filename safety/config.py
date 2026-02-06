"""
Safety Configuration
"""

from .guardrails import SafetyLevel

SAFETY_CONFIG = {
    "default_level": SafetyLevel.STANDARD,
    "auto_correct": True,
    "retry_threshold": 0.6,
    "alert_threshold": 0.5,
    "max_retries": 2,
    # Per-context overrides
    "context_levels": {
        "production": SafetyLevel.STRICT,
        "pentest": SafetyLevel.STANDARD,
        "development": SafetyLevel.PERMISSIVE,
        "critical": SafetyLevel.PARANOID,
    },
}
