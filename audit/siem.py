"""
SIEM Integration Module

Connects audit logs to external SIEM systems like Splunk, ELK Stack,
QRadar, and custom HTTP endpoints.
"""

import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
from dataclasses import dataclass

from .logger import AuditLogEntry


@dataclass
class SIEMConfig:
    """SIEM configuration"""
    url: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    index: str = "zen_audit"
    source_type: str = "_json"
    batch_size: int = 100
    flush_interval: int = 60
    timeout: int = 30
    ssl_verify: bool = True
    custom_headers: Optional[Dict[str, str]] = None


class SIEMBackend(ABC):
    """Abstract base class for SIEM backends"""

    def __init__(self, config: SIEMConfig):
        self.config = config

    @abstractmethod
    async def send(self, entries: List[AuditLogEntry]) -> bool:
        """Send entries to SIEM"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check SIEM connectivity"""
        pass

    def format_entry(self, entry: AuditLogEntry) -> Dict[str, Any]:
        """Format entry for SIEM (override in subclass)"""
        return {
            "timestamp": entry.timestamp.isoformat(),
            "id": entry.id,
            "level": entry.level,
            "category": entry.category,
            "event_type": entry.event_type,
            "message": entry.message,
            "user_id": entry.user_id,
            "ip_address": entry.ip_address,
            "resource_id": entry.resource_id,
            "hash": entry.hash,
        }


class SplunkBackend(SIEMBackend):
    """Splunk HTTP Event Collector integration"""

    def __init__(self, config: SIEMConfig):
        super().__init__(config)
        self.hec_url = f"{config.url}/services/collector/event"

    async def send(self, entries: List[AuditLogEntry]) -> bool:
        """Send entries to Splunk HEC"""
        if not entries:
            return True

        events = []
        for entry in entries:
            event = {
                "time": entry.timestamp.timestamp(),
                "source": "zen-ai-pentest",
                "sourcetype": self.config.source_type,
                "index": self.config.index,
                "event": self.format_entry(entry)
            }
            events.append(json.dumps(event))

        data = "\n".join(events)

        headers = {
            "Authorization": f"Splunk {self.config.api_key}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.hec_url,
                    data=data,
                    headers=headers,
                    ssl=self.config.ssl_verify,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("code") == 0
                    else:
                        print(f"Splunk error: {response.status}")
                        return False
            except Exception as e:
                print(f"Splunk send error: {e}")
                return False

    async def health_check(self) -> bool:
        """Check Splunk HEC health"""
        headers = {"Authorization": f"Splunk {self.config.api_key}"}
        health_url = f"{self.config.url}/services/collector/health"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    health_url,
                    headers=headers,
                    ssl=self.config.ssl_verify,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    return response.status == 200
            except Exception:
                return False


class ElasticsearchBackend(SIEMBackend):
    """Elasticsearch/ELK Stack integration"""

    async def send(self, entries: List[AuditLogEntry]) -> bool:
        """Send entries to Elasticsearch via Bulk API"""
        if not entries:
            return True

        # Build bulk request
        bulk_data = []
        for entry in entries:
            # Action line
            bulk_data.append(json.dumps({
                "index": {
                    "_index": f"{self.config.index}-{entry.timestamp.strftime('%Y.%m.%d')}",
                    "_id": entry.id
                }
            }))
            # Document line
            bulk_data.append(json.dumps(self.format_entry(entry)))

        data = "\n".join(bulk_data) + "\n"

        headers = {"Content-Type": "application/x-ndjson"}
        if self.config.custom_headers:
            headers.update(self.config.custom_headers)

        auth = None
        if self.config.username and self.config.password:
            auth = aiohttp.BasicAuth(self.config.username, self.config.password)
        elif self.config.api_key:
            headers["Authorization"] = f"ApiKey {self.config.api_key}"

        bulk_url = f"{self.config.url}/_bulk"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    bulk_url,
                    data=data,
                    headers=headers,
                    auth=auth,
                    ssl=self.config.ssl_verify,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        errors = result.get("errors", False)
                        if errors:
                            items = result.get("items", [])
                            error_count = sum(1 for item in items if "error" in item.get("index", {}))
                            print(f"Elasticsearch bulk errors: {error_count}")
                        return not errors
                    else:
                        print(f"Elasticsearch error: {response.status}")
                        return False
            except Exception as e:
                print(f"Elasticsearch send error: {e}")
                return False

    async def health_check(self) -> bool:
        """Check Elasticsearch cluster health"""
        async with aiohttp.ClientSession() as session:
            try:
                auth = None
                if self.config.username and self.config.password:
                    auth = aiohttp.BasicAuth(self.config.username, self.config.password)

                async with session.get(
                    f"{self.config.url}/_cluster/health",
                    auth=auth,
                    ssl=self.config.ssl_verify,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("status") in ["green", "yellow"]
                    return False
            except Exception:
                return False


class QRadarBackend(SIEMBackend):
    """IBM QRadar integration via HTTPS Receiver"""

    async def send(self, entries: List[AuditLogEntry]) -> bool:
        """Send entries to QRadar"""
        # QRadar uses LEEF (Log Event Extended Format) or JSON
        leef_events = []

        for entry in entries:
            # LEEF format: LEEF:2.0|vendor|product|version|event_id|attributes
            leef = (
                f"LEEF:2.0|ZenAI|PenTest|1.0|{entry.event_type}|"
                f"devTime={int(entry.timestamp.timestamp() * 1000)}\t"
                f"sev={self._level_to_severity(entry.level)}\t"
                f"usrName={entry.user_id or 'unknown'}\t"
                f"src={entry.ip_address or 'unknown'}\t"
                f"msg={entry.message}"
            )
            leef_events.append(leef)

        data = "\n".join(leef_events)

        headers = {"Content-Type": "text/plain"}
        if self.config.api_key:
            headers["SEC"] = self.config.api_key

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.config.url,
                    data=data,
                    headers=headers,
                    ssl=self.config.ssl_verify,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    return response.status == 200
            except Exception as e:
                print(f"QRadar send error: {e}")
                return False

    def _level_to_severity(self, level: str) -> int:
        """Convert log level to QRadar severity (0-10)"""
        mapping = {
            "debug": 1,
            "info": 2,
            "notice": 3,
            "warning": 5,
            "error": 7,
            "critical": 9,
            "alert": 10,
            "emergency": 10
        }
        return mapping.get(level, 5)

    async def health_check(self) -> bool:
        """Check QRadar connection"""
        # QRadar doesn't have a simple health endpoint
        # Try to send a test event
        test_entry = AuditLogEntry(
            id="health-check",
            timestamp=datetime.utcnow(),
            level="info",
            category="system",
            event_type="health_check",
            message="Health check"
        )
        return await self.send([test_entry])


class GenericHTTPBackend(SIEMBackend):
    """Generic HTTP endpoint integration"""

    async def send(self, entries: List[AuditLogEntry]) -> bool:
        """Send entries to generic HTTP endpoint"""
        if not entries:
            return True

        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "source": "zen-ai-pentest",
            "events": [self.format_entry(e) for e in entries]
        }

        headers = {"Content-Type": "application/json"}
        if self.config.custom_headers:
            headers.update(self.config.custom_headers)
        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.config.url,
                    json=data,
                    headers=headers,
                    ssl=self.config.ssl_verify,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    return response.status in [200, 201, 202]
            except Exception as e:
                print(f"HTTP send error: {e}")
                return False

    async def health_check(self) -> bool:
        """Check HTTP endpoint health"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    self.config.url,
                    ssl=self.config.ssl_verify,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    return response.status < 500
            except Exception:
                return False


class SIEMIntegration:
    """
    Main SIEM integration manager

    Supports multiple backends and handles failover.
    """

    BACKENDS = {
        "splunk": SplunkBackend,
        "elasticsearch": ElasticsearchBackend,
        "elk": ElasticsearchBackend,
        "qradar": QRadarBackend,
        "http": GenericHTTPBackend,
    }

    def __init__(self, configs: List[SIEMConfig]):
        self.backends: List[SIEMBackend] = []

        for config in configs:
            backend_class = self._detect_backend(config)
            if backend_class:
                self.backends.append(backend_class(config))

    def _detect_backend(self, config: SIEMConfig) -> Optional[type]:
        """Auto-detect backend type from URL"""
        url_lower = config.url.lower()

        if "splunk" in url_lower or ":8088" in url_lower:
            return SplunkBackend
        elif "elasticsearch" in url_lower or ":9200" in url_lower:
            return ElasticsearchBackend
        elif "qradar" in url_lower:
            return QRadarBackend
        else:
            return GenericHTTPBackend

    async def send(self, entries: List[AuditLogEntry]) -> Dict[str, bool]:
        """Send entries to all configured SIEMs"""
        results = {}

        for backend in self.backends:
            backend_name = type(backend).__name__
            try:
                success = await backend.send(entries)
                results[backend_name] = success
            except Exception as e:
                print(f"SIEM send error ({backend_name}): {e}")
                results[backend_name] = False

        return results

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all SIEM backends"""
        results = {}

        for backend in self.backends:
            backend_name = type(backend).__name__
            try:
                healthy = await backend.health_check()
                results[backend_name] = healthy
            except Exception:
                results[backend_name] = False

        return results
