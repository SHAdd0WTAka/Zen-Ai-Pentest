"""
Zen-AI-Pentest API Server

FastAPI-basiertes Backend für das Pentesting-Framework.
"""

import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import asyncio
import json
import logging
from typing import List, Optional
from datetime import datetime

from database.models import init_db, get_db, SessionLocal
from database.crud import (
    create_scan, get_scan, get_scans, update_scan_status,
    create_finding, get_findings, create_report, get_reports
)
from api.schemas import (
    ScanCreate, ScanResponse, ScanUpdate,
    FindingCreate, FindingResponse,
    ReportCreate, ReportResponse,
    ToolExecuteRequest, ToolExecuteResponse,
    WSMessage
)
from api.auth import verify_token, create_access_token
from api.websocket import ConnectionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# WebSocket Manager
ws_manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting up Zen-AI-Pentest API...")
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title="Zen-AI-Pentest API",
    description="Professional Pentesting Framework API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production: Einschränken!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# AUTHENTICATION
# ============================================================================

@app.post("/auth/login")
async def login(credentials: dict):
    """Login and get JWT token"""
    # Simplified - in production: verify against DB/LDAP
    if credentials.get("username") == "admin" and credentials.get("password") == "admin":
        token = create_access_token({"sub": "admin", "role": "admin"})
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/auth/me")
async def me(user: dict = Depends(verify_token)):
    """Get current user info"""
    return user

# ============================================================================
# SCANS
# ============================================================================

