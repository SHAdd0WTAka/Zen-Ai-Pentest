#!/usr/bin/env python3
"""
Automatisiertes VM Setup für Zen-AI-Pentest

Erstellt und konfiguriert Kali Linux, Windows und macOS VMs für Pentesting.
"""

import argparse
import json
import logging

import subprocess
import sys
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class VMSetup:
    """Automatisiertes VM Setup"""

    def __init__(self):
        self.vbox_manage = self._find_vbox_manage()
        self.system = self._detect_system()
        self.vm_base_path = Path.home() / "VirtualBox VMs"

    def _find_vbox_manage(self) -> str:
        """Findet VBoxManage"""
        paths = [
            "VBoxManage",
            "/usr/bin/VBoxManage",
            "/usr/local/bin/VBoxManage",
            "/Applications/VirtualBox.app/Contents/MacOS/VBoxManage",
            r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe",
            r"C:\Program Files (x86)\Oracle\VirtualBox\VBoxManage.exe",
        ]

        for path in paths:
            try:
                result = subprocess.run([path, "--version"], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return path
            except Exception:
                continue

        raise RuntimeError("VirtualBox nicht gefunden. Bitte installieren.")

    def _detect_system(self) -> str:
        """Erkennt Betriebssystem"""
        import platform

        return platform.system().lower()

    def _run(self, args: list, timeout: int = 60) -> tuple:
        """Führt VBoxManage Befehl aus"""
        cmd = [self.vbox_manage] + args
        logger.debug(f"Befehl: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout"

    def check_virtualization(self) -> bool:
        """Prüft ob Virtualisierung aktiviert ist"""
        logger.info("Prüfe Virtualisierungs-Unterstützung...")

        try:
            if self.system == "windows":
                result = subprocess.run(
                    ["powershell", "Get-ComputerInfo", "-Property", "HyperVRequirementVirtualizationFirmwareEnabled"],
                    capture_output=True,
                    text=True,
                )
                if "True" in result.stdout:
                    logger.info("✓ Virtualisierung aktiviert")
                    return True
            else:
                # Linux/macOS
                result = subprocess.run(["egrep", "-c", "(vmx|svm)", "/proc/cpuinfo"], capture_output=True, text=True)
                if int(result.stdout.strip()) > 0:
                    logger.info("✓ Virtualisierung aktiviert")
                    return True
        except Exception:
            pass

        logger.warning("⚠ Virtualisierung möglicherweise nicht aktiviert!")
        logger.warning("  Bitte im BIOS/UEFI aktivieren (VT-x/AMD-V)")
        return False

    def download_kali(self, version: str = "2024.3") -> Optional[Path]:
        """Lädt Kali Linux VM herunter"""
        import urllib.request
        import shutil

        filename = f"kali-linux-{version}-virtualbox-amd64.7z"
        url = f"https://kali.download/virtual-images/kali-{version}/{filename}"
        download_path = Path.home() / "Downloads" / filename

        if download_path.exists():
            logger.info(f"Kali Image bereits vorhanden: {download_path}")
            return download_path

        logger.info(f"Lade Kali Linux {version} herunter...")
        logger.info(f"URL: {url}")

        try:
            with urllib.request.urlopen(url) as response, open(download_path, "wb") as out_file:
                shutil.copyfileobj(response, out_file)
            logger.info(f"✓ Download abgeschlossen: {download_path}")
            return download_path
        except Exception as e:
            logger.error(f"Download fehlgeschlagen: {e}")
            return None

    def extract_7z(self, archive_path: Path, output_dir: Path) -> bool:
        """Entpackt 7z Archiv"""
        logger.info(f"Entpacke {archive_path}...")

        # 7z finden
        import shutil

        seven_zip = shutil.which("7z") or shutil.which("7za")
        if not seven_zip and self.system == "windows":
            seven_zip = r"C:\Program Files\7-Zip\7z.exe"

        if not seven_zip or not Path(seven_zip).exists():
            logger.error("7-Zip nicht gefunden. Bitte installieren.")
            return False

        try:
            result = subprocess.run(
                [seven_zip, "x", str(archive_path), f"-o{output_dir}", "-y"], capture_output=True, text=True, timeout=300
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Entpacken fehlgeschlagen: {e}")
            return False

    def import_kali_vm(self, ova_path: Path, vm_name: str = "kali-pentest") -> bool:
        """Importiert Kali VM"""
        logger.info(f"Importiere Kali VM als '{vm_name}'...")

        # Prüfe ob VM bereits existiert
        returncode, stdout, _ = self._run(["list", "vms"])
        if f'"{vm_name}"' in stdout:
            logger.warning(f"VM '{vm_name}' existiert bereits.")
            response = input("Überschreiben? (j/n): ")
            if response.lower() != "j":
                return False
            self._run(["unregistervm", vm_name, "--delete"])

        # Import
        returncode, stdout, stderr = self._run(
            ["import", str(ova_path), "--vsys", "0", "--vmname", vm_name, "--cpus", "4", "--memory", "8192"], timeout=300
        )

        if returncode == 0:
            logger.info(f"✓ VM '{vm_name}' importiert")
            return True
        else:
            logger.error(f"Import fehlgeschlagen: {stderr}")
            return False

    def configure_kali_vm(self, vm_name: str) -> bool:
        """Konfiguriert Kali VM"""
        logger.info(f"Konfiguriere {vm_name}...")

        # Netzwerk (Host-Only für isoliertes Testing)
        self._run(["modifyvm", vm_name, "--nic1", "hostonly"])
        self._run(["modifyvm", vm_name, "--hostonlyadapter1", "vboxnet0"])

        # Optional: Zweiter Adapter für Internet (NAT)
        self._run(["modifyvm", vm_name, "--nic2", "nat"])

        # Shared Folder (für Zen-Integration)
        zen_path = Path(__file__).parent.parent.absolute()
        self._run(["sharedfolder", "add", vm_name, "--name", "zen-ai-pentest", "--hostpath", str(zen_path), "--automount"])

        logger.info("✓ Konfiguration abgeschlossen")
        return True

    def create_snapshot(self, vm_name: str, snapshot_name: str = "clean_state") -> bool:
        """Erstellt Snapshot"""
        logger.info(f"Erstelle Snapshot '{snapshot_name}'...")

        returncode, _, stderr = self._run(
            ["snapshot", vm_name, "take", snapshot_name, "--description", "Clean state for pentesting"], timeout=120
        )

        if returncode == 0:
            logger.info(f"✓ Snapshot '{snapshot_name}' erstellt")
            return True
        else:
            logger.error(f"Snapshot fehlgeschlagen: {stderr}")
            return False

    def setup_kali(self) -> bool:
        """Komplettes Kali Setup"""
        logger.info("=" * 60)
        logger.info("KALI LINUX VM SETUP")
        logger.info("=" * 60)

        # 1. Prüfungen
        self.check_virtualization()

        # 2. Download
        archive = self.download_kali()
        if not archive:
            return False

        # 3. Entpacken
        extract_dir = archive.parent / "kali-extracted"
        if not self.extract_7z(archive, extract_dir):
            return False

        # 4. OVA finden
        ova_files = list(extract_dir.glob("*.ova"))
        if not ova_files:
            logger.error("Keine .ova Datei gefunden")
            return False

        # 5. Import
        if not self.import_kali_vm(ova_files[0]):
            return False

        # 6. Konfiguration
        self.configure_kali_vm("kali-pentest")

        # 7. Snapshot
        self.create_snapshot("kali-pentest", "clean_state")

        logger.info("=" * 60)
        logger.info("✓ KALI LINUX VM BEREIT!")
        logger.info("=" * 60)
        logger.info("Starte mit:")
        logger.info("  VBoxManage startvm 'kali-pentest'")
        logger.info("oder:")
        logger.info("  VirtualBox Manager → Doppelklick auf VM")

        return True

    def create_windows_vm(self, vm_name: str = "win10-target") -> bool:
        """Erstellt Windows 10 VM"""
        logger.info("=" * 60)
        logger.info("WINDOWS 10 VM SETUP")
        logger.info("=" * 60)

        logger.info("Windows VM muss manuell erstellt werden.")
        logger.info("Anleitung:")
        logger.info("1. Windows 10 ISO herunterladen")
        logger.info("2. VirtualBox → Neu → Windows 10 (64-bit)")
        logger.info("3. RAM: 4096 MB, HDD: 50 GB")
        logger.info("4. Nach Installation: Guest Additions installieren")
        logger.info("5. Snapshot 'clean_state' erstellen")

        # Basis-VM erstellen (ohne ISO)
        vm_path = self.vm_base_path / vm_name

        self._run(["createvm", "--name", vm_name, "--ostype", "Windows10_64", "--register"])
        self._run(["modifyvm", vm_name, "--memory", "4096", "--cpus", "2"])
        self._run(["modifyvm", vm_name, "--vram", "128"])

        # HDD erstellen
        hdd_path = vm_path / "disk.vdi"
        self._run(["createhd", "--filename", str(hdd_path), "--size", "51200", "--variant", "Standard"])

        # Storage
        self._run(["storagectl", vm_name, "--name", "SATA", "--add", "sata"])
        self._run(
            [
                "storageattach",
                vm_name,
                "--storagectl",
                "SATA",
                "--port",
                "0",
                "--device",
                "0",
                "--type",
                "hdd",
                "--medium",
                str(hdd_path),
            ]
        )

        logger.info(f"✓ Windows VM '{vm_name}' erstellt")
        logger.info(f"  HDD: {hdd_path}")
        logger.info("  ISO manuell mounten und installieren!")

        return True

    def list_vms(self):
        """Listet alle VMs auf"""
        returncode, stdout, _ = self._run(["list", "vms"])
        if returncode == 0:
            print("\nVerfügbare VMs:")
            print("-" * 40)
            for line in stdout.strip().split("\n"):
                if line:
                    print(f"  {line}")

        returncode, stdout, _ = self._run(["list", "runningvms"])
        if returncode == 0 and stdout.strip():
            print("\nLaufende VMs:")
            print("-" * 40)
            for line in stdout.strip().split("\n"):
                if line:
                    print(f"  {line}")

    def export_config(self):
        """Exportiert VM-Konfiguration"""
        config = {
            "default_vm": "kali-pentest",
            "vms": {"kali-pentest": {"os_type": "kali", "username": "kali", "password": "kali", "snapshot": "clean_state"}},
        }

        config_path = Path(__file__).parent.parent / "config" / "vm_config.json"
        config_path.parent.mkdir(exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Konfiguration exportiert nach: {config_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Zen-AI-Pentest VM Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s --kali           # Kali Linux VM setup
  %(prog)s --windows        # Windows VM erstellen
  %(prog)s --list           # VMs auflisten
  %(prog)s --full           # Komplettes Setup
        """,
    )

    parser.add_argument("--kali", action="store_true", help="Kali Linux VM setup")
    parser.add_argument("--windows", action="store_true", help="Windows VM erstellen")
    parser.add_argument("--list", action="store_true", help="VMs auflisten")
    parser.add_argument("--export-config", action="store_true", help="Konfig exportieren")
    parser.add_argument("--full", action="store_true", help="Komplettes Setup (Kali + Config)")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    setup = VMSetup()

    if args.list:
        setup.list_vms()

    elif args.kali or args.full:
        success = setup.setup_kali()
        if success and args.full:
            setup.export_config()
        sys.exit(0 if success else 1)

    elif args.windows:
        setup.create_windows_vm()

    elif args.export_config:
        setup.export_config()


if __name__ == "__main__":
    main()
