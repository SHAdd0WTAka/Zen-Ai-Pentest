# User-Based Rate Limiting

Dokumentation für das erweiterte Rate Limiting System mit User-Tiers.

## Übersicht

Das neue Rate Limiting System (`api/rate_limiter_v2.py`) bietet:

- **Tier-basierte Limits**: Verschiedene Limits je nach User-Typ
- **User-Tracking**: Rate Limiting pro Account statt nur pro IP
- **Dual Auth Protection**: IP + User-ID Tracking für Brute Force Schutz
- **Redis Support**: Für verteilte Systeme

## Rate Limit Tiers

| Tier | Requests/Min | Burst | Beschreibung |
|------|--------------|-------|--------------|
| anonymous | 30 | 5 | Nicht authentifizierte User |
| user | 60 | 10 | Standard User |
| premium | 120 | 20 | Premium User |
| admin | 300 | 50 | Administratoren |

### Umgebungsvariablen

```bash
# Rate Limits konfigurieren
RATE_LIMIT_ANON_RPM=30
RATE_LIMIT_USER_RPM=60
RATE_LIMIT_PREMIUM_RPM=120
RATE_LIMIT_ADMIN_RPM=300

# Storage Backend
RATE_LIMIT_STORAGE=memory  # oder 'redis'
REDIS_URL=redis://localhost:6379/0
```

## Verwendung

### Als Decorator

```python
from api.rate_limiter_v2 import rate_limit
from fastapi import Request

# Standard: User-Tier wird automatisch erkannt
@app.get("/api/data")
@rate_limit()
async def get_data(request: Request):
    return {"data": "value"}

# Eigene Limits
@app.get("/api/special")
@rate_limit(requests_per_minute=100, burst_size=20)
async def special_endpoint(request: Request):
    return {"special": "data"}

# Fixer Tier (z.B. für öffentliche Endpoints)
@app.get("/api/public")
@rate_limit(tier="anonymous")
async def public_endpoint(request: Request):
    return {"public": "data"}
```

### Als Middleware

```python
from fastapi import FastAPI
from api.rate_limiter_v2 import UserRateLimitMiddleware

app = FastAPI()
app.add_middleware(UserRateLimitMiddleware)
```

### Auth Rate Limiting

```python
from api.rate_limiter_v2 import check_user_auth_rate_limit

@app.post("/api/login")
async def login(request: Request, credentials: LoginData):
    client_ip = request.client.host
    
    # Prüfe Rate Limit (IP + User-ID)
    check_user_auth_rate_limit(client_ip, credentials.username)
    
    # ... Login Logik ...
```

## Response Headers

Bei erfolgreichen Requests:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Tier: user
```

Bei Rate Limit Überschreitung (HTTP 429):
```
Retry-After: 45
X-RateLimit-Limit: 60
X-RateLimit-Tier: user
```

## User-Tier Erkennung

Das System erkennt User-Tiers über:

1. **JWT Token** (empfohlen): Extrahiert User-ID und Tier aus dem Token
2. **HTTP Header**: `X-User-Tier: premium`
3. **Fallback**: Anonymous wenn nicht authentifiziert

### Integration mit JWT

```python
from api.rate_limiter_v2 import get_user_from_request

def get_user_from_request(request: Request) -> UserContext:
    auth_header = request.headers.get("authorization", "")
    
    if auth_header.startswith("Bearer "):
        token_data = decode_jwt(auth_header[7:])
        return UserContext(
            user_id=token_data["sub"],
            tier=token_data.get("tier", "user"),
            ip_address=request.client.host
        )
    
    return UserContext(tier="anonymous", ip_address=request.client.host)
```

## Auth Rate Limiting

Spezielles Rate Limiting für Login-Endpunkte:

- **5 Versuche pro Minute** pro IP
- **5 Versuche pro Minute** pro User-ID
- **5 Minuten Lockout** bei Überschreitung

```python
from api.rate_limiter_v2 import (
    check_user_auth_rate_limit,
    record_auth_failure,
    record_auth_success
)

@app.post("/api/login")
async def login(request: Request, credentials: LoginData):
    client_ip = request.client.host
    
    # Prüfe Rate Limit
    check_user_auth_rate_limit(client_ip, credentials.username)
    
    # Versuche Login
    user = authenticate(credentials)
    
    if not user:
        record_auth_failure(client_ip, credentials.username)
        raise HTTPException(401, "Invalid credentials")
    
    record_auth_success(client_ip, credentials.username)
    return {"token": create_jwt(user)}
```

## Monitoring

### Statistiken abrufen

```python
from api.rate_limiter_v2 import get_rate_limit_stats

stats = get_rate_limit_stats()
print(stats)
# {
#   "total_buckets": 150,
#   "by_tier": {
#     "anonymous": 100,
#     "user": 45,
#     "premium": 4,
#     "admin": 1
#   }
# }
```

### Logging

```python
import logging

logger = logging.getLogger("api.rate_limiter_v2")
logger.setLevel(logging.INFO)
```

Log-Events:
- `Rate limit exceeded for {tier} user {user_id}`
- `Auth rate limit exceeded: {reason} for {ip}/{user_id}`

## Redis Backend (Produktion)

Für verteilte Systeme mit mehreren API-Servern:

```bash
# Redis konfigurieren
RATE_LIMIT_STORAGE=redis
REDIS_URL=redis://localhost:6379/0
```

Vorteile:
- Geteilte Rate Limits über alle Server
- Persistente Speicherung
- Automatische TTL (1 Stunde)

## Migration von v1

Altes System (`api/rate_limiter.py`):
```python
from api.rate_limiter import rate_limit

@rate_limit(requests_per_minute=60)
async def endpoint(request: Request):
    pass
```

Neues System (`api/rate_limiter_v2.py`):
```python
from api.rate_limiter_v2 import rate_limit

@rate_limit()  # Automatisch basierend auf User-Tier
async def endpoint(request: Request):
    pass
```

## Testing

```bash
# Tests ausführen
pytest tests/test_rate_limiter_v2.py -v

# Mit Coverage
pytest tests/test_rate_limiter_v2.py --cov=api.rate_limiter_v2
```

## Troubleshooting

### "Rate limit exceeded" trotz wenig Requests

- Prüfe den `X-RateLimit-Tier` Header
- User-Tier wird möglicherweise nicht korrekt erkannt
- JWT Token prüfen

### Redis Connection Error

```
WARNING: Redis not available, falling back to memory
```

- Redis läuft nicht oder falsche URL
- Fallback auf In-Memory Storage (nicht für Produktion mit mehreren Servern!)

### Auth Rate Limit zu streng

Umgebungsvariablen anpassen:
```bash
AUTH_RATE_LIMIT=10  # Statt 5
AUTH_LOCKOUT_DURATION=180  # Statt 300 (3 Minuten statt 5)
```

---

**Letztes Update**: 2026-02-04
