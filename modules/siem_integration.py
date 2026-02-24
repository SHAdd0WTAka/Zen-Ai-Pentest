"""
SIEM Integration Module for Zen AI Pentest
Supports: Splunk, Elastic, Azure Sentinel, IBM QRadar
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)


@dataclass
class SIEMConfig:
    """SIEM connection configuration"""

    name: str
    type: str  # splunk, elastic, sentinel, qradar
    url: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    index: Optional[str] = None
    verify_ssl: bool = True
    timeout: int = 30


@dataclass
class SecurityEvent:
    """Normalized security event for SIEM ingestion"""

    timestamp: datetime
    severity: str  # critical, high, medium, low, info
    event_type: str
    source: str
    target: str
    description: str
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    raw_data: Optional[Dict] = None


class BaseSIEMConnector(ABC):
    """Base class for SIEM connectors"""

    def __init__(self, config: SIEMConfig):
        self.config = config
        self.session = requests.Session()
        self.session.verify = config.verify_ssl
        self.session.timeout = config.timeout

    @abstractmethod
    def connect(self) -> bool:
        """Test connection to SIEM"""
        pass

    @abstractmethod
    def send_event(self, event: SecurityEvent) -> bool:
        """Send security event to SIEM"""
        pass

    @abstractmethod
    def send_events_batch(self, events: List[SecurityEvent]) -> bool:
        """Send multiple events to SIEM"""
        pass

    @abstractmethod
    def query_threat_intel(self, indicator: str) -> Optional[Dict]:
        """Query SIEM for threat intelligence"""
        pass


class SplunkConnector(BaseSIEMConnector):
    """Splunk HTTP Event Collector (HEC) connector"""

    def connect(self) -> bool:
        try:
            url = urljoin(self.config.url, "/services/collector/health")
            headers = {"Authorization": f"Splunk {self.config.api_key}"}
            response = self.session.get(url, headers=headers)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Splunk connection failed: {e}")
            return False

    def send_event(self, event: SecurityEvent) -> bool:
        try:
            url = urljoin(self.config.url, "/services/collector/event")
            headers = {
                "Authorization": f"Splunk {self.config.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "time": event.timestamp.timestamp(),
                "sourcetype": "zen_ai_pentest",
                "index": self.config.index or "security",
                "event": {
                    "severity": event.severity,
                    "event_type": event.event_type,
                    "source": event.source,
                    "target": event.target,
                    "description": event.description,
                    "cve_id": event.cve_id,
                    "cvss_score": event.cvss_score,
                    **(event.raw_data or {}),
                },
            }

            response = self.session.post(url, headers=headers, json=payload)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send event to Splunk: {e}")
            return False

    def send_events_batch(self, events: List[SecurityEvent]) -> bool:
        """Send multiple events to Splunk"""
        try:
            url = urljoin(self.config.url, "/services/collector/event")
            headers = {
                "Authorization": f"Splunk {self.config.api_key}",
                "Content-Type": "application/json",
            }

            batch_data = ""
            for event in events:
                payload = {
                    "time": event.timestamp.timestamp(),
                    "sourcetype": "zen_ai_pentest",
                    "index": self.config.index or "security",
                    "event": {
                        "severity": event.severity,
                        "event_type": event.event_type,
                        "source": event.source,
                        "target": event.target,
                        "description": event.description,
                        "cve_id": event.cve_id,
                        "cvss_score": event.cvss_score,
                    },
                }
                batch_data += json.dumps(payload) + "\n"

            response = self.session.post(url, headers=headers, data=batch_data)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send batch to Splunk: {e}")
            return False

    def query_threat_intel(self, indicator: str) -> Optional[Dict]:
        """Query Splunk for threat intelligence"""
        try:
            search_query = (
                f'search index=threat_intel indicator="{indicator}" | head 1'
            )
            url = urljoin(self.config.url, "/services/search/jobs")
            headers = {"Authorization": f"Splunk {self.config.api_key}"}

            data = {"search": search_query, "output_mode": "json"}
            response = self.session.post(url, headers=headers, data=data)

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to query Splunk: {e}")
            return None


class ElasticConnector(BaseSIEMConnector):
    """Elastic/Elasticsearch connector"""

    def connect(self) -> bool:
        try:
            url = urljoin(self.config.url, "_cluster/health")
            headers = {"Authorization": f"ApiKey {self.config.api_key}"}
            response = self.session.get(url, headers=headers)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Elastic connection failed: {e}")
            return False

    def send_event(self, event: SecurityEvent) -> bool:
        try:
            index = self.config.index or "zen-ai-security"
            url = urljoin(self.config.url, f"{index}/_doc")
            headers = {"Authorization": f"ApiKey {self.config.api_key}"}

            document = {
                "@timestamp": event.timestamp.isoformat(),
                "severity": event.severity,
                "event.type": event.event_type,
                "source.ip": event.source,
                "destination.ip": event.target,
                "message": event.description,
                "vulnerability.cve": event.cve_id,
                "vulnerability.cvss": event.cvss_score,
            }

            response = self.session.post(url, headers=headers, json=document)
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Failed to send event to Elastic: {e}")
            return False

    def send_events_batch(self, events: List[SecurityEvent]) -> bool:
        """Send bulk events to Elastic"""
        try:
            index = self.config.index or "zen-ai-security"
            url = urljoin(self.config.url, "_bulk")
            headers = {"Authorization": f"ApiKey {self.config.api_key}"}

            bulk_data = ""
            for event in events:
                action = json.dumps({"index": {"_index": index}})
                document = json.dumps(
                    {
                        "@timestamp": event.timestamp.isoformat(),
                        "severity": event.severity,
                        "event.type": event.event_type,
                        "source.ip": event.source,
                        "destination.ip": event.target,
                        "message": event.description,
                        "vulnerability.cve": event.cve_id,
                        "vulnerability.cvss": event.cvss_score,
                    }
                )
                bulk_data += action + "\n" + document + "\n"

            response = self.session.post(
                url,
                headers={**headers, "Content-Type": "application/x-ndjson"},
                data=bulk_data,
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send bulk to Elastic: {e}")
            return False

    def query_threat_intel(self, indicator: str) -> Optional[Dict]:
        """Query Elastic for threat intelligence"""
        try:
            index = "threat-intel"
            url = urljoin(self.config.url, f"{index}/_search")
            headers = {"Authorization": f"ApiKey {self.config.api_key}"}

            query = {"query": {"match": {"indicator": indicator}}}

            response = self.session.post(url, headers=headers, json=query)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to query Elastic: {e}")
            return None


class AzureSentinelConnector(BaseSIEMConnector):
    """Azure Sentinel/Log Analytics connector"""

    def __init__(self, config: SIEMConfig):
        super().__init__(config)
        self.workspace_id = config.username  # Workspace ID
        self.shared_key = config.api_key  # Shared Key

    def connect(self) -> bool:
        try:
            # Test connection by querying Log Analytics
            url = f"https://api.loganalytics.io/v1/workspaces/{self.workspace_id}/query"
            headers = self._build_auth_header()

            response = self.session.get(url, headers=headers)
            return response.status_code in [
                200,
                401,
            ]  # 401 means auth works but query invalid
        except Exception as e:
            logger.error(f"Sentinel connection failed: {e}")
            return False

    def _build_auth_header(self) -> Dict[str, str]:
        """Build Azure API authentication header"""
        import base64
        import hashlib
        import hmac

        date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        string_to_hash = (
            f"POST\n{len('')}\napplication/json\nx-ms-date:{date}\n/api/logs"
        )
        decoded_key = base64.b64decode(self.shared_key)
        encoded_hash = base64.b64encode(
            hmac.new(
                decoded_key, string_to_hash.encode(), hashlib.sha256
            ).digest()
        ).decode()

        return {
            "Content-Type": "application/json",
            "Authorization": f"SharedKey {self.workspace_id}:{encoded_hash}",
            "x-ms-date": date,
            "Log-Type": "ZenAIPentest",
        }

    def send_event(self, event: SecurityEvent) -> bool:
        try:
            url = f"https://{self.workspace_id}.ods.opinsights.azure.com/api/logs?api-version=2016-04-01"
            headers = self._build_auth_header()

            log_data = [
                {
                    "TimeGenerated": event.timestamp.isoformat(),
                    "Severity": event.severity,
                    "EventType": event.event_type,
                    "Source": event.source,
                    "Target": event.target,
                    "Description": event.description,
                    "CVE": event.cve_id,
                    "CVSS": event.cvss_score,
                }
            ]

            response = self.session.post(url, headers=headers, json=log_data)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send event to Sentinel: {e}")
            return False

    def send_events_batch(self, events: List[SecurityEvent]) -> bool:
        """Send batch to Azure Log Analytics"""
        try:
            url = f"https://{self.workspace_id}.ods.opinsights.azure.com/api/logs?api-version=2016-04-01"
            headers = self._build_auth_header()

            log_data = []
            for event in events:
                log_data.append(
                    {
                        "TimeGenerated": event.timestamp.isoformat(),
                        "Severity": event.severity,
                        "EventType": event.event_type,
                        "Source": event.source,
                        "Target": event.target,
                        "Description": event.description,
                        "CVE": event.cve_id,
                        "CVSS": event.cvss_score,
                    }
                )

            response = self.session.post(url, headers=headers, json=log_data)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send batch to Sentinel: {e}")
            return False

    def query_threat_intel(self, indicator: str) -> Optional[Dict]:
        """Query Sentinel Threat Intelligence"""
        try:
            url = f"https://api.loganalytics.io/v1/workspaces/{self.workspace_id}/query"
            headers = self._build_auth_header()

            query = f"ThreatIntelligenceIndicator | where Indicator == '{indicator}' | limit 1"

            response = self.session.post(
                url, headers=headers, json={"query": query}
            )

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to query Sentinel: {e}")
            return None


class QRadarConnector(BaseSIEMConnector):
    """IBM QRadar connector"""

    def connect(self) -> bool:
        try:
            url = urljoin(self.config.url, "/api/system/about")
            headers = self._build_auth_header()
            response = self.session.get(url, headers=headers)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"QRadar connection failed: {e}")
            return False

    def _build_auth_header(self) -> Dict[str, str]:
        """Build QRadar authentication header"""
        import base64

        if self.config.api_key:
            return {"SEC": self.config.api_key}
        elif self.config.username and self.config.password:
            credentials = base64.b64encode(
                f"{self.config.username}:{self.config.password}".encode()
            ).decode()
            return {"Authorization": f"Basic {credentials}"}
        return {}

    def send_event(self, event: SecurityEvent) -> bool:
        try:
            url = urljoin(self.config.url, "/api/asset_model/assets")
            headers = self._build_auth_header()

            payload = {
                "event": {
                    "severity": event.severity,
                    "event_type": event.event_type,
                    "source": event.source,
                    "target": event.target,
                    "description": event.description,
                    "cve": event.cve_id,
                }
            }

            response = self.session.post(url, headers=headers, json=payload)
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Failed to send event to QRadar: {e}")
            return False

    def send_events_batch(self, events: List[SecurityEvent]) -> bool:
        """QRadar batch event submission"""
        for event in events:
            if not self.send_event(event):
                return False
        return True

    def query_threat_intel(self, indicator: str) -> Optional[Dict]:
        """Query QRadar reference sets"""
        try:
            url = urljoin(
                self.config.url, f"/api/reference_data/sets/{indicator}"
            )
            headers = self._build_auth_header()

            response = self.session.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to query QRadar: {e}")
            return None


class SIEMIntegrationManager:
    """Manager for multiple SIEM integrations"""

    def __init__(self):
        self.connectors: Dict[str, BaseSIEMConnector] = {}
        self._connector_classes = {
            "splunk": SplunkConnector,
            "elastic": ElasticConnector,
            "sentinel": AzureSentinelConnector,
            "qradar": QRadarConnector,
        }

    def add_siem(self, config: SIEMConfig) -> bool:
        """Add SIEM integration"""
        connector_class = self._connector_classes.get(config.type)
        if not connector_class:
            logger.error(f"Unknown SIEM type: {config.type}")
            return False

        connector = connector_class(config)
        if connector.connect():
            self.connectors[config.name] = connector
            logger.info(f"Connected to {config.name} ({config.type})")
            return True
        else:
            logger.error(f"Failed to connect to {config.name}")
            return False

    def send_to_all(self, event: SecurityEvent) -> Dict[str, bool]:
        """Send event to all configured SIEMs"""
        results = {}
        for name, connector in self.connectors.items():
            results[name] = connector.send_event(event)
        return results

    def send_batch_to_all(
        self, events: List[SecurityEvent]
    ) -> Dict[str, bool]:
        """Send batch of events to all SIEMs"""
        results = {}
        for name, connector in self.connectors.items():
            results[name] = connector.send_events_batch(events)
        return results

    def get_status(self) -> Dict[str, bool]:
        """Get connection status of all SIEMs"""
        return {
            name: connector.connect()
            for name, connector in self.connectors.items()
        }


# Factory function
def create_siem_connector(config: SIEMConfig) -> Optional[BaseSIEMConnector]:
    """Factory function to create appropriate SIEM connector"""
    connectors = {
        "splunk": SplunkConnector,
        "elastic": ElasticConnector,
        "sentinel": AzureSentinelConnector,
        "qradar": QRadarConnector,
    }

    connector_class = connectors.get(config.type.lower())
    if connector_class:
        return connector_class(config)

    logger.error(f"Unknown SIEM type: {config.type}")
    return None
