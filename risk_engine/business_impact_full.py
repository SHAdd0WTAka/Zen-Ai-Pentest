"""
Business Impact Scoring - Erweiterte Implementierung

Berechnet den geschäftlichen Impact von Sicherheitsfindings basierend auf:
- Data Sensitivity (PII, Financial, PHI)
- System Criticality (Production Core, etc.)
- Network Exposure (Internet, Internal, DMZ)
- Compliance Requirements (PCI-DSS, GDPR, HIPAA, etc.)
- Financial Impact (potenzieller Schaden in €)

Die Gewichtung folgt dem Standard-Risk-Modell:
- Data Sensitivity: 30%
- System Criticality: 25%
- Network Exposure: 20%
- Compliance: 15%
- Financial Impact: 10%
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class DataSensitivity(Enum):
    """Datensensitivitätsstufen"""

    PUBLIC = ("PUBLIC", 0.1, "Öffentliche Daten")
    INTERNAL = ("INTERNAL", 0.3, "Interne Geschäftsdaten")
    CONFIDENTIAL = ("CONFIDENTIAL", 0.6, "Vertrauliche Daten")
    PII = ("PII", 0.9, "Personenbezogene Daten")
    FINANCIAL = ("FINANCIAL", 0.95, "Finanzdaten")
    PHI = ("PHI", 1.0, "Gesundheitsdaten (Protected Health Information)")

    def __init__(self, label: str, weight: float, description: str):
        self.label = label
        self.weight = weight
        self.description = description


class SystemCriticality(Enum):
    """Systemkritikalitätsstufen"""

    MINIMAL = ("MINIMAL", 0.1, "Test/Entwicklung - Kein geschäftlicher Impact")
    LOW = ("LOW", 0.25, "Niedrig - Geringer geschäftlicher Impact")
    MEDIUM = ("MEDIUM", 0.5, "Mittel - Moderater geschäftlicher Impact")
    HIGH = ("HIGH", 0.75, "Hoch - Signifikanter geschäftlicher Impact")
    CRITICAL = ("CRITICAL", 1.0, "Kritisch - Geschäftskritisches System")

    def __init__(self, label: str, weight: float, description: str):
        self.label = label
        self.weight = weight
        self.description = description


class NetworkExposure(Enum):
    """Netzwerkexpositionsstufen"""

    AIR_GAPPED = ("AIR_GAPPED", 0.05, "Air-gapped - Kein Netzwerkzugriff")
    INTERNAL = ("INTERNAL", 0.3, "Internal - Internes Netzwerk")
    DMZ = ("DMZ", 0.6, "DMZ - Demilitarisierte Zone")
    INTRANET = ("INTRANET", 0.5, "Intranet - Intern erreichbar")
    VPN = ("VPN", 0.7, "VPN - VPN-Zugang erforderlich")
    INTERNET = ("INTERNET", 1.0, "Internet - Öffentlich erreichbar")

    def __init__(self, label: str, weight: float, description: str):
        self.label = label
        self.weight = weight
        self.description = description


class ComplianceFramework(Enum):
    """Compliance Frameworks mit ihren Strafgewichtungen"""

    PCI_DSS = ("PCI-DSS", 1.0, "Payment Card Industry Data Security Standard")
    GDPR = ("GDPR", 0.95, "EU Datenschutz-Grundverordnung")
    HIPAA = ("HIPAA", 0.95, "US Gesundheitsdatenschutz")
    SOX = ("SOX", 0.9, "Sarbanes-Oxley Act")
    CCPA = ("CCPA", 0.85, "California Consumer Privacy Act")
    ISO27001 = ("ISO27001", 0.75, "ISO/IEC 27001")
    SOC2 = ("SOC2", 0.75, "Service Organization Control 2")
    NIST = ("NIST", 0.7, "NIST Cybersecurity Framework")

    def __init__(self, name: str, weight: float, description: str):
        self.framework_name = name
        self.weight = weight
        self.description = description


@dataclass
class FinancialImpactEstimate:
    """Geschätzter finanzieller Impact"""

    potential_loss: float = 0.0  # Potenzieller Schaden in €
    response_cost: float = 0.0  # Incident Response Kosten
    regulatory_fines: float = 0.0  # Regulatorische Strafen
    reputation_cost: float = 0.0  # Reputationskosten

    @property
    def total(self) -> float:
        return self.potential_loss + self.response_cost + self.regulatory_fines + self.reputation_cost

    def get_normalized_score(self, organization_revenue: float = 100_000_000) -> float:
        """Normalisiert den finanziellen Impact auf 0-1 Skala"""
        if organization_revenue <= 0:
            return 0.5
        # Annahme: 10% des Umsatzes als maximaler Impact
        return min(1.0, self.total / (organization_revenue * 0.1))


@dataclass
class BusinessImpactFactors:
    """Container für alle Business Impact Faktoren"""

    data_sensitivity: DataSensitivity = DataSensitivity.INTERNAL
    system_criticality: SystemCriticality = SystemCriticality.MEDIUM
    network_exposure: NetworkExposure = NetworkExposure.INTERNAL
    compliance_frameworks: Set[ComplianceFramework] = field(default_factory=set)
    financial_impact: FinancialImpactEstimate = field(default_factory=FinancialImpactEstimate)

    # Optionale Metadaten
    asset_name: str = ""
    asset_owner: str = ""
    business_unit: str = ""
    data_volume_records: int = 0
    user_count: int = 0


@dataclass
class BusinessImpactScore:
    """Ergebnis der Business Impact Berechnung"""

    overall_score: float  # 0-1
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, MINIMAL

    # Einzelscores
    data_sensitivity_score: float
    system_criticality_score: float
    network_exposure_score: float
    compliance_score: float
    financial_impact_score: float

    # Details
    sla_target: str
    recommendations: List[str]
    risk_factors: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 3),
            "severity": self.severity,
            "sla_target": self.sla_target,
            "component_scores": {
                "data_sensitivity": round(self.data_sensitivity_score, 3),
                "system_criticality": round(self.system_criticality_score, 3),
                "network_exposure": round(self.network_exposure_score, 3),
                "compliance": round(self.compliance_score, 3),
                "financial_impact": round(self.financial_impact_score, 3),
            },
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat(),
        }


class BusinessImpactScorer:
    """
    Erweiterter Business Impact Scorer.

    Berechnet den geschäftlichen Impact basierend auf mehreren Faktoren
    und liefert priorisierte Empfehlungen.

    Gewichtung:
    - Data Sensitivity: 30%
    - System Criticality: 25%
    - Network Exposure: 20%
    - Compliance: 15%
    - Financial Impact: 10%

    Usage:
        scorer = BusinessImpactScorer()

        factors = {
            "data_sensitivity": "PII",
            "system_criticality": "CRITICAL",
            "exposure": "INTERNET",
            "compliance": ["PCI-DSS", "GDPR"],
            "financial_impact": 1000000
        }

        result = scorer.calculate(factors)
        print(f"Score: {result.overall_score}")
    """

    # Standardgewichtung
    WEIGHTS = {
        "data_sensitivity": 0.30,
        "system_criticality": 0.25,
        "network_exposure": 0.20,
        "compliance": 0.15,
        "financial_impact": 0.10,
    }

    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        """
        Initialisiert den Scorer.

        Args:
            custom_weights: Optionale angepasste Gewichtung
        """
        if custom_weights:
            self.WEIGHTS = custom_weights
        self.logger = logging.getLogger(__name__)

    def calculate(self, factors: Dict[str, Any]) -> BusinessImpactScore:
        """
        Berechnet den Business Impact Score.

        Args:
            factors: Dictionary mit:
                - data_sensitivity: str (PUBLIC, INTERNAL, CONFIDENTIAL, PII, FINANCIAL, PHI)
                - system_criticality: str (MINIMAL, LOW, MEDIUM, HIGH, CRITICAL)
                - exposure: str (AIR_GAPPED, INTERNAL, DMZ, INTRANET, VPN, INTERNET)
                - compliance: List[str] (PCI-DSS, GDPR, HIPAA, etc.)
                - financial_impact: float (Schaden in €)
                - organization_revenue: float (für Normalisierung)
                - data_volume_records: int (Anzahl betroffener Datensätze)

        Returns:
            BusinessImpactScore mit allen Details
        """
        # Data Sensitivity Score
        data_score = self._score_data_sensitivity(factors.get("data_sensitivity", "INTERNAL"))

        # System Criticality Score
        criticality_score = self._score_system_criticality(factors.get("system_criticality", "MEDIUM"))

        # Network Exposure Score
        exposure_score = self._score_network_exposure(factors.get("exposure", "INTERNAL"))

        # Compliance Score
        compliance_score = self._score_compliance(factors.get("compliance", []))

        # Financial Impact Score
        financial_score = self._score_financial_impact(
            factors.get("financial_impact", 0), factors.get("organization_revenue", 100_000_000)
        )

        # Gewichtete Summe
        overall_score = (
            data_score * self.WEIGHTS["data_sensitivity"]
            + criticality_score * self.WEIGHTS["system_criticality"]
            + exposure_score * self.WEIGHTS["network_exposure"]
            + compliance_score * self.WEIGHTS["compliance"]
            + financial_score * self.WEIGHTS["financial_impact"]
        )

        # Severity bestimmen
        severity = self._get_severity(overall_score)

        # SLA bestimmen
        sla = self._get_sla(overall_score)

        # Empfehlungen generieren
        recommendations = self._generate_recommendations(
            overall_score, data_score, criticality_score, exposure_score, compliance_score
        )

        return BusinessImpactScore(
            overall_score=round(overall_score, 3),
            severity=severity,
            data_sensitivity_score=round(data_score, 3),
            system_criticality_score=round(criticality_score, 3),
            network_exposure_score=round(exposure_score, 3),
            compliance_score=round(compliance_score, 3),
            financial_impact_score=round(financial_score, 3),
            sla_target=sla,
            recommendations=recommendations,
            risk_factors=factors,
        )

    def _score_data_sensitivity(self, sensitivity: str) -> float:
        """Bewertet die Datensensitivität."""
        sensitivity_map = {
            "public": DataSensitivity.PUBLIC,
            "internal": DataSensitivity.INTERNAL,
            "confidential": DataSensitivity.CONFIDENTIAL,
            "pii": DataSensitivity.PII,
            "financial": DataSensitivity.FINANCIAL,
            "phi": DataSensitivity.PHI,
            # Aliases
            "high": DataSensitivity.PII,
            "critical": DataSensitivity.PHI,
            "restricted": DataSensitivity.CONFIDENTIAL,
        }

        sens = sensitivity_map.get(sensitivity.lower(), DataSensitivity.INTERNAL)
        return sens.weight

    def _score_system_criticality(self, criticality: str) -> float:
        """Bewertet die Systemkritikalität."""
        criticality_map = {
            "minimal": SystemCriticality.MINIMAL,
            "low": SystemCriticality.LOW,
            "medium": SystemCriticality.MEDIUM,
            "high": SystemCriticality.HIGH,
            "critical": SystemCriticality.CRITICAL,
            # Aliases
            "production": SystemCriticality.CRITICAL,
            "core": SystemCriticality.CRITICAL,
            "standard": SystemCriticality.MEDIUM,
            "dev": SystemCriticality.MINIMAL,
            "test": SystemCriticality.MINIMAL,
        }

        crit = criticality_map.get(criticality.lower(), SystemCriticality.MEDIUM)
        return crit.weight

    def _score_network_exposure(self, exposure: str) -> float:
        """Bewertet die Netzwerkexposition."""
        exposure_map = {
            "air_gapped": NetworkExposure.AIR_GAPPED,
            "airgapped": NetworkExposure.AIR_GAPPED,
            "internal": NetworkExposure.INTERNAL,
            "intranet": NetworkExposure.INTRANET,
            "dmz": NetworkExposure.DMZ,
            "vpn": NetworkExposure.VPN,
            "internet": NetworkExposure.INTERNET,
            "public": NetworkExposure.INTERNET,
            # Aliases
            "private": NetworkExposure.INTERNAL,
            "isolated": NetworkExposure.AIR_GAPPED,
        }

        exp = exposure_map.get(exposure.lower(), NetworkExposure.INTERNAL)
        return exp.weight

    def _score_compliance(self, compliance: List[str]) -> float:
        """Bewertet die Compliance-Anforderungen."""
        if not compliance:
            return 0.3  # Standard wenn keine Compliance

        framework_map = {
            "pci-dss": ComplianceFramework.PCI_DSS,
            "pci_dss": ComplianceFramework.PCI_DSS,
            "pci": ComplianceFramework.PCI_DSS,
            "gdpr": ComplianceFramework.GDPR,
            "hipaa": ComplianceFramework.HIPAA,
            "sox": ComplianceFramework.SOX,
            "ccpa": ComplianceFramework.CCPA,
            "iso27001": ComplianceFramework.ISO27001,
            "iso": ComplianceFramework.ISO27001,
            "soc2": ComplianceFramework.SOC2,
            "nist": ComplianceFramework.NIST,
        }

        total_weight = 0
        for framework in compliance:
            fw = framework_map.get(framework.lower().replace("-", "_").replace(" ", "_"))
            if fw:
                total_weight += fw.weight

        if len(compliance) > 0:
            avg_weight = total_weight / len(compliance)
            # Boost wenn mehrere Frameworks betroffen
            if len(compliance) > 2:
                avg_weight = min(1.0, avg_weight * 1.1)
            return avg_weight

        return 0.3

    def _score_financial_impact(self, financial_impact: float, organization_revenue: float) -> float:
        """Bewertet den finanziellen Impact."""
        if organization_revenue <= 0:
            # Absolute Bewertung wenn kein Umsatz bekannt
            if financial_impact >= 10_000_000:
                return 1.0
            elif financial_impact >= 1_000_000:
                return 0.8
            elif financial_impact >= 100_000:
                return 0.6
            elif financial_impact >= 10_000:
                return 0.4
            elif financial_impact > 0:
                return 0.2
            return 0.0

        # Relative Bewertung zum Umsatz
        ratio = financial_impact / organization_revenue

        if ratio >= 0.1:  # > 10% des Umsatzes
            return 1.0
        elif ratio >= 0.05:  # > 5% des Umsatzes
            return 0.8
        elif ratio >= 0.01:  # > 1% des Umsatzes
            return 0.6
        elif ratio >= 0.005:  # > 0.5% des Umsatzes
            return 0.4
        elif ratio > 0:
            return 0.2
        return 0.0

    def _get_severity(self, score: float) -> str:
        """Bestimmt die Severity basierend auf dem Score."""
        if score >= 0.8:
            return "CRITICAL"
        elif score >= 0.6:
            return "HIGH"
        elif score >= 0.4:
            return "MEDIUM"
        elif score >= 0.2:
            return "LOW"
        return "MINIMAL"

    def _get_sla(self, score: float) -> str:
        """Bestimmt das SLA basierend auf dem Score."""
        if score >= 0.8:
            return "24h"
        elif score >= 0.6:
            return "72h"
        elif score >= 0.4:
            return "14d"
        elif score >= 0.2:
            return "30d"
        return "90d"

    def _generate_recommendations(
        self, overall_score: float, data_score: float, criticality_score: float, exposure_score: float, compliance_score: float
    ) -> List[str]:
        """Generiert Empfehlungen basierend auf den Scores."""
        recommendations = []

        # Overall Score Empfehlungen
        if overall_score >= 0.9:
            recommendations.append("SOFORTIGE AKTION: Kritischer Business Impact")
            recommendations.append("Management-Eskalation erforderlich")
        elif overall_score >= 0.7:
            recommendations.append("Schnelle Behebung erforderlich")

        # Data Sensitivity Empfehlungen
        if data_score >= 0.9:
            recommendations.append("Datenschutzbeauftragten informieren")
            recommendations.append("Betroffene Personen müssen möglicherweise benachrichtigt werden")
        elif data_score >= 0.6:
            recommendations.append("Datenverschlüsselung überprüfen")

        # Criticality Empfehlungen
        if criticality_score >= 0.8:
            recommendations.append("Business Continuity Plan aktivieren")
            recommendations.append("Failover-Systeme prüfen")

        # Exposure Empfehlungen
        if exposure_score >= 0.8:
            recommendations.append("Sofortige Netzwerksegmentierung empfohlen")
            recommendations.append("WAF/IPS Regeln überprüfen")
        elif exposure_score >= 0.5:
            recommendations.append("Zugriffsbeschränkungen prüfen")

        # Compliance Empfehlungen
        if compliance_score >= 0.9:
            recommendations.append("Compliance-Team benachrichtigen")
            recommendations.append("Regulatorische Meldungspflicht prüfen")
        elif compliance_score >= 0.7:
            recommendations.append("Audit-Trail sicherstellen")

        return recommendations

    def calculate_with_enums(
        self,
        data_sensitivity: DataSensitivity,
        system_criticality: SystemCriticality,
        network_exposure: NetworkExposure,
        compliance: Set[ComplianceFramework],
        financial_impact: Optional[FinancialImpactEstimate] = None,
    ) -> BusinessImpactScore:
        """
        Berechnet den Score mit Enum-Werten statt Strings.

        Type-sichere Alternative zu calculate().
        """
        factors = {
            "data_sensitivity": data_sensitivity.label,
            "system_criticality": system_criticality.label,
            "exposure": network_exposure.label,
            "compliance": [c.framework_name for c in compliance],
            "financial_impact": financial_impact.total if financial_impact else 0,
        }

        return self.calculate(factors)


def quick_business_score(
    data_sensitivity: str = "INTERNAL",
    system_criticality: str = "MEDIUM",
    exposure: str = "INTERNAL",
    compliance: Optional[List[str]] = None,
    financial_impact: float = 0,
) -> float:
    """
    Schnelle Berechnung des Business Impact Scores als float.

    Returns:
        Business Impact Score (0.0 - 1.0)
    """
    scorer = BusinessImpactScorer()
    factors = {
        "data_sensitivity": data_sensitivity,
        "system_criticality": system_criticality,
        "exposure": exposure,
        "compliance": compliance or [],
        "financial_impact": financial_impact,
    }
    result = scorer.calculate(factors)
    return result.overall_score
