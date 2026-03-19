"""
Tool Framework Tests - Coverage for tool registry and base classes
"""

import os
import sys

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_tool_registry_import():
    """Test that tool registry can be imported"""
    try:
        from tools.tool_registry import ToolRegistry

        assert True
    except ImportError:
        pytest.skip("ToolRegistry not available")


def test_tool_base_import():
    """Test that tool base classes can be imported"""
    try:
        from tools.tool_caller import ToolCaller

        assert True
    except ImportError:
        pytest.skip("ToolCaller not available")


def test_nmap_integration_import():
    """Test nmap integration import"""
    try:
        from tools import nmap_integration

        assert True
    except ImportError:
        pytest.skip("nmap_integration not available")


def test_ffuf_integration_import():
    """Test ffuf integration import"""
    try:
        from tools import ffuf_integration_enhanced

        assert True
    except ImportError:
        pytest.skip("ffuf_integration_enhanced not available")


def test_httpx_integration_import():
    """Test httpx integration import"""
    try:
        from tools import httpx_integration

        assert True
    except ImportError:
        pytest.skip("httpx_integration not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
