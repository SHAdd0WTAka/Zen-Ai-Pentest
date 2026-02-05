"""
ReAct Agent Loop für Zen-AI-Pentest
Implementiert Reasoning-Acting-Observing-Reflecting Pattern mit LangGraph

Phase 1: Echter agentischer Loop (2026 Roadmap)
"""

from typing import List, TypedDict, Annotated, Literal
from dataclasses import dataclass
import json
import logging

from langchain_core.tools import tool, BaseTool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.checkpoint.memory import MemorySaver

# Zen-AI-Pentest Imports
from ..core.llm_backend import LLMBackend
from ..tools.nmap_integration import NmapTool
from ..tools.nuclei_integration import NucleiTool
from ..tools.ffuf_integration import FfufTool
from ..database.cve_database import CVEDatabase


logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """
    State für den Agent-Loop.
    Persistiert über Iterationen via LangGraph.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    findings: List[dict]  # Pentest-Ergebnisse strukturiert
    target: str  # Aktuelles Ziel
    iteration: int  # Loop-Counter
    max_iterations: int  # Safety-Limit
    status: Literal["running", "paused", "completed", "error"]


@dataclass
class ReActAgentConfig:
    """Konfiguration für den ReAct-Agenten"""
    max_iterations: int = 10
    enable_sandbox: bool = True
    auto_approve_dangerous: bool = False
    use_human_in_the_loop: bool = True
    llm_model: str = "gpt-4o"


class ReActAgent:
    """
    ReAct Agent für autonomes Pentesting.
    
    Flow:
    1. Reason/Plan -> LLM entscheidet nächsten Schritt
    2. Act -> Führt Tools aus (sandboxed)
    3. Observe -> Sammelt Ergebnisse
    4. Reflect -> Bewertet Fortschritt
    5. Loop oder End
    """
    
    def __init__(self, config: ReActAgentConfig = None):
        self.config = config or ReActAgentConfig()
        self.llm = LLMBackend(model=self.config.llm_model)
        self.cve_db = CVEDatabase()
        
        # Tools initialisieren
        self.tools = self._initialize_tools()
        self.tools_by_name = {t.name: t for t in self.tools}
        
        # LangGraph Workflow
        self.graph = self._build_graph()
        
        logger.info(f"ReActAgent initialisiert mit {len(self.tools)} Tools")
    
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialisiert Pentest-Tools"""
        tools = []
        
        # Port Scanning
        @tool
        def scan_ports(target: str, ports: str = "top-1000") -> str:
            """Scannt Ports auf dem Target mit Nmap"""
            nmap = NmapTool()
            result = nmap.scan(target, ports)
            return json.dumps(result, indent=2)
        
        # Vulnerability Scanning
        @tool  
        def scan_vulnerabilities(target: str, templates: str = "critical,high") -> str:
            """Scannt nach CVEs mit Nuclei"""
            nuclei = NucleiTool()
            result = nuclei.scan(target, severity=templates)
            return json.dumps(result, indent=2)
        
        # Directory Bruteforce
        @tool
        def enumerate_directories(target: str, wordlist: str = "common.txt") -> str:
            """Enumerate directories mit ffuf"""
            ffuf = FfufTool()
            result = ffuf.directory_bruteforce(target, wordlist)
            return json.dumps(result, indent=2)
        
        # CVE Lookup
        @tool
        def lookup_cve(cve_id: str) -> str:
            """Sucht CVE-Details in der Datenbank"""
            cve = self.cve_db.get_cve(cve_id)
            if cve:
                return json.dumps({
                    "id": cve.id,
                    "severity": cve.severity,
                    "cvss": cve.cvss_score,
                    "description": cve.description,
                    "epss": cve.epss_score
                }, indent=2)
            return f"CVE {cve_id} nicht gefunden"
        
        # Exploit Validation
        @tool
        def validate_exploit(cve_id: str, target: str) -> str:
            """Validiert ob ein Exploit auf dem Target funktioniert (read-only)"""
            # TODO: Implementiere sichere Validierung
            return f"Exploit-Validierung für {cve_id} auf {target}: Noch nicht implementiert"
        
        tools = [scan_ports, scan_vulnerabilities, enumerate_directories, 
                lookup_cve, validate_exploit]
        return tools
    
    def _build_graph(self) -> StateGraph:
        """Baut den LangGraph Workflow"""
        
        # LLM mit Tool-Binding
        llm_with_tools = self.llm.bind_tools(self.tools)
        
        # System Prompt
        system_prompt = """Du bist ein autonomer Pentest-Agent für Zen-AI-Pentest.

Deine Aufgabe:
1. Analysiere das Target und plane den Angriff (Reconnaissance)
2. Führe Scans durch (Port, Vulnerability, Directory Enumeration)
3. Analysiere Ergebnisse auf Schwachstellen
4. Erstelle einen strukturierten Report

REGELN:
- Arbeite Schritt für Schritt (Reasoning)
- Nutze Tools für externe Aktionen
- Validiere Ergebnisse (CVSS + EPSS)
- Never execute destructive exploits without explicit approval
- Halte max 10 Iterationen ein

Wenn du fertig bist, gib eine finale Zusammenfassung aus."""

        def agent_node(state: AgentState) -> AgentState:
            """Agent Node: Reason/Plan"""
            # Check iteration limit
            if state["iteration"] >= state["max_iterations"]:
                return {
                    **state,
                    "messages": state["messages"] + [
                        AIMessage(content="Maximale Iterationen erreicht. Beende Scan.")
                    ],
                    "status": "completed"
                }
            
            # Prepare messages
            messages = [SystemMessage(content=system_prompt)] + state["messages"]
            
            # LLM Call
            response = llm_with_tools.invoke(messages)
            
            return {
                **state,
                "messages": [response],
                "iteration": state["iteration"] + 1
            }
        
        def tools_node(state: AgentState) -> AgentState:
            """Tools Node: Act/Observe"""
            last_message = state["messages"][-1]
            
            if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
                return state
            
            tool_messages = []
            new_findings = []
            
            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                args = tool_call["args"]
                tool_id = tool_call["id"]
                
                logger.info(f"Tool-Aufruf: {tool_name} mit Args: {args}")
                
                # Sicherheits-Check
                if self._is_dangerous_tool(tool_name) and self.config.use_human_in_the_loop:
                    if not self.config.auto_approve_dangerous:
                        result = f"[PENDING APPROVAL] Tool {tool_name} erfordert manuelle Freigabe"
                        tool_messages.append(ToolMessage(content=result, tool_call_id=tool_id))
                        continue
                
                # Tool ausführen
                try:
                    tool_func = self.tools_by_name.get(tool_name)
                    if tool_func:
                        result = tool_func.invoke(args)
                        
                        # Finding speichern
                        finding = {
                            "tool": tool_name,
                            "args": args,
                            "result": result,
                            "iteration": state["iteration"]
                        }
                        new_findings.append(finding)
                    else:
                        result = f"Tool {tool_name} nicht gefunden"
                    
                    tool_messages.append(ToolMessage(content=result, tool_call_id=tool_id))
                    
                except Exception as e:
                    error_msg = f"Fehler bei {tool_name}: {str(e)}"
                    logger.error(error_msg)
                    tool_messages.append(ToolMessage(content=error_msg, tool_call_id=tool_id))
            
            return {
                **state,
                "messages": tool_messages,
                "findings": state["findings"] + new_findings
            }
        
        def should_continue(state: AgentState) -> Literal["tools", "agent", "end"]:
            """Conditional Edge: Entscheidet über Loop-Fortsetzung"""
            last_message = state["messages"][-1]
            
            # Wenn fertig (keine Tool-Calls mehr)
            if state.get("status") == "completed":
                return "end"
            
            # Wenn Tools aufgerufen wurden
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tools"
            
            # Wenn Tool-Ergebnisse da sind -> zurück zum Agent
            if isinstance(last_message, ToolMessage):
                return "agent"
            
            # Sonst Ende
            return "end"
        
        # Graph bauen
        workflow = StateGraph(AgentState)
        
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tools_node)
        
        workflow.add_edge(START, "agent")
        
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "agent": "agent",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "tools",
            should_continue,
            {
                "tools": "tools",
                "agent": "agent", 
                "end": END
            }
        )
        
        # Mit Memory für Human-in-the-Loop
        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer)
    
    def _is_dangerous_tool(self, tool_name: str) -> bool:
        """Prüft ob ein Tool als gefährlich eingestuft wird"""
        dangerous = ["validate_exploit", "exploit", "sqlmap_exploit"]
        return any(d in tool_name.lower() for d in dangerous)
    
    def run(self, target: str, objective: str = "comprehensive scan") -> dict:
        """
        Führt den Agent-Loop aus.
        
        Args:
            target: Ziel-URL/IP
            objective: Scan-Ziel (z.B. "port scan", "vulnerability assessment")
            
        Returns:
            dict mit findings, messages, status
        """
        initial_state: AgentState = {
            "messages": [HumanMessage(content=f"{objective} on {target}")],
            "findings": [],
            "target": target,
            "iteration": 0,
            "max_iterations": self.config.max_iterations,
            "status": "running"
        }
        
        logger.info(f"Starte ReAct-Agent für {target}")
        
        # Graph ausführen
        result = self.graph.invoke(
            initial_state,
            config={"configurable": {"thread_id": f"pentest_{target}"}}
        )
        
        logger.info(f"Agent beendet nach {result['iteration']} Iterationen")
        
        return {
            "findings": result["findings"],
            "final_message": result["messages"][-1].content if result["messages"] else "",
            "iterations": result["iteration"],
            "status": result["status"],
            "target": target
        }
    
    def generate_report(self, result: dict) -> str:
        """Generiert einen strukturierten Report aus den Findings"""
        report = []
        report.append("=" * 70)
        report.append("ZEN-AI-PENTEST REPORT")
        report.append("=" * 70)
        report.append(f"\nTarget: {result['target']}")
        report.append(f"Status: {result['status']}")
        report.append(f"Iterations: {result['iterations']}")
        report.append("")
        
        if result['findings']:
            report.append("FINDINGS:")
            report.append("-" * 70)
            for i, finding in enumerate(result['findings'], 1):
                report.append(f"\n{i}. {finding['tool']}")
                report.append(f"   Args: {finding['args']}")
                report.append(f"   Result: {finding['result'][:200]}...")
        else:
            report.append("No findings detected.")
        
        report.append("")
        report.append("=" * 70)
        report.append("FINAL ANALYSIS:")
        report.append("=" * 70)
        report.append(result['final_message'])
        
        return "\n".join(report)


# Singleton-Instanz für einfachen Zugriff
_default_agent = None

def get_agent(config: ReActAgentConfig = None) -> ReActAgent:
    """Gibt die default Agent-Instanz zurück"""
    global _default_agent
    if _default_agent is None or config is not None:
        _default_agent = ReActAgent(config)
    return _default_agent


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    config = ReActAgentConfig(
        max_iterations=5,
        enable_sandbox=True,
        auto_approve_dangerous=False
    )
    
    agent = ReActAgent(config)
    result = agent.run("scanme.nmap.org", objective="Port scan and vulnerability assessment")
    
    print(agent.generate_report(result))
