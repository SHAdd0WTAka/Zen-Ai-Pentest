"""Scapy Integration für Zen-AI-Pentest"""
import logging
from typing import List, Dict

try:
    from scapy.all import IP, TCP, ICMP, ARP, Ether, sr1, srp, conf
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

logger = logging.getLogger(__name__)

class ScapyScanner:
    def __init__(self):
        if not SCAPY_AVAILABLE:
            raise RuntimeError("Scapy nicht installiert")
        conf.verb = 0
    
    def tcp_syn_scan(self, target: str, ports: List[int]) -> List[Dict]:
        results = []
        for port in ports:
            syn_pkt = IP(dst=target) / TCP(dport=port, flags='S')
            resp = sr1(syn_pkt, timeout=2, verbose=0)
            
            if resp and resp.haslayer(TCP) and resp.getlayer(TCP).flags == 0x12:
                results.append({'port': port, 'state': 'open'})
                rst_pkt = IP(dst=target) / TCP(dport=port, flags='R')
                sr1(rst_pkt, timeout=1, verbose=0)
            elif resp and resp.getlayer(TCP).flags == 0x14:
                results.append({'port': port, 'state': 'closed'})
            else:
                results.append({'port': port, 'state': 'filtered'})
        return results
    
    def arp_scan(self, network: str) -> List[Dict]:
        arp = ARP(pdst=network)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        result = srp(ether/arp, timeout=2, verbose=0)[0]
        return [{'ip': r.psrc, 'mac': r.hwsrc} for s, r in result]
    
    def icmp_ping(self, target: str) -> Dict:
        pkt = IP(dst=target) / ICMP()
        resp = sr1(pkt, timeout=2, verbose=0)
        return {'target': target, 'alive': resp is not None}

# LangChain Tool
from langchain_core.tools import tool

@tool
def scapy_syn_scan(target: str, ports: str) -> str:
    """TCP SYN Port Scan mit Scapy"""
    scanner = ScapyScanner()
    port_list = [int(p) for p in ports.split(",")]
    results = scanner.tcp_syn_scan(target, port_list)
    open_ports = [r['port'] for r in results if r['state'] == 'open']
    return f"Open ports: {open_ports}" if open_ports else "No open ports found"

@tool
def scapy_arp_scan(network: str) -> str:
    """ARP Scan für lokales Netzwerk"""
    scanner = ScapyScanner()
    results = scanner.arp_scan(network)
    return f"Found {len(results)} hosts: " + ", ".join([r['ip'] for r in results])
