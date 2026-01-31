# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.x.x   | :white_check_mark: |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**⚠️ IMPORTANT: This is a penetration testing tool. Please read carefully.**

### For Security Bugs in Zen AI Pentest

If you discover a security vulnerability in the Zen AI Pentest framework itself (not targets you're testing):

1. **DO NOT** open a public issue
2. Email security details to: `security@zen-ai-pentest.dev` (or create a private security advisory)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

| Phase | Timeframe |
|-------|-----------|
| Initial Response | 48 hours |
| Vulnerability Assessment | 7 days |
| Fix Implementation | 30 days |
| Public Disclosure | After fix release |

### Safe Harbor

We support responsible disclosure and follow the [GitHub Security Lab Safe Harbor](https://securitylab.github.com/advisories/) policy.

Security researchers who report vulnerabilities in good faith will be:
- Credited in our security advisories (unless they wish to remain anonymous)
- Added to our Hall of Fame
- Given early access to security patches

## Security Best Practices

### For Users

1. **Authorized Testing Only**: Only use this tool on systems you own or have explicit written permission to test.

2. **API Key Management**: 
   - Never commit API keys to version control
   - Use environment variables or secure vaults
   - Rotate keys regularly

3. **Data Handling**:
   - Sanitize all logs before sharing
   - Encrypt evidence files
   - Securely delete data after engagement

4. **Network Security**:
   - Use VPN/proxy for all testing
   - Implement rate limiting
   - Monitor for unexpected outbound connections

### For Contributors

- Never include real API keys or credentials in code
- Never include actual exploited system data
- Always validate inputs to prevent injection
- Always use safe subprocess execution
- Run security scans before submitting PRs

## Security Features

Zen AI Pentest includes several security measures:

- **Input Validation**: All user inputs are validated and sanitized
- **Secure Configuration**: API keys stored in environment variables
- **Rate Limiting**: Built-in protection against API abuse
- **Audit Logging**: All actions are logged for accountability
- **Container Isolation**: Docker support for isolated execution

## Known Security Considerations

1. **Python 3.13 on Windows**: There is a known asyncio issue with Python 3.13 on Windows. Use Python 3.11 or 3.12 for production deployments.

2. **LLM Backend Security**: When using direct API backends (ChatGPT, Claude), ensure:
   - API keys are rotated regularly
   - Usage is monitored for anomalies
   - Rate limits are configured appropriately

3. **CVE Database Updates**: The CVE database should be updated regularly to ensure accurate vulnerability detection.

## Compliance

This tool is designed for authorized security testing. Users are responsible for:
- Obtaining proper authorization before testing
- Complying with all applicable laws and regulations
- Following organizational security policies
- Respecting data privacy requirements (GDPR, CCPA, etc.)

## Security Advisories

View our [GitHub Security Advisories](https://github.com/SHAdd0WTAka/zen-ai-pentest/security/advisories) for:
- Published security vulnerabilities
- CVE assignments
- Security patch notifications

## Contact

- Security Team: security@zen-ai-pentest.dev
- General Issues: [GitHub Issues](https://github.com/SHAdd0WTAka/zen-ai-pentest/issues) (not for security vulnerabilities)
- Discussions: [GitHub Discussions](https://github.com/SHAdd0WTAka/zen-ai-pentest/discussions)
