"""Test zen_shield imports"""

import pytest


class TestZenShieldImports:
    """Test zen_shield can be imported"""

    def test_sanitizer_import(self):
        from zen_shield.sanitizer import ZenSanitizer

        assert ZenSanitizer is not None

    def test_circuit_breaker_import(self):
        from zen_shield.circuit_breaker import CircuitBreaker

        assert CircuitBreaker is not None

    def test_server_import(self):
        from zen_shield.server import BatchSanitizeRequest

        assert BatchSanitizeRequest is not None
