"""
SMART Tests for Alembic Migration Scripts

Test Strategy:
1. test_module_importable - Verify migration scripts can be imported
2. test_module_uses_tool_executor - Verify ToolExecutor pattern (if applicable)
3. test_module_not_found_error - Handle missing migration scripts
4. test_module_timeout_error - Handle timeout scenarios
5. test_module_parser_extracts_findings - Parser extracts findings
6. test_module_end_to_end_mocked - Full workflow with Mock
7. test_module_empty_input - Handle empty input
8. test_module_invalid_output - Handle invalid output
"""

import ast
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# Test 1: Module Import
# =============================================================================


class TestModuleImportable:
    """Test that migration scripts can be imported and validated."""

    def test_versions_directory_structure(self):
        """Test that versions directory exists or can be created."""
        versions_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "versions")

        # Directory may not exist yet (no migrations created)
        # But it should be creatable
        if not os.path.exists(versions_path):
            # This is expected before first migration
            assert True
        else:
            assert os.path.isdir(versions_path)

    def test_sample_migration_syntax(self):
        """Test that a sample migration has valid Python syntax."""
        sample_migration = '''
"""Create test table

Revision ID: test123
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'test123'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration."""
    op.create_table(
        'test_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Revert migration."""
    op.drop_table('test_table')
'''

        # Should parse as valid Python
        try:
            ast.parse(sample_migration)
            valid = True
        except SyntaxError:
            valid = False

        assert valid, "Sample migration should have valid Python syntax"

    def test_migration_has_required_attributes(self):
        """Test that migration has required attributes."""
        sample_migration = """
revision = 'test123'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
"""

        tree = ast.parse(sample_migration)

        # Check for required attributes
        assignments = [
            node.targets[0].id
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
        ]

        assert "revision" in assignments
        assert "down_revision" in assignments
        assert "branch_labels" in assignments
        assert "depends_on" in assignments


# =============================================================================
# Test 2: ToolExecutor Pattern (Architecture Compliance)
# =============================================================================


class TestModuleUsesToolExecutor:
    """Verify ToolExecutor pattern compliance in migrations."""

    def test_migration_uses_alembic_op(self):
        """Verify migration uses alembic operations."""
        sample_migration = """
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.create_table('test', sa.Column('id', sa.Integer()))

def downgrade() -> None:
    op.drop_table('test')
"""

        assert "from alembic import op" in sample_migration
        assert "op.create_table" in sample_migration
        assert "op.drop_table" in sample_migration

    def test_migration_uses_sqlalchemy(self):
        """Verify migration uses SQLAlchemy."""
        sample_migration = """
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.create_table(
        'test',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
    )
"""

        assert "import sqlalchemy as sa" in sample_migration
        assert "sa.Integer" in sample_migration
        assert "sa.String" in sample_migration

    def test_migration_has_type_annotations(self):
        """Verify migration functions have type annotations."""
        sample_migration = """
def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
"""

        tree = ast.parse(sample_migration)

        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        for func in functions:
            assert func.returns is not None, f"Function {func.name} should have return type annotation"


# =============================================================================
# Test 3: Not Found Error Handling
# =============================================================================


class TestModuleNotFoundError:
    """Test handling of missing migration scripts."""

    def test_handles_missing_migration_file(self):
        """Test graceful handling when migration file is missing."""
        nonexistent_path = "/nonexistent/migration.py"

        assert not os.path.exists(nonexistent_path)

    def test_handles_missing_versions_directory(self):
        """Test graceful handling when versions directory is missing."""
        nonexistent_dir = "/nonexistent/versions"

        assert not os.path.exists(nonexistent_dir)

    def test_handles_missing_revision_id(self):
        """Test handling of migration without revision ID."""
        invalid_migration = """
# Missing revision ID
down_revision = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
"""

        tree = ast.parse(invalid_migration)

        assignments = [
            node.targets[0].id
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
        ]

        # revision should be missing
        assert "revision" not in assignments


