"""
Pytest tests for covering missing lines in risk_engine/false_positive_engine.py.

Targets:
- Lines 100, 102: CVSSData.get_effective_score() returns environmental/temporal scores
- Lines 107-116: CVSSData.get_severity_rating() - Critical/High/Medium/Low/None
- Lines 130: EPSSData.is_critical()
- Lines 134-140: EPSSData.get_risk_level() - CRITICAL/HIGH/MEDIUM/LOW
- Lines 165-196: RiskFactors.get_weighted_risk_score() - weighted risk calculation
- Lines 259: ValidationResult.calculate_confidence()
- Lines 392-393, 407: FalsePositiveDatabase._save_to_storage() error handling
- Lines 421-423: FalsePositiveDatabase._load_from_storage() success path
- Lines 434-435, 444-448: FalsePositiveDatabase methods
- Lines 452-474: FalsePositiveDatabase.check_historical_match()
- Lines 478-503: FalsePositiveDatabase.get_fp_likelihood()
- Lines 607-612, 617-630: PatternMatcher methods
- Lines 908-919: Exploit maturity check
"""

import json
import os
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from risk_engine.false_positive_engine import (
    BayesianFilter,
    CVSSData,
    EPSSData,
    FalsePositiveDatabase,
    FalsePositiveEngine,
    Finding,
    FindingStatus,
    HistoricalFinding,
    RiskFactors,
    ValidationResult,
    VulnerabilityType,
    create_finding_from_scan_result,
)


class TestCVSSDataEffectiveScore:
    """Test CVSSData.get_effective_score() - Lines 100, 102"""

    def test_get_effective_score_returns_environmental_score(self):
        """Line 100: Return environmental_score when available."""
        cvss = CVSSData(base_score=5.0, temporal_score=6.0, environmental_score=8.5)
        assert cvss.get_effective_score() == 8.5

    def test_get_effective_score_returns_temporal_score(self):
        """Line 102: Return temporal_score when environmental is None."""
        cvss = CVSSData(base_score=5.0, temporal_score=6.5, environmental_score=None)
        assert cvss.get_effective_score() == 6.5

    def test_get_effective_score_returns_base_score(self):
        """Return base_score when both temporal and environmental are None."""
        cvss = CVSSData(base_score=7.0, temporal_score=None, environmental_score=None)
        assert cvss.get_effective_score() == 7.0


class TestCVSSDataSeverityRating:
    """Test CVSSData.get_severity() - Lines 107-116"""

    def test_get_severity_critical(self):
        """Line 108-109: Score >= 9.0 returns 'Critical'."""
        cvss = CVSSData(base_score=9.5)
        assert cvss.get_severity() == "Critical"

    def test_get_severity_critical_boundary(self):
        """Test boundary for Critical (exactly 9.0)."""
        cvss = CVSSData(base_score=9.0)
        assert cvss.get_severity() == "Critical"

    def test_get_severity_high(self):
        """Line 110-111: Score >= 7.0 and < 9.0 returns 'High'."""
        cvss = CVSSData(base_score=8.0)
        assert cvss.get_severity() == "High"

    def test_get_severity_high_boundary(self):
        """Test boundary for High (exactly 7.0)."""
        cvss = CVSSData(base_score=7.0)
        assert cvss.get_severity() == "High"

    def test_get_severity_medium(self):
        """Line 112-113: Score >= 4.0 and < 7.0 returns 'Medium'."""
        cvss = CVSSData(base_score=5.5)
        assert cvss.get_severity() == "Medium"

    def test_get_severity_medium_boundary(self):
        """Test boundary for Medium (exactly 4.0)."""
        cvss = CVSSData(base_score=4.0)
        assert cvss.get_severity() == "Medium"

    def test_get_severity_low(self):
        """Line 114-115: Score >= 0.1 and < 4.0 returns 'Low'."""
        cvss = CVSSData(base_score=2.5)
        assert cvss.get_severity() == "Low"

    def test_get_severity_low_boundary(self):
        """Test boundary for Low (exactly 0.1)."""
        cvss = CVSSData(base_score=0.1)
        assert cvss.get_severity() == "Low"

    def test_get_severity_none(self):
        """Line 116: Score < 0.1 returns 'None'."""
        cvss = CVSSData(base_score=0.0)
        assert cvss.get_severity() == "None"

    def test_get_severity_with_environmental_score(self):
        """Test severity calculation uses effective score (environmental)."""
        cvss = CVSSData(base_score=5.0, environmental_score=9.5)
        assert cvss.get_severity() == "Critical"


