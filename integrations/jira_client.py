"""
JIRA Integration für Zen-AI-Pentest
"""

import logging
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class JiraClient:
    """Client für JIRA Integration"""

    def __init__(self, base_url: str, username: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.auth = (username, api_token)
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}

    def test_connection(self) -> bool:
        """Testet die Verbindung zu JIRA"""
        try:
            response = requests.get(f"{self.base_url}/rest/api/2/myself", auth=self.auth, headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"JIRA connection test failed: {e}")
            return False

    def get_projects(self) -> List[Dict]:
        """Holt alle verfügbaren Projekte"""
        try:
            response = requests.get(f"{self.base_url}/rest/api/2/project", auth=self.auth, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Failed to get JIRA projects: {e}")
            return []

    def get_issue_types(self, project_key: str) -> List[Dict]:
        """Holt Issue-Typen für ein Projekt"""
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/2/issue/createmeta",
                params={"projectKeys": project_key, "expand": "projects.issuetypes"},
                auth=self.auth,
                headers=self.headers,
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                projects = data.get("projects", [])
                if projects:
                    return projects[0].get("issuetypes", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get issue types: {e}")
            return []

    def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Bug",
        priority: str = "High",
        labels: List[str] = None,
    ) -> Optional[Dict]:
        """Erstellt ein JIRA Issue"""
        try:
            payload = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": description,
                    "issuetype": {"name": issue_type},
                    "priority": {"name": priority},
                }
            }

            if labels:
                payload["fields"]["labels"] = labels

            response = requests.post(
                f"{self.base_url}/rest/api/2/issue", auth=self.auth, headers=self.headers, json=payload, timeout=10
            )

            if response.status_code == 201:
                return response.json()
            else:
                logger.error(f"JIRA create issue failed: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Failed to create JIRA issue: {e}")
            return None

    def create_finding_ticket(self, project_key: str, finding: Dict, scan_url: str = None) -> Optional[Dict]:
        """Erstellt ein Ticket aus einem Finding"""
        severity = finding.get("severity", "Medium")
        priority_map = {"Critical": "Highest", "High": "High", "Medium": "Medium", "Low": "Low", "Info": "Lowest"}

        summary = f"[{severity}] {finding.get('title', 'Security Finding')}"

        description = f"""h2. Security Finding Detected

*Severity:* {severity}
*Target:* {finding.get("target", "N/A")}
*Tool:* {finding.get("tool", "Unknown")}

h3. Description

{finding.get("description", "No description available")}

h3. Remediation

{finding.get("remediation", "No remediation steps provided")}

"""
        if scan_url:
            description += f"\n*Scan Details:* {scan_url}"

        return self.create_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            issue_type="Bug",
            priority=priority_map.get(severity, "Medium"),
            labels=["security", "pentest", "zen-ai"],
        )


# In-memory config storage (in production: use database)
JIRA_CONFIG = {"base_url": None, "username": None, "api_token": None, "enabled": False}


def get_jira_client() -> Optional[JiraClient]:
    """Gibt JIRA Client wenn konfiguriert"""
    if not JIRA_CONFIG["enabled"] or not JIRA_CONFIG["base_url"]:
        return None

    return JiraClient(base_url=JIRA_CONFIG["base_url"], username=JIRA_CONFIG["username"], api_token=JIRA_CONFIG["api_token"])
