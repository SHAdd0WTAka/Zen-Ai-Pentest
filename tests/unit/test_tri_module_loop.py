import asyncio
from unittest.mock import patch

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


class TestReasoningModule:
    @pytest.mark.asyncio
    async def test_analyze_returns_result(self):
        module = ReasoningModule()
        result = await module.analyze({"target": "10.0.0.1"}, "Scan network", step_number=0)
        assert isinstance(result, ReasoningResult)
        assert result.module == ModuleType.REASONING
        assert result.step_number == 0
        assert len(result.plan_steps) > 0
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_analyze_includes_context(self):
        module = ReasoningModule()
        result = await module.analyze({"findings": ["port 80 open"]}, "Test", step_number=1)
        assert result.metadata["context_findings_count"] == 1
        assert result.metadata["context_keys"] == ["findings"]

    @pytest.mark.asyncio
    async def test_confidence_decreases_with_steps(self):
        module = ReasoningModule()
        r0 = await module.analyze({}, "Test", step_number=0)
        r5 = await module.analyze({}, "Test", step_number=5)
        assert r0.confidence > r5.confidence

    @pytest.mark.asyncio
    async def test_termination_at_step_10(self):
        module = ReasoningModule()
        r = await module.analyze({}, "Test", step_number=10)
        assert r.should_stop is True

    @pytest.mark.asyncio
    async def test_termination_when_objective_achieved(self):
        module = ReasoningModule()
        r = await module.analyze({"objective_achieved": True}, "Test", step_number=0)
        assert r.should_stop is True

    def test_build_plan_returns_steps(self):
        module = ReasoningModule()
        steps = module._build_plan("test objective")
        assert len(steps) == 4
        assert steps[0].description == "Reconnaissance"
        assert steps[0].confidence == 0.95


class TestGenerationModule:
    @pytest.mark.asyncio
    async def test_generate_returns_action_plan(self):
        reasoning = ReasoningResult(
            plan_steps=[ReasoningStep("Reconnaissance", "Identify hosts", 0.95)],
            reasoning="Plan",
            confidence=0.9,
            should_stop=False,
            step_number=0,
        )
        module = GenerationModule()
        plan = await module.generate(reasoning)
        assert isinstance(plan, ActionPlan)
        assert plan.module == ModuleType.GENERATION
        assert len(plan.actions) > 0
        assert plan.step_number == 0

    @pytest.mark.asyncio
    async def test_actions_limited_to_three(self):
        reasoning = ReasoningResult(
            plan_steps=[
                ReasoningStep("Reconnaissance", "A", 0.9),
                ReasoningStep("Service Enumeration", "B", 0.9),
                ReasoningStep("Vulnerability Assessment", "C", 0.9),
                ReasoningStep("Focused Exploitation", "D", 0.9),
            ],
            reasoning="Plan",
            confidence=0.9,
            should_stop=False,
            step_number=0,
        )
        module = GenerationModule()
        plan = await module.generate(reasoning)
        assert len(plan.actions) <= 3

    def test_priority_computation(self):
        module = GenerationModule()
        assert module._compute_priority(0.95) == 1
        assert module._compute_priority(0.8) == 2
        assert module._compute_priority(0.5) == 3

    def test_tool_to_action(self):
        module = GenerationModule()
        step = ReasoningStep("Reconnaissance", "Identify hosts", 0.95)
        action = module._tool_to_action("nmap", step)
        assert isinstance(action, Action)
        assert action.tool == "nmap"
        assert "targets" in action.parameters


class TestParsingModule:
    @pytest.mark.asyncio
    async def test_parse_dict_result(self):
        module = ParsingModule()
        action = Action(tool="nmap", parameters={"targets": ["10.0.0.1"]})
        result = await module.parse({"findings": [{"port": 80}]}, action, step_number=0)
        assert isinstance(result, ParsedObservation)
        assert result.module == ModuleType.PARSING
        assert len(result.findings) > 0
        assert result.findings[0]["source"] == "nmap"

    @pytest.mark.asyncio
    async def test_parse_string_result(self):
        module = ParsingModule()
        action = Action(tool="curl", parameters={})
        result = await module.parse("raw output string", action, step_number=1)
        assert len(result.findings) == 1
        assert result.findings[0]["type"] == "text"

    @pytest.mark.asyncio
    async def test_parse_none_result(self):
        module = ParsingModule()
        action = Action(tool="test", parameters={})
        result = await module.parse(None, action, step_number=2)
        assert result.findings[0]["type"] == "empty"

    @pytest.mark.asyncio
    async def test_parse_extracts_errors_from_dict(self):
        module = ParsingModule()
        action = Action(tool="nmap", parameters={})
        result = await module.parse({"error": "Connection refused"}, action, step_number=0)
        assert len(result.errors) == 1
        assert "Connection refused" in result.errors[0]

    def test_parsing_stats(self):
        module = ParsingModule()
        action = Action(tool="nmap", parameters={})
        asyncio.run(module.parse({"findings": []}, action, step_number=0))
        asyncio.run(module.parse({"findings": []}, action, step_number=1))
        stats = module.get_stats()
        assert stats.get("nmap") == 2

    @pytest.mark.asyncio
    async def test_parse_unknown_type(self):
        module = ParsingModule()
        action = Action(tool="test", parameters={})
        result = await module.parse(42, action, step_number=0)
        assert result.findings[0]["type"] == "unknown"

    @pytest.mark.asyncio
    async def test_parse_metrics(self):
        module = ParsingModule()
        action = Action(tool="nmap", parameters={})
        result = await module.parse({"findings": [{"p": 1}, {"p": 2}]}, action, step_number=0)
        assert result.metrics["findings_count"] == 2
        assert result.metrics["errors_count"] == 0
        assert result.metrics["has_data"] is True
        assert result.metrics["tool"] == "nmap"