class TestEPSSDataRiskLevels:
    """Test EPSSData risk methods - Lines 130, 134-140"""

    def test_is_high_probability_true(self):
        """Line 130: epss_score >= 0.5 returns True."""
        epss = EPSSData(cve_id="CVE-2024-0001", epss_score=0.7, percentile=0.8)
        assert epss.is_high_probability() is True

    def test_is_high_probability_boundary(self):
        """Test boundary for is_high_probability (exactly 0.5)."""
        epss = EPSSData(cve_id="CVE-2024-0002", epss_score=0.5, percentile=0.5)
        assert epss.is_high_probability() is True

    def test_is_high_probability_false(self):
        """epss_score < 0.5 returns False."""
        epss = EPSSData(cve_id="CVE-2024-0003", epss_score=0.3, percentile=0.4)
        assert epss.is_high_probability() is False

    def test_get_risk_level_critical(self):
        """Line 134-135: epss_score >= 0.7 returns 'CRITICAL'."""
        epss = EPSSData(cve_id="CVE-2024-0004", epss_score=0.75, percentile=0.9)
        assert epss.get_risk_level() == "CRITICAL"

    def test_get_risk_level_critical_boundary(self):
        """Test boundary for CRITICAL (exactly 0.7)."""
        epss = EPSSData(cve_id="CVE-2024-0005", epss_score=0.7, percentile=0.7)
        assert epss.get_risk_level() == "CRITICAL"

    def test_get_risk_level_high(self):
        """Line 136-137: epss_score >= 0.4 and < 0.7 returns 'HIGH'."""
        epss = EPSSData(cve_id="CVE-2024-0006", epss_score=0.5, percentile=0.6)
        assert epss.get_risk_level() == "HIGH"

    def test_get_risk_level_high_boundary(self):
        """Test boundary for HIGH (exactly 0.4)."""
        epss = EPSSData(cve_id="CVE-2024-0007", epss_score=0.4, percentile=0.5)
        assert epss.get_risk_level() == "HIGH"

    def test_get_risk_level_medium(self):
        """Line 138-139: epss_score >= 0.1 and < 0.4 returns 'MEDIUM'."""
        epss = EPSSData(cve_id="CVE-2024-0008", epss_score=0.25, percentile=0.3)
        assert epss.get_risk_level() == "MEDIUM"

    def test_get_risk_level_medium_boundary(self):
        """Test boundary for MEDIUM (exactly 0.1)."""
        epss = EPSSData(cve_id="CVE-2024-0009", epss_score=0.1, percentile=0.2)
        assert epss.get_risk_level() == "MEDIUM"

    def test_get_risk_level_low(self):
        """Line 140: epss_score < 0.1 returns 'LOW'."""
        epss = EPSSData(cve_id="CVE-2024-0010", epss_score=0.05, percentile=0.1)
        assert epss.get_risk_level() == "LOW"

    def test_get_risk_level_low_zero(self):
        """Test LOW risk with score 0."""
        epss = EPSSData(cve_id="CVE-2024-0011", epss_score=0.0, percentile=0.0)
        assert epss.get_risk_level() == "LOW"


