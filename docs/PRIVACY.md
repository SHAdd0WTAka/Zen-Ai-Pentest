# Privacy Policy

**Effective Date**: 2026-02-16  
**Last Updated**: 2026-02-16  
**Project**: Zen-AI-Pentest  
**Contact**: security@zen-ai-pentest.dev

---

## 1. Introduction

Zen-AI-Pentest ("we", "us", "our") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our open-source penetration testing framework.

**Important Note**: Zen-AI-Pentest is a security testing tool designed for authorized use only. It should never be used on systems without explicit permission.

---

## 2. Information We Collect

### 2.1 No Personal Data Collection

Zen-AI-Pentest is primarily an open-source tool that runs locally or in your own infrastructure. **We do not collect personal data** through the software itself.

### 2.2 Data Processed by the Tool

When you use Zen-AI-Pentest for authorized security testing:

| Data Type | Purpose | Storage |
|-----------|---------|---------|
| Target IP addresses/URLs | Security scanning | Local only |
| Scan results | Vulnerability reporting | Local/self-hosted |
| Tool output | Analysis and reporting | Local/self-hosted |
| API keys (user-provided) | AI backend integration | User's environment |

### 2.3 GitHub Interactions

When you interact with our GitHub repository:
- Standard GitHub logging applies
- See [GitHub Privacy Statement](https://docs.github.com/en/site-policy/privacy-policies/github-privacy-statement)

---

## 3. How We Use Information

### 3.1 Local Processing

All data processed by Zen-AI-Pentest:
- ✅ Remains on your local machine or infrastructure
- ✅ Is never transmitted to us by default
- ✅ Can be configured for self-hosted operation

### 3.2 Optional Cloud Features

If you enable optional cloud features:

| Feature | Data Shared | Purpose |
|---------|-------------|---------|
| AI Backend | Scan summaries | Vulnerability analysis |
| Error Reporting | Error logs | Bug fixing |
| Update Checks | Version info | Security updates |

---

## 4. Data Storage and Security

### 4.1 Local Storage

All scan data is stored:
- On your local filesystem
- In your configured database (PostgreSQL/SQLite)
- In your Docker volumes (if using Docker)

### 4.2 Security Measures

We implement industry-standard security:
- Encryption at rest (when configured)
- Secure API key handling
- No plaintext password storage
- Audit logging capability

---

## 5. Your Rights (GDPR Compliance)

If you are in the European Economic Area (EEA), you have rights under GDPR:

| Right | How to Exercise |
|-------|-----------------|
| Access | All data is local - you have full access |
| Rectification | Edit local files directly |
| Erasure | Delete local files and database |
| Portability | Export data in JSON/CSV/PDF formats |
| Restriction | Stop using the software |
| Objection | Disable any optional features |

---

## 6. Third-Party Services

### 6.1 Optional Integrations

Zen-AI-Pentest can integrate with third-party services:

| Service | Data Shared | Privacy Policy |
|---------|-------------|----------------|
| OpenAI | Scan summaries | [OpenAI Privacy](https://openai.com/privacy) |
| Anthropic | Scan summaries | [Anthropic Privacy](https://www.anthropic.com/privacy) |
| Kimi AI | Scan summaries | [Kimi Privacy](https://www.moonshot.cn/privacy) |
| Slack | Notifications | [Slack Privacy](https://slack.com/trust/privacy/privacy-policy) |
| Discord | Notifications | [Discord Privacy](https://discord.com/privacy) |
| Telegram | Notifications | [Telegram Privacy](https://telegram.org/privacy) |

### 6.2 No Data Sales

We do not sell, trade, or rent your data to third parties.

---

## 7. Data Retention

### 7.1 Local Data

Retention is controlled entirely by you:
- Scan results: Until manually deleted
- Logs: Configurable retention period
- Database: Under your control

### 7.2 GitHub Data

See [GitHub's data retention policies](https://docs.github.com/en/site-policy/privacy-policies/github-privacy-statement#how-long-we-retain-your-information).

---

## 8. Children's Privacy

Zen-AI-Pentest is a professional security tool and is not intended for use by individuals under 18 years of age.

---

## 9. Changes to This Policy

We may update this Privacy Policy. Changes will be:
- Posted in the repository
- Noted in CHANGELOG.md
- Announced via GitHub releases

---

## 10. Contact Us

For privacy-related questions:

- **Email**: security@zen-ai-pentest.dev
- **GitHub Issues**: [Security tab](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/security)
- **Private Vulnerability Reporting**: [GitHub Advisories](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/security/advisories/new)

---

## 11. Compliance Summary

| Regulation | Compliance Status |
|------------|-------------------|
| GDPR | ✅ Self-hosted = data controller is user |
| CCPA | ✅ No data sales, local processing |
| MIT License | ✅ Open source, transparent |

---

*This privacy policy is maintained by ZenClaw Guardian.*  
*For the latest version, see the main branch of the repository.*
