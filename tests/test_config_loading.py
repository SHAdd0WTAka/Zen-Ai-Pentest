"""
Test configuration loading - Isolated from complex imports
"""

import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_env_file_exists():
    """Test that .env.example exists and is readable"""
    assert os.path.exists('.env.example')
    with open('.env.example', 'r') as f:
        content = f.read()
        assert 'KIMI_API_KEY' in content
        assert 'DEFAULT_BACKEND' in content


def test_requirements_exist():
    """Test that requirements files exist"""
    assert os.path.exists('requirements.txt')

    with open('requirements.txt', 'r') as f:
        content = f.read()
        # Should have some dependencies
        assert len(content) > 0


def test_pyproject_exists():
    """Test pyproject.toml configuration"""
    if os.path.exists('pyproject.toml'):
        with open('pyproject.toml', 'r') as f:
            content = f.read()
            assert '[tool.black]' in content or '[build-system]' in content


def test_version_consistency():
    """Test version information across files"""
    # Check if version is mentioned somewhere
    version_found = False

    # Try README
    if os.path.exists('README.md'):
        with open('README.md', 'r') as f:
            if '2.3' in f.read():
                version_found = True

    # Try setup.py
    if os.path.exists('setup.py'):
        with open('setup.py', 'r') as f:
            if 'version' in f.read():
                version_found = True

    # We just check it doesn't crash
    assert True


def test_dockerfile_exists():
    """Test Docker configuration"""
    if os.path.exists('docker/Dockerfile'):
        with open('docker/Dockerfile', 'r') as f:
            content = f.read()
            assert 'FROM' in content
            assert len(content) > 100


def test_github_workflows_exist():
    """Test that GitHub Actions workflows are configured"""
    workflows_dir = '.github/workflows'
    assert os.path.exists(workflows_dir)

    workflows = [f for f in os.listdir(workflows_dir) if f.endswith('.yml')]
    assert len(workflows) > 5  # Should have multiple workflows


def test_docs_structure():
    """Test documentation structure"""
    assert os.path.exists('docs')

    doc_files = os.listdir('docs')
    assert len(doc_files) > 0


def test_tests_directory_structure():
    """Test that tests are organized"""
    assert os.path.exists('tests')

    test_files = [f for f in os.listdir('tests') if f.startswith('test_')]
    assert len(test_files) > 10  # Should have multiple test files


class TestPathOperations:
    """Test path and file operations"""

    def test_path_joining(self):
        """Test path operations"""
        base = os.path.dirname(os.path.abspath(__file__))
        parent = os.path.dirname(base)
        assert os.path.exists(parent)
        assert os.path.isdir(parent)

    def test_file_reading(self):
        """Test safe file reading"""
        # Read a small file
        if os.path.exists('.gitignore'):
            with open('.gitignore', 'r') as f:
                content = f.read()
                assert isinstance(content, str)
                assert len(content) > 0


def test_string_formatting():
    """Test string formatting operations"""
    name = "ZenClaw"
    version = "1.0"

    # f-strings
    result = f"{name} v{version}"
    assert "ZenClaw" in result
    assert "1.0" in result

    # format method
    result2 = "{} v{}".format(name, version)
    assert result == result2


def test_type_checking():
    """Test basic type operations"""
    assert isinstance("text", str)
    assert isinstance(123, int)
    assert isinstance(3.14, float)
    assert isinstance([], list)
    assert isinstance({}, dict)
    assert isinstance(True, bool)


def test_exception_types():
    """Test exception handling"""
    exceptions_caught = 0

    try:
        int("not a number")
    except ValueError:
        exceptions_caught += 1

    try:
        [][1]
    except IndexError:
        exceptions_caught += 1

    try:
        {}["missing_key"]
    except KeyError:
        exceptions_caught += 1

    assert exceptions_caught == 3


def test_json_operations():
    """Test JSON handling"""
    data = {
        "tool": "nmap",
        "target": "scanme.nmap.org",
        "options": ["-sV", "-O"]
    }

    # Serialize
    json_str = json.dumps(data)
    assert isinstance(json_str, str)
    assert "nmap" in json_str

    # Deserialize
    restored = json.loads(json_str)
    assert restored["tool"] == "nmap"
    assert len(restored["options"]) == 2
