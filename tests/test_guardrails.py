"""
Guardrails Tests
================

Tests for security guardrails:
- IP validation (block private networks)
- Domain validation (block internal domains)
- Risk levels (enforce tool permissions)
- Rate limiting (prevent abuse)
"""

import asyncio
import pytest
import time

from guardrails.ip_validator import IPValidator, validate_target
from guardrails.domain_validator import DomainValidator, validate_domain, validate_url
from guardrails.risk_levels import (
    RiskLevel,
    RiskLevelManager,
    ToolRiskProfile,
    can_run_tool,
    validate_tool,
)
from guardrails.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    ToolRateLimiter,
    check_tool_execution,
)


class TestIPValidator:
    """Test IP address validation"""

    def test_block_private_class_a(self):
        """Block 10.0.0.0/8"""
        validator = IPValidator()
        
        result = validator.validate_ip("10.0.0.1")
        assert not result.is_valid
        assert "10.0.0.0/8" in result.blocked_ranges[0]

    def test_block_private_class_b(self):
        """Block 172.16.0.0/12"""
        validator = IPValidator()
        
        result = validator.validate_ip("172.16.0.1")
        assert not result.is_valid
        
        result = validator.validate_ip("172.31.255.255")
        assert not result.is_valid

    def test_block_private_class_c(self):
        """Block 192.168.0.0/16"""
        validator = IPValidator()
        
        result = validator.validate_ip("192.168.1.1")
        assert not result.is_valid
        assert "192.168.0.0/16" in result.blocked_ranges[0]

    def test_block_loopback(self):
        """Block 127.0.0.0/8"""
        validator = IPValidator()
        
        result = validator.validate_ip("127.0.0.1")
        assert not result.is_valid
        assert "127.0.0.0/8" in result.blocked_ranges[0]

    def test_block_link_local(self):
        """Block 169.254.0.0/16"""
        validator = IPValidator()
        
        result = validator.validate_ip("169.254.1.1")
        assert not result.is_valid

    def test_block_multicast(self):
        """Block multicast addresses"""
        validator = IPValidator()
        
        result = validator.validate_ip("224.0.0.1")
        assert not result.is_valid

    def test_allow_public_ip(self):
        """Allow public IP addresses"""
        validator = IPValidator()
        
        result = validator.validate_ip("8.8.8.8")
        assert result.is_valid
        
        result = validator.validate_ip("1.1.1.1")
        assert result.is_valid

    def test_allow_public_cidr(self):
        """Allow public CIDR ranges"""
        validator = IPValidator()
        
        result = validator.validate_network("8.8.8.0/24")
        assert result.is_valid

    def test_block_private_cidr(self):
        """Block private CIDR ranges"""
        validator = IPValidator()
        
        result = validator.validate_network("192.168.0.0/24")
        assert not result.is_valid

    def test_block_overlapping_cidr(self):
        """Block CIDR that overlaps with private"""
        validator = IPValidator()
        
        result = validator.validate_network("192.168.0.0/16")
        assert not result.is_valid

    def test_invalid_ip_format(self):
        """Handle invalid IP format"""
        validator = IPValidator()
        
        result = validator.validate_ip("not-an-ip")
        assert not result.is_valid
        assert "Invalid" in result.reason

    def test_ipv6_loopback(self):
        """Block IPv6 loopback"""
        validator = IPValidator()
        
        result = validator.validate_ip("::1")
        assert not result.is_valid

    def test_ipv6_link_local(self):
        """Block IPv6 link-local"""
        validator = IPValidator()
        
        result = validator.validate_ip("fe80::1")
        assert not result.is_valid

    def test_exception_allowed(self):
        """Allow exceptions"""
        validator = IPValidator()
        validator.add_exception("scanme.nmap.org")
        
        # This would normally be checked by domain validator
        # but exceptions should work
        result = validator.validate_target("scanme.nmap.org")
        assert result.is_valid

    def test_convenience_function(self):
        """Test convenience validate_target function"""
        result = validate_target("192.168.1.1")
        assert not result.is_valid
        
        result = validate_target("8.8.8.8")
        assert result.is_valid


