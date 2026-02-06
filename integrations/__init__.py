"""
CI/CD and External Tool Integrations for Zen AI Pentest

This module provides integrations with:
- GitHub (Actions, Issues, PRs)
- GitLab (CI/CD, Issues)
- Jenkins (Pipelines)
- Slack (Notifications)
- JIRA (Issue tracking)

Usage:
    # GitHub Integration
    from integrations import GitHubIntegration
    
    github = GitHubIntegration(token="ghp_...")
    await github.create_security_issue(finding, repo="owner/repo")
    
    # Slack Notifications
    from integrations import SlackNotifier
    
    slack = SlackNotifier(webhook_url="https://hooks.slack.com/...")
    await slack.notify_scan_completed(results)
    
    # JIRA Integration
    from integrations import JiraIntegration
    
    jira = JiraIntegration(
        server="https://your-domain.atlassian.net",
        username="user@example.com",
        api_token="..."
    )
    await jira.create_finding_ticket(finding, project="SEC")
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class IntegrationStatus(Enum):
    """Status of an integration."""
    CONFIGURED = "configured"
    CONNECTED = "connected"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class IntegrationConfig:
    """Configuration for an integration."""
    name: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    status: IntegrationStatus = IntegrationStatus.DISABLED
    last_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "status": self.status.value,
            "last_error": self.last_error
        }


# GitHub Integration
class GitHubIntegration:
    """Integration with GitHub for security workflows."""
    
    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        self.token = token
        self.base_url = base_url.rstrip('/')
        self.config = IntegrationConfig(name="github", enabled=bool(token))
        self._session = None
    
    async def _get_session(self):
        """Get or create aiohttp session."""
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
        return self._session
    
    async def test_connection(self) -> bool:
        """Test GitHub API connection."""
        if not self.token:
            return False
        
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/user") as resp:
                if resp.status == 200:
                    self.config.status = IntegrationStatus.CONNECTED
                    return True
                else:
                    self.config.status = IntegrationStatus.ERROR
                    return False
        except Exception as e:
            self.config.status = IntegrationStatus.ERROR
            self.config.last_error = str(e)
            logger.error(f"GitHub connection test failed: {e}")
            return False
    
    async def create_security_issue(
        self,
        finding: Dict[str, Any],
        repo: str,
        labels: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a security issue in a GitHub repository."""
        if not self.token:
            logger.warning("GitHub token not configured")
            return None
        
        session = await self._get_session()
        
        severity = finding.get('severity', 'Medium')
        title = f"[SECURITY] [{severity}] {finding.get('title', 'Security Finding')}"
        
        body = f"""## Security Finding Detected

**Severity:** {severity}
**Tool:** {finding.get('tool', 'Zen AI Pentest')}
**Target:** {finding.get('target', 'N/A')}

### Description
{finding.get('description', 'No description available.')}

### Remediation
{finding.get('remediation', 'No remediation steps provided.')}

---
*This issue was automatically created by Zen AI Pentest*
"""
        
        payload = {
            "title": title,
            "body": body,
            "labels": labels or ["security", "vulnerability", f"severity:{severity.lower()}"]
        }
        
        try:
            async with session.post(
                f"{self.base_url}/repos/{repo}/issues",
                json=payload
            ) as resp:
                if resp.status == 201:
                    return await resp.json()
                else:
                    logger.error(f"Failed to create GitHub issue: {resp.status}")
                    return None
        except Exception as e:
            logger.error(f"GitHub API error: {e}")
            return None
    
    async def create_check_run(
        self,
        repo: str,
        name: str,
        head_sha: str,
        status: str = "completed",
        conclusion: str = "neutral",
        output: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a check run for security scanning results."""
        if not self.token:
            return None
        
        session = await self._get_session()
        
        payload = {
            "name": name,
            "head_sha": head_sha,
            "status": status,
            "conclusion": conclusion,
            "output": output or {}
        }
        
        try:
            async with session.post(
                f"{self.base_url}/repos/{repo}/check-runs",
                json=payload
            ) as resp:
                if resp.status == 201:
                    return await resp.json()
                return None
        except Exception as e:
            logger.error(f"Failed to create check run: {e}")
            return None


# GitLab Integration
class GitLabIntegration:
    """Integration with GitLab CI/CD and Issues."""
    
    def __init__(self, token: Optional[str] = None, base_url: str = "https://gitlab.com"):
        self.token = token
        self.base_url = base_url.rstrip('/')
        self.config = IntegrationConfig(name="gitlab", enabled=bool(token))
        self._session = None
    
    async def _get_session(self):
        """Get or create aiohttp session."""
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession(
                headers={"PRIVATE-TOKEN": self.token}
            )
        return self._session
    
    async def test_connection(self) -> bool:
        """Test GitLab API connection."""
        if not self.token:
            return False
        
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/v4/user") as resp:
                if resp.status == 200:
                    self.config.status = IntegrationStatus.CONNECTED
                    return True
                return False
        except Exception as e:
            logger.error(f"GitLab connection test failed: {e}")
            return False
    
    async def create_issue(
        self,
        project_id: str,
        finding: Dict[str, Any],
        labels: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a security issue in GitLab."""
        if not self.token:
            return None
        
        session = await self._get_session()
        
        severity = finding.get('severity', 'Medium')
        title = f"[SECURITY] [{severity}] {finding.get('title', 'Security Finding')}"
        
        description = f"""## Security Finding

**Severity:** {severity}
**Target:** {finding.get('target', 'N/A')}

### Description
{finding.get('description', 'No description available.')}

### Remediation
{finding.get('remediation', 'No remediation steps provided.')}

---
*Generated by Zen AI Pentest*
"""
        
        payload = {
            "title": title,
            "description": description,
            "labels": ",".join(labels or ["security", f"severity::{severity.lower()}"])
        }
        
        try:
            async with session.post(
                f"{self.base_url}/api/v4/projects/{project_id}/issues",
                data=payload
            ) as resp:
                if resp.status == 201:
                    return await resp.json()
                return None
        except Exception as e:
            logger.error(f"Failed to create GitLab issue: {e}")
            return None


# Jenkins Integration
class JenkinsIntegration:
    """Integration with Jenkins CI/CD."""
    
    def __init__(
        self,
        url: str,
        username: Optional[str] = None,
        api_token: Optional[str] = None
    ):
        self.url = url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.config = IntegrationConfig(
            name="jenkins",
            enabled=bool(username and api_token)
        )
    
    async def trigger_job(
        self,
        job_name: str,
        parameters: Dict[str, Any] = None
    ) -> bool:
        """Trigger a Jenkins job."""
        import aiohttp
        
        auth = aiohttp.BasicAuth(self.username, self.api_token)
        
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.url}/job/{job_name}/build"
                if parameters:
                    url += "WithParameters"
                
                async with session.post(url, auth=auth, data=parameters or {}) as resp:
                    return resp.status == 201
            except Exception as e:
                logger.error(f"Failed to trigger Jenkins job: {e}")
                return False


