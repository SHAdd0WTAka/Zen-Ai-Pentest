"""Smoke tests for core/kimi_hermes_bridge.py"""

from pathlib import Path

import pytest

from core.kimi_hermes_bridge import KIMI_CREDENTIALS, KimiHermesBridge


class TestKimiHermesBridge:
    def test_init(self):
        bridge = KimiHermesBridge()
        assert bridge.token is None

    def test_get_best_token_returns_dict(self):
        token = KimiHermesBridge.get_best_token()
        assert token == {}

    def test_export_credentials_returns_false(self):
        bridge = KimiHermesBridge()
        assert bridge.export_credentials() is False


class TestConstants:
    def test_kimi_credentials_path(self):
        assert isinstance(KIMI_CREDENTIALS, Path)
        assert ".kimi-code" in str(KIMI_CREDENTIALS)
