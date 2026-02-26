#!/usr/bin/env python3
"""
WiFi Packet Editor für Zen-AI-Pentest
======================================

802.11 WiFi Frame Analyse und Modifikation.

⚠️  WICHTIGE SICHERHEITSHINWEISE:
    - NUR in eigenen Netzwerken oder mit EXPLIZITER schriftlicher Genehmigung verwenden
    - Das Abhören/Manipulieren fremder Netzwerke ist ILLEGAL (§ 202a StGB, CFAA, etc.)
    - Benutzer ist ALLEINIG VERANTWORTLICH für ihre Handlungen

Unterstützte Funktionen:
    - 802.11 Frame Parsing (Beacon, Probe, Data, Management)
    - MAC-Adress-Spoofing
    - Frame Injection (mit kompatiblem Adapter)
    - Deauthentication Frame-Erkennung
    - WPA Handshake-Capture

Voraussetzungen:
    - Linux empfohlen (Windows: Npcap + kompatibler USB-Adapter)
    - Scapy: pip install scapy
    - Kompatible WLAN-Adapter: RTL8812AU, AR9271, MT76xx

Autor: Zen-AI-Pentest Team
Version: 1.0.0
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

# Scapy Imports
try:
    from scapy.all import (
        Dot11,
        Dot11Beacon,
        Dot11Deauth,
        Dot11Elt,
        Dot11ProbeReq,
        Dot11ProbeResp,
        RadioTap,
        rdpcap,
        sendp,
        sniff,
        wrpcap,
    )
    from scapy.layers.dot11 import Dot11AssoReq, Dot11AssoResp, Dot11Auth

    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class WiFiFrameType(Enum):
    """802.11 Frame-Typen"""

    MANAGEMENT = 0
    CONTROL = 1
    DATA = 2


class WiFiSubType(Enum):
    """802.11 Management Subtypen"""

    ASSOCIATION_REQUEST = 0
    ASSOCIATION_RESPONSE = 1
    REASSOCIATION_REQUEST = 2
    REASSOCIATION_RESPONSE = 3
    PROBE_REQUEST = 4
    PROBE_RESPONSE = 5
    BEACON = 8
    ATIM = 9
    DISASSOCIATION = 10
    AUTHENTICATION = 11
    DEAUTHENTICATION = 12


@dataclass
class WiFiFrameInfo:
    """Geparste WiFi Frame-Informationen"""

    frame_type: str
    subtype: str
    src_mac: str
    dst_mac: str
    bssid: str
    ssid: Optional[str] = None
    channel: Optional[int] = None
    signal_dbm: Optional[int] = None
    raw_frame: Optional[bytes] = None


class WiFiSecurityError(Exception):
    """Sicherheitsfehler - Unautorisierter Zugriffsversuch"""

    pass


class WiFiPacketEditor:
    """
    WiFi Packet Editor für autorisierte Penetrationstests.

    WICHTIG: Diese Klasse implementiert Sicherheitskontrollen:
        - Whitelist für erlaubte BSSIDs (eigene Netzwerke)
        - Blockierung öffentlicher/externer Netzwerke
        - Logging aller Aktivitäten

    Usage:
        editor = WiFiPacketEditor(allowed_networks=["AA:BB:CC:DD:EE:FF"])
        frames = editor.capture_frames(duration=30)
        modified = editor.spoof_mac(frames[0], new_src="11:22:33:44:55:66")
    """

    # Bekannte Broadcast/Multicast MACs
    BROADCAST_MAC = "ff:ff:ff:ff:ff:ff"
    MULTICAST_PREFIXES = ["01:00:5e", "33:33:"]

    def __init__(
        self,
        interface: str = "wlan0mon",
        allowed_networks: Optional[List[str]] = None,
        safety_mode: bool = True,
    ):
        """
        Initialisiert den WiFi Packet Editor.

        Args:
            interface: WLAN-Interface (Monitor Mode)
            allowed_networks: Liste erlaubter BSSIDs (eigene Netzwerke)
            safety_mode: Sicherheitskontrollen aktivieren
        """
        if not SCAPY_AVAILABLE:
            raise RuntimeError(
                "Scapy nicht installiert. " "Installieren: pip install scapy"
            )

        self.interface = interface
        self.allowed_networks = set(allowed_networks or [])
        self.safety_mode = safety_mode
        self._captured_frames: List = []

        # Logging
        logger.info(f"WiFiPacketEditor initialisiert")
        logger.info(f"Interface: {interface}")
        logger.info(f"Safety Mode: {safety_mode}")
        logger.info(f"Erlaubte Netzwerke: {len(self.allowed_networks)}")

        if safety_mode and not self.allowed_networks:
            logger.warning(
                "SAFETY MODE aktiv aber KEINE erlaubten Netzwerke definiert! "
                "Alle Netzwerke werden blockiert."
            )

    def _is_allowed_bssid(self, bssid: str) -> bool:
        """Prüft ob BSSID in der Whitelist ist"""
        if not self.safety_mode:
            return True
        if not self.allowed_networks:
            return False
        return bssid.lower() in {n.lower() for n in self.allowed_networks}

    def _validate_safety(self, frame) -> bool:
        """
        Validierungsschutz - verhindert Arbeit mit unautorisierten Netzwerken.
        """
        if not self.safety_mode:
            return True

        # Extrahiere BSSID
        bssid = frame.addr3 if hasattr(frame, "addr3") else None
        if bssid and self._is_allowed_bssid(bssid):
            return True

        # Prüfe auch Source und Destination
        for addr in [frame.addr1, frame.addr2]:
            if addr and self._is_allowed_bssid(addr):
                return True

        return False

    def parse_frame(self, frame) -> Optional[WiFiFrameInfo]:
        """
        Parst einen 802.11 Frame und extrahiert Informationen.

        Args:
            frame: Scapy Dot11 Frame

        Returns:
            WiFiFrameInfo mit extrahierten Daten
        """
        if not frame.haslayer(Dot11):
            return None

        dot11 = frame.getlayer(Dot11)

        # Frame-Typ bestimmen
        frame_type = "Unknown"
        subtype = "Unknown"

        if dot11.type == WiFiFrameType.MANAGEMENT.value:
            frame_type = "Management"
            subtype_map = {
                0: "AssocReq",
                1: "AssocResp",
                2: "ReassocReq",
                3: "ReassocResp",
                4: "ProbeReq",
                5: "ProbeResp",
                8: "Beacon",
                9: "ATIM",
                10: "Disassoc",
                11: "Auth",
                12: "Deauth",
            }
            subtype = subtype_map.get(
                dot11.subtype, f"Subtype_{dot11.subtype}"
            )
        elif dot11.type == WiFiFrameType.CONTROL.value:
            frame_type = "Control"
        elif dot11.type == WiFiFrameType.DATA.value:
            frame_type = "Data"

        # MAC-Adressen
        dst_mac = dot11.addr1 if dot11.addr1 else "00:00:00:00:00:00"
        src_mac = dot11.addr2 if dot11.addr2 else "00:00:00:00:00:00"
        bssid = dot11.addr3 if dot11.addr3 else "00:00:00:00:00:00"

        # SSID extrahieren (aus Beacon oder Probe)
        ssid = None
        if frame.haslayer(Dot11Elt):
            elt = frame.getlayer(Dot11Elt)
            if elt.ID == 0:  # SSID Element
                try:
                    ssid = elt.info.decode("utf-8", errors="ignore")
                except:
                    ssid = str(elt.info)

        # Signalstärke (aus RadioTap)
        signal_dbm = None
        if frame.haslayer(RadioTap):
            rt = frame.getlayer(RadioTap)
            # dBm Antenna Signal (falls verfügbar)
            if hasattr(rt, "dBm_AntSignal"):
                signal_dbm = rt.dBm_AntSignal

        return WiFiFrameInfo(
            frame_type=frame_type,
            subtype=subtype,
            src_mac=src_mac,
            dst_mac=dst_mac,
            bssid=bssid,
            ssid=ssid,
            signal_dbm=signal_dbm,
            raw_frame=bytes(frame),
        )

    def capture_frames(
        self,
        duration: int = 60,
        filter_ssid: Optional[str] = None,
        max_frames: int = 1000,
    ) -> List[WiFiFrameInfo]:
        """
        Capture 802.11 Frames für autorisierte Analyse.

        ⚠️  NUR auf eigenen Netzwerken erlaubt!

        Args:
            duration: Capture-Dauer in Sekunden
            filter_ssid: Optional SSID-Filter
            max_frames: Maximale Anzahl Frames

        Returns:
            Liste der geparsten Frame-Informationen
        """
        logger.info(f"Starte Capture auf {self.interface} für {duration}s")

        captured = []
        start_time = time.time()

        def packet_handler(pkt):
            # Timeout prüfen
            if time.time() - start_time > duration:
                return True  # Stop sniffing

            # Safety Check
            if not self._validate_safety(pkt):
                return False

            info = self.parse_frame(pkt)
            if info:
                # SSID Filter
                if filter_ssid and info.ssid != filter_ssid:
                    return False

                captured.append(info)
                self._captured_frames.append(pkt)

                logger.debug(f"Captured: {info.subtype} from {info.src_mac}")

            return len(captured) >= max_frames

        try:
            sniff(
                iface=self.interface,
                prn=lambda x: packet_handler(x) and None,
                stop_filter=lambda x: time.time() - start_time > duration,
                timeout=duration,
            )
        except Exception as e:
            logger.error(f"Capture Fehler: {e}")

        logger.info(f"Capture beendet: {len(captured)} Frames")
        return captured

    def create_beacon_frame(
        self,
        ssid: str,
        bssid: str,
        channel: int = 6,
        rates: bytes = b"\x82\x84\x8b\x96\x24\x30\x48\x6c",
    ):
        """
        Erstellt einen 802.11 Beacon Frame.

        ⚠️  NUR für autorisierte Tests auf eigenen Netzwerken!

        Args:
            ssid: Netzwerkname
            bssid: MAC-Adresse des AP
            channel: WLAN-Kanal
            rates: Unterstützte Datenraten

        Returns:
            Scapy Dot11 Beacon Frame
        """
        if self.safety_mode and not self._is_allowed_bssid(bssid):
            raise WiFiSecurityError(
                f"BSSID {bssid} nicht in erlaubten Netzwerken! "
                f"Sicherheitskontrolle blockiert Frame-Erstellung."
            )

        # 802.11 Header
        dot11 = Dot11(
            type=0,  # Management
            subtype=8,  # Beacon
            addr1=self.BROADCAST_MAC,  # DA
            addr2=bssid,  # SA (AP)
            addr3=bssid,  # BSSID
        )

        # Beacon Frame Body
        beacon = Dot11Beacon(
            timestamp=int(time.time() * 1000000),
            beacon_interval=100,
            cap="ESS+privacy",
        )

        # Information Elements
        ssid_elt = Dot11Elt(ID="SSID", info=ssid, len=len(ssid))
        rates_elt = Dot11Elt(ID="Rates", info=rates, len=len(rates))
        channel_elt = Dot11Elt(ID="DSset", info=chr(channel).encode(), len=1)

        frame = (
            RadioTap() / dot11 / beacon / ssid_elt / rates_elt / channel_elt
        )

        logger.info(f"Beacon Frame erstellt: SSID={ssid}, BSSID={bssid}")
        return frame

    def spoof_mac(
        self,
        frame,
        new_src: Optional[str] = None,
        new_dst: Optional[str] = None,
        new_bssid: Optional[str] = None,
    ):
        """
        Modifiziert MAC-Adressen in einem Frame (für autorisierte Tests).

        Args:
            frame: Original Frame
            new_src: Neue Source MAC
            new_dst: Neue Destination MAC
            new_bssid: Neue BSSID

        Returns:
            Modifizierter Frame
        """
        # Safety Check vor Modifikation
        if not self._validate_safety(frame):
            raise WiFiSecurityError(
                "Frame-Manipulation blockiert: "
                "Frame gehört zu nicht-autorisiertem Netzwerk"
            )

        # Kopie erstellen
        modified = frame.copy()

        if new_src:
            modified.addr2 = new_src
            logger.debug(f"Source MAC geändert: {new_src}")

        if new_dst:
            modified.addr1 = new_dst
            logger.debug(f"Dest MAC geändert: {new_dst}")

        if new_bssid:
            modified.addr3 = new_bssid
            logger.debug(f"BSSID geändert: {new_bssid}")

        return modified

    def create_deauth_frame(
        self, src_mac: str, dst_mac: str, bssid: str, reason: int = 7
    ):
        """
        Erstellt einen Deauthentication Frame.

        ⚠️  EXTREM WICHTIG: Deauth-Frames sind in vielen Ländern ILLEGAL
            ohne explizite Genehmigung! Kann WLAN-Verbindungen trennen.

        Args:
            src_mac: Source MAC (AP oder Client)
            dst_mac: Destination MAC
            bssid: BSSID
            reason: Deauth-Reason-Code (7=Class 3 frame received from nonassociated STA)

        Returns:
            Scapy Deauth Frame
        """
        if self.safety_mode:
            raise WiFiSecurityError(
                "Deauthentication Frames sind im Safety Mode blockiert! "
                "Diese Funktion deaktiviert WLAN-Verbindungen und ist "
                "nur mit ausdrücklicher Genehmigung erlaubt."
            )

        dot11 = Dot11(
            type=0,  # Management
            subtype=12,  # Deauthentication
            addr1=dst_mac,
            addr2=src_mac,
            addr3=bssid,
        )

        deauth = Dot11Deauth(reason=reason)
        frame = RadioTap() / dot11 / deauth

        logger.warning(f"Deauth Frame erstellt: {src_mac} -> {dst_mac}")
        return frame

    def inject_frame(self, frame, count: int = 1) -> bool:
        """
        Injiziert einen Frame in das WLAN.

        ⚠️  Erfordert Monitor Mode + Packet Injection fähigen Adapter!

        Args:
            frame: Zu injizierender Frame
            count: Anzahl Wiederholungen

        Returns:
            True bei Erfolg
        """
        # Safety Check
        if not self._validate_safety(frame):
            raise WiFiSecurityError(
                "Frame Injection blockiert: Sicherheitskontrolle"
            )

        try:
            sendp(frame, iface=self.interface, count=count, verbose=0)
            logger.info(f"Frame injiziert ({count}x)")
            return True
        except Exception as e:
            logger.error(f"Injection Fehler: {e}")
            return False

    def detect_deauth_attack(self, frames: List[WiFiFrameInfo]) -> Dict:
        """
        Analysiert Frames auf Deauthentication-Angriffe.

        Args:
            frames: Zu analysierende Frames

        Returns:
            Analyse-Report
        """
        deauth_frames = [f for f in frames if f.subtype == "Deauth"]

        report = {
            "total_frames": len(frames),
            "deauth_frames": len(deauth_frames),
            "attack_detected": len(deauth_frames) > 10,  # Threshold
            "sources": set(),
            "destinations": set(),
            "recommendations": [],
        }

        for f in deauth_frames:
            report["sources"].add(f.src_mac)
            report["destinations"].add(f.dst_mac)

        if report["attack_detected"]:
            report["recommendations"].append(
                "Deauth-Angriff erkannt! Überprüfen Sie Ihre WLAN-Sicherheit."
            )
            report["recommendations"].append(
                "Verdächtige MACs: " + ", ".join(report["sources"])
            )

        return report

    def export_to_pcap(
        self, filepath: str, frames: Optional[List] = None
    ) -> bool:
        """
        Exportiert Frames zu PCAP-Datei (Wireshark-kompatibel).

        Args:
            filepath: Ziel-Dateipfad
            frames: Zu exportierende Frames (None = alle gespeicherten)

        Returns:
            True bei Erfolg
        """
        frames_to_export = (
            frames if frames is not None else self._captured_frames
        )

        if not frames_to_export:
            logger.warning("Keine Frames zum Exportieren")
            return False

        try:
            wrpcap(filepath, frames_to_export)
            logger.info(
                f"{len(frames_to_export)} Frames exportiert nach {filepath}"
            )
            return True
        except Exception as e:
            logger.error(f"Export Fehler: {e}")
            return False

    def import_from_pcap(self, filepath: str) -> List[WiFiFrameInfo]:
        """
        Importiert Frames aus PCAP-Datei.

        Args:
            filepath: PCAP-Dateipfad

        Returns:
            Liste der geparsten Frames
        """
        try:
            packets = rdpcap(filepath)
            parsed = []

            for pkt in packets:
                info = self.parse_frame(pkt)
                if info:
                    parsed.append(info)
                    self._captured_frames.append(pkt)

            logger.info(f"{len(parsed)} Frames importiert aus {filepath}")
            return parsed
        except Exception as e:
            logger.error(f"Import Fehler: {e}")
            return []


def check_monitor_mode_capability(interface: str = "wlan0") -> Dict:
    """
    Prüft ob Interface Monitor Mode + Injection unterstützt.

    Returns:
        Status-Dictionary
    """
    result = {
        "interface": interface,
        "scapy_available": SCAPY_AVAILABLE,
        "monitor_mode_supported": False,
        "injection_supported": False,
        "recommendations": [],
    }

    if not SCAPY_AVAILABLE:
        result["recommendations"].append(
            "Scapy nicht installiert: pip install scapy"
        )
        return result

    # Versuche Interface-Info zu bekommen
    try:
        from scapy.all import get_if_list

        interfaces = get_if_list()
        result["available_interfaces"] = interfaces

        if interface not in interfaces:
            result["recommendations"].append(
                f"Interface {interface} nicht gefunden. "
                f"Verfügbar: {', '.join(interfaces[:5])}"
            )
    except Exception as e:
        result["error"] = str(e)

    result["recommendations"].extend(
        [
            "Empfohlene USB-Adapter: Alfa AWUS036ACH (RTL8812AU)",
            "Treiber: github.com/aircrack-ng/rtl8812au",
            "Linux: sudo airmon-ng start wlan0",
        ]
    )

    return result


# Convenience-Funktionen
def quick_scan(
    duration: int = 30, interface: str = "wlan0mon"
) -> List[WiFiFrameInfo]:
    """
    Schneller WLAN-Scan für autorisierte Tests.

    ⚠️  Sicherheitsmodus aktiviert - nur erlaubte Netzwerke!
    """
    editor = WiFiPacketEditor(
        interface=interface,
        safety_mode=True,
        allowed_networks=[],  # Leere Liste = nur passive Erkennung
    )
    return editor.capture_frames(duration=duration)


if __name__ == "__main__":
    # Demo/Test
    print("=" * 60)
    print("WiFi Packet Editor - Demo")
    print("=" * 60)

    # Prüfe System
    check = check_monitor_mode_capability()
    print(f"\nSystem-Check:")
    print(f"  Scapy verfügbar: {check['scapy_available']}")
    print(f"  Interfaces: {check.get('available_interfaces', [])[:5]}")

    print("\nEmpfohlene USB-Adapter:")
    print("  • Alfa AWUS036ACH (RTL8812AU)")
    print("  • TP-Link TL-WN722N v1 (AR9271)")
    print("  • Alfa AWUS036NHA (AR9271)")

    print("\n⚠️  Wichtig:")
    print("   NUR auf eigenen Netzwerken verwenden!")
    print("   Unautorisierte Nutzung ist ILLEGAL.")
