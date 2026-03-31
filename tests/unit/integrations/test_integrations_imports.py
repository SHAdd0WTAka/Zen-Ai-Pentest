"""Test integration imports"""

import pytest


class TestIntegrationImports:
    """Test all integrations can be imported"""

    def test_jira_import(self):
        from integrations.jira_client import JiraClient

        assert JiraClient is not None

    def test_defect_dojo_import(self):
        from integrations.defect_dojo import DefectDojoClient

        assert DefectDojoClient is not None


class TestNotificationsImports:
    """Test notification modules can be imported"""

    def test_slack_import(self):
        from notifications.slack import SlackNotifier

        assert SlackNotifier is not None

    def test_email_import(self):
        from notifications.email import EmailNotifier

        assert EmailNotifier is not None

    def test_discord_import(self):
        from notifications.discord import DiscordNotifier

        assert DiscordNotifier is not None

    def test_telegram_import(self):
        from notifications.telegram import TelegramNotifier

        assert TelegramNotifier is not None
