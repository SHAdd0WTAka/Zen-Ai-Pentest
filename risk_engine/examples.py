"""
Beispiele und Tests für das Multi-Faktor Risk Scoring System

Dieses Modul demonstriert die Verwendung aller Risk Engine Komponenten:
- CVSS 3.1 Calculator (Base, Temporal, Environmental)
- EPSS Client (mit Caching)
- Business Impact Scorer
- Multi-Faktor Risk Scorer
- Risk Report Generation
"""

from risk_engine.business_impact_full import (
    BusinessImpactScorer,
)
from risk_engine.cvss_calculator_full import (
    CVSS31Calculator,
    calculate_cvss,
)
from risk_engine.epss_client_full import EPSSClientFull
from risk_engine.multi_factor_scorer import MultiFactorRiskScorer, RiskSeverity
from risk_engine.risk_report import RiskReport


def example_cvss_calculator():
    """
    Beispiel 1: CVSS 3.1 Calculator

    Demonstration aller CVSS Scores:
    - Base Score
    - Temporal Score
    - Environmental Score
    """
    print("=" * 70)
    print("BEISPIEL 1: CVSS 3.1 Calculator")
    print("=" * 70)

    calculator = CVSS31Calculator()

    # Beispiel: Log4j (CVE-2021-44228) - Critical RCE
    print("\n1.1 Log4j-like Vulnerability (CVSS 10.0)")
    print("-" * 50)

    result = calculator.calculate_full(
        attack_vector="NETWORK",
        attack_complexity="LOW",
        privileges_required="NONE",
        user_interaction="NONE",
        scope="CHANGED",
        confidentiality="HIGH",
        integrity="HIGH",
        availability="HIGH",
        # Temporal
        exploit_code_maturity="HIGH",
        remediation_level="UNAVAILABLE",
        report_confidence="CONFIRMED",
        # Environmental
        confidentiality_req="HIGH",
        integrity_req="HIGH",
        availability_req="HIGH",
    )

    print(f"Base Score:        {result.base_score}")
    print(f"Temporal Score:    {result.temporal_score}")
    print(f"Environmental:     {result.environmental_score}")
    print(f"Overall Score:     {result.overall_score}")
    print(f"Severity:          {result.severity}")
    print(f"Vector:            {result.vector_string}")

    # Beispiel: Einfacher Aufruf
    print("\n1.2 Einfacher API-Aufruf")
    print("-" * 50)

    simple_result = calculate_cvss(
        attack_vector="NETWORK",
        attack_complexity="LOW",
        privileges_required="NONE",
        scope="UNCHANGED",
        confidentiality="HIGH",
        integrity="HIGH",
        availability="NONE",
    )

    print(f"SQL Injection-like: {simple_result.base_score} ({simple_result.severity})")

    # Beispiel: XSS
    print("\n1.3 Cross-Site Scripting (XSS)")
    print("-" * 50)

    xss_result = calculate_cvss(
        attack_vector="NETWORK",
        attack_complexity="LOW",
        privileges_required="NONE",
        user_interaction="REQUIRED",
        scope="CHANGED",
        confidentiality="LOW",
        integrity="LOW",
        availability="NONE",
    )

    print(f"XSS Score: {xss_result.base_score} ({xss_result.severity})")
    print(f"Interpretation: {xss_result.details}")


