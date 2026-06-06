#!/usr/bin/env python3
"""
Agent Metrics Exporter for Zen-AI-Pentest
Exports Prometheus metrics from agents for the 100-agent deployment
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from aiohttp import web
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# =============================================================================
# Prometheus Metrics Definitions
# =============================================================================

# Create a custom registry
REGISTRY = CollectorRegistry()

# Agent Health Metrics
AGENT_STATUS = Gauge(
    "zen_agent_status",
    "Current status of the agent (1 = active, 0 = inactive)",
    ["agent_id", "status"],
    registry=REGISTRY,
)

AGENT_UP = Gauge(
    "zen_agent_up",
    "Whether the agent is up (1) or down (0)",
    ["agent_id"],
    registry=REGISTRY,
)

AGENT_LAST_HEARTBEAT = Gauge(
    "zen_agent_last_heartbeat_timestamp_seconds",
    "Timestamp of the last heartbeat received",
    ["agent_id"],
    registry=REGISTRY,
)

AGENT_INFO = Info("zen_agent", "Agent information", ["agent_id"], registry=REGISTRY)

# Task Metrics
TASKS_SUBMITTED = Counter(
    "zen_task_submitted_total",
    "Total number of tasks submitted",
    ["task_type", "priority"],
    registry=REGISTRY,
)

TASKS_COMPLETED = Counter(
    "zen_task_completed_total",
    "Total number of tasks completed",
    ["task_type", "status"],
    registry=REGISTRY,
)

TASKS_FAILED = Counter(
    "zen_task_failures_total",
    "Total number of task failures",
    ["task_type", "error_type"],
    registry=REGISTRY,
)

TASKS_TIMEOUT = Counter(
    "zen_task_timeouts_total",
    "Total number of task timeouts",
    ["task_type"],
    registry=REGISTRY,
)

TASK_DURATION = Histogram(
    "zen_task_duration_seconds",
    "Task execution duration in seconds",
    ["task_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0],
    registry=REGISTRY,
)

TASK_QUEUE_DEPTH = Gauge(
    "zen_task_queue_depth",
    "Current number of tasks in queue",
    ["queue_name"],
    registry=REGISTRY,
)

TASK_ROUTING_TIME = Gauge(
    "zen_task_routing_time_ms",
    "Time taken to route a task in milliseconds",
    registry=REGISTRY,
)

# Agent Pool Metrics
POOL_TOTAL_AGENTS = Gauge(
    "zen_pool_total_agents",
    "Total number of agents in the pool",
    registry=REGISTRY,
)

POOL_IDLE_AGENTS = Gauge(
    "zen_pool_idle_agents",
    "Number of idle agents in the pool",
    registry=REGISTRY,
)

POOL_BUSY_AGENTS = Gauge(
    "zen_pool_busy_agents",
    "Number of busy agents in the pool",
    registry=REGISTRY,
)

POOL_UNHEALTHY_AGENTS = Gauge(
    "zen_pool_unhealthy_agents",
    "Number of unhealthy agents in the pool",
    registry=REGISTRY,
)

POOL_SCALE_UP_EVENTS = Counter("zen_pool_scale_up_events", "Number of scale-up events", registry=REGISTRY)

POOL_SCALE_DOWN_EVENTS = Counter(
    "zen_pool_scale_down_events",
    "Number of scale-down events",
    registry=REGISTRY,
)

# Resource Metrics
AGENT_CPU_USAGE = Gauge(
    "zen_agent_cpu_usage_percent",
    "CPU usage percentage for the agent",
    ["agent_id"],
    registry=REGISTRY,
)

AGENT_MEMORY_USAGE = Gauge(
    "zen_agent_memory_usage_percent",
    "Memory usage percentage for the agent",
    ["agent_id"],
    registry=REGISTRY,
)

AGENT_NETWORK_RECEIVE = Counter(
    "zen_agent_network_receive_bytes_total",
    "Total network bytes received by the agent",
    ["agent_id"],
    registry=REGISTRY,
)

AGENT_NETWORK_TRANSMIT = Counter(
    "zen_agent_network_transmit_bytes_total",
    "Total network bytes transmitted by the agent",
    ["agent_id"],
    registry=REGISTRY,
)

# Error Metrics
ERRORS_TOTAL = Counter(
    "zen_errors_total",
    "Total number of errors",
    ["error_type", "component"],
    registry=REGISTRY,
)

AGENT_ERRORS = Counter(
    "zen_agent_errors_total",
    "Total number of agent errors",
    ["agent_id", "error_type"],
    registry=REGISTRY,
)

AGENT_ERROR_COUNT = Gauge(
    "zen_agent_error_count",
    "Current error count for the agent",
    ["agent_id"],
    registry=REGISTRY,
)

# WebSocket Metrics
WEBSOCKET_CONNECTIONS = Gauge(
    "websocket_active_connections",
    "Number of active WebSocket connections",
    ["node_id"],
    registry=REGISTRY,
)

WEBSOCKET_MESSAGES_SENT = Counter(
    "websocket_messages_sent_total",
    "Total WebSocket messages sent",
    ["node_id"],
    registry=REGISTRY,
)

WEBSOCKET_MESSAGES_RECEIVED = Counter(
    "websocket_messages_received_total",
    "Total WebSocket messages received",
    ["node_id"],
    registry=REGISTRY,
)

WEBSOCKET_MESSAGE_LATENCY = Histogram(
    "websocket_message_latency_seconds",
    "WebSocket message latency in seconds",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=REGISTRY,
)

WEBSOCKET_CONNECTION_ERRORS = Counter(
    "websocket_connection_errors_total",
    "Total WebSocket connection errors",
    ["error_type", "node_id"],
    registry=REGISTRY,
)

# Tool Execution Metrics
TOOL_EXECUTIONS = Counter(
    "zen_tool_executions_total",
    "Total number of tool executions",
    ["tool", "status"],
    registry=REGISTRY,
)

TOOL_FAILURES = Counter(
    "zen_tool_failures_total",
    "Total number of tool execution failures",
    ["tool", "error_type"],
    registry=REGISTRY,
)

TOOL_DURATION = Histogram(
    "zen_tool_duration_seconds",
    "Tool execution duration in seconds",
    ["tool"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1800.0, 3600.0],
    registry=REGISTRY,
)

# Security Metrics
SECURITY_FINDINGS = Counter(
    "zen_security_findings_total",
    "Total number of security findings",
    ["severity", "finding_type"],
    registry=REGISTRY,
)

SCAN_STARTED = Counter(
    "zen_scan_started_total",
    "Total number of scans started",
    ["scan_type"],
    registry=REGISTRY,
)

SCAN_COMPLETED = Counter(
    "zen_scan_completed_total",
    "Total number of scans completed",
    ["scan_type", "status"],
    registry=REGISTRY,
)

SCAN_FAILED = Counter(
    "zen_scan_failed_total",
    "Total number of failed scans",
    ["scan_type", "error_type"],
    registry=REGISTRY,
)

SCAN_DURATION = Histogram(
    "zen_scan_duration_seconds",
    "Scan duration in seconds",
    ["scan_type"],
    buckets=[10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1800.0, 3600.0, 7200.0],
    registry=REGISTRY,
)

SECURITY_INCIDENTS = Counter(
    "zen_security_incidents_total",
    "Total number of security incidents",
    ["incident_type", "severity"],
    registry=REGISTRY,
)

# Agent Task Metrics
AGENT_TASK_COUNT = Gauge(
    "zen_agent_task_count",
    "Number of tasks completed by the agent",
    ["agent_id"],
    registry=REGISTRY,
)

AGENT_TASKS_COMPLETED = Counter(
    "zen_agent_tasks_completed_total",
    "Total tasks completed by the agent",
    ["agent_id", "task_type"],
    registry=REGISTRY,
)

AGENT_TASKS_FAILED = Counter(
    "zen_agent_tasks_failed_total",
    "Total tasks failed by the agent",
    ["agent_id", "error_type"],
    registry=REGISTRY,
)

AGENT_TASK_DURATION = Histogram(
    "zen_agent_task_duration_seconds",
    "Task duration for this agent",
    ["agent_id", "task_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
    registry=REGISTRY,
)

# Request Metrics
REQUESTS_TOTAL = Counter(
    "zen_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status_code"],
    registry=REGISTRY,
)

REQUEST_DURATION = Histogram(
    "zen_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=REGISTRY,
)


# =============================================================================
# Metrics Exporter Class
# =============================================================================


@dataclass
class AgentMetrics:
    """Container for agent metrics data"""

    agent_id: str
    status: str = "idle"
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    task_count: int = 0
    error_count: int = 0
    last_heartbeat: float = field(default_factory=time.time)
    capabilities: List[str] = field(default_factory=list)
    version: str = "1.0.0"


class AgentMetricsExporter:
    """
    Metrics exporter for Zen-AI-Pentest agents.
    Collects and exposes Prometheus metrics from all agents.
    """

    def __init__(self, port: int = 9091, host: Optional[str] = None):
        self.port = port
        self.host = host or os.getenv("METRICS_HOST", "127.0.0.1")
        self.app = web.Application()
        self.agents: Dict[str, AgentMetrics] = {}
        self._lock = asyncio.Lock()
        self._running = False

        # Setup routes
        self.app.router.add_get("/metrics", self.metrics_handler)
        self.app.router.add_post("/agent/heartbeat", self.agent_heartbeat_handler)
        self.app.router.add_post("/agent/task", self.agent_task_handler)
        self.app.router.add_post("/agent/resource", self.agent_resource_handler)
        self.app.router.add_post("/agent/error", self.agent_error_handler)
        self.app.router.add_get("/health", self.health_handler)
        self.app.router.add_get("/agents", self.list_agents_handler)

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the metrics exporter"""
        logger.info(f"Starting Agent Metrics Exporter on port {self.port}")
        self._running = True

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        # Start web server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        logger.info(f"Metrics exporter listening on port {self.port}")

    async def stop(self):
        """Stop the metrics exporter"""
        logger.info("Stopping Agent Metrics Exporter")
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def metrics_handler(self, request: web.Request) -> web.Response:
        """Handle Prometheus metrics endpoint"""
        # Update metrics before serving
        await self._update_metrics()

        # Generate metrics output
        output = generate_latest(REGISTRY)
        return web.Response(body=output, content_type=CONTENT_TYPE_LATEST)

    async def health_handler(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response(
            {
                "status": "healthy",
                "agents_tracked": len(self.agents),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def list_agents_handler(self, request: web.Request) -> web.Response:
        """List all tracked agents"""
        async with self._lock:
            agents_data = {
                agent_id: {
                    "status": agent.status,
                    "task_count": agent.task_count,
                    "error_count": agent.error_count,
                    "cpu_usage": agent.cpu_usage,
                    "memory_usage": agent.memory_usage,
                    "last_heartbeat_age": time.time() - agent.last_heartbeat,
                }
                for agent_id, agent in self.agents.items()
            }
        return web.json_response(agents_data)

    async def agent_heartbeat_handler(self, request: web.Request) -> web.Response:
        """Handle agent heartbeat"""
        try:
            data = await request.json()
            agent_id = data.get("agent_id")

            if not agent_id:
                return web.json_response({"error": "agent_id is required"}, status=400)

            async with self._lock:
                if agent_id not in self.agents:
                    self.agents[agent_id] = AgentMetrics(agent_id=agent_id)

                agent = self.agents[agent_id]
                agent.status = data.get("status", agent.status)
                agent.last_heartbeat = time.time()
                agent.capabilities = data.get("capabilities", agent.capabilities)
                agent.version = data.get("version", agent.version)

            # Update Prometheus metrics
            AGENT_UP.labels(agent_id=agent_id).set(1)
            AGENT_LAST_HEARTBEAT.labels(agent_id=agent_id).set(time.time())
            AGENT_STATUS.labels(agent_id=agent_id, status=agent.status).set(1)

            # Clear other status values
            for status in ["idle", "busy", "error", "offline"]:
                if status != agent.status:
                    AGENT_STATUS.labels(agent_id=agent_id, status=status).set(0)

            return web.json_response({"status": "ok"})

        except Exception as e:
            logger.error(f"Error processing heartbeat: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def agent_task_handler(self, request: web.Request) -> web.Response:
        """Handle agent task metrics"""
        try:
            data = await request.json()
            agent_id = data.get("agent_id")
            task_type = data.get("task_type", "unknown")
            status = data.get("status", "completed")
            duration = data.get("duration_seconds", 0)

            if not agent_id:
                return web.json_response({"error": "agent_id is required"}, status=400)

            async with self._lock:
                if agent_id in self.agents:
                    agent = self.agents[agent_id]
                    if status == "completed":
                        agent.task_count += 1
                        AGENT_TASK_COUNT.labels(agent_id=agent_id).set(agent.task_count)
                        AGENT_TASKS_COMPLETED.labels(agent_id=agent_id, task_type=task_type).inc()
                        TASKS_COMPLETED.labels(task_type=task_type, status="success").inc()
                    elif status == "failed":
                        error_type = data.get("error_type", "unknown")
                        AGENT_TASKS_FAILED.labels(agent_id=agent_id, error_type=error_type).inc()
                        TASKS_FAILED.labels(task_type=task_type, error_type=error_type).inc()

                    AGENT_TASK_DURATION.labels(agent_id=agent_id, task_type=task_type).observe(duration)
                    TASK_DURATION.labels(task_type=task_type).observe(duration)

            return web.json_response({"status": "ok"})

        except Exception as e:
            logger.error(f"Error processing task metrics: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def agent_resource_handler(self, request: web.Request) -> web.Response:
        """Handle agent resource metrics"""
        try:
            data = await request.json()
            agent_id = data.get("agent_id")

            if not agent_id:
                return web.json_response({"error": "agent_id is required"}, status=400)

            cpu_usage = data.get("cpu_usage_percent", 0)
            memory_usage = data.get("memory_usage_percent", 0)
            network_rx = data.get("network_receive_bytes", 0)
            network_tx = data.get("network_transmit_bytes", 0)

            async with self._lock:
                if agent_id in self.agents:
                    agent = self.agents[agent_id]
                    agent.cpu_usage = cpu_usage
                    agent.memory_usage = memory_usage

            # Update Prometheus metrics
            AGENT_CPU_USAGE.labels(agent_id=agent_id).set(cpu_usage)
            AGENT_MEMORY_USAGE.labels(agent_id=agent_id).set(memory_usage)

            if network_rx > 0:
                AGENT_NETWORK_RECEIVE.labels(agent_id=agent_id).inc(network_rx)
            if network_tx > 0:
                AGENT_NETWORK_TRANSMIT.labels(agent_id=agent_id).inc(network_tx)

            return web.json_response({"status": "ok"})

        except Exception as e:
            logger.error(f"Error processing resource metrics: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def agent_error_handler(self, request: web.Request) -> web.Response:
        """Handle agent error metrics"""
        try:
            data = await request.json()
            agent_id = data.get("agent_id")
            error_type = data.get("error_type", "unknown")
            component = data.get("component", "agent")

            if not agent_id:
                return web.json_response({"error": "agent_id is required"}, status=400)

            async with self._lock:
                if agent_id in self.agents:
                    agent = self.agents[agent_id]
                    agent.error_count += 1
                    AGENT_ERROR_COUNT.labels(agent_id=agent_id).set(agent.error_count)

            # Update Prometheus metrics
            AGENT_ERRORS.labels(agent_id=agent_id, error_type=error_type).inc()
            ERRORS_TOTAL.labels(error_type=error_type, component=component).inc()

            return web.json_response({"status": "ok"})

        except Exception as e:
            logger.error(f"Error processing error metrics: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def _update_metrics(self):
        """Update aggregate metrics"""
        async with self._lock:
            total = len(self.agents)
            idle = sum(1 for a in self.agents.values() if a.status == "idle")
            busy = sum(1 for a in self.agents.values() if a.status == "busy")
            unhealthy = sum(1 for a in self.agents.values() if a.status in ["error", "offline"])

        POOL_TOTAL_AGENTS.set(total)
        POOL_IDLE_AGENTS.set(idle)
        POOL_BUSY_AGENTS.set(busy)
        POOL_UNHEALTHY_AGENTS.set(unhealthy)

    async def _cleanup_loop(self):
        """Background task to cleanup stale agents"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Run every minute

                current_time = time.time()
                stale_threshold = 300  # 5 minutes

                async with self._lock:
                    stale_agents = [
                        agent_id
                        for agent_id, agent in self.agents.items()
                        if current_time - agent.last_heartbeat > stale_threshold
                    ]

                    for agent_id in stale_agents:
                        logger.warning(f"Removing stale agent: {agent_id}")
                        self.agents.pop(agent_id)
                        AGENT_UP.labels(agent_id=agent_id).set(0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")


# =============================================================================
# Decorators for Instrumentation
# =============================================================================


def track_task_duration(task_type: str):
    """Decorator to track task execution duration"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                TASKS_COMPLETED.labels(task_type=task_type, status="success").inc()
                return result
            except Exception as e:
                TASKS_FAILED.labels(task_type=task_type, error_type=type(e).__name__).inc()
                raise
            finally:
                duration = time.time() - start_time
                TASK_DURATION.labels(task_type=task_type).observe(duration)

        return wrapper

    return decorator


def track_request_duration(method: str, endpoint: str):
    """Decorator to track request duration"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                status_code = 200
                return result
            except Exception:
                status_code = 500
                raise
            finally:
                duration = time.time() - start_time
                REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
                REQUESTS_TOTAL.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=str(status_code),
                ).inc()

        return wrapper

    return decorator


# =============================================================================
# Main Entry Point
# =============================================================================


async def main():
    """Main entry point for the metrics exporter"""
    exporter = AgentMetricsExporter(port=9091)
    await exporter.start()

    # Keep running
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
