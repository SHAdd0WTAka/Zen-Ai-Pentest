# 🏆 Zen-AI-Pentest Bug Bounty Program

> **Kein Cash - aber Ruhm, Punkte und Belohnungen!** 🎯

---

## 📋 Programm-Übersicht

| Detail | Information |
|--------|-------------|
| **Programm-Name** | Zen-AI-Bounty |
| **Season-Dauer** | 3 Monate |
| **Belohnungstyp** | Punkte + Leaderboard + Special Rewards |
| **Ziel** | Community-Engagement & Code-Qualität |

---

## 🎯 Bug-Klassifizierung (CVSS-ähnliches Rating)

### Severity Levels & Punktewerte

| Severity | CVSS Score | Punkte | Beschreibung |
|----------|------------|--------|--------------|
| 🔴 **Critical** | 9.0 - 10.0 | 1000 | RCE, Auth-Bypass, Data Breach |
| 🟠 **High** | 7.0 - 8.9 | 500 | SQL Injection, Privilege Escalation |
| 🟡 **Medium** | 4.0 - 6.9 | 200 | XSS, CSRF, Info Disclosure |
| 🟢 **Low** | 0.1 - 3.9 | 50 | Best Practices, Minor Issues |
| 💡 **Enhancement** | N/A | 25 | Feature Requests, Optimierungen |

### Bonus-Punkte

| Kategorie | Bonus | Bedingung |
|-----------|-------|-----------|
| 🎯 **First Blood** | +50% | Erster Finder eines Bug-Typs |
| 📝 **PoC Quality** | +25% | Ausgezeichneter Proof of Concept |
| 🔧 **Fix Provided** | +100% | Inklusive Patch/PR |
| 🎓 **Documentation** | +50% | Mit Dokumentation/Hilfe |

---

## 🏅 Leaderboard & Seasons

### Saison-Struktur

```
Season 1: Januar - März
Season 2: April - Juni
Season 3: Juli - September
Season 4: Oktober - Dezember
```

### Ranglisten-Kategorien

1. **🏆 Overall Champion** - Meiste Punkte gesamt
2. **🔥 Critical Hunter** - Meiste Critical/High Bugs
3. **🛠️ Fix Master** - Meiste bereitgestellte Fixes
4. **💡 Innovation Award** - Beste Feature-Vorschläge
5. **🎯 Consistency** - Aktivität über die gesamte Season

---

## 🎁 Belohnungen (Top 3 pro Season)

### 🥇 1. Platz
- **Titel:** "Zen-AI Security Champion [Season X]"
- **Rolle:** @Security Champion (Discord)
- **Reward:**
  - Exklusiver Badge im Repo
  - Feature in Release Notes
  - 1-on-1 Session mit Core Team
  - Limited Edition Merch (T-Shirt/Hoodie)
  - Early Access zu neuen Features

### 🥈 2. Platz
- **Titel:** "Elite Contributor"
- **Rolle:** @Elite Contributor (Discord)
- **Reward:**
  - Badge im Repo
  - Mention in Release Notes
  - Beta Access
  - Sticker Pack

### 🥉 3. Platz
- **Titel:** "Rising Star"
- **Rolle:** @Rising Star (Discord)
- **Reward:**
  - Badge im Repo
  - Discord Nitro (1 Monat) - sponsored
  - Special Thanks in Release

### 🎖️ Hall of Fame
Alle Top 10 pro Season kommen in die **Hall of Fame**:
- Permanente Erwähnung in README
- Dedicated Wall of Fame
- Lifetime Discord Role

---

## 📝 Bug Report Template

```markdown
## 🐛 Bug Report

**Titel:** [Kurze Beschreibung]

### Severity
- [ ] Critical (9.0-10.0)
- [ ] High (7.0-8.9)
- [ ] Medium (4.0-6.9)
- [ ] Low (0.1-3.9)
- [ ] Enhancement

### Beschreibung
[Klare Beschreibung des Bugs]

### Schritte zur Reproduktion
1. Schritt 1
2. Schritt 2
3. ...

### Erwartetes Verhalten
[Was sollte passieren]

### Tatsächliches Verhalten
[Was passiert stattdessen]

### Proof of Concept (PoC)
```code
[Hier Code oder Screenshots]
```

### Umgebung
- OS: [z.B. Windows 11]
- Python: [z.B. 3.11]
- Version: [z.B. 2.3.9]
- Commit: [optional]

### Impact
[Potenzielle Auswirkungen]

### Fix-Vorschlag (optional)
[Code-Änderung oder Lösungsansatz]

---
**Discord Handle:** @username
**Möchtest du einen PR erstellen?** [Ja/Nein]
```

