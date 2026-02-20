"""
Tests for Cloud Scanner Module
Q2 2026 - AWS/Azure/GCP Cloud Security Scanning
"""

import json
import pytest
import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import tempfile
import os

# Skip tests if scoutsuite_integration is not available
pytest.importorskip("scoutsuite_integration", allow_module_level=True)

from modules.cloud_scanner import (
    CloudScanner,
    CloudAccountManager,
    CloudAccount,
    ScanResult,
    ScheduledScan,
    ScanType,
    ScanSchedule,
    FindingDelta,
    CloudScannerAPI,
)
from scoutsuite_integration import CloudProvider, ScoutSuiteConfig, ScoutSuiteReport, ScoutSuiteFinding


# Fixtures
@pytest.fixture
def temp_accounts_file():
    """Create a temporary accounts file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"accounts": []}, f)
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def aws_account():
    """Create an AWS account fixture"""
    return CloudAccount(
        id="test-aws-123",
        name="Test AWS Account",
        provider=CloudProvider.AWS,
        credentials={
            "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "region": "us-east-1",
        },
        metadata={"environment": "test"},
    )


@pytest.fixture
def azure_account():
    """Create an Azure account fixture"""
    return CloudAccount(
        id="test-azure-456",
        name="Test Azure Subscription",
        provider=CloudProvider.AZURE,
        credentials={
            "tenant_id": "test-tenant-id",
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "subscription_id": "test-subscription-id",
        },
    )


@pytest.fixture
def gcp_account():
    """Create a GCP account fixture"""
    return CloudAccount(
        id="test-gcp-789",
        name="Test GCP Project",
        provider=CloudProvider.GCP,
        credentials={
            "service_account_key_path": "/path/to/key.json",
            "project_id": "test-project-id",
        },
    )


@pytest.fixture
def mock_scoutsuite_report():
    """Create a mock ScoutSuite report"""
    report = Mock(spec=ScoutSuiteReport)
    report.status = "completed"
    report.findings = [
        Mock(spec=ScoutSuiteFinding, id="finding-1", severity="high"),
        Mock(spec=ScoutSuiteFinding, id="finding-2", severity="medium"),
    ]
    report.to_dict.return_value = {
        "status": "completed",
        "findings_count": 2,
        "provider": "aws",
    }
    return report


# CloudAccountManager Tests
class TestCloudAccountManager:
    """Tests for CloudAccountManager class"""

    def test_initialization(self, temp_accounts_file):
        """Test CloudAccountManager initialization"""
        manager = CloudAccountManager(storage_path=temp_accounts_file)
        assert manager.accounts == {}

    def test_add_account_aws(self, temp_accounts_file, aws_account):
        """Test adding AWS account"""
        manager = CloudAccountManager(storage_path=temp_accounts_file)
        
        account = manager.add_account(
            name=aws_account.name,
            provider=aws_account.provider,
            credentials=aws_account.credentials,
            metadata=aws_account.metadata,
        )
        
        assert account.name == aws_account.name
        assert account.provider == CloudProvider.AWS
        assert account.id in manager.accounts
        assert account.enabled is True

    def test_add_account_azure(self, temp_accounts_file, azure_account):
        """Test adding Azure account"""
        manager = CloudAccountManager(storage_path=temp_accounts_file)
        
        account = manager.add_account(
            name=azure_account.name,
            provider=azure_account.provider,
            credentials=azure_account.credentials,
        )
        
        assert account.provider == CloudProvider.AZURE
        assert len(manager.accounts) == 1

    def test_add_account_gcp(self, temp_accounts_file, gcp_account):
        """Test adding GCP account"""
        manager = CloudAccountManager(storage_path=temp_accounts_file)
        
        account = manager.add_account(
            name=gcp_account.name,
            provider=gcp_account.provider,
            credentials=gcp_account.credentials,
        )
        
        assert account.provider == CloudProvider.GCP

    def test_get_account(self, temp_accounts_file, aws_account):
        """Test getting account by ID"""
        manager = CloudAccountManager(storage_path=temp_accounts_file)
        added = manager.add_account(
            name=aws_account.name,
            provider=aws_account.provider,
            credentials=aws_account.credentials,
        )
        
        retrieved = manager.get_account(added.id)
        assert retrieved is not None
        assert retrieved.id == added.id

    def test_get_account_not_found(self, temp_accounts_file):
        """Test getting non-existent account"""
        manager = CloudAccountManager(storage_path=temp_accounts_file)
        assert manager.get_account("non-existent") is None

    def test_get_accounts_by_provider(self, temp_accounts_file, aws_account, azure_account):
        """Test getting accounts by provider"""
        manager = CloudAccountManager(storage_path=temp_accounts_file)
        
        manager.add_account(
            name=aws_account.name,
            provider=aws_account.provider,
            credentials=aws_account.credentials,
        )
        manager.add_account(
            name=azure_account.name,
            provider=azure_account.provider,
            credentials=azure_account.credentials,
        )
        
        aws_accounts = manager.get_accounts_by_provider(CloudProvider.AWS)
        assert len(aws_accounts) == 1
        assert aws_accounts[0].provider == CloudProvider.AWS

    def test_update_account(self, temp_accounts_file, aws_account):
        """Test updating account"""
        manager = CloudAccountManager(storage_path=temp_accounts_file)
        added = manager.add_account(
            name=aws_account.name,
            provider=aws_account.provider,
            credentials=aws_account.credentials,
        )
        
        success = manager.update_account(
            added.id,
            name="Updated Name",
            enabled=False,
        )
        
        assert success is True
        updated = manager.get_account(added.id)
        assert updated.name == "Updated Name"
        assert updated.enabled is False

    def test_delete_account(self, temp_accounts_file, aws_account):
        """Test deleting account"""
        manager = CloudAccountManager(storage_path=temp_accounts_file)
        added = manager.add_account(
            name=aws_account.name,
            provider=aws_account.provider,
            credentials=aws_account.credentials,
        )
        
        success = manager.delete_account(added.id)
        assert success is True
        assert manager.get_account(added.id) is None

    def test_list_accounts(self, temp_accounts_file, aws_account, azure_account):
        """Test listing all accounts"""
        manager = CloudAccountManager(storage_path=temp_accounts_file)
        
        manager.add_account(
            name=aws_account.name,
            provider=aws_account.provider,
            credentials=aws_account.credentials,
        )
        manager.add_account(
            name=azure_account.name,
            provider=azure_account.provider,
            credentials=azure_account.credentials,
        )
        
        accounts = manager.list_accounts()
        assert len(accounts) == 2

    def test_persistence(self, temp_accounts_file, aws_account):
        """Test account persistence"""
        manager1 = CloudAccountManager(storage_path=temp_accounts_file)
        added = manager1.add_account(
            name=aws_account.name,
            provider=aws_account.provider,
            credentials=aws_account.credentials,
        )
        
        # Create new manager instance with same file
        manager2 = CloudAccountManager(storage_path=temp_accounts_file)
        retrieved = manager2.get_account(added.id)
        
        assert retrieved is not None
        assert retrieved.name == aws_account.name


# CloudScanner Tests
class TestCloudScanner:
    """Tests for CloudScanner class"""

    @pytest.fixture
    def scanner(self, temp_accounts_file):
        """Create a CloudScanner instance"""
        with patch("modules.cloud_scanner.ScoutSuiteIntegration") as mock_scout:
            mock_scout.return_value = Mock()
            scanner = CloudScanner({"accounts_file": temp_accounts_file})
            yield scanner

    def test_initialization(self, scanner):
        """Test CloudScanner initialization"""
        assert scanner.config is not None
        assert scanner.scheduled_scans == {}
        assert scanner.scan_results == {}
        assert scanner.scan_history == []

    def test_create_scan_config_full(self, scanner, aws_account):
        """Test creating full scan config"""
        config = scanner.create_scan_config(aws_account, ScanType.FULL)
        
        assert isinstance(config, ScoutSuiteConfig)
        assert config.provider == CloudProvider.AWS

    def test_create_scan_config_quick(self, scanner, aws_account):
        """Test creating quick scan config"""
        config = scanner.create_scan_config(aws_account, ScanType.QUICK)
        
        assert isinstance(config, ScoutSuiteConfig)
        assert len(config.services) > 0
        assert "iam" in config.services

    def test_create_scan_config_compliance(self, scanner, aws_account):
        """Test creating compliance scan config"""
        config = scanner.create_scan_config(aws_account, ScanType.COMPLIANCE)
        
        assert isinstance(config, ScoutSuiteConfig)
        assert "cloudtrail" in config.services

    def test_create_scan_config_custom(self, scanner, aws_account):
        """Test creating custom scan config"""
        custom_services = ["s3", "ec2"]
        config = scanner.create_scan_config(
            aws_account, ScanType.CUSTOM, custom_services=custom_services
        )
        
        assert config.services == custom_services

    @pytest.mark.asyncio
    async def test_scan_account_not_found(self, scanner):
        """Test scanning non-existent account"""
        with pytest.raises(ValueError, match="Konto nicht gefunden"):
            await scanner.scan_account("non-existent", ScanType.QUICK)

    @pytest.mark.asyncio
    async def test_scan_account_disabled(self, scanner, temp_accounts_file, aws_account):
        """Test scanning disabled account"""
        account = scanner.account_manager.add_account(
            name=aws_account.name,
            provider=aws_account.provider,
            credentials=aws_account.credentials,
        )
        scanner.account_manager.update_account(account.id, enabled=False)
        
        with pytest.raises(ValueError, match="Konto ist deaktiviert"):
            await scanner.scan_account(account.id, ScanType.QUICK)

    @pytest.mark.asyncio
    async def test_scan_account_success(self, scanner, aws_account, mock_scoutsuite_report):
        """Test successful account scan"""
        account = scanner.account_manager.add_account(
            name=aws_account.name,
            provider=aws_account.provider,
            credentials=aws_account.credentials,
        )
        
        # Mock the scoutsuite scan
        scanner.scoutsuite.scan = AsyncMock(return_value=mock_scoutsuite_report)
        scanner._setup_credentials = Mock()
        
        result = await scanner.scan_account(account.id, ScanType.QUICK)
        
        assert result.account_id == account.id
        assert result.status == "completed"
        assert result.report is not None
        assert result.scan_id in scanner.scan_results

    @pytest.mark.asyncio
    async def test_scan_account_error(self, scanner, aws_account):
        """Test scan with error"""
        account = scanner.account_manager.add_account(
            name=aws_account.name,
            provider=aws_account.provider,
            credentials=aws_account.credentials,
        )
        
        # Mock the scoutsuite scan to raise exception
        scanner.scoutsuite.scan = AsyncMock(side_effect=Exception("Scan failed"))
        scanner._setup_credentials = Mock()
        
        result = await scanner.scan_account(account.id, ScanType.QUICK)
        
        assert result.status == "error"
        assert result.error_message == "Scan failed"

    @pytest.mark.asyncio
    async def test_scan_multiple_accounts(self, scanner, aws_account, azure_account, mock_scoutsuite_report):
        """Test scanning multiple accounts"""
        aws = scanner.account_manager.add_account(
            name=aws_account.name,
            provider=aws_account.provider,
            credentials=aws_account.credentials,
        )
        azure = scanner.account_manager.add_account(
            name=azure_account.name,
            provider=azure_account.provider,
            credentials=azure_account.credentials,
        )
        
        scanner.scoutsuite.scan = AsyncMock(return_value=mock_scoutsuite_report)
        scanner._setup_credentials = Mock()
        
        results = await scanner.scan_multiple_accounts([aws.id, azure.id], ScanType.QUICK)
        
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_scan_all_accounts(self, scanner, aws_account, azure_account):
        """Test scanning all accounts"""
        scanner.account_manager.add_account(
            name=aws_account.name,
            provider=aws_account.provider,
            credentials=aws_account.credentials,
        )
        scanner.account_manager.add_account(
            name=azure_account.name,
            provider=azure_account.provider,
            credentials=azure_account.credentials,
        )
        
        scan_ids = scanner.scan_all_accounts(scan_type=ScanType.QUICK)
        
        assert len(scan_ids) == 2

    def test_calculate_delta(self, scanner, mock_scoutsuite_report):
        """Test calculating delta between reports"""
        # Create two reports with different findings
        report1 = Mock(spec=ScoutSuiteReport)
        report1.findings = [
            Mock(spec=ScoutSuiteFinding, id="finding-1"),
            Mock(spec=ScoutSuiteFinding, id="finding-2"),
        ]
        
        report2 = Mock(spec=ScoutSuiteReport)
        report2.findings = [
            Mock(spec=ScoutSuiteFinding, id="finding-2"),
            Mock(spec=ScoutSuiteFinding, id="finding-3"),
        ]
        
        delta = scanner.calculate_delta(report2, report1)
        
        assert len(delta.new_findings) == 1  # finding-3
        assert len(delta.resolved_findings) == 1  # finding-1
        assert len(delta.unchanged_findings) == 1  # finding-2

    def test_schedule_scan(self, scanner, aws_account):
        """Test scheduling a scan"""
        account = scanner.account_manager.add_account(
            name=aws_account.name,
            provider=aws_account.provider,
            credentials=aws_account.credentials,
        )
        
        scheduled = scanner.schedule_scan(
            account.id, ScanType.QUICK, ScanSchedule.DAILY
        )
        
        assert scheduled.account_id == account.id
        assert scheduled.scan_type == ScanType.QUICK
        assert scheduled.schedule == ScanSchedule.DAILY
        assert scheduled.next_run is not None

    def test_schedule_scan_invalid_account(self, scanner):
        """Test scheduling scan for invalid account"""
        with pytest.raises(ValueError, match="Konto nicht gefunden"):
            scanner.schedule_scan("invalid", ScanType.QUICK, ScanSchedule.DAILY)

    def test_get_scan_result(self, scanner):
        """Test getting scan result"""
        result = ScanResult(
            scan_id="test-scan-123",
            account_id="account-123",
            scan_type=ScanType.QUICK,
            start_time=datetime.now(),
            status="completed",
        )
        scanner.scan_results["test-scan-123"] = result
        
        retrieved = scanner.get_scan_result("test-scan-123")
        assert retrieved == result

    def test_get_scan_history(self, scanner):
        """Test getting scan history"""
        result1 = ScanResult(
            scan_id="scan-1",
            account_id="account-1",
            scan_type=ScanType.QUICK,
            start_time=datetime.now(),
            status="completed",
        )
        result2 = ScanResult(
            scan_id="scan-2",
            account_id="account-1",
            scan_type=ScanType.FULL,
            start_time=datetime.now(),
            status="completed",
        )
        scanner.scan_results["scan-1"] = result1
        scanner.scan_results["scan-2"] = result2
        
        history = scanner.get_scan_history(account_id="account-1")
        assert len(history) == 2

    def test_get_statistics(self, scanner):
        """Test getting statistics"""
        result = ScanResult(
            scan_id="scan-1",
            account_id="account-1",
            scan_type=ScanType.QUICK,
            start_time=datetime.now(),
            status="completed",
        )
        scanner.scan_results["scan-1"] = result
        
        stats = scanner.get_statistics()
        
        assert stats["total_scans"] == 1
        assert stats["successful_scans"] == 1
        assert stats["failed_scans"] == 0

    def test_add_scan_callback(self, scanner):
        """Test adding scan callback"""
        callback = Mock()
        scanner.add_scan_callback(callback)
        
        assert callback in scanner.scan_callbacks

    def test_cleanup_old_reports(self, scanner):
        """Test cleaning up old reports"""
        old_date = datetime(2020, 1, 1)
        result = ScanResult(
            scan_id="old-scan",
            account_id="account-1",
            scan_type=ScanType.QUICK,
            start_time=old_date,
            status="completed",
        )
        scanner.scan_results["old-scan"] = result
        
        scanner.cleanup_old_reports(days=30)
        
        assert "old-scan" not in scanner.scan_results


# CloudScannerAPI Tests
class TestCloudScannerAPI:
    """Tests for CloudScannerAPI class"""

    @pytest.fixture
    def api(self, temp_accounts_file):
        """Create a CloudScannerAPI instance"""
        with patch("modules.cloud_scanner.ScoutSuiteIntegration"):
            scanner = CloudScanner({"accounts_file": temp_accounts_file})
            yield CloudScannerAPI(scanner)

    @pytest.mark.asyncio
    async def test_handle_scan_request(self, api, aws_account):
        """Test handling scan request"""
        account = api.scanner.account_manager.add_account(
            name=aws_account.name,
            provider=aws_account.provider,
            credentials=aws_account.credentials,
        )
        
        with patch.object(api.scanner, 'scan_account', new_callable=AsyncMock) as mock_scan:
            mock_result = Mock()
            mock_result.scan_id = "test-scan-123"
            mock_result.status = "completed"
            mock_result.report = Mock(findings=[1, 2, 3])
            mock_scan.return_value = mock_result
            
            request = {"account_id": account.id, "scan_type": "quick"}
            response = await api.handle_scan_request(request)
            
            assert response["scan_id"] == "test-scan-123"
            assert response["status"] == "completed"

    @pytest.mark.asyncio
    async def test_handle_scan_request_missing_account(self, api):
        """Test handling scan request without account_id"""
        request = {"scan_type": "quick"}
        response = await api.handle_scan_request(request)
        
        assert "error" in response

    def test_handle_add_account(self, api, aws_account):
        """Test handling add account request"""
        request = {
            "name": aws_account.name,
            "provider": "aws",
            "credentials": aws_account.credentials,
            "metadata": aws_account.metadata,
        }
        
        response = api.handle_add_account(request)
        
        assert "account_id" in response
        assert response["status"] == "created"

    def test_handle_add_account_error(self, api):
        """Test handling add account with error"""
        request = {"name": "test"}  # Missing required fields
        response = api.handle_add_account(request)
        
        assert "error" in response

    def test_handle_get_results(self, api):
        """Test handling get results request"""
        result = ScanResult(
            scan_id="test-scan",
            account_id="account-1",
            scan_type=ScanType.QUICK,
            start_time=datetime.now(),
            status="completed",
        )
        api.scanner.scan_results["test-scan"] = result
        
        request = {"scan_id": "test-scan"}
        response = api.handle_get_results(request)
        
        assert response["scan_id"] == "test-scan"

    def test_handle_get_results_not_found(self, api):
        """Test handling get results for non-existent scan"""
        request = {"scan_id": "non-existent"}
        response = api.handle_get_results(request)
        
        assert "error" in response

    def test_handle_get_results_list(self, api):
        """Test handling get results list request"""
        request = {"limit": 10}
        response = api.handle_get_results(request)
        
        assert "results" in response
        assert "total" in response

    def test_handle_get_statistics(self, api):
        """Test handling get statistics request"""
        response = api.handle_get_statistics()
        
        assert "total_scans" in response


# Data Class Tests
class TestDataClasses:
    """Tests for data classes"""

    def test_cloud_account_to_dict(self, aws_account):
        """Test CloudAccount to_dict"""
        data = aws_account.to_dict()
        
        assert data["id"] == aws_account.id
        assert data["name"] == aws_account.name
        assert data["provider"] == "aws"

    def test_scan_result_to_dict(self):
        """Test ScanResult to_dict"""
        result = ScanResult(
            scan_id="test",
            account_id="account",
            scan_type=ScanType.QUICK,
            start_time=datetime.now(),
        )
        data = result.to_dict()
        
        assert data["scan_id"] == "test"
        assert data["scan_type"] == "quick"

    def test_scheduled_scan_to_dict(self):
        """Test ScheduledScan to_dict"""
        config = Mock(spec=ScoutSuiteConfig)
        scheduled = ScheduledScan(
            id="test-schedule",
            account_id="account",
            scan_type=ScanType.DAILY,
            schedule=ScanSchedule.DAILY,
            config=config,
        )
        data = scheduled.to_dict()
        
        assert data["id"] == "test-schedule"
        assert data["schedule"] == "daily"

    def test_finding_delta_to_dict(self):
        """Test FindingDelta to_dict"""
        delta = FindingDelta()
        data = delta.to_dict()
        
        assert "new_findings" in data
        assert "resolved_findings" in data
        assert "unchanged_findings_count" in data


# Enum Tests
class TestEnums:
    """Tests for enums"""

    def test_scan_type_values(self):
        """Test ScanType enum values"""
        assert ScanType.FULL.value == "full"
        assert ScanType.QUICK.value == "quick"
        assert ScanType.COMPLIANCE.value == "compliance"
        assert ScanType.CUSTOM.value == "custom"
        assert ScanType.DELTA.value == "delta"

    def test_scan_schedule_values(self):
        """Test ScanSchedule enum values"""
        assert ScanSchedule.ONCE.value == "once"
        assert ScanSchedule.HOURLY.value == "hourly"
        assert ScanSchedule.DAILY.value == "daily"
        assert ScanSchedule.WEEKLY.value == "weekly"
        assert ScanSchedule.MONTHLY.value == "monthly"
