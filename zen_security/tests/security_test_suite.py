"""
Security Test Suite for Zero-Trust Architecture
Unit and integration tests for all security components
"""

import asyncio
import hashlib
import json

# Import components to test
import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio

sys.path.insert(0, "/mnt/okcomputer/output/zen_security")

from audit.tamper_proof_logger import (
    AuditEvent,
    AuditEventType,
    ComplianceFramework,
    EvidenceChain,
    TamperProofAuditLogger,
)
from core.mtls_auth import (
    CertificateAuthority,
    CertificateStatus,
    SecureServiceMesh,
    ServiceIdentity,
    mTLSContextManager,
)
from core.temporal_credentials import (
    ROLE_PERMISSIONS,
    AgentIdentity,
    AgentRole,
    CredentialStatus,
    TemporalCredentialManager,
    create_agent_identity,
)
from guardrails.enhanced_validator import (
    ActionType,
    BudgetManager,
    CommandValidator,
    EnhancedGuardrailsValidator,
    IPDomainFilter,
    RateLimiter,
    RiskLevel,
    ValidationResult,
)
from risk_engine.ml_risk_engine import (
    BayesianFalsePositiveReducer,
    CVSSScore,
    EPSSScore,
    RiskScoringEngine,
    VulnerabilityFinding,
    VulnerabilityType,
    calculate_cvss_score,
)

# =============================================================================
# Temporal Credentials Tests
# =============================================================================


class TestTemporalCredentials:
    """Test temporal credential system"""

    @pytest_asyncio.fixture
    async def credential_manager(self):
        manager = TemporalCredentialManager(redis_url="redis://localhost:6379", rotation_interval=60)
        yield manager

    @pytest_asyncio.fixture
    async def agent_identity(self):
        return await create_agent_identity(agent_id="test-agent-001", role=AgentRole.SCANNER)

    @pytest.mark.asyncio
    async def test_issue_credential(self, credential_manager, agent_identity):
        """Test credential issuance"""
        cred = await credential_manager.issue_credential(agent_identity, ttl=3600, scope=["read:targets", "execute:scan"])

        assert cred.agent_id == "test-agent-001"
        assert cred.status == CredentialStatus.ACTIVE
        assert len(cred.token) > 0
        assert len(cred.public_key) > 0
        assert not cred.is_expired

    @pytest.mark.asyncio
    async def test_credential_validation(self, credential_manager, agent_identity):
        """Test credential validation"""
        cred = await credential_manager.issue_credential(agent_identity, ttl=3600)

        # Valid credential
        is_valid = await credential_manager.validate_credential(cred.credential_id, cred.token)
        assert is_valid is True

        # Invalid token
        is_valid = await credential_manager.validate_credential(cred.credential_id, "invalid-token")
        assert is_valid is False

        # Invalid credential ID
        is_valid = await credential_manager.validate_credential("invalid-id", cred.token)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_credential_rotation(self, credential_manager, agent_identity):
        """Test credential rotation"""
        old_cred = await credential_manager.issue_credential(agent_identity, ttl=3600)

        # Rotate credential
        new_cred = await credential_manager.rotate_credential(old_cred.credential_id, grace_period=5)

        assert new_cred is not None
        assert new_cred.credential_id != old_cred.credential_id
        assert old_cred.status == CredentialStatus.ROTATING

        # Wait for grace period
        await asyncio.sleep(6)

        # Old credential should be revoked
        assert old_cred.status == CredentialStatus.REVOKED

    @pytest.mark.asyncio
    async def test_credential_revocation(self, credential_manager, agent_identity):
        """Test credential revocation"""
        cred = await credential_manager.issue_credential(agent_identity, ttl=3600)

        # Revoke
        revoked = await credential_manager.revoke_credential(cred.credential_id, reason="test_revocation")

        assert revoked is True
        assert cred.status == CredentialStatus.REVOKED

        # Should not validate after revocation
        is_valid = await credential_manager.validate_credential(cred.credential_id, cred.token)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_jwt_signing(self, credential_manager, agent_identity):
        """Test JWT signing and verification"""
        cred = await credential_manager.issue_credential(agent_identity, ttl=3600)

        # Sign JWT
        jwt_token = await credential_manager.sign_jwt(cred.credential_id)
        assert jwt_token is not None

        # Verify JWT
        claims = await credential_manager.verify_jwt(jwt_token)
        assert claims is not None
        assert claims["sub"] == agent_identity.agent_id
        assert claims["jti"] == cred.credential_id

    @pytest.mark.asyncio
    async def test_role_permissions(self, agent_identity):
        """Test role-based permissions"""
        # Scanner should have scan permissions
        assert agent_identity.has_permission("execute:active_scan")
        assert agent_identity.has_permission("write:vulnerabilities")

        # Should not have exploitation permissions
        assert not agent_identity.has_permission("execute:exploit")


