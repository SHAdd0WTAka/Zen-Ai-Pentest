"""
Analysis Bot API Routes

Provides endpoints for autonomous vulnerability analysis.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from analysis_bot import AnalysisBot, AnalysisConfig
from api.auth import get_current_user
from database.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])


# Request/Response Models
class AnalysisTarget(BaseModel):
    """Analysis target specification"""

    type: str = Field(..., description="Target type: url, code, file")
    value: str = Field(..., description="Target value to analyze")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class AnalysisRequest(BaseModel):
    """Request body for analysis"""

    target: AnalysisTarget
    config: Optional[Dict[str, Any]] = Field(default=None, description="Analysis configuration")


class VulnerabilityResult(BaseModel):
    """Vulnerability finding"""

    id: str
    title: str
    description: str
    severity: str
    cvss_score: float
    cvss_vector: str
    cwe_id: Optional[str] = None
    evidence: Dict[str, Any]
    remediation: Optional[str] = None


class RiskAssessment(BaseModel):
    """Risk assessment result"""

    score: float
    level: str
    factors: Dict[str, float]
    breakdown: Dict[str, Any]


class AnalysisResponse(BaseModel):
    """Analysis response"""

    analysis_id: str
    status: str
    target: AnalysisTarget
    vulnerabilities: List[VulnerabilityResult]
    risk_assessment: RiskAssessment
    recommendations: List[Dict[str, Any]]
    completed_at: Optional[str] = None


# Global Analysis Bot instance
_analysis_bot: Optional[AnalysisBot] = None


def get_analysis_bot() -> AnalysisBot:
    """Get or create Analysis Bot instance"""
    global _analysis_bot
    if _analysis_bot is None:
        _analysis_bot = AnalysisBot()
    return _analysis_bot


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_target(
    request: AnalysisRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)
):
    """
    Analyze a target for vulnerabilities.

    Performs comprehensive vulnerability analysis including:
    - Static code analysis (if target is code)
    - Pattern-based vulnerability detection
    - CVSS scoring
    - Risk assessment
    - Exploitability check
    - Remediation recommendations

    Example:
        ```json
        {
            "target": {
                "type": "code",
                "value": "<?php echo $_GET['id']; ?>",
                "context": {"language": "php"}
            }
        }
        ```
    """
    try:
        bot = get_analysis_bot()

        # Create analysis config
        config = AnalysisConfig(user_id=str(current_user.id), **(request.config or {}))

        # Run analysis
        result = await bot.analyze(target=request.target.value, target_type=request.target.type, config=config)

        return AnalysisResponse(
            analysis_id=result.id,
            status=result.status,
            target=request.target,
            vulnerabilities=[
                VulnerabilityResult(
                    id=v.id,
                    title=v.title,
                    description=v.description,
                    severity=v.severity,
                    cvss_score=v.cvss_score,
                    cvss_vector=v.cvss_vector,
                    cwe_id=v.cwe_id,
                    evidence=v.evidence,
                    remediation=v.remediation,
                )
                for v in result.vulnerabilities
            ],
            risk_assessment=RiskAssessment(
                score=result.risk_score.score,
                level=result.risk_score.level,
                factors=result.risk_score.factors,
                breakdown=result.risk_score.breakdown,
            ),
            recommendations=result.recommendations,
            completed_at=result.completed_at,
        )

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/status/{analysis_id}")
async def get_analysis_status(analysis_id: str, current_user: User = Depends(get_current_user)):
    """Get status of an analysis job"""
    bot = get_analysis_bot()
    status = await bot.get_status(analysis_id)
    return status


@router.get("/vulnerabilities/{analysis_id}")
async def get_vulnerabilities(analysis_id: str, current_user: User = Depends(get_current_user)):
    """Get vulnerabilities found in an analysis"""
    bot = get_analysis_bot()
    vulns = await bot.get_vulnerabilities(analysis_id)
    return {"vulnerabilities": vulns}


@router.post("/batch")
async def analyze_batch(targets: List[AnalysisTarget], current_user: User = Depends(get_current_user)):
    """Analyze multiple targets in batch"""
    bot = get_analysis_bot()
    results = []

    for target in targets:
        result = await bot.analyze(target=target.value, target_type=target.type)
        results.append(result)

    return {"results": results}
