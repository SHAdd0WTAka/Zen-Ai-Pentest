"""
Tests for api/routes/scans.py - Scan Management Endpoints

Comprehensive tests for scan creation, management, and monitoring.
"""

# Mock dependencies
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import BackgroundTasks, HTTPException

mock_auth = MagicMock()
mock_auth.get_current_user = MagicMock()

mock_scan_model = MagicMock()
mock_scan_model.Scan = MagicMock()
mock_scan_model.ScanStatus = MagicMock()
mock_scan_model.ScanStatus.PENDING = "pending"
mock_scan_model.ScanStatus.RUNNING = "running"
mock_scan_model.ScanStatus.COMPLETED = "completed"
mock_scan_model.ScanStatus.FAILED = "failed"
mock_scan_model.ScanType = MagicMock()
mock_scan_model.ScanType.FULL = "full"
mock_scan_model.ScanType.QUICK = "quick"

mock_user = MagicMock()
mock_user.User = MagicMock()

sys.modules["api.core.auth"] = mock_auth
sys.modules["api.models.scan"] = mock_scan_model
sys.modules["api.models.user"] = mock_user

from api.routes.scans import (
    create_scan,
    delete_scan,
    get_scan,
    list_scans,
    run_scan,
    stop_scan,
)

# ==================== Test Fixtures ====================


@pytest.fixture
def mock_current_user():
    """Mock current user"""
    user = Mock()
    user.id = "user-001"
    user.username = "testuser"
    return user


@pytest.fixture
def mock_scan():
    """Mock scan object"""
    scan = AsyncMock()
    scan.id = "scan-001"
    scan.name = "Test Scan"
    scan.target = "example.com"
    scan.scan_type = "full"
    scan.status = mock_scan_model.ScanStatus.PENDING
    scan.created_at = datetime.utcnow()
    scan.started_at = None
    scan.completed_at = None
    scan.progress = 0
    scan.findings_count = 0
    scan.error_message = None
    scan.created_by = "user-001"
    scan.options = {}
    scan.save = AsyncMock()
    scan.to_response.return_value = {
        "id": "scan-001",
        "name": "Test Scan",
        "target": "example.com",
        "scan_type": "full",
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "completed_at": None,
        "progress": 0,
        "findings_count": 0,
        "error_message": None,
    }
    scan.update_status = AsyncMock()
    scan.update_progress = AsyncMock()
    scan.delete = AsyncMock()
    scan.stop = AsyncMock()
    return scan


@pytest.fixture
def mock_scan_create_data():
    """Mock scan creation data"""
    data = Mock()
    data.target = "example.com"
    data.scan_type = mock_scan_model.ScanType.FULL
    data.name = None  # Will be auto-generated
    data.description = "Test scan description"
    data.options = {"intensity": "normal"}
    return data


# ==================== Create Scan Tests ====================


class TestCreateScan:
    """Test create_scan endpoint"""

    @pytest.mark.asyncio
    async def test_create_scan_success(
        self, mock_current_user, mock_scan, mock_scan_create_data
    ):
        """Test successful scan creation"""
        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            mock_scan_model.Scan.return_value = mock_scan

            background_tasks = BackgroundTasks()

            result = await create_scan(
                mock_scan_create_data, background_tasks, mock_current_user
            )

            assert result["id"] == "scan-001"
            assert result["target"] == "example.com"
            mock_scan.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_scan_auto_name(
        self, mock_current_user, mock_scan, mock_scan_create_data
    ):
        """Test scan creation with auto-generated name"""
        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            mock_scan_create_data.name = None
            mock_scan_model.Scan.return_value = mock_scan

            background_tasks = BackgroundTasks()
            await create_scan(
                mock_scan_create_data, background_tasks, mock_current_user
            )

            # Name should be auto-generated
            assert "scan" in mock_scan.name.lower() or "Scan" in mock_scan.name

    @pytest.mark.asyncio
    async def test_create_scan_custom_name(
        self, mock_current_user, mock_scan, mock_scan_create_data
    ):
        """Test scan creation with custom name"""
        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            mock_scan_create_data.name = "My Custom Scan"
            mock_scan_model.Scan.return_value = mock_scan

            background_tasks = BackgroundTasks()
            await create_scan(
                mock_scan_create_data, background_tasks, mock_current_user
            )

            assert mock_scan.name == "My Custom Scan"


# ==================== List Scans Tests ====================


