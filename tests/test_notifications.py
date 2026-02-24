"""
Comprehensive tests for the notification system.

Tests cover:
- Email notifications (EmailNotifier)
- Slack notifications (SlackNotifier)
- Notification templates
- Webhook validation
- Error handling
"""

import json
import os
from datetime import datetime
from unittest.mock import Mock, mock_open, patch

import pytest
import requests

from notifications.email import EmailNotifier, email_scan_report
from notifications.slack import (
    SlackNotifier,
    _validate_slack_webhook_url,
    slack_notify_scan_complete,
)

# =============================================================================
# Email Notifier Tests
# =============================================================================


class TestEmailNotifier:
    """Tests for EmailNotifier class."""

    @pytest.fixture
    def email_notifier(self):
        """Create a test email notifier."""
        return EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password123",
            use_tls=True,
            from_addr="sender@example.com",
        )

    def test_initialization(self, email_notifier):
        """Test email notifier initialization."""
        assert email_notifier.smtp_host == "smtp.example.com"
        assert email_notifier.smtp_port == 587
        assert email_notifier.username == "test@example.com"
        assert email_notifier.password == "password123"
        assert email_notifier.use_tls is True
        assert email_notifier.from_addr == "sender@example.com"

    def test_initialization_defaults(self):
        """Test initialization with default values."""
        notifier = EmailNotifier(smtp_host="smtp.example.com")

        assert notifier.smtp_port == 587
        assert notifier.use_tls is True
        assert notifier.from_addr == notifier.username  # Defaults to username

    @patch("smtplib.SMTP")
    def test_send_email_success(self, mock_smtp_class, email_notifier):
        """Test successful email sending."""
        mock_smtp = Mock()
        mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = Mock(return_value=False)

        result = email_notifier.send_email(
            to_addrs=["recipient@example.com"],
            subject="Test Subject",
            body_text="Test body text",
        )

        assert result is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with(
            "test@example.com", "password123"
        )
        mock_smtp.sendmail.assert_called_once()

        # Check email parameters
        call_args = mock_smtp.sendmail.call_args
        assert call_args[0][0] == "sender@example.com"
        assert call_args[0][1] == ["recipient@example.com"]

    @patch("smtplib.SMTP")
    def test_send_email_multiple_recipients(
        self, mock_smtp_class, email_notifier
    ):
        """Test sending to multiple recipients."""
        mock_smtp = Mock()
        mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = Mock(return_value=False)

        result = email_notifier.send_email(
            to_addrs=["recipient1@example.com", "recipient2@example.com"],
            subject="Test",
            body_text="Test body",
        )

        assert result is True
        call_args = mock_smtp.sendmail.call_args
        assert call_args[0][1] == [
            "recipient1@example.com",
            "recipient2@example.com",
        ]

    @patch("smtplib.SMTP")
    def test_send_email_with_html(self, mock_smtp_class, email_notifier):
        """Test sending email with HTML body."""
        mock_smtp = Mock()
        mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = Mock(return_value=False)

        result = email_notifier.send_email(
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_text="Plain text",
            body_html="<html><body>HTML body</body></html>",
        )

        assert result is True
        # Check that sendmail was called with multipart message
        call_args = mock_smtp.sendmail.call_args
        message = call_args[0][2]
        assert "multipart" in message
        assert "Plain text" in message
        assert "HTML body" in message

    @patch("smtplib.SMTP")
    @patch("builtins.open", mock_open(read_data=b"PDF content"))
    def test_send_email_with_attachments(
        self, mock_smtp_class, email_notifier
    ):
        """Test sending email with attachments."""
        mock_smtp = Mock()
        mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = Mock(return_value=False)

        result = email_notifier.send_email(
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_text="See attached report",
            attachments=["/path/to/test_report.pdf"],
        )

        assert result is True
        call_args = mock_smtp.sendmail.call_args
        message = call_args[0][2]
        assert (
            "application/pdf" in message
            or "octet-stream" in message
            or "PDF content" in message
        )

    @patch("smtplib.SMTP")
    def test_send_email_failure(self, mock_smtp_class, email_notifier):
        """Test email sending failure."""
        mock_smtp = Mock()
        mock_smtp.sendmail.side_effect = Exception("SMTP Error")
        mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = Mock(return_value=False)

        result = email_notifier.send_email(
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_text="Test body",
        )

        assert result is False

    @patch("smtplib.SMTP")
    def test_send_email_no_auth(self, mock_smtp_class):
        """Test sending email without authentication."""
        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            use_tls=False,
            from_addr="sender@example.com",
        )

        mock_smtp = Mock()
        mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = Mock(return_value=False)

        result = notifier.send_email(
            to_addrs=["recipient@example.com"],
            subject="Test",
            body_text="Test body",
        )

        assert result is True
        mock_smtp.login.assert_not_called()

    @patch("smtplib.SMTP")
    @patch("builtins.open", mock_open(read_data=b"PDF content"))
    def test_send_scan_report(self, mock_smtp_class, email_notifier):
        """Test sending scan report email."""
        mock_smtp = Mock()
        mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = Mock(return_value=False)

        findings = [
            {"severity": "critical", "title": "Critical Issue"},
            {"severity": "high", "title": "High Issue"},
            {"severity": "high", "title": "Another High"},
            {"severity": "medium", "title": "Medium Issue"},
        ]

        result = email_notifier.send_scan_report(
            to_addrs=["admin@example.com"],
            scan_id=12345,
            target="example.com",
            report_file="/path/to/report.pdf",
            findings=findings,
        )

        assert result is True

        # Check email content
        call_args = mock_smtp.sendmail.call_args
        message = call_args[0][2]

        # Should include scan info
        assert "example.com" in message
        assert "12345" in message

        # Should include severity counts
        assert "Critical: 1" in message
        assert "High: 2" in message
        assert "Medium: 1" in message

    @patch("smtplib.SMTP")
    def test_send_scan_report_no_findings(
        self, mock_smtp_class, email_notifier
    ):
        """Test scan report with no findings."""
        mock_smtp = Mock()
        mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = Mock(return_value=False)

        result = email_notifier.send_scan_report(
            to_addrs=["admin@example.com"],
            scan_id=12345,
            target="example.com",
            report_file=None,
            findings=[],
        )

        assert result is True
        call_args = mock_smtp.sendmail.call_args
        message = call_args[0][2]
        assert "Critical: 0" in message
        assert "Total: 0" in message


