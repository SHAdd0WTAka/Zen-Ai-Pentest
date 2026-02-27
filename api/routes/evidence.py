"""
Evidence API Routes

REST API endpoints for evidence collection and management.
"""

import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.models import SessionLocal
from evidence import ChainOfCustody, EvidenceCollector
from evidence.models import Evidence

router = APIRouter(prefix="/evidence", tags=["Evidence"])


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic Schemas
class EvidenceCreate(BaseModel):
    """Schema for creating evidence."""

    scan_id: str = Field(..., description="Scan UUID")
    target_url: str = Field(..., description="Target URL")
    vulnerability: str = Field(..., description="Vulnerability type")
    severity: str = Field(..., description="critical/high/medium/low/info")
    payload: Optional[str] = Field(
        None, description="Proof of concept payload"
    )
    description: Optional[str] = Field(
        None, description="Detailed description"
    )
    remediation: Optional[str] = Field(None, description="Remediation advice")
    cvss_score: Optional[str] = Field(None, description="CVSS v3.1 score")
    cvss_vector: Optional[str] = Field(None, description="CVSS vector string")


class EvidenceResponse(BaseModel):
    """Schema for evidence response."""

    id: str
    scan_id: str
    evidence_type: str
    severity: str
    status: str
    title: str
    description: Optional[str]
    vulnerability_type: str
    proof_of_concept: Optional[str]
    target: dict
    timestamps: dict
    integrity: dict

    class Config:
        from_attributes = True


class EvidenceListResponse(BaseModel):
    """Schema for evidence list."""

    items: List[EvidenceResponse]
    total: int
    page: int
    page_size: int


class ChainOfCustodyResponse(BaseModel):
    """Schema for chain of custody."""

    valid: bool
    links_checked: int
    issues: Optional[List[str]]
    chain: List[dict]


@router.post(
    "/web",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_web_evidence(
    data: EvidenceCreate,
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Create web vulnerability evidence.

    Captures a web-based finding with optional screenshot.
    """
    collector = EvidenceCollector(
        db=db,
        scan_id=data.scan_id,
        agent_id=agent_id,
    )

    try:
        evidence = await collector.capture_web_finding(
            target_url=data.target_url,
            vulnerability=data.vulnerability,
            severity=data.severity,
            payload=data.payload,
            description=data.description,
            remediation=data.remediation,
            cvss_score=data.cvss_score,
            cvss_vector=data.cvss_vector,
            take_screenshot=True,
        )

        return evidence.to_dict()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to capture evidence: {str(e)}",
        )


@router.post(
    "/api",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_api_evidence(
    data: EvidenceCreate,
    request_data: Optional[dict] = None,
    response_data: Optional[dict] = None,
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Create API vulnerability evidence.

    Captures API findings with request/response data.
    """
    collector = EvidenceCollector(
        db=db,
        scan_id=data.scan_id,
        agent_id=agent_id,
    )

    try:
        evidence = collector.capture_api_finding(
            endpoint=data.target_url,
            method="POST",  # Could be parameterized
            vulnerability=data.vulnerability,
            severity=data.severity,
            request_data=request_data,
            response_data=response_data,
            description=data.description,
            remediation=data.remediation,
        )

        return evidence.to_dict()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to capture evidence: {str(e)}",
        )


@router.post(
    "/network",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_network_evidence(
    scan_id: str,
    target_ip: str,
    target_port: int,
    service: str,
    vulnerability: str,
    severity: str,
    banner: Optional[str] = None,
    nmap_output: Optional[str] = None,
    description: Optional[str] = None,
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Create network vulnerability evidence.

    Captures network scan findings.
    """
    collector = EvidenceCollector(
        db=db,
        scan_id=scan_id,
        agent_id=agent_id,
    )

    try:
        evidence = collector.capture_network_finding(
            target_ip=target_ip,
            target_port=target_port,
            service=service,
            vulnerability=vulnerability,
            severity=severity,
            banner=banner,
            nmap_output=nmap_output,
            description=description,
        )

        return evidence.to_dict()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to capture evidence: {str(e)}",
        )


@router.get("/", response_model=EvidenceListResponse)
def list_evidence(
    scan_id: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    vulnerability_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List all evidence with filtering.
    """
    query = db.query(Evidence)

    if scan_id:
        query = query.filter(Evidence.scan_id == scan_id)
    if severity:
        query = query.filter(Evidence.severity == severity)
    if status:
        query = query.filter(Evidence.status == status)
    if vulnerability_type:
        query = query.filter(Evidence.vulnerability_type == vulnerability_type)

    total = query.count()

    # Pagination
    offset = (page - 1) * page_size
    evidence_list = query.offset(offset).limit(page_size).all()

    return {
        "items": [e.to_dict() for e in evidence_list],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{evidence_id}", response_model=EvidenceResponse)
def get_evidence(
    evidence_id: str,
    db: Session = Depends(get_db),
):
    """
    Get a single evidence by ID.
    """
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found"
        )

    return evidence.to_dict()


@router.get("/{evidence_id}/chain", response_model=ChainOfCustodyResponse)
def get_chain_of_custody(
    evidence_id: str,
    db: Session = Depends(get_db),
):
    """
    Get chain of custody for evidence.

    Returns the complete audit trail with integrity verification.
    """
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found"
        )

    chain = ChainOfCustody(db)
    verification = chain.verify_chain(evidence_id)
    links = chain.get_chain(evidence_id)

    return {
        "valid": verification["valid"],
        "links_checked": verification["links_checked"],
        "issues": verification.get("issues"),
        "chain": [link.to_dict() for link in links],
    }


@router.get("/{evidence_id}/verify")
def verify_evidence_integrity(
    evidence_id: str,
    db: Session = Depends(get_db),
):
    """
    Verify evidence integrity.

    Checks both chain of custody and file hashes.
    """
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found"
        )

    # Verify chain
    chain = ChainOfCustody(db)
    chain_valid = chain.verify_chain(evidence_id)["valid"]

    # Verify file integrity
    file_valid = evidence.verify_integrity()

    return {
        "evidence_id": evidence_id,
        "chain_valid": chain_valid,
        "file_valid": file_valid,
        "overall_valid": chain_valid and file_valid,
        "hash": evidence.file_hash_sha256,
    }


@router.get("/{evidence_id}/download")
def download_evidence_file(
    evidence_id: str,
    db: Session = Depends(get_db),
):
    """
    Download evidence file (screenshot, log, etc.).
    """
    from fastapi.responses import FileResponse

    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found"
        )

    if not evidence.file_path or not os.path.exists(evidence.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence file not found",
        )

    # Add chain of custody link for download
    chain = ChainOfCustody(db)
    chain.add_link(
        evidence_id=evidence_id,
        action="downloaded",
        actor_type="user",
        actor_id="current_user",  # Should come from auth
        description="Evidence file downloaded",
    )

    return FileResponse(
        evidence.file_path,
        filename=f"evidence_{evidence_id}_{evidence.evidence_type}.png",
    )


