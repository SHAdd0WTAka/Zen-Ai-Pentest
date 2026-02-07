# Installation Guide

Komplette Installationsanleitung für Zen-AI Pentest mit Docker.

---

## 🐳 Docker Installation

### Windows

#### Option 1: Docker Desktop (Empfohlen)
```powershell
# 1. Lade herunter von:
# https://www.docker.com/products/docker-desktop

# 2. Installiere und starte Docker Desktop

# 3. Verifiziere Installation
docker --version
docker-compose --version
```

#### Option 2: Winget (Schnell)
```powershell
# Mit Windows Package Manager
winget install Docker.DockerDesktop

# Neustart erforderlich
```

#### Option 3: Chocolatey
```powershell
# Mit Chocolatey Paketmanager
choco install docker-desktop

# Oder nur Docker Engine (ohne GUI)
choco install docker-cli
choco install docker-compose
```

---

### Linux

#### Option 1: Offizielle Docker Repos (Empfohlen)
```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Ohne sudo nutzen
sudo usermod -aG docker $USER
newgrp docker
```

#### Option 2: Snap (Einfach)
```bash
# Universal für viele Distros
sudo snap install docker

# Docker Compose separat
sudo snap install docker-compose
```

#### Option 3: Script (Schnellste)
```bash
# Offizielles Install-Script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Oder mit Docker Compose
curl -SL https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Arch Linux
```bash
# Mit pacman
sudo pacman -S docker docker-compose

# Oder AUR
yay -S docker-desktop

# Service starten
sudo systemctl start docker
sudo systemctl enable docker
```

---

### macOS

#### Option 1: Docker Desktop (Empfohlen)
```bash
# Homebrew Cask
brew install --cask docker

# Oder manuell:
# https://www.docker.com/products/docker-desktop

# Starte Docker Desktop aus Applications
```

#### Option 2: Homebrew (Nur CLI)
```bash
# Nur Docker CLI (ohne Desktop)
brew install docker

# Docker Compose
brew install docker-compose

# Colima für VM (benötigt)
brew install colima
colima start

# Docker nutzen
docker context use colima
```

#### Option 3: MacPorts
```bash
# Mit MacPorts
sudo port install docker
docker-machine create default
```

---

### Termux (Android)

```bash
# Update packages
pkg update && pkg upgrade

# Install Docker (nur Root-Devices)
pkg install docker

# Alternative ohne Root: Podman
pkg install podman

# Test
podman --version
```

**⚠️ Hinweis:** Docker benötigt Root-Rechte. Ohne Root nutze:
- [UserLAnd](https://github.com/CypherpunkArmory/UserLAnd) + Docker
- Cloud Docker (Play-with-Docker)

---

### iPhone/iPad (iOS)

Docker läuft **nicht nativ** auf iOS. Alternativen:

#### Option 1: iSH (Alpine Linux Shell)
```bash
# Installiere iSH aus App Store
# https://apps.apple.com/us/app/ish-shell/id1436902243

# In iSH:
apk add docker docker-compose

# Sehr limitiert, nur für Tests
```

#### Option 2: SSH zu Remote Server
```bash
# Nutze iOS SSH Client (z.B. Termius, Blink Shell)
# Verbinde zu Linux Server mit Docker

# Oder GitHub Codespaces
# https://github.com/codespaces
```

#### Option 3: a-Shell
```bash
# Installiere a-Shell aus App Store
# https://apps.apple.com/us/app/a-shell/id1543537943

# Python nutzen (kein Docker)
pip install zen-ai-pentest
```

---

## 🚀 Zen-AI Pentest mit Docker

### Schnellstart

```bash
# Repository klonen
git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git
cd Zen-Ai-Pentest

# Mit Docker Compose starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f

# Container stoppen
docker-compose down
```

### Test-Container

```bash
# Teste Kimi Integration
docker-compose -f docker-compose.test.yml up

# Interaktiv
docker run -it --rm zen-ai-pentest /bin/bash
```

### Entwicklungs-Container

```bash
# VS Code Dev Container
# .devcontainer/devcontainer.json wird automatisch erkannt

# Manuel starten
docker build -t zen-pentest .
docker run -it -v $(pwd):/app zen-pentest /bin/bash
```

---

## 🔧 Ohne Docker (Alternative)

### Direkte Installation

```bash
# Python 3.11+ benötigt
python --version

# Repository klonen
git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git
cd Zen-Ai-Pentest

# Virtuelle Umgebung
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# Abhängigkeiten
pip install -r requirements.txt

# Konfiguration
python scripts/setup_wizard.py

# Testen
python scripts/check_config.py
```

---

## 📱 Plattform-spezifische Tipps

### Windows
- **WSL2 empfohlen** für bessere Performance
- Docker Desktop automatisch WSL2 Integration

### Linux
- Für Rootless: `dockerd-rootless-setuptool.sh install`
- AppArmor/SELinux beachten

### macOS
- Apple Silicon (M1/M2): Rosetta 2 installieren
- Mindestens macOS 10.15+

### Cloud Alternativen
```bash
# GitHub Codespaces (Browser-basiert)
# https://github.com/codespaces

# GitPod
# https://gitpod.io/#https://github.com/SHAdd0WTAka/Zen-Ai-Pentest

# Google Cloud Shell
# https://shell.cloud.google.com
```

---

## ✅ Verifikation

```bash
# Docker funktioniert?
docker run hello-world

# Compose funktioniert?
docker-compose --version

# Zen-AI Pentest läuft?
docker-compose ps
```

Bei Problemen: Siehe [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
