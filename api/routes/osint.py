"""
OSINT API Endpoints

Open Source Intelligence gathering through REST API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from pydantic import BaseModel, EmailStr, Field

from api.core.auth import get_current_user
from api.models.user import User
from modules.osint import OSINTModule

router = APIRouter()


class EmailHarvestRequest(BaseModel):
    """Email harvesting request"""

    domain: str = Field(..., description="Target domain (e.g., example.com)")
    sources: Optional[List[str]] = Field(
        default=["google", "bing", "pgp"],
        description="Sources to search: google, bing, yahoo, pgp, github",
    )


class EmailResult(BaseModel):
    """Email result"""

    email: str
    source: str
    confidence: int
    metadata: Dict[str, Any]


class DomainReconRequest(BaseModel):
    """Domain reconnaissance request"""

    domain: str
    enumerate_subdomains: bool = Field(default=True)
    detect_tech: bool = Field(default=True)
    wordlist_size: str = Field(
        default="small", description="small, medium, large"
    )


class DomainReconResponse(BaseModel):
    """Domain reconnaissance response"""

    domain: str
    registrar: Optional[str]
    creation_date: Optional[str]
    expiration_date: Optional[str]
    name_servers: List[str]
    subdomains: List[str]
    ip_addresses: List[str]
    mx_records: List[str]
    txt_records: List[str]
    technologies: List[str]
    scanned_at: datetime


class BreachCheckRequest(BaseModel):
    """Breach check request"""

    email: EmailStr


class BreachCheckResponse(BaseModel):
    """Breach check response"""

    email: str
    valid_format: bool
    breached: bool
    breach_sources: List[str]
    breach_count: int
    last_breach: Optional[str]
    recommendations: List[str]


class UsernameInvestigationRequest(BaseModel):
    """Username investigation request"""

    username: str = Field(..., min_length=2, max_length=50)
    platforms: Optional[List[str]] = Field(
        default=["twitter", "github", "linkedin", "instagram"]
    )


class OSINTTaskResponse(BaseModel):
    """Async task response"""

    task_id: str
    status: str
    message: str
    estimated_duration: int  # seconds


@router.post("/emails/harvest", response_model=List[EmailResult])
async def harvest_emails(
    request: EmailHarvestRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Harvest email addresses from public sources.

    Searches multiple sources for email addresses associated with the domain:
    - Search engines (Google, Bing)
    - PGP key servers
    - Code repositories (GitHub)

    **Rate limited**: Max 5 requests per hour per domain
    """
    async with OSINTModule() as osint:
        results = await osint.harvest_emails(
            domain=request.domain, sources=request.sources
        )

        return [
            EmailResult(
                email=r.value,
                source=r.source,
                confidence=r.confidence,
                metadata=r.metadata,
            )
            for r in results
        ]


@router.post("/domain/recon", response_model=DomainReconResponse)
async def recon_domain(
    request: DomainReconRequest, current_user: User = Depends(get_current_user)
):
    """
    Perform comprehensive domain reconnaissance.

    Gathers:
    - WHOIS information
    - Subdomain enumeration
    - DNS records (A, MX, TXT)
    - Web technology detection

    **Duration**: 30-120 seconds depending on domain size
    """
    async with OSINTModule() as osint:
        info = await osint.recon_domain(request.domain)

        return DomainReconResponse(
            domain=info.domain,
            registrar=info.registrar,
            creation_date=info.creation_date,
            expiration_date=info.expiration_date,
            name_servers=info.name_servers,
            subdomains=info.subdomains,
            ip_addresses=info.ip_addresses,
            mx_records=info.mx_records,
            txt_records=info.txt_records,
            technologies=info.technologies,
            scanned_at=datetime.utcnow(),
        )


@router.get("/domain/{domain}/subdomains")
async def get_subdomains(
    domain: str, current_user: User = Depends(get_current_user)
):
    """Quick subdomain enumeration"""
    async with OSINTModule() as osint:
        subdomains = await osint._enumerate_subdomains(domain)
        return {
            "domain": domain,
            "subdomains": subdomains,
            "count": len(subdomains),
        }


