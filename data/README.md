# Zen AI Pentest - Data Directory

This directory contains databases, templates, and payload collections for Zen AI Pentest.

## 📁 Structure

```
data/
├── cve_db/
│   └── ransomware_cves.json    # Ransomware & CVE database
├── nuclei_templates/            # Custom Nuclei templates
└── payloads/                    # Additional payload collections
```

## 🗄️ CVE Database

### Ransomware Entries

The `ransomware_cves.json` contains comprehensive information about major ransomware campaigns:

| Ransomware | First Seen | Decryptable | Associated CVEs |
|------------|------------|-------------|-----------------|
| **NotPetya** | 2017-06-27 | ❌ No | CVE-2017-0144/45/46/47/48 |
| **WannaCry** | 2017-05-12 | ❌ No | CVE-2017-0144 |
| **Bad Rabbit** | 2017-10-24 | ❌ No | - |
| **Ryuk** | 2018-08 | ❌ No | - |
| **Sodinokibi/REvil** | 2019-04 | ✅ Yes | CVE-2019-2725, CVE-2019-11510, CVE-2018-13379 |
| **DarkSide** | 2020-08 | ✅ Yes | - |
| **Original Petya** | 2016-03 | ✅ Yes | - |

### Critical CVEs

Key vulnerabilities frequently exploited by ransomware:

- **CVE-2017-0144** (EternalBlue) - SMB RCE, CVSS 8.1
- **CVE-2021-44228** (Log4Shell) - Log4j RCE, CVSS 10.0
- **CVE-2019-11510** - Pulse Secure VPN, CVSS 10.0
- **CVE-2018-13379** - Fortinet VPN, CVSS 9.8
- **CVE-2020-1472** (Zerologon) - Netlogon, CVSS 10.0
- **CVE-2021-26855** (ProxyLogon) - Exchange, CVSS 9.8

## 🎯 SQL Injection Payloads

The SQL Injection Database includes payloads for:

### Database Types
- MySQL/MariaDB
- PostgreSQL
- Microsoft SQL Server
- Oracle
- SQLite
- MongoDB (NoSQL)

### Techniques
- Error-Based Injection
- Union-Based Injection
- Boolean-Based Blind
- Time-Based Blind
- Stacked Queries
- Out-of-Band

### Payload Examples

#### MySQL Error-Based
```sql
' AND 1=CONVERT(int,@@version)--
```

#### PostgreSQL Time-Based
```sql
'; SELECT pg_sleep(5)--
```

#### MSSQL Command Execution
```sql
'; EXEC xp_cmdshell 'whoami'--
```

#### MongoDB NoSQL
```json
{"username": {"$ne": null}, "password": {"$ne": null}}
```

## 🔍 Nuclei Templates

### Template Categories

1. **CVE Templates** - Known vulnerability checks
2. **Misconfiguration** - Security misconfigurations
3. **Exposures** - Sensitive information exposure
4. **Technologies** - Technology detection
5. **Ransomware-Related** - Checks for ransomware indicators

### Using Templates

```python
from modules.nuclei_integration import NucleiIntegration

nuclei = NucleiIntegration(orchestrator)

# Run scan with specific templates
findings = await nuclei.scan_target(
    target="example.com",
    severity=["critical", "high"],
    tags=["cve", "ransomware"]
)
```

## 📊 Statistics

- **Ransomware Families**: 7+ major campaigns
- **CVEs Tracked**: 20+ critical vulnerabilities
- **SQL Payloads**: 50+ across 6 database types
- **WAF Bypass Variants**: 7+ encoding methods

## ⚠️ Usage Warning

The data in this directory is for authorized security testing only. Many payloads and exploits can cause damage if used improperly.

**Always ensure you have written permission before testing any systems.**

## 🔄 Updates

This database is regularly updated with:
- New ransomware campaigns
- Latest CVEs
- Emerging exploit techniques
- IOC updates

Last updated: 2024-01-29
