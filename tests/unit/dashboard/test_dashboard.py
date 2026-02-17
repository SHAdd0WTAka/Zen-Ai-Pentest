"""
Unit tests for Dashboard System

Tests the dashboard components including:
- Event system
- WebSocket handling
- Metrics collection
"""

import pytest
import asyncio
from datetime import datetime, timedelta

# Import dashboard components
try:
    from dashboard import DashboardManager, DashboardEvent, EventType
    from dashboard.events import EventStream
    from dashboard.websocket import DashboardWebSocket, WebSocketConnection
    from dashboard.metrics import MetricsCollector, MetricPoint
except ImportError:
    import sys
    sys.path.insert(0, "../../..")
    from dashboard import DashboardManager, DashboardEvent, EventType
    from dashboard.events import EventStream
    from dashboard.websocket import DashboardWebSocket, WebSocketConnection
    from dashboard.metrics import MetricsCollector, MetricPoint


class TestDashboardEvent:
    """Test DashboardEvent"""
    
    def test_event_creation(self):
        """Test event creation"""
        event = DashboardEvent(
            type=EventType.TASK_PROGRESS,
            data={"task_id": "123", "progress": 50},
            source="test"
        )
        
        assert event.type == EventType.TASK_PROGRESS
        assert event.data["progress"] == 50
        assert event.source == "test"
        assert event.id is not None
    
    def test_event_to_dict(self):
        """Test event serialization"""
        event = DashboardEvent(
            type=EventType.SYSTEM_METRICS,
            data={"cpu": 50},
            priority=2
        )
        
        data = event.to_dict()
        
        assert data["type"] == "system.metrics"
        assert data["data"]["cpu"] == 50
        assert data["priority"] == 2
        assert "timestamp" in data
    
    def test_task_progress_factory(self):
        """Test task progress event factory"""
        event = DashboardEvent.task_progress(
            task_id="123",
            progress=75,
            message="Almost done"
        )
        
        assert event.type == EventType.TASK_PROGRESS
        assert event.data["task_id"] == "123"
        assert event.data["progress"] == 75
        assert event.data["message"] == "Almost done"
    
    def test_security_alert_factory(self):
        """Test security alert factory"""
        event = DashboardEvent.security_alert(
            alert_type="sql_injection",
            severity="high",
            details={"target": "example.com"}
        )
        
        assert event.type == EventType.SECURITY_ALERT
        assert event.data["severity"] == "high"
        assert event.priority == 4  # High priority


class TestEventStream:
    """Test EventStream"""
    
    def test_stream_filtering(self):
        """Test event filtering"""
        stream = EventStream(
            event_types=[EventType.TASK_PROGRESS],
            min_priority=3
        )
        
        # Matching event
        event_match = DashboardEvent(
            type=EventType.TASK_PROGRESS,
            priority=4
        )
        
        # Non-matching: wrong type
        event_wrong_type = DashboardEvent(
            type=EventType.SYSTEM_METRICS,
            priority=4
        )
        
        # Non-matching: priority too low
        event_low_priority = DashboardEvent(
            type=EventType.TASK_PROGRESS,
            priority=1
        )
        
        assert stream.matches(event_match) is True
        assert stream.matches(event_wrong_type) is False
        assert stream.matches(event_low_priority) is False
    
    def test_buffer_management(self):
        """Test event buffering"""
        stream = EventStream(buffer_size=3)
        
        # Add events
        for i in range(5):
            event = DashboardEvent(
                type=EventType.TASK_PROGRESS,
                data={"index": i}
            )
            stream.add(event)
        
        # Buffer should only keep last 3
        recent = stream.get_recent(10)
        assert len(recent) == 3
        assert recent[-1].data["index"] == 4


class TestDashboardManager:
    """Test DashboardManager"""
    
    @pytest.fixture
    async def dashboard(self):
        """Create test dashboard"""
        from dashboard import DashboardConfig
        
        config = DashboardConfig(
            websocket_enabled=False,  # Skip WebSocket for tests
            metrics_enabled=True,
            metrics_interval=1
        )
        
        db = DashboardManager(config)
        await db.start()
        
        yield db
        
        await db.stop()
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test dashboard lifecycle"""
        from dashboard import DashboardConfig
        
        config = DashboardConfig(
            websocket_enabled=False,
            metrics_enabled=False
        )
        
        db = DashboardManager(config)
        
        assert not db._running
        
        await db.start()
        assert db._running
        
        await db.stop()
        assert not db._running
    
    @pytest.mark.asyncio
    async def test_broadcast(self, dashboard):
        """Test event broadcasting"""
        event = DashboardEvent(
            type=EventType.NOTIFICATION,
            data={"message": "Test"}
        )
        
        # Should work even without WebSocket
        count = await dashboard.broadcast(event)
        
        # Event should be buffered
        assert len(dashboard._event_buffer) > 0
    
    @pytest.mark.asyncio
    async def test_broadcast_task_progress(self, dashboard):
        """Test task progress broadcast"""
        count = await dashboard.broadcast_task_progress(
            task_id="test-123",
            progress=50,
            message="Halfway there"
        )
        
        # Check event was buffered
        events = [e for e in dashboard._event_buffer 
                  if e.type == EventType.TASK_PROGRESS]
        assert len(events) > 0
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, dashboard):
        """Test getting statistics"""
        stats = dashboard.get_statistics()
        
        assert "running" in stats
        assert stats["running"] is True
        assert "buffered_events" in stats


class TestMetricsCollector:
    """Test MetricsCollector"""
    
    @pytest.fixture
    async def collector(self):
        """Create test collector"""
        coll = MetricsCollector(collection_interval=1)
        await coll.start()
        
        yield coll
        
        await coll.stop()
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test collector lifecycle"""
        coll = MetricsCollector(collection_interval=60)
        
        assert not coll._running
        
        await coll.start()
        assert coll._running
        
        await coll.stop()
        assert not coll._running
    
    def test_metric_point(self):
        """Test MetricPoint"""
        point = MetricPoint(
            timestamp=datetime.utcnow(),
            value=42.5,
            labels={"host": "localhost"}
        )
        
        assert point.value == 42.5
        assert point.labels["host"] == "localhost"
    
    @pytest.mark.asyncio
    async def test_get_current_metrics(self, collector):
        """Test getting current metrics"""
        # Wait for at least one collection
        await asyncio.sleep(1.5)
        
        metrics = collector.get_current_metrics()
        
        assert "timestamp" in metrics
        assert "system" in metrics
    
    @pytest.mark.asyncio
    async def test_metric_history(self, collector):
        """Test metric history"""
        # Add some data points
        now = datetime.utcnow()
        
        collector._metrics["test_metric"] = [
            MetricPoint(timestamp=now - timedelta(minutes=5), value=10, labels={}),
            MetricPoint(timestamp=now - timedelta(minutes=3), value=20, labels={}),
            MetricPoint(timestamp=now - timedelta(minutes=1), value=30, labels={}),
        ]
        
        history = collector.get_metric_history("test_metric", duration_seconds=300)
        
        assert len(history) == 3


class TestMetricsAggregator:
    """Test MetricsAggregator"""
    
    def test_calculate_average(self):
        """Test average calculation"""
        from dashboard.metrics import MetricsAggregator
        
        points = [
            MetricPoint(timestamp=datetime.utcnow(), value=10, labels={}),
            MetricPoint(timestamp=datetime.utcnow(), value=20, labels={}),
            MetricPoint(timestamp=datetime.utcnow(), value=30, labels={}),
        ]
        
        avg = MetricsAggregator.calculate_average(points)
        assert avg == 20.0
    
    def test_calculate_min_max(self):
        """Test min/max calculation"""
        from dashboard.metrics import MetricsAggregator
        
        points = [
            MetricPoint(timestamp=datetime.utcnow(), value=10, labels={}),
            MetricPoint(timestamp=datetime.utcnow(), value=50, labels={}),
            MetricPoint(timestamp=datetime.utcnow(), value=30, labels={}),
        ]
        
        min_val, max_val = MetricsAggregator.calculate_min_max(points)
        assert min_val == 10
        assert max_val == 50
    
    def test_detect_trend_increasing(self):
        """Test increasing trend detection"""
        from dashboard.metrics import MetricsAggregator
        
        points = [
            MetricPoint(timestamp=datetime.utcnow(), value=10, labels={}),
            MetricPoint(timestamp=datetime.utcnow(), value=20, labels={}),
            MetricPoint(timestamp=datetime.utcnow(), value=30, labels={}),
            MetricPoint(timestamp=datetime.utcnow(), value=40, labels={}),
        ]
        
        trend = MetricsAggregator.detect_trend(points)
        assert trend == "increasing"
    
    def test_detect_trend_decreasing(self):
        """Test decreasing trend detection"""
        from dashboard.metrics import MetricsAggregator
        
        points = [
            MetricPoint(timestamp=datetime.utcnow(), value=40, labels={}),
            MetricPoint(timestamp=datetime.utcnow(), value=30, labels={}),
            MetricPoint(timestamp=datetime.utcnow(), value=20, labels={}),
            MetricPoint(timestamp=datetime.utcnow(), value=10, labels={}),
        ]
        
        trend = MetricsAggregator.detect_trend(points)
        assert trend == "decreasing"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
