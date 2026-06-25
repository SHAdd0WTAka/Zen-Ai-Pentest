"""
Unit tests for Subfinder Integration

Tests JSON parsing, command generation, error handling, and subdomain discovery.
Mocked - does not execute real subfinder scans.
"""

import asyncio
import json
import sys
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Ensure tools module is importable
sys.path.insert(0, "/workspaces/Zen-Ai-Pentest")

from tools.subfinder_integration import (
    SubfinderIntegration,
    SubfinderResult,
    enumerate_sync,
    subfinder_scan,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_subfinder_output() -> str:
    """Sample subfinder JSON output"""
    subdomains = [
        {"host": "www.example.com"},
        {"host": "mail.example.com"},
        {"host": "api.example.com"},
        {"host": "admin.example.com"},
        {"host": "blog.example.com"},
    ]
    return "\n".join(json.dumps(s) for s in subdomains)


@pytest.fixture
def sample_subfinder_single() -> str:
    """Sample single subdomain output"""
    return json.dumps({"host": "subdomain.example.com"})


@pytest.fixture
def sample_subfinder_plaintext() -> str:
    """Sample plaintext output (fallback)"""
    return """www.example.com
mail.example.com
api.example.com
[Info] Scan complete
admin.example.com
"""


@pytest.fixture
def sample_subfinder_with_duplicates() -> str:
    """Sample output with duplicate subdomains"""
    subdomains = [
        {"host": "www.example.com"},
        {"host": "www.example.com"},  # Duplicate
        {"host": "mail.example.com"},
        {"host": "mail.example.com"},  # Duplicate
    ]
    return "\n".join(json.dumps(s) for s in subdomains)


@pytest.fixture
def subfinder_integration():
    """Create SubfinderIntegration instance"""
    return SubfinderIntegration()


@pytest.fixture
def mock_subprocess_process():
    """Create mock async subprocess process"""
    process = AsyncMock()
    return process


# ============================================================================
# Test Classes - SubfinderResult Data Class
# ============================================================================


class TestSubfinderResult:
    """Test SubfinderResult dataclass"""

    def test_result_creation_success(self):
        """Test creating a successful SubfinderResult"""
        result = SubfinderResult(
            success=True,
            domain="example.com",
            subdomains=["www.example.com", "mail.example.com"],
            count=2,
            duration=5.5,
        )
        assert result.success is True
        assert result.domain == "example.com"
        assert result.subdomains == ["www.example.com", "mail.example.com"]
        assert result.count == 2
        assert result.duration == 5.5
        assert result.error is None

    def test_result_creation_failure(self):
        """Test creating a failed SubfinderResult"""
        result = SubfinderResult(
            success=False,
            domain="example.com",
            error="Command not found",
        )
        assert result.success is False
        assert result.error == "Command not found"
        assert result.subdomains == []
        assert result.count == 0

    def test_result_default_values(self):
        """Test SubfinderResult default values"""
        result = SubfinderResult(success=True)
        assert result.domain == ""
        assert result.subdomains == []
        assert result.count == 0
        assert result.error is None
        assert result.duration == 0.0


# ============================================================================
# Test Classes - SubfinderIntegration Initialization
# ============================================================================


class TestSubfinderIntegrationInitialization:
    """Test SubfinderIntegration initialization"""

    def test_init_default(self):
        """Test default initialization"""
        subfinder = SubfinderIntegration()
        assert subfinder.timeout == 300

    def test_init_custom_timeout(self):
        """Test initialization with custom timeout"""
        subfinder = SubfinderIntegration(timeout=600)
        assert subfinder.timeout == 600

    def test_init_zero_timeout(self):
        """Test initialization with zero timeout"""
        subfinder = SubfinderIntegration(timeout=0)
        assert subfinder.timeout == 0


# ============================================================================
# Test Classes - Enumeration
# ============================================================================


class TestEnumeration:
    """Test subdomain enumeration"""

    @pytest.mark.asyncio
    async def test_enumerate_success(self, subfinder_integration, sample_subfinder_output):
        """Test successful enumeration"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            sample_subfinder_output.encode(),
            b"",
        )
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate("example.com")

        assert result.success is True
        assert result.domain == "example.com"
        assert len(result.subdomains) == 5
        assert "www.example.com" in result.subdomains
        assert "mail.example.com" in result.subdomains
        assert result.count == 5
        assert result.error is None
        assert result.duration >= 0

    @pytest.mark.asyncio
    async def test_enumerate_command_structure(self, subfinder_integration):
        """Test that subfinder command is built correctly"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
            await subfinder_integration.enumerate("example.com")

            call_args = mock_exec.call_args[0]
            assert "subfinder" in call_args
            assert "-d" in call_args
            assert "example.com" in call_args
            assert "-json" in call_args
            assert "-silent" in call_args

    @pytest.mark.asyncio
    async def test_enumerate_recursive(self, subfinder_integration):
        """Test enumeration with recursive flag"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
            await subfinder_integration.enumerate("example.com", recursive=True)

            call_args = mock_exec.call_args[0]
            assert "-recursive" in call_args

    @pytest.mark.asyncio
    async def test_enumerate_non_recursive(self, subfinder_integration):
        """Test enumeration without recursive flag"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
            await subfinder_integration.enumerate("example.com", recursive=False)

            call_args = mock_exec.call_args[0]
            assert "-recursive" not in call_args

    @pytest.mark.asyncio
    async def test_enumerate_empty_result(self, subfinder_integration):
        """Test enumeration with empty result"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate("example.com")

        assert result.success is True
        assert result.subdomains == []
        assert result.count == 0

    @pytest.mark.asyncio
    async def test_enumerate_timeout(self, subfinder_integration):
        """Test enumeration timeout handling"""
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate("example.com")

        assert result.success is False
        assert result.error == "Timeout"
        assert result.domain == "example.com"

    @pytest.mark.asyncio
    async def test_enumerate_general_error(self, subfinder_integration):
        """Test enumeration general error handling"""
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(side_effect=Exception("Test error"))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate("example.com")

        assert result.success is False
        assert "Test error" in result.error
        assert result.domain == "example.com"


# ============================================================================
# Test Classes - JSON Parsing
# ============================================================================


class TestJsonParsing:
    """Test JSON output parsing"""

    @pytest.mark.asyncio
    async def test_parse_json_object(self, subfinder_integration, sample_subfinder_single):
        """Test parsing single JSON object"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            sample_subfinder_single.encode(),
            b"",
        )
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate("example.com")

        assert len(result.subdomains) == 1
        assert result.subdomains[0] == "subdomain.example.com"

    @pytest.mark.asyncio
    async def test_parse_multiple_json_objects(self, subfinder_integration, sample_subfinder_output):
        """Test parsing multiple JSON objects"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            sample_subfinder_output.encode(),
            b"",
        )
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate("example.com")

        assert len(result.subdomains) == 5
        expected = ["www.example.com", "mail.example.com", "api.example.com", "admin.example.com", "blog.example.com"]
        for subdomain in expected:
            assert subdomain in result.subdomains

    @pytest.mark.asyncio
    async def test_parse_fallback_plaintext(self, subfinder_integration, sample_subfinder_plaintext):
        """Test fallback plaintext parsing"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            sample_subfinder_plaintext.encode(),
            b"",
        )
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate("example.com")

        # Should extract subdomains and skip log lines starting with [
        assert "www.example.com" in result.subdomains
        assert "mail.example.com" in result.subdomains
        assert "api.example.com" in result.subdomains
        assert "admin.example.com" in result.subdomains
        assert "[Info] Scan complete" not in result.subdomains

    @pytest.mark.asyncio
    async def test_parse_duplicates_removed(self, subfinder_integration, sample_subfinder_with_duplicates):
        """Test that duplicate subdomains are removed"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            sample_subfinder_with_duplicates.encode(),
            b"",
        )
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate("example.com")

        assert len(result.subdomains) == 2
        assert result.count == 2
        assert result.subdomains.count("www.example.com") == 1
        assert result.subdomains.count("mail.example.com") == 1

    @pytest.mark.asyncio
    async def test_parse_sorted_output(self, subfinder_integration, sample_subfinder_output):
        """Test that subdomains are sorted"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            sample_subfinder_output.encode(),
            b"",
        )
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate("example.com")

        # Subdomains should be sorted alphabetically
        assert result.subdomains == sorted(result.subdomains)

    @pytest.mark.asyncio
    async def test_parse_empty_lines_ignored(self, subfinder_integration):
        """Test that empty lines are ignored"""
        output = "\n\n".join(
            [
                json.dumps({"host": "www.example.com"}),
                "",
                json.dumps({"host": "mail.example.com"}),
                "",
                "",
            ]
        )

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (output.encode(), b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate("example.com")

        assert len(result.subdomains) == 2

    @pytest.mark.asyncio
    async def test_parse_invalid_json_fallback(self, subfinder_integration):
        """Test fallback for invalid JSON"""
        output = """
invalid json line
www.example.com
another bad line
mail.example.com
"""

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (output.encode(), b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate("example.com")

        assert "www.example.com" in result.subdomains
        assert "mail.example.com" in result.subdomains


# ============================================================================
# Test Classes - Sync Wrapper
# ============================================================================


class TestSyncWrapper:
    """Test synchronous wrapper functions"""

    def test_enumerate_sync(self):
        """Test enumerate_sync wrapper"""
        output = json.dumps({"host": "www.example.com"})

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (output.encode(), b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = enumerate_sync("example.com")

        assert isinstance(result, SubfinderResult)
        assert result.success is True
        assert "www.example.com" in result.subdomains

    def test_enumerate_sync_recursive(self):
        """Test enumerate_sync with recursive flag"""
        output = json.dumps({"host": "sub.example.com"})

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (output.encode(), b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
            result = enumerate_sync("example.com", recursive=True)

            call_args = mock_exec.call_args[0]
            assert "-recursive" in call_args

    def test_subfinder_scan_alias(self):
        """Test that subfinder_scan is an alias for enumerate_sync"""
        output = json.dumps({"host": "www.example.com"})

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (output.encode(), b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = subfinder_scan("example.com")

        assert isinstance(result, SubfinderResult)
        assert result.success is True


# ============================================================================
# Test Classes - Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases"""

    @pytest.mark.asyncio
    async def test_empty_domain(self, subfinder_integration):
        """Test enumeration with empty domain"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate("")

        assert result.success is True
        assert result.domain == ""

    @pytest.mark.asyncio
    async def test_domain_with_subdomain(self, subfinder_integration):
        """Test enumeration with subdomain as input"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
            await subfinder_integration.enumerate("sub.example.com")

            call_args = mock_exec.call_args[0]
            assert "sub.example.com" in call_args

    @pytest.mark.asyncio
    async def test_domain_with_special_chars(self, subfinder_integration):
        """Test domain with special characters"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate("test-domain.co.uk")

            assert result.success is True

    @pytest.mark.asyncio
    async def test_very_long_domain(self, subfinder_integration):
        """Test with very long domain name"""
        long_domain = "a" * 50 + ".example.com"

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate(long_domain)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_unicode_domain(self, subfinder_integration):
        """Test with unicode domain"""
        unicode_domain = "例え.jp"

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate(unicode_domain)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_stderr_ignored(self, subfinder_integration, sample_subfinder_output):
        """Test that stderr is ignored in normal operation"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            sample_subfinder_output.encode(),
            b"Some warning message\nAnother warning",
        )
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate("example.com")

        assert result.success is True
        assert len(result.subdomains) == 5

    @pytest.mark.asyncio
    async def test_whitespace_only_output(self, subfinder_integration):
        """Test handling of whitespace-only output"""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"   \n\t\n   ", b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate("example.com")

        assert result.success is True
        assert result.subdomains == []
        assert result.count == 0

    @pytest.mark.asyncio
    async def test_missing_host_field(self, subfinder_integration):
        """Test handling of JSON without host field"""
        output = json.dumps({"source": "dns", "timestamp": "2024-01-01"})

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (output.encode(), b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate("example.com")

        assert result.success is True
        assert result.subdomains == []

    @pytest.mark.asyncio
    async def test_empty_host_value(self, subfinder_integration):
        """Test handling of empty host value"""
        output = json.dumps({"host": ""})

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (output.encode(), b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await subfinder_integration.enumerate("example.com")

        assert result.success is True
        assert result.subdomains == []


# ============================================================================
# Test Classes - Module Exports
# ============================================================================


class TestModuleExports:
    """Test module exports"""

    def test_all_classes_exported(self):
        """Test that all expected classes are exported"""
        from tools import subfinder_integration

        assert hasattr(subfinder_integration, "SubfinderIntegration")
        assert hasattr(subfinder_integration, "SubfinderResult")

    def test_all_functions_exported(self):
        """Test that all expected functions are exported"""
        from tools import subfinder_integration

        assert hasattr(subfinder_integration, "enumerate_sync")
        assert hasattr(subfinder_integration, "subfinder_scan")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
