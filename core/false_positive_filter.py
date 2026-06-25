"""
False Positive Filter - Multi-LLM Voting System
Phase 7.2: False-Positive-Reduktion durch Multi-LLM-Voting

Dieses Modul implementiert ein Voting-System mit mehreren LLM-Providern,
um die Validierung von Security-Findings zu verbessern und False Positives zu reduzieren.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VoteVerdict(str, Enum):
    """Possible verdicts from LLM voting"""

    VALID = "valid"
    FALSE_POSITIVE = "false_positive"
    UNCERTAIN = "uncertain"


@dataclass
class LLMVote:
    """Single vote from an LLM provider"""

    provider: str
    verdict: VoteVerdict
    confidence: float  # 0.0 to 1.0
    reasoning: str
    latency_ms: float = 0.0


@dataclass
class ValidationResult:
    """Result of multi-LLM validation"""

    is_valid: bool
    confidence: float
    votes: List[LLMVote]
    consensus: str
    recommended_action: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class FalsePositiveFilter:
    """
    Multi-LLM Voting System for finding validation.

    Uses multiple LLM providers to vote on the validity of a security finding.
    Reduces false positives by requiring consensus across different models.
    """

    # Confidence threshold for considering a finding valid
    CONFIDENCE_THRESHOLD = 0.7

    # Minimum number of votes required for consensus
    MIN_VOTES_REQUIRED = 2

    # Providers to use for voting (in order of priority)
    DEFAULT_PROVIDERS = ["openai", "anthropic", "openrouter"]

    def __init__(
        self,
        providers: Optional[List[str]] = None,
        confidence_threshold: float = 0.7,
        min_votes_required: int = 2,
    ):
        """
        Initialize the False Positive Filter.

        Args:
            providers: List of LLM providers to use for voting
            confidence_threshold: Minimum confidence score for valid finding
            min_votes_required: Minimum number of votes needed for consensus
        """
        self.providers = providers or self.DEFAULT_PROVIDERS
        self.confidence_threshold = confidence_threshold
        self.min_votes_required = min_votes_required
        self._llm_backends: Dict[str, Any] = {}

        logger.info(f"FalsePositiveFilter initialized with providers: {self.providers}")

    def _get_llm_backend(self, provider: str) -> Optional[Any]:
        """Get or initialize LLM backend for provider"""
        if provider not in self._llm_backends:
            try:
                # TODO: Implement actual LLM backend initialization
                # This is a placeholder - actual implementation would initialize
                # the appropriate backend (OpenAI, Anthropic, etc.)
                from core.llm_backend import LLMBackend

                self._llm_backends[provider] = LLMBackend(provider=provider)
            except Exception as e:
                logger.error(f"Failed to initialize LLM backend for {provider}: {e}")
                return None
        return self._llm_backends.get(provider)

    def _build_validation_prompt(self, finding: Dict[str, Any]) -> str:
        """
        Build a prompt for LLM validation.

        Args:
            finding: Security finding to validate

        Returns:
            Formatted prompt string
        """
        return f"""You are a security expert validating a vulnerability finding.

Please analyze the following security finding and determine if it is a TRUE POSITIVE (valid vulnerability) or FALSE POSITIVE.

FINDING DETAILS:
- Title: {finding.get("title", "N/A")}
- Severity: {finding.get("severity", "N/A")}
- Description: {finding.get("description", "N/A")}
- Tool: {finding.get("tool", "N/A")}
- Target: {finding.get("target", "N/A")}
- Evidence: {finding.get("evidence", "N/A")}

CVSS Score: {finding.get("cvss_score", "N/A")}
CVE IDs: {", ".join(finding.get("cve_ids", [])) if finding.get("cve_ids") else "N/A"}

INSTRUCTIONS:
1. Analyze if this finding represents a real security vulnerability
2. Consider common false positive patterns (e.g., generic error messages, non-exploitable configurations)
3. Provide a verdict: VALID (true vulnerability), FALSE_POSITIVE, or UNCERTAIN
4. Give your confidence level (0.0 to 1.0)
5. Explain your reasoning briefly

RESPOND IN JSON FORMAT:
{{
    "verdict": "valid|false_positive|uncertain",
    "confidence": 0.85,
    "reasoning": "Brief explanation of your decision"
}}
"""

    async def _query_provider(self, provider: str, finding: Dict[str, Any]) -> Optional[LLMVote]:
        """
        Query a single LLM provider for validation.

        Args:
            provider: LLM provider name
            finding: Finding to validate

        Returns:
            LLMVote or None if query failed
        """
        import time

        backend = self._get_llm_backend(provider)
        if not backend:
            return None

        start_time = time.time()

        try:
            self._build_validation_prompt(finding)

            # TODO: Replace with actual LLM query
            # For now, return a simulated response
            # In production, this would call backend.generate() or backend.chat()

            # Simulated response for demonstration
            # TODO: Implement actual LLM integration
            await asyncio.sleep(0.1)  # Simulate latency

            # Simple heuristic-based simulation
            # In production, this would be the actual LLM response
            simulated_response = self._simulate_validation(finding)

            latency = (time.time() - start_time) * 1000

            return LLMVote(
                provider=provider,
                verdict=VoteVerdict(simulated_response["verdict"]),
                confidence=simulated_response["confidence"],
                reasoning=simulated_response["reasoning"],
                latency_ms=latency,
            )

        except Exception as e:
            logger.error(f"Error querying provider {provider}: {e}")
            return None

    def _simulate_validation(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate LLM validation for demonstration purposes.

        TODO: Replace with actual LLM integration.

        Args:
            finding: Finding to validate

        Returns:
            Simulated validation result
        """
        # Simple heuristic-based simulation
        title = finding.get("title", "").lower()
        description = finding.get("description", "").lower()
        finding.get("evidence", "").lower()

        # Check for common false positive indicators
        fp_indicators = [
            "informational",
            "not vulnerable",
            "false positive",
            "unable to confirm",
            "no evidence",
        ]

        # Check for strong vulnerability indicators
        vuln_indicators = [
            "exploit",
            "injection",
            "rce",
            "sql",
            "xss",
            "cve-",
            "authenticated",
            "remote code",
        ]

        fp_score = sum(1 for ind in fp_indicators if ind in title or ind in description)
        vuln_score = sum(1 for ind in vuln_indicators if ind in title or ind in description)

        if fp_score > vuln_score:
            return {
                "verdict": "false_positive",
                "confidence": min(0.6 + fp_score * 0.1, 0.9),
                "reasoning": "Finding appears to be informational or lacks concrete exploitation evidence.",
            }
        elif vuln_score > 0:
            return {
                "verdict": "valid",
                "confidence": min(0.7 + vuln_score * 0.1, 0.95),
                "reasoning": f"Finding shows indicators of a real vulnerability ({vuln_score} positive signals).",
            }
        else:
            return {
                "verdict": "uncertain",
                "confidence": 0.5,
                "reasoning": "Insufficient information to make a definitive assessment.",
            }

    async def gather_votes(self, finding: Dict[str, Any]) -> List[LLMVote]:
        """
        Gather votes from all configured LLM providers.

        Args:
            finding: Finding to validate

        Returns:
            List of LLMVote objects
        """
        tasks = [self._query_provider(provider, finding) for provider in self.providers]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        votes = []
        for result in results:
            if isinstance(result, LLMVote):
                votes.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Provider query failed: {result}")

        return votes

    def calculate_confidence(self, votes: List[LLMVote]) -> float:
        """
        Calculate overall confidence from votes.

        Uses weighted voting based on provider confidence scores.

        Args:
            votes: List of LLMVote objects

        Returns:
            Overall confidence score (0.0 to 1.0)
        """
        if not votes:
            return 0.0

        # Count verdicts
        valid_votes = [v for v in votes if v.verdict == VoteVerdict.VALID]
        fp_votes = [v for v in votes if v.verdict == VoteVerdict.FALSE_POSITIVE]

        total_votes = len(votes)
        valid_count = len(valid_votes)
        fp_count = len(fp_votes)

        # Calculate weighted confidence
        valid_confidence = sum(v.confidence for v in valid_votes)
        fp_confidence = sum(v.confidence for v in fp_votes)

        # Consensus factor: higher when more providers agree
        max_agreement = max(valid_count, fp_count)
        consensus_factor = max_agreement / total_votes if total_votes > 0 else 0

        # Calculate final confidence
        if valid_count > fp_count:
            base_confidence = valid_confidence / valid_count if valid_count > 0 else 0
            return min(base_confidence * (0.8 + 0.2 * consensus_factor), 1.0)
        elif fp_count > valid_count:
            base_confidence = fp_confidence / fp_count if fp_count > 0 else 0
            return min(base_confidence * (0.8 + 0.2 * consensus_factor), 1.0)
        else:
            # Tie - return average confidence
            avg_confidence = sum(v.confidence for v in votes) / total_votes
            return avg_confidence * 0.7  # Reduce confidence on tie

    def determine_consensus(self, votes: List[LLMVote]) -> str:
        """
        Determine the consensus from votes.

        Args:
            votes: List of LLMVote objects

        Returns:
            Consensus description
        """
        if not votes:
            return "no_votes"

        valid_count = sum(1 for v in votes if v.verdict == VoteVerdict.VALID)
        fp_count = sum(1 for v in votes if v.verdict == VoteVerdict.FALSE_POSITIVE)
        uncertain_count = sum(1 for v in votes if v.verdict == VoteVerdict.UNCERTAIN)

        total = len(votes)

        if valid_count > fp_count and valid_count > uncertain_count:
            return f"valid ({valid_count}/{total} votes)"
        elif fp_count > valid_count and fp_count > uncertain_count:
            return f"false_positive ({fp_count}/{total} votes)"
        elif uncertain_count >= valid_count and uncertain_count >= fp_count:
            return f"uncertain ({uncertain_count}/{total} votes)"
        else:
            return f"split (valid:{valid_count}, fp:{fp_count}, uncertain:{uncertain_count})"

    async def validate_finding(self, finding: Dict[str, Any]) -> ValidationResult:
        """
        Validate a finding using multi-LLM voting.

        Args:
            finding: Security finding to validate

        Returns:
            ValidationResult with consensus and confidence
        """
        logger.info(f"Validating finding: {finding.get('title', 'Unknown')}")

        # Gather votes from all providers
        votes = await self.gather_votes(finding)

        if len(votes) < self.min_votes_required:
            logger.warning(f"Insufficient votes: {len(votes)}/{self.min_votes_required}")
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                votes=votes,
                consensus="insufficient_votes",
                recommended_action="manual_review",
                metadata={"error": "insufficient_votes"},
            )

        # Calculate overall confidence
        confidence = self.calculate_confidence(votes)

        # Determine consensus
        consensus = self.determine_consensus(votes)

        # Determine if finding is valid
        valid_votes = [v for v in votes if v.verdict == VoteVerdict.VALID]
        fp_votes = [v for v in votes if v.verdict == VoteVerdict.FALSE_POSITIVE]

        is_valid = len(valid_votes) > len(fp_votes) and confidence >= self.confidence_threshold

        # Determine recommended action
        if is_valid and confidence >= 0.9:
            recommended_action = "accept"
        elif is_valid and confidence >= self.confidence_threshold:
            recommended_action = "accept_with_review"
        elif not is_valid and confidence >= 0.8:
            recommended_action = "reject"
        else:
            recommended_action = "manual_review"

        result = ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            votes=votes,
            consensus=consensus,
            recommended_action=recommended_action,
            metadata={
                "threshold": self.confidence_threshold,
                "total_votes": len(votes),
                "valid_votes": len(valid_votes),
                "fp_votes": len(fp_votes),
            },
        )

        logger.info(f"Validation complete: is_valid={is_valid}, confidence={confidence:.2f}, consensus={consensus}")

        return result

    async def batch_validate(self, findings: List[Dict[str, Any]]) -> List[ValidationResult]:
        """
        Validate multiple findings in batch.

        Args:
            findings: List of findings to validate

        Returns:
            List of ValidationResult objects
        """
        tasks = [self.validate_finding(finding) for finding in findings]
        return await asyncio.gather(*tasks)


# Convenience function for direct usage
async def validate_finding(finding: Dict[str, Any], **kwargs) -> ValidationResult:
    """
    Convenience function to validate a single finding.

    Args:
        finding: Finding to validate
        **kwargs: Additional arguments for FalsePositiveFilter

    Returns:
        ValidationResult
    """
    filter_obj = FalsePositiveFilter(**kwargs)
    return await filter_obj.validate_finding(finding)