def example_epss_client():
    """
    Beispiel 2: EPSS Client

    Demonstration der EPSS Integration:
    - Einzelne CVE Abfrage
    - Batch Abfrage
    - Caching
    - Priorisierung
    """
    print("\n" + "=" * 70)
    print("BEISPIEL 2: EPSS Client")
    print("=" * 70)

    client = EPSSClientFull(cache_duration_hours=24)

    # Beispiel: Bekannte CVEs
    print("\n2.1 EPSS Scores für bekannte CVEs")
    print("-" * 50)

    test_cves = [
        "CVE-2021-44228",  # Log4j
        "CVE-2017-0144",  # EternalBlue
        "CVE-2014-0160",  # Heartbleed
    ]

    for cve in test_cves:
        try:
            score = client.get_score(cve)
            interpretation = client.interpret_score(score.score)

            print(f"\n{cve}:")
            print(f"  EPSS Score:     {score.score:.4f} ({score.percentage:.2f}%)")
            print(f"  Percentile:     {score.percentile:.4f}")
            print(f"  Risk Level:     {score.risk_level}")
            print(f"  Interpretation: {interpretation['level']}")
            print(f"  Cached:         {score.cached}")
        except Exception as e:
            print(f"  {cve}: Fehler - {e}")

    # Beispiel: Priorisierung
    print("\n2.2 Priorisierungs-Entscheidung")
    print("-" * 50)

    test_cases = [
        ("CVE-2021-44228", 10.0),  # Log4j + CVSS 10
        ("CVE-2019-11358", 6.1),  # jQuery + CVSS 6.1
    ]

    for cve, cvss in test_cases:
        try:
            should_prioritize, reason = client.should_prioritize(cve, threshold=0.2, cvss_score=cvss)
            score = client.get_score(cve)

            print(f"\n{cve} (CVSS: {cvss}):")
            print(f"  EPSS: {score.percentage:.2f}%")
            print(f"  Priorisieren: {'JA' if should_prioritize else 'Nein'}")
            print(f"  Grund: {reason}")
        except Exception as e:
            print(f"  {cve}: Fehler - {e}")

    # Cache Stats
    print("\n2.3 Cache Statistiken")
    print("-" * 50)
    stats = client.get_cache_stats()
    print(f"  Cache-Datei: {stats['cache_file']}")
    print(f"  Gültige Einträge: {stats['valid_entries']}")


def example_business_impact():
    """
    Beispiel 3: Business Impact Scoring

    Demonstration der Business Impact Berechnung:
    - Data Sensitivity
    - System Criticality
    - Network Exposure
    - Compliance
    - Financial Impact
    """
    print("\n" + "=" * 70)
    print("BEISPIEL 3: Business Impact Scoring")
    print("=" * 70)

    scorer = BusinessImpactScorer()

    # Beispiel 1: Kritisches Production System
    print("\n3.1 Kritisches Production System (Internet-exposed)")
    print("-" * 50)

    factors_1 = {
        "data_sensitivity": "PII",  # Personenbezogene Daten
        "system_criticality": "CRITICAL",  # Produktions-Kernsystem
        "exposure": "INTERNET",  # Öffentlich erreichbar
        "compliance": ["GDPR", "PCI-DSS"],  # Doppelte Compliance
        "financial_impact": 2_000_000,  # 2M€ potenzieller Schaden
        "organization_revenue": 100_000_000,  # 100M€ Umsatz
    }

    result_1 = scorer.calculate(factors_1)

    print(f"Overall Score:        {result_1.overall_score:.3f}")
    print(f"Severity:             {result_1.severity}")
    print(f"SLA Target:           {result_1.sla_target}")
    print("\nKomponenten:")
    print(f"  Data Sensitivity:   {result_1.data_sensitivity_score:.3f}")
    print(f"  System Criticality: {result_1.system_criticality_score:.3f}")
    print(f"  Network Exposure:   {result_1.network_exposure_score:.3f}")
    print(f"  Compliance:         {result_1.compliance_score:.3f}")
    print(f"  Financial Impact:   {result_1.financial_impact_score:.3f}")
    print("\nEmpfehlungen:")
    for rec in result_1.recommendations[:3]:
        print(f"  - {rec}")

    # Beispiel 2: Internes Test-System
    print("\n3.2 Internes Test-System")
    print("-" * 50)

    factors_2 = {
        "data_sensitivity": "INTERNAL",  # Interne Daten
        "system_criticality": "MINIMAL",  # Test-System
        "exposure": "INTERNAL",  # Nur intern
        "compliance": [],  # Keine Compliance
        "financial_impact": 5_000,  # 5K€ potenzieller Schaden
        "organization_revenue": 100_000_000,
    }

    result_2 = scorer.calculate(factors_2)

    print(f"Overall Score: {result_2.overall_score:.3f} ({result_2.severity})")
    print(f"SLA Target:    {result_2.sla_target}")

    # Beispiel 3: Finanz-System mit PHI Daten
    print("\n3.3 Gesundheits-System (HIPAA)")
    print("-" * 50)

    factors_3 = {
        "data_sensitivity": "PHI",  # Gesundheitsdaten
        "system_criticality": "HIGH",  # Wichtig
        "exposure": "VPN",  # VPN-Zugang
        "compliance": ["HIPAA", "GDPR"],
        "financial_impact": 500_000,
        "organization_revenue": 50_000_000,
    }

    result_3 = scorer.calculate(factors_3)
    print(f"Overall Score: {result_3.overall_score:.3f} ({result_3.severity})")
    print("Empfehlungen:")
    for rec in result_3.recommendations[:2]:
        print(f"  - {rec}")


