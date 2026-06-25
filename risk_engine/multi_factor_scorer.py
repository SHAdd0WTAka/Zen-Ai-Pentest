"""
Multi-Faktor Risk Scorer

Kombiniert:
- CVSS Base Score (30%): Technische Schwere
- EPSS Score (20%): Ausnutzungswahrscheinlichkeit
- Business Impact (35%): Geschäftlicher Impact
- Validation Confidence (15%): Bestätigte Ausnutzbarkeit

Formel:
Risk = (
    (CVSS_Base × 0.30) +
    (EPSS × 0.20) +
    (Business_Impact × 0.35) +
    (Validation_Confidence × 0.15)
) × 10

Severity Levels:
- 9.0-10.0: Critical (24h SLA)
- 7.0-8.9: High (72h SLA)
- 4.0-6.9: Medium (14d SLA)
- 1.0-3.9: Low (30d SLA)
- 0.0-0.9: Info (Best effort)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from risk_engine.business_impact_full import BusinessImpactScorer
from risk_engine.cvss_calculator_full import CVSS31Calculator
from risk_engine.epss_client_full import EPSSClientFull


class RiskSeverity(Enum):
    """Risiko-Schweregrade mit SLA-Anforderungen"""

    CRITICAL = (9.0, 10.0, "24h", "Kritisch - Sofortige Behebung")
    HIGH = (7.0, 8.9, "72h", "Hoch - Schnelle Behebung")
    MEDIUM = (4.0, 6.9, "14d", "Mittel - Standard-Behebung")
    LOW = (1.0, 3.9, "30d", "Niedrig - Optionale Behebung")
    INFO = (0.0, 0.9, "Best effort", "Info - Keine Behebung nötig")

    def __init__(self, min_score: float, max_score: float, sla: str, description: str):
        self.min_score = min_score
        self.max_score = max_score
        self.sla = sla
        self.description = description

    @classmethod
    def from_score(cls, score: float) -> "RiskSeverity":
        """Bestimmt den Severity Level basierend auf dem Score."""
        for level in cls:
            if level.min_score <= score <= level.max_score:
                return level
        return cls.INFO


@dataclass
class RiskComponent:
    """Einzelne Risikokomponente"""

    name: str
    score: float  # 0-1
    weight: float
    weighted_score: float  # score * weight
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiFactorRiskScore:
    """Vollständiges Multi-Faktor Risiko-Ergebnis"""

    # Hauptscore
    final_risk_score: float  # 0-10
    severity: RiskSeverity

    # Komponenten
    cvss_component: RiskComponent
    epss_component: RiskComponent
    business_component: RiskComponent
    validation_component: RiskComponent

    # Kontext
    cve_id: Optional[str]
    finding_title: str
    target: str

    # Empfehlungen
    sla_target: str
    recommendations: List[str]
    prioritized_actions: List[str]

    # Metadaten
    timestamp: datetime = field(default_factory=datetime.now)
    calculation_method: str = "cvss_epss_business_validation"

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary für JSON-Serialisierung."""
        return {
            "final_risk_score": round(self.final_risk_score, 2),
            "severity": {
                "level": self.severity.name,
                "description": self.severity.description,
                "min": self.severity.min_score,
                "max": self.severity.max_score,
                "sla": self.severity.sla,
            },
            "sla_target": self.sla_target,
            "components": {
                "cvss": {
                    "name": self.cvss_component.name,
                    "raw_score": round(self.cvss_component.score, 3),
                    "weight": self.cvss_component.weight,
                    "weighted_contribution": round(self.cvss_component.weighted_score, 3),
                    "details": self.cvss_component.details,
                },
                "epss": {
                    "name": self.epss_component.name,
                    "raw_score": round(self.epss_component.score, 3),
                    "weight": self.epss_component.weight,
                    "weighted_contribution": round(self.epss_component.weighted_score, 3),
                    "details": self.epss_component.details,
                },
                "business_impact": {
                    "name": self.business_component.name,
                    "raw_score": round(self.business_component.score, 3),
                    "weight": self.business_component.weight,
                    "weighted_contribution": round(self.business_component.weighted_score, 3),
                    "details": self.business_component.details,
                },
                "validation": {
                    "name": self.validation_component.name,
                    "raw_score": round(self.validation_component.score, 3),
                    "weight": self.validation_component.weight,
                    "weighted_contribution": round(self.validation_component.weighted_score, 3),
                    "details": self.validation_component.details,
                },
            },
            "finding": {"cve_id": self.cve_id, "title": self.finding_title, "target": self.target},
            "recommendations": self.recommendations,
            "prioritized_actions": self.prioritized_actions,
            "timestamp": self.timestamp.isoformat(),
            "calculation_method": self.calculation_method,
        }

    def get_summary(self) -> str:
        """Gibt eine Zusammenfassung als String zurück."""
        lines = [
            f"Risk Score: {self.final_risk_score:.1f}/10 ({self.severity.name})",
            f"SLA Target: {self.sla_target}",
            "",
            "Components:",
            f"  CVSS: {self.cvss_component.score:.2f} × {self.cvss_component.weight} = {self.cvss_component.weighted_score:.3f}",
            f"  EPSS: {self.epss_component.score:.2f} × {self.epss_component.weight} = {self.epss_component.weighted_score:.3f}",
            f"  Business: {self.business_component.score:.2f} × {self.business_component.weight} = {self.business_component.weighted_score:.3f}",
            f"  Validation: {self.validation_component.score:.2f} × {self.validation_component.weight} = {self.validation_component.weighted_score:.3f}",
            "",
            "Top Actions:",
        ]
        for i, action in enumerate(self.prioritized_actions[:3], 1):
            lines.append(f"  {i}. {action}")

        return "\n".join(lines)


