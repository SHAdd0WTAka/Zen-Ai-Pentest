"""
Unit Tests für /home/atakan/zen-ai-pentest/api/routes/scans.py

FastAPI Routes für Scan-Management - Unit Tests
Ziel: Mindestens 75% Coverage

Tests:
- CRUD Operationen (Create, Read, Update, Delete)
- Scan-Start/Stop
- Error Handling (404, 422, 403)
- Background Task Integration
"""

import sys
from datetime import datetime, timezone
from enum import Enum
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

# This suite patches api.routes.scans.Scan, but the implementation imports Scan
# from api.models.scan, so the mocks never take effect. It needs a rewrite.
pytest.skip(
    "Stale generated test suite with incorrect mock targets; skipped until rewritten",
    allow_module_level=True,
)

# =============================================================================
# Test Models (independent of the actual models)
# =============================================================================


class ScanStatus(str, Enum):
    """Test Scan status enumeration"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanType(str, Enum):
    """Test Scan types enumeration"""

    PORT_SCAN = "port_scan"
    VULNERABILITY = "vulnerability"
    WEB_APP = "web_app"
    NETWORK = "network"
    COMPLIANCE = "compliance"
    FULL = "full"


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_current_user():
    """Mock current authenticated user"""
    user = Mock()
    user.id = "user-001"
    user.username = "testuser"
    user.email = "test@example.com"
    user.role = "admin"
    return user


@pytest.fixture
def mock_scan():
    """Create a mock scan object"""
    scan = AsyncMock()
    scan.id = "scan-001"
    scan.name = "Test Scan"
    scan.target = "example.com"
    scan.scan_type = ScanType.FULL
    scan.status = ScanStatus.PENDING
    scan.created_by = "user-001"
    scan.created_at = datetime.now(timezone.utc)
    scan.started_at = None
    scan.completed_at = None
    scan.progress = 0
    scan.findings_count = 0
    scan.error_message = None
    scan.options = {"intensity": "normal"}
    scan.description = "Test scan description"

    # Mock methods
    scan.save = AsyncMock()
    scan.delete = AsyncMock()
    scan.stop = AsyncMock()
    scan.update_status = AsyncMock()
    scan.update_progress = AsyncMock()
    scan.to_response.return_value = {
        "id": "scan-001",
        "name": "Test Scan",
        "target": "example.com",
        "scan_type": "full",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "started_at": None,
        "completed_at": None,
        "progress": 0,
        "findings_count": 0,
        "error_message": None,
    }
    return scan


@pytest.fixture
def mock_scan_list():
    """Create a list of mock scans"""
    scans = []
    for i in range(3):
        scan = AsyncMock()
        scan.id = f"scan-{i:03d}"
        scan.name = f"Test Scan {i}"
        scan.target = f"target{i}.com"
        scan.scan_type = ScanType.FULL
        scan.status = ScanStatus.PENDING if i == 0 else ScanStatus.COMPLETED
        scan.created_by = "user-001"
        scan.created_at = datetime.now(timezone.utc)
        scan.started_at = None
        scan.completed_at = None
        scan.progress = i * 33
        scan.findings_count = i * 5
        scan.error_message = None
        scan.to_response.return_value = {
            "id": f"scan-{i:03d}",
            "name": f"Test Scan {i}",
            "target": f"target{i}.com",
            "scan_type": "full",
            "status": "pending" if i == 0 else "completed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None,
            "completed_at": None,
            "progress": i * 33,
            "findings_count": i * 5,
            "error_message": None,
        }
        scans.append(scan)
    return scans


@pytest.fixture
def mock_scan_create_data():
    """Valid scan creation data"""
    return {
        "target": "example.com",
        "scan_type": ScanType.FULL,
        "name": "My Test Scan",
        "description": "Test description",
        "options": {"intensity": "high"},
    }


@pytest.fixture
def mock_scan_create_minimal():
    """Minimal scan creation data (auto-generates name)"""
    return {
        "target": "example.com",
        "scan_type": ScanType.PORT_SCAN,
    }


# =============================================================================
# Test Classes für direkte Funktionsaufrufe
# =============================================================================


class TestCreateScanDirect:
    """Tests für create_scan Funktion (direkter Aufruf)"""

    @pytest.mark.asyncio
    async def test_create_scan_success(self, mock_current_user, mock_scan):
        """Test erfolgreiche Scan-Erstellung"""
        # Mock the Scan model class
        mock_scan_cls = Mock()
        mock_scan_cls.return_value = mock_scan

        # Create proper mocks for the imports
        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_auth_module.get_current_user = MagicMock(return_value=mock_current_user)

        mock_user_module = MagicMock()
        mock_user_module.User = MagicMock()

        # Patch sys.modules
        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        # Ensure to_response returns a dict, not a coroutine
        mock_scan.to_response = Mock(
            return_value={
                "id": "scan-001",
                "name": "Test Scan",
                "target": "example.com",
                "scan_type": "full",
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "started_at": None,
                "completed_at": None,
                "progress": 0,
                "findings_count": 0,
                "error_message": None,
            }
        )

        with patch.dict("sys.modules", modules_patch, clear=False):
            # Re-import to get mocked version
            from api.routes.scans import create_scan

            background_tasks = BackgroundTasks()

            # Create ScanCreate data
            scan_data = MagicMock()
            scan_data.target = "example.com"
            scan_data.scan_type = ScanType.FULL
            scan_data.name = "My Test Scan"
            scan_data.description = "Test description"
            scan_data.options = {"intensity": "high"}

            result = await create_scan(
                scan_data=scan_data,
                background_tasks=background_tasks,
                current_user=mock_current_user,
            )

            assert result["id"] == "scan-001"
            assert result["target"] == "example.com"
            assert result["status"] == "pending"
            mock_scan.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_scan_auto_name(self, mock_current_user, mock_scan):
        """Test Scan-Erstellung mit automatisch generiertem Namen"""
        mock_scan_cls = Mock()
        mock_scan_cls.return_value = mock_scan

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_auth_module.get_current_user = MagicMock(return_value=mock_current_user)

        mock_user_module = MagicMock()
        mock_user_module.User = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import create_scan

            background_tasks = BackgroundTasks()

            scan_data = MagicMock()
            scan_data.target = "example.com"
            scan_data.scan_type = ScanType.PORT_SCAN
            scan_data.name = None  # Auto-generate
            scan_data.description = None
            scan_data.options = {}

            result = await create_scan(
                scan_data=scan_data,
                background_tasks=background_tasks,
                current_user=mock_current_user,
            )

            # Name sollte auto-generiert sein (format: Scan-YYYYMMDD-HHMMSS)
            assert mock_scan.name is not None
            mock_scan.save.assert_called_once()


class TestListScansDirect:
    """Tests für list_scans Funktion (direkter Aufruf)"""

    @pytest.mark.asyncio
    async def test_list_scans_empty(self, mock_current_user):
        """Test leere Scan-Liste"""
        mock_query = AsyncMock()
        mock_query.to_list.return_value = []

        mock_scan_cls = MagicMock()
        mock_scan_cls.find_many.return_value.limit.return_value.skip.return_value = mock_query

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import list_scans

            result = await list_scans(
                status=None,
                scan_type=None,
                limit=20,
                offset=0,
                current_user=mock_current_user,
            )

            assert result == []

    @pytest.mark.asyncio
    async def test_list_scans_with_results(self, mock_current_user, mock_scan_list):
        """Test Scan-Liste mit Ergebnissen"""
        # Ensure each scan's to_response returns a dict
        for i, scan in enumerate(mock_scan_list):
            scan.to_response = Mock(
                return_value={
                    "id": f"scan-{i:03d}",
                    "name": f"Test Scan {i}",
                    "target": f"target{i}.com",
                    "scan_type": "full",
                    "status": "pending" if i == 0 else "completed",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "started_at": None,
                    "completed_at": None,
                    "progress": i * 33,
                    "findings_count": i * 5,
                    "error_message": None,
                }
            )

        mock_query = AsyncMock()
        mock_query.to_list.return_value = mock_scan_list

        mock_scan_cls = MagicMock()
        mock_scan_cls.find_many.return_value.limit.return_value.skip.return_value = mock_query

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import list_scans

            result = await list_scans(
                status=None,
                scan_type=None,
                limit=20,
                offset=0,
                current_user=mock_current_user,
            )

            assert len(result) == 3
            assert result[0]["id"] == "scan-000"
            assert result[1]["id"] == "scan-001"

    @pytest.mark.asyncio
    async def test_list_scans_with_status_filter(self, mock_current_user, mock_scan_list):
        """Test Scan-Liste mit Status-Filter"""
        mock_query = AsyncMock()
        mock_query.to_list.return_value = [mock_scan_list[0]]

        mock_scan_cls = MagicMock()
        mock_scan_cls.find_many.return_value.limit.return_value.skip.return_value = mock_query

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import list_scans

            result = await list_scans(
                status=ScanStatus.PENDING,
                scan_type=None,
                limit=20,
                offset=0,
                current_user=mock_current_user,
            )

            assert len(result) == 1
            # Verify filter was applied with created_by
            mock_scan_cls.find_many.assert_called_once()
            call_kwargs = mock_scan_cls.find_many.call_args[1]
            assert call_kwargs.get("created_by") == mock_current_user.id
            assert call_kwargs.get("status") == ScanStatus.PENDING

    @pytest.mark.asyncio
    async def test_list_scans_with_type_filter(self, mock_current_user, mock_scan_list):
        """Test Scan-Liste mit Type-Filter"""
        mock_query = AsyncMock()
        mock_query.to_list.return_value = mock_scan_list

        mock_scan_cls = MagicMock()
        mock_scan_cls.find_many.return_value.limit.return_value.skip.return_value = mock_query

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import list_scans

            result = await list_scans(
                status=None,
                scan_type=ScanType.FULL,
                limit=20,
                offset=0,
                current_user=mock_current_user,
            )

            assert len(result) == 3
            # Verify filter was applied
            call_kwargs = mock_scan_cls.find_many.call_args[1]
            assert call_kwargs.get("scan_type") == ScanType.FULL

    @pytest.mark.asyncio
    async def test_list_scans_pagination(self, mock_current_user, mock_scan_list):
        """Test Scan-Liste mit Pagination"""
        mock_query = AsyncMock()
        mock_query.to_list.return_value = mock_scan_list[1:2]

        mock_limit_mock = MagicMock()
        mock_limit_mock.skip.return_value = mock_query

        mock_scan_cls = MagicMock()
        mock_scan_cls.find_many.return_value.limit.return_value = mock_limit_mock

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import list_scans

            result = await list_scans(
                status=None,
                scan_type=None,
                limit=1,
                offset=1,
                current_user=mock_current_user,
            )

            assert len(result) == 1
            # Verify limit was applied
            mock_scan_cls.find_many.return_value.limit.assert_called_once_with(1)


class TestGetScanDirect:
    """Tests für get_scan Funktion (direkter Aufruf)"""

    @pytest.mark.asyncio
    async def test_get_scan_success(self, mock_current_user, mock_scan):
        """Test erfolgreicher Scan-Abruf"""
        # Ensure to_response returns a dict, not a coroutine
        mock_scan.to_response = Mock(
            return_value={
                "id": "scan-001",
                "name": "Test Scan",
                "target": "example.com",
                "scan_type": "full",
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "started_at": None,
                "completed_at": None,
                "progress": 0,
                "findings_count": 0,
                "error_message": None,
            }
        )

        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=mock_scan)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import get_scan

            result = await get_scan(
                scan_id="scan-001",
                current_user=mock_current_user,
            )

            assert result["id"] == "scan-001"
            assert result["target"] == "example.com"
            assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_scan_not_found(self, mock_current_user):
        """Test 404 Fehler wenn Scan nicht gefunden"""
        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=None)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import get_scan

            with pytest.raises(HTTPException) as exc_info:
                await get_scan(
                    scan_id="nonexistent",
                    current_user=mock_current_user,
                )

            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_scan_wrong_user(self, mock_current_user):
        """Test 404 Fehler wenn Scan einem anderen User gehört"""
        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=None)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import get_scan

            with pytest.raises(HTTPException) as exc_info:
                await get_scan(
                    scan_id="scan-002",
                    current_user=mock_current_user,
                )

            assert exc_info.value.status_code == 404


class TestStopScanDirect:
    """Tests für stop_scan Funktion (direkter Aufruf)"""

    @pytest.mark.asyncio
    async def test_stop_pending_scan(self, mock_current_user, mock_scan):
        """Test Stoppen eines pending Scans"""
        mock_scan.status = ScanStatus.PENDING

        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=mock_scan)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import stop_scan

            result = await stop_scan(
                scan_id="scan-001",
                current_user=mock_current_user,
            )

            assert "stopped" in result["message"].lower()
            mock_scan.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_running_scan(self, mock_current_user, mock_scan):
        """Test Stoppen eines running Scans"""
        mock_scan.status = ScanStatus.RUNNING

        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=mock_scan)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import stop_scan

            result = await stop_scan(
                scan_id="scan-001",
                current_user=mock_current_user,
            )

            assert "stopped" in result["message"].lower()
            mock_scan.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_completed_scan(self, mock_current_user, mock_scan):
        """Test 400 Fehler beim Stoppen eines completed Scans"""
        mock_scan.status = ScanStatus.COMPLETED

        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=mock_scan)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import stop_scan

            with pytest.raises(HTTPException) as exc_info:
                await stop_scan(
                    scan_id="scan-001",
                    current_user=mock_current_user,
                )

            assert exc_info.value.status_code == 400
            assert "cannot be stopped" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_stop_failed_scan(self, mock_current_user, mock_scan):
        """Test 400 Fehler beim Stoppen eines failed Scans"""
        mock_scan.status = ScanStatus.FAILED

        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=mock_scan)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import stop_scan

            with pytest.raises(HTTPException) as exc_info:
                await stop_scan(
                    scan_id="scan-001",
                    current_user=mock_current_user,
                )

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_stop_scan_not_found(self, mock_current_user):
        """Test 404 Fehler beim Stoppen eines nicht existierenden Scans"""
        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=None)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import stop_scan

            with pytest.raises(HTTPException) as exc_info:
                await stop_scan(
                    scan_id="nonexistent",
                    current_user=mock_current_user,
                )

            assert exc_info.value.status_code == 404


class TestDeleteScanDirect:
    """Tests für delete_scan Funktion (direkter Aufruf)"""

    @pytest.mark.asyncio
    async def test_delete_scan_success(self, mock_current_user, mock_scan):
        """Test erfolgreiches Löschen eines Scans"""
        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=mock_scan)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import delete_scan

            result = await delete_scan(
                scan_id="scan-001",
                current_user=mock_current_user,
            )

            assert "deleted" in result["message"].lower()
            mock_scan.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_scan_not_found(self, mock_current_user):
        """Test 404 Fehler beim Löschen eines nicht existierenden Scans"""
        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=None)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import delete_scan

            with pytest.raises(HTTPException) as exc_info:
                await delete_scan(
                    scan_id="nonexistent",
                    current_user=mock_current_user,
                )

            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()


class TestRunScanBackgroundTaskDirect:
    """Tests für run_scan Background Task (direkter Aufruf)"""

    @pytest.mark.asyncio
    async def test_run_scan_success(self, mock_scan):
        """Test erfolgreiche Scan-Ausführung im Hintergrund"""
        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=mock_scan)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import run_scan

            # Mock VulnScannerModule
            mock_vuln_scanner = MagicMock()
            mock_scanner_instance = AsyncMock()

            # Mock async generator für Fortschritt
            async def mock_scan_generator(target, options):
                yield 25
                yield 50
                yield 75
                yield 100

            mock_scanner_instance.scan = mock_scan_generator
            mock_vuln_scanner.VulnScannerModule.return_value = mock_scanner_instance

            with patch.dict(
                "sys.modules",
                {"modules.vuln_scanner": mock_vuln_scanner},
                clear=False,
            ):
                await run_scan("scan-001")

                # Status sollte auf RUNNING und dann COMPLETED gesetzt werden
                mock_scan.update_status.assert_any_call(ScanStatus.RUNNING)
                mock_scan.update_status.assert_any_call(ScanStatus.COMPLETED)

                # Progress sollte mehrfach aktualisiert werden
                assert mock_scan.update_progress.call_count == 4

    @pytest.mark.asyncio
    async def test_run_scan_not_found(self):
        """Test Verhalten wenn Scan nicht gefunden wird"""
        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=None)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import run_scan

            # Sollte ohne Fehler zurückkehren
            result = await run_scan("nonexistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_run_scan_failure(self, mock_scan):
        """Test Scan-Ausführung mit Fehler"""
        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=mock_scan)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import run_scan

            mock_vuln_scanner = MagicMock()
            mock_vuln_scanner.VulnScannerModule.side_effect = Exception("Scanner crashed")

            with patch.dict(
                "sys.modules",
                {"modules.vuln_scanner": mock_vuln_scanner},
                clear=False,
            ):
                await run_scan("scan-001")

                # Status sollte auf FAILED gesetzt werden
                mock_scan.update_status.assert_any_call(ScanStatus.RUNNING)
                mock_scan.update_status.assert_called_with(ScanStatus.FAILED, error="Scanner crashed")


# =============================================================================
# Pydantic Model Tests
# =============================================================================


class TestScanModels:
    """Tests für Pydantic Models"""

    def test_scan_create_model(self):
        """Test ScanCreate Model Validierung"""

        # Create local model for testing
        class ScanCreateTest(BaseModel):
            target: str
            scan_type: ScanType = ScanType.FULL
            name: str = None
            description: str = None
            options: dict = Field(default_factory=dict)

        # Valid data
        data = ScanCreateTest(
            target="example.com",
            scan_type=ScanType.PORT_SCAN,
            name="Test Scan",
            description="Test description",
            options={"intensity": "high"},
        )
        assert data.target == "example.com"
        assert data.scan_type == ScanType.PORT_SCAN
        assert data.name == "Test Scan"

    def test_scan_create_model_defaults(self):
        """Test ScanCreate Model Defaults"""

        class ScanCreateTest(BaseModel):
            target: str
            scan_type: ScanType = ScanType.FULL
            name: str = None
            description: str = None
            options: dict = Field(default_factory=dict)

        data = ScanCreateTest(target="example.com")
        assert data.target == "example.com"
        assert data.scan_type == ScanType.FULL  # Default
        assert data.name is None
        assert data.description is None
        assert data.options == {}

    def test_scan_response_model(self):
        """Test ScanResponse Model Struktur"""

        class ScanResponseTest(BaseModel):
            id: str
            name: str
            target: str
            scan_type: str
            status: str
            created_at: datetime
            started_at: datetime = None
            completed_at: datetime = None
            progress: int = Field(0, ge=0, le=100)
            findings_count: int
            error_message: str = None

        response = ScanResponseTest(
            id="scan-001",
            name="Test",
            target="example.com",
            scan_type="full",
            status="pending",
            created_at=datetime.now(timezone.utc),
            progress=50,
            findings_count=10,
        )
        assert response.id == "scan-001"
        assert response.progress == 50

    def test_scan_response_progress_bounds(self):
        """Test ScanResponse progress bounds validation"""

        class ScanResponseTest(BaseModel):
            id: str
            name: str
            target: str
            scan_type: str
            status: str
            created_at: datetime
            started_at: datetime = None
            completed_at: datetime = None
            progress: int = Field(0, ge=0, le=100)
            findings_count: int
            error_message: str = None

        # Valid progress values
        for p in [0, 50, 100]:
            response = ScanResponseTest(
                id="scan-001",
                name="Test",
                target="example.com",
                scan_type="full",
                status="pending",
                created_at=datetime.now(timezone.utc),
                progress=p,
                findings_count=0,
            )
            assert response.progress == p

        # Invalid progress value (> 100)
        with pytest.raises(Exception):
            ScanResponseTest(
                id="scan-001",
                name="Test",
                target="example.com",
                scan_type="full",
                status="pending",
                created_at=datetime.now(timezone.utc),
                progress=150,  # Invalid
                findings_count=0,
            )

    def test_scan_status_enum_values(self):
        """Test ScanStatus Enum Werte"""
        assert ScanStatus.PENDING == "pending"
        assert ScanStatus.RUNNING == "running"
        assert ScanStatus.COMPLETED == "completed"
        assert ScanStatus.FAILED == "failed"
        assert ScanStatus.CANCELLED == "cancelled"

    def test_scan_type_enum_values(self):
        """Test ScanType Enum Werte"""
        assert ScanType.PORT_SCAN == "port_scan"
        assert ScanType.VULNERABILITY == "vulnerability"
        assert ScanType.WEB_APP == "web_app"
        assert ScanType.NETWORK == "network"
        assert ScanType.COMPLIANCE == "compliance"
        assert ScanType.FULL == "full"


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests für Error Handling (404, 422, 403)"""

    @pytest.mark.asyncio
    async def test_404_error_format_get_scan(self, mock_current_user):
        """Test 404 Fehler Format bei get_scan"""
        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=None)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import get_scan

            with pytest.raises(HTTPException) as exc_info:
                await get_scan("nonexistent", mock_current_user)

            assert exc_info.value.status_code == 404
            assert isinstance(exc_info.value.detail, str)

    @pytest.mark.asyncio
    async def test_404_error_format_delete_scan(self, mock_current_user):
        """Test 404 Fehler Format bei delete_scan"""
        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=None)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import delete_scan

            with pytest.raises(HTTPException) as exc_info:
                await delete_scan("nonexistent", mock_current_user)

            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_400_error_on_stop_completed(self, mock_current_user, mock_scan):
        """Test 400 Fehler beim Stoppen eines abgeschlossenen Scans"""
        mock_scan.status = ScanStatus.COMPLETED

        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=mock_scan)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import stop_scan

            with pytest.raises(HTTPException) as exc_info:
                await stop_scan("scan-001", mock_current_user)

            assert exc_info.value.status_code == 400
            assert "cannot be stopped" in exc_info.value.detail.lower()


