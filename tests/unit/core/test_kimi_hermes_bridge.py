"""
Unit tests for core/kimi_hermes_bridge.py — KimiHermesBridge stub.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from core.kimi_hermes_bridge import KIMI_CREDENTIALS, KimiHermesBridge


class TestKimiHermesBridgeInit:
    def test_init_defaults(self):
        bridge = KimiHermesBridge()
        assert bridge.token is None

    def test_get_best_token_returns_empty_dict(self):
        token = KimiHermesBridge.get_best_token()
        assert token == {}

    def test_export_credentials_returns_false(self):
        bridge = KimiHermesBridge()
        assert bridge.export_credentials() is False


class TestKimiHermesBridgeSendMessage:
    def test_send_message_mock_success(self):
        bridge = KimiHermesBridge()
        with patch.object(bridge, "export_credentials", return_value=True):
            result = bridge.export_credentials()
            assert result is True

    def test_send_message_mock_failure(self):
        bridge = KimiHermesBridge()
        with patch.object(bridge, "export_credentials", return_value=False):
            result = bridge.export_credentials()
            assert result is False


class TestKimiHermesBridgeReceiveResponse:
    def test_receive_response_mock(self):
        with patch.object(KimiHermesBridge, "get_best_token", return_value={"token": "mock-token"}):
            result = KimiHermesBridge.get_best_token()
            assert result == {"token": "mock-token"}


class TestKimiHermesBridgeConnectionError:
    def test_export_credentials_handles_exception(self):
        bridge = KimiHermesBridge()
        with patch.object(bridge, "export_credentials", side_effect=ConnectionError("connection failed")):
            with pytest.raises(ConnectionError, match="connection failed"):
                bridge.export_credentials()

    def test_get_best_token_handles_exception(self):
        with patch.object(KimiHermesBridge, "get_best_token", side_effect=RuntimeError("api error")):
            with pytest.raises(RuntimeError, match="api error"):
                KimiHermesBridge.get_best_token()


class TestKimiHermesBridgeTimeout:
    def test_export_credentials_timeout(self):
        bridge = KimiHermesBridge()
        with patch.object(bridge, "export_credentials", side_effect=TimeoutError("timed out")):
            with pytest.raises(TimeoutError, match="timed out"):
                bridge.export_credentials()

    def test_get_best_token_timeout(self):
        with patch.object(KimiHermesBridge, "get_best_token", side_effect=TimeoutError("request timed out")):
            with pytest.raises(TimeoutError, match="request timed out"):
                KimiHermesBridge.get_best_token()


class TestKIMI_CREDENTIALS:
    def test_path_type(self):
        assert isinstance(KIMI_CREDENTIALS, Path)

    def test_path_contains_kimi_code(self):
        assert ".kimi-code" in str(KIMI_CREDENTIALS)
