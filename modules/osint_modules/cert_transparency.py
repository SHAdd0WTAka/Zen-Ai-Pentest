#!/usr/bin/env python3
"""
Certificate Transparency Modul für Zen-Ai-Pentest
==================================================
Durchsucht Certificate Transparency Logs:
- crt.sh Integration
- Google CT-Logs
- Subdomain-Discovery via Zertifikate
- Zertifikatsdetails
- Historische Zertifikate

Autor: ResearchBot-Team
Version: 1.0.0
Lizenz: MIT (Ethical Use Only)
"""

import asyncio
import logging
import json
import ssl
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger("ZenAI.OSINT.CT")


@dataclass
class Certificate:
    """Zertifikats-Datenklasse"""
    id: str
    domain: str
    issuer: Optional[str] = None
    subject: Optional[str] = None
    not_before: Optional[str] = None
    not_after: Optional[str] = None
    serial_number: Optional[str] = None
    san: List[str] = field(default_factory=list)
    fingerprint: Optional[str] = None
    raw: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class CertificateTransparency:
    """
    Certificate Transparency Log Scanner
    
    Durchsucht CT-Logs nach Zertifikaten und Subdomains.
    """
    
    # CT-Log-Quellen
    CT_SOURCES = {
        'crtsh': 'https://crt.sh',
        'certspotter': 'https://api.certspotter.com/v1',
    }
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialisiert den CT-Scanner
        
        Args:
            config: Optionale Konfiguration
        """
        self.config = config or {}
        self.timeout = self.config.get('timeout', 30.0)
        self.cache: Dict[str, List[Certificate]] = {}
        self.found_subdomains: Set[str] = set()
        
        logger.info("CertificateTransparency initialisiert")
    
    async def search(self, domain: str, include_expired: bool = True) -> Dict:
        """
        Durchsucht CT-Logs nach Zertifikaten
        
        Args:
            domain: Ziel-Domain
            include_expired: Auch abgelaufene Zertifikate einbeziehen
            
        Returns:
            Dictionary mit Zertifikaten und Subdomains
        """
        logger.info(f"Starte CT-Log-Suche für: {domain}")
        
        result = {
            'domain': domain,
            'certificates': [],
            'subdomains': [],
            'total_count': 0,
            'sources': []
        }
        
        # Sammle von verschiedenen Quellen
        tasks = [
            self._search_crtsh(domain, include_expired),
            self._search_certspotter(domain),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for source_result in results:
            if isinstance(source_result, Exception):
                logger.debug(f"CT-Quelle fehlgeschlagen: {source_result}")
                continue
            
            if source_result:
                result['certificates'].extend(source_result.get('certificates', []))
                result['subdomains'].extend(source_result.get('subdomains', []))
                if source_result.get('source'):
                    result['sources'].append(source_result['source'])
        
        # Deduplizieren
        seen_certs = set()
        unique_certs = []
        for cert in result['certificates']:
            cert_id = f"{cert.domain}:{cert.serial_number}"
            if cert_id not in seen_certs:
                seen_certs.add(cert_id)
                unique_certs.append(cert)
        
        result['certificates'] = [c.to_dict() for c in unique_certs]
        result['subdomains'] = sorted(list(set(result['subdomains'])))
        result['total_count'] = len(unique_certs)
        
        # Cache speichern
        self.cache[domain] = unique_certs
        self.found_subdomains.update(result['subdomains'])
        
        logger.info(f"CT-Log-Suche abgeschlossen: {len(unique_certs)} Zertifikate, "
                   f"{len(result['subdomains'])} Subdomains")
        
        return result
    
    async def _search_crtsh(self, domain: str, include_expired: bool = True) -> Dict:
        """Durchsucht crt.sh"""
        result = {
            'source': 'crt.sh',
            'certificates': [],
            'subdomains': []
        }
        
        try:
            import aiohttp
            
            # crt.sh API
            url = f"{self.CT_SOURCES['crtsh']}/?q=%.{domain}&output=json"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for entry in data:
                            # Extrahiere Zertifikatsinformationen
                            cert = Certificate(
                                id=str(entry.get('id', '')),
                                domain=entry.get('name_value', ''),
                                issuer=entry.get('issuer_name', ''),
                                not_before=entry.get('not_before'),
                                not_after=entry.get('not_after'),
                                serial_number=entry.get('serial_number')
                            )
                            
                            # Extrahiere Subdomains
                            name_value = entry.get('name_value', '')
                            for line in name_value.split('\n'):
                                line = line.strip().lower()
                                if line and line.endswith(domain):
                                    # Entferne Wildcards
                                    clean_domain = line.replace('*.', '')
                                    if clean_domain not in result['subdomains']:
                                        result['subdomains'].append(clean_domain)
                            
                            result['certificates'].append(cert)
                            
        except ImportError:
            logger.debug("aiohttp nicht verfügbar")
        except Exception as e:
            logger.debug(f"crt.sh Suche fehlgeschlagen: {e}")
        
        return result
    
    async def _search_certspotter(self, domain: str) -> Dict:
        """Durchsucht CertSpotter"""
        result = {
            'source': 'certspotter',
            'certificates': [],
            'subdomains': []
        }
        
        try:
            import aiohttp
            
            # CertSpotter API (ohne API-Key, limitiert)
            url = f"{self.CT_SOURCES['certspotter']}/issuances"
            params = {
                'domain': domain,
                'include_subdomains': 'true',
                'expand': 'dns_names'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for issuance in data:
                            # Extrahiere DNS-Namen
                            dns_names = issuance.get('dns_names', [])
                            
                            for dns_name in dns_names:
                                if dns_name.endswith(domain):
                                    result['subdomains'].append(dns_name.lower())
                            
                            # Erstelle Zertifikat
                            cert = Certificate(
                                id=issuance.get('id', ''),
                                domain=domain,
                                issuer=issuance.get('issuer', {}).get('name', ''),
                                not_before=issuance.get('not_before'),
                                not_after=issuance.get('not_after'),
                                san=dns_names
                            )
                            
                            result['certificates'].append(cert)
                            
        except ImportError:
            logger.debug("aiohttp nicht verfügbar")
        except Exception as e:
            logger.debug(f"CertSpotter Suche fehlgeschlagen: {e}")
        
        return result
    
    async def get_certificate_details(self, domain: str, port: int = 443) -> Optional[Dict]:
        """Holt Zertifikatsdetails direkt vom Server"""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(domain, port, ssl=context),
                timeout=10.0
            )
            
            ssl_obj = writer.get_extra_info('ssl_object')
            if ssl_obj:
                cert = ssl_obj.getpeercert()
                cipher = ssl_obj.cipher()
                version = ssl_obj.version()
                
                result = {
                    'subject': cert.get('subject'),
                    'issuer': cert.get('issuer'),
                    'not_before': cert.get('notBefore'),
                    'not_after': cert.get('notAfter'),
                    'serial_number': cert.get('serialNumber'),
                    'version': cert.get('version'),
                    'san': cert.get('subjectAltName', []),
                    'tls_version': version,
                    'cipher_suite': cipher[0] if cipher else None
                }
                
                writer.close()
                await writer.wait_closed()
                
                return result
                
        except Exception as e:
            logger.debug(f"Zertifikatsdetails konnten nicht abgerufen werden: {e}")
        
        return None
    
    def get_subdomains(self, domain: Optional[str] = None) -> List[str]:
        """Gibt gefundene Subdomains zurück"""
        if domain and domain in self.cache:
            subdomains = set()
            for cert in self.cache[domain]:
                subdomains.add(cert.domain)
                subdomains.update(cert.san)
            return sorted(list(subdomains))
        
        return sorted(list(self.found_subdomains))
    
    def get_expiring_certificates(self, days: int = 30) -> List[Certificate]:
        """Gibt bald ablaufende Zertifikate zurück"""
        expiring = []
        now = datetime.now()
        
        for domain, certs in self.cache.items():
            for cert in certs:
                if cert.not_after:
                    try:
                        expiry = datetime.fromisoformat(cert.not_after.replace('Z', '+00:00'))
                        days_until_expiry = (expiry - now).days
                        
                        if 0 <= days_until_expiry <= days:
                            expiring.append(cert)
                    except:
                        pass
        
        return expiring


async def main():
    """CLI-Interface für Certificate Transparency"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Certificate Transparency Scanner')
    parser.add_argument('domain', help='Ziel-Domain')
    parser.add_argument('--details', action='store_true', help='Zertifikatsdetails abrufen')
    parser.add_argument('-o', '--output', help='Ausgabedatei')
    parser.add_argument('-v', '--verbose', action='store_true')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    ct = CertificateTransparency()
    result = await ct.search(args.domain)
    
    # Ausgabe
    print(json.dumps(result, indent=2))
    
    # Zertifikatsdetails
    if args.details:
        details = await ct.get_certificate_details(args.domain)
        if details:
            print("\n=== Aktuelles Zertifikat ===")
            print(json.dumps(details, indent=2))
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nErgebnisse gespeichert in: {args.output}")


if __name__ == '__main__':
    asyncio.run(main())
