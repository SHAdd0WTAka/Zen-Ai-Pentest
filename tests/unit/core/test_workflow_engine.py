"""Test workflow engine"""

import pytest


class TestWorkflowEngine:
    """Test workflow engine"""

    def test_task_status_import(self):
        from core.workflow_engine import TaskStatus

        assert TaskStatus is not None

    def test_workflow_status_import(self):
        from core.workflow_engine import WorkflowStatus

        assert WorkflowStatus is not None

    def test_task_result_import(self):
        from core.workflow_engine import TaskResult

        assert TaskResult is not None
