"""
Integration Tests for Database Module
"""

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


class TestDatabaseConnection:
    """Test Database Connection"""

    def test_database_manager_creation(self):
        """Test database manager creation"""
        from database.models import SessionLocal

        # Just test that we can create a session
        db = SessionLocal()
        assert db is not None
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
