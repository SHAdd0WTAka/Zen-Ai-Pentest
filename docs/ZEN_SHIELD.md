# Zen Shield - Security Sanitization Module

Zen Shield ist eine Schutzschicht für Zen AI Pentest, die verhindert, dass sensible Daten (API-Keys, Tokens, interne IPs) an externe LLMs (GPT-4, Claude) geleakt werden.

## 🛡️ Was macht Zen Shield?

| Feature | Beschreibung | Nutzen |
|---------|--------------|--------|
| **Secret Masking** | Automatische Erkennung und Maskierung von Secrets | Compliance, keine Leaks |
| **Kostenreduktion** | 90% Noise-Reduktion vor GPT-4 | Sparen bei API-Kosten |
| **Prompt Injection Schutz** | Erkennung von Jailbreak-Versuchen | Sicherheit |
| **Lokale Verarbeitung** | Kleines LLM (Phi-3) läuft lokal | Datenschutz |
| **Fallback** | Regex-basiert bei LLM-Ausfall | Keine Single-Point-of-Failure |

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    Zen AI Pentest                           │
├─────────────────────────────────────────────────────────────┤
│  ZenOrchestrator                                            │
│  └─> ShieldedOrchestrator (neu)                            │
│       ├─> Zen Shield (lokal oder Service)                  │
│       └─> Big LLM (GPT-4/Claude)                           │
├─────────────────────────────────────────────────────────────┤
│  Zen Shield Pipeline:                                       │
│  1. Prompt Injection Detection                            │
│  2. Secret Scrubbing (Regex, immer aktiv)                 │
│  3. Context Compression (Phi-3 LLM)                       │
│  4. Risk Assessment                                       │
└─────────────────────────────────────────────────────────────┘
         │
         ▼ Falls Circuit Breaker offen
┌─────────────────────────────────────────────────────────────┐
│  Fallback Mode (nur Regex)                                  │
│  - Langsamer, aber deterministisch sicher                   │
│  - Keine externen Calls                                     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Option 1: Als Docker Service (empfohlen)

```bash
# Füge zu docker-compose.pentest.yml hinzu:
docker-compose -f docker-compose.pentest.yml -f docker-compose.shield.yml up -d
```

### Option 2: Lokale Installation

```bash
# Installation
pip install -r zen_shield/requirements.txt

# Server starten
python -m zen_shield.server
# -> läuft auf http://localhost:9000
```

### Option 3: Kleines LLM lokal (optional)

```bash
# Phi-3 Mini für Kompression
docker build -f zen_shield/Dockerfile.phi3 -t zen-phi3 .
docker run -p 8001:8001 zen-phi3
```

## 📖 Verwendung

### Python SDK

```python
from zen_shield import ZenSanitizer, SanitizerRequest

# Initialisieren
sanitizer = ZenSanitizer(
    small_llm_endpoint="http://localhost:8001",
    enable_compression=True
)

# Raw Tool Output
raw_nmap = """
Starting Nmap 7.94 ( https://nmap.org )
Nmap scan report for 192.168.1.1
Host is up (0.0032s latency).
PORT    STATE SERVICE
22/tcp  open  ssh
80/tcp  open  http

Found API Key: sk-live-abc123xyz789
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
"""

# Sanitization
request = SanitizerRequest(
    raw_data=raw_nmap,
    source_tool="nmap",
    intent="analyze"
)

response = await sanitizer.process(request)

print(response.cleaned_data)
# Output: API Key und Token sind maskiert
# [REDACTED_a1b2c3d4_API_KEY]
# [REDACTED_e5f6g7h8_BEARER_TOKEN]

print(response.safe_to_send)  # True
print(response.tokens_saved)  # ~500 Tokens gespart
```

### Integration mit ZenOrchestrator

```python
from core.shield_integration import ShieldedOrchestrator

async with ShieldedOrchestrator() as orchestrator:
    # Automatische Sanitization!
    result = await orchestrator.analyze_tool_output(
        raw_output=nmap_result,
        source_tool="nmap",
        intent="analyze"
    )

    # Nur bereinigte Daten gehen an GPT-4
    print(result["analysis"])
    print(result["sanitization"]["tokens_saved"])
```

### API Endpoints

```bash
# Health Check
curl http://localhost:9000/health

# Sanitization
curl -X POST http://localhost:9000/sanitize \
  -H "Content-Type: application/json" \
  -d '{
    "raw_data": "Found API key: sk-abc123...",
    "source_tool": "nmap",
    "intent": "analyze"
  }'

# Response:
{
  "cleaned_data": "Found API key: [REDACTED_..._API_KEY]",
  "redactions": [...],
  "safe_to_send": true,
  "compression_ratio": 0.3,
  "tokens_saved": 450
}
```

