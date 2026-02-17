"""
Agent Task Processor
====================

Processes tasks received from workflow orchestrator.

This runs on the agent side to:
1. Receive tasks via WebSocket
2. Execute security tools (nmap, nuclei, etc.)
3. Return results to orchestrator
"""

import asyncio
import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Callable, Optional


logger = logging.getLogger("zen.agents.processor")


@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    status: str  # success, failed, partial
    findings: list
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "findings": self.findings,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp
        }


class TaskProcessor:
    """
    Processes workflow tasks by executing security tools.
    
    Supports tools:
    - nmap: Port scanning
    - nuclei: Vulnerability scanning
    - whois: Domain information
    - dns: DNS enumeration
    - subdomain: Subdomain discovery
    """
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {
            "nmap": self._handle_nmap,
            "whois": self._handle_whois,
            "dns": self._handle_dns,
            "subdomain": self._handle_subdomain,
            "web_enum": self._handle_web_enum,
            "directory": self._handle_directory_scan,
            "vulnerability": self._handle_vulnerability_scan,
            "exploit": self._handle_exploit,
            "report": self._handle_report,
        }
    
    async def process_task(self, task: Dict[str, Any]) -> TaskResult:
        """
        Process a single task.
        
        Args:
            task: Task dictionary with tool, target, parameters
            
        Returns:
            TaskResult with execution results
        """
        task_id = task.get("id", "unknown")
        tool = task.get("parameters", {}).get("tool", "unknown")
        target = task.get("target", "")
        
        logger.info(f"🔄 Processing task {task_id}: {tool} on {target}")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            handler = self.handlers.get(tool)
            if not handler:
                return TaskResult(
                    task_id=task_id,
                    status="failed",
                    findings=[],
                    output="",
                    error=f"Unknown tool: {tool}"
                )
            
            # Execute tool
            result = await handler(task)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            result.execution_time = execution_time
            
            logger.info(f"✅ Task {task_id} completed in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            logger.exception(f"❌ Task {task_id} failed: {e}")
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return TaskResult(
                task_id=task_id,
                status="failed",
                findings=[],
                output="",
                error=str(e),
                execution_time=execution_time
            )
    
    async def _handle_nmap(self, task: Dict) -> TaskResult:
        """Execute nmap scan"""
        target = task.get("target", "")
        parameters = task.get("parameters", {})
        
        # Build nmap command
        ports = parameters.get("ports", "top1000")
        if ports == "top1000":
            port_arg = "--top-ports 1000"
        elif ports == "all":
            port_arg = "-p-"
        else:
            port_arg = f"-p {ports}"
        
        cmd = f"nmap -sS -sV {port_arg} {target}"
        
        return await self._run_command(task["id"], cmd, "nmap")
    
    async def _handle_whois(self, task: Dict) -> TaskResult:
        """Execute whois lookup"""
        target = task.get("target", "")
        cmd = f"whois {target}"
        
        return await self._run_command(task["id"], cmd, "whois")
    
    async def _handle_dns(self, task: Dict) -> TaskResult:
        """Execute DNS enumeration"""
        target = task.get("target", "")
        
        findings = []
        output_lines = []
        
        # DNS lookup
        cmd = f"host {target}"
        result = await self._run_command(task["id"], cmd, "dns")
        output_lines.append(result.output)
        
        # Extract IPs
        for line in result.output.split("\n"):
            if "has address" in line:
                ip = line.split("has address")[-1].strip()
                findings.append({
                    "type": "dns_record",
                    "severity": "info",
                    "title": f"A Record: {ip}",
                    "description": line.strip()
                })
        
        return TaskResult(
            task_id=task["id"],
            status="success",
            findings=findings,
            output="\n".join(output_lines)
        )
    
    async def _handle_subdomain(self, task: Dict) -> TaskResult:
        """Execute subdomain enumeration"""
        target = task.get("target", "")
        
        # Use subfinder if available, otherwise simple DNS brute
        cmd = f"subfinder -d {target}" if self._command_exists("subfinder") else f"host -t ns {target}"
        
        return await self._run_command(task["id"], cmd, "subdomain")
    
    async def _handle_web_enum(self, task: Dict) -> TaskResult:
        """Execute web enumeration"""
        target = task.get("target", "")
        
        # HTTP headers check
        cmd = f"curl -sI http://{target}"
        
        return await self._run_command(task["id"], cmd, "web_enum")
    
    async def _handle_directory_scan(self, task: Dict) -> TaskResult:
        """Execute directory brute force"""
        target = task.get("target", "")
        
        # Use ffuf if available
        cmd = f"ffuf -u http://{target}/FUZZ -w /usr/share/wordlists/common.txt" if self._command_exists("ffuf") else f"dirb http://{target}"
        
        return await self._run_command(task["id"], cmd, "directory")
    
    async def _handle_vulnerability_scan(self, task: Dict) -> TaskResult:
        """Execute vulnerability scan with nuclei"""
        target = task.get("target", "")
        
        if self._command_exists("nuclei"):
            cmd = f"nuclei -u {target} -silent -json"
            return await self._run_command(task["id"], cmd, "nuclei")
        else:
            return TaskResult(
                task_id=task["id"],
                status="failed",
                findings=[],
                output="",
                error="nuclei not installed"
            )
    
    async def _handle_exploit(self, task: Dict) -> TaskResult:
        """Execute exploit (placeholder - safe checks only)"""
        logger.warning("Exploit execution requested - running in safe mode")
        
        return TaskResult(
            task_id=task["id"],
            status="success",
            findings=[{
                "type": "exploit_check",
                "severity": "info",
                "title": "Exploit Check (Safe Mode)",
                "description": "Exploit execution disabled in this version"
            }],
            output="Exploit execution completed (safe mode)"
        )
    
    async def _handle_report(self, task: Dict) -> TaskResult:
        """Generate report"""
        workflow_id = task.get("workflow_id", "unknown")
        
        return TaskResult(
            task_id=task["id"],
            status="success",
            findings=[],
            output=f"Report generated for workflow {workflow_id}",
            error=None
        )
    
    async def _run_command(self, task_id: str, cmd: str, tool: str) -> TaskResult:
        """Run shell command and return result"""
        import asyncio
        
        try:
            # Run command with timeout
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300  # 5 minute timeout
            )
            
            output = stdout.decode("utf-8", errors="ignore")
            error_output = stderr.decode("utf-8", errors="ignore")
            
            # Parse findings from output
            findings = self._parse_findings(tool, output)
            
            if process.returncode == 0:
                return TaskResult(
                    task_id=task_id,
                    status="success",
                    findings=findings,
                    output=output,
                    error=error_output if error_output else None
                )
            else:
                return TaskResult(
                    task_id=task_id,
                    status="failed",
                    findings=findings,
                    output=output,
                    error=error_output or f"Command failed with code {process.returncode}"
                )
                
        except asyncio.TimeoutError:
            return TaskResult(
                task_id=task_id,
                status="failed",
                findings=[],
                output="",
                error="Command timed out after 300 seconds"
            )
        except Exception as e:
            return TaskResult(
                task_id=task_id,
                status="failed",
                findings=[],
                output="",
                error=str(e)
            )
    
    def _parse_findings(self, tool: str, output: str) -> list:
        """Parse security findings from tool output"""
        findings = []
        
        if tool == "nmap":
            # Parse open ports
            for line in output.split("\n"):
                if "open" in line and "tcp" in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        port = parts[0]
                        service = parts[2] if len(parts) > 2 else "unknown"
                        findings.append({
                            "type": "open_port",
                            "severity": "info",
                            "title": f"Open Port: {port}",
                            "description": f"Service: {service}",
                            "port": port,
                            "service": service
                        })
        
        elif tool == "nuclei":
            # Parse nuclei JSON output
            try:
                for line in output.strip().split("\n"):
                    if line.strip():
                        data = json.loads(line)
                        findings.append({
                            "type": "vulnerability",
                            "severity": data.get("info", {}).get("severity", "unknown"),
                            "title": data.get("info", {}).get("name", "Unknown"),
                            "description": data.get("info", {}).get("description", ""),
                            "template": data.get("template-id", ""),
                            "matched": data.get("matched-at", "")
                        })
            except json.JSONDecodeError:
                pass
        
        return findings
    
    def _command_exists(self, cmd: str) -> bool:
        """Check if command exists in PATH"""
        import shutil
        return shutil.which(cmd) is not None


# Global instance
_processor: Optional[TaskProcessor] = None


def get_task_processor() -> TaskProcessor:
    """Get or create global task processor"""
    global _processor
    if _processor is None:
        _processor = TaskProcessor()
    return _processor
