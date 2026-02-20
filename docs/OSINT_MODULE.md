# OSINT Module Documentation

## Overview

The Open Source Intelligence (OSINT) Module provides automated intelligence gathering capabilities for penetration testing. It collects and analyzes publicly available information from various sources.

## Features

- **Email Harvesting** - Find email addresses from search engines, PGP keys, and code repositories
- **Domain Reconnaissance** - Enumerate subdomains, analyze DNS records, detect technologies
- **Social Media Intelligence** - Investigate usernames across platforms
- **Data Breach Monitoring** - Check if credentials appear in known breaches
- **IP Intelligence** - Geolocation, ISP detection, proxy/VPN detection

## API Endpoints

### Email Harvesting

```bash
POST /api/v1/osint/emails/harvest
Authorization: Bearer <token>
Content-Type: application/json

{
  "domain": "example.com",
  "sources": ["google", "bing", "pgp"]
}
```

Response:
```json
{
  "emails": [
    {
      "email": "admin@example.com",
      "source": "pgp",
      "confidence": 9,
      "metadata": {"pgp_server": "keys.openpgp.org"}
    }
  ]
}
```

### Domain Reconnaissance

```bash
POST /api/v1/osint/domain/recon
Authorization: Bearer <token>
Content-Type: application/json

{
  "domain": "example.com",
  "enumerate_subdomains": true,
  "detect_tech": true
}
```

Response:
```json
{
  "domain": "example.com",
  "registrar": "Example Registrar, LLC",
  "creation_date": "2020-01-01",
  "subdomains": ["www.example.com", "mail.example.com"],
  "technologies": ["Apache", "PHP", "WordPress"],
  "ip_addresses": ["192.0.2.1"],
  "mx_records": ["mail.example.com"]
}
```

### Breach Check

```bash
POST /api/v1/osint/breach/check
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "user@example.com"
}
```

Response:
```json
{
  "email": "user@example.com",
  "breached": true,
  "breach_sources": ["LinkedIn 2012", "Adobe 2013"],
  "recommendations": [
    "Change password immediately",
    "Enable 2FA on all accounts"
  ]
}
```

## Python SDK Usage

### Basic Usage

```python
from modules.osint import OSINTModule

async with OSINTModule() as osint:
    # Harvest emails
    emails = await osint.harvest_emails("example.com")

    # Domain recon
    info = await osint.recon_domain("example.com")

    # Check breach
    profile = await osint.check_breach("user@example.com")
```

### Email Harvesting

```python
from modules.osint import harvest_emails

emails = await harvest_emails("example.com")
print(f"Found: {emails}")
```

### Domain Enumeration

```python
from modules.osint import enumerate_subdomains

subdomains = await enumerate_subdomains("example.com")
for sub in subdomains:
    print(f"Found: {sub}")
```

### Username Investigation

```python
async with OSINTModule() as osint:
    results = await osint.investigate_username("johndoe")

    for platform, data in results.items():
        if data["exists"]:
            print(f"Found on {platform}: {data['url']}")
```

## Sources

### Email Harvesting Sources

| Source | Description | Rate Limit |
|--------|-------------|------------|
| Google | Search engine dorks | 100/day |
| Bing | Microsoft search | 100/day |
| PGP | PGP key servers | Unlimited |
| GitHub | Code repositories | 60/hour |

### Domain Sources

- Certificate Transparency logs (crt.sh)
- DNS enumeration
- WHOIS records
- Web technology detection (Wappalyzer-style)

### Breach Sources

- Have I Been Pwned (requires API key)
- Known breach databases
- Leaked credential collections

## Rate Limiting

OSINT operations are rate-limited to prevent abuse:

| Operation | Limit | Window |
|-----------|-------|--------|
| Email Harvest | 50 | 24h |
| Domain Recon | 100 | 24h |
| Breach Check | 200 | 24h |
| Username Lookup | 100 | 24h |

## Ethical Considerations

⚠️ **Important**: OSINT gathering should only be performed:
- On domains you own
- With explicit written permission
- For legitimate security assessments
- In compliance with local laws

## Demo

Run the interactive demo:

```bash
python examples/osint_demo.py --domain example.com
python examples/osint_demo.py --email user@example.com
python examples/osint_demo.py --username johndoe
python examples/osint_demo.py --full example.com
```

## Configuration

Environment variables:

```bash
# Optional: HIBP API key for breach checking
HIBP_API_KEY=your_api_key

# Optional: Proxy for requests
OSINT_PROXY=http://proxy:8080

# Rate limiting
OSINT_RATE_LIMIT=100
```

## Output Formats

### JSON Report

```json
{
  "target": "example.com",
  "generated_at": "2026-01-30T12:00:00",
  "summary": {
    "total_findings": 42,
    "by_type": {
      "email": 15,
      "subdomain": 20,
      "technology": 7
    }
  },
  "findings": [...]
}
```

## Integration with Other Modules

OSINT results can feed into other modules:

```python
# Find subdomains, then scan them
from modules.osint import OSINTModule
from modules.vuln_scanner import VulnScannerModule

async with OSINTModule() as osint:
    info = await osint.recon_domain("example.com")

    scanner = VulnScannerModule()
    for subdomain in info.subdomains:
        await scanner.scan(subdomain)
```

## Troubleshooting

### No emails found
- Try different sources
- Check if domain has public email exposure
- Some domains intentionally hide email addresses

### Rate limiting
- Wait for quota reset
- Use different IP/proxy
- Upgrade API limits

### False positives
- Always verify findings manually
- Cross-reference multiple sources
- Check confidence scores

## References

- [OSINT Framework](https://osintframework.com/)
- [OSINT Curious](https://www.osintcurious.org/)
- [Have I Been Pwned](https://haveibeenpwned.com/)

---

*Use responsibly and ethically*
