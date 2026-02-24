#!/usr/bin/env python3
"""
Web-Scraper Modul für Zen-Ai-Pentest
====================================
Scraped Webseiten nach Informationen:
- Meta-Tags und Open Graph
- Links und Ressourcen
- Formulare und Eingabefelder
- Kommentare
- E-Mail-Adressen
- Interne Pfade
- Sicherheits-Header

Autor: ResearchBot-Team
Version: 1.0.0
Lizenz: MIT (Ethical Use Only)
"""

import asyncio
import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

logger = logging.getLogger("ZenAI.OSINT.WebScraper")


@dataclass
class ScrapedPage:
    """Gescrapte Seiten-Datenklasse"""

    url: str
    title: Optional[str] = None
    meta_tags: Dict[str, str] = field(default_factory=dict)
    links: List[str] = field(default_factory=list)
    forms: List[Dict] = field(default_factory=list)
    scripts: List[str] = field(default_factory=list)
    stylesheets: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    comments: List[str] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


class WebScraper:
    """
    Web-Scraper für Information-Gathering

    Extrahiert Informationen aus Webseiten.
    """

    # Zu suchende Muster
    PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        "api_key": r'(?:api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{16,})',
        "secret": r'(?:secret|token|password)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{8,})',
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialisiert den Web-Scraper

        Args:
            config: Optionale Konfiguration
        """
        self.config = config or {}
        self.timeout = self.config.get("timeout", 10.0)
        self.max_pages = self.config.get("max_pages", 10)
        self.follow_redirects = self.config.get("follow_redirects", True)
        self.user_agent = self.config.get(
            "user_agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0",
        )

        self.visited_urls: Set[str] = set()
        self.found_emails: Set[str] = set()
        self.found_links: Set[str] = set()
        self.pages: List[ScrapedPage] = []

        logger.info("WebScraper initialisiert")

    async def scrape(self, url: str, depth: int = 1) -> ScrapedPage:
        """
        Scraped eine Webseite

        Args:
            url: Ziel-URL
            depth: Crawling-Tiefe

        Returns:
            ScrapedPage mit extrahierten Informationen
        """
        logger.info(f"Starte Web-Scraping für: {url}")

        # Normalisiere URL
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        # Crawle Seiten
        await self._crawl(url, depth)

        # Hauptseite zurückgeben
        for page in self.pages:
            if page.url == url or page.url.rstrip("/") == url.rstrip("/"):
                return page

        # Fallback: erste Seite
        return self.pages[0] if self.pages else ScrapedPage(url=url)

    async def _crawl(self, url: str, depth: int) -> None:
        """Crawlt rekursiv durch die Webseite"""
        if depth <= 0 or len(self.visited_urls) >= self.max_pages:
            return

        if url in self.visited_urls:
            return

        self.visited_urls.add(url)

        # Lade Seite
        page = await self._fetch_page(url)
        if not page:
            return

        self.pages.append(page)

        # Folge Links
        if depth > 1:
            base_domain = urlparse(url).netloc

            for link in page.links[:20]:  # Limit Links
                parsed = urlparse(link)

                # Nur interne Links
                if parsed.netloc == base_domain or not parsed.netloc:
                    absolute_url = urljoin(url, link)
                    await self._crawl(absolute_url, depth - 1)

    async def _fetch_page(self, url: str) -> Optional[ScrapedPage]:
        """Lädt eine Webseite"""
        try:
            import aiohttp

            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    allow_redirects=self.follow_redirects,
                    ssl=False,
                ) as response:

                    if response.status != 200:
                        logger.debug(f"HTTP {response.status} für {url}")
                        return None

                    content_type = response.headers.get("Content-Type", "")
                    if "text/html" not in content_type:
                        logger.debug(
                            f"Nicht-HTML Content-Type: {content_type}"
                        )
                        return None

                    html = await response.text()

                    return self._parse_html(url, html, dict(response.headers))

        except ImportError:
            logger.debug("aiohttp nicht verfügbar")
        except Exception as e:
            logger.debug(f"Fehler beim Laden von {url}: {e}")

        return None

    def _parse_html(self, url: str, html: str, headers: Dict) -> ScrapedPage:
        """Parst HTML-Inhalt"""
        page = ScrapedPage(url=url, headers=headers)

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")

            # Titel
            title_tag = soup.find("title")
            if title_tag:
                page.title = title_tag.get_text(strip=True)

            # Meta-Tags
            for meta in soup.find_all("meta"):
                name = meta.get("name", meta.get("property", ""))
                content = meta.get("content", "")
                if name and content:
                    page.meta_tags[name] = content

            # Links
            for link in soup.find_all("a", href=True):
                href = link["href"]
                absolute = urljoin(url, href)
                if absolute not in page.links:
                    page.links.append(absolute)
                    self.found_links.add(absolute)

            # Formulare
            for form in soup.find_all("form"):
                form_data = {
                    "action": form.get("action", ""),
                    "method": form.get("method", "get").upper(),
                    "inputs": [],
                }

                for input_tag in form.find_all(
                    ["input", "textarea", "select"]
                ):
                    input_data = {
                        "name": input_tag.get("name", ""),
                        "type": input_tag.get("type", "text"),
                        "required": input_tag.get("required") is not None,
                    }
                    form_data["inputs"].append(input_data)

                page.forms.append(form_data)

            # Scripts
            for script in soup.find_all("script", src=True):
                src = script["src"]
                absolute = urljoin(url, src)
                if absolute not in page.scripts:
                    page.scripts.append(absolute)

            # Stylesheets
            for css in soup.find_all("link", rel="stylesheet", href=True):
                href = css["href"]
                absolute = urljoin(url, href)
                if absolute not in page.stylesheets:
                    page.stylesheets.append(absolute)

            # Images
            for img in soup.find_all("img", src=True):
                src = img["src"]
                absolute = urljoin(url, src)
                if absolute not in page.images:
                    page.images.append(absolute)

            # Kommentare
            comments = soup.find_all(
                string=lambda text: isinstance(text, str)
                and text.strip().startswith("<!--")
            )
            for comment in comments:
                text = comment.strip()
                if len(text) > 10:  # Nur längere Kommentare
                    page.comments.append(text[:500])  # Limit Länge

            # E-Mail-Adressen
            emails = re.findall(self.PATTERNS["email"], html)
            for email in emails:
                if email not in page.emails:
                    page.emails.append(email)
                    self.found_emails.add(email)

        except ImportError:
            logger.debug("BeautifulSoup nicht verfügbar, verwende Regex")

            # Fallback zu Regex
            # Titel
            title_match = re.search(
                r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL
            )
            if title_match:
                page.title = title_match.group(1).strip()

            # Links
            links = re.findall(
                r'href=["\']([^"\']+)["\']', html, re.IGNORECASE
            )
            for link in links:
                absolute = urljoin(url, link)
                if absolute not in page.links:
                    page.links.append(absolute)

            # E-Mails
            emails = re.findall(self.PATTERNS["email"], html)
            page.emails = list(set(emails))

        return page

    def get_all_emails(self) -> List[str]:
        """Gibt alle gefundenen E-Mail-Adressen zurück"""
        return sorted(list(self.found_emails))

    def get_all_links(self) -> List[str]:
        """Gibt alle gefundenen Links zurück"""
        return sorted(list(self.found_links))

    def get_forms(self) -> List[Dict]:
        """Gibt alle gefundenen Formulare zurück"""
        forms = []
        for page in self.pages:
            forms.extend(page.forms)
        return forms

    def get_internal_links(self, base_url: str) -> List[str]:
        """Gibt nur interne Links zurück"""
        base_domain = urlparse(base_url).netloc
        internal = []

        for link in self.found_links:
            parsed = urlparse(link)
            if parsed.netloc == base_domain or not parsed.netloc:
                internal.append(link)

        return internal


async def main():
    """CLI-Interface für Web-Scraper"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Web Scraper")
    parser.add_argument("url", help="Ziel-URL")
    parser.add_argument(
        "-d", "--depth", type=int, default=1, help="Crawling-Tiefe"
    )
    parser.add_argument("-o", "--output", help="Ausgabedatei")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = WebScraper()
    result = await scraper.scrape(args.url, depth=args.depth)

    # Ausgabe
    print(json.dumps(result.to_dict(), indent=2))

    # Zusammenfassung
    print("\n=== Zusammenfassung ===")
    print(f"Gecrawlte Seiten: {len(scraper.pages)}")
    print(f"Gefundene E-Mails: {len(scraper.get_all_emails())}")
    print(f"Gefundene Links: {len(scraper.get_all_links())}")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"\nErgebnisse gespeichert in: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
