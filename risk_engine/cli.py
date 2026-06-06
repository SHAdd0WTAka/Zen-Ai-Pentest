"""
Risk Scoring CLI

Command-line interface for the Risk Scoring engine.
"""

import argparse
import json
import sys


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Zen-AI-Pentest Risk Scoring CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Calculate risk for a CVE
  %(prog)s calculate --cve CVE-2021-44228

  # Calculate risk with context
  %(prog)s calculate --cve CVE-2021-44228 --internet-facing --criticality critical

  # Calculate CVSS from metrics
  %(prog)s cvss --av N --ac L --pr N --ui N --s U --c H --i H --a H

  # Get EPSS score
  %(prog)s epss CVE-2021-44228

  # Prioritize findings from file
  %(prog)s prioritize --file findings.json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Calculate command
    calc_parser = subparsers.add_parser("calculate", help="Calculate risk score")
    calc_parser.add_argument("--cve", help="CVE ID")
    calc_parser.add_argument("--cvss", type=float, help="CVSS score")
    calc_parser.add_argument("--title", help="Finding title")
    calc_parser.add_argument("--description", help="Finding description")
    calc_parser.add_argument("--internet-facing", action="store_true", help="Internet-facing asset")
    calc_parser.add_argument(
        "--criticality", choices=["critical", "high", "medium", "low"], default="medium", help="Asset criticality"
    )
    calc_parser.add_argument(
        "--data-sensitivity",
        choices=["pii", "phi", "financial", "confidential", "internal", "public"],
        default="internal",
        help="Data sensitivity",
    )
    calc_parser.add_argument("--compliance", nargs="+", help="Compliance frameworks (GDPR, HIPAA, PCI-DSS)")
    calc_parser.add_argument("--exploit-available", action="store_true", help="Exploit code available")
    calc_parser.add_argument("--output", "-o", choices=["json", "table"], default="table", help="Output format")

    # CVSS command
    cvss_parser = subparsers.add_parser("cvss", help="Calculate CVSS score")
    cvss_parser.add_argument("--av", choices=["N", "A", "L", "P"], default="N", help="Attack Vector")
    cvss_parser.add_argument("--ac", choices=["L", "H"], default="L", help="Attack Complexity")
    cvss_parser.add_argument("--pr", choices=["N", "L", "H"], default="N", help="Privileges Required")
    cvss_parser.add_argument("--ui", choices=["N", "R"], default="N", help="User Interaction")
    cvss_parser.add_argument("--s", choices=["U", "C"], default="U", help="Scope")
    cvss_parser.add_argument("--c", choices=["N", "L", "H"], default="N", help="Confidentiality Impact")
    cvss_parser.add_argument("--i", choices=["N", "L", "H"], default="N", help="Integrity Impact")
    cvss_parser.add_argument("--a", choices=["N", "L", "H"], default="N", help="Availability Impact")

    # EPSS command
    epss_parser = subparsers.add_parser("epss", help="Get EPSS score")
    epss_parser.add_argument("cve", help="CVE ID")

    # CVE command
    cve_parser = subparsers.add_parser("cve", help="Get CVE information")
    cve_parser.add_argument("cve", help="CVE ID")

    # Prioritize command
    prio_parser = subparsers.add_parser("prioritize", help="Prioritize findings")
    prio_parser.add_argument("--file", "-f", required=True, help="JSON file with findings")
    prio_parser.add_argument("--internet-facing", action="store_true", help="Internet-facing context")
    prio_parser.add_argument("--limit", "-n", type=int, default=10, help="Limit results")

    # Dashboard command
    dash_parser = subparsers.add_parser("dashboard", help="Generate dashboard stats")
    dash_parser.add_argument("--file", "-f", required=True, help="JSON file with findings")

    # Severity levels command
    subparsers.add_parser("severity-levels", help="Show severity levels")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == "calculate":
        cmd_calculate(args)
    elif args.command == "cvss":
        cmd_cvss(args)
    elif args.command == "epss":
        cmd_epss(args)
    elif args.command == "cve":
        cmd_cve(args)
    elif args.command == "prioritize":
        cmd_prioritize(args)
    elif args.command == "dashboard":
        cmd_dashboard(args)
    elif args.command == "severity-levels":
        cmd_severity_levels()


def cmd_calculate(args):
    """Calculate risk score."""
    from risk_engine.scorer import RiskScorer

    scorer = RiskScorer()

    # Build finding
    finding = {
        "title": args.title or "Unknown",
        "description": args.description or "",
    }

    if args.cve:
        finding["cve_id"] = args.cve
    if args.cvss:
        finding["cvss_score"] = args.cvss
    if args.exploit_available:
        finding["exploit_available"] = True

    # Build context
    context = {
        "internet_facing": args.internet_facing,
        "asset_criticality": args.criticality,
        "data_sensitivity": args.data_sensitivity,
        "compliance": args.compliance or [],
    }

    # Calculate
    result = scorer.calculate(finding, context)

    # Output
    if args.output == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"\n{'=' * 60}")
        print(f"RISK SCORE: {result.value:.2f}/10")
        print(f"{'=' * 60}")
        print(f"Severity: {result.severity.name} ({result.severity.label})")
        print(f"SLA Target: {result.severity.sla}")
        print(f"Confidence: {result.confidence:.0%}")
        print("\nComponents:")
        print(f"  CVSS Base: {result.components.cvss_base:.2f}")
        print(f"  EPSS: {result.components.epss_score:.4f} ({result.components.epss_score * 100:.2f}%)")
        print(f"  Business Impact: {result.components.business_impact:.3f}")
        print(f"  Exploit Availability: {result.components.exploit_availability:.3f}")
        print("\nPrioritized Actions:")
        for action in result.prioritized_actions:
            print(f"  • {action}")


