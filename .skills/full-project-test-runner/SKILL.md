---
name: full-project-test-runner
description: |
  Comprehensive test runner for entire Python projects.

  Use when:
  - Running all tests in a project
  - Discovering untested files
  - Generating coverage reports
  - Finding gaps in test coverage
  - Testing all modules systematically

  Works with pytest and generates detailed reports.
---

# Full Project Test Runner

Execute comprehensive testing across entire codebase.

## Workflow

### Step 1: Discover
- Find all Python files in project
- Identify existing test files
- Map modules to their tests

### Step 2: Analyze Coverage
- Run pytest with coverage
- Identify untested modules
- Calculate coverage statistics

### Step 3: Execute All Tests
- Run full test suite
- Capture failures
- Generate reports

### Step 4: Report
- Summary of results
- Failed tests list
- Coverage gaps
- Recommendations

## Usage

```bash
# Test entire project
./scripts/test_project.py /path/to/project

# With coverage report
./scripts/test_project.py /path/to/project --coverage

# Fail fast (stop on first failure)
./scripts/test_project.py /path/to/project --fail-fast
```

## Output

- Test count: X passed, Y failed, Z errors
- Coverage: XX.X%
- Untested files list
- Failed test details

See [references/USAGE.md](references/USAGE.md) for detailed examples.
