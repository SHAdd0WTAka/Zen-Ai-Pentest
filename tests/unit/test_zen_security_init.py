"""Unit tests for zen_security/__init__.py with mocked submodules."""

import sys
import types
from unittest.mock import AsyncMock, MagicMock

import pytest


def _inject_zen_security_mocks():
    """Populate sys.modules with lightweight mocks for zen_security submodules."""
    packages = [
        "zen_security.adversarial",
        "zen_security.audit",
        "zen_security.core",
        "zen_security.guardrails",
        "zen_security.risk_engine",
    ]
    for pkg in packages:
        if pkg not in sys.modules:
            mod = types.ModuleType(pkg)
            mod.__path__ = []
            sys.modules[pkg] = mod

    def _make_enum(name, members):
        class _EnumLike:
            __slots__ = ("value",)

            def __init__(self, value):
                self.value = value

            def __eq__(self, other):
                return isinstance(other, _EnumLike) and self.value == other.value

            def __hash__(self):
                return hash(self.value)

            def __repr__(self):
                return f"{name}({self.value!r})"

        for key, val in members.items():
            setattr(_EnumLike, key, _EnumLike(val))
        return _EnumLike

    enums = {
        "AgentRole": {"SCANNER": "scanner"},
        "CredentialStatus": {"ACTIVE": "active"},
        "ActionType": {"PORT_SCAN": "port_scan"},
        "RiskLevel": {"LOW": "low", "MEDIUM": "medium", "HIGH": "high"},
        "ValidationResult": {
            "APPROVED": "approved",
            "DENIED": "denied",
            "ESCALATION_REQUIRED": "escalation_required",
        },
        "AuditEventType": {
            "CONFIG_CHANGED": "config_changed",
            "AGENT_CREATED": "agent_created",
            "AGENT_DESTROYED": "agent_destroyed",
            "ACTION_APPROVED": "action_approved",
            "ACTION_DENIED": "action_denied",
            "SECURITY_ALERT": "security_alert",
        },
        "ComplianceFramework": {"ISO27001": "iso27001"},
        "CertificateStatus": {"VALID": "valid"},
        "Severity": {"LOW": "low"},
        "VulnerabilityType": {"XSS": "xss"},
        "TestSeverity": {"LOW": "low"},
        "AttackVector": {"NETWORK": "network"},
    }

    enum_map = {name: _make_enum(name, members) for name, members in enums.items()}

    module_exports = {
        "zen_security.adversarial.red_team_framework": [
            "AdversarialTest",
            "AttackVector",
            "AuthenticationBypassTests",
            "FuzzingEngine",
            "InjectionTests",
            "RedTeamOrchestrator",
            "SecurityTestResult",
            "TestSeverity",
        ],
        "zen_security.audit.tamper_proof_logger": [
            "AuditEvent",
            "AuditEventType",
            "ComplianceFramework",
            "DigitalSignatureManager",
            "EvidenceChain",
            "TamperProofAuditLogger",
        ],
        "zen_security.core.mtls_auth": [
            "CertificateAuthority",
            "CertificateBundle",
            "CertificateStatus",
            "SecureServiceMesh",
            "ServiceIdentity",
            "mTLSContextManager",
        ],
        "zen_security.core.temporal_credentials": [
            "ROLE_PERMISSIONS",
            "AgentIdentity",
            "AgentRole",
            "CredentialStatus",
            "TemporalCredential",
            "TemporalCredentialManager",
            "create_agent_identity",
        ],
        "zen_security.guardrails.enhanced_validator": [
            "ActionType",
            "BudgetConfig",
            "BudgetManager",
            "CommandValidator",
            "EnhancedGuardrailsValidator",
            "GuardrailDecision",
            "IPDomainFilter",
            "RateLimitConfig",
            "RateLimiter",
            "RiskLevel",
            "ValidationResult",
        ],
        "zen_security.risk_engine.ml_risk_engine": [
            "BayesianFalsePositiveReducer",
            "BehavioralAnalyzer",
            "BehavioralProfile",
            "CVSSScore",
            "EPSSScore",
            "RiskScoringEngine",
            "Severity",
            "VulnerabilityFinding",
            "VulnerabilityType",
            "calculate_cvss_score",
        ],
    }

    enum_names = set(enums.keys())
    for mod_name, names in module_exports.items():
        mod = types.ModuleType(mod_name)
        for n in names:
            if n in enum_names:
                setattr(mod, n, enum_map[n])
            elif n == "create_agent_identity":
                setattr(mod, n, AsyncMock(name=n))
            else:
                setattr(mod, n, MagicMock(name=n))
        sys.modules[mod_name] = mod


