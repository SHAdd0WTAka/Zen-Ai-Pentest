# Contributing to Zen AI Pentest

Thank you for your interest in contributing to Zen AI Pentest! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/Zen-Ai-Pentest.git`
3. Create a branch: `git checkout -b feature/your-feature-name`

## Development Setup

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run tests with coverage
pytest --cov=modules --cov-report=html
```

## Code Style

- Follow PEP 8 for Python code
- Use type hints where possible
- Write docstrings for all public functions
- Maximum line length: 100 characters

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for >70% code coverage
- Use pytest for unit tests

## Submitting Changes

1. **Commit Messages**: Use conventional commits format
   - `feat:` New feature
   - `fix:` Bug fix
   - `test:` Adding tests
   - `docs:` Documentation changes
   - `refactor:` Code refactoring
   - `security:` Security improvements

2. **Pull Request Process**:
   - Update README.md if needed
   - Update documentation
   - Add tests for new code
   - Ensure CI passes
   - Request review from maintainers

## Reporting Issues

When reporting issues, please include:
- Description of the problem
- Steps to reproduce
- Expected behavior
- Actual behavior
- System information (OS, Python version)
- Relevant logs or screenshots

## Security Issues

Please report security issues privately to the maintainers.
Do NOT open public issues for security vulnerabilities.

## Code of Conduct

- Be respectful and constructive
- Welcome newcomers
- Focus on what's best for the community
- Show empathy towards others

## Questions?

Join our discussions or open an issue!
