"""
Crawl4AI Integration for Zen-AI-Pentest
Advanced web crawling, JavaScript rendering, and data extraction
"""

import asyncio
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


@dataclass
class CrawlResult:
    """Structured result from web crawling"""

    url: str
    title: str
    markdown: str
    html: str
    links: List[str]
    emails: List[str]
    subdomains: List[str]
    technologies: List[str]
    forms: List[Dict[str, Any]]
    screenshots: Optional[str] = None


class Crawl4AIIntegration:
    """
    Integration with crawl4ai for advanced web reconnaissance

    Features:
    - JavaScript rendering for SPAs
    - Automatic subdomains discovery
    - Email/PII extraction
    - Form detection
    - Technology fingerprinting
    - Screenshot capture
    """

    def __init__(self, headless: bool = True, verbose: bool = False):
        self.headless = headless
        self.verbose = verbose
        self.browser_config = BrowserConfig(headless=headless, verbose=verbose)

    async def crawl_target(
        self,
        url: str,
        depth: int = 1,
        extract_emails: bool = True,
        extract_subdomains: bool = True,
        screenshot: bool = False,
        javascript: bool = True,
        wordlist: Optional[List[str]] = None,
    ) -> CrawlResult:
        """
        Crawl a target URL and extract intelligence

        Args:
            url: Target URL to crawl
            depth: Crawling depth (1 = single page)
            extract_emails: Extract email addresses
            extract_subdomains: Extract subdomains
            screenshot: Capture screenshot
            javascript: Execute JavaScript (for SPAs)
            wordlist: Optional custom wordlist for fuzzing

        Returns:
            CrawlResult with extracted data
        """
        crawl_config = CrawlerRunConfig(
            word_count_threshold=10,
            exclude_external_links=False,
            remove_overlay_elements=True,
            process_iframes=True,
            screenshot=screenshot,
        )

        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            result = await crawler.arun(url=url, config=crawl_config)

            # Parse results
            emails = []
            subdomains = []
            technologies = []
            forms = []

            if extract_emails:
                emails = self._extract_emails(result.markdown + result.html)

            if extract_subdomains:
                base_domain = urlparse(url).netloc
                subdomains = self._extract_subdomains(
                    result.markdown + result.html, base_domain
                )

            # Detect technologies from HTML
            technologies = self._detect_technologies(result.html)

            # Extract forms
            forms = self._extract_forms(result.html)

            return CrawlResult(
                url=url,
                title=result.metadata.get("title", ""),
                markdown=result.markdown,
                html=result.html,
                links=list(result.links.get("internal", [])),
                emails=emails,
                subdomains=subdomains,
                technologies=technologies,
                forms=forms,
                screenshots=result.screenshot if screenshot else None,
            )

    async def crawl_multiple(
        self, urls: List[str], max_concurrent: int = 3, **kwargs
    ) -> List[CrawlResult]:
        """Crawl multiple URLs concurrently"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def crawl_with_limit(url):
            async with semaphore:
                return await self.crawl_target(url, **kwargs)

        tasks = [crawl_with_limit(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        emails = re.findall(email_pattern, text)
        return list(set(emails))  # Remove duplicates

    def _extract_subdomains(self, text: str, base_domain: str) -> List[str]:
        """Extract subdomains from text"""
        # Remove port if present
        base_domain = base_domain.split(":")[0]

        # Pattern for subdomains
        pattern = rf"https?://([a-zA-Z0-9_-]+\.)*{re.escape(base_domain)}"
        matches = re.findall(pattern, text)

        subdomains = []
        for match in matches:
            subdomain = match.rstrip(".")
            if subdomain and subdomain != "www":
                subdomains.append(f"{subdomain}.{base_domain}")

        return list(set(subdomains))

    def _detect_technologies(self, html: str) -> List[str]:
        """Detect web technologies from HTML"""
        tech_signatures = {
            "WordPress": [r"wp-content", r"wp-includes", r"wordpress"],
            "Drupal": [r"drupal", r"sites/default"],
            "Joomla": [r"joomla", r"com_content"],
            "React": [r"reactroot", r"__react", r"reactjs"],
            "Vue.js": [r"__vue__", r"vue-router"],
            "Angular": [r"ng-app", r"angular"],
            "jQuery": [r"jquery", r"jquery.min.js"],
            "Bootstrap": [r"bootstrap", r"bootstrap.min.css"],
            "Django": [r"csrfmiddlewaretoken", r"__debug__"],
            "Flask": [r"werkzeug", r"flask"],
            "Laravel": [r"laravel_session", r"csrf-token"],
            "PHP": [r"\.php", r"<?php"],
            "Python": [r"wsgi", r"python"],
            "Node.js": [r"express", r"node.js"],
            "Apache": [r"apache", r"server: apache"],
            "Nginx": [r"nginx", r"server: nginx"],
        }

        detected = []
        html_lower = html.lower()

        for tech, signatures in tech_signatures.items():
            for sig in signatures:
                if re.search(sig, html_lower):
                    detected.append(tech)
                    break

        return detected

    def _extract_forms(self, html: str) -> List[Dict[str, Any]]:
        """Extract form information from HTML"""
        forms = []

        # Simple regex-based form extraction
        form_pattern = r"<form[^>]*>(.*?)</form>"
        input_pattern = r'<input[^>]*name=["\']([^"\']+)["\'][^>]*>'
        action_pattern = r'<form[^>]*action=["\']([^"\']*)["\'][^>]*>'
        method_pattern = r'<form[^>]*method=["\']([^"\']*)["\'][^>]*>'

        for form_match in re.finditer(
            form_pattern, html, re.DOTALL | re.IGNORECASE
        ):
            form_html = form_match.group(0)

            # Extract inputs
            inputs = re.findall(input_pattern, form_html, re.IGNORECASE)

            # Extract action
            action_match = re.search(action_pattern, form_html, re.IGNORECASE)
            action = action_match.group(1) if action_match else ""

            # Extract method
            method_match = re.search(method_pattern, form_html, re.IGNORECASE)
            method = method_match.group(1).upper() if method_match else "GET"

            forms.append(
                {
                    "action": action,
                    "method": method,
                    "inputs": inputs,
                    "input_count": len(inputs),
                }
            )

        return forms


# Synchronous wrapper for easier usage
def crawl_target_sync(url: str, **kwargs) -> CrawlResult:
    """Synchronous wrapper for crawl_target"""
    crawler = Crawl4AIIntegration()
    return asyncio.run(crawler.crawl_target(url, **kwargs))


def crawl_multiple_sync(urls: List[str], **kwargs) -> List[CrawlResult]:
    """Synchronous wrapper for crawl_multiple"""
    crawler = Crawl4AIIntegration()
    return asyncio.run(crawler.crawl_multiple(urls, **kwargs))
