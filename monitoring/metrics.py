"""
Prometheus Metrics Integration für Zen AI Pentest - Performance Optimized

Provides:
- Request latency histograms
- Request counters (by endpoint, status code, method)
- Error rates
- Active connections gauge
- Business metrics (scans, findings, reports)
- Tool execution metrics
- Cache performance metrics
- Database query metrics
- Memory usage tracking
"""

import time
import asyncio
import psutil
from typing import Callable, Optional, Dict, Any
from functools import wraps
from contextlib import contextmanager

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest


# Custom registry
METRICS_REGISTRY = CollectorRegistry()

# =============================================================================
# HTTP Metrics
# =============================================================================

# Request latency
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint", "status_code"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=METRICS_REGISTRY,
)

# Request counter
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total", 
    "Total HTTP requests", 
    ["method", "endpoint", "status_code"], 
    registry=METRICS_REGISTRY
)

# Requests in progress
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
    registry=METRICS_REGISTRY,
)

# Errors counter
HTTP_ERRORS_TOTAL = Counter(
    "http_errors_total", 
    "Total HTTP errors", 
    ["method", "endpoint", "status_code", "error_type"], 
    registry=METRICS_REGISTRY
)

# Response size
HTTP_RESPONSE_SIZE = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
    buckets=[100, 1000, 10000, 100000, 1000000, 10000000],
    registry=METRICS_REGISTRY,
)

# =============================================================================
# Application Metrics
# =============================================================================

# Scans metrics
SCANS_CREATED = Counter(
    "scans_created_total", 
    "Total number of scans created", 
    ["scan_type"], 
    registry=METRICS_REGISTRY
)

SCANS_COMPLETED = Counter(
    "scans_completed_total", 
    "Total number of scans completed", 
    ["scan_type", "status"], 
    registry=METRICS_REGISTRY
)

SCANS_ACTIVE = Gauge(
    "scans_active", 
    "Number of currently active scans", 
    registry=METRICS_REGISTRY
)

SCAN_DURATION = Histogram(
    "scan_duration_seconds",
    "Scan execution duration in seconds",
    ["scan_type"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600],
    registry=METRICS_REGISTRY,
)

# Findings metrics
FINDINGS_DISCOVERED = Counter(
    "findings_discovered_total", 
    "Total number of findings discovered", 
    ["severity"], 
    registry=METRICS_REGISTRY
)

FINDINGS_BY_TYPE = Counter(
    "findings_by_type_total", 
    "Total findings by vulnerability type", 
    ["vulnerability_type"], 
    registry=METRICS_REGISTRY
)

# Report metrics
REPORTS_GENERATED = Counter(
    "reports_generated_total", 
    "Total number of reports generated", 
    ["format"], 
    registry=METRICS_REGISTRY
)

# Authentication metrics
AUTH_ATTEMPTS = Counter(
    "auth_attempts_total", 
    "Total authentication attempts", 
    ["result"], 
    registry=METRICS_REGISTRY
)

ACTIVE_SESSIONS = Gauge(
    "active_sessions", 
    "Number of active user sessions", 
    registry=METRICS_REGISTRY
)

# Rate limiting metrics
RATE_LIMIT_HITS = Counter(
    "rate_limit_hits_total", 
    "Total rate limit hits", 
    ["tier", "endpoint"], 
    registry=METRICS_REGISTRY
)

# =============================================================================
# Database Metrics
# =============================================================================

DB_CONNECTIONS_ACTIVE = Gauge(
    "db_connections_active", 
    "Number of active database connections", 
    registry=METRICS_REGISTRY
)

DB_CONNECTIONS_IDLE = Gauge(
    "db_connections_idle", 
    "Number of idle database connections", 
    registry=METRICS_REGISTRY
)

DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=METRICS_REGISTRY,
)

DB_QUERIES_TOTAL = Counter(
    "db_queries_total",
    "Total number of database queries",
    ["query_type", "status"],
    registry=METRICS_REGISTRY,
)

# =============================================================================
# Tool Execution Metrics
# =============================================================================

TOOL_EXECUTION_DURATION = Histogram(
    "tool_execution_duration_seconds",
    "Security tool execution duration in seconds",
    ["tool_name", "status"],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0],
    registry=METRICS_REGISTRY,
)

