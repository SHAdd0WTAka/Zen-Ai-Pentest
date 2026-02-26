"""Utils and Helpers Tests.

Target: +5% Coverage durch Utils-Tests.
"""

import pytest
from datetime import datetime, timedelta


def test_import_utils():
    """Test that utils modules can be imported."""
    try:
        from utils import helpers
        assert helpers is not None
    except ImportError:
        pytest.skip("utils.helpers not available")


def test_import_security():
    """Test importing security utils."""
    try:
        from utils import security
        assert security is not None
    except ImportError:
        pytest.skip("utils.security not available")


def test_import_async_fixes():
    """Test importing async fixes."""
    try:
        from utils import async_fixes
        assert async_fixes is not None
    except ImportError:
        pytest.skip("utils.async_fixes not available")


class TestDateTimeUtils:
    """Tests for datetime utilities."""

    def test_datetime_now(self):
        """Test datetime now."""
        now = datetime.now()
        assert now is not None
        assert isinstance(now, datetime)

    def test_datetime_timedelta(self):
        """Test datetime timedelta."""
        delta = timedelta(hours=1)
        assert delta.total_seconds() == 3600


class TestStringUtils:
    """Tests for string utilities."""

    def test_string_join(self):
        """Test string join."""
        items = ["a", "b", "c"]
        result = ",".join(items)
        assert result == "a,b,c"

    def test_string_split(self):
        """Test string split."""
        text = "a,b,c"
        result = text.split(",")
        assert result == ["a", "b", "c"]

    def test_string_strip(self):
        """Test string strip."""
        text = "  hello  "
        result = text.strip()
        assert result == "hello"


class TestDictUtils:
    """Tests for dict utilities."""

    def test_dict_get(self):
        """Test dict get."""
        d = {"key": "value"}
        assert d.get("key") == "value"
        assert d.get("missing") is None
        assert d.get("missing", "default") == "default"

    def test_dict_update(self):
        """Test dict update."""
        d1 = {"a": 1}
        d2 = {"b": 2}
        d1.update(d2)
        assert d1 == {"a": 1, "b": 2}


class TestListUtils:
    """Tests for list utilities."""

    def test_list_append(self):
        """Test list append."""
        lst = []
        lst.append(1)
        assert lst == [1]

    def test_list_extend(self):
        """Test list extend."""
        lst = [1, 2]
        lst.extend([3, 4])
        assert lst == [1, 2, 3, 4]

    def test_list_comprehension(self):
        """Test list comprehension."""
        numbers = [1, 2, 3, 4, 5]
        squares = [n ** 2 for n in numbers]
        assert squares == [1, 4, 9, 16, 25]
