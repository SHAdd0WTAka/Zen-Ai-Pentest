#!/usr/bin/env python3
"""
Integration Example: Using Personas with Zen-AI-Pentest Multi-Agent System

This example shows how to integrate the new personas with the existing
AgentOrchestrator and multi-agent collaboration system.
"""

import asyncio
import logging
from typing import Dict, List

from agents.agent_orchestrator import AgentOrchestrator
from agents.personas import create_persona

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ZenAI.Integration")


class PentestWorkflow:
    """
    Example workflow demonstrating persona integration with the multi-agent system.

    This class shows how personas can work together in a coordinated
    penetration test against a target.
    """

    def __init__(self):
        self.orchestrator = AgentOrchestrator()
        self.results = {}

    async def setup_personas(self):
        """Initialize and register all personas with the orchestrator"""
        logger.info("Setting up personas...")

        # Create persona instances
        personas = {
            "webapp": create_persona("webapp_expert", "WebApp-Scanner"),
            "api": create_persona("api_security_expert", "API-Tester"),
            "cloud": create_persona("cloud_security_expert", "Cloud-Auditor"),
            "crypto": create_persona("crypto_expert", "SSL-Analyzer"),
            "osint": create_persona("social_engineering_expert", "OSINT-Gatherer"),
        }

        # Register with orchestrator
        for name, persona in personas.items():
            self.orchestrator.register_agent(persona)
            logger.info(f"  Registered: {persona.name}")

        return personas

    async def run_web_application_assessment(self, target: str):
        """
        Run a comprehensive web application assessment.

        Workflow:
        1. OSINT gathering
        2. Web application scan
        3. API security testing
        4. SSL/TLS analysis
        5. Report generation
        """
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Starting Web Application Assessment: {target}")
        logger.info(f"{'=' * 60}")

        # Phase 1: OSINT Gathering
        logger.info("\n[Phase 1] OSINT Gathering")
        osint_persona = create_persona("social_engineering_expert", "OSINT-Phase1")

        osint_task = {"type": "osint_gathering", "context": {"target": target, "scope": ["corporate", "technical", "social"]}}

        osint_result = await osint_persona.execute_task(osint_task)
        self.results["osint"] = osint_result

        if osint_result["status"] == "complete":
            logger.info(f"  Found {osint_result['results'].get('data_points', 0)} data points")
            tech_stack = osint_result["results"].get("technologies", [])
            if tech_stack:
                logger.info(f"  Technology stack: {', '.join(tech_stack)}")

        # Phase 2: Web Application Scan
        logger.info("\n[Phase 2] Web Application Scanning")
        webapp_persona = create_persona("webapp_expert", "WebApp-Phase2")

        webapp_task = {
            "type": "webapp_scan",
            "context": {
                "target": target,
                "scan_depth": "comprehensive",
                "test_sqli": True,
                "test_xss": True,
                "test_csrf": True,
            },
        }

        webapp_result = await webapp_persona.execute_task(webapp_task)
        self.results["webapp"] = webapp_result

        if webapp_result["status"] == "complete":
            findings = webapp_result.get("findings", [])
            logger.info(f"  Vulnerabilities found: {len(findings)}")

        # Phase 3: API Security Testing
        logger.info("\n[Phase 3] API Security Testing")
        api_persona = create_persona("api_security_expert", "API-Phase3")

        api_task = {
            "type": "api_security_scan",
            "context": {
                "target": f"https://{target}/api",
                "api_type": "rest",
                "test_auth": True,
                "test_bola": True,
                "test_rate_limit": True,
            },
        }

        api_result = await api_persona.execute_task(api_task)
        self.results["api"] = api_result

        if api_result["status"] == "complete":
            endpoints = api_result.get("endpoints", [])
            logger.info(f"  Endpoints discovered: {len(endpoints)}")

        # Phase 4: SSL/TLS Analysis
        logger.info("\n[Phase 4] SSL/TLS Analysis")
        crypto_persona = create_persona("crypto_expert", "Crypto-Phase4")

        crypto_task = {
            "type": "ssl_scan",
            "context": {"target": target, "port": 443, "check_vulnerabilities": True, "cipher_analysis": True},
        }

        crypto_result = await crypto_persona.execute_task(crypto_task)
        self.results["crypto"] = crypto_result

        if crypto_result["status"] == "complete":
            ssl_grade = crypto_result.get("analysis", {}).get("ssl_grade", "Unknown")
            logger.info(f"  SSL Grade: {ssl_grade}")

        # Phase 5: Generate Report
        logger.info("\n[Phase 5] Generating Assessment Report")
        report = await self._generate_webapp_report()

        return report

    async def run_cloud_infrastructure_assessment(self, provider: str, target: str):
        """
        Run a cloud infrastructure security assessment.

        Workflow:
        1. Cloud provider enumeration
        2. IAM analysis
        3. Storage security check
        4. Network security review
        5. Compliance check
        """
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Starting Cloud Assessment: {provider} - {target}")
        logger.info(f"{'=' * 60}")

        cloud_persona = create_persona("cloud_security_expert", "Cloud-Assessor")

        # Cloud audit task
        cloud_task = {
            "type": "cloud_audit",
            "context": {
                "provider": provider,
                "target": target,
                "regions": ["us-east-1", "us-west-2", "eu-west-1"],
                "checks": ["iam", "s3", "ec2", "cloudtrail", "guardduty"],
            },
        }

        result = await cloud_persona.execute_task(cloud_task)

        if result["status"] == "complete":
            findings = result.get("results", {}).get("findings", [])
            critical = len([f for f in findings if f.get("severity") == "critical"])
            high = len([f for f in findings if f.get("severity") == "high"])

            logger.info(f"  Total findings: {len(findings)}")
            logger.info(f"  Critical: {critical}, High: {high}")

        return result

    async def run_incident_response_forensics(self, evidence_sources: List[Dict]):
        """
        Run digital forensics and incident response workflow.

        Workflow:
        1. Evidence collection
        2. Memory analysis
        3. Log analysis
        4. Timeline reconstruction
        5. IOC extraction
        """
        logger.info(f"\n{'=' * 60}")
        logger.info("Starting Incident Response Forensics")
        logger.info(f"{'=' * 60}")

        forensics_persona = create_persona("forensics_expert", "DFIR-Analyst")

        # Memory analysis
        logger.info("\n[Phase 1] Memory Analysis")
        memory_task = {
            "type": "memory_analysis",
            "context": {"dump_path": "/evidence/memory.dmp", "profile": "Win10x64_19041"},
        }

        memory_result = await forensics_persona.execute_task(memory_task)

        if memory_result["status"] == "complete":
            suspicious = memory_result["results"].get("suspicious_processes", [])
            logger.info(f"  Suspicious processes: {len(suspicious)}")

        # Log analysis
        logger.info("\n[Phase 2] Log Analysis")
        log_task = {
            "type": "log_analysis",
            "context": {
                "log_path": "/var/log/auth.log",
                "log_type": "linux",
                "time_range": {"start": "2026-03-01T00:00:00Z", "end": "2026-03-31T23:59:59Z"},
            },
        }

        log_result = await forensics_persona.execute_task(log_task)

        if log_result["status"] == "complete":
            suspicious_events = log_result["results"].get("suspicious", [])
            logger.info(f"  Suspicious events: {len(suspicious_events)}")

        return {"memory": memory_result, "logs": log_result}

    async def _generate_webapp_report(self) -> Dict:
        """Generate consolidated web application assessment report"""
        report = {
            "assessment_type": "Web Application Security",
            "findings_summary": {
                "osint": self.results.get("osint", {}).get("results", {}),
                "webapp": self.results.get("webapp", {}).get("findings", []),
                "api": self.results.get("api", {}).get("endpoints", []),
                "crypto": self.results.get("crypto", {}).get("analysis", {}),
            },
            "risk_level": self._calculate_overall_risk(),
            "recommendations": self._compile_recommendations(),
        }

        return report

    def _calculate_overall_risk(self) -> str:
        """Calculate overall risk level from all findings"""
        risk_levels = ["low", "medium", "high", "critical"]
        max_risk = 0

        for result in self.results.values():
            if isinstance(result, dict):
                analysis = result.get("analysis", {})
                risk = analysis.get("risk_level", "low")
                if risk in risk_levels:
                    max_risk = max(max_risk, risk_levels.index(risk))

        return risk_levels[max_risk]

    def _compile_recommendations(self) -> List[str]:
        """Compile recommendations from all personas"""
        recommendations = []

        for result in self.results.values():
            if isinstance(result, dict):
                analysis = result.get("analysis", {})
                recs = analysis.get("recommendations", [])
                recommendations.extend(recs)

        return list(set(recommendations))  # Remove duplicates