TOOL_EXECUTIONS_TOTAL = Counter(
    "tool_executions_total",
    "Total number of tool executions",
    ["tool_name", "status", "safety_level"],
    registry=METRICS_REGISTRY,
)

TOOL_EXECUTIONS_ACTIVE = Gauge(
    "tool_executions_active",
    "Number of currently running tool executions",
    ["tool_name"],
    registry=METRICS_REGISTRY,
)

TOOL_OUTPUT_SIZE = Histogram(
    "tool_output_size_bytes",
    "Size of tool output in bytes",
    ["tool_name"],
    buckets=[1024, 10240, 102400, 1048576, 10485760, 52428800],
    registry=METRICS_REGISTRY,
)

# =============================================================================
# Cache Metrics
# =============================================================================

CACHE_HITS_TOTAL = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["cache_tier", "cache_name"],
    registry=METRICS_REGISTRY,
)

CACHE_MISSES_TOTAL = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["cache_tier", "cache_name"],
    registry=METRICS_REGISTRY,
)

CACHE_SIZE = Gauge(
    "cache_size",
    "Current number of items in cache",
    ["cache_tier", "cache_name"],
    registry=METRICS_REGISTRY,
)

CACHE_EVICTIONS_TOTAL = Counter(
    "cache_evictions_total",
    "Total number of cache evictions",
    ["cache_tier", "cache_name"],
    registry=METRICS_REGISTRY,
)

CACHE_OPERATION_DURATION = Histogram(
    "cache_operation_duration_seconds",
    "Cache operation duration in seconds",
    ["operation", "cache_tier"],
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
    registry=METRICS_REGISTRY,
)

# =============================================================================
# Memory Metrics
# =============================================================================

MEMORY_USAGE_BYTES = Gauge(
    "memory_usage_bytes",
    "Current memory usage in bytes",
    ["type"],
    registry=METRICS_REGISTRY,
)

MEMORY_GC_COLLECTIONS = Counter(
    "memory_gc_collections_total",
    "Total number of garbage collections",
    ["generation"],
    registry=METRICS_REGISTRY,
)

# =============================================================================
# Agent Metrics
# =============================================================================

AGENT_ITERATIONS = Histogram(
    "agent_iterations",
    "Number of agent iterations per run",
    ["agent_type"],
    buckets=[1, 5, 10, 20, 50],
    registry=METRICS_REGISTRY,
)

AGENT_EXECUTION_DURATION = Histogram(
    "agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_type", "status"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
    registry=METRICS_REGISTRY,
)

AGENT_FINDINGS_DISCOVERED = Histogram(
    "agent_findings_discovered",
    "Number of findings discovered per agent run",
    ["agent_type"],
    buckets=[0, 1, 5, 10, 25, 50, 100],
    registry=METRICS_REGISTRY,
)

# =============================================================================
# CVE Database Metrics
# =============================================================================

CVE_LOOKUP_DURATION = Histogram(
    "cve_lookup_duration_seconds",
    "CVE lookup duration in seconds",
    ["lookup_type", "cache_hit"],
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
    registry=METRICS_REGISTRY,
)

CVE_CACHE_SIZE = Gauge(
    "cve_cache_size",
    "Number of CVE entries in cache",
    registry=METRICS_REGISTRY,
)

# Application info
APP_INFO = Info("app_info", "Application information", registry=METRICS_REGISTRY)

# =============================================================================
# Metrics Middleware
# =============================================================================


class MetricsMiddleware:
    """
    FastAPI Middleware for Prometheus metrics collection.

    Usage:
        app.add_middleware(MetricsMiddleware)
    """

    def __init__(self, app, exclude_paths: Optional[list] = None):
        self.app = app
        self.exclude_paths = exclude_paths or ["/metrics", "/health", "/docs", "/openapi.json"]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_path = scope.get("path", "/")

        # Skip excluded paths
        if any(request_path.startswith(p) for p in self.exclude_paths):
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")

        # Track in-progress
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=request_path).inc()

        start_time = time.time()

        # Capture status code
        status_code = 200
        response_size = 0

        async def wrapped_send(message):
            nonlocal status_code, response_size

            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                response_size = len(body)

            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        except Exception as e:
            status_code = 500
            HTTP_ERRORS_TOTAL.labels(
                method=method, endpoint=request_path, status_code="500", error_type=type(e).__name__
            ).inc()
            raise
        finally:
            duration = time.time() - start_time

            # Record metrics
            HTTP_REQUEST_DURATION.labels(
                method=method, endpoint=request_path, status_code=str(status_code)
            ).observe(duration)

            HTTP_REQUESTS_TOTAL.labels(
                method=method, endpoint=request_path, status_code=str(status_code)
            ).inc()

            HTTP_RESPONSE_SIZE.labels(method=method, endpoint=request_path).observe(response_size)

            HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=request_path).dec()