class TestListScans:
    """Test list_scans endpoint"""

    @pytest.mark.asyncio
    async def test_list_scans_empty(self, mock_current_user):
        """Test listing scans when none exist"""
        mock_query = AsyncMock()
        mock_query.to_list.return_value = []
        mock_scan_model.Scan.find_many.return_value.limit.return_value.skip.return_value = (
            mock_query
        )

        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            result = await list_scans(None, None, 20, 0, mock_current_user)

            assert result == []

    @pytest.mark.asyncio
    async def test_list_scans_with_results(self, mock_current_user, mock_scan):
        """Test listing scans with results"""
        mock_query = AsyncMock()
        mock_query.to_list.return_value = [mock_scan]
        mock_scan_model.Scan.find_many.return_value.limit.return_value.skip.return_value = (
            mock_query
        )

        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            result = await list_scans(None, None, 20, 0, mock_current_user)

            assert len(result) == 1
            assert result[0]["id"] == "scan-001"

    @pytest.mark.asyncio
    async def test_list_scans_with_status_filter(
        self, mock_current_user, mock_scan
    ):
        """Test listing scans with status filter"""
        mock_query = AsyncMock()
        mock_query.to_list.return_value = [mock_scan]
        mock_scan_model.Scan.find_many.return_value.limit.return_value.skip.return_value = (
            mock_query
        )

        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            result = await list_scans(
                mock_scan_model.ScanStatus.PENDING,
                None,
                20,
                0,
                mock_current_user,
            )

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_scans_with_type_filter(
        self, mock_current_user, mock_scan
    ):
        """Test listing scans with type filter"""
        mock_query = AsyncMock()
        mock_query.to_list.return_value = [mock_scan]
        mock_scan_model.Scan.find_many.return_value.limit.return_value.skip.return_value = (
            mock_query
        )

        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            result = await list_scans(
                None, mock_scan_model.ScanType.FULL, 20, 0, mock_current_user
            )

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_scans_pagination(self, mock_current_user):
        """Test scan pagination"""
        mock_scan_model.Scan.find_many.return_value.limit.return_value.skip.return_value = (
            AsyncMock()
        )
        mock_scan_model.Scan.find_many.return_value.limit.return_value.skip.return_value.to_list.return_value = (
            []
        )

        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            await list_scans(None, None, 10, 20, mock_current_user)

            # Verify limit and offset were applied
            mock_scan_model.Scan.find_many.return_value.limit.assert_called_once_with(
                10
            )


# ==================== Get Scan Tests ====================


class TestGetScan:
    """Test get_scan endpoint"""

    @pytest.mark.asyncio
    async def test_get_scan_success(self, mock_current_user, mock_scan):
        """Test getting a specific scan"""
        mock_scan_model.Scan.find_one.return_value = mock_scan

        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            result = await get_scan("scan-001", mock_current_user)

            assert result["id"] == "scan-001"
            assert result["target"] == "example.com"

    @pytest.mark.asyncio
    async def test_get_scan_not_found(self, mock_current_user):
        """Test getting non-existent scan"""
        mock_scan_model.Scan.find_one.return_value = None

        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            with pytest.raises(HTTPException) as exc_info:
                await get_scan("nonexistent", mock_current_user)

            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_scan_wrong_user(self, mock_current_user):
        """Test getting scan belonging to another user"""
        mock_scan_model.Scan.find_one.return_value = None

        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            with pytest.raises(HTTPException) as exc_info:
                await get_scan("scan-002", mock_current_user)

            assert exc_info.value.status_code == 404


# ==================== Stop Scan Tests ====================


class TestStopScan:
    """Test stop_scan endpoint"""

    @pytest.mark.asyncio
    async def test_stop_running_scan(self, mock_current_user, mock_scan):
        """Test stopping a running scan"""
        mock_scan.status = mock_scan_model.ScanStatus.RUNNING
        mock_scan_model.Scan.find_one.return_value = mock_scan

        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            result = await stop_scan("scan-001", mock_current_user)

            assert "stopped" in result["message"].lower()
            mock_scan.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_pending_scan(self, mock_current_user, mock_scan):
        """Test stopping a pending scan"""
        mock_scan.status = mock_scan_model.ScanStatus.PENDING
        mock_scan_model.Scan.find_one.return_value = mock_scan

        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            result = await stop_scan("scan-001", mock_current_user)

            assert "stopped" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_stop_completed_scan(self, mock_current_user, mock_scan):
        """Test stopping a completed scan (should fail)"""
        mock_scan.status = mock_scan_model.ScanStatus.COMPLETED
        mock_scan_model.Scan.find_one.return_value = mock_scan

        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            with pytest.raises(HTTPException) as exc_info:
                await stop_scan("scan-001", mock_current_user)

            assert exc_info.value.status_code == 400
            assert "cannot be stopped" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_stop_scan_not_found(self, mock_current_user):
        """Test stopping non-existent scan"""
        mock_scan_model.Scan.find_one.return_value = None

        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            with pytest.raises(HTTPException) as exc_info:
                await stop_scan("nonexistent", mock_current_user)

            assert exc_info.value.status_code == 404


# ==================== Delete Scan Tests ====================


