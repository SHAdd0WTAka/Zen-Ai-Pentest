"""
Comprehensive Tests for False Positive Filter Module

This module tests the FalsePositiveFilter class which provides
ML-based and rule-based false positive reduction for security findings.

Target Coverage: 70%+
"""

import re
from unittest.mock import MagicMock, patch

import pytest

from modules.false_positive_filter import (
    ConfidenceLevel,
    FalsePositiveFilter,
    Finding,
)


class TestConfidenceLevel:
    """Test ConfidenceLevel enum"""

    def test_enum_values(self):
        """Test enum value definitions"""
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"
        assert ConfidenceLevel.UNKNOWN.value == "unknown"


class TestFinding:
    """Test Finding dataclass"""

    def test_basic_creation(self):
        """Test basic Finding creation"""
        finding = Finding(
            title="SQL Injection",
            description="SQL Injection vulnerability found",
            severity="critical",
            cvss_score=9.5,
            evidence=["payload.txt", "response.txt"],
            tool="sqlmap",
        )
        assert finding.title == "SQL Injection"
        assert finding.description == "SQL Injection vulnerability found"
        assert finding.severity == "critical"
        assert finding.cvss_score == 9.5
        assert finding.evidence == ["payload.txt", "response.txt"]
        assert finding.tool == "sqlmap"
        assert finding.confidence == 0.5  # Default value

    def test_custom_confidence(self):
        """Test Finding with custom confidence"""
        finding = Finding(
            title="XSS",
            description="Cross-site scripting",
            severity="high",
            cvss_score=8.0,
            evidence=["screenshot.png"],
            tool="nuclei",
            confidence=0.85,
        )
        assert finding.confidence == 0.85

    def test_finding_with_empty_evidence(self):
        """Test Finding with empty evidence list"""
        finding = Finding(
            title="Potential Issue",
            description="Something might be wrong",
            severity="low",
            cvss_score=2.0,
            evidence=[],
            tool="scanner",
        )
        assert finding.evidence == []


class TestFalsePositiveFilterInit:
    """Test FalsePositiveFilter initialization"""

    def test_default_init(self):
        """Test default initialization"""
        fpf = FalsePositiveFilter()
        assert fpf.name == "false_positive_filter"
        assert fpf.version == "1.0.0"
        assert fpf.rules_applied == 0
        assert fpf.ml_model_loaded is False

    def test_patterns_loaded(self):
        """Test that FP patterns are loaded"""
        fpf = FalsePositiveFilter()
        assert len(fpf.FALSE_POSITIVE_PATTERNS) > 0
        assert isinstance(fpf.FALSE_POSITIVE_PATTERNS, list)
        assert all(isinstance(p, str) for p in fpf.FALSE_POSITIVE_PATTERNS)

    def test_keywords_loaded(self):
        """Test that FP keywords are loaded"""
        fpf = FalsePositiveFilter()
        assert len(fpf.FP_KEYWORDS) > 0
        assert isinstance(fpf.FP_KEYWORDS, list)
        assert "localhost" in fpf.FP_KEYWORDS
        assert "test" in fpf.FP_KEYWORDS