# =============================================================================
# Decorators for function-level metrics
# =============================================================================


def timed(metric: Histogram, labels: Optional[dict] = None):
    """
    Decorator to time function execution.

    Usage:
        @timed(DB_QUERY_DURATION, labels={"query_type": "select"})
        def get_user(user_id: int):
            return db.query(User).get(user_id)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper

    return decorator


def counted(metric: Counter, labels: Optional[dict] = None):
    """
    Decorator to count function calls.

    Usage:
        @counted(SCANS_CREATED, labels={"scan_type": "web"})
        def create_scan(scan_type: str):
            return Scan.create(type=scan_type)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if labels:
                metric.labels(**labels).inc()
            else:
                metric.inc()
            return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if labels:
                metric.labels(**labels).inc()
            else:
                metric.inc()
            return await func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper

    return decorator


@contextmanager
def timed_context(metric: Histogram, labels: Optional[dict] = None):
    """
    Context manager for timing code blocks.

    Usage:
        with timed_context(DB_QUERY_DURATION, {"query_type": "select"}):
            result = db.query(User).all()
    """
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        if labels:
            metric.labels(**labels).observe(duration)
        else:
            metric.observe(duration)


# =============================================================================
# Helper functions for business metrics
# =============================================================================


def record_scan_created(scan_type: str):
    """Record that a scan was created"""
    SCANS_CREATED.labels(scan_type=scan_type).inc()
    SCANS_ACTIVE.inc()


def record_scan_completed(scan_type: str, status: str, duration_seconds: float):
    """Record that a scan completed"""
    SCANS_COMPLETED.labels(scan_type=scan_type, status=status).inc()
    SCANS_ACTIVE.dec()
    SCAN_DURATION.labels(scan_type=scan_type).observe(duration_seconds)


def record_finding(severity: str, vulnerability_type: str):
    """Record a discovered finding"""
    FINDINGS_DISCOVERED.labels(severity=severity).inc()
    FINDINGS_BY_TYPE.labels(vulnerability_type=vulnerability_type).inc()


def record_report_generated(format: str):
    """Record a generated report"""
    REPORTS_GENERATED.labels(format=format).inc()


def record_auth_attempt(success: bool):
    """Record authentication attempt"""
    result = "success" if success else "failure"
    AUTH_ATTEMPTS.labels(result=result).inc()


def record_rate_limit_hit(tier: str, endpoint: str):
    """Record rate limit hit"""
    RATE_LIMIT_HITS.labels(tier=tier, endpoint=endpoint).inc()


# =============================================================================
# Tool execution metrics helpers
# =============================================================================


def record_tool_execution(tool_name: str, duration: float, success: bool, safety_level: str = "read_only"):
    """Record tool execution metrics"""
    status = "success" if success else "failure"
    TOOL_EXECUTION_DURATION.labels(tool_name=tool_name, status=status).observe(duration)
    TOOL_EXECUTIONS_TOTAL.labels(tool_name=tool_name, status=status, safety_level=safety_level).inc()


def record_tool_output_size(tool_name: str, size_bytes: int):
    """Record tool output size"""
    TOOL_OUTPUT_SIZE.labels(tool_name=tool_name).observe(size_bytes)


# =============================================================================
# Cache metrics helpers
# =============================================================================


def record_cache_hit(cache_tier: str, cache_name: str = "default"):
    """Record cache hit"""
    CACHE_HITS_TOTAL.labels(cache_tier=cache_tier, cache_name=cache_name).inc()


def record_cache_miss(cache_tier: str, cache_name: str = "default"):
    """Record cache miss"""
    CACHE_MISSES_TOTAL.labels(cache_tier=cache_tier, cache_name=cache_name).inc()