class TestEmailScanReport:
    """Tests for email_scan_report convenience function."""

    @patch.dict(
        os.environ,
        {
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_USER": "user@gmail.com",
            "SMTP_PASS": "app_password",
        },
    )
    @patch("notifications.email.EmailNotifier")
    def test_email_scan_report_success(self, mock_notifier_class):
        """Test successful scan report email."""
        mock_notifier = Mock()
        mock_notifier.send_email = Mock(return_value=True)
        mock_notifier_class.return_value = mock_notifier

        result = email_scan_report(
            recipient="admin@example.com",
            scan_id=123,
            report_file="/path/to/report.pdf",
        )

        assert result == "Email sent"
        mock_notifier_class.assert_called_once_with(
            "smtp.gmail.com",
            username="user@gmail.com",
            password="app_password",
        )
        mock_notifier.send_email.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    def test_email_scan_report_no_credentials(self):
        """Test scan report without credentials."""
        result = email_scan_report(
            recipient="admin@example.com",
            scan_id=123,
            report_file="/path/to/report.pdf",
        )

        assert "credentials not configured" in result


# =============================================================================
# Slack Notifier Tests
# =============================================================================


class TestSlackWebhookValidation:
    """Tests for Slack webhook URL validation."""

    def test_valid_webhook_url(self):
        """Test validation of valid Slack webhook URL."""
        url = "https://hooks.slack.com/services/T00/B00/PLACEHOLDER"
        result = _validate_slack_webhook_url(url)
        assert result == url

    def test_empty_url(self):
        """Test validation with empty URL."""
        with pytest.raises(ValueError, match="webhook_url is required"):
            _validate_slack_webhook_url("")

    def test_none_url(self):
        """Test validation with None URL."""
        with pytest.raises(ValueError, match="webhook_url is required"):
            _validate_slack_webhook_url(None)

    def test_invalid_scheme(self):
        """Test validation with invalid scheme."""
        with pytest.raises(ValueError, match="Invalid webhook URL scheme"):
            _validate_slack_webhook_url("ftp://hooks.slack.com/services/xxx")

    def test_invalid_host(self):
        """Test validation with non-Slack host."""
        with pytest.raises(ValueError, match="Webhook host is not allowed"):
            _validate_slack_webhook_url("https://evil.com/webhook")

    def test_malformed_url(self):
        """Test validation with malformed URL."""
        with pytest.raises(ValueError, match="Invalid webhook URL"):
            _validate_slack_webhook_url("not_a_url")