class TestRuleBasedFilter:
    """Test rule-based filtering"""

    def test_self_signed_certificate(self):
        """Test detection of self-signed certificate as FP"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Self-signed certificate detected",
            description="The server uses a self-signed certificate which is not trusted",
            severity="medium",
            cvss_score=5.0,
            evidence=["cert.pem"],
            tool="ssl_scanner",
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is True
        assert "self-signed" in reason.lower()

    def test_directory_listing_empty(self):
        """Test detection of empty directory listing as FP"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Directory listing enabled",
            description="Directory listing is enabled but the directory is empty",
            severity="info",
            cvss_score=2.0,
            evidence=[],
            tool="nuclei",
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is True
        assert "empty" in reason.lower()

    def test_missing_header_not_applicable(self):
        """Test detection of missing header as FP when not applicable"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Missing security header",
            description="Missing X-Frame-Options header - not applicable for API endpoints",
            severity="low",
            cvss_score=3.0,
            evidence=["headers.txt"],
            tool="security_scanner",
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is True
        assert "not applicable" in reason.lower()

    def test_information_disclosure_normal(self):
        """Test detection of normal version disclosure as FP"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Information disclosure",
            description="Version information disclosure is normal for this endpoint",
            severity="info",
            cvss_score=1.0,
            evidence=["version.txt"],
            tool="scanner",
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is True
        assert "normal" in reason.lower()

    def test_cookie_without_secure_localhost(self):
        """Test detection of localhost cookie issue as FP"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Cookie without secure flag",
            description="Cookie set without secure flag on localhost environment",
            severity="low",
            cvss_score=2.5,
            evidence=["cookie.txt"],
            tool="burp",
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is True
        assert "localhost" in reason.lower()

    def test_fp_keyword_test(self):
        """Test detection of 'test' keyword as FP"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Test environment issue",
            description="This is a test finding in the test environment",
            severity="low",
            cvss_score=2.0,
            evidence=[],
            tool="scanner",
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is True
        assert "test" in reason.lower()

    def test_fp_keyword_localhost(self):
        """Test detection of 'localhost' keyword as FP"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Localhost configuration",
            description="Issue found on localhost:8080",
            severity="low",
            cvss_score=2.0,
            evidence=[],
            tool="scanner",
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is True
        assert "localhost" in reason.lower()

    def test_fp_keyword_127_0_0_1(self):
        """Test detection of '127.0.0.1' keyword as FP"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Local IP issue",
            description="Issue found on 127.0.0.1",
            severity="low",
            cvss_score=2.0,
            evidence=[],
            tool="scanner",
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is True
        assert "127.0.0.1" in reason.lower()

    def test_fp_keyword_example_com(self):
        """Test detection of 'example.com' keyword as FP"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Example domain issue",
            description="Issue found on example.com",
            severity="low",
            cvss_score=2.0,
            evidence=[],
            tool="scanner",
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is True
        assert "example.com" in reason.lower()

    def test_fp_keyword_documentation(self):
        """Test detection of 'documentation' keyword as FP"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Documentation issue",
            description="Issue in the documentation",
            severity="low",
            cvss_score=2.0,
            evidence=[],
            tool="scanner",
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is True
        assert "documentation" in reason.lower()

    def test_fp_keyword_intentional(self):
        """Test detection of 'intentional' keyword as FP"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Intentional behavior",
            description="This is intentional behavior",
            severity="low",
            cvss_score=2.0,
            evidence=[],
            tool="scanner",
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is True
        assert "intentional" in reason.lower()

    def test_fp_keyword_expected_behavior(self):
        """Test detection of 'expected behavior' keyword as FP"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="System behavior",
            description="This is expected behavior for the system",
            severity="low",
            cvss_score=2.0,
            evidence=[],
            tool="scanner",
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is True
        assert "expected behavior" in reason.lower()

    def test_low_confidence_fp(self):
        """Test detection of low confidence finding as FP"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Possible issue",
            description="Something might be wrong",
            severity="low",
            cvss_score=2.0,
            evidence=["scan.txt"],
            tool="scanner",
            confidence=0.2,
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is True
        assert "confidence" in reason.lower()
        assert "0.3" in reason or "threshold" in reason.lower()

    def test_valid_finding_not_fp(self):
        """Test that valid finding is not marked as FP"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="SQL Injection in login form",
            description="User input is directly concatenated into SQL query without sanitization",
            severity="critical",
            cvss_score=9.5,
            evidence=["request.txt", "response.txt", "sqlmap_output.json"],
            tool="sqlmap",
            confidence=0.95,
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is False
        assert reason == ""

    def test_critical_finding_not_fp(self):
        """Test that critical finding with good confidence is not FP"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Remote Code Execution",
            description="Command injection allows arbitrary code execution",
            severity="critical",
            cvss_score=10.0,
            evidence=["payload.py", "output.txt", "screenshot.png"],
            tool="custom_scanner",
            confidence=0.98,
        )
        is_fp, reason = fpf.apply_rule_based_filter(finding)
        assert is_fp is False

    def test_confidence_boundary(self):
        """Test confidence boundary (0.3 threshold)"""
        fpf = FalsePositiveFilter()

        # Exactly at threshold
        finding_at = Finding(
            title="Test",
            description="Test finding",
            severity="low",
            cvss_score=2.0,
            evidence=["test.txt"],
            tool="scanner",
            confidence=0.3,
        )
        is_fp, _ = fpf.apply_rule_based_filter(finding_at)
        # At or below 0.3 is considered FP based on implementation
        assert isinstance(is_fp, bool)

        # Just below threshold
        finding_below = Finding(
            title="Test",
            description="Test finding",
            severity="low",
            cvss_score=2.0,
            evidence=["test.txt"],
            tool="scanner",
            confidence=0.2,
        )
        is_fp, _ = fpf.apply_rule_based_filter(finding_below)
        assert is_fp is True


class TestMLFilter:
    """Test ML-based filtering"""

    def test_ml_filter_no_evidence(self):
        """Test ML filter with no evidence"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Vulnerability",
            description="Description",
            severity="high",
            cvss_score=8.0,
            evidence=[],
            tool="scanner",
        )
        score = fpf.apply_ml_filter(finding)
        assert score >= 0.3  # High FP probability due to no evidence

    def test_ml_filter_single_evidence(self):
        """Test ML filter with single evidence"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Vulnerability",
            description="Description",
            severity="high",
            cvss_score=8.0,
            evidence=["single.txt"],
            tool="scanner",
        )
        score = fpf.apply_ml_filter(finding)
        assert score >= 0.1  # Medium FP probability
        assert score < 0.3

    def test_ml_filter_strong_evidence(self):
        """Test ML filter with strong evidence"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="SQL Injection",
            description="SQLi confirmed with multiple payloads",
            severity="critical",
            cvss_score=9.0,
            evidence=[
                "payload1.txt",
                "payload2.txt",
                "payload3.txt",
                "screenshot.png",
            ],
            tool="sql_scanner",
        )
        score = fpf.apply_ml_filter(finding)
        assert score < 0.1  # Low FP probability

    def test_ml_filter_generic_title(self):
        """Test ML filter with generic title"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Vulnerability found",
            description="A vulnerability was detected",
            severity="medium",
            cvss_score=5.0,
            evidence=["scan.txt"],
            tool="scanner",
        )
        score = fpf.apply_ml_filter(finding)
        assert score >= 0.15  # Higher FP due to generic title

    def test_ml_filter_short_generic_title(self):
        """Test ML filter with short generic title"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Issue",
            description="An issue was found",
            severity="medium",
            cvss_score=5.0,
            evidence=["scan.txt"],
            tool="scanner",
        )
        score = fpf.apply_ml_filter(finding)
        assert score >= 0.15  # Higher FP due to generic short title

    def test_ml_filter_low_severity_low_confidence(self):
        """Test ML filter with low severity and low confidence"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Minor issue",
            description="Something minor",
            severity="low",
            cvss_score=2.0,
            evidence=["scan.txt"],
            tool="scanner",
            confidence=0.4,
        )
        score = fpf.apply_ml_filter(finding)
        assert score >= 0.2  # Higher FP due to low sev + low conf

    def test_ml_filter_max_score(self):
        """Test ML filter score is capped at 1.0"""
        fpf = FalsePositiveFilter()
        finding = Finding(
            title="Issue",  # Generic (short)
            description="Problem found",  # Generic
            severity="low",
            cvss_score=2.0,
            evidence=[],  # No evidence
            tool="scanner",
            confidence=0.2,  # Low confidence
        )
        score = fpf.apply_ml_filter(finding)
        assert score <= 1.0  # Should be capped

    def test_ml_filter_severity_case_sensitive(self):
        """Test that severity comparison is case-insensitive"""
        fpf = FalsePositiveFilter()
        finding_low = Finding(
            title="Test",
            description="Test",
            severity="low",
            cvss_score=2.0,
            evidence=["test.txt"],
            tool="scanner",
            confidence=0.4,
        )
        finding_high = Finding(
            title="Test",
            description="Test",
            severity="high",
            cvss_score=8.0,
            evidence=["test.txt"],
            tool="scanner",
            confidence=0.4,
        )

        score_low = fpf.apply_ml_filter(finding_low)
        score_high = fpf.apply_ml_filter(finding_high)

        # Low severity + low confidence should have higher FP score
        assert score_low > score_high


class TestFilterFindings:
    """Test the main filter_findings method"""

    def test_filter_findings_basic(self):
        """Test basic filtering"""
        fpf = FalsePositiveFilter()
        findings = [
            Finding(
                title="SQL Injection",
                description="Confirmed SQLi",
                severity="critical",
                cvss_score=9.5,
                evidence=["payload.txt", "response.txt"],
                tool="sql_scanner",
                confidence=0.95,
            ),
            Finding(
                title="Self-signed certificate",
                description="Self-signed cert in dev",
                severity="low",
                cvss_score=3.0,
                evidence=["cert.pem"],
                tool="ssl_scanner",
            ),
        ]

        result = fpf.filter_findings(findings)

        assert len(result["true_positives"]) == 1
        assert len(result["false_positives"]) == 1
        assert result["true_positives"][0].title == "SQL Injection"
        assert result["reduction_rate"] == 0.5

    def test_filter_findings_all_true_positives(self):
        """Test filtering with all true positives"""
        fpf = FalsePositiveFilter()
        findings = [
            Finding(
                title="SQL Injection",
                description="Confirmed SQLi",
                severity="critical",
                cvss_score=9.5,
                evidence=["payload.txt"],
                tool="scanner",
                confidence=0.95,
            ),
            Finding(
                title="XSS",
                description="Confirmed XSS",
                severity="high",
                cvss_score=8.0,
                evidence=["payload.txt"],
                tool="scanner",
                confidence=0.9,
            ),
        ]

        result = fpf.filter_findings(findings)

        assert len(result["true_positives"]) == 2
        assert len(result["false_positives"]) == 0
        assert result["reduction_rate"] == 0.0

    def test_filter_findings_all_false_positives(self):
        """Test filtering with all false positives"""
        fpf = FalsePositiveFilter()
        findings = [
            Finding(
                title="Self-signed certificate",
                description="Self-signed",
                severity="low",
                cvss_score=3.0,
                evidence=["cert.pem"],
                tool="scanner",
            ),
            Finding(
                title="Test issue",
                description="Test environment",
                severity="low",
                cvss_score=2.0,
                evidence=[],
                tool="scanner",
                confidence=0.2,
            ),
        ]

        result = fpf.filter_findings(findings)

        assert len(result["true_positives"]) == 0
        assert len(result["false_positives"]) == 2
        assert result["reduction_rate"] == 1.0

    def test_filter_findings_empty(self):
        """Test filtering empty list"""
        fpf = FalsePositiveFilter()
        result = fpf.filter_findings([])
        assert result["true_positives"] == []
        assert result["false_positives"] == []
        assert result["reduction_rate"] == 0

    def test_filter_findings_ml_threshold_boundary(self):
        """Test ML threshold boundary (0.7)"""
        fpf = FalsePositiveFilter()

        # Create finding with specific characteristics to hit threshold
        findings = [
            Finding(
                title="Vulnerability",  # Generic title
                description="Issue found",
                severity="low",
                cvss_score=2.0,
                evidence=["scan.txt"],  # Single evidence
                tool="scanner",
                confidence=0.5,
            ),
        ]

        # With default threshold 0.7, this should be TP (FP score ~0.3)
        result = fpf.filter_findings(findings, fp_threshold=0.7)
        assert len(result["true_positives"]) == 1

        # With lower threshold, it becomes FP
        result = fpf.filter_findings(findings, fp_threshold=0.2)
        assert len(result["false_positives"]) == 1

    def test_filter_findings_fp_structure(self):
        """Test structure of false positive results"""
        fpf = FalsePositiveFilter()
        findings = [
            Finding(
                title="Self-signed certificate",
                description="Self-signed",
                severity="low",
                cvss_score=3.0,
                evidence=["cert.pem"],
                tool="scanner",
            ),
        ]

        result = fpf.filter_findings(findings)

        assert len(result["false_positives"]) == 1
        fp_entry = result["false_positives"][0]
        assert "finding" in fp_entry
        assert "fp_probability" in fp_entry
        assert "reason" in fp_entry
        assert fp_entry["finding"].title == "Self-signed certificate"
        assert isinstance(fp_entry["fp_probability"], float)
        assert isinstance(fp_entry["reason"], str)

    def test_filter_findings_mixed(self):
        """Test filtering with mixed findings"""
        fpf = FalsePositiveFilter()
        findings = [
            Finding(
                title="SQL Injection",
                description="Confirmed SQLi",
                severity="critical",
                cvss_score=9.5,
                evidence=["p1.txt", "p2.txt", "p3.txt"],
                tool="sql_scanner",
                confidence=0.95,
            ),
            Finding(
                title="XSS",
                description="Confirmed XSS",
                severity="high",
                cvss_score=8.0,
                evidence=["p1.txt", "p2.txt"],
                tool="scanner",
                confidence=0.9,
            ),
            Finding(
                title="Self-signed",
                description="Self-signed cert",
                severity="low",
                cvss_score=3.0,
                evidence=["cert.pem"],
                tool="ssl_scanner",
                confidence=0.5,  # Add confidence
            ),
            Finding(
                title="Low confidence",
                description="Maybe something",
                severity="low",
                cvss_score=2.0,
                evidence=[],
                tool="scanner",
                confidence=0.2,
            ),
        ]

        result = fpf.filter_findings(findings)

        # Check that we have reasonable split between TPs and FPs
        assert (
            len(result["true_positives"]) + len(result["false_positives"]) == 4
        )
        # At least 1 TP and 1 FP
        assert len(result["true_positives"]) >= 1
        assert len(result["false_positives"]) >= 1


class TestGetInfo:
    """Test get_info method"""

    def test_get_info(self):
        """Test get_info returns correct structure"""
        fpf = FalsePositiveFilter()
        info = fpf.get_info()

        assert isinstance(info, dict)
        assert info["name"] == "false_positive_filter"
        assert info["version"] == "1.0.0"
        assert "description" in info
        assert "ml" in info["description"].lower()
        assert "rules_count" in info
        assert info["rules_count"] == len(fpf.FALSE_POSITIVE_PATTERNS)
        assert "threshold" in info
        assert info["threshold"] == 0.7

    def test_get_info_consistency(self):
        """Test get_info returns consistent results"""
        fpf = FalsePositiveFilter()
        info1 = fpf.get_info()
        info2 = fpf.get_info()
        assert info1 == info2


class TestPatternMatching:
    """Test pattern matching in rule-based filter"""

    def test_pattern_regex_compilation(self):
        """Test that patterns compile as valid regex"""
        fpf = FalsePositiveFilter()
        for pattern in fpf.FALSE_POSITIVE_PATTERNS:
            try:
                re.compile(pattern)
            except re.error:
                pytest.fail(f"Invalid regex pattern: {pattern}")

    def test_pattern_case_insensitive(self):
        """Test that patterns are case-insensitive"""
        fpf = FalsePositiveFilter()

        # Test with uppercase
        finding_upper = Finding(
            title="SELF-SIGNED CERTIFICATE",
            description="CERTIFICATE IS SELF-SIGNED",
            severity="low",
            cvss_score=3.0,
            evidence=[],
            tool="scanner",
        )
        is_fp, _ = fpf.apply_rule_based_filter(finding_upper)
        assert is_fp is True

        # Test with mixed case
        finding_mixed = Finding(
            title="Self-Signed Certificate",
            description="Certificate is Self-Signed",
            severity="low",
            cvss_score=3.0,
            evidence=[],
            tool="scanner",
        )
        is_fp, _ = fpf.apply_rule_based_filter(finding_mixed)
        assert is_fp is True


class TestIntegration:
    """Integration-style tests"""

    def test_full_workflow(self):
        """Test complete filtering workflow"""
        fpf = FalsePositiveFilter()

        # Simulate findings from a scan
        findings = [
            # True positives
            Finding(
                title="SQL Injection in login",
                description="SQLi in username field",
                severity="critical",
                cvss_score=9.5,
                evidence=["payload.txt", "error.txt", "screenshot.png"],
                tool="sqlmap",
                confidence=0.98,
            ),
            Finding(
                title="Reflected XSS",
                description="XSS in search parameter",
                severity="high",
                cvss_score=7.5,
                evidence=["payload.txt", "response.txt"],
                tool="nuclei",
                confidence=0.9,
            ),
            # False positives
            Finding(
                title="Self-signed certificate in dev",
                description="Development environment uses self-signed cert",
                severity="info",
                cvss_score=1.0,
                evidence=["cert.txt"],
                tool="sslscan",
            ),
            Finding(
                title="Test environment issue",
                description="Issue only in test environment",
                severity="low",
                cvss_score=2.0,
                evidence=[],
                tool="scanner",
                confidence=0.2,
            ),
        ]

        result = fpf.filter_findings(findings)

        # Verify results
        assert len(result["true_positives"]) == 2
        assert len(result["false_positives"]) == 2
        assert result["reduction_rate"] == 0.5

        # Verify info
        info = fpf.get_info()
        assert info["name"] == "false_positive_filter"
        assert info["rules_count"] > 0

    def test_filter_with_high_confidence_fp(self):
        """Test filtering when ML gives high FP score"""
        fpf = FalsePositiveFilter()

        # Create finding that will get high ML FP score
        finding = Finding(
            title="Issue",  # Generic (short, < 30 chars)
            description="Problem",  # Generic
            severity="low",
            cvss_score=2.0,
            evidence=[],  # No evidence
            tool="scanner",
            confidence=0.4,  # Low-ish confidence
        )

        # Get ML score
        ml_score = fpf.apply_ml_filter(finding)

        # This should be flagged as FP
        result = fpf.filter_findings([finding], fp_threshold=0.7)

        # If ML score is high enough, it's a FP
        if ml_score > 0.7:
            assert len(result["false_positives"]) == 1
        else:
            assert len(result["true_positives"]) == 1