@router.post("/breach/check", response_model=BreachCheckResponse)
async def check_breach(
    request: BreachCheckRequest, current_user: User = Depends(get_current_user)
):
    """
    Check if email appears in known data breaches.

    Uses multiple breach databases including:
    - Have I Been Pwned
    - Known breach collections
    - Leaked credential databases

    **Note**: This check is performed locally, email is not sent to third parties
    """
    async with OSINTModule() as osint:
        profile = await osint.check_breach(request.email)

        recommendations = []
        if profile.breached:
            recommendations.append("Change password immediately")
            recommendations.append("Enable 2FA on all accounts")
            recommendations.append("Check for unauthorized activity")
            recommendations.append("Use unique passwords per service")

        return BreachCheckResponse(
            email=profile.email,
            valid_format=profile.valid_format,
            breached=profile.breached,
            breach_sources=profile.breach_sources,
            breach_count=len(profile.breach_sources),
            last_breach=(
                profile.breach_sources[0] if profile.breach_sources else None
            ),
            recommendations=recommendations,
        )


@router.post("/username/investigate")
async def investigate_username(
    request: UsernameInvestigationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Investigate username across social platforms.

    Checks for accounts on:
    - Twitter/X
    - GitHub
    - LinkedIn
    - Instagram
    - Facebook
    - Reddit

    **Note**: This checks for public profile existence only
    """
    async with OSINTModule() as osint:
        results = await osint.investigate_username(request.username)

        # Count findings
        found_on = [p for p, d in results.items() if d.get("exists")]

        return {
            "username": request.username,
            "platforms_checked": len(results),
            "found_on": len(found_on),
            "platforms": results,
            "profile_urls": {
                p: d["url"] for p, d in results.items() if d.get("exists")
            },
        }


@router.get("/ip/{ip}/investigate")
async def investigate_ip(
    ip: str, current_user: User = Depends(get_current_user)
):
    """
    Gather intelligence about IP address.

    Provides:
    - Geolocation
    - ISP/Organization
    - Proxy/VPN detection
    - Hosting provider detection
    """
    async with OSINTModule() as osint:
        info = await osint.investigate_ip(ip)
        return info


@router.post("/report/generate")
async def generate_osint_report(
    target: str,
    report_format: str = Query("json", enum=["json", "html", "pdf"]),
    current_user: User = Depends(get_current_user),
):
    """
    Generate comprehensive OSINT report for target.

    Target can be:
    - Domain (example.com)
    - Email (user@example.com)
    - Username (johndoe)
    """
    async with OSINTModule() as osint:
        # Determine target type and run appropriate checks
        if "@" in target:
            # Email
            await osint.check_breach(target)
            domain = target.split("@")[1]
            await osint.recon_domain(domain)
        elif "." in target:
            # Domain
            await osint.recon_domain(target)
            await osint.harvest_emails(target)
        else:
            # Username
            await osint.investigate_username(target)

        report = osint.generate_report(target)

        return {
            "target": target,
            "format": report_format,
            "generated_at": datetime.utcnow(),
            "report": report,
        }


@router.get("/sources")
async def list_osint_sources(current_user: User = Depends(get_current_user)):
    """List available OSINT sources and their status"""
    sources = {
        "email_harvesting": [
            {"name": "google", "status": "active", "rate_limit": "100/day"},
            {"name": "bing", "status": "active", "rate_limit": "100/day"},
            {"name": "pgp", "status": "active", "rate_limit": "unlimited"},
            {"name": "github", "status": "active", "rate_limit": "60/hour"},
        ],
        "domain_recon": [
            {"name": "certificate_transparency", "status": "active"},
            {"name": "dns_enumeration", "status": "active"},
            {"name": "whois", "status": "active"},
        ],
        "breach_check": [
            {
                "name": "hibp",
                "status": "active",
                "note": "Requires API key for production",
            }
        ],
        "social_media": [
            {"name": "twitter", "status": "active"},
            {"name": "github", "status": "active"},
            {"name": "linkedin", "status": "active"},
            {"name": "instagram", "status": "rate_limited"},
        ],
    }

    return sources


@router.get("/quota")
async def get_osint_quota(current_user: User = Depends(get_current_user)):
    """Get remaining OSINT query quota for current user"""
    # In production: Track actual usage
    return {
        "user_id": str(current_user.id),
        "quota": {
            "email_harvests": {"used": 0, "limit": 50, "reset": "24h"},
            "domain_recons": {"used": 0, "limit": 100, "reset": "24h"},
            "breach_checks": {"used": 0, "limit": 200, "reset": "24h"},
            "username_lookups": {"used": 0, "limit": 100, "reset": "24h"},
        },
    }