def record_cache_eviction(cache_tier: str, cache_name: str = "default"):
    """Record cache eviction"""
    CACHE_EVICTIONS_TOTAL.labels(cache_tier=cache_tier, cache_name=cache_name).inc()


def update_cache_size(cache_tier: str, size: int, cache_name: str = "default"):
    """Update cache size gauge"""
    CACHE_SIZE.labels(cache_tier=cache_tier, cache_name=cache_name).set(size)


# =============================================================================
# Memory metrics helpers
# =============================================================================


def update_memory_metrics():
    """Update memory usage metrics"""
    import os
    process = psutil.Process(os.getpid())
    
    MEMORY_USAGE_BYTES.labels(type="rss").set(process.memory_info().rss)
    MEMORY_USAGE_BYTES.labels(type="vms").set(process.memory_info().vms)
    
    # System memory
    system_mem = psutil.virtual_memory()
    MEMORY_USAGE_BYTES.labels(type="system_used").set(system_mem.used)
    MEMORY_USAGE_BYTES.labels(type="system_available").set(system_mem.available)


def record_gc_collection(generation: int):
    """Record garbage collection"""
    MEMORY_GC_COLLECTIONS.labels(generation=str(generation)).inc()


# =============================================================================
# Agent metrics helpers
# =============================================================================


def record_agent_execution(agent_type: str, iterations: int, duration: float, status: str, findings: int):
    """Record agent execution metrics"""
    AGENT_ITERATIONS.labels(agent_type=agent_type).observe(iterations)
    AGENT_EXECUTION_DURATION.labels(agent_type=agent_type, status=status).observe(duration)
    AGENT_FINDINGS_DISCOVERED.labels(agent_type=agent_type).observe(findings)


# =============================================================================
# Metrics endpoint
# =============================================================================


def get_metrics():
    """Generate Prometheus metrics output"""
    # Update memory metrics before generating
    update_memory_metrics()
    return generate_latest(METRICS_REGISTRY)


def init_app_info(version: str, environment: str):
    """Initialize application info metric"""
    APP_INFO.info({"version": version, "environment": environment})


# =============================================================================
# Health check with metrics
# =============================================================================


def get_health_status():
    """Get comprehensive health status with metrics"""
    # Count total requests in last collection
    total_requests = 0
    for metric in METRICS_REGISTRY.collect():
        if metric.name == "http_requests_total":
            for sample in metric.samples:
                total_requests += sample.value

    # Get memory info
    import os
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()

    return {
        "status": "healthy",
        "metrics": {
            "total_requests": int(total_requests),
            "active_scans": int(SCANS_ACTIVE._value.get()),
            "active_sessions": int(ACTIVE_SESSIONS._value.get()),
        },
        "memory": {
            "rss_mb": round(mem_info.rss / (1024 * 1024), 2),
            "vms_mb": round(mem_info.vms / (1024 * 1024), 2),
        },
        "timestamp": time.time(),
    }


# =============================================================================
# Performance monitoring decorator
# =============================================================================


def monitor_performance(operation_type: str):
    """
    Comprehensive performance monitoring decorator.
    Records duration, errors, and custom metrics.
    
    Usage:
        @monitor_performance("database_query")
        async def fetch_data():
            return await db.query()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            error_type = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error_type = type(e).__name__
                raise
            finally:
                duration = time.time() - start_time
                
                # Record timing
                DB_QUERY_DURATION.labels(query_type=operation_type).observe(duration)
                
                # Record success/failure
                status = "error" if error_type else "success"
                DB_QUERIES_TOTAL.labels(query_type=operation_type, status=status).inc()
                
                if error_type:
                    HTTP_ERRORS_TOTAL.labels(
                        method="internal",
                        endpoint=operation_type,
                        status_code="500",
                        error_type=error_type
                    ).inc()
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            error_type = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error_type = type(e).__name__
                raise
            finally:
                duration = time.time() - start_time
                
                DB_QUERY_DURATION.labels(query_type=operation_type).observe(duration)
                status = "error" if error_type else "success"
                DB_QUERIES_TOTAL.labels(query_type=operation_type, status=status).inc()
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator
