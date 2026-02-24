"""
Tests for SIEM Integration Module
Splunk, Elastic, Azure Sentinel, IBM QRadar
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from modules.siem_integration import (
    AzureSentinelConnector,
    BaseSIEMConnector,
    ElasticConnector,
    QRadarConnector,
    SecurityEvent,
    SIEMConfig,
    SIEMIntegrationManager,
    SplunkConnector,
    create_siem_connector,
)


# Fixtures
@pytest.fixture
def splunk_config():
    """Create a Splunk SIEM config"""
    return SIEMConfig(
        name="test-splunk",
        type="splunk",
        url="https://splunk.example.com:8088",
        api_key="test-api-key-12345",
        index="security",
        verify_ssl=True,
        timeout=30,
    )


@pytest.fixture
def elastic_config():
    """Create an Elastic SIEM config"""
    return SIEMConfig(
        name="test-elastic",
        type="elastic",
        url="https://elastic.example.com:9200",
        api_key="test-elastic-api-key",
        index="zen-ai-security",
        verify_ssl=True,
        timeout=30,
    )


@pytest.fixture
def sentinel_config():
    """Create an Azure Sentinel config"""
    return SIEMConfig(
        name="test-sentinel",
        type="sentinel",
        url="https://ods.opinsights.azure.com",
        api_key="dGVzdC1zaGFyZWQta2V5LWFhYWE=",  # Valid base64: test-shared-key-aaaa
        username="test-workspace-id",
        verify_ssl=True,
        timeout=30,
    )


@pytest.fixture
def qradar_config():
    """Create a QRadar config"""
    return SIEMConfig(
        name="test-qradar",
        type="qradar",
        url="https://qradar.example.com",
        api_key="test-qradar-token",
        verify_ssl=True,
        timeout=30,
    )


@pytest.fixture
def sample_security_event():
    """Create a sample security event"""
    return SecurityEvent(
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        severity="high",
        event_type="vulnerability_detected",
        source="zen-ai-pentest",
        target="192.168.1.100",
        description="SQL Injection vulnerability found in login form",
        cve_id="CVE-2024-0001",
        cvss_score=9.8,
        raw_data={"scan_id": "scan-123", "tool": "sqlmap"},
    )


@pytest.fixture
def mock_session():
    """Create a mock requests session"""
    with patch(
        "modules.siem_integration.requests.Session"
    ) as mock_session_class:
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        yield mock_session


# SIEMConfig Tests
class TestSIEMConfig:
    """Tests for SIEMConfig dataclass"""

    def test_splunk_config_creation(self, splunk_config):
        """Test Splunk config creation"""
        assert splunk_config.name == "test-splunk"
        assert splunk_config.type == "splunk"
        assert splunk_config.url == "https://splunk.example.com:8088"
        assert splunk_config.api_key == "test-api-key-12345"
        assert splunk_config.index == "security"
        assert splunk_config.verify_ssl is True
        assert splunk_config.timeout == 30

    def test_elastic_config_creation(self, elastic_config):
        """Test Elastic config creation"""
        assert elastic_config.type == "elastic"
        assert elastic_config.index == "zen-ai-security"

    def test_sentinel_config_creation(self, sentinel_config):
        """Test Sentinel config creation"""
        assert sentinel_config.type == "sentinel"
        assert sentinel_config.username == "test-workspace-id"
        # Base64 encoded key for testing
        assert sentinel_config.api_key == "dGVzdC1zaGFyZWQta2V5LWFhYWE="

    def test_qradar_config_creation(self, qradar_config):
        """Test QRadar config creation"""
        assert qradar_config.type == "qradar"
        assert qradar_config.api_key == "test-qradar-token"

    def test_config_with_optional_fields(self):
        """Test config with optional fields"""
        config = SIEMConfig(
            name="minimal-config",
            type="splunk",
            url="https://splunk.example.com",
            # api_key, index, username, password are optional
        )

        assert config.api_key is None
        assert config.index is None
        assert config.username is None
        assert config.password is None


# SecurityEvent Tests
class TestSecurityEvent:
    """Tests for SecurityEvent dataclass"""

    def test_security_event_creation(self, sample_security_event):
        """Test security event creation"""
        assert sample_security_event.timestamp == datetime(
            2024, 1, 15, 10, 30, 0
        )
        assert sample_security_event.severity == "high"
        assert sample_security_event.event_type == "vulnerability_detected"
        assert sample_security_event.source == "zen-ai-pentest"
        assert sample_security_event.target == "192.168.1.100"
        assert sample_security_event.cve_id == "CVE-2024-0001"
        assert sample_security_event.cvss_score == 9.8
        assert sample_security_event.raw_data is not None

    def test_security_event_minimal(self):
        """Test security event with minimal fields"""
        event = SecurityEvent(
            timestamp=datetime.now(),
            severity="medium",
            event_type="scan_completed",
            source="zen-ai-pentest",
            target="10.0.0.1",
            description="Scan completed successfully",
            # cve_id, cvss_score, raw_data are optional
        )

        assert event.cve_id is None
        assert event.cvss_score is None
        assert event.raw_data is None


# SplunkConnector Tests
class TestSplunkConnector:
    """Tests for SplunkConnector"""

    def test_initialization(self, splunk_config):
        """Test Splunk connector initialization"""
        with patch("modules.siem_integration.requests.Session"):
            connector = SplunkConnector(splunk_config)

            assert connector.config == splunk_config
            assert connector.session is not None

    def test_connect_success(self, splunk_config):
        """Test successful connection to Splunk"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response

            connector = SplunkConnector(splunk_config)
            result = connector.connect()

            assert result is True
            mock_session.get.assert_called_once()
            # Verify correct URL and headers
            call_args = mock_session.get.call_args
            assert "/services/collector/health" in call_args[0][0]

    def test_connect_failure(self, splunk_config):
        """Test failed connection to Splunk"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 401
            mock_session.get.return_value = mock_response

            connector = SplunkConnector(splunk_config)
            result = connector.connect()

            assert result is False

    def test_connect_exception(self, splunk_config):
        """Test connection with exception"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            mock_session.get.side_effect = Exception("Connection error")

            connector = SplunkConnector(splunk_config)
            result = connector.connect()

            assert result is False

    def test_send_event_success(self, splunk_config, sample_security_event):
        """Test sending event to Splunk"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_session.post.return_value = mock_response

            connector = SplunkConnector(splunk_config)
            result = connector.send_event(sample_security_event)

            assert result is True
            mock_session.post.assert_called_once()

            # Verify payload structure
            call_args = mock_session.post.call_args
            assert "Authorization" in call_args[1]["headers"]
            assert (
                "Splunk test-api-key-12345"
                == call_args[1]["headers"]["Authorization"]
            )

    def test_send_event_failure(self, splunk_config, sample_security_event):
        """Test sending event failure"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 401
            mock_session.post.return_value = mock_response

            connector = SplunkConnector(splunk_config)
            result = connector.send_event(sample_security_event)

            assert result is False

    def test_send_events_batch_success(
        self, splunk_config, sample_security_event
    ):
        """Test sending batch events to Splunk"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_session.post.return_value = mock_response

            connector = SplunkConnector(splunk_config)
            events = [sample_security_event, sample_security_event]
            result = connector.send_events_batch(events)

            assert result is True
            # Should send as single batch
            mock_session.post.assert_called_once()

    def test_query_threat_intel_success(self, splunk_config):
        """Test querying threat intelligence from Splunk"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [{"indicator": "1.2.3.4"}]
            }
            mock_session.post.return_value = mock_response

            connector = SplunkConnector(splunk_config)
            result = connector.query_threat_intel("1.2.3.4")

            assert result is not None
            assert result["results"][0]["indicator"] == "1.2.3.4"

    def test_query_threat_intel_not_found(self, splunk_config):
        """Test querying threat intel with no results"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 404
            mock_session.post.return_value = mock_response

            connector = SplunkConnector(splunk_config)
            result = connector.query_threat_intel("1.2.3.4")

            assert result is None


# ElasticConnector Tests
class TestElasticConnector:
    """Tests for ElasticConnector"""

    def test_initialization(self, elastic_config):
        """Test Elastic connector initialization"""
        with patch("modules.siem_integration.requests.Session"):
            connector = ElasticConnector(elastic_config)

            assert connector.config == elastic_config

    def test_connect_success(self, elastic_config):
        """Test successful connection to Elastic"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response

            connector = ElasticConnector(elastic_config)
            result = connector.connect()

            assert result is True
            call_args = mock_session.get.call_args
            assert "_cluster/health" in call_args[0][0]

    def test_send_event_success(self, elastic_config, sample_security_event):
        """Test sending event to Elastic"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 201
            mock_session.post.return_value = mock_response

            connector = ElasticConnector(elastic_config)
            result = connector.send_event(sample_security_event)

            assert result is True

            # Verify payload structure
            call_args = mock_session.post.call_args
            assert call_args[1]["json"]["@timestamp"] is not None
            assert call_args[1]["json"]["severity"] == "high"

    def test_send_events_batch_success(
        self, elastic_config, sample_security_event
    ):
        """Test sending batch events to Elastic"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_session.post.return_value = mock_response

            connector = ElasticConnector(elastic_config)
            events = [sample_security_event, sample_security_event]
            result = connector.send_events_batch(events)

            assert result is True
            call_args = mock_session.post.call_args
            assert "_bulk" in call_args[0][0]
            assert (
                call_args[1]["headers"]["Content-Type"]
                == "application/x-ndjson"
            )

    def test_query_threat_intel(self, elastic_config):
        """Test querying threat intelligence from Elastic"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"hits": {"hits": []}}
            mock_session.post.return_value = mock_response

            connector = ElasticConnector(elastic_config)
            result = connector.query_threat_intel("1.2.3.4")

            assert result is not None


# AzureSentinelConnector Tests
class TestAzureSentinelConnector:
    """Tests for AzureSentinelConnector"""

    def test_initialization(self, sentinel_config):
        """Test Sentinel connector initialization"""
        with patch("modules.siem_integration.requests.Session"):
            connector = AzureSentinelConnector(sentinel_config)

            assert connector.config == sentinel_config
            assert connector.workspace_id == "test-workspace-id"
            assert connector.shared_key == "dGVzdC1zaGFyZWQta2V5LWFhYWE="

    def test_connect_success(self, sentinel_config):
        """Test successful connection to Sentinel"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = (
                401  # 401 means auth worked but query was invalid
            )
            mock_session.get.return_value = mock_response

            connector = AzureSentinelConnector(sentinel_config)
            result = connector.connect()

            assert result is True

    def test_build_auth_header(self, sentinel_config):
        """Test building authentication header"""
        with patch("modules.siem_integration.requests.Session"):
            connector = AzureSentinelConnector(sentinel_config)
            headers = connector._build_auth_header()

            assert "Authorization" in headers
            assert headers["Authorization"].startswith("SharedKey")
            assert "Content-Type" in headers
            assert "x-ms-date" in headers
            assert "Log-Type" in headers

    def test_send_event_success(self, sentinel_config, sample_security_event):
        """Test sending event to Sentinel"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_session.post.return_value = mock_response

            connector = AzureSentinelConnector(sentinel_config)
            result = connector.send_event(sample_security_event)

            assert result is True

            # Verify it's a list
            call_args = mock_session.post.call_args
            assert isinstance(call_args[1]["json"], list)
            assert len(call_args[1]["json"]) == 1

    def test_send_events_batch(self, sentinel_config, sample_security_event):
        """Test sending batch events to Sentinel"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_session.post.return_value = mock_response

            connector = AzureSentinelConnector(sentinel_config)
            events = [sample_security_event, sample_security_event]
            result = connector.send_events_batch(events)

            assert result is True
            call_args = mock_session.post.call_args
            assert len(call_args[1]["json"]) == 2