class TestTriModuleLoop:
    @pytest.mark.asyncio
    async def test_run_returns_loop_result(self):
        loop = TriModuleLoop(
            ReasoningModule(),
            GenerationModule(),
            ParsingModule(),
            max_iterations=2,
            timeout_per_module=10.0,
        )
        result = await loop.run("Test objective", {"target": "10.0.0.1"})
        assert isinstance(result, LoopResult)
        assert result.objective == "Test objective"
        assert result.loop_id.startswith("tri_")
        assert result.total_steps > 0

    @pytest.mark.asyncio
    async def test_max_iterations_limit(self):
        loop = TriModuleLoop(
            ReasoningModule(),
            GenerationModule(),
            ParsingModule(),
            max_iterations=1,
            timeout_per_module=10.0,
        )
        result = await loop.run("Quick test", {})
        assert result.final_status in (LoopStatus.MAX_ITERATIONS, LoopStatus.COMPLETED)
        assert result.total_steps <= 2

    @pytest.mark.asyncio
    async def test_event_flow(self):
        events = []

        def collector(data):
            events.append(data)

        loop = TriModuleLoop(
            ReasoningModule(),
            GenerationModule(),
            ParsingModule(),
            max_iterations=1,
        )
        loop.event_bus.on("reasoning.complete", collector)
        loop.event_bus.on("generation.complete", collector)
        loop.event_bus.on("parsing.complete", collector)
        loop.event_bus.on("loop.complete", collector)

        await loop.run("Test events", {})
        assert len(events) >= 3

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        loop = TriModuleLoop(
            ReasoningModule(),
            GenerationModule(),
            ParsingModule(),
            max_iterations=5,
            timeout_per_module=10.0,
        )

        async def timeout_side(coro, label):
            raise asyncio.TimeoutError()

        with patch.object(loop, "_run_with_timeout", side_effect=timeout_side):
            with pytest.raises(asyncio.TimeoutError):
                await loop.run("Will timeout", {})

    @pytest.mark.asyncio
    async def test_result_contains_findings(self):
        loop = TriModuleLoop(
            ReasoningModule(),
            GenerationModule(),
            ParsingModule(),
            max_iterations=1,
            timeout_per_module=10.0,
        )
        result = await loop.run("Find vulns", {"target": "10.0.0.1"})
        assert len(result.reasoning_steps) >= 1
        assert len(result.action_plans) >= 0

    @pytest.mark.asyncio
    async def test_cancel_does_not_raise(self):
        loop = TriModuleLoop(
            ReasoningModule(),
            GenerationModule(),
            ParsingModule(),
            max_iterations=5,
        )
        loop.cancel()
        assert loop._cancelled is True

    def test_loop_result_serialization(self):
        r = LoopResult(objective="test", final_status=LoopStatus.COMPLETED, total_steps=3)
        d = r.to_dict()
        assert d["objective"] == "test"
        assert d["final_status"] == "COMPLETED"
        assert d["total_steps"] == 3
        assert d["loop_id"] == r.loop_id

    def test_reasoning_result_serialization(self):
        step = ReasoningStep("Recon", "Find hosts", 0.95)
        rr = ReasoningResult(
            plan_steps=[step],
            reasoning="Plan",
            confidence=0.9,
            should_stop=False,
            step_number=0,
        )
        d = rr.to_dict()
        assert d["module"] == "REASONING"
        assert len(d["plan_steps"]) == 1
        assert d["plan_steps"][0]["description"] == "Recon"

    @pytest.mark.asyncio
    async def test_execute_action_emulates_when_no_executor(self):
        loop = TriModuleLoop(
            ReasoningModule(),
            GenerationModule(),
            ParsingModule(),
            max_iterations=1,
        )
        result = await loop._execute_action(Action(tool="nmap", parameters={"targets": ["x"]}), 0)
        assert isinstance(result, dict)
        assert "findings" in result
