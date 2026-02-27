"""
Report Database Models

Models for storing report metadata and generation history.
"""

import enum
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ReportType(str, enum.Enum):
    """Types of penetration test reports."""
    EXECUTIVE = "executive"  # C-Level summary
    TECHNICAL = "technical"  # Full technical details
    COMPLIANCE = "compliance"  # Compliance-focused
    EVIDENCE = "evidence"  # Evidence package only
    CUSTOM = "custom"  # User-defined template


class ReportStatus(str, enum.Enum):
    """Status of report generation."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class ReportFormat(str, enum.Enum):
    """Supported export formats."""
    PDF = "pdf"
    HTML = "html"
    DOCX = "docx"
    JSON = "json"
    XML = "xml"


class ComplianceFramework(str, enum.Enum):
    """Supported compliance frameworks."""
    OWASP_TOP_10 = "owasp_top_10"
    OWASP_ASVS = "owasp_asvs"
    ISO_27001 = "iso_27001"
    PCI_DSS = "pci_dss"
    NIST_CSF = "nist_csf"
    CIS_CONTROLS = "cis_controls"
    BSI_Grundschutz = "bsi_grundschutz"


class Report(Base):
    """
    Report generation record.
    
    Tracks all generated reports with metadata for audit purposes.
    """
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String(36), ForeignKey("scans.id"), nullable=False, index=True)
    
    # Report metadata
    report_type = Column(Enum(ReportType), nullable=False)
    report_format = Column(Enum(ReportFormat), nullable=False)
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING)
    
    # Report details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    company_name = Column(String(255))
    
    # Scope
    scope_included = Column(Text)  # What was tested
    scope_excluded = Column(Text)  # What was NOT tested
    
    # Dates
    pentest_start_date = Column(DateTime)
    pentest_end_date = Column(DateTime)
    report_date = Column(DateTime, default=datetime.utcnow)
    
    # Risk summary
    total_findings = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    info_count = Column(Integer, default=0)
    
    # CVSS statistics
    avg_cvss_score = Column(String(10))
    max_cvss_score = Column(String(10))
    
    # File info
    file_path = Column(String(512))
    file_size = Column(Integer)
    file_hash_sha256 = Column(String(64))
    
    # Compliance mapping
    compliance_framework = Column(Enum(ComplianceFramework))
    compliance_mappings = Column(Text)  # JSON string
    
    # Generation info
    generated_by = Column(String(36))  # User ID
    generated_at = Column(DateTime, default=datetime.utcnow)
    generation_duration_ms = Column(Integer)
    
    # Template used
    template_name = Column(String(100))
    template_version = Column(String(20))
    
    # Options
    include_evidence = Column(String(1), default="1")  # Boolean as string for SQLite
    include_remediation = Column(String(1), default="1")
    include_appendices = Column(String(1), default="1")
    
    # Error info (if failed)
    error_message = Column(Text)
    
    def to_dict(self) -> Dict:
        """Convert report to dictionary."""
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "report_type": self.report_type.value if self.report_type else None,
            "format": self.report_format.value if self.report_format else None,
            "status": self.status.value if self.status else None,
            "title": self.title,
            "description": self.description,
            "company_name": self.company_name,
            "scope": {
                "included": self.scope_included,
                "excluded": self.scope_excluded,
            },
            "dates": {
                "pentest_start": self.pentest_start_date.isoformat() if self.pentest_start_date else None,
                "pentest_end": self.pentest_end_date.isoformat() if self.pentest_end_date else None,
                "report": self.report_date.isoformat() if self.report_date else None,
            },
            "findings_summary": {
                "total": self.total_findings,
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "info": self.info_count,
            },
            "cvss": {
                "average": self.avg_cvss_score,
                "maximum": self.max_cvss_score,
            },
            "file": {
                "path": self.file_path,
                "size": self.file_size,
                "hash": self.file_hash_sha256,
            },
            "compliance": {
                "framework": self.compliance_framework.value if self.compliance_framework else None,
                "mappings": self.compliance_mappings,
            },
            "generation": {
                "by": self.generated_by,
                "at": self.generated_at.isoformat() if self.generated_at else None,
                "duration_ms": self.generation_duration_ms,
            },
            "template": {
                "name": self.template_name,
                "version": self.template_version,
            },
            "options": {
                "include_evidence": self.include_evidence == "1",
                "include_remediation": self.include_remediation == "1",
                "include_appendices": self.include_appendices == "1",
            },
        }
    
    def get_risk_rating(self) -> str:
        """Calculate overall risk rating based on findings."""
        if self.critical_count > 0:
            return "CRITICAL"
        elif self.high_count > 0:
            return "HIGH"
        elif self.medium_count > 0:
            return "MEDIUM"
        elif self.low_count > 0:
            return "LOW"
        else:
            return "INFORMATIONAL"


class ReportSection(Base):
    """
    Individual sections within a report.
    
    Allows for modular report building and custom sections.
    """
    __tablename__ = "report_sections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("reports.id"), nullable=False)
    
    section_name = Column(String(100), nullable=False)
    section_order = Column(Integer, default=0)
    section_content = Column(Text)  # HTML or Markdown content
    
    # Section metadata
    section_type = Column(String(50))  # summary, findings, evidence, appendix
    included = Column(String(1), default="1")


class ReportTemplate(Base):
    """
    Report templates for reuse.
    
    Pre-configured report layouts for different use cases.
    """
    __tablename__ = "report_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    report_type = Column(Enum(ReportType), nullable=False)
    
    # Template content (Jinja2)
    html_template = Column(Text)
    css_styles = Column(Text)
    
    # Default options
    default_include_evidence = Column(String(1), default="1")
    default_include_remediation = Column(String(1), default="1")
    default_include_appendices = Column(String(1), default="1")
    
    # Version control
    version = Column(String(20), default="1.0.0")
    created_by = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    is_default = Column(String(1), default="0")
    is_active = Column(String(1), default="1")


# Database setup
def init_reports_db(database_url: str = None):
    """Initialize reports database tables."""
    from sqlalchemy import create_engine
    
    if database_url is None:
        database_url = "sqlite:///reports.db"
    
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine
