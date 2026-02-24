#!/usr/bin/env python3
"""
DNS-Enumeration Modul für Zen-Ai-Pentest
========================================
Erfasst DNS-Informationen:
- A, AAAA, MX, NS, TXT, SOA, CNAME Records
- DNSSEC-Informationen
- Zone Transfer Versuche
- Reverse DNS
- SPF/DMARC/DKIM Records

Autor: ResearchBot-Team
Version: 1.0.0
Lizenz: MIT (Ethical Use Only)
"""

import asyncio
import logging
import socket
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

logger = logging.getLogger("ZenAI.OSINT.DNS")


@dataclass
class DNSRecord:
    """DNS-Record Datenklasse"""

    record_type: str
    name: str
    value: str
    ttl: int = 0
    priority: Optional[int] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class DNSEnumerator:
    """
    DNS-Enumerator für Information-Gathering

    Sammelt umfassende DNS-Informationen über ein Ziel.
    """

    # Standard DNS-Record-Typen
    RECORD_TYPES = [
        "A",
        "AAAA",
        "MX",
        "NS",
        "TXT",
        "SOA",
        "CNAME",
        "PTR",
        "SRV",
        "CAA",
    ]

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialisiert den DNS-Enumerator

        Args:
            config: Optionale Konfiguration
        """
        self.config = config or {}
        self.timeout = self.config.get("timeout", 5.0)
        self.dns_servers = self.config.get(
            "dns_servers",
            [
                "8.8.8.8",  # Google
                "8.8.4.4",  # Google
                "1.1.1.1",  # Cloudflare
                "1.0.0.1",  # Cloudflare
                "9.9.9.9",  # Quad9
            ],
        )
        self.cache: Dict[str, Dict] = {}

        logger.info("DNSEnumerator initialisiert")

    async def enumerate(self, domain: str) -> Dict:
        """
        Führt vollständige DNS-Enumeration durch

        Args:
            domain: Ziel-Domain

        Returns:
            Dictionary mit allen DNS-Informationen
        """
        logger.info(f"Starte DNS-Enumeration für: {domain}")

        if domain in self.cache:
            return self.cache[domain]

        result = {
            "domain": domain,
            "records": {},
            "dnssec": {},
            "zone_transfer": False,
            "reverse_dns": {},
            "email_security": {},
            "nameservers": [],
            "timestamp": None,
        }

        # Sammle alle Record-Typen
        for record_type in self.RECORD_TYPES:
            records = await self._query_records(domain, record_type)
            if records:
                result["records"][record_type] = records

        # Extrahiere Nameserver
        if "NS" in result["records"]:
            result["nameservers"] = [
                r["value"] for r in result["records"]["NS"]
            ]

        # Prüfe DNSSEC
        result["dnssec"] = await self._check_dnssec(domain)

        # Versuche Zone Transfer
        result["zone_transfer"] = await self._try_zone_transfer(domain)

        # Reverse DNS für gefundene IPs
        if "A" in result["records"]:
            for record in result["records"]["A"]:
                ip = record["value"]
                reverse = await self._reverse_dns_lookup(ip)
                if reverse:
                    result["reverse_dns"][ip] = reverse

        # Email-Security Records
        result["email_security"] = await self._check_email_security(domain)

        result["timestamp"] = asyncio.get_event_loop().time()
        self.cache[domain] = result

        logger.info(f"DNS-Enumeration abgeschlossen für: {domain}")
        return result

    async def _query_records(
        self, domain: str, record_type: str
    ) -> List[Dict]:
        """Fragt DNS-Records ab"""
        records = []

        try:
            # Verwende dnspython falls verfügbar
            import dns.resolver

            resolver = dns.resolver.Resolver()
            resolver.timeout = self.timeout
            resolver.lifetime = self.timeout * 2

            # Setze DNS-Server
            if self.dns_servers:
                resolver.nameservers = self.dns_servers

            try:
                answers = resolver.resolve(domain, record_type)

                for answer in answers:
                    record = {
                        "type": record_type,
                        "name": domain,
                        "value": str(answer),
                        "ttl": (
                            answers.rrset.ttl
                            if hasattr(answers, "rrset")
                            else 0
                        ),
                    }

                    # Extrahiere Priority für MX-Records
                    if record_type == "MX":
                        record["priority"] = answer.preference

                    records.append(record)

            except dns.resolver.NXDOMAIN:
                logger.debug(f"NXDOMAIN für {domain} {record_type}")
            except dns.resolver.NoAnswer:
                logger.debug(f"Keine Antwort für {domain} {record_type}")
            except Exception as e:
                logger.debug(f"DNS-Abfrage fehlgeschlagen: {e}")

        except ImportError:
            # Fallback zu socket
            if record_type == "A":
                try:
                    addr_info = await asyncio.get_event_loop().getaddrinfo(
                        domain, None, family=socket.AF_INET
                    )
                    for info in addr_info:
                        records.append(
                            {
                                "type": "A",
                                "name": domain,
                                "value": info[4][0],
                                "ttl": 0,
                            }
                        )
                except (socket.gaierror, socket.herror, OSError):
                    pass

        return records

    async def _check_dnssec(self, domain: str) -> Dict:
        """Prüft DNSSEC-Status"""
        result = {
            "enabled": False,
            "validated": False,
            "algorithm": None,
            "key_tag": None,
        }

        try:
            import dns.dnssec
            import dns.resolver

            # Frage DNSKEY-Records ab
            try:
                resolver = dns.resolver.Resolver()
                answers = resolver.resolve(domain, "DNSKEY")

                result["enabled"] = True

                for answer in answers:
                    result["algorithm"] = dns.dnssec.algorithm_to_text(
                        answer.algorithm
                    )
                    result["key_tag"] = answer.key_tag
                    break

            except dns.resolver.NoAnswer:
                pass
            except Exception as e:
                logger.debug(f"DNSSEC-Check fehlgeschlagen: {e}")

        except ImportError:
            logger.debug("dnspython nicht verfügbar für DNSSEC-Check")

        return result

    async def _try_zone_transfer(self, domain: str) -> bool:
        """Versucht DNS Zone Transfer (AXFR)"""
        try:
            import dns.query
            import dns.resolver
            import dns.zone

            # Finde NS-Records
            ns_records = await self._query_records(domain, "NS")

            for ns_record in ns_records:
                ns_server = ns_record["value"].rstrip(".")
                try:
                    zone = dns.zone.from_xfr(
                        dns.query.xfr(ns_server, domain, timeout=5)
                    )

                    if zone:
                        logger.info(
                            f"Zone Transfer erfolgreich von {ns_server}"
                        )
                        return True

                except Exception as e:
                    logger.debug(
                        f"Zone Transfer von {ns_server} fehlgeschlagen: {e}"
                    )

        except ImportError:
            logger.debug("dnspython nicht verfügbar für Zone Transfer")
        except Exception as e:
            logger.debug(f"Zone Transfer fehlgeschlagen: {e}")

        return False

    async def _reverse_dns_lookup(self, ip: str) -> Optional[str]:
        """Führt Reverse DNS-Lookup durch"""
        try:
            hostname = await asyncio.get_event_loop().run_in_executor(
                None, socket.gethostbyaddr, ip
            )
            return hostname[0]
        except (socket.herror, socket.gaierror):
            return None

    async def _check_email_security(self, domain: str) -> Dict:
        """Prüft Email-Security-Records (SPF, DMARC, DKIM)"""
        result = {"spf": None, "dmarc": None, "dkim": None, "mx": []}

        # SPF-Record
        spf_records = await self._query_records(domain, "TXT")
        for record in spf_records:
            value = record["value"]
            if "v=spf1" in value:
                result["spf"] = {
                    "record": value,
                    "policy": self._parse_spf_policy(value),
                }
                break

        # DMARC-Record
        dmarc_domain = f"_dmarc.{domain}"
        dmarc_records = await self._query_records(dmarc_domain, "TXT")
        for record in dmarc_records:
            value = record["value"]
            if "v=DMARC1" in value:
                result["dmarc"] = {
                    "record": value,
                    "policy": self._parse_dmarc_policy(value),
                }
                break

        # DKIM-Records (versuche gängige Selektoren)
        dkim_selectors = [
            "default",
            "google",
            "mail",
            "selector1",
            "selector2",
            "dkim",
        ]
        for selector in dkim_selectors:
            dkim_domain = f"{selector}._domainkey.{domain}"
            dkim_records = await self._query_records(dkim_domain, "TXT")
            if dkim_records:
                result["dkim"] = {
                    "selector": selector,
                    "record": dkim_records[0]["value"],
                }
                break

        # MX-Records
        mx_records = await self._query_records(domain, "MX")
        result["mx"] = [
            {"server": r["value"], "priority": r.get("priority", 0)}
            for r in mx_records
        ]

        return result

    def _parse_spf_policy(self, spf_record: str) -> str:
        """Parst SPF-Policy aus Record"""
        if "~all" in spf_record:
            return "softfail"
        elif "-all" in spf_record:
            return "fail"
        elif "?all" in spf_record:
            return "neutral"
        elif "+all" in spf_record:
            return "pass"
        return "unknown"

    def _parse_dmarc_policy(self, dmarc_record: str) -> str:
        """Parst DMARC-Policy aus Record"""
        if "p=reject" in dmarc_record:
            return "reject"
        elif "p=quarantine" in dmarc_record:
            return "quarantine"
        elif "p=none" in dmarc_record:
            return "none"
        return "unknown"

    def get_nameservers(self, domain: str) -> List[str]:
        """Gibt die Nameserver einer Domain zurück"""
        if domain in self.cache:
            return self.cache[domain].get("nameservers", [])
        return []

    def get_ip_addresses(self, domain: str) -> List[str]:
        """Gibt alle IP-Adressen einer Domain zurück"""
        ips = []
        if domain in self.cache:
            records = self.cache[domain].get("records", {})
            if "A" in records:
                ips.extend([r["value"] for r in records["A"]])
            if "AAAA" in records:
                ips.extend([r["value"] for r in records["AAAA"]])
        return ips


async def main():
    """CLI-Interface für DNS-Enumeration"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="DNS Enumerator")
    parser.add_argument("domain", help="Ziel-Domain")
    parser.add_argument("-o", "--output", help="Ausgabedatei")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    enumerator = DNSEnumerator()
    result = await enumerator.enumerate(args.domain)

    # Ausgabe
    print(json.dumps(result, indent=2))

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nErgebnisse gespeichert in: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
