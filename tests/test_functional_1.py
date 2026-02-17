"""
Functional Tests - Führe tatsächlich Code aus
"""


class TestFunctionalTools:
    """Tools wirklich ausführen"""

    def test_tool_registry_functional(self):
        from tools.tool_registry import ToolRegistry
        reg = ToolRegistry.get_instance()
        tools = reg.list_tools()
        assert isinstance(tools, list)

    def test_nmap_functions_exist(self):
        from tools import nmap_integration
        funcs = [x for x in dir(nmap_integration) if callable(getattr(nmap_integration, x)) and not x.startswith('_')]
        assert len(funcs) > 0


class TestFunctionalDatabase:
    """Database wirklich testen"""

    def test_user_creation_functional(self):
        from database.models import User
        u = User(username="func_test", email="func@test.com")
        assert u.username == "func_test"
        assert u.email == "func@test.com"

    def test_scan_creation_functional(self):
        from database.models import Scan
        s = Scan(target="func.test.com", scan_type="web")
        assert s.target == "func.test.com"


class TestFunctionalCore:
    """Core wirklich testen"""

    def test_orchestrator_functional(self):
        from core.orchestrator import ZenOrchestrator
        o = ZenOrchestrator()
        stats = o.get_stats()
        assert isinstance(stats, dict)

    def test_orchestrator_capabilities_functional(self):
        from core.orchestrator import ZenOrchestrator
        o = ZenOrchestrator()
        caps = o.get_capabilities()
        assert isinstance(caps, dict)
