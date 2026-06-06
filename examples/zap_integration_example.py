"""OWASP ZAP Integration Examples for Zen-AI-Pentest

This example demonstrates the full capabilities of the ZAP integration:
- Basic scanning
- Authenticated scanning
- API scanning (OpenAPI/GraphQL)
- Batch scanning
- Pipeline workflows
- Report generation

Author: Zen-AI-Pentest Team
"""

import asyncio
import json
from datetime import datetime, timezone

from modules.zap_orchestrator import (
    ZAPBatchScanner,
    ZAPOrchestrator,
    ZAPOrchestratorConfig,
    ZAPScanPipeline,
    quick_scan,
)

# Import ZAP components
from tools.zap_integration import (
    ZAPAuthConfig,
    ZAPAuthMethod,
    ZAPContext,
    ZAPDockerManager,
    ZAPScanner,
    ZAPScanPolicy,
)

# ═══════════════════════════════════════════════════════════════
# Example 1: Basic Scan
# ═══════════════════════════════════════════════════════════════


async def example_basic_scan():
    """Basic ZAP scan example"""
    print("\n" + "=" * 60)
    print("Example 1: Basic ZAP Scan")
    print("=" * 60)

    # Method 1: Direct scanner usage
    scanner = ZAPScanner(
        target="http://scanme.nmap.org",
        api_url="http://localhost:8080",
        options={
            "spider": True,
            "active_scan": True,
            "scan_timeout": 300,
        },
    )

    result = await scanner.scan()

    print(f"Scan Success: {result.success}")
    print(f"Scan Time: {result.scan_time:.2f}s")
    print(f"URLs Crawled: {result.urls_crawled}")
    print(f"Alerts Found: {len(result.alerts)}")
    print(f"  - High: {len(result.get_high_risk())}")
    print(f"  - Medium: {len(result.get_medium_risk())}")
    print(f"  - Low: {len(result.get_low_risk())}")

    # Print first 3 high risk alerts
    for alert in result.get_high_risk()[:3]:
        print(f"\n  High Risk: {alert.name}")
        print(f"    URL: {alert.url}")
        print(f"    CWE: {alert.cwe_id}")


# ═══════════════════════════════════════════════════════════════
# Example 2: Spider Only Scan
# ═══════════════════════════════════════════════════════════════


async def example_spider_only():
    """Spider-only crawl example"""
    print("\n" + "=" * 60)
    print("Example 2: Spider Only Scan")
    print("=" * 60)

    scanner = ZAPScanner(
        target="http://scanme.nmap.org",
        api_url="http://localhost:8080",
        options={
            "spider": True,
            "active_scan": False,  # Disable active scanning
            "recursion_depth": 3,
            "max_children": 100,
        },
    )

    result = await scanner.spider_scan()

    print(f"Spider Scan ID: {result.scan_id}")
    print(f"Completed: {result.completed}")
    print(f"URLs Found: {len(result.urls_found)}")
    print("\nFirst 5 URLs:")
    for url in result.urls_found[:5]:
        print(f"  - {url}")


# ═══════════════════════════════════════════════════════════════
# Example 3: Authenticated Scan (Form-Based)
# ═══════════════════════════════════════════════════════════════


async def example_authenticated_scan():
    """Authenticated scan with form-based login"""
    print("\n" + "=" * 60)
    print("Example 3: Authenticated Scan (Form-Based)")
    print("=" * 60)

    # Create authentication configuration
    auth_config = ZAPAuthConfig(
        method=ZAPAuthMethod.FORM_BASED,
        login_url="http://target.example.com/login",
        username="admin",
        password="admin123",
        username_field="username",
        password_field="password",
        logged_in_indicator="Welcome.*admin",
        logged_out_indicator="Login",
    )

    scanner = ZAPScanner(
        target="http://target.example.com",
        api_url="http://localhost:8080",
        options={
            "spider": True,
            "active_scan": True,
            "scan_timeout": 600,
            "context_name": "authenticated_context",
        },
    )

    result = await scanner.scan(auth_config=auth_config)

    print(f"Auth Success: {result.auth_success}")
    print(f"Context: {result.context_name}")
    print(f"Alerts Found: {len(result.alerts)}")

    # Print authenticated findings
    for alert in result.get_high_risk():
        print(f"\n  High: {alert.name}")
        print(f"    URL: {alert.url}")


# ═══════════════════════════════════════════════════════════════
# Example 4: JWT Authenticated Scan
# ═══════════════════════════════════════════════════════════════