# QRadarConnector Tests
class TestQRadarConnector:
    """Tests for QRadarConnector"""

    def test_initialization(self, qradar_config):
        """Test QRadar connector initialization"""
        with patch("modules.siem_integration.requests.Session"):
            connector = QRadarConnector(qradar_config)

            assert connector.config == qradar_config

    def test_connect_success(self, qradar_config):
        """Test successful connection to QRadar"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response

            connector = QRadarConnector(qradar_config)
            result = connector.connect()

            assert result is True

    def test_build_auth_header_with_api_key(self, qradar_config):
        """Test building auth header with API key"""
        with patch("modules.siem_integration.requests.Session"):
            connector = QRadarConnector(qradar_config)
            headers = connector._build_auth_header()

            assert headers["SEC"] == "test-qradar-token"

    def test_build_auth_header_with_credentials(self):
        """Test building auth header with username/password"""
        config = SIEMConfig(
            name="test-qradar",
            type="qradar",
            url="https://qradar.example.com",
            username="admin",
            password="secret",
        )

        with patch("modules.siem_integration.requests.Session"):
            connector = QRadarConnector(config)
            headers = connector._build_auth_header()

            assert "Authorization" in headers
            assert headers["Authorization"].startswith("Basic")

    def test_send_event_success(self, qradar_config, sample_security_event):
        """Test sending event to QRadar"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 201
            mock_session.post.return_value = mock_response

            connector = QRadarConnector(qradar_config)
            result = connector.send_event(sample_security_event)

            assert result is True

    def test_send_events_batch(self, qradar_config, sample_security_event):
        """Test sending batch events to QRadar"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 201
            mock_session.post.return_value = mock_response

            connector = QRadarConnector(qradar_config)
            events = [sample_security_event, sample_security_event]
            result = connector.send_events_batch(events)

            assert result is True
            # QRadar sends events one by one
            assert mock_session.post.call_count == 2

    def test_send_events_batch_partial_failure(
        self, qradar_config, sample_security_event
    ):
        """Test batch with partial failure"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # First call succeeds, second fails
            mock_session.post.side_effect = [
                Mock(status_code=201),
                Mock(status_code=500),
            ]

            connector = QRadarConnector(qradar_config)
            events = [sample_security_event, sample_security_event]
            result = connector.send_events_batch(events)

            assert result is False


