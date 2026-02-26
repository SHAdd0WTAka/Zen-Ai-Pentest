"""Einfache API Module Tests."""

import pytest

def test_api_main_import():
    """Test that api.main can be imported."""
    from api.main import app
    assert app is not None

def test_api_auth_import():
    """Test that api.auth can be imported."""
    from api.auth import create_access_token
    assert create_access_token is not None

def test_api_schemas_import():
    """Test that api.schemas can be imported."""
    from api.schemas import ScanCreate
    assert ScanCreate is not None