_inject_zen_security_mocks()

import zen_security
from zen_security import ZeroTrustSecurity


def _reset_async_mocks(security):
    """Configure deterministic mocks on a fresh ZeroTrustSecurity instance."""
    security.credential_manager.connect = AsyncMock()
    security.credential_manager.disconnect = AsyncMock()
    security.credential_manager.issue_credential = AsyncMock()
    security.credential_manager.revoke_all_agent_credentials = AsyncMock()
    security.credential_manager.get_statistics = MagicMock(return_value={"cred_stats": True})

    security.service_mesh.initialize = AsyncMock()
    security.service_mesh.register_service = AsyncMock(
        return_value={
            "spiffe_id": "spiffe://test",
            "certificate": MagicMock(name="certificate"),
        }
    )
    security.service_mesh.ca = MagicMock()
    security.service_mesh.ca.revoke_certificate = MagicMock()

    security.guardrails.initialize = AsyncMock()
    security.guardrails.set_audit_callback = MagicMock()
    security.guardrails.validate_action = AsyncMock()
    security.guardrails.ip_filter = MagicMock()
    security.guardrails.ip_filter.redis = MagicMock()
    security.guardrails.ip_filter.redis.close = AsyncMock()

    security.risk_engine.initialize = AsyncMock()
    security.risk_engine.score_finding = AsyncMock()
    security.risk_engine.get_statistics = MagicMock(return_value={"risk_stats": True})

    security.audit_logger.connect = AsyncMock()
    security.audit_logger.disconnect = AsyncMock()
    security.audit_logger.log_event = AsyncMock()
    security.audit_logger.create_evidence_chain = AsyncMock()
    security.audit_logger.verify_integrity = AsyncMock(return_value={"valid": True})
    security.audit_logger.generate_compliance_report = AsyncMock(return_value={"report": True})
    security.audit_logger.get_statistics = AsyncMock(return_value={"audit_stats": True})
    security.audit_logger.redis = MagicMock()
    security.audit_logger.redis.close = AsyncMock()

    zen_security.create_agent_identity = AsyncMock(return_value=MagicMock(permissions={"perm:read"}))


@pytest.fixture
def security():
    inst = ZeroTrustSecurity(redis_url="redis://mock:6379")
    _reset_async_mocks(inst)
    return inst


class TestZeroTrustSecurityInit:
    def test_init_creates_components(self):
        s = ZeroTrustSecurity(redis_url="redis://custom:6379", config_path="/tmp/cfg")
        assert s.redis_url == "redis://custom:6379"
        assert s.config_path == "/tmp/cfg"
        assert s._initialized is False
        zen_security.TemporalCredentialManager.assert_called_once_with(redis_url="redis://custom:6379")
        zen_security.SecureServiceMesh.assert_called_once_with(redis_url="redis://custom:6379")
        zen_security.EnhancedGuardrailsValidator.assert_called_once_with(redis_url="redis://custom:6379")
        zen_security.RiskScoringEngine.assert_called_once_with(redis_url="redis://custom:6379")
        zen_security.TamperProofAuditLogger.assert_called_once_with(redis_url="redis://custom:6379")