async def example_multi_persona_collaboration():
    """
    Example showing multiple personas working together on a target.
    """
    logger.info("\n" + "=" * 60)
    logger.info("Multi-Persona Collaboration Example")
    logger.info("=" * 60)

    target = "example-target.com"

    # Create orchestrator
    orchestrator = AgentOrchestrator()

    # Create and register personas
    personas = {
        "osint": create_persona("social_engineering_expert", "OSINT-Agent"),
        "webapp": create_persona("webapp_expert", "WebApp-Agent"),
        "api": create_persona("api_security_expert", "API-Agent"),
        "crypto": create_persona("crypto_expert", "Crypto-Agent"),
    }

    for persona in personas.values():
        orchestrator.register_agent(persona)

    logger.info(f"\nCoordinated assessment of {target}")

    # Execute tasks in parallel
    tasks = [
        personas["osint"].execute_task(
            {"type": "osint_gathering", "context": {"target": target, "scope": ["corporate", "technical"]}}
        ),
        personas["webapp"].execute_task({"type": "webapp_scan", "context": {"target": target, "scan_depth": "normal"}}),
        personas["api"].execute_task(
            {"type": "api_security_scan", "context": {"target": f"https://{target}/api", "api_type": "rest"}}
        ),
        personas["crypto"].execute_task({"type": "ssl_scan", "context": {"target": target, "port": 443}}),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    logger.info("\nResults:")
    for (name, _), result in zip(personas.items(), results):
        if isinstance(result, Exception):
            logger.info(f"  {name}: Error - {result}")
        else:
            status = result.get("status", "unknown")
            logger.info(f"  {name}: {status}")


async def example_custom_workflow():
    """
    Example of creating a custom workflow with personas.
    """
    logger.info("\n" + "=" * 60)
    logger.info("Custom Workflow Example")
    logger.info("=" * 60)

    # Create workflow instance
    workflow = PentestWorkflow()

    # Run web application assessment
    target = "testphp.vulnweb.com"
    report = await workflow.run_web_application_assessment(target)

    logger.info("\nAssessment Report Summary:")
    logger.info(f"  Target: {target}")
    logger.info(f"  Overall Risk: {report['risk_level'].upper()}")
    logger.info(f"  Recommendations: {len(report['recommendations'])}")

    for rec in report["recommendations"][:3]:
        logger.info(f"    - {rec}")


async def main():
    """Main execution function"""
    print("\n" + "=" * 60)
    print("Zen-AI-Pentest Personas - Integration Examples")
    print("=" * 60)

    # Example 1: Multi-persona collaboration
    await example_multi_persona_collaboration()

    # Example 2: Custom workflow
    await example_custom_workflow()

    print("\n" + "=" * 60)
    print("Integration examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
