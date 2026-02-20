# VirtualBox Setup Guide für Zen-AI-Pentest

Diese Anleitung beschreibt die Einrichtung von VirtualBox mit Kali Linux, Windows und macOS für isolierte Pentest-Umgebungen.

---

## Inhaltsverzeichnis

1. [Systemanforderungen](#systemanforderungen)
2. [VirtualBox Installation](#virtualbox-installation)
   - [Windows](#windows)
   - [Linux (Kali/Debian/Ubuntu)](#linux)
   - [macOS](#macos)
3. [VM-Erstellung](#vm-erstellung)
   - [Kali Linux VM](#kali-linux-vm)
   - [Windows VM](#windows-vm)
   - [macOS VM](#macos-vm)
4. [Netzwerk-Konfiguration](#netzwerk-konfiguration)
5. [Guest Additions](#guest-additions)
6. [Integration mit Zen-AI-Pentest](#integration)

---

## Systemanforderungen

### Minimal
- **CPU**: 4 Cores (mit VT-x/AMD-V Unterstützung)
- **RAM**: 8 GB
- **Storage**: 50 GB freier Speicher
- **Netzwerk**: Internet-Verbindung für Updates

### Empfohlen
- **CPU**: 8+ Cores
- **RAM**: 16+ GB
- **Storage**: 100+ GB SSD
- **GPU**: Optional für GPU-Passthrough

### BIOS/UEFI Einstellungen
Virtualisierung muss aktiviert sein:
- Intel: **VT-x** (Virtualization Technology)
- AMD: **AMD-V** (Secure Virtual Machine)

> ⚠️ **Wichtig**: Ohne aktivierte Virtualisierung laufen VMs extrem langsam!

---

## VirtualBox Installation

### Windows

#### Schritt 1: Download
1. Besuche [virtualbox.org](https://www.virtualbox.org/wiki/Downloads)
2. Lade "Windows hosts" herunter

#### Schritt 2: Installation
```powershell
# Als Administrator ausführen
VirtualBox-7.x.x-Win.exe
```

Während der Installation:
- ✅ USB Support (optional)
- ✅ VirtualBox Networking
- ✅ Python Support (für Zen-Integration)

#### Schritt 3: Verification
```powershell
# In PowerShell
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" --version
# Output: 7.x.x
```

#### Troubleshooting Windows
**Problem**: "VT-x is not available"
```powershell
# Prüfe Hyper-V Status
Get-ComputerInfo -Property HyperVRequirementVirtualizationFirmwareEnabled

# Falls Hyper-V aktiv, deaktivieren:
bcdedit /set hypervisorlaunchtype off
# Neustart erforderlich!
```

**Problem**: Netzwerk-Adapter nicht verfügbar
```powershell
# Repariere VirtualBox Netzwerk
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" hostonlyif create
```

---

### Linux (Kali/Debian/Ubuntu)

#### Schritt 1: Repository hinzufügen
```bash
# Debian/Ubuntu/Kali
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/oracle-virtualbox-2016.gpg] https://download.virtualbox.org/virtualbox/debian $(lsb_release -cs) contrib" | sudo tee /etc/apt/sources.list.d/virtualbox.list

# GPG Key
wget -q https://www.virtualbox.org/download/oracle_vbox_2016.asc -O- | sudo gpg --dearmor --yes --output /usr/share/keyrings/oracle-virtualbox-2016.gpg
```

#### Schritt 2: Installation
```bash
sudo apt update
sudo apt install -y virtualbox-7.0

# Optional: Extension Pack
wget https://download.virtualbox.org/virtualbox/7.0.x/Oracle_VirtualBox_Extension_Pack-7.0.x.vbox-extpack
sudo VBoxManage extpack install Oracle_VirtualBox_Extension_Pack-7.0.x.vbox-extpack
```

#### Schritt 3: User zur vboxusers Gruppe
```bash
sudo usermod -aG vboxusers $USER
# Ausloggen und wieder einloggen!
```

#### Schritt 4: Verification
```bash
VBoxManage --version
which VBoxManage
# /usr/bin/VBoxManage
```

#### Troubleshooting Linux
**Problem**: Kernel Module nicht geladen
```bash
# Rebuild VirtualBox Modules
sudo /sbin/vboxconfig

# Oder:
sudo modprobe vboxdrv
sudo modprobe vboxnetflt
sudo modprobe vboxnetadp
```

**Problem**: Permission denied
```bash
# Prüfe Gruppen-Mitgliedschaft
groups $USER
# Sollte enthalten: vboxusers

# Falls nicht:
newgrp vboxusers
```

---

### macOS

#### Schritt 1: Download
1. Besuche [virtualbox.org](https://www.virtualbox.org/wiki/Downloads)
2. Lade "OS X hosts" herunter

#### Schritt 2: Installation
```bash
# DMG öffnen und VirtualBox.pkg installieren
# Bei Intel Macs: Keine zusätzlichen Schritte nötig
# Bei Apple Silicon (M1/M2): Nicht unterstützt!
```

> ⚠️ **Apple Silicon (M1/M2/M3)**: VirtualBox läuft nur auf Intel-Macs! Für Apple Silicon nutze [UTM](https://mac.getutm.app/) oder Parallels.

#### Schritt 3: Security Einstellungen
```bash
# System Preferences > Security & Privacy
# "Allow" für Oracle America, Inc.
```

#### Schritt 4: Verification
```bash
/Applications/VirtualBox.app/Contents/MacOS/VBoxManage --version
```

#### Troubleshooting macOS
**Problem**: "System Extension Blocked"
```bash
# Systemeinstellungen > Sicherheit > "Allow"
# Neustart erforderlich
```

---

## VM-Erstellung

### Kali Linux VM

#### Methode 1: Offizielles OVA (Empfohlen)

1. **Download**: [Kali Linux VirtualBox Image](https://www.kali.org/get-kali/#kali-virtual-machines)
   ```bash
   # Direktlink (Version prüfen!)
   wget https://kali.download/virtual-images/kali-2024.x/kali-linux-2024.x-virtualbox-amd64.7z
   ```

2. **Entpacken**:
   ```bash
   # 7z installieren falls nötig
   # Windows: 7-Zip, macOS: brew install p7zip
   7z x kali-linux-2024.x-virtualbox-amd64.7z
   ```

3. **Importieren**:
   ```bash
   VBoxManage import kali-linux-2024.x-virtualbox-amd64.ova \
     --vsys 0 \
     --vmname "kali-pentest" \
     --cpus 4 \
     --memory 8192
   ```

#### Methode 2: Manuelle Installation

1. **ISO Download**: [Kali Linux Installer](https://www.kali.org/get-kali/)

2. **VM Erstellen**:
   ```bash
   VBoxManage createvm --name "kali-pentest" --ostype "Debian_64" --register

   # Speicher
   VBoxManage modifyvm "kali-pentest" --memory 8192 --cpus 4

   # Festplatte (50 GB)
   VBoxManage createhd --filename "~/VirtualBox VMs/kali-pentest/disk.vdi" --size 51200

   # Storage Controller
   VBoxManage storagectl "kali-pentest" --name "SATA" --add sata
   VBoxManage storageattach "kali-pentest" --storagectl "SATA" --port 0 --device 0 --type hdd --medium "~/VirtualBox VMs/kali-pentest/disk.vdi"

   # ISO mounten
   VBoxManage storageattach "kali-pentest" --storagectl "SATA" --port 1 --device 0 --type dvddrive --medium ~/Downloads/kali-linux-2024.x-installer-amd64.iso
   ```

3. **Installation starten**:
   ```bash
   VBoxManage startvm "kali-pentest"
   ```

4. **Nach Installation**:
   - Username: `kali`
   - Password: `kali`
   - Aktualisieren: `sudo apt update && sudo apt full-upgrade -y`

#### Kali VM Konfiguration

```bash
# Guest Additions installieren
sudo apt install -y virtualbox-guest-x11 virtualbox-guest-utils virtualbox-guest-dkms

# Pentest-Tools
sudo apt install -y nmap nikto gobuster sqlmap metasploit-framework

# Python für Zen-Integration
sudo apt install -y python3-pip python3-venv

# Snapshot erstellen (clean state)
VBoxManage snapshot "kali-pentest" take "clean_state" --description "Fresh Kali install"
```

---

### Windows VM

#### Windows 10/11 VM erstellen

1. **ISO Download**: [Windows 10/11 ISO](https://www.microsoft.com/software-download/windows10)

2. **VM Erstellen**:
   ```bash
   VBoxManage createvm --name "win10-pentest" --ostype "Windows10_64" --register

   # Hardware
   VBoxManage modifyvm "win10-pentest" --memory 4096 --cpus 2
   VBoxManage modifyvm "win10-pentest" --vram 128

   # Storage
   VBoxManage createhd --filename "~/VirtualBox VMs/win10-pentest/disk.vdi" --size 51200
   VBoxManage storagectl "win10-pentest" --name "SATA" --add sata
   VBoxManage storageattach "win10-pentest" --storagectl "SATA" --port 0 --device 0 --type hdd --medium "~/VirtualBox VMs/win10-pentest/disk.vdi"
   VBoxManage storageattach "win10-pentest" --storagectl "SATA" --port 1 --device 0 --type dvddrive --medium ~/Downloads/Win10.iso
   ```

3. **Nach Installation**:
   - Guest Additions installieren (VirtualBox Menu > Devices > Insert Guest Additions CD)
   - Windows Updates
   - Defender konfigurieren (Ausschlüsse für Pentest-Tools)

#### Windows als Target VM

Für Pentests gegen Windows-Targets:

```powershell
# In Windows VM (als Admin)
# Remote Desktop aktivieren
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -name "fDenyTSConnections" -value 0
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"

# SMB aktivieren (für Tests)
Enable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol

# Schwachstellen für Testing (nur in isolierter VM!)
# z.B. SMBv1, unpatched Services
```

> ⚠️ **Warnung**: Windows VM nur für autorisierte Tests in isolierter Umgebung!

---

### macOS VM

> ⚠️ **Wichtig**: macOS VMs sind nur auf macOS Hosts legal!

#### Voraussetzungen
- Host: macOS (Intel)
- macOS Installer App (vom App Store)

#### Erstellung mit VBoxManage

```bash
# macOS Installer App vorbereiten
# /Applications/Install\ macOS\ [Version].app

# VM erstellen
VBoxManage createvm --name "macos-target" --ostype "MacOS_64" --register
VBoxManage modifyvm "macos-target" --memory 4096 --cpus 2

# Weitere Konfiguration komplex - siehe:
# https://github.com/myspaghetti/macos-virtualbox
```

> **Empfehlung**: Nutze [macos-virtualbox](https://github.com/myspaghetti/macos-virtualbox) Script für automatisierte Erstellung.

---

## Netzwerk-Konfiguration

### NAT (Standard)
```bash
VBoxManage modifyvm "kali-pentest" --nic1 nat
# VM hat Internet, ist aber isoliert
```

### Host-Only (Empfohlen für Testing)
```bash
# Host-Only Adapter erstellen (einmalig)
VBoxManage hostonlyif create

# Adapter zuweisen
VBoxManage modifyvm "kali-pentest" --nic1 hostonly
VBoxManage modifyvm "kali-pentest" --hostonlyadapter1 vboxnet0

# Target VM im gleichen Netz
VBoxManage modifyvm "win10-pentest" --nic1 hostonly
VBoxManage modifyvm "win10-pentest" --hostonlyadapter1 vboxnet0
```

### Bridged (VM ist im gleichen Netz wie Host)
```bash
VBoxManage modifyvm "kali-pentest" --nic1 bridged
VBoxManage modifyvm "kali-pentest" --bridgeadapter1 eth0  # oder en0 auf macOS
```

### Internal Network (VMs nur untereinander)
```bash
VBoxManage modifyvm "kali-pentest" --nic1 intnet
VBoxManage modifyvm "kali-pentest" --intnet1 "pentest-lab"

VBoxManage modifyvm "win10-pentest" --nic1 intnet
VBoxManage modifyvm "win10-pentest" --intnet1 "pentest-lab"
```

---

## Guest Additions

Guest Additions ermöglichen:
- Shared Clipboard
- Drag & Drop
- Dynamische Auflösung
- Guest Control (Befehle vom Host ausführen)

### Installation

**In Kali Linux:**
```bash
sudo apt install -y virtualbox-guest-x11 virtualbox-guest-utils
sudo reboot
```

**In Windows:**
- VirtualBox Menu > Devices > Insert Guest Additions CD Image
- Setup.exe ausführen
- Neustart

**In macOS:**
- VirtualBox Menu > Devices > Insert Guest Additions CD Image
- Installer ausführen

---

## Integration mit Zen-AI-Pentest

### Konfiguration

Erstelle `config/vm_config.json`:
```json
{
  "default_vm": "kali-pentest",
  "vms": {
    "kali-pentest": {
      "os_type": "kali",
      "username": "kali",
      "password": "kali",
      "snapshot": "clean_state"
    },
    "win10-target": {
      "os_type": "windows",
      "username": "user",
      "password": "password",
      "snapshot": "fresh_install"
    }
  },
  "network": {
    "mode": "host_only",
    "subnet": "192.168.56.0/24"
  }
}
```

### Verwendung im Code

```python
from virtualization.vm_manager import VirtualBoxManager, PentestSandbox

# VM Manager initialisieren
vbox = VirtualBoxManager()

# Liste VMs
for vm in vbox.list_vms():
    print(f"{vm['name']}: {'Running' if vbox.is_running(vm['name']) else 'Stopped'}")

# Sandbox erstellen
sandbox = PentestSandbox(vbox)

# Session starten
sandbox.create_session("pentest_001", target_vm="kali-pentest")

# Tools ausführen
exit_code, stdout, stderr = sandbox.execute_tool(
    "pentest_001",
    "nmap",
    "-sV 192.168.56.101"
)
print(stdout)

# Session beenden
sandbox.end_session("pentest_001")
```

### Automatisierte VM-Erstellung

```bash
# Setup-Script ausführen
python scripts/setup_vms.py --install-kali --install-windows
```

---

## Schnellstart

### Ein-Befehl-Setup (Linux/macOS)

```bash
# 1. VirtualBox installieren (siehe oben)

# 2. Kali VM herunterladen und importieren
wget https://kali.download/virtual-images/kali-2024.3/kali-linux-2024.3-virtualbox-amd64.7z
7z x kali-linux-2024.3-virtualbox-amd64.7z
VBoxManage import kali-linux-2024.3-virtualbox-amd64.ova --vsys 0 --vmname "kali-pentest"

# 3. Snapshot erstellen
VBoxManage snapshot "kali-pentest" take "clean_state"

# 4. Test
VBoxManage startvm "kali-pentest" --type headless
```

### Ein-Befehl-Setup (Windows PowerShell)

```powershell
# 1. VirtualBox installieren

# 2. Kali herunterladen (mit BitsTransfer)
Start-BitsTransfer -Source "https://kali.download/virtual-images/kali-2024.3/kali-linux-2024.3-virtualbox-amd64.7z" -Destination "$env:USERPROFILE\Downloads\kali.7z"

# 3. Entpacken (7-Zip erforderlich)
& "C:\Program Files\7-Zip\7z.exe" x "$env:USERPROFILE\Downloads\kali.7z"

# 4. Importieren
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" import kali-linux-2024.3-virtualbox-amd64.ova --vsys 0 --vmname "kali-pentest"

# 5. Snapshot
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" snapshot "kali-pentest" take "clean_state"
```

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| "VT-x is not available" | Virtualisierung im BIOS aktivieren, Hyper-V deaktivieren |
| "Cannot register the DVD image" | ISO-Datei neu herunterladen, Checksum prüfen |
| VM startet nicht | Logs prüfen: `VBoxManage showvminfo "VM-Name" --details` |
| Kein Netzwerk | Adapter prüfen: `VBoxManage modifyvm "VM" --nic1 nat` |
| Langsame VM | Guest Additions installieren, CPU-Limit erhöhen |

---

## Nächste Schritte

1. [ReAct Agent Integration](../REACT_AGENT.md) - Automatisierte Pentests in VMs
2. [CI/CD Integration](../CI_CD.md) - VMs in GitHub Actions nutzen
3. [API Dokumentation](../../API.md) - Programmatischer Zugriff

---

## Support

- VirtualBox Forums: [forums.virtualbox.org](https://forums.virtualbox.org/)
- Kali Docs: [kali.org/docs](https://www.kali.org/docs/)
- Zen-AI-Pentest Issues: [GitHub Issues](https://github.com/SHAdd0WTAka/zen-ai-pentest/issues)
