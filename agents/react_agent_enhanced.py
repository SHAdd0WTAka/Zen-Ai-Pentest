"""
Enhanced ReAct Agent Loop mit Plan-and-Execute + Reflection
Issue #18: [2026-Q1] ReAct / Plan-and-Execute Reasoning Loop

Verbessert den bestehenden ReAct Agent um:
1. Plan Phase - Explizite Planung vor Ausführung
2. Reflection Phase - Analyse der Ergebnisse
3. Memory Integration - Langfristiges Lernen
4. Better Error Recovery - Robuste Fehlerbehandlung
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, add_messages

from ..core.llm_backend import LLMBackend
from ..database.cve_database import CVEDatabase
from ..tools.ffuf_integration import FfufTool
from ..tools.nmap_integration import NmapTool
from ..tools.nuclei_integration import NucleiTool
from ..tools.tool_registry import ToolCategory, ToolRegistry, ToolSafetyLevel

logger = logging.getLogger(__name__)


class PlanStep(TypedDict):
    """Einzelner Schritt im Plan"""

    step_number: int
    action: str
    tool: Optional[str]
    expected_outcome: str
    completed: bool
    result: Optional[str]


class AgentStateEnhanced(TypedDict):
    """Erweiterter State für den ReAct Loop"""

    messages: Annotated[List[BaseMessage], add_messages]
    findings: List[dict]
    target: str
    objective: str
    iteration: int
    max_iterations: int
    status: Literal[
        "planning",
        "executing",
        "observing",
        "reflecting",
        "completed",
        "error",
    ]

    # Neue Felder für Plan-and-Execute
    plan: List[PlanStep]
    current_step_index: int
    reflections: List[dict]
    memory_context: Dict[str, Any]  # Langfristiges Gedächtnis

    # Fehlerbehandlung
    error_count: int
    max_errors: int
    last_error: Optional[str]


@dataclass
class ReActAgentConfigEnhanced:
    """Erweiterte Konfiguration"""

    max_iterations: int = 10
    max_plan_steps: int = 5
    enable_sandbox: bool = True
    auto_approve_dangerous: bool = False
    use_human_in_the_loop: bool = True
    llm_model: str = "gpt-4o"
    enable_reflection: bool = True
    enable_planning: bool = True
    memory_enabled: bool = True


class ReActAgentEnhanced:
    """
    Enhanced ReAct Agent mit Plan-and-Execute + Reflection

    Phase 1: PLAN - LLM erstellt einen strukturierten Plan
    Phase 2: EXECUTE - Führt Plan-Schritte aus (Tools)
    Phase 3: OBSERVE - Sammelt Ergebnisse
    Phase 4: REFLECT - Bewertet Fortschritt und passt Plan an
    Phase 5: LOOP oder END
    """

    def __init__(self, config: ReActAgentConfigEnhanced = None):
        self.config = config or ReActAgentConfigEnhanced()
        self.llm = LLMBackend(model=self.config.llm_model)
        self.cve_db = CVEDatabase()
        self.registry = ToolRegistry()

        # Tools in Registry laden
        self._initialize_tools()

        # Hole Tools aus Registry
        self.tools = self.registry.get_all_tools()
        self.tools_by_name = {t.name: t for t in self.tools}

        # LangGraph Workflow
        self.graph = self._build_graph()

        # Memory für langfristiges Lernen
        self.session_memory: Dict[str, Any] = {}

        logger.info(
            f"Enhanced ReActAgent initialisiert mit {len(self.tools)} Tools aus Registry"
        )

    def _initialize_tools(self):
        """Initialisiert Pentest-Tools in der Registry"""

        @tool
        def scan_ports(target: str, ports: str = "top-1000") -> str:
            """Scannt Ports auf dem Target mit Nmap"""
            nmap = NmapTool()
            result = nmap.scan(target, ports)
            return json.dumps(result, indent=2)

        self.registry.register(
            tool=scan_ports,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["port", "scan", "nmap"],
        )

        @tool
        def scan_vulnerabilities(
            target: str, templates: str = "critical,high"
        ) -> str:
            """Scannt nach CVEs mit Nuclei"""
            nuclei = NucleiTool()
            result = nuclei.scan(target, severity=templates)
            return json.dumps(result, indent=2)

        self.registry.register(
            tool=scan_vulnerabilities,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["vulnerability", "scan", "nuclei", "cve"],
        )

        @tool
        def enumerate_directories(
            target: str, wordlist: str = "common.txt"
        ) -> str:
            """Enumerate directories mit ffuf"""
            ffuf = FfufTool()
            result = ffuf.directory_bruteforce(target, wordlist)
            return json.dumps(result, indent=2)

        self.registry.register(
            tool=enumerate_directories,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["directory", "enumeration", "ffuf", "fuzzing"],
        )

        @tool
        def lookup_cve(cve_id: str) -> str:
            """Sucht CVE-Details in der Datenbank"""
            cve = self.cve_db.get_cve(cve_id)
            if cve:
                return json.dumps(
                    {
                        "id": cve.id,
                        "severity": cve.severity,
                        "cvss": cve.cvss_score,
                        "description": cve.description,
                        "epss": cve.epss_score,
                    },
                    indent=2,
                )
            return f"CVE {cve_id} nicht gefunden"

        self.registry.register(
            tool=lookup_cve,
            category=ToolCategory.UTILITY,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["cve", "lookup", "database"],
        )

        @tool
        def validate_exploit(cve_id: str, target: str) -> str:
            """Validiert ob ein Exploit auf dem Target funktioniert (read-only)"""
            return f"Exploit-Validierung für {cve_id} auf {target}: Noch nicht implementiert"

        self.registry.register(
            tool=validate_exploit,
            category=ToolCategory.EXPLOITATION,
            safety_level=ToolSafetyLevel.DANGEROUS,
            requires_approval=True,
            tags=["exploit", "validation", "dangerous"],
        )

    def _build_graph(self) -> StateGraph:
        """Baut den erweiterten LangGraph Workflow"""

        # === PHASE 1: PLAN ===
        def plan_node(state: AgentStateEnhanced) -> AgentStateEnhanced:
            """Plan Node: Erstellt einen strukturierten Plan"""
            logger.info(f"[PLAN] Iteration {state['iteration']}")

            if not self.config.enable_planning:
                # Skip planning, direkt zu execution
                return {**state, "status": "executing"}

            system_prompt = """Du bist ein strategischer Pentest-Planer.

