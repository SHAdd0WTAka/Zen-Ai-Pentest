"""Test credential lifecycle"""

import pytest


class TestCredentialLifecycle:
    """Test credential lifecycle"""

    def test_import(self):
        from core.credential_lifecycle import CredentialType

        assert CredentialType is not None

    def test_status_import(self):
        from core.credential_lifecycle import CredentialStatus

        assert CredentialStatus is not None

    def test_temporal_import(self):
        from core.credential_lifecycle import TemporalCredential

        assert TemporalCredential is not None