# Slack Notifier
class SlackNotifier:
    """Slack notification integration."""
    
    def __init__(self, webhook_url: Optional[str] = None, channel: Optional[str] = None):
        self.webhook_url = webhook_url
        self.channel = channel
        self.config = IntegrationConfig(name="slack", enabled=bool(webhook_url))
    
    async def notify_scan_started(self, target: str, scan_type: str = "security"):
        """Notify that a scan has started."""
        message = {
            "text": "🔍 Security scan started",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🔍 Zen AI Pentest - Scan Started"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Target:*\n{target}"},
                        {"type": "mrkdwn", "text": f"*Type:*\n{scan_type}"},
                        {"type": "mrkdwn", "text": f"*Time:*\n{datetime.now().isoformat()}"}
                    ]
                }
            ]
        }
        
        if self.channel:
            message["channel"] = self.channel
        
        await self._send(message)
    
    async def notify_scan_completed(
        self,
        results: Dict[str, Any],
        target: str
    ):
        """Notify that a scan has completed."""
        findings = results.get('findings', [])
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for finding in findings:
            sev = finding.get('severity', 'unknown').lower()
            if sev in severity_counts:
                severity_counts[sev] += 1
        
        message = {
            "text": f"✅ Security scan completed for {target}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Zen AI Pentest - Scan Completed"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Target:*\n{target}"},
                        {"type": "mrkdwn", "text": f"*Total Findings:*\n{len(findings)}"},
                        {"type": "mrkdwn", "text": f"*Critical:*\n{severity_counts['critical']}"},
                        {"type": "mrkdwn", "text": f"*High:*\n{severity_counts['high']}"},
                    ]
                }
            ]
        }
        
        if severity_counts['critical'] > 0:
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🚨 *Action Required:* {severity_counts['critical']} critical vulnerabilities found!"
                }
            })
        
        await self._send(message)
    
    async def notify_finding(self, finding: Dict[str, Any]):
        """Notify about a specific finding."""
        severity = finding.get('severity', 'Unknown')
        emoji = {"Critical": "🚨", "High": "⚠️", "Medium": "⚡", "Low": "ℹ️"}.get(severity, "ℹ️")
        
        message = {
            "text": f"{emoji} Security Finding: {finding.get('title', 'Unknown')}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} Security Finding Detected"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Title:*\n{finding.get('title', 'N/A')}"},
                        {"type": "mrkdwn", "text": f"*Severity:*\n{severity}"},
                        {"type": "mrkdwn", "text": f"*Target:*\n{finding.get('target', 'N/A')}"},
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Description:*\n{finding.get('description', 'No description')[:500]}"
                    }
                }
            ]
        }
        
        await self._send(message)
    
    async def _send(self, message: Dict[str, Any]):
        """Send message to Slack webhook."""
        if not self.webhook_url:
            logger.debug("Slack webhook not configured, skipping notification")
            return
        
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.webhook_url,
                    json=message
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"Slack notification failed: {resp.status}")
            except Exception as e:
                logger.error(f"Failed to send Slack notification: {e}")


