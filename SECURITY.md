# Security Policy

## Supported Versions

The following versions of Zen-AI-Pentest are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.3.x   | :white_check_mark: |
| 2.2.x   | :white_check_mark: |
| < 2.2   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please do **NOT** open a public issue.

### How to Report

**Preferred Method (Private):**
1. **GitHub Security Advisories**: Use [GitHub's private vulnerability reporting](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/security/advisories/new) - this keeps your report confidential

2. **Security Email**: security@zen-ai-pentest.dev

3. **Direct Contact**: Contact @SHAdd0WTAka directly on GitHub

### What Happens Next

1. **Acknowledgment**: We will acknowledge receipt within 48 hours
2. **Assessment**: We will assess the vulnerability within 1 week
3. **Fix Timeline**: We aim to fix critical vulnerabilities within 30 days
4. **Disclosure**: After fixing, we will publicly disclose the vulnerability with credit to the reporter (unless they prefer anonymity)

### Security Response Team

- @SHAdd0WTAka - Security Lead

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Time

- **Acknowledgment**: Within 48 hours
- **Assessment**: Within 1 week
- **Fix & Release**: Within 30 days (depending on severity)

## Security Best Practices

### For Users

- **Never** run Zen-AI-Pentest against systems you don't own or have explicit permission to test
- Keep your API keys secure (use environment variables, never commit them)
- Regularly update to the latest version
- Review generated reports before sharing

### For Contributors

- All code must pass security scanning (Bandit, CodeQL)
- Dependencies are automatically checked for vulnerabilities
- No hardcoded secrets or credentials
- Input validation is mandatory for all user-facing functions

## Security Features

- Automated dependency scanning via Dependabot
- CodeQL static analysis for Python
- Secret scanning enabled
- Branch protection rules
- Required security reviews for PRs

## Acknowledgments

We thank the following security researchers who have responsibly disclosed vulnerabilities:

- *List will be populated as disclosures are made*

---

Last updated: 2026-02-16
