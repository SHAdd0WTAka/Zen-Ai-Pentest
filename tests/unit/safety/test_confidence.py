"""
Unit Tests für safety/confidence.py
"""

from dataclasses import dataclass
from typing import List

import pytest

from safety.confidence import ConfidenceScore, ConfidenceScorer

pytestmark = pytest.mark.unit


# Mock classes for testing
@dataclass
class MockGuardrailResult:
    confidence_penalty: float


@dataclass
class MockValidationResult:
    confidence_impact: float
    errors: List[str]


@dataclass
class MockFactCheckResult:
    confidence: float


class TestConfidenceScore:
    """Test ConfidenceScore dataclass"""

    def test_score_creation(self):
        """Test creating ConfidenceScore"""
        score = ConfidenceScore(
            score=0.85,
            level="high",
            breakdown={"guardrails": 0.9, "validation": 0.8},
            recommendations=["Test recommendation"],
        )
        assert score.score == 0.85
        assert score.level == "high"
        assert len(score.breakdown) == 2
        assert len(score.recommendations) == 1


class TestConfidenceScorerInit:
    """Test ConfidenceScorer initialization"""

    def test_default_weights(self):
        """Test default weights are set"""
        scorer = ConfidenceScorer()
        assert scorer.weights["guardrails"] == 0.25
        assert scorer.weights["validation"] == 0.25
        assert scorer.weights["fact_check"] == 0.30
        assert scorer.weights["consistency"] == 0.20
        assert sum(scorer.weights.values()) == 1.0

    def test_weights_sum_to_one(self):
        """Test weights sum to 1.0"""
        scorer = ConfidenceScorer()
        total = sum(scorer.weights.values())
        assert abs(total - 1.0) < 0.001


class TestConfidenceScorerCalculate:
    """Test calculate method"""

    def test_calculate_no_inputs(self):
        """Test calculation with no inputs"""
        scorer = ConfidenceScorer()
        result = scorer.calculate()

        # Default values: guardrails=1.0, validation=1.0, fact_check=0.5, consistency=1.0
        # Expected: 1.0*0.25 + 1.0*0.25 + 0.5*0.30 + 1.0*0.20 = 0.25 + 0.25 + 0.15 + 0.20 = 0.85
        assert result.score > 0.8
        assert result.level == "medium"  # 0.85 is >= 0.7 but < 0.9
        assert "guardrails" in result.breakdown
        assert "validation" in result.breakdown

    def test_calculate_high_confidence(self):
        """Test high confidence scenario"""
        scorer = ConfidenceScorer()

        guardrail = MockGuardrailResult(confidence_penalty=0.0)
        validation = MockValidationResult(confidence_impact=0.0, errors=[])
        fact_checks = [MockFactCheckResult(confidence=0.9)]

        result = scorer.calculate(
            guardrail_result=guardrail,
            validation_result=validation,
            fact_check_results=fact_checks,
            consistency_score=1.0,
        )

        assert result.score >= 0.9
        assert result.level == "high"

    def test_calculate_low_confidence(self):
        """Test low confidence scenario"""
        scorer = ConfidenceScorer()

        guardrail = MockGuardrailResult(confidence_penalty=0.8)
        validation = MockValidationResult(
            confidence_impact=0.8, errors=["error"]
        )
        fact_checks = [MockFactCheckResult(confidence=0.3)]

        result = scorer.calculate(
            guardrail_result=guardrail,
            validation_result=validation,
            fact_check_results=fact_checks,
            consistency_score=0.4,
        )

        assert result.score < 0.7
        assert result.level in ["low", "critical"]
        assert len(result.recommendations) > 0

    def test_calculate_with_guardrail_violation(self):
        """Test with guardrail violation"""
        scorer = ConfidenceScorer()
        guardrail = MockGuardrailResult(confidence_penalty=0.5)

        result = scorer.calculate(guardrail_result=guardrail)

        assert result.breakdown["guardrails"] == 0.5
        assert (
            "Review output for uncertainty indicators"
            in result.recommendations
        )

    def test_calculate_with_validation_errors(self):
        """Test with validation errors"""
        scorer = ConfidenceScorer()
        validation = MockValidationResult(
            confidence_impact=0.3, errors=["format error"]
        )

        result = scorer.calculate(validation_result=validation)

        assert result.breakdown["validation"] == 0.7
        assert "Fix structural/format errors" in result.recommendations

    def test_calculate_with_fact_check_failures(self):
        """Test with fact check failures"""
        scorer = ConfidenceScorer()
        fact_checks = [
            MockFactCheckResult(confidence=0.9),
            MockFactCheckResult(confidence=0.5),
            MockFactCheckResult(confidence=0.3),
        ]

        result = scorer.calculate(fact_check_results=fact_checks)

        # 1 out of 3 verified (confidence > 0.7)
        assert result.breakdown["fact_check"] == 1 / 3
        assert "Verify factual claims" in result.recommendations

    def test_calculate_with_low_consistency(self):
        """Test with low consistency score"""
        scorer = ConfidenceScorer()
        result = scorer.calculate(consistency_score=0.5)

        assert result.breakdown["consistency"] == 0.5
        assert "Check for internal contradictions" in result.recommendations

    def test_calculate_critical_level(self):
        """Test critical confidence level"""
        scorer = ConfidenceScorer()

        guardrail = MockGuardrailResult(confidence_penalty=1.0)
        validation = MockValidationResult(
            confidence_impact=1.0, errors=["error"]
        )

        result = scorer.calculate(
            guardrail_result=guardrail,
            validation_result=validation,
            consistency_score=0.0,
        )

        assert result.level == "critical"
        assert any("HIGH RISK" in r for r in result.recommendations)