class TestZeroTrustSecurityLifecycle:
    async def test_initialize_connects_components(self, security):
        await security.initialize()
        assert security._initialized is True
        security.credential_manager.connect.assert_awaited_once()
        security.service_mesh.initialize.assert_awaited_once()
        security.guardrails.initialize.assert_awaited_once()
        security.risk_engine.initialize.assert_awaited_once()
        security.audit_logger.connect.assert_awaited_once()
        security.guardrails.set_audit_callback.assert_called_once_with(security._audit_guardrail_decision)
        security.audit_logger.log_event.assert_awaited_once()

    async def test_initialize_already_initialized_noop(self, security):
        await security.initialize()
        security.credential_manager.connect.reset_mock()
        await security.initialize()
        security.credential_manager.connect.assert_not_awaited()


class TestZeroTrustSecurityProvision:
    async def test_provision_agent(self, security):
        security._initialized = True
        identity_mock = MagicMock(permissions={"perm:a", "perm:b"})
        credential_mock = MagicMock(credential_id="cred-123")
        cert_mock = MagicMock(name="cert")
        zen_security.create_agent_identity.return_value = identity_mock
        security.credential_manager.issue_credential.return_value = credential_mock
        security.service_mesh.register_service.return_value = {
            "spiffe_id": "spiffe://agent-001",
            "certificate": cert_mock,
        }

        result = await security.provision_agent(
            agent_id="agent-001",
            role=zen_security.AgentRole.SCANNER,
        )

        zen_security.create_agent_identity.assert_awaited_once_with(
            agent_id="agent-001",
            role=zen_security.AgentRole.SCANNER,
            custom_permissions=None,
        )
        call_args = security.credential_manager.issue_credential.await_args
        assert call_args.args[0] is identity_mock
        assert call_args.kwargs["ttl"] == 3600
        assert set(call_args.kwargs["scope"]) == identity_mock.permissions

        security.service_mesh.register_service.assert_awaited_once_with(
            service_id="agent-001",
            service_type=zen_security.AgentRole.SCANNER.value,
            host="agent-001.zen-pentest.svc.cluster.local",
            port=8443,
        )
        security.audit_logger.log_event.assert_awaited_once()
        assert result["identity"] is identity_mock
        assert result["credential"] is credential_mock
        assert result["certificate"] is cert_mock
        assert result["spiffe_id"] == "spiffe://agent-001"

    async def test_provision_agent_not_initialized_raises(self, security):
        with pytest.raises(RuntimeError, match="not initialized"):
            await security.provision_agent("agent-001", zen_security.AgentRole.SCANNER)


class TestZeroTrustSecurityRevoke:
    async def test_revoke_agent(self, security):
        await security.revoke_agent("agent-001", reason="test")
        security.credential_manager.revoke_all_agent_credentials.assert_awaited_once_with("agent-001", "test")
        security.service_mesh.ca.revoke_certificate.assert_called_once_with("agent-001")
        security.audit_logger.log_event.assert_awaited_once()


