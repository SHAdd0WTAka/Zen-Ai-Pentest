# GitHub Environments Setup

## Sicheres Secret-Management ohne Token-Exposure

Diese Anleitung erklärt, wie du GitHub Environments mit Protection Rules einrichtest, um Secrets sicher zu verwalten - ohne sie jemals im Chat oder lokal zu exponieren.

---

## 🎯 Was ist GitHub Environments?

GitHub Environments ermöglichen:
- **Protection Rules** - Manuelle Genehmigung vor dem Ausführen
- **Required Reviewers** - Mindestens 1 Person muss bestätigen
- **Branch Protection** - Nur bestimmte Branches dürfen deployen
- **Keine lokale Token-Exposure** - Alles läuft in GitHub Actions

---

## 📋 Einrichtung

### Schritt 1: Environment erstellen

1. Gehe zu deinem Repository auf GitHub
2. **Settings** → **Environments** (linke Seitenleiste)
3. Klicke auf **"New environment"**
4. Name: `production`
5. Klicke **"Configure environment"**

### Schritt 2: Protection Rules konfigurieren

#### Required Reviewers
```
☑️ Required reviewers
   Add up to 6 people to review workflow runs
   
   → Füge dich selbst hinzu (@SHAdd0WTAka)
```

#### Deployment Branches
```
☑️ Deployment branches
   Select branches that can deploy to this environment
   
   → Wähle: "Selected branches"
   → Füge hinzu: "main"
```

#### Wait Timer (optional)
```
☑️ Wait timer
   Set a wait time of up to 30 days
   
   → Empfohlen: 0-5 Minuten (für Discord-Updates)
```

### Schritt 3: Secrets hinzufügen

Im Environment `production`:

1. Scrolle zu **"Environment secrets"**
2. Klicke **"Add secret"**
3. Name: `DISCORD_BOT_TOKEN`
4. Value: Dein Discord Bot Token (aus Discord Developer Portal)
5. Klicke **"Add secret"**

---

## 🚀 Verwendung

### Workflow ausführen

1. Gehe zu **Actions** → **"Discord - Fill Channels with Content"**
2. Klicke **"Run workflow"**
3. Wähle Branch: `main`
4. Klicke **"Run workflow"**

### Was passiert dann?

1. Workflow wird gestartet
2. **PAUSE** - Wartet auf deine Genehmigung (Email/Notification)
3. Du erhältst eine Benachrichtigung: "Review pending deployment"
4. Klicke **"Review deployments"**
5. Prüfe die Änderungen
6. Klicke **"Approve and deploy"**
7. Workflow läuft mit den Secrets aus dem Environment

---

## 🔒 Sicherheitsvorteile

| Vorher (lokal) | Nachher (GitHub Environments) |
|----------------|-------------------------------|
| Token im Terminal/Chat | ❌ Token nur in GitHub Secrets |
| Manuelle Eingabe | ❌ Keine menschliche Eingabe nötig |
| Keine Audit-Logs | ✅ Wer hat wann was genehmigt? |
| Keine 2FA | ✅ Required Reviewer = 2FA via GitHub |
| Keine Branch-Kontrolle | ✅ Nur `main` darf deployen |

---

## 📊 Kosten

**KOSTENLOS** - Environments sind Teil von GitHub Free/Pro/Team/Enterprise.

---

## 🎯 Zusammenfassung

Nach der Einrichtung:
1. **Keine Token mehr im Chat** 🎉
2. **Jede Ausführung erfordert deine Genehmigung** 🔐
3. **Audit-Trail für alle Änderungen** 📋
4. **Nur du kannst den Workflow genehmigen** 👤

---

## 📞 Support

Bei Problemen:
- GitHub Docs: https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment
- Oder frage im Discord: https://discord.gg/BSmCqjhY

---

**Letzte Aktualisierung**: 2026-02-11
