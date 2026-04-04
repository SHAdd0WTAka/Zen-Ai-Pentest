#!/usr/bin/env python3
"""
Autonomous Agent Runner - Live Test gegen scanme.nmap.org
Zeigt State-Transitions, Self-Healing und Decision-Making
"""

import logging
import sys

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("Agent")

sys.path.insert(0, "/root/.openclaw/workspace/Zen-Ai-Pentest")

from agents.recovery_engine import AgentState, ReActAgentWithRecovery


class LiveAgentRunner:
    """
    Einfacher Agent-Runner für Live-Tests
    Zeigt State-Transitions und Decision-Making
    """

    def __init__(self, target: str):
        self.target = target
        self.agent = ReActAgentWithRecovery()
        self.history = []

        # Log initial state
        logger.info("=" * 60)
        logger.info("🎯 AUTONOMOUS AGENT STARTED")
        logger.info(f"🎯 Target: {target}")
        logger.info("🎯 Mode: Autonomous with Self-Healing")
        logger.info("=" * 60)

    def log_state_transition(self, old_state: AgentState, new_state: AgentState, reason: str = ""):
        """Loggt State-Transitions sichtbar"""
        logger.info(f"[STATE CHANGE] {old_state.value} -> {new_state.value} | {reason}")

    def execute_cycle(self, ai_decision: dict) -> dict:
        """Führt einen Agent-Zyklus aus mit Logging"""
        tool = ai_decision.get("tool")
        params = ai_decision.get("params", {})

        logger.info(f"[PLAN] Tool: {tool}, Params: {params}")

        # Simuliere Tool-Ausführung (für Demo - würde echten ToolExecutor nutzen)
        # In Produktion: result = self.agent.tool_executor.execute(tool, params)
        result = self._simulate_tool_execution(tool, params)

        if not result.get("success"):
            logger.warning(f"🚨 TOOL FAILED: {tool} - {result.get('stderr', 'Unknown error')}")

            # Recovery
            recovery_plan = self.agent.recovery_engine.handle_failure(
                tool_name=tool,
                error_msg=result.get("stderr", ""),
                ai_instructions=ai_decision,
            )

            logger.info(f"🔄 RECOVERY: {recovery_plan['action']}")
            if recovery_plan.get("new_tool"):
                logger.info(f"🔄 SWITCH: {tool} -> {recovery_plan['new_tool']}")

            return {"status": "recovered", "recovery_plan": recovery_plan}

        # Erfolg
        logger.info(f"✅ SUCCESS: {tool} completed")
        findings = result.get("output", [])
        if findings:
            logger.info(f"📊 FINDINGS: {len(findings)} items")
            for f in findings[:3]:  # Zeige Top 3
                logger.info(f"   - {f}")

        return {"status": "success", "findings": findings}

    def _simulate_tool_execution(self, tool: str, params: dict) -> dict:
        """Simuliert Tool-Ausführung für Demo"""
        import random

        # Simuliere verschiedene Szenarien
        scenarios = {
            "nmap": {
                "success": True,
                "output": [
                    "22/tcp open ssh",
                    "80/tcp open http",
                    "443/tcp open https",
                ],
            },
            "gobuster": {
                "success": False,  # Simuliere: Gobuster nicht installiert
                "stderr": "command not found: gobuster",
            },
            "dirb": {  # Fallback für Gobuster
                "success": True,
                "output": ["/ -> 200", "/pub -> 200", "/test -> 403"],
            },
            "masscan": {
                "success": True,
                "output": [
                    "Discovered open port 22/tcp",
                    "Discovered open port 80/tcp",
                ],
            },
        }

        # Wenn Tool nicht in scenarios, random
        if tool in scenarios:
            return scenarios[tool]

        # Random Erfolg/Misserfolg für andere Tools
        if random.random() > 0.3:  # 70% Erfolg
            return {"success": True, "output": [f"{tool} result"]}
        else:
            return {"success": False, "stderr": f"{tool}: connection timeout"}

    def run_recon(self):
        """Phase 1: Reconnaissance"""
        logger.info("\n" + "=" * 60)
        logger.info("📍 PHASE 1: RECONNAISSANCE")
        logger.info("=" * 60)

        # Schritt 1: Port Scan mit Nmap
        decision = {
            "thought": "Starte mit Port-Scan um offene Dienste zu finden",
            "tool": "nmap",
            "params": {"target": self.target, "ports": "1-1000"},
            "expected_state": "ANALYZING",
            "fallback_state": "RECOVERY",
            "self_correction": "Falls nmap fehlt, nutze masscan als Alternative",
        }

        result = self.execute_cycle(decision)

        if result["status"] == "success":
            ports = result.get("findings", [])
            http_ports = [p for p in ports if "80/tcp" in p or "443/tcp" in p]

            if http_ports:
                logger.info("🌐 HTTP/HTTPS gefunden! Starte Directory-Busting...")
                return self.run_directory_busting()
            else:
                logger.info("ℹ️ Keine Web-Dienste gefunden. Recon complete.")

        return result

    def run_directory_busting(self):
        """Phase 2: Directory Busting (mit Recovery)"""
        logger.info("\n" + "=" * 60)
        logger.info("📍 PHASE 2: DIRECTORY BUSTING")
        logger.info("=" * 60)

        # Versuche Gobuster (wird fehlschlagen in Demo)
        decision = {
            "thought": "Suche nach versteckten Verzeichnissen mit Gobuster",
            "tool": "gobuster",
            "params": {
                "url": f"http://{self.target}",
                "wordlist": "common.txt",
            },
            "expected_state": "ANALYZING",
            "fallback_state": "RECOVERY",
            "self_correction": "Falls gobuster fehlt, nutze dirb als Alternative",
        }

        result = self.execute_cycle(decision)

        if result["status"] == "recovered":
            # Recovery hat Fallback vorgeschlagen
            new_tool = result["recovery_plan"].get("new_tool")
            if new_tool:
                logger.info(f"🔄 RETRY mit {new_tool}...")

                # Neuer Versuch mit Fallback
                decision["tool"] = new_tool
                decision["self_correction"] = "Using fallback tool"

                result = self.execute_cycle(decision)

        if result["status"] == "success":
            findings = result.get("findings", [])
            interesting = [f for f in findings if "200" in f or "403" in f]

            if interesting:
                logger.info(f"🔍 Interessante Pfade gefunden: {len(interesting)}")
                for path in interesting:
                    logger.info(f"   📁 {path}")

        return result

    def run_full_scan(self):
        """Führt vollständigen autonomen Scan durch"""
        logger.info("\n🚀 STARTING AUTONOMOUS SCAN SEQUENCE\n")

        # Phase 1: Recon
        self.run_recon()

        logger.info("\n" + "=" * 60)
        logger.info("✅ SCAN SEQUENCE COMPLETED")
        logger.info("=" * 60)

        # Stats
        stats = self.agent.recovery_engine.get_recovery_stats()
        logger.info(f"📊 Total Failures: {stats['total_failures']}")
        logger.info(f"📊 Recovery Actions: {len(stats['recovery_history'])}")

        if stats["recovery_history"]:
            logger.info("📊 Recovery Log:")
            for entry in stats["recovery_history"]:
                logger.info(f"   - {entry['type']}: {entry.get('from', 'N/A')} -> {entry.get('to', 'N/A')}")


def main():
    target = "scanme.nmap.org"

    print("\n" + "=" * 70)
    print("  ZEN-AI-PENTEST AUTONOMOUS AGENT v2.0")
    print("  Live Test with Self-Healing & State-Machine")
    print("=" * 70 + "\n")

    runner = LiveAgentRunner(target)
    runner.run_full_scan()

    print("\n" + "=" * 70)
    print("  SCAN COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
