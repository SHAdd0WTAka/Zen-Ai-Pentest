"""Tests for utils.sudo_check module."""

import os

import pytest


class TestIsRoot:
    def test_returns_bool(self):
        from utils.sudo_check import is_root

        result = is_root()
        assert isinstance(result, bool)


class TestRequireRoot:
    def test_raises_permission_error_when_not_root(self):
        from utils.sudo_check import require_root

        if os.geteuid() != 0:
            with pytest.raises(PermissionError) as excinfo:
                require_root("Need sudo")
            assert "Need sudo" in str(excinfo.value)
        else:
            require_root("test")


class TestCheckRootWarning:
    def test_returns_bool(self):
        from utils.sudo_check import check_root_warning

        result = check_root_warning()
        assert isinstance(result, bool)
