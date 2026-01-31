"""
VirtualBox VM Manager für Zen-AI-Pentest

Verwaltet VMs für isolierte Pentest-Umgebungen.
Unterstützt Kali Linux, Windows und macOS (Intel) VMs.
"""

import subprocess
import json
import logging
import time
from typing import Optional, List, Dict, Literal
from dataclasses import dataclass
from pathlib import Path
import platform

logger = logging.getLogger(__name__)


@dataclass
class VMConfig:
    """Konfiguration für eine VM"""
    name: str
    os_type: Literal["kali", "windows", "macos"]
    vm_path: str  # Pfad zur .vbox oder VM-Name
    snapshot_name: Optional[str] = "clean_state"
    network_mode: Literal["nat", "bridged", "host_only", "internal"] = "nat"
    memory_mb: int = 4096
    cpus: int = 2


class VirtualBoxManager:
    """
    Manager für VirtualBox-VMs.
    
    Features:
    - VM Start/Stop/Reset
    - Snapshot Management
    - Netzwerk-Konfiguration
    - Guest Control (Befehle in VM ausführen)
    - Multi-OS Unterstützung
    """
    
    def __init__(self):
        self.vbox_manage = self._find_vbox_manage()
        if not self.vbox_manage:
            raise RuntimeError("VBoxManage nicht gefunden. Ist VirtualBox installiert?")
        
        self.system = platform.system().lower()
        logger.info(f"VirtualBoxManager initialisiert (OS: {self.system})")
    
    def _find_vbox_manage(self) -> Optional[str]:
        """Findet VBoxManage Binary"""
        possible_paths = [
            # Windows
            r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe",
            r"C:\Program Files (x86)\Oracle\VirtualBox\VBoxManage.exe",
            # Linux
            "/usr/bin/VBoxManage",
            "/usr/local/bin/VBoxManage",
            # macOS
            "/Applications/VirtualBox.app/Contents/MacOS/VBoxManage",
            "VBoxManage",  # Im PATH
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logger.info(f"VBoxManage gefunden: {path} (Version: {result.stdout.strip()})")
                    return path
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return None
    
    def _run_vbox_command(self, args: List[str], timeout: int = 60) -> tuple:
        """Führt VBoxManage Befehl aus"""
        cmd = [self.vbox_manage] + args
        logger.debug(f"VBoxManage Befehl: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            logger.error(f"VBoxManage Timeout nach {timeout}s")
            return -1, "", "Timeout"
        except Exception as e:
            logger.error(f"VBoxManage Fehler: {e}")
            return -1, "", str(e)
    
    def list_vms(self, running_only: bool = False) -> List[Dict]:
        """Listet alle VMs auf"""
        args = ["list", "runningvms" if running_only else "vms"]
        returncode, stdout, stderr = self._run_vbox_command(args)
        
        if returncode != 0:
            logger.error(f"Konnte VMs nicht auflisten: {stderr}")
            return []
        
        vms = []
        for line in stdout.strip().split('\n'):
            if line:
                # Format: "VM Name" {uuid}
                parts = line.rsplit(' ', 1)
                if len(parts) == 2:
                    name = parts[0].strip('"')
                    uuid = parts[1].strip('{}')
                    vms.append({"name": name, "uuid": uuid})
        
        return vms
    
    def vm_exists(self, vm_name: str) -> bool:
        """Prüft ob VM existiert"""
        vms = self.list_vms()
        return any(vm["name"] == vm_name for vm in vms)
    
    def is_running(self, vm_name: str) -> bool:
        """Prüft ob VM läuft"""
        running = self.list_vms(running_only=True)
        return any(vm["name"] == vm_name for vm in running)
    
    def start_vm(self, vm_name: str, headless: bool = True) -> bool:
        """Startet eine VM"""
        if self.is_running(vm_name):
            logger.info(f"VM {vm_name} läuft bereits")
            return True
        
        mode = "headless" if headless else "gui"
        returncode, stdout, stderr = self._run_vbox_command(
            ["startvm", vm_name, "--type", mode],
            timeout=120
        )
        
        if returncode == 0:
            logger.info(f"VM {vm_name} gestartet ({mode})")
            # Warte auf Guest Additions
            time.sleep(5)
            return True
        else:
            logger.error(f"Fehler beim Starten von {vm_name}: {stderr}")
            return False
    
    def stop_vm(self, vm_name: str, force: bool = False) -> bool:
        """Stoppt eine VM"""
        if not self.is_running(vm_name):
            logger.info(f"VM {vm_name} ist nicht aktiv")
            return True
        
        method = "poweroff" if force else "acpipowerbutton"
        returncode, stdout, stderr = self._run_vbox_command(
            ["controlvm", vm_name, method],
            timeout=30
        )
        
        if returncode == 0:
            logger.info(f"VM {vm_name} gestoppt ({method})")
            return True
        else:
            logger.error(f"Fehler beim Stoppen von {vm_name}: {stderr}")
            return False
    
    def reset_vm(self, vm_name: str) -> bool:
        """Resetet eine VM (hard reset)"""
        returncode, stdout, stderr = self._run_vbox_command(
            ["controlvm", vm_name, "reset"],
            timeout=30
        )
        return returncode == 0
    
    def create_snapshot(self, vm_name: str, snapshot_name: str, description: str = "") -> bool:
        """Erstellt Snapshot"""
        returncode, stdout, stderr = self._run_vbox_command([
            "snapshot", vm_name, "take", snapshot_name,
            "--description", description or f"Snapshot {snapshot_name}"
        ], timeout=120)
        
        if returncode == 0:
            logger.info(f"Snapshot {snapshot_name} für {vm_name} erstellt")
            return True
        else:
            logger.error(f"Snapshot-Fehler: {stderr}")
            return False
    
    def restore_snapshot(self, vm_name: str, snapshot_name: str) -> bool:
        """Stellt Snapshot wieder her"""
        # VM muss aus sein
        if self.is_running(vm_name):
            logger.info(f"Stoppe VM {vm_name} für Snapshot-Restore...")
            self.stop_vm(vm_name, force=True)
            time.sleep(3)
        
        returncode, stdout, stderr = self._run_vbox_command([
            "snapshot", vm_name, "restore", snapshot_name
        ], timeout=120)
        
        if returncode == 0:
            logger.info(f"Snapshot {snapshot_name} für {vm_name} wiederhergestellt")
            return True
        else:
            logger.error(f"Restore-Fehler: {stderr}")
            return False
    
    def list_snapshots(self, vm_name: str) -> List[Dict]:
        """Listet Snapshots einer VM"""
        returncode, stdout, stderr = self._run_vbox_command(
            ["snapshot", vm_name, "list", "--machinereadable"]
        )
        
        snapshots = []
        if returncode == 0:
            current_snapshot = None
            for line in stdout.split('\n'):
                if line.startswith('CurrentSnapshotUUID='):
                    current_snapshot = line.split('=')[1].strip('"')
                elif line.startswith('SnapshotName'):
                    parts = line.split('=')
                    if len(parts) == 2:
                        name = parts[1].strip('"')
                        snapshots.append({
                            "name": name,
                            "current": False  # Wird später gesetzt
                        })
        
        return snapshots
    
    def execute_in_vm(self, vm_name: str, command: str, 
                      username: str = "user", password: str = "user",
                      timeout: int = 60) -> tuple:
        """
        Führt Befehl in VM aus (via Guest Control).
        Benötigt Guest Additions und laufende VM.
        """
        if not self.is_running(vm_name):
            logger.error(f"VM {vm_name} läuft nicht")
            return -1, "", "VM not running"
        
        # Befehl splitten für guestcontrol
        args = [
            "guestcontrol", vm_name, "run",
            "--username", username,
            "--password", password,
            "--exe", "/bin/bash" if "linux" in platform.system().lower() else "cmd.exe",
            "--",
            "-c" if "linux" in platform.system().lower() else "/c",
            command
        ]
        
        returncode, stdout, stderr = self._run_vbox_command(args, timeout)
        return returncode, stdout, stderr
    
    def configure_network(self, vm_name: str, mode: Literal["nat", "bridged", "host_only", "internal"] = "nat",
                         adapter: int = 1) -> bool:
        """Konfiguriert Netzwerk-Adapter"""
        nic_type = {
            "nat": "nat",
            "bridged": "bridged",
            "host_only": "hostonly",
            "internal": "intnet"
        }.get(mode, "nat")
        
        returncode, stdout, stderr = self._run_vbox_command([
            "modifyvm", vm_name,
            f"--nic{adapter}", nic_type
        ])
        
        if returncode == 0:
            logger.info(f"Netzwerk für {vm_name} auf {mode} gesetzt")
            return True
        else:
            logger.error(f"Netzwerk-Konfigurationsfehler: {stderr}")
            return False
    
    def get_vm_info(self, vm_name: str) -> Dict:
        """Gibt VM-Informationen"""
        returncode, stdout, stderr = self._run_vbox_command(
            ["showvminfo", vm_name, "--machinereadable"]
        )
        
        info = {}
        if returncode == 0:
            for line in stdout.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    info[key] = value.strip('"')
        
        return info
    
    def clone_vm(self, source_vm: str, new_name: str, 
                 linked: bool = True, snapshot: Optional[str] = None) -> bool:
        """Klont eine VM"""
        mode = "--mode=machine" if not linked else "--mode=machine --options=Link"
        
        args = ["clonevm", source_vm, "--name", new_name, "--register"]
        if linked:
            args.extend(["--mode", "machine", "--options", "Link"])
        if snapshot:
            args.extend(["--snapshot", snapshot])
        
        returncode, stdout, stderr = self._run_vbox_command(args, timeout=300)
        
        if returncode == 0:
            logger.info(f"VM {source_vm} nach {new_name} geklont")
            return True
        else:
            logger.error(f"Clone-Fehler: {stderr}")
            return False
    
    def delete_vm(self, vm_name: str, delete_files: bool = True) -> bool:
        """Löscht eine VM"""
        # Stoppe falls läuft
        if self.is_running(vm_name):
            self.stop_vm(vm_name, force=True)
            time.sleep(2)
        
        args = ["unregistervm", vm_name]
        if delete_files:
            args.append("--delete")
        
        returncode, stdout, stderr = self._run_vbox_command(args)
        
        if returncode == 0:
            logger.info(f"VM {vm_name} gelöscht")
            return True
        else:
            logger.error(f"Löschfehler: {stderr}")
            return False


class PentestSandbox:
    """
    High-Level Sandbox für Pentests.
    Verwaltet Kali-Linux VM als sichere Testumgebung.
    """
    
    def __init__(self, vm_manager: VirtualBoxManager):
        self.vm = vm_manager
        self.active_sessions = {}
    
    def create_session(self, session_id: str, target_vm: str = "kali-pentest") -> bool:
        """Erstellt neue Pentest-Session"""
        if not self.vm.vm_exists(target_vm):
            logger.error(f"VM {target_vm} nicht gefunden")
            return False
        
        # Restore clean state
        if not self.vm.restore_snapshot(target_vm, "clean_state"):
            logger.warning("Konnte clean_state nicht wiederherstellen, erstelle neuen...")
            self.vm.create_snapshot(target_vm, f"session_{session_id}")
        
        # Start VM
        if not self.vm.start_vm(target_vm, headless=False):
            return False
        
        self.active_sessions[session_id] = {
            "vm_name": target_vm,
            "start_time": time.time(),
            "findings": []
        }
        
        logger.info(f"Session {session_id} gestartet auf {target_vm}")
        return True
    
    def execute_tool(self, session_id: str, tool: str, args: str,
                    username: str = "kali", password: str = "kali") -> tuple:
        """Führt Tool in Session aus"""
        if session_id not in self.active_sessions:
            return -1, "", "Session nicht gefunden"
        
        vm_name = self.active_sessions[session_id]["vm_name"]
        
        # Tool-Mapping
        tool_commands = {
            "nmap": f"nmap {args}",
            "nuclei": f"nuclei {args}",
            "ffuf": f"ffuf {args}",
            "gobuster": f"gobuster {args}",
            "sqlmap": f"sqlmap {args}",
            "metasploit": f"msfconsole -q -x '{args}'",
        }
        
        command = tool_commands.get(tool, f"{tool} {args}")
        
        return self.vm.execute_in_vm(vm_name, command, username, password)
    
    def end_session(self, session_id: str, save_snapshot: bool = False) -> bool:
        """Beendet Session"""
        if session_id not in self.active_sessions:
            return False
        
        vm_name = self.active_sessions[session_id]["vm_name"]
        
        if save_snapshot:
            self.vm.create_snapshot(vm_name, f"session_{session_id}_ended")
        
        self.vm.stop_vm(vm_name)
        del self.active_sessions[session_id]
        
        logger.info(f"Session {session_id} beendet")
        return True


# Factory-Funktion
def get_vm_manager() -> VirtualBoxManager:
    """Gibt VM Manager Instanz zurück"""
    return VirtualBoxManager()


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    try:
        vbox = VirtualBoxManager()
        
        print("Verfügbare VMs:")
        for vm in vbox.list_vms():
            running = "[RUNNING]" if vbox.is_running(vm["name"]) else "[STOPPED]"
            print(f"  {running} {vm['name']}")
        
    except RuntimeError as e:
        print(f"Fehler: {e}")