async def example_jwt_scan():
    """Scan with JWT authentication"""
    print("\n" + "=" * 60)
    print("Example 4: JWT Authenticated Scan")
    print("=" * 60)

    auth_config = ZAPAuthConfig(
        method=ZAPAuthMethod.MANUAL,
        login_url="http://api.example.com",
        jwt_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        jwt_header_name="Authorization",
        jwt_header_prefix="Bearer",
        logged_in_indicator="200",
    )

    scanner = ZAPScanner(
        target="http://api.example.com",
        api_url="http://localhost:8080",
    )

    # Use context for authenticated scanning
    context = ZAPContext(
        name="jwt_context",
        include_regexes=["http://api.example.com.*"],
        auth_config=auth_config,
    )

    # Create context via context manager
    context_id = await scanner.context_manager.create_context(context)
    print(f"Created context: {context_id}")

    result = await scanner.scan(auth_config=auth_config)
    print(f"Scan complete: {len(result.alerts)} alerts")


# ═══════════════════════════════════════════════════════════════
# Example 5: OpenAPI Scan
# ═══════════════════════════════════════════════════════════════


async def example_openapi_scan():
    """OpenAPI/Swagger API scan"""
    print("\n" + "=" * 60)
    print("Example 5: OpenAPI Scan")
    print("=" * 60)

    scanner = ZAPScanner(
        target="http://api.example.com",
        api_url="http://localhost:8080",
    )

    # Import OpenAPI spec and scan
    result = await scanner.openapi_scan(
        openapi_url="http://api.example.com/openapi.json",
        target_url="http://api.example.com",
        context_name="api_context",
    )

    print(f"OpenAPI Import Complete: {result.completed}")
    print(f"URLs Found: {len(result.urls_found)}")

    # Get alerts from API scan
    alerts = await scanner.get_alerts()
    print(f"API Vulnerabilities Found: {len(alerts)}")


# ═══════════════════════════════════════════════════════════════
# Example 6: GraphQL Scan
# ═══════════════════════════════════════════════════════════════


async def example_graphql_scan():
    """GraphQL endpoint scan"""
    print("\n" + "=" * 60)
    print("Example 6: GraphQL Scan")
    print("=" * 60)

    scanner = ZAPScanner(
        target="http://graphql.example.com",
        api_url="http://localhost:8080",
    )

    # Import GraphQL schema
    result = await scanner.graphql_scan(
        endpoint="http://graphql.example.com/graphql",
        schema_url="http://graphql.example.com/schema.graphql",
        context_name="graphql_context",
    )

    print(f"GraphQL Import Complete: {result.completed}")
    print(f"URLs Found: {len(result.urls_found)}")


# ═══════════════════════════════════════════════════════════════
# Example 7: Report Generation
# ═══════════════════════════════════════════════════════════════


async def example_report_generation():
    """Generate various report formats"""
    print("\n" + "=" * 60)
    print("Example 7: Report Generation")
    print("=" * 60)

    scanner = ZAPScanner(
        target="http://scanme.nmap.org",
        api_url="http://localhost:8080",
    )

    # First run a scan
    result = await scanner.scan()

    if result.success:
        # Generate HTML report
        html_report = await scanner.generate_report(
            report_format="html",
            output_path="./reports/zap_report.html",
        )
        print(f"HTML Report: {html_report}")

        # Generate JSON report
        json_report = await scanner.generate_report(
            report_format="json",
            output_path="./reports/zap_report.json",
        )
        print(f"JSON Report: {json_report}")

        # Generate SARIF report
        sarif_report = await scanner._generate_sarif_report(
            output_path="./reports/zap_report.sarif",
        )
        print(f"SARIF Report: {sarif_report}")

        # Get report as dictionary
        report_dict = await scanner.get_report("json")
        print("\nReport Summary:")
        print(f"  Total Alerts: {report_dict['summary']['total']}")
        print(f"  High: {report_dict['summary']['high']}")
        print(f"  Medium: {report_dict['summary']['medium']}")
        print(f"  Low: {report_dict['summary']['low']}")


# ═══════════════════════════════════════════════════════════════
# Example 8: Using Orchestrator
# ═══════════════════════════════════════════════════════════════


