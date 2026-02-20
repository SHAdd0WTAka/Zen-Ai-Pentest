# Contributing to Zen-AI-Pentest

> **Thank you for your interest in contributing!**

We welcome contributions from the community. This document provides detailed guidelines for contributing to Zen-AI-Pentest.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pull Request Checklist](#pull-request-checklist)
- [Code Review Process](#code-review-process)
- [Testing Requirements](#testing-requirements)
- [Code Style Guide](#code-style-guide)
- [Commit Message Convention](#commit-message-convention)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Security Issues](#security-issues)
- [Recognition](#recognition)

---

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

**Key principles:**
- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Respect different viewpoints

---

## Getting Started

### Prerequisites

- Python 3.11+
- Docker (optional, but recommended)
- Git
- A GitHub account

### Development Setup

```bash
# 1. Fork the repository on GitHub
# Click the "Fork" button on https://github.com/SHAdd0WTAka/zen-ai-pentest

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/zen-ai-pentest.git
cd zen-ai-pentest

# 3. Add upstream remote
git remote add upstream https://github.com/SHAdd0WTAka/zen-ai-pentest.git

# 4. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 5. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 6. Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# 7. Run tests to verify setup
pytest tests/unit/ -v
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed development setup.

---

## Development Workflow

### 1. Create a Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name

# Branch naming conventions:
# - feature/description    - New features
# - fix/description        - Bug fixes
# - docs/description       - Documentation
# - refactor/description   - Code refactoring
# - test/description       - Test additions/updates
# - security/description   - Security fixes
```

### 2. Make Changes

- Write code following our style guide
- Add/update tests as needed
- Update documentation
- Keep commits focused and atomic

### 3. Test Your Changes

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_your_module.py -v

# Run linting
ruff check .
black --check .

# Run security scan
bandit -r . -ll
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with conventional message
git commit -m "feat: add new vulnerability scanner

- Implement scanner for CVE-2024-XXXX
- Add safety controls for private IP blocking
- Include comprehensive tests

Closes #123"
```

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request via GitHub
# https://github.com/SHAdd0WTAka/zen-ai-pentest/pulls
```

---

## Pull Request Checklist

Before submitting your PR, ensure:

### Code Quality
- [ ] Code follows the project's style guide
- [ ] All tests pass locally
- [ ] New code has test coverage (minimum 80%)
- [ ] Security components have 100% coverage
- [ ] No linting errors (`ruff check .`)
- [ ] Code is formatted (`black .`)
- [ ] Type hints are used where appropriate
- [ ] No new security vulnerabilities (`bandit -r .`)

### Documentation
- [ ] Code includes docstrings
- [ ] README is updated if needed
- [ ] API documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Breaking changes are documented

### Functionality
- [ ] Feature works as described
- [ ] Edge cases are handled
- [ ] Error messages are helpful
- [ ] Backwards compatibility is maintained (or breaking changes are justified)
- [ ] Performance is acceptable

### PR Description
- [ ] Clear title following conventional commits
- [ ] Detailed description of changes
- [ ] Issue references (e.g., "Closes #123")
- [ ] Screenshots/GIFs for UI changes
- [ ] Testing instructions

### Example PR Description

```markdown
## Description
Add support for custom Nuclei templates in scan configuration.

Fixes #456

## Changes
- Add `custom_templates` field to ScanConfig
- Update NucleiIntegration to load custom templates
- Add validation for template file paths
- Update API documentation

## Testing
1. Create a custom template file
2. Submit scan with `custom_templates` parameter
3. Verify template is used during scan

## Checklist
- [x] Tests added for new functionality
- [x] Documentation updated
- [x] All tests pass
- [x] Code follows style guide

## Screenshots
[If applicable]
```

---

## Code Review Process

### For Contributors

1. **Submit PR**: Create a pull request with detailed description
2. **Automated Checks**: CI will run tests and checks automatically
3. **Reviewer Assignment**: Maintainers will be assigned automatically
4. **Address Feedback**: Make requested changes
5. **Approval**: At least one maintainer approval required
6. **Merge**: Maintainer will merge when ready

### For Reviewers

#### Review Checklist
- [ ] Code is correct and efficient
- [ ] Tests cover new functionality
- [ ] Security implications considered
- [ ] Documentation is clear
- [ ] No breaking changes without justification

#### Review Guidelines

**Be Constructive:**
```
✅ "Consider using a dictionary here for O(1) lookup instead of list"
❌ "This is inefficient"
```

**Explain Why:**
```
✅ "This pattern could lead to SQL injection. Consider using parameterized queries instead."
❌ "Security issue"
```

**Suggest Improvements:**
```
✅ "What do you think about extracting this into a separate function?"
❌ "Refactor this"
```

#### Review Timeline
- Initial review: Within 48 hours
- Follow-up reviews: Within 24 hours
- Emergency fixes: Within 4 hours

---

## Testing Requirements

### Coverage Requirements

| Component | Minimum Coverage |
|-----------|------------------|
| Core modules | 85% |
| API endpoints | 80% |
| Tool integrations | 75% |
| Security/guardrails | 100% |
| Database models | 80% |
| Risk engine | 90% |

### Running Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=. --cov-report=html

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Specific test
pytest tests/unit/test_react_agent.py::TestReActAgent::test_reasoning -v

# Exclude slow tests
pytest -m "not slow"
```

### Writing Tests

See [docs/TESTING.md](docs/TESTING.md) for comprehensive testing guide.

```python
# Example test
def test_feature():
    """Test description."""
    # Arrange
    input_data = {"key": "value"}
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_output
```

---

## Code Style Guide

### Python Style

We use:
- **Black**: Code formatting (line length: 127)
- **Ruff**: Linting
- **isort**: Import sorting
- **mypy**: Type checking (optional)

```python
# Line length: 127 characters (not 79)

# Imports: grouped and sorted
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional

# Third-party
import httpx
from fastapi import FastAPI

# Local
from tools.nmap_integration import NmapScanner


# Class naming: PascalCase
class MyClassName:
    """Docstring with description.
    
    Attributes:
        attr1: Description of attr1
        attr2: Description of attr2
    """
    
    # Constants: UPPER_CASE
    MAX_RETRIES = 3
    
    def __init__(self, param1: str, param2: int = 10):
        """Initialize the class.
        
        Args:
            param1: First parameter
            param2: Second parameter (default: 10)
        """
        self.param1 = param1
        self._param2 = param2  # Private
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

---

## Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `test` | Adding or updating tests |
| `refactor` | Code refactoring |
| `perf` | Performance improvements |
| `security` | Security improvements |
| `chore` | Maintenance tasks |
| `ci` | CI/CD changes |
| `style` | Code style changes (formatting) |

### Examples

```bash
# Feature
feat(scans): add support for scheduled scans

# Bug fix
fix(nmap): handle timeout for large networks

# Documentation
docs(api): update authentication examples

# Test
test(guardrails): add tests for IP validation

# Security
security(auth): fix JWT token validation bypass
```

### Detailed Example

```
feat(orchestrator): implement task prioritization

- Add priority queue for task scheduling
- Implement priority inheritance for dependent tasks
- Add API endpoints for priority management
- Update documentation with examples

Breaking Change: Task priority now required in API
tasks must specify priority field

Closes #123
Relates to #456
```

---

## Reporting Bugs

### Before Reporting

1. Search existing issues to avoid duplicates
2. Check if issue is already fixed in latest version
3. Try to isolate the problem

### Bug Report Template

```markdown
**Description**
Clear description of the bug

**To Reproduce**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11.4]
- Zen-AI-Pentest version: [e.g., 3.0.0]
- Installation method: [e.g., Docker, pip]

**Logs**
```
Paste relevant logs here
```

**Screenshots**
If applicable

**Additional Context**
Any other relevant information
```

---

## Suggesting Features

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem

**Describe the solution you'd like**
What you want to happen

**Describe alternatives you've considered**
Other approaches you've thought about

**Additional context**
Mockups, examples, or use cases
```

---

## Security Issues

**DO NOT** report security vulnerabilities in public issues.

Instead:
- Use [GitHub Security Advisories](https://github.com/SHAdd0WTAka/zen-ai-pentest/security/advisories/new)
- Or email: security@zen-ai-pentest.dev

Include:
- Description of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will:
1. Acknowledge receipt within 48 hours
2. Investigate and verify
3. Develop and test fix
4. Coordinate disclosure
5. Credit you (with permission)

See [SECURITY.md](SECURITY.md) for details.

---

## Recognition

Contributors will be recognized in:

- **README.md** - Contributors section
- **Release notes** - Feature acknowledgments
- **CHANGELOG.md** - Change attribution

### Levels of Contribution

| Level | Description | Recognition |
|-------|-------------|-------------|
| First-time | First PR merged | Mention in release notes |
| Contributor | 3+ PRs merged | Listed in CONTRIBUTORS.md |
| Regular | 10+ PRs merged | Listed in README.md |
| Core | Significant features | Listed as core contributor |

---

## Additional Resources

- [Development Guide](docs/DEVELOPMENT.md)
- [Testing Guide](docs/TESTING.md)
- [API Guide](docs/API_GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Project Governance](GOVERNANCE.md)

---

<p align="center">
  <b>Thank you for contributing! 🚀</b><br>
  <sub>Questions? Join our <a href="https://discord.gg/zJZUJwK9AC">Discord</a></sub>
</p>
