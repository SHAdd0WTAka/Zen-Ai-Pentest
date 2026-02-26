# Roadmap: 7.91% → 80% Coverage

## Analyse: Wo ist der Code?

```bash
# Top 10 Module nach Zeilenanzahl (ungefähr)
wc -l api/main.py tools/*/ modules/*/ agents/*/ core/*/*.py 2>/dev/null | sort -rn | head -20
```

## Strategie: Funktionale Tests statt nur Imports

### Phase A: API Endpunkte testen (Impact: +15%)
```python
# Mit TestClient direkt Endpunkte testen
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
```

### Phase B: Database CRUD testen (Impact: +10%)
```python
# Mit SQLite In-Memory DB testen
from database.models import Scan, Finding
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///:memory:")
Session = sessionmaker(bind=engine)
```

### Phase C: Tool Execution mocking (Impact: +20%)
```python
# Tools mocken, aber Logik testen
from unittest.mock import patch, MagicMock

@patch("subprocess.run")
def test_nmap_execution(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="...")
    # Teste Tool-Logik
```

## Quick-Win Liste

1. **TestClient für alle API Routes** (~2h, +10% Coverage)
2. **Model-Init Tests für alle DB Models** (~1h, +5% Coverage)
3. **Mock-Tests für Tool-Execution** (~3h, +15% Coverage)
4. **Agent-Methoden Tests** (~2h, +8% Coverage)
5. **Utils-Funktionen Tests** (~1h, +5% Coverage)

## Empfohlener nächster Schritt

Möchtest du:
- **A**: API Endpunkte mit TestClient testen (schnell, +10%)
- **B**: Database Models mit SQLite testen (schnell, +5%)
- **C**: Tool-Mocking für Execution-Tests (mittel, +15%)
- **D**: Eine spezifische Datei/Modul priorisieren?

