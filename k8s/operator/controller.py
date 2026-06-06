"""
Kubernetes Operator Controller for Zen-AI-Pentest.

This module implements the main controller logic for watching and managing
ZenScan and ZenReport custom resources in a Kubernetes cluster.
"""

import asyncio
import logging
import os
import signal
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from kubernetes.client.rest import ApiException

# Kubernetes client
from kubernetes import client, config, watch

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Kubernetes watch event types."""

    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"
    ERROR = "ERROR"
    BOOKMARK = "BOOKMARK"


class ControllerState(Enum):
    """Controller operational states."""

    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"


@dataclass
class ControllerConfig:
    """Controller configuration."""

    namespace: str = "default"
    resync_interval: int = 300  # seconds
    worker_count: int = 5
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    enable_metrics: bool = True
    enable_leader_election: bool = True
    lease_duration: int = 15  # seconds
    lease_name: str = "zen-operator-lock"

    # Resource limits
    max_concurrent_scans: int = 10
    scan_timeout: int = 3600

    # Image settings
    scanner_image: str = "shadd0wtaka/zen-pentest:latest"
    image_pull_policy: str = "Always"

    # Storage
    storage_class: str = "standard"
    reports_storage_size: str = "10Gi"

    @classmethod
    def from_env(cls) -> "ControllerConfig":
        """Load configuration from environment variables."""
        return cls(
            namespace=os.getenv("OPERATOR_NAMESPACE", "default"),
            resync_interval=int(os.getenv("RESYNC_INTERVAL", "300")),
            worker_count=int(os.getenv("WORKER_COUNT", "5")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            retry_delay=int(os.getenv("RETRY_DELAY", "5")),
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
            enable_leader_election=os.getenv("ENABLE_LEADER_ELECTION", "true").lower() == "true",
            lease_duration=int(os.getenv("LEASE_DURATION", "15")),
            lease_name=os.getenv("LEASE_NAME", "zen-operator-lock"),
            max_concurrent_scans=int(os.getenv("MAX_CONCURRENT_SCANS", "10")),
            scan_timeout=int(os.getenv("SCAN_TIMEOUT", "3600")),
            scanner_image=os.getenv("SCANNER_IMAGE", "shadd0wtaka/zen-pentest:latest"),
            image_pull_policy=os.getenv("IMAGE_PULL_POLICY", "Always"),
            storage_class=os.getenv("STORAGE_CLASS", "standard"),
            reports_storage_size=os.getenv("REPORTS_STORAGE_SIZE", "10Gi"),
        )


class ZenOperator:
    """
    Main Kubernetes Operator for Zen-AI-Pentest.

    Manages ZenScan and ZenReport custom resources by watching for changes
    and reconciling the desired state with the actual cluster state.
    """

    # CRD Configuration
    GROUP = "security.zen-ai.io"
    VERSION = "v1"
    ZENSCAN_PLURAL = "zenscans"
    ZENREPORT_PLURAL = "zenreports"

    def __init__(self, config: Optional[ControllerConfig] = None):
        """Initialize the operator controller."""
        self.config = config or ControllerConfig.from_env()
        self.state = ControllerState.INITIALIZING

        # Kubernetes clients
        self.core_api: Optional[client.CoreV1Api] = None
        self.batch_api: Optional[client.BatchV1Api] = None
        self.custom_api: Optional[client.CustomObjectsApi] = None
        self.apps_api: Optional[client.AppsV1Api] = None
        self.rbac_api: Optional[client.RbacAuthorizationV1Api] = None
        self.networking_api: Optional[client.NetworkingV1Api] = None

        # Event handling
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self.is_leader = False
        self.leader_election_task: Optional[asyncio.Task] = None

        # Metrics
        self.metrics = {
            "events_processed": 0,
            "scans_created": 0,
            "scans_completed": 0,
            "scans_failed": 0,
            "reconcile_errors": 0,
            "last_resync": None,
        }

        # Shutdown handling
        self._shutdown_event = asyncio.Event()

        logger.info("ZenOperator initialized")

    def initialize_k8s_clients(self) -> None:
        """Initialize Kubernetes API clients."""
        try:
            # Try to load in-cluster config first, then fall back to kubeconfig
            try:
                config.load_incluster_config()
                logger.info("Loaded in-cluster Kubernetes configuration")
            except config.ConfigException:
                config.load_kube_config()
                logger.info("Loaded kubeconfig file")

            # Initialize API clients
            self.core_api = client.CoreV1Api()
            self.batch_api = client.BatchV1Api()
            self.custom_api = client.CustomObjectsApi()
            self.apps_api = client.AppsV1Api()
            self.rbac_api = client.RbacAuthorizationV1Api()
            self.networking_api = client.NetworkingV1Api()

            logger.info("Kubernetes API clients initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes clients: {e}")
            raise

    async def start(self) -> None:
        """Start the operator controller."""
        logger.info("Starting ZenOperator...")

        self.initialize_k8s_clients()
        self.state = ControllerState.RUNNING

        # Setup signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))

        # Start leader election if enabled
        if self.config.enable_leader_election:
            self.leader_election_task = asyncio.create_task(self.run_leader_election())
            await asyncio.sleep(1)  # Wait for initial leader check
        else:
            self.is_leader = True

        # Start worker tasks
        self.workers = [asyncio.create_task(self.worker_loop(i)) for i in range(self.config.worker_count)]

        # Start watchers
        watchers = [
            asyncio.create_task(self.watch_zenscans()),
            asyncio.create_task(self.watch_zenreports()),
            asyncio.create_task(self.periodic_resync()),
        ]

        logger.info(f"ZenOperator started with {self.config.worker_count} workers")

        # Wait for shutdown
        await self._shutdown_event.wait()

        # Cancel watchers
        for w in watchers:
            w.cancel()

        logger.info("ZenOperator stopped")

    async def shutdown(self) -> None:
        """Graceful shutdown of the operator."""
        if self.state == ControllerState.SHUTTING_DOWN:
            return

        logger.info("Shutting down ZenOperator...")
        self.state = ControllerState.SHUTTING_DOWN

        # Signal shutdown
        self._shutdown_event.set()

        # Cancel leader election
        if self.leader_election_task:
            self.leader_election_task.cancel()

        # Wait for workers to finish
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)

        self.state = ControllerState.STOPPED
        logger.info("ZenOperator shutdown complete")

    async def run_leader_election(self) -> None:
        """Run leader election using ConfigMap lock."""
        while not self._shutdown_event.is_set():
            try:
                if await self.try_acquire_leadership():
                    if not self.is_leader:
                        logger.info("Became leader")
                        self.is_leader = True
                else:
                    if self.is_leader:
                        logger.info("Lost leadership")
                        self.is_leader = False

                await asyncio.sleep(self.config.lease_duration)
            except Exception as e:
                logger.error(f"Leader election error: {e}")
                await asyncio.sleep(5)

    async def try_acquire_leadership(self) -> bool:
        """Try to acquire leadership lease."""
        try:
            now = datetime.now(timezone.utc).isoformat()
            lock_data = {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {"name": self.config.lease_name, "namespace": self.config.namespace},
                "data": {"holderIdentity": os.getenv("HOSTNAME", "unknown"), "acquireTime": now, "renewTime": now},
            }

            try:
                self.core_api.read_namespaced_config_map(name=self.config.lease_name, namespace=self.config.namespace)
                # Lock exists, try to update
                self.core_api.replace_namespaced_config_map(
                    name=self.config.lease_name, namespace=self.config.namespace, body=lock_data
                )
                return True
            except ApiException as e:
                if e.status == 404:
                    # Lock doesn't exist, create it
                    self.core_api.create_namespaced_config_map(namespace=self.config.namespace, body=lock_data)
                    return True
                raise
        except Exception as e:
            logger.debug(f"Failed to acquire leadership: {e}")
            return False

    async def watch_zenscans(self) -> None:
        """Watch for ZenScan resource changes."""
        logger.info("Starting ZenScan watcher...")

        while not self._shutdown_event.is_set():
            try:
                if not self.is_leader:
                    await asyncio.sleep(1)
                    continue

                w = watch.Watch()
                for event in w.stream(
                    self.custom_api.list_namespaced_custom_object,
                    group=self.GROUP,
                    version=self.VERSION,
                    namespace=self.config.namespace,
                    plural=self.ZENSCAN_PLURAL,
                    watch=True,
                    timeout_seconds=self.config.resync_interval,
                ):
                    if self._shutdown_event.is_set():
                        break

                    await self.event_queue.put({"resource_type": "zenscan", "event": event})
                    self.metrics["events_processed"] += 1

            except Exception as e:
                logger.error(f"ZenScan watch error: {e}")
                await asyncio.sleep(5)

    async def watch_zenreports(self) -> None:
        """Watch for ZenReport resource changes."""
        logger.info("Starting ZenReport watcher...")

        while not self._shutdown_event.is_set():
            try:
                if not self.is_leader:
                    await asyncio.sleep(1)
                    continue

                w = watch.Watch()
                for event in w.stream(
                    self.custom_api.list_namespaced_custom_object,
                    group=self.GROUP,
                    version=self.VERSION,
                    namespace=self.config.namespace,
                    plural=self.ZENREPORT_PLURAL,
                    watch=True,
                    timeout_seconds=self.config.resync_interval,
                ):
                    if self._shutdown_event.is_set():
                        break

                    await self.event_queue.put({"resource_type": "zenreport", "event": event})
                    self.metrics["events_processed"] += 1

            except Exception as e:
                logger.error(f"ZenReport watch error: {e}")
                await asyncio.sleep(5)

    async def worker_loop(self, worker_id: int) -> None:
        """Worker loop for processing events."""
        logger.info(f"Worker {worker_id} started")

        while not self._shutdown_event.is_set():
            try:
                # Get event with timeout
                try:
                    item = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                resource_type = item["resource_type"]
                event = item["event"]

                if resource_type == "zenscan":
                    await self.handle_zenscan_event(event)
                elif resource_type == "zenreport":
                    await self.handle_zenreport_event(event)

                self.event_queue.task_done()

            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                self.metrics["reconcile_errors"] += 1
                await asyncio.sleep(1)

        logger.info(f"Worker {worker_id} stopped")

    async def handle_zenscan_event(self, event: Dict[str, Any]) -> None:
        """Handle ZenScan resource events."""
        from handlers import ScanJobHandler

        obj = event["object"]
        event_type = event["type"]
        name = obj.get("metadata", {}).get("name", "unknown")
        namespace = obj.get("metadata", {}).get("namespace", "default")

        logger.info(f"Processing ZenScan {event_type}: {namespace}/{name}")

        handler = ScanJobHandler(self)

        try:
            if event_type == EventType.ADDED:
                await handler.create_scan_job(obj)
            elif event_type == EventType.MODIFIED:
                await handler.update_scan_job(obj)
            elif event_type == EventType.DELETED:
                await handler.delete_scan_job(obj)
        except Exception as e:
            logger.error(f"Failed to handle ZenScan event: {e}")
            await self.update_status(namespace, name, self.ZENSCAN_PLURAL, {"phase": "Failed", "message": str(e)})

    async def handle_zenreport_event(self, event: Dict[str, Any]) -> None:
        """Handle ZenReport resource events."""
        from handlers import ReportJobHandler

        obj = event["object"]
        event_type = event["type"]
        name = obj.get("metadata", {}).get("name", "unknown")
        namespace = obj.get("metadata", {}).get("namespace", "default")

        logger.info(f"Processing ZenReport {event_type}: {namespace}/{name}")

        handler = ReportJobHandler(self)

        try:
            if event_type == EventType.ADDED:
                await handler.create_report_job(obj)
            elif event_type == EventType.MODIFIED:
                await handler.update_report_job(obj)
            elif event_type == EventType.DELETED:
                await handler.delete_report_job(obj)
        except Exception as e:
            logger.error(f"Failed to handle ZenReport event: {e}")
            await self.update_status(namespace, name, self.ZENREPORT_PLURAL, {"phase": "Failed", "message": str(e)})

    async def update_status(self, namespace: str, name: str, plural: str, status: Dict[str, Any]) -> None:
        """Update the status of a custom resource."""
        try:
            # Add timestamp
            status["lastTransitionTime"] = datetime.now(timezone.utc).isoformat() + "Z"

            self.custom_api.patch_namespaced_custom_object_status(
                group=self.GROUP, version=self.VERSION, namespace=namespace, plural=plural, name=name, body={"status": status}
            )
            logger.debug(f"Updated status for {namespace}/{name}")
        except ApiException as e:
            logger.error(f"Failed to update status: {e}")

    async def periodic_resync(self) -> None:
        """Periodically resync all resources."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.config.resync_interval)

                if not self.is_leader:
                    continue

                logger.debug("Running periodic resync...")

                # List all zenscans and requeue them
                zenscans = self.custom_api.list_namespaced_custom_object(
                    group=self.GROUP, version=self.VERSION, namespace=self.config.namespace, plural=self.ZENSCAN_PLURAL
                )

                for item in zenscans.get("items", []):
                    await self.event_queue.put({"resource_type": "zenscan", "event": {"type": "MODIFIED", "object": item}})

                self.metrics["last_resync"] = datetime.now(timezone.utc).isoformat()
                logger.debug(f"Resynced {len(zenscans.get('items', []))} ZenScans")

            except Exception as e:
                logger.error(f"Resync error: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get current operator metrics."""
        return {**self.metrics, "state": self.state.value, "is_leader": self.is_leader, "queue_size": self.event_queue.qsize()}


async def main():
    """Main entry point for the operator."""
    config = ControllerConfig.from_env()
    operator = ZenOperator(config)

    try:
        await operator.start()
    except Exception as e:
        logger.error(f"Operator crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
