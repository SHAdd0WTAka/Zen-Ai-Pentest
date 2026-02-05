"""
Dashboard API Endpoints - Issue #24

Provides dashboard statistics, real-time updates, and monitoring endpoints.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.auth import verify_token
from api.websocket import ConnectionManager
from database.models import Scan, Finding, Report, get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Dashboard WebSocket manager
dashboard_ws_manager = ConnectionManager()


# ============================================================================
# Pydantic Models
# ============================================================================

class StatsResponse(BaseModel):
    """Dashboard statistics response"""
    total_scans: int
    active_scans: int
    completed_scans: int
    failed_scans: int
    cancelled_scans: int
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    info_findings: int
    severity_distribution: List[Dict[str, Any]]
    scans_by_status: Dict[str, int]
    recent_trends: List[Dict[str, Any]]


class ActiveScanInfo(BaseModel):
    """Active scan information"""
    id: int
    name: str
    target: str
    scan_type: str
    status: str
    progress: int
    started_at: Optional[str]
    duration_seconds: Optional[int]
    findings_count: int


class RecentFinding(BaseModel):
    """Recent finding information"""
    id: int
    title: str
    severity: str
    target: str
    tool: Optional[str]
    scan_id: int
    scan_name: str
    created_at: str
    cvss_score: Optional[float]


class DashboardActivity(BaseModel):
    """Dashboard activity item"""
    id: str
    type: str  # scan_started, scan_completed, finding_found, report_generated
    title: str
    description: str
    timestamp: str
    severity: Optional[str] = None
    scan_id: Optional[int] = None


# ============================================================================
# Helper Functions
# ============================================================================

def get_severity_color(severity: str) -> str:
    """Get color code for severity level"""
    colors = {
        'critical': '#ef4444',
        'high': '#f97316',
        'medium': '#eab308',
        'low': '#22c55e',
        'info': '#3b82f6'
    }
    return colors.get(severity.lower(), '#6b7280')


def get_severity_order(severity: str) -> int:
    """Get sort order for severity (highest first)"""
    order = {
        'critical': 0,
        'high': 1,
        'medium': 2,
        'low': 3,
        'info': 4
    }
    return order.get(severity.lower(), 5)


async def broadcast_dashboard_update(message: Dict[str, Any]):
    """Broadcast update to all dashboard WebSocket clients"""
    await dashboard_ws_manager.broadcast_global(message)


# ============================================================================
# REST Endpoints
# ============================================================================

@router.get("/stats", response_model=StatsResponse)
async def get_dashboard_stats(
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard statistics.
    
    Returns counts of scans by status, findings by severity,
    and trend data for the past 30 days.
    """
    try:
        # Scan counts
        total_scans = db.query(Scan).count()
        active_scans = db.query(Scan).filter(Scan.status == "running").count()
        completed_scans = db.query(Scan).filter(Scan.status == "completed").count()
        failed_scans = db.query(Scan).filter(Scan.status == "failed").count()
        cancelled_scans = db.query(Scan).filter(Scan.status == "cancelled").count()
        
        # Findings counts
        total_findings = db.query(Finding).count()
        
        severity_counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }
        
        results = db.query(Finding.severity, func.count(Finding.id)).group_by(Finding.severity).all()
        for sev, count in results:
            if sev in severity_counts:
                severity_counts[sev] = count
        
        # Build severity distribution for charts
        severity_distribution = [
            {"name": "Critical", "value": severity_counts['critical'], "color": "#ef4444"},
            {"name": "High", "value": severity_counts['high'], "color": "#f97316"},
            {"name": "Medium", "value": severity_counts['medium'], "color": "#eab308"},
            {"name": "Low", "value": severity_counts['low'], "color": "#22c55e"},
            {"name": "Info", "value": severity_counts['info'], "color": "#3b82f6"}
        ]
        
        # Scans by status
        scans_by_status = {
            "pending": db.query(Scan).filter(Scan.status == "pending").count(),
            "running": active_scans,
            "completed": completed_scans,
            "failed": failed_scans,
            "cancelled": cancelled_scans
        }
        
        # Calculate trends (scans per day for last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        trends = []
        
        for i in range(30):
            day_start = thirty_days_ago + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            day_scans = db.query(Scan).filter(
                Scan.created_at >= day_start,
                Scan.created_at < day_end
            ).count()
            
            day_findings = db.query(Finding).join(Scan).filter(
                Scan.created_at >= day_start,
                Scan.created_at < day_end
            ).count()
            
            trends.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "scans": day_scans,
                "findings": day_findings
            })
        
        return StatsResponse(
            total_scans=total_scans,
            active_scans=active_scans,
            completed_scans=completed_scans,
            failed_scans=failed_scans,
            cancelled_scans=cancelled_scans,
            total_findings=total_findings,
            critical_findings=severity_counts['critical'],
            high_findings=severity_counts['high'],
            medium_findings=severity_counts['medium'],
            low_findings=severity_counts['low'],
            info_findings=severity_counts['info'],
            severity_distribution=severity_distribution,
            scans_by_status=scans_by_status,
            recent_trends=trends
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/active-scans", response_model=List[ActiveScanInfo])
async def get_active_scans(
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get all currently running/active scans.
    
    Returns a list of scans with status 'running' or 'pending'
    including progress information and duration.
    """
    try:
        active = db.query(Scan).filter(
            Scan.status.in_(["running", "pending"])
        ).order_by(Scan.started_at.desc()).all()
        
        result = []
        for scan in active:
            duration = None
            if scan.started_at:
                duration = int((datetime.utcnow() - scan.started_at).total_seconds())
            
            # Get findings count for this scan
            findings_count = db.query(Finding).filter(Finding.scan_id == scan.id).count()
            
            # Calculate progress (simplified - could be enhanced with more granular tracking)
            progress = 0
            if scan.status == "running" and scan.started_at:
                # Estimate progress based on typical scan duration (10 minutes)
                elapsed = (datetime.utcnow() - scan.started_at).total_seconds()
                progress = min(int((elapsed / 600) * 100), 99)  # Cap at 99% until complete
            elif scan.status == "completed":
                progress = 100
            
            result.append(ActiveScanInfo(
                id=scan.id,
                name=scan.name,
                target=scan.target,
                scan_type=scan.scan_type,
                status=scan.status,
                progress=progress,
                started_at=scan.started_at.isoformat() if scan.started_at else None,
                duration_seconds=duration,
                findings_count=findings_count
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting active scans: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active scans: {str(e)}")


@router.get("/recent-findings", response_model=List[RecentFinding])
async def get_recent_findings(
    limit: int = 20,
    severity: Optional[str] = None,
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get recent findings across all scans.
    
    - **limit**: Number of findings to return (default: 20, max: 100)
    - **severity**: Filter by severity level (optional)
    
    Returns findings sorted by creation time (newest first).
    """
    try:
        query = db.query(Finding).join(Scan).order_by(Finding.created_at.desc())
        
        if severity:
            query = query.filter(Finding.severity == severity.lower())
        
        findings = query.limit(min(limit, 100)).all()
        
        result = []
        for finding in findings:
            result.append(RecentFinding(
                id=finding.id,
                title=finding.title,
                severity=finding.severity,
                target=finding.target or "Unknown",
                tool=finding.tool,
                scan_id=finding.scan_id,
                scan_name=finding.scan.name if finding.scan else "Unknown",
                created_at=finding.created_at.isoformat(),
                cvss_score=finding.cvss_score
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting recent findings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recent findings: {str(e)}")


@router.get("/activities", response_model=List[DashboardActivity])
async def get_recent_activities(
    limit: int = 50,
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get recent dashboard activities.
    
    Combines scan events, findings discoveries, and report generations
    into a unified activity feed.
    
    - **limit**: Number of activities to return (default: 50, max: 100)
    """
    try:
        activities = []
        
        # Recent scans
        recent_scans = db.query(Scan).order_by(Scan.created_at.desc()).limit(limit // 3).all()
        for scan in recent_scans:
            if scan.status == "running":
                activities.append(DashboardActivity(
                    id=f"scan-start-{scan.id}",
                    type="scan_started",
                    title=f"Scan Started: {scan.name}",
                    description=f"Target: {scan.target}",
                    timestamp=scan.created_at.isoformat(),
                    scan_id=scan.id
                ))
            elif scan.status == "completed":
                activities.append(DashboardActivity(
                    id=f"scan-complete-{scan.id}",
                    type="scan_completed",
                    title=f"Scan Completed: {scan.name}",
                    description=f"Target: {scan.target}",
                    timestamp=scan.completed_at.isoformat() if scan.completed_at else scan.created_at.isoformat(),
                    scan_id=scan.id
                ))
        
        # Recent critical/high findings
        recent_findings = db.query(Finding).filter(
            Finding.severity.in_(["critical", "high"])
        ).order_by(Finding.created_at.desc()).limit(limit // 3).all()
        
        for finding in recent_findings:
            activities.append(DashboardActivity(
                id=f"finding-{finding.id}",
                type="finding_found",
                title=f"{finding.severity.upper()} Finding: {finding.title[:50]}",
                description=f"Found in {finding.scan.name if finding.scan else 'Unknown Scan'}",
                timestamp=finding.created_at.isoformat(),
                severity=finding.severity,
                scan_id=finding.scan_id
            ))
        
        # Recent reports
        recent_reports = db.query(Report).order_by(Report.created_at.desc()).limit(limit // 3).all()
        for report in recent_reports:
            activities.append(DashboardActivity(
                id=f"report-{report.id}",
                type="report_generated",
                title="Report Generated",
                description=f"Format: {report.format.upper()}",
                timestamp=report.created_at.isoformat(),
                scan_id=report.scan_id
            ))
        
        # Sort by timestamp descending
        activities.sort(key=lambda x: x.timestamp, reverse=True)
        
        return activities[:min(limit, 100)]
        
    except Exception as e:
        logger.error(f"Error getting activities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get activities: {str(e)}")


@router.get("/metrics/live")
async def get_live_metrics(
    user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get live system metrics for real-time monitoring.
    
    Returns current system load metrics and WebSocket connection stats.
    """
    try:
        # Get connection stats
        ws_stats = dashboard_ws_manager.get_stats()
        
        # Calculate scan rates (last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        scans_last_hour = db.query(Scan).filter(
            Scan.created_at >= one_hour_ago
        ).count()
        
        findings_last_hour = db.query(Finding).filter(
            Finding.created_at >= one_hour_ago
        ).count()
        
        return {
            "websocket_connections": ws_stats,
            "scans_per_hour": scans_last_hour,
            "findings_per_hour": findings_last_hour,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting live metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get live metrics: {str(e)}")


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@router.websocket("/ws")
async def dashboard_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.
    
    Clients will receive:
    - scan_started: When a new scan is initiated
    - scan_completed: When a scan finishes
    - finding_found: When a new finding is discovered
    - stats_update: Periodic statistics refresh
    
    Client messages:
    - { "action": "subscribe", "events": ["scans", "findings"] }
    - { "action": "ping" }
    - { "action": "unsubscribe" }
    """
    await dashboard_ws_manager.connect(websocket, "global")
    subscribed_events = {"all"}
    
    try:
        # Send initial connection acknowledgment
        await websocket.send_json({
            "type": "connected",
            "message": "Dashboard WebSocket connected",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                action = message.get("action")
                
                if action == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif action == "subscribe":
                    events = message.get("events", ["all"])
                    subscribed_events = set(events)
                    await websocket.send_json({
                        "type": "subscribed",
                        "events": list(subscribed_events)
                    })
                
                elif action == "unsubscribe":
                    subscribed_events = set()
                    await websocket.send_json({
                        "type": "unsubscribed"
                    })
                
                elif action == "get_stats":
                    # Trigger immediate stats response
                    await websocket.send_json({
                        "type": "stats_request_ack",
                        "message": "Use REST API for stats data"
                    })
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown action: {action}"
                    })
                    
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
                
    except WebSocketDisconnect:
        dashboard_ws_manager.disconnect(websocket, "global")
        logger.info("Dashboard WebSocket disconnected")
    except Exception as e:
        logger.error(f"Dashboard WebSocket error: {e}")
        dashboard_ws_manager.disconnect(websocket, "global")


# ============================================================================
# Helper for broadcasting from other modules
# ============================================================================

async def notify_scan_started(scan_id: int, scan_name: str, target: str):
    """Broadcast scan started event"""
    await dashboard_ws_manager.broadcast_global({
        "type": "scan_started",
        "scan_id": scan_id,
        "scan_name": scan_name,
        "target": target,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_scan_completed(scan_id: int, scan_name: str, findings_count: int):
    """Broadcast scan completed event"""
    await dashboard_ws_manager.broadcast_global({
        "type": "scan_completed",
        "scan_id": scan_id,
        "scan_name": scan_name,
        "findings_count": findings_count,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_finding_found(finding_id: int, title: str, severity: str, scan_id: int):
    """Broadcast new finding event"""
    await dashboard_ws_manager.broadcast_global({
        "type": "finding_found",
        "finding_id": finding_id,
        "title": title,
        "severity": severity,
        "scan_id": scan_id,
        "timestamp": datetime.utcnow().isoformat()
    })
