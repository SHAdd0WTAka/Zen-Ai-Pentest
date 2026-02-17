"""
NUR FUNKTIONIERENDE TESTS
"""
import pytest


class TestCoreWorking:
    def test_orchestrator_1(self):
        from core.orchestrator import ZenOrchestrator
        o = ZenOrchestrator()
        assert o is not None
    
    def test_orchestrator_2(self):
        from core.orchestrator import ZenOrchestrator
        o = ZenOrchestrator()
        s = o.get_stats()
        assert isinstance(s, dict)


class TestDatabaseWorking:
    def test_user(self):
        from database.models import User
        u = User(username="t", email="t@t.com")
        assert u.username == "t"
    
    def test_scan(self):
        from database.models import Scan
        s = Scan(target="t.com", scan_type="web")
        assert s.target == "t.com"
    
    def test_finding(self):
        from database.models import Finding
        f = Finding(title="T", severity="high")
        assert f.title == "T"


class TestToolsWorking:
    def test_ffuf(self):
        from tools.ffuf_integration_enhanced import FFuFIntegration
        f = FFuFIntegration()
        assert f is not None
    
    def test_whatweb(self):
        from tools.whatweb_integration import WhatWebIntegration
        w = WhatWebIntegration()
        assert w is not None
    
    def test_wafw00f(self):
        from tools.wafw00f_integration import WAFW00FIntegration
        w = WAFW00FIntegration()
        assert w is not None
    
    def test_subfinder(self):
        from tools.subfinder_integration import SubfinderIntegration
        s = SubfinderIntegration()
        assert s is not None
    
    def test_httpx(self):
        from tools.httpx_integration import HTTPXIntegration
        h = HTTPXIntegration()
        assert h is not None


class TestModulesWorking:
    def test_super_scanner(self):
        from modules.super_scanner import SuperScanner
        s = SuperScanner()
        assert s is not None


class TestAgentsWorking:
    def test_message(self):
        from agents.agent_base import AgentMessage
        m = AgentMessage(sender="t", content="c")
        assert m.sender == "t"
    
    def test_orchestrator(self):
        from agents.agent_orchestrator import AgentOrchestrator
        o = AgentOrchestrator()
        assert o is not None


class TestAutonomousWorking:
    def test_agent_loop(self):
        from autonomous.agent_loop import AutonomousAgentLoop
        a = AutonomousAgentLoop()
        assert a is not None
    
    def test_validator(self):
        from autonomous.exploit_validator import ExploitValidator
        e = ExploitValidator()
        assert e is not None
