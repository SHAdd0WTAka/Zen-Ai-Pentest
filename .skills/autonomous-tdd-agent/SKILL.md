---
name: autonomous-tdd-agent
description: |
  Autonomous Test-Driven Development Agent workflow for implementing features without human intervention.

  Use this skill when:
  - Implementing new features from failing tests
  - Fixing broken test suites
  - Creating production-ready code with test coverage
  - Working in TDD mode with minimal guidance

  The skill provides a 6-step autonomous loop: analyze tests → implement → predict → iterate → refactor → summarize.
  Works with any Python project using pytest.
---

# Autonomous TDD Agent

Execute Test-Driven Development autonomously without asking for clarification. Make reasonable assumptions, document them, and proceed through the implementation loop.

## The 6-Step Autonomous Loop

### Step 1: Analyze Failing Tests
- Read the test file completely
- Identify all test classes and methods
- Understand what the tests expect (inputs, outputs, side effects)
- Note required classes, functions, and their signatures
- Document assumptions in comments

### Step 2: Initial Implementation
- Create the minimal implementation to satisfy the tests
- Focus on correctness over elegance
- Include proper imports and exports
- Add basic error handling

### Step 3: Predict Test Results
- Before running, predict which tests will pass/fail
- Document your prediction as a comment
- Run the actual tests
- Compare prediction vs reality

### Step 4: Iterate Until Green
- Fix failing tests one by one
- Document each fix in code comments
- Never skip a failing test
- If stuck, try alternative approaches

### Step 5: Refactor
- Once all tests pass, improve code quality
- Extract functions, add type hints, improve naming
- Ensure no tests break during refactoring
- Remove duplication

### Step 6: Summarize
- Provide summary of changes across iterations
- Document key decisions and assumptions
- Note test coverage achieved

## Workflow Pattern

```python
# 1. READ TESTS
# Read and understand all test requirements

# 2. IMPLEMENT
# Write initial implementation

# 3. TEST & ITERATE
while failing_tests > 0:
    run_tests()
    fix_failures()
    document_fixes()

# 4. REFACTOR
improve_code_quality()
verify_tests_still_pass()

# 5. SUMMARIZE
report_changes()
```

## Rules

1. **Never ask for clarification** - Make reasonable assumptions and document them
2. **Implement both approaches** - If two valid approaches exist, implement both as branches
3. **Minimal changes** - Only change what's necessary to make tests pass
4. **Document everything** - Every assumption, every fix, every iteration
5. **Test everything** - All code paths must be covered

## Example Usage

```
Feature: Implement a rate limiter
Test file: tests/unit/test_rate_limiter.py

[Execute 6-step loop autonomously]
```

## Output Format

After completion, provide:
1. Final implementation code
2. Iteration summary table
3. Test results
4. Key assumptions made

See [references/WORKFLOW_EXAMPLES.md](references/WORKFLOW_EXAMPLES.md) for detailed examples.
