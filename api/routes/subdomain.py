#!/usr/bin/env python3
"""
Subdomain Scanning API Routes
RESTful API for subdomain enumeration
"""

import asyncio
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.core.auth import get_current_user
from modules.subdomain_scanner import SubdomainScanner, SubdomainResult

router = APIRouter(prefix="/subdomain", tags=["subdomain"])

# In-memory storage for scan jobs (replace with Redis/DB in production)
scan_jobs = {}


class SubdomainScanRequest(BaseModel):
    """Request model for subdomain scan"""
    domain: str = Field(..., description="Target domain to scan", example="target.com")
    techniques: List[str] = Field(
        default=["dns", "wordlist", "crt"],
        description="Enumeration techniques to use"
    )
    check_http: bool = Field(default=True, description="Check HTTP/HTTPS availability")
    max_workers: int = Field(default=50, ge=1, le=200, description="Concurrent workers")
    timeout: int = Field(default=10, ge=1, le=60, description="Request timeout in seconds")
    custom_wordlist: Optional[List[str]] = Field(default=None, description="Custom subdomain wordlist")


class SubdomainScanResponse(BaseModel):
    """Response model for subdomain scan result"""
    subdomain: str
    ip_addresses: List[str] = []
    status_code: Optional[int] = None
    server_header: Optional[str] = None
    technologies: List[str] = []
    is_alive: bool = False
    discovered_at: str


class ScanJobResponse(BaseModel):
    """Scan job status response"""
    job_id: str
    status: str  # pending, running, completed, failed
    domain: str
    progress: int = 0
    results_count: int = 0
    message: Optional[str] = None


class ScanSummary(BaseModel):
    """Summary of scan results"""
    total_discovered: int
    live_hosts: int
    dns_only: int
    techniques_used: List[str]
    scan_duration: float


def result_to_dict(subdomain: str, result: SubdomainResult) -> dict:
    """Convert SubdomainResult to dict"""
    return {
        "subdomain": subdomain,
        "ip_addresses": result.ip_addresses,
        "status_code": result.status_code,
        "server_header": result.server_header,
        "technologies": result.technologies,
        "is_alive": result.is_alive,
        "discovered_at": result.discovered_at.isoformat() if result.discovered_at else None,
    }


@router.post("/scan", response_model=ScanJobResponse)
async def start_subdomain_scan(
    request: SubdomainScanRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Start a new subdomain enumeration scan
    
    Returns a job ID that can be used to check scan status and retrieve results.
    """
    import uuid
    
    job_id = str(uuid.uuid4())
    
    scan_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "domain": request.domain,
        "progress": 0,
        "results": {},
        "results_count": 0,
        "message": "Scan queued",
        "user": current_user.get("username", "anonymous"),
    }
    
    # Start scan in background
    background_tasks.add_task(_run_scan, job_id, request)
    
    return ScanJobResponse(
        job_id=job_id,
        status="pending",
        domain=request.domain,
        message="Scan started"
    )


async def _run_scan(job_id: str, request: SubdomainScanRequest):
    """Background task to run subdomain scan"""
    import time
    
    start_time = time.time()
    scan_jobs[job_id]["status"] = "running"
    scan_jobs[job_id]["message"] = "Scan in progress..."
    
    try:
        scanner = SubdomainScanner(
            max_workers=request.max_workers,
            timeout=request.timeout
        )
        
        # Run scan
        results = await scanner.scan(
            domain=request.domain,
            techniques=request.techniques,
            check_http=request.check_http,
            wordlist=request.custom_wordlist
        )
        
        # Update job with results
        scan_jobs[job_id]["status"] = "completed"
        scan_jobs[job_id]["results"] = {
            sub: result_to_dict(sub, res) for sub, res in results.items()
        }
        scan_jobs[job_id]["results_count"] = len(results)
        scan_jobs[job_id]["progress"] = 100
        scan_jobs[job_id]["scan_duration"] = time.time() - start_time
        scan_jobs[job_id]["message"] = f"Scan completed. Found {len(results)} subdomains"
        
    except Exception as e:
        scan_jobs[job_id]["status"] = "failed"
        scan_jobs[job_id]["message"] = f"Scan failed: {str(e)}"


@router.get("/scan/{job_id}", response_model=ScanJobResponse)
async def get_scan_status(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the status of a running or completed scan"""
    if job_id not in scan_jobs:
        raise HTTPException(status_code=404, detail="Scan job not found")
    
    job = scan_jobs[job_id]
    return ScanJobResponse(
        job_id=job_id,
        status=job["status"],
        domain=job["domain"],
        progress=job.get("progress", 0),
        results_count=job.get("results_count", 0),
        message=job.get("message")
    )


@router.get("/scan/{job_id}/results", response_model=List[SubdomainScanResponse])
async def get_scan_results(
    job_id: str,
    alive_only: bool = Query(False, description="Only return live hosts"),
    current_user: dict = Depends(get_current_user)
):
    """Get results from a completed scan"""
    if job_id not in scan_jobs:
        raise HTTPException(status_code=404, detail="Scan job not found")
    
    job = scan_jobs[job_id]
    
    if job["status"] not in ["completed", "running"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Scan not ready. Status: {job['status']}"
        )
    
    results = job.get("results", {})
    
    # Filter if requested
    if alive_only:
        results = {k: v for k, v in results.items() if v.get("is_alive", False)}
    
    return list(results.values())


@router.get("/scan/{job_id}/summary", response_model=ScanSummary)
async def get_scan_summary(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get summary statistics for a scan"""
    if job_id not in scan_jobs:
        raise HTTPException(status_code=404, detail="Scan job not found")
    
    job = scan_jobs[job_id]
    results = job.get("results", {})
    
    live_count = sum(1 for r in results.values() if r.get("is_alive", False))
    
    return ScanSummary(
        total_discovered=len(results),
        live_hosts=live_count,
        dns_only=len(results) - live_count,
        techniques_used=[],  # TODO: store in job
        scan_duration=job.get("scan_duration", 0)
    )


@router.delete("/scan/{job_id}")
async def delete_scan_job(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a scan job and its results"""
    if job_id not in scan_jobs:
        raise HTTPException(status_code=404, detail="Scan job not found")
    
    del scan_jobs[job_id]
    return {"message": "Scan job deleted"}


@router.get("/scans", response_model=List[ScanJobResponse])
async def list_scan_jobs(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100)
):
    """List recent scan jobs"""
    user_jobs = [
        ScanJobResponse(
            job_id=jid,
            status=job["status"],
            domain=job["domain"],
            progress=job.get("progress", 0),
            results_count=job.get("results_count", 0),
            message=job.get("message")
        )
        for jid, job in list(scan_jobs.items())[-limit:]
    ]
    return user_jobs


@router.post("/quick-scan")
async def quick_subdomain_scan(
    domain: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Quick synchronous subdomain scan
    
    Returns results immediately (may take 30-60 seconds for large domains).
    For longer scans, use the async /scan endpoint.
    """
    scanner = SubdomainScanner(max_workers=30, timeout=10)
    
    try:
        results = await scanner.scan(
            domain=domain,
            techniques=["dns", "wordlist", "crt"],
            check_http=True
        )
        
        return {
            "domain": domain,
            "total_found": len(results),
            "results": [result_to_dict(sub, res) for sub, res in results.items()]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")
