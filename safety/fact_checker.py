"""
Fact Checker - Verify claims against known data sources
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re


class FactCheckStatus(Enum):
    VERIFIED = "verified"
    CONTRADICTED = "contradicted"
    UNKNOWN = "unknown"
    PARTIAL = "partial"


@dataclass
class FactCheckResult:
    """Result of fact checking"""
    claim: str
    status: FactCheckStatus
    confidence: float
    evidence: List[str]
    source: str
    correction: Optional[str] = None


class FactChecker:
    """
    Checks AI outputs against verified facts.
    Uses CVE database, known vulnerabilities, and scan results.
    """
    
    def __init__(self, cve_db=None, knowledge_base=None):
        self.cve_db = cve_db
        self.knowledge_base = knowledge_base or {}
        self.check_history: List[FactCheckResult] = []
        
        # Known facts cache
        self._verified_facts: Dict[str, Any] = {}
        self._known_falsehoods: List[str] = []
    
    def check_output(self, output: str, context: Optional[Dict] = None) -> List[FactCheckResult]:
        """
        Check all verifiable claims in output
        """
        results = []
        
        # Extract claims
        claims = self._extract_claims(output)
        
        for claim in claims:
            result = self._verify_claim(claim, context)
            results.append(result)
            self.check_history.append(result)
        
        return results
    
    def _extract_claims(self, text: str) -> List[Dict]:
        """Extract verifiable claims from text"""
        claims = []
        
        # CVE claims
        cve_pattern = r'(CVE-\d{4}-\d{4,})'
        for match in re.finditer(cve_pattern, text, re.IGNORECASE):
            cve_id = match.group(1).upper()
            # Extract surrounding context
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end]
            
            claims.append({
                'type': 'cve',
                'id': cve_id,
                'text': context,
                'extracted': cve_id
            })
        
        # Port/service claims
        port_pattern = r'port\s+(\d{1,5})\s+(is\s+)?(open|closed|filtered)'
        for match in re.finditer(port_pattern, text, re.IGNORECASE):
            claims.append({
                'type': 'port_status',
                'port': match.group(1),
                'status': match.group(3).lower(),
                'text': match.group(0)
            })
        
        # Version claims
        version_pattern = r'(Apache|Nginx|OpenSSH|MySQL)[/\s]+(\d+\.\d+(\.\d+)?)'
        for match in re.finditer(version_pattern, text, re.IGNORECASE):
            claims.append({
                'type': 'version',
                'software': match.group(1),
                'version': match.group(2),
                'text': match.group(0)
            })
        
        # Severity claims
        severity_pattern = r'(critical|high|medium|low|informational)\s+(severity|risk|vulnerability)'
        for match in re.finditer(severity_pattern, text, re.IGNORECASE):
            claims.append({
                'type': 'severity',
                'level': match.group(1).lower(),
                'text': match.group(0)
            })
        
        return claims
    
    def _verify_claim(self, claim: Dict, context: Optional[Dict]) -> FactCheckResult:
        """Verify a single claim"""
        claim_type = claim.get('type')
        
        if claim_type == 'cve':
            return self._verify_cve(claim)
        elif claim_type == 'port_status':
            return self._verify_port_status(claim, context)
        elif claim_type == 'version':
            return self._verify_version(claim, context)
        elif claim_type == 'severity':
            return self._verify_severity(claim, context)
        
        return FactCheckResult(
            claim=claim.get('text', ''),
            status=FactCheckStatus.UNKNOWN,
            confidence=0.0,
            evidence=[],
            source='unknown'
        )
    
    def _verify_cve(self, claim: Dict) -> FactCheckResult:
        """Verify CVE claim against database"""
        cve_id = claim['id']
        
        # Check if CVE exists
        if self.cve_db:
            cve_info = self.cve_db.get(cve_id)
            if cve_info:
                return FactCheckResult(
                    claim=f"CVE reference: {cve_id}",
                    status=FactCheckStatus.VERIFIED,
                    confidence=0.95,
                    evidence=["Found in CVE database"],
                    source='cve_db',
                    correction=None
                )
            else:
                return FactCheckResult(
                    claim=f"CVE reference: {cve_id}",
                    status=FactCheckStatus.CONTRADICTED,
                    confidence=0.9,
                    evidence=[f"CVE {cve_id} not found in database"],
                    source='cve_db',
                    correction=f"Verify CVE ID - {cve_id} appears invalid"
                )
        
        # Basic format validation
        if re.match(r'CVE-\d{4}-\d{4,}', cve_id):
            return FactCheckResult(
                claim=f"CVE reference: {cve_id}",
                status=FactCheckStatus.PARTIAL,
                confidence=0.5,
                evidence=["Format valid, but not verified against database"],
                source='format_check'
            )
        
        return FactCheckResult(
            claim=f"CVE reference: {cve_id}",
            status=FactCheckStatus.CONTRADICTED,
            confidence=0.8,
            evidence=["Invalid CVE format"],
            source='format_check'
        )
    
    def _verify_port_status(self, claim: Dict, context: Optional[Dict]) -> FactCheckResult:
        """Verify port status against scan results"""
        port = claim['port']
        claimed_status = claim['status']
        
        # Check against context (previous scan results)
        if context and 'scan_results' in context:
            scan_ports = context['scan_results'].get('ports', {})
            if port in scan_ports:
                actual_status = scan_ports[port].get('state', 'unknown')
                if actual_status == claimed_status:
                    return FactCheckResult(
                        claim=f"Port {port} is {claimed_status}",
                        status=FactCheckStatus.VERIFIED,
                        confidence=0.95,
                        evidence=["Matches scan result"],
                        source='scan_data'
                    )
                else:
                    return FactCheckResult(
                        claim=f"Port {port} is {claimed_status}",
                        status=FactCheckStatus.CONTRADICTED,
                        confidence=0.9,
                        evidence=[f"Scan shows port {port} is {actual_status}"],
                        source='scan_data',
                        correction=f"Port {port} is actually {actual_status}"
                    )
        
        return FactCheckResult(
            claim=f"Port {port} is {claimed_status}",
            status=FactCheckStatus.UNKNOWN,
            confidence=0.3,
            evidence=["No scan data to verify"],
            source='none'
        )
    
    def _verify_version(self, claim: Dict, context: Optional[Dict]) -> FactCheckResult:
        """Verify software version"""
        software = claim['software']
        version = claim['version']
        
        if context and 'service_versions' in context:
            detected = context['service_versions'].get(software.lower())
            if detected:
                if detected == version:
                    return FactCheckResult(
                        claim=f"{software} version {version}",
                        status=FactCheckStatus.VERIFIED,
                        confidence=0.9,
                        evidence=["Matches detected version"],
                        source='scan_data'
                    )
                else:
                    return FactCheckResult(
                        claim=f"{software} version {version}",
                        status=FactCheckStatus.CONTRADICTED,
                        confidence=0.85,
                        evidence=[f"Detected {software} {detected}"],
                        source='scan_data',
                        correction=f"Actual version is {detected}"
                    )
        
        return FactCheckResult(
            claim=f"{software} version {version}",
            status=FactCheckStatus.UNKNOWN,
            confidence=0.4,
            evidence=["No version data available"],
            source='none'
        )
    
    def _verify_severity(self, claim: Dict, context: Optional[Dict]) -> FactCheckResult:
        """Verify severity rating"""
        level = claim['level']
        
        # Severity levels are subjective but should be consistent
        valid_levels = ['critical', 'high', 'medium', 'low', 'informational']
        
        if level.lower() in valid_levels:
            return FactCheckResult(
                claim=f"Severity: {level}",
                status=FactCheckStatus.VERIFIED,
                confidence=0.7,
                evidence=["Valid severity level"],
                source='standard'
            )
        
        return FactCheckResult(
            claim=f"Severity: {level}",
            status=FactCheckStatus.CONTRADICTED,
            confidence=0.8,
            evidence=["Invalid severity level"],
            source='standard',
            correction=f"Use standard levels: {', '.join(valid_levels)}"
        )
    
    def get_stats(self) -> Dict:
        """Get fact checking statistics"""
        if not self.check_history:
            return {'total': 0}
        
        total = len(self.check_history)
        verified = sum(1 for r in self.check_history if r.status == FactCheckStatus.VERIFIED)
        contradicted = sum(1 for r in self.check_history if r.status == FactCheckStatus.CONTRADICTED)
        
        return {
            'total': total,
            'verified': verified,
            'contradicted': contradicted,
            'unknown': total - verified - contradicted,
            'accuracy_rate': verified / total if total > 0 else 0
        }
