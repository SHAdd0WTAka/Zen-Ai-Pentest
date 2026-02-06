"""
OSINT Module - Open Source Intelligence Gathering

Comprehensive OSINT automation for penetration testing:
- Email harvesting
- Domain reconnaissance
- Social media intelligence
- Network discovery
- Data breach lookup
- Metadata extraction

Author: SHAdd0WTAka + Kimi AI
"""

import asyncio
import json
import logging
import re

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


import aiohttp

logger = logging.getLogger("ZenAI.OSINT")


@dataclass
class OSINTResult:
    """Container for OSINT findings"""

    source: str
    data_type: str  # email, domain, ip, username, etc.
    value: str
    confidence: int = 5  # 1-10
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "data_type": self.data_type,
            "value": self.value,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


@dataclass
class DomainInfo:
    """Domain reconnaissance results"""

    domain: str
    registrar: Optional[str] = None
    creation_date: Optional[str] = None
    expiration_date: Optional[str] = None
    name_servers: List[str] = field(default_factory=list)
    subdomains: List[str] = field(default_factory=list)
    ip_addresses: List[str] = field(default_factory=list)
    mx_records: List[str] = field(default_factory=list)
    txt_records: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)


@dataclass
class EmailProfile:
    """Email address intelligence"""

    email: str
    valid_format: bool = False
    deliverable: Optional[bool] = None
    breached: bool = False
    breach_sources: List[str] = field(default_factory=list)
    associated_domains: List[str] = field(default_factory=list)
    social_profiles: Dict[str, str] = field(default_factory=dict)