class TestSlackNotifier:
    """Tests for SlackNotifier class."""

    @pytest.fixture
    def slack_notifier(self):
        """Create a test Slack notifier."""
        return SlackNotifier("https://hooks.slack.com/services/T00/B00/XXX")

    def test_initialization(self, slack_notifier):
        """Test Slack notifier initialization."""
        assert (
            slack_notifier.webhook_url
            == "https://hooks.slack.com/services/T00/B00/XXX"
        )

    def test_initialization_invalid_url(self):
        """Test initialization with invalid URL."""
        with pytest.raises(ValueError):
            SlackNotifier("https://evil.com/webhook")

    @patch("requests.post")
    def test_send_message_success(self, mock_post, slack_notifier):
        """Test successful message sending."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = slack_notifier.send_message("Hello, Slack!")

        assert result is True
        mock_post.assert_called_once()

        # Check payload
        call_args = mock_post.call_args
        assert (
            call_args[0][0] == "https://hooks.slack.com/services/T00/B00/XXX"
        )
        payload = call_args[1]["json"]
        assert payload["text"] == "Hello, Slack!"

    @patch("requests.post")
    def test_send_message_with_channel(self, mock_post, slack_notifier):
        """Test sending message to specific channel."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = slack_notifier.send_message("Hello", channel="#alerts")

        assert result is True
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["channel"] == "#alerts"

    @patch("requests.post")
    def test_send_message_failure(self, mock_post, slack_notifier):
        """Test message sending failure."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        result = slack_notifier.send_message("Hello")

        assert result is False

    @patch("requests.post")
    def test_send_message_exception(self, mock_post, slack_notifier):
        """Test message sending with exception."""
        mock_post.side_effect = requests.RequestException("Connection error")

        result = slack_notifier.send_message("Hello")

        assert result is False

    @patch("requests.post")
    def test_send_scan_completed_success(self, mock_post, slack_notifier):
        """Test successful scan completion notification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = slack_notifier.send_scan_completed(
            scan_id=12345,
            target="example.com",
            findings_count=10,
            critical_count=2,
        )

        assert result is True
        mock_post.assert_called_once()

        # Check payload structure
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert "attachments" in payload
        attachment = payload["attachments"][0]
        assert attachment["color"] == "danger"  # Because critical_count > 0
        assert "Pentest Scan Completed" in attachment["title"]

        # Check fields
        fields = {f["title"]: f["value"] for f in attachment["fields"]}
        assert fields["Scan ID"] == "12345"
        assert fields["Target"] == "example.com"
        assert fields["Total Findings"] == 10
        assert fields["Critical"] == 2

    @patch("requests.post")
    def test_send_scan_completed_warning(self, mock_post, slack_notifier):
        """Test scan completion with warning color (findings but no critical)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = slack_notifier.send_scan_completed(
            scan_id=12345,
            target="example.com",
            findings_count=5,
            critical_count=0,
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["attachments"][0]["color"] == "warning"

    @patch("requests.post")
    def test_send_scan_completed_good(self, mock_post, slack_notifier):
        """Test scan completion with good color (no findings)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = slack_notifier.send_scan_completed(
            scan_id=12345,
            target="example.com",
            findings_count=0,
            critical_count=0,
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["attachments"][0]["color"] == "good"

    @patch("requests.post")
    def test_send_critical_finding(self, mock_post, slack_notifier):
        """Test critical finding notification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        finding = {
            "title": "SQL Injection",
            "description": "A critical SQL injection vulnerability was found in the login form.",
            "target": "https://example.com/login",
            "tool": "sqlmap",
            "cvss_score": 9.8,
        }

        result = slack_notifier.send_critical_finding(finding)

        assert result is True

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        attachment = payload["attachments"][0]

        assert attachment["color"] == "danger"
        assert "CRITICAL: SQL Injection" in attachment["title"]
        assert "SQL injection vulnerability" in attachment["text"]

        fields = {f["title"]: f["value"] for f in attachment["fields"]}
        assert fields["Severity"] == "CRITICAL"
        assert fields["Target"] == "https://example.com/login"
        assert fields["Tool"] == "sqlmap"
        assert fields["CVSS"] == "9.8"

    @patch("requests.post")
    def test_send_critical_finding_minimal(self, mock_post, slack_notifier):
        """Test critical finding with minimal data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        finding = {
            "title": "Unknown Issue"
            # Missing other fields
        }

        result = slack_notifier.send_critical_finding(finding)

        assert result is True
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert "attachments" in payload


class TestSlackNotifyScanComplete:
    """Tests for slack_notify_scan_complete convenience function."""

    @patch.dict(
        os.environ,
        {"SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/T00/B00/XXX"},
    )
    @patch("notifications.slack.SlackNotifier")
    def test_notify_success(self, mock_notifier_class):
        """Test successful notification."""
        mock_notifier = Mock()
        mock_notifier.send_scan_completed = Mock(return_value=True)
        mock_notifier_class.return_value = mock_notifier

        result = slack_notify_scan_complete(
            scan_id=123,
            target="example.com",
            findings_count=5,
            critical_count=1,
        )

        assert result == "Notification sent"
        mock_notifier_class.assert_called_once()
        mock_notifier.send_scan_completed.assert_called_once_with(
            123, "example.com", 5, 1
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_notify_no_webhook(self):
        """Test notification without webhook configured."""
        result = slack_notify_scan_complete(
            scan_id=123,
            target="example.com",
            findings_count=5,
            critical_count=0,
        )

        assert "webhook not configured" in result

    @patch.dict(os.environ, {"SLACK_WEBHOOK_URL": "https://evil.com/webhook"})
    def test_notify_invalid_webhook(self):
        """Test notification with invalid webhook."""
        result = slack_notify_scan_complete(
            scan_id=123,
            target="example.com",
            findings_count=5,
            critical_count=0,
        )

        assert "Invalid Slack webhook configuration" in result


# =============================================================================
# Integration Tests
# =============================================================================


class TestNotificationIntegration:
    """Integration tests for notification system."""

    @patch("smtplib.SMTP")
    @patch("requests.post")
    @patch("builtins.open", mock_open(read_data=b"PDF content"))
    def test_dual_notification(self, mock_post, mock_smtp_class, mock_file):
        """Test sending both email and Slack notifications."""
        # Setup mocks
        mock_smtp = Mock()
        mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp_class.return_value.__exit__ = Mock(return_value=False)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Send email
        email_notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            username="test@example.com",
            password="pass",
        )
        email_result = email_notifier.send_scan_report(
            to_addrs=["admin@example.com"],
            scan_id=123,
            target="example.com",
            report_file="/path/to/report.pdf",
            findings=[{"severity": "high", "title": "Issue"}],
        )

        # Send Slack
        slack_notifier = SlackNotifier(
            "https://hooks.slack.com/services/T00/B00/XXX"
        )
        slack_result = slack_notifier.send_scan_completed(
            scan_id=123,
            target="example.com",
            findings_count=1,
            critical_count=0,
        )

        assert email_result is True
        assert slack_result is True
        mock_smtp.sendmail.assert_called_once()
        mock_post.assert_called_once()

    def test_notification_templates(self):
        """Test that notification templates are properly formatted."""
        # This test verifies the structure of notification payloads
        # without actually sending them

        with patch("smtplib.SMTP"):
            email_notifier = EmailNotifier(
                smtp_host="smtp.example.com", from_addr="test@example.com"
            )

            # Capture the email content
            with patch.object(email_notifier, "send_email") as mock_send:
                mock_send.return_value = True

                email_notifier.send_scan_report(
                    to_addrs=["admin@example.com"],
                    scan_id=12345,
                    target="example.com",
                    report_file="report.pdf",
                    findings=[
                        {"severity": "critical", "title": "Crit"},
                        {"severity": "high", "title": "High"},
                        {"severity": "high", "title": "High2"},
                        {"severity": "medium", "title": "Med"},
                    ],
                )

                # Verify the call
                assert mock_send.called
                call_kwargs = mock_send.call_args[1]

                assert "Pentest Report: example.com" in call_kwargs["subject"]
                assert "Critical: 1" in call_kwargs["body_text"]
                assert "High: 2" in call_kwargs["body_text"]
                assert "Medium: 1" in call_kwargs["body_text"]
                assert "Total: 4" in call_kwargs["body_text"]

                # HTML version should have styling
                assert "<html>" in call_kwargs["body_html"]
                assert "color: red" in call_kwargs["body_html"]

    @patch("requests.post")
    def test_slack_message_structure(self, mock_post):
        """Test Slack message structure for different scenarios."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notifier = SlackNotifier(
            "https://hooks.slack.com/services/T00/B00/XXX"
        )

        # Test scan completion message
        notifier.send_scan_completed(1, "test.com", 5, 0)

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        # Verify structure
        assert "attachments" in payload
        assert len(payload["attachments"]) == 1
        attachment = payload["attachments"][0]
        assert "title" in attachment
        assert "fields" in attachment
        assert "footer" in attachment
        assert "ts" in attachment

        # Should have 4 fields
        assert len(attachment["fields"]) == 4
        field_titles = [f["title"] for f in attachment["fields"]]
        assert "Scan ID" in field_titles
        assert "Target" in field_titles
        assert "Total Findings" in field_titles
        assert "Critical" in field_titles

        # All fields should have short=True for side-by-side display
        assert all(f.get("short") for f in attachment["fields"])
