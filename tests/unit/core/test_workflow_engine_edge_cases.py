import asyncio

import pytest

from core.workflow_engine import (
    FunctionTask,
    Task,
    TaskResult,
    TaskStatus,
    Workflow,
    WorkflowEngine,
    WorkflowStatus,
    task,
)


class DummyTask(Task):
    async def execute(self, context):
        return TaskResult(success=True, data=context.get("x"))


@pytest.mark.asyncio
async def test_function_task_sync_and_async_execution():
    async def afunc(context):
        return context.get("a")

    def sfunc(context):
        return context.get("b")

    t1 = FunctionTask("a", afunc)
    t2 = FunctionTask("b", sfunc)

    r1 = await t1.execute({"a": 1})
    r2 = await t2.execute({"b": 2})

    assert r1.success and r1.data == 1
    assert r2.success and r2.data == 2


@pytest.mark.asyncio
async def test_function_task_failure_returns_error_and_traceback():
    def boom(context):
        raise RuntimeError("nope")

    task_obj = FunctionTask("boom", boom)
    res = await task_obj.execute({})
    assert res.success is False
    assert "nope" in (res.error or "")
    assert "traceback" in res.metadata


def test_workflow_execution_order_and_cyclic_detection():
    wf = Workflow("w")
    a = DummyTask(name="a", task_id="a")
    b = DummyTask(name="b", task_id="b", dependencies=["a"])
    c = DummyTask(name="c", task_id="c", dependencies=["b"])
    wf.add_tasks(a, b, c)

    order = wf.get_execution_order()
    assert order[0] == ["a"]
    assert order[1] == ["b"]

    wf2 = Workflow("w2")
    x = DummyTask(name="x", task_id="x", dependencies=["y"])
    y = DummyTask(name="y", task_id="y", dependencies=["x"])
    wf2.add_tasks(x, y)
    with pytest.raises(ValueError):
        wf2.get_execution_order()


@pytest.mark.asyncio
async def test_execute_workflow_completed_and_context_save():
    async def produce(context):
        return "ok"

    wf = Workflow("main")
    t = FunctionTask(
        "t",
        produce,
        task_id="t",
        metadata={"save_to_context": True, "context_key": "k"},
    )
    wf.add_task(t)

    engine = WorkflowEngine()
    state = await engine.execute_workflow(wf, initial_context={})

    assert state.status == WorkflowStatus.COMPLETED
    assert state.context["k"] == "ok"
    assert state.tasks["t"].status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_execute_workflow_failed_when_task_fails_after_retries(
    monkeypatch,
):
    async def fail(context):
        raise RuntimeError("bad")

    wf = Workflow("f")
    t = FunctionTask("t", fail, task_id="t", max_retries=1, retry_delay=0)
    wf.add_task(t)

    async def no_sleep(*_args, **_kwargs):
        return None

    monkeypatch.setattr("core.workflow_engine.asyncio.sleep", no_sleep)
    engine = WorkflowEngine()
    state = await engine.execute_workflow(wf, initial_context={})

    assert state.status == WorkflowStatus.FAILED
    assert state.tasks["t"].status == TaskStatus.FAILED


@pytest.mark.asyncio
async def test_execute_workflow_skips_task_on_condition_false():
    wf = Workflow("cond")
    t = DummyTask(name="cond_task", task_id="ct", condition=lambda ctx: False)
    wf.add_task(t)

    engine = WorkflowEngine()
    state = await engine.execute_workflow(wf, initial_context={})
    assert state.tasks["ct"].status == TaskStatus.SKIPPED


@pytest.mark.asyncio
async def test_execute_parallel_tasks_branch():
    wf = Workflow("p")
    t1 = DummyTask(name="a", task_id="a")
    t2 = DummyTask(name="b", task_id="b")
    wf.add_tasks(t1, t2)

    engine = WorkflowEngine(max_parallel_tasks=2)
    state = await engine.execute_workflow(wf, initial_context={"x": 1})
    assert state.status == WorkflowStatus.COMPLETED
    assert state.tasks["a"].status == TaskStatus.COMPLETED
    assert state.tasks["b"].status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_cancel_workflow_emits_event():
    engine = WorkflowEngine()
    fired = []

    async def on_cancel(data):
        fired.append(data)

    engine.on("workflow.cancelled", on_cancel)

    async def never():
        await asyncio.sleep(10)

    task_obj = asyncio.create_task(never())
    engine._running_workflows["w1"] = task_obj
    await engine.cancel_workflow("w1")
    assert fired and fired[0]["workflow_id"] == "w1"
    task_obj.cancel()


def test_create_workflow_from_config_and_missing_function():
    engine = WorkflowEngine()

    config = {
        "name": "cfg",
        "tasks": [{"name": "x", "type": "function", "function": "f", "task_id": "x"}],
    }

    with pytest.raises(NotImplementedError):
        engine.create_workflow_from_config(config)


def test_task_decorator_builds_function_task():
    @task(name="decor", save_to_context=True, context_key="k")
    async def fn(context):
        return 1

    assert isinstance(fn, FunctionTask)
    assert fn.metadata["save_to_context"] is True
    assert fn.metadata["context_key"] == "k"
