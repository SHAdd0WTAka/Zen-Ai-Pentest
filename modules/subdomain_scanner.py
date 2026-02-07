#!/usr/bin/env python3
"""
Subdomain Scanner Module
Advanced subdomain enumeration with multiple techniques
Author: SHAdd0WTAka
"""

import asyncio
import json
import logging
import socket
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

import aiohttp
import dns.resolver

logger = logging.getLogger("ZenAI")


@dataclass
class SubdomainResult:
    """Result container for subdomain enumeration"""

    subdomain: str
    ip_addresses: List[str] = field(default_factory=list)
    status_code: Optional[int] = None
    server_header: Optional[str] = None
    technologies: List[str] = field(default_factory=list)
    is_alive: bool = False
    screenshot_path: Optional[str] = None
    discovered_at: datetime = field(default_factory=datetime.now)


class SubdomainScanner:
    """
    Advanced subdomain enumeration scanner
    Combines multiple techniques: DNS enumeration, wordlist brute-force,
    certificate transparency logs, and OSINT
    """

    # Common subdomain wordlist
    DEFAULT_WORDLIST = [
        # Core services
        "www", "mail", "ftp", "localhost", "webmail", "smtp", "pop", "ns1", "ns2",
        # Admin interfaces
        "admin", "portal", "test", "ns", "api", "dev", "www2", "ns3", "blog",
        # Infrastructure
        "vpn", "www1", "imap", "forum", "routing", "gate", "m", "mobile", "dns",
        "blog", "webdisk", "lists", "support", "remote", "web", "host", "proxy",
        # Development & Staging
        "dev", "staging", "demo", "beta", "alpha", "preview", "uat", "qa",
        "test", "testing", "sandbox", "stage", "development", "integration",
        # API & Services
        "api", "api-v1", "api-v2", "api-v3", "rest", "graphql", "gql", "ws",
        "wss", "service", "services", "app", "apps", "cdn", "static", "assets",
        "media", "files", "data", "download", "downloads", "upload", "uploads",
        # Corporate
        "corp", "corporate", "intranet", "extranet", "internal", "private",
        "secure", "auth", "sso", "login", "account", "accounts", "user", "users",
        "customer", "customers", "client", "clients", "partner", "partners",
        # Communication
        "chat", "mail", "email", "webmail", "smtp", "pop3", "imap", "mx",
        "mx1", "mx2", "news", "newsletter", "rss", "feed", "social",
        # Cloud & Infrastructure
        "cloud", "aws", "azure", "gcp", "k8s", "kubernetes", "docker", "registry",
        "jenkins", "ci", "cd", "git", "gitlab", "github", "bitbucket", "svn",
        # Monitoring & Management
        "monitor", "monitoring", "nagios", "zabbix", "prometheus", "grafana",
        "logs", "logging", "status", "health", "ping", "metrics", "stats",
        "admin", "administrator", "root", "manage", "management", "panel", "cp",
        # Backup & Storage
        "backup", "backups", "archive", "archives", "storage", "store", "db",
        "database", "mysql", "postgres", "mongo", "redis", "elastic", "elasticsearch",
        # E-commerce
        "shop", "store", "cart", "checkout", "payment", "payments", "pay",
        "billing", "invoice", "order", "orders", "product", "products",
        # Geographic
        "us", "uk", "eu", "asia", "au", "ca", "de", "fr", "jp", "cn", "br",
        "na", "emea", "apac", "latam", "east", "west", "north", "south",
        # Legacy/Other
        "old", "legacy", "v1", "v2", "v3", "2018", "2019", "2020", "2021", "2022",
        "2023", "2024", "2025", "2026",
    ]

    def __init__(self, orchestrator=None, max_workers: int = 50, timeout: int = 10):
        self.orchestrator = orchestrator
        self.max_workers = max_workers
        self.timeout = timeout
        self.results: Dict[str, SubdomainResult] = {}
        self.wordlist = self.DEFAULT_WORDLIST.copy()

    async def scan(
        self,
        domain: str,
        wordlist: Optional[List[str]] = None,
        techniques: Optional[List[str]] = None,
        check_http: bool = True,
    ) -> Dict[str, SubdomainResult]:
        """
        Perform comprehensive subdomain enumeration

        Args:
            domain: Target domain (e.g., "target.com")
            wordlist: Custom wordlist (uses default if None)
            techniques: List of techniques to use
                       ["dns", "wordlist", "crt", "osint"]
            check_http: Whether to check HTTP/HTTPS availability

        Returns:
            Dictionary of subdomain -> SubdomainResult
        """
        domain = domain.lower().strip()
        if domain.startswith(("http://", "https://")):
            domain = urlparse(domain).netloc

        logger.info(f"[SubdomainScanner] Starting scan for {domain}")
        start_time = datetime.now()

        if techniques is None:
            techniques = ["dns", "wordlist", "crt"]

        if wordlist:
            self.wordlist = wordlist

        discovered: Set[str] = set()

        # Technique 1: DNS Enumeration
        if "dns" in techniques:
            dns_results = await self._dns_enumeration(domain)
            discovered.update(dns_results)
            logger.info(f"[SubdomainScanner] DNS enumeration found {len(dns_results)} subdomains")

        # Technique 2: Wordlist Brute-force
        if "wordlist" in techniques:
            wordlist_results = await self._wordlist_bruteforce(domain)
            discovered.update(wordlist_results)
            logger.info(f"[SubdomainScanner] Wordlist found {len(wordlist_results)} subdomains")

        # Technique 3: Certificate Transparency Logs
        if "crt" in techniques:
            crt_results = await self._crt_sh_enum(domain)
            discovered.update(crt_results)
            logger.info(f"[SubdomainScanner] CRT.sh found {len(crt_results)} subdomains")

        # Technique 4: OSINT via LLM (if orchestrator available)
        if "osint" in techniques and self.orchestrator:
            osint_results = await self._llm_assisted_enum(domain)
            discovered.update(osint_results)
            logger.info(f"[SubdomainScanner] OSINT found {len(osint_results)} subdomains")

        # Remove wildcards and validate
        discovered = self._filter_wildcards(discovered, domain)

        # Check HTTP/HTTPS if requested
        if check_http:
            await self._check_http_availability(discovered)

        # Build results
        for subdomain in discovered:
            if subdomain not in self.results:
                self.results[subdomain] = SubdomainResult(subdomain=subdomain)

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"[SubdomainScanner] Scan completed in {duration:.2f}s - Found {len(self.results)} subdomains")

        return self.results

    async def _dns_enumeration(self, domain: str) -> Set[str]:
        """Enumerate subdomains using DNS queries"""
        discovered = set()
        # Common prefixes for DNS enumeration
        prefixes = ["www", "mail", "ftp", "ns", "ns1", "ns2", "mx", "mx1", "mx2", "blog", "shop"]

        tasks = []
        for prefix in prefixes:
            subdomain = f"{prefix}.{domain}"
            for rtype in ["A", "AAAA", "CNAME"]:
                tasks.append(self._dns_query(subdomain, rtype))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, str):
                discovered.add(result)

        return discovered

    async def _dns_query(self, subdomain: str, record_type: str) -> Optional[str]:
        """Perform single DNS query"""
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = self.timeout
            resolver.lifetime = self.timeout

            answers = resolver.resolve(subdomain, record_type)
            if answers:
                return subdomain
        except Exception:
            pass
        return None

    async def _wordlist_bruteforce(self, domain: str) -> Set[str]:
        """Brute force subdomains using wordlist"""
        discovered = set()
        semaphore = asyncio.Semaphore(self.max_workers)

        async def check_subdomain(prefix: str) -> Optional[str]:
            async with semaphore:
                subdomain = f"{prefix}.{domain}"
                try:
                    # Try DNS resolution
                    loop = asyncio.get_event_loop()
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        await asyncio.wait_for(
                            loop.run_in_executor(executor, socket.gethostbyname, subdomain),
                            timeout=self.timeout
                        )
                    return subdomain
                except Exception:
                    return None

        # Create tasks for all wordlist entries
        tasks = [check_subdomain(prefix) for prefix in self.wordlist]
        results = await asyncio.gather(*tasks)

        for result in results:
            if result:
                discovered.add(result)

        return discovered

    async def _crt_sh_enum(self, domain: str) -> Set[str]:
        """Query Certificate Transparency logs via crt.sh"""
        discovered = set()
        url = f"https://crt.sh/?q=%.{domain}&output=json"

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for entry in data:
                            name = entry.get("name_value", "").lower().strip()
                            # Handle multiple names (wildcard certificates)
                            for sub in name.split("\n"):
                                sub = sub.strip()
                                # Remove wildcards
                                if sub.startswith("*."):
                                    sub = sub[2:]
                                # Validate it's a subdomain of target
                                if sub.endswith(f".{domain}") or sub == domain:
                                    if sub != domain:
                                        discovered.add(sub)
        except Exception as e:
            logger.debug(f"[SubdomainScanner] CRT.sh lookup failed: {e}")

        return discovered

    async def _llm_assisted_enum(self, domain: str) -> Set[str]:
        """Use LLM to suggest likely subdomains based on target type"""
        discovered = set()

        if not self.orchestrator:
            return discovered

        try:
            prompt = f"""
Analyze the domain "{domain}" and suggest likely subdomains.
Consider the domain type (corporate, tech, e-commerce, etc.) and suggest:
1. Common infrastructure subdomains
2. Likely application-specific subdomains
3. Regional/geographic subdomains
4. Service-specific subdomains

Return ONLY a comma-separated list of subdomain names (without the domain).
Example: admin,api,dev,staging,us-west,cdn
"""
            response = await self.orchestrator.process(prompt)
            content = response.content.lower()

            # Parse comma-separated or newline-separated values
            separators = [",", "\n", " ", ";"]
            candidates = [content]
            for sep in separators:
                new_candidates = []
                for c in candidates:
                    new_candidates.extend(c.split(sep))
                candidates = new_candidates

            for candidate in candidates:
                candidate = candidate.strip()
                # Clean up common prefixes/suffixes
                candidate = candidate.replace("*.", "").replace(f".{domain}", "")
                if candidate and "." not in candidate and len(candidate) > 1:
                    discovered.add(f"{candidate}.{domain}")

        except Exception as e:
            logger.debug(f"[SubdomainScanner] LLM enumeration failed: {e}")

        return discovered

    def _filter_wildcards(self, subdomains: Set[str], domain: str) -> Set[str]:
        """Filter out wildcard DNS entries"""
        filtered = set()
        wildcards = set()

        # Test for wildcards by checking random subdomains
        test_subdomains = [
            f"test12345.{domain}",
            f"random98765.{domain}",
            f"wildcard-check.{domain}"
        ]

        wildcard_ips = set()
        for test_sub in test_subdomains:
            try:
                ip = socket.gethostbyname(test_sub)
                wildcard_ips.add(ip)
            except Exception:
                pass

        # Filter results
        for subdomain in subdomains:
            if subdomain in wildcards:
                continue
            try:
                ip = socket.gethostbyname(subdomain)
                if ip not in wildcard_ips:
                    filtered.add(subdomain)
            except Exception:
                # If we can't resolve, still keep it (might be CNAME or other record)
                filtered.add(subdomain)

        return filtered

    async def _check_http_availability(self, subdomains: Set[str]):
        """Check HTTP/HTTPS availability for discovered subdomains"""
        semaphore = asyncio.Semaphore(self.max_workers)

        async def check_url(subdomain: str, protocol: str):
            async with semaphore:
                url = f"{protocol}://{subdomain}"
                try:
                    timeout = aiohttp.ClientTimeout(total=self.timeout)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(url, allow_redirects=True, ssl=False) as response:
                            if subdomain not in self.results:
                                self.results[subdomain] = SubdomainResult(subdomain=subdomain)

                            result = self.results[subdomain]
                            result.is_alive = True
                            result.status_code = response.status

                            # Get server header
                            result.server_header = response.headers.get("Server", "Unknown")

                            # Detect technologies
                            result.technologies = self._detect_technologies(response.headers, await response.text())

                except Exception:
                    pass

        # Check both HTTP and HTTPS
        tasks = []
        for subdomain in subdomains:
            tasks.append(check_url(subdomain, "http"))
            tasks.append(check_url(subdomain, "https"))

        await asyncio.gather(*tasks, return_exceptions=True)

    def _detect_technologies(self, headers: Dict, body: str) -> List[str]:
        """Detect technologies from HTTP response"""
        techs = []

        # Server headers
        server = headers.get("Server", "").lower()
        if "nginx" in server:
            techs.append("nginx")
        elif "apache" in server:
            techs.append("apache")
        elif "iis" in server or "microsoft" in server:
            techs.append("IIS")
        elif "cloudflare" in server:
            techs.append("Cloudflare")

        # X-Powered-By
        powered = headers.get("X-Powered-By", "").lower()
        if "php" in powered:
            techs.append("PHP")
        elif "asp.net" in powered:
            techs.append("ASP.NET")

        # Via header (CDN)
        via = headers.get("Via", "").lower()
        if "cloudfront" in via:
            techs.append("AWS CloudFront")
        elif "akamai" in via:
            techs.append("Akamai")

        # Body detection
        body_lower = body.lower()[:5000]  # Check first 5KB
        indicators = {
            "wordpress": "WordPress",
            "drupal": "Drupal",
            "joomla": "Joomla",
            "react": "React",
            "vue.js": "Vue.js",
            "angular": "Angular",
            "bootstrap": "Bootstrap",
            "jquery": "jQuery",
            "aws": "AWS",
            "gcp": "Google Cloud",
            "azure": "Azure",
        }

        for indicator, tech in indicators.items():
            if indicator in body_lower:
                techs.append(tech)

        return list(set(techs))

    def export_results(self, format_type: str = "json") -> str:
        """Export results to various formats"""
        if format_type == "json":
            data = {
                subdomain: {
                    "ip_addresses": result.ip_addresses,
                    "status_code": result.status_code,
                    "server_header": result.server_header,
                    "technologies": result.technologies,
                    "is_alive": result.is_alive,
                    "discovered_at": result.discovered_at.isoformat(),
                }
                for subdomain, result in self.results.items()
            }
            return json.dumps(data, indent=2)

        elif format_type == "txt":
            lines = [f"# Subdomain Scan Results - {datetime.now().isoformat()}", ""]
            for subdomain in sorted(self.results.keys()):
                result = self.results[subdomain]
                lines.append(f"{subdomain}")
                if result.ip_addresses:
                    lines.append(f"  IP: {', '.join(result.ip_addresses)}")
                if result.status_code:
                    lines.append(f"  Status: {result.status_code}")
                if result.technologies:
                    lines.append(f"  Tech: {', '.join(result.technologies)}")
                lines.append("")
            return "\n".join(lines)

        elif format_type == "csv":
            lines = ["subdomain,ip_addresses,status_code,server,technologies,is_alive"]
            for subdomain, result in self.results.items():
                ips = "|".join(result.ip_addresses) if result.ip_addresses else ""
                techs = "|".join(result.technologies) if result.technologies else ""
                lines.append(
                    f'"{subdomain}","{ips}",{result.status_code or ""},'
                    f'"{result.server_header or ""}","{techs}",{result.is_alive}'
                )
            return "\n".join(lines)

        else:
            raise ValueError(f"Unsupported format: {format_type}")


