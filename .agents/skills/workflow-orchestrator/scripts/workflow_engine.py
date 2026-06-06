#!/usr/bin/env python3
"""
Workflow Engine for Module Orchestration

Manages the execution of multi-phase penetration testing workflows
with iteration support, dependency resolution, and adaptive strategies.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("workflow_engine")


class ModuleStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()
    BLOCKED = auto()  # Dependencies not met


class WorkflowStatus(Enum):
    INITIALIZING = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    MAX_ITERATIONS = auto()


@dataclass
class ModuleResult:
    """Result from a module execution."""

    module_name: str
    status: ModuleStatus
    outputs: Dict[str, Any] = field(default_factory=dict)
    findings: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def is_empty(self) -> bool:
        """Check if result has no meaningful findings."""
        return len(self.findings) == 0 and len(self.outputs) == 0

    @property
    def has_errors(self) -> bool:
        """Check if execution had errors."""
        return len(self.errors) > 0 or self.status == ModuleStatus.FAILED


@dataclass
class WorkflowContext:
    """Context passed between workflow iterations."""

    target: str
    iteration: int = 0
    max_iterations: int = 3
    results: Dict[str, List[ModuleResult]] = field(default_factory=dict)
    findings: List[Dict] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    adaptations: List[Dict] = field(default_factory=list)

    def get_latest_result(self, module_name: str) -> Optional[ModuleResult]:
        """Get the most recent result for a module."""
        if module_name in self.results and self.results[module_name]:
            return self.results[module_name][-1]
        return None

    def get_all_results(self, module_name: str) -> List[ModuleResult]:
        """Get all results for a module across iterations."""
        return self.results.get(module_name, [])

    def add_result(self, result: ModuleResult):
        """Add a result to the context."""
        if result.module_name not in self.results:
            self.results[result.module_name] = []
        self.results[result.module_name].append(result)

        # Merge findings
        self.findings.extend(result.findings)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "target": self.target,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "results": {
                k: [
                    {
                        "module_name": r.module_name,
                        "status": r.status.name,
                        "outputs": r.outputs,
                        "findings": r.findings,
                        "errors": r.errors,
                        "execution_time": r.execution_time,
                        "timestamp": r.timestamp,
                    }
                    for r in v
                ]
                for k, v in self.results.items()
            },
            "findings": self.findings,
            "state": self.state,
            "adaptations": self.adaptations,
        }


@dataclass
class WorkflowStep:
    """A single step in the workflow."""

    name: str
    module: Any  # Module instance
    depends_on: List[str] = field(default_factory=list)
    required: bool = False
    condition: Optional[Callable[[WorkflowContext], bool]] = None
    input_mapper: Optional[Callable[[WorkflowContext], Dict]] = None
    fallback: Optional[Any] = None  # Fallback module
    max_retries: int = 1
    timeout: int = 300


class WorkflowEngine:
    """
    Orchestrates multi-phase penetration testing workflows.

    Features:
    - Dependency resolution
    - Iterative execution
    - Adaptive fallback strategies
    - Parallel execution of independent modules
    """

    def __init__(self, state_manager=None, parallel: bool = True, max_concurrent: int = 3):
        self.state_manager = state_manager
        self.parallel = parallel
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._hooks: Dict[str, List[Callable]] = {
            "pre_iteration": [],
            "post_iteration": [],
            "pre_module": [],
            "post_module": [],
            "adaptation": [],
        }

    def register_hook(self, event: str, callback: Callable):
        """Register a hook for workflow events."""
        if event in self._hooks:
            self._hooks[event].append(callback)

    async def _trigger_hooks(self, event: str, *args, **kwargs):
        """Trigger all hooks for an event."""
        for hook in self._hooks.get(event, []):
            try:
                await hook(*args, **kwargs)
            except Exception as e:
                logger.error(f"Hook error for {event}: {e}")

    async def execute(self, steps: List[WorkflowStep], context: WorkflowContext, adaptive_strategy=None) -> WorkflowContext:
        """
        Execute workflow with iterations.

        Args:
            steps: Workflow steps to execute
            context: Initial workflow context
            adaptive_strategy: Strategy for handling empty results

        Returns:
            Updated context with all results
        """
        logger.info(f"Starting workflow for {context.target}")

        while context.iteration < context.max_iterations:
            context.iteration += 1
            logger.info(f"=== Iteration {context.iteration}/{context.max_iterations} ===")

            await self._trigger_hooks("pre_iteration", context)

            # Execute all steps for this iteration
            iteration_complete = await self._execute_iteration(steps, context, adaptive_strategy)

            await self._trigger_hooks("post_iteration", context)

            # Check if we should continue
            if iteration_complete or self._is_workflow_complete(context, steps):
                logger.info("Workflow complete")
                break

            # Check for early termination conditions
            if self._should_terminate_early(context):
                logger.info("Early termination triggered")
                break

        # Save final state
        if self.state_manager:
            await self.state_manager.save(context)

        return context

    async def _execute_iteration(self, steps: List[WorkflowStep], context: WorkflowContext, adaptive_strategy) -> bool:
        """
        Execute one iteration of the workflow.

        Returns:
            True if iteration completed all steps successfully
        """
        completed_steps = set()
        failed_required = False

        # Build dependency graph
        pending = set(step.name for step in steps)

        while pending and not failed_required:
            # Find steps ready to execute (dependencies met)
            ready = []
            for step in steps:
                if step.name in pending:
                    deps_met = all(dep in completed_steps for dep in step.depends_on)
                    if deps_met:
                        ready.append(step)

            if not ready:
                # Deadlock - remaining steps have unmet dependencies
                logger.error(f"Dependency deadlock for: {pending}")
                break

            # Execute ready steps
            if self.parallel and len(ready) > 1:
                # Execute in parallel
                tasks = [self._execute_step(step, context, adaptive_strategy) for step in ready]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for step, result in zip(ready, results):
                    pending.discard(step.name)
                    if isinstance(result, Exception):
                        logger.error(f"Step {step.name} failed: {result}")
                        if step.required:
                            failed_required = True
                    else:
                        completed_steps.add(step.name)
            else:
                # Execute sequentially
                for step in ready:
                    try:
                        await self._execute_step(step, context, adaptive_strategy)
                        completed_steps.add(step.name)
                        pending.discard(step.name)
                    except Exception as e:
                        logger.error(f"Step {step.name} failed: {e}")
                        pending.discard(step.name)
                        if step.required:
                            failed_required = True
                            break

        return not failed_required and not pending

    async def _execute_step(self, step: WorkflowStep, context: WorkflowContext, adaptive_strategy) -> ModuleResult:
        """
        Execute a single workflow step.

        Args:
            step: Step to execute
            context: Current workflow context
            adaptive_strategy: Strategy for adaptations

        Returns:
            Module execution result
        """
        # Check condition
        if step.condition and not step.condition(context):
            logger.info(f"Skipping {step.name} - condition not met")
            return ModuleResult(module_name=step.name, status=ModuleStatus.SKIPPED)

        # Check state if state manager available
        if self.state_manager:
            inputs = step.input_mapper(context) if step.input_mapper else {}
            if await self.state_manager.is_tested(context.target, step.name, inputs):
                logger.info(f"Skipping {step.name} - already tested")
                cached = await self.state_manager.get_result(context.target, step.name)
                if cached:
                    return cached

        await self._trigger_hooks("pre_module", step, context)

        # Prepare inputs
        inputs = {}
        if step.input_mapper:
            inputs = step.input_mapper(context)

        # Execute with semaphore for concurrency control
        async with self._semaphore:
            start_time = datetime.now()

            try:
                # Execute module
                result = await self._run_module(step.module, inputs, step.timeout)
                execution_time = (datetime.now() - start_time).total_seconds()

                module_result = ModuleResult(
                    module_name=step.name,
                    status=ModuleStatus.COMPLETED,
                    outputs=result.get("outputs", {}),
                    findings=result.get("findings", []),
                    errors=result.get("errors", []),
                    execution_time=execution_time,
                )

            except asyncio.TimeoutError:
                logger.warning(f"Module {step.name} timed out")
                module_result = ModuleResult(
                    module_name=step.name,
                    status=ModuleStatus.FAILED,
                    errors=["Execution timeout"],
                    execution_time=step.timeout,
                )
            except Exception as e:
                logger.error(f"Module {step.name} failed: {e}")
                module_result = ModuleResult(module_name=step.name, status=ModuleStatus.FAILED, errors=[str(e)])

        # Store result
        context.add_result(module_result)

        # Handle empty results with adaptive strategy
        if module_result.is_empty and adaptive_strategy:
            await self._handle_empty_result(step, context, adaptive_strategy)

        # Save to state
        if self.state_manager:
            await self.state_manager.store(context.target, step.name, module_result, inputs)

        await self._trigger_hooks("post_module", step, module_result, context)

        return module_result

    async def _run_module(self, module: Any, inputs: Dict, timeout: int) -> Dict:
        """
        Run a module with timeout.

        Args:
            module: Module instance with async run() method
            inputs: Input parameters
            timeout: Maximum execution time

        Returns:
            Module output dictionary
        """
        if hasattr(module, "run"):
            coro = module.run(**inputs)
            return await asyncio.wait_for(coro, timeout=timeout)
        elif callable(module):
            if asyncio.iscoroutinefunction(module):
                return await asyncio.wait_for(module(**inputs), timeout=timeout)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                return await asyncio.wait_for(loop.run_in_executor(None, module, **inputs), timeout=timeout)
        else:
            raise ValueError("Module must have run() method or be callable")

    async def _handle_empty_result(self, step: WorkflowStep, context: WorkflowContext, adaptive_strategy):
        """Handle empty result with adaptive strategy."""
        if step.fallback:
            logger.info(f"Triggering fallback for {step.name}")

            fallback_step = WorkflowStep(
                name=f"{step.name}_fallback", module=step.fallback, depends_on=step.depends_on, timeout=step.timeout
            )

            await self._trigger_hooks("adaptation", step, fallback_step, context)

            # Record adaptation
            context.adaptations.append(
                {
                    "iteration": context.iteration,
                    "trigger_module": step.name,
                    "fallback_module": fallback_step.name,
                    "reason": "empty_result",
                }
            )

            # Execute fallback
            await self._execute_step(fallback_step, context, None)

    def _is_workflow_complete(self, context: WorkflowContext, steps: List[WorkflowStep]) -> bool:
        """Check if workflow has achieved completion criteria."""
        # Check if we have critical findings
        critical_findings = [f for f in context.findings if f.get("severity") in ["critical", "high"]]
        if len(critical_findings) >= 3:
            logger.info("Workflow complete: sufficient critical findings")
            return True

        # Check if all required steps completed
        for step in steps:
            if step.required:
                results = context.get_all_results(step.name)
                if not results or results[-1].status != ModuleStatus.COMPLETED:
                    return False

        return True

    def _should_terminate_early(self, context: WorkflowContext) -> bool:
        """Check for early termination conditions."""
        # Too many consecutive failures
        recent_failures = 0
        for module_results in context.results.values():
            if module_results:
                last = module_results[-1]
                if last.status in [ModuleStatus.FAILED, ModuleStatus.SKIPPED]:
                    recent_failures += 1

        if recent_failures >= 5:
            logger.warning("Early termination: too many failures")
            return True

        # Target unresponsive
        unresponsive_count = sum(1 for findings in context.findings if findings.get("type") == "unresponsive")
        if unresponsive_count >= 3:
            logger.warning("Early termination: target unresponsive")
            return True

        return False


class WorkflowTemplate:
    """Load and validate workflow templates."""

    @staticmethod
    def load(path: str) -> List[WorkflowStep]:
        """Load workflow from YAML/JSON file."""
        import yaml

        with open(path) as f:
            data = yaml.safe_load(f)

        steps = []
        for step_data in data.get("steps", []):
            step = WorkflowStep(
                name=step_data["name"],
                module=step_data["module"],  # Would need actual module resolution
                depends_on=step_data.get("depends_on", []),
                required=step_data.get("required", False),
                timeout=step_data.get("timeout", 300),
            )
            steps.append(step)

        return steps


if __name__ == "__main__":
    # Test workflow engine
    async def test():
        # Mock module
        class MockModule:
            async def run(self, **kwargs):
                await asyncio.sleep(0.1)
                return {"outputs": {"ports": [80, 443]}, "findings": [{"type": "open_port", "port": 80}]}

        # Create workflow
        steps = [
            WorkflowStep(name="port_scan", module=MockModule(), required=True),
            WorkflowStep(name="web_scan", module=MockModule(), depends_on=["port_scan"]),
        ]

        context = WorkflowContext(target="example.com", max_iterations=2)

        engine = WorkflowEngine()
        result = await engine.execute(steps, context)

        print(f"Completed {result.iteration} iterations")
        print(f"Findings: {len(result.findings)}")
        print(json.dumps(result.to_dict(), indent=2))

    asyncio.run(test())
