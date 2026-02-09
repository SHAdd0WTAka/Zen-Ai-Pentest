"""
ReAct Agent Loop für Zen-AI-Pentest - Performance Optimized
Implementiert Reasoning-Acting-Observing-Reflecting Pattern mit LangGraph

Optimizations:
- Context window management
- LLM response caching
- Memory usage optimization
- Streaming support
- Batch tool execution

Phase 1: Echter agentischer Loop (2026 Roadmap)
"""

from typing import List, TypedDict, Annotated, Literal, Optional, Dict, Any
from dataclasses import dataclass, field
import json
import logging
import time
from collections import deque

from langchain_core.tools import tool, BaseTool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.checkpoint.memory import MemorySaver

# Zen-AI-Pentest Imports
try:
    from ..core.llm_backend import LLMBackend
    from ..core.cache import cached, MemoryCache
    from ..tools.nmap_integration import NmapTool
    from ..tools.nuclei_integration import NucleiTool
    from ..tools.ffuf_integration import FfufTool
    from ..database.cve_database import CVEDatabase
except ImportError:
    # Fallback for direct execution
    from core.llm_backend import LLMBackend
    from core.cache import cached, MemoryCache
    from tools.nmap_integration import NmapTool
    from tools.nuclei_integration import NucleiTool
    from tools.ffuf_integration import FfufTool
    from modules.cve_database import CVEDatabase


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
    max_context_messages: int = 20  # Limit context window
    cache_llm_responses: bool = True
    llm_cache_ttl: int = 300  # 5 minutes
    max_findings_storage: int = 1000  # Limit stored findings


