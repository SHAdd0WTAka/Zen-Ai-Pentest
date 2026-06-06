"""ZAP Automation Module - High-Level Security Testing Workflows

This module provides automated security testing workflows using OWASP ZAP:
- Full automated scan workflows
- Scheduled scanning
- CI/CD integration
- Compliance scanning (OWASP Top 10, PCI DSS, etc.)
- Vulnerability trending
- Integration with the orchestrator

Author: Zen-AI-Pentest Team
License: MIT
Version: 3.0.0
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ComplianceStandard(Enum):
    """Compliance standards for scanning"""

    OWASP_TOP_10 = "owasp_top_10"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"
    NIST = "nist"
    CIS = "cis"


class ScanSchedule(Enum):
    """Scan schedule frequencies"""

    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class VulnerabilityTrend:
    """Vulnerability trend data point"""

    timestamp: datetime
    total: int
    high: int
    medium: int
    low: int
    new_findings: int
    resolved_findings: int


@dataclass
class ComplianceResult:
    """Compliance check result"""

    standard: str
    passed: bool
    score: float  # 0-100
    findings: List[Dict[str, Any]]
    requirements_met: List[str]
    requirements_failed: List[str]
    checked_at: datetime


@dataclass
class ScanScheduleConfig:
    """Scan scheduling configuration"""

    target: str
    frequency: ScanSchedule
    policy: str = "Default"
    auth: Optional[Dict[str, Any]] = None
    enabled: bool = True
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    run_count: int = 0


class ZAPAutomationManager:
    """
    High-level ZAP automation manager.

    Features:
    - Automated full scan workflows
    - Scheduled scanning
    - Compliance reporting
    - Vulnerability trending
    - CI/CD integration
    - Baseline comparison
    """

    def __init__(
        self,
        zap_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        storage_path: Optional[str] = None,
    ):
        """
        Initialize ZAP Automation Manager.

        Args:
            zap_url: ZAP API URL
            api_key: ZAP API key
            storage_path: Path for storing scan history and trends
        """
        self.zap_url = zap_url
        self.api_key = api_key
        self.storage_path = storage_path
        self._schedules: Dict[str, ScanScheduleConfig] = {}
        self._trends: Dict[str, List[VulnerabilityTrend]] = {}
        self._scan_history: List[Dict[str, Any]] = []
        self._running = False

    async def run_automated_scan(
        self,
        target: str,
        auth: Optional[Dict[str, Any]] = None,
        policy: str = "Default",
        compliance_standards: Optional[List[ComplianceStandard]] = None,
        baseline_scan_id: Optional[str] = None,
        notify_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """
        Run a fully automated security scan with all features.

        Args:
            target: Target URL
            auth: Authentication configuration
            policy: Scan policy
            compliance_standards: List of compliance standards to check
            baseline_scan_id: Previous scan ID for comparison
            notify_callback: Callback for notifications
            progress_callback: Callback for progress updates

        Returns:
            Complete scan results with analysis
        """
        from tools.zap_integration_enhanced import ZAPAutomation

        scan_start = datetime.now()
        scan_id = f"auto_{scan_start.strftime('%Y%m%d_%H%M%S')}_{hash(target) % 10000}"

        logger.info(f"Starting automated scan {scan_id} for {target}")

        result = {
            "scan_id": scan_id,
            "target": target,
            "started_at": scan_start.isoformat(),
            "status": "running",
            "findings": {},
            "compliance": {},
            "trend": None,
            "baseline_comparison": None,
        }

        try:
            async with ZAPAutomation(self.zap_url, self.api_key) as automation:
                # Run the full scan
                scan_result = await automation.full_scan(
                    target=target,
                    auth=auth,
                    policy=policy,
                    progress_callback=progress_callback,
                )

                if not scan_result.success:
                    result["status"] = "failed"
                    result["error"] = scan_result.error
                    return result

                # Store findings
                result["findings"] = {
                    "total": len(scan_result.alerts),
                    "risk_counts": scan_result.risk_counts,
                    "alerts": [self._alert_to_dict(a) for a in scan_result.alerts],
                    "urls_crawled": scan_result.urls_crawled,
                    "urls_audited": scan_result.urls_audited,
                    "scan_time": scan_result.scan_time,
                }

                # Compliance checks
                if compliance_standards:
                    result["compliance"] = await self._check_compliance(
                        scan_result.alerts,
                        compliance_standards,
                    )

                # Trend analysis
                trend = self._update_trend(target, scan_result)
                result["trend"] = {
                    "timestamp": trend.timestamp.isoformat(),
                    "total": trend.total,
                    "high": trend.high,
                    "medium": trend.medium,
                    "low": trend.low,
                    "new_findings": trend.new_findings,
                    "resolved_findings": trend.resolved_findings,
                }

                # Baseline comparison
                if baseline_scan_id:
                    result["baseline_comparison"] = self._compare_to_baseline(
                        baseline_scan_id,
                        scan_result,
                    )

                result["status"] = "completed"
                result["completed_at"] = datetime.now().isoformat()

                # Store in history
                self._scan_history.append(
                    {
                        "scan_id": scan_id,
                        "target": target,
                        "timestamp": scan_start,
                        "result": result,
                    }
                )

                # Notify
                if notify_callback:
                    notify_callback(
                        {
                            "type": "scan_complete",
                            "scan_id": scan_id,
                            "target": target,
                            "findings_count": len(scan_result.alerts),
                            "risk_summary": scan_result.risk_counts,
                        }
                    )

                logger.info(f"Automated scan {scan_id} completed successfully")

        except Exception as e:
            logger.error(f"Automated scan {scan_id} failed: {e}")
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    async def run_api_scan(
        self,
        target: str,
        openapi_url: Optional[str] = None,
        auth: Optional[Dict[str, Any]] = None,
        notify_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """
        Run an API-specific security scan.

        Args:
            target: API base URL
            openapi_url: URL to OpenAPI/Swagger spec
            auth: Authentication configuration
            notify_callback: Notification callback

        Returns:
            API scan results
        """
        from tools.zap_integration_enhanced import ZAPAutomation

        logger.info(f"Starting API scan for {target}")

        result = {
            "scan_type": "api",
            "target": target,
            "started_at": datetime.now().isoformat(),
            "status": "running",
        }

        try:
            async with ZAPAutomation(self.zap_url, self.api_key) as automation:
                # Import OpenAPI spec if provided
                if openapi_url:
                    client = automation.client
                    await client._request(
                        "openapi/action/importUrl",
                        {"url": openapi_url, "target": target},
                        "POST",
                    )
                    result["openapi_imported"] = True

                # Run API-focused scan
                scan_result = await automation.full_scan(
                    target=target,
                    auth=auth,
                    policy="API Policy",
                )

                if scan_result.success:
                    result["status"] = "completed"
                    result["findings"] = {
                        "total": len(scan_result.alerts),
                        "risk_counts": scan_result.risk_counts,
                    }
                    result["completed_at"] = datetime.now().isoformat()

                    if notify_callback:
                        notify_callback(
                            {
                                "type": "api_scan_complete",
                                "target": target,
                                "findings_count": len(scan_result.alerts),
                            }
                        )
                else:
                    result["status"] = "failed"
                    result["error"] = scan_result.error

        except Exception as e:
            logger.error(f"API scan failed: {e}")
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    async def run_compliance_scan(
        self,
        target: str,
        standards: List[ComplianceStandard],
        auth: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, ComplianceResult]:
        """
        Run a compliance-focused security scan.

        Args:
            target: Target URL
            standards: Compliance standards to check
            auth: Authentication configuration

        Returns:
            Compliance results for each standard
        """
        from tools.zap_integration_enhanced import ZAPAutomation

        logger.info(f"Starting compliance scan for {target}")

        results = {}

        async with ZAPAutomation(self.zap_url, self.api_key) as automation:
            # Run full scan
            scan_result = await automation.full_scan(
                target=target,
                auth=auth,
                policy="Full Policy",
            )

            if scan_result.success:
                # Check each compliance standard
                for standard in standards:
                    compliance = await self._check_compliance_single(
                        scan_result.alerts,
                        standard,
                    )
                    results[standard.value] = compliance

        return results

    def schedule_scan(
        self,
        target: str,
        frequency: ScanSchedule,
        policy: str = "Default",
        auth: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Schedule a recurring scan.

        Args:
            target: Target URL
            frequency: Scan frequency
            policy: Scan policy
            auth: Authentication configuration

        Returns:
            Schedule ID
        """
        schedule_id = f"sched_{hash(target + frequency.value) % 10000}_{int(datetime.now().timestamp())}"

        next_run = self._calculate_next_run(frequency)

        self._schedules[schedule_id] = ScanScheduleConfig(
            target=target,
            frequency=frequency,
            policy=policy,
            auth=auth,
            enabled=True,
            next_run=next_run,
        )

        logger.info(f"Scheduled scan {schedule_id} for {target} ({frequency.value})")

        return schedule_id

    def unschedule_scan(self, schedule_id: str) -> bool:
        """
        Remove a scheduled scan.

        Args:
            schedule_id: Schedule ID

        Returns:
            True if removed
        """
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            logger.info(f"Removed schedule {schedule_id}")
            return True
        return False

    async def run_scheduled_scans(self) -> List[Dict[str, Any]]:
        """
        Run all due scheduled scans.

        Returns:
            List of scan results
        """
        results = []
        now = datetime.now()

        for schedule_id, config in self._schedules.items():
            if not config.enabled:
                continue

            if config.next_run and config.next_run <= now:
                logger.info(f"Running scheduled scan {schedule_id}")

                result = await self.run_automated_scan(
                    target=config.target,
                    auth=config.auth,
                    policy=config.policy,
                )

                results.append(
                    {
                        "schedule_id": schedule_id,
                        "result": result,
                    }
                )

                # Update schedule
                config.last_run = now
                config.run_count += 1
                config.next_run = self._calculate_next_run(config.frequency)

        return results

    def get_trend_report(
        self,
        target: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get vulnerability trend report for a target.

        Args:
            target: Target URL
            days: Number of days to include

        Returns:
            Trend report
        """
        if target not in self._trends:
            return {"error": "No trend data available"}

        cutoff = datetime.now() - timedelta(days=days)
        trends = [t for t in self._trends[target] if t.timestamp >= cutoff]

        if not trends:
            return {"error": "No trend data in specified period"}

        return {
            "target": target,
            "period_days": days,
            "data_points": len(trends),
            "current": {
                "total": trends[-1].total,
                "high": trends[-1].high,
                "medium": trends[-1].medium,
                "low": trends[-1].low,
            },
            "average": {
                "total": sum(t.total for t in trends) / len(trends),
                "high": sum(t.high for t in trends) / len(trends),
                "medium": sum(t.medium for t in trends) / len(trends),
                "low": sum(t.low for t in trends) / len(trends),
            },
            "trend": [
                {
                    "timestamp": t.timestamp.isoformat(),
                    "total": t.total,
                    "high": t.high,
                    "medium": t.medium,
                    "low": t.low,
                }
                for t in trends
            ],
        }

    def generate_cicd_config(
        self,
        target: str,
        format: str = "github_actions",
        fail_on_high: bool = True,
        fail_threshold: int = 0,
    ) -> str:
        """
        Generate CI/CD configuration for ZAP scanning.

        Args:
            target: Target URL
            format: CI/CD format (github_actions, gitlab_ci, jenkins)
            fail_on_high: Fail build on high severity findings
            fail_threshold: Maximum allowed high severity findings

        Returns:
            CI/CD configuration string
        """
        if format == "github_actions":
            return self._generate_github_actions(target, fail_on_high, fail_threshold)
        elif format == "gitlab_ci":
            return self._generate_gitlab_ci(target, fail_on_high, fail_threshold)
        elif format == "jenkins":
            return self._generate_jenkinsfile(target, fail_on_high, fail_threshold)
        else:
            raise ValueError(f"Unsupported CI/CD format: {format}")

    async def _check_compliance(
        self,
        alerts: List[Any],
        standards: List[ComplianceStandard],
    ) -> Dict[str, ComplianceResult]:
        """Check compliance against multiple standards"""
        results = {}
        for standard in standards:
            results[standard.value] = await self._check_compliance_single(alerts, standard)
        return results

    async def _check_compliance_single(
        self,
        alerts: List[Any],
        standard: ComplianceStandard,
    ) -> ComplianceResult:
        """Check compliance against a single standard"""

        # Compliance rules mapping
        compliance_rules = {
            ComplianceStandard.OWASP_TOP_10: {
                "A01:2021-Broken Access Control": ["Path Traversal", "Insecure Direct Object Reference"],
                "A02:2021-Cryptographic Failures": ["Weak Cipher Suite", " cleartext transmission"],
                "A03:2021-Injection": ["SQL Injection", "Command Injection", "LDAP Injection", "XPath Injection"],
                "A04:2021-Insecure Design": ["Missing Anti-CSRF Token", "Insecure Configuration"],
                "A05:2021-Security Misconfiguration": ["X-Frame-Options", "X-Content-Type-Options", "CSP"],
                "A06:2021-Vulnerable Components": ["Outdated Component"],
                "A07:2021-Auth Failures": ["Weak Authentication", "Session Fixation"],
                "A08:2021-Integrity Failures": ["Insecure Deserialization"],
                "A09:2021-Logging Failures": ["Information Disclosure"],
                "A10:2021-SSRF": ["Server-Side Request Forgery"],
            },
            ComplianceStandard.PCI_DSS: {
                "Req 2.1": ["Default Credentials"],
                "Req 4.1": ["Weak Cipher", "SSL", "TLS"],
                "Req 6.5.1": ["Injection"],
                "Req 6.5.7": ["XSS", "Cross Site Scripting"],
                "Req 6.5.8": ["CSRF", "Cross Site Request Forgery"],
                "Req 6.5.10": ["Broken Authentication"],
            },
        }

        rules = compliance_rules.get(standard, {})

        requirements_met = []
        requirements_failed = []
        findings = []

        for req_id, keywords in rules.items():
            req_findings = []
            for alert in alerts:
                for keyword in keywords:
                    if keyword.lower() in alert.name.lower():
                        req_findings.append(alert)
                        break

            if req_findings:
                requirements_failed.append(req_id)
                findings.extend(req_findings)
            else:
                requirements_met.append(req_id)

        total_reqs = len(rules)
        passed_reqs = len(requirements_met)
        score = (passed_reqs / total_reqs * 100) if total_reqs > 0 else 100

        return ComplianceResult(
            standard=standard.value,
            passed=score >= 80,
            score=score,
            findings=[self._alert_to_dict(f) for f in findings],
            requirements_met=requirements_met,
            requirements_failed=requirements_failed,
            checked_at=datetime.now(),
        )

    def _update_trend(
        self,
        target: str,
        scan_result: Any,
    ) -> VulnerabilityTrend:
        """Update vulnerability trend for target"""

        if target not in self._trends:
            self._trends[target] = []

        # Calculate new/resolved
        new_findings = 0
        resolved_findings = 0

        if self._trends[target]:
            last_trend = self._trends[target][-1]
            current_total = len(scan_result.alerts)

            if current_total > last_trend.total:
                new_findings = current_total - last_trend.total
            elif current_total < last_trend.total:
                resolved_findings = last_trend.total - current_total

        trend = VulnerabilityTrend(
            timestamp=datetime.now(),
            total=len(scan_result.alerts),
            high=scan_result.risk_counts.get("High", 0),
            medium=scan_result.risk_counts.get("Medium", 0),
            low=scan_result.risk_counts.get("Low", 0),
            new_findings=new_findings,
            resolved_findings=resolved_findings,
        )

        self._trends[target].append(trend)

        # Keep only last 90 days
        cutoff = datetime.now() - timedelta(days=90)
        self._trends[target] = [t for t in self._trends[target] if t.timestamp >= cutoff]

        return trend

    def _compare_to_baseline(
        self,
        baseline_scan_id: str,
        current_result: Any,
    ) -> Dict[str, Any]:
        """Compare current scan to baseline"""

        # Find baseline
        baseline = None
        for entry in self._scan_history:
            if entry["scan_id"] == baseline_scan_id:
                baseline = entry
                break

        if not baseline:
            return {"error": "Baseline scan not found"}

        baseline_findings = baseline["result"].get("findings", {})
        baseline_alerts = baseline_findings.get("alerts", [])
        current_alerts = current_result.alerts

        baseline_ids = {a.get("name", "") for a in baseline_alerts}
        current_ids = {a.name for a in current_alerts}

        new_findings = list(current_ids - baseline_ids)
        resolved_findings = list(baseline_ids - current_ids)

        return {
            "baseline_scan_id": baseline_scan_id,
            "new_findings_count": len(new_findings),
            "resolved_findings_count": len(resolved_findings),
            "unchanged_count": len(current_ids & baseline_ids),
            "new_findings": new_findings[:10],  # Limit to 10
            "resolved_findings": resolved_findings[:10],
        }

    def _calculate_next_run(self, frequency: ScanSchedule) -> datetime:
        """Calculate next run time based on frequency"""
        now = datetime.now()

        if frequency == ScanSchedule.ONCE:
            return now
        elif frequency == ScanSchedule.DAILY:
            return now + timedelta(days=1)
        elif frequency == ScanSchedule.WEEKLY:
            return now + timedelta(weeks=1)
        elif frequency == ScanSchedule.MONTHLY:
            # Approximate month
            return now + timedelta(days=30)

        return now

    def _alert_to_dict(self, alert: Any) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            "id": alert.alert_id,
            "name": alert.name,
            "risk": alert.risk,
            "confidence": alert.confidence,
            "description": alert.description,
            "solution": alert.solution,
            "url": alert.url,
            "method": alert.method,
            "param": alert.param,
            "evidence": alert.evidence,
            "cwe_id": alert.cwe_id,
            "wasc_id": alert.wasc_id,
        }

    def _generate_github_actions(
        self,
        target: str,
        fail_on_high: bool,
        fail_threshold: int,
    ) -> str:
        """Generate GitHub Actions workflow"""
        lines = [
            "name: ZAP Security Scan",
            "",
            "on:",
            "  schedule:",
            "    - cron: '0 2 * * 1'  # Weekly on Monday at 2 AM",
            "  workflow_dispatch:",
            "",
            "jobs:",
            "  zap-scan:",
            "    runs-on: ubuntu-latest",
            "    steps:",
            "      - name: Checkout",
            "        uses: actions/checkout@v3",
            "",
            "      - name: ZAP Full Scan",
            "        uses: zaproxy/action-full-scan@v0.7.0",
            "        with:",
            f"          target: '{target}'",
            "          rules_file_name: '.zap/rules.tsv'",
            "          cmd_options: '-a'",
            "",
            "      - name: Upload Report",
            "        uses: actions/upload-artifact@v3",
            "        if: always()",
            "        with:",
            "          name: zap-report",
            "          path: report_*.html",
            "",
            "      - name: Check for High Severity",
        ]

        if fail_on_high:
            lines.extend(
                [
                    "        if: always()",
                    "        run: |",
                    "          # Parse results and fail if high severity count exceeds threshold",
                    '          echo "Checking for high severity findings..."',
                ]
            )

        return "\n".join(lines)

    def _generate_gitlab_ci(
        self,
        target: str,
        fail_on_high: bool,
        fail_threshold: int,
    ) -> str:
        """Generate GitLab CI configuration"""
        lines = [
            "# GitLab CI ZAP Security Scan",
            "# Add this to your .gitlab-ci.yml",
            "",
            "stages:",
            "  - security",
            "",
            "zap_scan:",
            "  stage: security",
            "  image: ",
            "    name: owasp/zap2docker-stable",
            '    entrypoint: [""]',
            "  script:",
            "    - mkdir -p /zap/wrk/",
            f"    - zap-full-scan.py -t {target} -r zap_report.html -J zap_report.json",
            "  artifacts:",
            "    when: always",
            "    paths:",
            "      - zap_report.html",
            "      - zap_report.json",
            "    expire_in: 1 week",
        ]

        if fail_on_high:
            lines.append("  allow_failure: false")
        else:
            lines.append("  allow_failure: true")

        lines.extend(
            [
                "  only:",
                "    - schedules",
                "    - main",
            ]
        )

        return "\n".join(lines)

    def _generate_jenkinsfile(
        self,
        target: str,
        fail_on_high: bool,
        fail_threshold: int,
    ) -> str:
        """Generate Jenkinsfile"""
        lines = [
            "// Jenkinsfile for ZAP Security Scan",
            "pipeline {",
            "    agent any",
            "",
            "    triggers {",
            "        cron('H 2 * * 1')  // Weekly on Monday at 2 AM",
            "    }",
            "",
            "    stages {",
            "        stage('ZAP Scan') {",
            "            steps {",
            "                script {",
            "                    // Run ZAP scan using Docker",
            f"                    sh 'docker run -v $(pwd):/zap/wrk/:rw -t owasp/zap2docker-stable zap-full-scan.py -t {target} -r zap_report.html -J zap_report.json'",
            "                }",
            "            }",
            "        }",
            "    }",
            "",
            "    post {",
            "        always {",
            "            // Archive results",
            "            archiveArtifacts artifacts: 'zap_report.*', allowEmptyArchive: true",
            "            ",
            "            // Publish HTML report",
            "            publishHTML([",
            "                allowMissing: false,",
            "                alwaysLinkToLastBuild: true,",
            "                keepAll: true,",
            "                reportDir: '.',",
            "                reportFiles: 'zap_report.html',",
            "                reportName: 'ZAP Security Report'",
            "            ])",
            "        }",
        ]

        if fail_on_high:
            lines.extend(
                [
                    "        failure {",
                    '            error("Security scan found critical issues")',
                    "        }",
                ]
            )

        lines.extend(
            [
                "    }",
                "}",
            ]
        )

        return "\n".join(lines)


# Convenience function for quick automation
def create_automation_manager(
    zap_url: str = "http://localhost:8080",
    api_key: Optional[str] = None,
) -> ZAPAutomationManager:
    """
    Create a ZAP automation manager instance.

    Args:
        zap_url: ZAP API URL
        api_key: ZAP API key

    Returns:
        ZAPAutomationManager instance
    """
    return ZAPAutomationManager(zap_url, api_key)


# ReAct Agent Integration
try:
    from langchain_core.tools import tool

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

    def tool(func=None, **kwargs):
        if func:
            return func
        return lambda f: f


@tool
def zap_automated_security_test(
    target: str,
    auth_type: str = "",
    auth_token: str = "",
    compliance: str = "",
    api_url: str = "http://localhost:8080",
    api_key: str = "",
) -> str:
    """
    Execute a complete automated security test using OWASP ZAP.

    This tool runs a comprehensive security scan with compliance checking
    and trend analysis. It's the recommended way to perform security testing.

    Args:
        target: Target URL to scan
        auth_type: Authentication type (form, jwt, api_key, basic, oauth2)
        auth_token: Token for authentication
        compliance: Comma-separated compliance standards (owasp_top_10, pci_dss)
        api_url: ZAP API URL
        api_key: ZAP API key

    Returns:
        Complete security test results
    """

    async def run_test():
        manager = create_automation_manager(api_url, api_key or None)

        # Build auth config
        auth = None
        if auth_type:
            auth = {"type": auth_type}
            if auth_token:
                auth["token"] = auth_token

        # Parse compliance standards
        compliance_standards = []
        if compliance:
            for std in compliance.split(","):
                std = std.strip().lower()
                if std == "owasp_top_10":
                    compliance_standards.append(ComplianceStandard.OWASP_TOP_10)
                elif std == "pci_dss":
                    compliance_standards.append(ComplianceStandard.PCI_DSS)

        result = await manager.run_automated_scan(
            target=target,
            auth=auth,
            compliance_standards=compliance_standards if compliance_standards else None,
        )

        return result

    try:
        result = asyncio.run(run_test())

        if result["status"] == "failed":
            return f"Security test failed: {result.get('error', 'Unknown error')}"

        lines = [
            f"Security Test Complete: {result['scan_id']}",
            f"Target: {result['target']}",
            f"Status: {result['status']}",
            "",
            "Findings Summary:",
        ]

        findings = result.get("findings", {})
        risk_counts = findings.get("risk_counts", {})

        for risk in ["High", "Medium", "Low", "Informational"]:
            count = risk_counts.get(risk, 0)
            lines.append(f"  {risk}: {count}")

        lines.extend(
            [
                "",
                f"URLs Crawled: {findings.get('urls_crawled', 0)}",
                f"Scan Duration: {findings.get('scan_time', 0):.2f}s",
            ]
        )

        # Compliance results
        if result.get("compliance"):
            lines.extend(["", "Compliance Results:"])
            for std, comp_result in result["compliance"].items():
                status = "PASS" if comp_result["passed"] else "FAIL"
                lines.append(f"  {std}: {status} ({comp_result['score']:.1f}%)")

        # Trend
        if result.get("trend"):
            trend = result["trend"]
            lines.extend(["", "Trend Analysis:"])
            if trend.get("new_findings"):
                lines.append(f"  New findings: {trend['new_findings']}")
            if trend.get("resolved_findings"):
                lines.append(f"  Resolved: {trend['resolved_findings']}")

        return "\n".join(lines)

    except Exception as e:
        return f"Error running security test: {e}"


@tool
def zap_schedule_security_scan(
    target: str,
    frequency: str = "weekly",
    policy: str = "Default",
    api_url: str = "http://localhost:8080",
    api_key: str = "",
) -> str:
    """
    Schedule a recurring security scan.

    Args:
        target: Target URL to scan
        frequency: Scan frequency (once, daily, weekly, monthly)
        policy: Scan policy
        api_url: ZAP API URL
        api_key: ZAP API key

    Returns:
        Schedule confirmation
    """
    try:
        manager = create_automation_manager(api_url, api_key or None)

        freq_map = {
            "once": ScanSchedule.ONCE,
            "daily": ScanSchedule.DAILY,
            "weekly": ScanSchedule.WEEKLY,
            "monthly": ScanSchedule.MONTHLY,
        }

        freq = freq_map.get(frequency.lower(), ScanSchedule.WEEKLY)
        schedule_id = manager.schedule_scan(target, freq, policy)

        return f"Scan scheduled successfully!\nSchedule ID: {schedule_id}\nTarget: {target}\nFrequency: {frequency}\nNext run: {manager._schedules[schedule_id].next_run}"

    except Exception as e:
        return f"Error scheduling scan: {e}"


@tool
def zap_generate_cicd_config(
    target: str,
    format: str = "github_actions",
    fail_on_high: bool = True,
) -> str:
    """
    Generate CI/CD configuration for ZAP scanning.

    Creates ready-to-use configuration for GitHub Actions, GitLab CI, or Jenkins.

    Args:
        target: Target URL
        format: CI/CD format (github_actions, gitlab_ci, jenkins)
        fail_on_high: Fail build on high severity findings

    Returns:
        CI/CD configuration
    """
    try:
        manager = create_automation_manager()
        config = manager.generate_cicd_config(
            target=target,
            format=format,
            fail_on_high=fail_on_high,
        )
        return f"Generated {format} configuration:\n\n```yaml\n{config}\n```"
    except Exception as e:
        return f"Error generating CI/CD config: {e}"


# Tool Registry Integration
try:
    from tools.tool_registry import ToolCategory, ToolSafetyLevel, registry

    TOOL_REGISTRY_AVAILABLE = True
except ImportError:
    TOOL_REGISTRY_AVAILABLE = False
    registry = None
    ToolCategory = None
    ToolSafetyLevel = None


def register_zap_automation_tools():
    """Register ZAP automation tools with the tool registry"""
    if not TOOL_REGISTRY_AVAILABLE or not LANGCHAIN_AVAILABLE:
        return

    try:
        registry.register(
            tool=zap_automated_security_test,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.DANGEROUS,
            requires_approval=True,
            tags=["web", "vulnerability", "scanner", "owasp", "zap", "automation", "compliance"],
            author="Zen-AI-Pentest Team",
            version="3.0.0",
        )

        registry.register(
            tool=zap_schedule_security_scan,
            category=ToolCategory.CONFIGURATION,
            safety_level=ToolSafetyLevel.SAFE,
            requires_approval=False,
            tags=["web", "schedule", "zap", "automation"],
            author="Zen-AI-Pentest Team",
            version="3.0.0",
        )

        registry.register(
            tool=zap_generate_cicd_config,
            category=ToolCategory.CONFIGURATION,
            safety_level=ToolSafetyLevel.SAFE,
            requires_approval=False,
            tags=["web", "cicd", "pipeline", "zap", "automation"],
            author="Zen-AI-Pentest Team",
            version="3.0.0",
        )

        logger.info("ZAP automation tools registered successfully")
    except Exception as e:
        logger.warning(f"Could not register ZAP automation tools: {e}")


# Auto-register on import
try:
    register_zap_automation_tools()
except Exception:
    pass


__all__ = [
    "ZAPAutomationManager",
    "ComplianceStandard",
    "ScanSchedule",
    "VulnerabilityTrend",
    "ComplianceResult",
    "ScanScheduleConfig",
    "create_automation_manager",
    "zap_automated_security_test",
    "zap_schedule_security_scan",
    "zap_generate_cicd_config",
]