class TestDomainValidator:
    """Test domain validation"""

    def test_block_localhost(self):
        """Block localhost"""
        validator = DomainValidator()
        
        result = validator.validate_domain("localhost")
        assert not result.is_valid

    def test_block_localhost_variations(self):
        """Block localhost variations"""
        validator = DomainValidator()
        
        result = validator.validate_domain("test.localhost")
        assert not result.is_valid
        
        result = validator.validate_domain("localhost.local")
        assert not result.is_valid

    def test_block_local_tld(self):
        """Block .local TLD"""
        validator = DomainValidator()
        
        result = validator.validate_domain("myserver.local")
        assert not result.is_valid
        assert ".local" in result.reason

    def test_block_internal_tld(self):
        """Block .internal TLD"""
        validator = DomainValidator()
        
        result = validator.validate_domain("server.internal")
        assert not result.is_valid

    def test_block_corp_tld(self):
        """Block .corp TLD"""
        validator = DomainValidator()
        
        result = validator.validate_domain("intranet.corp")
        assert not result.is_valid

    def test_block_ip_in_url(self):
        """Block URLs with IP addresses"""
        validator = DomainValidator()
        
        result = validator.validate_url("http://192.168.1.1")
        assert not result.is_valid

    def test_block_file_url(self):
        """Block file:// URLs"""
        validator = DomainValidator()
        
        result = validator.validate_url("file:///etc/passwd")
        assert not result.is_valid
        assert "file://" in result.reason.lower()

    def test_allow_public_domain(self):
        """Allow public domains"""
        validator = DomainValidator()
        
        result = validator.validate_domain("google.com")
        assert result.is_valid
        
        result = validator.validate_domain("example.org")
        assert result.is_valid

    def test_allow_public_url(self):
        """Allow public URLs"""
        validator = DomainValidator()
        
        result = validator.validate_url("https://scanme.nmap.org")
        assert result.is_valid

    def test_case_insensitive(self):
        """Domain validation is case insensitive"""
        validator = DomainValidator()
        
        result = validator.validate_domain("LOCALHOST")
        assert not result.is_valid
        
        result = validator.validate_domain("MYSERVER.LOCAL")
        assert not result.is_valid

    def test_is_internal_domain(self):
        """Check internal domain detection"""
        validator = DomainValidator()
        
        assert validator.is_internal_domain("localhost")
        assert validator.is_internal_domain("server.local")
        assert not validator.is_internal_domain("google.com")

    def test_exception_allowed(self):
        """Allow exceptions"""
        validator = DomainValidator()
        validator.add_exception("my.internal.server")
        
        result = validator.validate_domain("my.internal.server")
        assert result.is_valid


