"""
Integration Bridge - API for Pentesting Tool Orchestration
Connects Zen AI Pentest with classic tools (Nmap, Metasploit, SQLmap, etc.)
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import docker
from docker.errors import DockerException
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Zen Pentest Integration Bridge",
    description="API for orchestrating classic pentesting tools",
    version="1.0.0",
)

# Docker client
try:
    docker_client = docker.from_env()
except DockerException:
    docker_client = None
    logger.warning("Docker client not available")

# Shared directories
SHARED_SCANS = Path("/shared/scans")
SHARED_REPORTS = Path("/shared/reports")

# Active scans tracking
active_scans: Dict[str, Dict[str, Any]] = {}


class ScanRequest(BaseModel):
    """Base scan request model"""

    target: str = Field(..., description="Target host/IP/URL")
    options: Dict[str, Any] = Field(
        default_factory=dict, description="Tool-specific options"
    )
    callback_url: Optional[str] = Field(None, description="Webhook URL for completion")


class NmapScanRequest(ScanRequest):
    """Nmap-specific scan request"""

    scan_type: str = Field(
        "tcp_syn", description="Scan type: tcp_syn, tcp_connect, udp, comprehensive"
    )
    ports: str = Field("top-1000", description="Port specification")
    scripts: List[str] = Field(default_factory=list, description="NSE scripts to run")


class SQLMapRequest(ScanRequest):
    """SQLMap scan request"""

    url: str = Field(..., description="Target URL")
    method: str = Field("GET", description="HTTP method")
    data: Optional[str] = Field(None, description="POST data")
    cookies: Optional[str] = Field(None, description="Cookies")
    level: int = Field(1, ge=1, le=5, description="Test level")
    risk: int = Field(1, ge=1, le=3, description="Risk level")
    dbms: Optional[str] = Field(None, description="Target DBMS")


class MetasploitRequest(BaseModel):
    """Metasploit module execution request"""

    module: str = Field(..., description="Metasploit module path")
    rhosts: str = Field(..., description="Target hosts")
    rport: int = Field(443, description="Target port")
    options: Dict[str, Any] = Field(default_factory=dict, description="Module options")


class ScanResult(BaseModel):
    """Scan result model"""

    scan_id: str
    tool: str
    target: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    output_file: Optional[str] = None
    raw_output: Optional[str] = None
    parsed_results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Nmap Integration
@app.post("/api/v1/scan/nmap", response_model=ScanResult)
async def run_nmap_scan(request: NmapScanRequest, background_tasks: BackgroundTasks):
    """
    Execute Nmap scan against target
    """
    scan_id = str(uuid.uuid4())[:8]
    output_file = SHARED_SCANS / f"nmap_{scan_id}.xml"

    # Build Nmap command
    cmd_parts = ["nmap", "-oX", str(output_file)]

    # Scan type
    scan_flags = {
        "tcp_syn": "-sS",
        "tcp_connect": "-sT",
        "udp": "-sU",
        "comprehensive": "-sS -sV -sC -O -A",
    }
    cmd_parts.extend(scan_flags.get(request.scan_type, "-sS").split())

    # Ports
    if request.ports == "top-1000":
        cmd_parts.append("--top-ports")
        cmd_parts.append("1000")
    elif request.ports == "all":
        cmd_parts.append("-p-")
    else:
        cmd_parts.extend(["-p", request.ports])

    # Scripts
    if request.scripts:
        cmd_parts.append(f"--script={','.join(request.scripts)}")

    cmd_parts.append(request.target)

    # Start scan
    scan_info = {
        "scan_id": scan_id,
        "tool": "nmap",
        "target": request.target,
        "status": "running",
        "start_time": datetime.utcnow(),
        "command": " ".join(cmd_parts),
        "output_file": str(output_file),
    }
    active_scans[scan_id] = scan_info

    # Run in background
    background_tasks.add_task(
        execute_docker_scan,
        container_name="zen-nmap",
        command=cmd_parts,
        scan_id=scan_id,
        output_file=output_file,
    )

    return ScanResult(**scan_info)


# SQLMap Integration
@app.post("/api/v1/scan/sqlmap", response_model=ScanResult)
async def run_sqlmap_scan(request: SQLMapRequest, background_tasks: BackgroundTasks):
    """
    Execute SQLMap scan against target URL
    """
    scan_id = str(uuid.uuid4())[:8]
    output_dir = SHARED_SCANS / f"sqlmap_{scan_id}"
    output_dir.mkdir(exist_ok=True)

    # Build SQLMap command
    cmd_parts = [
        "sqlmap",
        "-u",
        request.url,
        "--method",
        request.method,
        "--level",
        str(request.level),
        "--risk",
        str(request.risk),
        "--output-dir",
        str(output_dir),
        "--batch",
        "--format",
        "json",
    ]

    if request.data:
        cmd_parts.extend(["--data", request.data])
    if request.cookies:
        cmd_parts.extend(["--cookie", request.cookies])
    if request.dbms:
        cmd_parts.extend(["--dbms", request.dbms])

    # Additional options
    cmd_parts.extend(["--random-agent", "--threads", "10", "--timeout", "30"])

    scan_info = {
        "scan_id": scan_id,
        "tool": "sqlmap",
        "target": request.url,
        "status": "running",
        "start_time": datetime.utcnow(),
        "command": " ".join(cmd_parts),
        "output_dir": str(output_dir),
    }
    active_scans[scan_id] = scan_info

    background_tasks.add_task(
        execute_docker_scan,
        container_name="zen-sqlmap",
        command=cmd_parts,
        scan_id=scan_id,
        output_file=output_dir / "log",
    )

    return ScanResult(**scan_info)


# Metasploit Integration
@app.post("/api/v1/scan/metasploit", response_model=ScanResult)
async def run_metasploit_module(
    request: MetasploitRequest, background_tasks: BackgroundTasks
):
    """
    Execute Metasploit module
    """
    scan_id = str(uuid.uuid4())[:8]
    rc_file = SHARED_SCANS / f"msf_{scan_id}.rc"
    output_file = SHARED_SCANS / f"msf_{scan_id}.txt"

    # Generate resource script
    with open(rc_file, "w") as f:
        f.write(f"use {request.module}\n")
        f.write(f"set RHOSTS {request.rhosts}\n")
        f.write(f"set RPORT {request.rport}\n")
        for key, value in request.options.items():
            f.write(f"set {key} {value}\n")
        f.write(f"spool {output_file}\n")
        f.write("run\n")
        f.write("spool off\n")
        f.write("exit\n")

    cmd_parts = ["msfconsole", "-q", "-r", str(rc_file)]

    scan_info = {
        "scan_id": scan_id,
        "tool": "metasploit",
        "target": request.rhosts,
        "status": "running",
        "start_time": datetime.utcnow(),
        "command": " ".join(cmd_parts),
        "output_file": str(output_file),
    }
    active_scans[scan_id] = scan_info

    background_tasks.add_task(
        execute_docker_scan,
        container_name="zen-metasploit",
        command=cmd_parts,
        scan_id=scan_id,
        output_file=output_file,
    )

    return ScanResult(**scan_info)


# Nuclei Integration
@app.post("/api/v1/scan/nuclei", response_model=ScanResult)
async def run_nuclei_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Execute Nuclei vulnerability scan
    """
    scan_id = str(uuid.uuid4())[:8]
    output_file = SHARED_SCANS / f"nuclei_{scan_id}.json"

    cmd_parts = [
        "nuclei",
        "-u",
        request.target,
        "-json-export",
        str(output_file),
        "-c",
        str(request.options.get("concurrency", 50)),
        "-rl",
        str(request.options.get("rate_limit", 150)),
    ]

    # Add severity filter if specified
    if "severity" in request.options:
        cmd_parts.extend(["-s", request.options["severity"]])

    # Add templates if specified
    if "templates" in request.options:
        for template in request.options["templates"]:
            cmd_parts.extend(["-t", template])

    scan_info = {
        "scan_id": scan_id,
        "tool": "nuclei",
        "target": request.target,
        "status": "running",
        "start_time": datetime.utcnow(),
        "command": " ".join(cmd_parts),
        "output_file": str(output_file),
    }
    active_scans[scan_id] = scan_info

    background_tasks.add_task(
        execute_docker_scan,
        container_name="zen-nuclei",
        command=cmd_parts,
        scan_id=scan_id,
        output_file=output_file,
    )

    return ScanResult(**scan_info)


