"""
Risk Scoring Examples
"""
from risk import (
    RiskEngine,
    CVSSVector,
    BusinessContext,
    ImpactLevel,
    RiskReportGenerator
)


def example_basic_risk():
    """Basic risk calculation"""
    engine = RiskEngine()
    
    # Calculate risk for a CVE
    risk = engine.calculate_risk(
        cve_id="CVE-2023-1234",
        cvss_vector=CVSSVector(
            av="N",  # Network
            ac="L",  # Low complexity
            pr="N",  # No privileges
            ui="N",  # No interaction
            s="U",   # Unchanged scope
            c="H",   # High confidentiality
            i="H",   # High integrity
            a="H"    # High availability
        )
    )
    
    print(f"CVE: {risk.cve_id}")
    print(f"CVSS: {risk.cvss_score} ({risk.cvss_severity})")
    print(f"EPSS: {risk.epss_probability}%")
    print(f"Business: {risk.business_impact_score}")
    print(f"Overall: {risk.overall_risk_score} - {risk.risk_priority}")
    
    return risk


def example_with_business_context():
    """Risk with business context"""
    engine = RiskEngine()
    
    # Define business context
    context = BusinessContext(
        asset_type="web_server",
        asset_value=ImpactLevel.HIGH,
        data_classification="confidential",
        exposure="internet",
        compliance_requirements=["PCI-DSS", "GDPR"],
        business_critical=True,
        user_impact=5000
    )
    
    risk = engine.calculate_risk(
        cve_id="CVE-2023-5678",
        cvss_vector=CVSSVector(
            av="N", ac="H", pr="L", ui="N",
            s="U", c="H", i="L", a="N"
        ),
        business_context=context
    )
    
    print("\nWith Business Context:")
    print(f"Overall Risk: {risk.overall_risk_score}")
    print(f"Priority: {risk.risk_priority}")
    
    return risk


def example_report():
    """Generate risk report"""
    engine = RiskEngine()
    
    # Calculate risks for multiple CVEs
    cves = [
        {"id": "CVE-2023-1111", "data": {"cvss3": {"vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"}}},
        {"id": "CVE-2023-2222", "data": {"cvss3": {"vectorString": "CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:N"}}},
        {"id": "CVE-2023-3333", "data": {}},
    ]
    
    risks = engine.calculate_batch(cves)
    
    # Generate reports
    generator = RiskReportGenerator()
    
    executive = generator.generate(risks, "executive", organization="Acme Corp")
    print("\nExecutive Summary:")
    print(f"  Critical: {executive['summary']['critical_count']}")
    print(f"  High: {executive['summary']['high_count']}")
    
    remediation = generator.generate(risks, "remediation")
    print(f"\nRemediation items: {len(remediation['items'])}")
    
    return risks


if __name__ == '__main__':
    print("=== Basic Risk Calculation ===")
    example_basic_risk()
    
    print("\n=== With Business Context ===")
    example_with_business_context()
    
    print("\n=== Batch Processing ===")
    example_report()