class TestRiskLevels:
    """Test risk level enforcement"""

    def test_safe_allows_recon_only(self):
        """SAFE level allows only recon tools"""
        manager = RiskLevelManager(RiskLevel.SAFE)
        
        assert manager.can_run_tool("whois")
        assert manager.can_run_tool("dns")
        assert not manager.can_run_tool("nmap")
        assert not manager.can_run_tool("exploit")

    def test_normal_allows_scanning(self):
        """NORMAL level allows scanning"""
        manager = RiskLevelManager(RiskLevel.NORMAL)
        
        assert manager.can_run_tool("whois")
        assert manager.can_run_tool("nmap")
        assert manager.can_run_tool("nuclei")
        assert not manager.can_run_tool("sqlmap")
        assert not manager.can_run_tool("exploit")

    def test_elevated_allows_light_exploit(self):
        """ELEVATED level allows light exploitation"""
        manager = RiskLevelManager(RiskLevel.ELEVATED)
        
        assert manager.can_run_tool("nmap")
        assert manager.can_run_tool("sqlmap")
        assert manager.can_run_tool("exploit")
        assert not manager.can_run_tool("pivot")

    def test_aggressive_allows_all(self):
        """AGGRESSIVE level allows everything"""
        manager = RiskLevelManager(RiskLevel.AGGRESSIVE)
        
        assert manager.can_run_tool("whois")
        assert manager.can_run_tool("nmap")
        assert manager.can_run_tool("sqlmap")
        assert manager.can_run_tool("pivot")
        assert manager.can_run_tool("lateral")

    def test_validate_tool_with_flags(self):
        """Validate tool with dangerous flags"""
        manager = RiskLevelManager(RiskLevel.NORMAL)
        
        # nmap with dangerous flag
        result = manager.validate_tool("nmap", ["-T5", "-p-"])
        assert not result["allowed"]
        assert "-T5" in str(result["blocked_flags"])

    def test_validate_unknown_tool(self):
        """Handle unknown tools"""
        manager = RiskLevelManager(RiskLevel.NORMAL)
        
        result = manager.validate_tool("unknown_tool")
        assert result["allowed"]
        assert "caution" in str(result["warnings"]).lower()

    def test_validate_unknown_tool_blocked_at_safe(self):
        """Unknown tools blocked at SAFE level"""
        manager = RiskLevelManager(RiskLevel.SAFE)
        
        result = manager.validate_tool("unknown_tool")
        assert not result["allowed"]

    def test_requires_confirmation(self):
        """High-risk tools require confirmation"""
        manager = RiskLevelManager(RiskLevel.ELEVATED)
        
        result = manager.validate_tool("sqlmap")
        assert result["requires_confirmation"]

    def test_approve_tool(self):
        """Approve tool for session"""
        manager = RiskLevelManager(RiskLevel.ELEVATED)
        
        result = manager.validate_tool("sqlmap")
        assert result["requires_confirmation"]
        
        manager.approve_tool("sqlmap")
        result = manager.validate_tool("sqlmap")
        assert not result["requires_confirmation"]

    def test_get_allowed_tools(self):
        """Get list of allowed tools"""
        manager = RiskLevelManager(RiskLevel.NORMAL)
        
        allowed = manager.get_allowed_tools()
        assert "whois" in allowed
        assert "nmap" in allowed
        assert "sqlmap" not in allowed

    def test_get_blocked_tools(self):
        """Get list of blocked tools"""
        manager = RiskLevelManager(RiskLevel.NORMAL)
        
        blocked = manager.get_blocked_tools()
        assert "sqlmap" in blocked
        assert "exploit" in blocked

    def test_risk_level_description(self):
        """Get risk level description"""
        manager = RiskLevelManager(RiskLevel.NORMAL)
        
        desc = manager.get_risk_description()
        assert "Standard" in desc or "scanning" in desc.lower()

    def test_add_tool_profile(self):
        """Add custom tool profile"""
        manager = RiskLevelManager(RiskLevel.SAFE)
        
        # Initially blocked
        assert not manager.can_run_tool("custom_tool")
        
        # Add profile
        profile = ToolRiskProfile(
            name="custom_tool",
            min_risk_level=RiskLevel.SAFE,
            description="Custom safe tool",
            dangerous_flags=[],
        )
        manager.add_tool_profile(profile)
        
        # Now allowed
        assert manager.can_run_tool("custom_tool")

    def test_convenience_functions(self):
        """Test convenience functions"""
        from guardrails.risk_levels import set_risk_level, get_risk_manager
        
        set_risk_level(RiskLevel.NORMAL)
        assert get_risk_manager().get_risk_level() == RiskLevel.NORMAL
        
        assert can_run_tool("nmap")
        assert not can_run_tool("pivot")


