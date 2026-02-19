#!/usr/bin/env python3
"""
WHOIS Lookup Modul für Zen-Ai-Pentest
======================================
Führt WHOIS-Abfragen durch:
- Domain-Registrierungsinformationen
- Registrar-Daten
- Name-Server
- Wichtige Daten (Creation, Expiration, Update)
- Abuse-Kontakte

Autor: ResearchBot-Team
Version: 1.0.0
Lizenz: MIT (Ethical Use Only)
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger("ZenAI.OSINT.WHOIS")


@dataclass
class WhoisRecord:
    """WHOIS-Record Datenklasse"""
    domain_name: str
    registrar: Optional[str] = None
    registrar_url: Optional[str] = None
    registrar_iana_id: Optional[str] = None
    
    # Kontaktinformationen
    registrant_name: Optional[str] = None
    registrant_organization: Optional[str] = None
    registrant_email: Optional[str] = None
    registrant_phone: Optional[str] = None
    registrant_country: Optional[str] = None
    
    admin_name: Optional[str] = None
    admin_organization: Optional[str] = None
    admin_email: Optional[str] = None
    admin_phone: Optional[str] = None
    
    tech_name: Optional[str] = None
    tech_organization: Optional[str] = None
    tech_email: Optional[str] = None
    tech_phone: Optional[str] = None
    
    # Daten
    creation_date: Optional[str] = None
    expiration_date: Optional[str] = None
    updated_date: Optional[str] = None
    
    # DNS
    name_servers: List[str] = field(default_factory=list)
    dnssec: Optional[str] = None
    
    # Status
    status: List[str] = field(default_factory=list)
    
    # Rohdaten
    raw: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class WhoisLookup:
    """
    WHOIS Lookup für Domain-Informationen
    
    Sammelt Registrierungsinformationen über Domains.
    """
    
    # WHOIS-Server für verschiedene TLDs
    WHOIS_SERVERS = {
        'com': 'whois.verisign-grs.com',
        'net': 'whois.verisign-grs.com',
        'org': 'whois.pir.org',
        'info': 'whois.afilias.net',
        'biz': 'whois.biz',
        'us': 'whois.nic.us',
        'uk': 'whois.nic.uk',
        'de': 'whois.denic.de',
        'fr': 'whois.nic.fr',
        'eu': 'whois.eu',
        'nl': 'whois.sidn.nl',
        'it': 'whois.nic.it',
        'es': 'whois.nic.es',
        'pl': 'whois.dns.pl',
        'ru': 'whois.tcinet.ru',
        'cn': 'whois.cnnic.cn',
        'jp': 'whois.jprs.jp',
        'io': 'whois.nic.io',
        'co': 'whois.nic.co',
        'ai': 'whois.nic.ai',
        'app': 'whois.nic.google',
        'dev': 'whois.nic.google',
        'cloud': 'whois.nic.cloud',
        'tech': 'whois.nic.tech',
    }
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialisiert den WHOIS-Lookup
        
        Args:
            config: Optionale Konfiguration
        """
        self.config = config or {}
        self.timeout = self.config.get('timeout', 10.0)
        self.cache: Dict[str, WhoisRecord] = {}
        
        logger.info("WhoisLookup initialisiert")
    
    async def lookup(self, domain: str) -> WhoisRecord:
        """
        Führt WHOIS-Lookup durch
        
        Args:
            domain: Ziel-Domain
            
        Returns:
            WhoisRecord mit allen Informationen
        """
        logger.info(f"Starte WHOIS-Lookup für: {domain}")
        
        if domain in self.cache:
            return self.cache[domain]
        
        # Extrahiere TLD
        tld = domain.split('.')[-1].lower()
        
        # Versuche Python-whois Bibliothek
        try:
            result = await self._lookup_python_whois(domain)
        except Exception as e:
            logger.debug(f"Python-whois fehlgeschlagen: {e}")
            result = WhoisRecord(domain_name=domain)
        
        # Fallback zu system whois
        if not result.registrar:
            try:
                result = await self._lookup_system_whois(domain)
            except Exception as e:
                logger.debug(f"System whois fehlgeschlagen: {e}")
        
        self.cache[domain] = result
        logger.info(f"WHOIS-Lookup abgeschlossen für: {domain}")
        return result
    
    async def _lookup_python_whois(self, domain: str) -> WhoisRecord:
        """Verwendet python-whois Bibliothek"""
        try:
            import whois
            
            w = whois.whois(domain)
            
            record = WhoisRecord(domain_name=domain)
            
            # Extrahiere Felder
            if hasattr(w, 'registrar') and w.registrar:
                record.registrar = w.registrar
            
            if hasattr(w, 'registrar_url') and w.registrar_url:
                record.registrar_url = w.registrar_url
            
            if hasattr(w, 'name_servers') and w.name_servers:
                if isinstance(w.name_servers, list):
                    record.name_servers = [ns.lower() for ns in w.name_servers]
                else:
                    record.name_servers = [w.name_servers.lower()]
            
            if hasattr(w, 'creation_date') and w.creation_date:
                record.creation_date = self._format_date(w.creation_date)
            
            if hasattr(w, 'expiration_date') and w.expiration_date:
                record.expiration_date = self._format_date(w.expiration_date)
            
            if hasattr(w, 'updated_date') and w.updated_date:
                record.updated_date = self._format_date(w.updated_date)
            
            if hasattr(w, 'status') and w.status:
                if isinstance(w.status, list):
                    record.status = w.status
                else:
                    record.status = [w.status]
            
            if hasattr(w, 'dnssec') and w.dnssec:
                record.dnssec = str(w.dnssec)
            
            # Kontaktinformationen
            if hasattr(w, 'registrant_name') and w.registrant_name:
                record.registrant_name = w.registrant_name
            
            if hasattr(w, 'registrant_organization') and w.registrant_organization:
                record.registrant_organization = w.registrant_organization
            
            if hasattr(w, 'registrant_email') and w.registrant_email:
                record.registrant_email = w.registrant_email
            
            if hasattr(w, 'admin_email') and w.admin_email:
                record.admin_email = w.admin_email
            
            if hasattr(w, 'tech_email') and w.tech_email:
                record.tech_email = w.tech_email
            
            return record
            
        except ImportError:
            raise Exception("python-whois nicht installiert")
    
    async def _lookup_system_whois(self, domain: str) -> WhoisRecord:
        """Verwendet system whois Kommando"""
        record = WhoisRecord(domain_name=domain)
        
        try:
            proc = await asyncio.create_subprocess_exec(
                'whois', domain,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.timeout
            )
            
            if stdout:
                raw_output = stdout.decode('utf-8', errors='ignore')
                record.raw = raw_output[:10000]  # Limit raw data
                
                # Parse wichtige Felder
                record = self._parse_whois_output(raw_output, record)
                
        except asyncio.TimeoutError:
            logger.warning(f"WHOIS-Timeout für {domain}")
        except Exception as e:
            logger.debug(f"WHOIS-Lookup Fehler: {e}")
        
        return record
    
    def _parse_whois_output(self, output: str, record: WhoisRecord) -> WhoisRecord:
        """Parst WHOIS-Output"""
        lines = output.split('\n')
        
        # Mapping von Feldnamen zu Record-Attributen
        field_mapping = {
            'registrar': ['Registrar:', 'registrar:', 'Registrar Name:'],
            'registrar_url': ['Registrar URL:', 'Registrar Website:'],
            'creation_date': ['Creation Date:', 'Created:', 'Domain Registration Date:'],
            'expiration_date': ['Registry Expiry Date:', 'Expiration Date:', 'Expires:'],
            'updated_date': ['Updated Date:', 'Last Updated:', 'Modified:'],
            'dnssec': ['DNSSEC:', 'Dnssec:'],
            'registrant_name': ['Registrant Name:', 'Registrant:'],
            'registrant_organization': ['Registrant Organization:', 'Registrant Org:'],
            'registrant_email': ['Registrant Email:', 'Registrant E-mail:'],
            'admin_email': ['Admin Email:', 'Admin E-mail:', 'Administrative Contact Email:'],
            'tech_email': ['Tech Email:', 'Tech E-mail:', 'Technical Contact Email:'],
        }
        
        name_servers = set()
        statuses = set()
        
        for line in lines:
            line = line.strip()
            
            # Überspringe Kommentare und leere Zeilen
            if not line or line.startswith('%') or line.startswith('#'):
                continue
            
            # Parse Name-Server
            for ns_prefix in ['Name Server:', 'Nameserver:', 'nserver:', 'Nameserver:']:
                if line.startswith(ns_prefix):
                    ns = line.split(':', 1)[1].strip().lower()
                    if ns:
                        name_servers.add(ns)
                    break
            
            # Parse Status
            for status_prefix in ['Status:', 'Domain Status:', 'status:']:
                if line.startswith(status_prefix):
                    status = line.split(':', 1)[1].strip()
                    if status:
                        statuses.add(status)
                    break
            
            # Parse andere Felder
            for field, prefixes in field_mapping.items():
                for prefix in prefixes:
                    if line.startswith(prefix):
                        value = line.split(':', 1)[1].strip()
                        if value and value not in ['', 'REDACTED', 'NOT DISCLOSED']:
                            setattr(record, field, value)
                        break
        
        record.name_servers = sorted(list(name_servers))
        record.status = sorted(list(statuses))
        
        return record
    
    def _format_date(self, date_value: Any) -> Optional[str]:
        """Formatiert Datums-Werte"""
        if isinstance(date_value, list):
            date_value = date_value[0]
        
        if isinstance(date_value, datetime):
            return date_value.isoformat()
        
        if isinstance(date_value, str):
            # Versuche verschiedene Formate zu parsen
            formats = [
                '%Y-%m-%d',
                '%Y-%m-%d %H:%M:%S',
                '%d-%m-%Y',
                '%d/%m/%Y',
                '%m/%d/%Y',
            ]
            
            for fmt in formats:
                try:
                    parsed = datetime.strptime(date_value.split('T')[0], fmt)
                    return parsed.isoformat()
                except:
                    continue
            
            return date_value
        
        return None
    
    def get_domain_age(self, domain: str) -> Optional[int]:
        """Gibt das Alter einer Domain in Tagen zurück"""
        if domain not in self.cache:
            return None
        
        record = self.cache[domain]
        if not record.creation_date:
            return None
        
        try:
            creation = datetime.fromisoformat(record.creation_date.replace('Z', '+00:00'))
            age = (datetime.now() - creation).days
            return age
        except:
            return None
    
    def is_expired(self, domain: str) -> bool:
        """Prüft ob eine Domain abgelaufen ist"""
        if domain not in self.cache:
            return False
        
        record = self.cache[domain]
        if not record.expiration_date:
            return False
        
        try:
            expiration = datetime.fromisoformat(record.expiration_date.replace('Z', '+00:00'))
            return datetime.now() > expiration
        except:
            return False
    
    def get_abuse_contacts(self, domain: str) -> List[str]:
        """Gibt Abuse-Kontakte zurück"""
        contacts = []
        
        if domain in self.cache:
            record = self.cache[domain]
            
            if record.registrant_email:
                contacts.append(record.registrant_email)
            if record.admin_email:
                contacts.append(record.admin_email)
            if record.tech_email:
                contacts.append(record.tech_email)
        
        return list(set(contacts))


async def main():
    """CLI-Interface für WHOIS-Lookup"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='WHOIS Lookup')
    parser.add_argument('domain', help='Ziel-Domain')
    parser.add_argument('-o', '--output', help='Ausgabedatei')
    parser.add_argument('-v', '--verbose', action='store_true')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    whois = WhoisLookup()
    result = await whois.lookup(args.domain)
    
    # Ausgabe
    print(json.dumps(result.to_dict(), indent=2))
    
    # Zusätzliche Informationen
    age = whois.get_domain_age(args.domain)
    if age is not None:
        print(f"\nDomain-Alter: {age} Tage")
    
    if whois.is_expired(args.domain):
        print("WARNUNG: Domain ist abgelaufen!")
    
    abuse_contacts = whois.get_abuse_contacts(args.domain)
    if abuse_contacts:
        print(f"\nAbuse-Kontakte: {', '.join(abuse_contacts)}")
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"\nErgebnisse gespeichert in: {args.output}")


if __name__ == '__main__':
    asyncio.run(main())