class TestRiskFactorsWeightedScore:
    """Test RiskFactors.get_weighted_risk_score() - Lines 165-196"""

    def test_get_weighted_risk_score_basic(self):
        """Test basic weighted risk score calculation."""
        cvss = CVSSData(base_score=8.0)
        risk_factors = RiskFactors(
            cvss_data=cvss,
            epss_score=0.5,
            business_impact=0.6,
            exploitability=0.4,
            asset_criticality=0.5,
        )
        score = risk_factors.get_weighted_risk_score()
        assert 0.0 <= score <= 1.0

    def test_get_weighted_risk_score_internet_exposed_multiplier(self):
        """Line 179-180: Internet exposed adds 0.3 to context multiplier."""
        cvss = CVSSData(base_score=5.0)
        risk_factors = RiskFactors(cvss_data=cvss, internet_exposed=True)
        score = risk_factors.get_weighted_risk_score()
        # Context multiplier should be 1.3 (1.0 + 0.3)
        assert score > 0

    def test_get_weighted_risk_score_exploit_available_multiplier(self):
        """Line 181-182: Exploit code available adds 0.2 to context multiplier."""
        cvss = CVSSData(base_score=5.0)
        risk_factors = RiskFactors(cvss_data=cvss, exploit_code_available=True)
        score = risk_factors.get_weighted_risk_score()
        # Context multiplier should be 1.2 (1.0 + 0.2)
        assert score > 0

    def test_get_weighted_risk_score_active_exploitation_multiplier(self):
        """Line 183-184: Active exploitation adds 0.4 to context multiplier."""
        cvss = CVSSData(base_score=5.0)
        risk_factors = RiskFactors(cvss_data=cvss, active_exploitation_observed=True)
        score = risk_factors.get_weighted_risk_score()
        # Context multiplier should be 1.4 (1.0 + 0.4)
        assert score > 0

    def test_get_weighted_risk_score_no_patch_multiplier(self):
        """Line 185-186: No patch available adds 0.1 to context multiplier."""
        cvss = CVSSData(base_score=5.0)
        risk_factors = RiskFactors(cvss_data=cvss, patch_available=False)
        score = risk_factors.get_weighted_risk_score()
        # Context multiplier should be 1.1 (1.0 + 0.1)
        assert score > 0

    def test_get_weighted_risk_score_all_multipliers(self):
        """Test all context multipliers combined."""
        cvss = CVSSData(base_score=7.0)
        risk_factors = RiskFactors(
            cvss_data=cvss,
            epss_score=0.6,
            business_impact=0.7,
            exploitability=0.5,
            asset_criticality=0.6,
            internet_exposed=True,  # +0.3
            exploit_code_available=True,  # +0.2
            active_exploitation_observed=True,  # +0.4
            patch_available=False,  # +0.1
        )
        # Context multiplier = 1.0 + 0.3 + 0.2 + 0.4 + 0.1 = 2.0
        # min(2.0, 2.0) = 2.0
        score = risk_factors.get_weighted_risk_score()
        assert 0.0 <= score <= 1.0
        # Should have higher score due to multipliers
        assert score > 0.3

    def test_get_weighted_risk_score_with_environmental_cvss(self):
        """Test weighted score with environmental CVSS score."""
        cvss = CVSSData(base_score=5.0, environmental_score=9.0)
        risk_factors = RiskFactors(cvss_data=cvss)
        score = risk_factors.get_weighted_risk_score()
        # Should use environmental score (9.0 / 10.0 = 0.9)
        assert score > 0.2

    def test_get_weighted_risk_score_capped_at_1(self):
        """Test that score is capped at 1.0."""
        cvss = CVSSData(base_score=10.0)
        risk_factors = RiskFactors(
            cvss_data=cvss,
            epss_score=1.0,
            business_impact=1.0,
            exploitability=1.0,
            asset_criticality=1.0,
            internet_exposed=True,
            exploit_code_available=True,
            active_exploitation_observed=True,
            patch_available=False,
        )
        score = risk_factors.get_weighted_risk_score()
        assert score <= 1.0


