import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.tri_module_loop import (
    Action,
    ActionPlan,
    GenerationModule,
    LoopResult,
    LoopStatus,
    ModuleType,
    ParsedObservation,
    ParsingModule,
    ReasoningModule,
    ReasoningResult,
    ReasoningStep,
    TriModuleLoop,
)


@pytest.fixture
def reasoning_module():
    return ReasoningModule()


@pytest.fixture
def generation_module():
    return GenerationModule()


@pytest.fixture
def parsing_module():
    return ParsingModule()


@pytest.fixture
def loop(reasoning_module, generation_module, parsing_module):
    return TriModuleLoop(
        reasoning_module,
        generation_module,
        parsing_module,
        max_iterations=2,
        timeout_per_module=10.0,
    )


class TestModuleInitialization:
    def test_reasoning_module_init(self, reasoning_module):
        assert reasoning_module.llm is None
        assert reasoning_module.conversation_history == []
        assert reasoning_module.relevant_context == {}

    def test_generation_module_init(self, generation_module):
        assert generation_module.tool_registry == {}
        assert "Reconnaissance" in generation_module._tool_map

    def test_parsing_module_init(self, parsing_module):
        assert parsing_module._parsing_stats == {}

    def test_tri_module_loop_init(self, loop):
        assert loop.max_iterations == 2
        assert loop.timeout_per_module == 10.0
        assert loop.reasoning is not None
        assert loop.generation is not None
        assert loop.parsing is not None
        assert loop.tool_executor is None
        assert loop.result is not None
        assert loop._cancelled is False

    def test_tri_module_loop_with_tool_executor(self):
        executor = MagicMock()
        loop = TriModuleLoop(ReasoningModule(), GenerationModule(), ParsingModule(), tool_executor=executor)
        assert loop.tool_executor is executor


class TestProcessBasicFlow:
    @pytest.mark.asyncio
    async def test_run_returns_result(self, loop):
        result = await loop.run("Test objective", {"target": "10.0.0.1"})
        assert isinstance(result, LoopResult)
        assert result.objective == "Test objective"
        assert result.loop_id.startswith("tri_")

    @pytest.mark.asyncio
    async def test_run_without_context(self, loop):
        result = await loop.run("Test")
        assert result.objective == "Test"
        assert result.total_steps > 0

    @pytest.mark.asyncio
    async def test_run_populates_stats(self, loop):
        result = await loop.run("Stats test")
        assert "reasoning_count" in result.stats
        assert "action_plans_count" in result.stats
        assert "observations_count" in result.stats
        assert "total_findings" in result.stats
        assert "duration_seconds" in result.stats
        assert "status" in result.stats


class TestModuleCommunication:
    @pytest.mark.asyncio
    async def test_reasoning_feeds_generation(self, loop):
        result = await loop.run("Communication test", {})
        if result.action_plans:
            plan = result.action_plans[0]
            assert plan.step_number >= 0

    @pytest.mark.asyncio
    async def test_generation_feeds_parsing(self, loop):
        result = await loop.run("Parse test", {})
        if result.observations:
            obs = result.observations[0]
            assert isinstance(obs, ParsedObservation)
            assert obs.step_number >= 0

    @pytest.mark.asyncio
    async def test_findings_accumulate(self, loop):
        result = await loop.run("Findings test", {"target": "10.0.0.1"})
        total = sum(len(o.findings) for o in result.observations)
        assert len(result.all_findings) == total

    @pytest.mark.asyncio
    async def test_event_bus_events_fired(self, loop):
        events = []

        async def collector(data):
            events.append(type(data).__name__)

        loop.event_bus.on("reasoning.complete", collector)
        loop.event_bus.on("generation.complete", collector)

        await loop.run("Event test", {})
        assert len(events) >= 1


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_execute_action_error_returns_error_dict(self, loop):
        action = Action(tool="nonexistent_tool", parameters={})
        result = await loop._execute_action(action, 0)
        assert isinstance(result, dict)
        assert "findings" in result

    @pytest.mark.asyncio
    async def test_execute_action_with_executor_error(self, loop):
        executor = AsyncMock()
        executor.execute = AsyncMock(side_effect=RuntimeError("execution failed"))
        loop.tool_executor = executor
        action = Action(tool="nmap", parameters={"target": "10.0.0.1"})
        result = await loop._execute_action(action, 0)
        assert result["error"] == "execution failed"
        assert result["tool"] == "nmap"

    @pytest.mark.asyncio
    async def test_execute_action_with_executor_success(self, loop):
        executor = AsyncMock()
        executor.execute = AsyncMock(return_value={"success": True, "data": "result"})
        loop.tool_executor = executor
        action = Action(tool="nmap", parameters={"target": "10.0.0.1"})
        result = await loop._execute_action(action, 0)
        assert result == {"success": True, "data": "result"}

    @pytest.mark.asyncio
    async def test_run_with_timeout_success(self, loop):
        result = await loop._run_with_timeout(asyncio.sleep(0.01), "test")
        assert result is None

    @pytest.mark.asyncio
    async def test_run_with_timeout_raises(self, loop):
        loop.timeout_per_module = 0.01
        with pytest.raises(asyncio.TimeoutError):
            await loop._run_with_timeout(asyncio.sleep(10), "test")

    @pytest.mark.asyncio
    async def test_run_with_timeout_sets_status(self, loop):
        loop.timeout_per_module = 0.01
        with patch.object(loop.event_bus, "emit", new=AsyncMock()):
            with pytest.raises(asyncio.TimeoutError):
                await loop._run_with_timeout(asyncio.sleep(10), "test")
            assert loop.result.final_status == LoopStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_emulate_tool_known(self, loop):
        result = loop._emulate_tool("nmap", {"target": "10.0.0.1"})
        assert "findings" in result

    @pytest.mark.asyncio
    async def test_emulate_tool_unknown(self, loop):
        result = loop._emulate_tool("unknown_tool", {})
        assert "findings" in result
        assert "command" in result


