"""
SIEM Integration API v1.0
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.siem_integration import (
    SecurityEvent,
    SIEMConfig,
    SIEMIntegrationManager,
)

router = APIRouter()

# Global SIEM manager instance
siem_manager = SIEMIntegrationManager()


class SIEMConnectionRequest(BaseModel):
    """SIEM connection configuration"""

    name: str
    type: str  # splunk, elastic, sentinel, qradar
    url: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    index: Optional[str] = None
    verify_ssl: bool = True


class SecurityEventRequest(BaseModel):
    """Security event for SIEM ingestion"""

    severity: str
    event_type: str
    source: str
    target: str
    description: str
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    timestamp: Optional[datetime] = None


class SIEMStatusResponse(BaseModel):
    """SIEM connection status"""

    name: str
    type: str
    connected: bool
    url: str


@router.post("/connect", response_model=Dict[str, Any])
async def connect_siem(config: SIEMConnectionRequest):
    """
    Connect to a SIEM platform

    Supported types:
    - splunk: Splunk HTTP Event Collector
    - elastic: Elasticsearch/Elastic SIEM
    - sentinel: Azure Sentinel
    - qradar: IBM QRadar
    """
    siem_config = SIEMConfig(
        name=config.name,
        type=config.type,
        url=config.url,
        api_key=config.api_key,
        username=config.username,
        password=config.password,
        index=config.index,
        verify_ssl=config.verify_ssl,
    )

    success = siem_manager.add_siem(siem_config)

    if success:
        return {
            "success": True,
            "message": f"Connected to {config.name} ({config.type})",
            "timestamp": datetime.utcnow().isoformat(),
        }
    else:
        raise HTTPException(
            status_code=400, detail=f"Failed to connect to {config.name}"
        )


@router.get("/status", response_model=List[SIEMStatusResponse])
async def get_siem_status():
    """Get status of all configured SIEM connections"""
    status = siem_manager.get_status()

    results = []
    for name, connected in status.items():
        connector = siem_manager.connectors.get(name)
        if connector:
            results.append(
                SIEMStatusResponse(
                    name=name,
                    type=connector.config.type,
                    connected=connected,
                    url=connector.config.url,
                )
            )

    return results


@router.post("/events", response_model=Dict[str, Any])
async def send_security_event(event: SecurityEventRequest):
    """
    Send security event to all configured SIEMs

    Severity levels: critical, high, medium, low, info
    """
    security_event = SecurityEvent(
        timestamp=event.timestamp or datetime.utcnow(),
        severity=event.severity,
        event_type=event.event_type,
        source=event.source,
        target=event.target,
        description=event.description,
        cve_id=event.cve_id,
        cvss_score=event.cvss_score,
    )

    results = siem_manager.send_to_all(security_event)

    return {
        "success": any(results.values()),
        "results": results,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/events/batch", response_model=Dict[str, Any])
async def send_security_events_batch(events: List[SecurityEventRequest]):
    """Send multiple security events to all SIEMs"""
    security_events = [
        SecurityEvent(
            timestamp=e.timestamp or datetime.utcnow(),
            severity=e.severity,
            event_type=e.event_type,
            source=e.source,
            target=e.target,
            description=e.description,
            cve_id=e.cve_id,
            cvss_score=e.cvss_score,
        )
        for e in events
    ]

    results = siem_manager.send_batch_to_all(security_events)

    return {
        "success": any(results.values()),
        "sent_count": len(events),
        "results": results,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/query/{siem_name}")
async def query_threat_intel(siem_name: str, indicator: str):
    """Query threat intelligence from a specific SIEM"""
    connector = siem_manager.connectors.get(siem_name)

    if not connector:
        raise HTTPException(
            status_code=404, detail=f"SIEM '{siem_name}' not found"
        )

    result = connector.query_threat_intel(indicator)

    return {
        "siem": siem_name,
        "indicator": indicator,
        "found": result is not None,
        "data": result,
    }


@router.get("/supported")
async def get_supported_siems():
    """List supported SIEM platforms"""
    return {
        "supported_siems": [
            {
                "type": "splunk",
                "name": "Splunk HTTP Event Collector",
                "auth_methods": ["api_key"],
                "features": ["events", "batch", "threat_intel"],
            },
            {
                "type": "elastic",
                "name": "Elasticsearch/Elastic SIEM",
                "auth_methods": ["api_key"],
                "features": ["events", "batch", "threat_intel"],
            },
            {
                "type": "sentinel",
                "name": "Azure Sentinel",
                "auth_methods": ["workspace_id", "shared_key"],
                "features": ["events", "batch", "threat_intel"],
            },
            {
                "type": "qradar",
                "name": "IBM QRadar",
                "auth_methods": ["api_key", "username/password"],
                "features": ["events", "batch", "threat_intel"],
            },
        ]
    }
