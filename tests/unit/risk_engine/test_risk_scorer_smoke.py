"""Smoke tests for analysis_bot/engines/risk_scorer.py"""

from datetime import datetime

import pytest

from analysis_bot.engines.risk_scorer import (
    AssetCriticality,
    RiskFactors,
    RiskLevel,
    RiskScore,
    RiskScorer,
    ThreatActor,
    get_risk_scorer,
)


class TestEnums:
    def test_risk_level_values(self):
        assert RiskLevel.CRITICAL.value == "critical"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.LOW.value == "low"

    def test_asset_criticality_values(self):
        assert AssetCriticality.CRITICAL.value == 5
        assert AssetCriticality.MINIMAL.value == 1

    def test_threat_actor_values(self):
        assert ThreatActor.STATE_SPONSORED.value == "state_sponsored"
        assert ThreatActor.SCRIPT_KIDDIE.value == "script_kiddie"


class TestRiskFactors:
    def test_default_instantiation(self):
        rf = RiskFactors()
        assert rf.exploitability == 5.0
        assert rf.data_sensitivity == 5.0

    def test_custom_values(self):
        rf = RiskFactors(exploitability=8.0, business_impact=9.0)
        assert rf.exploitability == 8.0
        assert rf.business_impact == 9.0

    def test_to_dict(self):
        rf = RiskFactors()
        d = rf.to_dict()
        assert isinstance(d, dict)
        assert "exploitability" in d


class TestRiskScore:
    def test_default_instantiation(self):
        rs = RiskScore()
        assert rs.final_score == 0.0
        assert rs.risk_level == RiskLevel.LOW
        assert rs.calculated_by == "RiskScorer"

    def test_to_dict(self):
        rs = RiskScore(final_score=7.5, risk_level=RiskLevel.HIGH)
        d = rs.to_dict()
        assert d["final_score"] == 7.5
        assert d["risk_level"] == "high"
        assert "calculated_at" in d


class TestRiskScorer:
    def test_init(self):
        scorer = RiskScorer()
        assert scorer.scoring_history == []
        assert "cvss" in scorer.weights

    def test_init_with_custom_weights(self):
        weights = {"cvss": 1.0}
        scorer = RiskScorer(weights=weights)
        assert scorer.weights["cvss"] == 1.0

    def test_calculate_cvss_score(self):
        scorer = RiskScorer()
        result = scorer.calculate_cvss_score("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        assert "base_score" in result
        assert result["base_score"] > 0

    def test_calculate_dread_score(self):
        scorer = RiskScorer()
        result = scorer.calculate_dread_score(
            damage=8, reproducibility=7, exploitability=6, affected_users=5, discoverability=4
        )
        assert result["dread_score"] == 6.0

    def test_get_risk_matrix(self):
        scorer = RiskScorer()
        matrix = scorer.get_risk_matrix()
        assert isinstance(matrix, dict)
        assert len(matrix) == 5

    def test_get_risk_scorer_singleton(self):
        scorer = get_risk_scorer()
        assert isinstance(scorer, RiskScorer)
        assert get_risk_scorer() is scorer
