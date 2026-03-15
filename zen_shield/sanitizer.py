"""
Zen Sanitizer - Main orchestrator for data sanitization
Brings together all filters: secrets, compression, injection detection
"""

import logging
import time

from .circuit_breaker import CircuitBreaker
from .filters.compress import ContextCompressor
from .filters.injection import PromptInjectionDetector
from .filters.secrets import SecretScrubber
from .schemas import (
    RedactionInfo,
    RiskLevel,
    SanitizerRequest,
    SanitizerResponse,
)

logger = logging.getLogger(__name__)


class ZenSanitizer:
    """
    Main sanitizer orchestrator.

    Pipeline:
    1. Prompt injection detection
    2. Secret scrubbing (regex, always active)
    3. Context compression (LLM or fallback)
    4. Risk assessment
    """

    def __init__(
        self,
        small_llm_endpoint: str = "http://localhost:8001",
        enable_compression: bool = True,
        enable_injection_detection: bool = True,
        circuit_breaker_threshold: int = 3,
    ):
        """
        Initialize Zen Sanitizer

        Args:
            small_llm_endpoint: URL of small local LLM for compression
            enable_compression: Whether to enable compression step
            enable_injection_detection: Whether to check for prompt injection
            circuit_breaker_threshold: Failures before fallback mode
        """
        self.secret_scrubber = SecretScrubber()
        self.injection_detector = (
            PromptInjectionDetector() if enable_injection_detection else None
        )
        self.enable_compression = enable_compression

        # Circuit breaker for LLM operations
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_threshold
        )

        # Compression with circuit breaker protection
        self.compressor = ContextCompressor(small_llm_endpoint)

    async def process(self, request: SanitizerRequest) -> SanitizerResponse:
        """
        Process raw data through sanitization pipeline

        Args:
            request: Sanitization request

        Returns:
            SanitizerResponse with cleaned data and metadata
        """
        start_time = time.time()
        raw_data = request.raw_data

        from utils.security import sanitize_log_value

        logger.info(
            f"Processing {len(raw_data)} chars from {sanitize_log_value(request.source_tool)}"
        )

        # Step 1: Prompt injection detection
        if self.injection_detector:
            is_injection, injection_matches = self.injection_detector.scan(
                raw_data
            )
            if is_injection:
                logger.warning(
                    f"Detected {len(injection_matches)} injection attempts"
                )
                raw_data = self.injection_detector.sanitize(raw_data)
        else:
            is_injection = False
            injection_matches = []

        # Step 2: Secret scrubbing (always active, deterministic)
        cleaned_data, secret_redactions = self.secret_scrubber.scrub(raw_data)

        logger.info(f"Scrubbed {len(secret_redactions)} secrets")

        # Step 3: Context compression (with circuit breaker)
        if self.enable_compression and len(cleaned_data) > 500:
            try:
                compression_result = await self.circuit_breaker.execute(
                    self._compress_with_fallback,
                    cleaned_data,
                    request.source_tool,
                    request.compression_target,
                )

                cleaned_data = compression_result.compressed_text
                compression_ratio = compression_result.compression_ratio
                tokens_saved = compression_result.tokens_saved
                fallback_used = compression_result.method == "fallback"

            except Exception as e:
                logger.error(f"Compression failed: {e}")
                compression_ratio = 1.0
                tokens_saved = 0
                fallback_used = True
        else:
            compression_ratio = 1.0
            tokens_saved = 0
            fallback_used = False

        # Step 4: Risk assessment
        risk_indicators = self._assess_risk(
            cleaned_data, secret_redactions, injection_matches
        )

        # Determine risk level
        if len(secret_redactions) > 10 or len(injection_matches) > 2:
            risk_level = RiskLevel.DANGER
        elif len(secret_redactions) > 0 or len(injection_matches) > 0:
            risk_level = RiskLevel.SUSPECT
        else:
            risk_level = RiskLevel.CLEAN

        # Convert redactions to proper schema
        redaction_infos = [RedactionInfo(**r) for r in secret_redactions]

        # Add injection redactions
        for match in injection_matches:
            redaction_infos.append(
                RedactionInfo(
                    type=f"injection_{match.pattern_name}",
                    position=(0, 0),  # Not tracked for injection
                    hash="",
                    context=match.matched_text[:20],
                )
            )

        processing_time = (time.time() - start_time) * 1000

        response = SanitizerResponse(
            cleaned_data=cleaned_data,
            redactions=redaction_infos,
            risk_indicators=risk_indicators,
            compression_ratio=compression_ratio,
            safe_to_send=risk_level != RiskLevel.DANGER
            or len(secret_redactions) <= 5,
            fallback_used=fallback_used
            or not self.circuit_breaker.get_status()["state"] == "closed",
            risk_level=risk_level,
            tokens_saved=tokens_saved,
            processing_time_ms=processing_time,
        )

        logger.info(
            f"Sanitization complete: "
            f"{len(secret_redactions)} secrets, "
            f"ratio={compression_ratio:.2f}, "
            f"risk={risk_level.value}, "
            f"time={processing_time:.1f}ms"
        )

        return response

    async def _compress_with_fallback(
        self, text: str, source_tool: str, target_tokens: int
    ):
        """Wrapper for compression with circuit breaker"""
        async with self.compressor:
            return await self.compressor.compress(
                text, source_tool, max_output_tokens=target_tokens
            )

    def _assess_risk(
        self,
        cleaned_data: str,
        secret_redactions: list,
        injection_matches: list,
    ) -> list:
        """
        Assess overall risk indicators

        Returns:
            List of risk indicator strings
        """
        indicators = []

        # Secret-based indicators
        if secret_redactions:
            types_found = set(r["type"] for r in secret_redactions)
            indicators.extend(f"contains_{t}" for t in types_found)

        # Injection indicators
        if injection_matches:
            for match in injection_matches:
                indicators.append(f"injection_attempt_{match.pattern_name}")
                if match.severity == "critical":
                    indicators.append("critical_injection_attempt")

        # Content-based indicators
        indicators.extend(self.secret_scrubber.analyze_risk(cleaned_data))

        # Circuit breaker status
        if self.circuit_breaker.get_status()["state"] != "closed":
            indicators.append("fallback_mode_active")

        return list(set(indicators))  # Deduplicate

    async def quick_scrub(self, text: str) -> str:
        """
        Quick scrub without full pipeline
        Useful for simple cases where only secrets need removal
        """
        cleaned, _ = self.secret_scrubber.scrub(text)
        return cleaned

    def get_stats(self) -> dict:
        """Get sanitizer statistics"""
        return {
            "circuit_breaker": self.circuit_breaker.get_status(),
            "config": {
                "compression_enabled": self.enable_compression,
                "injection_detection_enabled": self.injection_detector
                is not None,
            },
        }

    async def health_check(self) -> dict:
        """Health check for sanitizer components"""
        async with self.compressor:
            llm_healthy = await self.compressor._healthcheck()

        return {
            "status": "healthy",
            "secret_scrubber": "active",
            "injection_detector": (
                "active" if self.injection_detector else "disabled"
            ),
            "small_llm": "available" if llm_healthy else "unavailable",
            "circuit_breaker": self.circuit_breaker.get_status()["state"],
        }