# Gobuster Integration
@app.post("/api/v1/scan/gobuster", response_model=ScanResult)
async def run_gobuster_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Execute Gobuster directory/file scan
    """
    scan_id = str(uuid.uuid4())[:8]
    output_file = SHARED_SCANS / f"gobuster_{scan_id}.txt"

    mode = request.options.get("mode", "dir")
    wordlist = request.options.get("wordlist", "/wordlists/dirb/common.txt")

    cmd_parts = [
        "gobuster",
        mode,
        "-u",
        request.target,
        "-w",
        wordlist,
        "-o",
        str(output_file),
        "-t",
        str(request.options.get("threads", 50)),
    ]

    if "extensions" in request.options and mode == "dir":
        cmd_parts.extend(["-x", request.options["extensions"]])

    scan_info = {
        "scan_id": scan_id,
        "tool": "gobuster",
        "target": request.target,
        "status": "running",
        "start_time": datetime.utcnow(),
        "command": " ".join(cmd_parts),
        "output_file": str(output_file),
    }
    active_scans[scan_id] = scan_info

    background_tasks.add_task(
        execute_docker_scan,
        container_name="zen-gobuster",
        command=cmd_parts,
        scan_id=scan_id,
        output_file=output_file,
    )

    return ScanResult(**scan_info)


# Amass Integration
@app.post("/api/v1/scan/amass", response_model=ScanResult)
async def run_amass_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Execute Amass subdomain enumeration
    """
    scan_id = str(uuid.uuid4())[:8]
    output_file = SHARED_SCANS / f"amass_{scan_id}.json"

    cmd_parts = [
        "amass",
        "enum",
        "-d",
        request.target,
        "-json",
        str(output_file),
        "-active" if request.options.get("active", False) else "-passive",
    ]

    scan_info = {
        "scan_id": scan_id,
        "tool": "amass",
        "target": request.target,
        "status": "running",
        "start_time": datetime.utcnow(),
        "command": " ".join(cmd_parts),
        "output_file": str(output_file),
    }
    active_scans[scan_id] = scan_info

    background_tasks.add_task(
        execute_docker_scan,
        container_name="zen-amass",
        command=cmd_parts,
        scan_id=scan_id,
        output_file=output_file,
    )

    return ScanResult(**scan_info)


