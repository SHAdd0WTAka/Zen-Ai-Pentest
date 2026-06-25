"""Smoke tests for core/subdomain_monitor.py"""

import pytest

from core.subdomain_monitor import (
    ContinuousSubdomainScanner,
    MonitoredDomain,
    SubdomainDiff,
    SubdomainMonitor,
    check_domain_changes,
)


class TestSubdomainDiff:
    def test_creation(self):
        diff = SubdomainDiff(
            new=["admin.example.com"],
            removed=["old.example.com"],
            unchanged=["www.example.com"],
            changed=[],
        )
        assert diff.new == ["admin.example.com"]
        assert diff.removed == ["old.example.com"]
        assert diff.unchanged == ["www.example.com"]
        assert diff.changed == []


class TestMonitoredDomain:
    def test_creation(self):
        from datetime import datetime, timezone

        domain = MonitoredDomain(
            domain="example.com",
            created_at=datetime.now(timezone.utc),
            scan_interval_hours=48,
        )
        assert domain.domain == "example.com"
        assert domain.scan_interval_hours == 48
        assert domain.notify_on_changes is True


class TestSubdomainMonitor:
    def test_init_no_db(self):
        monitor = SubdomainMonitor()
        assert monitor.db is None
        assert monitor.storage_path is None

    def test_init_with_storage_path(self, tmp_path):
        monitor = SubdomainMonitor(storage_path=str(tmp_path))
        assert monitor.storage_path == tmp_path

    def test_get_monitored_domains_empty(self):
        monitor = SubdomainMonitor()
        assert monitor.get_monitored_domains() == []

    def test_remove_nonexistent(self):
        monitor = SubdomainMonitor()
        assert monitor.remove_monitored_domain("nonexistent.com") is False


class TestContinuousSubdomainScanner:
    def test_init(self):
        monitor = SubdomainMonitor()
        scanner = ContinuousSubdomainScanner(monitor)
        assert scanner.monitor is monitor
        assert scanner._running is False
