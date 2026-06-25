import pytest

from database.correlation_engine import (
    CorrelatedGroup,
    CorrelationEngine,
    CorrelationResult,
    _count_severities,
    _dedup_key,
    _list_hosts,
    _max_cvss_in,
    _max_severity_among,
    _severity_rank,
    severity_score,
)


def _mkf(id_, title, severity, cvss, cve, target, port, service, tool="nmap", scan_id=1):
    return {
        "id": id_,
        "scan_id": scan_id,
        "title": title,
        "description": "",
        "severity": severity,
        "cvss_score": cvss,
        "cve_id": cve,
        "target": target,
        "port": port,
        "service": service,
        "tool": tool,
    }


class TestHelpers:
    def test_severity_rank(self):
        assert _severity_rank("critical") == 4
        assert _severity_rank("high") == 3
        assert _severity_rank("medium") == 2
        assert _severity_rank("low") == 1
        assert _severity_rank("info") == 0
        assert _severity_rank("unknown") == -1

    def test_max_severity_among(self):
        assert _max_severity_among(["info", "low", "high"]) == "high"
        assert _max_severity_among(["info", "medium"]) == "medium"
        assert _max_severity_among([]) == "info"

    def test_count_severities(self):
        sevs = ["critical", "high", "critical", "low", "info"]
        assert _count_severities(sevs, "critical") == 2
        assert _count_severities(sevs, "high") == 1
        assert _count_severities(sevs, "medium") == 0

    def test_max_cvss_in(self):
        findings = [
            {"cvss_score": 5.0},
            {"cvss_score": 9.8},
            {"cvss_score": None},
        ]
        assert _max_cvss_in(findings) == 9.8
        with pytest.raises(ValueError):
            _max_cvss_in([])

    def test_list_hosts(self):
        findings = [
            {"target": "10.0.0.1"},
            {"target": "10.0.0.2"},
            {"target": "10.0.0.1"},
        ]
        assert _list_hosts(findings) == ["10.0.0.1", "10.0.0.2"]

    def test_dedup_key_cve(self):
        f = {"cve_id": "CVE-2024-1234", "target": "10.0.0.1", "port": 80}
        assert _dedup_key(f) == "CVE-2024-1234"

    def test_dedup_key_hash(self):
        f = {"cve_id": "", "target": "10.0.0.1", "port": 80, "service": "http", "title": "Weak SSL"}
        key = _dedup_key(f)
        assert key.startswith("c") or key.isalnum()
        assert len(key) == 64

    def test_severity_score_convenience(self):
        assert severity_score("critical") == 4
        assert severity_score("info") == 0


class TestCorrelationEngineDedup:
    def test_cve_dedup(self):
        engine = CorrelationEngine()
        findings = [
            _mkf(1, "Apache RCE", "critical", 9.8, "CVE-2024-1234", "10.0.0.1", 80, "http"),
            _mkf(2, "Apache RCE", "critical", 9.8, "CVE-2024-1234", "10.0.0.1", 80, "http", tool="nikto"),
        ]
        result = engine.correlate_findings_in_memory(findings)
        assert result.original_findings_count == 2
        assert result.correlated_count == 1
        assert len(result.groups) == 1

    def test_host_port_service_dedup(self):
        engine = CorrelationEngine()
        findings = [
            _mkf(1, "Weak SSL", "medium", 5.0, "", "10.0.0.1", 443, "https", tool="sslscan"),
            _mkf(2, "Weak SSL", "medium", 5.0, "", "10.0.0.1", 443, "https", tool="testssl"),
        ]
        result = engine.correlate_findings_in_memory(findings)
        assert result.correlated_count == 1

    def test_different_findings_not_deduped(self):
        engine = CorrelationEngine()
        findings = [
            _mkf(1, "Vuln A", "high", 7.5, "", "10.0.0.1", 80, "http"),
            _mkf(2, "Vuln B", "medium", 5.0, "", "10.0.0.2", 443, "https"),
        ]
        result = engine.correlate_findings_in_memory(findings)
        assert result.correlated_count == 2

    def test_empty_findings(self):
        engine = CorrelationEngine()
        result = engine.correlate_findings_in_memory([])
        assert result.original_findings_count == 0
        assert result.correlated_count == 0
        assert result.risk_score == 0.0


class TestCorrelationEngineWidespread:
    def test_cve_widespread_detection(self):
        engine = CorrelationEngine()
        findings = [_mkf(i, "Log4Shell", "critical", 10.0, "CVE-2021-44228", f"10.0.0.{i}", 80, "http") for i in range(1, 5)]
        result = engine.correlate_findings_in_memory(findings)
        assert len(result.widespread) == 1
        assert "CVE-2021-44228" in result.widespread
        assert result.groups[0].is_widespread is True

    def test_non_cve_widespread_detection(self):
        engine = CorrelationEngine()
        findings = [_mkf(i, "OpenSSH Banner", "low", 2.5, "", f"10.0.0.{i}", 22, "ssh") for i in range(1, 5)]
        result = engine.correlate_findings_in_memory(findings)
        assert "OpenSSH Banner" in result.widespread
        for g in result.groups:
            if g.key == result.widespread[0]:
                assert g.is_widespread is True

    def test_not_widespread_under_three_hosts(self):
        engine = CorrelationEngine()
        findings = [
            _mkf(1, "Some Vuln", "medium", 5.0, "", "10.0.0.1", 80, "http"),
            _mkf(2, "Some Vuln", "medium", 5.0, "", "10.0.0.2", 80, "http"),
        ]
        result = engine.correlate_findings_in_memory(findings)
        assert len(result.widespread) == 0


