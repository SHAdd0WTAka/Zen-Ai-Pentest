# Secrets Management Architecture

## 🔒 Übersicht: Lokale Sicherheit ohne Cloud-Abhängigkeit

Diese Dokumentation erklärt detailliert, wie das Secrets Management im Zen-AI-Pentest-Projekt funktioniert - **vollständig lokal, transparent und unter deiner Kontrolle**.

> ⚠️ **Wichtiger Hinweis:** Deine Secrets werden **niemals** an externe Server gesendet. Alle Operationen finden ausschließlich auf deinem lokalen System statt.

---

## 🏗️ Systemarchitektur

### Datenfluss-Diagramm

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DEIN LOKALES SYSTEM                                │
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                 │
│  │   VS Codium  │────▶│  MCP Server  │────▶│   Obsidian   │                 │
│  │   (Editor)   │◄────│  (lokal)     │◄────│   Vault      │                 │
│  └──────────────┘     └──────────────┘     └──────────────┘                 │
│         │                      │                      │                      │
│         ▼                      ▼                      ▼                      │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │              CREDENTIAL HELPER PIPELINE                       │           │
│  │  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐   │           │
│  │  │Git Push │───▶│  JWT    │───▶│ GitHub  │───▶│  Temp   │   │           │
│  │  │Trigger  │    │  Auth   │    │   API   │    │  Token  │   │           │
│  │  └─────────┘    └─────────┘    └─────────┘    └─────────┘   │           │
│  │       │                                              │        │           │
│  │       └──────────────────────────────────────────────┘        │           │
│  │                         (1 Stunde gültig)                     │           │
│  └──────────────────────────────────────────────────────────────┘           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   GitHub.com    │
                    │  (nur für Auth) │
                    └─────────────────┘
```

---

## 🔐 Der komplette Ablauf (Schritt für Schritt)

### Phase 1: Secrets Speicherung (Einmalig)

```
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 1: Secrets in Obsidian Vault speichern                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Dein Arbeitsablauf:                                            │
│                                                                 │
│  1. Du erstellst eine Datei:                                    │
│     ~/Documents/Obsidian Vault/Secrets/secrets.yaml             │
│                                                                 │
│  2. Du fügst deine Secrets hinzu:                               │
│     github:                                                     │
│       app_id: "2872904"                                         │
│       private_key: |
│         -----BEGIN RSA PRIVATE KEY-----                         │
│         MIIEpAIBAAKCAQEA...                                     │
│         -----END RSA PRIVATE KEY-----                           │
│                                                                 │
│  3. Obsidian verschlüsselt diese Datei automatisch              │
│     (wenn Vault-Verschlüsselung aktiviert)                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 2: MCP Server liest Secrets (Lokal!)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Was passiert:                                                  │
│                                                                 │
│  • Der MCP Server läuft auf localhost (127.0.0.1)               │
│  • Er liest direkt aus deinem Dateisystem                      │
│  • KEINE Netzwerkverbindung zu externen Servern                │
│  • Secrets bleiben im RAM, werden nicht gespeichert            │
│                                                                 │
│  Code-Ausschnitt (mcp/obsidian/src/index.ts):                   │
│  ```typescript                                                  │
│  const secrets = await readLocalFile(                           │
│    '~/Documents/Obsidian Vault/Secrets/secrets.yaml'            │
│  );                                                             │
│  // Nur lokaler Dateisystem-Zugriff!                           │
│  ```                                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 2: Token-Generierung (Bei jedem Git Push)

```
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 3: JWT Erstellung (Lokal auf deinem Rechner)          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Zeitpunkt: Du führst `git push` aus                           │
│                                                                 │
│  Ablauf:                                                        │
│  ┌─────────┐    ┌──────────────────────────────────────────┐   │
│  │  Git    │───▶│  Credential Helper wird aufgerufen       │   │
│  │  Push   │    │  (github-app-credential-helper.py)       │   │
│  └─────────┘    └──────────────────────────────────────────┘   │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  1. Private Key wird aus ~/Downloads/ gelesen            │   │
│  │  2. JWT Payload wird erstellt:                           │   │
│  │     {                                                    │   │
│  │       "iat": 1708780800,  // Issued at (jetzt)          │   │
│  │       "exp": 1708781400,  // Expires (jetzt + 10min)    │   │
│  │       "iss": "2872904"      // GitHub App ID            │   │
│  │     }                                                    │   │
│  │  3. JWT wird mit RSA-SHA256 signiert                     │   │
│  │  4. JWT wird an GitHub API gesendet                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 4: Installation Token von GitHub (1 Stunde gültig)    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  GitHub antwortet mit temporärem Token:                        │
│                                                                 │
│  ```json                                                        │
│  {                                                              │
│    "token": "ghs_xxxxxxxxxxxx",  // 1 Stunde gültig!           │
│    "expires_at": "2026-02-24T15:30:00Z"                        │
│  }                                                              │
│  ```                                                            │
│                                                                 │
│  ⚠️ WICHTIG: Dieser Token wird NIE gespeichert!                │
│                                                                 │
│  Der Credential Helper gibt ihn direkt an Git weiter:          │
│  ```                                                            │
│  username=x-access-token                                        │
│  password=ghs_xxxxxxxxxxxx                                      │
│  ```                                                            │
│                                                                 │
│  Git verwendet ihn sofort für den Push, dann wird er           │
│  verworfen (cache timeout = 0).                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⏰ Token-Lebenszyklus & Auto-Refresh

### Warum nur 1 Stunde?

```
Zeitachse:
─────────────────────────────────────────────────────────────────►

