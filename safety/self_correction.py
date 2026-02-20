"""
Self-Correction - Automatic output improvement
"""

import re
from typing import Any, Dict, List


class SelfCorrection:
    """
    Attempts to automatically correct detected issues.
    Falls back to retry/reject if auto-correction fails.
    """

    def __init__(self):
        self.correction_history: List[Dict] = []

    def attempt_correction(self, output: str, issues: List[str], fact_corrections: List[str]) -> Dict[str, Any]:
        """
        Attempt to correct output automatically
        """
        corrected = output
        corrections_made = []

        # Apply factual corrections first
        for correction in fact_corrections:
            # Simple replacement (would need more sophisticated logic in production)
            if "is actually" in correction.lower():
                parts = correction.split("is actually")
                if len(parts) == 2:
                    wrong = parts[0].strip()
                    right = parts[1].strip()
                    corrected = corrected.replace(wrong, right)
                    corrections_made.append(f"Corrected: {wrong} -> {right}")

        # Fix uncertainty language
        uncertainty_fixes = {
            r"\bmaybe\b": "",
            r"\bperhaps\b": "",
            r"\bI think\b": "",
            r"\bprobably\b": "likely",
        }

        for pattern, replacement in uncertainty_fixes.items():
            matches = re.findall(pattern, corrected, re.IGNORECASE)
            if matches:
                corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
                corrections_made.append(f"Reduced uncertainty: {matches}")

        # Remove false security claims
        false_claims = ["impossible to exploit", "completely secure", "100% safe", "unhackable"]

        for claim in false_claims:
            if claim.lower() in corrected.lower():
                corrected = re.sub(claim, "[REVIEW NEEDED: Absolute security claim removed]", corrected, flags=re.IGNORECASE)
                corrections_made.append(f"Removed false claim: {claim}")

        # Record correction
        self.correction_history.append(
            {
                "original_length": len(output),
                "corrected_length": len(corrected),
                "issues_found": len(issues),
                "corrections_made": len(corrections_made),
            }
        )

        return {
            "success": len(corrections_made) > 0,
            "original": output,
            "corrected": corrected,
            "corrections": corrections_made,
            "still_needs_review": len(issues) > len(corrections_made),
        }

    def generate_retry_prompt(self, original_prompt: str, issues: List[str], confidence_breakdown: Dict[str, float]) -> str:
        """
        Generate an improved prompt for retry
        """
        retry_prompt = f"""{original_prompt}

IMPORTANT - Previous attempt had issues:
"""

        # Add specific guidance based on issues
        if "guardrails" in confidence_breakdown and confidence_breakdown["guardrails"] < 0.7:
            retry_prompt += "\n- Be more specific and avoid uncertainty language (maybe, perhaps, I think)"

        if "fact_check" in confidence_breakdown and confidence_breakdown["fact_check"] < 0.8:
            retry_prompt += "\n- Verify all technical claims against known data"

        if "validation" in confidence_breakdown and confidence_breakdown["validation"] < 0.8:
            retry_prompt += "\n- Follow the exact output format specified"

        retry_prompt += "\n\nPlease provide a corrected response."

        return retry_prompt

    def get_correction_stats(self) -> Dict[str, Any]:
        """Get self-correction statistics"""
        if not self.correction_history:
            return {"total_attempts": 0}

        total = len(self.correction_history)
        successful = sum(1 for h in self.correction_history if h["corrections_made"] > 0)

        return {
            "total_attempts": total,
            "successful_corrections": successful,
            "success_rate": successful / total if total > 0 else 0,
            "avg_corrections": sum(h["corrections_made"] for h in self.correction_history) / total,
        }
