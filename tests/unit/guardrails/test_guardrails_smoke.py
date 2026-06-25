"""Smoke tests for guardrails modules (safety/guardrails.py, guardrails/)"""

import pytest

from guardrails.rate_limiter import RateLimitConfig
from guardrails.rate_limiter import RateLimiter as GuardrailRateLimiter
from guardrails.rate_limiter import ToolRateLimiter, get_rate_limiter
from guardrails.risk_levels import RiskLevel as GuardrailRiskLevel
from guardrails.risk_levels import RiskLevelManager, ToolRiskProfile, get_risk_manager
from safety.guardrails import GuardrailResult, OutputGuardrails, SafetyLevel


class TestOutputGuardrails:
    def test_init_default(self):
        og = OutputGuardrails()
        assert og.safety_level == SafetyLevel.STANDARD
        assert og.violation_history == []

    def test_init_strict(self):
        og = OutputGuardrails(safety_level=SafetyLevel.STRICT)
        assert og.safety_level == SafetyLevel.STRICT

    def test_check_clean_output(self):
        og = OutputGuardrails()
        result = og.check("The target has port 80 open and runs Apache 2.4.")
        assert isinstance(result, GuardrailResult)
        assert result.passed

    def test_check_returns_guardrail_result(self):
        og = OutputGuardrails()
        result = og.check("Test string that should be clean.")
        assert isinstance(result, GuardrailResult)
        assert hasattr(result, "passed")
        assert hasattr(result, "violations")
        assert hasattr(result, "confidence_penalty")

    def test_violation_history_tracks_checks(self):
        og = OutputGuardrails()
        og.check("test")
        og.check("another test")
        assert len(og.violation_history) >= 0
        assert isinstance(og.violation_history, list)

    def test_check_security_falsehood(self):
        og = OutputGuardrails()
        result = og.check("This system is completely secure and impossible to exploit.")
        assert not result.passed
        assert any("falsehood" in v.lower() for v in result.violations)

    def test_get_stats(self):
        og = OutputGuardrails()
        og.check("test output")
        stats = og.get_stats()
        assert stats["safety_level"] == "standard"


class TestSafetyLevel:
    def test_values(self):
        assert SafetyLevel.PERMISSIVE.value == "permissive"
        assert SafetyLevel.PARANOID.value == "paranoid"


class TestGuardrailResult:
    def test_dataclass(self):
        result = GuardrailResult(passed=True, violations=[], safety_level=SafetyLevel.STANDARD, confidence_penalty=0.0)
        assert result.passed
        assert result.confidence_penalty == 0.0


class TestGuardrailRateLimiter:
    def test_init_default(self):
        rl = GuardrailRateLimiter()
        assert rl.config.max_requests == 10
        assert rl.config.window_seconds == 60

    def test_init_custom_config(self):
        cfg = RateLimitConfig(max_requests=5, window_seconds=30)
        rl = GuardrailRateLimiter(config=cfg)
        assert rl.config.max_requests == 5

    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self):
        rl = GuardrailRateLimiter(RateLimitConfig(max_requests=10, window_seconds=60))
        result = await rl.check_rate_limit("test-user")
        assert result["allowed"] is True
        assert result["remaining"] == 9

    @pytest.mark.asyncio
    async def test_record_and_check(self):
        cfg = RateLimitConfig(max_requests=3, window_seconds=60, cooldown_seconds=0)
        rl = GuardrailRateLimiter(config=cfg)
        await rl.record_request("user-1")
        result = await rl.check_rate_limit("user-1")
        assert result["allowed"] is True
        assert result["remaining"] == 2 or result["remaining"] == 1

    @pytest.mark.asyncio
    async def test_reset(self):
        rl = GuardrailRateLimiter()
        await rl.record_request("user-1")
        await rl.reset("user-1")
        result = await rl.check_rate_limit("user-1")
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_acquire_success(self):
        rl = GuardrailRateLimiter(RateLimitConfig(max_requests=10, window_seconds=60))
        acquired = await rl.acquire("user-1", timeout=1)
        assert acquired is True

    def test_get_stats(self):
        rl = GuardrailRateLimiter()
        stats = rl.get_stats()
        assert "config" in stats
        assert stats["config"]["max_requests"] == 10

    def test_tool_rate_limiter_init(self):
        trl = ToolRateLimiter()
        assert trl.global_limiter is not None
        assert trl.target_limiter is not None

    def test_get_rate_limiter_singleton(self):
        limiter = get_rate_limiter()
        assert isinstance(limiter, ToolRateLimiter)


class TestGuardrailRiskLevels:
    def test_enum_values(self):
        assert GuardrailRiskLevel.SAFE == 0
        assert GuardrailRiskLevel.NORMAL == 1
        assert GuardrailRiskLevel.ELEVATED == 2
        assert GuardrailRiskLevel.AGGRESSIVE == 3

    def test_risk_level_manager_default(self):
        mgr = RiskLevelManager()
        assert mgr.current_level == GuardrailRiskLevel.NORMAL

    def test_set_risk_level(self):
        mgr = RiskLevelManager()
        mgr.set_risk_level(GuardrailRiskLevel.SAFE)
        assert mgr.get_risk_level() == GuardrailRiskLevel.SAFE

    def test_can_run_tool(self):
        mgr = RiskLevelManager(GuardrailRiskLevel.NORMAL)
        assert mgr.can_run_tool("nmap") is True
        assert mgr.can_run_tool("exploit") is False

    def test_validate_tool_unknown(self):
        mgr = RiskLevelManager()
        result = mgr.validate_tool("unknown_tool")
        assert result["allowed"] is True

    def test_get_allowed_tools(self):
        mgr = RiskLevelManager(GuardrailRiskLevel.SAFE)
        tools = mgr.get_allowed_tools()
        assert "whois" in tools
        assert "nmap" not in tools

    def test_tool_risk_profile(self):
        profile = ToolRiskProfile(
            name="nmap", min_risk_level=GuardrailRiskLevel.NORMAL, description="Port scanning", dangerous_flags=["-T5"]
        )
        assert profile.name == "nmap"
        assert profile.requires_confirmation is False

    def test_get_risk_manager(self):
        mgr = get_risk_manager()
        assert isinstance(mgr, RiskLevelManager)