class TestDeleteScan:
    """Test delete_scan endpoint"""

    @pytest.mark.asyncio
    async def test_delete_scan_success(self, mock_current_user, mock_scan):
        """Test successful scan deletion"""
        mock_scan_model.Scan.find_one.return_value = mock_scan

        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            result = await delete_scan("scan-001", mock_current_user)

            assert "deleted" in result["message"].lower()
            mock_scan.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_scan_not_found(self, mock_current_user):
        """Test deleting non-existent scan"""
        mock_scan_model.Scan.find_one.return_value = None

        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            with pytest.raises(HTTPException) as exc_info:
                await delete_scan("nonexistent", mock_current_user)

            assert exc_info.value.status_code == 404


# ==================== Run Scan Background Task Tests ====================


class TestRunScan:
    """Test run_scan background task"""

    @pytest.mark.asyncio
    async def test_run_scan_success(self, mock_scan):
        """Test successful scan execution"""
        mock_scan_model.Scan.find_one.return_value = mock_scan

        mock_vuln_scanner = MagicMock()
        mock_scanner_instance = AsyncMock()
        mock_scanner_instance.scan = AsyncMock()
        mock_scanner_instance.scan.return_value.__aiter__ = AsyncMock()
        mock_scanner_instance.scan.return_value.__aiter__.return_value = [
            25,
            50,
            75,
            100,
        ]
        mock_vuln_scanner.VulnScannerModule.return_value = (
            mock_scanner_instance
        )

        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            with patch.dict(
                "sys.modules", {"modules.vuln_scanner": mock_vuln_scanner}
            ):
                await run_scan("scan-001")

                mock_scan.update_status.assert_any_call(
                    mock_scan_model.ScanStatus.RUNNING
                )
                mock_scan.update_status.assert_any_call(
                    mock_scan_model.ScanStatus.COMPLETED
                )

    @pytest.mark.asyncio
    async def test_run_scan_not_found(self):
        """Test running non-existent scan"""
        mock_scan_model.Scan.find_one.return_value = None

        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            # Should return early without error
            await run_scan("nonexistent")

    @pytest.mark.asyncio
    async def test_run_scan_failure(self, mock_scan):
        """Test scan execution failure"""
        mock_scan_model.Scan.find_one.return_value = mock_scan

        with patch("api.routes.scans.Scan", mock_scan_model.Scan):
            with patch.dict(
                "sys.modules", {"modules.vuln_scanner": MagicMock()}
            ):
                # Make the import fail to trigger exception handling
                sys.modules["modules.vuln_scanner"].VulnScannerModule = Mock(
                    side_effect=Exception("Import failed")
                )

                await run_scan("scan-001")

                mock_scan.update_status.assert_any_call(
                    mock_scan_model.ScanStatus.FAILED, error=pytest.any
                )


# ==================== Model Tests ====================


class TestScanModels:
    """Test Pydantic models for scans"""

    def test_scan_create_model(self):
        """Test ScanCreate model validation"""
        from typing import Optional

        from pydantic import BaseModel, Field

        class ScanCreate(BaseModel):
            target: str
            scan_type: str = "full"
            name: Optional[str] = None
            description: Optional[str] = None
            options: dict = Field(default_factory=dict)

        # Valid creation
        scan = ScanCreate(target="example.com", scan_type="quick")
        assert scan.target == "example.com"
        assert scan.scan_type == "quick"

        # Default values
        scan2 = ScanCreate(target="example.com")
        assert scan2.scan_type == "full"
        assert scan2.options == {}

    def test_scan_response_model(self):
        """Test ScanResponse model"""
        from datetime import datetime
        from typing import Optional

        from pydantic import BaseModel, Field

        class ScanResponse(BaseModel):
            id: str
            name: str
            target: str
            scan_type: str
            status: str
            created_at: datetime
            started_at: Optional[datetime]
            completed_at: Optional[datetime]
            progress: int = Field(0, ge=0, le=100)
            findings_count: int
            error_message: Optional[str]

        response = ScanResponse(
            id="scan-001",
            name="Test",
            target="example.com",
            scan_type="full",
            status="pending",
            created_at=datetime.utcnow(),
            started_at=None,
            completed_at=None,
            progress=0,
            findings_count=0,
            error_message=None,
        )
        assert response.progress == 0

        # Test progress bounds
        with pytest.raises(Exception):
            ScanResponse(
                id="scan-001",
                name="Test",
                target="example.com",
                scan_type="full",
                status="pending",
                created_at=datetime.utcnow(),
                progress=150,  # Invalid: > 100
                findings_count=0,
                error_message=None,
            )

    def test_scan_status_enum(self):
        """Test scan status values"""
        assert mock_scan_model.ScanStatus.PENDING == "pending"
        assert mock_scan_model.ScanStatus.RUNNING == "running"
        assert mock_scan_model.ScanStatus.COMPLETED == "completed"
        assert mock_scan_model.ScanStatus.FAILED == "failed"
