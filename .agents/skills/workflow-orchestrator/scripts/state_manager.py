#!/usr/bin/env python3
"""
Smart State Management

Manages workflow state to prevent redundant scans and enable
resumable workflows using persistent storage.
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("state_manager")


@dataclass
class TestRecord:
    """Record of a test execution."""

    target: str
    module_name: str
    inputs_hash: str
    result_hash: str
    timestamp: datetime
    findings_count: int
    execution_time: float
    metadata: Dict[str, Any]


@dataclass
class TestedPath:
    """Record of a tested path/endpoint."""

    path: str
    method: str
    params: Dict[str, Any]
    timestamp: datetime
    result: str  # success, failure, error


class StateManager:
    """
    Manages workflow state with persistent storage.

    Features:
    - Deduplication of tests based on inputs
    - Path tracking to avoid redundant crawling
    - Result caching for fast replays
    - Expiration of old results
    """

    def __init__(self, storage_path: Optional[str] = None, cache_duration_hours: int = 24, max_cache_entries: int = 10000):
        self.storage_path = Path(storage_path) if storage_path else None
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.max_cache_entries = max_cache_entries

        # In-memory caches
        self._test_cache: Dict[str, TestRecord] = {}
        self._path_cache: Dict[str, Set[str]] = {}  # target -> paths
        self._result_cache: Dict[str, Any] = {}

        # Tracking current target
        self._current_target: Optional[str] = None

        # Lock for thread safety
        self._lock = asyncio.Lock()

        # Load existing state if available
        if self.storage_path:
            self._load_state()

    def for_target(self, target: str) -> "StateManager":
        """Create a state manager scoped to a specific target."""
        new_manager = StateManager(
            storage_path=str(self.storage_path) if self.storage_path else None,
            cache_duration_hours=int(self.cache_duration.total_seconds() / 3600),
            max_cache_entries=self.max_cache_entries,
        )
        new_manager._test_cache = self._test_cache
        new_manager._path_cache = self._path_cache
        new_manager._result_cache = self._result_cache
        new_manager._current_target = target
        return new_manager

    def _make_key(self, target: str, module_name: str, inputs: Dict) -> str:
        """Create a unique key for a test."""
        key_data = f"{target}:{module_name}:{json.dumps(inputs, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]

    def _make_path_key(self, path: str, method: str, params: Dict) -> str:
        """Create a unique key for a tested path."""
        key_data = f"{method}:{path}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]

    async def is_tested(self, target: str, module_name: str, inputs: Dict, max_age_hours: Optional[int] = None) -> bool:
        """
        Check if a test has already been performed.

        Args:
            target: Target identifier
            module_name: Module that performed the test
            inputs: Test inputs
            max_age_hours: Optional max age for valid cache

        Returns:
            True if test was performed and cache is valid
        """
        async with self._lock:
            key = self._make_key(target, module_name, inputs)

            if key not in self._test_cache:
                return False

            record = self._test_cache[key]

            # Check expiration
            max_age = timedelta(hours=max_age_hours) if max_age_hours else self.cache_duration
            if datetime.now() - record.timestamp > max_age:
                logger.debug(f"Cache expired for {key}")
                return False

            logger.debug(f"Cache hit for {module_name} on {target}")
            return True

    async def get_result(self, target: str, module_name: str, inputs: Optional[Dict] = None) -> Optional[Any]:
        """
        Get cached result for a test.

        Args:
            target: Target identifier
            module_name: Module that performed the test
            inputs: Test inputs (optional for lookup)

        Returns:
            Cached result or None
        """
        async with self._lock:
            key = self._make_key(target, module_name, inputs or {})
            return self._result_cache.get(key)

    async def store(
        self,
        target: str,
        module_name: str,
        result: Any,
        inputs: Optional[Dict] = None,
        execution_time: float = 0.0,
        metadata: Optional[Dict] = None,
    ):
        """
        Store a test result.

        Args:
            target: Target identifier
            module_name: Module that performed the test
            result: Test result
            inputs: Test inputs
            execution_time: Execution time in seconds
            metadata: Additional metadata
        """
        async with self._lock:
            key = self._make_key(target, module_name, inputs or {})

            # Calculate hashes
            inputs_hash = hashlib.sha256(json.dumps(inputs or {}, sort_keys=True).encode()).hexdigest()[:16]

            result_str = json.dumps(result, default=str, sort_keys=True)
            result_hash = hashlib.sha256(result_str.encode()).hexdigest()[:16]

            # Extract findings count
            findings_count = 0
            if hasattr(result, "findings"):
                findings_count = len(result.findings)
            elif isinstance(result, dict):
                findings_count = len(result.get("findings", []))

            # Create record
            record = TestRecord(
                target=target,
                module_name=module_name,
                inputs_hash=inputs_hash,
                result_hash=result_hash,
                timestamp=datetime.now(),
                findings_count=findings_count,
                execution_time=execution_time,
                metadata=metadata or {},
            )

            # Store in cache
            self._test_cache[key] = record
            self._result_cache[key] = result

            # Cleanup old entries if needed
            if len(self._test_cache) > self.max_cache_entries:
                await self._cleanup_old_entries()

            # Persist to disk
            if self.storage_path:
                await self._save_state()

            logger.debug(f"Stored result for {module_name} on {target}")

    async def add_tested_path(self, path: str, method: str = "GET", params: Optional[Dict] = None, result: str = "success"):
        """
        Mark a path as tested.

        Args:
            path: URL path
            method: HTTP method
            params: Request parameters
            result: Test result (success, failure, error)
        """
        if not self._current_target:
            raise ValueError("No target set, use for_target() first")

        async with self._lock:
            if self._current_target not in self._path_cache:
                self._path_cache[self._current_target] = set()

            path_key = self._make_path_key(path, method, params or {})
            self._path_cache[self._current_target].add(path_key)

            logger.debug(f"Marked path as tested: {method} {path}")

    async def is_path_tested(self, path: str, method: str = "GET", params: Optional[Dict] = None) -> bool:
        """
        Check if a path has already been tested.

        Args:
            path: URL path
            method: HTTP method
            params: Request parameters

        Returns:
            True if path was tested
        """
        if not self._current_target:
            return False

        async with self._lock:
            if self._current_target not in self._path_cache:
                return False

            path_key = self._make_path_key(path, method, params or {})
            return path_key in self._path_cache[self._current_target]

    async def get_tested_paths(self) -> List[Dict]:
        """Get all tested paths for current target."""
        if not self._current_target:
            return []

        async with self._lock:
            paths = self._path_cache.get(self._current_target, set())
            return [{"hash": p} for p in paths]  # Return hashes only for memory

    async def get_tested_count(self) -> int:
        """Get number of tested paths for current target."""
        if not self._current_target:
            return 0

        async with self._lock:
            return len(self._path_cache.get(self._current_target, set()))

    async def clear_target(self, target: Optional[str] = None):
        """Clear cached data for a target."""
        target = target or self._current_target
        if not target:
            return

        async with self._lock:
            # Clear path cache
            if target in self._path_cache:
                del self._path_cache[target]

            # Clear test cache for target
            keys_to_remove = [k for k, v in self._test_cache.items() if v.target == target]
            for key in keys_to_remove:
                del self._test_cache[key]
                if key in self._result_cache:
                    del self._result_cache[key]

            logger.info(f"Cleared state for {target}")

    async def _cleanup_old_entries(self):
        """Remove old cache entries."""
        cutoff = datetime.now() - self.cache_duration

        keys_to_remove = [k for k, v in self._test_cache.items() if v.timestamp < cutoff]

        for key in keys_to_remove:
            del self._test_cache[key]
            if key in self._result_cache:
                del self._result_cache[key]

        logger.debug(f"Cleaned up {len(keys_to_remove)} old entries")

    async def _save_state(self):
        """Save state to disk."""
        if not self.storage_path:
            return

        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)

            state_file = self.storage_path / "workflow_state.json"

            state = {
                "test_cache": {k: {**asdict(v), "timestamp": v.timestamp.isoformat()} for k, v in self._test_cache.items()},
                "path_cache": {k: list(v) for k, v in self._path_cache.items()},
                "saved_at": datetime.now().isoformat(),
            }

            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        """Load state from disk."""
        if not self.storage_path:
            return

        try:
            state_file = self.storage_path / "workflow_state.json"

            if not state_file.exists():
                return

            with open(state_file) as f:
                state = json.load(f)

            # Load test cache
            for key, data in state.get("test_cache", {}).items():
                self._test_cache[key] = TestRecord(
                    target=data["target"],
                    module_name=data["module_name"],
                    inputs_hash=data["inputs_hash"],
                    result_hash=data["result_hash"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    findings_count=data["findings_count"],
                    execution_time=data["execution_time"],
                    metadata=data.get("metadata", {}),
                )

            # Load path cache
            for target, paths in state.get("path_cache", {}).items():
                self._path_cache[target] = set(paths)

            logger.info(
                f"Loaded state: {len(self._test_cache)} tests, " f"{sum(len(p) for p in self._path_cache.values())} paths"
            )

        except Exception as e:
            logger.error(f"Failed to load state: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get state manager statistics."""
        return {
            "cached_tests": len(self._test_cache),
            "cached_targets": len(self._path_cache),
            "total_tested_paths": sum(len(p) for p in self._path_cache.values()),
            "current_target": self._current_target,
            "storage_path": str(self.storage_path) if self.storage_path else None,
        }