---

## 📊 Punkteberechnung - Beispiele

### Beispiel 1: Critical Bug
```
RCE in API Endpoint
+ Critical: 1000 Punkte
+ First Blood: +50% (500 Punkte)
+ PoC Quality: +25% (250 Punkte)
+ Fix Provided: +100% (1000 Punkte)
-----------------------------------
Total: 2750 Punkte 🏆
```

### Beispiel 2: Medium Bug
```
Reflected XSS
+ Medium: 200 Punkte
+ Fix Provided: +100% (200 Punkte)
-----------------------------------
Total: 400 Punkte
```

### Beispiel 3: Enhancement
```
Feature Request: Neue API Endpoint
+ Enhancement: 25 Punkte
+ Documentation: +50% (12 Punkte)
-----------------------------------
Total: 37 Punkte
```

---

## 🚫 Out of Scope

Die folgenden Bugs sind **nicht** qualifiziert:

- ⚠️ Self-XSS (kein User-Impact)
- ⚠️ Social Engineering
- ⚠️ Drittanbieter-Services (außer direkte Integration)
- ⚠️ Rate Limiting ohne konkreten Impact
- ⚠️ Best Practices ohne Sicherheitsrelevanz
- ⚠️ Duplikate (nur Erstfinder bekommt Punkte)

---

## ✅ In Scope

| Bereich | Beschreibung |
|---------|--------------|
| **API** | FastAPI Endpoints, Authentication, Authorization |
| **Agents** | ReAct Agent, Tool Execution, Memory System |
| **Database** | SQL Injection, Data Exposure |
| **Docker** | Container Security, Privilege Escalation |
| **CI/CD** | Workflow Security, Secret Exposure |
| **Documentation** | Sensible Informationen im Repo |
| **Dependencies** | CVEs in verwendeten Packages |

---

## 🎯 Saison-Ziele

### Season 1 Ziele (Beispiel)
- [ ] 10+ qualifizierte Bug Reports
- [ ] 2+ Critical/High Severity Bugs
- [ ] 5+ Community Mitglieder im Leaderboard
- [ ] 3+ bereitgestellte Fixes von Community

---

## 📈 Leaderboard Tracking

Das Leaderboard wird automatisch aktualisiert:
- **GitHub:** `LEADERBOARD.md` im Repo
- **Discord:** #leaderboard Channel
- **Website:** Zen-AI-Pentest Homepage (zukünftig)

### Aktuelle Punktestände (Beispiel)

| Rang | Handle | Punkte | Critical | High | Medium | Low | Fixes |
|------|--------|--------|----------|------|--------|-----|-------|
| 🥇 | @hacker_pro | 2750 | 1 | 2 | 1 | 0 | 2 |
| 🥈 | @security_ninja | 1200 | 0 | 1 | 3 | 2 | 1 |
| 🥉 | @bug_hunter | 800 | 0 | 0 | 2 | 4 | 0 |

---

## 🎬 Ablauf

### 1. Bug Melden
- Issue auf GitHub erstellen mit Label `bug-bounty`
- Template ausfüllen
- Discord: #bug-reports mit Link zum Issue

### 2. Validierung
- Core Team prüft Report (1-3 Tage)
- Severity bestimmt
- Punkte berechnet

### 3. Punktevergabe
- Automatische Punkte-Eintragung
- Discord Notification
- Leaderboard Update

### 4. Fix & Reward
- Fix wird implementiert
- Punkte werden final bestätigt
- Belohnungen am Season-Ende verteilt

---

## 🛡️ Responsible Disclosure

1. **Niemals** öffentlich machen vor Fix
2. **Niemals** Produktionsdaten verwenden
3. **Niemals** Denial of Service ohne Absprache
4. **Immer** GitHub Issues für Tracking nutzen

---

## 📞 Kontakt

| Kanal | Verwendung |
|-------|------------|
| **GitHub Issues** | Bug Reports mit `bug-bounty` Label |
| **Discord** | #bug-reports für Diskussionen |
| **Email** | security@zen-ai-pentest.com (für sensitive Bugs) |

---

## 🎉 Los geht's!

**Ready to hunt some bugs?** 🐛🔍

> *"Jeder Bug ist eine Chance, das Projekt besser zu machen!"*

**Aktuelle Season:** Season 1 (Jan - Mär 2026)
**Leaderboard:** [Siehe Discord #leaderboard](https://discord.gg/zJZUJwK9AC)

---

*Last Updated: 13.02.2026*
*Programm-Version: 1.0*
