# VS Code Setup für Coverage

## Installation

### 1. Extensions installieren

Öffne VS Code und installiere diese Extensions:

```
Ctrl+Shift+X  (oder Cmd+Shift+X auf Mac)
```

Suche und installiere:
- **Coverage Gutters** (ryanluker.vscode-coverage-gutters)
- **Python** (ms-python.python)
- **Python Test Explorer** (LittleFoxTeam.vscode-python-test-adapter)
- **Error Lens** (usernamehw.errorlens)

### 2. Coverage generieren

**Option A: Über Terminal**
```bash
pytest tests/test_working_final.py --cov=core --cov-report=xml
```

**Option B: Über VS Code Task**
```
Ctrl+Shift+P → "Tasks: Run Task" → "Generate Coverage Report"
```

**Option C: Über Makefile**
```bash
make coverage
```

### 3. Coverage Gutters aktivieren

Nach dem Generieren der `coverage.xml`:

```
Ctrl+Shift+P → "Coverage Gutters: Watch"
```

Oder klicke auf das **Watch-Icon** in der Statusleiste unten.

## Farbcodierung

- 🟢 **Grün** - Code ist getestet
- 🔴 **Rot** - Code fehlt Tests
- 🟡 **Gelb** - Code ist teilweise getestet

## Tastenkürzel

| Befehl | Shortcut |
|--------|----------|
| Coverage anzeigen | `Ctrl+Shift+7` |
| Coverage ausblenden | `Ctrl+Shift+8` |
| Tests ausführen | `Ctrl+Shift+T` |
| Tasks anzeigen | `Ctrl+Shift+P` → "Tasks" |

## Troubleshooting

### Coverage wird nicht angezeigt
1. Prüfe ob `coverage.xml` existiert:
   ```bash
   ls -la coverage.xml
   ```

2. Datei manuell laden:
   ```
   Ctrl+Shift+P → "Coverage Gutters: Load"
   ```

3. VS Code neu starten

### Tests werden nicht gefunden
1. Python Interpreter wählen:
   ```
   Ctrl+Shift+P → "Python: Select Interpreter"
   ```

2. Pytest-Pfad prüfen in `.vscode/settings.json`

## Coverage Report öffnen

**HTML Report:**
```bash
# Generiere HTML
pytest tests/test_working_final.py --cov=core --cov-report=html

# Öffne im Browser
python -m webbrowser htmlcov/index.html
```

Oder über VS Code:
```
Ctrl+Shift+P → "Tasks: Run Task" → "Open HTML Coverage"
```
