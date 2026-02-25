# Security Expectations

This document describes what users can and cannot expect from Zen-AI-Pentest in terms of security.

## What Users CAN Expect

### 1. Safe Tool Execution

- **Private IP Blocking**: By default, tools cannot scan private IP ranges (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
- **Docker Sandboxing**: All tools run in isolated Docker containers with resource limits
- **Timeout Protection**: All scans have automatic timeouts to prevent hanging processes
- **Read-only Filesystems**: Containers run with read-only root filesystems where possible

### 2. Secure Defaults

- **No automatic exploitation**: The framework does not automatically exploit vulnerabilities
- **Explicit confirmation required**: High-risk actions require user confirmation
- **Audit logging**: All actions are logged for accountability
- **Input validation**: All user inputs are validated and sanitized

### 3. Data Protection

- **Local processing**: Scan data is processed locally, not sent to external servers
- **Optional encryption**: Reports can be encrypted with user-provided keys
- **Secure storage**: Credentials are never stored in plain text

### 4. Dependency Security

- **Vulnerability scanning**: All dependencies are regularly scanned (Snyk, pip-audit)
- **Signed commits**: All releases are signed
- **Reproducible builds**: Docker images are built from pinned versions

## What Users CANNOT Expect

### 1. Complete Safety

⚠️ **Warning**: This is a penetration testing framework that executes real security tools.

- **Real network traffic**: Tools generate actual network traffic
- **Potential disruption**: Aggressive scans may disrupt services
- **False negatives**: No guarantee that all vulnerabilities are found
- **Tool limitations**: Individual tools may have their own security issues

### 2. Legal Protection

- **User responsibility**: You are solely responsible for compliance with laws
- **Authorization required**: Only scan systems you own or have explicit permission to test
- **No liability**: The project maintainers are not liable for misuse

### 3. Absolute Security

- **Known limitations**: No software is 100% secure
- **Bug bounty**: We encourage responsible disclosure of vulnerabilities
- **Continuous improvement**: Security is an ongoing process

## Security Responsibilities

### User Responsibilities

1. **Legal compliance**: Ensure you have authorization before scanning
2. **Safe testing**: Use test environments when possible
3. **Report issues**: Report security vulnerabilities responsibly
4. **Keep updated**: Use the latest version for security patches

### Project Responsibilities

1. **Prompt fixes**: Security vulnerabilities will be fixed promptly
2. **Transparent disclosure**: Security issues are disclosed responsibly
3. **Regular audits**: Continuous security monitoring
4. **Clear documentation**: This document and SECURITY.md

## Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

Instead:
1. Create a private security advisory on GitHub
2. Or email: security [at] zen-ai-pentest.dev

We will respond within 48 hours.

## Compliance Standards

- OpenSSF Best Practices (passing)
- CWE/SANS Top 25 awareness
- OWASP guidelines where applicable

---

*Last updated: 2026-02-25*
*See also: [SECURITY.md](SECURITY.md) for vulnerability reporting*
