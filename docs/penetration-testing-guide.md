# External Penetration Testing Guide

This document provides guidelines for conducting external penetration testing on the Zen AI Pentest platform.

## Scope

### In-Scope Assets

| Asset Type | Target | Details |
|------------|--------|---------|
| Web Application | https://pentest.example.com | Main application |
| API | https://pentest.example.com/api/v1 | REST API endpoints |
| API | https://pentest.example.com/api/v2 | REST API endpoints (new) |
| Infrastructure | *.pentest.example.com | Subdomains |

### Out-of-Scope

- Physical security testing
- Social engineering attacks on employees
- DoS/DDoS attacks
- Third-party services (unless explicitly approved)
- Customer data from production (use test accounts only)

## Testing Environment

### Staging Environment

```
URL: https://staging.pentest.example.com
Credentials: Provided upon request
API Keys: Provided upon request
```

### Test Accounts

| Role | Username | Password | Permissions |
|------|----------|----------|-------------|
| Admin | pentest_admin | [REDACTED] | Full access |
| User | pentest_user | [REDACTED] | Standard user |
| Read-Only | pentest_readonly | [REDACTED] | View only |

**Note:** Contact security@zen-pentest.local for test credentials.

## Rules of Engagement

### Allowed Testing Methods

✅ **Permitted:**
- Automated vulnerability scanning (low intensity)
- Manual penetration testing
- Authentication bypass attempts
- Injection testing (SQLi, XSS, Command Injection)
- CSRF/XSRF testing
- Business logic flaw testing
- IDOR (Insecure Direct Object Reference) testing
- Session management testing
- Rate limiting tests (moderate intensity)

❌ **Prohibited:**
- Any form of Denial of Service (DoS/DDoS)
- Brute force attacks against production
- Data exfiltration beyond proof-of-concept
- Modifying/deleting data in production
- Testing on other customers' data
- Social engineering
- Physical security testing
- Resource exhaustion attacks

### Testing Hours

- **Staging:** 24/7 allowed
- **Production:** Business hours only (09:00 - 18:00 UTC)

### Rate Limiting

Be aware of rate limits:
- Anonymous: 30 requests/minute
- Authenticated: 60 requests/minute
- Use provided API keys for higher limits during testing

## Testing Checklist

### Authentication & Authorization

- [ ] Test login functionality
  - [ ] Brute force protection
  - [ ] Account lockout mechanisms
  - [ ] Password reset flow
  - [ ] MFA/2FA if implemented
  
- [ ] Test session management
  - [ ] Session fixation
  - [ ] Session timeout
  - [ ] Concurrent sessions
  - [ ] Logout functionality

- [ ] Test authorization
  - [ ] Horizontal privilege escalation
  - [ ] Vertical privilege escalation
  - [ ] IDOR vulnerabilities

### Input Validation

- [ ] Test for SQL Injection
  - [ ] Error-based SQLi
  - [ ] Time-based blind SQLi
  - [ ] Union-based SQLi

- [ ] Test for XSS
  - [ ] Reflected XSS
  - [ ] Stored XSS
  - [ ] DOM-based XSS

- [ ] Test for Command Injection
- [ ] Test for Path Traversal
- [ ] Test for XML/XXE Injection
- [ ] Test for NoSQL Injection

### API Security

- [ ] Test API authentication
- [ ] Test rate limiting
- [ ] Test for mass assignment
- [ ] Test for insecure direct object references
- [ ] Test for excessive data exposure
- [ ] Test for lack of resources & rate limiting
- [ ] Test for broken function level authorization

### Business Logic

- [ ] Test scan creation limits
- [ ] Test report generation limits
- [ ] Test finding manipulation
- [ ] Test payment/billing flows (if applicable)
- [ ] Test export functionality

### CSRF Protection

- [ ] Test CSRF token validation
- [ ] Test state-changing actions without token
- [ ] Test token reuse
- [ ] Test token expiration

### Other

- [ ] Test CORS configuration
- [ ] Test security headers
- [ ] Test SSL/TLS configuration
- [ ] Test for sensitive data exposure
- [ ] Test for security misconfigurations

## Reporting

### Report Template

```markdown
# Vulnerability Report

## Executive Summary
- Severity: [Critical/High/Medium/Low/Info]
- CVSS Score: [X.X]
- CWE: [CWE-XXX]

## Technical Details

### Vulnerable Endpoint
```
[URL/Endpoint]
```

### Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Proof of Concept
```
[Code/Payload used]
```

### Impact
[Description of potential impact]

### Remediation
[Recommended fix]

### References
- [CWE Link]
- [OWASP Link]
```

### Severity Ratings

| Severity | CVSS Score | Response Time | Bounty Range |
|----------|------------|---------------|--------------|
| Critical | 9.0 - 10.0 | 24 hours | $5,000 - $10,000 |
| High | 7.0 - 8.9 | 48 hours | $1,000 - $5,000 |
| Medium | 4.0 - 6.9 | 1 week | $250 - $1,000 |
| Low | 0.1 - 3.9 | 2 weeks | $100 - $250 |
| Info | N/A | Best effort | Swag/Recognition |

## Tools

### Recommended Tools

- **Web Proxy:** Burp Suite Professional, OWASP ZAP
- **Scanner:** Nuclei, Nessus, OpenVAS
- **API Testing:** Postman, Insomnia
- **SQLi:** SQLMap
- **XSS:** XSStrike, DalFox
- **SSL/TLS:** SSL Labs, testssl.sh
- **Headers:** Security Headers, Mozilla Observatory

### Custom Scripts

We provide custom test scripts for authorized testers:

```bash
# Clone testing scripts
git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest-testing.git

# Run basic tests
python -m pytest tests/security/

# Run API tests
newman run postman/zen-pentest-security.json
```

## Communication

### Reporting Channel

**Email:** security@zen-pentest.local

**Format:**
- Subject: `[PENTEST] Finding: [Brief Description]`
- Encrypt reports with PGP key (available at /security/pgp-key.txt)

### Emergency Contacts

For critical vulnerabilities requiring immediate attention:

- Security Team: +1-XXX-XXX-XXXX
- On-call Engineer: +1-XXX-XXX-XXXX

## Legal

### Safe Harbor

We have implemented a Safe Harbor policy:

```
We will not initiate legal action against researchers who:
1. Make good faith efforts to comply with this policy
2. Report vulnerabilities promptly
3. Do not access/modify data beyond what is necessary
4. Do not exploit vulnerabilities beyond proof-of-concept
```

### Terms

By participating in our penetration testing program, you agree to:
- Keep all findings confidential until fixed
- Not disclose vulnerabilities publicly without permission
- Not access data of other users
- Not degrade our services
- Delete all test data after completion

## Post-Testing

### Certificate of Testing

Upon completion and report submission, testers will receive:
- Certificate of participation
- Letter of recognition (if desired)
- Swag package

### Retesting

After fixes are deployed:
- Retesting is encouraged
- New findings in fixed areas are eligible for bounty
- Coordinate with security team for retest windows

---

**Last Updated:** 2026-02-04  
**Version:** 1.0  
**Contact:** security@zen-pentest.local
