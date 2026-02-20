# VirtualBox Virtualisierung - Zusammenfassung

## Übersicht

Zen-AI-Pentest unterstützt jetzt vollständige VirtualBox-Integration für isolierte Pentest-Umgebungen. Damit können Tests sicher in VMs durchgeführt werden, ohne das Host-System zu gefährden.

---

## Features

### ✅ Implementiert

| Feature | Beschreibung | Status |
|---------|--------------|--------|
| **VM Management** | Start/Stop/Reset von VMs | ✅ |
| **Snapshot Control** | Clean-State-Workflow | ✅ |
| **Guest Control** | Befehle in VMs ausführen | ✅ |
| **Multi-OS** | Kali, Windows, macOS Support | ✅ |
| **Netzwerk** | NAT, Bridged, Host-Only, Internal | ✅ |
| **Sandbox API** | High-Level Pentest-Sessions | ✅ |
| **ReAct Integration** | Agent nutzt VMs automatisch | ✅ |
| **Setup Script** | Automatisierte VM-Erstellung | ✅ |

---

## Dateien

```
zen-ai-pentest/
├── virtualization/
│   └── vm_manager.py          # Core VM Management
├── scripts/
│   └── setup_vms.py           # Automatisiertes Setup
├── examples/
│   └── vm_pentest_example.py  # Beispiele & Workflows
├── docs/
│   ├── setup/
│   │   └── VIRTUALBOX_SETUP.md  # Komplette Anleitung
│   └── VIRTUALIZATION_SUMMARY.md # Diese Datei
└── docker/
    └── docker-compose.vm.yml    # Docker Integration
```

---

## Schnellstart

### 1. VirtualBox Installieren

**Windows:**
```powershell
# Download von virtualbox.org
# Installieren mit Standard-Einstellungen
```

**Linux (Kali/Debian):**
```bash
sudo apt update
sudo apt install -y virtualbox
sudo usermod -aG vboxusers $USER
# Neuanmeldung erforderlich!
```

**macOS:**
```bash
# Download DMG von virtualbox.org
# Installation + Security-Freigabe in Systemeinstellungen
```

### 2. Kali VM Setup

```bash
# Automatisches Setup
python scripts/setup_vms.py --kali

# Oder manuell:
# 1. Kali OVA herunterladen
# 2. Importieren
# 3. Snapshot erstellen
```

### 3. Erster Pentest

```python
from virtualization.vm_manager import VirtualBoxManager, PentestSandbox

# Initialisieren
vbox = VirtualBoxManager()
sandbox = PentestSandbox(vbox)

# Session starten
sandbox.create_session("pentest_001", "kali-pentest")

# Nmap in VM ausführen
exit_code, stdout, stderr = sandbox.execute_tool(
    "pentest_001", "nmap", "-sV target.com"
)
print(stdout)

# Aufräumen
sandbox.end_session("pentest_001")
```

---

## Unterstützte Betriebssysteme

### Host (Wo VirtualBox läuft)

| OS | Status | Anmerkungen |
|----|--------|-------------|
| Windows 10/11 | ✅ Vollständig | Hyper-V deaktivieren |
| Linux (Debian/Ubuntu/Kali) | ✅ Vollständig | vboxusers Gruppe |
| macOS Intel | ✅ Vollständig | Kernel Extensions |
| macOS Apple Silicon | ❌ Nicht unterstützt | Nutze UTM stattdessen |

### Guest (VMs)

| OS | Zweck | Setup |
|----|-------|-------|
| **Kali Linux** | Haupt-Pentest-VM | `setup_vms.py --kali` |
| **Windows 10/11** | Target/Testing | Manuelle Installation |
| **Windows Server** | Enterprise Targets | Manuelle Installation |
| **macOS** | Target (nur auf Mac Host) | Manuelle Installation |

---

## Architektur

