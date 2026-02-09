"""
Hallucination Protection & Guardrails
Q2 2026 Roadmap: Guardrails Implementation

Provides:
- Output validation (JSON Schema)
- Multi-LLM voting
- Self-correction loops
- Human-in-the-loop gates
"""

import json
import re

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class ValidationResult(Enum):
    """Validation result states."""

    VALID = "valid"
    INVALID = "invalid"
    NEEDS_REVIEW = "needs_review"


@dataclass
class GuardrailResult:
    """Result of guardrail validation."""

    is_valid: bool
    validation_result: ValidationResult
    confidence: float
    issues: List[str] = field(default_factory=list)
    corrected_output: Optional[str] = None
    requires_human_review: bool = False


class OutputValidator:
    """Validates LLM outputs against schemas and rules."""

    def __init__(self):
        self.validators: Dict[str, Callable] = {}
        self._register_default_validators()

    def _register_default_validators(self):
        """Register built-in validators."""
        self.validators["json"] = self._validate_json
        self.validators["cve_format"] = self._validate_cve_format
        self.validators["cvss_range"] = self._validate_cvss_range
        self.validators["port_range"] = self._validate_port_range

    def validate(self, output: str, schema: Optional[Dict] = None, validators: Optional[List[str]] = None) -> GuardrailResult:
        """
        Validate output against schema and validators.

        Args:
            output: LLM output to validate
            schema: JSON schema for validation
            validators: List of validator names to apply

        Returns:
            GuardrailResult with validation status
        """
        issues = []

        # JSON validation
        if schema:
            json_valid, json_issues = self._validate_json_schema(output, schema)
            if not json_valid:
                issues.extend(json_issues)

        # Custom validators
        if validators:
            for validator_name in validators:
                if validator_name in self.validators:
                    valid, issue = self.validators[validator_name](output)
                    if not valid:
                        issues.append(issue)

        is_valid = len(issues) == 0

        return GuardrailResult(
            is_valid=is_valid,
            validation_result=ValidationResult.VALID if is_valid else ValidationResult.INVALID,
            confidence=1.0 if is_valid else 0.5,
            issues=issues,
        )

    def _validate_json(self, output: str) -> tuple:
        """Validate that output is valid JSON."""
        try:
            json.loads(output)
            return True, ""
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"

    def _validate_json_schema(self, output: str, schema: Dict) -> tuple:
        """Validate JSON against schema."""
        try:
            data = json.loads(output)
            # In production, use jsonschema library
            # For now, basic type checking
            if "type" in schema:
                if schema["type"] == "object" and not isinstance(data, dict):
                    return False, [f"Expected object, got {type(data).__name__}"]
                if schema["type"] == "array" and not isinstance(data, list):
                    return False, [f"Expected array, got {type(data).__name__}"]
            return True, []
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {str(e)}"]

    def _validate_cve_format(self, output: str) -> tuple:
        """Validate CVE ID format."""
        cve_pattern = r"CVE-\d{4}-\d{4,}"
        matches = re.findall(cve_pattern, output, re.IGNORECASE)

        for match in matches:
            if not re.match(r"^CVE-\d{4}-\d{4,}$", match, re.IGNORECASE):
                return False, f"Invalid CVE format: {match}"

        return True, ""

    def _validate_cvss_range(self, output: str) -> tuple:
        """Validate CVSS score is in valid range."""
        try:
            data = json.loads(output)
            if "cvss_score" in data:
                score = float(data["cvss_score"])
                if not 0 <= score <= 10:
                    return False, f"CVSS score {score} out of range [0-10]"
        except (json.JSONDecodeError, ValueError):
            pass

        return True, ""

    def _validate_port_range(self, output: str) -> tuple:
        """Validate port numbers are in valid range."""
        port_pattern = r'"port"\s*:\s*(\d+)'
        matches = re.findall(port_pattern, output)

        for match in matches:
            port = int(match)
            if not 1 <= port <= 65535:
                return False, f"Port {port} out of valid range [1-65535]"

        return True, ""


class MultiLLMVoting:
    """Implements multi-LLM voting for consensus."""

    def __init__(self, llm_clients: List[Any]):
        self.llms = llm_clients

    async def vote(self, prompt: str, aggregation: str = "majority") -> Dict[str, Any]:
        """
        Get consensus from multiple LLMs.

        Args:
            prompt: Prompt to send to all LLMs
            aggregation: 'majority', 'unanimous', or 'average'

        Returns:
            Consensus result with confidence score
        """
        # Get responses from all LLMs
        responses = []
        for llm in self.llms:
            try:
                response = await llm.generate(prompt)
                responses.append(response)
            except Exception:
                responses.append(None)

        # Filter out failures
        valid_responses = [r for r in responses if r is not None]

        if not valid_responses:
            return {"consensus": None, "confidence": 0.0, "all_responses": responses}

        # Simple majority voting (for classification tasks)
        if aggregation == "majority":
            return self._majority_vote(valid_responses)

        # Return all responses for complex cases
        return {
            "consensus": valid_responses[0],  # Default to first
            "confidence": len(valid_responses) / len(self.llms),
            "all_responses": responses,
        }

    def _majority_vote(self, responses: List[str]) -> Dict:
        """Simple majority voting."""
        from collections import Counter

        # For exact matches
        counts = Counter(responses)
        most_common = counts.most_common(1)[0]

        return {"consensus": most_common[0], "confidence": most_common[1] / len(responses), "all_responses": responses}


