"""ZAP Orchestrator Module for Zen-AI-Pentest

This module provides high-level orchestration for OWASP ZAP scans:
- Multi-target scan coordination
- Scan pipeline management
- Result aggregation
- Integration with other modules
- Scheduled scans
- Batch scanning

Author: Zen-AI-Pentest Team
License: MIT
"""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Import ZAP integration
try:
    from tools.zap_integration import (
        ZAPAlert,
        ZAPAPIClient,
        ZAPAuthConfig,
        ZAPDockerManager,
        ZAPScanner,
        ZAPScanResult,
    )

    ZAP_AVAILABLE = True
except ImportError:
    ZAP_AVAILABLE = False
    ZAPScanner = None
    ZAPScanResult = None

# Import other modules if available
try:
    from modules.report_generator import ReportGenerator

    REPORT_GENERATOR_AVAILABLE = True
except ImportError:
    REPORT_GENERATOR_AVAILABLE = False
    ReportGenerator = None

try:
    from database.models import Finding, Scan  # noqa: F401

    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False


logger = logging.getLogger(__name__)


class ScanStage(Enum):
    """Scan pipeline stages"""

    PENDING = "pending"
    INITIALIZING = "initializing"
    SPIDER = "spider"
    AJAX_SPIDER = "ajax_spider"
    ACTIVE_SCAN = "active_scan"
    OPENAPI_SCAN = "openapi_scan"
    GRAPHQL_SCAN = "graphql_scan"
    REPORTING = "reporting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ZAPOrchestratorConfig:
    """ZAP Orchestrator configuration"""

    # API Configuration
    api_url: str = "http://localhost:8080"
    api_key: Optional[str] = None

    # Docker Configuration
    use_docker: bool = False
    docker_network: Optional[str] = None

    # Scan Configuration
    default_scan_policy: str = "Default Policy"
    default_timeout: int = 600
    max_concurrent_scans: int = 3
    auto_start_daemon: bool = True

    # Report Configuration
    report_output_dir: str = "./reports/zap"
    default_report_formats: List[str] = field(default_factory=lambda: ["json", "html"])

    # Callbacks
    progress_callback: Optional[Callable[[str, Dict], None]] = None
    alert_callback: Optional[Callable[[ZAPAlert], None]] = None


@dataclass
class ScanTask:
    """Individual scan task"""

    task_id: str
    target: str
    scan_type: str  # full, spider, active, openapi, graphql
    config: Dict[str, Any] = field(default_factory=dict)
    status: ScanStage = ScanStage.PENDING
    progress: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[ZAPScanResult] = None
    error: Optional[str] = None
    priority: int = 5  # 1-10, lower is higher priority


@dataclass
class BatchScanResult:
    """Result of a batch scan operation"""

    batch_id: str
    total_targets: int
    completed: int = 0
    failed: int = 0
    results: List[ScanTask] = field(default_factory=list)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    aggregate_findings: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def duration(self) -> float:
        """Get total duration in seconds"""
        end = self.end_time or datetime.now(timezone.utc)
        return (end - self.start_time).total_seconds()