13:00 Uhr       13:30 Uhr       14:00 Uhr       14:30 Uhr
   │                 │                 │                 │
   ▼                 ▼                 ▼                 ▼
┌──────┐        ┌──────┐        ┌──────┐        ┌──────┐
│ Push │        │ Push │        │ Push │        │ Push │
│Token1│   →    │Token2│   →    │Token3│   →    │Token4│
│(1h)  │        │(1h)  │        │(1h)  │        │(1h)  │
└──────┘        └──────┘        └──────┘        └──────┘
   │                 │                 │                 │
   │            ┌────┴────┐       ┌────┴────┐       ┌────┴────┐
   │            │Token1   │       │Token2   │       │Token3   │
   │            │EXPIRIERT│       │EXPIRIERT│       │EXPIRIERT│
   │            └─────────┘       └─────────┘       └─────────┘
   │
   └─────────────────────────────────────────────────────────────
                    Token wird bei JEDEM Push neu generiert!
                    Alter Token wird ungültig.
```

### Was passiert beim Ablaufen?

| Zeit | Ereignis | Was passiert |
|------|----------|--------------|
| T+0 | `git push` | Neuer Token wird generiert (gültig für 1h) |
| T+30min | `git push` | NEUER Token wird generiert, alter Token läuft in 30min ab |
| T+1h | - | Alter Token ist ungültig, aber du hast bereits einen neuen |
| T+2h | `git push` | Falls längere Pause: Einfach neuen Token generieren |

**Fazit:** Du musst dich nie um Token-Verlängerung kümmern - es passiert automatisch bei jedem Push!

---

## 🛡️ Sicherheitsgarantien

### Was wir garantieren

```
┌─────────────────────────────────────────────────────────────────┐
│  ✅ LOKALE VERARBEITUNG                                         │
├─────────────────────────────────────────────────────────────────┤
│  • Private Key liegt NUR auf deinem Rechner                     │
│  • JWT wird lokal generiert (RSA-Signatur auf deiner CPU)       │
│  • Keine Secrets werden an MCP-Server-Entwickler gesendet       │
│  • Keine Telemetrie, kein Tracking                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ✅ KEINE SPEICHERUNG                                           │
├─────────────────────────────────────────────────────────────────┤
│  • Temporäre Tokens werden nicht auf Festplatte gespeichert     │
│  • Git Credential Cache ist deaktiviert (timeout = 0)           │
│  • Keine Logs mit sensitiven Daten                              │
│  • Memory wird nach Verwendung sofort bereinigt                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ✅ KURZLEBIGE TOKENS                                           │
├─────────────────────────────────────────────────────────────────┤
│  • Tokens sind maximal 1 Stunde gültig                          │
│  • Bei Verlust: Token ist nach 1h wertlos                       │
│  • Vergleich: Personal Access Tokens sind unbefristet gültig    │
│  • Automatische Rotation bei jedem Push                         │
└─────────────────────────────────────────────────────────────────┘
```

### Was wir NICHT können (und warum das gut ist)

```
┌─────────────────────────────────────────────────────────────────┐
│  ❌ WIR KÖNNEN NICHT:                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Auf deine Secrets zugreifen                                │
│     → Private Key ist nur auf deinem System                     │
│     → Wir haben keinen Zugriff auf deinen Obsidian Vault       │
│                                                                 │
│  2. Deine Tokens speichern oder protokollieren                 │
│     → Token wird im Credential Helper nicht gespeichert        │
│     → Keine Datenbank, keine Logs                               │
│                                                                 │
│  3. Deine Code-Änderungen sehen                                 │
│     → GitHub App hat nur Repository-Zugriff                     │
│     → Wir haben keinen Zugriff auf deine Repositories          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Vergleich: Sicherheitsmethoden

| Aspekt | Obsidian Vault + GitHub App | Personal Access Token (PAT) | Fest im Code |
|--------|---------------------------|----------------------------|--------------|
| **Speicherort** | Lokal, verschlüsselt | GitHub-Server (dein Account) | Git-Repository (unsicher!) |
| **Token-Lebensdauer** | 1 Stunde (automatisch erneuert) | Unbegrenzt (bis manuell widerrufen) | Unbegrenzt |
| **Bei Verlust** | Token nach 1h wertlos | Sofortiger Zugriff möglich | Sofortiger Zugriff möglich |
| **Setup-Komplexität** | Einmalig, dann automatisch | Manuell, regelmäßige Erneuerung | Keines (aber gefährlich) |
| **Transparenz** | ✅ Vollständig lokal | ⚠️ GitHub-speichert Token | ❌ Öffentlich sichtbar |
| **Auto-Rotation** | ✅ Ja, bei jedem Push | ❌ Nein | ❌ Nein |