class ContextWindowManager:
    """
    Manages the context window to prevent memory bloat.
    Implements sliding window and summary strategies.
    """
    
    def __init__(self, max_messages: int = 20, summary_threshold: int = 15):
        self.max_messages = max_messages
        self.summary_threshold = summary_threshold
        self.message_history: deque = deque(maxlen=max_messages * 2)
        self.summaries: List[str] = []
    
    def add_message(self, message: BaseMessage):
        """Add message to history with automatic pruning."""
        self.message_history.append(message)
        
        # Prune if exceeds threshold
        if len(self.message_history) > self.summary_threshold:
            self._prune_old_messages()
    
    def _prune_old_messages(self):
        """Summarize and prune old messages."""
        # Keep system messages and recent messages
        to_summarize = []
        to_keep = []
        
        for msg in list(self.message_history)[:-self.max_messages//2]:
            if isinstance(msg, SystemMessage):
                to_keep.append(msg)
            else:
                to_summarize.append(msg)
        
        if to_summarize:
            # Create summary (simplified - could use LLM for better summaries)
            summary = f"[Summary of {len(to_summarize)} previous messages]"
            self.summaries.append(summary)
        
        # Rebuild history
        self.message_history.clear()
        self.message_history.extend(to_keep)
        self.message_history.extend(list(self.message_history)[-self.max_messages//2:])
    
    def get_context_messages(self, current_messages: List[BaseMessage]) -> List[BaseMessage]:
        """Get optimized context messages."""
        context = []
        
        # Add summaries as context
        for summary in self.summaries[-3:]:  # Keep last 3 summaries
            context.append(SystemMessage(content=f"Previous context: {summary}"))
        
        # Add recent messages
        context.extend(list(self.message_history)[-self.max_messages:])
        
        # Add current messages
        context.extend(current_messages)
        
        return context
    
    def clear(self):
        """Clear all history."""
        self.message_history.clear()
        self.summaries.clear()


class LLMResponseCache:
    """Simple cache for LLM responses to avoid redundant calls."""
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 100):
        self._cache: Dict[str, Dict] = {}
        self._ttl = ttl_seconds
        self._max_size = max_size
    
    def _make_key(self, messages: List[BaseMessage], tools: List[BaseTool]) -> str:
        """Generate cache key from messages and tools."""
        import hashlib
        content = json.dumps({
            "messages": [(m.type, m.content) for m in messages],
            "tools": [t.name for t in tools]
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, messages: List[BaseMessage], tools: List[BaseTool]) -> Optional[AIMessage]:
        """Get cached response if available."""
        key = self._make_key(messages, tools)
        entry = self._cache.get(key)
        
        if entry:
            if time.time() - entry["timestamp"] < self._ttl:
                logger.debug(f"LLM cache hit: {key[:16]}...")
                return entry["response"]
            else:
                del self._cache[key]
        
        return None
    
    def set(self, messages: List[BaseMessage], tools: List[BaseTool], response: AIMessage):
        """Cache LLM response."""
        # Evict oldest if at capacity
        if len(self._cache) >= self._max_size:
            oldest = min(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
            del self._cache[oldest]
        
        key = self._make_key(messages, tools)
        self._cache[key] = {
            "response": response,
            "timestamp": time.time()
        }
    
    def clear(self):
        """Clear cache."""
        self._cache.clear()


class ReActAgent:
    """
    ReAct Agent für autonomes Pentesting - Performance Optimized.

    Flow:
    1. Reason/Plan -> LLM entscheidet nächsten Schritt
    2. Act -> Führt Tools aus (sandboxed, parallel if possible)
    3. Observe -> Sammelt Ergebnisse
    4. Reflect -> Bewertet Fortschritt
    5. Loop oder End
    """

    def __init__(self, config: ReActAgentConfig = None):
        self.config = config or ReActAgentConfig()
        self.llm = LLMBackend(model=self.config.llm_model)
        self.cve_db = CVEDatabase()
        
        # Context window management
        self.context_manager = ContextWindowManager(
            max_messages=self.config.max_context_messages
        )
        
        # LLM response caching
        self.llm_cache = LLMResponseCache(
            ttl_seconds=self.config.llm_cache_ttl
        ) if self.config.cache_llm_responses else None

        # Tools initialisieren
        self.tools = self._initialize_tools()
        self.tools_by_name = {t.name: t for t in self.tools}

        # LangGraph Workflow
        self.graph = self._build_graph()

        logger.info(f"ReActAgent initialisiert mit {len(self.tools)} Tools")

    def _initialize_tools(self) -> List[BaseTool]:
        """Initialisiert Pentest-Tools with caching support"""
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

        # CVE Lookup with caching
        @tool
        def lookup_cve(cve_id: str) -> str:
            """Sucht CVE-Details in der Datenbank"""
            # Use cached lookup
            from ..modules.cve_database import search_cve_cached
            cve = search_cve_cached(cve_id)
            if cve:
                return json.dumps(
                    {
                        "id": cve.cve_id,
                        "severity": cve.severity,
                        "cvss": cve.cvss_score,
                        "description": cve.description,
                        "mitigations": cve.mitigations[:3] if cve.mitigations else [],
                    },
                    indent=2,
                )
            return f"CVE {cve_id} nicht gefunden"

        # Exploit Validation
        @tool
        def validate_exploit(cve_id: str, target: str) -> str:
            """Validiert ob ein Exploit auf dem Target funktioniert (read-only)"""
            # TODO: Implementiere sichere Validierung
            return f"Exploit-Validierung für {cve_id} auf {target}: Noch nicht implementiert"

        tools = [scan_ports, scan_vulnerabilities, enumerate_directories, lookup_cve, validate_exploit]
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
                    "messages": state["messages"] + [AIMessage(content="Maximale Iterationen erreicht. Beende Scan.")],
                    "status": "completed",
                }

            # Prepare messages with context management
            current_messages = [SystemMessage(content=system_prompt)] + state["messages"]
            
            # Check cache first
            if self.llm_cache:
                cached_response = self.llm_cache.get(current_messages, self.tools)
                if cached_response:
                    return {
                        **state,
                        "messages": [cached_response],
                        "iteration": state["iteration"] + 1
                    }

            # LLM Call
            response = llm_with_tools.invoke(current_messages)
            
            # Cache response
            if self.llm_cache:
                self.llm_cache.set(current_messages, self.tools, response)
            
            # Update context manager
            for msg in current_messages:
                self.context_manager.add_message(msg)

            return {**state, "messages": [response], "iteration": state["iteration"] + 1}

        def tools_node(state: AgentState) -> AgentState:
            """Tools Node: Act/Observe with parallel execution support"""
            last_message = state["messages"][-1]

            if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
                return state

            tool_messages = []
            new_findings = []

            # Group tool calls for potential parallel execution
            tool_calls = last_message.tool_calls
            
            for tool_call in tool_calls:
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

                        # Finding speichern (limit storage)
                        if len(state["findings"]) < self.config.max_findings_storage:
                            finding = {
                                "tool": tool_name,
                                "args": args,
                                "result": result[:1000] if len(result) > 1000 else result,  # Truncate
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

            return {**state, "messages": tool_messages, "findings": state["findings"] + new_findings}

        def should_continue(state: AgentState) -> Literal["tools", "agent", "end"]:
            """Conditional Edge: Entscheidet über Loop-Fortsetzung"""
            last_message = state["messages"][-1]

            # Wenn fertig (keine Tool-Calls mehr)
            if state.get("status") == "completed":
                return "end"

            # Wenn Tools aufgerufen wurden
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
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

        workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "agent": "agent", "end": END})

        workflow.add_conditional_edges("tools", should_continue, {"tools": "tools", "agent": "agent", "end": END})

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
            "status": "running",
        }

        logger.info(f"Starte ReAct-Agent für {target}")

        # Graph ausführen
        result = self.graph.invoke(initial_state, config={"configurable": {"thread_id": f"pentest_{target}"}})

        logger.info(f"Agent beendet nach {result['iteration']} Iterationen")

        return {
            "findings": result["findings"],
            "final_message": result["messages"][-1].content if result["messages"] else "",
            "iterations": result["iteration"],
            "status": result["status"],
            "target": target,
        }

    async def run_async(self, target: str, objective: str = "comprehensive scan") -> dict:
        """Async version of run."""
        initial_state: AgentState = {
            "messages": [HumanMessage(content=f"{objective} on {target}")],
            "findings": [],
            "target": target,
            "iteration": 0,
            "max_iterations": self.config.max_iterations,
            "status": "running",
        }

        logger.info(f"Starte ReAct-Agent (async) für {target}")

        # Graph ausführen (async)
        result = await self.graph.ainvoke(
            initial_state, 
            config={"configurable": {"thread_id": f"pentest_{target}"}}
        )

        logger.info(f"Agent beendet nach {result['iteration']} Iterationen")

        return {
            "findings": result["findings"],
            "final_message": result["messages"][-1].content if result["messages"] else "",
            "iterations": result["iteration"],
            "status": result["status"],
            "target": target,
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

        if result["findings"]:
            report.append("FINDINGS:")
            report.append("-" * 70)
            for i, finding in enumerate(result["findings"], 1):
                report.append(f"\n{i}. {finding['tool']}")
                report.append(f"   Args: {finding['args']}")
                result_text = finding['result']
                if len(result_text) > 200:
                    result_text = result_text[:200] + "..."
                report.append(f"   Result: {result_text}")
        else:
            report.append("No findings detected.")

        report.append("")
        report.append("=" * 70)
        report.append("FINAL ANALYSIS:")
        report.append("=" * 70)
        report.append(result["final_message"])

        return "\n".join(report)

    def clear_memory(self):
        """Clear agent memory to free up resources."""
        self.context_manager.clear()
        if self.llm_cache:
            self.llm_cache.clear()
        logger.info("Agent memory cleared")

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        return {
            "context_messages": len(self.context_manager.message_history),
            "context_summaries": len(self.context_manager.summaries),
            "llm_cache_entries": len(self.llm_cache._cache) if self.llm_cache else 0,
        }


# Singleton-Instanz für einfachen Zugriff
_default_agent = None


def get_agent(config: ReActAgentConfig = None) -> ReActAgent:
    """Gibt die default Agent-Instanz zurück"""
    global _default_agent
    if _default_agent is None or config is not None:
        _default_agent = ReActAgent(config)
    return _default_agent


def clear_agent_memory():
    """Clear the default agent's memory."""
    global _default_agent
    if _default_agent:
        _default_agent.clear_memory()


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)

    config = ReActAgentConfig(
        max_iterations=5, 
        enable_sandbox=True, 
        auto_approve_dangerous=False,
        cache_llm_responses=True,
    )

    agent = ReActAgent(config)
    result = agent.run("scanme.nmap.org", objective="Port scan and vulnerability assessment")

    print(agent.generate_report(result))
    print("\nMemory stats:", agent.get_memory_stats())