async def example_orchestrator():
    """Using the ZAP Orchestrator"""
    print("\n" + "=" * 60)
    print("Example 8: ZAP Orchestrator")
    print("=" * 60)

    # Configure orchestrator
    config = ZAPOrchestratorConfig(
        api_url="http://localhost:8080",
        api_key=None,
        auto_start_daemon=False,  # Assume ZAP is already running
        max_concurrent_scans=2,
        report_output_dir="./reports/zap",
        default_report_formats=["json", "html"],
    )

    orchestrator = ZAPOrchestrator(config)
    await orchestrator.initialize()

    try:
        # Queue multiple scans
        task1 = await orchestrator.scan(
            target="http://target1.example.com",
            scan_type="spider",
            priority=1,
        )
        print(f"Queued spider scan: {task1}")

        task2 = await orchestrator.scan(
            target="http://target2.example.com",
            scan_type="full",
            config={"scan_policy": "SQL Injection"},
            priority=2,
        )
        print(f"Queued full scan: {task2}")

        # Wait for completion
        completed = await orchestrator.wait_for_completion(
            task_ids=[task1, task2],
            timeout=1800,
        )

        print(f"\nCompleted {len(completed)} scans:")
        for task_id, task in completed.items():
            if task.result:
                print(f"  {task_id}: {len(task.result.alerts)} alerts")

    finally:
        await orchestrator.shutdown()


# ═══════════════════════════════════════════════════════════════
# Example 9: Batch Scanning
# ═══════════════════════════════════════════════════════════════


async def example_batch_scan():
    """Batch scanning multiple targets"""
    print("\n" + "=" * 60)
    print("Example 9: Batch Scanning")
    print("=" * 60)

    config = ZAPOrchestratorConfig(
        api_url="http://localhost:8080",
        auto_start_daemon=False,
        max_concurrent_scans=3,
    )

    orchestrator = ZAPOrchestrator(config)
    await orchestrator.initialize()

    try:
        batch_scanner = ZAPBatchScanner(orchestrator)

        targets = [
            "http://target1.example.com",
            "http://target2.example.com",
            "http://target3.example.com",
        ]

        result = await batch_scanner.scan_targets(
            targets=targets,
            scan_type="spider",
            max_concurrent=3,
        )

        print(f"Batch ID: {result.batch_id}")
        print(f"Total: {result.total_targets}")
        print(f"Completed: {result.completed}")
        print(f"Failed: {result.failed}")
        print(f"Duration: {result.duration:.2f}s")
        print(f"Total Findings: {len(result.aggregate_findings)}")

        # Generate aggregate report
        report_path = batch_scanner.generate_aggregate_report(
            result,
            "./reports/batch_report.json",
        )
        print(f"Aggregate Report: {report_path}")

    finally:
        await orchestrator.shutdown()


# ═══════════════════════════════════════════════════════════════
# Example 10: Scan Pipeline
# ═══════════════════════════════════════════════════════════════


async def example_scan_pipeline():
    """Multi-stage scan pipeline"""
    print("\n" + "=" * 60)
    print("Example 10: Scan Pipeline")
    print("=" * 60)

    config = ZAPOrchestratorConfig(
        api_url="http://localhost:8080",
        auto_start_daemon=False,
    )

    orchestrator = ZAPOrchestrator(config)
    await orchestrator.initialize()

    try:
        pipeline = ZAPScanPipeline(orchestrator)

        # Build pipeline
        pipeline.add_stage(
            name="Spider Crawl",
            scan_type="spider",
            config={"timeout": 300},
        )
        pipeline.add_stage(
            name="AJAX Spider",
            scan_type="ajax",
            config={"timeout": 300},
        )
        pipeline.add_stage(
            name="Active Scan",
            scan_type="active",
            config={
                "scan_policy": "Default Policy",
                "timeout": 600,
            },
        )

        # Execute pipeline
        result = await pipeline.execute(
            target="http://target.example.com",
            base_config={"stop_on_failure": False},
        )

        print(f"Pipeline Success: {result['success']}")
        print(f"Stages executed: {len(result['stages'])}")

        for stage in result["stages"]:
            print(f"  {stage['name']}: {stage.get('alerts_count', 0)} alerts")

    finally:
        await orchestrator.shutdown()


# ═══════════════════════════════════════════════════════════════
# Example 11: Quick Scan Helper
# ═══════════════════════════════════════════════════════════════


async def example_quick_scan_helper():
    """Using the quick_scan helper function"""
    print("\n" + "=" * 60)
    print("Example 11: Quick Scan Helper")
    print("=" * 60)

    result = await quick_scan(
        target="http://scanme.nmap.org",
        api_url="http://localhost:8080",
    )

    print("Quick Scan Complete!")
    print(f"Success: {result.success}")
    print(f"Alerts: {len(result.alerts)}")
    print(f"High Risk: {len(result.get_high_risk())}")


