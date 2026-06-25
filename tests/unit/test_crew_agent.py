import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest

from agents.agent_base import AgentRole
from agents.crew_agent import Crew, CrewAgent, CrewResult, CrewTask
from core.workflow_engine import EventBus


class TestCrewAgent:
    def test_create_agent_with_role_goal_backstory(self):
        agent = CrewAgent(
            name="TestBot",
            role="Vulnerability Analyst",
            goal="Find all vulnerabilities",
            backstory="Expert in security analysis",
            agent_role=AgentRole.ANALYST,
        )
        assert agent.name == "TestBot"
        assert agent.role_description == "Vulnerability Analyst"
        assert agent.goal == "Find all vulnerabilities"
        assert agent.backstory == "Expert in security analysis"
        assert agent.role == AgentRole.ANALYST
        assert agent.allow_delegation is False

    def test_agent_tools(self):
        def mock_tool():
            pass

        agent = CrewAgent(name="ToolBot", role="Scanner", goal="Scan", tools=[mock_tool])
        assert agent.has_tool("mock_tool") is True
        assert agent.has_tool("nonexistent") is False
        assert "mock_tool" in agent.tool_names()

    def test_agent_execute_task(self):
        agent = CrewAgent(name="ExecBot", role="Worker", goal="Execute")
        task = {"id": "task-1", "description": "Do something"}
        result = asyncio.run(agent.execute_task(task))
        assert result["task_id"] == "task-1"
        assert result["agent"] == "ExecBot"
        assert "Do something" in result["output"]

    def test_agent_get_summary(self):
        agent = CrewAgent(
            name="SummaryBot",
            role="Reporter",
            goal="Summarize",
            agent_role=AgentRole.REPORTER,
        )
        summary = agent.get_summary()
        assert summary["name"] == "SummaryBot"
        assert summary["role"] == "Reporter"
        assert summary["allow_delegation"] is False
        assert summary["assigned_tasks"] == 0

    def test_agent_delegation(self):
        async def run():
            target = CrewAgent(name="TargetBot", role="Worker", goal="Work")
            orchestrator = AsyncMock()
            delegator = CrewAgent(
                name="LeadBot",
                role="Manager",
                goal="Manage",
                allow_delegation=True,
                orchestrator=orchestrator,
            )
            task = CrewTask(id="del-task", description="Delegated work")
            result = await delegator.delegate_work(task, target)
            assert result["task_id"] == "del-task"
            assert result["agent"] == "TargetBot"

        asyncio.run(run())


class TestCrewTask:
    def test_create_task(self):
        task = CrewTask(description="Scan ports", expected_output="List of ports")
        assert task.id.startswith("task_")
        assert task.description == "Scan ports"
        assert task.expected_output == "List of ports"
        assert task._status == "pending"

    def test_task_to_dict(self):
        agent = CrewAgent(name="DictBot", role="Test", goal="Test")
        task = CrewTask(
            id="t1",
            description="Test",
            expected_output="OK",
            agent=agent,
        )
        d = task.to_dict()
        assert d["id"] == "t1"
        assert d["agent"] == "DictBot"
        assert d["status"] == "pending"

    def test_task_set_output(self):
        task = CrewTask(description="Test")
        task.set_output({"result": "done"})
        assert task._output == {"result": "done"}
        assert task._status == "completed"

    def test_task_set_failed(self):
        task = CrewTask(description="Test")
        task.set_failed("Something broke")
        assert task._status == "failed"
        assert "error" in task._output

    def test_task_requires_tools(self):
        def tool_a():
            pass

        def tool_b():
            pass

        task = CrewTask(description="Test", tools=[tool_a, tool_b])
        names = task.requires_tools()
        assert "tool_a" in names
        assert "tool_b" in names

    def test_task_context_dependencies(self):
        dep = CrewTask(description="Dep")
        task = CrewTask(description="Main", context=[dep])
        assert dep in task.context
        assert dep.id in task.to_dict()["context_ids"]