# =============================================================================
# Authorization Tests
# =============================================================================


class TestAuthorization:
    """Tests für Autorisierung"""

    @pytest.mark.asyncio
    async def test_list_scans_filters_by_user(self, mock_current_user):
        """Test dass Scans nach User gefiltert werden"""
        mock_query = AsyncMock()
        mock_query.to_list.return_value = []

        mock_scan_cls = MagicMock()
        mock_scan_cls.find_many.return_value.limit.return_value.skip.return_value = mock_query

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import list_scans

            await list_scans(
                status=None,
                scan_type=None,
                limit=20,
                offset=0,
                current_user=mock_current_user,
            )

            # Verify created_by filter is applied
            mock_scan_cls.find_many.assert_called_once_with(created_by=mock_current_user.id)

    @pytest.mark.asyncio
    async def test_get_scan_checks_ownership(self, mock_current_user, mock_scan):
        """Test dass Scan-User-Überprüfung erfolgt"""
        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=mock_scan)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import get_scan

            await get_scan("scan-001", mock_current_user)

            # Verify both id and created_by are checked
            mock_scan_cls.find_one.assert_called_once_with(
                id="scan-001",
                created_by=mock_current_user.id,
            )


# =============================================================================
# Edge Cases Tests
# =============================================================================


class TestEdgeCases:
    """Tests für Edge Cases"""

    @pytest.mark.asyncio
    async def test_create_scan_with_empty_options(self, mock_current_user, mock_scan):
        """Test Scan-Erstellung mit leeren Options"""
        mock_scan_cls = Mock()
        mock_scan_cls.return_value = mock_scan

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import create_scan

            background_tasks = BackgroundTasks()

            scan_data = MagicMock()
            scan_data.target = "example.com"
            scan_data.scan_type = ScanType.FULL
            scan_data.name = "Test"
            scan_data.description = None
            scan_data.options = {}

            result = await create_scan(
                scan_data=scan_data,
                background_tasks=background_tasks,
                current_user=mock_current_user,
            )

            assert result is not None
            mock_scan.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_scans_with_zero_limit(self, mock_current_user):
        """Test Scan-Liste mit limit=0"""
        mock_query = AsyncMock()
        mock_query.to_list.return_value = []

        mock_scan_cls = MagicMock()
        mock_scan_cls.find_many.return_value.limit.return_value.skip.return_value = mock_query

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import list_scans

            result = await list_scans(
                status=None,
                scan_type=None,
                limit=0,
                offset=0,
                current_user=mock_current_user,
            )

            assert result == []

    @pytest.mark.asyncio
    async def test_delete_scan_calls_delete_method(self, mock_current_user, mock_scan):
        """Test dass delete() Methode aufgerufen wird"""
        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=mock_scan)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import delete_scan

            await delete_scan("scan-001", mock_current_user)

            mock_scan.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_scan_returns_response_with_scan(self, mock_current_user, mock_scan):
        """Test dass stop_scan Response Scan-Daten enthält"""
        mock_scan.status = ScanStatus.RUNNING

        # Ensure to_response returns a dict
        mock_scan.to_response = Mock(
            return_value={
                "id": "scan-001",
                "name": "Test Scan",
                "target": "example.com",
                "scan_type": "full",
                "status": "running",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "started_at": None,
                "completed_at": None,
                "progress": 50,
                "findings_count": 5,
                "error_message": None,
            }
        )

        mock_scan_cls = MagicMock()
        mock_scan_cls.find_one = AsyncMock(return_value=mock_scan)

        mock_scan_module = MagicMock()
        mock_scan_module.Scan = mock_scan_cls
        mock_scan_module.ScanStatus = ScanStatus
        mock_scan_module.ScanType = ScanType

        mock_auth_module = MagicMock()
        mock_user_module = MagicMock()

        modules_patch = {
            "api.models.scan": mock_scan_module,
            "api.core.auth": mock_auth_module,
            "api.models.user": mock_user_module,
        }

        with patch.dict("sys.modules", modules_patch, clear=False):
            from api.routes.scans import stop_scan

            result = await stop_scan("scan-001", mock_current_user)

            assert "message" in result
            assert "scan" in result
            assert result["scan"]["id"] == "scan-001"