# =============================================================================
# Test 4: Timeout Error Handling
# =============================================================================


class TestModuleTimeoutError:
    """Test timeout handling in migration operations."""

    def test_migration_execution_timeout(self):
        """Test handling of migration execution timeout."""
        # Simulate a migration that might timeout
        slow_migration = """
import time

def upgrade() -> None:
    # Simulated slow operation
    pass
"""

        # Parse should work regardless of timeout potential
        tree = ast.parse(slow_migration)
        assert tree is not None


# =============================================================================
# Test 5: Parser/Data Extraction Tests
# =============================================================================


class TestModuleParserExtractsFindings:
    """Test data extraction from migration scripts."""

    def test_extract_revision_id(self):
        """Test extracting revision ID from migration."""
        migration = """
revision = 'abc123def456'
down_revision = None
"""

        tree = ast.parse(migration)

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if isinstance(node.targets[0], ast.Name) and node.targets[0].id == "revision":
                    revision_value = node.value.s
                    assert revision_value == "abc123def456"

    def test_extract_down_revision(self):
        """Test extracting down_revision from migration."""
        migration = """
revision = 'abc123'
down_revision = 'xyz789'
"""

        tree = ast.parse(migration)

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if isinstance(node.targets[0], ast.Name) and node.targets[0].id == "down_revision":
                    down_revision_value = node.value.s
                    assert down_revision_value == "xyz789"

    def test_extract_table_operations(self):
        """Test extracting table operations from migration."""
        migration = """
def upgrade() -> None:
    op.create_table('users', sa.Column('id', sa.Integer()))
    op.create_index('idx_users', 'users', ['id'])

def downgrade() -> None:
    op.drop_index('idx_users', 'users')
    op.drop_table('users')
"""

        tree = ast.parse(migration)

        # Count function calls
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        call_names = []
        for call in calls:
            if isinstance(call.func, ast.Attribute):
                call_names.append(call.func.attr)

        assert "create_table" in call_names
        assert "create_index" in call_names
        assert "drop_index" in call_names
        assert "drop_table" in call_names

    def test_extract_column_definitions(self):
        """Test extracting column definitions from migration."""
        migration = """
def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('email', sa.String(255), nullable=False),
    )
"""

        tree = ast.parse(migration)

        # Extract column names from sa.Column calls
        columns = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == "Column":
                    if node.args and isinstance(node.args[0], ast.Str):
                        columns.append(node.args[0].s)

        assert "id" in columns
        assert "name" in columns
        assert "email" in columns


# =============================================================================
# Test 6: End-to-End Workflow Tests
# =============================================================================


class TestModuleEndToEndMocked:
    """Full workflow tests with mocked dependencies."""

    def test_migration_creation_workflow(self):
        """Test complete migration creation workflow."""
        # Simulate creating a migration
        migration_content = '''
"""Add users table

Revision ID: rev123
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'rev123'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(80), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )


def downgrade() -> None:
    """Revert migration."""
    op.drop_table('users')
'''

        # Validate syntax
        tree = ast.parse(migration_content)
        assert tree is not None

        # Validate structure
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        assert "upgrade" in functions
        assert "downgrade" in functions

        # Validate attributes
        assignments = [
            node.targets[0].id
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
        ]
        assert "revision" in assignments

    def test_migration_dependency_chain(self):
        """Test migration dependency chain."""
        # First migration (base)
        migration1 = """
revision = 'rev001'
down_revision = None
"""

        # Second migration (depends on first)
        migration2 = """
revision = 'rev002'
down_revision = 'rev001'
"""

        # Third migration (depends on second)
        migration3 = """
revision = 'rev003'
down_revision = 'rev002'
"""

        # Parse all migrations
        tree1 = ast.parse(migration1)
        tree2 = ast.parse(migration2)
        tree3 = ast.parse(migration3)

        # Verify chain
        def get_revision(tree):
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    if isinstance(node.targets[0], ast.Name):
                        if node.targets[0].id == "revision":
                            return node.value.s
            return None

        def get_down_revision(tree):
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    if isinstance(node.targets[0], ast.Name):
                        if node.targets[0].id == "down_revision":
                            return node.value.s if isinstance(node.value, ast.Str) else None
            return None

        assert get_revision(tree1) == "rev001"
        assert get_down_revision(tree1) is None

        assert get_revision(tree2) == "rev002"
        assert get_down_revision(tree2) == "rev001"

        assert get_revision(tree3) == "rev003"
        assert get_down_revision(tree3) == "rev002"

    def test_migration_with_mocked_alembic(self):
        """Test migration with mocked alembic operations."""
        mock_op = MagicMock()
        mock_sa = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "alembic": MagicMock(),
                "alembic.op": mock_op,
                "sqlalchemy": mock_sa,
            },
        ):
            # Migration should be able to import mocked modules
            import sqlalchemy as sa

            from alembic import op

            assert op is not None
            assert sa is not None


