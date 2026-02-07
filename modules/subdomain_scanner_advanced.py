#!/usr/bin/env python3
"""
Advanced Subdomain Scanner Module
Extended enumeration techniques and integrations
Author: SHAdd0WTAka
"""

import asyncio
import hashlib
import json
import logging
import random
import re
import ssl
import string
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp
import dns.query
import dns.resolver
import dns.zone

from modules.subdomain_scanner import SubdomainResult, SubdomainScanner

logger = logging.getLogger("ZenAI")


@dataclass
class PermutationConfig:
    """Configuration for subdomain permutation"""
    insert_dashes: bool = True
    insert_dots: bool = False
    insert_numbers: bool = True
    add_prefixes: bool = True
    add_suffixes: bool = True
    max_permutations: int = 1000


class AdvancedSubdomainScanner(SubdomainScanner):
    """
    Extended subdomain scanner with advanced techniques:
    - DNS Zone Transfer (AXFR)
    - Subdomain permutation/mangling
    - VirusTotal API integration
    - CNAME chaining
    - IPv6 enumeration
    - SPF/DMARC record analysis
    """

    COMMON_PREFIXES = [
        "dev", "stg", "stage", "test", "uat", "qa", "prod", "production",
        "api", "api-v1", "api-v2", "api-v3", "rest", "graphql",
        "admin", "manage", "panel", "dashboard", "portal",
        "cdn", "static", "assets", "media", "files", "img", "images",
        "www", "www1", "www2", "web", "web1", "web2",
        "mail", "email", "smtp", "pop", "imap", "mx", "mx1", "mx2",
        "vpn", "remote", "access", "secure", "auth", "sso",
        "git", "gitlab", "github", "bitbucket", "svn", "cvs",
        "jenkins", "ci", "cd", "build", "deploy",
        "monitor", "nagios", "zabbix", "prometheus", "grafana",
        "db", "db1", "db2", "mysql", "postgres", "mongo", "redis",
        "es", "elastic", "search", "solr",
        "k8s", "kube", "kubernetes", "docker", "registry",
        "us", "uk", "eu", "asia", "au", "ca", "de", "fr", "jp",
        "east", "west", "north", "south", "central",
        "old", "legacy", "v1", "v2", "v3", "2018", "2019", "2020",
        "2021", "2022", "2023", "2024", "2025", "2026",
    ]

    COMMON_SUFFIXES = [
        "-dev", "-stg", "-stage", "-test", "-uat", "-qa", "-prod",
        "-01", "-02", "-03", "-1", "-2", "-3",
        "-new", "-old", "-legacy", "-beta", "-alpha",
        "-us", "-eu", "-asia", "-au", "-uk",
        "-east", "-west", "-north", "-south",
    ]

    def __init__(self, orchestrator=None, max_workers: int = 50, timeout: int = 10):
        super().__init__(orchestrator, max_workers, timeout)
        self.virustotal_api_key: Optional[str] = None
        self.permutation_config = PermutationConfig()

    def set_virustotal_key(self, api_key: str):
        """Set VirusTotal API key for enhanced enumeration"""
        self.virustotal_api_key = api_key

    async def scan_advanced(
        self,
        domain: str,
        techniques: Optional[List[str]] = None,
        check_http: bool = True,
        permutation_depth: int = 1,
    ) -> Dict[str, SubdomainResult]:
        """
        Perform advanced subdomain enumeration with all techniques
        
        Techniques:
        - basic: Basic DNS + wordlist + CRT.sh
        - axfr: DNS Zone Transfer attempts
        - permute: Subdomain permutation/mangling
        - virustotal: VirusTotal API lookup
        - dnsrecords: SPF, DMARC, MX analysis
        - ipv6: IPv6 address enumeration
        - alienvault: AlienVault OTX lookup
        - bufferover: BufferOver DNS data
        """
        domain = domain.lower().strip()
        if domain.startswith(("http://", "https://")):
            domain = urlparse(domain).netloc

        logger.info(f"[AdvancedScanner] Starting advanced scan for {domain}")
        start_time = datetime.now()

        if techniques is None:
            techniques = ["basic", "permute", "dnsrecords"]

        discovered: Set[str] = set()

        # Basic enumeration
        if "basic" in techniques:
            basic_results = await self.scan(domain, check_http=False)
            discovered.update(basic_results.keys())

        # DNS Zone Transfer
        if "axfr" in techniques:
            axfr_results = await self._try_zone_transfer(domain)
            discovered.update(axfr_results)
            logger.info(f"[AdvancedScanner] Zone transfer found {len(axfr_results)} subdomains")

        # Subdomain permutation
        if "permute" in techniques and permutation_depth > 0:
            permute_results = await self._permutation_scan(domain, discovered)
            discovered.update(permute_results)
            logger.info(f"[AdvancedScanner] Permutation found {len(permute_results)} subdomains")

        # VirusTotal lookup
        if "virustotal" in techniques and self.virustotal_api_key:
            vt_results = await self._virustotal_lookup(domain)
            discovered.update(vt_results)
            logger.info(f"[AdvancedScanner] VirusTotal found {len(vt_results)} subdomains")

        # DNS records analysis
        if "dnsrecords" in techniques:
            dns_results = await self._analyze_dns_records(domain)
            discovered.update(dns_results)
            logger.info(f"[AdvancedScanner] DNS analysis found {len(dns_results)} subdomains")

        # IPv6 enumeration
        if "ipv6" in techniques:
            ipv6_results = await self._ipv6_enumeration(domain)
            discovered.update(ipv6_results)
            logger.info(f"[AdvancedScanner] IPv6 found {len(ipv6_results)} subdomains")

        # External sources
        if "alienvault" in techniques:
            av_results = await self._alienvault_lookup(domain)
            discovered.update(av_results)
            logger.info(f"[AdvancedScanner] AlienVault found {len(av_results)} subdomains")

        if "bufferover" in techniques:
            bo_results = await self._bufferover_lookup(domain)
            discovered.update(bo_results)
            logger.info(f"[AdvancedScanner] BufferOver found {len(bo_results)} subdomains")

        # Filter and validate
        discovered = self._filter_wildcards(discovered, domain)

        # HTTP checking
        if check_http:
            await self._check_http_availability(discovered)

        # Build final results
        for subdomain in discovered:
            if subdomain not in self.results:
                self.results[subdomain] = SubdomainResult(subdomain=subdomain)

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"[AdvancedScanner] Completed in {duration:.2f}s - Total: {len(self.results)}")

        return self.results

    async def _try_zone_transfer(self, domain: str) -> Set[str]:
        """Attempt DNS zone transfer (AXFR) from discovered NS servers"""
        discovered = set()
        
        try:
            # Get NS records
            resolver = dns.resolver.Resolver()
            ns_records = resolver.resolve(domain, "NS")
            
            for ns in ns_records:
                ns_server = str(ns).rstrip(".")
                try:
                    # Try AXFR
                    zone = dns.zone.from_xfr(dns.query.xfr(ns_server, domain, timeout=self.timeout))
                    if zone:
                        for name, node in zone.nodes.items():
                            subdomain = f"{name}.{domain}".rstrip(".")
                            if subdomain != domain:
                                discovered.add(subdomain.lower())
                        logger.info(f"[AdvancedScanner] AXFR successful from {ns_server}")
                except Exception as e:
                    logger.debug(f"[AdvancedScanner] AXFR failed from {ns_server}: {e}")
                    
        except Exception as e:
            logger.debug(f"[AdvancedScanner] Zone transfer enumeration failed: {e}")
            
        return discovered

    async def _permutation_scan(
        self, 
        domain: str, 
        base_subdomains: Set[str],
    ) -> Set[str]:
        """Generate and test subdomain permutations"""
        discovered = set()
        
        # Extract base names from discovered subdomains
        base_names = set()
        for sub in base_subdomains:
            name = sub.replace(f".{domain}", "").split(".")[0]
            base_names.add(name)
        
        # Generate permutations
        permutations = set()
        
        for base in base_names:
            # Add prefixes
            if self.permutation_config.add_prefixes:
                for prefix in self.COMMON_PREFIXES:
                    permutations.add(f"{prefix}-{base}")
                    permutations.add(f"{prefix}{base}")
                    permutations.add(f"{prefix}.{base}")
            
            # Add suffixes
            if self.permutation_config.add_suffixes:
                for suffix in self.COMMON_SUFFIXES:
                    permutations.add(f"{base}{suffix}")
            
            # Insert numbers
            if self.permutation_config.insert_numbers:
                for i in range(1, 10):
                    permutations.add(f"{base}{i}")
                    permutations.add(f"{base}-{i}")
            
            # Dash variations
            if self.permutation_config.insert_dashes:
                permutations.add(base.replace("-", ""))
                permutations.add(base.replace("-", "_"))
        
        # Limit permutations
        permutations = list(permutations)[:self.permutation_config.max_permutations]
        
        # Test permutations
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def test_permutation(name: str) -> Optional[str]:
            async with semaphore:
                subdomain = f"{name}.{domain}"
                try:
                    loop = asyncio.get_event_loop()
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        await asyncio.wait_for(
                            loop.run_in_executor(executor, 
                                lambda: dns.resolver.resolve(subdomain, "A")),
                            timeout=self.timeout
                        )
                    return subdomain
                except Exception:
                    return None
        
        tasks = [test_permutation(p) for p in permutations]
        results = await asyncio.gather(*tasks)
        
        for result in results:
            if result:
                discovered.add(result)
        
        return discovered

    async def _virustotal_lookup(self, domain: str) -> Set[str]:
        """Query VirusTotal API for subdomains"""
        discovered = set()
        
        if not self.virustotal_api_key:
            return discovered
        
        url = f"https://www.virustotal.com/vtapi/v2/domain/report"
        params = {
            "apikey": self.virustotal_api_key,
            "domain": domain
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        subdomains = data.get("subdomains", [])
                        for sub in subdomains:
                            discovered.add(sub.lower())
        except Exception as e:
            logger.debug(f"[AdvancedScanner] VirusTotal lookup failed: {e}")
        
        return discovered

    async def _analyze_dns_records(self, domain: str) -> Set[str]:
        """Extract subdomains from SPF, DMARC, and other DNS records"""
        discovered = set()
        resolver = dns.resolver.Resolver()
        resolver.timeout = self.timeout
        
        # Check SPF record
        try:
            answers = resolver.resolve(domain, "TXT")
            for rdata in answers:
                txt = str(rdata)
                # Extract domains from SPF include statements
                includes = re.findall(r'include:([^\s"]+)', txt)
                for inc in includes:
                    discovered.add(inc.lower())
                    # Try to resolve includes
                    try:
                        inc_answers = resolver.resolve(inc, "A")
                        if inc_answers:
                            discovered.add(inc.lower())
                    except:
                        pass
        except:
            pass
        
        # Check DMARC
        try:
            dmarc_domain = f"_dmarc.{domain}"
            answers = resolver.resolve(dmarc_domain, "TXT")
            for rdata in answers:
                txt = str(rdata)
                # Extract report URIs
                uris = re.findall(r'rua=mailto:([^\s;"]+)', txt)
                for uri in uris:
                    if "@" in uri:
                        report_domain = uri.split("@")[1]
                        discovered.add(report_domain.lower())
        except:
            pass
        
        # Check MX records for subdomains
        try:
            answers = resolver.resolve(domain, "MX")
            for rdata in answers:
                exchange = str(rdata.exchange).rstrip(".").lower()
                if exchange.endswith(f".{domain}") or exchange == domain:
                    continue  # Skip main domain
                # Check if MX is a subdomain
                parts = exchange.split(".")
                if len(parts) > 2:
                    potential_sub = ".".join(parts[:-2]) + f".{domain}"
                    discovered.add(potential_sub.lower())
        except:
            pass
        
        return discovered

    async def _ipv6_enumeration(self, domain: str) -> Set[str]:
        """Enumerate IPv6 addresses for subdomains"""
        discovered = set()
        resolver = dns.resolver.Resolver()
        resolver.timeout = self.timeout
        
        # Common prefixes to check for AAAA records
        prefixes = ["www", "mail", "ftp", "ns", "ns1", "ns2", "mx", "api", "dev"]
        
        for prefix in prefixes:
            subdomain = f"{prefix}.{domain}"
            try:
                answers = resolver.resolve(subdomain, "AAAA")
                if answers:
                    discovered.add(subdomain.lower())
            except:
                pass
        
        return discovered

    async def _alienvault_lookup(self, domain: str) -> Set[str]:
        """Query AlienVault OTX for subdomains"""
        discovered = set()
        url = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns"
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for entry in data.get("passive_dns", []):
                            hostname = entry.get("hostname", "").lower()
                            if hostname and hostname.endswith(f".{domain}"):
                                discovered.add(hostname)
        except Exception as e:
            logger.debug(f"[AdvancedScanner] AlienVault lookup failed: {e}")
        
        return discovered

    async def _bufferover_lookup(self, domain: str) -> Set[str]:
        """Query BufferOver DNS data"""
        discovered = set()
        url = f"https://dns.bufferover.run/dns?q=.{domain}"
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for record in data.get("FDNS_A", []):
                            parts = record.split(",")
                            if len(parts) >= 2:
                                subdomain = parts[1].lower()
                                if subdomain.endswith(f".{domain}"):
                                    discovered.add(subdomain)
        except Exception as e:
            logger.debug(f"[AdvancedScanner] BufferOver lookup failed: {e}")
        
        return discovered

    def generate_report(self) -> Dict:
        """Generate comprehensive scan report"""
        live_hosts = [r for r in self.results.values() if r.is_alive]
        dns_only = [r for r in self.results.values() if not r.is_alive]
        
        # Technology statistics
        tech_stats = {}
        for result in self.results.values():
            for tech in result.technologies:
                tech_stats[tech] = tech_stats.get(tech, 0) + 1
        
        # Server statistics
        server_stats = {}
        for result in self.results.values():
            server = result.server_header or "Unknown"
            server_stats[server] = server_stats.get(server, 0) + 1
        
        return {
            "summary": {
                "total_discovered": len(self.results),
                "live_hosts": len(live_hosts),
                "dns_only": len(dns_only),
            },
            "technologies": dict(sorted(tech_stats.items(), key=lambda x: x[1], reverse=True)),
            "servers": dict(sorted(server_stats.items(), key=lambda x: x[1], reverse=True)),
            "live_subdomains": [
                {
                    "subdomain": r.subdomain,
                    "status_code": r.status_code,
                    "technologies": r.technologies,
                }
                for r in sorted(live_hosts, key=lambda x: x.subdomain)
            ],
            "discovered_at": datetime.now().isoformat(),
        }


# Convenience function
async def scan_subdomains_advanced(
    domain: str,
    techniques: Optional[List[str]] = None,
    check_http: bool = True,
    virustotal_key: Optional[str] = None,
) -> Dict[str, SubdomainResult]:
    """
    Standalone advanced subdomain scanner
    
    Args:
        domain: Target domain
        techniques: List of techniques to use
        check_http: Check HTTP availability
        virustotal_key: Optional VirusTotal API key
    
    Returns:
        Dictionary of subdomain results
    """
    scanner = AdvancedSubdomainScanner(max_workers=50)
    if virustotal_key:
        scanner.set_virustotal_key(virustotal_key)
    
    return await scanner.scan_advanced(
        domain=domain,
        techniques=techniques,
        check_http=check_http
    )


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    
    if len(sys.argv) < 2:
        print("Usage: python subdomain_scanner_advanced.py <domain>")
        print("Example: python subdomain_scanner_advanced.py target.com")
        sys.exit(1)
    
    target = sys.argv[1]
    print(f"[*] Starting advanced subdomain scan for: {target}\n")
    
    scanner = AdvancedSubdomainScanner(max_workers=30)
    
    results = asyncio.run(scanner.scan_advanced(
        target,
        techniques=["basic", "permute", "dnsrecords"],
        check_http=True
    ))
    
    print(f"\n[+] Found {len(results)} subdomains\n")
    
    report = scanner.generate_report()
    print(json.dumps(report, indent=2))