def cmd_cvss(args):
    """Calculate CVSS score."""
    from risk_engine.cvss import CVSSCalculator

    calc = CVSSCalculator()

    metrics = {
        "AV": args.av,
        "AC": args.ac,
        "PR": args.pr,
        "UI": args.ui,
        "S": args.s,
        "C": args.c,
        "I": args.i,
        "A": args.a,
    }

    score = calc.calculate(metrics)
    vector = calc.get_vector_from_metrics(metrics)

    # Determine severity
    severity = "None"
    if score >= 9.0:
        severity = "Critical"
    elif score >= 7.0:
        severity = "High"
    elif score >= 4.0:
        severity = "Medium"
    elif score >= 0.1:
        severity = "Low"

    print(f"\nCVSS Base Score: {score}")
    print(f"Vector: {vector}")
    print(f"Severity: {severity}")


def cmd_epss(args):
    """Get EPSS score."""
    from risk_engine.epss import EPSSClient

    client = EPSSClient()
    score = client.get_score(args.cve)
    percentile = client.get_percentile(args.cve)
    interpretation = client.interpret_score(score)

    print(f"\n{args.cve}")
    print(f"EPSS Score: {score:.4f} ({score * 100:.2f}%)")
    if percentile:
        print(f"Percentile: {percentile:.4f} (top {percentile * 100:.2f}%)")
    print(f"Interpretation: {interpretation}")


def cmd_cve(args):
    """Get CVE information."""
    from risk_engine.scorer import RiskScorer

    scorer = RiskScorer()
    info = scorer.get_cve_info(args.cve)

    if not info:
        print(f"CVE {args.cve} not found")
        return

    print(f"\n{info.cve_id}")
    print(f"{'=' * 60}")
    print(f"CVSS Score: {info.cvss_score}")
    print(f"CVSS Vector: {info.cvss_vector}")
    print(f"EPSS Score: {info.epss_score:.4f} ({info.epss_score * 100:.2f}%)")
    if info.epss_percentile:
        print(f"EPSS Percentile: {info.epss_percentile:.4f}")
    print("\nDescription:")
    print(info.description[:500] + "..." if len(info.description) > 500 else info.description)
    print("\nReferences:")
    for ref in info.references[:5]:
        print(f"  • {ref}")


def cmd_prioritize(args):
    """Prioritize findings."""
    from risk_engine.scorer import RiskScorer

    # Load findings
    with open(args.file) as f:
        data = json.load(f)

    findings = data if isinstance(data, list) else data.get("findings", [])

    scorer = RiskScorer()

    context = {
        "internet_facing": args.internet_facing,
    }

    prioritized = scorer.prioritize_findings(findings, context)

    print(f"\n{'=' * 80}")
    print(f"Prioritized Findings (Top {args.limit})")
    print(f"{'=' * 80}")

    for i, finding in enumerate(prioritized[: args.limit], 1):
        risk = finding.get("risk_score", {})
        print(f"\n{i}. {finding.get('title', 'Unknown')}")
        print(f"   Risk Score: {risk.get('risk_score', 'N/A')}")
        print(f"   Severity: {risk.get('severity', {}).get('level', 'N/A')}")
        print(f"   SLA: {risk.get('sla_target', 'N/A')}")


def cmd_dashboard(args):
    """Generate dashboard stats."""
    from risk_engine.scorer import RiskScorer

    # Load findings
    with open(args.file) as f:
        data = json.load(f)

    findings = data if isinstance(data, list) else data.get("findings", [])

    scorer = RiskScorer()
    stats = scorer.get_dashboard_stats(findings)

    print(f"\n{'=' * 60}")
    print("Risk Dashboard Statistics")
    print(f"{'=' * 60}")
    print(f"Total Findings: {stats['total_findings']}")
    print(f"Average Risk Score: {stats['avg_risk_score']:.2f}")
    print(f"High Risk Count: {stats['high_risk_count']}")
    print(f"Critical Count: {stats['critical_count']}")
    print("\nBy Severity:")
    for sev, count in stats["by_severity"].items():
        print(f"  {sev}: {count}")

    if stats["requires_immediate_action"]:
        print("\n⚠️  IMMEDIATE ACTION REQUIRED - Critical findings detected!")


def cmd_severity_levels():
    """Show severity levels."""
    from risk_engine.scorer import SeverityLevel

    print(f"\n{'=' * 60}")
    print("Risk Severity Levels")
    print(f"{'=' * 60}")
    print()

    for level in SeverityLevel:
        print(f"{level.name}")
        print(f"  Range: {level.min_score} - {level.max_score}")
        print(f"  SLA: {level.sla}")
        print(f"  Label: {level.label}")
        print()

    print("Formula:")
    print("  Risk Score = (CVSS×0.30 + EPSS×0.25 + Business×0.35 + Exploit×0.10) × 10")


if __name__ == "__main__":
    main()