class TestCorrelationEngineRiskScore:
    def test_risk_score_calculation(self):
        engine = CorrelationEngine()
        findings = [
            _mkf(1, "Critical RCE", "critical", 9.8, "CVE-2024-0001", "10.0.0.1", 80, "http"),
            _mkf(2, "High XSS", "high", 6.5, "", "10.0.0.1", 80, "http"),
        ]
        result = engine.correlate_findings_in_memory(findings)
        assert 0.0 <= result.risk_score <= 10.0

    def test_risk_score_capped_at_10(self):
        result = CorrelationEngine._compute_risk_score(
            severities=["critical", "critical"],
            group_count=10,
            max_cvss=9.9,
            widespread_count=3,
        )
        assert result == 10.0

    def test_risk_score_base_from_cvss(self):
        result = CorrelationEngine._compute_risk_score(
            severities=["info"],
            group_count=1,
            max_cvss=7.5,
            widespread_count=0,
        )
        assert result == 7.5

    def test_risk_score_base_default_when_no_cvss(self):
        result = CorrelationEngine._compute_risk_score(
            severities=["info"],
            group_count=1,
            max_cvss=0.0,
            widespread_count=0,
        )
        assert result == 5.0

    def test_risk_severity_boost(self):
        critical = CorrelationEngine._compute_risk_score(
            severities=["critical"],
            group_count=1,
            max_cvss=5.0,
            widespread_count=0,
        )
        info = CorrelationEngine._compute_risk_score(
            severities=["info"],
            group_count=1,
            max_cvss=5.0,
            widespread_count=0,
        )
        assert critical == 6.0
        assert info == 5.0

    def test_risk_group_boost(self):
        many = CorrelationEngine._compute_risk_score(
            severities=["info"],
            group_count=5,
            max_cvss=5.0,
            widespread_count=0,
        )
        few = CorrelationEngine._compute_risk_score(
            severities=["info"],
            group_count=1,
            max_cvss=5.0,
            widespread_count=0,
        )
        assert many == 5.5
        assert few == 5.0

    def test_risk_widespread_boost(self):
        w = CorrelationEngine._compute_risk_score(
            severities=["info"],
            group_count=1,
            max_cvss=5.0,
            widespread_count=1,
        )
        no_w = CorrelationEngine._compute_risk_score(
            severities=["info"],
            group_count=1,
            max_cvss=5.0,
            widespread_count=0,
        )
        assert w == 6.0
        assert no_w == 5.0


class TestCorrelationEngineReport:
    def test_generate_report_text(self):
        engine = CorrelationEngine()
        findings = [
            _mkf(1, "Critical RCE", "critical", 9.8, "CVE-2024-0001", "10.0.0.1", 80, "http"),
            _mkf(2, "Info Leak", "info", 0.0, "", "10.0.0.2", 22, "ssh"),
        ]
        result = engine.correlate_findings_in_memory(findings)
        report = CorrelationEngine._format_report(42, result)
        assert "Correlation Report" in report
        assert "Scan #42" in report
        assert "Critical" in report
        assert "risk_score" in report or "Risk" in report

    def test_report_severity_counts(self):
        engine = CorrelationEngine()
        findings = [
            _mkf(1, "Critical", "critical", 9.8, "CVE-1", "10.0.0.1", 80, "http"),
            _mkf(2, "High", "high", 7.5, "", "10.0.0.1", 80, "http"),
            _mkf(3, "Medium", "medium", 5.0, "", "10.0.0.1", 80, "http"),
            _mkf(4, "Low", "low", 2.5, "", "10.0.0.1", 80, "http"),
            _mkf(5, "Info", "info", 0.0, "", "10.0.0.1", 80, "http"),
        ]
        result = engine.correlate_findings_in_memory(findings)
        assert result.critical_count >= 1
        assert result.high_count >= 1
        assert result.medium_count >= 1
        assert result.low_count >= 1
        assert result.info_count >= 1

    def test_correlated_group_max_severity(self):
        findings = [
            _mkf(1, "Vuln", "high", 7.5, "CVE-2024-X", "10.0.0.1", 80, "http"),
            _mkf(2, "Vuln", "medium", 5.0, "CVE-2024-X", "10.0.0.1", 80, "http"),
        ]
        engine = CorrelationEngine()
        result = engine.correlate_findings_in_memory(findings)
        g = result.groups[0]
        assert g.max_severity == "high"
        assert g.max_cvss == 7.5

    def test_correlated_group_hosts(self):
        findings = [
            _mkf(1, "Vuln", "high", 7.5, "CVE-X", "10.0.0.1", 80, "http"),
            _mkf(2, "Vuln", "high", 7.5, "CVE-X", "10.0.0.2", 80, "http"),
        ]
        engine = CorrelationEngine()
        result = engine.correlate_findings_in_memory(findings)
        g = result.groups[0]
        assert g.hosts_affected == 2
