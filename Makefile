# Zen AI Pentest - Makefile
# Quick commands for development tasks

.PHONY: help install install-dev test lint format clean docker-build docker-run docs

# Default target
help:
	@echo "Zen AI Pentest - Available Commands:"
	@echo ""
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make test         - Run all tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make lint         - Run all linters"
	@echo "  make format       - Format code with black and isort"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo "  make docs         - Build documentation"
	@echo "  make demo         - Run CVE demo"
	@echo "  make security     - Run security scans"
	@echo ""

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt 2>/dev/null || pip install pytest pytest-asyncio pytest-cov black isort flake8 bandit safety mypy pre-commit

# Testing
test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=core --cov=agents --cov=backends --cov-report=html --cov-report=term

# Code Quality
lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=15 --max-line-length=127 --statistics --exclude=venv,env,__pycache__,.git,logs,evidence
	bandit -r . -ll || true

format:
	black .
	isort .

format-check:
	black --check --diff .
	isort --check-only --diff .

# Security
security:
	bandit -r . -f json -o bandit-report.json || true
	bandit -r . -ll
	safety check -r requirements.txt || true

# Type Checking
type-check:
	mypy core/ agents/ backends/ modules/ --ignore-missing-imports

# Cleaning
clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .coverage htmlcov/
	rm -rf logs/*.log evidence/*
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Docker
docker-build:
	docker build -t zen-ai-pentest:latest .

docker-run:
	docker run -it --rm -v $(PWD)/logs:/app/logs -v $(PWD)/evidence:/app/evidence zen-ai-pentest:latest

# Documentation
docs:
	cd docs && mkdocs serve

docs-build:
	cd docs && mkdocs build

# Demos
demo:
	python examples/cve_and_ransomware_demo.py

demo-post-scan:
	python examples/post_scan_demo.py

demo-multi-agent:
	python examples/multi_agent_demo.py 2>/dev/null || echo "Demo not available"

# Pre-commit
setup-pre-commit:
	pre-commit install

run-pre-commit:
	pre-commit run --all-files

# Release
release-check:
	python -m build
	twine check dist/*

release-test:
	twine upload --repository testpypi dist/*

release:
	twine upload dist/*

# Development Server
run-api:
	cd api && uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-cli:
	python -m zen_ai_pentest --help

# Git Hooks
install-hooks:
	cp .githooks/pre-commit .git/hooks/pre-commit 2>/dev/null || echo "No custom hooks to install"
	chmod +x .git/hooks/pre-commit 2>/dev/null || true

# CI Helpers
ci-test:
	pytest tests/ -v --tb=short --cov=./ --cov-report=xml

ci-lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	black --check .

ci-security:
	bandit -r . -ll || true