class TestValidationResultToDict:
    """Test ValidationResult.to_dict() - Line 259"""

    def test_validation_result_to_dict(self):
        """Test that to_dict returns correct structure."""
        finding = Finding(
            id="test-001",
            title="Test Finding",
            description="Test description",
            severity="high",
        )
        result = ValidationResult(
            finding=finding,
            is_false_positive=False,
            confidence=0.85,
            risk_score=0.75,
            priority=1,
            reasoning="Test reasoning",
            recommendations=["Fix it"],
            validation_methods=["test"],
            llm_votes={"gpt": False},
        )
        result_dict = result.to_dict()
        assert result_dict["finding_id"] == "test-001"
        assert result_dict["is_false_positive"] is False
        assert result_dict["confidence"] == 0.85
        assert result_dict["risk_score"] == 0.75
        assert result_dict["priority"] == 1
        assert result_dict["reasoning"] == "Test reasoning"
        assert result_dict["recommendations"] == ["Fix it"]
        assert result_dict["validation_methods"] == ["test"]
        assert result_dict["llm_votes"] == {"gpt": False}


class TestFalsePositiveDatabaseStorage:
    """Test FalsePositiveDatabase storage operations - Lines 392-393, 407, 421-423"""

    def test_save_to_storage_error_handling(self):
        """Lines 392-393, 407: Test _save_to_storage error handling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "test_db.json")
            db = FalsePositiveDatabase(storage_path)

            # Create a finding
            finding = Finding(
                id="test-001",
                title="Test Finding",
                description="Test description for the finding",
                severity="medium",
            )

            # Add the finding first (should work)
            db.add_finding(finding, is_false_positive=False)

            # Now make the file read-only to cause an error
            os.chmod(storage_path, 0o444)

            try:
                # Try to add another finding - should handle error gracefully
                finding2 = Finding(
                    id="test-002",
                    title="Test Finding 2",
                    description="Another test description",
                    severity="low",
                )
                # Should not raise exception
                db.add_finding(finding2, is_false_positive=True)
            finally:
                os.chmod(storage_path, 0o600)

    def test_load_from_storage_success(self):
        """Lines 421-423: Test _load_from_storage success path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "test_db.json")

            # Create initial database and add findings
            db1 = FalsePositiveDatabase(storage_path)
            finding = Finding(
                id="test-001",
                title="Test Finding",
                description="Test description for the finding",
                severity="high",
            )
            db1.add_finding(finding, is_false_positive=False, user_feedback=False)

            # Create new database instance with same storage path
            # This should load the saved data
            db2 = FalsePositiveDatabase(storage_path)

            # Verify data was loaded
            assert len(db2.findings) == 1
            loaded_hash = finding.get_hash()
            assert loaded_hash in db2.findings
            loaded = db2.findings[loaded_hash]
            assert loaded.is_false_positive is False
            assert loaded.user_feedback is False


