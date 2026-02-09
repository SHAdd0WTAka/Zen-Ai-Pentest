# Zen AI Pentest Bug Bounty Program

## Program Overview

We believe in the power of the security community to help us build a more secure product. Our bug bounty program rewards security researchers for finding and responsibly disclosing vulnerabilities.

| Program Details | |
|----------------|---|
| **Program Type** | Public |
| **Scope** | Web Application, APIs, Infrastructure |
| **Reward Range** | $100 - $10,000 |
| **Response Time** | 48 hours (triage) |
| **Payout Time** | 30 days after fix |

## Scope

### In-Scope

| Target | Type | Severity Focus |
|--------|------|----------------|
| https://app.zen-pentest.com | Web Application | All severities |
| https://api.zen-pentest.com/v1 | REST API | All severities |
| https://api.zen-pentest.com/v2 | REST API (new) | All severities |
| *.zen-pentest.com | Subdomains | High/Critical only |

### Out-of-Scope

- Physical security
- Social engineering
- DoS/DDoS attacks
- Third-party services without proof of impact
- Spam/Phishing campaigns
- UAT/Development environments

## Rewards

### Bounty Table

| Severity | CVSS Score | Bounty Range | Example Vulnerabilities |
|----------|------------|--------------|------------------------|
| **Critical** | 9.0 - 10.0 | $5,000 - $10,000 | RCE, SQLi (data extraction), Auth bypass |
| **High** | 7.0 - 8.9 | $1,000 - $5,000 | Stored XSS, IDOR (sensitive data), Privilege escalation |
| **Medium** | 4.0 - 6.9 | $250 - $1,000 | Reflected XSS, CSRF, Information disclosure |
| **Low** | 0.1 - 3.9 | $100 - $250 | Missing headers, Verbose error messages |
| **Informational** | N/A | Swag | Best practices, Recommendations |

### Bonus Rewards

| Achievement | Bonus |
|-------------|-------|
| Complete authentication bypass | +$2,000 |
| Remote Code Execution | +$3,000 |
| Chain 3+ vulnerabilities | +50% bounty |
| High-quality report with POC | +20% bounty |
| First report of new vulnerability class | +$500 |

## Rules

### Do's ✅

- Test within defined scope only
- Use test accounts (request at security@zen-pentest.local)
- Stop testing if you access non-public data
- Report vulnerabilities promptly
- Provide detailed reproduction steps
- Keep findings confidential

### Don'ts ❌

- Do not test on production user data
- Do not perform DoS/DDoS attacks
- Do not use automated scanners at high intensity
- Do not publicly disclose vulnerabilities
- Do not extort or demand ransom
- Do not violate any laws

### Rate Limiting

Our platform has rate limiting:
- Anonymous: 30 req/min
- Authenticated: 60 req/min

**Stay under these limits or request elevated access.**

## Reporting

### How to Report

**Email:** security@zen-pentest.local

**PGP Key:** [Download](https://zen-pentest.com/security/pgp-key.txt)

**Format:**
```
Subject: [BB] [Severity] Brief Vulnerability Description

Body:
1. Target/URL
2. Vulnerability Type
3. Steps to Reproduce
4. Impact
5. Suggested Fix
6. Attachments (POC, Screenshots)
```

### Report Template

```markdown
# Bug Bounty Report

## Researcher
- Name/Handle: [Your name]
- Email: [Your email]
- HackerOne/Bugcrowd: [Profile URL]

## Vulnerability
- Type: [e.g., SQL Injection]
- Severity: [Critical/High/Medium/Low]
- CVSS: [Score with vector]
- CWE: [CWE ID]

## Affected Target
- URL: [Full URL]
- Parameter: [Vulnerable parameter]
- Component: [API endpoint/Feature]

## Description
[Detailed description of the vulnerability]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Proof of Concept
```
[Code, payload, or curl command]
```

## Impact
[What can an attacker do?]

## Suggested Fix
[How to fix the vulnerability]

## Attachments
- [Screenshot/Video POC]
- [Burp/ZAP request file]
```

## Process

### Timeline

```
Day 0:  Report Submitted
Day 1:  Acknowledgment (auto-reply)
Day 2:  Triage Complete (severity assigned)
Week 1: Fix development begins
Week 2-4: Fix deployed
Day 30: Bounty payout
```

### Status Updates

You'll receive updates at these milestones:
1. **Acknowledged** - We received your report
2. **Triaged** - Severity determined
3. **In Progress** - Fix being developed
4. **Fixed** - Fix deployed to production
5. **Paid** - Bounty processed

### Duplicate Reports

If your report is a duplicate:
- You'll be notified
- Original reporter gets bounty
- You get recognition/hall of fame
- Possible small reward for thorough report

## Safe Harbor

We provide legal safe harbor for good faith research:

```
We will not pursue legal action against researchers who:
1. Comply with this policy
2. Make good faith efforts to avoid privacy violations
3. Do not willfully destroy data
4. Do not extort or threaten disclosure
5. Report vulnerabilities promptly
```

**Complete Safe Harbor Policy:** [Link]

## Recognition

### Hall of Fame

Top researchers are recognized on our security page:

| Rank | Researcher | Findings | Total Bounty |
|------|------------|----------|--------------|
| 🥇 | @researcher1 | 12 | $15,500 |
| 🥈 | @researcher2 | 8 | $8,200 |
| 🥉 | @researcher3 | 5 | $4,500 |

### Badges

- **First Blood** - First valid report
- **Critical Hunter** - 3+ critical findings
- **Quality Reporter** - 5+ high-quality reports
- **Top Researcher** - Top 3 by bounty earned

## Exclusions

The following are NOT eligible for bounty:

- Missing security headers without exploitable impact
- Self-XSS without exploitable scenario
- Known vulnerabilities in third-party components
- Vulnerabilities requiring social engineering
- Physical security issues
- Best practice violations without security impact
- Outdated software versions without proof of exploitability

## Tips for Success

### Focus Areas

1. **Authentication Issues**
   - Password reset flaws
   - MFA bypasses
   - JWT vulnerabilities

2. **Authorization Flaws**
   - IDOR (Insecure Direct Object Reference)
   - Privilege escalation
   - Access control bypasses

3. **Injection Vulnerabilities**
   - SQL Injection
   - Command Injection
   - Template Injection

4. **Business Logic**
   - Scan limit bypasses
   - Report generation abuse
   - Finding manipulation

### Tools We Recommend

- Burp Suite Pro
- OWASP ZAP
- Nuclei
- SQLMap
- Postman
- Custom Python scripts

## Contact

| Type | Contact |
|------|---------|
| **Bug Reports** | security@zen-pentest.local |
| **Program Questions** | bugbounty@zen-pentest.local |
| **Status Inquiries** | Include report ID in subject |
| **Emergency** | +1-XXX-XXX-XXXX |

## Program Updates

### Changelog

- **2026-02-04** - Program launched
- **2026-01-15** - Beta testing completed
- **2025-12-01** - Program preparation started

### Planned Updates

- [ ] HackerOne integration (Q2 2026)
- [ ] Bugcrowd integration (Q3 2026)
- [ ] Increased bounty ranges (Q4 2026)

---

**Program Status:** Active  
**Last Modified:** 2026-02-04  
**Version:** 1.0  
**Questions?** bugbounty@zen-pentest.local
