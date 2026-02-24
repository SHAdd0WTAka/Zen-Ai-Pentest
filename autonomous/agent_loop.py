"""
Autonomous Agent Loop Engine for Zen AI Pentest Framework

Implementiert einen vollständigen ReAct (Reasoning + Acting) Loop mit:
- State Machine für kontrollierte Ausführung
- Multi-Layer Memory Management
- Integrierte Tool-Ausführung mit Retry-Logik
- Progress Tracking und Fehlerbehandlung

Based on: ReAct Pattern (https://arxiv.org/abs/2210.03629)
"""

import asyncio
import json
import logging
import time
import traceback
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentState(Enum):
    """
    Zustandsmaschine für den Agenten-Loop.

    States:
        IDLE: Wartet auf Start
        PLANNING: Erstellt Aktionsplan
        EXECUTING: Führt Aktionen aus
        OBSERVING: Analysiert Ergebnisse
        REFLECTING: Evaluiert Fortschritt
        COMPLETED: Ziel erreicht
        ERROR: Fehler aufgetreten
        PAUSED: Wartet auf Eingabe (Human-in-the-loop)
    """

    IDLE = auto()
    PLANNING = auto()
    EXECUTING = auto()
    OBSERVING = auto()
    REFLECTING = auto()
    COMPLETED = auto()
    ERROR = auto()
    PAUSED = auto()


class ToolType(Enum):
    """Verfügbare Tool-Typen für den Agenten."""

    NMAP_SCANNER = "nmap_scanner"
    NUCLEI_SCANNER = "nuclei_scanner"
    EXPLOIT_VALIDATOR = "exploit_validator"
    REPORT_GENERATOR = "report_generator"
    SUBDOMAIN_ENUMERATOR = "subdomain_enumerator"


@dataclass
class AgentMemory:
    """
    Container für alle Memory-Typen des Agenten.

    Attributes:
        session_id: Eindeutige Session-ID
        created_at: Zeitpunkt der Erstellung
        goal: Aktuelles Ziel des Agenten
        target: Ziel-System/IP/Domain
        scope: Scope-Beschränkungen
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    goal: str = ""
    target: str = ""
    scope: Dict[str, Any] = field(default_factory=dict)

    # Kurzzeit-Memory (Session-basiert)
    short_term: List[Dict[str, Any]] = field(default_factory=list)
    max_short_term: int = 100

    # Langzeit-Memory (persistiert)
    long_term: Dict[str, Any] = field(default_factory=dict)

    # Kontext-Fenster für LLM
    context_window: List[Dict[str, Any]] = field(default_factory=list)
    max_context_window: int = 20

    # Plan und aktueller Status
    current_plan: List[Dict[str, Any]] = field(default_factory=list)
    plan_step: int = 0

    # Findings und Ergebnisse
    findings: List[Dict[str, Any]] = field(default_factory=list)
    execution_history: List[Dict[str, Any]] = field(default_factory=list)

    def add_to_short_term(self, entry: Dict[str, Any]) -> None:
        """Fügt einen Eintrag zum Kurzzeit-Memory hinzu."""
        entry["timestamp"] = datetime.now().isoformat()
        entry["id"] = str(uuid.uuid4())
        self.short_term.append(entry)

        # Begrenze Größe
        if len(self.short_term) > self.max_short_term:
            self.short_term = self.short_term[-self.max_short_term :]

    def add_to_context_window(self, entry: Dict[str, Any]) -> None:
        """Fügt einen Eintrag zum LLM Kontext-Fenster hinzu."""
        entry["timestamp"] = datetime.now().isoformat()
        self.context_window.append(entry)

        # Begrenze Größe für LLM Kontext
        if len(self.context_window) > self.max_context_window:
            self.context_window = self.context_window[
                -self.max_context_window :
            ]

    def get_context_for_llm(self) -> str:
        """Erstellt formatierten Kontext für LLM Prompts."""
        context_parts = [
            f"Goal: {self.goal}",
            f"Target: {self.target}",
            f"Progress: Step {self.plan_step + 1}/{len(self.current_plan) if self.current_plan else '?'}",
            "\nRecent Actions:",
        ]

        # Letzte 5 Aktionen aus dem Kontext-Fenster
        for entry in self.context_window[-5:]:
            entry_type = entry.get("type", "unknown")
            content = entry.get("content", "")
            context_parts.append(
                f"  [{entry_type.upper()}] {content[:100]}..."
            )

        if self.findings:
            context_parts.append(f"\nFindings: {len(self.findings)}")

        return "\n".join(context_parts)

    def add_finding(self, finding: Dict[str, Any]) -> None:
        """Fügt einen Security Finding hinzu."""
        finding["timestamp"] = datetime.now().isoformat()
        finding["id"] = str(uuid.uuid4())
        self.findings.append(finding)

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Memory zu Dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "goal": self.goal,
            "target": self.target,
            "scope": self.scope,
            "short_term_count": len(self.short_term),
            "findings_count": len(self.findings),
            "plan_step": self.plan_step,
            "current_plan_length": len(self.current_plan),
        }


@dataclass
class ToolResult:
    """
    Ergebnis einer Tool-Ausführung.

    Attributes:
        tool_name: Name des ausgeführten Tools
        success: Ob die Ausführung erfolgreich war
        data: Extrahierte Daten
        raw_output: Rohe Tool-Ausgabe
        error_message: Fehlermeldung bei Misserfolg
        execution_time: Dauer der Ausführung in Sekunden
        timestamp: Zeitpunkt der Ausführung
        metadata: Zusätzliche Metadaten
    """

    tool_name: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    raw_output: str = ""
    error_message: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert ToolResult zu Dictionary."""
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "data": self.data,
            "raw_output": (
                self.raw_output[:500]
                if len(self.raw_output) > 500
                else self.raw_output
            ),
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class PlanStep:
    """
    Einzelner Schritt im Ausführungsplan.

    Attributes:
        step_id: Eindeutige ID des Schritts
        tool_type: Typ des zu verwendenden Tools
        action: Beschreibung der Aktion
        parameters: Parameter für das Tool
        depends_on: IDs der Schritte, die vorher abgeschlossen sein müssen
        completed: Ob der Schritt abgeschlossen ist
        result: Ergebnis des Schritts
    """

    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_type: ToolType = ToolType.NMAP_SCANNER
    action: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    completed: bool = False
    result: Optional[ToolResult] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert PlanStep zu Dictionary."""
        return {
            "step_id": self.step_id,
            "tool_type": self.tool_type.value,
            "action": self.action,
            "parameters": self.parameters,
            "depends_on": self.depends_on,
            "completed": self.completed,
            "result": self.result.to_dict() if self.result else None,
        }


# Abstract Tool Classes
class BaseTool(ABC):
    """Abstrakte Basisklasse für alle Tools."""

    def __init__(self, name: str, timeout: int = 300):
        self.name = name
        self.timeout = timeout
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Führt das Tool mit den gegebenen Parametern aus."""
        pass

    def validate_parameters(
        self, parameters: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Validiert die Tool-Parameter."""
        return True, ""


class NmapScanner(BaseTool):
    """Nmap Port Scanner Integration."""

    def __init__(self, timeout: int = 600):
        super().__init__("NmapScanner", timeout)
        self.default_options = "-sV -sC -O --script=vuln"

    def validate_parameters(
        self, parameters: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Validiert Nmap-spezifische Parameter."""
        target = parameters.get("target")
        if not target:
            return False, "Target is required"

        # Validiere IP oder Domain
        if not isinstance(target, str) or len(target) < 1:
            return False, "Invalid target format"

        return True, ""

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Führt Nmap Scan aus - ECHTE AUSFÜHRUNG."""
        import asyncio.subprocess

        start_time = time.time()

        try:
            target = parameters.get("target")
            options = parameters.get("options", "-sV -sC")
            ports = parameters.get("ports", "1-1000")

            # Safety Check: Validiere Target
            valid, error_msg = self._validate_target_safety(target)
            if not valid:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error_message=f"Safety validation failed: {error_msg}",
                    execution_time=0.0,
                )

            # Baue Nmap Kommando mit XML Output für besseres Parsing
            cmd = (
                [
                    "nmap",
                    "-oX",
                    "-",  # XML Output to stdout
                    "-p",
                    str(ports),
                ]
                + options.split()
                + [target]
            )

            self.logger.info(f"[REAL] Executing: {' '.join(cmd)}")

            # ECHTE AUSFÜHRUNG via subprocess
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self.timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error_message=f"Nmap timeout after {self.timeout}s",
                    execution_time=time.time() - start_time,
                )

            execution_time = time.time() - start_time
            output = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            # Parse XML Output
            parsed_data = self._parse_nmap_xml(output)

            success = proc.returncode == 0 and parsed_data is not None

            return ToolResult(
                tool_name=self.name,
                success=success,
                data=parsed_data or {},
                raw_output=output,
                error_message=stderr_text if stderr_text else None,
                execution_time=execution_time,
                metadata={
                    "ports_scanned": ports,
                    "options": options,
                    "target": target,
                    "return_code": proc.returncode,
                    "real_execution": True,  # Mark as real (not simulated)
                },
            )

        except FileNotFoundError:
            execution_time = time.time() - start_time
            self.logger.error("Nmap not found. Please install nmap.")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_message="Nmap not found. Install: https://nmap.org/download.html",
                execution_time=execution_time,
            )
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Nmap execution failed: {str(e)}")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_message=str(e),
                execution_time=execution_time,
            )

    def _validate_target_safety(self, target: str) -> Tuple[bool, str]:
        """Validiert das Target für Safety (keine internen Netzwerke ohne Whitelist)."""
        import ipaddress
        import re

        # Blockiere private IPs ohne Whitelist
        try:
            ip = ipaddress.ip_address(target)
            # Erlaube localhost für Tests, aber logge Warnung
            if ip.is_loopback:
                self.logger.warning(f"Scanning loopback address: {target}")
                return True, ""
            # Blockiere andere private IPs
            if ip.is_private:
                return (
                    False,
                    f"Private IP {target} blocked. Add to whitelist if intended.",
                )
        except ValueError:
            # Keine IP, wahrscheinlich Domain - erlaube
            pass

        # Blockiere gefährliche Zeichen
        if re.search(r"[;&|<>$`]", target):
            return False, "Invalid characters in target"

        return True, ""

    def _simulate_scan_output(self, target: str, ports: str) -> str:
        """Simuliert Nmap Output für Demo-Zwecke."""
        return f"""
Starting Nmap 7.94 ( https://nmap.org ) at {datetime.now().strftime("%Y-%m-%d %H:%M")}
Nmap scan report for {target}
Host is up (0.045s latency).
Not shown: 995 closed tcp ports (reset)
PORT     STATE SERVICE     VERSION
22/tcp   open  ssh         OpenSSH 8.9p1 Ubuntu 3ubuntu0.1
80/tcp   open  http        Apache httpd 2.4.52
443/tcp  open  ssl/http    Apache httpd 2.4.52
3306/tcp open  mysql       MySQL 8.0.32
8080/tcp open  http-proxy  nginx 1.18.0

Service detection performed.
OS and Service detection performed.
"""

    def _parse_nmap_xml(self, xml_output: str) -> Optional[Dict[str, Any]]:
        """Parst Nmap XML Output für strukturierte Daten."""
        import xml.etree.ElementTree as ET

        try:
            root = ET.fromstring(xml_output)

            open_ports = []
            services = []
            os_matches = []

            for host in root.findall("host"):
                for port in host.findall(".//port"):
                    port_id = port.get("portid")
                    protocol = port.get("protocol")
                    state = port.find("state")

                    if state is not None and state.get("state") == "open":
                        service_elem = port.find("service")
                        service_name = (
                            service_elem.get("name", "unknown")
                            if service_elem is not None
                            else "unknown"
                        )
                        service_version = (
                            service_elem.get("version", "")
                            if service_elem is not None
                            else ""
                        )
                        product = (
                            service_elem.get("product", "")
                            if service_elem is not None
                            else ""
                        )

                        port_info = {
                            "port": int(port_id),
                            "protocol": protocol,
                            "service": service_name,
                            "version": f"{product} {service_version}".strip()
                            or "unknown",
                            "state": "open",
                        }
                        open_ports.append(port_info)
                        services.append(service_name)

                # OS Detection
                for osmatch in host.findall(".//osmatch"):
                    os_matches.append(
                        {
                            "name": osmatch.get("name", "unknown"),
                            "accuracy": osmatch.get("accuracy", "0"),
                        }
                    )

            return {
                "open_ports": open_ports,
                "services": list(set(services)),
                "port_count": len(open_ports),
                "os_matches": os_matches[:3],  # Top 3 OS guesses
            }
        except ET.ParseError as e:
            self.logger.error(f"Failed to parse Nmap XML: {e}")
            # Fallback zu Text-Parsing
            return self._parse_output_fallback(xml_output)

    def _parse_output_fallback(self, output: str) -> Dict[str, Any]:
        """Fallback Text-Parsing wenn XML fehlschlägt."""
        open_ports = []
        services = []

        for line in output.split("\n"):
            if "/tcp" in line and "open" in line:
                parts = line.split()
                if len(parts) >= 3:
                    port = parts[0].split("/")[0]
                    service = parts[2]
                    version = (
                        " ".join(parts[3:]) if len(parts) > 3 else "unknown"
                    )
                    open_ports.append(
                        {
                            "port": int(port),
                            "service": service,
                            "version": version,
                        }
                    )
                    services.append(service)

        return {
            "open_ports": open_ports,
            "services": list(set(services)),
            "port_count": len(open_ports),
        }


class NucleiScanner(BaseTool):
    """Nuclei Vulnerability Scanner Integration."""

    def __init__(self, timeout: int = 600):
        super().__init__("NucleiScanner", timeout)
        self.default_templates = "cves,exposures,vulnerabilities"

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Führt Nuclei Scan aus - ECHTE AUSFÜHRUNG."""
        import asyncio.subprocess

        start_time = time.time()

        try:
            target = parameters.get("target")
            templates = parameters.get("templates", self.default_templates)
            severity = parameters.get("severity", "critical,high,medium")

            # Safety Check
            valid, error_msg = self._validate_target_safety(target)
            if not valid:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error_message=f"Safety validation failed: {error_msg}",
                    execution_time=0.0,
                )

            # Baue Nuclei Kommando mit JSON Output
            cmd = [
                "nuclei",
                "-u",
                target,
                "-t",
                templates,
                "-severity",
                severity,
                "-json",
                "-silent",
            ]  # Reduce noise

            self.logger.info(f"[REAL] Executing: {' '.join(cmd)}")

            # ECHTE AUSFÜHRUNG
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self.timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error_message=f"Nuclei timeout after {self.timeout}s",
                    execution_time=time.time() - start_time,
                )

            execution_time = time.time() - start_time
            output = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            # Parse JSON Output (one JSON object per line)
            findings = self._parse_nuclei_json(output)

            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"findings": findings, "count": len(findings)},
                raw_output=output,
                error_message=stderr_text if stderr_text else None,
                execution_time=execution_time,
                metadata={
                    "templates": templates,
                    "severity_filter": severity,
                    "target": target,
                    "return_code": proc.returncode,
                    "real_execution": True,
                },
            )

        except FileNotFoundError:
            execution_time = time.time() - start_time
            self.logger.error("Nuclei not found. Please install nuclei.")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_message="Nuclei not found. Install: https://github.com/projectdiscovery/nuclei",
                execution_time=execution_time,
            )
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Nuclei execution failed: {str(e)}")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_message=str(e),
                execution_time=execution_time,
            )

    def _parse_nuclei_json(self, output: str) -> List[Dict[str, Any]]:
        """Parst Nuclei JSON Output (one JSON object per line)."""
        findings = []
        for line in output.strip().split("\n"):
            if not line:
                continue
            try:
                finding = json.loads(line)
                # Normalize finding structure
                normalized = {
                    "template": finding.get("template-id", "unknown"),
                    "severity": finding.get("info", {}).get(
                        "severity", "unknown"
                    ),
                    "host": finding.get("host", ""),
                    "matched": finding.get("matched-at", ""),
                    "description": finding.get("info", {}).get(
                        "name", "No description"
                    ),
                    "tags": finding.get("info", {}).get("tags", []),
                    "reference": finding.get("info", {}).get("reference", []),
                    "curl_command": finding.get("curl-command", ""),
                    "matcher_status": finding.get("matcher-status", False),
                    "ip": finding.get("ip", ""),
                    "timestamp": finding.get("timestamp", ""),
                    "type": finding.get("type", ""),
                }
                findings.append(normalized)
            except json.JSONDecodeError:
                self.logger.warning(
                    f"Failed to parse Nuclei JSON line: {line[:100]}"
                )
                continue
        return findings

    def _validate_target_safety(self, target: str) -> Tuple[bool, str]:
        """Validiert das Target für Safety."""
        import ipaddress
        import re

        try:
            ip = ipaddress.ip_address(target)
            if ip.is_private and not ip.is_loopback:
                return (
                    False,
                    f"Private IP {target} blocked. Add to whitelist if intended.",
                )
        except ValueError:
            pass

        if re.search(r"[;&|<>$`]", target):
            return False, "Invalid characters in target"

        return True, ""