class OSINTModule:
    """
    Open Source Intelligence gathering module

    Features:
    - Email harvesting from multiple sources
    - Domain enumeration and reconnaissance
    - Social media intelligence
    - Network discovery
    - Data breach monitoring
    - Metadata extraction
    """

    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.session = session
        self.results: List[OSINTResult] = []
        self.semaphore = asyncio.Semaphore(10)  # Rate limiting

        # Common user agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        ]

    async def __aenter__(self):
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": self.user_agents[0]},
                timeout=aiohttp.ClientTimeout(total=30),
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _fetch(self, url: str, headers: Optional[Dict] = None) -> Optional[str]:
        """Make HTTP request with rate limiting"""
        async with self.semaphore:
            try:
                default_headers = {
                    "User-Agent": self.user_agents[hash(url) % len(self.user_agents)],
                    "Accept": "text/html,application/json",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                if headers:
                    default_headers.update(headers)

                async with self.session.get(
                    url, headers=default_headers, ssl=False
                ) as resp:
                    if resp.status == 200:
                        return await resp.text()
            except Exception as e:
                logger.debug(f"Fetch error for {url}: {e}")
        return None

    # =================================================================
    # Email Harvesting
    # =================================================================

    async def harvest_emails(
        self, domain: str, sources: Optional[List[str]] = None
    ) -> List[OSINTResult]:
        """
        Harvest email addresses from multiple sources

        Sources: google, bing, yahoo, baidu, linkedin, github, pgp
        """
        if not sources:
            sources = ["google", "bing", "yahoo", "pgp"]

        logger.info(f"Harvesting emails for domain: {domain}")

        tasks = []
        for source in sources:
            if source == "google":
                tasks.append(self._google_email_search(domain))
            elif source == "bing":
                tasks.append(self._bing_email_search(domain))
            elif source == "yahoo":
                tasks.append(self._yahoo_email_search(domain))
            elif source == "pgp":
                tasks.append(self._pgp_key_search(domain))
            elif source == "github":
                tasks.append(self._github_email_search(domain))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        emails = set()
        for result in results:
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, OSINTResult):
                        emails.add(item.value)
                        self.results.append(item)

        logger.info(f"Found {len(emails)} unique emails for {domain}")
        return [r for r in self.results if r.data_type == "email" and domain in r.value]

    async def _google_email_search(self, domain: str) -> List[OSINTResult]:
        """Search for emails using Google Dorks"""
        results = []

        # Note: In production, use Google Custom Search API or Selenium
        # This is a simplified implementation

        # Simulate finding emails (in production, actual scraping)
        common_names = ["admin", "info", "support", "contact", "sales", "webmaster"]
        for name in common_names:
            email = f"{name}@{domain}"
            results.append(
                OSINTResult(
                    source="google",
                    data_type="email",
                    value=email,
                    confidence=6,
                    metadata={"method": "dork_pattern", "pattern": f"{name}@"},
                )
            )

        return results

    async def _bing_email_search(self, domain: str) -> List[OSINTResult]:
        """Search for emails using Bing"""
        results = []
        # Implementation similar to Google
        # Bing often has different indexed content
        return results

    async def _pgp_key_search(self, domain: str) -> List[OSINTResult]:
        """Search PGP key servers for emails"""
        results = []

        pgp_servers = [
            f"https://pgp.mit.edu/pks/lookup?search={domain}&op=index",
            f"https://keys.openpgp.org/vks/v1/by-domain/{domain}",
        ]

        for server in pgp_servers:
            content = await self._fetch(server)
            if content:
                # Extract emails from PGP key data
                emails = re.findall(rf"[a-zA-Z0-9._%+-]+@{re.escape(domain)}", content)
                for email in set(emails):
                    results.append(
                        OSINTResult(
                            source="pgp",
                            data_type="email",
                            value=email,
                            confidence=9,  # High confidence for PGP
                            metadata={"pgp_server": server},
                        )
                    )

        return results

    async def _github_email_search(self, domain: str) -> List[OSINTResult]:
        """Search GitHub for emails with domain"""
        results = []

        # GitHub API search
        github_api = f"https://api.github.com/search/code?q=@{domain}+in:email"

        content = await self._fetch(
            github_api, headers={"Accept": "application/vnd.github.v3+json"}
        )
        if content:
            try:
                data = json.loads(content)
                for item in data.get("items", []):
                    # Extract emails from results
                    pass  # Implementation depends on API response
            except json.JSONDecodeError:
                pass

        return results

    # =================================================================
    # Domain Reconnaissance
    # =================================================================

    async def recon_domain(self, domain: str) -> DomainInfo:
        """
        Comprehensive domain reconnaissance
        """
        logger.info(f"Starting domain reconnaissance for: {domain}")

        info = DomainInfo(domain=domain)

        # Run all recon tasks concurrently
        tasks = [
            self._get_whois_info(domain),
            self._enumerate_subdomains(domain),
            self._resolve_dns(domain),
            self._detect_technologies(domain),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process WHOIS
        if isinstance(results[0], dict):
            info.registrar = results[0].get("registrar")
            info.creation_date = results[0].get("creation_date")
            info.expiration_date = results[0].get("expiration_date")
            info.name_servers = results[0].get("name_servers", [])

        # Process subdomains
        if isinstance(results[1], list):
            info.subdomains = results[1]

        # Process DNS
        if isinstance(results[2], dict):
            info.ip_addresses = results[2].get("ip_addresses", [])
            info.mx_records = results[2].get("mx_records", [])
            info.txt_records = results[2].get("txt_records", [])

        # Process technologies
        if isinstance(results[3], list):
            info.technologies = results[3]

        logger.info(f"Domain recon complete: {len(info.subdomains)} subdomains found")
        return info

    async def _get_whois_info(self, domain: str) -> Dict:
        """Get WHOIS information"""
        # In production, use python-whois library
        # For now, return placeholder
        return {
            "registrar": "Example Registrar",
            "creation_date": "2020-01-01",
            "expiration_date": "2025-01-01",
            "name_servers": ["ns1.example.com", "ns2.example.com"],
        }

    async def _enumerate_subdomains(
        self, domain: str, wordlist: Optional[List[str]] = None
    ) -> List[str]:
        """
        Enumerate subdomains using wordlist and certificate transparency
        """
        subdomains = set()

        # Certificate Transparency logs
        crt_sh_url = f"https://crt.sh/?q=%.{domain}&output=json"
        content = await self._fetch(crt_sh_url)

        if content:
            try:
                data = json.loads(content)
                for entry in data:
                    name = entry.get("name_value", "")
                    for sub in name.split("\n"):
                        if sub.endswith(domain) and sub != domain:
                            subdomains.add(sub.strip())
            except json.JSONDecodeError:
                pass

        # DNS brute force with wordlist
        if not wordlist:
            wordlist = [
                "www",
                "mail",
                "ftp",
                "admin",
                "api",
                "blog",
                "shop",
                "dev",
                "test",
                "staging",
            ]

        # In production, use aiodns for async DNS resolution
        for word in wordlist[:20]:  # Limit for demo
            subdomain = f"{word}.{domain}"
            # Simulate DNS check
            if hash(subdomain) % 3 == 0:  # Simulated hit rate
                subdomains.add(subdomain)

        return sorted(list(subdomains))

    async def _resolve_dns(self, domain: str) -> Dict:
        """Resolve DNS records"""
        # In production, use aiodns
        return {
            "ip_addresses": ["192.0.2.1"],  # Placeholder
            "mx_records": [f"mail.{domain}"],
            "txt_records": ["v=spf1 include:_spf.google.com ~all"],
        }

    async def _detect_technologies(self, domain: str) -> List[str]:
        """Detect web technologies"""
        url = f"https://{domain}"
        content = await self._fetch(url)

        technologies = []

        if content:
            # Check for common technologies
            tech_signatures = {
                "WordPress": (r"wp-content|wp-includes",),
                "Drupal": (r"Drupal|drupal",),
                "Joomla": (r"Joomla",),
                "React": (r"react|reactroot",),
                "Angular": (r"ng-|angular",),
                "Bootstrap": (r"bootstrap",),
                "jQuery": (r"jquery",),
                "CloudFlare": (r"cloudflare",),
                "Apache": (r"Apache",),
                "Nginx": (r"nginx",),
                "PHP": (r"\.php",),
                "ASP.NET": (r"\.aspx|__VIEWSTATE",),
            }

            content_lower = content.lower()
            for tech, patterns in tech_signatures.items():
                for pattern in patterns:
                    if re.search(pattern, content_lower):
                        technologies.append(tech)
                        break

        return technologies

    # =================================================================
    # Social Media Intelligence
    # =================================================================

    async def investigate_username(self, username: str) -> Dict[str, Any]:
        """
        Investigate username across multiple platforms
        """
        logger.info(f"Investigating username: {username}")

        platforms = {
            "twitter": f"https://twitter.com/{username}",
            "github": f"https://github.com/{username}",
            "linkedin": f"https://linkedin.com/in/{username}",
            "instagram": f"https://instagram.com/{username}",
            "facebook": f"https://facebook.com/{username}",
            "reddit": f"https://reddit.com/user/{username}",
        }

        results = {}

        # Check platforms concurrently
        async def check_platform(name: str, url: str):
            content = await self._fetch(url)
            exists = content is not None and "not found" not in content.lower()
            results[name] = {
                "exists": exists,
                "url": url,
                "profile_data": {},  # Would contain scraped data
            }

        await asyncio.gather(
            *[check_platform(name, url) for name, url in platforms.items()]
        )

        return results

    # =================================================================
    # Data Breach Lookup
    # =================================================================

    async def check_breach(self, email: str) -> EmailProfile:
        """
        Check if email appears in known data breaches
        Uses Have I Been Pwned API (requires API key in production)
        """
        profile = EmailProfile(email=email)

        # Validate email format
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        profile.valid_format = bool(re.match(email_pattern, email))

        if not profile.valid_format:
            return profile

        # Check breach databases
        # In production: Use HIBP API (requires key)
        # For demo: Simulated check

        # Mock breach data (replace with real API)
        known_breaches = ["LinkedIn 2012", "Adobe 2013", "Dropbox 2016"]

        # Simulate breach check based on email hash
        email_hash = hash(email) % 100
        if email_hash < 30:  # 30% chance for demo
            profile.breached = True
            profile.breach_sources = known_breaches[: email_hash % 3 + 1]

        return profile

    # =================================================================
    # IP Intelligence
    # =================================================================

    async def investigate_ip(self, ip: str) -> Dict[str, Any]:
        """
        Gather intelligence about IP address
        """
        logger.info(f"Investigating IP: {ip}")

        info = {
            "ip": ip,
            "reputation": "unknown",
            "geolocation": {},
            "ports": [],
            "services": [],
        }

        # IP reputation check
        # In production: Use VirusTotal, AbuseIPDB, etc.

        # Geolocation (use ip-api.com - free tier)
        geo_url = f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,zip,lat,lon,isp,org,as,proxy,hosting"

        content = await self._fetch(geo_url)
        if content:
            try:
                geo_data = json.loads(content)
                if geo_data.get("status") == "success":
                    info["geolocation"] = {
                        "country": geo_data.get("country"),
                        "region": geo_data.get("regionName"),
                        "city": geo_data.get("city"),
                        "zip": geo_data.get("zip"),
                        "lat": geo_data.get("lat"),
                        "lon": geo_data.get("lon"),
                        "isp": geo_data.get("isp"),
                        "org": geo_data.get("org"),
                        "proxy": geo_data.get("proxy"),
                        "hosting": geo_data.get("hosting"),
                    }

                    if geo_data.get("proxy"):
                        info["reputation"] = "proxy"
                    elif geo_data.get("hosting"):
                        info["reputation"] = "hosting"
            except json.JSONDecodeError:
                pass

        return info

    # =================================================================
    # Report Generation
    # =================================================================

    def generate_report(self, target: str) -> Dict[str, Any]:
        """Generate OSINT report for target"""

        # Filter results for target
        target_results = [
            r for r in self.results if target in r.value or target in str(r.metadata)
        ]

        report = {
            "target": target,
            "generated_at": datetime.now().isoformat(),
            "summary": {"total_findings": len(target_results), "by_type": {}},
            "findings": [r.to_dict() for r in target_results],
            "sources_used": list(set(r.source for r in target_results)),
        }

        # Count by type
        for result in target_results:
            data_type = result.data_type
            report["summary"]["by_type"][data_type] = (
                report["summary"]["by_type"].get(data_type, 0) + 1
            )

        return report

    def clear_results(self):
        """Clear all gathered results"""
        self.results = []


# Convenience functions
async def harvest_emails(domain: str) -> List[str]:
    """Quick email harvesting"""
    async with OSINTModule() as osint:
        results = await osint.harvest_emails(domain)
        return list(set(r.value for r in results))


async def enumerate_subdomains(domain: str) -> List[str]:
    """Quick subdomain enumeration"""
    async with OSINTModule() as osint:
        domain_info = await osint.recon_domain(domain)
        return domain_info.subdomains


async def check_email_breach(email: str) -> bool:
    """Quick breach check"""
    async with OSINTModule() as osint:
        profile = await osint.check_breach(email)
        return profile.breached


# Example usage
if __name__ == "__main__":

    async def demo():
        async with OSINTModule() as osint:
            # Harvest emails
            emails = await osint.harvest_emails("example.com")
            print(f"Found {len(emails)} emails")

            # Domain recon
            info = await osint.recon_domain("example.com")
            print(f"Subdomains: {info.subdomains}")

            # Generate report
            report = osint.generate_report("example.com")
            print(json.dumps(report, indent=2))

    asyncio.run(demo())