class SmartMemory:
    """
    High-level interface for workflow memory.

    Provides semantic operations on top of StateManager.
    """

    def __init__(self, state_manager: StateManager):
        self.state = state_manager

    async def should_scan_port(self, host: str, port: int, protocol: str = "tcp") -> bool:
        """Check if a port should be scanned."""
        key = f"{protocol}:{host}:{port}"
        return not await self.state.is_path_tested(key, "PORT_SCAN")

    async def mark_port_scanned(self, host: str, port: int, protocol: str = "tcp", state: str = "open"):
        """Mark a port as scanned."""
        key = f"{protocol}:{host}:{port}"
        await self.state.add_tested_path(key, "PORT_SCAN", {"state": state})

    async def should_test_endpoint(self, path: str, method: str = "GET", params: Optional[Dict] = None) -> bool:
        """Check if an endpoint should be tested."""
        return not await self.state.is_path_tested(path, method, params)

    async def get_unique_params(self, base_path: str, param_sets: List[Dict]) -> List[Dict]:
        """
        Filter parameter sets to only untested combinations.

        Args:
            base_path: Base URL path
            param_sets: List of parameter dictionaries

        Returns:
            List of untested parameter combinations
        """
        unique = []
        for params in param_sets:
            if not await self.state.is_path_tested(base_path, "GET", params):
                unique.append(params)
        return unique

    async def find_similar_tests(self, module_name: str, threshold: float = 0.8) -> List[Dict]:
        """
        Find tests with similar inputs.

        Args:
            module_name: Module to search for
            threshold: Similarity threshold (0-1)

        Returns:
            List of similar test records
        """
        # Simple implementation - could use more sophisticated similarity
        similar = []
        for key, record in self.state._test_cache.items():
            if record.module_name == module_name:
                similar.append(
                    {
                        "target": record.target,
                        "inputs_hash": record.inputs_hash,
                        "timestamp": record.timestamp.isoformat(),
                        "findings": record.findings_count,
                    }
                )
        return similar


if __name__ == "__main__":
    # Test state manager
    async def test():
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StateManager(storage_path=tmpdir)

            # Test basic operations
            target = "example.com"
            scoped = manager.for_target(target)

            # Check if tested (should be False)
            is_tested = await scoped.is_tested(target, "nmap", {"ports": "80,443"})
            print(f"Is tested (before): {is_tested}")

            # Store result
            await scoped.store(
                target=target,
                module_name="nmap",
                result={"open_ports": [80, 443]},
                inputs={"ports": "80,443"},
                execution_time=5.0,
            )

            # Check again (should be True)
            is_tested = await scoped.is_tested(target, "nmap", {"ports": "80,443"})
            print(f"Is tested (after): {is_tested}")

            # Get cached result
            result = await scoped.get_result(target, "nmap", {"ports": "80,443"})
            print(f"Cached result: {result}")

            # Test path tracking
            await scoped.add_tested_path("/admin", "GET", {"id": "1"})
            is_path_tested = await scoped.is_path_tested("/admin", "GET", {"id": "1"})
            print(f"Path tested: {is_path_tested}")

            # Stats
            print(f"\nStats: {manager.get_stats()}")

    asyncio.run(test())