class TestCrew:
    @pytest.mark.asyncio
    async def test_sequential_execution(self):
        a1 = CrewAgent(name="Alpha", role="Scanner", goal="Scan targets")
        a2 = CrewAgent(name="Beta", role="Analyzer", goal="Analyze results")
        t1 = CrewTask(description="Scan phase 1", expected_output="hosts")
        t2 = CrewTask(description="Analyze phase 2", expected_output="report", context=[t1])

        crew = Crew(agents=[a1, a2], tasks=[t1, t2], process="sequential")
        result = await crew.kickoff()
        assert isinstance(result, CrewResult)
        assert result.successful is True
        assert len(result.tasks_output) == 2
        assert result.usage_metrics["completed_tasks"] == 2
        assert result.usage_metrics["failed_tasks"] == 0

    @pytest.mark.asyncio
    async def test_hierarchical_execution_with_manager(self):
        mgr = CrewAgent(
            name="Manager",
            role="Manager",
            goal="Coordinate team",
            allow_delegation=True,
        )
        worker = CrewAgent(name="Worker", role="Analyst", goal="Analyze")
        task = CrewTask(description="Perform analysis", expected_output="findings")

        crew = Crew(
            agents=[mgr, worker],
            tasks=[task],
            process="hierarchical",
            manager_agent=mgr,
        )
        result = await crew.kickoff()
        assert result.successful is True
        assert result.usage_metrics["delegations"] >= 1

    @pytest.mark.asyncio
    async def test_hierarchical_auto_selects_manager(self):
        delegator = CrewAgent(
            name="Senior",
            role="Lead",
            goal="Lead team",
            allow_delegation=True,
        )
        worker = CrewAgent(name="Junior", role="Analyst", goal="Analyze")
        task = CrewTask(description="Do work", expected_output="work")

        crew = Crew(
            agents=[delegator, worker],
            tasks=[task],
            process="hierarchical",
        )
        result = await crew.kickoff()
        assert result.successful is True

    @pytest.mark.asyncio
    async def test_crew_events_emitted(self):
        events = []

        def collector(data):
            events.append(data)

        agent = CrewAgent(name="EventBot", role="Scanner", goal="Scan")
        task = CrewTask(description="Test event", expected_output="ok")
        bus = EventBus()
        bus.on("crew.started", collector)
        bus.on("crew.completed", collector)

        crew = Crew(agents=[agent], tasks=[task], event_bus=bus)
        await crew.kickoff()
        assert len(events) >= 2

    @pytest.mark.asyncio
    async def test_delegation_logic(self):
        tool_agent = CrewAgent(
            name="ToolUser",
            role="Scanner",
            goal="Scan",
            tools=[lambda: None],
        )
        no_tool = CrewAgent(name="NoTool", role="Helper", goal="Help")
        t1 = CrewTask(description="Scan ports", expected_output="ports", tools=[lambda: None])

        crew = Crew(agents=[no_tool, tool_agent], tasks=[t1])
        assigned = crew._assign_task(t1)
        assert assigned.name == "ToolUser"

    @pytest.mark.asyncio
    async def test_task_skipped_when_dependency_missing(self):
        a1 = CrewAgent(name="Agent", role="Worker", goal="Work")
        dep = CrewTask(id="dep-task", description="Must run first")
        main = CrewTask(description="Depends on dep", context=[dep])

        crew = Crew(agents=[a1], tasks=[main])
        result = await crew.kickoff()
        assert result.usage_metrics["skipped_tasks"] >= 1

    @pytest.mark.asyncio
    async def test_agent_task_assignment_tracking(self):
        agent = CrewAgent(name="BusyBot", role="Worker", goal="Work")
        task = CrewTask(description="Task 1", expected_output="done")
        crew = Crew(agents=[agent], tasks=[task])
        await crew.kickoff()
        assert len(agent._assigned_tasks) == 1

    def test_find_agent_methods(self):
        a1 = CrewAgent(name="FindMe", role="Specialist", goal="Find")
        a2 = CrewAgent(name="Other", role="Generalist", goal="Other")
        crew = Crew(agents=[a1, a2], tasks=[CrewTask(description="d")])
        assert crew.find_agent_by_name("FindMe") is a1
        assert crew.find_agent_by_name("Nobody") is None
        assert crew.find_agent_by_role("Specialist") is a1
        assert crew.find_agent_by_role("missing") is None

    def test_crew_validation(self):
        with pytest.raises(ValueError, match="At least one agent"):
            Crew(agents=[], tasks=[CrewTask(description="d")])
        with pytest.raises(ValueError, match="At least one task"):
            Crew(agents=[CrewAgent(name="a", role="r", goal="g")], tasks=[])
        with pytest.raises(ValueError, match="Unknown process"):
            Crew(
                agents=[CrewAgent(name="a", role="r", goal="g")],
                tasks=[CrewTask(description="d")],
                process="invalid",
            )

    def test_crew_result_successful(self):
        r1 = CrewResult(tasks_output=[{"status": "completed"}, {"status": "completed"}])
        assert r1.successful is True
        r2 = CrewResult(tasks_output=[{"status": "completed"}, {"status": "failed"}])
        assert r2.successful is False

    def test_crew_build_result(self):
        agent = CrewAgent(name="ResultBot", role="Test", goal="Test")
        task = CrewTask(description="Test task", agent=agent)
        task.set_output({"key": "val"})
        crew = Crew(agents=[agent], tasks=[task])
        result = crew._build_result()
        assert len(result.tasks_output) == 1
        assert result.tasks_output[0]["status"] == "completed"
        assert result.tasks_output[0]["agent"] == "ResultBot"


@pytest.mark.asyncio
async def test_create_crew_convenience():
    from agents.crew_agent import create_crew

    agent = CrewAgent(name="ConvBot", role="Test", goal="Test")
    task = CrewTask(description="Test")
    crew = create_crew(agents=[agent], tasks=[task])
    assert isinstance(crew, Crew)
    assert crew.process == "sequential"
