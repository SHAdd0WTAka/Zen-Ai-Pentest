"""Smoke tests for modules/osint_super.py"""

import pytest

try:
    from modules.osint_super import OSINTSuperModule, OSINTSuperResult

    HAS_OSINT = True
except ImportError as e:
    HAS_OSINT = False
    IMPORT_ERROR = str(e)


class TestOSINTSuperResult:
    def test_creation(self):
        if not HAS_OSINT:
            pytest.skip(f"Skipped: {IMPORT_ERROR}")
        result = OSINTSuperResult(
            target="johndoe",
            target_type="username",
            timestamp="2026-01-01T00:00:00",
        )
        assert result.target == "johndoe"
        assert result.target_type == "username"
        assert result.social_media == {}
        assert result.email_check == {}
        assert result.summary == {}


class TestOSINTSuperModule:
    def test_init(self):
        if not HAS_OSINT:
            pytest.skip(f"Skipped: {IMPORT_ERROR}")
        module = OSINTSuperModule(output_dir="/tmp/test_osint_reports")
        assert module.output_dir is not None
        assert module.sherlock is not None
        assert module.ignorant is not None
        assert module.subfinder is not None
        assert module.amass is not None
        assert module.whatweb is not None

    def test_init_creates_output_dir(self):
        if not HAS_OSINT:
            pytest.skip(f"Skipped: {IMPORT_ERROR}")
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "reports")
            module = OSINTSuperModule(output_dir=output)
            assert os.path.isdir(output)

    def test_generate_username_summary_empty(self):
        if not HAS_OSINT:
            pytest.skip(f"Skipped: {IMPORT_ERROR}")
        module = OSINTSuperModule(output_dir="/tmp/test_osint_reports")
        result = OSINTSuperResult(
            target="testuser",
            target_type="username",
            timestamp="2026-01-01T00:00:00",
        )
        summary = module._generate_username_summary(result)
        assert summary["risk_level"] == "low"
        assert summary["accounts_found"] == 0
        assert summary["recommendations"] == []

    def test_generate_email_summary_empty(self):
        if not HAS_OSINT:
            pytest.skip(f"Skipped: {IMPORT_ERROR}")
        module = OSINTSuperModule(output_dir="/tmp/test_osint_reports")
        result = OSINTSuperResult(
            target="test@example.com",
            target_type="email",
            timestamp="2026-01-01T00:00:00",
        )
        summary = module._generate_email_summary(result)
        assert summary["risk_level"] == "low"
        assert summary["email_platforms"] == 0

    def test_generate_domain_summary_empty(self):
        if not HAS_OSINT:
            pytest.skip(f"Skipped: {IMPORT_ERROR}")
        module = OSINTSuperModule(output_dir="/tmp/test_osint_reports")
        result = OSINTSuperResult(
            target="example.com",
            target_type="domain",
            timestamp="2026-01-01T00:00:00",
        )
        summary = module._generate_domain_summary(result)
        assert summary["risk_level"] == "low"
        assert summary["subdomains"] == 0
        assert summary["attack_surface"] == "small"
