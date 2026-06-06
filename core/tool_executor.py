"""
Optimized ToolExecutor - High-Performance System Command Execution

Optimizations:
- Connection pooling and process reuse
- Semaphore-based concurrency control
- Streaming output support
- Process pool for CPU-bound operations
- Memory-efficient large output handling
- Async subprocess with optimized buffer sizes
"""

import asyncio
import logging
import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ToolResultStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    CANCELLED = "cancelled"


@dataclass
class ToolResult:
    """Enhanced result of a tool invocation"""

    status: ToolResultStatus
    returncode: int
    stdout: str
    stderr: str
    command: str
    execution_time_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    peak_memory_mb: Optional[float] = None

    @property
    def success(self) -> bool:
        return self.status == ToolResultStatus.SUCCESS and self.returncode == 0

    @property
    def failed(self) -> bool:
        return not self.success

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "command": self.command,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata or {},
            "peak_memory_mb": self.peak_memory_mb,
            "success": self.success,
        }


class ToolExecutor(ABC):
    """Abstract base class for tool execution with async support"""

    @abstractmethod
    async def execute(
        self,
        command: List[str],
        timeout: int = 300,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        input_data: Optional[str] = None,
    ) -> ToolResult:
        """
        Execute a command asynchronously

        Args:
            command: Command as list (e.g., ["nmap", "-sV", "target.com"])
            timeout: Timeout in seconds
            env: Optional environment variables
            cwd: Optional working directory
            input_data: Optional stdin input

        Returns:
            ToolResult with execution results
        """

    @abstractmethod
    def execute_sync(
        self,
        command: List[str],
        timeout: int = 300,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        input_data: Optional[str] = None,
    ) -> ToolResult:
        """Synchronous execute for non-async contexts"""

    async def execute_batch(
        self,
        commands: List[List[str]],
        max_concurrent: int = 5,
        timeout: int = 300,
        env: Optional[Dict[str, str]] = None,
    ) -> List[ToolResult]:
        """
        Execute multiple commands in parallel with concurrency limit

        Args:
            commands: List of command lists
            max_concurrent: Maximum concurrent executions
            timeout: Timeout per command
            env: Optional environment variables

        Returns:
            List of ToolResults
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_limit(cmd: List[str]) -> ToolResult:
            async with semaphore:
                return await self.execute(cmd, timeout=timeout, env=env)

        return await asyncio.gather(*[execute_with_limit(cmd) for cmd in commands])

    async def execute_streaming(
        self,
        command: List[str],
        timeout: int = 300,
        env: Optional[Dict[str, str]] = None,
        stdout_callback: Optional[Callable[[str], None]] = None,
        stderr_callback: Optional[Callable[[str], None]] = None,
    ) -> ToolResult:
        """
        Execute with streaming output callbacks

        Args:
            command: Command as list
            timeout: Timeout in seconds
            env: Optional environment variables
            stdout_callback: Called for each stdout line
            stderr_callback: Called for each stderr line

        Returns:
            ToolResult with collected output
        """
        raise NotImplementedError("Streaming not supported by this executor")


class RealToolExecutor(ToolExecutor):
    """
    High-performance real tool execution with:
    - Semaphore-based concurrency control
    - Optimized buffer sizes
    - Process pool for CPU-bound operations
    - Memory-efficient streaming
    """

    def __init__(
        self,
        max_concurrent: int = 10,
        max_workers: int = 4,
        buffer_size: int = 65536,
        enable_streaming: bool = True,
    ):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.buffer_size = buffer_size
        self.enable_streaming = enable_streaming
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self._process_pool: Optional[ProcessPoolExecutor] = None
        self._command_cache: Dict[str, str] = {}  # Cache for command paths

    def _find_command(self, command: str) -> Optional[str]:
        """Find command path with caching"""
        if command in self._command_cache:
            return self._command_cache[command]

        path = shutil.which(command)
        if path:
            self._command_cache[command] = path
        return path

    async def execute(
        self,
        command: List[str],
        timeout: int = 300,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        input_data: Optional[str] = None,
    ) -> ToolResult:
        """Execute command with semaphore-controlled concurrency"""
        import time

        start_time = time.time()
        cmd_str = " ".join(command)

        async with self.semaphore:
            # Check if command exists
            if not self._find_command(command[0]):
                return ToolResult(
                    status=ToolResultStatus.NOT_FOUND,
                    returncode=-1,
                    stdout="",
                    stderr=f"Command not found: {command[0]}",
                    command=cmd_str,
                )

            # Merge environment variables
            process_env = os.environ.copy()
            if env:
                process_env.update(env)

            try:
                proc = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.PIPE if input_data else None,
                    env=process_env,
                    cwd=cwd,
                    limit=self.buffer_size,
                )

                try:
                    # Communicate with timeout
                    if input_data:
                        stdout, stderr = await asyncio.wait_for(proc.communicate(input=input_data.encode()), timeout=timeout)
                    else:
                        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

                    execution_time = int((time.time() - start_time) * 1000)

                    # Decode with error handling
                    stdout_str = stdout.decode("utf-8", errors="replace")
                    stderr_str = stderr.decode("utf-8", errors="replace")

                    # Truncate if too large (> 10MB)
                    max_output = 10 * 1024 * 1024
                    if len(stdout_str) > max_output:
                        stdout_str = stdout_str[:max_output] + "\n[Output truncated...]"
                    if len(stderr_str) > max_output:
                        stderr_str = stderr_str[:max_output] + "\n[Error output truncated...]"

                    return ToolResult(
                        status=(ToolResultStatus.SUCCESS if proc.returncode == 0 else ToolResultStatus.ERROR),
                        returncode=proc.returncode,
                        stdout=stdout_str,
                        stderr=stderr_str,
                        command=cmd_str,
                        execution_time_ms=execution_time,
                        metadata={
                            "pid": proc.pid,
                            "buffer_size": self.buffer_size,
                        },
                    )

                except asyncio.TimeoutError:
                    # Kill the process group
                    try:
                        proc.kill()
                        await asyncio.wait_for(proc.wait(), timeout=5)
                    except asyncio.TimeoutError:
                        # Force kill if necessary
                        try:
                            os.kill(proc.pid, 9)
                        except ProcessLookupError:
                            pass

                    return ToolResult(
                        status=ToolResultStatus.TIMEOUT,
                        returncode=-1,
                        stdout="",
                        stderr=f"Command timed out after {timeout}s",
                        command=cmd_str,
                        execution_time_ms=timeout * 1000,
                    )

            except FileNotFoundError:
                return ToolResult(
                    status=ToolResultStatus.NOT_FOUND,
                    returncode=-1,
                    stdout="",
                    stderr=f"Command not found: {command[0]}",
                    command=cmd_str,
                )
            except Exception as e:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    returncode=-1,
                    stdout="",
                    stderr=str(e),
                    command=cmd_str,
                )

    def execute_sync(
        self,
        command: List[str],
        timeout: int = 300,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        input_data: Optional[str] = None,
    ) -> ToolResult:
        """Synchronous execute using thread pool"""
        import time

        start_time = time.time()
        cmd_str = " ".join(command)

        # Merge environment variables
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=process_env,
                cwd=cwd,
                input=input_data,
            )
            execution_time = int((time.time() - start_time) * 1000)

            return ToolResult(
                status=(ToolResultStatus.SUCCESS if result.returncode == 0 else ToolResultStatus.ERROR),
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                command=cmd_str,
                execution_time_ms=execution_time,
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                status=ToolResultStatus.TIMEOUT,
                returncode=-1,
                stdout="",
                stderr=f"Command timed out after {timeout}s",
                command=cmd_str,
                execution_time_ms=timeout * 1000,
            )
        except FileNotFoundError:
            return ToolResult(
                status=ToolResultStatus.NOT_FOUND,
                returncode=-1,
                stdout="",
                stderr=f"Command not found: {command[0]}",
                command=cmd_str,
            )
        except Exception as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                returncode=-1,
                stdout="",
                stderr=str(e),
                command=cmd_str,
            )

    async def execute_streaming(
        self,
        command: List[str],
        timeout: int = 300,
        env: Optional[Dict[str, str]] = None,
        stdout_callback: Optional[Callable[[str], None]] = None,
        stderr_callback: Optional[Callable[[str], None]] = None,
    ) -> ToolResult:
        """Execute with streaming output"""
        import time

        start_time = time.time()
        cmd_str = " ".join(command)

        async with self.semaphore:
            # Check if command exists
            if not self._find_command(command[0]):
                return ToolResult(
                    status=ToolResultStatus.NOT_FOUND,
                    returncode=-1,
                    stdout="",
                    stderr=f"Command not found: {command[0]}",
                    command=cmd_str,
                )

            process_env = os.environ.copy()
            if env:
                process_env.update(env)

            try:
                proc = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=process_env,
                )

                stdout_lines = []
                stderr_lines = []

                async def read_stream(stream, callback, lines_list):
                    """Read stream line by line"""
                    while True:
                        line = await stream.readline()
                        if not line:
                            break
                        line_str = line.decode("utf-8", errors="replace")
                        lines_list.append(line_str)
                        if callback:
                            callback(line_str.rstrip())

                # Read both streams concurrently
                await asyncio.wait_for(
                    asyncio.gather(
                        read_stream(proc.stdout, stdout_callback, stdout_lines),
                        read_stream(proc.stderr, stderr_callback, stderr_lines),
                    ),
                    timeout=timeout,
                )

                await proc.wait()
                execution_time = int((time.time() - start_time) * 1000)

                return ToolResult(
                    status=(ToolResultStatus.SUCCESS if proc.returncode == 0 else ToolResultStatus.ERROR),
                    returncode=proc.returncode,
                    stdout="".join(stdout_lines),
                    stderr="".join(stderr_lines),
                    command=cmd_str,
                    execution_time_ms=execution_time,
                )

            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return ToolResult(
                    status=ToolResultStatus.TIMEOUT,
                    returncode=-1,
                    stdout="",
                    stderr=f"Command timed out after {timeout}s",
                    command=cmd_str,
                    execution_time_ms=timeout * 1000,
                )
            except Exception as e:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    returncode=-1,
                    stdout="",
                    stderr=str(e),
                    command=cmd_str,
                )

    async def execute_with_retry(
        self,
        command: List[str],
        timeout: int = 300,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        env: Optional[Dict[str, str]] = None,
    ) -> ToolResult:
        """Execute with automatic retry on failure"""
        last_result = None

        for attempt in range(max_retries + 1):
            result = await self.execute(command, timeout=timeout, env=env)

            if result.success:
                return result

            last_result = result

            if attempt < max_retries:
                logger.warning(
                    f"Command failed (attempt {attempt + 1}/{max_retries + 1}), "
                    f"retrying in {retry_delay}s: {result.stderr[:200]}"
                )
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

        return last_result

    async def execute_in_pool(
        self,
        command: List[str],
        timeout: int = 300,
    ) -> ToolResult:
        """Execute in process pool for CPU-bound operations"""
        if self._process_pool is None:
            self._process_pool = ProcessPoolExecutor(max_workers=2)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._process_pool,
            self.execute_sync,
            command,
            timeout,
        )

    def shutdown(self):
        """Shutdown executor and release resources"""
        self._thread_pool.shutdown(wait=True)
        if self._process_pool:
            self._process_pool.shutdown(wait=True)


class MockToolExecutor(ToolExecutor):
    """
    Enhanced mock implementation for tests.
    Supports predefined responses, pattern matching, and call tracking.
    """

    def __init__(self):
        self.mock_responses: Dict[str, ToolResult] = {}
        self.pattern_responses: List[Tuple[Callable, ToolResult]] = []
        self.call_history: List[Tuple[List[str], ToolResult]] = []
        self.default_result = ToolResult(
            status=ToolResultStatus.SUCCESS,
            returncode=0,
            stdout="",
            stderr="",
            command="mock",
        )
        self.delay: float = 0.0

    def add_mock_response(self, command_pattern: str, result: ToolResult):
        """Add a mock response for exact or partial command match"""
        self.mock_responses[command_pattern] = result

    def add_pattern_response(
        self,
        matcher: Callable[[List[str]], bool],
        result: ToolResult,
    ):
        """Add a mock response with custom matcher function"""
        self.pattern_responses.append((matcher, result))

    def add_mock_from_fixture(self, command_pattern: str, fixture_path: str):
        """Load mock result from a fixture file"""
        import json

        with open(fixture_path, "r") as f:
            data = json.load(f)

        result = ToolResult(
            status=ToolResultStatus(data.get("status", "success")),
            returncode=data.get("returncode", 0),
            stdout=data.get("stdout", ""),
            stderr=data.get("stderr", ""),
            command=data.get("command", command_pattern),
            execution_time_ms=data.get("execution_time_ms", 100),
            metadata=data.get("metadata"),
        )
        self.add_mock_response(command_pattern, result)

    def set_delay(self, delay: float):
        """Set artificial delay for all responses (simulates real execution)"""
        self.delay = delay

    def _find_response(self, command: List[str]) -> ToolResult:
        """Find matching mock response"""
        cmd_str = " ".join(command)

        # Check pattern matchers first
        for matcher, result in self.pattern_responses:
            if matcher(command):
                return result

        # Check exact/partial matches
        for pattern, result in self.mock_responses.items():
            if pattern in cmd_str:
                return result

        return self.default_result

    async def execute(
        self,
        command: List[str],
        timeout: int = 300,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        input_data: Optional[str] = None,
    ) -> ToolResult:
        """Return mock result with optional delay"""
        if self.delay > 0:
            await asyncio.sleep(self.delay)

        result = self._find_response(command)
        result.command = " ".join(command)
        self.call_history.append((command, result))
        return result

    def execute_sync(
        self,
        command: List[str],
        timeout: int = 300,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        input_data: Optional[str] = None,
    ) -> ToolResult:
        """Return mock result synchronously"""
        import time

        if self.delay > 0:
            time.sleep(self.delay)

        result = self._find_response(command)
        result.command = " ".join(command)
        self.call_history.append((command, result))
        return result

    async def execute_batch(
        self,
        commands: List[List[str]],
        max_concurrent: int = 5,
        timeout: int = 300,
        env: Optional[Dict[str, str]] = None,
    ) -> List[ToolResult]:
        """Execute batch of mock commands"""
        return [await self.execute(cmd, timeout, env) for cmd in commands]

    def was_called_with(self, pattern: str) -> bool:
        """Check if a command with pattern was called"""
        for cmd, _ in self.call_history:
            if pattern in " ".join(cmd):
                return True
        return False

    def get_calls(self) -> List[Tuple[List[str], ToolResult]]:
        """Get all called commands"""
        return self.call_history.copy()

    def clear_history(self):
        """Clear call history"""
        self.call_history.clear()

    def get_call_count(self) -> int:
        """Get total number of calls"""
        return len(self.call_history)


# =============================================================================
# Global Executor Management
# =============================================================================

_default_executor: Optional[ToolExecutor] = None
_executor_lock = asyncio.Lock()


async def get_executor() -> ToolExecutor:
    """Get the current executor (thread-safe)"""
    global _default_executor
    if _default_executor is None:
        async with _executor_lock:
            if _default_executor is None:
                _default_executor = RealToolExecutor(
                    max_concurrent=10,
                    max_workers=4,
                )
    return _default_executor


def set_executor(executor: ToolExecutor):
    """Set the global executor (for testing)"""
    global _default_executor
    _default_executor = executor


def reset_executor():
    """Reset executor to RealToolExecutor"""
    global _default_executor
    if isinstance(_default_executor, RealToolExecutor):
        _default_executor.shutdown()
    _default_executor = RealToolExecutor()


async def close_executor():
    """Close and cleanup global executor"""
    global _default_executor
    if isinstance(_default_executor, RealToolExecutor):
        _default_executor.shutdown()
    _default_executor = None


# =============================================================================
# Convenience Functions
# =============================================================================


async def run_command(
    command: List[str],
    timeout: int = 300,
    env: Optional[Dict[str, str]] = None,
    cwd: Optional[str] = None,
) -> ToolResult:
    """Convenience function to run a command"""
    executor = await get_executor()
    return await executor.execute(command, timeout, env, cwd)


async def run_commands_parallel(
    commands: List[List[str]],
    max_concurrent: int = 5,
    timeout: int = 300,
) -> List[ToolResult]:
    """Convenience function to run multiple commands in parallel"""
    executor = await get_executor()
    return await executor.execute_batch(commands, max_concurrent, timeout)


async def run_command_with_retry(
    command: List[str],
    timeout: int = 300,
    max_retries: int = 3,
) -> ToolResult:
    """Convenience function to run command with retry"""
    executor = await get_executor()
    if isinstance(executor, RealToolExecutor):
        return await executor.execute_with_retry(command, timeout, max_retries)
    return await executor.execute(command, timeout)


__all__ = [
    # Enums and Classes
    "ToolResultStatus",
    "ToolResult",
    "ToolExecutor",
    "RealToolExecutor",
    "MockToolExecutor",
    # Functions
    "get_executor",
    "set_executor",
    "reset_executor",
    "close_executor",
    "run_command",
    "run_commands_parallel",
    "run_command_with_retry",
]
