# TOP 5 Roadmap - Zen-AI Pentest

**Zeitraum:** 2026-02-07 bis 2026-02-14 (7 Tage)  
**Ziel:** Production-Ready v2.5.0

---

## Task 1: Health Check Fix (Tag 1)

### Schritt 1.1: Entrypoint Script erstellen
```bash
# docker-entrypoint.sh erstellen
cat > docker-entrypoint.sh << 'EOF'
#!/bin/bash
set -e
echo "Starting Zen-AI Pentest API..."
exec "$@"
EOF
chmod +x docker-entrypoint.sh
```

### Schritt 1.2: Dockerfile aktualisieren
```dockerfile
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Schritt 1.3: Docker Compose ohne Volume Mount
```yaml
api:
  volumes: []  # Kein Code-Mount mehr
  command: uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## Task 2: Test Coverage 80% (Tag 2-3)

### Schritt 2.1: Test Fixtures
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token"}
```

### Schritt 2.2: API Tests
```python
# tests/test_api.py
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert "services" in response.json()
```

### Schritt 2.3: Coverage Check
```bash
pytest --cov=api --cov=tools --cov-report=term-missing
```

---

## Task 3: WebSocket Echtzeit (Tag 4)

### Schritt 3.1: WebSocket Manager
```python
# api/websocket.py
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.connections = []
    
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)
    
    async def broadcast(self, message: dict):
        for conn in self.connections:
            await conn.send_json(message)
```

### Schritt 3.2: Frontend WebSocket Hook
```javascript
// useWebSocket.js
export function useWebSocket() {
  const [connected, setConnected] = useState(false);
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    ws.onopen = () => setConnected(true);
    return () => ws.close();
  }, []);
  
  return { connected };
}
```

---

## Task 4: Report Templates (Tag 5-6)

### Schritt 4.1: HTML Template
```html
<!-- templates/report.html -->
<h1>Penetration Test Report</h1>
<h2>{{ scan.name }}</h2>
<ul>
  <li>Critical: {{ counts.critical }}</li>
  <li>High: {{ counts.high }}</li>
</ul>
```

### Schritt 4.2: PDF Generator
```python
import pdfkit
from jinja2 import Template

def generate_pdf(scan_id):
    html = template.render(scan=get_scan(scan_id))
    pdfkit.from_string(html, f"report_{scan_id}.pdf")
```

---

## Task 5: HTTPS/TLS (Tag 7)

### Schritt 5.1: SSL Zertifikat
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

### Schritt 5.2: Nginx SSL
```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
}
```

---

## Tagesplan

| Tag | Task | Deliverable |
|-----|------|-------------|
| 1 | Health Check Fix | curl /health zeigt services |
| 2 | Test Setup | pytest --cov funktioniert |
| 3 | Tests schreiben | 80% Coverage erreicht |
| 4 | WebSocket | Echtzeit Updates im Browser |
| 5 | Report Templates | PDF Generierung |
| 6 | HTTPS Setup | SSL Zertifikat läuft |
| 7 | Final Testing | Alle 5 Tasks ✅ |

---

**Starte mit Task 1?**
