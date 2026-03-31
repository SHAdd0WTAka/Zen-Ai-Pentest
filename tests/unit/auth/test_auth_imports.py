"""Test auth module imports"""

import pytest


class TestAuthImports:
    """Test auth modules can be imported"""

    def test_jwt_handler_import(self):
        from auth.jwt_handler import JWTHandler

        assert JWTHandler is not None

    def test_password_hasher_import(self):
        from auth.password_hasher import PasswordHasher

        assert PasswordHasher is not None

    def test_rbac_import(self):
        from auth.rbac import RBACManager

        assert RBACManager is not None

    def test_mfa_import(self):
        from auth.mfa import MFAManager

        assert MFAManager is not None

    def test_session_manager_import(self):
        from auth.session_manager import SessionManager

        assert SessionManager is not None


class TestDatabaseModels:
    """Test database models can be imported"""

    def test_user_model_import(self):
        from database.models import User

        assert User is not None

    def test_scan_model_import(self):
        from database.models import Scan

        assert Scan is not None

    def test_finding_model_import(self):
        from database.models import Finding

        assert Finding is not None

    def test_report_model_import(self):
        from database.models import Report

        assert Report is not None

    def test_crud_import(self):
        from database.crud import AsyncDatabaseSession

        assert AsyncDatabaseSession is not None