# JIRA Integration (wrapper around existing jira_client)
class JiraIntegration:
    """Integration with JIRA for issue tracking."""
    
    def __init__(
        self,
        server: str,
        username: Optional[str] = None,
        api_token: Optional[str] = None
    ):
        self.server = server.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.config = IntegrationConfig(
            name="jira",
            enabled=bool(username and api_token)
        )
        self._client = None
    
    def _get_client(self):
        """Get or create JIRA client."""
        if self._client is None and self.config.enabled:
            try:
                from .jira_client import JiraClient
                self._client = JiraClient(
                    base_url=self.server,
                    username=self.username,
                    api_token=self.api_token
                )
            except Exception as e:
                logger.error(f"Failed to create JIRA client: {e}")
        return self._client
    
    async def test_connection(self) -> bool:
        """Test JIRA connection."""
        client = self._get_client()
        if not client:
            return False
        
        try:
            result = client.test_connection()
            self.config.status = IntegrationStatus.CONNECTED if result else IntegrationStatus.ERROR
            return result
        except Exception as e:
            self.config.status = IntegrationStatus.ERROR
            self.config.last_error = str(e)
            return False
    
    async def create_finding_ticket(
        self,
        finding: Dict[str, Any],
        project_key: str
    ) -> Optional[Dict[str, Any]]:
        """Create a ticket from a security finding."""
        client = self._get_client()
        if not client:
            logger.warning("JIRA not configured")
            return None
        
        try:
            return client.create_finding_ticket(finding, project_key)
        except Exception as e:
            logger.error(f"Failed to create JIRA ticket: {e}")
            return None


# Factory functions
def create_github_integration(config: Dict[str, Any]) -> GitHubIntegration:
    """Create GitHub integration from config."""
    return GitHubIntegration(
        token=config.get('token'),
        base_url=config.get('base_url', 'https://api.github.com')
    )


def create_gitlab_integration(config: Dict[str, Any]) -> GitLabIntegration:
    """Create GitLab integration from config."""
    return GitLabIntegration(
        token=config.get('token'),
        base_url=config.get('base_url', 'https://gitlab.com')
    )


def create_slack_notifier(config: Dict[str, Any]) -> SlackNotifier:
    """Create Slack notifier from config."""
    return SlackNotifier(
        webhook_url=config.get('webhook_url'),
        channel=config.get('channel')
    )


def create_jira_integration(config: Dict[str, Any]) -> JiraIntegration:
    """Create JIRA integration from config."""
    return JiraIntegration(
        server=config.get('server'),
        username=config.get('username'),
        api_token=config.get('api_token')
    )


def load_integrations_from_config(config_path: str = "config/integrations.json") -> Dict[str, Any]:
    """Load all integrations from configuration file."""
    import json
    import os
    
    integrations = {}
    
    if not os.path.exists(config_path):
        logger.warning(f"Integration config not found: {config_path}")
        return integrations
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if config.get('github', {}).get('enabled'):
            integrations['github'] = create_github_integration(config['github'])
        
        if config.get('gitlab', {}).get('enabled'):
            integrations['gitlab'] = create_gitlab_integration(config['gitlab'])
        
        if config.get('slack', {}).get('enabled'):
            integrations['slack'] = create_slack_notifier(config['slack'])
        
        if config.get('jira', {}).get('enabled'):
            integrations['jira'] = create_jira_integration(config['jira'])
        
        logger.info(f"Loaded {len(integrations)} integrations")
        
    except Exception as e:
        logger.error(f"Failed to load integrations: {e}")
    
    return integrations


__all__ = [
    # Integration classes
    "GitHubIntegration",
    "GitLabIntegration",
    "JenkinsIntegration",
    "SlackNotifier",
    "JiraIntegration",
    
    # Configuration
    "IntegrationConfig",
    "IntegrationStatus",
    
    # Factory functions
    "create_github_integration",
    "create_gitlab_integration",
    "create_slack_notifier",
    "create_jira_integration",
    "load_integrations_from_config",
]

__version__ = "2.0.0"
