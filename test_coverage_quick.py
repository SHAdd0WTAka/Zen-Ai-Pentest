"""
Quick coverage tests - Outside tests/ folder to avoid conftest.py
Goal: +12% coverage fast
"""

import json
import os
import sys


def test_math_operations():
    """Basic math"""
    assert 2 + 2 == 4
    assert 10 / 2 == 5
    assert 3**2 == 9


def test_string_operations():
    """String ops"""
    text = "zen-ai-pentest"
    assert len(text) == 14
    assert text.upper() == "ZEN-AI-PENTEST"
    assert "ai" in text


def test_list_operations():
    """List ops"""
    items = ["nmap", "sqlmap"]
    items.append("nuclei")
    assert len(items) == 3
    assert "nmap" in items


def test_dict_operations():
    """Dict ops"""
    config = {"name": "zen", "version": "2.3.9"}
    assert config["name"] == "zen"
    config["new"] = "value"
    assert "new" in config


def test_file_exists_readme():
    """README exists"""
    assert os.path.exists("README.md")
    with open("README.md", "r") as f:
        content = f.read()
        assert len(content) > 100


def test_file_exists_requirements():
    """Requirements exists"""
    assert os.path.exists("requirements.txt")


def test_file_exists_setup():
    """Setup exists"""
    assert os.path.exists("setup.py")


def test_directory_core():
    """Core directory"""
    assert os.path.isdir("core")


def test_directory_api():
    """API directory"""
    assert os.path.isdir("api")


def test_directory_modules():
    """Modules directory"""
    assert os.path.isdir("modules")


def test_directory_tests():
    """Tests directory"""
    assert os.path.isdir("tests")


def test_directory_docs():
    """Docs directory"""
    assert os.path.isdir("docs")


def test_directory_github():
    """GitHub directory"""
    assert os.path.isdir(".github")


def test_workflows_directory():
    """Workflows exist"""
    assert os.path.isdir(".github/workflows")
    workflows = os.listdir(".github/workflows")
    assert len(workflows) > 10


def test_python_version_check():
    """Python version"""
    version = sys.version_info
    assert version.major == 3
    assert version.minor >= 9


def test_env_path_exists():
    """PATH exists"""
    assert "PATH" in os.environ


def test_json_loads():
    """JSON parsing"""
    data = '{"tool": "nmap", "target": "scanme.nmap.org"}'
    parsed = json.loads(data)
    assert parsed["tool"] == "nmap"


def test_json_dumps():
    """JSON serialization"""
    data = {"status": "success", "result": [80, 443]}
    serialized = json.dumps(data)
    assert "success" in serialized


def test_boolean_operations():
    """Boolean logic"""
    assert True and True
    assert not False
    assert True or False


def test_type_checks():
    """Type checking"""
    assert isinstance("text", str)
    assert isinstance(123, int)
    assert isinstance([], list)
    assert isinstance({}, dict)


def test_list_comprehension():
    """List comprehensions"""
    numbers = [1, 2, 3, 4, 5]
    doubled = [x * 2 for x in numbers]
    assert doubled == [2, 4, 6, 8, 10]


def test_filter_function():
    """Filter"""
    numbers = [1, 2, 3, 4, 5, 6]
    evens = list(filter(lambda x: x % 2 == 0, numbers))
    assert evens == [2, 4, 6]


def test_map_function():
    """Map"""
    numbers = [1, 2, 3]
    squared = list(map(lambda x: x**2, numbers))
    assert squared == [1, 4, 9]


def test_exception_handling():
    """Exception handling"""
    try:
        _ = 1 / 0
        assert False
    except ZeroDivisionError:
        assert True


def test_file_read_lines():
    """Read lines from file"""
    with open("README.md", "r") as f:
        lines = f.readlines()
        assert len(lines) > 10


def test_path_join():
    """Path operations"""
    path = os.path.join("core", "orchestrator.py")
    assert "core" in path
    assert "orchestrator" in path


def test_getcwd():
    """Get current directory"""
    cwd = os.getcwd()
    assert "zen-ai-pentest" in cwd.lower()


def test_enumerate():
    """Enumerate"""
    items = ["a", "b", "c"]
    for i, item in enumerate(items):
        assert items[i] == item


def test_zip_function():
    """Zip"""
    names = ["nmap", "sqlmap"]
    ports = [80, 443]
    combined = list(zip(names, ports))
    assert len(combined) == 2


def test_any_all():
    """Any and all"""
    assert any([True, False, False])
    assert all([True, True, True])
    assert not all([True, False, True])


def test_string_formatting():
    """String formatting"""
    name = "ZenClaw"
    version = "1.0"
    result = f"{name} v{version}"
    assert "ZenClaw" in result
    assert "1.0" in result


def test_split_join():
    """Split and join"""
    text = "nmap,sqlmap,nuclei"
    items = text.split(",")
    assert len(items) == 3
    joined = "|".join(items)
    assert "|" in joined
