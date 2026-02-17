

@router.get("/tools/status")
async def get_tools_status():
    """Get pentest tools installation status"""
    try:
        from tools.integrations.tool_checker import ToolChecker
        
        checker = ToolChecker()
        report = checker.get_status_report()
        
        return report
    except Exception as e:
        return {
            "ready": False,
            "error": str(e),
            "message": "Tool checker not available"
        }


@router.post("/tools/install")
async def install_tools(background_tasks: BackgroundTasks):
    """Trigger tool installation (runs in background)"""
    import subprocess
    import sys
    
    def run_installer():
        try:
            if sys.platform == "win32":
                subprocess.Popen(["powershell", "-ExecutionPolicy", "Bypass", "-File", "scripts/install-tools.ps1"])
            else:
                subprocess.Popen(["bash", "scripts/install-tools.sh", "--all"])
        except Exception as e:
            logger.error(f"Failed to start installer: {e}")
    
    background_tasks.add_task(run_installer)
    
    return {
        "status": "installation_started",
        "message": "Tool installation started in background. Check /system/tools/status for progress."
    }
"""
System Management Endpoints

System status, health checks, and administrative functions.
"""

import platform
from datetime import datetime


import psutil
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.core.auth import require_permissions
from api.models.user import User, UserRole

router = APIRouter()


class SystemStatus(BaseModel):
    """System status response"""

    status: str
    version: str
    uptime: float
    environment: str


class SystemMetrics(BaseModel):
    """System resource metrics"""

    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_io_sent_mb: float
    network_io_recv_mb: float


class APIStats(BaseModel):
    """API usage statistics"""

    total_requests: int
    requests_per_minute: float
    average_response_time_ms: float
    error_rate: float
    active_connections: int


@router.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Get basic system status"""
    return {
        "status": "operational",
        "version": "1.0.0",
        "uptime": psutil.boot_time(),
        "environment": "production",
    }


@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics(
    current_user: User = Depends(require_permissions(UserRole.ADMIN)),
):
    """Get detailed system resource metrics (admin only)"""
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)

    # Memory
    memory = psutil.virtual_memory()
    memory_used_gb = memory.used / (1024**3)
    memory_total_gb = memory.total / (1024**3)

    # Disk
    disk = psutil.disk_usage("/")
    disk_used_gb = disk.used / (1024**3)
    disk_total_gb = disk.total / (1024**3)

    # Network
    net_io = psutil.net_io_counters()
    network_sent_mb = net_io.bytes_sent / (1024**2)
    network_recv_mb = net_io.bytes_recv / (1024**2)

    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_used_gb": round(memory_used_gb, 2),
        "memory_total_gb": round(memory_total_gb, 2),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk_used_gb, 2),
        "disk_total_gb": round(disk_total_gb, 2),
        "network_io_sent_mb": round(network_sent_mb, 2),
        "network_io_recv_mb": round(network_recv_mb, 2),
    }


@router.get("/info")
async def get_system_info(
    current_user: User = Depends(require_permissions(UserRole.ADMIN)),
):
    """Get detailed system information (admin only)"""
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "processor": platform.processor(),
        "hostname": platform.node(),
        "cpu_count": psutil.cpu_count(),
        "cpu_freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        "load_average": psutil.getloadavg() if hasattr(psutil, "getloadavg") else None,
    }


@router.get("/stats", response_model=APIStats)
async def get_api_stats(
    current_user: User = Depends(require_permissions(UserRole.ADMIN)),
):
    """Get API usage statistics (admin only)"""
    # TODO: Implement actual stats tracking
    return {
        "total_requests": 0,
        "requests_per_minute": 0.0,
        "average_response_time_ms": 0.0,
        "error_rate": 0.0,
        "active_connections": 0,
    }


@router.get("/logs")
async def get_system_logs(lines: int = 100, current_user: User = Depends(require_permissions(UserRole.ADMIN))):
    """Get recent system logs (admin only)"""
    try:
        with open("logs/zen_ai.log", "r") as f:
            logs = f.readlines()
        return {"logs": logs[-lines:]}
    except FileNotFoundError:
        return {"logs": [], "message": "Log file not found"}


@router.post("/maintenance")
async def toggle_maintenance_mode(enabled: bool, current_user: User = Depends(require_permissions(UserRole.ADMIN))):
    """Toggle maintenance mode (admin only)"""
    # TODO: Implement maintenance mode
    return {
        "message": f"Maintenance mode {'enabled' if enabled else 'disabled'}",
        "enabled": enabled,
    }


@router.post("/clear-cache")
async def clear_system_cache(
    current_user: User = Depends(require_permissions(UserRole.ADMIN)),
):
    """Clear system cache (admin only)"""
    from api.core.cache import clear_cache

    await clear_cache()
    return {"message": "Cache cleared"}


@router.get("/database/status")
async def get_database_status(
    current_user: User = Depends(require_permissions(UserRole.ADMIN)),
):
    """Get database connection status (admin only)"""
    # TODO: Implement actual DB status check
    return {"status": "connected", "type": "postgresql", "latency_ms": 0}


@router.get("/cache/status")
async def get_cache_status(
    current_user: User = Depends(require_permissions(UserRole.ADMIN)),
):
    """Get cache status (admin only)"""
    # TODO: Implement actual cache status
    return {
        "status": "connected",
        "type": "redis",
        "keys_count": 0,
        "memory_usage_mb": 0,
    }
