# Subdomain Scanning Module

Das Zen AI Pentest Framework bietet umfassende Subdomain-Enumeration-Funktionen mit mehreren Scan-Techniken und Integrationen.

## Übersicht

Das Subdomain-Scanning-Modul bietet:

- **Multi-Technik Enumeration**: DNS, Wordlist, Certificate Transparency
- **Erweiterte Techniken**: Permutation, Zone Transfer, OSINT-Integrationen
- **HTTP/HTTPS Prüfung**: Automatische Verfügbarkeits- und Technologie-Erkennung
- **API-Endpunkte**: RESTful API für Integration
- **Flexible Exportformate**: JSON, TXT, CSV

## Module

### SubdomainScanner (Basis)

```python
from modules.subdomain_scanner import SubdomainScanner

scanner = SubdomainScanner(max_workers=50, timeout=10)
results = await scanner.scan(
    domain="target.com",
    techniques=["dns", "wordlist", "crt"],
    check_http=True
)
```

### AdvancedSubdomainScanner

```python
from modules.subdomain_scanner_advanced import AdvancedSubdomainScanner

scanner = AdvancedSubdomainScanner(max_workers=50)
results = await scanner.scan_advanced(
    domain="target.com",
    techniques=["basic", "permute", "dnsrecords", "virustotal"],
    check_http=True
)
```

## CLI Tools

### Quick Scan

```bash
# Einfacher Scan für target.com
python scan_target_subdomains.py

# Allgemeine Domain
python tools/subdomain_scan.py example.com
```

### Erweiterter Scan

```bash
# Standard-Scan
python tools/subdomain_enum.py target.com

# Erweiterter Scan mit allen Techniken
python tools/subdomain_enum.py target.com --advanced

# Mit VirusTotal Integration
python tools/subdomain_enum.py target.com --advanced --virustotal-key <API_KEY>

# Benutzerdefinierte Wordlist
python tools/subdomain_enum.py target.com -w custom_wordlist.txt

# Export
python tools/subdomain_enum.py target.com -o results.json --format json
```

## API Integration

### REST API Endpunkte

```python
# Scan starten
POST /api/v1/subdomain/scan
{
    "domain": "target.com",
    "techniques": ["dns", "wordlist", "crt"],
    "check_http": true
}

# Scan-Status prüfen
GET /api/v1/subdomain/scan/{job_id}

# Ergebnisse abrufen
GET /api/v1/subdomain/scan/{job_id}/results

# Schneller Scan (synchron)
POST /api/v1/subdomain/quick-scan?domain=target.com
```

## Techniken

### Basis-Techniken

| Technik | Beschreibung |
|---------|--------------|
| `dns` | DNS Enumeration (A, AAAA, CNAME, MX) |
| `wordlist` | Brute-Force mit Wordlist |
| `crt` | Certificate Transparency (crt.sh) |
| `osint` | LLM-gestützte Vorschläge |

### Erweiterte Techniken

| Technik | Beschreibung |
|---------|--------------|
| `axfr` | DNS Zone Transfer Versuch |
| `permute` | Subdomain Permutation/Mangling |
| `virustotal` | VirusTotal API Lookup |
| `alienvault` | AlienVault OTX Integration |
| `bufferover` | BufferOver DNS Data |
| `dnsrecords` | SPF/DMARC/MX Analysis |
| `ipv6` | IPv6 Address Enumeration |

## Beispiele

### Python Integration

```python
import asyncio
from modules.subdomain_scanner import SubdomainScanner

async def main():
    scanner = SubdomainScanner()
    results = await scanner.scan("target.com")
    
    for subdomain, result in results.items():
        if result.is_alive:
            print(f"{subdomain}: HTTP {result.status_code}")

asyncio.run(main())
```

### Integration mit ReconModule

```python
from modules.recon import ReconModule

recon = ReconModule(orchestrator)
results = await recon.comprehensive_subdomain_scan(
    domain="target.com",
    advanced=True
)
```

## Ausgabeformate

### JSON
```json
{
  "subdomain.target.com": {
    "ip_addresses": ["192.168.1.1"],
    "status_code": 200,
    "server_header": "nginx/1.18.0",
    "technologies": ["nginx", "PHP"],
    "is_alive": true
  }
}
```

### CSV
```csv
subdomain,ip_addresses,status_code,server,technologies,is_alive
subdomain.target.com,192.168.1.1,200,nginx,"nginx|PHP",true
```

## Wordlist

Die Standard-Wordlist enthält über 100 gängige Subdomain-Präfixe:

- Infrastruktur: `www`, `mail`, `ftp`, `ns`, `mx`
- Entwicklung: `dev`, `staging`, `test`, `uat`, `qa`
- API: `api`, `rest`, `graphql`, `ws`
- Admin: `admin`, `panel`, `manage`, `dashboard`
- Cloud: `cdn`, `static`, `assets`, `media`

## Performance

- Standard: 50 gleichzeitige Worker
- Timeout: 10 Sekunden pro Request
- Anpassbar über `--workers` und `--timeout` Parameter

## Best Practices

1. **Rate Limiting beachten**: Bei externen APIs (VirusTotal) Rate-Limits beachten
2. **Wordlist anpassen**: Zielspezifische Wordlists verwenden
3. **Wildcard-Filter**: Automatische Wildcard-Erkennung nutzen
4. **HTTP-Check**: Für Live-Hosts immer `--check-http` verwenden

## Fehlerbehebung

### Keine Ergebnisse

- Domain auf Tippfehler prüfen
- Netzwerkverbindung testen
- DNS-Resolver überprüfen

### Zeitüberschreitungen

- Timeout erhöhen: `--timeout 30`
- Worker reduzieren: `--workers 20`
- `--no-http` für schnelleren DNS-only Scan

## Lizenz

Dieses Modul ist Teil des Zen AI Pentest Frameworks und unterliegt dessen Lizenz.