# SIEMIntegrationManager Tests
class TestSIEMIntegrationManager:
    """Tests for SIEMIntegrationManager"""

    def test_initialization(self):
        """Test manager initialization"""
        manager = SIEMIntegrationManager()

        assert manager.connectors == {}
        assert "splunk" in manager._connector_classes
        assert "elastic" in manager._connector_classes
        assert "sentinel" in manager._connector_classes
        assert "qradar" in manager._connector_classes

    def test_add_siem_splunk(self, splunk_config):
        """Test adding Splunk SIEM"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response

            manager = SIEMIntegrationManager()
            result = manager.add_siem(splunk_config)

            assert result is True
            assert "test-splunk" in manager.connectors

    def test_add_siem_connection_failure(self, splunk_config):
        """Test adding SIEM with connection failure"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 401
            mock_session.get.return_value = mock_response

            manager = SIEMIntegrationManager()
            result = manager.add_siem(splunk_config)

            assert result is False
            assert "test-splunk" not in manager.connectors

    def test_add_siem_unknown_type(self):
        """Test adding SIEM with unknown type"""
        config = SIEMConfig(
            name="unknown",
            type="unknown_type",
            url="https://unknown.com",
        )

        manager = SIEMIntegrationManager()
        result = manager.add_siem(config)

        assert result is False

    def test_send_to_all(
        self, splunk_config, elastic_config, sample_security_event
    ):
        """Test sending event to all SIEMs"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_session.post.return_value = mock_response

            manager = SIEMIntegrationManager()
            manager.add_siem(splunk_config)
            manager.add_siem(elastic_config)

            results = manager.send_to_all(sample_security_event)

            assert "test-splunk" in results
            assert "test-elastic" in results
            assert results["test-splunk"] is True
            assert results["test-elastic"] is True

    def test_send_batch_to_all(self, splunk_config, sample_security_event):
        """Test sending batch to all SIEMs"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_session.post.return_value = mock_response

            manager = SIEMIntegrationManager()
            manager.add_siem(splunk_config)

            events = [sample_security_event, sample_security_event]
            results = manager.send_batch_to_all(events)

            assert "test-splunk" in results
            assert results["test-splunk"] is True

    def test_get_status(self, splunk_config):
        """Test getting connection status of all SIEMs"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response

            manager = SIEMIntegrationManager()
            manager.add_siem(splunk_config)

            status = manager.get_status()

            assert "test-splunk" in status
            assert status["test-splunk"] is True


# Factory Function Tests
class TestFactoryFunction:
    """Tests for create_siem_connector factory function"""

    def test_create_splunk_connector(self, splunk_config):
        """Test creating Splunk connector via factory"""
        connector = create_siem_connector(splunk_config)

        assert connector is not None
        assert isinstance(connector, SplunkConnector)

    def test_create_elastic_connector(self, elastic_config):
        """Test creating Elastic connector via factory"""
        connector = create_siem_connector(elastic_config)

        assert connector is not None
        assert isinstance(connector, ElasticConnector)

    def test_create_sentinel_connector(self, sentinel_config):
        """Test creating Sentinel connector via factory"""
        connector = create_siem_connector(sentinel_config)

        assert connector is not None
        assert isinstance(connector, AzureSentinelConnector)

    def test_create_qradar_connector(self, qradar_config):
        """Test creating QRadar connector via factory"""
        connector = create_siem_connector(qradar_config)

        assert connector is not None
        assert isinstance(connector, QRadarConnector)

    def test_create_unknown_connector(self):
        """Test creating connector for unknown type"""
        config = SIEMConfig(
            name="unknown",
            type="unknown_type",
            url="https://unknown.com",
        )

        connector = create_siem_connector(config)

        assert connector is None


# BaseSIEMConnector Tests
class TestBaseSIEMConnector:
    """Tests for BaseSIEMConnector abstract class"""

    def test_base_connector_is_abstract(self):
        """Test that BaseSIEMConnector is abstract"""
        config = SIEMConfig(name="test", type="test", url="https://test.com")

        with pytest.raises(TypeError):
            BaseSIEMConnector(config)


# Integration Tests
class TestIntegration:
    """Integration tests for SIEM module"""

    def test_multiple_siem_workflow(
        self, splunk_config, elastic_config, sample_security_event
    ):
        """Test workflow with multiple SIEMs"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_session.post.return_value = mock_response

            # Initialize manager and add SIEMs
            manager = SIEMIntegrationManager()
            assert manager.add_siem(splunk_config) is True
            assert manager.add_siem(elastic_config) is True

            # Send event to all
            results = manager.send_to_all(sample_security_event)
            assert all(results.values())

            # Check status
            status = manager.get_status()
            assert all(status.values())

    def test_event_with_all_severities(self, splunk_config):
        """Test sending events with different severities"""
        with patch(
            "modules.siem_integration.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_session.post.return_value = mock_response

            manager = SIEMIntegrationManager()
            manager.add_siem(splunk_config)

            severities = ["critical", "high", "medium", "low", "info"]
            for severity in severities:
                event = SecurityEvent(
                    timestamp=datetime.now(),
                    severity=severity,
                    event_type="test",
                    source="test",
                    target="test",
                    description="Test event",
                )
                result = manager.send_to_all(event)
                assert result["test-splunk"] is True

    def test_event_serialization(self, sample_security_event):
        """Test that events can be serialized properly"""
        # Convert to dict-like structure (as would happen in JSON serialization)
        event_dict = {
            "timestamp": sample_security_event.timestamp.isoformat(),
            "severity": sample_security_event.severity,
            "event_type": sample_security_event.event_type,
            "source": sample_security_event.source,
            "target": sample_security_event.target,
            "description": sample_security_event.description,
            "cve_id": sample_security_event.cve_id,
            "cvss_score": sample_security_event.cvss_score,
            "raw_data": sample_security_event.raw_data,
        }

        # Should be JSON serializable
        json_str = json.dumps(event_dict)
        assert json_str is not None

        # Should be deserializable
        restored = json.loads(json_str)
        assert restored["severity"] == "high"