def example_multi_factor_scorer():
    """
    Beispiel 4: Multi-Faktor Risk Scorer

    Kombiniert CVSS + EPSS + Business Impact + Validation
    """
    print("\n" + "=" * 70)
    print("BEISPIEL 4: Multi-Faktor Risk Scorer")
    print("=" * 70)

    scorer = MultiFactorRiskScorer()

    # Beispiel 1: Log4j-ähnliche kritische Schwachstelle
    print("\n4.1 Kritische RCE (Log4j-ähnlich)")
    print("-" * 50)

    result_1 = scorer.calculate(
        finding_title="Critical Remote Code Execution",
        target="production-api.example.com",
        cve_id="CVE-2021-44228",
        cvss_metrics={"AV": "N", "AC": "L", "PR": "N", "UI": "N", "S": "C", "C": "H", "I": "H", "A": "H"},
        business_factors={
            "data_sensitivity": "PII",
            "system_criticality": "CRITICAL",
            "exposure": "INTERNET",
            "compliance": ["GDPR"],
            "financial_impact": 5_000_000,
        },
        validation_status="confirmed",
        epss_score=0.97,  # Log4j hat sehr hohen EPSS
    )

    print(f"Final Risk Score: {result_1.final_risk_score:.2f}/10")
    print(f"Severity:         {result_1.severity.name}")
    print(f"SLA Target:       {result_1.sla_target}")
    print("\nKomponenten-Breakdown:")
    print(f"  CVSS (30%):      {result_1.cvss_component.score:.3f} × 0.30 = {result_1.cvss_component.weighted_score:.3f}")
    print(f"  EPSS (20%):      {result_1.epss_component.score:.3f} × 0.20 = {result_1.epss_component.weighted_score:.3f}")
    print(
        f"  Business (35%):  {result_1.business_component.score:.3f} × 0.35 = {result_1.business_component.weighted_score:.3f}"
    )
    print(
        f"  Validation (15%): {result_1.validation_component.score:.3f} × 0.15 = {result_1.validation_component.weighted_score:.3f}"
    )
    print("\nPriorisierte Aktionen:")
    for i, action in enumerate(result_1.prioritized_actions[:3], 1):
        print(f"  {i}. {action}")

    # Beispiel 2: Mittlere SQL Injection
    print("\n4.2 SQL Injection (Internal System)")
    print("-" * 50)

    result_2 = scorer.calculate(
        finding_title="SQL Injection in Admin Panel",
        target="admin.internal.local",
        cvss_score=8.6,
        epss_score=0.35,
        business_factors={
            "data_sensitivity": "CONFIDENTIAL",
            "system_criticality": "HIGH",
            "exposure": "INTERNAL",
            "compliance": ["ISO27001"],
            "financial_impact": 200_000,
        },
        validation_status="available",
    )

    print(f"Final Risk Score: {result_2.final_risk_score:.2f}/10")
    print(f"Severity:         {result_2.severity.name}")
    print(f"SLA Target:       {result_2.sla_target}")

    # Beispiel 3: Information Disclosure (Low)
    print("\n4.3 Information Disclosure (Low Risk)")
    print("-" * 50)

    result_3 = scorer.calculate(
        finding_title="Server Version Disclosure",
        target="www.example.com",
        cvss_score=2.3,
        epss_score=0.05,
        business_factors={
            "data_sensitivity": "PUBLIC",
            "system_criticality": "LOW",
            "exposure": "INTERNET",
            "compliance": [],
            "financial_impact": 1_000,
        },
        validation_status="unknown",
    )

    print(f"Final Risk Score: {result_3.final_risk_score:.2f}/10")
    print(f"Severity:         {result_3.severity.name}")
    print(f"Empfehlung:       {result_3.recommendations[0] if result_3.recommendations else 'Standard-Behebung'}")


def example_risk_report():
    """
    Beispiel 5: Risk Report Generation

    Erzeugt strukturierte Reports in verschiedenen Formaten.
    """
    print("\n" + "=" * 70)
    print("BEISPIEL 5: Risk Report Generation")
    print("=" * 70)

    # Report erstellen
    report = RiskReport(report_title="Q1 2024 Security Assessment", organization="ACME Corporation")

    # Findings hinzufügen
    findings_data = [
        {
            "cve_id": "CVE-2024-0001",
            "title": "Critical SQL Injection",
            "description": "Remote code execution via SQL injection in login form",
            "target": "api.production.acme.com",
            "cvss": 9.8,
            "epss": 0.85,
            "business": {
                "data_sensitivity": "PII",
                "system_criticality": "CRITICAL",
                "exposure": "INTERNET",
                "compliance": ["GDPR", "PCI-DSS"],
                "financial_impact": 2_000_000,
            },
            "validation": "confirmed",
            "recommendations": ["Apply vendor patch", "Enable WAF rule", "Input validation"],
        },
        {
            "cve_id": "CVE-2024-0002",
            "title": "XSS in Admin Panel",
            "description": "Stored cross-site scripting vulnerability",
            "target": "admin.acme.com",
            "cvss": 7.5,
            "epss": 0.45,
            "business": {
                "data_sensitivity": "CONFIDENTIAL",
                "system_criticality": "HIGH",
                "exposure": "INTERNET",
                "compliance": ["GDPR"],
                "financial_impact": 100_000,
            },
            "validation": "available",
            "recommendations": ["Content Security Policy", "Output encoding"],
        },
        {
            "cve_id": "CVE-2024-0003",
            "title": "Outdated TLS Version",
            "description": "TLS 1.0 still supported",
            "target": "legacy.acme.com",
            "cvss": 5.0,
            "epss": 0.15,
            "business": {
                "data_sensitivity": "INTERNAL",
                "system_criticality": "MEDIUM",
                "exposure": "INTERNAL",
                "compliance": ["PCI-DSS"],
                "financial_impact": 10_000,
            },
            "validation": "theoretical",
            "recommendations": ["Disable TLS 1.0", "Enable TLS 1.3"],
        },
        {
            "cve_id": None,
            "title": "Missing Security Headers",
            "description": "Security headers not configured",
            "target": "www.acme.com",
            "cvss": 3.1,
            "epss": 0.02,
            "business": {
                "data_sensitivity": "PUBLIC",
                "system_criticality": "LOW",
                "exposure": "INTERNET",
                "compliance": [],
                "financial_impact": 1_000,
            },
            "validation": "unknown",
            "recommendations": ["Add HSTS header", "Add CSP header"],
        },
    ]

    scorer = MultiFactorRiskScorer()

    for data in findings_data:
        # Berechne Multi-Faktor Score
        score = scorer.calculate(
            finding_title=data["title"],
            target=data["target"],
            cve_id=data["cve_id"],
            cvss_score=data["cvss"],
            epss_score=data["epss"],
            business_factors=data["business"],
            validation_status=data["validation"],
        )

        # Füge zum Report hinzu
        report.add_finding_from_calculation(risk_score=score, description=data["description"])

    # Summary anzeigen
    print("\n5.1 Report Summary")
    print("-" * 50)
    summary = report.get_summary()

    print(f"Total Findings:     {summary.total_findings}")
    print(f"Critical:           {summary.critical_count}")
    print(f"High:               {summary.high_count}")
    print(f"Medium:             {summary.medium_count}")
    print(f"Low:                {summary.low_count}")
    print(f"\nAverage Risk:       {summary.average_risk_score:.2f}/10")
    print(f"Max Risk:           {summary.max_risk_score:.2f}/10")
    print(f"Due within 24h:     {summary.findings_due_24h}")
    print(f"Est. Remediation:   €{summary.total_estimated_cost:,.0f}")

    # Priorisierte Findings
    print("\n5.2 Top 3 Prioritized Findings")
    print("-" * 50)

    for i, finding in enumerate(report.get_prioritized_findings()[:3], 1):
        print(f"\n{i}. {finding.title}")
        print(f"   Risk: {finding.final_risk_score:.1f}/10 ({finding.severity})")
        print(f"   SLA:  {finding.sla_target}")
        print(f"   Top Action: {finding.actions[0] if finding.actions else 'Standard patch'}")

    # JSON Export (Snippet)
    print("\n5.3 JSON Export (Snippet)")
    print("-" * 50)
    json_output = report.to_json(indent=2)
    # Nur ersten Teil anzeigen
    lines = json_output.split("\n")[:20]
    for line in lines:
        print(line)
    print("...")

    # Markdown Export (Snippet)
    print("\n5.4 Markdown Export (Snippet)")
    print("-" * 50)
    md_output = report.to_markdown()
    lines = md_output.split("\n")[:25]
    for line in lines:
        print(line)
    print("...")


def example_formula_demonstration():
    """
    Beispiel 6: Formel-Demonstration

    Zeigt die genaue Berechnung des Multi-Faktor Risk Scores.
    """
    print("\n" + "=" * 70)
    print("BEISPIEL 6: Risk Score Formel-Demonstration")
    print("=" * 70)

    print("\nFormel:")
    print("-" * 50)
    print("Risk = (")
    print("    (CVSS_Base × 0.30) +")
    print("    (EPSS × 0.20) +")
    print("    (Business_Impact × 0.35) +")
    print("    (Validation_Confidence × 0.15)")
    print(") × 10")

    print("\n\nBerechnungsbeispiel:")
    print("-" * 50)

    # Werte
    cvss_base = 9.8
    epss = 0.85
    business = 0.92
    validation = 1.0

    print("\nEingabewerte:")
    print(f"  CVSS Base Score:      {cvss_base}")
    print(f"  EPSS Score:           {epss}")
    print(f"  Business Impact:      {business}")
    print(f"  Validation Conf.:     {validation}")

    # Gewichtete Werte
    cvss_weighted = (cvss_base / 10) * 0.30
    epss_weighted = epss * 0.20
    business_weighted = business * 0.35
    validation_weighted = validation * 0.15

    print("\nGewichtete Beiträge:")
    print(f"  CVSS:    ({cvss_base}/10) × 0.30 = {cvss_weighted:.4f}")
    print(f"  EPSS:    {epss} × 0.20 = {epss_weighted:.4f}")
    print(f"  Business: {business} × 0.35 = {business_weighted:.4f}")
    print(f"  Valid.:  {validation} × 0.15 = {validation_weighted:.4f}")

    # Summe
    total = cvss_weighted + epss_weighted + business_weighted + validation_weighted
    final = total * 10

    print(
        f"\nSumme: {cvss_weighted:.4f} + {epss_weighted:.4f} + {business_weighted:.4f} + {validation_weighted:.4f} = {total:.4f}"
    )
    print(f"Final Risk Score: {total:.4f} × 10 = {final:.2f}")

    # Severity
    severity = RiskSeverity.from_score(final)
    print(f"\nErgebnis: {final:.1f}/10 ({severity.name})")
    print(f"SLA: {severity.sla}")


def run_all_examples():
    """Führt alle Beispiele aus."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " Multi-Faktor Risk Scoring System - Beispiele ".center(68) + "║")
    print("╚" + "═" * 68 + "╝")

    example_cvss_calculator()
    example_epss_client()
    example_business_impact()
    example_multi_factor_scorer()
    example_risk_report()
    example_formula_demonstration()

    print("\n" + "=" * 70)
    print("Alle Beispiele erfolgreich abgeschlossen!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_examples()
