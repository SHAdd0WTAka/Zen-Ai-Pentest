"""Test websocket imports"""

import pytest


class TestWebsocketImports:
    """Test websocket can be imported"""

    def test_websocket_manager_import(self):
        from api.websocket_manager import ConnectionManager

        assert ConnectionManager is not None