class TestFalsePositiveDatabaseMatching:
    """Test FalsePositiveDatabase matching methods - Lines 434-435, 444-448, 452-474, 478-503"""

    def test_calculate_similarity(self):
        """Lines 444-448: Test _calculate_similarity method."""
        db = FalsePositiveDatabase()

        # Test with identical hashes
        hash1 = "abc123"
        hash2 = "abc123"
        similarity = db._calculate_similarity(hash1, hash2)
        assert similarity == 1.0

        # Test with completely different hashes
        hash3 = "xyz789"
        similarity = db._calculate_similarity(hash1, hash3)
        assert 0.0 <= similarity < 1.0

        # Test with some overlap
        hash4 = "abc124"
        similarity = db._calculate_similarity(hash1, hash4)
        assert 0.0 < similarity < 1.0

    def test_check_historical_match_exact(self):
        """Lines 452-474: Test check_historical_match with exact match."""
        db = FalsePositiveDatabase()
        finding = Finding(
            id="test-001",
            title="Test Finding",
            description="Test description for the finding",
            severity="medium",
        )

        # Add finding to database
        db.add_finding(finding, is_false_positive=False)

        # Check for exact match
        match = db.check_historical_match(finding)
        assert match is not None
        assert match.is_false_positive is False

    def test_check_historical_match_similarity_search(self):
        """Lines 421-423: Test similarity search in check_historical_match."""
        db = FalsePositiveDatabase()
        db.similarity_threshold = 0.1  # Low threshold for testing

        finding1 = Finding(
            id="test-001",
            title="Test Finding",
            description="Test description for the finding",
            severity="medium",
        )

        # Add finding to database
        db.add_finding(finding1, is_false_positive=False)

        # Create similar finding (will have different but similar hash)
        finding2 = Finding(
            id="test-002",
            title="Test Finding",
            description="Test description for the finding similar",
            severity="medium",
        )

        # Check for similarity match
        match = db.check_historical_match(finding2)
        # With very low threshold, might match
        # This tests the similarity search path (lines 420-423)

    def test_check_historical_match_no_match(self):
        """Test check_historical_match returns None when no match."""
        db = FalsePositiveDatabase()
        finding = Finding(
            id="test-001",
            title="Test Finding",
            description="Test description for the finding",
            severity="medium",
        )

        # Don't add anything to database
        match = db.check_historical_match(finding)
        assert match is None

    def test_get_fp_likelihood_with_user_feedback(self):
        """Lines 432-433, 434-435: Test get_fp_likelihood with user feedback."""
        db = FalsePositiveDatabase()
        finding = Finding(
            id="test-001",
            title="Test Finding",
            description="Test description for the finding",
            severity="medium",
        )

        # Add finding as false positive with user feedback
        db.add_finding(finding, is_false_positive=True, user_feedback=True)

        # Check likelihood
        likelihood = db.get_fp_likelihood(finding)
        assert likelihood == 1.0

    def test_get_fp_likelihood_with_user_feedback_false(self):
        """Test get_fp_likelihood with user feedback indicating not FP."""
        db = FalsePositiveDatabase()
        finding = Finding(
            id="test-001",
            title="Test Finding",
            description="Test description for the finding",
            severity="medium",
        )

        # Add finding as NOT false positive with user feedback
        db.add_finding(finding, is_false_positive=False, user_feedback=False)

        # Check likelihood
        likelihood = db.get_fp_likelihood(finding)
        assert likelihood == 0.0

    def test_get_fp_likelihood_occurrence_count_high(self):
        """Lines 434-435: Test get_fp_likelihood with occurrence_count >= 3."""
        db = FalsePositiveDatabase()
        finding = Finding(
            id="test-001",
            title="Test Finding",
            description="Test description for the finding",
            severity="medium",
        )

        # Add finding multiple times to increase occurrence count
        db.add_finding(finding, is_false_positive=True)
        db.add_finding(finding, is_false_positive=True)
        db.add_finding(finding, is_false_positive=True)

        # Check likelihood
        likelihood = db.get_fp_likelihood(finding)
        assert likelihood == 0.8

    def test_get_fp_likelihood_occurrence_count_low_fp(self):
        """Test get_fp_likelihood with occurrence_count >= 3 but not FP."""
        db = FalsePositiveDatabase()
        finding = Finding(
            id="test-001",
            title="Test Finding",
            description="Test description for the finding",
            severity="medium",
        )

        # Add finding multiple times as not false positive
        db.add_finding(finding, is_false_positive=False)
        db.add_finding(finding, is_false_positive=False)
        db.add_finding(finding, is_false_positive=False)

        # Check likelihood
        likelihood = db.get_fp_likelihood(finding)
        assert likelihood == 0.2

    def test_get_fp_likelihood_bayesian_filter(self):
        """Test get_fp_likelihood using Bayesian filter (no historical match)."""
        db = FalsePositiveDatabase()
        finding = Finding(
            id="test-001",
            title="Test Finding",
            description="Test description for the finding",
            severity="medium",
        )

        # Don't add to database - should use Bayesian filter
        likelihood = db.get_fp_likelihood(finding)
        # Should return a value between 0 and 1
        assert 0.0 <= likelihood <= 1.0


