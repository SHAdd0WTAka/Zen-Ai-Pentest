"""
Web UI Backend - FastAPI
Q3 2026 Roadmap: Web Dashboard
"""

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Import our autonomous modules
import sys
sys.path.append('../..')
from autonomous import AutonomousAgent, AgentConfig
from autonomous.tool_executor import SafetyLevel
from risk_engine import RiskScorer


# ============== Pydantic Models ==============

class ScanRequest(BaseModel):
    target: str
    goal: Optional[str] = None
    scan_type: str = "comprehensive"  # quick, standard, comprehensive
    safety_level: str = "non_destructive"
    scope: Optional[Dict] = None


class ScanStatus(BaseModel):
    scan_id: str
    status: str  # pending, running, completed, failed
    progress: float  # 0-100
    current_step: int
    total_steps: int
    findings_count: int
    start_time: Optional[str]
    end_time: Optional[str]
    error_message: Optional[str]


class Finding(BaseModel):
    id: str
    type: str
    severity: str
    title: str
    description: str
    target: str
    evidence: Optional[Dict]
    risk_score: Optional[Dict]
    timestamp: str


class DashboardStats(BaseModel):
    total_scans: int
    active_scans: int
    completed_scans: int
    failed_scans: int
    total_findings: int
    critical_findings: int
    high_findings: int
    tools_used: List[str]


# ============== Global State ==============

class ScanManager:
    """Manages active scans and their state."""
    
    def __init__(self):
        self.active_scans: Dict[str, Dict] = {}
        self.scan_history: List[Dict] = []
        self.clients: List[WebSocket] = []
    
    async def start_scan(self, scan_id: str, request: ScanRequest) -> None:
        """Start a new scan."""
        self.active_scans[scan_id] = {
            'id': scan_id,
            'request': request,
            'status': 'pending',
            'progress': 0.0,
            'current_step': 0,
            'total_steps': 50,
            'findings': [],
            'logs': [],
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'error': None
        }
    
    async def update_progress(self, scan_id: str, progress: float, step: int, message: str = "") -> None:
        """Update scan progress."""
        if scan_id in self.active_scans:
            self.active_scans[scan_id]['progress'] = progress
            self.active_scans[scan_id]['current_step'] = step
            if message:
                self.active_scans[scan_id]['logs'].append({
                    'timestamp': datetime.now().isoformat(),
                    'message': message
                })
            
            # Broadcast to connected clients
            await self.broadcast({
                'type': 'progress',
                'scan_id': scan_id,
                'data': self.get_scan_status(scan_id)
            })
    
    async def add_finding(self, scan_id: str, finding: Dict) -> None:
        """Add a finding to a scan."""
        if scan_id in self.active_scans:
            self.active_scans[scan_id]['findings'].append(finding)
            
            await self.broadcast({
                'type': 'finding',
                'scan_id': scan_id,
                'data': finding
            })
    
    def complete_scan(self, scan_id: str, success: bool = True, error: Optional[str] = None) -> None:
        """Mark a scan as completed."""
        if scan_id in self.active_scans:
            self.active_scans[scan_id]['status'] = 'completed' if success else 'failed'
            self.active_scans[scan_id]['end_time'] = datetime.now().isoformat()
            self.active_scans[scan_id]['error'] = error
            
            # Move to history
            self.scan_history.append(self.active_scans[scan_id])
            del self.active_scans[scan_id]
    
    def get_scan_status(self, scan_id: str) -> Optional[Dict]:
        """Get current status of a scan."""
        if scan_id in self.active_scans:
            scan = self.active_scans[scan_id]
            return {
                'scan_id': scan_id,
                'status': scan['status'],
                'progress': scan['progress'],
                'current_step': scan['current_step'],
                'total_steps': scan['total_steps'],
                'findings_count': len(scan['findings']),
                'start_time': scan['start_time'],
                'end_time': scan['end_time'],
                'error_message': scan['error']
            }
        return None
    
    def get_all_scans(self) -> List[Dict]:
        """Get all scans (active + history)."""
        all_scans = list(self.active_scans.values()) + self.scan_history
        return [
            {
                'scan_id': s['id'],
                'target': s['request'].target,
                'status': s.get('status', 'unknown'),
                'progress': s.get('progress', 0),
                'findings_count': len(s.get('findings', [])),
                'start_time': s.get('start_time'),
                'end_time': s.get('end_time')
            }
            for s in sorted(all_scans, key=lambda x: x.get('start_time', ''), reverse=True)
        ]
    
    def get_dashboard_stats(self) -> DashboardStats:
        """Get dashboard statistics."""
        all_scans = list(self.active_scans.values()) + self.scan_history
        
        total_findings = 0
        critical = 0
        high = 0
        tools_used = set()
        
        for scan in all_scans:
            findings = scan.get('findings', [])
            total_findings += len(findings)
            for f in findings:
                if f.get('severity') == 'CRITICAL':
                    critical += 1
                elif f.get('severity') == 'HIGH':
                    high += 1
                if 'tool' in f:
                    tools_used.add(f['tool'])
        
        return DashboardStats(
            total_scans=len(all_scans),
            active_scans=len(self.active_scans),
            completed_scans=len([s for s in self.scan_history if s.get('status') == 'completed']),
            failed_scans=len([s for s in self.scan_history if s.get('status') == 'failed']),
            total_findings=total_findings,
            critical_findings=critical,
            high_findings=high,
            tools_used=list(tools_used)
        )
    
    async def connect_client(self, websocket: WebSocket) -> None:
        """Connect a WebSocket client."""
        await websocket.accept()
        self.clients.append(websocket)
    
    async def disconnect_client(self, websocket: WebSocket) -> None:
        """Disconnect a WebSocket client."""
        if websocket in self.clients:
            self.clients.remove(websocket)
    
    async def broadcast(self, message: Dict) -> None:
        """Broadcast message to all connected clients."""
        disconnected = []
        for client in self.clients:
            try:
                await client.send_json(message)
            except:
                disconnected.append(client)
        
        # Clean up disconnected clients
        for client in disconnected:
            if client in self.clients:
                self.clients.remove(client)