## 🔍 Secret-Erkennung

Zen Shield erkennt automatisch:

| Typ | Beispiel |
|-----|----------|
| API Keys | `sk-abc123...`, `api_key=xyz789` |
| Bearer Tokens | `Bearer eyJ0eXAiOiJKV1Q...` |
| JWT Tokens | Komplette JWT Struktur |
| AWS Keys | `AKIAIOSFODNN7EXAMPLE` |
| Private Keys | PEM, OpenSSH, RSA |
| DB Connections | `mongodb://user:pass@host` |
| Interne IPs | RFC 1918 (10.x, 172.16-31.x, 192.168.x) |
| Session Cookies | `session=abc123...` |
| Credit Cards | `1234-5678-9012-3456` |
| GitHub Tokens | `ghp_xxxxxxxxxxxx` |
| Slack Tokens | `xoxb-xxxxxxxxxxxx` |

## 💰 Kosteneinsparungen

Beispiel: Nmap Scan mit 10.000 Zeilen Output

| Schritt | Tokens | Kosten (GPT-4) |
|---------|--------|----------------|
| Rohdaten | 2.500 | $0.075 |
| Nach Zen Shield | 250 | $0.0075 |
| **Einsparung** | **90%** | **$0.0675 (90%)** |

Bei 100 Scans/Tag: **~$200/Monat gespart**

## 🔄 Circuit Breaker

Wenn das kleine LLM ausfällt:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   CLOSED    │ --> │  HALF_OPEN  │ --> │    OPEN     │
│  (Normal)   │     │  (Testing)  │     │ (Fallback)  │
└─────────────┘     └─────────────┘     └─────────────┘
       ▲                                      │
       └──────────────────────────────────────┘
              (Nach 60s Recovery)
```

Im Fallback-Modus:
- Nur Regex-basierte Erkennung (deterministisch)
- Einfache Heuristik für Kompression
- Langsamer, aber 100% sicher

## 🐳 Docker Compose Integration

```yaml
# docker-compose.shield.yml
version: '3.8'

services:
  # Zen Shield Sanitizer Service
  zen-shield:
    build: ./zen_shield
    container_name: zen-shield
    ports:
      - "9000:9000"
    environment:
      - SMALL_LLM_URL=http://zen-phi3:8001
    networks:
      - pentest-network
      - internal-network
    restart: unless-stopped

  # Optional: Small LLM for compression
  zen-phi3:
    build:
      context: ./zen_shield
      dockerfile: Dockerfile.phi3
    container_name: zen-phi3
    ports:
      - "8001:8001"
    networks:
      - internal-network
    restart: unless-stopped
    profiles:
      - local-llm
```

Starten:
```bash
# Mit lokalem LLM
docker-compose -f docker-compose.pentest.yml \
  -f docker-compose.shield.yml \
  --profile local-llm up -d

# Ohne lokales LLM (nur Regex-Fallback)
docker-compose -f docker-compose.pentest.yml \
  -f docker-compose.shield.yml up -d
```

## 🧪 Testing

```bash
# Unit Tests
cd zen_shield
pytest tests/ -v

# Integration Test
python examples/shield_demo.py

# Load Test
python -m locust -f load_test.py
```

## 📊 Monitoring

```bash
# Circuit Breaker Status
curl http://localhost:9000/stats

# Health Check
curl http://localhost:9000/health
{
  "status": "healthy",
  "small_llm_available": true,
  "circuit_breaker_state": "closed"
}
```

## 🔐 Sicherheitsaspekte

1. **Kein Data-Leakage**: Alle Secrets werden lokal maskiert
2. **Deterministisch**: Regex-Patterns sind reproduzierbar
3. **Keine External Calls** im Fallback-Modus
4. **Audit Trail**: Alle Redactions werden geloggt

## 🤝 Integration in bestehende Workflows

### CI/CD Pipeline

```yaml
# .github/workflows/secure-scan.yml
- name: Run Secure Scan
  run: |
    docker-compose up -d zen-shield
    python scan.py | \
      curl -X POST http://localhost:9000/sanitize \
        -H "Content-Type: application/json" \
        -d @- > cleaned_results.json
    # cleaned_results.json ist sicher für GPT-4
```

### Mit bestimmten Tools

```python
# Nur für sensible Tools
if tool in ["burp", "nuclei", "nmap"]:
    use_shield = True
else:
    use_shield = False

results = await orchestrator.comprehensive_scan_with_shield(
    target="example.com",
    tools=["nmap", "nuclei"],
    use_shield=use_shield
)
```

## 📝 License

MIT License - Teil von Zen AI Pentest
