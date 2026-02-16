"""
Standalone tests - No imports, no dependencies
Run with: python -m pytest tests/test_standalone.py -v
"""
import os
import sys


def test_basic_math():
    """Basic math operations"""
    assert 1 + 1 == 2
    assert 10 / 2 == 5
    assert 3 * 3 == 9
    assert 10 - 5 == 5


def test_string_ops():
    """String operations"""
    text = "zen-ai-pentest"
    assert len(text) == 14
    assert text.upper() == "ZEN-AI-PENTEST"
    assert "ai" in text
    assert text.startswith("zen")


def test_list_ops():
    """List operations"""
    tools = ["nmap", "sqlmap", "nuclei"]
    assert len(tools) == 3
    tools.append("metasploit")
    assert len(tools) == 4
    assert "nmap" in tools


def test_dict_ops():
    """Dict operations"""
    config = {"name": "zen", "version": "2.3.9"}
    assert config["name"] == "zen"
    assert "version" in config
    config["new_key"] = "value"
    assert config["new_key"] == "value"


def test_file_structure():
    """Check critical files exist"""
    files = ["README.md", "requirements.txt", "setup.py"]
    for f in files:
        assert os.path.exists(f), f"{f} missing"


def test_directory_structure():
    """Check directories exist"""
    dirs = ["core", "api", "modules", "tests", "docs"]
    for d in dirs:
        assert os.path.isdir(d), f"{d} not a directory"


def test_python_version():
    """Check Python version"""
    version = sys.version_info
    assert version.major == 3
    assert version.minor >= 9


def test_env_vars():
    """Environment variables"""
    assert "PATH" in os.environ


def test_boolean_logic():
    """Boolean operations"""
    assert True is True
    assert False is False
    assert not False is True
    assert True and True is True
    assert True or False is True


def test_type_checking():
    """Type checking"""
    assert isinstance("text", str)
    assert isinstance(123, int)
    assert isinstance(3.14, float)
    assert isinstance([], list)
    assert isinstance({}, dict)


def test_error_handling():
    """Error handling"""
    try:
        _ = 1 / 0
        assert False, "Should have raised"
    except ZeroDivisionError:
        assert True


def test_iteration():
    """Iteration"""
    items = [1, 2, 3]
    total = 0
    for i in items:
        total += i
    assert total == 6


def test_comprehensions():
    """List comprehensions"""
    squares = [x**2 for x in range(5)]
    assert squares == [0, 1, 4, 9, 16]


def test_lambda():
    """Lambda functions"""
    double = lambda x: x * 2
    assert double(5) == 10


def test_map_filter():
    """Map and filter"""
    nums = [1, 2, 3, 4, 5]
    doubled = list(map(lambda x: x * 2, nums))
    assert doubled == [2, 4, 6, 8, 10]
    
    evens = list(filter(lambda x: x % 2 == 0, nums))
    assert evens == [2, 4]