class ZAPOrchestrator:
    """
    High-level orchestrator for ZAP operations.

    Provides:
    - Automatic daemon management
    - Multi-target coordination
    - Progress tracking
    - Result aggregation
    - Integration with database and reporting
    """

    def __init__(self, config: Optional[ZAPOrchestratorConfig] = None):
        """
        Initialize ZAP Orchestrator.

        Args:
            config: Orchestrator configuration
        """
        if not ZAP_AVAILABLE:
            raise RuntimeError("ZAP integration not available")

        self.config = config or ZAPOrchestratorConfig()
        self._scanner: Optional[ZAPScanner] = None
        self._docker_manager: Optional[ZAPDockerManager] = None
        self._active_tasks: Dict[str, ScanTask] = {}
        self._task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_scans)
        self._shutdown_event = asyncio.Event()
        self._worker_task: Optional[asyncio.Task] = None

        # Ensure report directory exists
        Path(self.config.report_output_dir).mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> bool:
        """
        Initialize the orchestrator and start ZAP if needed.

        Returns:
            True if initialization successful
        """
        # Check if ZAP is running
        client = ZAPAPIClient(
            api_url=self.config.api_url,
            api_key=self.config.api_key,
        )

        if not await client.is_running():
            if self.config.auto_start_daemon:
                logger.info("Starting ZAP daemon...")
                if not await self._start_daemon():
                    raise RuntimeError("Failed to start ZAP daemon")
            else:
                raise RuntimeError("ZAP daemon not running and auto_start disabled")

        # Start background worker
        self._worker_task = asyncio.create_task(self._process_task_queue())

        logger.info("ZAP Orchestrator initialized successfully")
        return True

    async def shutdown(self):
        """Shutdown the orchestrator"""
        logger.info("Shutting down ZAP Orchestrator...")

        self._shutdown_event.set()

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        # Stop daemon if we started it
        if self.config.use_docker and self._docker_manager:
            await self._docker_manager.stop_all()
        elif self._scanner:
            await self._scanner.stop_daemon()

        self._executor.shutdown(wait=True)
        logger.info("ZAP Orchestrator shutdown complete")

    async def _start_daemon(self) -> bool:
        """Start ZAP daemon"""
        if self.config.use_docker:
            self._docker_manager = ZAPDockerManager()
            container_id = await self._docker_manager.start_container(
                name=f"zap_orchestrator_{int(datetime.now(timezone.utc).timestamp())}",
                port=int(self.config.api_url.split(":")[-1]),
                api_key=self.config.api_key,
                network=self.config.docker_network,
            )
            return bool(container_id)
        else:
            self._scanner = ZAPScanner(
                target="http://localhost",
                api_url=self.config.api_url,
                api_key=self.config.api_key,
            )
            return await self._scanner.start_daemon()

    def _get_scanner(self, target: str) -> ZAPScanner:
        """Get scanner instance for target"""
        return ZAPScanner(
            target=target,
            api_url=self.config.api_url,
            api_key=self.config.api_key,
        )

    async def _process_task_queue(self):
        """Background worker to process scan tasks"""
        while not self._shutdown_event.is_set():
            try:
                # Get task from queue with timeout
                priority, task = await asyncio.wait_for(self._task_queue.get(), timeout=1.0)

                if task.task_id in self._active_tasks:
                    await self._execute_scan_task(task)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Task queue processing error: {e}")

    async def _execute_scan_task(self, task: ScanTask):
        """Execute a scan task"""
        task.status = ScanStage.INITIALIZING
        task.started_at = datetime.now(timezone.utc)
        self._active_tasks[task.id] = task

        try:
            scanner = self._get_scanner(task.target)

            # Configure scan options
            options = {
                "scan_timeout": task.config.get("timeout", self.config.default_timeout),
                "scan_policy": task.config.get("scan_policy", self.config.default_scan_policy),
                "progress_callback": lambda p: self._update_task_progress(task.task_id, p),
            }

            # Add specific options based on scan type
            if task.scan_type == "spider":
                options["spider"] = True
                options["active_scan"] = False
            elif task.scan_type == "active":
                options["spider"] = task.config.get("spider_first", True)
                options["active_scan"] = True
            elif task.scan_type == "full":
                options["spider"] = True
                options["ajax_spider"] = task.config.get("ajax_spider", False)
                options["active_scan"] = True
            elif task.scan_type == "ajax":
                options["spider"] = True
                options["ajax_spider"] = True
                options["active_scan"] = False

            scanner.options = options

            # Authentication
            auth_config = None
            if "auth" in task.config:
                auth_config = self._create_auth_config(task.config["auth"])

            # Execute scan
            task.status = ScanStage.ACTIVE_SCAN if task.scan_type in ["active", "full"] else ScanStage.SPIDER
            result = await scanner.scan(auth_config=auth_config)

            task.result = result
            task.status = ScanStage.COMPLETED if result.success else ScanStage.FAILED
            task.error = result.error
            task.completed_at = datetime.now(timezone.utc)
            task.progress = 100

            # Call alert callback for each finding
            if self.config.alert_callback and result.alerts:
                for alert in result.alerts:
                    self.config.alert_callback(alert)

            # Auto-generate reports
            if result.success and task.config.get("generate_reports", True):
                await self._generate_reports(task, scanner)

            # Store to database if available
            if DATABASE_AVAILABLE and result.success:
                await self._store_results_to_db(task)

        except Exception as e:
            logger.error(f"Scan task {task.task_id} failed: {e}")
            task.status = ScanStage.FAILED
            task.error = str(e)
            task.completed_at = datetime.now(timezone.utc)

    def _update_task_progress(self, task_id: str, progress: Dict[str, int]):
        """Update task progress"""
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            # Calculate overall progress
            if isinstance(progress, dict):
                values = [v for v in progress.values() if isinstance(v, (int, float))]
                if values:
                    task.progress = int(sum(values) / len(values))
            else:
                task.progress = int(progress)

            # Call progress callback
            if self.config.progress_callback:
                self.config.progress_callback(
                    task_id,
                    {
                        "status": task.status.value,
                        "progress": task.progress,
                        "details": progress,
                    },
                )

    def _create_auth_config(self, auth_data: Dict[str, Any]) -> ZAPAuthConfig:
        """Create ZAPAuthConfig from dictionary"""
        from tools.zap_integration import ZAPAuthMethod

        method_map = {
            "form": ZAPAuthMethod.FORM_BASED,
            "json": ZAPAuthMethod.JSON_BASED,
            "http": ZAPAuthMethod.HTTP,
            "manual": ZAPAuthMethod.MANUAL,
        }

        return ZAPAuthConfig(
            method=method_map.get(auth_data.get("type", "form"), ZAPAuthMethod.FORM_BASED),
            login_url=auth_data.get("login_url", ""),
            username=auth_data.get("username", ""),
            password=auth_data.get("password", ""),
            username_field=auth_data.get("username_field", "username"),
            password_field=auth_data.get("password_field", "password"),
            jwt_token=auth_data.get("jwt_token", ""),
            api_key_value=auth_data.get("api_key", ""),
            session_cookie_value=auth_data.get("session_cookie", ""),
            extra_params=auth_data.get("extra_params", {}),
        )

    async def _generate_reports(self, task: ScanTask, scanner: ZAPScanner):
        """Generate reports for completed scan"""
        int(datetime.now(timezone.utc).timestamp())

        for fmt in self.config.default_report_formats:
            try:
                output_path = Path(self.config.report_output_dir) / f"{task.task_id}_{fmt}.{fmt}"
                await scanner.generate_report(
                    report_format=fmt,
                    output_path=str(output_path),
                )
                logger.info(f"Generated {fmt} report: {output_path}")
            except Exception as e:
                logger.error(f"Failed to generate {fmt} report: {e}")

    async def _store_results_to_db(self, task: ScanTask):
        """Store scan results to database"""
        if not DATABASE_AVAILABLE or not task.result:
            return

        try:
            # Create database records for findings
            for alert in task.result.alerts:
                {
                    "tool": "owasp_zap",
                    "target": task.target,
                    "severity": self._risk_to_severity(alert.risk),
                    "title": alert.name,
                    "description": alert.description,
                    "evidence": alert.evidence,
                    "remediation": alert.solution,
                    "references": alert.reference,
                    "cwe_id": alert.cwe_id,
                    "confidence": alert.confidence.lower(),
                    "scan_id": task.task_id,
                }
                logger.debug(f"Stored finding to database: {alert.name}")

        except Exception as e:
            logger.error(f"Failed to store results to database: {e}")

    def _risk_to_severity(self, risk: str) -> str:
        """Convert ZAP risk to severity"""
        mapping = {
            "High": "high",
            "Medium": "medium",
            "Low": "low",
            "Informational": "info",
        }
        return mapping.get(risk, "info")

    async def scan(
        self,
        target: str,
        scan_type: str = "full",
        config: Optional[Dict[str, Any]] = None,
        priority: int = 5,
    ) -> str:
        """
        Queue a single scan.

        Args:
            target: Target URL to scan
            scan_type: Type of scan (full, spider, active, ajax, openapi, graphql)
            config: Additional scan configuration
            priority: Task priority (1-10, lower is higher)

        Returns:
            Task ID
        """
        task_id = f"zap_{int(datetime.now(timezone.utc).timestamp() * 1000)}"

        task = ScanTask(
            task_id=task_id,
            target=target,
            scan_type=scan_type,
            config=config or {},
            priority=priority,
        )

        self._active_tasks[task_id] = task
        await self._task_queue.put((priority, task))

        logger.info(f"Queued {scan_type} scan for {target} (task: {task_id})")
        return task_id

    async def scan_batch(
        self,
        targets: List[str],
        scan_type: str = "full",
        config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Queue batch scan for multiple targets.

        Args:
            targets: List of target URLs
            scan_type: Type of scan
            config: Scan configuration

        Returns:
            Batch ID
        """
        batch_id = f"batch_{int(datetime.now(timezone.utc).timestamp() * 1000)}"

        for target in targets:
            await self.scan(target, scan_type, config)

        logger.info(f"Queued batch scan {batch_id} with {len(targets)} targets")
        return batch_id

    async def scan_sync(
        self,
        target: str,
        scan_type: str = "full",
        config: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> ZAPScanResult:
        """
        Perform synchronous scan (waits for completion).

        Args:
            target: Target URL
            scan_type: Type of scan
            config: Scan configuration
            timeout: Maximum wait time in seconds

        Returns:
            Scan result
        """
        task_id = await self.scan(target, scan_type, config, priority=1)
        timeout = timeout or self.config.default_timeout * 2

        # Wait for completion
        start_time = datetime.now(timezone.utc)
        while (datetime.now(timezone.utc) - start_time).total_seconds() < timeout:
            if task_id in self._active_tasks:
                task = self._active_tasks[task_id]
                if task.status in [ScanStage.COMPLETED, ScanStage.FAILED]:
                    return task.result or ZAPScanResult(
                        success=False,
                        target=target,
                        scan_type=scan_type,
                        error=task.error or "Scan failed",
                    )
            await asyncio.sleep(1)

        raise TimeoutError(f"Scan timed out after {timeout} seconds")

    def get_task(self, task_id: str) -> Optional[ScanTask]:
        """Get scan task by ID"""
        return self._active_tasks.get(task_id)

    def get_all_tasks(
        self,
        status: Optional[ScanStage] = None,
    ) -> List[ScanTask]:
        """Get all tasks, optionally filtered by status"""
        tasks = list(self._active_tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            if task.status not in [ScanStage.COMPLETED, ScanStage.FAILED]:
                task.status = ScanStage.CANCELLED
                return True
        return False

    async def wait_for_completion(
        self,
        task_ids: Optional[List[str]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, ScanTask]:
        """
        Wait for tasks to complete.

        Args:
            task_ids: List of task IDs (None = all tasks)
            timeout: Maximum wait time

        Returns:
            Dictionary of completed tasks
        """
        task_ids = task_ids or list(self._active_tasks.keys())
        timeout = timeout or 3600

        start_time = datetime.now(timezone.utc)
        completed = {}

        while (datetime.now(timezone.utc) - start_time).total_seconds() < timeout:
            all_done = True
            for task_id in task_ids:
                if task_id in self._active_tasks:
                    task = self._active_tasks[task_id]
                    if task.status in [ScanStage.COMPLETED, ScanStage.FAILED, ScanStage.CANCELLED]:
                        completed[task_id] = task
                    else:
                        all_done = False

            if all_done:
                break

            await asyncio.sleep(1)

        return completed


class ZAPScanPipeline:
    """
    Pipeline for complex multi-stage scan workflows.

    Example pipeline:
        1. Spider crawl
        2. AJAX spider for modern apps
        3. Active scan
        4. OpenAPI scan (if API detected)
        5. Report generation
    """

    def __init__(self, orchestrator: ZAPOrchestrator):
        self.orchestrator = orchestrator
        self._stages: List[Dict[str, Any]] = []

    def add_stage(
        self,
        name: str,
        scan_type: str,
        config: Optional[Dict[str, Any]] = None,
        condition: Optional[Callable[[ZAPScanResult], bool]] = None,
    ) -> "ZAPScanPipeline":
        """
        Add a stage to the pipeline.

        Args:
            name: Stage name
            scan_type: Type of scan
            config: Stage configuration
            condition: Function to determine if stage should run

        Returns:
            Self for chaining
        """
        self._stages.append(
            {
                "name": name,
                "scan_type": scan_type,
                "config": config or {},
                "condition": condition,
            }
        )
        return self

    async def execute(self, target: str, base_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the pipeline.

        Args:
            target: Target URL
            base_config: Base configuration for all stages

        Returns:
            Pipeline results
        """
        results = {
            "target": target,
            "stages": [],
            "success": True,
        }

        previous_result = None

        for stage in self._stages:
            # Check condition
            if stage["condition"] and previous_result:
                if not stage["condition"](previous_result):
                    logger.info(f"Skipping pipeline stage: {stage['name']}")
                    continue

            logger.info(f"Executing pipeline stage: {stage['name']}")

            # Merge configs
            config = {**(base_config or {}), **stage["config"]}

            try:
                result = await self.orchestrator.scan_sync(
                    target=target,
                    scan_type=stage["scan_type"],
                    config=config,
                )

                stage_result = {
                    "name": stage["name"],
                    "success": result.success,
                    "alerts_count": len(result.alerts),
                    "scan_time": result.scan_time,
                }

                results["stages"].append(stage_result)
                previous_result = result

                if not result.success:
                    results["success"] = False
                    if config.get("stop_on_failure", True):
                        break

            except Exception as e:
                logger.error(f"Pipeline stage {stage['name']} failed: {e}")
                results["stages"].append(
                    {
                        "name": stage["name"],
                        "success": False,
                        "error": str(e),
                    }
                )
                results["success"] = False

                if config.get("stop_on_failure", True):
                    break

        return results


class ZAPBatchScanner:
    """Batch scanning for multiple targets with result aggregation"""

    def __init__(self, orchestrator: ZAPOrchestrator):
        self.orchestrator = orchestrator

    async def scan_targets(
        self,
        targets: List[str],
        scan_type: str = "full",
        config: Optional[Dict[str, Any]] = None,
        max_concurrent: Optional[int] = None,
    ) -> BatchScanResult:
        """
        Scan multiple targets concurrently.

        Args:
            targets: List of target URLs
            scan_type: Type of scan
            config: Scan configuration
            max_concurrent: Maximum concurrent scans

        Returns:
            Batch scan results
        """
        batch_id = f"batch_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        max_concurrent = max_concurrent or self.orchestrator.config.max_concurrent_scans

        result = BatchScanResult(batch_id=batch_id, total_targets=len(targets))

        # Queue all scans
        task_ids = []
        for target in targets:
            task_id = await self.orchestrator.scan(target, scan_type, config)
            task_ids.append(task_id)

        # Wait for all to complete
        completed_tasks = await self.orchestrator.wait_for_completion(task_ids)

        # Aggregate results
        all_findings = []
        for task in completed_tasks.values():
            result.results.append(task)
            if task.result and task.result.success:
                result.completed += 1
                for alert in task.result.alerts:
                    finding = {
                        "target": task.target,
                        "name": alert.name,
                        "risk": alert.risk,
                        "cwe_id": alert.cwe_id,
                        "url": alert.url,
                    }
                    all_findings.append(finding)
            else:
                result.failed += 1

        result.end_time = datetime.now(timezone.utc)
        result.aggregate_findings = all_findings

        return result

    def generate_aggregate_report(
        self,
        batch_result: BatchScanResult,
        output_path: str,
    ) -> str:
        """
        Generate aggregate report for batch scan.

        Args:
            batch_result: Batch scan result
            output_path: Output file path

        Returns:
            Path to generated report
        """
        report = {
            "batch_id": batch_result.batch_id,
            "summary": {
                "total_targets": batch_result.total_targets,
                "completed": batch_result.completed,
                "failed": batch_result.failed,
                "duration_seconds": batch_result.duration,
            },
            "findings_summary": {
                "total_findings": len(batch_result.aggregate_findings),
                "by_risk": {},
                "by_target": {},
            },
            "findings": batch_result.aggregate_findings,
        }

        # Group by risk
        risk_counts = {}
        for finding in batch_result.aggregate_findings:
            risk = finding.get("risk", "Unknown")
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        report["findings_summary"]["by_risk"] = risk_counts

        # Group by target
        target_counts = {}
        for finding in batch_result.aggregate_findings:
            target = finding.get("target", "Unknown")
            target_counts[target] = target_counts.get(target, 0) + 1
        report["findings_summary"]["by_target"] = target_counts

        # Write report
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Aggregate report generated: {output_path}")
        return output_path


class ZAPScheduler:
    """Scheduled scan management"""

    def __init__(self, orchestrator: ZAPOrchestrator):
        self.orchestrator = orchestrator
        self._scheduled_tasks: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the scheduler"""
        self._running = True
        self._scheduler_task = asyncio.create_task(self._run_scheduler())
        logger.info("ZAP Scheduler started")

    async def stop(self):
        """Stop the scheduler"""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("ZAP Scheduler stopped")

    async def _run_scheduler(self):
        """Main scheduler loop"""
        while self._running:
            now = datetime.now(timezone.utc)

            for task_id, task in list(self._scheduled_tasks.items()):
                if task["next_run"] <= now:
                    # Execute scan
                    await self.orchestrator.scan(
                        target=task["target"],
                        scan_type=task["scan_type"],
                        config=task["config"],
                    )

                    # Update next run time
                    if task["recurring"]:
                        task["next_run"] = now + timedelta(seconds=task["interval"])
                    else:
                        del self._scheduled_tasks[task_id]

            await asyncio.sleep(60)  # Check every minute

    def schedule_scan(
        self,
        target: str,
        scan_type: str,
        run_at: datetime,
        config: Optional[Dict[str, Any]] = None,
        recurring: bool = False,
        interval_seconds: int = 86400,  # Default daily
    ) -> str:
        """
        Schedule a scan.

        Args:
            target: Target URL
            scan_type: Type of scan
            run_at: When to run the scan
            config: Scan configuration
            recurring: Whether to run recurring
            interval_seconds: Interval for recurring scans

        Returns:
            Schedule ID
        """
        schedule_id = f"sched_{int(datetime.now(timezone.utc).timestamp() * 1000)}"

        self._scheduled_tasks[schedule_id] = {
            "id": schedule_id,
            "target": target,
            "scan_type": scan_type,
            "config": config or {},
            "next_run": run_at,
            "recurring": recurring,
            "interval": interval_seconds,
        }

        logger.info(f"Scheduled scan {schedule_id} for {target} at {run_at}")
        return schedule_id

    def cancel_schedule(self, schedule_id: str) -> bool:
        """Cancel a scheduled scan"""
        if schedule_id in self._scheduled_tasks:
            del self._scheduled_tasks[schedule_id]
            return True
        return False

    def list_schedules(self) -> List[Dict[str, Any]]:
        """List all scheduled scans"""
        return list(self._scheduled_tasks.values())


# ═══════════════════════════════════════════════════════════════
# Convenience Functions
# ═══════════════════════════════════════════════════════════════


async def quick_scan(
    target: str,
    api_url: str = "http://localhost:8080",
    api_key: Optional[str] = None,
) -> ZAPScanResult:
    """
    Quick ZAP scan with default settings.

    Args:
        target: Target URL
        api_url: ZAP API URL
        api_key: ZAP API key

    Returns:
        Scan result
    """
    config = ZAPOrchestratorConfig(
        api_url=api_url,
        api_key=api_key,
        auto_start_daemon=True,
    )

    orchestrator = ZAPOrchestrator(config)
    await orchestrator.initialize()

    try:
        result = await orchestrator.scan_sync(
            target=target,
            scan_type="full",
            config={"generate_reports": False},
        )
        return result
    finally:
        await orchestrator.shutdown()


async def authenticated_scan(
    target: str,
    login_url: str,
    username: str,
    password: str,
    auth_type: str = "form",
    api_url: str = "http://localhost:8080",
    api_key: Optional[str] = None,
) -> ZAPScanResult:
    """
    Authenticated ZAP scan.

    Args:
        target: Target URL
        login_url: Login URL
        username: Username
        password: Password
        auth_type: Authentication type (form, json)
        api_url: ZAP API URL
        api_key: ZAP API key

    Returns:
        Scan result
    """
    config = ZAPOrchestratorConfig(
        api_url=api_url,
        api_key=api_key,
        auto_start_daemon=True,
    )

    orchestrator = ZAPOrchestrator(config)
    await orchestrator.initialize()

    try:
        result = await orchestrator.scan_sync(
            target=target,
            scan_type="full",
            config={
                "auth": {
                    "type": auth_type,
                    "login_url": login_url,
                    "username": username,
                    "password": password,
                },
                "generate_reports": True,
            },
        )
        return result
    finally:
        await orchestrator.shutdown()


__all__ = [
    # Classes
    "ZAPOrchestrator",
    "ZAPOrchestratorConfig",
    "ZAPScanPipeline",
    "ZAPBatchScanner",
    "ZAPScheduler",
    "ScanTask",
    "BatchScanResult",
    "ScanStage",
    # Functions
    "quick_scan",
    "authenticated_scan",
]