Analysiere das Ziel und erstelle einen strukturierten Plan mit maximal 5 Schritten.

Für jeden Schritt definiere:
1. action: Was soll gemacht werden?
2. tool: Welches Tool wird genutzt (scan_ports, scan_vulnerabilities, enumerate_directories, lookup_cve, validate_exploit)?
3. expected_outcome: Was erwarten wir als Ergebnis?

Beispiel-Plan:
{
  "plan": [
    {"step": 1, "action": "Port Scan", "tool": "scan_ports", "expected_outcome": "Offene Ports identifizieren"},
    {"step": 2, "action": "Vulnerability Scan", "tool": "scan_vulnerabilities", "expected_outcome": "CVEs finden"}
  ]
}

WICHTIG:
- Sei spezifisch bei den Tools
- Berücksichtige vorherige Ergebnisse
- Passe den Plan an wenn nötig"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=(
                        f"Ziel: {state['target']}\n"
                        f"Aufgabe: {state['objective']}\n"
                        f"Vorherige Ergebnisse: {len(state['findings'])} findings"
                    )
                ),
            ]

            # LLM generiert Plan
            response = self.llm.invoke(messages)

            # Parse Plan aus Response
            try:
                plan_data = self._parse_plan_from_response(response.content)
                plan = [
                    PlanStep(
                        step_number=i + 1,
                        action=step["action"],
                        tool=step.get("tool"),
                        expected_outcome=step["expected_outcome"],
                        completed=False,
                        result=None,
                    )
                    for i, step in enumerate(plan_data.get("plan", []))
                ]
            except Exception as e:
                logger.error(f"Fehler beim Parsen des Plans: {e}")
                plan = []

            return {
                **state,
                "plan": plan,
                "current_step_index": 0,
                "status": "executing" if plan else "completed",
                "messages": state["messages"]
                + [AIMessage(content=f"Plan erstellt: {len(plan)} Schritte")],
            }

        # === PHASE 2: EXECUTE ===
        def execute_node(state: AgentStateEnhanced) -> AgentStateEnhanced:
            """Execute Node: Führt aktuellen Plan-Schritt aus"""
            logger.info(
                f"[EXECUTE] Schritt {state['current_step_index'] + 1}/{len(state['plan'])}"
            )

            # Aktuellen Schritt holen
            if not state["plan"] or state["current_step_index"] >= len(
                state["plan"]
            ):
                return {**state, "status": "completed"}

            current_step = state["plan"][state["current_step_index"]]

            # Wenn kein Tool nötig, überspringen
            if not current_step.get("tool"):
                return {
                    **state,
                    "current_step_index": state["current_step_index"] + 1,
                    "status": "observing",
                }

            tool_name = current_step["tool"]

            # Safety Check
            if (
                self._is_dangerous_tool(tool_name)
                and self.config.use_human_in_the_loop
            ):
                if not self.config.auto_approve_dangerous:
                    result = f"[PENDING APPROVAL] Tool {tool_name} erfordert manuelle Freigabe"
                    return {
                        **state,
                        "status": "reflecting",
                        "messages": state["messages"]
                        + [
                            ToolMessage(content=result, tool_call_id="pending")
                        ],
                    }

            # Tool ausführen
            try:
                tool_func = self.tools_by_name.get(tool_name)
                if tool_func:
                    # Args aus dem Kontext bauen
                    args = {"target": state["target"]}
                    result = tool_func.invoke(args)

                    # Schritt aktualisieren
                    state["plan"][state["current_step_index"]][
                        "result"
                    ] = result
                    state["plan"][state["current_step_index"]][
                        "completed"
                    ] = True

                    # Finding speichern
                    finding = {
                        "tool": tool_name,
                        "step": state["current_step_index"] + 1,
                        "result": result,
                        "timestamp": datetime.now().isoformat(),
                    }

                    return {
                        **state,
                        "findings": state["findings"] + [finding],
                        "status": "observing",
                        "messages": state["messages"]
                        + [
                            ToolMessage(
                                content=result[:500],
                                tool_call_id=f"step_{state['current_step_index']}",
                            )
                        ],
                    }
                else:
                    error = f"Tool {tool_name} nicht gefunden"
                    return {
                        **state,
                        "status": "reflecting",
                        "last_error": error,
                        "error_count": state.get("error_count", 0) + 1,
                    }

            except Exception as e:
                error = f"Fehler bei {tool_name}: {str(e)}"
                logger.error(error)
                return {
                    **state,
                    "status": "reflecting",
                    "last_error": error,
                    "error_count": state.get("error_count", 0) + 1,
                }

        # === PHASE 3: OBSERVE ===
        def observe_node(state: AgentStateEnhanced) -> AgentStateEnhanced:
            """Observe Node: Analysiert das Ergebnis"""
            logger.info("[OBSERVE] Analysiere Ergebnisse")

            current_step = state["plan"][state["current_step_index"]]
            result = current_step.get("result", "")

            # LLM analysiert das Ergebnis
            system_prompt = """Du bist ein Pentest-Analyst.

Analysiere das Ergebnis des letzten Schritts:
- War es erfolgreich?
- Gibt es kritische Findings?
- Soll der Plan angepasst werden?

Antworte in 2-3 Sätzen."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=f"Schritt: {current_step['action']}\nErgebnis: {result[:1000]}"
                ),
            ]

            response = self.llm.invoke(messages)

            return {
                **state,
                "status": "reflecting",
                "messages": state["messages"]
                + [AIMessage(content=f"Observation: {response.content}")],
            }

        # === PHASE 4: REFLECT ===
        def reflect_node(state: AgentStateEnhanced) -> AgentStateEnhanced:
            """Reflect Node: Bewertet Fortschritt und entscheidet weiteres Vorgehen"""
            logger.info("[REFLECT] Bewerte Fortschritt")

            if not self.config.enable_reflection:
                return self._advance_or_complete(state)

            # Prüfe Fehler
            if state.get("error_count", 0) >= state.get("max_errors", 3):
                return {
                    **state,
                    "status": "error",
                    "messages": state["messages"]
                    + [AIMessage(content="Zu viele Fehler - breche ab.")],
                }

            # Prüfe Iterations-Limit
            if state["iteration"] >= state["max_iterations"]:
                return {
                    **state,
                    "status": "completed",
                    "messages": state["messages"]
                    + [AIMessage(content="Maximale Iterationen erreicht.")],
                }

            # Reflection mit LLM
            system_prompt = """Du bist ein strategischer Berater für Pentests.

