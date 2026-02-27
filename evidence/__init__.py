"""
Zen-AI-Pentest Evidence Collection Module

Provides tamper-proof evidence collection for penetration testing:
- Screenshots with timestamps
- Chain of custody logging
- Cryptographic verification (SHA-256)
- Export for legal proceedings

Usage:
    from evidence import EvidenceCollector
    
    collector = EvidenceCollector(scan_id="scan-123")
    finding = await collector.capture_finding(
        target="https://example.com",
        vulnerability="SQL Injection",
        severity="Critical",
        proof={"payload": "' OR 1=1 --"}
    )
"""

from .collector import EvidenceCollector
from .chain_of_custody import ChainOfCustody
from .storage import EvidenceStorage
from .models import Evidence, ChainLink, EvidenceStatus

__version__ = "1.0.0"
__all__ = [
    "EvidenceCollector",
    "ChainOfCustody", 
    "EvidenceStorage",
    "Evidence",
    "ChainLink",
    "EvidenceStatus",
]
