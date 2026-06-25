"""Smoke tests for notifications/email_sender.py"""

import pytest

from notifications.email_sender import EmailConfig, EmailReporter, send_report_after_scan


class TestEmailConfig:
    def test_defaults(self):
        config = EmailConfig(smtp_host="smtp.example.com", smtp_port=587, username="user", password="pass")
        assert config.smtp_host == "smtp.example.com"
        assert config.smtp_port == 587
        assert config.use_tls is True

    def test_validate_valid(self):
        config = EmailConfig(smtp_host="smtp.example.com", smtp_port=587, username="user", password="pass")
        assert config.validate() is True

    def test_validate_invalid(self):
        config = EmailConfig(smtp_host="", smtp_port=0, username="", password="")
        assert config.validate() is False

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("SMTP_USER", "test@gmail.com")
        monkeypatch.setenv("SMTP_PASS", "secret")
        config = EmailConfig.from_env()
        assert config.smtp_host == "smtp.gmail.com"
        assert config.username == "test@gmail.com"


class TestEmailReporter:
    def test_init_with_config(self):
        config = EmailConfig(smtp_host="smtp.example.com", smtp_port=587, username="user", password="pass")
        reporter = EmailReporter(config)
        assert reporter.config.smtp_host == "smtp.example.com"

    def test_init_from_env(self, monkeypatch):
        monkeypatch.setenv("SMTP_HOST", "smtp.mail.com")
        monkeypatch.setenv("SMTP_PORT", "465")
        monkeypatch.setenv("SMTP_USER", "u")
        monkeypatch.setenv("SMTP_PASS", "p")
        reporter = EmailReporter()
        assert reporter.config.smtp_host == "smtp.mail.com"


class TestSendReportAfterScan:
    def test_function_exists(self):
        assert callable(send_report_after_scan)
