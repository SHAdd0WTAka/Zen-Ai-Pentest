"""Test agents v2 imports"""

import pytest


class TestAgentsV2Imports:
    """Test agents v2 can be imported"""

    def test_agent_client_import(self):
        from agents.v2.agent_client import AgentClient

        assert AgentClient is not None

    def test_agent_task_processor_import(self):
        from agents.v2.agent_task_processor import TaskProcessor

        assert TaskProcessor is not None

    def test_auth_manager_import(self):
        from agents.v2.auth_manager import AgentAuthenticator

        assert AgentAuthenticator is not None

    def test_message_queue_import(self):
        from agents.v2.message_queue import MessageStatus

        assert MessageStatus is not None

    def test_secure_message_import(self):
        from agents.v2.secure_message import SecureMessage

        assert SecureMessage is not None

    def test_worker_agent_import(self):
        from agents.v2.worker_agent import WorkerAgent

        assert WorkerAgent is not None