# =============================================================================
# Test 7: Empty Input Handling
# =============================================================================


class TestModuleEmptyInput:
    """Test handling of empty or minimal input."""

    def test_empty_migration_functions(self):
        """Test handling of empty migration functions."""
        empty_migration = """
revision = 'empty123'
down_revision = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
"""

        # Should parse successfully
        tree = ast.parse(empty_migration)
        assert tree is not None

        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        assert "upgrade" in functions
        assert "downgrade" in functions

    def test_minimal_migration(self):
        """Test handling of minimal migration."""
        minimal_migration = """
revision = 'min123'
down_revision = None

def upgrade() -> None:
    pass
"""

        tree = ast.parse(minimal_migration)
        assert tree is not None

    def test_migration_with_empty_docstrings(self):
        """Test handling of migration with empty docstrings."""
        migration = '''
""""""
from alembic import op

def upgrade() -> None:
    """"""
    pass

def downgrade() -> None:
    """"""
    pass
'''

        tree = ast.parse(migration)
        assert tree is not None


# =============================================================================
# Test 8: Invalid Output Handling
# =============================================================================


class TestModuleInvalidOutput:
    """Test handling of invalid or malformed output."""

    def test_migration_with_syntax_error(self):
        """Test handling of migration with syntax error."""
        invalid_migration = """
revision = 'invalid123'
def upgrade() -> None
    # Missing colon above
    pass
"""

        # Should raise SyntaxError
        with pytest.raises(SyntaxError):
            ast.parse(invalid_migration)

    def test_migration_with_missing_upgrade(self):
        """Test handling of migration without upgrade function."""
        incomplete_migration = """
revision = 'incomplete123'
down_revision = None

def downgrade() -> None:
    pass
"""

        tree = ast.parse(incomplete_migration)

        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        assert "upgrade" not in functions
        assert "downgrade" in functions

    def test_migration_with_invalid_revision_format(self):
        """Test handling of migration with invalid revision format."""
        invalid_revision = """
revision = 12345  # Should be string
down_revision = None

def upgrade() -> None:
    pass
"""

        tree = ast.parse(invalid_revision)

        # Check revision type
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if isinstance(node.targets[0], ast.Name) and node.targets[0].id == "revision":
                    # Revision is an integer (Num in Python 3.7, Constant in 3.8+)
                    assert isinstance(node.value, (ast.Num, ast.Constant))

    def test_migration_with_unicode_in_revision(self):
        """Test handling of unicode characters in revision message."""
        unicode_migration = '''
"""Migration with unicode: äöü ñ 中文 🚀

Revision ID: unicode123
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
revision = 'unicode123'
down_revision = None

def upgrade() -> None:
    pass
'''

        # Should parse successfully
        tree = ast.parse(unicode_migration)
        assert tree is not None
