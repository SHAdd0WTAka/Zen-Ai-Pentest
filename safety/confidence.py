"""
Confidence Scorer - Calculate output confidence score
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ConfidenceScore:
    """Overall confidence assessment"""

    score: float  # 0.0 - 1.0
    level: str  # "high", "medium", "low", "critical"
    breakdown: Dict[str, float]
    recommendations: List[str]


class ConfidenceScorer:
    """
    Calculates confidence score based on multiple signals:
    - Guardrail violations
    - Validation errors
    - Fact check results
    - Historical accuracy
    """

    def __init__(self):
        self.weights = {"guardrails": 0.25, "validation": 0.25, "fact_check": 0.30, "consistency": 0.20}

    def calculate(
        self, guardrail_result=None, validation_result=None, fact_check_results=None, consistency_score: float = 1.0
    ) -> ConfidenceScore:
        """
        Calculate overall confidence score
        """
        breakdown = {}
        recommendations = []

        # Guardrail score
        if guardrail_result:
            guardrail_score = 1.0 - guardrail_result.confidence_penalty
            breakdown["guardrails"] = max(0.0, guardrail_score)
            if guardrail_score < 0.7:
                recommendations.append("Review output for uncertainty indicators")
        else:
            breakdown["guardrails"] = 1.0

        # Validation score
        if validation_result:
            validation_score = 1.0 - validation_result.confidence_impact
            breakdown["validation"] = max(0.0, validation_score)
            if validation_result.errors:
                recommendations.append("Fix structural/format errors")
        else:
            breakdown["validation"] = 1.0

        # Fact check score
        if fact_check_results:
            total = len(fact_check_results)
            if total > 0:
                verified = sum(1 for r in fact_check_results if r.confidence > 0.7)
                fact_score = verified / total
                breakdown["fact_check"] = fact_score
                if fact_score < 0.8:
                    recommendations.append("Verify factual claims")
            else:
                breakdown["fact_check"] = 0.5  # Neutral if no claims
        else:
            breakdown["fact_check"] = 0.5

        # Consistency
        breakdown["consistency"] = consistency_score
        if consistency_score < 0.8:
            recommendations.append("Check for internal contradictions")

        # Calculate weighted score
        total_score = sum(breakdown[key] * self.weights[key] for key in self.weights.keys())

        # Determine level
        if total_score >= 0.9:
            level = "high"
        elif total_score >= 0.7:
            level = "medium"
        elif total_score >= 0.5:
            level = "low"
        else:
            level = "critical"
            recommendations.insert(0, "HIGH RISK: Significant hallucination detected")

        return ConfidenceScore(score=round(total_score, 3), level=level, breakdown=breakdown, recommendations=recommendations)

    def should_retry(self, score: ConfidenceScore, threshold: float = 0.6) -> bool:
        """Determine if output should be regenerated"""
        return score.score < threshold

    def should_alert(self, score: ConfidenceScore) -> bool:
        """Determine if human review needed"""
        return score.level in ["low", "critical"]
