"""Test database imports"""

import pytest


class TestDatabaseModels:
    """Test database models"""

    def test_user_model(self):
        from database.models import User

        assert User is not None

    def test_scan_model(self):
        from database.models import Scan

        assert Scan is not None

    def test_finding_model(self):
        from database.models import Finding

        assert Finding is not None

    def test_report_model(self):
        from database.models import Report

        assert Report is not None

    def test_target_model(self):
        from database.models import Asset

        assert Asset is not None


class TestDatabaseAuth:
    """Test database auth models"""

    def test_auth_user_model(self):
        from database.auth_models import User as AuthUser

        assert AuthUser is not None


class TestDatabaseCRUD:
    """Test database CRUD"""

    def test_crud_import(self):
        from database.crud import AsyncDatabaseSession

        assert AsyncDatabaseSession is not None
