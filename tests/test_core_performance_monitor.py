"""Tests for core.performance_monitor module."""

import time

import pytest


class TestPerformanceMetric:
    def test_create_metric(self):
        from core.performance_monitor import PerformanceMetric

        m = PerformanceMetric(name="test", duration_ms=100.0)
        assert m.name == "test"
        assert m.duration_ms == 100.0
        assert m.memory_delta_mb == 0.0
        assert m.metadata == {}

    def test_metric_with_metadata(self):
        from core.performance_monitor import PerformanceMetric

        m = PerformanceMetric(name="test", duration_ms=50.0, metadata={"endpoint": "/api"})
        assert m.metadata["endpoint"] == "/api"


class TestMetricStats:
    def test_initial_state(self):
        from core.performance_monitor import MetricStats

        s = MetricStats()
        assert s.count == 0
        assert s.min_duration_ms == float("inf")

    def test_update(self):
        from core.performance_monitor import MetricStats

        s = MetricStats()
        s.update(100.0)
        assert s.count == 1
        assert s.total_duration_ms == 100.0
        assert s.min_duration_ms == 100.0
        assert s.max_duration_ms == 100.0
        assert s.avg_duration_ms == 100.0

    def test_update_multiple(self):
        from core.performance_monitor import MetricStats

        s = MetricStats()
        s.update(50.0)
        s.update(150.0)
        assert s.count == 2
        assert s.total_duration_ms == 200.0
        assert s.min_duration_ms == 50.0
        assert s.max_duration_ms == 150.0
        assert s.avg_duration_ms == 100.0

    def test_update_with_slow_threshold_default(self):
        from core.performance_monitor import MetricStats

        s = MetricStats()
        s.update(500.0)
        assert s.slow_queries == 0
        s.update(1500.0)
        assert s.slow_queries == 1

    def test_update_with_custom_slow_threshold(self):
        from core.performance_monitor import MetricStats

        s = MetricStats()
        s.update(50.0, slow_threshold_ms=30.0)
        assert s.slow_queries == 1


class TestPerformanceMonitor:
    def test_init(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        assert pm._enabled is True
        assert pm.slow_query_threshold_ms == 1000.0
        assert pm.memory_threshold_mb == 100.0
        assert pm.max_metrics == 10000

    def test_enable_disable(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        assert pm._enabled is True
        pm.disable()
        assert pm._enabled is False
        pm.enable()
        assert pm._enabled is True

    def test_configure_thresholds(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        pm.configure(slow_query_threshold_ms=500.0, memory_threshold_mb=50.0)
        assert pm.slow_query_threshold_ms == 500.0
        assert pm.memory_threshold_mb == 50.0

    def test_start_stop_timer(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        pm.start_timer("test_op")
        time.sleep(0.01)
        metric = pm.stop_timer("test_op")
        assert metric is not None
        assert metric.name == "test_op"
        assert metric.duration_ms > 0

    def test_stop_timer_returns_none_when_disabled(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        pm.disable()
        pm.start_timer("test_op")
        metric = pm.stop_timer("test_op")
        assert metric is None

    def test_stop_nonexistent_timer(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        result = pm.stop_timer("nonexistent")
        assert result is None

    def test_timer_context_manager(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        with pm.timer("ctx_test"):
            time.sleep(0.01)
        stats = pm.get_stats("general")
        assert stats["count"] == 1
        assert stats["avg_duration_ms"] > 0

    def test_get_stats_empty(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        stats = pm.get_stats("general")
        assert stats["count"] == 0
        assert stats["avg_duration_ms"] == 0.0

    def test_get_stats_all_categories(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        pm.start_timer("database.query")
        pm.stop_timer("database.query")
        all_stats = pm.get_stats()
        assert "database" in all_stats
        assert all_stats["database"]["count"] == 1

    def test_slow_operations_tracking(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor(slow_query_threshold_ms=0.01)
        pm.start_timer("fast_op")
        pm.stop_timer("fast_op")
        pm.start_timer("slow_op")
        time.sleep(0.05)
        pm.stop_timer("slow_op")
        slow_ops = pm.get_slow_operations()
        assert any(m.name == "slow_op" for m in slow_ops)

    def test_recent_metrics(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        pm.start_timer("op1")
        pm.stop_timer("op1")
        recent = pm.get_recent_metrics()
        assert len(recent) >= 1

    def test_reset(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        pm.start_timer("op1")
        pm.stop_timer("op1")
        pm.reset()
        assert len(pm._metrics) == 0
        assert len(pm._stats) == 0
        assert len(pm._active_timers) == 0

    def test_max_metrics_eviction(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor(max_metrics=5)
        for i in range(10):
            pm.start_timer(f"op{i}")
            pm.stop_timer(f"op{i}")
        assert len(pm._metrics) == 5

    def test_report(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        pm.start_timer("op1")
        pm.stop_timer("op1")
        report = pm.report()
        assert "summary" in report
        assert "categories" in report
        assert "config" in report
        assert report["summary"]["total_operations"] == 1

    def test_report_empty(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        report = pm.report()
        assert report["summary"]["total_operations"] == 0
        assert report["summary"]["slow_percentage"] == 0.0

    def test_metric_category_database(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        pm.start_timer("db_query_users")
        pm.stop_timer("db_query_users")
        pm.start_timer("database.select")
        pm.stop_timer("database.select")
        stats = pm.get_stats("database")
        assert stats["count"] == 2

    def test_metric_category_api(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        pm.start_timer("api_endpoint_login")
        pm.stop_timer("api_endpoint_login")
        stats = pm.get_stats("api")
        assert stats["count"] == 1

    def test_metric_category_tools(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        pm.start_timer("tool_nmap_scan")
        pm.stop_timer("tool_nmap_scan")
        stats = pm.get_stats("tools")
        assert stats["count"] == 1

    def test_metric_category_cache(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        pm.start_timer("cache_lookup")
        pm.stop_timer("cache_lookup")
        stats = pm.get_stats("cache")
        assert stats["count"] == 1

    def test_timed_decorator_sync(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        decorated = pm.timed(name="sync_fn")(lambda: 42)
        result = decorated()
        assert result == 42
        stats = pm.get_stats("general")
        assert stats["count"] >= 1

    def test_timed_decorator_disabled(self):
        from core.performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        pm.disable()
        decorated = pm.timed(name="skip_fn")(lambda: 99)
        result = decorated()
        assert result == 99
        stats = pm.get_stats("general")
        assert stats["count"] == 0


class TestPerformanceTimer:
    def test_context_manager(self):
        from core.performance_monitor import PerformanceMonitor, _PerformanceTimer

        pm = PerformanceMonitor()
        timer = _PerformanceTimer(pm, "ctx_test", True, None)
        with timer:
            time.sleep(0.005)
        stats = pm.get_stats("general")
        assert stats["count"] == 1


class TestGlobalMonitor:
    def test_get_monitor_singleton(self):
        from core.performance_monitor import get_monitor

        m1 = get_monitor()
        m2 = get_monitor()
        assert m1 is m2

    def test_configure_monitor(self):
        from core.performance_monitor import configure_monitor, get_monitor

        configure_monitor(slow_query_threshold_ms=500.0)
        monitor = get_monitor()
        assert monitor.slow_query_threshold_ms == 500.0

    def test_timed_convenience(self):
        from core.performance_monitor import get_monitor, timed

        decorated = timed(name="conv_test")(lambda: "ok")
        result = decorated()
        assert result == "ok"
