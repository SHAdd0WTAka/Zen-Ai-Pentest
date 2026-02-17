"""
Docker Sandbox for Secure Tool Execution

Provides isolated execution environment for security tools
to prevent damage to host system and contain exploits.
"""

import asyncio
import logging
import tempfile
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SandboxResult:
    """Result of sandboxed execution."""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    execution_time: float
    container_id: Optional[str] = None
    error_message: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)


class DockerSandbox:
    """
    Docker-based sandbox for executing security tools safely.

    Features:
    - Network isolation
    - Resource limits (CPU, memory)
    - Volume mounts (read-only where possible)
    - Automatic cleanup
    - Timeout enforcement
    """

    def __init__(
        self,
        image: str = "zen-pentest-tools:latest",
        network_mode: str = "none",  # Disabled by default for safety
        memory_limit: str = "512m",
        cpu_limit: str = "1.0",
        timeout: int = 300,
        auto_cleanup: bool = True
    ):
        """
        Initialize Docker sandbox.

        Args:
            image: Docker image with tools installed
            network_mode: 'none', 'bridge', or custom network
            memory_limit: Maximum memory (e.g., '512m', '1g')
            cpu_limit: CPU limit (e.g., '1.0', '0.5')
            timeout: Maximum execution time in seconds
            auto_cleanup: Remove containers after execution
        """
        self.image = image
        self.network_mode = network_mode
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.timeout = timeout
        self.auto_cleanup = auto_cleanup
        self.logger = logging.getLogger(__name__)

    async def execute(
        self,
        command: List[str],
        working_dir: str = "/workspace",
        input_files: Optional[Dict[str, str]] = None,
        output_dirs: Optional[List[str]] = None,
        environment: Optional[Dict[str, str]] = None
    ) -> SandboxResult:
        """
        Execute a command in Docker sandbox.

        Args:
            command: Command and arguments as list
            working_dir: Working directory inside container
            input_files: Dict of {host_path: container_path} for input files
            output_dirs: List of directories to copy from container after execution
            environment: Environment variables to set

        Returns:
            SandboxResult with execution details
        """
        import asyncio.subprocess

        start_time = datetime.now()
        container_name = f"zen-sandbox-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{os.urandom(4).hex()}"

        try:
            # Build docker run command
            docker_cmd = [
                "docker", "run",
                "--name", container_name,
                "--rm" if self.auto_cleanup else "",
                "--network", self.network_mode,
                "--memory", self.memory_limit,
                "--cpus", self.cpu_limit,
                "--security-opt", "no-new-privileges:true",
                "--cap-drop", "ALL",  # Drop all capabilities
                "--read-only",  # Read-only root filesystem
                "--tmpfs", "/tmp:noexec,nosuid,size=100m",
                "-w", working_dir,
            ]

            # Remove empty strings
            docker_cmd = [arg for arg in docker_cmd if arg]

            # Add volume mounts for input files
            if input_files:
                for host_path, container_path in input_files.items():
                    docker_cmd.extend(["-v", f"{host_path}:{container_path}:ro"])

            # Add volume mounts for output directories
            temp_output_dirs = []
            if output_dirs:
                for out_dir in output_dirs:
                    temp_dir = tempfile.mkdtemp()
                    temp_output_dirs.append((temp_dir, out_dir))
                    docker_cmd.extend(["-v", f"{temp_dir}:{out_dir}:rw"])

            # Add environment variables
            if environment:
                for key, value in environment.items():
                    docker_cmd.extend(["-e", f"{key}={value}"])

            # Add image and command
            docker_cmd.append(self.image)
            docker_cmd.extend(command)

            self.logger.info(f"[SANDBOX] Executing: {' '.join(docker_cmd)}")

            # Execute
            proc = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                # Kill container
                await self._kill_container(container_name)
                return SandboxResult(
                    success=False,
                    stdout="",
                    stderr="",
                    return_code=-1,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    container_id=container_name,
                    error_message=f"Timeout after {self.timeout}s"
                )

            execution_time = (datetime.now() - start_time).total_seconds()

            # Collect artifacts from output directories
            artifacts = []
            for temp_dir, container_dir in temp_output_dirs:
                if os.path.exists(temp_dir):
                    for file in os.listdir(temp_dir):
                        artifacts.append(os.path.join(temp_dir, file))

            return SandboxResult(
                success=proc.returncode == 0,
                stdout=stdout.decode('utf-8', errors='replace'),
                stderr=stderr.decode('utf-8', errors='replace'),
                return_code=proc.returncode,
                execution_time=execution_time,
                container_id=container_name,
                artifacts=artifacts
            )

        except FileNotFoundError:
            return SandboxResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                execution_time=(datetime.now() - start_time).total_seconds(),
                error_message="Docker not found. Please install Docker."
            )
        except Exception as e:
            self.logger.error(f"[SANDBOX] Execution failed: {e}")
            return SandboxResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                execution_time=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )

    async def _kill_container(self, container_name: str):
        """Kill a running container."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "kill", container_name,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
            self.logger.warning(f"[SANDBOX] Killed container {container_name}")
        except Exception as e:
            self.logger.error(f"[SANDBOX] Failed to kill container: {e}")

    async def is_available(self) -> bool:
        """Check if Docker is available."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "version",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await asyncio.wait_for(proc.wait(), timeout=5)
            return proc.returncode == 0
        except Exception:
            return False


class SandboxedToolExecutor:
    """
    Executes security tools in Docker sandbox.

    Provides unified interface for running tools safely.
    """

    def __init__(self):
        self.sandbox = DockerSandbox()
        self.logger = logging.getLogger(__name__)

    async def execute_tool(
        self,
        tool_name: str,
        tool_args: List[str],
        target: str,
        **kwargs
    ) -> SandboxResult:
        """
        Execute a security tool in sandbox.

        Args:
            tool_name: Name of the tool (nmap, nuclei, etc.)
            tool_args: Arguments for the tool
            target: Target to scan

        Returns:
            SandboxResult
        """
        # Build command based on tool
        if tool_name == "nmap":
            command = ["nmap"] + tool_args + [target]
        elif tool_name == "nuclei":
            command = ["nuclei"] + tool_args + ["-u", target]
        elif tool_name == "sqlmap":
            command = ["sqlmap"] + tool_args + ["-u", target]
        else:
            command = [tool_name] + tool_args

        self.logger.info(f"[EXECUTOR] Running {tool_name} against {target} in sandbox")

        return await self.sandbox.execute(
            command=command,
            **kwargs
        )


# Example usage and test
async def test_sandbox():
    """Test the Docker sandbox."""
    sandbox = DockerSandbox()

    # Check if Docker is available
    if not await sandbox.is_available():
        print("[TEST] Docker not available, skipping test")
        return

    print("[TEST] Testing Docker sandbox...")

    # Test simple command
    result = await sandbox.execute(
        command=["echo", "Hello from sandbox!"]
    )

    print(f"[TEST] Success: {result.success}")
    print(f"[TEST] Output: {result.stdout.strip()}")
    print(f"[TEST] Execution time: {result.execution_time:.2f}s")


if __name__ == "__main__":
    print("Docker Sandbox for Secure Tool Execution")
    print("=" * 60)
    print()
    print("This module provides:")
    print("  - Network isolation")
    print("  - Resource limits")
    print("  - Read-only filesystem")
    print("  - Automatic cleanup")
    print()

    asyncio.run(test_sandbox())
