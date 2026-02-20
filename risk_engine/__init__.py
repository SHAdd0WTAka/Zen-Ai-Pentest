"""
Risk Engine für das Zen-AI-Pentest Framework.

Dieses Paket enthält:
- FalsePositiveEngine: Multi-Faktor-Validierung und FP-Reduzierung
- BusinessImpactCalculator: Geschäftliche Impact-Bewertung
- CVSS Scoring und EPSS Integration
- Compliance-Risiko-Analyse

Usage:
    from risk_engine import FalsePositiveEngine, BusinessImpactCalculator
    from risk_engine import Finding, RiskFactors, ConfidenceLevel

    # False Positive Engine
    fp_engine = FalsePositiveEngine()
    result = await fp_engine.validate_finding(finding)

    # Business Impact Calculator
    impact_calc = BusinessImpactCalculator(
        organization_size="large",
        annual_revenue=100000000,
        industry="finance"
    )
    impact = impact_calc.calculate_overall_impact(
        asset_context=asset,
        finding_type="sql_injection",
        severity="critical"
    )
"""

from .business_impact_calculator import (
    AssetContext,
    AssetCriticality,
    BusinessImpactCalculator,
    BusinessImpactResult,
    ComplianceFramework,
    ComplianceImpact,
    DataClassification,
    FinancialImpact,
    ReputationImpact,
    get_calculator,
)
from .cvss import CVSSCalculator
from .epss import EPSSClient
from .false_positive_engine import (
    BayesianFilter,
    ConfidenceLevel,
    CVSSData,
    EPSSData,
    FalsePositiveDatabase,
    FalsePositiveEngine,
    Finding,
    FindingStatus,
    LLMVotingEngine,
    RiskFactors,
    ValidationResult,
    VulnerabilityType,
    create_finding_from_scan_result,
)

# Additional exports for backwards compatibility
from .scorer import RiskScore, RiskScorer, SeverityLevel

__all__ = [
    # False Positive Engine
    "FalsePositiveEngine",
    "Finding",
    "ValidationResult",
    "RiskFactors",
    "CVSSData",
    "EPSSData",
    "ConfidenceLevel",
    "FindingStatus",
    "VulnerabilityType",
    "create_finding_from_scan_result",
    "FalsePositiveDatabase",
    "BayesianFilter",
    "LLMVotingEngine",
    # Business Impact Calculator
    "BusinessImpactCalculator",
    "BusinessImpactResult",
    "AssetContext",
    "AssetCriticality",
    "DataClassification",
    "ComplianceFramework",
    "FinancialImpact",
    "ComplianceImpact",
    "ReputationImpact",
    "get_calculator",
    # Additional scoring modules
    "RiskScorer",
    "RiskScore",
    "SeverityLevel",
    "CVSSCalculator",
    "EPSSClient",
]

__version__ = "2.0.0"
