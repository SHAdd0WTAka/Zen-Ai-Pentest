"""
Tests für CRUD Operations
"""

import pytest
import sys
import os

from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, "C:\\Users\\Ataka\\source\\repos\\SHAdd0WTAka\\Zen-Ai-Pentest")

os.environ["DATABASE_URL"] = "sqlite:///./test_crud.db"

from database import crud


class TestCRUDBase:
    """Test base CRUD operations"""
    
    @patch('database.crud.SessionLocal')
    def test_get_user(self, mock_session_class):
        mock_db = MagicMock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = crud.get_user(mock_db, user_id=1)
        
        assert result.username == "testuser"
    
    @patch('database.crud.SessionLocal')
    def test_get_user_by_username(self, mock_session_class):
        mock_db = MagicMock()
        mock_user = Mock()
        mock_user.username = "testuser"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = crud.get_user_by_username(mock_db, username="testuser")
        
        assert result is not None
    
    @patch('database.crud.SessionLocal')
    def test_get_users(self, mock_session_class):
        mock_db = MagicMock()
        mock_users = [Mock(), Mock(), Mock()]
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_users
        
        result = crud.get_users(mock_db, skip=0, limit=10)
        
        assert len(result) == 3
    
    @patch('database.crud.SessionLocal')
    def test_create_user(self, mock_session_class):
        mock_db = MagicMock()
        user_data = Mock()
        user_data.username = "newuser"
        user_data.email = "new@example.com"
        user_data.password = "password123"
        
        _ = crud.create_user(mock_db, user=user_data)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


class TestScanCRUD:
    """Test Scan CRUD operations"""
    
    @patch('database.crud.SessionLocal')
    def test_get_scan(self, mock_session_class):
        mock_db = MagicMock()
        mock_scan = Mock()
        mock_scan.id = 1
        mock_scan.name = "Test Scan"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_scan
        
        result = crud.get_scan(mock_db, scan_id=1)
        
        assert result.name == "Test Scan"
    
    @patch('database.crud.SessionLocal')
    def test_get_scans(self, mock_session_class):
        mock_db = MagicMock()
        mock_scans = [Mock(), Mock()]
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_scans
        
        result = crud.get_scans(mock_db, skip=0, limit=10)
        
        assert len(result) == 2
    
    @patch('database.crud.SessionLocal')
    def test_create_scan(self, mock_session_class):
        mock_db = MagicMock()
        scan_data = Mock()
        scan_data.name = "New Scan"
        scan_data.target = "example.com"
        scan_data.scan_type = "web"
        
        _ = crud.create_scan(mock_db, scan=scan_data)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


class TestFindingCRUD:
    """Test Finding CRUD operations"""
    
    @patch('database.crud.SessionLocal')
    def test_get_finding(self, mock_session_class):
        mock_db = MagicMock()
        mock_finding = Mock()
        mock_finding.id = 1
        mock_finding.title = "SQL Injection"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_finding
        
        result = crud.get_finding(mock_db, finding_id=1)
        
        assert result.title == "SQL Injection"
    
    @patch('database.crud.SessionLocal')
    def test_get_findings_by_scan(self, mock_session_class):
        mock_db = MagicMock()
        mock_findings = [Mock(), Mock(), Mock()]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_findings
        
        result = crud.get_findings_by_scan(mock_db, scan_id=1)
        
        assert len(result) == 3


class TestReportCRUD:
    """Test Report CRUD operations"""
    
    @patch('database.crud.SessionLocal')
    def test_get_report(self, mock_session_class):
        mock_db = MagicMock()
        mock_report = Mock()
        mock_report.id = 1
        mock_report.format = "pdf"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_report
        
        result = crud.get_report(mock_db, report_id=1)
        
        assert result.format == "pdf"
    
    @patch('database.crud.SessionLocal')
    def test_get_reports_by_scan(self, mock_session_class):
        mock_db = MagicMock()
        mock_reports = [Mock()]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_reports
        
        result = crud.get_reports_by_scan(mock_db, scan_id=1)
        
        assert len(result) == 1


class TestAuditLogCRUD:
    """Test Audit Log CRUD operations"""
    
    @patch('database.crud.SessionLocal')
    def test_create_audit_log(self, mock_session_class):
        mock_db = MagicMock()
        
        _ = crud.create_audit_log(
            mock_db,
            user_id=1,
            action="login",
            resource="auth",
            details={"ip": "192.168.1.1"}
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @patch('database.crud.SessionLocal')
    def test_get_audit_logs(self, mock_session_class):
        mock_db = MagicMock()
        mock_logs = [Mock(), Mock(), Mock(), Mock()]
        mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_logs
        
        result = crud.get_audit_logs(mock_db, skip=0, limit=10)
        
        assert len(result) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
