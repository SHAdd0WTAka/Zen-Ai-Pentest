"""
Findings Management Endpoints

View, filter, and manage discovered vulnerabilities.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.core.auth import get_current_user
from api.models.finding import Finding, FindingSeverity, FindingStatus
from api.models.user import User

router = APIRouter()


class FindingResponse(BaseModel):
    """Finding response model"""

    id: str
    scan_id: str
    title: str
    description: str
    severity: str
    status: str
    cvss_score: Optional[float]
    cve_id: Optional[str]
    affected_host: str
    port: Optional[int]
    service: Optional[str]
    evidence: dict
    remediation: Optional[str]
    discovered_at: datetime
    verified_at: Optional[datetime]


class FindingUpdate(BaseModel):
    """Finding update request"""

    status: Optional[FindingStatus] = None
    severity: Optional[FindingSeverity] = None
    notes: Optional[str] = None
    false_positive: Optional[bool] = None


@router.get("/", response_model=List[FindingResponse])
async def list_findings(
    scan_id: Optional[str] = None,
    severity: Optional[FindingSeverity] = None,
    status: Optional[FindingStatus] = None,
    search: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """
    List all findings with filtering options.

    - **scan_id**: Filter by specific scan
    - **severity**: Filter by severity (critical, high, medium, low, info)
    - **status**: Filter by status (new, verified, false_positive, remediated)
    - **search**: Search in title and description
    """
    filters = {}

    if scan_id:
        filters["scan_id"] = scan_id
    if severity:
        filters["severity"] = severity
    if status:
        filters["status"] = status

    findings = await Finding.find_many(**filters).limit(limit).skip(offset).to_list()

    # Apply text search if provided
    if search:
        findings = [f for f in findings if search.lower() in f.title.lower() or search.lower() in f.description.lower()]

    return [f.to_response() for f in findings]


@router.get("/summary")
async def get_findings_summary(scan_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    """Get summary statistics of findings"""
    filters = {}
    if scan_id:
        filters["scan_id"] = scan_id

    findings = await Finding.find_many(**filters).to_list()

    summary = {
        "total": len(findings),
        "by_severity": {
            "critical": len([f for f in findings if f.severity == FindingSeverity.CRITICAL]),
            "high": len([f for f in findings if f.severity == FindingSeverity.HIGH]),
            "medium": len([f for f in findings if f.severity == FindingSeverity.MEDIUM]),
            "low": len([f for f in findings if f.severity == FindingSeverity.LOW]),
            "info": len([f for f in findings if f.severity == FindingSeverity.INFO]),
        },
        "by_status": {
            "new": len([f for f in findings if f.status == FindingStatus.NEW]),
            "verified": len([f for f in findings if f.status == FindingStatus.VERIFIED]),
            "false_positive": len([f for f in findings if f.status == FindingStatus.FALSE_POSITIVE]),
            "remediated": len([f for f in findings if f.status == FindingStatus.REMEDIATED]),
        },
    }

    return summary


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(finding_id: str, current_user: User = Depends(get_current_user)):
    """Get detailed information about a specific finding"""
    finding = await Finding.find_one(id=finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding.to_response()


@router.patch("/{finding_id}", response_model=FindingResponse)
async def update_finding(
    finding_id: str,
    update_data: FindingUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update finding status, severity, or notes"""
    finding = await Finding.find_one(id=finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    update_dict = update_data.dict(exclude_unset=True)

    if update_dict.get("false_positive"):
        update_dict["status"] = FindingStatus.FALSE_POSITIVE

    for field, value in update_dict.items():
        setattr(finding, field, value)

    await finding.save()
    return finding.to_response()


@router.post("/{finding_id}/verify")
async def verify_finding(
    finding_id: str,
    verified: bool = True,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Mark a finding as verified or false positive"""
    finding = await Finding.find_one(id=finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    if verified:
        finding.status = FindingStatus.VERIFIED
        finding.verified_at = datetime.utcnow()
    else:
        finding.status = FindingStatus.FALSE_POSITIVE

    if notes:
        finding.notes = notes

    await finding.save()
    return finding.to_response()


@router.get("/severity/{severity}", response_model=List[FindingResponse])
async def get_findings_by_severity(
    severity: FindingSeverity,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """Get all findings of a specific severity level"""
    findings = await Finding.find_many(severity=severity).limit(limit).to_list()
    return [f.to_response() for f in findings]


@router.delete("/{finding_id}")
async def delete_finding(finding_id: str, current_user: User = Depends(get_current_user)):
    """Delete a finding (requires admin permissions)"""
    finding = await Finding.find_one(id=finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    # TODO: Check admin permissions

    await finding.delete()
    return {"message": "Finding deleted"}
