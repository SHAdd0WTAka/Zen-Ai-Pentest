"""
Evidence Database Models

SQLAlchemy models for storing evidence with full audit trails.
"""

import enum
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class EvidenceStatus(str, enum.Enum):
    """Status of evidence in the chain of custody."""
    COLLECTED = "collected"
    VERIFIED = "verified"
    EXPORTED = "exported"
    ARCHIVED = "archived"
    COMPROMISED = "compromised"


class SeverityLevel(str, enum.Enum):
    """Severity classification for findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Evidence(Base):
    """
    Main evidence record.
    
    Each piece of evidence has:
    - Unique ID (UUID)
    - SHA-256 hash for integrity
    - Timestamp (UTC)
    - Collector identity
    - Chain of custody links
    """
    __tablename__ = "evidence"

    id = Column(String(36), primary_key=True)
    scan_id = Column(String(36), ForeignKey("scans.id"), nullable=False, index=True)
    finding_id = Column(String(36), ForeignKey("findings.id"), nullable=True)
    
    # Evidence metadata
    evidence_type = Column(String(50), nullable=False)  # screenshot, log, pcap, etc.
    severity = Column(Enum(SeverityLevel), nullable=False)
    status = Column(Enum(EvidenceStatus), default=EvidenceStatus.COLLECTED)
    
    # Target information
    target_url = Column(String(2048))
    target_ip = Column(String(45))  # IPv6 compatible
    target_port = Column(Integer)
    target_domain = Column(String(255))
    
    # Evidence content
    title = Column(String(255), nullable=False)
    description = Column(Text)
    vulnerability_type = Column(String(100))
    proof_of_concept = Column(Text)  # Payload, exploit code, etc.
    remediation = Column(Text)
    
    # File storage
    file_path = Column(String(512))  # Path to screenshot/log file
    file_size = Column(Integer)  # Bytes
    file_hash_sha256 = Column(String(64))  # Integrity hash
    
    # CVSS scoring
    cvss_score = Column(String(10))
    cvss_vector = Column(String(100))
    
    # Timestamps
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime)
    archived_at = Column(DateTime)
    
    # Collector identity
    collector_agent_id = Column(String(36))
    collector_user_id = Column(String(36))
    collector_ip = Column(String(45))
    
    # Tamper detection
    previous_hash = Column(String(64))  # Hash of previous evidence (blockchain-like)
    signature = Column(Text)  # Digital signature
    
    # Relationships
    chain_links = relationship("ChainLink", back_populates="evidence", order_by="ChainLink.sequence")
    
    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of evidence data for integrity verification."""
        data = {
            "id": self.id,
            "scan_id": self.scan_id,
            "evidence_type": self.evidence_type,
            "target_url": self.target_url,
            "title": self.title,
            "description": self.description,
            "proof_of_concept": self.proof_of_concept,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "collector_agent_id": self.collector_agent_id,
        }
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify evidence hasn't been tampered with."""
        if not self.file_hash_sha256:
            return True
        
        try:
            with open(self.file_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash == self.file_hash_sha256
        except (FileNotFoundError, IOError):
            return False
    
    def to_dict(self) -> Dict:
        """Convert evidence to dictionary for API responses."""
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "finding_id": self.finding_id,
            "evidence_type": self.evidence_type,
            "severity": self.severity.value if self.severity else None,
            "status": self.status.value if self.status else None,
            "target": {
                "url": self.target_url,
                "ip": self.target_ip,
                "port": self.target_port,
                "domain": self.target_domain,
            },
            "title": self.title,
            "description": self.description,
            "vulnerability_type": self.vulnerability_type,
            "proof_of_concept": self.proof_of_concept,
            "remediation": self.remediation,
            "file": {
                "path": self.file_path,
                "size": self.file_size,
                "hash_sha256": self.file_hash_sha256,
            },
            "cvss": {
                "score": self.cvss_score,
                "vector": self.cvss_vector,
            },
            "timestamps": {
                "collected": self.collected_at.isoformat() if self.collected_at else None,
                "verified": self.verified_at.isoformat() if self.verified_at else None,
                "archived": self.archived_at.isoformat() if self.archived_at else None,
            },
            "collector": {
                "agent_id": self.collector_agent_id,
                "user_id": self.collector_user_id,
                "ip": self.collector_ip,
            },
            "integrity": {
                "verified": self.verify_integrity(),
                "hash": self.file_hash_sha256,
            },
            "chain_of_custody": [link.to_dict() for link in self.chain_links],
        }


class ChainLink(Base):
    """
    Chain of Custody Link.
    
    Tracks every access/modification to evidence for legal proceedings.
    Immutable once created.
    """
    __tablename__ = "chain_links"

    id = Column(String(36), primary_key=True)
    evidence_id = Column(String(36), ForeignKey("evidence.id"), nullable=False, index=True)
    
    # Link sequence (order in chain)
    sequence = Column(Integer, nullable=False)
    
    # Action performed
    action = Column(String(50), nullable=False)  # created, viewed, exported, verified, archived
    action_description = Column(Text)
    
    # Actor identity
    actor_type = Column(String(20), nullable=False)  # agent, user, system
    actor_id = Column(String(36), nullable=False)
    actor_name = Column(String(255))
    actor_ip = Column(String(45))
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Cryptographic proof
    previous_link_hash = Column(String(64))  # Hash of previous link
    current_hash = Column(String(64), nullable=False)  # Hash of this link
    signature = Column(Text)  # Digital signature
    
    # Relationships
    evidence = relationship("Evidence", back_populates="chain_links")
    
    def calculate_hash(self) -> str:
        """Calculate hash of this chain link."""
        data = {
            "id": self.id,
            "evidence_id": self.evidence_id,
            "sequence": self.sequence,
            "action": self.action,
            "actor_id": self.actor_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "previous_hash": self.previous_link_hash,
        }
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        """Convert chain link to dictionary."""
        return {
            "id": self.id,
            "sequence": self.sequence,
            "action": self.action,
            "description": self.action_description,
            "actor": {
                "type": self.actor_type,
                "id": self.actor_id,
                "name": self.actor_name,
                "ip": self.actor_ip,
            },
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "hash": self.current_hash,
            "previous_hash": self.previous_link_hash,
        }


class EvidenceExport(Base):
    """
    Evidence Export Record.
    
    Tracks when evidence was exported for legal proceedings.
    """
    __tablename__ = "evidence_exports"

    id = Column(String(36), primary_key=True)
    evidence_id = Column(String(36), ForeignKey("evidence.id"), nullable=False)
    
    # Export details
    export_format = Column(String(20), nullable=False)  # pdf, html, json, raw
    export_path = Column(String(512))
    export_hash = Column(String(64))
    
    # Legal metadata
    case_number = Column(String(100))
    legal_hold = Column(String(100))
    requesting_party = Column(String(255))
    
    # Exporter identity
    exported_by = Column(String(36), nullable=False)
    exported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Verification
    verified_by = Column(String(36))
    verified_at = Column(DateTime)


# Database setup
def init_evidence_db(database_url: str = None):
    """Initialize evidence database tables."""
    from database.models import Base as DBBase
    
    if database_url is None:
        database_url = "sqlite:///evidence.db"
    
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine


SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def get_evidence_db():
    """Get database session for evidence."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