```
┌─────────────────────────────────────────────┐
│           Zen-AI-Pentest (Host)             │
│  ┌─────────────────────────────────────┐   │
│  │        ReAct Agent                  │   │
│  │  ┌──────────┐  ┌──────────────┐   │   │
│  │  │ Reason   │→ │ VM Tools     │   │   │
│  │  └──────────┘  └──────────────┘   │   │
│  └─────────────────────────────────────┘   │
│                    ↓                        │
│  ┌─────────────────────────────────────┐   │
│  │     VirtualBox Manager              │   │
│  │  - VM Start/Stop                    │   │
│  │  - Snapshots                        │   │
│  │  - Guest Control                    │   │
│  └─────────────────────────────────────┘   │
│                    ↓                        │
│  ┌─────────────────────────────────────┐   │
│  │      VirtualBox (Hypervisor)        │   │
│  └─────────────────────────────────────┘   │
│              ↓              ↓               │
│     ┌──────────┐     ┌──────────┐          │
│     │ Kali VM  │     │ Win VM   │          │
│     │ (Attack) │     │ (Target) │          │
│     └──────────┘     └──────────┘          │
└─────────────────────────────────────────────┘
```

---

## API-Referenz

### VirtualBoxManager

```python
from virtualization.vm_manager import VirtualBoxManager

vbox = VirtualBoxManager()

# VM Status
vbox.list_vms()                      # Alle VMs
vbox.list_vms(running_only=True)     # Nur laufende
vbox.is_running("vm-name")           # Prüft Status

# VM Steuerung
vbox.start_vm("vm-name", headless=True)
vbox.stop_vm("vm-name", force=False)
vbox.reset_vm("vm-name")

# Snapshots
vbox.create_snapshot("vm", "snapshot-name")
vbox.restore_snapshot("vm", "snapshot-name")
vbox.list_snapshots("vm")

# Netzwerk
vbox.configure_network("vm", mode="host_only")

# Guest Control (Befehle in VM)
vbox.execute_in_vm("vm", "nmap -sV target.com",
                   username="kali", password="kali")
```

### PentestSandbox

```python
from virtualization.vm_manager import PentestSandbox

sandbox = PentestSandbox(vbox)

# Session Management
sandbox.create_session("session-id", "kali-pentest")
sandbox.execute_tool("session-id", "nmap", "-sV target.com")
sandbox.end_session("session-id")
```

---

## Best Practices

### 1. Sicherheit

- **Niemals** Produktiv-Systeme ohne Autorisierung testen
- VMs in **Host-Only** oder **Internal Network** für isolierte Labs
- **Snapshots** vor jedem Pentest wiederherstellen
- **Linked Clones** für parallele Tests verwenden

### 2. Performance

- Mindestens **8 GB RAM** für Host + VMs
- **SSD** für VM-Storage empfohlen
- **4+ CPU Cores** für flüssige Ausführung
- **Guest Additions** installieren für bessere Performance

### 3. Workflow

```
1. VM auf "clean_state" Snapshot zurücksetzen
2. Pentest durchführen
3. Ergebnisse exportieren
4. VM stoppen oder Snapshot mit Ergebnissen speichern
5. Zurück zu clean_state für nächsten Test
```

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| "VT-x not available" | BIOS: Virtualisierung aktivieren, Hyper-V deaktivieren |
| "Permission denied" | User zur Gruppe `vboxusers` hinzufügen |
| VM startet nicht | Logs prüfen: `VBoxManage showvminfo "VM"` |
| Kein Netzwerk | Adapter prüfen: NAT für Internet, Host-Only für Isolation |
| Langsame VMs | Guest Additions installieren, RAM/CPU erhöhen |

---

## Nächste Schritte

1. **Setup**: [VIRTUALBOX_SETUP.md](setup/VIRTUALBOX_SETUP.md)
2. **ReAct Agent**: [REACT_AGENT.md](REACT_AGENT.md)
3. **Beispiele**: `python examples/vm_pentest_example.py 1`

---

## Ressourcen

- VirtualBox Manual: https://www.virtualbox.org/manual/
- Kali Linux VMs: https://www.kali.org/get-kali/#kali-virtual-machines
- Zen-AI-Pentest Issues: https://github.com/SHAdd0WTAka/zen-ai-pentest/issues

---

**Status**: ✅ VirtualBox-Integration vollständig implementiert und dokumentiert.