Bewerte den aktuellen Stand:
1. Sind wir auf dem richtigen Weg?
2. Soll der Plan angepasst werden?
3. Brauchen wir weitere Iterationen?

Antworte mit einer klaren Empfehlung."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=(
                        f"Plan-Fortschritt: {state['current_step_index'] + 1}/{len(state['plan'])}\n"
                        f"Findings: {len(state['findings'])}"
                    )
                ),
            ]

            response = self.llm.invoke(messages)

            # Speichere Reflection
            reflection = {
                "iteration": state["iteration"],
                "timestamp": datetime.now().isoformat(),
                "analysis": response.content,
                "findings_count": len(state["findings"]),
            }

            return self._advance_or_complete(
                {
                    **state,
                    "reflections": state.get("reflections", []) + [reflection],
                    "messages": state["messages"]
                    + [AIMessage(content=f"Reflection: {response.content}")],
                }
            )

        # Hilfsfunktion für State Transition
        def _advance_or_complete(
            state: AgentStateEnhanced,
        ) -> AgentStateEnhanced:
            """Entscheidet ob weiter oder fertig"""
            next_index = state["current_step_index"] + 1

            if next_index >= len(state["plan"]):
                # Plan ist komplett - neue Iteration oder fertig?
                if state["iteration"] < state["max_iterations"] - 1:
                    # Neue Iteration mit neuem Plan
                    return {
                        **state,
                        "iteration": state["iteration"] + 1,
                        "current_step_index": 0,
                        "status": "planning",
                    }
                else:
                    return {**state, "status": "completed"}
            else:
                # Nächster Schritt
                return {
                    **state,
                    "current_step_index": next_index,
                    "status": "executing",
                }

        # === GRAPH BAUEN ===
        workflow = StateGraph(AgentStateEnhanced)

        workflow.add_node("plan", plan_node)
        workflow.add_node("execute", execute_node)
        workflow.add_node("observe", observe_node)
        workflow.add_node("reflect", reflect_node)

        # Entry Point
        workflow.add_edge(START, "plan")

        # Transitions
        workflow.add_edge("plan", "execute")
        workflow.add_edge("execute", "observe")
        workflow.add_edge("observe", "reflect")

        # Conditional from reflect
        workflow.add_conditional_edges(
            "reflect",
            lambda state: state["status"],
            {
                "planning": "plan",
                "executing": "execute",
                "completed": END,
                "error": END,
            },
        )

        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer)

    def _parse_plan_from_response(self, content: str) -> dict:
        """Parst den Plan aus der LLM Response"""
        # Versuche JSON zu extrahieren
        try:
            # Suche nach JSON-Block
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            return json.loads(json_str.strip())
        except Exception:
            # Fallback: manuelles Parsen
            logger.warning("Konnte Plan nicht als JSON parsen, nutze Fallback")
            return {
                "plan": [
                    {
                        "action": "Port Scan",
                        "tool": "scan_ports",
                        "expected_outcome": "Offene Ports finden",
                    },
                    {
                        "action": "Vulnerability Scan",
                        "tool": "scan_vulnerabilities",
                        "expected_outcome": "CVEs identifizieren",
                    },
                ]
            }

    def _is_dangerous_tool(self, tool_name: str) -> bool:
        """Prüft ob ein Tool als gefährlich eingestuft wird"""
        dangerous = ["validate_exploit", "exploit", "sqlmap_exploit"]
        return any(d in tool_name.lower() for d in dangerous)

    def run(self, target: str, objective: str = "comprehensive scan") -> dict:
        """Führt den Enhanced ReAct-Agent aus"""
        initial_state: AgentStateEnhanced = {
            "messages": [HumanMessage(content=f"{objective} on {target}")],
            "findings": [],
            "target": target,
            "objective": objective,
            "iteration": 0,
            "max_iterations": self.config.max_iterations,
            "status": "planning",
            "plan": [],
            "current_step_index": 0,
            "reflections": [],
            "memory_context": {},
            "error_count": 0,
            "max_errors": 3,
            "last_error": None,
        }

        logger.info(f"Starte Enhanced ReAct-Agent für {target}")

        result = self.graph.invoke(
            initial_state,
            config={
                "configurable": {
                    "thread_id": f"pentest_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
            },
        )

        logger.info(
            f"Agent beendet nach {result['iteration']} Iterationen, {len(result['findings'])} findings"
        )

        return {
            "findings": result["findings"],
            "plan": result["plan"],
            "reflections": result["reflections"],
            "iterations": result["iteration"],
            "status": result["status"],
            "target": target,
            "objective": objective,
        }

    def generate_report(self, result: dict) -> str:
        """Generiert einen detaillierten Report"""
        report = []
        report.append("=" * 70)
        report.append("ZEN-AI-PENTEST REPORT (Enhanced ReAct)")
        report.append("=" * 70)
        report.append(f"\nTarget: {result['target']}")
        report.append(f"Objective: {result['objective']}")
        report.append(f"Status: {result['status']}")
        report.append(f"Iterations: {result['iterations']}")
        report.append("")

        # Plan
        if result.get("plan"):
            report.append("EXECUTION PLAN:")
            report.append("-" * 70)
            for step in result["plan"]:
                status = "✓" if step.get("completed") else "○"
                report.append(
                    f"{status} Step {step['step_number']}: {step['action']}"
                )
                if step.get("result"):
                    report.append(f"    Result: {step['result'][:100]}...")

        # Findings
        report.append("")
        report.append("FINDINGS:")
        report.append("-" * 70)
        for i, finding in enumerate(result["findings"], 1):
            report.append(f"\n{i}. {finding['tool']} (Step {finding['step']})")
            report.append(f"   {finding['result'][:200]}...")

        # Reflections
        if result.get("reflections"):
            report.append("")
            report.append("REFLECTIONS:")
            report.append("-" * 70)
            for ref in result["reflections"]:
                report.append(f"\nIteration {ref['iteration']}:")
                report.append(f"  {ref['analysis'][:200]}...")

        report.append("")
        report.append("=" * 70)

        return "\n".join(report)


# Singleton
_default_enhanced_agent = None


def get_enhanced_agent(
    config: ReActAgentConfigEnhanced = None,
) -> ReActAgentEnhanced:
    """Gibt die default Enhanced Agent-Instanz zurück"""
    global _default_enhanced_agent
    if _default_enhanced_agent is None or config is not None:
        _default_enhanced_agent = ReActAgentEnhanced(config)
    return _default_enhanced_agent


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    config = ReActAgentConfigEnhanced(
        max_iterations=3, enable_planning=True, enable_reflection=True
    )

    agent = ReActAgentEnhanced(config)
    result = agent.run(
        "scanme.nmap.org", objective="Port scan and vulnerability assessment"
    )

    print(agent.generate_report(result))