@app.post("/scans", response_model=ScanResponse)
async def create_new_scan(
    scan: ScanCreate,
    background_tasks: BackgroundTasks,
    user: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """Create a new pentest scan"""
    db_scan = create_scan(
        db,
        name=scan.name,
        target=scan.target,
        scan_type=scan.scan_type,
        config=scan.config,
        user_id=user.get("sub")
    )
    
    # Start scan in background
    background_tasks.add_task(run_scan_task, db_scan.id, scan.dict())
    
    return db_scan

@app.get("/scans", response_model=List[ScanResponse])
async def list_scans(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    user: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """List all scans with optional filtering"""
    scans = get_scans(db, skip=skip, limit=limit, status=status)
    return scans

@app.get("/scans/{scan_id}", response_model=ScanResponse)
async def get_scan_by_id(
    scan_id: int,
    user: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """Get scan details by ID"""
    scan = get_scan(db, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan

@app.patch("/scans/{scan_id}", response_model=ScanResponse)
async def update_scan(
    scan_id: int,
    update: ScanUpdate,
    user: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """Update scan status or config"""
    scan = update_scan_status(db, scan_id, update.status, update.config)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan

@app.delete("/scans/{scan_id}")
async def delete_scan(
    scan_id: int,
    user: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """Delete a scan"""
    # Implementation here
    return {"message": "Scan deleted"}

# ============================================================================
# FINDINGS
# ============================================================================

@app.get("/scans/{scan_id}/findings", response_model=List[FindingResponse])
async def get_scan_findings(
    scan_id: int,
    severity: Optional[str] = None,
    user: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """Get all findings for a scan"""
    findings = get_findings(db, scan_id, severity)
    return findings

@app.post("/scans/{scan_id}/findings", response_model=FindingResponse)
async def add_finding(
    scan_id: int,
    finding: FindingCreate,
    user: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """Add a finding to a scan"""
    db_finding = create_finding(
        db,
        scan_id=scan_id,
        title=finding.title,
        description=finding.description,
        severity=finding.severity,
        cvss_score=finding.cvss_score,
        evidence=finding.evidence,
        tool=finding.tool
    )
    return db_finding

# ============================================================================
# TOOLS EXECUTION
# ============================================================================

@app.post("/tools/execute", response_model=ToolExecuteResponse)
async def execute_tool(
    request: ToolExecuteRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """Execute a pentesting tool"""
    # Create scan entry
    db_scan = create_scan(
        db,
        name=f"Tool: {request.tool_name}",
        target=request.target,
        scan_type="tool_execution",
        config=request.parameters,
        user_id=user.get("sub")
    )
    
    # Execute in background
    background_tasks.add_task(
        execute_tool_task,
        db_scan.id,
        request.tool_name,
        request.target,
        request.parameters
    )
    
    return ToolExecuteResponse(
        scan_id=db_scan.id,
        status="started",
        message=f"Tool {request.tool_name} execution started"
    )

@app.get("/tools")
async def list_tools(user: dict = Depends(verify_token)):
    """List available tools"""
    from tools import TOOL_REGISTRY
    
    tools = []
    for name, func in TOOL_REGISTRY.items():
        if func:
            tools.append({
                "name": name,
                "description": func.__doc__ or "No description",
                "category": get_tool_category(name)
            })
    
    return {"tools": tools}

def get_tool_category(tool_name: str) -> str:
    """Get tool category based on name"""
    categories = {
        "nmap": "network",
        "masscan": "network",
        "scapy": "network",
        "tshark": "network",
        "burp": "web",
        "sqlmap": "web",
        "gobuster": "web",
        "metasploit": "exploitation",
        "hydra": "brute_force",
        "amass": "recon",
        "bloodhound": "ad",
        "cme": "ad",
        "responder": "ad",
        "aircrack": "wireless"
    }
    
    for key, cat in categories.items():
        if key in tool_name.lower():
            return cat
    return "other"

# ============================================================================
# REPORTS
# ============================================================================

@app.post("/reports", response_model=ReportResponse)
async def generate_report(
    report: ReportCreate,
    background_tasks: BackgroundTasks,
    user: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """Generate a report from scan findings"""
    db_report = create_report(
        db,
        scan_id=report.scan_id,
        format=report.format,
        template=report.template,
        user_id=user.get("sub")
    )
    
    # Generate in background
    background_tasks.add_task(
        generate_report_task,
        db_report.id,
        report.scan_id,
        report.format
    )
    
    return db_report

@app.get("/reports", response_model=List[ReportResponse])
async def list_reports(
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """List all reports"""
    reports = get_reports(db, skip, limit)
    return reports

@app.get("/reports/{report_id}/download")
async def download_report(
    report_id: int,
    user: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """Download a generated report"""
    from fastapi.responses import FileResponse
    
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or not report.file_path:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        report.file_path,
        filename=f"report_{report_id}.{report.format}"
    )

# ============================================================================
# WEBSOCKET
# ============================================================================

@app.websocket("/ws/scans/{scan_id}")
async def scan_websocket(websocket: WebSocket, scan_id: int):
    """WebSocket for real-time scan updates"""
    await ws_manager.connect(websocket, scan_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, scan_id)

@app.websocket("/ws/notifications")
async def notifications_websocket(websocket: WebSocket):
    """WebSocket for global notifications"""
    await ws_manager.connect(websocket, "global")
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "global")

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def run_scan_task(scan_id: int, scan_config: dict):
    """Background task for running a scan"""
    from agents.react_agent import ReActAgent, ReActAgentConfig
    
    db = SessionLocal()
    try:
        update_scan_status(db, scan_id, "running")
        
        # Notify via WebSocket
        await ws_manager.broadcast_to_scan(scan_id, {
            "type": "status",
            "status": "running",
            "message": "Scan started"
        })
        
        # Run agent
        config = ReActAgentConfig(max_iterations=10)
        agent = ReActAgent(config)
        
        result = agent.run(
            target=scan_config["target"],
            objective=scan_config.get("objective", "comprehensive scan")
        )
        
        # Save findings
        for finding_data in result.get("findings", []):
            create_finding(
                db,
                scan_id=scan_id,
                title=f"Finding from {finding_data.get('tool', 'unknown')}",
                description=str(finding_data.get('result', ''))[:500],
                severity="medium",
                tool=finding_data.get('tool')
            )
        
        update_scan_status(db, scan_id, "completed", {
            "result": result.get("final_message", ""),
            "iterations": result.get("iterations", 0)
        })
        
        # Notify completion
        await ws_manager.broadcast_to_scan(scan_id, {
            "type": "status",
            "status": "completed",
            "message": "Scan completed",
            "findings_count": len(result.get("findings", []))
        })
        
    except Exception as e:
        logger.error(f"Scan task error: {e}")
        update_scan_status(db, scan_id, "failed", {"error": str(e)})
        
        await ws_manager.broadcast_to_scan(scan_id, {
            "type": "error",
            "message": str(e)
        })
    finally:
        db.close()

async def execute_tool_task(scan_id: int, tool_name: str, target: str, parameters: dict):
    """Execute a single tool"""
    from tools import TOOL_REGISTRY
    
    db = SessionLocal()
    try:
        tool_func = TOOL_REGISTRY.get(tool_name)
        if not tool_func:
            raise ValueError(f"Tool {tool_name} not found")
        
        # Execute tool
        result = tool_func(target, **parameters)
        
        # Save finding
        create_finding(
            db,
            scan_id=scan_id,
            title=f"{tool_name} result",
            description=str(result)[:1000],
            severity="info",
            tool=tool_name
        )
        
        update_scan_status(db, scan_id, "completed")
        
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        update_scan_status(db, scan_id, "failed", {"error": str(e)})
    finally:
        db.close()

async def generate_report_task(report_id: int, scan_id: int, format: str):
    """Generate report in background"""
    from reports.generator import ReportGenerator
    
    db = SessionLocal()
    try:
        generator = ReportGenerator()
        
        if format == "pdf":
            file_path = generator.generate_pdf(scan_id)
        elif format == "html":
            file_path = generator.generate_html(scan_id)
        else:
            file_path = generator.generate_json(scan_id)
        
        # Update report
        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            report.file_path = file_path
            report.status = "completed"
            db.commit()
        
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            report.status = "failed"
            db.commit()
    finally:
        db.close()

# ============================================================================
# HEALTH & INFO
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/info")
async def api_info():
    """API information"""
    return {
        "name": "Zen-AI-Pentest API",
        "version": "2.0.0",
        "description": "Professional Pentesting Framework",
        "endpoints": {
            "scans": "/scans",
            "findings": "/scans/{id}/findings",
            "tools": "/tools",
            "reports": "/reports"
        }
    }

# ============================================================================
# STATS
# ============================================================================

@app.get("/stats/overview")
async def get_stats_overview(
    user: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """Get dashboard statistics overview"""
    from sqlalchemy import func
    from database.models import Scan, Finding
    
    # Basic counts
    total_scans = db.query(Scan).count()
    completed_scans = db.query(Scan).filter(Scan.status == "completed").count()
    running_scans = db.query(Scan).filter(Scan.status == "running").count()
    
    # Findings counts
    total_findings = db.query(Finding).count()
    
    # Severity distribution
    severity_counts = db.query(
        Finding.severity, 
        func.count(Finding.id)
    ).group_by(Finding.severity).all()
    
    severity_distribution = [
        {"name": sev.capitalize(), "value": count, "color": get_severity_color(sev)}
        for sev, count in severity_counts
    ]
    
    # Fill missing severities
    all_severities = ['critical', 'high', 'medium', 'low', 'info']
    existing = {s['name'].lower(): s for s in severity_distribution}
    for sev in all_severities:
        if sev not in existing:
            severity_distribution.append({
                "name": sev.capitalize(),
                "value": 0,
                "color": get_severity_color(sev)
            })
    
    return {
        "total_scans": total_scans,
        "completed_scans": completed_scans,
        "running_scans": running_scans,
        "total_findings": total_findings,
        "critical_findings": sum(1 for s in severity_counts if s[0] == 'critical'),
        "severity_distribution": severity_distribution,
        "trends": [],  # TODO: Implement trends
        "tool_usage": []  # TODO: Implement tool usage
    }

def get_severity_color(severity: str) -> str:
    """Get color for severity level"""
    colors = {
        'critical': '#ef4444',
        'high': '#f97316',
        'medium': '#eab308',
        'low': '#22c55e',
        'info': '#3b82f6'
    }
    return colors.get(severity.lower(), '#6b7280')

@app.get("/stats/trends")
async def get_stats_trends(
    days: int = 30,
    user: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """Get scan trends for the last N days"""
    # TODO: Implement trend calculation
    return []

@app.get("/stats/severity")
async def get_severity_stats(
    user: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """Get findings by severity"""
    from sqlalchemy import func
    from database.models import Finding
    
    severity_counts = db.query(
        Finding.severity, 
        func.count(Finding.id)
    ).group_by(Finding.severity).all()
    
    return [
        {"severity": sev, "count": count}
        for sev, count in severity_counts
    ]

@app.get("/stats/tools")
async def get_tool_usage(
    user: dict = Depends(verify_token),
    db = Depends(get_db)
):
    """Get tool usage statistics"""
    # TODO: Implement tool usage tracking
    return []

# Import models for reports
from database.models import Report

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