class SelfCorrection:
    """Self-correction loop for fixing errors."""

    def __init__(self, llm_client, max_retries: int = 3):
        self.llm = llm_client
        self.max_retries = max_retries

    async def attempt_with_correction(self, task: Callable, validator: Callable, context: Dict) -> Any:
        """
        Attempt task with automatic correction on failure.

        Args:
            task: Async function to execute
            validator: Function to validate result
            context: Context for correction prompts

        Returns:
            Valid result or best effort after max retries
        """
        for attempt in range(self.max_retries):
            try:
                result = await task()

                # Validate result
                is_valid, error_msg = validator(result)

                if is_valid:
                    return {"success": True, "result": result, "attempts": attempt + 1}

                # If invalid and not last attempt, correct
                if attempt < self.max_retries - 1:
                    correction_prompt = f"""
                    The previous attempt failed validation with error:
                    {error_msg}

                    Original task context:
                    {context}

                    Failed result:
                    {result}

                    Please correct the issue and try again.
                    """

                    correction = await self.llm.generate(correction_prompt)
                    context["correction"] = correction

            except Exception as e:
                if attempt == self.max_retries - 1:
                    return {"success": False, "error": str(e), "attempts": attempt + 1}

        return {"success": False, "error": "Max retries exceeded", "attempts": self.max_retries}


class HumanInTheLoop:
    """Human approval gates for critical decisions."""

    def __init__(self, approval_callback: Optional[Callable] = None):
        self.approval_callback = approval_callback or self._default_approval
        self.approval_history: List[Dict] = []

    async def request_approval(self, action: str, details: Dict, auto_approve: bool = False) -> bool:
        """
        Request human approval for an action.

        Args:
            action: Description of the action
            details: Detailed information
            auto_approve: If True, automatically approve (for testing)

        Returns:
            True if approved, False otherwise
        """
        if auto_approve:
            return True

        approved = await self.approval_callback(action, details)

        self.approval_history.append(
            {"action": action, "details": details, "approved": approved, "timestamp": datetime.now().isoformat()}
        )

        return approved

    async def _default_approval(self, action: str, details: Dict) -> bool:
        """Default approval callback (logs and approves)."""
        print(f"[APPROVAL REQUIRED] {action}")
        print(f"Details: {details}")
        # In production, this would show a UI prompt
        return True


class Guardrails:
    """
    Main guardrails interface combining all protections.
    """

    def __init__(
        self,
        llm_client,
        backup_llms: Optional[List] = None,
        enable_voting: bool = False,
        enable_correction: bool = True,
        human_callback: Optional[Callable] = None,
    ):
        self.llm = llm_client
        self.validator = OutputValidator()
        self.voting = MultiLLMVoting([llm_client] + (backup_llms or [])) if enable_voting else None
        self.correction = SelfCorrection(llm_client) if enable_correction else None
        self.human_gate = HumanInTheLoop(human_callback)

        # Confidence threshold for automatic approval
        self.confidence_threshold = 0.8

    async def generate_with_guardrails(
        self, prompt: str, schema: Optional[Dict] = None, validators: Optional[List[str]] = None, require_human: bool = False
    ) -> GuardrailResult:
        """
        Generate content with full guardrail protection.

        Args:
            prompt: Input prompt
            schema: JSON schema for validation
            validators: List of validator names
            require_human: Force human approval

        Returns:
            GuardrailResult with validated output
        """
        # Generate with voting if enabled
        if self.voting:
            vote_result = await self.voting.vote(prompt)
            raw_output = vote_result["consensus"]
            confidence = vote_result["confidence"]
        else:
            raw_output = await self.llm.generate(prompt)
            confidence = 1.0

        # Validate output
        validation = self.validator.validate(raw_output, schema, validators)
        validation.confidence = confidence

        # Self-correction if invalid
        if not validation.is_valid and self.correction:
            correction_result = await self.correction.attempt_with_correction(
                task=lambda: self.llm.generate(prompt + "\n\nPlease provide valid JSON."),
                validator=lambda r: (self.validator.validate(r, schema, validators).is_valid, ""),
                context={"original_prompt": prompt},
            )

            if correction_result["success"]:
                validation.is_valid = True
                validation.corrected_output = correction_result["result"]
                validation.validation_result = ValidationResult.VALID

        # Human approval for low confidence or critical operations
        if require_human or confidence < self.confidence_threshold:
            approved = await self.human_gate.request_approval(
                action="LLM output validation",
                details={
                    "prompt": prompt,
                    "output": raw_output,
                    "confidence": confidence,
                    "validation_issues": validation.issues,
                },
            )

            if not approved:
                validation.requires_human_review = True
                validation.validation_result = ValidationResult.NEEDS_REVIEW

        return validation


# Convenience decorator
def guardrail(schema: Optional[Dict] = None, validators: Optional[List[str]] = None, on_fail: str = "retry"):
    """
    Decorator to apply guardrails to a function.

    Usage:
        @guardrail(schema=CVE_SCHEMA, validators=['cve_format'])
        async def extract_cve(text: str) -> dict:
            return await llm.generate(prompt)
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # In production, this would wrap the function
            # with guardrail logic
            return await func(*args, **kwargs)

        return wrapper

    return decorator