class MultiFactorRiskScorer:
    """
    Multi-Faktor Risk Scorer

    Kombiniert CVSS, EPSS, Business Impact und Validation Confidence
    zu einem einheitlichen Risikoscore.

    Standard-Gewichtung:
    - CVSS Base: 30%
    - EPSS: 20%
    - Business Impact: 35%
    - Validation Confidence: 15%

    Usage:
        scorer = MultiFactorRiskScorer()

        result = scorer.calculate(
            cve_id="CVE-2024-1234",
            finding_title="Critical SQL Injection",
            target="production-db.example.com",
            cvss_metrics={
                "attack_vector": "NETWORK",
                "attack_complexity": "LOW",
                "privileges_required": "NONE",
                "scope": "CHANGED",
                "confidentiality": "HIGH",
                "integrity": "HIGH",
                "availability": "HIGH"
            },
            business_factors={
                "data_sensitivity": "PII",
                "system_criticality": "CRITICAL",
                "exposure": "INTERNET",
                "compliance": ["GDPR"],
                "financial_impact": 1000000
            },
            validation_status="confirmed"
        )

        print(result.get_summary())
    """

    # Standard-Gewichtung
    DEFAULT_WEIGHTS = {"cvss": 0.30, "epss": 0.20, "business": 0.35, "validation": 0.15}

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        enable_epss: bool = True,
        enable_business: bool = True,
        organization_revenue: float = 100_000_000,
    ):
        """
        Initialisiert den Multi-Faktor Risk Scorer.

        Args:
            weights: Angepasste Gewichtung (optional)
            enable_epss: EPSS-Integration aktivieren
            enable_business: Business Impact Scoring aktivieren
            organization_revenue: Jahresumsatz für Finanz-Normalisierung
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.organization_revenue = organization_revenue

        # Initialisiere Komponenten
        self.cvss_calc = CVSS31Calculator()
        self.epss_client = EPSSClientFull() if enable_epss else None
        self.business_scorer = BusinessImpactScorer() if enable_business else None

        self.logger = logging.getLogger(__name__)

    def calculate(
        self,
        finding_title: str,
        target: str,
        cve_id: Optional[str] = None,
        cvss_score: Optional[float] = None,
        cvss_metrics: Optional[Dict[str, str]] = None,
        epss_score: Optional[float] = None,
        business_factors: Optional[Dict[str, Any]] = None,
        validation_status: str = "unknown",
        validation_confidence: Optional[float] = None,
    ) -> MultiFactorRiskScore:
        """
        Berechnet den Multi-Faktor Risk Score.

        Args:
            finding_title: Titel des Findings
            target: Zielsystem
            cve_id: CVE ID (optional)
            cvss_score: Direkter CVSS Score (optional, sonst berechnet)
            cvss_metrics: CVSS Metriken für Berechnung (optional)
            epss_score: Direkter EPSS Score (optional, sonst von API)
            business_factors: Business Impact Faktoren (optional)
            validation_status: confirmed, available, theoretical, unknown
            validation_confidence: Direkte Confidence (0-1, optional)

        Returns:
            MultiFactorRiskScore mit allen Details
        """
        # 1. CVSS Score (normalisiert auf 0-1)
        cvss_norm, cvss_details = self._calculate_cvss(cve_id, cvss_score, cvss_metrics)

        # 2. EPSS Score (0-1)
        epss_norm, epss_details = self._calculate_epss(cve_id, epss_score)

        # 3. Business Impact (0-1)
        business_norm, business_details = self._calculate_business(business_factors)

        # 4. Validation Confidence (0-1)
        validation_norm, validation_details = self._calculate_validation(validation_status, validation_confidence)

        # Multi-Faktor Formel anwenden
        # Risk = (CVSS×0.30 + EPSS×0.20 + Business×0.35 + Validation×0.15) × 10
        final_score = (
            cvss_norm * self.weights["cvss"]
            + epss_norm * self.weights["epss"]
            + business_norm * self.weights["business"]
            + validation_norm * self.weights["validation"]
        ) * 10

        # Severity bestimmen
        severity = RiskSeverity.from_score(final_score)

        # Komponenten erstellen
        cvss_component = RiskComponent(
            name="CVSS Base Score",
            score=cvss_norm,
            weight=self.weights["cvss"],
            weighted_score=cvss_norm * self.weights["cvss"],
            details=cvss_details,
        )

        epss_component = RiskComponent(
            name="EPSS Exploit Probability",
            score=epss_norm,
            weight=self.weights["epss"],
            weighted_score=epss_norm * self.weights["epss"],
            details=epss_details,
        )

        business_component = RiskComponent(
            name="Business Impact",
            score=business_norm,
            weight=self.weights["business"],
            weighted_score=business_norm * self.weights["business"],
            details=business_details,
        )

        validation_component = RiskComponent(
            name="Validation Confidence",
            score=validation_norm,
            weight=self.weights["validation"],
            weighted_score=validation_norm * self.weights["validation"],
            details=validation_details,
        )

        # Empfehlungen generieren
        recommendations, prioritized = self._generate_recommendations(
            final_score, severity, cvss_norm, epss_norm, business_norm, validation_norm
        )

        return MultiFactorRiskScore(
            final_risk_score=round(final_score, 2),
            severity=severity,
            cvss_component=cvss_component,
            epss_component=epss_component,
            business_component=business_component,
            validation_component=validation_component,
            cve_id=cve_id,
            finding_title=finding_title,
            target=target,
            sla_target=severity.sla,
            recommendations=recommendations,
            prioritized_actions=prioritized,
        )

    def _calculate_cvss(
        self, cve_id: Optional[str], cvss_score: Optional[float], cvss_metrics: Optional[Dict[str, str]]
    ) -> Tuple[float, Dict[str, Any]]:
        """Berechnet den normalisierten CVSS Score."""
        details = {}

        if cvss_score is not None:
            # Direkter CVSS Score übergeben
            score = cvss_score
            details["source"] = "provided"
            details["raw_score"] = cvss_score
        elif cvss_metrics:
            # Aus Metriken berechnen
            result = self.cvss_calc.calculate_simple(cvss_metrics)
            score = result
            details["source"] = "calculated"
            details["metrics"] = cvss_metrics
        elif cve_id:
            # Aus CVE ID Lookup (würde NVD API benötigen)
            # Fallback: Schätzung
            score = 7.0  # Default
            details["source"] = "default"
            details["note"] = "No CVSS data provided, using default"
        else:
            score = 5.0
            details["source"] = "default"
            details["note"] = "No CVSS information available"

        # Normalisieren auf 0-1
        normalized = min(1.0, score / 10.0)
        details["normalized_score"] = normalized

        return normalized, details

    def _calculate_epss(self, cve_id: Optional[str], epss_score: Optional[float]) -> Tuple[float, Dict[str, Any]]:
        """Berechnet den normalisierten EPSS Score."""
        details = {}

        if epss_score is not None:
            # Direkter EPSS Score übergeben
            score = epss_score
            details["source"] = "provided"
        elif cve_id and self.epss_client:
            # Von API holen
            try:
                epss_result = self.epss_client.get_score(cve_id)
                score = epss_result.score
                details["source"] = "api"
                details["percentile"] = epss_result.percentile
                details["cached"] = epss_result.cached
            except Exception as e:
                self.logger.warning(f"EPSS lookup failed: {e}")
                score = 0.5  # Default wenn API fehlschlägt
                details["source"] = "default"
                details["error"] = str(e)
        else:
            score = 0.5  # Neutraler Default
            details["source"] = "default"

        details["raw_score"] = score
        return score, details

    def _calculate_business(self, business_factors: Optional[Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
        """Berechnet den normalisierten Business Impact Score."""
        details = {}

        if business_factors and self.business_scorer:
            result = self.business_scorer.calculate(business_factors)
            score = result.overall_score
            details["source"] = "calculated"
            details["full_result"] = result.to_dict()
        else:
            # Default: Mittlerer Impact
            score = 0.5
            details["source"] = "default"

        details["raw_score"] = score
        return score, details

    def _calculate_validation(
        self, validation_status: str, validation_confidence: Optional[float]
    ) -> Tuple[float, Dict[str, Any]]:
        """Berechnet den Validation Confidence Score."""
        details = {}

        if validation_confidence is not None:
            score = validation_confidence
            details["source"] = "provided"
        else:
            # Basierend auf Status
            status_scores = {
                "confirmed": 1.0,  # Exploit bestätigt
                "validated": 1.0,  # Validierter Exploit
                "available": 0.7,  # Exploit-Code verfügbar
                "poc": 0.5,  # Proof of Concept
                "theoretical": 0.3,  # Theoretisch ausnutzbar
                "unknown": 0.1,  # Unbekannt
                "none": 0.0,  # Kein Exploit
            }
            score = status_scores.get(validation_status.lower(), 0.1)
            details["source"] = "status"
            details["status"] = validation_status

        details["raw_score"] = score
        return score, details

    def _generate_recommendations(
        self, final_score: float, severity: RiskSeverity, cvss: float, epss: float, business: float, validation: float
    ) -> Tuple[List[str], List[str]]:
        """Generiert Empfehlungen basierend auf allen Faktoren."""
        recommendations = []
        prioritized = []

        # Severity-basierte Empfehlungen
        if severity == RiskSeverity.CRITICAL:
            prioritized.append("SOFORTIGE ISOLIERUNG des betroffenen Systems")
            prioritized.append("Emergency Patch innerhalb 24h")
            prioritized.append("Incident Response Team aktivieren")
            recommendations.append("Netzwerksegmentierung überprüfen")
            recommendations.append("Logging und Monitoring verstärken")

        elif severity == RiskSeverity.HIGH:
            prioritized.append("Patch innerhalb 72h einspielen")
            prioritized.append("WAF/IPS Regeln implementieren")
            recommendations.append("Kompensierende Kontrollen aktivieren")

        elif severity == RiskSeverity.MEDIUM:
            prioritized.append("Im nächsten Wartungsfenster patchen")
            recommendations.append("Workaround dokumentieren")

        # CVSS-basierte Empfehlungen
        if cvss >= 0.9:
            recommendations.append("Kritische technische Schwere - sofortige Aktion")
        elif cvss >= 0.7:
            recommendations.append("Hohe technische Schwere - priorisieren")

        # EPSS-basierte Empfehlungen
        if epss >= 0.5:
            prioritized.insert(0, f"HOHE AUSNUTZUNGSwahrscheinlichkeit ({epss * 100:.1f}%) - sofort patchen!")
        elif epss >= 0.3:
            recommendations.append(f"EPSS: {epss * 100:.1f}% Wahrscheinlichkeit - überwachen")

        # Business Impact Empfehlungen
        if business >= 0.8:
            prioritized.append("KRITISCHER BUSINESS IMPACT - Management informieren")
            recommendations.append("Business Continuity Plan prüfen")
        elif business >= 0.6:
            recommendations.append("Signifikanter Business Impact")

        # Validation Empfehlungen
        if validation >= 0.8:
            recommendations.append("Exploit bestätigt - sofortige Gegenmaßnahmen")

        return recommendations, prioritized

    def prioritize_findings(self, findings: List[Dict[str, Any]]) -> List[Tuple[MultiFactorRiskScore, int]]:
        """
        Priorisiert mehrere Findings nach Risk Score.

        Returns:
            Liste von (MultiFactorRiskScore, Rank) Tupeln
        """
        scored = []

        for finding in findings:
            score = self.calculate(
                finding_title=finding.get("title", "Unknown"),
                target=finding.get("target", "Unknown"),
                cve_id=finding.get("cve_id"),
                cvss_score=finding.get("cvss_score"),
                cvss_metrics=finding.get("cvss_metrics"),
                epss_score=finding.get("epss_score"),
                business_factors=finding.get("business_factors"),
                validation_status=finding.get("validation_status", "unknown"),
                validation_confidence=finding.get("validation_confidence"),
            )
            scored.append(score)

        # Sortieren nach Score (absteigend)
        scored.sort(key=lambda x: x.final_risk_score, reverse=True)

        # Mit Rank zurückgeben
        return [(score, i + 1) for i, score in enumerate(scored)]


def calculate_risk(
    finding_title: str,
    target: str,
    cve_id: Optional[str] = None,
    cvss_score: Optional[float] = None,
    epss_score: Optional[float] = None,
    **kwargs,
) -> float:
    """
    Schnelle Risk Score Berechnung als float.

    Returns:
        Risk Score (0-10)
    """
    scorer = MultiFactorRiskScorer()
    result = scorer.calculate(
        finding_title=finding_title, target=target, cve_id=cve_id, cvss_score=cvss_score, epss_score=epss_score, **kwargs
    )
    return result.final_risk_score