---

## 🚀 Einrichtung (Schritt für Schritt)

### Option 1: Obsidian Vault (Empfohlen)

```bash
# Schritt 1: Setup-Script ausführen
bash mcp/obsidian/setup.sh

# Schritt 2: Secrets eintragen
code ~/Documents/Obsidian\ Vault/Secrets/secrets.yaml

# Schritt 3: VS Codium neu laden
# Ctrl+Shift+P → Developer: Reload Window
```

**Was passiert im Hintergrund:**
1. Script erstellt `Secrets/` Ordner in deinem Obsidian Vault
2. Erstellt `secrets.yaml` Template
3. Konfiguriert MCP Server für lokale Verbindung
4. Richtet Credential Helper für Git ein

### Option 2: Manuelles Setup (Für Experten)

Falls du das Setup selbst durchführen möchtest:

```bash
# 1. Ordner erstellen
mkdir -p ~/Documents/Obsidian\ Vault/Secrets

# 2. Secrets-Datei erstellen
cat > ~/Documents/Obsidian\ Vault/Secrets/secrets.yaml << 'EOF'
github:
  app_id: "2872904"
  private_key_path: ~/Downloads/zen-ai-pentest-kimi-assistant.*.pem
  installation_id: "110359081"
EOF

# 3. Berechtigungen setzen
chmod 600 ~/Documents/Obsidian\ Vault/Secrets/secrets.yaml

# 4. Credential Helper konfigurieren
git config --local credential.helper ~/zen-ai-pentest/github-app-credential-helper.py
```

---

## 🔄 Fehlerbehebung

### Problem: "Token expired"

**Lösung:** Normalerweise nicht nötig - Token wird automatisch erneuert. Falls nicht:

```bash
# Credential Cache leeren
git credential-cache exit

# Erneut versuchen
git push
```

### Problem: "Could not read private key"

**Lösung:** Prüfe den Pfad in `secrets.yaml`:

```bash
# Ist der Private Key vorhanden?
ls -la ~/Downloads/zen-ai-pentest-kimi-assistant.*.pem

# Berechtigungen prüfen
chmod 600 ~/Downloads/zen-ai-pentest-kimi-assistant.*.pem
```

### Problem: "Resource not accessible"

**Lösung:** GitHub App muss Repository-Zugriff haben:

1. Gehe zu: https://github.com/settings/installations
2. Klicke auf "Zen-AI-Pentest-Kimi-Assistant"
3. "Configure" → Füge das Repository hinzu

---

## 📊 Technische Spezifikationen

### Token-Details

| Eigenschaft | Wert | Beschreibung |
|-------------|------|--------------|
| JWT Gültigkeit | 10 Minuten | Zeit für die Authentifizierung bei GitHub |
| Installation Token Gültigkeit | 60 Minuten | Zeit für Git-Operationen |
| Signatur-Algorithmus | RS256 | RSA mit SHA-256 (industriestandard) |
| Key-Länge | 2048 Bit | Sichere RSA-Schlüssellänge |
| Token-Format | `ghs_...` | GitHub Server-to-Server Token |

### Dateistruktur

```
~/Documents/Obsidian Vault/
└── Secrets/
    ├── secrets.yaml          # Deine Secrets (von dir verwaltet)
    ├── secrets.yaml.enc      # Automatisch verschlüsselt (optional)
    └── README.md             # Lokale Dokumentation

~/zen-ai-pentest/
├── github-app-credential-helper.py    # Token-Generierung (lokal)
├── generate_installation_token.py     # Manuelle Token-Generierung
├── setup-github-app-auth.sh           # Einrichtungsscript
└── mcp/
    └── obsidian/
        ├── setup.sh                     # MCP Setup
        └── src/
            └── index.ts                 # MCP Server (nur lokale Verbindung)
```

---

## 🎯 Zusammenfassung für Sicherheitsbewusste

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  🔒 DEINE SECRETS BLEIBEN DEINE SECRETS                         │
│                                                                 │
│  • Keine Cloud-Speicherung                                      │
│  • Keine externe Datenübertragung                              │
│  • Keine Protokollierung durch uns                              │
│  • Open Source: Du kannst den Code prüfen                      │
│                                                                 │
│  📂 Repository: github.com/SHAdd0WTAka/zen-ai-pentest           │
│  📧 Kontakt: Bei Fragen oder Sicherheitsbedenken               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

**Letzte Aktualisierung:** 2026-02-24  
**Dokumentationsversion:** 1.0  
**GitHub App ID:** 2872904  
**MCP Server Version:** 1.0.0 (lokal)
