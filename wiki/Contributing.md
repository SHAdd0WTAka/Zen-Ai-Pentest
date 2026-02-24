# Contributing

Danke für dein Interesse an Zen-AI-Pentest! 🎉

## Entwicklungs-Setup

### 1. Repository klonen

```bash
git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.git
cd zen-ai-pentest
```

### 2. Virtuelle Umgebung

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

## Workflow

### 1. Branch erstellen

```bash
git checkout -b feature/my-feature
# oder
git checkout -b fix/my-bugfix
```

### 2. Entwickeln

```bash
# Code schreiben
# Tests schreiben
# Dokumentation aktualisieren
```

### 3. Committen

```bash
git add .
git commit -m "feat: add new feature"
```

**Commit Convention:**
- `feat:` Neue Funktion
- `fix:` Bugfix
- `docs:` Dokumentation
- `style:` Formatierung
- `refactor:` Code-Refactoring
- `test:` Tests
- `chore:` Wartung

### 4. Pushen

```bash
git push origin feature/my-feature
```

### 5. Pull Request

1. Auf GitHub zu "Pull requests" gehen
2. "New pull request" klicken
3. Branch auswählen
4. Template ausfüllen
5. Submit

## Code Style

### Python

- **PEP 8** Einhalten
- **Black** Formatierung
- **Type Hints** verwenden

```python
def my_function(param: str) -> dict:
    """Docstring hier."""
    return {"result": param}
```

### Testing

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=.

# Spezifischer Test
pytest tests/test_my_module.py
```

### Docstrings

```python
def scan_target(target: str, ports: list[int]) -> dict:
    """Scan a target for open ports.

    Args:
        target: The target hostname or IP.
        ports: List of ports to scan.

    Returns:
        Dictionary with scan results.

    Raises:
        ValueError: If target is invalid.
    """
```

## Pull Request Guidelines

### Vor dem Submit

- [ ] Alle Tests passing
- [ ] Pre-commit Hooks passing
- [ ] Dokumentation aktualisiert
- [ ] Changelog aktualisiert
- [ ] Keine Secrets im Code

### PR Template

```markdown
## Beschreibung
Kurze Beschreibung der Änderungen.

## Type of Change
- [ ] Bugfix
- [ ] New Feature
- [ ] Breaking Change
- [ ] Documentation

## Testing
- [ ] Tests added/updated
- [ ] All tests passing

## Checklist
- [ ] Code folgt Style Guide
- [ ] Pre-commit Hooks passing
- [ ] Dokumentation aktualisiert
```

## Code Review

Alle PRs benötigen:
- 1 Review von Maintainer
- Alle Checks passing
- Keine Konflikte

## Security

### Sensitive Data

Niemals committen:
- API Keys
- Passwörter
- Private Keys
- `.env` Dateien

### Report Security Issues

Security-Vulnerabilities bitte NICHT öffentlich melden.

Stattdessen:
1. Security Advisory erstellen
2. Oder: shadd0wtaka@protonmail.com

## Dokumentation

### Wiki aktualisieren

Bei neuen Features:
1. Wiki-Seite erstellen/aktualisieren
2. README.md aktualisieren
3. API-Doku aktualisieren

### Code Comments

```python
# ✅ Gut
# Calculate CVSS score based on impact and exploitability
cvss = calculate_cvss(impact, exploitability)

# ❌ Schlecht
# Calculate CVSS
cvss = calculate_cvss(impact, exploitability)
```

## Community

### Discord

https://discord.gg/BSmCqjhY

### GitHub Discussions

https://github.com/SHAdd0WTAka/zen-ai-pentest/discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Danksagung

Alle Contributors werden in der README.md erwähnt! 🙏
