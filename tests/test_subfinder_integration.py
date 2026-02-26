"""Tests for tools/subfinder_integration.py."""

import json
import pytest
from unittest.mock import MagicMock, patch

from tools.subfinder_integration import (
    SubfinderIntegration,
    SubfinderResult,
    enumerate_sync,
)


class TestSubfinderResult:
    """Test SubfinderResult dataclass."""

    def test_default_creation(self):
        """Test creating result with defaults."""
        result = SubfinderResult(success=True)

        assert result.success is True
        assert result.domain == ""
        assert result.subdomains == []
        assert result.count == 0
        assert result.error is None
        assert result.duration == 0.0

    def test_full_creation(self):
        """Test creating result with all fields."""
        result = SubfinderResult(
            success=True,
            domain="example.com",
            subdomains=["sub1.example.com", "sub2.example.com"],
            count=2,
            error=None,
            duration=1.5,
        )

        assert result.domain == "example.com"
        assert len(result.subdomains) == 2
        assert result.count == 2
        assert result.duration == 1.5


class TestSubfinderIntegration:
    """Test SubfinderIntegration class."""

    def test_init_default_timeout(self):
        """Test initialization with default timeout."""
        integration = SubfinderIntegration()
        assert integration.timeout == 300

    def test_init_custom_timeout(self):
        """Test initialization with custom timeout."""
        integration = SubfinderIntegration(timeout=60)
        assert integration.timeout == 60


class TestEnumerateSync:
    """Test synchronous wrapper."""

    def test_enumerate_sync(self):
        """Test synchronous wrapper function."""
        with patch.object(
            SubfinderIntegration, "enumerate"
        ) as mock_enum:
            mock_enum.return_value = SubfinderResult(
                success=True,
                domain="example.com",
                subdomains=["sub.example.com"],
                count=1,
            )

            result = enumerate_sync("example.com")

            assert result.success is True
            assert result.domain == "example.com"
            mock_enum.assert_called_once_with("example.com", False)

    def test_enumerate_sync_recursive(self):
        """Test synchronous wrapper with recursive."""
        with patch.object(
            SubfinderIntegration, "enumerate"
        ) as mock_enum:
            mock_enum.return_value = SubfinderResult(success=True)

            enumerate_sync("example.com", recursive=True)

            mock_enum.assert_called_once_with("example.com", True)


class TestSubfinderParsing:
    """Test result parsing logic."""

    def test_json_parsing(self):
        """Test JSON output parsing."""
        # Simulate the parsing logic from the integration
        output = '{"host":"sub1.example.com"}\n{"host":"sub2.example.com"}\n'
        subdomains = []

        for line in output.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                host = data.get("host", "")
                if host:
                    subdomains.append(host)
            except json.JSONDecodeError:
                if line and not line.startswith("["):
                    subdomains.append(line.strip())

        assert len(subdomains) == 2
        assert "sub1.example.com" in subdomains

    def test_plain_text_fallback_parsing(self):
        """Test plain text fallback parsing."""
        output = "sub1.example.com\n[info] Starting\nsub2.example.com\n"
        subdomains = []

        for line in output.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                host = data.get("host", "")
                if host:
                    subdomains.append(host)
            except json.JSONDecodeError:
                if line and not line.startswith("["):
                    subdomains.append(line.strip())

        assert len(subdomains) == 2
        assert "sub1.example.com" in subdomains
        assert "[info] Starting" not in subdomains

    def test_empty_output_parsing(self):
        """Test empty output parsing."""
        output = ""
        subdomains = []

        for line in output.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                host = data.get("host", "")
                if host:
                    subdomains.append(host)
            except json.JSONDecodeError:
                if line and not line.startswith("["):
                    subdomains.append(line.strip())

        assert subdomains == []