# Global scan manager
scan_manager = ScanManager()


# ============== FastAPI App ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🚀 Zen AI Pentest Web UI starting...")
    yield
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title="Zen AI Pentest Web UI",
    description="Autonomous penetration testing dashboard",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== API Endpoints ==============

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics."""
    return scan_manager.get_dashboard_stats()


@app.get("/api/scans", response_model=List[Dict])
async def get_all_scans():
    """Get all scans."""
    return scan_manager.get_all_scans()


@app.post("/api/scans", response_model=Dict)
async def create_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Create and start a new scan."""
    scan_id = str(uuid.uuid4())
    
    await scan_manager.start_scan(scan_id, request)
    
    # Start scan in background
    background_tasks.add_task(run_scan, scan_id, request)
    
    return {
        "scan_id": scan_id,
        "status": "started",
        "message": f"Scan started for target: {request.target}"
    }


@app.get("/api/scans/{scan_id}")
async def get_scan(scan_id: str):
    """Get scan details."""
    # Check active scans
    if scan_id in scan_manager.active_scans:
        return scan_manager.active_scans[scan_id]
    
    # Check history
    for scan in scan_manager.scan_history:
        if scan['id'] == scan_id:
            return scan
    
    raise HTTPException(status_code=404, detail="Scan not found")


@app.get("/api/scans/{scan_id}/status", response_model=ScanStatus)
async def get_scan_status(scan_id: str):
    """Get scan status."""
    status = scan_manager.get_scan_status(scan_id)
    if status:
        return ScanStatus(**status)
    raise HTTPException(status_code=404, detail="Scan not found")


@app.get("/api/scans/{scan_id}/findings", response_model=List[Finding])
async def get_scan_findings(scan_id: str):
    """Get scan findings."""
    # Check active scans
    if scan_id in scan_manager.active_scans:
        findings = scan_manager.active_scans[scan_id]['findings']
        return [Finding(**f) for f in findings]
    
    # Check history
    for scan in scan_manager.scan_history:
        if scan['id'] == scan_id:
            findings = scan.get('findings', [])
            return [Finding(**f) for f in findings]
    
    raise HTTPException(status_code=404, detail="Scan not found")


