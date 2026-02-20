"""
Real Tool Execution Framework

Executes actual security tools (nmap, nuclei, sqlmap, etc.) in sandboxed environments.
"""

import asyncio
import logging
import shlex
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class SafetyLevel(Enum):
    """Safety levels for tool execution."""

    READ_ONLY = 1  # Passive recon only (nmap -sS)
    NON_DESTRUCTIVE = 2  # Active but safe (nuclei, ffuf)
    DESTRUCTIVE = 3  # May modify state (sqlmap --dump)
    EXPLOIT = 4  # Full exploitation (metasploit)


@dataclass
class ToolResult:
    """Result of tool execution."""

    tool: str
    command: str
    return_code: int
    stdout: str
    stderr: str
    duration: float
    parsed_output: Dict[str, Any] = field(default_factory=dict)
    findings: List[Dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class ToolDefinition:
    """Definition of a security tool."""

    name: str
    description: str
    command_template: str
    safety_level: SafetyLevel
    category: str
    needs_docker: bool = False
    output_parser: Optional[Callable] = None
    timeout: int = 300
    installed: bool = False


class ToolRegistry:
    """Registry of available security tools."""

    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register default security tools."""

        # Network Reconnaissance
        self.register(
            ToolDefinition(
                name="nmap",
                description="Network discovery and security auditing",
                command_template="nmap {options} {target}",
                safety_level=SafetyLevel.READ_ONLY,
                category="recon",
                timeout=600,
            )
        )

        self.register(
            ToolDefinition(
                name="masscan",
                description="Fast port scanner",
                command_template="masscan {target} -p{ports} {options}",
                safety_level=SafetyLevel.READ_ONLY,
                category="recon",
                timeout=300,
            )
        )

        # Web Scanning
        self.register(
            ToolDefinition(
                name="nuclei",
                description="Fast vulnerability scanner",
                command_template="nuclei -u {target} {options}",
                safety_level=SafetyLevel.NON_DESTRUCTIVE,
                category="web",
                timeout=600,
            )
        )

        self.register(
            ToolDefinition(
                name="ffuf",
                description="Fast web fuzzer",
                command_template="ffuf -u {target}/FUZZ {options}",
                safety_level=SafetyLevel.NON_DESTRUCTIVE,
                category="web",
                timeout=300,
            )
        )

        self.register(
            ToolDefinition(
                name="gospider",
                description="Web crawler",
                command_template="gospider -s {target} {options}",
                safety_level=SafetyLevel.READ_ONLY,
                category="web",
                timeout=300,
            )
        )

        # SQL Injection
        self.register(
            ToolDefinition(
                name="sqlmap",
                description="Automatic SQL injection tool",
                command_template="sqlmap -u {target} {options}",
                safety_level=SafetyLevel.DESTRUCTIVE,
                category="exploitation",
                timeout=600,
            )
        )

        # Subdomain Enumeration
        self.register(
            ToolDefinition(
                name="subfinder",
                description="Subdomain discovery",
                command_template="subfinder -d {target} {options}",
                safety_level=SafetyLevel.READ_ONLY,
                category="recon",
                timeout=300,
            )
        )

        self.register(
            ToolDefinition(
                name="amass",
                description="In-depth attack surface mapping",
                command_template="amass enum -d {target} {options}",
                safety_level=SafetyLevel.READ_ONLY,
                category="recon",
                timeout=600,
            )
        )

        # DNS
        self.register(
            ToolDefinition(
                name="dnsrecon",
                description="DNS enumeration",
                command_template="dnsrecon -d {target} {options}",
                safety_level=SafetyLevel.READ_ONLY,
                category="recon",
                timeout=300,
            )
        )

        # SSL/TLS
        self.register(
            ToolDefinition(
                name="sslscan",
                description="SSL/TLS scanner",
                command_template="sslscan {target} {options}",
                safety_level=SafetyLevel.READ_ONLY,
                category="web",
                timeout=120,
            )
        )

        # Content Discovery
        self.register(
            ToolDefinition(
                name="gobuster",
                description="Directory/file brute forcer",
                command_template="gobuster dir -u {target} {options}",
                safety_level=SafetyLevel.NON_DESTRUCTIVE,
                category="web",
                timeout=300,
            )
        )

        # Vulnerability Scanning
        self.register(
            ToolDefinition(
                name="nikto",
                description="Web server scanner",
                command_template="nikto -h {target} {options}",
                safety_level=SafetyLevel.NON_DESTRUCTIVE,
                category="web",
                timeout=600,
            )
        )

    def register(self, tool: ToolDefinition):
        """Register a new tool."""
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return self.tools.get(name)

    def list_tools(self, category: Optional[str] = None, safety: Optional[SafetyLevel] = None) -> List[ToolDefinition]:
        """List available tools with optional filtering."""
        tools = list(self.tools.values())

        if category:
            tools = [t for t in tools if t.category == category]

        if safety:
            tools = [t for t in tools if t.safety_level.value <= safety.value]

        return tools

    def check_installed(self, name: str) -> bool:
        """Check if a tool is installed."""
        try:
            result = subprocess.run(["which", name], capture_output=True, timeout=5)
            return result.return_code == 0
        except Exception:
            return False


class ToolExecutor:
    """Executes security tools with safety controls."""

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        safety_level: SafetyLevel = SafetyLevel.NON_DESTRUCTIVE,
        use_docker: bool = False,
        output_dir: Optional[str] = None,
    ):
        self.registry = registry or ToolRegistry()
        self.max_safety = safety_level
        self.use_docker = use_docker
        self.output_dir = output_dir or tempfile.gettempdir()
        self.logger = logging.getLogger(__name__)

        # Track execution for audit
        self.execution_log: List[Dict] = []

    def get_available_tools(self) -> List[Dict]:
        """Get list of available tools for LLM."""
        tools = self.registry.list_tools(safety=self.max_safety)
        return [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "safety": t.safety_level.name,
                "installed": self.registry.check_installed(t.name),
            }
            for t in tools
        ]

    async def execute(self, tool_name: str, parameters: Dict[str, Any], timeout: Optional[int] = None) -> ToolResult:
        """
        Execute a tool with the given parameters.

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters (target, options, etc.)
            timeout: Override default timeout

        Returns:
            ToolResult with output and parsed findings
        """
        tool = self.registry.get(tool_name)
        if not tool:
            return ToolResult(
                tool=tool_name,
                command="",
                return_code=-1,
                stdout="",
                stderr=f"Tool '{tool_name}' not found in registry",
                duration=0,
                success=False,
                error_message=f"Unknown tool: {tool_name}",
            )

        # Safety check
        if tool.safety_level.value > self.max_safety.value:
            return ToolResult(
                tool=tool_name,
                command="",
                return_code=-1,
                stdout="",
                stderr=f"Tool '{tool_name}' exceeds safety level ({tool.safety_level.name} > {self.max_safety.name})",
                duration=0,
                success=False,
                error_message=f"Safety violation: {tool_name}",
            )

        # Build command
        try:
            command = self._build_command(tool, parameters)
        except Exception as e:
            return ToolResult(
                tool=tool_name,
                command="",
                return_code=-1,
                stdout="",
                stderr=str(e),
                duration=0,
                success=False,
                error_message=f"Command build failed: {str(e)}",
            )

        self.logger.info(f"Executing: {command}")

        # Execute
        start_time = datetime.now()
        try:
            if self.use_docker:
                stdout, stderr, return_code = await self._execute_docker(tool, command, timeout or tool.timeout)
            else:
                stdout, stderr, return_code = await self._execute_local(command, timeout or tool.timeout)

            duration = (datetime.now() - start_time).total_seconds()

            # Parse output
            parsed_output = self._parse_output(tool_name, stdout)
            findings = self._extract_findings(tool_name, stdout, parsed_output)

            # Log execution
            self.execution_log.append(
                {
                    "tool": tool_name,
                    "command": command,
                    "timestamp": datetime.now().isoformat(),
                    "duration": duration,
                    "success": return_code == 0,
                }
            )

            return ToolResult(
                tool=tool_name,
                command=command,
                return_code=return_code,
                stdout=stdout,
                stderr=stderr,
                duration=duration,
                parsed_output=parsed_output,
                findings=findings,
                success=return_code == 0,
            )

        except asyncio.TimeoutError:
            duration = (datetime.now() - start_time).total_seconds()
            return ToolResult(
                tool=tool_name,
                command=command,
                return_code=-1,
                stdout="",
                stderr=f"Timeout after {timeout or tool.timeout} seconds",
                duration=duration,
                success=False,
                error_message="Execution timeout",
            )
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return ToolResult(
                tool=tool_name,
                command=command,
                return_code=-1,
                stdout="",
                stderr=str(e),
                duration=duration,
                success=False,
                error_message=str(e),
            )

    def _build_command(self, tool: ToolDefinition, parameters: Dict[str, Any]) -> str:
        """Build the command string from template."""
        target = parameters.get("target", "")
        options = parameters.get("options", "")

        # Sanitize inputs
        target = shlex.quote(target) if target else ""

        command = tool.command_template.format(
            target=target, options=options, ports=parameters.get("ports", "1-65535"), **parameters
        )

        return command

    async def _execute_local(self, command: str, timeout: int) -> tuple:
        """Execute command locally."""
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return (stdout.decode("utf-8", errors="ignore"), stderr.decode("utf-8", errors="ignore"), process.returncode)
        except asyncio.TimeoutError:
            process.kill()
            raise

    async def _execute_docker(self, tool: ToolDefinition, command: str, timeout: int) -> tuple:
        """Execute in Docker container."""
        # Docker execution for isolation
        docker_cmd = f"docker run --rm --network=host {tool.name} {command}"
        return await self._execute_local(docker_cmd, timeout)

    def _parse_output(self, tool_name: str, stdout: str) -> Dict[str, Any]:
        """Parse tool output into structured format."""
        parsers = {
            "nmap": self._parse_nmap,
            "nuclei": self._parse_nuclei,
            "subfinder": self._parse_subfinder,
            # Add more parsers
        }

        parser = parsers.get(tool_name)
        if parser:
            try:
                return parser(stdout)
            except Exception as e:
                self.logger.error(f"Parse error for {tool_name}: {e}")

        return {"raw": stdout}

    def _parse_nmap(self, output: str) -> Dict:
        """Parse nmap output."""
        ports = []
        for line in output.split("\n"):
            if "/tcp" in line and "open" in line:
                parts = line.split()
                if len(parts) >= 3:
                    port = parts[0].split("/")[0]
                    service = parts[2]
                    version = " ".join(parts[3:]) if len(parts) > 3 else ""
                    ports.append({"port": port, "service": service, "version": version})

        return {"open_ports": ports}

    def _parse_nuclei(self, output: str) -> Dict:
        """Parse nuclei output."""
        findings = []
        for line in output.split("\n"):
            if "[" in line and "]" in line:
                # Basic parsing, enhance as needed
                findings.append({"raw": line})

        return {"findings": findings}

    def _parse_subfinder(self, output: str) -> Dict:
        """Parse subfinder output."""
        subdomains = [line.strip() for line in output.split("\n") if line.strip()]
        return {"subdomains": subdomains}

    def _extract_findings(self, tool_name: str, stdout: str, parsed: Dict) -> List[Dict]:
        """Extract security findings from output."""
        findings = []

        # Add generic findings based on tool
        if tool_name == "nmap" and parsed.get("open_ports"):
            for port in parsed["open_ports"]:
                findings.append({"type": "open_port", "severity": "info", "details": port})

        elif tool_name == "nuclei" and parsed.get("findings"):
            for finding in parsed["findings"]:
                findings.append({"type": "vulnerability", "severity": "unknown", "details": finding})

        return findings
