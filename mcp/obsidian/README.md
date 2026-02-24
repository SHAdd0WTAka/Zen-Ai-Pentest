# 🔐 Obsidian MCP Server

Ein MCP (Model Context Protocol) Server für sichere Credential-Speicherung in Obsidian.

## 🚀 Schnellstart

### 1. Vault einrichten
```bash
bash mcp/obsidian/setup.sh
```

### 2. Secrets eintragen
```bash
# Editieren
code ~/Documents/Obsidian\ Vault/Secrets/secrets.yaml
```

### 3. VS Codium neu laden
```
Ctrl+Shift+P → Developer: Reload Window
```

## 📁 Struktur

```
~/Documents/Obsidian Vault/Secrets/
├── secrets.yaml      # Hauptdatei mit allen Secrets
├── .gitignore        # Ignoriert alles (Security)
└── README.md         # Dokumentation
```

## 📝 Secrets Format

```yaml
# secrets.yaml
DB_PASSWORD: "super-secure-password"
OPENAI_API_KEY: "sk-..."
GITHUB_TOKEN: "ghp_..."
```

## 🔌 Verwendung im Chat

Sobald eingerichtet, kannst du Secrets abrufen:

```
"Welche Datenbank-Credentials haben wir?"
→ MCP Server liest aus Obsidian Vault

"Setze die GitHub Token Umgebungsvariable"
→ Export GITHUB_TOKEN=ghp_...
```

## 🛡️ Sicherheit

- ✅ Vault ist automatisch `.gitignore`d
- ✅ Lokale Speicherung nur auf deinem Rechner
- ✅ Keine Cloud-Synchronisation der Secrets
- ✅ Alternative zu AWS Secrets Manager für lokale Entwicklung

## 🔄 Backup

Für Backup empfohlen:
1. **Encrypted Git** (git-crypt)
2. **Syncthing** mit verschlüsseltem Ordner
3. **Manuelles Backup** auf verschlüsseltes USB-Laufwerk

## 🐛 Troubleshooting

**Problem:** Vault nicht gefunden  
**Lösung:** `OBSIDIAN_VAULT_PATH` Umgebungsvariable setzen

**Problem:** Secrets werden nicht gelesen  
**Lösung:** Dateiformat prüfen (YAML/JSON/Markdown)
