"""Tests for false positive filter module"""
import pytest
from modules.false_positive_filter import (
    FalsePositiveFilter, Finding, ConfidenceLevel
)


class TestFalsePositiveFilter:
    """Test FalsePositiveFilter functionality"""

    def test_init(self):
        """Test filter initialization"""
        fpf = FalsePositiveFilter()
        assert fpf.name == "false_positive_filter"
        assert fpf.rules_applied == 0

    def test_apply_rule_based_filter_self_signed(self):
        """Test FP detection for self-signed certificate"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Self-signed certificate detected",
            description="The server uses a self-signed certificate",
            severity="medium",
            cvss_score=5.0,
            evidence=["cert.pem"],
            tool="ssl_scanner"
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is True
        assert "self-signed" in reason.lower()

    def test_apply_rule_based_filter_valid(self):
        """Test valid finding (not FP)"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="SQL Injection in login form",
            description="User input is directly concatenated into SQL query",
            severity="critical",
            cvss_score=9.5,
            evidence=["request.txt", "response.txt", "sqlmap_output"],
            tool="sql_scanner",
            confidence=0.95
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is False

    def test_apply_rule_based_filter_low_confidence(self):
        """Test FP detection for low confidence"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Possible vulnerability",
            description="Something might be wrong",
            severity="low",
            cvss_score=2.0,
            evidence=[],
            tool="scanner",
            confidence=0.1
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is True
        assert "confidence" in reason.lower()

    def test_apply_ml_filter_no_evidence(self):
        """Test ML filter with no evidence"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Vulnerability",
            description="Description",
            severity="high",
            cvss_score=8.0,
            evidence=[],
            tool="scanner"
        )
        score = fpf.apply_ml_filter(finding)
        assert score >= 0.3  # High FP probability due to no evidence

    def test_apply_ml_filter_strong_evidence(self):
        """Test ML filter with strong evidence"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="SQL Injection",
            description="SQLi confirmed",
            severity="critical",
            cvss_score=9.0,
            evidence=["payload.txt", "response.txt", "screenshot.png"],
            tool="sql_scanner"
        )
        score = fpf.apply_ml_filter(finding)
        assert score < 0.3  # Low FP probability

    def test_filter_findings_reduction(self):
        """Test filtering multiple findings"""
        fpf = FalsePositiveFilter()
        findings = [
            Finding(
                title="Self-signed certificate",
                description="Self-signed cert in dev environment",
                severity="low",
                cvss_score=3.0,
                evidence=["cert.pem"],
                tool="ssl_scanner"
            ),
            Finding(
                title="SQL Injection",
                description="Confirmed SQLi",
                severity="critical",
                cvss_score=9.5,
                evidence=["payload.txt", "response.txt"],
                tool="sql_scanner",
                confidence=0.95
            ),
            Finding(
                title="Low confidence alert",
                description="Maybe something",
                severity="low",
                cvss_score=2.0,
                evidence=[],
                tool="scanner",
                confidence=0.2
            )
        ]
        
        result = fpf.filter_findings(findings)
        
        # Should have 1 true positive (SQLi)
        assert len(result['true_positives']) == 1
        assert result['true_positives'][0].title == "SQL Injection"
        
        # Should have 2 false positives
        assert len(result['false_positives']) == 2
        
        # Reduction rate should be ~67%
        assert result['reduction_rate'] == pytest.approx(0.67, abs=0.01)

    def test_filter_findings_empty(self):
        """Test filtering empty list"""
        fpf = FalsePositiveFilter()
        result = fpf.filter_findings([])
        assert result['reduction_rate'] == 0

    def test_get_info(self):
        """Test module info"""
        fpf = FalsePositiveFilter()
        info = fpf.get_info()
        assert info['name'] == 'false_positive_filter'
        assert 'ml' in info['description'].lower()
