"""
Beispiel: ReAct Agent für Zen-AI-Pentest

Dieses Beispiel zeigt, wie der autonome Agent für verschiedene
Pentest-Szenarien verwendet wird.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.react_agent import ReActAgent, ReActAgentConfig


def example_1_basic_scan():
    """
    Beispiel 1: Basis Port Scan
    """
    print("=" * 70)
    print("BEISPIEL 1: Basic Port Scan")
    print("=" * 70)
    print()

    # Agent konfigurieren
    config = ReActAgentConfig(max_iterations=3, enable_sandbox=True, auto_approve_dangerous=False)

    agent = ReActAgent(config)

    # Scan ausführen
    target = "scanme.nmap.org"  # Offizieller Nmap Test-Server
    result = agent.run(target=target, objective="Scan top 100 ports and identify services")

    # Report anzeigen
    print(agent.generate_report(result))
    print()


def example_2_vulnerability_assessment():
    """
    Beispiel 2: Vulnerability Assessment
    """
    print("=" * 70)
    print("BEISPIEL 2: Vulnerability Assessment")
    print("=" * 70)
    print()

    config = ReActAgentConfig(
        max_iterations=5,
        enable_sandbox=True,
        use_human_in_the_loop=True,  # Für gefährliche Aktionen
    )

    agent = ReActAgent(config)

    target = "testphp.vulnweb.com"  # Offizieller Acunetix Test-Server
    result = agent.run(target=target, objective="Find vulnerabilities (CVEs) and misconfigurations")

    print(agent.generate_report(result))
    print()


def example_3_full_assessment():
    """
    Beispiel 3: Vollständige Assessment (Recon -> Scan -> Exploit-Check)
    """
    print("=" * 70)
    print("BEISPIEL 3: Full Assessment mit ReAct Loop")
    print("=" * 70)
    print()

    config = ReActAgentConfig(max_iterations=10, enable_sandbox=True, auto_approve_dangerous=False, llm_model="gpt-4o")

    agent = ReActAgent(config)

    target = "example.com"
    result = agent.run(
        target=target,
        objective="""
        Comprehensive penetration test:
        1. Port scan all ports
        2. Directory enumeration
        3. Vulnerability scanning
        4. CVE lookup for found services
        5. Risk assessment
        """,
    )

    print(agent.generate_report(result))
    print()

    # Detaillierte Findings
    print("DETAILED FINDINGS:")
    print("-" * 70)
    for finding in result["findings"]:
        print(f"\nTool: {finding['tool']}")
        print(f"Iteration: {finding['iteration']}")
        print(f"Result: {finding['result'][:300]}...")


def example_4_interactive_mode():
    """
    Beispiel 4: Interaktiver Modus mit Human-in-the-Loop
    """
    print("=" * 70)
    print("BEISPIEL 4: Interactive Mode (Human-in-the-Loop)")
    print("=" * 70)
    print()

    config = ReActAgentConfig(
        max_iterations=10,
        use_human_in_the_loop=True,
        auto_approve_dangerous=False,  # Manuelle Freigabe erforderlich
    )

    agent = ReActAgent(config)

    print("Starting interactive session...")
    print("The agent will pause before dangerous actions.")
    print()

    target = input("Enter target (e.g., scanme.nmap.org): ") or "scanme.nmap.org"

    result = agent.run(target=target, objective="Full security assessment with exploit validation")

    print("\n" + agent.generate_report(result))


def example_5_continuous_mode():
    """
    Beispiel 5: Continuous Monitoring Mode
    """
    print("=" * 70)
    print("BEISPIEL 5: Continuous Monitoring")
    print("=" * 70)
    print()

    import time

    import schedule

    config = ReActAgentConfig(max_iterations=5, enable_sandbox=True)

    agent = ReActAgent(config)
    target = "example.com"

    def daily_scan():
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting daily scan...")
        result = agent.run(target=target, objective="Quick vulnerability check")

        # Speichere Ergebnis
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"scan_results_{timestamp}.txt"

        with open(filename, "w") as f:
            f.write(agent.generate_report(result))

        print(f"Results saved to {filename}")

    # Schedule täglicher Scan
    schedule.every().day.at("02:00").do(daily_scan)

    print("Continuous monitoring started.")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ReAct Agent Examples")
    parser.add_argument("example", choices=["1", "2", "3", "4", "5", "all"], help="Which example to run (1-5 or all)")

    args = parser.parse_args()

    examples = {
        "1": example_1_basic_scan,
        "2": example_2_vulnerability_assessment,
        "3": example_3_full_assessment,
        "4": example_4_interactive_mode,
        "5": example_5_continuous_mode,
    }

    if args.example == "all":
        for key in ["1", "2", "3"]:
            examples[key]()
            input("\nPress Enter to continue...")
    else:
        examples[args.example]()
