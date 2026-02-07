# 🛡️ SICHERHEITSHINWEIS - API KEY MANAGEMENT

## ✅ Status: Key Widerrufen

| Aktion | Status | Datum |
|--------|--------|-------|
| Key exposed in Commit | ✅ Identifiziert | 2026-02-07 |
| Key revoked bei Kimi | ✅ Bestätigt | 2026-02-07 |
| Repository bereinigt | ✅ Erledigt | 2026-02-07 |

## 🔐 Sichere API Key Verwaltung

### 1. Key niemals committen

```bash
# Prüfe vor jedem Commit:
git status
grep -r "sk-" . --include="*.py" --include="*.sh" --include="*.md"
```

### 2. .env Datei nutzen

```bash
# .env Datei erstellen (wird nicht committet)
cat > .env << 'EOF'
export KIMI_API_KEY="dein-key-hier"
export DEFAULT_BACKEND="kimi"
export DEFAULT_MODEL="kimi-k2.5"
EOF

# Oder direkt im Terminal:
export KIMI_API_KEY="dein-key-hier"
```

### 3. .gitignore prüfen

```bash
# Sollte enthalten sein:
echo ".env" >> .gitignore
echo "*.env.backup" >> .gitignore
```

### 4. Key Rotation

**Empfohlene Praxis:**
- Keys regelmäßig rotieren (alle 90 Tage)
- Separate Keys für Entwicklung/Produktion
- Keys sofort widerrufen bei Verdacht auf Kompromittierung

## 🚀 Schnellstart (nach Key Revoke)

### Neuen Key generieren
1. Gehe zu: https://platform.moonshot.cn/
2. Logge dich ein
3. Erstelle neuen API Key
4. Kopiere den Key

### Lokal einrichten
```bash
cd ~/Zen-Ai-Pentest

# .env erstellen
cat > .env << 'EOF'
export KIMI_API_KEY="DEIN_NEUER_KEY_HIER"
export DEFAULT_BACKEND="kimi"
export DEFAULT_MODEL="kimi-k2.5"
export LOG_LEVEL="INFO"
EOF

# Testen
source .env
echo "Key gesetzt: ${KIMI_API_KEY:0:10}..."
```

## ✅ Best Practices

1. **Niemals Keys in Code committen**
2. **Niemals Keys in Logs ausgeben**
3. **Niemals Keys im Browser (Web UI) anzeigen**
4. **Keys in Umgebungsvariablen speichern**
5. **Bei Verdacht: Sofort widerrufen und neuen erstellen**

---
*Letzte Aktualisierung: 2026-02-07*  
*Status: Alle Keys bereinigt ✅*