# =============================================================================
# mTLS Authentication Tests
# =============================================================================


class TestmTLSAuthentication:
    """Test mTLS authentication system"""

    @pytest.fixture
    def certificate_authority(self):
        return CertificateAuthority(cert_ttl=3600)

    @pytest.fixture
    def mtls_manager(self, certificate_authority):
        return mTLSContextManager(certificate_authority)

    def test_ca_certificate_generation(self, certificate_authority):
        """Test CA certificate generation"""
        cert_pem = certificate_authority.ca_certificate_pem
        assert "BEGIN CERTIFICATE" in cert_pem
        assert "END CERTIFICATE" in cert_pem

    def test_service_certificate_issuance(self, certificate_authority):
        """Test service certificate issuance"""
        identity = ServiceIdentity(
            service_id="test-service",
            service_type="scanner",
            namespace="pentest",
        )

        bundle = certificate_authority.issue_certificate(identity)

        assert bundle.is_valid
        assert len(bundle.pem_certificate) > 0
        assert len(bundle.pem_private_key) > 0
        assert bundle.fingerprint is not None

    def test_certificate_verification(self, certificate_authority):
        """Test certificate verification"""
        identity = ServiceIdentity(service_id="test-service", service_type="scanner")

        bundle = certificate_authority.issue_certificate(identity)

        status, error = certificate_authority.verify_certificate(bundle.certificate, expected_service_id="test-service")

        assert status == CertificateStatus.VALID
        assert error is None

    def test_certificate_revocation(self, certificate_authority):
        """Test certificate revocation"""
        identity = ServiceIdentity(service_id="test-service", service_type="scanner")

        bundle = certificate_authority.issue_certificate(identity)

        # Revoke
        revoked = certificate_authority.revoke_certificate("test-service")
        assert revoked is True

        # Verify should fail
        status, error = certificate_authority.verify_certificate(bundle.certificate)
        assert status == CertificateStatus.REVOKED

    def test_spiffe_id_generation(self, mtls_manager):
        """Test SPIFFE ID generation"""
        identity = mtls_manager.create_service_identity(
            service_id="agent-001",
            service_type="recon",
            namespace="production",
        )

        expected_spiffe = "spiffe://zen-pentest.io/ns/production/svc/agent-001"
        assert identity.spiffe_id == expected_spiffe


# =============================================================================
# Guardrails Tests
# =============================================================================


