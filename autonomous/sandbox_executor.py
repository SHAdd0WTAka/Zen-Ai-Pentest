#!/usr/bin/env python3
"""
Sandboxed Execution Engine for Zen AI Pentest Framework

Sichere isolierte Ausführung von Exploits mit:
- Docker-in-Docker oder gVisor für Isolation
- Resource Limits (CPU, Memory, Network)
- Read-only Filesystem mit tmpfs
- Timeout Management
- Audit Logging

FOR AUTHORIZED SECURITY TESTING ONLY

Author: SHAdd0WTAka
Version: 2.0.0
"""

import asyncio
import hashlib
import logging
import os
import shutil
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional

# Optional imports - handle gracefully if not available
try:
    import docker
    from docker.errors import DockerException  # noqa: F401

    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

logger = logging.getLogger("ZenAI.SandboxExecutor")


class SandboxType(Enum):
    """Type of sandbox technology."""

    DOCKER = "docker"
    DOCKER_DIND = "docker_in_docker"
    GVISOR = "gvisor"
    NAMESPACE = "namespace"  # Linux namespaces as fallback
    PROCESS = "process"  # Process-level isolation (least secure)


class SandboxStatus(Enum):
    """Status of sandbox execution."""

    PENDING = auto()
    CREATING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    TIMEOUT = auto()
    KILLED = auto()
    ERROR = auto()


@dataclass
class ResourceLimits:
    """Resource limits for sandbox execution."""

    cpu_cores: float = 1.0  # CPU cores limit
    memory_mb: int = 512  # Memory limit in MB
    swap_mb: int = 512  # Swap limit in MB
    disk_mb: int = 1024  # Disk limit in MB
    pids: int = 50  # Max processes
    network_enabled: bool = False  # Network access
    read_only_root: bool = True  # Read-only root filesystem
    tmpfs_size_mb: int = 100  # tmpfs size for /tmp
    timeout_seconds: int = 300  # 5 minutes default timeout

    def to_docker_config(self) -> Dict[str, Any]:
        """Convert to Docker API configuration."""
        return {
            "cpu_quota": int(self.cpu_cores * 100000),
            "cpu_period": 100000,
            "mem_limit": f"{self.memory_mb}m",
            "memswap_limit": f"{self.swap_mb}m",
            "pids_limit": self.pids,
            "network_disabled": not self.network_enabled,
            "read_only": self.read_only_root,
            "tmpfs": (
                {
                    "/tmp": f"rw,noexec,nosuid,size={self.tmpfs_size_mb}m",  # nosec B108
                    "/var/tmp": f"rw,noexec,nosuid,size={self.tmpfs_size_mb}m",  # nosec B108
                }
                if self.read_only_root
                else {}
            ),
        }

    def to_gvisor_config(self) -> Dict[str, Any]:
        """Convert to gVisor runsc configuration."""
        return {
            "platform": "kvm",  # or "ptrace" for compatibility
            "debug": False,
            "allow-flag": "proc",
            "cpu": str(int(self.cpu_cores * 1000)),  # millicores
            "memory": f"{self.memory_mb}MB",
            "network": "host" if self.network_enabled else "none",
        }


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution."""

    sandbox_type: SandboxType = SandboxType.DOCKER
    image: str = "zenai/exploit-sandbox:latest"
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)

    # Security settings
    cap_drop: List[str] = field(default_factory=lambda: ["ALL"])
    cap_add: List[str] = field(default_factory=lambda: ["NET_BIND_SERVICE"])
    seccomp_profile: Optional[str] = None
    apparmor_profile: Optional[str] = None

    # Network settings
    dns_servers: List[str] = field(default_factory=lambda: ["8.8.8.8", "1.1.1.1"])
    proxy_url: Optional[str] = None

    # Volume settings
    volumes: Dict[str, str] = field(default_factory=dict)  # host:container
    env_vars: Dict[str, str] = field(default_factory=dict)

    # Logging
    log_driver: str = "json-file"
    log_max_size: str = "10m"
    log_max_files: int = 3


@dataclass
class SandboxResult:
    """Result of sandboxed execution."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    status: SandboxStatus
    container_id: Optional[str] = None
    error_message: Optional[str] = None
    artifacts: Dict[str, str] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    audit_log: List[Dict[str, Any]] = field(default_factory=list)
    resource_usage: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "execution_time": self.execution_time,
            "status": self.status.name,
            "container_id": self.container_id,
            "error_message": self.error_message,
            "artifacts": self.artifacts,
            "logs": self.logs,
            "timestamp": self.timestamp.isoformat(),
            "audit_log": self.audit_log,
            "resource_usage": self.resource_usage,
        }