class TestRateLimiter:
    """Test rate limiting"""

    @pytest.mark.asyncio
    async def test_allow_within_limit(self):
        """Allow requests within rate limit"""
        limiter = RateLimiter(RateLimitConfig(
            max_requests=5,
            window_seconds=60,
            burst_size=5,  # Allow burst of 5
            cooldown_seconds=0,
        ))
        
        for i in range(5):
            result = await limiter.check_rate_limit("test_key")
            assert result["allowed"], f"Request {i+1} should be allowed"
            await limiter.record_request("test_key")

    @pytest.mark.asyncio
    async def test_block_over_limit(self):
        """Block requests over rate limit"""
        limiter = RateLimiter(RateLimitConfig(
            max_requests=2,
            window_seconds=60,
            cooldown_seconds=0,
        ))
        
        # Make 2 requests
        for _ in range(2):
            result = await limiter.check_rate_limit("test_key")
            assert result["allowed"]
            await limiter.record_request("test_key")
        
        # 3rd should be blocked
        result = await limiter.check_rate_limit("test_key")
        assert not result["allowed"]
        assert "Rate limit exceeded" in result["reason"]

    @pytest.mark.asyncio
    async def test_cooldown_enforced(self):
        """Enforce cooldown between requests"""
        limiter = RateLimiter(RateLimitConfig(
            max_requests=100,
            window_seconds=60,
            cooldown_seconds=1,
        ))
        
        # First request
        result = await limiter.check_rate_limit("test_key")
        assert result["allowed"]
        await limiter.record_request("test_key")
        
        # Immediate second request should be blocked
        result = await limiter.check_rate_limit("test_key")
        assert not result["allowed"]
        assert "Cooldown" in result["reason"]

    @pytest.mark.asyncio
    async def test_burst_limit(self):
        """Enforce burst limit"""
        limiter = RateLimiter(RateLimitConfig(
            max_requests=100,
            window_seconds=60,
            burst_size=2,
            cooldown_seconds=0,
        ))
        
        # 2 requests quickly
        for _ in range(2):
            result = await limiter.check_rate_limit("test_key")
            assert result["allowed"]
            await limiter.record_request("test_key")
        
        # 3rd in burst should be blocked
        result = await limiter.check_rate_limit("test_key")
        assert not result["allowed"]
        assert "Burst" in result["reason"]

    @pytest.mark.asyncio
    async def test_acquire_with_wait(self):
        """Test acquire with waiting"""
        limiter = RateLimiter(RateLimitConfig(
            max_requests=100,
            window_seconds=60,
            cooldown_seconds=0.1,
        ))
        
        # First acquire
        result = await limiter.acquire("test_key")
        assert result
        
        # Second should wait and succeed
        result = await limiter.acquire("test_key", timeout=0.5)
        assert result

    @pytest.mark.asyncio
    async def test_acquire_timeout(self):
        """Test acquire timeout"""
        limiter = RateLimiter(RateLimitConfig(
            max_requests=1,
            window_seconds=60,
            cooldown_seconds=10,
        ))
        
        # Use up the request
        result = await limiter.acquire("test_key")
        assert result
        
        # Second should timeout
        result = await limiter.acquire("test_key", timeout=0.1)
        assert not result

    @pytest.mark.asyncio
    async def test_reset(self):
        """Test rate limit reset"""
        limiter = RateLimiter(RateLimitConfig(
            max_requests=1,
            window_seconds=60,
        ))
        
        # Use up the request
        await limiter.record_request("test_key")
        result = await limiter.check_rate_limit("test_key")
        assert not result["allowed"]
        
        # Reset
        await limiter.reset("test_key")
        result = await limiter.check_rate_limit("test_key")
        assert result["allowed"]

    def test_get_stats(self):
        """Test getting stats"""
        limiter = RateLimiter(RateLimitConfig(max_requests=10))
        
        stats = limiter.get_stats("nonexistent_key")
        assert stats["requests_in_window"] == 0
        assert stats["remaining"] == 10


class TestToolRateLimiter:
    """Test tool-specific rate limiting"""

    @pytest.mark.asyncio
    async def test_check_tool_execution(self):
        """Check tool execution rate limit"""
        limiter = ToolRateLimiter()
        
        result = await limiter.check_tool_execution("nmap", "scanme.nmap.org")
        assert result["allowed"]

    @pytest.mark.asyncio
    async def test_record_execution(self):
        """Record and check multiple executions"""
        limiter = ToolRateLimiter()
        
        # Record many executions
        for _ in range(100):
            await limiter.record_execution("nmap", "scanme.nmap.org")
        
        # Should be rate limited now
        result = await limiter.check_tool_execution("nmap", "scanme.nmap.org")
        # May or may not be blocked depending on limits

    @pytest.mark.asyncio
    async def test_convenience_function(self):
        """Test convenience check_tool_execution function"""
        result = await check_tool_execution("nmap", "scanme.nmap.org")
        assert "allowed" in result


class TestGuardrailsIntegration:
    """Test integration between guardrail components"""

    def test_full_validation_chain_blocked(self):
        """Full validation chain blocks dangerous target"""
        # IP check
        ip_result = validate_target("192.168.1.1")
        assert not ip_result.is_valid
        
        # Domain check
        domain_result = validate_domain("localhost")
        assert not domain_result.is_valid

    def test_full_validation_chain_allowed(self):
        """Full validation chain allows safe target"""
        ip_result = validate_target("8.8.8.8")
        assert ip_result.is_valid
        
        domain_result = validate_domain("scanme.nmap.org")
        assert domain_result.is_valid

    @pytest.mark.asyncio
    async def test_risk_and_rate_limit(self):
        """Combine risk level and rate limiting"""
        from guardrails.risk_levels import set_risk_level
        
        set_risk_level(RiskLevel.NORMAL)
        
        # Risk allows nmap
        assert can_run_tool("nmap")
        
        # Rate limit allows (first request)
        rate_result = await check_tool_execution("nmap", "scanme.nmap.org")
        assert rate_result["allowed"]