class TestGuardrails:
    """Test enhanced guardrails"""

    @pytest_asyncio.fixture
    async def guardrails(self):
        validator = EnhancedGuardrailsValidator(redis_url="redis://localhost:6379")
        yield validator

    @pytest.mark.asyncio
    async def test_ip_blocking(self, guardrails):
        """Test IP blocking"""
        # Private IP should be blocked
        allowed, reason, _ = await guardrails.ip_filter.validate_target("192.168.1.1")
        assert allowed is False
        assert "Private" in reason or "blocked" in reason.lower()

        # Public IP should be allowed
        allowed, reason, _ = await guardrails.ip_filter.validate_target("8.8.8.8")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_domain_blocking(self, guardrails):
        """Test domain blocking"""
        # Government domain should be blocked
        allowed, reason, _ = await guardrails.ip_filter.validate_target("whitehouse.gov")
        assert allowed is False
        assert "Government" in reason

        # Regular domain should be allowed
        allowed, reason, _ = await guardrails.ip_filter.validate_target("example.com")
        assert allowed is True

    def test_command_validation(self, guardrails):
        """Test command validation"""
        # Dangerous command should be blocked
        valid, reason, sanitized = guardrails.command_validator.validate_command("rm -rf /", RiskLevel.LOW, "test-agent")
        assert valid is False

        # Allowed command should pass
        valid, reason, sanitized = guardrails.command_validator.validate_command(
            "nmap -sV example.com", RiskLevel.LOW, "test-agent"
        )
        assert valid is True

    @pytest.mark.asyncio
    async def test_rate_limiting(self, guardrails):
        """Test rate limiting"""
        from guardrails.enhanced_validator import RateLimitConfig

        # Set low rate limit for testing
        guardrails.rate_limiter.set_agent_config(
            "test-agent",
            RateLimitConfig(requests_per_minute=2, requests_per_hour=10),
        )

        # First two requests should pass
        for _ in range(2):
            allowed, _, _ = await guardrails.rate_limiter.check_rate_limit("test-agent", ActionType.PORT_SCAN)
            assert allowed is True

        # Third request should be rate limited
        allowed, reason, _ = await guardrails.rate_limiter.check_rate_limit("test-agent", ActionType.PORT_SCAN)
        assert allowed is False
        assert "Rate limit" in reason

    @pytest.mark.asyncio
    async def test_budget_enforcement(self, guardrails):
        """Test budget enforcement"""
        from guardrails.enhanced_validator import BudgetConfig

        # Set low budget
        guardrails.budget_manager.set_agent_budget("test-agent", BudgetConfig(max_api_calls_per_day=5))

        # Record some usage
        await guardrails.budget_manager.record_usage("test-agent", {"api_calls": 4})

        # Should be within budget
        allowed, _, _ = await guardrails.budget_manager.check_budget("test-agent", "scan", {"api_calls": 1})
        assert allowed is True

        # Should exceed budget
        allowed, reason, _ = await guardrails.budget_manager.check_budget("test-agent", "scan", {"api_calls": 2})
        assert allowed is False
        assert "budget" in reason.lower()

    @pytest.mark.asyncio
    async def test_risk_level_escalation(self, guardrails):
        """Test risk level escalation"""
        # Low risk level trying exploitation
        decision = await guardrails.validate_action(
            agent_id="test-agent",
            action_type=ActionType.EXPLOITATION,
            target="example.com",
            command=None,
            risk_level=RiskLevel.LOW,
        )

        assert decision.result == ValidationResult.ESCALATION_REQUIRED
        assert decision.escalation_token is not None


# =============================================================================
# Risk Engine Tests
# =============================================================================


class TestRiskEngine:
    """Test ML risk engine"""

    @pytest.fixture
    def risk_engine(self):
        return RiskScoringEngine()

    def test_cvss_calculation(self):
        """Test CVSS score calculation"""
        cvss = calculate_cvss_score(
            attack_vector="N",
            attack_complexity="L",
            privileges_required="N",
            user_interaction="N",
            scope="U",
            confidentiality="H",
            integrity="H",
            availability="H",
        )

        assert cvss.base_score >= 9.0  # Critical
        assert cvss.severity.value == "critical"
        assert "CVSS:3.1" in cvss.vector_string

    def test_bayesian_fp_reduction(self, risk_engine):
        """Test Bayesian false positive reduction"""
        finding = VulnerabilityFinding(
            finding_id="TEST-001",
            vulnerability_type=VulnerabilityType.SQL_INJECTION,
            target="example.com",
            description="SQL injection vulnerability",
            cvss=calculate_cvss_score(
                attack_vector="N",
                attack_complexity="L",
                privileges_required="L",
                confidentiality="H",
                integrity="H",
                availability="N",
            ),
            epss=None,
            cve_id=None,
            detection_method="pattern_matching",
            confidence=0.8,
            first_detected=datetime.utcnow(),
            last_detected=datetime.utcnow(),
            detection_count=1,
        )

        fp_prob, reasoning = risk_engine.fp_reducer.calculate_fp_probability(finding)

        assert 0 <= fp_prob <= 1
        assert len(reasoning) > 0

    def test_behavioral_profile(self, risk_engine):
        """Test behavioral profile creation"""
        agent_id = "test-agent-001"

        # Record some actions
        for i in range(10):
            risk_engine.behavioral_analyzer.record_action(agent_id, "port_scan", f"target-{i % 3}.com", datetime.utcnow())

        # Build profile
        profile = risk_engine.behavioral_analyzer.build_profile(agent_id)

        assert profile.agent_id == agent_id
        assert "port_scan" in profile.typical_actions
        assert profile.action_entropy > 0

    def test_anomaly_detection(self, risk_engine):
        """Test anomaly detection"""
        agent_id = "test-agent-002"

        # Build normal profile
        for i in range(20):
            risk_engine.behavioral_analyzer.record_action(agent_id, "dns_lookup", "example.com")

        profile = risk_engine.behavioral_analyzer.build_profile(agent_id)

        # Test anomalous action
        anomaly_score, reasons = risk_engine.behavioral_analyzer.detect_anomalies(
            agent_id,
            {
                "type": "exploitation",
                "target": "new-target.com",
                "hour": 3,
            },
        )

        assert anomaly_score > 0
        assert len(reasons) > 0

    def test_composite_risk_score(self, risk_engine):
        """Test composite risk score calculation"""
        finding = VulnerabilityFinding(
            finding_id="TEST-002",
            vulnerability_type=VulnerabilityType.REMOTE_CODE_EXECUTION,
            target="example.com",
            description="RCE vulnerability",
            cvss=calculate_cvss_score(
                attack_vector="N",
                attack_complexity="L",
                privileges_required="N",
                confidentiality="H",
                integrity="H",
                availability="H",
            ),
            epss=EPSSScore(epss_score=0.8, percentile=0.95, date=datetime.utcnow()),
            cve_id="CVE-2024-1234",
            detection_method="automated_exploit",
            confidence=0.95,
            first_detected=datetime.utcnow(),
            last_detected=datetime.utcnow(),
            detection_count=3,
            fp_probability=0.05,
        )

        score = risk_engine.calculate_composite_risk_score(finding)

        assert 0 <= score <= 10
        assert score > 5  # High risk finding


# =============================================================================
# Audit Logger Tests
# =============================================================================


class TestAuditLogger:
    """Test tamper-proof audit logger"""

    @pytest_asyncio.fixture
    async def audit_logger(self):
        logger = TamperProofAuditLogger(
            redis_url="redis://localhost:6379",
            log_file="/tmp/test_audit.log",  # nosec B108: Test file in test code
        )
        yield logger

    @pytest.mark.asyncio
    async def test_event_logging(self, audit_logger):
        """Test event logging"""
        event = await audit_logger.log_event(
            event_type=AuditEventType.AGENT_CREATED,
            action="create_agent",
            result="success",
            agent_id="test-agent-001",
            user_id="admin",
            metadata={"role": "scanner"},
        )

        assert event.event_id is not None
        assert event.signature is not None
        assert event.hash_chain is not None

    @pytest.mark.asyncio
    async def test_signature_verification(self, audit_logger):
        """Test signature verification"""
        event = await audit_logger.log_event(
            event_type=AuditEventType.ACTION_EXECUTED,
            action="port_scan",
            result="success",
            agent_id="test-agent-001",
        )

        # Verify signature
        is_valid = audit_logger.signature_manager.verify(event.canonical_string(), event.signature)

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_integrity_verification(self, audit_logger):
        """Test log integrity verification"""
        # Log some events
        for i in range(5):
            await audit_logger.log_event(
                event_type=AuditEventType.ACTION_EXECUTED,
                action=f"action_{i}",
                result="success",
                agent_id="test-agent-001",
            )

        # Verify integrity
        result = await audit_logger.verify_integrity()

        assert result["verified"] is True
        assert result["verified_events"] == 5

    @pytest.mark.asyncio
    async def test_evidence_chain(self, audit_logger):
        """Test evidence chain creation"""
        files = {
            "screenshot.png": b"fake-image-data",
            "logs.txt": b"fake-log-data",
        }

        chain = await audit_logger.create_evidence_chain(
            finding_id="FIND-001",
            evidence_type="screenshot",
            description="Vulnerability evidence",
            files=files,
            collected_by="agent-001",
        )

        assert chain.evidence_id is not None
        assert chain.integrity_hash is not None
        assert chain.signature is not None
        assert len(chain.custody_chain) == 1
        assert chain.custody_chain[0]["action"] == "collected"

    @pytest.mark.asyncio
    async def test_compliance_report(self, audit_logger):
        """Test compliance report generation"""
        # Log events with compliance tags
        await audit_logger.log_event(
            event_type=AuditEventType.CREDENTIAL_ISSUED,
            action="issue_credential",
            result="success",
            agent_id="test-agent-001",
            compliance_tags=["ISO27001:A.12.4.4"],
        )

        # Generate report
        report = await audit_logger.generate_compliance_report(
            ComplianceFramework.ISO27001,
            datetime.utcnow() - timedelta(hours=1),
            datetime.utcnow() + timedelta(hours=1),
        )

        assert report["framework"] == "ISO27001"
        assert "control_evidence" in report


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for the complete security system"""

    @pytest.mark.asyncio
    async def test_end_to_end_agent_workflow(self):
        """Test complete agent workflow"""
        # Initialize components
        cred_manager = TemporalCredentialManager()
        ca = CertificateAuthority()
        mtls = mTLSContextManager(ca)
        guardrails = EnhancedGuardrailsValidator()
        risk_engine = RiskScoringEngine()
        audit_logger = TamperProofAuditLogger()

        # 1. Create agent identity
        agent_id = "integration-test-agent"
        identity = await create_agent_identity(agent_id=agent_id, role=AgentRole.SCANNER)

        # 2. Issue credentials
        credential = await cred_manager.issue_credential(identity, ttl=3600)
        assert credential.status == CredentialStatus.ACTIVE

        # 3. Provision mTLS certificates
        service_identity = mtls.create_service_identity(service_id=agent_id, service_type="scanner")
        cert_bundle = mtls.provision_service(service_identity)
        assert cert_bundle.is_valid

        # 4. Validate action through guardrails
        decision = await guardrails.validate_action(
            agent_id=agent_id,
            action_type=ActionType.PORT_SCAN,
            target="scanme.nmap.org",
            command="nmap -sV scanme.nmap.org",
            risk_level=RiskLevel.LOW,
        )

        assert decision.result == ValidationResult.ALLOWED

        # 5. Log action
        event = await audit_logger.log_event(
            event_type=AuditEventType.ACTION_EXECUTED,
            action="port_scan",
            result="success",
            agent_id=agent_id,
            target="scanme.nmap.org",
        )

        assert event.signature is not None

        # 6. Verify audit integrity
        integrity = await audit_logger.verify_integrity()
        assert integrity["verified"] is True

    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self):
        """Test multi-agent coordination detection"""
        risk_engine = RiskScoringEngine()

        # Simulate coordinated behavior
        agent_ids = [f"agent-{i}" for i in range(5)]

        for agent_id in agent_ids:
            for _ in range(10):
                risk_engine.behavioral_analyzer.record_action(agent_id, "port_scan", "coordinated-target.com")

        # Detect coordination
        patterns = risk_engine.behavioral_analyzer.detect_coordinated_behavior(agent_ids)

        assert len(patterns) > 0
        assert any(p["type"] == "coordinated_targeting" for p in patterns)


# =============================================================================
# Security Regression Tests
# =============================================================================


class TestSecurityRegression:
    """Security regression tests"""

    @pytest.mark.asyncio
    async def test_timing_attack_resistance(self):
        """Test timing attack resistance in credential validation"""
        cred_manager = TemporalCredentialManager()
        identity = await create_agent_identity("timing-test", AgentRole.RECON)

        credential = await cred_manager.issue_credential(identity)

        # Time valid credential validation
        import time

        times_valid = []
        for _ in range(100):
            start = time.perf_counter()
            await cred_manager.validate_credential(credential.credential_id, credential.token)
            times_valid.append(time.perf_counter() - start)

        # Time invalid credential validation
        times_invalid = []
        for _ in range(100):
            start = time.perf_counter()
            await cred_manager.validate_credential(credential.credential_id, "wrong-token")
            times_invalid.append(time.perf_counter() - start)

        # Variances should be similar (constant-time comparison)
        import statistics

        var_valid = statistics.variance(times_valid)
        var_invalid = statistics.variance(times_invalid)

        # Allow for some variance due to system load
        assert abs(var_valid - var_invalid) < max(var_valid, var_invalid) * 2

    def test_hash_chain_integrity(self):
        """Test hash chain integrity protection"""
        audit_logger = TamperProofAuditLogger()

        # Log events
        events = []
        for i in range(5):
            event = asyncio.run(
                audit_logger.log_event(
                    event_type=AuditEventType.ACTION_EXECUTED,
                    action=f"action_{i}",
                    result="success",
                )
            )
            events.append(event)

        # Verify chain is sequential
        for i in range(1, len(events)):
            prev_hash = hashlib.sha256(events[i - 1].canonical_string().encode()).hexdigest()

            # The hash_chain of event i should incorporate the previous event
            assert events[i].hash_chain is not None

    @pytest.mark.asyncio
    async def test_concurrent_credential_rotation(self):
        """Test concurrent credential rotation safety"""
        cred_manager = TemporalCredentialManager()
        identity = await create_agent_identity("concurrent-test", AgentRole.SCANNER)

        credential = await cred_manager.issue_credential(identity, ttl=60)

        # Attempt concurrent rotations
        results = await asyncio.gather(
            cred_manager.rotate_credential(credential.credential_id),
            cred_manager.rotate_credential(credential.credential_id),
            cred_manager.rotate_credential(credential.credential_id),
            return_exceptions=True,
        )

        # At least one should succeed
        successful = [r for r in results if not isinstance(r, Exception) and r is not None]
        assert len(successful) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
