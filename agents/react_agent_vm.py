"""
ReAct Agent mit VirtualBox VM-Integration

Erweiterung des ReAct Agents für isolierte VM-basierte Pentests.
"""

from typing import List
import logging

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .react_agent import ReActAgent, ReActAgentConfig, AgentState
from ..virtualization.vm_manager import VirtualBoxManager, PentestSandbox


logger = logging.getLogger(__name__)


class VMAgentConfig(ReActAgentConfig):
    """Erweiterte Konfiguration für VM-basierten Agent"""

    use_vm: bool = True
    vm_name: str = "kali-pentest"
    vm_username: str = "kali"
    vm_password: str = "kali"
    auto_restore_snapshot: bool = True


class VMReActAgent(ReActAgent):
    """
    ReAct Agent mit VM-Backend.

    Führt alle Tools in einer isolierten Kali Linux VM aus
    für maximale Sicherheit und Reproduzierbarkeit.
    """

    def __init__(self, config: VMAgentConfig = None):
        self.vm_config = config or VMAgentConfig()

        # VM Manager initialisieren
        if self.vm_config.use_vm:
            self.vbox = VirtualBoxManager()
            self.sandbox = PentestSandbox(self.vbox)
            self.session_id = None

        # Parent init ohne Tools (wir überschreiben sie)
        self.config = self.vm_config
        self.llm = None  # Wird in _build_graph gesetzt
        self.tools = []
        self.graph = self._build_graph_with_vm()

        logger.info(f"VMReActAgent initialisiert (VM: {self.vm_config.vm_name})")

    def _build_graph_with_vm(self):
        """Baut Graph mit VM-Tools"""
        from ..core.llm_backend import LLMBackend

        self.llm = LLMBackend(model=self.config.llm_model)

        # VM-basierte Tools erstellen
        self.tools = self._create_vm_tools()
        llm_with_tools = self.llm.bind_tools(self.tools)

        system_prompt = """Du bist ein autonomer Pentest-Agent mit VM-Integration.

Deine Aufgabe:
1. Führe alle Tests in einer isolierten VM durch
2. Nutze Snapshots für Clean-State-Workflows
3. Dokumentiere alle Findings strukturiert
4. Fasse Ergebnisse am Ende zusammen

SICHERHEIT:
- Alle Scans laufen in der VM 'kali-pentest'
- Snapshots werden automatisch verwaltet
- Keine Auswirkungen auf das Host-System

Wenn fertig, gib eine finale Zusammenfassung."""

        def agent_node(state: AgentState) -> AgentState:
            if state["iteration"] >= state["max_iterations"]:
                return {
                    **state,
                    "messages": state["messages"] + [AIMessage(content="Maximale Iterationen erreicht.")],
                    "status": "completed",
                }

            messages = [SystemMessage(content=system_prompt)] + state["messages"]
            response = llm_with_tools.invoke(messages)

            return {**state, "messages": [response], "iteration": state["iteration"] + 1}

        def tools_node(state: AgentState) -> AgentState:
            last_message = state["messages"][-1]

            if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
                return state

            tool_messages = []
            new_findings = []

            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                args = tool_call["args"]
                tool_id = tool_call["id"]

                logger.info(f"VM-Tool-Aufruf: {tool_name}")

                try:
                    tool_func = {t.name: t for t in self.tools}.get(tool_name)
                    if tool_func:
                        result = tool_func.invoke(args)
                        tool_messages.append(ToolMessage(content=result, tool_call_id=tool_id))
                        new_findings.append({"tool": tool_name, "args": args, "result": result})
                    else:
                        tool_messages.append(ToolMessage(content=f"Tool {tool_name} nicht gefunden", tool_call_id=tool_id))
                except Exception as e:
                    error_msg = f"VM-Tool-Fehler: {str(e)}"
                    logger.error(error_msg)
                    tool_messages.append(ToolMessage(content=error_msg, tool_call_id=tool_id))

            return {**state, "messages": tool_messages, "findings": state["findings"] + new_findings}

        def should_continue(state: AgentState):
            last_message = state["messages"][-1]

            if state.get("status") == "completed":
                return "end"

            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"

            if isinstance(last_message, ToolMessage):
                return "agent"

            return "end"

        workflow = StateGraph(AgentState)
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tools_node)
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "agent": "agent", "end": END})
        workflow.add_conditional_edges("tools", should_continue, {"tools": "tools", "agent": "agent", "end": END})

        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer)

    def _create_vm_tools(self) -> List:
        """Erstellt VM-basierte Tools"""
        from langchain_core.tools import tool

        @tool
        def vm_nmap_scan(target: str, ports: str = "top-100") -> str:
            """Scannt Ports in VM mit Nmap"""
            if not self.session_id:
                return "Keine aktive Session"

            port_arg = "--top-ports 100" if ports == "top-100" else f"-p {ports}"
            exit_code, stdout, stderr = self.sandbox.execute_tool(
                self.session_id, "nmap", f"{port_arg} {target}", self.vm_config.vm_username, self.vm_config.vm_password
            )
            return stdout if exit_code == 0 else stderr

        @tool
        def vm_nuclei_scan(target: str, severity: str = "critical,high") -> str:
            """Scannt nach CVEs in VM mit Nuclei"""
            if not self.session_id:
                return "Keine aktive Session"

            exit_code, stdout, stderr = self.sandbox.execute_tool(
                self.session_id, "nuclei", f"-u {target} -s {severity}", self.vm_config.vm_username, self.vm_config.vm_password
            )
            return stdout if exit_code == 0 else stderr

        @tool
        def vm_gobuster_scan(target: str, wordlist: str = "common.txt") -> str:
            """Directory Enumeration in VM mit Gobuster"""
            if not self.session_id:
                return "Keine aktive Session"

            exit_code, stdout, stderr = self.sandbox.execute_tool(
                self.session_id,
                "gobuster",
                f"dir -u {target} -w /usr/share/wordlists/dirb/{wordlist}",
                self.vm_config.vm_username,
                self.vm_config.vm_password,
            )
            return stdout if exit_code == 0 else stderr

        @tool
        def restore_vm_snapshot(snapshot_name: str = "clean_state") -> str:
            """Stellt VM-Snapshot wieder her"""
            success = self.vbox.restore_snapshot(self.vm_config.vm_name, snapshot_name)
            return f"Snapshot {snapshot_name} wiederhergestellt" if success else "Fehler"

        return [vm_nmap_scan, vm_nuclei_scan, vm_gobuster_scan, restore_vm_snapshot]

    def run(self, target: str, objective: str = "comprehensive scan") -> dict:
        """Führt VM-basierten Pentest durch"""

        # VM Session starten
        if self.vm_config.use_vm:
            import uuid

            self.session_id = f"vm_pentest_{uuid.uuid4().hex[:8]}"

            logger.info(f"Starte VM-Session: {self.session_id}")

            if self.vm_config.auto_restore_snapshot:
                logger.info("Stelle clean_state Snapshot wieder her...")
                self.vbox.restore_snapshot(self.vm_config.vm_name, "clean_state")

            if not self.sandbox.create_session(self.session_id, self.vm_config.vm_name):
                raise RuntimeError("Konnte VM-Session nicht starten")

        try:
            # Parent run aufrufen
            initial_state = {
                "messages": [HumanMessage(content=f"{objective} on {target}")],
                "findings": [],
                "target": target,
                "iteration": 0,
                "max_iterations": self.config.max_iterations,
                "status": "running",
            }

            result = self.graph.invoke(initial_state, config={"configurable": {"thread_id": self.session_id}})

            return {
                "findings": result["findings"],
                "final_message": result["messages"][-1].content if result["messages"] else "",
                "iterations": result["iteration"],
                "status": result["status"],
                "target": target,
                "session_id": self.session_id,
            }

        finally:
            # Aufräumen
            if self.session_id and self.vm_config.use_vm:
                logger.info("Beende VM-Session...")
                self.sandbox.end_session(self.session_id)
                self.session_id = None


# Factory
def get_vm_agent(config: VMAgentConfig = None) -> VMReActAgent:
    """Gibt VM-basierten Agent zurück"""
    return VMReActAgent(config)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    config = VMAgentConfig(use_vm=True, vm_name="kali-pentest", max_iterations=5, auto_restore_snapshot=True)

    agent = VMReActAgent(config)
    result = agent.run("scanme.nmap.org", "Port scan and vulnerability assessment")

    print("\n" + "=" * 70)
    print("VM-BASIERTER PENTEST ABGESCHLOSSEN")
    print("=" * 70)
    print(f"Session: {result.get('session_id')}")
    print(f"Iterations: {result['iterations']}")
    print(f"Findings: {len(result['findings'])}")
    print("\nFinal Analysis:")
    print(result["final_message"][:500])