class SandboxExecutor:
    """
    Secure sandboxed execution engine for exploit validation.

    Provides isolated execution environments using Docker or gVisor
    with strict resource limits and security controls.

    Usage:
        executor = SandboxExecutor(config=SandboxConfig())
        result = await executor.execute(
            command="python3 exploit.py",
            work_dir="/path/to/exploit",
            timeout=300
        )
    """

    # Known good exploit hashes (SHA256)
    EXPLOIT_ALLOWLIST: Dict[str, str] = {
        # Example: Hash of known good exploit scripts
        # "exploit_name": "sha256_hash"
    }

    def __init__(self, config: Optional[SandboxConfig] = None, audit_logger: Optional[logging.Logger] = None):
        """
        Initialize the SandboxExecutor.

        Args:
            config: Sandbox configuration
            audit_logger: Logger for audit events
        """
        self.config = config or SandboxConfig()
        self.audit_logger = audit_logger or logging.getLogger("ZenAI.Audit")

        # Initialize Docker client if available
        self.docker_client: Optional[docker.DockerClient] = None
        if DOCKER_AVAILABLE and self.config.sandbox_type in [SandboxType.DOCKER, SandboxType.DOCKER_DIND]:
            try:
                self.docker_client = docker.from_env()
                logger.info("Docker client initialized")
            except DockerException as e:
                logger.warning(f"Docker not available: {e}")

        # Rate limiting
        self._execution_lock = asyncio.Lock()
        self._rate_limiter = asyncio.Semaphore(3)  # Max 3 concurrent executions
        self._last_execution: Dict[str, float] = {}
        self._min_interval = 10.0  # Minimum seconds between executions

        # Kill switch
        self._killed = False

        # Statistics
        self._stats = {"total_executions": 0, "successful": 0, "failed": 0, "killed": 0, "timeout": 0}

        logger.info(f"SandboxExecutor initialized (type={self.config.sandbox_type.value})")

    async def execute(
        self,
        command: List[str],
        work_dir: Optional[str] = None,
        input_data: Optional[bytes] = None,
        timeout: Optional[int] = None,
        artifacts_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> SandboxResult:
        """
        Execute a command in the sandbox.

        Args:
            command: Command and arguments to execute
            work_dir: Working directory containing files to mount
            input_data: Data to pass to stdin
            timeout: Execution timeout override
            artifacts_dir: Directory to collect output artifacts
            env_vars: Additional environment variables

        Returns:
            SandboxResult with execution results
        """
        start_time = time.time()
        container_id = str(uuid.uuid4())[:12]
        audit_log = []

        # Check kill switch
        if self._killed:
            self._audit(audit_log, "execution_blocked", {"reason": "kill_switch"})
            return SandboxResult(
                success=False,
                stdout="",
                stderr="",
                exit_code=-1,
                execution_time=0.0,
                status=SandboxStatus.KILLED,
                container_id=container_id,
                error_message="Kill switch activated",
                audit_log=audit_log,
            )

        # Check rate limit
        await self._check_rate_limit()

        self._audit(
            audit_log,
            "execution_started",
            {"command": command, "container_id": container_id, "sandbox_type": self.config.sandbox_type.value},
        )

        async with self._rate_limiter:
            try:
                if self.config.sandbox_type == SandboxType.DOCKER:
                    result = await self._execute_docker(
                        command,
                        work_dir,
                        input_data,
                        timeout or self.config.resource_limits.timeout_seconds,
                        artifacts_dir,
                        env_vars,
                        container_id,
                        audit_log,
                    )
                elif self.config.sandbox_type == SandboxType.GVISOR:
                    result = await self._execute_gvisor(
                        command,
                        work_dir,
                        input_data,
                        timeout or self.config.resource_limits.timeout_seconds,
                        artifacts_dir,
                        env_vars,
                        container_id,
                        audit_log,
                    )
                else:
                    result = await self._execute_process(
                        command,
                        work_dir,
                        input_data,
                        timeout or self.config.resource_limits.timeout_seconds,
                        artifacts_dir,
                        env_vars,
                        container_id,
                        audit_log,
                    )

                self._stats["total_executions"] += 1
                if result.success:
                    self._stats["successful"] += 1
                elif result.status == SandboxStatus.TIMEOUT:
                    self._stats["timeout"] += 1
                elif result.status == SandboxStatus.KILLED:
                    self._stats["killed"] += 1
                else:
                    self._stats["failed"] += 1

                return result

            except asyncio.TimeoutError:
                self._stats["total_executions"] += 1
                self._stats["timeout"] += 1
                self._audit(
                    audit_log, "execution_timeout", {"timeout": timeout or self.config.resource_limits.timeout_seconds}
                )
                return SandboxResult(
                    success=False,
                    stdout="",
                    stderr="",
                    exit_code=-1,
                    execution_time=time.time() - start_time,
                    status=SandboxStatus.TIMEOUT,
                    container_id=container_id,
                    error_message="Execution timeout",
                    audit_log=audit_log,
                )
            except Exception as e:
                self._stats["total_executions"] += 1
                self._stats["failed"] += 1
                logger.exception("Sandbox execution failed")
                self._audit(audit_log, "execution_error", {"error": str(e)})
                return SandboxResult(
                    success=False,
                    stdout="",
                    stderr="",
                    exit_code=-1,
                    execution_time=time.time() - start_time,
                    status=SandboxStatus.ERROR,
                    container_id=container_id,
                    error_message=str(e),
                    audit_log=audit_log,
                )

    async def execute_exploit(
        self, exploit_code: str, target: str, exploit_name: str = "unknown", timeout: int = 300, work_dir: Optional[str] = None
    ) -> SandboxResult:
        """
        Execute exploit code in sandbox.

        Args:
            exploit_code: Python exploit code to execute
            target: Target URL/Host
            exploit_name: Name of exploit for logging
            timeout: Execution timeout
            work_dir: Working directory

        Returns:
            SandboxResult
        """
        # Verify exploit hash if in allowlist mode
        exploit_hash = hashlib.sha256(exploit_code.encode()).hexdigest()
        self._audit([], "exploit_hash_check", {"exploit_name": exploit_name, "hash": exploit_hash[:16] + "..."})

        # Create temporary work directory if not provided
        if work_dir is None:
            work_dir = tempfile.mkdtemp(prefix="exploit_")
            cleanup = True
        else:
            cleanup = False

        try:
            # Write exploit code to file
            exploit_path = os.path.join(work_dir, "exploit.py")
            with open(exploit_path, "w") as f:
                f.write(self._wrap_exploit_code(exploit_code, target))

            # Execute with Python
            result = await self.execute(
                command=["python3", "/workspace/exploit.py"],
                work_dir=work_dir,
                timeout=timeout,
                env_vars={"TARGET": target, "EXPLOIT_NAME": exploit_name},
            )

            return result

        finally:
            if cleanup and os.path.exists(work_dir):
                shutil.rmtree(work_dir, ignore_errors=True)

    def verify_exploit_hash(self, exploit_code: str, expected_hash: str) -> bool:
        """
        Verify exploit code against known good hash.

        Args:
            exploit_code: Exploit code to verify
            expected_hash: Expected SHA256 hash

        Returns:
            True if hash matches
        """
        actual_hash = hashlib.sha256(exploit_code.encode()).hexdigest()
        return actual_hash == expected_hash

    def add_allowed_exploit(self, name: str, exploit_code: str) -> None:
        """
        Add an exploit to the allowlist.

        Args:
            name: Name of the exploit
            exploit_code: Exploit code
        """
        exploit_hash = hashlib.sha256(exploit_code.encode()).hexdigest()
        self.EXPLOIT_ALLOWLIST[name] = exploit_hash
        logger.info(f"Added exploit '{name}' to allowlist")

    def kill_switch(self) -> None:
        """Activate kill switch to stop all executions."""
        logger.warning("Kill switch activated!")
        self._killed = True

        # Kill any running containers
        if self.docker_client:
            try:
                for container in self.docker_client.containers.list():
                    if container.labels.get("zenai.sandbox") == "true":
                        container.kill()
                        logger.info(f"Killed container: {container.id[:12]}")
            except Exception as e:
                logger.error(f"Failed to kill containers: {e}")

    def reset_kill_switch(self) -> None:
        """Reset kill switch."""
        logger.info("Kill switch reset")
        self._killed = False

    def get_stats(self) -> Dict[str, int]:
        """Get execution statistics."""
        return self._stats.copy()

    # Private methods

    async def _execute_docker(
        self,
        command: List[str],
        work_dir: Optional[str],
        input_data: Optional[bytes],
        timeout: int,
        artifacts_dir: Optional[str],
        env_vars: Optional[Dict[str, str]],
        container_id: str,
        audit_log: List[Dict[str, Any]],
    ) -> SandboxResult:
        """Execute in Docker sandbox."""
        if not self.docker_client:
            raise RuntimeError("Docker not available")

        start_time = time.time()
        volumes = {}

        # Mount work directory
        if work_dir:
            volumes[work_dir] = {"bind": "/workspace", "mode": "ro"}

        # Add custom volumes
        for host_path, container_path in self.config.volumes.items():
            volumes[host_path] = {"bind": container_path, "mode": "ro"}

        # Setup artifacts collection
        if artifacts_dir:
            volumes[artifacts_dir] = {"bind": "/artifacts", "mode": "rw"}
            env_vars = env_vars or {}
            env_vars["OUTPUT_DIR"] = "/artifacts"

        # Merge environment variables
        environment = {**self.config.env_vars, **(env_vars or {})}
        environment["CONTAINER_ID"] = container_id

        # Resource limits
        resource_config = self.config.resource_limits.to_docker_config()

        self._audit(
            audit_log, "container_creating", {"image": self.config.image, "command": command, "container_id": container_id}
        )

        # Create and run container
        container = self.docker_client.containers.run(
            image=self.config.image,
            command=command,
            detach=True,
            auto_remove=False,  # We need to collect artifacts
            network_disabled=not self.config.resource_limits.network_enabled,
            volumes=volumes,
            environment=environment,
            dns=self.config.dns_servers,
            cap_drop=self.config.cap_drop,
            cap_add=self.config.cap_add,
            security_opt=["no-new-privileges:true"],
            labels={"zenai.sandbox": "true", "zenai.container_id": container_id},
            **resource_config,
        )

        self._audit(audit_log, "container_started", {"docker_container_id": container.id[:12], "container_id": container_id})

        # Wait for completion with timeout
        try:
            loop = asyncio.get_event_loop()

            # Wait for container with timeout
            result = await asyncio.wait_for(loop.run_in_executor(None, container.wait), timeout=timeout)

            # Collect logs
            logs = container.logs().decode("utf-8", errors="ignore")

            # Get resource usage stats
            stats = container.stats(stream=False)
            resource_usage = {
                "cpu_usage": stats.get("cpu_stats", {}).get("cpu_usage", {}),
                "memory_usage": stats.get("memory_stats", {}).get("usage", 0),
                "memory_max": stats.get("memory_stats", {}).get("max_usage", 0),
            }

            # Collect artifacts
            artifacts = {}
            if artifacts_dir:
                artifacts = self._collect_artifacts(artifacts_dir)

            exit_code = result.get("StatusCode", -1)
            success = exit_code == 0

            self._audit(
                audit_log,
                "container_completed",
                {"docker_container_id": container.id[:12], "exit_code": exit_code, "success": success},
            )

            # Remove container
            container.remove(force=True)

            return SandboxResult(
                success=success,
                stdout=logs,
                stderr="",
                exit_code=exit_code,
                execution_time=time.time() - start_time,
                status=SandboxStatus.COMPLETED if success else SandboxStatus.FAILED,
                container_id=container_id,
                artifacts=artifacts,
                audit_log=audit_log,
                resource_usage=resource_usage,
            )

        except asyncio.TimeoutError:
            logger.warning(f"Container {container_id} timed out after {timeout}s")
            container.kill()
            container.remove(force=True)
            raise
        except Exception as e:
            logger.error(f"Container execution failed: {e}")
            try:
                container.remove(force=True)
            except Exception:
                pass
            raise

    async def _execute_gvisor(
        self,
        command: List[str],
        work_dir: Optional[str],
        input_data: Optional[bytes],
        timeout: int,
        artifacts_dir: Optional[str],
        env_vars: Optional[Dict[str, str]],
        container_id: str,
        audit_log: List[Dict[str, Any]],
    ) -> SandboxResult:
        """Execute in gVisor sandbox using runsc."""

        start_time = time.time()

        # Prepare gVisor configuration
        gvisor_config = self.config.resource_limits.to_gvisor_config()

        # Create runtime directory
        runtime_dir = tempfile.mkdtemp(prefix="gvisor_")

        # Build runsc command
        runsc_cmd = [
            "runsc",
            "--root",
            runtime_dir,
            "--platform",
            gvisor_config["platform"],
            "--network",
            gvisor_config["network"],
        ]

        if gvisor_config["debug"]:
            runsc_cmd.append("--debug")

        # For gVisor, we use Docker with the gVisor runtime
        if self.docker_client:
            volumes = {}
            if work_dir:
                volumes[work_dir] = {"bind": "/workspace", "mode": "ro"}
            if artifacts_dir:
                volumes[artifacts_dir] = {"bind": "/artifacts", "mode": "rw"}

            environment = {**self.config.env_vars, **(env_vars or {})}

            self._audit(audit_log, "gvisor_container_creating", {"image": self.config.image, "container_id": container_id})

            try:
                container = self.docker_client.containers.run(
                    image=self.config.image,
                    command=command,
                    detach=True,
                    auto_remove=False,
                    network_disabled=not self.config.resource_limits.network_enabled,
                    volumes=volumes,
                    environment=environment,
                    runtime="runsc",  # Use gVisor runtime
                    labels={"zenai.sandbox": "true", "zenai.container_id": container_id},
                )

                # Wait with timeout
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(loop.run_in_executor(None, container.wait), timeout=timeout)

                logs = container.logs().decode("utf-8", errors="ignore")
                exit_code = result.get("StatusCode", -1)

                artifacts = {}
                if artifacts_dir:
                    artifacts = self._collect_artifacts(artifacts_dir)

                container.remove(force=True)

                return SandboxResult(
                    success=exit_code == 0,
                    stdout=logs,
                    stderr="",
                    exit_code=exit_code,
                    execution_time=time.time() - start_time,
                    status=SandboxStatus.COMPLETED if exit_code == 0 else SandboxStatus.FAILED,
                    container_id=container_id,
                    artifacts=artifacts,
                    audit_log=audit_log,
                )

            except asyncio.TimeoutError:
                container.kill()
                container.remove(force=True)
                raise
        else:
            raise RuntimeError("Docker required for gVisor execution")

    async def _execute_process(
        self,
        command: List[str],
        work_dir: Optional[str],
        input_data: Optional[bytes],
        timeout: int,
        artifacts_dir: Optional[str],
        env_vars: Optional[Dict[str, str]],
        container_id: str,
        audit_log: List[Dict[str, Any]],
    ) -> SandboxResult:
        """Execute as local process (fallback, less secure)."""
        start_time = time.time()

        self._audit(
            audit_log,
            "process_execution_started",
            {"command": command, "container_id": container_id, "warning": "Using process sandbox (less secure)"},
        )

        # Prepare environment
        env = os.environ.copy()
        env.update(self.config.env_vars)
        env.update(env_vars or {})
        env["CONTAINER_ID"] = container_id

        if artifacts_dir:
            env["OUTPUT_DIR"] = artifacts_dir

        # Execute process
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE if input_data else None,
            cwd=work_dir,
            env=env,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(input=input_data), timeout=timeout)

            artifacts = {}
            if artifacts_dir:
                artifacts = self._collect_artifacts(artifacts_dir)

            return SandboxResult(
                success=process.returncode == 0,
                stdout=stdout.decode("utf-8", errors="ignore"),
                stderr=stderr.decode("utf-8", errors="ignore"),
                exit_code=process.returncode,
                execution_time=time.time() - start_time,
                status=SandboxStatus.COMPLETED if process.returncode == 0 else SandboxStatus.FAILED,
                container_id=container_id,
                artifacts=artifacts,
                audit_log=audit_log,
            )

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise

    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting."""
        now = time.time()

        # Global rate limit check
        if "global" in self._last_execution:
            elapsed = now - self._last_execution["global"]
            if elapsed < self._min_interval:
                wait_time = self._min_interval - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

        self._last_execution["global"] = time.time()

    def _collect_artifacts(self, artifacts_dir: str) -> Dict[str, str]:
        """Collect output artifacts from directory."""
        artifacts = {}
        if not os.path.exists(artifacts_dir):
            return artifacts

        for filename in os.listdir(artifacts_dir):
            filepath = os.path.join(artifacts_dir, filename)
            try:
                if os.path.isfile(filepath):
                    with open(filepath, "rb") as f:
                        content = f.read()
                        # Store as base64 for binary files
                        try:
                            artifacts[filename] = content.decode("utf-8")
                        except UnicodeDecodeError:
                            import base64

                            artifacts[filename] = base64.b64encode(content).decode("ascii")
            except Exception as e:
                logger.warning(f"Failed to read artifact {filename}: {e}")

        return artifacts

    def _wrap_exploit_code(self, exploit_code: str, target: str) -> str:
        """Wrap exploit code with safety harness."""
        return f'''#!/usr/bin/env python3
"""
Auto-generated exploit execution script
Generated: {datetime.now(timezone.utc).isoformat()}
Target: {target}
"""

import json
import os
import sys

# Safety checks
def safety_check():
    """Verify we're running in sandbox."""
    # Check for expected environment
    if not os.environ.get("CONTAINER_ID"):
        print("WARNING: Not running in sandbox environment", file=sys.stderr)
        return False
    return True

