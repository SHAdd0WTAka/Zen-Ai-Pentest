#!/usr/bin/env python3
"""
Email-Harvester Modul für Zen-Ai-Pentest
=========================================
Sammelt E-Mail-Adressen von verschiedenen Quellen:
- Webseiten
- Search Engines
- Social Media
- Public APIs
- Mailing Lists
- WHOIS-Daten

Autor: ResearchBot-Team
Version: 1.0.0
Lizenz: MIT (Ethical Use Only)
"""

import asyncio
import logging
import re
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Set

logger = logging.getLogger("ZenAI.OSINT.EmailHarvester")


@dataclass
class EmailAddress:
    """E-Mail-Adressen Datenklasse"""

    email: str
    source: str
    confidence: float = 1.0
    context: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class EmailHarvester:
    """
    Email-Harvester für OSINT

    Sammelt E-Mail-Adressen aus verschiedenen Quellen.
    """

    # E-Mail-Muster
    EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

    # Häufige E-Mail-Formate
    EMAIL_FORMATS = [
        "{first}.{last}@{domain}",
        "{first}{last}@{domain}",
        "{first}_{last}@{domain}",
        "{first}-{last}@{domain}",
        "{f}{last}@{domain}",
        "{first}{l}@{domain}",
        "{first}@{domain}",
        "{last}@{domain}",
        "{first}.{last}@{domain}",
    ]

    # Disposable E-Mail-Domains
    DISPOSABLE_DOMAINS = {
        "tempmail.com",
        "throwaway.com",
        "mailinator.com",
        "guerrillamail.com",
        "sharklasers.com",
        "spam4.me",
        "trashmail.com",
        "yopmail.com",
        "temp.inbox.com",
        "mailnesia.com",
        "tempmailaddress.com",
        "burnermail.io",
        "temp-mail.org",
        "fakeinbox.com",
        "getairmail.com",
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialisiert den Email-Harvester

        Args:
            config: Optionale Konfiguration
        """
        self.config = config or {}
        self.timeout = self.config.get("timeout", 10.0)
        self.max_results = self.config.get("max_results", 100)
        self.verify_emails = self.config.get("verify_emails", False)

        self.found_emails: Dict[str, EmailAddress] = {}
        self.verified_emails: Set[str] = set()

        logger.info("EmailHarvester initialisiert")

    async def harvest(
        self, domain: str, sources: Optional[List[str]] = None
    ) -> Dict:
        """
        Sammelt E-Mail-Adressen für eine Domain

        Args:
            domain: Ziel-Domain
            sources: Liste der zu verwendenden Quellen

        Returns:
            Dictionary mit gefundenen E-Mail-Adressen
        """
        logger.info(f"Starte Email-Harvesting für: {domain}")

        if sources is None:
            sources = ["web", "whois", "permutations"]

        tasks = []

        if "web" in sources:
            tasks.append(self._harvest_from_web(domain))

        if "whois" in sources:
            tasks.append(self._harvest_from_whois(domain))

        if "permutations" in sources:
            tasks.append(self._harvest_from_permutations(domain))

        await asyncio.gather(*tasks, return_exceptions=True)

        # Entferne Duplikate und bereinige
        self._deduplicate_and_clean()

        # Verifiziere falls gewünscht
        if self.verify_emails:
            await self._verify_emails()

        result = {
            "domain": domain,
            "emails": [e.to_dict() for e in self.found_emails.values()],
            "total_found": len(self.found_emails),
            "verified": len(self.verified_emails),
            "common_formats": self._identify_common_formats(),
        }

        logger.info(
            f"Email-Harvesting abgeschlossen: {len(self.found_emails)} Adressen gefunden"
        )

        return result

    async def _harvest_from_web(self, domain: str) -> None:
        """Harvested E-Mails von Webseiten"""
        try:
            import aiohttp

            urls_to_check = [
                f"https://{domain}",
                f"https://www.{domain}",
                f"https://{domain}/contact",
                f"https://{domain}/about",
                f"https://{domain}/team",
                f"https://{domain}/imprint",
            ]

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            async with aiohttp.ClientSession(headers=headers) as session:
                for url in urls_to_check:
                    try:
                        async with session.get(
                            url, timeout=self.timeout, ssl=False
                        ) as response:
                            if response.status == 200:
                                text = await response.text()

                                # Suche E-Mails
                                emails = re.findall(
                                    self.EMAIL_PATTERN, text, re.IGNORECASE
                                )

                                for email in emails:
                                    if self._is_valid_email(email):
                                        self._add_email(
                                            email, "web", context=url
                                        )

                    except Exception as e:
                        logger.debug(f"Fehler beim Abrufen von {url}: {e}")

        except ImportError:
            logger.debug("aiohttp nicht verfügbar")

    async def _harvest_from_whois(self, domain: str) -> None:
        """Harvested E-Mails aus WHOIS-Daten"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "whois",
                domain,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)

            if stdout:
                output = stdout.decode("utf-8", errors="ignore")

                # Suche E-Mails
                emails = re.findall(self.EMAIL_PATTERN, output, re.IGNORECASE)

                for email in emails:
                    if self._is_valid_email(email):
                        self._add_email(email, "whois")

        except Exception as e:
            logger.debug(f"WHOIS-Harvesting fehlgeschlagen: {e}")

    async def _harvest_from_permutations(self, domain: str) -> None:
        """Generiert E-Mail-Adressen aus Permutationen"""
        # Häufige Vornamen und Nachnamen
        common_names = [
            ("john", "doe"),
            ("jane", "doe"),
            ("admin", ""),
            ("support", ""),
            ("info", ""),
            ("contact", ""),
            ("sales", ""),
            ("marketing", ""),
            ("hr", ""),
            ("help", ""),
            ("webmaster", ""),
            ("postmaster", ""),
            ("hostmaster", ""),
            ("abuse", ""),
            ("security", ""),
            ("noc", ""),
            ("billing", ""),
            ("legal", ""),
            ("press", ""),
            ("careers", ""),
        ]

        for first, last in common_names:
            for format_str in self.EMAIL_FORMATS:
                email = format_str.format(
                    first=first,
                    last=last,
                    f=first[0] if first else "",
                    l=last[0] if last else "",
                    domain=domain,
                )

                # Füge nur als potenziell hinzu (niedrigere Confidence)
                if self._is_valid_email(email):
                    self._add_email(email, "permutation", confidence=0.3)

    def _is_valid_email(self, email: str) -> bool:
        """Prüft ob eine E-Mail-Adresse gültig ist"""
        # Grundlegende Validierung
        if not re.match(self.EMAIL_PATTERN, email):
            return False

        # Prüfe auf Disposable-Domains
        domain = email.split("@")[1].lower()
        if domain in self.DISPOSABLE_DOMAINS:
            return False

        # Prüfe auf offensichtlich ungültige Adressen
        invalid_patterns = [
            r"example\.com$",
            r"test\.com$",
            r"localhost$",
            r"\.local$",
            r"\.invalid$",
            r"\.test$",
            r"^noreply@",
            r"^no-reply@",
            r"^donotreply@",
        ]

        for pattern in invalid_patterns:
            if re.search(pattern, email, re.IGNORECASE):
                return False

        return True

    def _add_email(
        self,
        email: str,
        source: str,
        confidence: float = 1.0,
        context: Optional[str] = None,
    ) -> None:
        """Fügt eine E-Mail-Adresse hinzu"""
        email = email.lower().strip()

        if email in self.found_emails:
            # Aktualisiere bestehenden Eintrag
            existing = self.found_emails[email]
            existing.confidence = max(existing.confidence, confidence)
            if context and not existing.context:
                existing.context = context
        else:
            # Neuer Eintrag
            self.found_emails[email] = EmailAddress(
                email=email,
                source=source,
                confidence=confidence,
                context=context,
            )

    def _deduplicate_and_clean(self) -> None:
        """Entfernt Duplikate und bereinigt die Liste"""
        # Entferne Einträge über dem Limit
        if len(self.found_emails) > self.max_results:
            # Sortiere nach Confidence und behalte die besten
            sorted_emails = sorted(
                self.found_emails.items(),
                key=lambda x: x[1].confidence,
                reverse=True,
            )
            self.found_emails = dict(sorted_emails[: self.max_results])

    async def _verify_emails(self) -> None:
        """Verifiziert E-Mail-Adressen (DNS/MX-Check)"""
        for email in list(self.found_emails.keys()):
            domain = email.split("@")[1]

            try:
                # MX-Record prüfen
                import dns.resolver

                answers = dns.resolver.resolve(domain, "MX")

                if answers:
                    self.verified_emails.add(email)

            except Exception:
                # Kein MX-Record gefunden
                pass

    def _identify_common_formats(self) -> List[str]:
        """Identifiziert häufige E-Mail-Formate"""
        formats_found = []

        for email in self.found_emails.keys():
            local_part = email.split("@")[0]

            if (
                "." in local_part
                and "_" not in local_part
                and "-" not in local_part
            ):
                formats_found.append("first.last")
            elif "_" in local_part:
                formats_found.append("first_last")
            elif "-" in local_part:
                formats_found.append("first-last")
            elif len(local_part) <= 3:
                formats_found.append("initials")
            else:
                formats_found.append("other")

        # Zähle Häufigkeiten
        from collections import Counter

        format_counts = Counter(formats_found)

        return [
            f"{fmt} ({count})" for fmt, count in format_counts.most_common(5)
        ]

    def get_emails_by_source(self, source: str) -> List[EmailAddress]:
        """Gibt E-Mails nach Quelle gefiltert zurück"""
        return [e for e in self.found_emails.values() if e.source == source]

    def get_emails_by_confidence(
        self, min_confidence: float = 0.5
    ) -> List[EmailAddress]:
        """Gibt E-Mails mit Mindest-Confidence zurück"""
        return [
            e
            for e in self.found_emails.values()
            if e.confidence >= min_confidence
        ]


async def main():
    """CLI-Interface für Email-Harvester"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Email Harvester")
    parser.add_argument("domain", help="Ziel-Domain")
    parser.add_argument(
        "--verify", action="store_true", help="E-Mails verifizieren"
    )
    parser.add_argument("-o", "--output", help="Ausgabedatei")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config = {"verify_emails": args.verify}
    harvester = EmailHarvester(config)
    result = await harvester.harvest(args.domain)

    # Ausgabe
    print(json.dumps(result, indent=2))

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nErgebnisse gespeichert in: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
