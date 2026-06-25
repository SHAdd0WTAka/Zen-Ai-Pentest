"""
=============================================================================
Zen-AI-Pentest — Comprehensive Test Suite
=============================================================================
Run with:
    pytest tests/test_comprehensive_suite.py -v --tb=short
=============================================================================
"""

import base64
import hashlib
import hmac as _hmac
import json as _json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Try to import real modules, fall back to stubs if not available
try:
    from risk_engine.cvss import CVSSCalculator
except ImportError:
    CVSSCalculator = None

try:
    from risk_engine.epss import EPSSClient
except ImportError:
    EPSSClient = None

try:
    from risk_engine.false_positive_engine import FalsePositiveEngine
except ImportError:
    FalsePositiveEngine = None

try:
    from autonomous.memory import AgentMemory
except ImportError:
    AgentMemory = None

try:
    from autonomous.exploit_validator import ExploitValidator
except ImportError:
    ExploitValidator = None

try:
    from agents.react_agent import ReActAgent, ReActAgentConfig
except ImportError:
    ReActAgent = None
    ReActAgentConfig = None

try:
    from api.auth import AuthManager
except ImportError:
    AuthManager = None


# =============================================================================
# TESTS
# =============================================================================


@pytest.mark.skipif(CVSSCalculator is None, reason="CVSSCalculator not available")
class TestCVSSCalculator:
    """risk_engine/cvss.py tests"""

    @pytest.fixture
    def calc(self):
        return CVSSCalculator()

    def test_critical_network_vector(self, calc):
        s = calc.calculate_base_score("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        assert 9.0 <= s <= 10.0

    def test_local_vector_medium_range(self, calc):
        s = calc.calculate_base_score("CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N")
        assert 4.0 <= s <= 8.9

    def test_severity_none(self, calc):
        assert calc.get_severity(0.0) == "None"

    def test_severity_low(self, calc):
        assert calc.get_severity(2.5) == "Low"

    def test_severity_medium(self, calc):
        assert calc.get_severity(5.0) == "Medium"

    def test_severity_high(self, calc):
        assert calc.get_severity(8.0) == "High"

    def test_severity_critical(self, calc):
        assert calc.get_severity(9.5) == "Critical"

    def test_temporal_lte_base(self, calc):
        assert calc.calculate_temporal_score(9.8, "proof_of_concept") <= 9.8

    def test_temporal_high_maturity_equals_base(self, calc):
        assert calc.calculate_temporal_score(7.0, "high") == 7.0

    def test_boundary_4_is_medium(self, calc):
        assert calc.get_severity(4.0) == "Medium"

    def test_boundary_7_is_high(self, calc):
        assert calc.get_severity(7.0) == "High"

    def test_boundary_9_is_critical(self, calc):
        assert calc.get_severity(9.0) == "Critical"

    def test_invalid_vector_raises(self, calc):
        with pytest.raises(ValueError):
            calc.calculate_base_score("BAD")

    def test_empty_vector_raises(self, calc):
        with pytest.raises(ValueError):
            calc.calculate_base_score("")

    def test_cvss2_raises(self, calc):
        with pytest.raises(ValueError):
            calc.calculate_base_score("AV:N/AC:L/Au:N/C:C/I:C/A:C")


@pytest.mark.skipif(EPSSClient is None, reason="EPSSClient not available")
class TestEPSSClient:
    """risk_engine/epss.py tests"""

    @pytest.fixture
    def client(self):
        return EPSSClient()

    def test_log4shell_high_score(self, client):
        assert client.get_score("CVE-2021-44228")["epss"] > 0.9

    def test_unknown_cve_default_range(self, client):
        r = client.get_score("CVE-9999-99999")
        assert 0.0 <= r["epss"] <= 1.0

    def test_bulk_returns_all_keys(self, client):
        cves = ["CVE-2021-44228", "CVE-2023-00001"]
        assert set(client.get_bulk_scores(cves).keys()) == set(cves)

    def test_score_range_valid(self, client):
        r = client.get_score("CVE-2023-00001")
        assert 0.0 <= r["epss"] <= 1.0

    def test_invalid_format_raises(self, client):
        with pytest.raises(ValueError):
            client.get_score("NOTACVE")

    def test_empty_bulk_returns_empty(self, client):
        assert client.get_bulk_scores([]) == {}


@pytest.mark.skipif(FalsePositiveEngine is None, reason="FalsePositiveEngine not available")
class TestFalsePositiveEngine:
    """risk_engine/false_positive_engine.py tests"""

    @pytest.fixture
    def engine(self):
        return FalsePositiveEngine(confidence_threshold=0.7)

    def test_high_confidence_not_fp(self, engine):
        assert not engine.validate({"confidence": 0.95})["is_false_positive"]

    def test_low_confidence_is_fp(self, engine):
        assert engine.validate({"confidence": 0.3})["is_false_positive"]

    def test_filter_removes_fp(self, engine):
        findings = [
            {"id": "f1", "confidence": 0.9},
            {"id": "f2", "confidence": 0.2},
            {"id": "f3", "confidence": 0.8},
        ]
        ids = [f["id"] for f in engine.filter_findings(findings)]
        assert "f2" not in ids
        assert "f1" in ids

    def test_validate_preserves_fields(self, engine):
        r = engine.validate({"id": "x", "cve_id": "CVE-X", "confidence": 0.9})
        assert r["cve_id"] == "CVE-X"

    def test_at_threshold_not_fp(self, engine):
        assert not engine.validate({"confidence": 0.7})["is_false_positive"]

    def test_all_high_confidence_kept(self, engine):
        findings = [{"id": str(i), "confidence": 0.9} for i in range(5)]
        assert len(engine.filter_findings(findings)) == 5

    def test_all_low_confidence_removed(self, engine):
        findings = [{"id": str(i), "confidence": 0.1} for i in range(5)]
        assert engine.filter_findings(findings) == []

    def test_custom_threshold(self, engine):
        engine2 = FalsePositiveEngine(confidence_threshold=0.5)
        assert not engine2.validate({"confidence": 0.6})["is_false_positive"]


@pytest.mark.skipif(AgentMemory is None, reason="AgentMemory not available")
class TestAgentMemory:
    """autonomous/memory.py tests"""

    @pytest.fixture
    def memory(self):
        return AgentMemory(max_short_term=3)

    def test_add_increases_count(self, memory):
        memory.add_observation({"data": "x"})
        assert memory.short_term_count == 1

    def test_get_context_respects_n(self, memory):
        for i in range(3):
            memory.add_observation({"seq": i})
        assert len(memory.get_context(last_n=2)) <= 2

    def test_clear_empties_short_term(self, memory):
        memory.add_observation({"x": 1})
        memory.clear_short_term()
        assert memory.short_term_count == 0

    def test_overflow_evicts_to_long_term(self, memory):
        for i in range(5):
            memory.add_observation({"seq": i})
        assert memory.short_term_count <= 3
        assert memory.long_term_count >= 1

    def test_get_context_n_larger_than_stored(self, memory):
        memory.add_observation({"x": 1})
        assert len(memory.get_context(last_n=100)) == 1

    def test_empty_context_returns_empty(self, memory):
        assert memory.get_context() == []


@pytest.mark.skipif(ExploitValidator is None, reason="ExploitValidator not available")
class TestExploitValidator:
    """autonomous/exploit_validator.py tests"""

    @pytest.fixture
    def validator(self):
        return ExploitValidator(max_risk_level=2)

    def test_allowed_within_threshold(self, validator):
        assert validator.validate_exploit({"risk_level": 1})["allowed"]

    def test_blocked_exceeds_threshold(self, validator):
        assert not validator.validate_exploit({"risk_level": 3})["allowed"]

    def test_sandbox_succeeds_for_allowed(self, validator):
        r = validator.execute_in_sandbox({"risk_level": 0})
        assert r["success"]
        assert r["output"] is not None

    def test_sandbox_fails_for_blocked(self, validator):
        r = validator.execute_in_sandbox({"risk_level": 3})
        assert not r["success"]
        assert r["output"] is None

    def test_preserves_exploit_name(self, validator):
        assert validator.validate_exploit({"name": "probe", "risk_level": 1})["name"] == "probe"

    def test_at_threshold_is_allowed(self, validator):
        assert validator.validate_exploit({"risk_level": 2})["allowed"]

    def test_zero_risk_allowed(self, validator):
        assert validator.validate_exploit({"risk_level": 0})["allowed"]

    def test_invalid_max_level_raises(self):
        with pytest.raises(ValueError):
            ExploitValidator(max_risk_level=99)

    def test_negative_level_raises(self):
        with pytest.raises(ValueError):
            ExploitValidator(max_risk_level=-1)


@pytest.mark.skipif(ReActAgent is None, reason="ReActAgent not available")
class TestReActAgent:
    """agents/react_agent.py tests"""

    @pytest.fixture
    def agent(self):
        return ReActAgent(ReActAgentConfig(max_iterations=5, safety_level=2))

    def test_initial_state_idle(self, agent):
        assert agent.state == "IDLE"

    def test_run_returns_dict(self, agent):
        assert isinstance(agent.run("t.com", "recon"), dict)

    def test_run_sets_target(self, agent):
        assert agent.run("192.168.1.1", "scan")["target"] == "192.168.1.1"

    def test_run_completes(self, agent):
        agent.run("t.com", "audit")
        assert agent.state == "COMPLETED"

    def test_result_has_findings(self, agent):
        assert "findings" in agent.run("t.com", "test")

    def test_report_contains_target(self, agent):
        r = agent.run("x.com", "r")
        assert "x.com" in agent.generate_report(r)

    def test_reset_to_idle(self, agent):
        agent.run("t.com", "t")
        agent.reset()
        assert agent.state == "IDLE"

    def test_reset_clears_memory(self, agent):
        agent.memory.add_observation({"x": 1})
        agent.reset()
        assert agent.memory.short_term_count == 0

    def test_empty_target_raises(self, agent):
        with pytest.raises(ValueError):
            agent.run("", "obj")

    def test_successive_runs(self, agent):
        agent.run("t1.com", "r1")
        agent.reset()
        assert agent.run("t2.com", "r2")["target"] == "t2.com"

    def test_config_stored(self, agent):
        assert agent.config.max_iterations == 5
        assert agent.config.safety_level == 2


@pytest.mark.skipif(AuthManager is None, reason="AuthManager not available")
class TestAuthManager:
    """api/auth.py tests"""

    @pytest.fixture
    def auth(self):
        return AuthManager(secret_key="test-secret-2026")

    def test_register_succeeds(self, auth):
        assert auth.register_user("alice", "p")

    def test_register_duplicate_false(self, auth):
        auth.register_user("b", "p")
        assert not auth.register_user("b", "p2")

    def test_valid_creds_return_token(self, auth):
        auth.register_user("c", "p")
        assert auth.authenticate("c", "p") is not None

    def test_wrong_password_none(self, auth):
        auth.register_user("d", "right")
        assert auth.authenticate("d", "wrong") is None

    def test_unknown_user_none(self, auth):
        assert auth.authenticate("nobody", "p") is None

    def test_valid_token_verifies(self, auth):
        auth.register_user("e", "p")
        token = auth.authenticate("e", "p")
        payload = auth.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "e"

    def test_tampered_token_rejected(self, auth):
        auth.register_user("f", "p")
        token = auth.authenticate("f", "p")
        assert auth.verify_token(token[:-5] + "XXXXX") is None

    def test_expired_token_rejected(self):
        a = AuthManager("k", expiration_seconds=-1)
        a.register_user("g", "p")
        t = a.authenticate("g", "p")
        assert a.verify_token(t) is None

    def test_garbage_token_none(self, auth):
        assert auth.verify_token("not.real.token") is None

    def test_empty_token_none(self, auth):
        assert auth.verify_token("") is None

    def test_empty_secret_raises(self):
        with pytest.raises(ValueError):
            AuthManager(secret_key="")

    def test_different_users_different_tokens(self, auth):
        auth.register_user("u1", "p")
        auth.register_user("u2", "p")
        assert auth.authenticate("u1", "p") != auth.authenticate("u2", "p")