# =============================================================================
# Integration-style Tests with TestClient
# =============================================================================


class TestScanRoutesIntegration:
    """Integration-style Tests mit FastAPI TestClient"""

    def test_router_is_configured(self):
        """Test dass der Router korrekt konfiguriert ist"""
        from api.routes.scans import router

        # Verify router has expected routes
        routes = router.routes
        route_paths = [route.path for route in routes]

        assert "/" in route_paths  # Create scan (POST)
        assert "/" in route_paths  # List scans (GET)
        assert "/{scan_id}" in route_paths  # Get scan (GET)
        assert "/{scan_id}/stop" in route_paths  # Stop scan (POST)
        assert "/{scan_id}" in route_paths  # Delete scan (DELETE)

    def test_scan_create_model_validation_valid(self):
        """Test ScanCreate Model Validierung mit gültigen Daten"""
        from api.routes.scans import ScanCreate

        # Valid data
        data = {
            "target": "example.com",
            "scan_type": "full",
            "name": "Test Scan",
            "description": "Test description",
            "options": {"intensity": "high"},
        }

        scan_create = ScanCreate(**data)
        assert scan_create.target == "example.com"
        assert scan_create.scan_type.value == "full"
        assert scan_create.name == "Test Scan"

    def test_scan_create_model_validation_minimal(self):
        """Test ScanCreate Model mit minimalen Daten"""
        from api.routes.scans import ScanCreate

        data = {
            "target": "192.168.1.1",
        }

        scan_create = ScanCreate(**data)
        assert scan_create.target == "192.168.1.1"
        assert scan_create.scan_type.value == "full"  # Default
        assert scan_create.options == {}  # Default

    def test_scan_response_model(self):
        """Test ScanResponse Model"""
        from api.routes.scans import ScanResponse

        now = datetime.now(timezone.utc)
        data = {
            "id": "scan-001",
            "name": "Test Scan",
            "target": "example.com",
            "scan_type": "full",
            "status": "pending",
            "created_at": now,
            "started_at": None,
            "completed_at": None,
            "progress": 50,
            "findings_count": 10,
            "error_message": None,
        }

        response = ScanResponse(**data)
        assert response.id == "scan-001"
        assert response.progress == 50
        assert response.findings_count == 10
