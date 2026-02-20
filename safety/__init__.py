"""
Hallucination Protection & Safety Guardrails

Multi-layered safety system to prevent AI hallucinations
and ensure reliable outputs in security contexts.
"""

from .confidence import ConfidenceScorer
from .fact_checker import FactChecker, FactCheckResult
from .guardrails import OutputGuardrails, SafetyLevel
from .self_correction import SelfCorrection
from .validator import OutputValidator, ValidationResult

__all__ = [
    "OutputGuardrails",
    "SafetyLevel",
    "OutputValidator",
    "ValidationResult",
    "FactChecker",
    "FactCheckResult",
    "ConfidenceScorer",
    "SelfCorrection",
]
