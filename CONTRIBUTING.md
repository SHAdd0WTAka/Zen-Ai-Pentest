# Contributing to Zen AI Pentest

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🚀 Quick Start

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit using conventional commits (`git commit -m "feat: add amazing feature"`)
5. Push to your fork
6. Open a Pull Request

## 📝 Commit Message Format

We use [Conventional Commits](https://conventionalcommits.org/):

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks
- `security:` - Security fixes

## 🧪 Testing

Before submitting a PR:

```bash
# Run tests
pytest tests/

# Run linting
ruff check .

# Run type checking
mypy core/ agents/
```

## 🐛 Reporting Issues

When reporting issues, please include:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)

## 🔒 Security

Please report security vulnerabilities privately to the maintainers.

## 📋 Code Review Process

1. All PRs require review before merging
2. CI checks must pass
3. Documentation must be updated if needed

## 🙏 Thank You!

Every contribution helps make Zen AI Pentest better!