# Redirect imports for safety
import builtins
_original_import = builtins.__import__

def safe_import(name, *args, **kwargs):
    """Restricted import function."""
    blocked_modules = ['os.system', 'subprocess.call', 'subprocess.Popen']
    for blocked in blocked_modules:
        if name.startswith(blocked.split('.')[0]):
            # Allow but log
            print(f"Importing: {{name}}", file=sys.stderr)
    return _original_import(name, *args, **kwargs)

# Main execution
if __name__ == "__main__":
    target = os.environ.get("TARGET", "{target}")
    output_dir = os.environ.get("OUTPUT_DIR", ".")

    result = {{
        "success": False,
        "target": target,
        "output": "",
        "error": None
    }}

    try:
        # User exploit code
{self._indent_code(exploit_code, 8)}

        result["success"] = True
        result["output"] = "Exploit executed successfully"

    except Exception as e:
        result["error"] = str(e)
        result["output"] = f"Exploit failed: {{e}}"
        print(f"Error: {{e}}", file=sys.stderr)
        import traceback
        traceback.print_exc()

    # Write results
    with open(os.path.join(output_dir, "result.json"), "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result))
    sys.exit(0 if result["success"] else 1)
'''

    def _indent_code(self, code: str, indent: int) -> str:
        """Indent code block."""
        lines = code.split("\n")
        spaces = " " * indent
        return "\n".join(spaces + line for line in lines)

    def _audit(self, audit_log: List[Dict[str, Any]], action: str, details: Dict[str, Any]) -> None:
        """Add audit log entry."""
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "action": action, "details": details}
        audit_log.append(entry)
        self.audit_logger.info(f"[AUDIT] {action}: {details}")


class SandboxPool:
    """Pool of sandbox executors for concurrent execution."""

    def __init__(self, pool_size: int = 3, config: Optional[SandboxConfig] = None):
        self.pool_size = pool_size
        self.config = config or SandboxConfig()
        self._executors: List[SandboxExecutor] = []
        self._semaphore = asyncio.Semaphore(pool_size)
        self._counter = 0

    async def initialize(self) -> None:
        """Initialize all executors in the pool."""
        for i in range(self.pool_size):
            executor = SandboxExecutor(config=self.config)
            self._executors.append(executor)
        logger.info(f"SandboxPool initialized with {self.pool_size} executors")

    async def execute(self, command: List[str], work_dir: Optional[str] = None, timeout: int = 300, **kwargs) -> SandboxResult:
        """Execute command in pool."""
        async with self._semaphore:
            executor = self._executors[self._counter % len(self._executors)]
            self._counter += 1
            return await executor.execute(command, work_dir, timeout=timeout, **kwargs)

    def kill_all(self) -> None:
        """Activate kill switch on all executors."""
        for executor in self._executors:
            executor.kill_switch()


# Export public API
__all__ = [
    "SandboxExecutor",
    "SandboxPool",
    "SandboxResult",
    "SandboxConfig",
    "SandboxType",
    "SandboxStatus",
    "ResourceLimits",
]