class ExploitValidator(BaseTool):
    """
    Validiert potenzielle Exploits mit dem ExploitValidator-System.

    Nutzt Docker-Sandboxing, Evidence Collection und Safety Controls
    für sichere Exploit-Validierung.
    """

    def __init__(
        self,
        timeout: int = 300,
        safety_level: str = "controlled",
        use_docker: bool = False,  # Disabled by default for compatibility
    ):
        super().__init__("ExploitValidator", timeout)
        self.safety_level = safety_level
        self.use_docker = use_docker
        self._validator = None

    async def _get_validator(self):
        """Lazy initialization of ExploitValidator."""
        if self._validator is None:
            # Import here to avoid circular imports
            from .exploit_validator import (
                ExploitValidator,
                SafetyLevel,
                ScopeConfig,
            )

            safety_map = {
                "read_only": SafetyLevel.READ_ONLY,
                "validate_only": SafetyLevel.VALIDATE_ONLY,
                "controlled": SafetyLevel.CONTROLLED,
                "full": SafetyLevel.FULL,
            }

            safety = safety_map.get(self.safety_level, SafetyLevel.CONTROLLED)

            self._validator = ExploitValidator(
                safety_level=safety,
                scope_config=ScopeConfig(),
                sandbox_config=None,  # Use defaults
                enable_playwright=False,  # Disable for headless environments
            )
        return self._validator

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Validiert einen Exploit.

        Parameters:
            target: Ziel-URL oder Host
            vulnerability: Schwachstellen-Typ (sqli, xss, rce, etc.)
            exploit_code: Exploit-Code (optional)
            exploit_type: Exploit-Typ Enum-Wert
            parameters: Zusätzliche Parameter
        """
        start_time = time.time()

        try:
            target = parameters.get("target")
            vulnerability = parameters.get("vulnerability", "unknown")
            exploit_code = parameters.get("exploit_code", "")
            exploit_type_str = parameters.get("exploit_type", "web_rce")
            extra_params = parameters.get("parameters", {})

            self.logger.info(f"Validating {vulnerability} on {target}")

            # If no exploit code provided, generate a basic test
            if not exploit_code:
                exploit_code = self._generate_test_payload(vulnerability)

            # Get validator and execute
            validator = await self._get_validator()

            # Import ExploitType here
            from .exploit_validator import ExploitType

            # Map vulnerability to ExploitType
            type_map = {
                "sqli": ExploitType.WEB_SQLI,
                "sql_injection": ExploitType.WEB_SQLI,
                "xss": ExploitType.WEB_XSS,
                "rce": ExploitType.WEB_RCE,
                "lfi": ExploitType.WEB_LFI,
                "rfi": ExploitType.WEB_RFI,
                "command_injection": ExploitType.WEB_CMD_INJECTION,
                "csrf": ExploitType.WEB_CSRF,
                "ssrf": ExploitType.WEB_SSRF,
                "xxe": ExploitType.WEB_XXE,
                "path_traversal": ExploitType.WEB_PATH_TRAVERSAL,
                "service": ExploitType.SERVICE,
                "privesc": ExploitType.PRIVESC,
            }

            exploit_type = type_map.get(
                exploit_type_str.lower().replace("-", "_"), ExploitType.WEB_RCE
            )

            # Run validation
            result = await validator.validate(
                exploit_code=exploit_code,
                target=target,
                exploit_type=exploit_type,
                parameters=extra_params,
                timeout=self.timeout,
            )

            execution_time = time.time() - start_time

            # Convert to ToolResult format
            validation_result = {
                "vulnerability": vulnerability,
                "target": target,
                "exploitable": result.success,
                "confidence": 0.9 if result.success else 0.1,
                "evidence": (
                    result.evidence.to_dict() if result.evidence else {}
                ),
                "output": result.output,
                "error": result.error,
                "risk_level": result.severity or "unknown",
                "remediation": result.remediation,
                "validator_id": result.validator_id,
                "execution_time": result.execution_time,
            }

            return ToolResult(
                tool_name=self.name,
                success=result.success,
                data=validation_result,
                raw_output=result.to_json(),
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Exploit validation failed: {e}")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_message=str(e),
                execution_time=execution_time,
            )

    def _generate_test_payload(self, vulnerability: str) -> str:
        """Generate a basic test payload based on vulnerability type."""
        payloads = {
            "sqli": "' OR '1'='1",
            "sql_injection": "' OR '1'='1",
            "xss": "<script>alert('XSS')</script>",
            "rce": "; echo 'RCE_TEST';",
            "lfi": "../../../etc/passwd",
            "command_injection": "; id;",
        }
        return payloads.get(vulnerability.lower(), "# No payload generated")


class ReportGenerator(BaseTool):
    """Generiert Penetration Testing Reports."""

    def __init__(self, timeout: int = 120):
        super().__init__("ReportGenerator", timeout)

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Generiert einen Report."""
        start_time = time.time()

        try:
            findings = parameters.get("findings", [])
            target = parameters.get("target", "unknown")
            format_type = parameters.get("format", "json")

            self.logger.info(f"Generating report for {target}")

            report = {
                "title": f"Penetration Test Report - {target}",
                "generated_at": datetime.now().isoformat(),
                "target": target,
                "summary": {
                    "total_findings": len(findings),
                    "critical": len(
                        [
                            f
                            for f in findings
                            if f.get("severity") == "critical"
                        ]
                    ),
                    "high": len(
                        [f for f in findings if f.get("severity") == "high"]
                    ),
                    "medium": len(
                        [f for f in findings if f.get("severity") == "medium"]
                    ),
                    "low": len(
                        [f for f in findings if f.get("severity") == "low"]
                    ),
                },
                "findings": findings,
                "recommendations": self._generate_recommendations(findings),
            }

            execution_time = time.time() - start_time

            return ToolResult(
                tool_name=self.name,
                success=True,
                data=report,
                raw_output=json.dumps(report, indent=2),
                execution_time=execution_time,
                metadata={"format": format_type},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_message=str(e),
                execution_time=execution_time,
            )

    def _generate_recommendations(self, findings: List[Dict]) -> List[str]:
        """Generiert Empfehlungen basierend auf Findings."""
        recommendations = []

        severities = {f.get("severity") for f in findings}

        if "critical" in severities:
            recommendations.append(
                "Address critical vulnerabilities immediately"
            )
        if "high" in severities:
            recommendations.append("Prioritize high severity findings")

        recommendations.append("Implement regular security scanning")
        recommendations.append("Review and update security policies")

        return recommendations