@router.post("/{evidence_id}/export")
def export_evidence(
    evidence_id: str,
    format: str = Query("pdf", enum=["pdf", "html", "json"]),
    db: Session = Depends(get_db),
):
    """
    Export evidence for legal proceedings.

    Generates a court-ready report with chain of custody.
    """
    from evidence.storage import EvidenceExporter

    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found"
        )

    # Get chain of custody report
    chain = ChainOfCustody(db)
    chain_report = chain.export_chain_report(evidence_id)

    # Export evidence
    exporter = EvidenceExporter(None)

    output_path = f"evidence/exports/{evidence_id}.{format}"

    if format == "json":
        exporter.export_to_json([evidence.to_dict()], output_path)
    elif format == "html":
        exporter.export_to_html([evidence.to_dict()], output_path)
    elif format == "pdf":
        exporter.export_to_pdf([evidence.to_dict()], output_path)

    # Add export link to chain
    chain.add_link(
        evidence_id=evidence_id,
        action="exported",
        actor_type="user",
        actor_id="current_user",
        description=f"Evidence exported as {format.upper()}",
    )

    return {
        "evidence_id": evidence_id,
        "format": format,
        "export_path": output_path,
        "chain_report": chain_report,
    }


@router.get("/stats/summary")
def get_evidence_stats(
    scan_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get evidence statistics.
    """
    from sqlalchemy import func

    query = db.query(Evidence)
    if scan_id:
        query = query.filter(Evidence.scan_id == scan_id)

    total = query.count()

    # Severity breakdown
    severity_counts = (
        query.with_entities(Evidence.severity, func.count(Evidence.id))
        .group_by(Evidence.severity)
        .all()
    )

    # Type breakdown
    type_counts = (
        query.with_entities(Evidence.evidence_type, func.count(Evidence.id))
        .group_by(Evidence.evidence_type)
        .all()
    )

    # Recent evidence
    recent = query.order_by(Evidence.collected_at.desc()).limit(5).all()

    return {
        "total_evidence": total,
        "by_severity": {s.value: c for s, c in severity_counts},
        "by_type": {t: c for t, c in type_counts},
        "recent": [e.to_dict() for e in recent],
    }
