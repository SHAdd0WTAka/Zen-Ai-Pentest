"""PentestGPT-inspired Tri-Module Agent Loop (Reasoning -> Generation -> Parsing)."""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

from core.workflow_engine import EventBus

logger = logging.getLogger("ZenAI.TriModule")


class ModuleType(Enum):
    REASONING = auto()
    GENERATION = auto()
    PARSING = auto()


class LoopStatus(Enum):
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    TIMEOUT = auto()
    MAX_ITERATIONS = auto()


@dataclass
class ReasoningStep:
    description: str
    rationale: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass
class ReasoningResult:
    plan_steps: List[ReasoningStep]
    reasoning: str
    confidence: float
    should_stop: bool
    module: ModuleType = ModuleType.REASONING
    step_number: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_steps": [s.to_dict() for s in self.plan_steps],
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "should_stop": self.should_stop,
            "module": self.module.name,
            "step_number": self.step_number,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Action:
    tool: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_outcome: str = ""
    priority: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "parameters": self.parameters,
            "expected_outcome": self.expected_outcome,
            "priority": self.priority,
        }


@dataclass
class ActionPlan:
    actions: List[Action]
    priority: int = 0
    module: ModuleType = ModuleType.GENERATION
    step_number: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "actions": [a.to_dict() for a in self.actions],
            "priority": self.priority,
            "module": self.module.name,
            "step_number": self.step_number,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ParsedObservation:
    findings: List[Dict[str, Any]]
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    module: ModuleType = ModuleType.PARSING
    step_number: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "findings": self.findings,
            "extracted_data": self.extracted_data,
            "errors": self.errors,
            "metrics": self.metrics,
            "module": self.module.name,
            "step_number": self.step_number,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class LoopResult:
    reasoning_steps: List[ReasoningResult] = field(default_factory=list)
    action_plans: List[ActionPlan] = field(default_factory=list)
    observations: List[ParsedObservation] = field(default_factory=list)
    all_findings: List[Dict[str, Any]] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    final_status: LoopStatus = LoopStatus.RUNNING
    total_steps: int = 0
    loop_id: str = field(default_factory=lambda: f"tri_{uuid.uuid4().hex[:8]}")
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    objective: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "objective": self.objective,
            "final_status": self.final_status.name,
            "total_steps": self.total_steps,
            "reasoning_steps": [r.to_dict() for r in self.reasoning_steps],
            "action_plans": [a.to_dict() for a in self.action_plans],
            "observations": [o.to_dict() for o in self.observations],
            "all_findings": self.all_findings,
            "stats": self.stats,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ReasoningModule:
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm = llm_client
        self.conversation_history: List[Dict[str, Any]] = []
        self.relevant_context: Dict[str, Any] = {}

    async def analyze(
        self,
        context: Dict[str, Any],
        objective: str,
        step_number: int = 0,
    ) -> ReasoningResult:
        self.relevant_context.update(context)
        self.conversation_history.append({"role": "system", "content": objective})

        plan_steps = self._build_plan(objective)
        reasoning = self._synthesize_reasoning(plan_steps)
        confidence = self._estimate_confidence(step_number)
        should_stop = self._decide_termination(step_number)

        result = ReasoningResult(
            plan_steps=plan_steps,
            reasoning=reasoning,
            confidence=confidence,
            should_stop=should_stop,
            step_number=step_number,
            metadata={
                "history_length": len(self.conversation_history),
                "context_keys": list(context.keys()),
                "context_findings_count": len(context.get("findings", [])),
            },
        )

        self.conversation_history.append(
            {
                "role": "assistant",
                "content": f"Step {step_number}: {reasoning[:200]}",
            }
        )

        logger.debug(
            "ReasoningModule.analyze step=%d confidence=%.2f stop=%s steps=%d",
            step_number,
            confidence,
            should_stop,
            len(plan_steps),
        )
        return result

    def _build_plan(self, objective: str) -> List[ReasoningStep]:
        return [
            ReasoningStep("Reconnaissance", "Identify live hosts and services", 0.95),
            ReasoningStep("Service Enumeration", "Find version info and potential vulns", 0.90),
            ReasoningStep("Vulnerability Assessment", "Cross-reference against known CVEs", 0.85),
            ReasoningStep("Focused Exploitation", "Exploit confirmed vulnerabilities", 0.70),
        ]

    def _synthesize_reasoning(self, steps: List[ReasoningStep]) -> str:
        return "Planned approach:\n" + "\n".join(f"  {i}. {s.description} — {s.rationale}" for i, s in enumerate(steps, 1))

    def _estimate_confidence(self, step: int) -> float:
        return max(0.3, 1.0 - (step * 0.08))

    def _decide_termination(self, step: int) -> bool:
        return step >= 10 or self.relevant_context.get("objective_achieved", False)


class GenerationModule:
    def __init__(self, tool_registry: Optional[Dict[str, Any]] = None):
        self.tool_registry = tool_registry or {}
        self._tool_map: Dict[str, List[str]] = {
            "Reconnaissance": ["nmap", "masscan", "dnsrecon"],
            "Service Enumeration": ["nmap", "gobuster", "ffuf"],
            "Vulnerability Assessment": ["nuclei", "trivy", "nikto"],
            "Focused Exploitation": ["sqlmap", "metasploit", "searchsploit"],
        }

    async def generate(self, reasoning_result: ReasoningResult) -> ActionPlan:
        actions: List[Action] = []
        for step in reasoning_result.plan_steps:
            tools = self._tool_map.get(step.description, ["custom"])
            for tool in tools[:2]:
                actions.append(self._tool_to_action(tool, step))

        plan = ActionPlan(
            actions=actions[:3],
            priority=self._compute_priority(reasoning_result.confidence),
            step_number=reasoning_result.step_number,
            metadata={
                "source_reasoning_confidence": reasoning_result.confidence,
                "plan_steps_count": len(reasoning_result.plan_steps),
            },
        )

        logger.debug(
            "GenerationModule.generate step=%d priority=%d actions=%d",
            plan.step_number,
            plan.priority,
            len(plan.actions),
        )
        return plan

    def _tool_to_action(self, tool: str, step: ReasoningStep) -> Action:
        param_map: Dict[str, Dict[str, Any]] = {
            "nmap": {"targets": ["$target"], "ports": "1-1000", "flags": "-sV -sC"},
            "masscan": {"targets": ["$target"], "rate": 1000, "ports": "1-65535"},
            "gobuster": {"url": "$target", "wordlist": "common.txt", "threads": 50},
            "ffuf": {"url": "$target/FUZZ", "wordlist": "api.txt"},
            "nuclei": {"targets": ["$target"], "templates": ["cves", "misconfigurations"]},
            "trivy": {"target": "$target", "scanners": ["vuln"]},
            "sqlmap": {"url": "$target", "batch": True, "risk": 2, "level": 3},
        }
        params = param_map.get(tool, {})
        return Action(
            tool=tool, parameters=params, expected_outcome=f"Gather intelligence: {step.description}", priority=len(params)
        )

    def _compute_priority(self, confidence: float) -> int:
        if confidence >= 0.9:
            return 1
        elif confidence >= 0.7:
            return 2
        return 3


class ParsingModule:
    def __init__(self):
        self._parsing_stats: Dict[str, int] = {}

    async def parse(
        self,
        raw_result: Any,
        action: Action,
        step_number: int = 0,
    ) -> ParsedObservation:
        findings: List[Dict[str, Any]] = []
        errors: List[str] = []
        extracted: Dict[str, Any] = {}

        if isinstance(raw_result, dict):
            extracted = raw_result
            if raw_result.get("error"):
                errors.append(str(raw_result["error"]))
            for key in ("findings", "vulnerabilities", "results", "output"):
                items = raw_result.get(key)
                if isinstance(items, list):
                    for item in items:
                        findings.append(
                            {
                                "source": action.tool,
                                "type": "raw",
                                "data": item if isinstance(item, dict) else {"value": item},
                                "step": step_number,
                            }
                        )
        elif isinstance(raw_result, str):
            extracted = {"raw_output": raw_result[:1000]}
            findings.append(
                {
                    "source": action.tool,
                    "type": "text",
                    "data": {"preview": raw_result[:200]},
                    "step": step_number,
                }
            )
        elif raw_result is None:
            findings.append(
                {
                    "source": action.tool,
                    "type": "empty",
                    "data": {},
                    "step": step_number,
                }
            )
        else:
            findings.append(
                {
                    "source": action.tool,
                    "type": "unknown",
                    "data": {"type": type(raw_result).__name__},
                    "step": step_number,
                }
            )

        metrics = {
            "findings_count": len(findings),
            "errors_count": len(errors),
            "has_data": len(extracted) > 0,
            "tool": action.tool,
        }

        result = ParsedObservation(
            findings=findings,
            extracted_data=extracted,
            errors=errors,
            metrics=metrics,
            step_number=step_number,
        )

        tool_key = action.tool
        self._parsing_stats[tool_key] = self._parsing_stats.get(tool_key, 0) + 1

        logger.debug(
            "ParsingModule.parse step=%d tool=%s findings=%d errors=%d",
            step_number,
            action.tool,
            len(findings),
            len(errors),
        )
        return result

    def get_stats(self) -> Dict[str, int]:
        return dict(self._parsing_stats)


class TriModuleLoop:
    def __init__(
        self,
        reasoning_module: ReasoningModule,
        generation_module: GenerationModule,
        parsing_module: ParsingModule,
        tool_executor: Optional[Any] = None,
        max_iterations: int = 10,
        timeout_per_module: float = 30.0,
        checkpoint_callback: Optional[Callable[[LoopResult], None]] = None,
    ):
        self.reasoning = reasoning_module
        self.generation = generation_module
        self.parsing = parsing_module
        self.tool_executor = tool_executor
        self.max_iterations = max_iterations
        self.timeout_per_module = timeout_per_module
        self.checkpoint_callback = checkpoint_callback

        self.event_bus = EventBus()
        self.result = LoopResult()
        self._current_context: Dict[str, Any] = {}
        self._cancelled = False

        self._register_events()

    def _register_events(self) -> None:
        self.event_bus.on("reasoning.complete", self._on_reasoning_complete)
        self.event_bus.on("generation.complete", self._on_generation_complete)
        self.event_bus.on("execution.complete", self._on_execution_complete)
        self.event_bus.on("parsing.complete", self._on_parsing_complete)

    async def _on_reasoning_complete(self, data: ReasoningResult) -> None:
        if data.should_stop:
            await self.event_bus.emit("loop.complete", self.result)
            return
        plan = await self._run_with_timeout(
            self.generation.generate(data),
            "GenerationModule.generate",
        )
        plan.step_number = data.step_number
        self.result.action_plans.append(plan)
        await self.event_bus.emit("generation.complete", plan)

    async def _on_generation_complete(self, data: ActionPlan) -> None:
        raw_results: List[Any] = []
        for action in data.actions:
            raw = await self._execute_action(action, data.step_number)
            raw_results.append(raw)
        await self.event_bus.emit(
            "execution.complete",
            {
                "raw_results": raw_results,
                "actions": data.actions,
                "step_number": data.step_number,
            },
        )

    async def _on_execution_complete(self, data: Dict[str, Any]) -> None:
        raw_results = data["raw_results"]
        actions = data["actions"]
        step = data["step_number"]
        for raw, action in zip(raw_results, actions):
            obs = await self._run_with_timeout(
                self.parsing.parse(raw, action, step),
                "ParsingModule.parse",
            )
            obs.step_number = step
            self.result.observations.append(obs)
            self.result.all_findings.extend(obs.findings)
            self._current_context.setdefault("findings", []).extend(obs.findings)
        await self.event_bus.emit(
            "parsing.complete",
            {
                "step_number": step,
                "context": self._current_context,
            },
        )

    async def _on_parsing_complete(self, data: Dict[str, Any]) -> None:
        step = data["step_number"] + 1
        if step >= self.max_iterations:
            self.result.final_status = LoopStatus.MAX_ITERATIONS
            await self.event_bus.emit("loop.complete", self.result)
            return
        reasoning = await self._run_with_timeout(
            self.reasoning.analyze(self._current_context, self.result.objective, step),
            "ReasoningModule.analyze",
        )
        reasoning.step_number = step
        self.result.reasoning_steps.append(reasoning)
        await self.event_bus.emit("reasoning.complete", reasoning)

    async def _execute_action(self, action: Action, step: int) -> Any:
        logger.info("Executing step=%d tool=%s params=%s", step, action.tool, action.parameters)
        if self.tool_executor and hasattr(self.tool_executor, "execute"):
            try:
                return await self.tool_executor.execute(action.tool, action.parameters)
            except Exception as e:
                return {"error": str(e), "tool": action.tool}
        return self._emulate_tool(action.tool, action.parameters)

    def _emulate_tool(self, tool: str, params: Dict[str, Any]) -> Any:
        t = tool.lower()
        sims: Dict[str, Any] = {
            "nmap": {
                "findings": [
                    {"port": 22, "state": "open", "service": "ssh", "version": "OpenSSH 8.9p1"},
                    {"port": 80, "state": "open", "service": "http", "version": "nginx 1.24.0"},
                ],
                "hosts_up": 1,
                "execution_time_ms": 45230,
            },
            "nuclei": {
                "findings": [
                    {"template": "CVE-2023-44487", "severity": "high", "matched": "/http2"},
                ],
                "results": 2,
                "execution_time_ms": 28500,
            },
            "gobuster": {
                "findings": [
                    {"path": "/admin", "status": 200, "size": 4521},
                    {"path": "/.git", "status": 301, "size": 178},
                ],
                "execution_time_ms": 18300,
            },
            "sqlmap": {
                "findings": [
                    {"type": "time-based-blind", "parameter": "id", "technique": "blind"},
                ],
                "vulnerabilities": [{"title": "SQL Injection", "severity": "critical"}],
                "execution_time_ms": 125000,
            },
            "trivy": {
                "findings": [
                    {"vuln_id": "CVE-2024-21626", "package": "runc", "severity": "CRITICAL"},
                    {"vuln_id": "CVE-2023-39325", "package": "golang.org/x/net", "severity": "HIGH"},
                ],
                "execution_time_ms": 34200,
            },
            "ffuf": {
                "findings": [
                    {"url": "/api/v1/users", "status": 200, "size": 1240},
                    {"url": "/api/v1/admin", "status": 403, "size": 45},
                ],
                "execution_time_ms": 15600,
            },
        }
        data = sims.get(t, {"findings": [{"note": f"Simulated result for {t}"}]})
        data["command"] = f"{t} {json.dumps(params)}"
        return data

    async def _run_with_timeout(self, coro, label: str) -> Any:
        try:
            return await asyncio.wait_for(coro, timeout=self.timeout_per_module)
        except asyncio.TimeoutError:
            logger.error("%s timed out after %ds", label, self.timeout_per_module)
            self.result.final_status = LoopStatus.TIMEOUT
            await self.event_bus.emit("loop.complete", self.result)
            raise

    async def run(
        self,
        objective: str,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> LoopResult:
        logger.info("TriModuleLoop starting — objective: %s", objective)
        self.result = LoopResult(objective=objective)
        self._current_context = dict(initial_context or {})
        self._cancelled = False

        event_loop = asyncio.get_event_loop()
        stop_future = event_loop.create_future()

        def on_loop_complete(data: Any) -> None:
            if not stop_future.done():
                stop_future.set_result(data)

        self.event_bus.on("loop.complete", on_loop_complete)

        first_reasoning = await self._run_with_timeout(
            self.reasoning.analyze(self._current_context, objective, 0),
            "ReasoningModule.analyze (initial)",
        )
        first_reasoning.step_number = 0
        self.result.reasoning_steps.append(first_reasoning)
        await self.event_bus.emit("reasoning.complete", first_reasoning)

        try:
            final = await asyncio.wait_for(stop_future, timeout=3600)
            if isinstance(final, LoopResult):
                self.result = final
        except asyncio.TimeoutError:
            self.result.final_status = LoopStatus.TIMEOUT
            logger.error("TriModuleLoop timed out overall")

        self.result.completed_at = datetime.now()
        self.result.total_steps = len(self.result.reasoning_steps)

        stats = {
            "reasoning_count": len(self.result.reasoning_steps),
            "action_plans_count": len(self.result.action_plans),
            "observations_count": len(self.result.observations),
            "total_findings": len(self.result.all_findings),
            "status": self.result.final_status.name,
            "duration_seconds": (self.result.completed_at - self.result.started_at).total_seconds(),
        }
        self.result.stats = stats

        self.event_bus.off("loop.complete", on_loop_complete)

        if self.checkpoint_callback:
            self.checkpoint_callback(self.result)

        logger.info(
            "TriModuleLoop complete — status=%s steps=%d findings=%d",
            self.result.final_status.name,
            self.result.total_steps,
            len(self.result.all_findings),
        )
        return self.result

    def cancel(self) -> None:
        self._cancelled = True
        logger.warning("TriModuleLoop cancelled by user")


async def _demo() -> None:
    logger.info("=" * 60)
    logger.info("Tri-Module Loop — PentestGPT Demo")
    logger.info("=" * 60)
    loop = TriModuleLoop(
        ReasoningModule(),
        GenerationModule(),
        ParsingModule(),
        max_iterations=3,
        timeout_per_module=15.0,
    )
    result = await loop.run(
        "Recon and vuln assessment on 10.0.0.1/24",
        {"target": "10.0.0.1/24", "scope": "internal"},
    )
    logger.info(
        "Status: %s | Steps: %d | Duration: %.1fs | Findings: %d",
        result.final_status.name,
        result.total_steps,
        result.stats.get("duration_seconds", 0),
        len(result.all_findings),
    )
    for rr in result.reasoning_steps:
        logger.info("  Step %d: confidence=%.2f stop=%s", rr.step_number, rr.confidence, rr.should_stop)
    for ap in result.action_plans:
        for a in ap.actions:
            logger.info("  Action: %s", a.tool)
    for f in result.all_findings[:5]:
        logger.info("  Finding [%s]: %s", f.get("source", "?"), list(f.get("data", {}).keys())[:2])
    logger.info("Demo complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")
    asyncio.run(_demo())
