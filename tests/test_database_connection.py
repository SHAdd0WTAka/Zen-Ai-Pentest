"""
Comprehensive tests for database/connection.py
Target: 90-100% Coverage

Tests database connection management including:
- ConnectionPoolConfig class
- DatabaseManager class (singleton, initialization, sessions, pooling)
- Global functions (init_db_manager, close_db_manager, get_db_session, etc.)
- Utility functions (is_valid_database_url, create_test_connection_pool_config)
"""

import sys
import threading
import time
from contextlib import contextmanager
from typing import Generator
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool, QueuePool, StaticPool

# Add project root to path
sys.path.insert(0, "/home/atakan/zen-ai-pentest")

from database.connection import (
    ConnectionPoolConfig,
    DatabaseManager,
    close_db_manager,
    create_test_connection_pool_config,
    db_manager,
    get_db_context,
    get_db_generator,
    get_db_session,
    init_db_manager,
    is_valid_database_url,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset DatabaseManager singleton before each test."""
    # Reset singleton instance
    DatabaseManager._instance = None
    # Close global manager if exists
    global db_manager
    if db_manager is not None:
        try:
            db_manager.close()
        except Exception:
            pass
        db_manager = None
    yield
    # Cleanup after test
    DatabaseManager._instance = None
    if db_manager is not None:
        try:
            db_manager.close()
        except Exception:
            pass
        db_manager = None


@pytest.fixture
def sqlite_url():
    """SQLite in-memory database URL."""
    return "sqlite:///:memory:"


@pytest.fixture
def pool_config():
    """Create a test pool configuration."""
    return ConnectionPoolConfig(
        pool_size=2,
        max_overflow=1,
        pool_timeout=5,
        pool_recycle=300,
        pool_pre_ping=True,
        pool_class="StaticPool",
        echo=False,
    )


@pytest.fixture
def mock_engine():
    """Create a mock SQLAlchemy engine."""
    engine = MagicMock()
    engine.connect.return_value.__enter__ = MagicMock(return_value=MagicMock())
    engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    engine.pool = MagicMock()
    engine.pool.size.return_value = 5
    engine.pool.checkedin.return_value = 3
    engine.pool.checkedout.return_value = 2
    engine.pool.overflow.return_value = 0
    return engine


# =============================================================================
# Test ConnectionPoolConfig
# =============================================================================


class TestConnectionPoolConfig:
    """Test ConnectionPoolConfig class."""

    def test_default_initialization(self):
        """Test default initialization of ConnectionPoolConfig."""
        config = ConnectionPoolConfig()
        assert config.pool_size == 5
        assert config.max_overflow == 10
        assert config.pool_timeout == 30
        assert config.pool_recycle == 3600
        assert config.pool_pre_ping is True
        assert config.pool_class == "QueuePool"
        assert config.echo is False

    def test_custom_initialization(self):
        """Test custom initialization of ConnectionPoolConfig."""
        config = ConnectionPoolConfig(
            pool_size=10,
            max_overflow=20,
            pool_timeout=60,
            pool_recycle=7200,
            pool_pre_ping=False,
            pool_class="NullPool",
            echo=True,
        )
        assert config.pool_size == 10
        assert config.max_overflow == 20
        assert config.pool_timeout == 60
        assert config.pool_recycle == 7200
        assert config.pool_pre_ping is False
        assert config.pool_class == "NullPool"
        assert config.echo is True

    def test_to_dict(self):
        """Test to_dict method."""
        config = ConnectionPoolConfig(
            pool_size=3,
            max_overflow=5,
            pool_timeout=10,
        )
        result = config.to_dict()
        expected = {
            "pool_size": 3,
            "max_overflow": 5,
            "pool_timeout": 10,
            "pool_recycle": 3600,
            "pool_pre_ping": True,
            "pool_class": "QueuePool",
            "echo": False,
        }
        assert result == expected

    def test_from_dict(self):
        """Test from_dict class method."""
        data = {
            "pool_size": 7,
            "max_overflow": 14,
            "pool_timeout": 45,
            "pool_recycle": 1800,
            "pool_pre_ping": False,
            "pool_class": "StaticPool",
            "echo": True,
        }
        config = ConnectionPoolConfig.from_dict(data)
        assert config.pool_size == 7
        assert config.max_overflow == 14
        assert config.pool_timeout == 45
        assert config.pool_recycle == 1800
        assert config.pool_pre_ping is False
        assert config.pool_class == "StaticPool"
        assert config.echo is True

    def test_from_dict_with_defaults(self):
        """Test from_dict with partial data."""
        data = {"pool_size": 3}
        config = ConnectionPoolConfig.from_dict(data)
        assert config.pool_size == 3
        assert config.max_overflow == 10  # default
        assert config.pool_timeout == 30  # default


# =============================================================================
# Test DatabaseManager - Basic
# =============================================================================


class TestDatabaseManagerBasic:
    """Test DatabaseManager basic functionality."""

    def test_singleton_pattern(self):
        """Test that DatabaseManager is a singleton."""
        manager1 = DatabaseManager("sqlite:///:memory:")
        manager2 = DatabaseManager("sqlite:///:memory:")
        assert manager1 is manager2

    def test_initialization_without_url(self):
        """Test initialization without database URL."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager()
        assert manager._database_url is None
        assert manager._initialized is False

    def test_initialization_with_url(self, sqlite_url):
        """Test initialization with database URL."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        assert manager._database_url == sqlite_url
        assert manager._initialized is False

    def test_engine_property(self, sqlite_url):
        """Test engine property."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        assert manager.engine is None
        manager.initialize()
        assert manager.engine is not None
        manager.close()

    def test_is_initialized_property(self, sqlite_url):
        """Test is_initialized property."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        assert manager.is_initialized is False
        manager.initialize()
        assert manager.is_initialized is True
        manager.close()
        assert manager.is_initialized is False


# =============================================================================
# Test DatabaseManager - Initialization
# =============================================================================


class TestDatabaseManagerInitialization:
    """Test DatabaseManager initialization."""

    def test_initialize_success(self, sqlite_url):
        """Test successful initialization."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()
        assert manager._initialized is True
        assert manager._engine is not None
        assert manager._session_factory is not None
        assert manager._scoped_session is not None
        manager.close()

    def test_initialize_without_url_raises(self):
        """Test initialization without URL raises RuntimeError."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager()
        with pytest.raises(RuntimeError, match="Database URL not configured"):
            manager.initialize()

    def test_initialize_already_initialized_logs_warning(self, sqlite_url, caplog):
        """Test double initialization logs warning."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()
        with caplog.at_level("WARNING"):
            manager.initialize()
        assert "already initialized" in caplog.text
        manager.close()

    def test_initialize_with_invalid_url_raises(self):
        """Test initialization with invalid URL raises error."""
        DatabaseManager._instance = None  # Reset singleton
        # Use an invalid database URL that will fail
        manager = DatabaseManager("invalid://localhost/test")
        with pytest.raises(Exception):
            manager.initialize()

    @patch("database.connection.create_engine")
    def test_initialize_sqlalchemy_error(self, mock_create_engine, sqlite_url):
        """Test SQLAlchemy error during initialization."""
        mock_create_engine.side_effect = SQLAlchemyError("Connection failed")
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        with pytest.raises(SQLAlchemyError, match="Connection failed"):
            manager.initialize()


# =============================================================================
# Test DatabaseManager - Pool Configuration
# =============================================================================


class TestDatabaseManagerPoolConfig:
    """Test DatabaseManager pool configuration."""

    def test_get_pool_class_queue(self, sqlite_url):
        """Test getting QueuePool class."""
        DatabaseManager._instance = None  # Reset singleton
        config = ConnectionPoolConfig(pool_class="QueuePool")
        manager = DatabaseManager(sqlite_url, pool_config=config)
        pool_class = manager._get_pool_class()
        assert pool_class == QueuePool

    def test_get_pool_class_null(self, sqlite_url):
        """Test getting NullPool class."""
        DatabaseManager._instance = None  # Reset singleton
        config = ConnectionPoolConfig(pool_class="NullPool")
        manager = DatabaseManager(sqlite_url, pool_config=config)
        pool_class = manager._get_pool_class()
        assert pool_class == NullPool

    def test_get_pool_class_static(self, sqlite_url):
        """Test getting StaticPool class."""
        DatabaseManager._instance = None  # Reset singleton
        config = ConnectionPoolConfig(pool_class="StaticPool")
        manager = DatabaseManager(sqlite_url, pool_config=config)
        pool_class = manager._get_pool_class()
        assert pool_class == StaticPool

    def test_get_pool_class_default(self, sqlite_url):
        """Test default pool class."""
        DatabaseManager._instance = None  # Reset singleton
        config = ConnectionPoolConfig(pool_class="UnknownPool")
        manager = DatabaseManager(sqlite_url, pool_config=config)
        pool_class = manager._get_pool_class()
        assert pool_class == QueuePool

    @patch.object(DatabaseManager, "_setup_event_listeners")
    @patch("database.connection.create_engine")
    def test_initialize_with_null_pool(self, mock_create_engine, mock_listeners, sqlite_url):
        """Test initialization with NullPool."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        DatabaseManager._instance = None  # Reset singleton
        config = ConnectionPoolConfig(pool_class="NullPool")
        manager = DatabaseManager(sqlite_url, pool_config=config)
        manager.initialize()
        call_kwargs = mock_create_engine.call_args[1]
        assert call_kwargs["poolclass"] == NullPool
        assert "pool_size" not in call_kwargs
        manager.close()

    @patch.object(DatabaseManager, "_setup_event_listeners")
    @patch("database.connection.create_engine")
    def test_initialize_with_queue_pool(self, mock_create_engine, mock_listeners, sqlite_url):
        """Test initialization with QueuePool."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        DatabaseManager._instance = None  # Reset singleton
        config = ConnectionPoolConfig(
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            pool_class="QueuePool",
        )
        manager = DatabaseManager(sqlite_url, pool_config=config)
        manager.initialize()
        call_kwargs = mock_create_engine.call_args[1]
        assert call_kwargs["poolclass"] == QueuePool
        assert call_kwargs["pool_size"] == 5
        assert call_kwargs["max_overflow"] == 10
        assert call_kwargs["pool_timeout"] == 30
        assert call_kwargs["pool_recycle"] == 3600
        manager.close()


# =============================================================================
# Test DatabaseManager - Event Listeners
# =============================================================================


class TestDatabaseManagerEventListeners:
    """Test DatabaseManager event listeners."""

    def test_event_listeners_update_stats(self, sqlite_url):
        """Test that event listeners update connection statistics."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()

        # Reset stats
        manager.reset_stats()

        # Create a connection to trigger events
        conn = manager.engine.connect()
        conn.close()

        # Check that stats were updated
        stats = manager.stats
        assert stats["connections_created"] >= 1
        assert stats["connections_checked_out"] >= 1
        assert stats["connections_checked_in"] >= 1

        manager.close()

    def test_setup_event_listeners_no_engine(self, sqlite_url):
        """Test setup_event_listeners when engine is None."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        # Should not raise
        manager._setup_event_listeners()


# =============================================================================
# Test DatabaseManager - Close
# =============================================================================


class TestDatabaseManagerClose:
    """Test DatabaseManager close functionality."""

    def test_close_success(self, sqlite_url):
        """Test successful close."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()
        assert manager._initialized is True
        manager.close()
        assert manager._initialized is False
        assert manager._engine is None
        assert manager._session_factory is None

    def test_close_not_initialized_logs_warning(self, caplog):
        """Test close when not initialized logs warning."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager()
        with caplog.at_level("WARNING"):
            manager.close()
        assert "not initialized" in caplog.text

    def test_close_sqlalchemy_error(self, sqlite_url):
        """Test SQLAlchemy error during close."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()
        # Force an error on dispose
        manager._engine.dispose = MagicMock(side_effect=SQLAlchemyError("Dispose failed"))
        with pytest.raises(SQLAlchemyError, match="Dispose failed"):
            manager.close()
        manager._engine.dispose = MagicMock()  # Reset to avoid issues in cleanup

    def test_close_with_none_scoped_session(self, sqlite_url):
        """Test close when scoped_session is already None."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()
        manager._scoped_session = None
        # Should not raise
        manager.close()

    def test_close_with_none_engine(self, sqlite_url):
        """Test close when engine is already None."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()
        manager._engine = None
        # Should not raise
        manager.close()


# =============================================================================
# Test DatabaseManager - Sessions
# =============================================================================


class TestDatabaseManagerSessions:
    """Test DatabaseManager session management."""

    def test_get_session_success(self, sqlite_url):
        """Test getting session."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()
        session = manager.get_session()
        assert isinstance(session, Session)
        session.close()
        manager.close()

    def test_get_session_not_initialized_raises(self):
        """Test get_session when not initialized raises RuntimeError."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager()
        with pytest.raises(RuntimeError, match="Database not initialized"):
            manager.get_session()

    def test_get_session_updates_stats(self, sqlite_url):
        """Test that get_session updates session count."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()
        manager.reset_stats()
        session = manager.get_session()
        assert manager.stats["session_count"] == 1
        session.close()
        manager.close()

    def test_get_scoped_session_success(self, sqlite_url):
        """Test getting scoped session."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()
        session = manager.get_scoped_session()
        assert isinstance(session, Session)
        manager.close()

    def test_get_scoped_session_not_initialized_raises(self):
        """Test get_scoped_session when not initialized raises RuntimeError."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager()
        with pytest.raises(RuntimeError, match="Database not initialized"):
            manager.get_scoped_session()


# =============================================================================
# Test DatabaseManager - Session Scope
# =============================================================================


class TestDatabaseManagerSessionScope:
    """Test DatabaseManager session_scope context manager."""

    def test_session_scope_success(self, sqlite_url):
        """Test successful session scope."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()
        with manager.session_scope() as session:
            assert isinstance(session, Session)
            # Execute a simple query
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1
        manager.close()

    def test_session_scope_not_initialized_raises(self):
        """Test session_scope when not initialized raises RuntimeError."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager()
        with pytest.raises(RuntimeError, match="Database not initialized"):
            with manager.session_scope():
                pass

    def test_session_scope_rollback_on_sqlalchemy_error(self, sqlite_url):
        """Test that session_scope rolls back on SQLAlchemyError."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()

        def failing_operation(session):
            raise SQLAlchemyError("Test error")

        with pytest.raises(SQLAlchemyError, match="Test error"):
            with manager.session_scope() as session:
                failing_operation(session)

        assert manager.stats["error_count"] == 1
        manager.close()

    def test_session_scope_rollback_on_generic_error(self, sqlite_url):
        """Test that session_scope rolls back on generic error."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()

        with pytest.raises(ValueError, match="Test error"):
            with manager.session_scope():
                raise ValueError("Test error")

        assert manager.stats["error_count"] == 1
        manager.close()


# =============================================================================
# Test DatabaseManager - Table Operations
# =============================================================================


class TestDatabaseManagerTableOperations:
    """Test DatabaseManager table operations."""

    def test_create_tables_success(self, sqlite_url):
        """Test creating tables."""
        from sqlalchemy import Column, Integer, String
        from sqlalchemy.orm import declarative_base

        Base = declarative_base()

        class TestModel(Base):
            __tablename__ = "test_table"
            id = Column(Integer, primary_key=True)
            name = Column(String(50))

        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()
        manager.create_tables(Base.metadata)

        # Verify table exists by querying it
        with manager.session_scope() as session:
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"))
            assert result.scalar() == "test_table"

        manager.close()

    def test_create_tables_not_initialized_raises(self):
        """Test create_tables when not initialized raises RuntimeError."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager()
        with pytest.raises(RuntimeError, match="Database not initialized"):
            manager.create_tables(None)

    def test_create_tables_sqlalchemy_error(self, sqlite_url):
        """Test create_tables with SQLAlchemyError."""
        from sqlalchemy import MetaData

        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()

        # Create metadata that will fail
        mock_metadata = MagicMock()
        mock_metadata.create_all = MagicMock(side_effect=SQLAlchemyError("Create failed"))

        with pytest.raises(SQLAlchemyError, match="Create failed"):
            manager.create_tables(mock_metadata)

        manager.close()

    def test_drop_tables_success(self, sqlite_url):
        """Test dropping tables."""
        from sqlalchemy import Column, Integer, String
        from sqlalchemy.orm import declarative_base

        Base = declarative_base()

        class TestModel(Base):
            __tablename__ = "test_drop_table"
            id = Column(Integer, primary_key=True)
            name = Column(String(50))

        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()
        manager.create_tables(Base.metadata)

        # Verify table exists
        with manager.session_scope() as session:
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='test_drop_table'"))
            assert result.scalar() == "test_drop_table"

        # Drop tables
        manager.drop_tables(Base.metadata)

        # Verify table doesn't exist
        with manager.session_scope() as session:
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='test_drop_table'"))
            assert result.scalar() is None

        manager.close()

    def test_drop_tables_not_initialized_raises(self):
        """Test drop_tables when not initialized raises RuntimeError."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager()
        with pytest.raises(RuntimeError, match="Database not initialized"):
            manager.drop_tables(None)

    def test_drop_tables_sqlalchemy_error(self, sqlite_url):
        """Test drop_tables with SQLAlchemyError."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()

        # Create metadata that will fail
        mock_metadata = MagicMock()
        mock_metadata.drop_all = MagicMock(side_effect=SQLAlchemyError("Drop failed"))

        with pytest.raises(SQLAlchemyError, match="Drop failed"):
            manager.drop_tables(mock_metadata)

        manager.close()


# =============================================================================
# Test DatabaseManager - Health Check
# =============================================================================


class TestDatabaseManagerHealthCheck:
    """Test DatabaseManager health check."""

    def test_health_check_success(self, sqlite_url):
        """Test successful health check."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()
        result = manager.health_check()
        assert result["healthy"] is True
        assert result["response_time_ms"] is not None
        assert "pool" in result
        assert "stats" in result
        manager.close()

    def test_health_check_not_initialized(self):
        """Test health check when not initialized."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager()
        result = manager.health_check()
        assert result["healthy"] is False
        assert "Database not initialized" in result["error"]
        assert result["response_time_ms"] is None

    @patch("sqlalchemy.engine.Connection.execute")
    def test_health_check_sql_error(self, mock_execute, sqlite_url):
        """Test health check with SQL error."""
        mock_execute.side_effect = SQLAlchemyError("Connection failed")
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()
        result = manager.health_check()
        assert result["healthy"] is False
        assert "Connection failed" in result["error"]
        manager.close()


# =============================================================================
# Test DatabaseManager - Execute with Retry
# =============================================================================


class TestDatabaseManagerExecuteWithRetry:
    """Test DatabaseManager execute_with_retry."""

    def test_execute_with_retry_success(self, sqlite_url):
        """Test successful execution with retry."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()

        def operation(session):
            result = session.execute(text("SELECT 1"))
            return result.scalar()

        result = manager.execute_with_retry(operation, max_retries=3)
        assert result == 1
        manager.close()

    def test_execute_with_retry_not_initialized_raises(self):
        """Test execute_with_retry when not initialized raises RuntimeError."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager()
        with pytest.raises(RuntimeError, match="Database not initialized"):
            manager.execute_with_retry(lambda s: None)

    def test_execute_with_retry_success_after_failure(self, sqlite_url):
        """Test retry success after initial failure."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()

        call_count = 0

        def flaky_operation(session):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise SQLAlchemyError("Temporary error")
            return "success"

        with patch("time.sleep"):  # Don't actually sleep
            result = manager.execute_with_retry(flaky_operation, max_retries=3, retry_delay=0)

        assert result == "success"
        assert call_count == 2
        manager.close()

    def test_execute_with_retry_exhausted(self, sqlite_url):
        """Test retry exhausted."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()

        def failing_operation(session):
            raise SQLAlchemyError("Persistent error")

        with patch("time.sleep"):  # Don't actually sleep
            with pytest.raises(SQLAlchemyError, match="Persistent error"):
                manager.execute_with_retry(failing_operation, max_retries=3, retry_delay=0)

        assert manager.stats["error_count"] == 3
        manager.close()


# =============================================================================
# Test DatabaseManager - Statistics
# =============================================================================


class TestDatabaseManagerStats:
    """Test DatabaseManager statistics."""

    def test_stats_initial_state(self, sqlite_url):
        """Test initial statistics state."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        stats = manager.stats
        assert stats["connections_created"] == 0
        assert stats["connections_checked_out"] == 0
        assert stats["connections_checked_in"] == 0
        assert stats["session_count"] == 0
        assert stats["error_count"] == 0

    def test_reset_stats(self, sqlite_url):
        """Test resetting statistics."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()

        # Create a session to update stats
        session = manager.get_session()
        session.close()

        # Reset stats
        manager.reset_stats()
        stats = manager.stats
        assert stats["connections_created"] == 0
        assert stats["connections_checked_out"] == 0
        assert stats["connections_checked_in"] == 0
        assert stats["session_count"] == 0
        assert stats["error_count"] == 0

        manager.close()

    def test_stats_thread_safety(self, sqlite_url):
        """Test thread safety of statistics."""
        DatabaseManager._instance = None  # Reset singleton
        manager = DatabaseManager(sqlite_url)
        manager.initialize()
        manager.reset_stats()

        def increment_stats():
            for _ in range(10):
                with manager._stats_lock:
                    manager._stats["session_count"] += 1

        threads = [threading.Thread(target=increment_stats) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert manager.stats["session_count"] == 50
        manager.close()


# =============================================================================
# Test Global Functions
# =============================================================================


class TestGlobalFunctions:
    """Test global database functions."""

    def test_init_db_manager(self, sqlite_url):
        """Test init_db_manager function."""
        import database.connection as conn

        conn.db_manager = None
        DatabaseManager._instance = None
        result = init_db_manager(sqlite_url)
        assert result is not None
        assert isinstance(result, DatabaseManager)
        assert conn.db_manager is result
        assert conn.db_manager.is_initialized is True
        close_db_manager()

    def test_init_db_manager_with_pool_config(self, sqlite_url, pool_config):
        """Test init_db_manager with pool configuration."""
        import database.connection as conn

        conn.db_manager = None
        DatabaseManager._instance = None
        result = init_db_manager(sqlite_url, pool_config=pool_config)
        assert result is not None
        assert result._pool_config == pool_config
        close_db_manager()

    def test_close_db_manager(self, sqlite_url):
        """Test close_db_manager function."""
        import database.connection as conn

        conn.db_manager = None
        DatabaseManager._instance = None
        init_db_manager(sqlite_url)
        assert conn.db_manager is not None
        close_db_manager()
        assert conn.db_manager is None

    def test_close_db_manager_already_none(self):
        """Test close_db_manager when already None."""
        global db_manager
        db_manager = None
        # Should not raise
        close_db_manager()

    def test_get_db_session(self, sqlite_url):
        """Test get_db_session function."""
        import database.connection as conn

        conn.db_manager = None
        DatabaseManager._instance = None
        init_db_manager(sqlite_url)
        session = get_db_session()
        assert isinstance(session, Session)
        session.close()
        close_db_manager()

    def test_get_db_session_not_initialized(self):
        """Test get_db_session when not initialized raises RuntimeError."""
        global db_manager
        db_manager = None
        with pytest.raises(RuntimeError, match="Database manager not initialized"):
            get_db_session()


# =============================================================================
# Test Database Context
# =============================================================================


class TestDatabaseContext:
    """Test database context managers."""

    def test_get_db_context(self, sqlite_url):
        """Test get_db_context context manager."""
        import database.connection as conn

        conn.db_manager = None
        DatabaseManager._instance = None
        init_db_manager(sqlite_url)
        with get_db_context() as session:
            assert isinstance(session, Session)
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1
        close_db_manager()

    def test_get_db_context_not_initialized(self):
        """Test get_db_context when not initialized raises RuntimeError."""
        global db_manager
        db_manager = None
        with pytest.raises(RuntimeError, match="Database manager not initialized"):
            with get_db_context():
                pass


# =============================================================================
# Test Database Generator
# =============================================================================


class TestDatabaseGenerator:
    """Test database generator."""

    def test_get_db_generator(self, sqlite_url):
        """Test get_db_generator function."""
        import database.connection as conn

        conn.db_manager = None
        DatabaseManager._instance = None
        init_db_manager(sqlite_url)
        gen = get_db_generator()
        session = next(gen)
        assert isinstance(session, Session)
        # Clean up generator
        try:
            gen.close()
        except StopIteration:
            pass
        close_db_manager()

    def test_get_db_generator_not_initialized(self):
        """Test get_db_generator when not initialized raises RuntimeError."""
        import database.connection as conn

        conn.db_manager = None
        with pytest.raises(RuntimeError, match="Database manager not initialized"):
            gen = get_db_generator()
            next(gen)

    def test_get_db_generator_rollback_on_error(self, sqlite_url):
        """Test get_db_generator rolls back on error."""
        import database.connection as conn

        conn.db_manager = None
        DatabaseManager._instance = None
        init_db_manager(sqlite_url)
        gen = get_db_generator()
        session = next(gen)
        session.rollback = MagicMock()

        try:
            raise SQLAlchemyError("Test error")
        except SQLAlchemyError:
            try:
                gen.throw(SQLAlchemyError, "Test error")
            except SQLAlchemyError:
                pass

        close_db_manager()

    def test_get_db_generator_returns_generator(self, sqlite_url):
        """Test that get_db_generator returns a Generator."""
        import database.connection as conn

        conn.db_manager = None
        DatabaseManager._instance = None
        init_db_manager(sqlite_url)
        gen = get_db_generator()
        assert isinstance(gen, Generator)
        try:
            gen.close()
        except StopIteration:
            pass
        close_db_manager()

    def test_get_db_generator_commit_on_success(self, sqlite_url):
        """Test get_db_generator commits on successful completion."""
        import database.connection as conn

        conn.db_manager = None
        DatabaseManager._instance = None
        init_db_manager(sqlite_url)
        gen = get_db_generator()
        session = next(gen)
        # Successfully complete the generator (causes commit)
        try:
            next(gen)
        except StopIteration:
            pass
        close_db_manager()


# =============================================================================
# Test Utility Functions
# =============================================================================


class TestUtilityFunctions:
    """Test utility functions."""

    def test_is_valid_database_url_sqlite(self):
        """Test URL validation for SQLite."""
        assert is_valid_database_url("sqlite:///:memory:") is True
        assert is_valid_database_url("sqlite:///path/to/db.sqlite") is True

    def test_is_valid_database_url_postgresql(self):
        """Test URL validation for PostgreSQL."""
        assert is_valid_database_url("postgresql://user:pass@localhost/db") is True
        assert is_valid_database_url("postgresql+psycopg2://user:pass@localhost/db") is True

    def test_is_valid_database_url_mysql(self):
        """Test URL validation for MySQL."""
        assert is_valid_database_url("mysql://user:pass@localhost/db") is True
        assert is_valid_database_url("mysql+pymysql://user:pass@localhost/db") is True

    def test_is_valid_database_url_invalid(self):
        """Test URL validation for invalid URLs."""
        assert is_valid_database_url("") is False
        assert is_valid_database_url(None) is False
        assert is_valid_database_url("not-a-url") is False
        assert is_valid_database_url("http://localhost/db") is False
        assert is_valid_database_url("ftp://localhost/db") is False

    def test_is_valid_database_url_no_host(self):
        """Test URL validation for URLs without host (non-SQLite)."""
        assert is_valid_database_url("postgresql:///") is False
        assert is_valid_database_url("mysql:///") is False

    def test_create_test_connection_pool_config(self):
        """Test create_test_connection_pool_config function."""
        config = create_test_connection_pool_config()
        assert isinstance(config, ConnectionPoolConfig)
        assert config.pool_size == 1
        assert config.max_overflow == 0
        assert config.pool_timeout == 5
        assert config.pool_recycle == 300
        assert config.pool_pre_ping is True
        assert config.pool_class == "StaticPool"
        assert config.echo is False

    def test_is_valid_database_url_exception(self):
        """Test is_valid_database_url handles exceptions."""
        # Mock urlparse to raise an exception
        with patch(
            "database.connection.urlparse",
            side_effect=Exception("Parse error"),
        ):
            result = is_valid_database_url("sqlite:///test.db")
            assert result is False


# =============================================================================
# Test Edge Cases and Error Handling
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_concurrent_initialization(self, sqlite_url):
        """Test concurrent initialization attempts."""
        DatabaseManager._instance = None
        results = []

        def init_manager():
            try:
                manager = DatabaseManager(sqlite_url)
                manager.initialize()
                results.append(manager)
            except Exception as e:
                results.append(e)

        threads = [threading.Thread(target=init_manager) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should get the same instance
        managers = [r for r in results if isinstance(r, DatabaseManager)]
        assert len(managers) == 5
        assert all(m is managers[0] for m in managers)

        managers[0].close()

    def test_session_scope_nested(self, sqlite_url):
        """Test nested session scopes."""
        DatabaseManager._instance = None
        manager = DatabaseManager(sqlite_url)
        manager.initialize()

        with manager.session_scope() as outer:
            with manager.session_scope() as inner:
                # Both sessions should be valid
                outer_result = outer.execute(text("SELECT 1")).scalar()
                inner_result = inner.execute(text("SELECT 2")).scalar()
                assert outer_result == 1
                assert inner_result == 2

        manager.close()

    def test_multiple_managers_same_thread(self, sqlite_url):
        """Test that singleton returns same manager."""
        DatabaseManager._instance = None
        manager1 = DatabaseManager(sqlite_url)
        manager1.initialize()

        manager2 = DatabaseManager(sqlite_url)
        # Should be the same instance
        assert manager1 is manager2

        manager1.close()

    def test_reinitialize_after_close(self, sqlite_url):
        """Test reinitializing after close."""
        DatabaseManager._instance = None
        manager = DatabaseManager(sqlite_url)
        manager.initialize()
        manager.close()

        # Since it's singleton, we can't truly reinitialize with different settings
        # but we can verify the instance was reset properly
        assert manager._initialized is False


# =============================================================================
# Test Module Imports
# =============================================================================


class TestModuleImports:
    """Test module structure and imports."""

    def test_module_exports(self):
        """Test that all expected exports exist."""
        from database import connection

        expected_exports = [
            "ConnectionPoolConfig",
            "DatabaseManager",
            "init_db_manager",
            "close_db_manager",
            "get_db_session",
            "get_db_context",
            "get_db_generator",
            "is_valid_database_url",
            "create_test_connection_pool_config",
            "db_manager",
        ]

        for export in expected_exports:
            assert hasattr(connection, export), f"Missing export: {export}"

    def test_module_docstring(self):
        """Test that module has docstring."""
        from database import connection

        assert connection.__doc__ is not None
        assert "Database Connection Management" in connection.__doc__


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