class TestZeroTrustSecurityActions:
    async def test_validate_agent_action_delegates_to_guardrails(self, security):
        decision = MagicMock()
        security.guardrails.validate_action.return_value = decision
        result = await security.validate_agent_action(
            agent_id="a1",
            action_type=zen_security.ActionType.PORT_SCAN,
            target="example.com",
            command="nmap",
            risk_level=zen_security.RiskLevel.LOW,
            estimated_cost={"cpu": 1.0},
        )
        assert result is decision
        security.guardrails.validate_action.assert_awaited_once_with(
            agent_id="a1",
            action_type=zen_security.ActionType.PORT_SCAN,
            target="example.com",
            command="nmap",
            risk_level=zen_security.RiskLevel.LOW,
            estimated_cost={"cpu": 1.0},
        )

    async def test_score_vulnerability(self, security):
        finding = MagicMock()
        scored = MagicMock()
        security.risk_engine.score_finding.return_value = scored
        result = await security.score_vulnerability(finding, context={"foo": "bar"})
        assert result is scored
        security.risk_engine.score_finding.assert_awaited_once_with(finding, {"foo": "bar"})

    async def test_create_evidence(self, security):
        chain = MagicMock()
        security.audit_logger.create_evidence_chain.return_value = chain
        files = {"screenshot.png": b"data"}
        result = await security.create_evidence(
            finding_id="f-1",
            evidence_type="screenshot",
            description="desc",
            files=files,
            collected_by="agent-1",
        )
        assert result is chain
        security.audit_logger.create_evidence_chain.assert_awaited_once_with(
            finding_id="f-1",
            evidence_type="screenshot",
            description="desc",
            files=files,
            collected_by="agent-1",
        )

    async def test_verify_audit_integrity(self, security):
        expected = {"valid": True, "count": 10}
        security.audit_logger.verify_integrity.return_value = expected
        result = await security.verify_audit_integrity()
        assert result == expected

    async def test_generate_compliance_report(self, security):
        from datetime import datetime

        expected = {"framework": "iso"}
        security.audit_logger.generate_compliance_report.return_value = expected
        result = await security.generate_compliance_report(
            zen_security.ComplianceFramework.ISO27001,
            datetime(2024, 1, 1),
            datetime(2024, 12, 31),
        )
        assert result == expected
        security.audit_logger.generate_compliance_report.assert_awaited_once()

    async def test_get_statistics(self, security):
        result = await security.get_statistics()
        assert result == {
            "credentials": {"cred_stats": True},
            "audit": {"audit_stats": True},
            "risk_engine": {"risk_stats": True},
        }
        security.credential_manager.get_statistics.assert_called_once()
        security.audit_logger.get_statistics.assert_awaited_once()
        security.risk_engine.get_statistics.assert_called_once()


class TestZeroTrustSecurityAuditCallback:
    async def test_audit_guardrail_decision_approved(self, security):
        from types import SimpleNamespace

        decision = SimpleNamespace(
            result=zen_security.ValidationResult.APPROVED,
            action_type=zen_security.ActionType.PORT_SCAN,
            agent_id="a1",
            reason="ok",
            risk_level=zen_security.RiskLevel.LOW,
            metadata={"target": "t"},
        )
        await security._audit_guardrail_decision(decision)
        call_kwargs = security.audit_logger.log_event.await_args.kwargs
        assert call_kwargs["event_type"] is zen_security.AuditEventType.ACTION_APPROVED

    async def test_audit_guardrail_decision_denied(self, security):
        from types import SimpleNamespace

        decision = SimpleNamespace(
            result=zen_security.ValidationResult.DENIED,
            action_type=zen_security.ActionType.PORT_SCAN,
            agent_id="a1",
            reason="bad",
            risk_level=zen_security.RiskLevel.HIGH,
            metadata={},
        )
        await security._audit_guardrail_decision(decision)
        call_kwargs = security.audit_logger.log_event.await_args.kwargs
        assert call_kwargs["event_type"] is zen_security.AuditEventType.ACTION_DENIED

    async def test_audit_guardrail_decision_escalation(self, security):
        from types import SimpleNamespace

        decision = SimpleNamespace(
            result=zen_security.ValidationResult.ESCALATION_REQUIRED,
            action_type=zen_security.ActionType.PORT_SCAN,
            agent_id="a1",
            reason="escalate",
            risk_level=zen_security.RiskLevel.MEDIUM,
            metadata={"target": "x"},
        )
        await security._audit_guardrail_decision(decision)
        call_kwargs = security.audit_logger.log_event.await_args.kwargs
        assert call_kwargs["event_type"] is zen_security.AuditEventType.SECURITY_ALERT


class TestZeroTrustSecurityClose:
    async def test_close_disconnects_components(self, security):
        await security.close()
        security.credential_manager.disconnect.assert_awaited_once()
        security.audit_logger.redis.close.assert_awaited_once()
        security.guardrails.ip_filter.redis.close.assert_awaited_once()
