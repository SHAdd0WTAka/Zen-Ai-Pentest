"""
Prometheus Metrics Integration für Zen AI Pentest

Provides:
- Request latency histograms
- Request counters (by endpoint, status code, method)
- Error rates
- Active connections gauge
- Business metrics (scans, findings, reports)
"""

import time
from typing import Callable, Optional
from functools import wraps

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    CollectorRegistry,
    generate_latest,
    generate_latest
)


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
    registry=METRICS_REGISTRY
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
    registry=METRICS_REGISTRY
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
    registry=METRICS_REGISTRY
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
    registry=METRICS_REGISTRY
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

# Database metrics
DB_CONNECTIONS_ACTIVE = Gauge(
    "db_connections_active",
    "Number of active database connections",
    registry=METRICS_REGISTRY
)

DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=METRICS_REGISTRY
)

# Application info
APP_INFO = Info(
    "app_info",
    "Application information",
    registry=METRICS_REGISTRY
)

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
                method=method,
                endpoint=request_path,
                status_code="500",
                error_type=type(e).__name__
            ).inc()
            raise
        finally:
            duration = time.time() - start_time
            
            # Record metrics
            HTTP_REQUEST_DURATION.labels(
                method=method,
                endpoint=request_path,
                status_code=str(status_code)
            ).observe(duration)
            
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=request_path,
                status_code=str(status_code)
            ).inc()
            
            HTTP_RESPONSE_SIZE.labels(
                method=method,
                endpoint=request_path
            ).observe(response_size)
            
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=request_path).dec()


# =============================================================================
# Decorator for function-level metrics
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
        return wrapper
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
        return wrapper
    return decorator


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
# Metrics endpoint
# =============================================================================

def get_metrics():
    """Generate Prometheus metrics output"""
    return generate_latest(METRICS_REGISTRY)


def init_app_info(version: str, environment: str):
    """Initialize application info metric"""
    APP_INFO.info({
        "version": version,
        "environment": environment
    })


# =============================================================================
# Health check with metrics
# =============================================================================

def get_health_status():
    """Get comprehensive health status with metrics"""
    pass  # Registry imported but metrics come from METRICS_REGISTRY
    
    # Count total requests in last collection
    total_requests = 0
    for metric in METRICS_REGISTRY.collect():
        if metric.name == "http_requests_total":
            for sample in metric.samples:
                total_requests += sample.value
    
    return {
        "status": "healthy",
        "metrics": {
            "total_requests": int(total_requests),
            "active_scans": int(SCANS_ACTIVE._value.get()),
            "active_sessions": int(ACTIVE_SESSIONS._value.get())
        }
    }
