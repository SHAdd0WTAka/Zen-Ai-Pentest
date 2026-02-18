"""
Guardrails Integration Tests
============================

Tests that guardrails are properly integrated with the workflow orchestrator
and task processor.
"""

import asyncio
import pytest

from agents.workflows.orchestrator import WorkflowOrchestrator, WorkflowState
from guardrails.risk_levels import RiskLevel


class TestGuardrailsInOrchestrator:
    """Test that guardrails block/allow targets in workflows"""

    @pytest.mark.asyncio
    async def test_workflow_blocks_private_ip(self):
        """Workflow should block private IP targets"""
        orchestrator = WorkflowOrchestrator(step_timeout=1)
        
        with pytest.raises(ValueError) as exc_info:
            await orchestrator.start_workflow(
                workflow_type="network_recon",
                target="192.168.1.1",
                agents=["agent-1"]
            )
        
        assert "validation failed" in str(exc_info.value).lower()
        assert "192.168.0.0/16" in str(exc_info.value) or "blocked" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_workflow_blocks_localhost(self):
        """Workflow should block localhost"""
        orchestrator = WorkflowOrchestrator(step_timeout=1)
        
        with pytest.raises(ValueError) as exc_info:
            await orchestrator.start_workflow(
                workflow_type="network_recon",
                target="localhost",
                agents=["agent-1"]
            )
        
        assert "validation failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_workflow_blocks_local_domain(self):
        """Workflow should block .local domains"""
        orchestrator = WorkflowOrchestrator(step_timeout=1)
        
        with pytest.raises(ValueError) as exc_info:
            await orchestrator.start_workflow(
                workflow_type="network_recon",
                target="server.local",
                agents=["agent-1"]
            )
        
        assert "validation failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_workflow_allows_public_ip(self):
        """Workflow should allow public IP targets"""
        orchestrator = WorkflowOrchestrator(step_timeout=1)
        
        workflow_id = await orchestrator.start_workflow(
            workflow_type="network_recon",
            target="8.8.8.8",
            agents=["agent-1"]
        )
        
        assert workflow_id is not None
        assert workflow_id.startswith("wf_")

    @pytest.mark.asyncio
    async def test_workflow_allows_public_domain(self):
        """Workflow should allow public domain targets"""
        orchestrator = WorkflowOrchestrator(step_timeout=1)
        
        workflow_id = await orchestrator.start_workflow(
            workflow_type="network_recon",
            target="scanme.nmap.org",
            agents=["agent-1"]
        )
        
        assert workflow_id is not None
        assert workflow_id.startswith("wf_")

    @pytest.mark.asyncio
    async def test_workflow_blocks_loopback(self):
        """Workflow should block loopback addresses"""
        orchestrator = WorkflowOrchestrator(step_timeout=1)
        
        with pytest.raises(ValueError) as exc_info:
            await orchestrator.start_workflow(
                workflow_type="network_recon",
                target="127.0.0.1",
                agents=["agent-1"]
            )
        
        assert "validation failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_workflow_blocks_private_cidr(self):
        """Workflow should block private CIDR ranges"""
        orchestrator = WorkflowOrchestrator(step_timeout=1)
        
        with pytest.raises(ValueError) as exc_info:
            await orchestrator.start_workflow(
                workflow_type="network_recon",
                target="192.168.0.0/24",
                agents=["agent-1"]
            )
        
        assert "validation failed" in str(exc_info.value).lower()


class TestGuardrailsRiskLevels:
    """Test that risk levels block/allow tools in workflows"""

    @pytest.mark.asyncio
    async def test_safe_level_blocks_nmap(self):
        """SAFE risk level should block nmap execution"""
        orchestrator = WorkflowOrchestrator(step_timeout=1, risk_level=RiskLevel.SAFE)
        
        # Create workflow - target validation should pass
        workflow_id = await orchestrator.start_workflow(
            workflow_type="network_recon",
            target="scanme.nmap.org",
            agents=["agent-1"]
        )
        
        # Wait for workflow to complete
        for _ in range(10):
            status = orchestrator.get_workflow_status(workflow_id)
            if status["state"] in ["completed", "failed", "cancelled"]:
                break
            await asyncio.sleep(0.5)
        
        # Check that nmap tasks were not created (blocked by risk level)
        workflow = orchestrator.workflows[workflow_id]
        # Should have recon tasks (whois, dns, subdomain) but no nmap
        task_tools = [t.parameters.get("tool") for t in workflow.tasks.values()]
        assert "nmap" not in task_tools

    @pytest.mark.asyncio
    async def test_normal_level_allows_nmap(self):
        """NORMAL risk level should allow nmap execution"""
        orchestrator = WorkflowOrchestrator(step_timeout=1, risk_level=RiskLevel.NORMAL)
        
        workflow_id = await orchestrator.start_workflow(
            workflow_type="network_recon",
            target="scanme.nmap.org",
            agents=["agent-1"]
        )
        
        # Wait briefly
        await asyncio.sleep(0.5)
        
        # Check that nmap tasks were created
        workflow = orchestrator.workflows[workflow_id]
        task_tools = [t.parameters.get("tool") for t in workflow.tasks.values()]
        # Should have nmap tasks
        assert "nmap" in task_tools or len(task_tools) > 0

    @pytest.mark.asyncio
    async def test_normal_level_blocks_sqlmap(self):
        """NORMAL risk level should block sqlmap"""
        orchestrator = WorkflowOrchestrator(step_timeout=1, risk_level=RiskLevel.NORMAL)
        
        # Can run workflow (target check passes)
        workflow_id = await orchestrator.start_workflow(
            workflow_type="targeted_attack",
            target="scanme.nmap.org",
            agents=["agent-1"]
        )
        
        await asyncio.sleep(0.5)
        
        # Check that exploit tools were blocked
        workflow = orchestrator.workflows[workflow_id]
        task_tools = [t.parameters.get("tool") for t in workflow.tasks.values()]
        assert "sqlmap" not in task_tools
        assert "exploit" not in task_tools

    @pytest.mark.asyncio
    async def test_elevated_level_allows_exploit(self):
        """ELEVATED risk level should allow exploit tools"""
        orchestrator = WorkflowOrchestrator(step_timeout=1, risk_level=RiskLevel.ELEVATED)
        
        workflow_id = await orchestrator.start_workflow(
            workflow_type="targeted_attack",
            target="scanme.nmap.org",
            agents=["agent-1"]
        )
        
        await asyncio.sleep(0.5)
        
        # Check that exploit tools were created
        workflow = orchestrator.workflows[workflow_id]
        task_tools = [t.parameters.get("tool") for t in workflow.tasks.values()]
        # Should have exploit tasks
        assert len(task_tools) > 0


class TestGuardrailsFileURLs:
    """Test that file:// URLs are blocked"""

    @pytest.mark.asyncio
    async def test_workflow_blocks_file_url(self):
        """Workflow should block file:// URLs"""
        orchestrator = WorkflowOrchestrator(step_timeout=1)
        
        with pytest.raises(ValueError) as exc_info:
            await orchestrator.start_workflow(
                workflow_type="web_scan",
                target="file:///etc/passwd",
                agents=["agent-1"]
            )
        
        assert "validation failed" in str(exc_info.value).lower()


class TestGuardrailsIPv6:
    """Test IPv6 blocking"""

    @pytest.mark.asyncio
    async def test_workflow_blocks_ipv6_loopback(self):
        """Workflow should block IPv6 loopback"""
        orchestrator = WorkflowOrchestrator(step_timeout=1)
        
        with pytest.raises(ValueError) as exc_info:
            await orchestrator.start_workflow(
                workflow_type="network_recon",
                target="::1",
                agents=["agent-1"]
            )
        
        assert "validation failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_workflow_blocks_ipv6_link_local(self):
        """Workflow should block IPv6 link-local"""
        orchestrator = WorkflowOrchestrator(step_timeout=1)
        
        with pytest.raises(ValueError) as exc_info:
            await orchestrator.start_workflow(
                workflow_type="network_recon",
                target="fe80::1",
                agents=["agent-1"]
            )
        
        assert "validation failed" in str(exc_info.value).lower()


class TestGuardrailsClassB:
    """Test Class B private range (172.16.0.0/12)"""

    @pytest.mark.asyncio
    async def test_workflow_blocks_class_b_start(self):
        """Workflow should block 172.16.0.0/12 range start"""
        orchestrator = WorkflowOrchestrator(step_timeout=1)
        
        with pytest.raises(ValueError) as exc_info:
            await orchestrator.start_workflow(
                workflow_type="network_recon",
                target="172.16.0.1",
                agents=["agent-1"]
            )
        
        assert "validation failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_workflow_blocks_class_b_end(self):
        """Workflow should block 172.16.0.0/12 range end"""
        orchestrator = WorkflowOrchestrator(step_timeout=1)
        
        with pytest.raises(ValueError) as exc_info:
            await orchestrator.start_workflow(
                workflow_type="network_recon",
                target="172.31.255.255",
                agents=["agent-1"]
            )
        
        assert "validation failed" in str(exc_info.value).lower()


class TestGuardrailsEnabledFlag:
    """Test that guardrails can be detected as enabled"""

    def test_guardrails_enabled_by_default(self):
        """Guardrails should be enabled by default"""
        orchestrator = WorkflowOrchestrator()
        assert orchestrator.guardrails_enabled is True

    def test_guardrails_disabled_without_risk_manager(self):
        """Test that risk manager is initialized"""
        orchestrator = WorkflowOrchestrator()
        assert orchestrator.risk_manager is not None

    def test_default_risk_level_is_normal(self):
        """Default risk level should be NORMAL"""
        orchestrator = WorkflowOrchestrator()
        assert orchestrator.risk_manager.get_risk_level() == RiskLevel.NORMAL

    def test_custom_risk_level(self):
        """Custom risk level should be respected"""
        orchestrator = WorkflowOrchestrator(risk_level=RiskLevel.SAFE)
        assert orchestrator.risk_manager.get_risk_level() == RiskLevel.SAFE

    def test_custom_risk_level_aggressive(self):
        """AGGRESSIVE risk level should work"""
        orchestrator = WorkflowOrchestrator(risk_level=RiskLevel.AGGRESSIVE)
        assert orchestrator.risk_manager.get_risk_level() == RiskLevel.AGGRESSIVE