class TestLoopResult:
    def test_loop_result_defaults(self):
        r = LoopResult()
        assert r.reasoning_steps == []
        assert r.action_plans == []
        assert r.observations == []
        assert r.final_status == LoopStatus.RUNNING
        assert r.total_steps == 0

    def test_loop_result_to_dict(self):
        r = LoopResult(objective="test", final_status=LoopStatus.COMPLETED, total_steps=3)
        d = r.to_dict()
        assert d["objective"] == "test"
        assert d["final_status"] == "COMPLETED"
        assert d["total_steps"] == 3

    def test_reasoning_result_to_dict(self):
        step = ReasoningStep("Recon", "Find hosts", 0.95)
        rr = ReasoningResult(
            plan_steps=[step],
            reasoning="Plan",
            confidence=0.9,
            should_stop=False,
            step_number=0,
        )
        d = rr.to_dict()
        assert len(d["plan_steps"]) == 1
        assert d["plan_steps"][0]["description"] == "Recon"

    def test_action_plan_to_dict(self):
        action = Action(tool="nmap", parameters={"targets": ["x"]}, expected_outcome="Scan", priority=1)
        plan = ActionPlan(actions=[action], priority=2, step_number=0)
        d = plan.to_dict()
        assert len(d["actions"]) == 1
        assert d["actions"][0]["tool"] == "nmap"
        assert d["priority"] == 2

    def test_parsed_observation_to_dict(self):
        obs = ParsedObservation(
            findings=[{"source": "nmap", "type": "raw"}],
            extracted_data={"port": 80},
            errors=[],
            step_number=0,
        )
        d = obs.to_dict()
        assert len(d["findings"]) == 1
        assert d["extracted_data"]["port"] == 80


class TestCancel:
    def test_cancel_sets_flag(self, loop):
        assert loop._cancelled is False
        loop.cancel()
        assert loop._cancelled is True

    @pytest.mark.asyncio
    async def test_run_resets_cancel(self, loop):
        loop.cancel()
        assert loop._cancelled is True
        await loop.run("Reset test", {})
        assert loop._cancelled is False


class TestCheckpointCallback:
    @pytest.mark.asyncio
    async def test_checkpoint_callback_called(self):
        callback = MagicMock()
        loop = TriModuleLoop(
            ReasoningModule(),
            GenerationModule(),
            ParsingModule(),
            max_iterations=1,
            checkpoint_callback=callback,
        )
        await loop.run("Callback test", {})
        callback.assert_called_once()
        assert isinstance(callback.call_args[0][0], LoopResult)


class TestDataclassModels:
    def test_reasoning_step_to_dict(self):
        step = ReasoningStep("Recon", "Find hosts", 0.95, {"extra": "info"})
        d = step.to_dict()
        assert d["description"] == "Recon"
        assert d["rationale"] == "Find hosts"
        assert d["confidence"] == 0.95
        assert d["metadata"] == {"extra": "info"}

    def test_action_defaults(self):
        a = Action(tool="nmap")
        assert a.parameters == {}
        assert a.expected_outcome == ""
        assert a.priority == 0

    def test_action_to_dict(self):
        a = Action(tool="nmap", parameters={"p": 1}, expected_outcome="scan", priority=2)
        d = a.to_dict()
        assert d["tool"] == "nmap"
        assert d["priority"] == 2

    def test_loop_status_enum(self):
        assert LoopStatus.RUNNING.name == "RUNNING"
        assert LoopStatus.COMPLETED.name == "COMPLETED"
        assert LoopStatus.TIMEOUT.name == "TIMEOUT"
        assert LoopStatus.MAX_ITERATIONS.name == "MAX_ITERATIONS"

    def test_module_type_enum(self):
        assert ModuleType.REASONING.name == "REASONING"
        assert ModuleType.GENERATION.name == "GENERATION"
        assert ModuleType.PARSING.name == "PARSING"