class TestFalsePositiveDatabaseAddFinding:
    """Test FalsePositiveDatabase.add_finding with user feedback - Lines 391-393"""

    def test_add_finding_updates_existing_with_feedback(self):
        """Lines 391-393: Test updating existing finding with user feedback."""
        db = FalsePositiveDatabase()
        finding = Finding(
            id="test-001",
            title="Test Finding",
            description="Test description for the finding",
            severity="medium",
        )

        # Add finding first time
        db.add_finding(finding, is_false_positive=False)
        finding_hash = finding.get_hash()

        # Add again with user feedback
        db.add_finding(finding, is_false_positive=False, user_feedback=True)

        # Check that user feedback was recorded
        hist = db.findings[finding_hash]
        assert hist.user_feedback is True
        assert hist.feedback_timestamp is not None


class TestLLMVotingEnginePatternMatching:
    """Test LLMVotingEngine pattern matching - Lines 607-612, 617-630"""

    def test_parse_response_false_positive(self):
        """Lines 607-612: Test _parse_response with false positive indicators."""
        from risk_engine.false_positive_engine import LLMVotingEngine

        engine = LLMVotingEngine()

        # Test with false_positive in response
        assert engine._parse_response("This is FALSE_POSITIVE") is True
        assert engine._parse_response("This is false_positive") is True
        assert engine._parse_response("false positive detected") is True
        assert engine._parse_response("This is a false positive finding") is True

    def test_parse_response_true_positive(self):
        """Test _parse_response without false positive indicators."""
        from risk_engine.false_positive_engine import LLMVotingEngine

        engine = LLMVotingEngine()

        # Test with true positive response
        assert engine._parse_response("TRUE_POSITIVE") is False
        assert engine._parse_response("This is a true positive") is False
        assert engine._parse_response("Confirmed vulnerability") is False

    def test_heuristic_decision_with_fp_indicators(self):
        """Lines 617-630: Test _heuristic_decision with FP indicators."""
        from risk_engine.false_positive_engine import LLMVotingEngine

        engine = LLMVotingEngine()

        # Create finding with multiple FP indicators
        finding = Finding(
            id="test-001",
            title="Informational Finding",
            description="This is informational and best practice recommendation",
            severity="info",
        )

        result = engine._heuristic_decision(finding)
        # Should return True (likely FP) with 2+ indicators
        assert result is True

    def test_heuristic_decision_without_fp_indicators(self):
        """Test _heuristic_decision without FP indicators."""
        from risk_engine.false_positive_engine import LLMVotingEngine

        engine = LLMVotingEngine()

        # Create finding without FP indicators
        finding = Finding(
            id="test-001",
            title="SQL Injection",
            description="Critical SQL injection vulnerability found in login form",
            severity="critical",
        )

        result = engine._heuristic_decision(finding)
        # Should return False (likely not FP) with < 2 indicators
        assert result is False

    def test_heuristic_decision_single_indicator(self):
        """Test _heuristic_decision with single FP indicator."""
        from risk_engine.false_positive_engine import LLMVotingEngine

        engine = LLMVotingEngine()

        # Create finding with only one FP indicator
        finding = Finding(
            id="test-001",
            title="Test",
            description="This is informational only",
            severity="low",
        )

        result = engine._heuristic_decision(finding)
        # Should return False (likely not FP) with only 1 indicator
        assert result is False


