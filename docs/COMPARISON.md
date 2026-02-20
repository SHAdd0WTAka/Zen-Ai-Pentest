# Competitive Benchmark Comparison Methodology

This document describes the methodology used for comparing Zen-AI-Pentest against competitor tools including PentestGPT and AutoPentest-DRL.

## Table of Contents

- [Overview](#overview)
- [Test Criteria](#test-criteria)
- [Scoring System](#scoring-system)
- [Test Scenarios](#test-scenarios)
- [Metrics](#metrics)
- [Known Limitations](#known-limitations)
- [Latest Results](#latest-results)
- [Running Comparisons Locally](#running-comparisons-locally)

---

## Overview

The competitive benchmark framework provides standardized, repeatable testing to objectively compare Zen-AI-Pentest against other AI-powered and traditional penetration testing tools.

### Goals

1. **Objective Comparison**: Provide data-driven comparison based on standardized tests
2. **Continuous Improvement**: Track performance over time and identify improvement areas
3. **Transparency**: Open methodology and reproducible results
4. **User Guidance**: Help users select the right tool for their needs

### Competitors Tested

| Tool | Type | License | Focus |
|------|------|---------|-------|
| **PentestGPT** | AI-Powered (LLM) | MIT | Web, API, Network testing with GPT-4 |
| **AutoPentest-DRL** | AI-Powered (DRL) | MIT | Network penetration testing with Deep RL |

---

## Test Criteria

### Selection Criteria

Test cases are selected based on:

1. **Real-World Relevance**: Tests represent actual security scenarios
2. **Coverage Diversity**: Tests span multiple security domains
3. **Difficulty Progression**: Tests range from easy to expert level
4. **Measurable Outcomes**: Results can be objectively evaluated

### Test Categories

| Category | Count | Description |
|----------|-------|-------------|
| Reconnaissance | 1 | Network discovery, enumeration, fingerprinting |
| Vulnerability Scanning | 2 | SQL injection, XSS detection |
| Authentication | 1 | JWT, session management, MFA |
| API Security | 1 | REST API testing, authorization |
| Web Security | 1 | Crawling, depth testing, hidden discovery |
| Network Security | 1 | Port scanning, service detection |
| Cloud Security | 1 | AWS S3, misconfigurations |
| Container Security | 1 | Docker image and runtime scanning |
| Reporting | 1 | Report generation, quality assessment |

### Test Environment

All tests run in isolated Docker environments to ensure:
- **Reproducibility**: Same environment every run
- **Safety**: No impact on production systems
- **Scalability**: Easy to add new test targets
- **Version Control**: Test targets version-pinned

---

## Scoring System

### Primary Metrics (Weighted)

| Metric | Weight | Description | Calculation |
|--------|--------|-------------|-------------|
| **Detection Rate** | 30% | % of expected vulnerabilities found | TP / Expected |
| **Precision** | 20% | Accuracy of findings | TP / (TP + FP) |
| **Recall** | 15% | Coverage of actual vulnerabilities | TP / (TP + FN) |
| **F1 Score** | 15% | Harmonic mean of precision and recall | 2*(P*R)/(P+R) |
| **Speed** | 10% | Scan efficiency | 1 / Duration (normalized) |
| **Cost Efficiency** | 10% | Findings per dollar | Findings / Cost |

### Scoring Formula

```
Overall Score =
    0.30 * Detection Rate +
    0.20 * Precision +
    0.15 * Recall +
    0.15 * F1 Score +
    0.10 * Speed Score +
    0.10 * Cost Efficiency Score
```

### Grade Scale

| Score Range | Grade | Description |
|-------------|-------|-------------|
| 0.90 - 1.00 | A+ | Excellent performance |
| 0.80 - 0.89 | A | Very good performance |
| 0.70 - 0.79 | B | Good performance |
| 0.60 - 0.69 | C | Acceptable performance |
| 0.50 - 0.59 | D | Below average |
| < 0.50 | F | Poor performance |

### Severity Weights

Vulnerabilities are weighted by severity:

| Severity | Weight |
|----------|--------|
| Critical | 4.0 |
| High | 3.0 |
| Medium | 2.0 |
| Low | 1.0 |
| Info | 0.5 |

---

## Test Scenarios

### 1. Reconnaissance (recon_01_basic_scan)

**Objective**: Test network discovery and service enumeration capabilities

**Target**: Multi-service Docker environment with SSH, HTTP, MySQL

**Expected Findings**:
- Service detection (18 services)
- Version identification
- OS fingerprinting

**Success Criteria**:
- ≥80% of services detected
- ≤10% false positive rate

### 2. SQL Injection (vuln_01_sql_injection)

**Objective**: Detect and classify SQL injection vulnerabilities

**Target**: DVWA (Damn Vulnerable Web Application)

**Expected Findings**:
- Classic SQL injection
- Blind SQL injection
- Union-based injection

**Success Criteria**:
- ≥75% detection rate
- Correct injection type identification

### 3. Cross-Site Scripting (vuln_02_xss)

**Objective**: Detect reflected, stored, and DOM-based XSS

**Target**: XSS laboratory application

**Expected Findings**:
- Reflected XSS (HTML, JS, attribute contexts)
- Stored XSS
- DOM-based XSS

**Success Criteria**:
- ≥80% detection rate
- Context-aware payload generation

### 4. JWT Security (auth_01_jwt_test)

**Objective**: Test JWT implementation security analysis

**Target**: JWT laboratory with multiple vulnerabilities

**Expected Findings**:
- Algorithm confusion (none/HS256)
- Weak secrets
- Missing signature validation

**Success Criteria**:
- ≥70% detection rate
- Successful token manipulation

### 5. API Security (api_01_rest_scan)

**Objective**: REST API security assessment

**Target**: crAPI (Completely Ridiculous API)

**Expected Findings**:
- Broken object-level authorization (IDOR)
- Broken authentication
- Mass assignment
- Rate limiting issues

**Success Criteria**:
- ≥70% detection rate
- Authorization flaws identified

### 6. Web Crawling (web_01_crawl_depth)

**Objective**: Test crawling depth and coverage

**Target**: Multi-depth web application with hidden endpoints

**Expected Findings**:
- Deep page discovery (150+ pages)
- Hidden endpoint detection
- JavaScript-rendered content

**Success Criteria**:
- ≥60% coverage at depth 3
- Hidden endpoints discovered

### 7. Network Scanning (net_01_port_scan)

**Objective**: Port scanning and service detection

**Target**: Network with 18 TCP and 6 UDP services

**Expected Findings**:
- All open ports
- Service versions
- OS fingerprint

**Success Criteria**:
- ≥85% port detection
- Version identification

### 8. Cloud Security (cloud_01_s3_check)

**Objective**: AWS S3 bucket security assessment

**Target**: Simulated S3 environment with misconfigurations

**Expected Findings**:
- Public access configurations
- Encryption settings
- Bucket policies

**Success Criteria**:
- ≥80% misconfiguration detection

### 9. Container Security (container_01_docker_scan)

**Objective**: Docker image and runtime security

**Target**: Vulnerable container image

**Expected Findings**:
- Vulnerable packages
- Hardcoded secrets
- Privilege issues
- CIS benchmark violations

**Success Criteria**:
- ≥75% detection rate

### 10. Report Generation (report_01_pdf_gen)

**Objective**: Security report quality assessment

**Target**: Pre-defined findings dataset

**Expected Output**:
- Executive summary
- Technical details
- Remediation guidance
- CVSS scoring

**Success Criteria**:
- All sections complete
- Accurate CVSS scoring

---

## Metrics

### Detection Accuracy

Measures how effectively a tool identifies actual vulnerabilities.

```
True Positives (TP): Correctly identified vulnerabilities
False Positives (FP): Incorrectly flagged as vulnerabilities
False Negatives (FN): Missed vulnerabilities
True Negatives (TN): Correctly identified as safe
```

**Key Metrics**:
- **Precision**: TP / (TP + FP) - How accurate are findings?
- **Recall**: TP / (TP + FN) - How complete is coverage?
- **F1 Score**: 2 * (Precision * Recall) / (Precision + Recall) - Balanced measure

### False Positive Rate

```
FPR = FP / (FP + TN)
```

Lower is better. Security tools should minimize false positives to avoid alert fatigue.

### Scan Speed

Measured in:
- **Time to First Finding**: How quickly vulnerabilities are found
- **Total Scan Duration**: Complete test time
- **Pages/Endpoints per Second**: Efficiency metric

### Report Quality

Evaluated on:
- **Completeness**: All findings documented
- **Accuracy**: Correct severity and technical details
- **Clarity**: Understandable by both technical and executive audiences
- **Actionability**: Clear remediation steps

### Coverage Depth

Measures breadth of testing:
- **Web**: Crawling depth, JavaScript coverage
- **API**: Endpoint coverage, parameter testing
- **Network**: Port coverage, protocol support
- **Cloud**: Service coverage, configuration checks

---

## Known Limitations

### Tool-Specific Limitations

#### PentestGPT

**Strengths**:
- Excellent contextual understanding
- Good at complex attack chains
- Natural language interaction

**Limitations**:
- Requires OpenAI API access (cost)
- Slower due to LLM latency
- May miss subtle vulnerabilities
- Limited CI/CD integration

#### AutoPentest-DRL

**Strengths**:
- Autonomous exploitation
- Attack graph generation
- No API costs after training

**Limitations**:
- Network-focused only
- Limited web application testing
- Requires Metasploit
- Training time for new environments

#### Zen-AI-Pentest

**Strengths**:
- Multi-vector testing
- Integrated reporting
- CI/CD ready

**Limitations**:
- Limited mobile testing
- Cloud provider coverage gaps
- Resource intensive

### Test Limitations

1. **Simulation vs. Reality**: Test environments may not capture all real-world complexity
2. **Version Sensitivity**: Results may vary with tool versions
3. **Configuration Dependency**: Competitor tools may need specific configuration
4. **Resource Constraints**: Full tests require significant compute resources

### Statistical Considerations

- **Sample Size**: 10 test cases provide good coverage but limited statistical power
- **Variance**: Results may vary between runs due to non-deterministic elements
- **Significance**: Differences < 5% may not be statistically significant

---

## Latest Results

### Overall Rankings ({{latest_run_date}})

| Rank | Tool | Overall Score | Grade |
|------|------|---------------|-------|
| 🥇 | {{tool_1}} | {{score_1}} | {{grade_1}} |
| 🥈 | {{tool_2}} | {{score_2}} | {{grade_2}} |
| 🥉 | {{tool_3}} | {{score_3}} | {{grade_3}} |

### Category Winners

| Category | Winner | Score |
|----------|--------|-------|
| Reconnaissance | {{winner}} | {{score}} |
| SQL Injection | {{winner}} | {{score}} |
| XSS | {{winner}} | {{score}} |
| Authentication | {{winner}} | {{score}} |
| API Security | {{winner}} | {{score}} |
| Web Security | {{winner}} | {{score}} |
| Network | {{winner}} | {{score}} |
| Cloud | {{winner}} | {{score}} |
| Container | {{winner}} | {{score}} |
| Reporting | {{winner}} | {{score}} |

### Historical Trend

```
Zen-AI-Pentest Performance:

2024-01: ████████████████████████████████████ 72%
2024-02: ████████████████████████████████████ 74%
2024-03: ████████████████████████████████████ 76%
2024-04: ████████████████████████████████████ 78%
2024-05: █████████████████████████████████████ 80%
2024-06: █████████████████████████████████████ 82%
```

[View Full Historical Data →](../benchmarks/reports/historical/)

---

## Running Comparisons Locally

### Prerequisites

```bash
# Install Zen-AI-Pentest
pip install -e .

# Install benchmark dependencies
pip install pyyaml aiohttp pandas matplotlib

# Optional: Install competitors
pip install pentestgpt  # For PentestGPT
# AutoPentest-DRL requires separate installation
```

### Quick Start

```bash
# Run all benchmarks
python -m benchmarks.run_benchmarks --competitor all

# Run specific competitor
python -m benchmarks.run_benchmarks --competitor pentestgpt

# Run specific test case
python -m benchmarks.run_benchmarks --test-case vuln_01_sql_injection

# Generate comparison report
python scripts/analyze_competitors.py --mode compare --results-dir benchmark_results
```

### Advanced Usage

```python
from benchmarks.comparison import (
    PentestGPTComparator,
    AutoPentestComparator,
    load_test_suite
)

# Load test cases
test_suite = load_test_suite("benchmarks/scenarios/test_cases/")

# Initialize comparators
pentestgpt = PentestGPTComparator()
autopentest = AutoPentestComparator()

# Run comparisons
for test_case in test_suite.test_cases:
    pentestgpt_result = pentestgpt.execute_test(test_case)
    autopentest_result = autopentest.execute_test(test_case)

    # Compare and analyze
    comparison = ComparisonMetrics(
        test_case_id=test_case.id,
        competitor_results=[pentestgpt_result, autopentest_result]
    )

    print(f"Winner for {test_case.id}: {comparison.determine_winner()}")
```

---

## Contributing

To add new test cases or improve the comparison framework:

1. Fork the repository
2. Create a new test case in `benchmarks/scenarios/test_cases/`
3. Add expected findings and success criteria
4. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

---

## References

- [PentestGPT Repository](https://github.com/GeleiDeng/PentestGPT)
- [AutoPentest-DRL Repository](https://github.com/crond-jaist/AutoPentest-DRL)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [NIST SP 800-115](https://csrc.nist.gov/publications/detail/sp/800-115/final)

---

## License

This benchmark framework is released under the MIT License. Competitor tools maintain their respective licenses.

---

*Last Updated: {{last_updated}}*

*For questions or issues, please open an issue on GitHub.*
