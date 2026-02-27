"""
Chain of Custody Manager

Implements an immutable audit trail for evidence using blockchain-like
hash chaining. Each action creates a new link that references the previous.

This ensures tamper-evident logging suitable for legal proceedings.
"""

import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from .models import ChainLink, Evidence, EvidenceStatus


class ChainOfCustody:
    """
    Manages the chain of custody for evidence.
    
    Each evidence item has an immutable chain of actions:
    - COLLECTED → VERIFIED → EXPORTED → ARCHIVED
    
    The chain uses cryptographic hashing to detect tampering.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._last_link_hash: Optional[str] = None
    
    def create_initial_link(
        self,
        evidence_id: str,
        actor_type: str,
        actor_id: str,
        actor_name: str = None,
        actor_ip: str = None,
        description: str = None,
    ) -> ChainLink:
        """
        Create the first link in the chain when evidence is collected.
        
        Args:
            evidence_id: UUID of the evidence
            actor_type: 'agent', 'user', or 'system'
            actor_id: ID of the actor
            actor_name: Human-readable name
            actor_ip: IP address of actor
            description: Optional description
            
        Returns:
            The created ChainLink
        """
        link_id = str(uuid.uuid4())
        
        link = ChainLink(
            id=link_id,
            evidence_id=evidence_id,
            sequence=1,
            action="created",
            action_description=description or "Evidence initially collected",
            actor_type=actor_type,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_ip=actor_ip,
            timestamp=datetime.utcnow(),
            previous_link_hash="0" * 64,  # Genesis hash
        )
        
        # Calculate hash after setting all fields
        link.current_hash = link.calculate_hash()
        
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        
        return link
    
    def add_link(
        self,
        evidence_id: str,
        action: str,
        actor_type: str,
        actor_id: str,
        actor_name: str = None,
        actor_ip: str = None,
        description: str = None,
    ) -> ChainLink:
        """
        Add a new link to the chain.
        
        Args:
            evidence_id: UUID of the evidence
            action: Type of action (viewed, exported, verified, etc.)
            actor_type: 'agent', 'user', or 'system'
            actor_id: ID of the actor
            actor_name: Human-readable name
            actor_ip: IP address
            description: Optional description
            
        Returns:
            The created ChainLink
        """
        # Get the last link in the chain
        last_link = (
            self.db.query(ChainLink)
            .filter(ChainLink.evidence_id == evidence_id)
            .order_by(ChainLink.sequence.desc())
            .first()
        )
        
        sequence = 1
        previous_hash = "0" * 64
        
        if last_link:
            sequence = last_link.sequence + 1
            previous_hash = last_link.current_hash
        
        link_id = str(uuid.uuid4())
        
        link = ChainLink(
            id=link_id,
            evidence_id=evidence_id,
            sequence=sequence,
            action=action,
            action_description=description,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_ip=actor_ip,
            timestamp=datetime.utcnow(),
            previous_link_hash=previous_hash,
        )
        
        # Calculate hash after setting all fields
        link.current_hash = link.calculate_hash()
        
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        
        return link
    
    def verify_chain(self, evidence_id: str) -> Dict:
        """
        Verify the integrity of the entire chain.
        
        Checks:
        1. Each link's hash is correct
        2. Each link correctly references the previous
        3. No links are missing (sequence continuity)
        
        Returns:
            Dict with verification results
        """
        links = (
            self.db.query(ChainLink)
            .filter(ChainLink.evidence_id == evidence_id)
            .order_by(ChainLink.sequence.asc())
            .all()
        )
        
        if not links:
            return {
                "valid": False,
                "error": "No chain links found",
                "links_checked": 0,
                "broken_at": None,
            }
        
        issues = []
        
        for i, link in enumerate(links):
            # Check sequence continuity
            expected_sequence = i + 1
            if link.sequence != expected_sequence:
                issues.append(f"Sequence break at position {i}: expected {expected_sequence}, got {link.sequence}")
            
            # Recalculate hash
            calculated_hash = link.calculate_hash()
            if calculated_hash != link.current_hash:
                issues.append(f"Hash mismatch at link {link.sequence}")
            
            # Check previous hash (except for first link)
            if i > 0:
                expected_previous = links[i - 1].current_hash
                if link.previous_link_hash != expected_previous:
                    issues.append(f"Previous hash mismatch at link {link.sequence}")
            
            # Check first link has genesis hash
            if i == 0 and link.previous_link_hash != "0" * 64:
                issues.append("Genesis link doesn't have correct genesis hash")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "links_checked": len(links),
            "broken_at": issues[0] if issues else None,
        }
    
    def get_chain(self, evidence_id: str) -> List[ChainLink]:
        """Get all links in the chain for evidence."""
        return (
            self.db.query(ChainLink)
            .filter(ChainLink.evidence_id == evidence_id)
            .order_by(ChainLink.sequence.asc())
            .all()
        )
    
    def export_chain_report(self, evidence_id: str, format: str = "json") -> Dict:
        """
        Generate a chain of custody report for legal proceedings.
        
        Args:
            evidence_id: UUID of evidence
            format: 'json', 'pdf', or 'html'
            
        Returns:
            Report data
        """
        evidence = self.db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            return {"error": "Evidence not found"}
        
        links = self.get_chain(evidence_id)
        verification = self.verify_chain(evidence_id)
        
        report = {
            "report_type": "Chain of Custody",
            "generated_at": datetime.utcnow().isoformat(),
            "evidence": {
                "id": evidence.id,
                "title": evidence.title,
                "collected_at": evidence.collected_at.isoformat() if evidence.collected_at else None,
                "current_status": evidence.status.value if evidence.status else None,
            },
            "verification": verification,
            "chain": [link.to_dict() for link in links],
            "summary": {
                "total_actions": len(links),
                "first_action": links[0].action if links else None,
                "last_action": links[-1].action if links else None,
                "unique_actors": len(set(link.actor_id for link in links)),
            },
            "legal_statement": (
                "This chain of custody report certifies that the evidence "
                f"'{evidence.title}' has been handled according to established procedures. "
                f"The chain contains {len(links)} verified links and is "
                f"{'VALID' if verification['valid'] else 'COMPROMISED'}."
            ),
        }
        
        return report
    
    def detect_tampering(self, evidence_id: str) -> Optional[str]:
        """
        Check if evidence has been tampered with.
        
        Returns:
            None if clean, error message if tampered
        """
        verification = self.verify_chain(evidence_id)
        
        if not verification["valid"]:
            return f"Chain of custody broken: {verification['broken_at']}"
        
        # Also verify file integrity
        evidence = self.db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if evidence and not evidence.verify_integrity():
            return "File integrity check failed - evidence file has been modified"
        
        return None


class LegalHoldManager:
    """
    Manages legal holds on evidence.
    
    Ensures evidence is preserved and not deleted when under legal hold.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def place_hold(
        self,
        evidence_id: str,
        case_number: str,
        reason: str,
        authorized_by: str,
    ) -> Dict:
        """Place a legal hold on evidence."""
        chain = ChainOfCustody(self.db)
        
        link = chain.add_link(
            evidence_id=evidence_id,
            action="legal_hold_placed",
            actor_type="user",
            actor_id=authorized_by,
            description=f"Legal hold placed for case {case_number}: {reason}",
        )
        
        return {
            "status": "hold_placed",
            "evidence_id": evidence_id,
            "case_number": case_number,
            "link_id": link.id,
            "timestamp": link.timestamp.isoformat(),
        }
    
    def release_hold(
        self,
        evidence_id: str,
        case_number: str,
        authorized_by: str,
    ) -> Dict:
        """Release a legal hold."""
        chain = ChainOfCustody(self.db)
        
        link = chain.add_link(
            evidence_id=evidence_id,
            action="legal_hold_released",
            actor_type="user",
            actor_id=authorized_by,
            description=f"Legal hold released for case {case_number}",
        )
        
        return {
            "status": "hold_released",
            "evidence_id": evidence_id,
            "case_number": case_number,
            "link_id": link.id,
            "timestamp": link.timestamp.isoformat(),
        }
