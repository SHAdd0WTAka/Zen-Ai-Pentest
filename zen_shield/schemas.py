"""
Pydantic Schemas for Zen Shield Sanitizer
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RiskLevel(Enum):
    """Risk classification levels"""

    CLEAN = "clean"
    SUSPECT = "suspect"  # Suspicious strings but no clear secret
    DANGER = "danger"  # Definite secret found
    INJECTION = "injection"  # Prompt injection attempt


class SanitizerRequest(BaseModel):
    """Request model for sanitization"""

    raw_data: str = Field(
        ...,
        description="Raw tool output (Nmap, Burp, etc.)",
        max_length=500000,  # 500KB limit
    )
    source_tool: str = Field(
        ..., description="Source tool: nmap, nuclei, ffuf, sqlmap, etc."
    )
    intent: str = Field(
        "analyze", description="Purpose: analyze, explain, exploit, report"
    )
    user_context: Optional[str] = Field(None, description="Additional user context")
    compression_target: int = Field(
        500, description="Target token count for compression"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "raw_data": "Nmap scan results...",
                "source_tool": "nmap",
                "intent": "analyze",
                "compression_target": 500,
            }
        }


class RedactionInfo(BaseModel):
    """Information about a redacted secret"""

    type: str = Field(..., description="Secret type: api_key, bearer_token, etc.")
    position: tuple = Field(..., description="(start, end) position in original text")
    hash: str = Field(..., description="Hash of original value for tracking")
    context: str = Field(..., description="Context snippet (first 10 chars)")


class SanitizerResponse(BaseModel):
    """Response model after sanitization"""

    cleaned_data: str = Field(..., description="Sanitized data safe for LLM")
    redactions: List[RedactionInfo] = Field(
        default_factory=list, description="What was removed and why"
    )
    risk_indicators: List[str] = Field(
        default_factory=list,
        description="Risk flags: 'contains_jwt', 'base64_encoded', etc.",
    )
    compression_ratio: float = Field(1.0, description="Compression ratio achieved")
    safe_to_send: bool = Field(
        ..., description="Whether data is safe to send to external LLM"
    )
    fallback_used: bool = Field(False, description="Whether regex fallback was used")
    risk_level: RiskLevel = Field(
        RiskLevel.CLEAN, description="Overall risk assessment"
    )
    tokens_saved: int = Field(0, description="Estimated tokens saved by compression")
    processing_time_ms: float = Field(
        0.0, description="Processing time in milliseconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "cleaned_data": "Sanitized output...",
                "redactions": [],
                "risk_indicators": ["contains_internal_ip"],
                "compression_ratio": 0.3,
                "safe_to_send": True,
                "fallback_used": False,
                "risk_level": "suspect",
            }
        }


class HealthStatus(BaseModel):
    """Health check response"""

    status: str = "healthy"
    small_llm_available: bool = True
    circuit_breaker_state: str = "closed"
    active_filters: List[str] = Field(default_factory=list)
    version: str = "1.0.0"


class CompressionStats(BaseModel):
    """Statistics about compression performance"""

    original_chars: int
    cleaned_chars: int
    compression_ratio: float
    secrets_found: int
    risk_level: str
    method_used: str  # 'llm' or 'fallback'