# WPScan Integration
@app.post("/api/v1/scan/wpscan", response_model=ScanResult)
async def run_wpscan(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Execute WPScan WordPress vulnerability scan
    """
    scan_id = str(uuid.uuid4())[:8]
    output_file = SHARED_SCANS / f"wpscan_{scan_id}.json"

    cmd_parts = [
        "wpscan",
        "--url",
        request.target,
        "--format",
        "json",
        "-o",
        str(output_file),
        "--random-user-agent",
    ]

    if "api_token" in request.options:
        cmd_parts.extend(["--api-token", request.options["api_token"]])

    if request.options.get("enumerate", True):
        cmd_parts.extend(["-e", "vp,vt,cb,dbe,u,m"])

    scan_info = {
        "scan_id": scan_id,
        "tool": "wpscan",
        "target": request.target,
        "status": "running",
        "start_time": datetime.utcnow(),
        "command": " ".join(cmd_parts),
        "output_file": str(output_file),
    }
    active_scans[scan_id] = scan_info

    background_tasks.add_task(
        execute_docker_scan,
        container_name="zen-wpscan",
        command=cmd_parts,
        scan_id=scan_id,
        output_file=output_file,
    )

    return ScanResult(**scan_info)


# Helper function to execute scans in Docker containers
async def execute_docker_scan(
    container_name: str,
    command: List[str],
    scan_id: str,
    output_file: Path,
    timeout: int = 3600,
):
    """Execute scan command in Docker container"""
    try:
        if not docker_client:
            logger.error("Docker client not available")
            active_scans[scan_id]["status"] = "failed"
            active_scans[scan_id]["error"] = "Docker not available"
            return

        container = docker_client.containers.get(container_name)

        logger.info(f"Starting scan {scan_id} in {container_name}: {' '.join(command)}")

        # Execute command
        exit_code, output = container.exec_run(
            command, workdir="/scans", timeout=timeout
        )

        # Update scan status
        active_scans[scan_id]["status"] = "completed" if exit_code == 0 else "failed"
        active_scans[scan_id]["end_time"] = datetime.utcnow()
        active_scans[scan_id]["exit_code"] = exit_code

        # Read output file if exists
        if output_file.exists():
            try:
                with open(output_file, "r", encoding="utf-8", errors="ignore") as f:
                    active_scans[scan_id]["raw_output"] = f.read()[:10000]  # Limit size
            except Exception as e:
                logger.warning(f"Could not read output file: {e}")

        logger.info(f"Scan {scan_id} completed with exit code {exit_code}")

    except Exception as e:
        logger.error(f"Scan {scan_id} failed: {e}")
        active_scans[scan_id]["status"] = "failed"
        active_scans[scan_id]["error"] = str(e)
        active_scans[scan_id]["end_time"] = datetime.utcnow()


# Status endpoints
@app.get("/api/v1/scan/{scan_id}", response_model=ScanResult)
async def get_scan_status(scan_id: str):
    """Get status of a specific scan"""
    if scan_id not in active_scans:
        raise HTTPException(status_code=404, detail="Scan not found")
    return ScanResult(**active_scans[scan_id])


@app.get("/api/v1/scans", response_model=List[ScanResult])
async def list_scans(
    status: Optional[str] = Query(None, description="Filter by status"),
    tool: Optional[str] = Query(None, description="Filter by tool"),
):
    """List all scans with optional filters"""
    results = list(active_scans.values())

    if status:
        results = [s for s in results if s["status"] == status]
    if tool:
        results = [s for s in results if s["tool"] == tool]

    return [ScanResult(**s) for s in results]


@app.delete("/api/v1/scan/{scan_id}")
async def cancel_scan(scan_id: str):
    """Cancel a running scan"""
    if scan_id not in active_scans:
        raise HTTPException(status_code=404, detail="Scan not found")

    # TODO: Implement scan cancellation
    active_scans[scan_id]["status"] = "cancelled"
    active_scans[scan_id]["end_time"] = datetime.utcnow()

    return {"message": f"Scan {scan_id} cancelled"}


# Results parsing endpoints
@app.get("/api/v1/scan/{scan_id}/results")
async def get_scan_results(scan_id: str, format: str = "json"):
    """
    Get parsed scan results
    """
    if scan_id not in active_scans:
        raise HTTPException(status_code=404, detail="Scan not found")

    scan = active_scans[scan_id]
    output_file = scan.get("output_file")

    if not output_file or not Path(output_file).exists():
        return {"error": "Output file not found"}

    # Parse based on tool type
    parser = get_parser(scan["tool"])
    if parser:
        try:
            results = parser(Path(output_file))
            return {"scan_id": scan_id, "results": results}
        except Exception as e:
            return {"error": f"Failed to parse results: {e}"}

    # Return raw output if no parser available
    with open(output_file, "r", encoding="utf-8", errors="ignore") as f:
        return {"scan_id": scan_id, "raw": f.read()}


def get_parser(tool: str):
    """Get appropriate result parser for tool"""
    parsers = {
        "nmap": parse_nmap_xml,
        "nuclei": parse_nuclei_json,
        "sqlmap": parse_sqlmap_json,
        "wpscan": parse_wpscan_json,
        "amass": parse_amass_json,
    }
    return parsers.get(tool)


def parse_nmap_xml(file_path: Path) -> Dict[str, Any]:
    """Parse Nmap XML output"""
    import xml.etree.ElementTree as ET

    tree = ET.parse(file_path)
    root = tree.getroot()

    hosts = []
    for host in root.findall("host"):
        host_info = {
            "address": (
                host.find("address").get("addr") if host.find("address") else None
            ),
            "status": (
                host.find("status").get("state") if host.find("status") else "unknown"
            ),
            "ports": [],
        }

        ports = host.find("ports")
        if ports:
            for port in ports.findall("port"):
                port_info = {
                    "port": port.get("portid"),
                    "protocol": port.get("protocol"),
                    "state": (
                        port.find("state").get("state")
                        if port.find("state")
                        else "unknown"
                    ),
                    "service": (
                        port.find("service").get("name")
                        if port.find("service")
                        else None
                    ),
                }
                host_info["ports"].append(port_info)

        hosts.append(host_info)

    return {
        "hosts": hosts,
        "scan_info": root.find("scaninfo").attrib if root.find("scaninfo") else {},
    }


def parse_nuclei_json(file_path: Path) -> List[Dict[str, Any]]:
    """Parse Nuclei JSON output"""
    results = []
    with open(file_path, "r") as f:
        for line in f:
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return results


def parse_sqlmap_json(file_path: Path) -> Dict[str, Any]:
    """Parse SQLMap JSON log output"""
    # SQLMap outputs to directory, need to find latest log
    log_file = file_path / "log"
    if log_file.exists():
        with open(log_file, "r") as f:
            return {"log": f.read()}
    return {}


def parse_wpscan_json(file_path: Path) -> Dict[str, Any]:
    """Parse WPScan JSON output"""
    with open(file_path, "r") as f:
        return json.load(f)


def parse_amass_json(file_path: Path) -> List[str]:
    """Parse Amass JSON output"""
    subdomains = []
    with open(file_path, "r") as f:
        for line in f:
            try:
                data = json.loads(line)
                if "name" in data:
                    subdomains.append(data["name"])
            except json.JSONDecodeError:
                continue
    return subdomains


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "docker_available": docker_client is not None,
        "active_scans": len(
            [s for s in active_scans.values() if s["status"] == "running"]
        ),
        "total_scans": len(active_scans),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
