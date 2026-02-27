"""
Evidence Collector

Main module for collecting and managing evidence during penetration tests.
Integrates with Playwright for screenshots, handles all evidence types.
"""

import asyncio
import hashlib
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from .chain_of_custody import ChainOfCustody
from .models import Evidence, EvidenceStatus, SeverityLevel
from .storage import EvidenceStorage


class EvidenceCollector:
    """
    Main evidence collection interface.
    
    Usage:
        collector = EvidenceCollector(db_session, scan_id="scan-123")
        
        # Capture a finding with screenshot
        evidence = await collector.capture_web_finding(
            target_url="https://vulnerable.com/admin",
            vulnerability="SQL Injection",
            severity="critical",
            payload="' OR 1=1 --",
            take_screenshot=True
        )
    """
    
    def __init__(
        self,
        db: Session,
        scan_id: str,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        self.db = db
        self.scan_id = scan_id
        self.agent_id = agent_id
        self.user_id = user_id
        self.storage = EvidenceStorage()
        self.chain = ChainOfCustody(db)
        
        # Evidence counters
        self.evidence_count = 0
        self.screenshot_count = 0
    
    async def capture_web_finding(
        self,
        target_url: str,
        vulnerability: str,
        severity: str,
        payload: Optional[str] = None,
        description: Optional[str] = None,
        remediation: Optional[str] = None,
        take_screenshot: bool = True,
        page_content: Optional[str] = None,
        headers: Optional[Dict] = None,
        cvss_score: Optional[str] = None,
        cvss_vector: Optional[str] = None,
    ) -> Evidence:
        """
        Capture web application vulnerability evidence.
        
        Args:
            target_url: The vulnerable URL
            vulnerability: Type (SQLi, XSS, etc.)
            severity: critical/high/medium/low/info
            payload: The attack payload used
            description: Detailed description
            remediation: How to fix
            take_screenshot: Capture screenshot
            page_content: HTML content
            headers: HTTP response headers
            cvss_score: CVSS v3.1 score
            cvss_vector: CVSS vector string
            
        Returns:
            Evidence object
        """
        evidence_id = str(uuid.uuid4())
        
        # Parse target URL
        parsed = self._parse_url(target_url)
        
        # Generate title
        title = f"{vulnerability} at {parsed['path'][:50]}"
        
        # Build description
        full_description = self._build_description(
            vulnerability=vulnerability,
            target=target_url,
            payload=payload,
            description=description,
            headers=headers,
        )
        
        # Create evidence record
        evidence = Evidence(
            id=evidence_id,
            scan_id=self.scan_id,
            evidence_type="web_vulnerability",
            severity=SeverityLevel(severity.lower()),
            status=EvidenceStatus.COLLECTED,
            target_url=target_url,
            target_domain=parsed["domain"],
            target_port=parsed["port"],
            title=title,
            description=full_description,
            vulnerability_type=vulnerability,
            proof_of_concept=payload,
            remediation=remediation,
            cvss_score=cvss_score,
            cvss_vector=cvss_vector,
            collected_at=datetime.utcnow(),
            collector_agent_id=self.agent_id,
            collector_user_id=self.user_id,
        )
        
        # Take screenshot if requested
        if take_screenshot and PLAYWRIGHT_AVAILABLE:
            try:
                screenshot_path = await self._take_screenshot(
                    evidence_id=evidence_id,
                    url=target_url,
                    payload=payload,
                )
                if screenshot_path:
                    evidence.file_path = screenshot_path
                    evidence.file_size = os.path.getsize(screenshot_path)
                    evidence.file_hash_sha256 = self._hash_file(screenshot_path)
                    self.screenshot_count += 1
            except Exception as e:
                # Log error but don't fail the evidence collection
                print(f"Screenshot failed: {e}")
        
        # Save to database
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        
        # Create chain of custody link
        self.chain.create_initial_link(
            evidence_id=evidence_id,
            actor_type="agent" if self.agent_id else "user",
            actor_id=self.agent_id or self.user_id or "system",
            description=f"Evidence collected: {vulnerability} at {target_url}",
        )
        
        self.evidence_count += 1
        
        return evidence
    
    def capture_api_finding(
        self,
        endpoint: str,
        method: str,
        vulnerability: str,
        severity: str,
        request_data: Optional[Dict] = None,
        response_data: Optional[Dict] = None,
        description: Optional[str] = None,
        remediation: Optional[str] = None,
    ) -> Evidence:
        """
        Capture API vulnerability evidence.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            vulnerability: Type of vulnerability
            severity: Severity level
            request_data: Request details
            response_data: Response details
            description: Description
            remediation: Fix recommendation
            
        Returns:
            Evidence object
        """
        evidence_id = str(uuid.uuid4())
        
        # Build proof of concept from request/response
        poc = self._build_api_poc(method, endpoint, request_data, response_data)
        
        evidence = Evidence(
            id=evidence_id,
            scan_id=self.scan_id,
            evidence_type="api_vulnerability",
            severity=SeverityLevel(severity.lower()),
            status=EvidenceStatus.COLLECTED,
            target_url=endpoint,
            title=f"{vulnerability} in {method} {endpoint[:50]}",
            description=description or f"API vulnerability found in {method} {endpoint}",
            vulnerability_type=vulnerability,
            proof_of_concept=poc,
            remediation=remediation,
            collected_at=datetime.utcnow(),
            collector_agent_id=self.agent_id,
            collector_user_id=self.user_id,
        )
        
        # Store request/response as JSON file
        api_data = {
            "request": request_data,
            "response": response_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        json_path = self.storage.save_json(evidence_id, api_data)
        evidence.file_path = json_path
        evidence.file_size = os.path.getsize(json_path)
        evidence.file_hash_sha256 = self._hash_file(json_path)
        
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        
        self.chain.create_initial_link(
            evidence_id=evidence_id,
            actor_type="agent" if self.agent_id else "user",
            actor_id=self.agent_id or self.user_id or "system",
            description=f"API evidence collected: {vulnerability}",
        )
        
        self.evidence_count += 1
        
        return evidence
    
    def capture_network_finding(
        self,
        target_ip: str,
        target_port: int,
        service: str,
        vulnerability: str,
        severity: str,
        banner: Optional[str] = None,
        nmap_output: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Evidence:
        """
        Capture network/service vulnerability evidence.
        
        Args:
            target_ip: IP address
            target_port: Port number
            service: Service name
            vulnerability: Vulnerability type
            severity: Severity level
            banner: Service banner
            nmap_output: Raw scan output
            description: Description
            
        Returns:
            Evidence object
        """
        evidence_id = str(uuid.uuid4())
        
        # Build proof of concept
        poc_parts = []
        if banner:
            poc_parts.append(f"Service Banner: {banner}")
        if nmap_output:
            poc_parts.append(f"Scan Output:\n{nmap_output[:2000]}")
        
        poc = "\n\n".join(poc_parts) if poc_parts else None
        
        evidence = Evidence(
            id=evidence_id,
            scan_id=self.scan_id,
            evidence_type="network_vulnerability",
            severity=SeverityLevel(severity.lower()),
            status=EvidenceStatus.COLLECTED,
            target_ip=target_ip,
            target_port=target_port,
            title=f"{vulnerability} on {service} ({target_ip}:{target_port})",
            description=description or f"Network vulnerability detected on {target_ip}:{target_port}",
            vulnerability_type=vulnerability,
            proof_of_concept=poc,
            collected_at=datetime.utcnow(),
            collector_agent_id=self.agent_id,
            collector_user_id=self.user_id,
        )
        
        # Save scan output
        if nmap_output:
            txt_path = self.storage.save_text(evidence_id, nmap_output)
            evidence.file_path = txt_path
            evidence.file_size = os.path.getsize(txt_path)
            evidence.file_hash_sha256 = self._hash_file(txt_path)
        
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        
        self.chain.create_initial_link(
            evidence_id=evidence_id,
            actor_type="agent" if self.agent_id else "user",
            actor_id=self.agent_id or self.user_id or "system",
            description=f"Network evidence collected: {vulnerability} on {target_ip}:{target_port}",
        )
        
        self.evidence_count += 1
        
        return evidence
    
    async def _take_screenshot(
        self,
        evidence_id: str,
        url: str,
        payload: Optional[str] = None,
        wait_for: Optional[str] = None,
    ) -> Optional[str]:
        """
        Take screenshot using Playwright.
        
        Args:
            evidence_id: Evidence UUID
            url: URL to screenshot
            payload: Optional payload to inject
            wait_for: Optional selector to wait for
            
        Returns:
            Path to screenshot file
        """
        if not PLAYWRIGHT_AVAILABLE:
            return None
        
        screenshot_path = f"evidence/screenshots/{evidence_id}.png"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            page = await context.new_page()
            
            try:
                # Navigate to URL
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Inject payload if provided (for showing exploitation)
                if payload:
                    # Try to fill forms with payload
                    try:
                        inputs = await page.query_selector_all('input[type="text"], input:not([type])')
                        if inputs:
                            await inputs[0].fill(payload)
                            await asyncio.sleep(0.5)
                    except:
                        pass
                
                # Wait for specific element if requested
                if wait_for:
                    await page.wait_for_selector(wait_for, timeout=5000)
                
                # Take screenshot
                await page.screenshot(path=screenshot_path, full_page=True)
                
            except Exception as e:
                # Try viewport screenshot if full page fails
                try:
                    await page.screenshot(path=screenshot_path)
                except:
                    await browser.close()
                    raise e
            
            await browser.close()
        
        return screenshot_path if os.path.exists(screenshot_path) else None
    
    def _parse_url(self, url: str) -> Dict:
        """Parse URL into components."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return {
                "domain": parsed.hostname or "",
                "port": parsed.port or (443 if parsed.scheme == "https" else 80),
                "path": parsed.path or "/",
                "scheme": parsed.scheme,
            }
        except:
            return {"domain": "", "port": 80, "path": "/", "scheme": "http"}
    
    def _build_description(
        self,
        vulnerability: str,
        target: str,
        payload: Optional[str],
        description: Optional[str],
        headers: Optional[Dict],
    ) -> str:
        """Build detailed description."""
        parts = []
        
        if description:
            parts.append(description)
        else:
            parts.append(f"A {vulnerability} vulnerability was identified at {target}")
        
        if payload:
            parts.append(f"\nProof of Concept Payload:\n```\n{payload}\n```")
        
        if headers:
            relevant_headers = {k: v for k, v in headers.items() 
                              if k.lower() in ['server', 'x-powered-by', 'content-type']}
            if relevant_headers:
                parts.append(f"\nRelevant Headers:\n```json\n{json.dumps(relevant_headers, indent=2)}\n```")
        
        return "\n\n".join(parts)
    
    def _build_api_poc(
        self,
        method: str,
        endpoint: str,
        request_data: Optional[Dict],
        response_data: Optional[Dict],
    ) -> str:
        """Build proof of concept for API findings."""
        parts = [f"{method} {endpoint}"]
        
        if request_data:
            parts.append(f"\nRequest:\n```json\n{json.dumps(request_data, indent=2)}\n```")
        
        if response_data:
            parts.append(f"\nResponse:\n```json\n{json.dumps(response_data, indent=2)}\n```")
        
        return "\n".join(parts)
    
    def _hash_file(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def get_summary(self) -> Dict:
        """Get summary of collected evidence."""
        return {
            "scan_id": self.scan_id,
            "total_evidence": self.evidence_count,
            "screenshots_taken": self.screenshot_count,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
        }


class EvidenceBatchCollector:
    """
    Batch evidence collection for multiple findings.
    """
    
    def __init__(self, db: Session, scan_id: str):
        self.db = db
        self.scan_id = scan_id
        self.collector = EvidenceCollector(db, scan_id)
        self.evidence_list: List[Evidence] = []
    
    async def add_web_finding(self, **kwargs) -> Evidence:
        """Add web finding to batch."""
        evidence = await self.collector.capture_web_finding(**kwargs)
        self.evidence_list.append(evidence)
        return evidence
    
    def add_api_finding(self, **kwargs) -> Evidence:
        """Add API finding to batch."""
        evidence = self.collector.capture_api_finding(**kwargs)
        self.evidence_list.append(evidence)
        return evidence
    
    def add_network_finding(self, **kwargs) -> Evidence:
        """Add network finding to batch."""
        evidence = self.collector.capture_network_finding(**kwargs)
        self.evidence_list.append(evidence)
        return evidence
    
    def get_all(self) -> List[Evidence]:
        """Get all collected evidence."""
        return self.evidence_list
    
    def export_batch(self, format: str = "json") -> Dict:
        """Export all evidence in batch."""
        return {
            "scan_id": self.scan_id,
            "count": len(self.evidence_list),
            "evidence": [e.to_dict() for e in self.evidence_list],
            "exported_at": datetime.utcnow().isoformat(),
        }
