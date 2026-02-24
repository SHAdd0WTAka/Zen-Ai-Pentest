"""
Zen-Ai-Pentest AnalysisBot - Hauptmodul
=======================================
AnalysisBot fÃ¼r das Zen-Ai-Pentest Multi-Agent-System.

Autor: AnalysisBot
Version: 1.0.0 (2026)

Features:
- Schwachstellen-Analyse
- Risiko-Bewertung (CVSS, FAIR, DREAD, OWASP)
- Exploitability-Assessment
- Impact-Analyse
- Empfehlungs-Generierung
- Compliance-Mapping
- Report-Generierung
"""

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .engines.exploitability_checker import (
    ExploitabilityAssessment,
    get_exploitability_checker,
)
from .engines.recommendation_engine import (
    ComplianceFramework,
    Recommendation,
    RemediationPriority,
    get_recommendation_engine,
)
from .engines.risk_scorer import (
    AssetCriticality,
    RiskFactors,
    RiskScore,
    ThreatActor,
    get_risk_scorer,
)

# Lokale Module
from .engines.vulnerability_analyzer import (
    CVSSVector,
    Vulnerability,
    VulnerabilityCategory,
    VulnerabilitySource,
    get_analyzer,
)

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AnalysisStatus(Enum):
    """Status der Analyse"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class AnalysisResult:
    """Ergebnis einer vollstÃ¤ndigen Analyse"""

    # Identifikation
    analysis_id: str = field(
        default_factory=lambda: f"ANALYSIS-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    )
    target: str = ""

    # Status
    status: AnalysisStatus = AnalysisStatus.PENDING

    # Komponenten
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    risk_scores: List[RiskScore] = field(default_factory=list)
    exploitability_assessments: List[ExploitabilityAssessment] = field(
        default_factory=list
    )
    recommendations: List[Recommendation] = field(default_factory=list)

    # Aggregierte Ergebnisse
    summary: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)

    # Metadaten
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    analysis_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "target": self.target,
            "status": self.status.value,
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "risk_scores": [r.to_dict() for r in self.risk_scores],
            "exploitability_assessments": [
                e.to_dict() for e in self.exploitability_assessments
            ],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "summary": self.summary,
            "statistics": self.statistics,
            "started_at": (
                self.started_at.isoformat() if self.started_at else None
            ),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "duration_seconds": self.duration_seconds,
            "analysis_version": self.analysis_version,
        }


@dataclass
class AnalysisConfig:
    """Konfiguration fÃ¼r die Analyse"""

    # Aktivierte Module
    enable_vulnerability_analysis: bool = True
    enable_risk_scoring: bool = True
    enable_exploitability_check: bool = True
    enable_recommendations: bool = True

    # Scoring-Methoden
    scoring_methods: List[str] = field(
        default_factory=lambda: ["cvss", "fair", "dread", "owasp", "context"]
    )
    scoring_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "cvss": 0.30,
            "fair": 0.25,
            "dread": 0.20,
            "owasp": 0.15,
            "context": 0.10,
        }
    )

    # Risk Factors
    risk_factors: Optional[RiskFactors] = None
    asset_criticality: AssetCriticality = AssetCriticality.MEDIUM
    threat_actor: ThreatActor = ThreatActor.CYBERCRIMINAL

    # Filter
    min_severity: str = "low"  # info, low, medium, high, critical
    max_results: int = 1000

    # Compliance
    compliance_frameworks: List[ComplianceFramework] = field(
        default_factory=list
    )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["asset_criticality"] = self.asset_criticality.value
        data["threat_actor"] = self.threat_actor.value
        data["compliance_frameworks"] = [
            cf.value for cf in self.compliance_frameworks
        ]
        if self.risk_factors:
            data["risk_factors"] = self.risk_factors.to_dict()
        return data


class AnalysisBot:
    """
    AnalysisBot - Hauptklasse fÃ¼r das Zen-Ai-Pentest Multi-Agent-System.

    Der AnalysisBot koordiniert alle Analyse-Module:
    - VulnerabilityAnalyzer: Schwachstellenerkennung
    - RiskScorer: Risiko-Bewertung
    - ExploitabilityChecker: Exploitierbarkeits-Analyse
    - RecommendationEngine: Empfehlungs-Generierung

    Usage:
        bot = AnalysisBot()
        result = bot.analyze(vulnerabilities, config)
        report = bot.generate_report(result, format="json")
    """

    def __init__(self):
        # Initialisiere Module
        self.vulnerability_analyzer = get_analyzer()
        self.risk_scorer = get_risk_scorer()
        self.exploitability_checker = get_exploitability_checker()
        self.recommendation_engine = get_recommendation_engine()

        # Tracking
        self.analysis_history: List[AnalysisResult] = []
        self.metrics = defaultdict(int)

        logger.info("AnalysisBot initialisiert")

    def analyze(
        self,
        vulnerabilities: List[Dict[str, Any]],
        config: Optional[AnalysisConfig] = None,
    ) -> AnalysisResult:
        """
        FÃ¼hrt eine vollstÃ¤ndige Analyse durch.

        Args:
            vulnerabilities: Liste von Schwachstellen-Dictionaries
            config: Analyse-Konfiguration

        Returns:
            AnalysisResult mit allen Analyse-Ergebnissen
        """
        config = config or AnalysisConfig()
        result = AnalysisResult()
        result.started_at = datetime.utcnow()
        result.status = AnalysisStatus.RUNNING

        logger.info(
            f"Starte Analyse von {len(vulnerabilities)} Schwachstellen"
        )

        try:
            # 1. Vulnerability Analysis
            if config.enable_vulnerability_analysis:
                logger.info("FÃ¼hre Schwachstellen-Analyse durch...")
                result.vulnerabilities = self._analyze_vulnerabilities(
                    vulnerabilities
                )
                self.metrics["vulnerabilities_analyzed"] += len(
                    result.vulnerabilities
                )

            # 2. Risk Scoring
            if config.enable_risk_scoring:
                logger.info("Berechne Risiko-Scores...")
                result.risk_scores = self._calculate_risk_scores(
                    result.vulnerabilities, config
                )
                self.metrics["risk_scores_calculated"] += len(
                    result.risk_scores
                )

            # 3. Exploitability Assessment
            if config.enable_exploitability_check:
                logger.info("Bewerte Exploitierbarkeit...")
                result.exploitability_assessments = (
                    self._assess_exploitability(result.vulnerabilities)
                )
                self.metrics["exploitability_assessed"] += len(
                    result.exploitability_assessments
                )

            # 4. Generate Recommendations
            if config.enable_recommendations:
                logger.info("Generiere Empfehlungen...")
                result.recommendations = self._generate_recommendations(
                    result.vulnerabilities,
                    result.risk_scores,
                    result.exploitability_assessments,
                )
                self.metrics["recommendations_generated"] += len(
                    result.recommendations
                )

            # 5. Generate Summary
            result.summary = self._generate_summary(result)
            result.statistics = self._generate_statistics(result)

            result.status = AnalysisStatus.COMPLETED

        except Exception as e:
            logger.error(f"Analyse-Fehler: {e}")
            result.status = AnalysisStatus.FAILED
            result.summary["error"] = str(e)

        finally:
            result.completed_at = datetime.utcnow()
            if result.started_at:
                result.duration_seconds = (
                    result.completed_at - result.started_at
                ).total_seconds()

            self.analysis_history.append(result)

        logger.info(f"Analyse abgeschlossen in {result.duration_seconds:.2f}s")
        return result

    async def analyze_async(
        self,
        vulnerabilities: List[Dict[str, Any]],
        config: Optional[AnalysisConfig] = None,
    ) -> AnalysisResult:
        """Asynchrone Version der Analyse"""
        # FÃ¼hre Analyse in Thread-Pool aus
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.analyze, vulnerabilities, config
        )

    def analyze_code(
        self, code: str, filename: str = "", language: str = "auto"
    ) -> List[Vulnerability]:
        """
        Analysiert Code auf Schwachstellen.

        Args:
            code: Zu analysierender Code
            filename: Dateiname
            language: Programmiersprache

        Returns:
            Liste gefundener Schwachstellen
        """
        return self.vulnerability_analyzer.analyze_code(
            code, filename, language
        )

    def analyze_http_response(
        self, response: Dict[str, Any], target: str
    ) -> List[Vulnerability]:
        """
        Analysiert HTTP-Response auf Schwachstellen.

        Args:
            response: HTTP-Response-Daten
            target: Ziel-URL oder IP

        Returns:
            Liste gefundener Schwachstellen
        """
        return self.vulnerability_analyzer.analyze_http_response(
            response, target
        )

    def calculate_risk(
        self,
        vulnerability: Dict[str, Any],
        config: Optional[AnalysisConfig] = None,
    ) -> RiskScore:
        """
        Berechnet Risiko-Score fÃ¼r eine Schwachstelle.

        Args:
            vulnerability: Schwachstellen-Daten
            config: Analyse-Konfiguration

        Returns:
            RiskScore
        """
        config = config or AnalysisConfig()

        return self.risk_scorer.calculate_comprehensive_risk(
            cvss_vector=vulnerability.get("cvss_vector"),
            cvss_score=vulnerability.get("cvss_score"),
            factors=config.risk_factors,
            asset_criticality=config.asset_criticality,
            threat_actor=config.threat_actor,
            custom_weights=config.scoring_weights,
        )

    def assess_exploitability(
        self, vulnerability: Dict[str, Any]
    ) -> ExploitabilityAssessment:
        """
        Bewertet Exploitierbarkeit einer Schwachstelle.

        Args:
            vulnerability: Schwachstellen-Daten

        Returns:
            ExploitabilityAssessment
        """
        return self.exploitability_checker.assess_vulnerability(vulnerability)

    def generate_recommendation(
        self,
        vulnerability: Dict[str, Any],
        risk_score: Dict[str, Any],
        exploitability: Dict[str, Any],
    ) -> Recommendation:
        """
        Generiert Empfehlung fÃ¼r eine Schwachstelle.

        Args:
            vulnerability: Schwachstellen-Daten
            risk_score: Risk Score Daten
            exploitability: Exploitability Daten

        Returns:
            Recommendation
        """
        return self.recommendation_engine.generate_recommendation(
            vulnerability, risk_score, exploitability
        )

    def prioritize_vulnerabilities(
        self,
        vulnerabilities: List[Dict[str, Any]],
        config: Optional[AnalysisConfig] = None,
    ) -> List[Dict[str, Any]]:
        """
        Priorisiert Schwachstellen nach Risiko.

        Args:
            vulnerabilities: Liste von Schwachstellen
            config: Analyse-Konfiguration

        Returns:
            Priorisierte Liste
        """
        config = config or AnalysisConfig()

        prioritized = []
        for vuln in vulnerabilities:
            risk_score = self.calculate_risk(vuln, config)
            exploitability = self.assess_exploitability(vuln)

            # Berechne Gesamt-Score
            total_score = (
                risk_score.final_score * 0.6 + exploitability.score * 0.4
            )

            prioritized.append(
                {
                    **vuln,
                    "risk_score": risk_score.to_dict(),
                    "exploitability": exploitability.to_dict(),
                    "total_score": round(total_score, 2),
                }
            )

        # Sortiere nach Gesamt-Score
        prioritized.sort(key=lambda x: x["total_score"], reverse=True)

        # Weise Rang zu
        for i, item in enumerate(prioritized):
            item["priority_rank"] = i + 1

        return prioritized

    def generate_report(
        self, result: AnalysisResult, format: str = "json"
    ) -> Union[str, Dict]:
        """
        Generiert einen Bericht aus Analyse-Ergebnissen.

        Args:
            result: AnalysisResult
            format: Berichtsformat (json, html, markdown, pdf)

        Returns:
            Bericht im gewÃ¼nschten Format
        """
        if format == "json":
            return json.dumps(result.to_dict(), indent=2, default=str)

        elif format == "dict":
            return result.to_dict()

        elif format == "html":
            return self._generate_html_report(result)

        elif format == "markdown":
            return self._generate_markdown_report(result)

        else:
            raise ValueError(f"Nicht unterstÃ¼tztes Format: {format}")

    def generate_remediation_plan(
        self, result: AnalysisResult, team_capacity: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generiert einen Remediation-Plan.

        Args:
            result: AnalysisResult
            team_capacity: Team-KapazitÃ¤t

        Returns:
            Remediation-Plan
        """
        vuln_data = [v.to_dict() for v in result.vulnerabilities]
        risk_data = [r.to_dict() for r in result.risk_scores]

        return self.recommendation_engine.generate_remediation_plan(
            vuln_data, risk_data, team_capacity
        )

    def get_compliance_report(
        self, result: AnalysisResult, framework: ComplianceFramework
    ) -> Dict[str, Any]:
        """
        Generiert Compliance-Bericht.

        Args:
            result: AnalysisResult
            framework: Compliance-Framework

        Returns:
            Compliance-Bericht
        """
        findings = []

        for vuln in result.vulnerabilities:
            controls = self.recommendation_engine.get_compliance_mapping(
                vuln.category.value, framework
            )

            if controls:
                findings.append(
                    {
                        "vulnerability_id": vuln.id,
                        "vulnerability_name": vuln.name,
                        "category": vuln.category.value,
                        "severity": vuln.severity,
                        "affected_controls": controls,
                    }
                )

        return {
            "framework": framework.value,
            "generated_at": datetime.utcnow().isoformat(),
            "total_findings": len(findings),
            "findings": findings,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Gibt Bot-Statistiken zurÃ¼ck"""
        return {
            "total_analyses": len(self.analysis_history),
            "metrics": dict(self.metrics),
            "last_analysis": (
                self.analysis_history[-1].to_dict()
                if self.analysis_history
                else None
            ),
        }

    def export_results(self, result: AnalysisResult, filepath: str) -> None:
        """Exportiert Ergebnisse als JSON-Datei"""
        with open(filepath, "w") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        logger.info(f"Ergebnisse exportiert nach {filepath}")

    def _analyze_vulnerabilities(
        self, vulnerabilities: List[Dict[str, Any]]
    ) -> List[Vulnerability]:
        """Analysiert Schwachstellen"""
        analyzed = []
        for vuln_data in vulnerabilities:
            vuln = Vulnerability(
                id=vuln_data.get("id", ""),
                cve_id=vuln_data.get("cve_id"),
                cwe_id=vuln_data.get("cwe_id"),
                name=vuln_data.get("name", ""),
                description=vuln_data.get("description", ""),
                category=VulnerabilityCategory(
                    vuln_data.get("category", "unknown")
                ),
                target=vuln_data.get("target", ""),
                location=vuln_data.get("location", ""),
                severity=vuln_data.get("severity", "info"),
                cvss_score=vuln_data.get("cvss_score", 0.0),
                cvss_vector=CVSSVector.from_vector_string(
                    vuln_data.get("cvss_vector", "")
                ),
                source=VulnerabilitySource(
                    vuln_data.get("source", "automated_scanner")
                ),
                evidence=vuln_data.get("evidence", {}),
                references=vuln_data.get("references", []),
            )
            analyzed.append(vuln)
        return analyzed

    def _calculate_risk_scores(
        self, vulnerabilities: List[Vulnerability], config: AnalysisConfig
    ) -> List[RiskScore]:
        """Berechnet Risiko-Scores"""
        scores = []
        for vuln in vulnerabilities:
            score = self.risk_scorer.calculate_comprehensive_risk(
                cvss_vector=(
                    vuln.cvss_vector.to_vector_string()
                    if vuln.cvss_vector
                    else None
                ),
                cvss_score=vuln.cvss_score,
                factors=config.risk_factors,
                asset_criticality=config.asset_criticality,
                threat_actor=config.threat_actor,
                custom_weights=config.scoring_weights,
            )
            scores.append(score)
        return scores

    def _assess_exploitability(
        self, vulnerabilities: List[Vulnerability]
    ) -> List[ExploitabilityAssessment]:
        """Bewertet Exploitierbarkeit"""
        assessments = []
        for vuln in vulnerabilities:
            vuln_dict = vuln.to_dict()
            assessment = self.exploitability_checker.assess_vulnerability(
                vuln_dict
            )
            assessments.append(assessment)
        return assessments

    def _generate_recommendations(
        self,
        vulnerabilities: List[Vulnerability],
        risk_scores: List[RiskScore],
        exploitability: List[ExploitabilityAssessment],
    ) -> List[Recommendation]:
        """Generiert Empfehlungen"""
        recommendations = []
        for vuln, risk, exploit in zip(
            vulnerabilities, risk_scores, exploitability
        ):
            rec = self.recommendation_engine.generate_recommendation(
                vuln.to_dict(), risk.to_dict(), exploit.to_dict()
            )
            recommendations.append(rec)
        return recommendations

    def _generate_summary(self, result: AnalysisResult) -> Dict[str, Any]:
        """Generiert Zusammenfassung"""
        severity_counts = defaultdict(int)
        for vuln in result.vulnerabilities:
            severity_counts[vuln.severity] += 1

        risk_level_counts = defaultdict(int)
        for score in result.risk_scores:
            risk_level_counts[score.risk_level.value] += 1

        exploitability_levels = defaultdict(int)
        for assessment in result.exploitability_assessments:
            exploitability_levels[assessment.level.value] += 1

        return {
            "total_vulnerabilities": len(result.vulnerabilities),
            "by_severity": dict(severity_counts),
            "by_risk_level": dict(risk_level_counts),
            "by_exploitability": dict(exploitability_levels),
            "critical_count": severity_counts.get("critical", 0),
            "high_count": severity_counts.get("high", 0),
            "requires_immediate_action": severity_counts.get("critical", 0)
            > 0,
        }

    def _generate_statistics(self, result: AnalysisResult) -> Dict[str, Any]:
        """Generiert Statistiken"""
        if not result.risk_scores:
            return {}

        scores = [r.final_score for r in result.risk_scores]
        avg_score = sum(scores) / len(scores) if scores else 0
        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0

        return {
            "average_risk_score": round(avg_score, 2),
            "max_risk_score": round(max_score, 2),
            "min_risk_score": round(min_score, 2),
            "total_recommendations": len(result.recommendations),
            "immediate_actions": len(
                [
                    r
                    for r in result.recommendations
                    if r.recommended_option
                    and r.recommended_option.priority
                    == RemediationPriority.IMMEDIATE
                ]
            ),
        }

    def _generate_html_report(self, result: AnalysisResult) -> str:
        """Generiert HTML-Bericht"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Zen-Ai-Pentest Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1, h2 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .critical {{ color: #d32f2f; }}
        .high {{ color: #f57c00; }}
        .medium {{ color: #fbc02d; }}
        .low {{ color: #388e3c; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Zen-Ai-Pentest Analysis Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Analysis ID:</strong> {result.analysis_id}</p>
        <p><strong>Target:</strong> {result.target}</p>
        <p><strong>Status:</strong> {result.status.value}</p>
        <p><strong>Duration:</strong> {result.duration_seconds:.2f} seconds</p>
        <p><strong>Total Vulnerabilities:</strong> {result.summary.get('total_vulnerabilities', 0)}</p>
    </div>

    <h2>Vulnerabilities by Severity</h2>
    <table>
        <tr><th>Severity</th><th>Count</th></tr>
"""
        for severity, count in result.summary.get("by_severity", {}).items():
            css_class = severity
            html += f"<tr><td class='{css_class}'>{severity.upper()}</td><td>{count}</td></tr>\n"

        html += """
    </table>

    <h2>Detailed Findings</h2>
    <table>
        <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Category</th>
            <th>Severity</th>
            <th>Risk Score</th>
        </tr>
"""
        for vuln, risk in zip(result.vulnerabilities, result.risk_scores):
            html += f"""
        <tr>
            <td>{vuln.id}</td>
            <td>{vuln.name}</td>
            <td>{vuln.category.value}</td>
            <td class='{vuln.severity}'>{vuln.severity.upper()}</td>
            <td>{risk.final_score}</td>
        </tr>
"""

        html += """
    </table>
</body>
</html>
"""
        return html

    def _generate_markdown_report(self, result: AnalysisResult) -> str:
        """Generiert Markdown-Bericht"""
        md = f"""# Zen-Ai-Pentest Analysis Report

## Summary

| Field | Value |
|-------|-------|
| Analysis ID | {result.analysis_id} |
| Target | {result.target} |
| Status | {result.status.value} |
| Duration | {result.duration_seconds:.2f} seconds |
| Total Vulnerabilities | {result.summary.get('total_vulnerabilities', 0)} |

## Vulnerabilities by Severity

| Severity | Count |
|----------|-------|
"""
        for severity, count in result.summary.get("by_severity", {}).items():
            md += f"| {severity.upper()} | {count} |\n"

        md += """
## Detailed Findings

| ID | Name | Category | Severity | Risk Score |
|----|------|----------|----------|------------|
"""
        for vuln, risk in zip(result.vulnerabilities, result.risk_scores):
            md += f"| {vuln.id} | {vuln.name} | {vuln.category.value} | {vuln.severity.upper()} | {risk.final_score} |\n"

        return md


# Singleton-Instanz
_bot = None


def get_analysis_bot() -> AnalysisBot:
    """Gibt die Singleton-Instanz des AnalysisBots zurÃ¼ck"""
    global _bot
    if _bot is None:
        _bot = AnalysisBot()
    return _bot


# Convenience-Funktionen
def analyze_vulnerabilities(
    vulnerabilities: List[Dict[str, Any]],
    config: Optional[AnalysisConfig] = None,
) -> AnalysisResult:
    """Kurzform fÃ¼r Analyse"""
    bot = get_analysis_bot()
    return bot.analyze(vulnerabilities, config)


def quick_analyze(vulnerability: Dict[str, Any]) -> Dict[str, Any]:
    """Schnellanalyse einer einzelnen Schwachstelle"""
    bot = get_analysis_bot()

    result = bot.analyze([vulnerability])

    return {
        "vulnerability": (
            result.vulnerabilities[0].to_dict()
            if result.vulnerabilities
            else None
        ),
        "risk_score": (
            result.risk_scores[0].to_dict() if result.risk_scores else None
        ),
        "exploitability": (
            result.exploitability_assessments[0].to_dict()
            if result.exploitability_assessments
            else None
        ),
        "recommendation": (
            result.recommendations[0].to_dict()
            if result.recommendations
            else None
        ),
    }


if __name__ == "__main__":
    # Demo/Test
    print("=" * 60)
    print("Zen-Ai-Pentest AnalysisBot v1.0.0")
    print("=" * 60)

    # Beispiel-Schwachstellen
    test_vulnerabilities = [
        {
            "id": "VULN-001",
            "name": "SQL Injection in Login Form",
            "category": "sql_injection",
            "description": "User input is directly concatenated into SQL query",
            "target": "https://example.com/login",
            "severity": "critical",
            "cvss_score": 9.8,
            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            "cve_id": "CVE-2021-1234",
            "evidence": {"parameter": "username", "payload": "' OR '1'='1"},
        },
        {
            "id": "VULN-002",
            "name": "Cross-Site Scripting in Search",
            "category": "xss",
            "description": "Search parameter reflects user input without encoding",
            "target": "https://example.com/search",
            "severity": "high",
            "cvss_score": 7.5,
            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
        },
        {
            "id": "VULN-003",
            "name": "Missing Security Headers",
            "category": "configuration",
            "description": "Several security headers are missing",
            "target": "https://example.com",
            "severity": "medium",
            "cvss_score": 5.0,
        },
    ]

    # Konfiguration
    config = AnalysisConfig(
        enable_vulnerability_analysis=True,
        enable_risk_scoring=True,
        enable_exploitability_check=True,
        enable_recommendations=True,
        asset_criticality=AssetCriticality.HIGH,
        threat_actor=ThreatActor.CYBERCRIMINAL,
        compliance_frameworks=[
            ComplianceFramework.OWASP_ASVS,
            ComplianceFramework.PCI_DSS,
        ],
    )

    # Analyse durchfÃ¼hren
    bot = AnalysisBot()
    result = bot.analyze(test_vulnerabilities, config)

    # Ergebnisse anzeigen
    print("\n" + "=" * 60)
    print("ANALYSIS RESULTS")
    print("=" * 60)

    print(f"\nAnalysis ID: {result.analysis_id}")
    print(f"Status: {result.status.value}")
    print(f"Duration: {result.duration_seconds:.2f} seconds")

    print("\n--- Summary ---")
    print(json.dumps(result.summary, indent=2))

    print("\n--- Statistics ---")
    print(json.dumps(result.statistics, indent=2))

    print("\n--- Vulnerabilities ---")
    for vuln in result.vulnerabilities:
        print(f"\n  {vuln.id}: {vuln.name}")
        print(f"    Category: {vuln.category.value}")
        print(f"    Severity: {vuln.severity}")

    print("\n--- Risk Scores ---")
    for risk in result.risk_scores:
        print(f"  Final Score: {risk.final_score} ({risk.risk_level.value})")

    print("\n--- Recommendations ---")
    for rec in result.recommendations:
        if rec.recommended_option:
            print(f"  {rec.vulnerability_id}: {rec.recommended_option.title}")
            print(f"    Priority: {rec.recommended_option.priority.value}")
            print(f"    Effort: {rec.recommended_option.effort.value}")

    # Report generieren
    print("\n" + "=" * 60)
    print("GENERATING REPORTS")
    print("=" * 60)

    json_report = bot.generate_report(result, format="json")
    print(f"\nJSON Report length: {len(json_report)} characters")

    md_report = bot.generate_report(result, format="markdown")
    print(f"Markdown Report length: {len(md_report)} characters")

    # Remediation Plan
    plan = bot.generate_remediation_plan(result, {"hours_per_week": 40})
    print(f"\nRemediation Plan: {plan['estimated_weeks']} weeks estimated")

    # Compliance Report
    compliance = bot.get_compliance_report(
        result, ComplianceFramework.OWASP_ASVS
    )
    print(f"Compliance Findings: {compliance['total_findings']}")

    print("\n" + "=" * 60)
    print("AnalysisBot Demo Complete")
    print("=" * 60)