# ═══════════════════════════════════════════════════════════════
# Example 12: Docker Management
# ═══════════════════════════════════════════════════════════════


async def example_docker_management():
    """Managing ZAP via Docker"""
    print("\n" + "=" * 60)
    print("Example 12: Docker Management")
    print("=" * 60)

    docker = ZAPDockerManager()

    # Start container
    container_id = await docker.start_container(
        name="zap_scan_session",
        port=8080,
        api_key="my-secret-key",
        network="zen_network",
    )
    print(f"Started container: {container_id}")

    # Check if running
    is_running = docker.is_running("zap_scan_session")
    print(f"Container running: {is_running}")

    # Use the container
    scanner = ZAPScanner(
        target="http://target.example.com",
        api_url="http://localhost:8080",
        api_key="my-secret-key",
    )

    result = await scanner.scan()
    print(f"Scan complete: {len(result.alerts)} alerts")

    # Stop container
    await docker.stop_container("zap_scan_session")
    print("Container stopped")


# ═══════════════════════════════════════════════════════════════
# Example 13: Custom Scan Policy
# ═══════════════════════════════════════════════════════════════


async def example_custom_policy():
    """Using specific scan policies"""
    print("\n" + "=" * 60)
    print("Example 13: Custom Scan Policy")
    print("=" * 60)

    policies = [
        ZAPScanPolicy.SQL_INJECTION,
        ZAPScanPolicy.XSS,
        ZAPScanPolicy.COMMAND_INJECTION,
    ]

    for policy in policies:
        print(f"\nScanning with policy: {policy.value}")

        scanner = ZAPScanner(
            target="http://target.example.com",
            api_url="http://localhost:8080",
            options={
                "active_scan": True,
                "scan_policy": policy.value,
                "scan_timeout": 300,
            },
        )

        result = await scanner.active_scan()
        print(f"  Alerts: {result.alerts_found}")


# ═══════════════════════════════════════════════════════════════
# Example 14: Alert Filtering and Export
# ═══════════════════════════════════════════════════════════════


async def example_alert_filtering():
    """Filter and export alerts"""
    print("\n" + "=" * 60)
    print("Example 14: Alert Filtering")
    print("=" * 60)

    scanner = ZAPScanner(
        target="http://target.example.com",
        api_url="http://localhost:8080",
    )

    # Run scan
    result = await scanner.scan()

    # Filter alerts
    high_alerts = result.get_high_risk()
    medium_alerts = result.get_medium_risk()

    # Export to JSON
    export_data = {
        "scan_date": datetime.now(timezone.utc).isoformat(),
        "target": result.target,
        "summary": {
            "total": len(result.alerts),
            "high": len(high_alerts),
            "medium": len(medium_alerts),
            "low": len(result.get_low_risk()),
        },
        "high_risk_findings": [
            {
                "name": a.name,
                "url": a.url,
                "cwe": a.cwe_id,
                "evidence": a.evidence,
            }
            for a in high_alerts
        ],
    }

    with open("./reports/filtered_alerts.json", "w") as f:
        json.dump(export_data, f, indent=2)

    print(f"Exported {len(high_alerts)} high-risk findings")


# ═══════════════════════════════════════════════════════════════
# Main Runner
# ═══════════════════════════════════════════════════════════════


async def run_all_examples():
    """Run all examples"""
    examples = [
        ("Basic Scan", example_basic_scan),
        ("Spider Only", example_spider_only),
        # Note: The following require actual targets
        # ("Authenticated", example_authenticated_scan),
        # ("JWT Scan", example_jwt_scan),
        # ("OpenAPI", example_openapi_scan),
        # ("GraphQL", example_graphql_scan),
        ("Reports", example_report_generation),
        # ("Orchestrator", example_orchestrator),
        # ("Batch", example_batch_scan),
        # ("Pipeline", example_scan_pipeline),
        # ("Quick Helper", example_quick_scan_helper),
        # ("Docker", example_docker_management),
        # ("Custom Policy", example_custom_policy),
        # ("Alert Filtering", example_alert_filtering),
    ]

    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\nError in {name}: {e}")


if __name__ == "__main__":
    print("OWASP ZAP Integration Examples for Zen-AI-Pentest")
    print("=" * 60)

    # Run examples
    asyncio.run(run_all_examples())

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
