# Contributing to Zen-AI-Pentest

First off, thank you for considering contributing to Zen-AI-Pentest! It's people like you that make this tool better for the security community.

## 🚀 Getting Started

### Development Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/zen-ai-pentest.git
cd zen-ai-pentest

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_react_agent.py -v

# Run with markers
pytest -m "not slow"  # Skip slow tests
```

## 📋 Contribution Guidelines

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings (Google style)
- Maximum line length: 100 characters

```python
def scan_target(target: str, ports: List[int] = None) -> ScanResult:
    """
    Scan a target for open ports.
    
    Args:
        target: IP address or hostname
        ports: List of ports to scan (default: top 1000)
        
    Returns:
        ScanResult object with findings
        
    Raises:
        ValueError: If target is invalid
    """
    pass
```

### Commit Messages

Use conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style (formatting, no logic change)
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

Example:
```
feat(tools): add Nessus vulnerability scanner integration

- Add NessusAPI class for REST API communication
- Support scan initiation and report download
- Add tests for Nessus integration
```

### Pull Request Process

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code
   - Add tests
   - Update documentation

3. **Ensure tests pass**
   ```bash
   pytest
   flake8
   black --check .
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**
   - Fill out the PR template
   - Link related issues
   - Request review from maintainers

## 🏗️ Project Structure

```
zen-ai-pentest/
├── api/              # FastAPI endpoints
├── agents/           # AI agent implementations
├── database/         # Database models
├── tools/            # Pentesting tool integrations
├── virtualization/   # VM management
├── gui/              # Web interface
├── reports/          # Report generation
├── notifications/    # Slack/email alerts
├── tests/            # Test suite
└── docs/             # Documentation
```

## 🛠️ Adding New Tools

To add a new pentesting tool:

1. Create file in `tools/`:
   ```python
   # tools/my_tool_integration.py
   from langchain_core.tools import tool
   
   @tool
   def my_tool_scan(target: str) -> str:
       """Description of what this tool does"""
       # Implementation
       return "Result"
   ```

2. Register in `tools/__init__.py`:
   ```python
   from .my_tool_integration import my_tool_scan
   
   TOOL_REGISTRY = {
       # ... existing tools
       'my_tool_scan': my_tool_scan,
   }
   ```

3. Add tests in `tests/tools/test_my_tool.py`

4. Update documentation

## 🧪 Testing Guidelines

### Unit Tests

```python
# tests/tools/test_nmap.py
def test_nmap_scan_localhost():
    """Test nmap scan against localhost"""
    from tools.nmap_integration import NmapTool
    
    nmap = NmapTool()
    result = nmap.scan("127.0.0.1", "22,80")
    
    assert isinstance(result, dict)
    assert "scan" in result
```

### Integration Tests

```python
# tests/integration/test_api.py
@pytest.mark.integration
def test_create_scan_api(client):
    """Test creating scan via API"""
    response = client.post("/scans", json={
        "name": "Test Scan",
        "target": "scanme.nmap.org",
        "scan_type": "network"
    })
    assert response.status_code == 201
```

## 📝 Documentation

- Update README.md if adding major features
- Add docstrings to all public functions
- Update API docs in `docs/API.md`
- Add examples to `examples/`

## 🐛 Reporting Bugs

Use GitHub Issues with template:

```markdown
**Description**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What you expected to happen

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11]
- Version: [e.g., 2.0.0]

**Screenshots**
If applicable

**Additional Context**
Any other information
```

## 💡 Feature Requests

Create GitHub Issue with label `enhancement`:

- Describe the feature
- Explain use case
- Propose implementation (optional)

## 🔒 Security Issues

**DO NOT** create public issues for security vulnerabilities.

Instead, email: security@zen-pentest.local

Include:
- Description of vulnerability
- Steps to reproduce
- Possible impact
- Suggested fix (if any)

## 🏅 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

## 📜 Code of Conduct

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Personal or political attacks
- Publishing others' private information

## ❓ Questions?

- Join our [Discord](https://discord.gg/zen-pentest)
- Start a [Discussion](https://github.com/SHAdd0WTAka/zen-ai-pentest/discussions)
- Email: support@zen-pentest.local

Thank you for contributing! 🙏