class TestFalsePositiveEngineLearnFromFeedback:
    """Test FalsePositiveEngine.learn_from_feedback - Lines 908-919"""

    @pytest.mark.asyncio
    async def test_learn_from_feedback_logs_info(self):
        """Lines 908-919: Test learn_from_feedback logs correctly."""
        engine = FalsePositiveEngine(enable_llm_voting=False)

        with patch("risk_engine.false_positive_engine.logger") as mock_logger:
            await engine.learn_from_feedback("finding-001", is_fp=True, user="test_user")

            # Verify logging was called
            mock_logger.info.assert_called()
            # Check that the finding_id is in the log message
            log_calls = [call for call in mock_logger.info.call_args_list]
            assert any("finding-001" in str(call) for call in log_calls)

    @pytest.mark.asyncio
    async def test_learn_from_feedback_no_user(self):
        """Test learn_from_feedback without user parameter."""
        engine = FalsePositiveEngine(enable_llm_voting=False)

        with patch("risk_engine.false_positive_engine.logger") as mock_logger:
            await engine.learn_from_feedback("finding-002", is_fp=False)

            # Verify logging was called
            mock_logger.info.assert_called()
            log_calls = [call for call in mock_logger.info.call_args_list]
            assert any("finding-002" in str(call) for call in log_calls)


class TestCreateFindingFromScanResult:
    """Test create_finding_from_scan_result helper function."""

    def test_create_finding_basic(self):
        """Test basic finding creation."""
        scan_result = {
            "id": "scan-001",
            "title": "XSS Vulnerability",
            "description": "Found XSS in search field",
            "severity": "high",
            "type": "xss",
            "target": "example.com",
            "source": "nuclei",
        }

        finding = create_finding_from_scan_result(scan_result)

        assert finding.id == "scan-001"
        assert finding.title == "XSS Vulnerability"
        assert finding.vulnerability_type == VulnerabilityType.XSS

    def test_create_finding_with_cvss(self):
        """Test finding creation with CVSS data."""
        scan_result = {
            "id": "scan-002",
            "title": "SQL Injection",
            "description": "SQLi in login",
            "severity": "critical",
            "type": "sql_injection",
            "cvss": {
                "base_score": 9.8,
                "vector_string": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                "version": "3.1",
            },
        }

        finding = create_finding_from_scan_result(scan_result)

        assert finding.risk_factors.cvss_data.base_score == 9.8
        assert finding.risk_factors.cvss_data.version == "3.1"


class TestIntegrationScenarios:
    """Integration tests combining multiple components."""

    def test_full_fp_workflow(self):
        """Test complete false positive workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "fp_db.json")

            # Create database
            db = FalsePositiveDatabase(storage_path)

            # Create finding
            finding = Finding(
                id="int-test-001",
                title="Test Vulnerability",
                description="This is a test description for integration testing",
                severity="medium",
                vulnerability_type=VulnerabilityType.MISCONFIGURATION,
                risk_factors=RiskFactors(
                    cvss_data=CVSSData(base_score=6.5),
                    epss_score=0.3,
                    internet_exposed=True,
                    patch_available=False,
                ),
            )

            # Add to database as false positive
            db.add_finding(finding, is_false_positive=True, user_feedback=True)

            # Check historical match
            match = db.check_historical_match(finding)
            assert match is not None
            assert match.user_feedback is True

            # Get likelihood
            likelihood = db.get_fp_likelihood(finding)
            assert likelihood == 1.0

    def test_cvss_epss_integration(self):
        """Test CVSS and EPSS data integration."""
        # Create CVSS data with environmental score
        cvss = CVSSData(base_score=7.0, temporal_score=7.5, environmental_score=8.5)

        # Verify effective score uses environmental
        assert cvss.get_effective_score() == 8.5
        assert cvss.get_severity() == "High"

        # Create EPSS data
        epss = EPSSData(cve_id="CVE-2024-9999", epss_score=0.85, percentile=0.95)

        # Verify EPSS risk level
        assert epss.get_risk_level() == "CRITICAL"
        assert epss.is_high_probability() is True

        # Create risk factors
        risk_factors = RiskFactors(
            cvss_data=cvss,
            epss_score=epss.epss_score,
            internet_exposed=True,
            exploit_code_available=True,
            active_exploitation_observed=True,
            patch_available=False,
        )

        # Calculate weighted score
        score = risk_factors.get_weighted_risk_score()
        assert 0.0 <= score <= 1.0
