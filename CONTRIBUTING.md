# Contributing to Zen-AI-Pentest

Thank you for your interest in contributing to Zen-AI-Pentest! This document explains how you can contribute to the project.

## 🚀 How to Contribute

### Reporting Bugs

If you find a bug, please report it by opening an issue on GitHub:

1. Go to [Issues](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/issues)
2. Click "New Issue"
3. Use the bug report template
4. Provide as much detail as possible

Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version)
- Error messages or screenshots

### Suggesting Features

We welcome feature suggestions! To suggest a feature:

1. Open a new issue
2. Label it as "enhancement"
3. Describe the feature and its use case
4. Explain why it would be useful

### Pull Requests

To submit code changes:

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/YOUR_USERNAME/Zen-Ai-Pentest.git`
3. **Create** a feature branch: `git checkout -b feature/amazing-feature`
4. **Make** your changes
5. **Test** your changes: `pytest tests/ -v`
6. **Commit** your changes: `git commit -m 'feat: Add amazing feature'`
7. **Push** to the branch: `git push origin feature/amazing-feature`
8. **Open** a Pull Request against the `main` branch

### Development Setup

```bash
# Clone the repository
git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git
cd Zen-Ai-Pentest

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v
```

See [docs/BUILD.md](docs/BUILD.md) for detailed build instructions.

### Code Standards

We use the following tools for code quality:

- **Ruff**: Linting and formatting (`ruff check .`, `ruff format .`)
- **Black**: Code formatting (line length 127)
- **isort**: Import sorting
- **mypy**: Type checking (optional)
- **Bandit**: Security scanning

All PRs must:
- Follow PEP 8 style guidelines
- Pass all automated tests
- Include tests for new features
- Update documentation as needed
- Pass security scanning (Bandit)

### Testing

All contributions must include appropriate tests. We require:
- **Minimum 80% code coverage** for new features
- **100% coverage** for critical security components
- All tests must pass before PR can be merged

See [docs/TESTING.md](docs/TESTING.md) for detailed testing information.

#### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=. --cov-report=html

# Unit tests only
pytest tests/unit/ -v

# Exclude slow tests
pytest -m "not slow"

# Specific test file
pytest tests/test_react_agent.py -v

# Integration tests
pytest tests/integration/ -v
```

#### Coverage Requirements

| Component | Minimum Coverage |
|-----------|------------------|
| Core modules | 85% |
| API endpoints | 80% |
| Tool integrations | 75% |
| Security/guardrails | 100% |

View coverage reports:
```bash
# HTML report
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=. --cov-report=term-missing
```

## 🛡️ Security

For security issues, please **DO NOT** open a public issue. Instead:

- Use [GitHub Security Advisories](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/security/advisories/new)
- Or email: security@zen-ai-pentest.dev

See [SECURITY.md](SECURITY.md) for details.

## 📝 Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `security:` Security improvements
- `chore:` Maintenance tasks

Example:
```
feat: add nuclei integration

- Add Nuclei tool wrapper
- Implement JSON output parsing
- Add safety controls

Closes #123
```

## 📋 Review Process

1. PRs require at least one maintainer review
2. Automated checks must pass
3. Security scanning must pass
4. The PR description should reference related issues

## 🎉 Recognition

Contributors will be recognized in our README and release notes!

Thank you for helping make Zen-AI-Pentest better! 🦞

## 📚 Additional Resources

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [Build Instructions](docs/BUILD.md)
- [Testing Guide](docs/TESTING.md)
- [Project Governance](GOVERNANCE.md)
