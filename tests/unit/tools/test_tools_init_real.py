"""REAL tests for tools __init__ module."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# Test importing the tools package
def test_tools_import():
    """Test that tools package can be imported."""
    import tools

    assert tools is not None


def test_tools_has_integrations():
    """Test that tools has integrations."""
    from tools import integrations

    assert integrations is not None


def test_nmap_available():
    """Test nmap integration availability."""
    from tools import nmap_integration

    assert nmap_integration is not None
    assert hasattr(nmap_integration, "NmapScanner")


def test_nmap_scantype_available():
    """Test ScanType enum available."""
    from tools.nmap_integration import ScanType

    assert len(ScanType) > 0


def test_nmap_timing_available():
    """Test TimingTemplate enum available."""
    from tools.nmap_integration import TimingTemplate

    assert len(TimingTemplate) > 0
