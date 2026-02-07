"""
Beispiel für die Verwendung der False-Positive-Reduction Engine.

Dieses Beispiel zeigt, wie die Engine zur Validierung und Priorisierung
von Security Findings verwendet wird.
"""

import asyncio


from risk_engine import (
    FalsePositiveEngine,
    BusinessImpactCalculator,
    Finding,
    RiskFactors,
    CVSSData,
    AssetContext,
    AssetCriticality,
    DataClassification,
    ComplianceFramework,
)


async def example_false_positive_detection():
    """Beispiel: False-Positive-Erkennung."""
    print("=" * 60)
    print("Beispiel 1: False-Positive-Erkennung")
    print("=" * 60)

    # Engine initialisieren
    engine = FalsePositiveEngine(
        fp_database_path="fp_database.json",
        enable_llm_voting=False,  # In Produktion auf True setzen
    )

    # Beispiel-Finding 1: SQL Injection (echte Schwachstelle)
    finding_real = Finding(
        id="FIND-001",
        title="SQL Injection in Login-Form",
        description="Die Login-Formular ist anfällig für SQL-Injection-Angriffe. "
        "Ein Angreifer kann durch Manipulation des Benutzernamen-Feldes "
        "authentifizierte Zugriffe erlangen.",
        severity="critical",
        vulnerability_type="sql_injection",
        risk_factors=RiskFactors(
            cvss_data=CVSSData(base_score=9.8, vector_string="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
            epss_score=0.95,
            business_impact=0.9,
            exploitability=0.95,
            asset_criticality=1.0,
            internet_exposed=True,
            data_classification="restricted",
            patch_available=False,
            exploit_code_available=True,
        ),
        raw_evidence={"payload": "' OR '1'='1", "response": "Login successful", "endpoint": "/api/login"},
        target="https://example.com/api/login",
        cve_ids=["CVE-2023-1234"],
    )

    # Beispiel-Finding 2: Informational (wahrscheinlich FP)
    finding_info = Finding(
        id="FIND-002",
        title="Informational: Server Banner Detected",
        description="Der Webserver sendet einen Server-Header mit Versionsinformationen. "
        "Dies ist eine informative Feststellung und stellt nicht direkt eine "
        "Schwachstelle dar, könnte aber für Reconnaissance genutzt werden.",
        severity="info",
        vulnerability_type="information_disclosure",
        risk_factors=RiskFactors(
            cvss_data=CVSSData(base_score=2.3),
            epss_score=0.05,
            business_impact=0.1,
            exploitability=0.1,
            asset_criticality=0.3,
            internet_exposed=True,
            data_classification="public",
            patch_available=True,
        ),
        raw_evidence={"header": "Server: Apache/2.4.41"},
        target="https://example.com",
    )

    # Validierung durchführen
    result1 = await engine.validate_finding(finding_real)
    result2 = await engine.validate_finding(finding_info)

    # Ergebnisse anzeigen
    print("\n--- Finding 1: SQL Injection ---")
    print(f"False Positive: {result1.is_false_positive}")
    print(f"Konfidenz: {result1.confidence:.2%}")
    print(f"Risiko-Score: {result1.risk_score:.2f}")
    print(f"Priorität: {result1.priority}")
    print(f"Status: {result1.finding.status.value}")
    print(f"Begründung: {result1.reasoning}")
    print("Empfehlungen:")
    for rec in result1.recommendations:
        print(f"  - {rec}")

    print("\n--- Finding 2: Informational ---")
    print(f"False Positive: {result2.is_false_positive}")
    print(f"Konfidenz: {result2.confidence:.2%}")
    print(f"Risiko-Score: {result2.risk_score:.2f}")
    print(f"Priorität: {result2.priority}")
    print(f"Status: {result2.finding.status.value}")
    print(f"Begründung: {result2.reasoning}")
    print("Empfehlungen:")
    for rec in result2.recommendations:
        print(f"  - {rec}")


async def example_business_impact_calculation():
    """Beispiel: Business-Impact-Berechnung."""
    print("\n" + "=" * 60)
    print("Beispiel 2: Business-Impact-Berechnung")
    print("=" * 60)

    # Calculator initialisieren
    calculator = BusinessImpactCalculator(
        organization_size="large",
        annual_revenue=500000000,  # 500M EUR
        industry="finance",
    )

    # Asset-Kontext erstellen
    asset = AssetContext(
        asset_id="PROD-DB-001",
        asset_name="Production Customer Database",
        asset_type="database",
        criticality=AssetCriticality.CRITICAL,
        data_classification=DataClassification.RESTRICTED,
        compliance_frameworks={ComplianceFramework.GDPR, ComplianceFramework.PCI_DSS},
        internet_exposed=False,
        user_count=5000000,
        revenue_dependency=40.0,
    )

    # Impact berechnen
    impact = calculator.calculate_overall_impact(
        asset_context=asset,
        finding_type="sql_injection",
        severity="critical",
        breach_likelihood=0.8,
        data_volume_records=5000000,
    )

    # Ergebnisse anzeigen
    print(f"\nAsset: {asset.asset_name}")
    print(f"Gesamt-Impact-Score: {impact.overall_score:.2f}")
    print(f"Risiko-Kategorie: {impact.get_risk_category()}")

    print("\nFinanzieller Impact:")
    print(f"  Direkte Kosten: €{impact.financial_impact.direct_costs:,.2f}")
    print(f"  Indirekte Kosten: €{impact.financial_impact.indirect_costs:,.2f}")
    print(f"  Regulatorische Strafen: €{impact.financial_impact.regulatory_fines:,.2f}")
    print(f"  Rechtskosten: €{impact.financial_impact.legal_costs:,.2f}")
    print(f"  Reputationskosten: €{impact.financial_impact.reputation_costs:,.2f}")
    print(f"  GESAMT: €{impact.financial_impact.total_costs:,.2f}")

    print("\nCompliance-Impact:")
    print(f"  Betroffene Frameworks: {', '.join(f.framework_name for f in impact.compliance_impact.frameworks)}")
    print(f"  Verletzte Controls: {', '.join(impact.compliance_impact.violated_controls[:5])}")
    print(f"  Maximale Strafe: €{impact.compliance_impact.get_max_fine():,.2f}")

    print(f"\nReputation-Impact: {impact.reputation_impact.name}")
    print(f"  Beschreibung: {impact.reputation_impact.description}")

    print("\nEinzelfaktoren:")
    print(f"  Asset-Kritikalität: {impact.asset_criticality_score:.2f}")
    print(f"  Daten-Sensitivität: {impact.data_sensitivity_score:.2f}")
    print(f"  Expositions-Score: {impact.exposure_score:.2f}")

    print("\nPriorisierte Empfehlungen:")
    for rec in impact.get_prioritized_remediation():
        print(f"  - {rec}")


async def example_prioritization():
    """Beispiel: Finding-Priorisierung."""
    print("\n" + "=" * 60)
    print("Beispiel 3: Finding-Priorisierung")
    print("=" * 60)

    engine = FalsePositiveEngine(enable_llm_voting=False)

    # Mehrere Findings erstellen
    findings = [
        Finding(
            id="F001",
            title="Critical SQL Injection",
            description="Remote code execution via SQL injection",
            severity="critical",
            risk_factors=RiskFactors(
                cvss_data=CVSSData(base_score=9.8),
                epss_score=0.9,
                business_impact=0.95,
                exploitability=0.95,
                asset_criticality=1.0,
                internet_exposed=True,
            ),
        ),
        Finding(
            id="F002",
            title="XSS in Admin Panel",
            description="Stored XSS vulnerability",
            severity="high",
            risk_factors=RiskFactors(
                cvss_data=CVSSData(base_score=7.5),
                epss_score=0.6,
                business_impact=0.7,
                exploitability=0.7,
                asset_criticality=0.8,
                internet_exposed=False,
            ),
        ),
        Finding(
            id="F003",
            title="Outdated TLS Version",
            description="TLS 1.0 still supported",
            severity="medium",
            risk_factors=RiskFactors(
                cvss_data=CVSSData(base_score=5.0),
                epss_score=0.2,
                business_impact=0.4,
                exploitability=0.3,
                asset_criticality=0.5,
                internet_exposed=True,
            ),
        ),
        Finding(
            id="F004",
            title="Information Disclosure",
            description="Server version in headers",
            severity="info",
            risk_factors=RiskFactors(
                cvss_data=CVSSData(base_score=2.0),
                epss_score=0.05,
                business_impact=0.1,
                exploitability=0.1,
                asset_criticality=0.3,
                internet_exposed=True,
            ),
        ),
    ]

    # Findings priorisieren
    prioritized = engine.prioritize_findings(findings)

    print("\nPriorisierte Findings:")
    print(f"{'Rank':<6} {'ID':<8} {'Title':<30} {'Severity':<10} {'Risk Score'}")
    print("-" * 70)

    for i, finding in enumerate(prioritized, 1):
        risk = engine.calculate_risk_score(finding.risk_factors)
        print(f"{i:<6} {finding.id:<8} {finding.title[:28]:<30} {finding.severity:<10} {risk:.2f}")


async def main():
    """Hauptfunktion mit allen Beispielen."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " Zen-AI-Pentest False-Positive Engine Demo ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")

    try:
        await example_false_positive_detection()
        await example_business_impact_calculation()
        await example_prioritization()

        print("\n" + "=" * 60)
        print("Alle Beispiele erfolgreich abgeschlossen!")
        print("=" * 60)

    except Exception as e:
        print(f"\nFehler: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