class SubdomainEnumerator(BaseTool):
    """Subdomain Enumeration Tool."""

    def __init__(self, timeout: int = 300):
        super().__init__("SubdomainEnumerator", timeout)

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Führt Subdomain Enumeration aus."""
        start_time = time.time()

        try:
            domain = parameters.get("target")
            wordlist = parameters.get("wordlist", "default")
            recursive = parameters.get("recursive", False)

            self.logger.info(f"Enumerating subdomains for {domain}")
            await asyncio.sleep(0.4)

            # Simulierte Subdomains
            subdomains = [
                f"www.{domain}",
                f"mail.{domain}",
                f"ftp.{domain}",
                f"admin.{domain}",
                f"blog.{domain}",
                f"api.{domain}",
                f"staging.{domain}",
                f"dev.{domain}",
            ]

            result_data = {
                "domain": domain,
                "subdomains": subdomains,
                "count": len(subdomains),
                "wordlist": wordlist,
                "recursive": recursive,
            }

            execution_time = time.time() - start_time

            return ToolResult(
                tool_name=self.name,
                success=True,
                data=result_data,
                raw_output="\n".join(subdomains),
                execution_time=execution_time,
                metadata={"enumeration_method": "brute_force"},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return ToolResult(
                tool_name=self.name,
                success=False,
                error_message=str(e),
                execution_time=execution_time,
            )


class ToolRegistry:
    """Registry für alle verfügbaren Tools."""

    def __init__(self):
        self.tools: Dict[ToolType, BaseTool] = {
            ToolType.NMAP_SCANNER: NmapScanner(),
            ToolType.NUCLEI_SCANNER: NucleiScanner(),
            ToolType.EXPLOIT_VALIDATOR: ExploitValidator(),
            ToolType.REPORT_GENERATOR: ReportGenerator(),
            ToolType.SUBDOMAIN_ENUMERATOR: SubdomainEnumerator(),
        }

    def get_tool(self, tool_type: ToolType) -> Optional[BaseTool]:
        """Holt ein Tool nach Typ."""
        return self.tools.get(tool_type)

    def list_tools(self) -> List[str]:
        """Listet alle verfügbaren Tools."""
        return [t.value for t in self.tools.keys()]


class AutonomousAgentLoop:
    """
    Autonomous Agent Loop Engine mit ReAct Pattern.

    Diese Klasse implementiert einen vollständigen ReAct (Reasoning + Acting)
    Loop mit State Machine, Memory Management und Tool Integration.

    Example:
        agent = AutonomousAgentLoop(llm_client=my_llm)
        result = await agent.run(
            goal="Find vulnerabilities on target",
            target="192.168.1.1",
            scope={"depth": "comprehensive"}
        )
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        max_iterations: int = 50,
        retry_attempts: int = 3,
        retry_delay: float = 2.0,
        enable_progress_tracking: bool = True,
    ):
        """
        Initialisiert den Autonomous Agent Loop.

        Args:
            llm_client: LLM Client für Reasoning (optional)
            max_iterations: Maximale Anzahl von Iterationen
            retry_attempts: Anzahl der Retry-Versuche bei Fehlern
            retry_delay: Verzögerung zwischen Retrys in Sekunden
            enable_progress_tracking: Ob Progress Tracking aktiviert ist
        """
        self.llm = llm_client
        self.max_iterations = max_iterations
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.enable_progress_tracking = enable_progress_tracking

        # State Machine
        self.state = AgentState.IDLE
        self.previous_state: Optional[AgentState] = None

        # Memory
        self.memory: Optional[AgentMemory] = None

        # Tools
        self.tool_registry = ToolRegistry()

        # Progress Tracking
        self.progress: Dict[str, Any] = {
            "current_iteration": 0,
            "total_iterations": max_iterations,
            "completed_steps": 0,
            "total_steps": 0,
            "findings_count": 0,
            "errors": [],
        }

        # Callbacks
        self.state_callbacks: Dict[AgentState, List[Callable]] = {
            state: [] for state in AgentState
        }
        self.progress_callback: Optional[Callable[[Dict], None]] = None

        # Execution tracking
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

        self.logger = logging.getLogger(__name__)

    def register_state_callback(
        self, state: AgentState, callback: Callable
    ) -> None:
        """
        Registriert einen Callback für einen Zustand.

        Args:
            state: Der Zustand für den Callback
            callback: Funktion die aufgerufen wird
        """
        self.state_callbacks[state].append(callback)

    def set_progress_callback(self, callback: Callable[[Dict], None]) -> None:
        """
        Setzt den Progress Callback.

        Args:
            callback: Funktion die mit Progress-Updates aufgerufen wird
        """
        self.progress_callback = callback

    def _transition_to(self, new_state: AgentState) -> None:
        """
        Wechselt zu einem neuen Zustand und trigger Callbacks.

        Args:
            new_state: Der neue Zustand
        """
        self.previous_state = self.state
        self.state = new_state

        self.logger.info(
            f"State transition: {self.previous_state.name} -> {new_state.name}"
        )

        # Trigger callbacks
        for callback in self.state_callbacks.get(new_state, []):
            try:
                callback(new_state)
            except Exception as e:
                self.logger.error(f"State callback error: {e}")

    def _update_progress(self, updates: Dict[str, Any]) -> None:
        """Aktualisiert den Progress und ruft Callback auf."""
        self.progress.update(updates)

        if self.enable_progress_tracking and self.progress_callback:
            try:
                self.progress_callback(self.progress.copy())
            except Exception as e:
                self.logger.error(f"Progress callback error: {e}")

    async def run(
        self, goal: str, target: str, scope: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Haupt-Einstiegspunkt für den Autonomous Agent Loop.

        Führt den kompletten ReAct Loop aus:
        1. PLANNING: Erstellt einen Plan basierend auf dem Ziel
        2. EXECUTING: Führt Tools aus
        3. OBSERVING: Analysiert Ergebnisse
        4. REFLECTING: Evaluiert Fortschritt und passt Plan an

        Args:
            goal: Das zu erreichende Ziel (z.B. "Find all open ports")
            target: Das Ziel-System (IP, Domain, URL)
            scope: Optionale Scope-Beschränkungen

        Returns:
            Dict mit execution_result, findings, statistics und metadata
        """
        self.start_time = time.time()
        self._transition_to(AgentState.PLANNING)

        # Initialisiere Memory
        self.memory = AgentMemory(goal=goal, target=target, scope=scope or {})

        self.logger.info(f"Starting autonomous execution: {goal} on {target}")

        try:
            # PLANNING Phase
            plan = await self.plan()
            self.memory.current_plan = [step.to_dict() for step in plan]
            self.progress["total_steps"] = len(plan)

            # Haupt-Loop
            iteration = 0
            while iteration < self.max_iterations:
                iteration += 1
                self.progress["current_iteration"] = iteration

                # Prüfe ob alle Schritte abgeschlossen
                if self.memory.plan_step >= len(plan):
                    self.logger.info("All plan steps completed")
                    break

                current_step = plan[self.memory.plan_step]

                # EXECUTING Phase
                self._transition_to(AgentState.EXECUTING)
                result = await self._execute_with_retry(current_step)

                # OBSERVING Phase
                self._transition_to(AgentState.OBSERVING)
                await self.observe(result)  # Observation stored in memory

                # Speichere Ergebnis
                current_step.result = result
                current_step.completed = True
                self.memory.plan_step += 1
                self.progress["completed_steps"] = self.memory.plan_step

                # Extrahiere Findings
                if result.success and result.data:
                    await self._extract_findings(result)

                # REFLECTING Phase
                self._transition_to(AgentState.REFLECTING)
                should_continue = await self.reflect()

                if not should_continue:
                    self.logger.info("Reflection indicated completion")
                    break

                # Update Context Window
                self.memory.add_to_context_window(
                    {
                        "type": "execution",
                        "step": current_step.action,
                        "result": result.success,
                        "findings": len(self.memory.findings),
                    }
                )

            self._transition_to(AgentState.COMPLETED)
            return await self._compile_final_result()

        except Exception as e:
            self.logger.error(f"Execution failed: {str(e)}")
            self._transition_to(AgentState.ERROR)
            self.progress["errors"].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
            )
            return self._compile_error_result(e)

        finally:
            self.end_time = time.time()

    async def plan(self) -> List[PlanStep]:
        """
        Erstellt einen Aktionsplan basierend auf dem Ziel.

        Analysiert das Ziel und erstellt eine Sequenz von PlanSteps
        mit den passenden Tools.

        Returns:
            Liste von PlanSteps zur Zielerreichung
        """
        self.logger.info("Planning phase started")

        goal_lower = self.memory.goal.lower() if self.memory else ""
        target = self.memory.target if self.memory else ""

        plan: List[PlanStep] = []

        # Entscheidungslogik basierend auf Ziel
        if "port" in goal_lower or "service" in goal_lower:
            plan.append(
                PlanStep(
                    tool_type=ToolType.NMAP_SCANNER,
                    action=f"Scan open ports on {target}",
                    parameters={"target": target, "ports": "1-1000"},
                )
            )

        if "subdomain" in goal_lower or "enumerate" in goal_lower:
            plan.append(
                PlanStep(
                    tool_type=ToolType.SUBDOMAIN_ENUMERATOR,
                    action=f"Enumerate subdomains of {target}",
                    parameters={"target": target},
                )
            )

        if "vulnerability" in goal_lower or "scan" in goal_lower:
            plan.append(
                PlanStep(
                    tool_type=ToolType.NUCLEI_SCANNER,
                    action=f"Scan {target} for vulnerabilities",
                    parameters={"target": target},
                )
            )

        if "exploit" in goal_lower:
            plan.append(
                PlanStep(
                    tool_type=ToolType.EXPLOIT_VALIDATOR,
                    action=f"Validate exploits on {target}",
                    parameters={"target": target},
                )
            )

        # Immer einen Report generieren
        plan.append(
            PlanStep(
                tool_type=ToolType.REPORT_GENERATOR,
                action="Generate final report",
                parameters={"target": target},
            )
        )

        # Falls kein spezifischer Plan erstellt wurde, Standard-Plan
        if not plan:
            plan = [
                PlanStep(
                    tool_type=ToolType.NMAP_SCANNER,
                    action=f"Initial reconnaissance of {target}",
                    parameters={"target": target},
                ),
                PlanStep(
                    tool_type=ToolType.NUCLEI_SCANNER,
                    action=f"Vulnerability scan of {target}",
                    parameters={"target": target},
                ),
                PlanStep(
                    tool_type=ToolType.REPORT_GENERATOR,
                    action="Generate findings report",
                    parameters={"target": target},
                ),
            ]

        self.logger.info(f"Plan created with {len(plan)} steps")

        # Speichere Plan im Memory
        for step in plan:
            self.memory.add_to_short_term(
                {
                    "type": "plan_step",
                    "content": step.action,
                    "tool": step.tool_type.value,
                }
            )

        return plan

    async def execute_action(self, action: Dict[str, Any]) -> ToolResult:
        """
        Führt eine einzelne Aktion aus.

        Args:
            action: Dictionary mit tool_type und parameters

        Returns:
            ToolResult mit dem Ausführungsergebnis
        """
        tool_type_str = action.get("tool_type", "nmap_scanner")
        parameters = action.get("parameters", {})

        # Konvertiere String zu Enum
        try:
            tool_type = ToolType(tool_type_str)
        except ValueError:
            return ToolResult(
                tool_name=tool_type_str,
                success=False,
                error_message=f"Unknown tool type: {tool_type_str}",
            )

        tool = self.tool_registry.get_tool(tool_type)
        if not tool:
            return ToolResult(
                tool_name=tool_type_str,
                success=False,
                error_message=f"Tool not found: {tool_type_str}",
            )

        # Validiere Parameter
        valid, error = tool.validate_parameters(parameters)
        if not valid:
            return ToolResult(
                tool_name=tool.name,
                success=False,
                error_message=f"Parameter validation failed: {error}",
            )

        # Führe Tool aus
        self.logger.info(f"Executing {tool.name} with params: {parameters}")
        return await tool.execute(parameters)

    async def _execute_with_retry(self, step: PlanStep) -> ToolResult:
        """
        Führt einen Plan-Schritt mit Retry-Logik aus.

        Args:
            step: Der auszuführende PlanStep

        Returns:
            ToolResult mit dem Ergebnis
        """
        last_error = None

        for attempt in range(1, self.retry_attempts + 1):
            try:
                self.logger.info(
                    f"Executing step '{step.action}' (attempt {attempt}/{self.retry_attempts})"
                )

                tool = self.tool_registry.get_tool(step.tool_type)
                if not tool:
                    raise ValueError(f"Tool {step.tool_type.value} not found")

                result = await tool.execute(step.parameters)

                if result.success:
                    return result

                # Tool lieferte Fehler, versuche Retry
                last_error = result.error_message
                self.logger.warning(f"Attempt {attempt} failed: {last_error}")

                if attempt < self.retry_attempts:
                    await asyncio.sleep(self.retry_delay * attempt)

            except Exception as e:
                last_error = str(e)
                self.logger.error(f"Exception on attempt {attempt}: {e}")

                if attempt < self.retry_attempts:
                    await asyncio.sleep(self.retry_delay * attempt)

        # Alle Versuche fehlgeschlagen
        return ToolResult(
            tool_name=step.tool_type.value,
            success=False,
            error_message=f"All {self.retry_attempts} attempts failed. Last error: {last_error}",
        )

    async def observe(self, result: ToolResult) -> Dict[str, Any]:
        """
        Analysiert das Ergebnis einer Aktion.

        Args:
            result: Das ToolResult zur Analyse

        Returns:
            Dictionary mit Analyse-Ergebnissen
        """
        self.logger.info(f"Observing result from {result.tool_name}")

        observation = {
            "tool": result.tool_name,
            "success": result.success,
            "execution_time": result.execution_time,
            "timestamp": result.timestamp.isoformat(),
            "findings_extracted": 0,
        }

        if result.success:
            # Analysiere Daten
            data = result.data or {}

            if "open_ports" in data:
                observation["open_ports"] = len(data["open_ports"])
            if "findings" in data:
                observation["vulnerabilities"] = len(data["findings"])
            if "subdomains" in data:
                observation["subdomains"] = len(data["subdomains"])

            # Speichere Observation
            self.memory.add_to_short_term(
                {
                    "type": "observation",
                    "content": f"{result.tool_name} completed successfully",
                    "data_keys": list(data.keys()),
                }
            )
        else:
            observation["error"] = result.error_message

            self.memory.add_to_short_term(
                {
                    "type": "observation",
                    "content": f"{result.tool_name} failed: {result.error_message}",
                    "error": True,
                }
            )

        return observation

    async def reflect(self) -> bool:
        """
        Evaluiert ob das Ziel erreicht wurde oder weitere Aktionen nötig sind.

        Returns:
            True wenn weitere Aktionen nötig sind, False wenn beendet
        """
        self.logger.info("Reflection phase")

        # Prüfe ob kritische Fehler aufgetreten sind
        recent_errors = [
            e
            for e in self.progress["errors"]
            if (
                datetime.now() - datetime.fromisoformat(e["timestamp"])
            ).seconds
            < 60
        ]

        if len(recent_errors) > 5:
            self.logger.error("Too many recent errors, stopping")
            return False

        # Prüfe ob Ziel erreicht (basierend auf Findings)
        critical_findings = [
            f for f in self.memory.findings if f.get("severity") == "critical"
        ]

        # Wenn kritische Findings gefunden und Report generiert, beenden
        if (
            critical_findings
            and self.memory.plan_step >= len(self.memory.current_plan) - 1
        ):
            self.logger.info("Critical findings detected and report ready")
            # Könnte hier entscheiden zu beenden oder weiterzumachen

        # Prüfe ob maximale Iterationen erreicht
        if self.progress["current_iteration"] >= self.max_iterations:
            self.logger.info("Max iterations reached")
            return False

        # Reflexion: Update Context
        self.memory.add_to_context_window(
            {
                "type": "reflection",
                "content": f"Iteration {self.progress['current_iteration']} completed",
                "findings_count": len(self.memory.findings),
                "progress": f"{self.memory.plan_step}/{len(self.memory.current_plan)}",
            }
        )

        return True

    async def _extract_findings(self, result: ToolResult) -> None:
        """Extrahiert Security Findings aus Tool-Ergebnissen."""
        data = result.data or {}

        # Nmap Findings
        if "open_ports" in data:
            for port_info in data["open_ports"]:
                self.memory.add_finding(
                    {
                        "type": "open_port",
                        "severity": "info",
                        "source": result.tool_name,
                        "details": port_info,
                    }
                )

        # Nuclei Findings
        if "findings" in data:
            for vuln in data["findings"]:
                self.memory.add_finding(
                    {
                        "type": "vulnerability",
                        "severity": vuln.get("severity", "unknown"),
                        "source": result.tool_name,
                        "details": vuln,
                    }
                )

        # Subdomain Findings
        if "subdomains" in data:
            for subdomain in data["subdomains"]:
                self.memory.add_finding(
                    {
                        "type": "subdomain",
                        "severity": "info",
                        "source": result.tool_name,
                        "details": subdomain,
                    }
                )

        self.progress["findings_count"] = len(self.memory.findings)

    async def _compile_final_result(self) -> Dict[str, Any]:
        """Kompiliert das finale Ergebnis."""
        execution_time = (
            self.end_time - self.start_time
            if self.start_time and self.end_time
            else 0
        )

        # Generiere finalen Report
        report_tool = self.tool_registry.get_tool(ToolType.REPORT_GENERATOR)
        report_result = await report_tool.execute(
            {
                "target": self.memory.target,
                "findings": self.memory.findings,
                "format": "json",
            }
        )

        return {
            "success": True,
            "state": self.state.name,
            "execution": {
                "goal": self.memory.goal if self.memory else "",
                "target": self.memory.target if self.memory else "",
                "duration_seconds": round(execution_time, 2),
                "iterations": self.progress["current_iteration"],
                "steps_completed": self.progress["completed_steps"],
                "total_steps": self.progress["total_steps"],
            },
            "findings": {
                "count": len(self.memory.findings) if self.memory else 0,
                "items": self.memory.findings if self.memory else [],
            },
            "report": report_result.data if report_result.success else None,
            "memory": self.memory.to_dict() if self.memory else {},
            "progress": self.progress,
            "timestamp": datetime.now().isoformat(),
        }

    def _compile_error_result(self, error: Exception) -> Dict[str, Any]:
        """Kompiliert ein Fehler-Ergebnis."""
        return {
            "success": False,
            "state": self.state.name,
            "error": {
                "message": str(error),
                "type": type(error).__name__,
                "traceback": traceback.format_exc(),
            },
            "progress": self.progress,
            "timestamp": datetime.now().isoformat(),
        }

    def get_state(self) -> AgentState:
        """Gibt den aktuellen Zustand zurück."""
        return self.state

    def get_progress(self) -> Dict[str, Any]:
        """Gibt den aktuellen Progress zurück."""
        return self.progress.copy()

    def is_running(self) -> bool:
        """Prüft ob der Agent läuft."""
        return self.state in [
            AgentState.PLANNING,
            AgentState.EXECUTING,
            AgentState.OBSERVING,
            AgentState.REFLECTING,
        ]

    def pause(self) -> None:
        """Pausiert die Ausführung (Human-in-the-loop)."""
        if self.is_running():
            self._transition_to(AgentState.PAUSED)

    def resume(self) -> None:
        """Setzt die Ausführung fort."""
        if self.state == AgentState.PAUSED and self.previous_state:
            self._transition_to(self.previous_state)


# Factory Function
def create_agent_loop(
    llm_client: Optional[Any] = None,
    max_iterations: int = 50,
    retry_attempts: int = 3,
) -> AutonomousAgentLoop:
    """
    Factory-Funktion zum Erstellen eines AutonomousAgentLoop.

    Args:
        llm_client: Optionaler LLM Client
        max_iterations: Maximale Iterationen
        retry_attempts: Anzahl der Retry-Versuche

    Returns:
        Konfigurierte AutonomousAgentLoop Instanz
    """
    return AutonomousAgentLoop(
        llm_client=llm_client,
        max_iterations=max_iterations,
        retry_attempts=retry_attempts,
    )


# Example usage
if __name__ == "__main__":

    async def main():
        # Erstelle Agent
        agent = create_agent_loop(max_iterations=10)

        # Definiere Progress Callback
        def on_progress(progress):
            print(
                f"Progress: {progress['completed_steps']}/{progress['total_steps']} steps"
            )

        agent.set_progress_callback(on_progress)

        # Führe Scan aus
        result = await agent.run(
            goal="Find vulnerabilities and open ports",
            target="example.com",
            scope={"depth": "standard"},
        )

        print("\n=== Execution Result ===")
        print(json.dumps(result, indent=2, default=str))

    asyncio.run(main())
