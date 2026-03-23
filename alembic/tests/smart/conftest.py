"""
Pytest fixtures for alembic migration tests.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest


# Mock SQLAlchemy and Alembic before importing env.py
@pytest.fixture(autouse=True)
def mock_sqlalchemy_alembic():
    """Mock SQLAlchemy and Alembic modules."""
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__ = Mock(return_value=MagicMock())
    mock_engine.connect.return_value.__exit__ = Mock(return_value=False)

    mock_config = MagicMock()
    mock_config.config_file_name = None
    mock_config.get_main_option.return_value = "sqlite:///test.db"
    mock_config.get_section.return_value = {}
    mock_config.config_ini_section = "alembic"

    mock_context = MagicMock()
    mock_context.config = mock_config
    mock_context.is_offline_mode.return_value = False

    mock_base = MagicMock()
    mock_base.metadata = MagicMock()

    mock_db_url = "sqlite:///test.db"

    with patch.dict(
        "sys.modules",
        {
            "sqlalchemy": MagicMock(),
            "sqlalchemy.engine": MagicMock(),
            "alembic": MagicMock(),
            "alembic.context": mock_context,
            "database": MagicMock(),
            "database.models": MagicMock(),
        },
    ):
        with patch("sqlalchemy.engine_from_config", return_value=mock_engine):
            with patch("sqlalchemy.pool.NullPool", MagicMock()):
                with patch("database.models.DATABASE_URL", mock_db_url):
                    with patch("database.models.Base", mock_base):
                        yield {
                            "context": mock_context,
                            "engine": mock_engine,
                            "base": mock_base,
                            "db_url": mock_db_url,
                        }


@pytest.fixture
def mock_alembic_context():
    """Create a mock Alembic context."""
    context = MagicMock()
    context.config = MagicMock()
    context.config.config_file_name = None
    context.config.get_main_option.return_value = "sqlite:///test.db"
    context.config.get_section.return_value = {}
    context.config.config_ini_section = "alembic"
    context.is_offline_mode.return_value = False
    return context


@pytest.fixture
def mock_sqlalchemy_engine():
    """Create a mock SQLAlchemy engine."""
    engine = MagicMock()
    connection = MagicMock()
    engine.connect.return_value.__enter__ = Mock(return_value=connection)
    engine.connect.return_value.__exit__ = Mock(return_value=False)
    return engine


@pytest.fixture
def mock_database_models():
    """Create mock database models."""
    base = MagicMock()
    base.metadata = MagicMock()
    base.metadata.tables = {}
    return {
        "Base": base,
        "DATABASE_URL": "sqlite:///test.db",
    }


@pytest.fixture
def sample_migration_script():
    """Create a sample migration script content."""
    return '''
"""Create users table

Revision ID: abc123
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'abc123'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )


def downgrade() -> None:
    """Revert migration."""
    op.drop_table('users')
'''


@pytest.fixture
def sample_alembic_ini():
    """Create sample alembic.ini content."""
    return """
# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = alembic

# template used to generate migration files
# file_template = %%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python-dateutil library that can be
# installed by adding `alembic[tz]` to the pip requirements
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment asynchronously
# usually only useful for async database engines
# run_async = false

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses
# os.pathsep.
# version_path_separator = os

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = sqlite:///test.db

[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""


@pytest.fixture
def mock_env_vars():
    """Create mock environment variables."""
    return {
        "DATABASE_URL": "postgresql://user:pass@localhost/testdb",
        "TESTING": "true",
    }
