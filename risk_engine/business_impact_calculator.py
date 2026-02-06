"""
Business Impact Calculator für das Zen-AI-Pentest Framework.

Berechnet den geschäftlichen Impact von Sicherheitsfindings basierend auf
Asset-Wertung, Datenklassifizierung, Compliance-Anforderungen und finanziellen Faktoren.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Logger konfigurieren
logger = logging.getLogger(__name__)


class DataClassification(Enum):
    """Datenklassifizierungsstufen nach sensitivität."""

    PUBLIC = ("public", 0.1, "Öffentlich zugängliche Daten")
    INTERNAL = ("internal", 0.3, "Interne Geschäftsdaten")
    CONFIDENTIAL = ("confidential", 0.6, "Vertrauliche Daten")
    RESTRICTED = ("restricted", 0.9, "Streng vertrauliche Daten")

    def __init__(self, label: str, weight: float, description: str):
        self.label = label
        self.weight = weight
        self.description = description


class ComplianceFramework(Enum):
    """Compliance-Frameworks mit ihren jeweiligen Impact-Gewichtungen."""

    PCI_DSS = ("PCI-DSS", 0.95, {"payment_data": 1.0, "cardholder_data": 0.9})
    HIPAA = ("HIPAA", 0.9, {"phi": 1.0, "medical_records": 0.9, "patient_data": 0.85})
    GDPR = ("GDPR", 0.85, {"pii": 0.9, "personal_data": 0.85, "sensitive_data": 0.95})
    SOX = ("SOX", 0.8, {"financial_data": 0.9, "audit_logs": 0.7})
    ISO27001 = ("ISO27001", 0.75, {"isms_data": 0.8, "security_controls": 0.7})
    NIST = ("NIST", 0.7, {"federal_data": 0.9, "critical_infrastructure": 0.85})

    def __init__(self, name: str, base_weight: float, data_weights: Dict[str, float]):
        self.framework_name = name
        self.base_weight = base_weight
        self.data_weights = data_weights


class AssetCriticality(Enum):
    """Kritikalitätsstufen von Assets."""

    CRITICAL = (5, 1.0, "Geschäftskritische Systeme")
    HIGH = (4, 0.8, "Wichtige Geschäftssysteme")
    MEDIUM = (3, 0.5, "Standard-Geschäftssysteme")
    LOW = (2, 0.3, "Nicht-kritische Systeme")
    MINIMAL = (1, 0.1, "Test/Entwicklungssysteme")

    def __init__(self, level: int, weight: float, description: str):
        self.level = level
        self.weight = weight
        self.description = description


class ReputationImpact(Enum):
    """Mögliche Auswirkungen auf den Ruf des Unternehmens."""

    SEVERE = (1.0, "Ernsthafter Imageschaden, Medienberichterstattung")
    HIGH = (0.7, "Signifikanter Reputationsschaden")
    MODERATE = (0.4, "Mäßiger Rufschaden")
    LOW = (0.1, "Geringer bis kein Rufschaden")

    def __init__(self, weight: float, description: str):
        self.weight = weight
        self.description = description


@dataclass
class FinancialImpact:
    """Finanzielle Auswirkungen eines Sicherheitsvorfalls."""

    direct_costs: float = 0.0  # Direkte Kosten (Response, Forensik, etc.)
    indirect_costs: float = 0.0  # Indirekte Kosten (Ausfallzeiten, etc.)
    regulatory_fines: float = 0.0  # Regulatorische Strafen
    legal_costs: float = 0.0  # Rechtskosten
    reputation_costs: float = 0.0  # Kosten durch Reputationsschaden

    @property
    def total_costs(self) -> float:
        """Berechnet die gesamten finanziellen Auswirkungen."""
        return self.direct_costs + self.indirect_costs + self.regulatory_fines + self.legal_costs + self.reputation_costs


@dataclass
class ComplianceImpact:
    """Compliance-bezogene Auswirkungen."""

    frameworks: Set[ComplianceFramework] = field(default_factory=set)
    violated_controls: List[str] = field(default_factory=list)
    potential_fines: Dict[ComplianceFramework, float] = field(default_factory=dict)
    audit_findings: List[str] = field(default_factory=list)

    def get_max_fine(self) -> float:
        """Gibt die maximal mögliche Strafe zurück."""
        return max(self.potential_fines.values()) if self.potential_fines else 0.0

    def get_compliance_score(self) -> float:
        """Berechnet einen Compliance-Risiko-Score (0-1)."""
        if not self.frameworks:
            return 0.0

        base_score = sum(fw.base_weight for fw in self.frameworks) / len(self.frameworks)
        violation_multiplier = min(1.0, len(self.violated_controls) * 0.1)
        return min(1.0, base_score * (1 + violation_multiplier))


@dataclass
class AssetContext:
    """Kontextinformationen für ein Asset."""

    asset_id: str
    asset_name: str
    asset_type: str
    criticality: AssetCriticality
    data_classification: DataClassification
    compliance_frameworks: Set[ComplianceFramework] = field(default_factory=set)
    internet_exposed: bool = False
    user_count: int = 0
    revenue_dependency: float = 0.0  # Prozentualer Anteil am Umsatz

    def get_exposure_factor(self) -> float:
        """Berechnet den Expositionsfaktor basierend auf verschiedenen Parametern."""
        exposure = 0.0

        if self.internet_exposed:
            exposure += 0.4

        if self.user_count > 10000:
            exposure += 0.3
        elif self.user_count > 1000:
            exposure += 0.2
        elif self.user_count > 100:
            exposure += 0.1

        exposure += min(0.3, self.revenue_dependency / 100)

        return min(1.0, exposure)


@dataclass
class BusinessImpactResult:
    """Ergebnis der Business-Impact-Berechnung."""

    asset_id: str
    overall_score: float  # 0-1 Skala
    financial_impact: FinancialImpact
    compliance_impact: ComplianceImpact
    reputation_impact: ReputationImpact
    asset_criticality_score: float
    data_sensitivity_score: float
    exposure_score: float
    timestamp: datetime = field(default_factory=datetime.now)

    def get_risk_category(self) -> str:
        """Kategorisiert das Risiko basierend auf dem Gesamtscore."""
        if self.overall_score >= 0.9:
            return "CRITICAL"
        elif self.overall_score >= 0.7:
            return "HIGH"
        elif self.overall_score >= 0.4:
            return "MEDIUM"
        elif self.overall_score >= 0.2:
            return "LOW"
        return "MINIMAL"

    def get_prioritized_remediation(self) -> List[str]:
        """Generiert priorisierte Empfehlungen basierend auf dem Impact."""
        recommendations = []

        if self.financial_impact.total_costs > 1000000:
            recommendations.append("Sofortige Eskalation an das Management erforderlich")

        if self.compliance_impact.violated_controls:
            recommendations.append(f"Compliance-Verstöße beheben: {', '.join(self.compliance_impact.violated_controls[:3])}")

        if self.reputation_impact.weight >= 0.7:
            recommendations.append("PR-Team benachrichtigen für mögliche Krisenkommunikation")

        if self.exposure_score >= 0.7:
            recommendations.append("Netzwerksegmentierung und Zugangskontrollen überprüfen")

        return recommendations


class BusinessImpactCalculator:
    """
    Berechnet den geschäftlichen Impact von Sicherheitsfindings.

    Berücksichtigt finanzielle, compliance-bezogene und reputationsbezogene Faktoren.
    """

    def __init__(self, organization_size: str = "medium", annual_revenue: float = 0.0, industry: str = "technology"):
        """
        Initialisiert den Calculator.

        Args:
            organization_size: Größe der Organisation (small, medium, large, enterprise)
            annual_revenue: Jährlicher Umsatz in der lokalen Währung
            industry: Branche für branchenspezifische Anpassungen
        """
        self.organization_size = organization_size
        self.annual_revenue = annual_revenue
        self.industry = industry

        # Branchenspezifische Multiplikatoren
        self.industry_multipliers = {
            "healthcare": {"compliance": 1.2, "reputation": 1.3, "financial": 1.1},
            "finance": {"compliance": 1.3, "reputation": 1.2, "financial": 1.2},
            "retail": {"compliance": 1.1, "reputation": 1.1, "financial": 1.0},
            "technology": {"compliance": 1.0, "reputation": 1.2, "financial": 1.1},
            "government": {"compliance": 1.4, "reputation": 1.0, "financial": 0.9},
            "manufacturing": {"compliance": 0.9, "reputation": 0.9, "financial": 1.0},
        }

        # Organisationsspezifische Basiskosten
        self.base_response_costs = {
            "small": 50000,
            "medium": 150000,
            "large": 500000,
            "enterprise": 2000000,
        }

        logger.info(f"BusinessImpactCalculator initialisiert für {industry} ({organization_size})")

    def calculate_financial_impact(
        self, asset_context: AssetContext, breach_likelihood: float = 0.5, data_volume_records: int = 0
    ) -> FinancialImpact:
        """
        Berechnet den finanziellen Impact eines potenziellen Vorfalls.

        Args:
            asset_context: Kontext des betroffenen Assets
            breach_likelihood: Wahrscheinlichkeit eines Datenlecks (0-1)
            data_volume_records: Anzahl der potenziell betroffenen Datensätze

        Returns:
            FinancialImpact-Objekt mit allen Kostenkomponenten
        """
        multipliers = self.industry_multipliers.get(self.industry, {"compliance": 1.0, "reputation": 1.0, "financial": 1.0})

        # Direkte Kosten
        base_response = self.base_response_costs.get(self.organization_size, 150000)
        direct_costs = base_response * breach_likelihood * multipliers["financial"]

        # Indirekte Kosten (Ausfallzeiten)
        outage_hours = self._estimate_outage_hours(asset_context)
        hourly_cost = (self.annual_revenue / 8760) * asset_context.revenue_dependency / 100
        indirect_costs = outage_hours * hourly_cost * breach_likelihood

        # Regulatorische Strafen
        regulatory_fines = self._calculate_regulatory_fines(asset_context, data_volume_records, breach_likelihood)

        # Rechtskosten
        legal_costs = self._estimate_legal_costs(data_volume_records, breach_likelihood)

        # Reputationskosten
        reputation_costs = self._calculate_reputation_costs(asset_context, breach_likelihood) * multipliers["reputation"]

        impact = FinancialImpact(
            direct_costs=direct_costs,
            indirect_costs=indirect_costs,
            regulatory_fines=regulatory_fines,
            legal_costs=legal_costs,
            reputation_costs=reputation_costs,
        )

        logger.debug(f"Finanzieller Impact für {asset_context.asset_id}: {impact.total_costs:,.2f}")
        return impact

    def calculate_compliance_impact(self, asset_context: AssetContext, finding_type: str, severity: str) -> ComplianceImpact:
        """
        Berechnet den Compliance-Impact eines Findings.

        Args:
            asset_context: Kontext des betroffenen Assets
            finding_type: Typ des Findings
            severity: Schwere des Findings

        Returns:
            ComplianceImpact-Objekt
        """
        impact = ComplianceImpact()
        impact.frameworks = asset_context.compliance_frameworks.copy()

        severity_multiplier = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}.get(severity.lower(), 0.5)

        for framework in asset_context.compliance_frameworks:
            # Potenzielle Strafen berechnen
            max_fine = self._get_max_regulatory_fine(framework)
            adjusted_fine = max_fine * severity_multiplier
            impact.potential_fines[framework] = adjusted_fine

            # Verletzte Controls identifizieren
            violated = self._identify_violated_controls(framework, finding_type)
            impact.violated_controls.extend(violated)

        logger.debug(f"Compliance-Impact für {asset_context.asset_id}: {len(impact.violated_controls)} verletzte Controls")
        return impact

    def assess_reputation_impact(
        self, asset_context: AssetContext, data_classification: DataClassification, public_exposure: bool = False
    ) -> ReputationImpact:
        """
        Bewertet den potenziellen Reputationsschaden.

        Args:
            asset_context: Kontext des betroffenen Assets
            data_classification: Klassifizierung der betroffenen Daten
            public_exposure: Ob der Vorfall öffentlich bekannt werden könnte

        Returns:
            ReputationImpact-Enum-Wert
        """
        score = 0.0

        # Datenklassifizierung
        score += data_classification.weight * 0.4

        # Asset-Kritikalität
        score += asset_context.criticality.weight * 0.3

        # Öffentliche Exposition
        if public_exposure or asset_context.internet_exposed:
            score += 0.3

        # Benutzeranzahl (Auswirkungsgrad)
        if asset_context.user_count > 1000000:
            score += 0.2
        elif asset_context.user_count > 100000:
            score += 0.15
        elif asset_context.user_count > 10000:
            score += 0.1

        # Branchenmultiplikator
        multipliers = self.industry_multipliers.get(self.industry, {"reputation": 1.0})
        score = min(1.0, score * multipliers["reputation"])

        if score >= 0.8:
            return ReputationImpact.SEVERE
        elif score >= 0.6:
            return ReputationImpact.HIGH
        elif score >= 0.3:
            return ReputationImpact.MODERATE
        return ReputationImpact.LOW

    def calculate_overall_impact(
        self,
        asset_context: AssetContext,
        finding_type: str,
        severity: str,
        breach_likelihood: float = 0.5,
        data_volume_records: int = 0,
    ) -> BusinessImpactResult:
        """
        Berechnet den gesamten Business Impact.

        Args:
            asset_context: Kontext des betroffenen Assets
            finding_type: Typ des Findings
            severity: Schwere des Findings
            breach_likelihood: Wahrscheinlichkeit eines Vorfalls
            data_volume_records: Anzahl betroffener Datensätze

        Returns:
            BusinessImpactResult mit allen Impact-Komponenten
        """
        # Finanzieller Impact
        financial = self.calculate_financial_impact(asset_context, breach_likelihood, data_volume_records)

        # Compliance Impact
        compliance = self.calculate_compliance_impact(asset_context, finding_type, severity)

        # Reputation Impact
        reputation = self.assess_reputation_impact(
            asset_context, asset_context.data_classification, public_exposure=asset_context.internet_exposed
        )

        # Einzelne Scores
        asset_criticality_score = asset_context.criticality.weight
        data_sensitivity_score = asset_context.data_classification.weight
        exposure_score = asset_context.get_exposure_factor()

        # Gewichtete Berechnung des Gesamtscores
        # Gewichtung: Finanzen 30%, Compliance 25%, Reputation 20%, Asset 15%, Daten 10%
        financial_normalized = (
            min(1.0, financial.total_costs / (self.annual_revenue * 0.1)) if self.annual_revenue > 0 else 0.5
        )
        compliance_normalized = compliance.get_compliance_score()

        overall_score = (
            financial_normalized * 0.30
            + compliance_normalized * 0.25
            + reputation.weight * 0.20
            + asset_criticality_score * 0.15
            + data_sensitivity_score * 0.10
        )

        # Exposure-Faktor als Multiplikator
        overall_score = min(1.0, overall_score * (1 + exposure_score * 0.2))

        result = BusinessImpactResult(
            asset_id=asset_context.asset_id,
            overall_score=overall_score,
            financial_impact=financial,
            compliance_impact=compliance,
            reputation_impact=reputation,
            asset_criticality_score=asset_criticality_score,
            data_sensitivity_score=data_sensitivity_score,
            exposure_score=exposure_score,
        )

        logger.info(
            f"Business Impact für {asset_context.asset_id}: Score={overall_score:.2f}, Kategorie={result.get_risk_category()}"
        )

        return result

    def _estimate_outage_hours(self, asset_context: AssetContext) -> float:
        """Schätzt die Ausfallzeit basierend auf der Asset-Kritikalität."""
        base_hours = {
            AssetCriticality.CRITICAL: 72,
            AssetCriticality.HIGH: 48,
            AssetCriticality.MEDIUM: 24,
            AssetCriticality.LOW: 8,
            AssetCriticality.MINIMAL: 2,
        }
        return base_hours.get(asset_context.criticality, 24)

    def _calculate_regulatory_fines(
        self, asset_context: AssetContext, data_volume_records: int, breach_likelihood: float
    ) -> float:
        """Berechnet potenzielle regulatorische Strafen."""
        max_fine = 0.0

        for framework in asset_context.compliance_frameworks:
            fine = self._get_max_regulatory_fine(framework)
            # Skalierung basierend auf Datenvolumen
            volume_multiplier = min(2.0, 1 + (data_volume_records / 100000))
            max_fine = max(max_fine, fine * volume_multiplier)

        return max_fine * breach_likelihood

    def _get_max_regulatory_fine(self, framework: ComplianceFramework) -> float:
        """Gibt die maximale Strafe für ein Framework zurück."""
        # Höchststrafen in USD
        max_fines = {
            ComplianceFramework.GDPR: 20000000,  # 20M EUR oder 4% des Umsatzes
            ComplianceFramework.HIPAA: 1500000,  # pro Verstoß
            ComplianceFramework.PCI_DSS: 100000,  # pro Monat
            ComplianceFramework.SOX: 5000000,  # + Gefängnisstrafe
            ComplianceFramework.ISO27001: 50000,  # Zertifizierungsverlust
            ComplianceFramework.NIST: 1000000,  # Vertragsstrafen
        }
        return max_fines.get(framework, 100000)

    def _estimate_legal_costs(self, data_volume_records: int, breach_likelihood: float) -> float:
        """Schätzt die Rechtskosten."""
        base_costs = 50000
        per_record_cost = 0.50  # Durchschnittliche Kosten pro Datensatz
        return (base_costs + data_volume_records * per_record_cost) * breach_likelihood

    def _calculate_reputation_costs(self, asset_context: AssetContext, breach_likelihood: float) -> float:
        """Berechnet die Kosten durch Reputationsschaden."""
        if self.annual_revenue == 0:
            return 50000 * breach_likelihood

        # Geschätzter Umsatzverlust durch Reputationsschaden (5-15%)
        revenue_loss_percentage = 0.05 + (asset_context.criticality.level * 0.02)
        return self.annual_revenue * revenue_loss_percentage * breach_likelihood

    def _identify_violated_controls(self, framework: ComplianceFramework, finding_type: str) -> List[str]:
        """Identifiziert verletzte Controls basierend auf dem Finding-Typ."""
        control_mapping = {
            "sql_injection": ["Input Validation", "Secure Coding", "WAF Protection"],
            "xss": ["Output Encoding", "Content Security Policy", "Input Validation"],
            "authentication_bypass": ["Authentication", "Access Control", "Session Management"],
            "sensitive_data_exposure": ["Data Encryption", "Access Control", "Data Classification"],
            "broken_access_control": ["Access Control", "Authorization", "RBAC"],
            "security_misconfiguration": ["Configuration Management", "Hardening", "Patch Management"],
            "insufficient_logging": ["Logging and Monitoring", "Audit Controls", "SIEM"],
            "cryptographic_failure": ["Cryptography", "Key Management", "Data Protection"],
        }

        finding_lower = finding_type.lower().replace(" ", "_")
        return control_mapping.get(finding_lower, ["General Security Control"])

    def compare_impacts(self, results: List[BusinessImpactResult]) -> List[Tuple[BusinessImpactResult, int]]:
        """
        Vergleicht mehrere Impact-Ergebnisse und priorisiert sie.

        Args:
            results: Liste von BusinessImpactResult-Objekten

        Returns:
            Liste von Tupeln (Result, Priorität)
        """
        # Sortieren nach Gesamtscore (absteigend)
        sorted_results = sorted(results, key=lambda x: x.overall_score, reverse=True)

        return [(result, i + 1) for i, result in enumerate(sorted_results)]


# Singleton-Instanz für einfachen Zugriff
_default_calculator: Optional[BusinessImpactCalculator] = None


def get_calculator(
    organization_size: str = "medium", annual_revenue: float = 0.0, industry: str = "technology"
) -> BusinessImpactCalculator:
    """Gibt eine Calculator-Instanz zurück (erstellt eine neue bei Bedarf)."""
    global _default_calculator
    if _default_calculator is None:
        _default_calculator = BusinessImpactCalculator(organization_size, annual_revenue, industry)
    return _default_calculator