class TestConfidenceScorerRetry:
    """Test retry logic"""

    def test_should_retry_low_score(self):
        """Test retry with low score"""
        scorer = ConfidenceScorer()
        low_score = ConfidenceScore(
            score=0.4, level="critical", breakdown={}, recommendations=[]
        )
        assert scorer.should_retry(low_score, threshold=0.6) is True

    def test_should_not_retry_high_score(self):
        """Test no retry with high score"""
        scorer = ConfidenceScorer()
        high_score = ConfidenceScore(
            score=0.9, level="high", breakdown={}, recommendations=[]
        )
        assert scorer.should_retry(high_score, threshold=0.6) is False

    def test_should_retry_custom_threshold(self):
        """Test retry with custom threshold"""
        scorer = ConfidenceScorer()
        score = ConfidenceScore(
            score=0.7, level="medium", breakdown={}, recommendations=[]
        )
        assert scorer.should_retry(score, threshold=0.8) is True
        assert scorer.should_retry(score, threshold=0.6) is False


class TestConfidenceScorerAlert:
    """Test alert logic"""

    def test_should_alert_critical(self):
        """Test alert for critical level"""
        scorer = ConfidenceScorer()
        score = ConfidenceScore(
            score=0.3, level="critical", breakdown={}, recommendations=[]
        )
        assert scorer.should_alert(score) is True

    def test_should_alert_low(self):
        """Test alert for low level"""
        scorer = ConfidenceScorer()
        score = ConfidenceScore(
            score=0.5, level="low", breakdown={}, recommendations=[]
        )
        assert scorer.should_alert(score) is True

    def test_should_not_alert_medium(self):
        """Test no alert for medium level"""
        scorer = ConfidenceScorer()
        score = ConfidenceScore(
            score=0.75, level="medium", breakdown={}, recommendations=[]
        )
        assert scorer.should_alert(score) is False

    def test_should_not_alert_high(self):
        """Test no alert for high level"""
        scorer = ConfidenceScorer()
        score = ConfidenceScore(
            score=0.95, level="high", breakdown={}, recommendations=[]
        )
        assert scorer.should_alert(score) is False