# Convenience function for standalone usage
async def scan_subdomains(
    domain: str,
    wordlist: Optional[List[str]] = None,
    check_http: bool = True,
    max_workers: int = 50,
) -> Dict[str, SubdomainResult]:
    """
    Standalone function to scan subdomains

    Args:
        domain: Target domain
        wordlist: Optional custom wordlist
        check_http: Whether to check HTTP availability
        max_workers: Maximum concurrent workers

    Returns:
        Dictionary of subdomain results
    """
    scanner = SubdomainScanner(max_workers=max_workers)
    return await scanner.scan(domain, wordlist=wordlist, check_http=check_http)


if __name__ == "__main__":
    # Demo usage
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if len(sys.argv) < 2:
        print("Usage: python subdomain_scanner.py <domain>")
        print("Example: python subdomain_scanner.py target.com")
        sys.exit(1)

    target = sys.argv[1]
    print(f"[*] Starting subdomain scan for: {target}")

    results = asyncio.run(scan_subdomains(target, check_http=True))

    print(f"\n[+] Found {len(results)} subdomains:\n")
    print(f"{'Subdomain':<40} {'Status':<8} {'Technologies'}")
    print("-" * 80)

    for subdomain in sorted(results.keys()):
        result = results[subdomain]
        status = str(result.status_code) if result.status_code else "N/A"
        techs = ", ".join(result.technologies[:3]) if result.technologies else "N/A"
        print(f"{subdomain:<40} {status:<8} {techs}")
