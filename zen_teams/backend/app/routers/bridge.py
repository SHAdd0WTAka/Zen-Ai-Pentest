"""Zen-AI-Pentest Bridge API Router"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.services.bridge import zen_bridge

router = APIRouter()


class ScanTriggerRequest(BaseModel):
    target: str
    scan_type: str = "full"
    ticket_id: Optional[str] = None
    options: Optional[dict] = None


class ToolRunRequest(BaseModel):
    tool_name: str
    target: str
    options: Optional[dict] = None


@router.get("/health")
async def bridge_health():
    """Check Zen-AI-Pentest bridge connectivity"""
    return await zen_bridge.health_check()


@router.post("/scan")
async def trigger_scan(request: ScanTriggerRequest):
    """Trigger a scan in Zen-AI-Pentest"""
    try:
        result = await zen_bridge.create_scan(
            target=request.target,
            scan_type=request.scan_type,
            options=request.options,
        )
        return {
            "status": "success",
            "scan_id": result.get("id"),
            "message": f"Scan started for {request.target}",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scan: {str(e)}")


@router.get("/scan/{scan_id}")
async def get_scan_status(scan_id: str):
    """Get scan status from Zen-AI-Pentest"""
    try:
        result = await zen_bridge.get_scan(scan_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Scan not found: {str(e)}")


@router.get("/scan/{scan_id}/results")
async def get_scan_results(scan_id: str):
    """Get scan results from Zen-AI-Pentest"""
    try:
        result = await zen_bridge.get_scan_results(scan_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Results not found: {str(e)}")


@router.get("/scans")
async def list_scans(status: Optional[str] = None, limit: int = 50):
    """List scans from Zen-AI-Pentest"""
    try:
        result = await zen_bridge.list_scans(status=status, limit=limit)
        return {"scans": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list scans: {str(e)}")


@router.post("/tool/run")
async def run_tool(request: ToolRunRequest):
    """Run a specific pentest tool"""
    try:
        result = await zen_bridge.run_tool(
            tool_name=request.tool_name,
            target=request.target,
            options=request.options,
        )
        return {
            "status": "success",
            "message": f"Tool {request.tool_name} executed on {request.target}",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run tool: {str(e)}")


@router.get("/tools")
async def list_tools():
    """List available pentest tools"""
    try:
        result = await zen_bridge.get_tools()
        return {"tools": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")


@router.post("/report/generate/{scan_id}")
async def generate_report(scan_id: str, format: str = "pdf"):
    """Generate a report for a scan"""
    try:
        result = await zen_bridge.generate_report(scan_id=scan_id, format=format)
        return {
            "status": "success",
            "message": f"Report generated in {format} format",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")
