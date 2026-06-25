"""Smoke tests for core/integrated_security.py"""

import pytest

try:
    from core.integrated_security import IntegratedSecurityManager, SecurityError, SecurityStatus, get_security_manager

    HAS_SECURITY = True
except ImportError as e:
    HAS_SECURITY = False
    IMPORT_ERROR = str(e)


class TestSecurityStatus:
    def test_dataclass_fields(self):
        if not HAS_SECURITY:
            pytest.skip(f"Skipped: {IMPORT_ERROR}")
        status = SecurityStatus(
            kill_switch_armed=True,
            p2p_connected=False,
            vault_unlocked=False,
            active_credentials=0,
            last_heartbeat=None,
            session_duration=None,
        )
        assert status.kill_switch_armed is True
        assert status.p2p_connected is False
        assert status.active_credentials == 0


class TestSecurityError:
    def test_is_exception(self):
        if not HAS_SECURITY:
            pytest.skip(f"Skipped: {IMPORT_ERROR}")
        exc = SecurityError("test error")
        assert isinstance(exc, Exception)
        assert str(exc) == "test error"


class TestIntegratedSecurityManager:
    def test_init(self):
        if not HAS_SECURITY:
            pytest.skip(f"Skipped: {IMPORT_ERROR}")
        manager = IntegratedSecurityManager()
        assert manager.kill_switch is not None
        assert manager.temporal_ca is not None
        assert manager.vault_manager is not None

    def test_get_status_defaults(self):
        if not HAS_SECURITY:
            pytest.skip(f"Skipped: {IMPORT_ERROR}")
        manager = IntegratedSecurityManager()
        status = manager.get_status()
        assert isinstance(status, SecurityStatus)


class TestGetSecurityManager:
    def test_returns_manager(self):
        if not HAS_SECURITY:
            pytest.skip(f"Skipped: {IMPORT_ERROR}")
        mgr = get_security_manager()
        assert isinstance(mgr, IntegratedSecurityManager)

    def test_singleton(self):
        if not HAS_SECURITY:
            pytest.skip(f"Skipped: {IMPORT_ERROR}")
        mgr1 = get_security_manager()
        mgr2 = get_security_manager()
        assert mgr1 is mgr2
