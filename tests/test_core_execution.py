"""
Core Execution Tests - Führt wirklich Code aus
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCoreOrchestratorExecution:
    """Core Orchestrator wirklich testen"""
    
    def test_orchestrator_import_and_creation(self):
        from core.orchestrator import ZenOrchestrator
        orch = ZenOrchestrator()
        assert orch is not None
    
    def test_orchestrator_has_attributes(self):
        from core.orchestrator import ZenOrchestrator
        orch = ZenOrchestrator()
        assert hasattr(orch, 'request_count')
        assert hasattr(orch, 'results_cache')
    
    def test_orchestrator_get_stats(self):
        from core.orchestrator import ZenOrchestrator
        orch = ZenOrchestrator()
        stats = orch.get_stats()
        assert isinstance(stats, dict)
    
    def test_orchestrator_get_capabilities(self):
        from core.orchestrator import ZenOrchestrator
        orch = ZenOrchestrator()
        caps = orch.get_capabilities()
        assert isinstance(caps, dict)
    
    def test_orchestrator_repr(self):
        from core.orchestrator import ZenOrchestrator
        orch = ZenOrchestrator()
        r = repr(orch)
        assert isinstance(r, str)
    
    def test_orchestrator_str(self):
        from core.orchestrator import ZenOrchestrator
        orch = ZenOrchestrator()
        s = str(orch)
        assert isinstance(s, str)


class TestDatabaseModelsExecution:
    """Database Models wirklich testen"""
    
    def test_user_creation(self):
        from database.models import User
        user = User(username="test", email="test@test.com")
        assert user.username == "test"
        assert user.email == "test@test.com"
    
    def test_user_repr(self):
        from database.models import User
        user = User(username="testuser")
        r = repr(user)
        assert isinstance(r, str)
    
    def test_scan_creation(self):
        from database.models import Scan
        scan = Scan(target="example.com", scan_type="network")
        assert scan.target == "example.com"
        assert scan.scan_type == "network"
    
    def test_finding_creation(self):
        from database.models import Finding
        finding = Finding(title="Test Finding", severity="high")
        assert finding.title == "Test Finding"
        assert finding.severity == "high"
    
    def test_report_creation(self):
        from database.models import Report
        report = Report(format="pdf", status="pending")
        assert report.format == "pdf"


class TestUtilsExecution:
    """Utils wirklich testen"""
    
    def test_colorize_function(self):
        try:
            from utils.helpers import colorize
            result = colorize("test", "red")
            assert isinstance(result, str)
        except ImportError:
            pytest.skip("colorize nicht verfügbar")
    
    def test_banner_function(self):
        try:
            from utils.helpers import print_banner
            assert callable(print_banner)
        except ImportError:
            pytest.skip("print_banner nicht verfügbar")


class TestAutonomousExecution:
    """Autonomous Module wirklich testen"""
    
    def test_autonomous_agent_loop_import(self):
        from autonomous.agent_loop import AutonomousAgentLoop
        assert AutonomousAgentLoop is not None
    
    def test_exploit_validator_import(self):
        from autonomous.exploit_validator import ExploitValidator
        assert ExploitValidator is not None


class TestToolsInitExecution:
    """Tools Init wirklich testen"""
    
    def test_tools_init_available_tools(self):
        import tools
        # Prüfe ob __all__ existiert
        if hasattr(tools, '__all__'):
            assert isinstance(tools.__all__, list)
    
    def test_tools_nmap_quick_scan(self):
        from tools.nmap_integration import nmap_quick_scan
        assert callable(nmap_quick_scan)
    
    def test_tools_nmap_vuln_scan(self):
        from tools.nmap_integration import nmap_vuln_scan
        assert callable(nmap_vuln_scan)