@app.get("/api/scans/{scan_id}/logs")
async def get_scan_logs(scan_id: str):
    """Get scan logs."""
    if scan_id in scan_manager.active_scans:
        return scan_manager.active_scans[scan_id]['logs']
    
    for scan in scan_manager.scan_history:
        if scan['id'] == scan_id:
            return scan.get('logs', [])
    
    raise HTTPException(status_code=404, detail="Scan not found")


@app.delete("/api/scans/{scan_id}")
async def cancel_scan(scan_id: str):
    """Cancel an active scan."""
    if scan_id in scan_manager.active_scans:
        scan_manager.complete_scan(scan_id, success=False, error="Cancelled by user")
        return {"message": "Scan cancelled"}
    
    raise HTTPException(status_code=404, detail="Scan not found or already completed")


# ============== WebSocket ==============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates."""
    await scan_manager.connect_client(websocket)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'ping':
                await websocket.send_json({'type': 'pong'})
                
    except WebSocketDisconnect:
        await scan_manager.disconnect_client(websocket)


# ============== Background Scan Task ==============

async def run_scan(scan_id: str, request: ScanRequest):
    """Background task to run the scan."""
    try:
        await scan_manager.update_progress(scan_id, 0, 0, "Initializing scan...")
        
        # Map safety level
        safety_map = {
            'read_only': SafetyLevel.READ_ONLY,
            'non_destructive': SafetyLevel.NON_DESTRUCTIVE,
            'destructive': SafetyLevel.DESTRUCTIVE,
            'exploit': SafetyLevel.EXPLOIT
        }
        safety = safety_map.get(request.safety_level, SafetyLevel.NON_DESTRUCTIVE)
        
        # Create agent config
        config = AgentConfig(
            safety_level=safety,
            max_iterations=50,
            enable_memory=True
        )
        
        # Create mock LLM client (in production, use real backend)
        class MockLLM:
            async def generate(self, prompt: str) -> str:
                # Simulate LLM responses
                if "reasoning" in prompt.lower():
                    return "I should start with reconnaissance to understand the target."
                elif "action" in prompt.lower():
                    return '{"action_type": "TOOL_CALL", "tool_name": "nmap", "parameters": {"target": "' + request.target + '"}}'
                return "Continue with the assessment."
        
        agent = AutonomousAgent(MockLLM(), config)
        
        await scan_manager.update_progress(scan_id, 10, 1, "Starting reconnaissance...")
        
        # Run the scan
        goal = request.goal or f"Comprehensive security assessment of {request.target}"
        result = await agent.run(goal=goal, target=request.target, scope=request.scope)
        
        await scan_manager.update_progress(scan_id, 50, 25, "Analyzing results...")
        
        # Process findings and calculate risk scores
        risk_scorer = RiskScorer()
        
        for finding in result.get('findings', []):
            # Calculate risk score
            risk = risk_scorer.calculate(finding, {
                'internet_facing': True,  # Would be determined from target
                'data_sensitivity': 'internal'
            })
            
            finding_with_risk = {
                **finding,
                'risk_score': risk.to_dict(),
                'scan_id': scan_id,
                'timestamp': datetime.now().isoformat()
            }
            
            await scan_manager.add_finding(scan_id, finding_with_risk)
        
        await scan_manager.update_progress(scan_id, 100, 50, "Scan completed")
        
        # Complete the scan
        scan_manager.complete_scan(scan_id, success=True)
        
    except Exception as e:
        await scan_manager.update_progress(scan_id, 0, 0, f"Error: {str(e)}")
        scan_manager.complete_scan(scan_id, success=False, error=str(e))


# ============== Static Files ==============

# Serve React frontend (in production, build and copy files)
try:
    app.mount("/static", StaticFiles(directory="../frontend/build/static"), name="static")
    
    @app.get("/")
    async def serve_frontend():
        return FileResponse("../frontend/build/index.html")
        
    @app.get("/{path:path}")
    async def serve_frontend_routes(path: str):
        return FileResponse("../frontend/build/index.html")
except:
    pass  # Frontend not built yet


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
