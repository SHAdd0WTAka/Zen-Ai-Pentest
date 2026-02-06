"""
Risk Engine - Combines CVSS + EPSS + Business Impact
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from .cvss import CVSSCalculator, CVSSVector
from .epss import EPSSClient
from .business_impact import BusinessImpactScorer, BusinessContext


@dataclass
class RiskScore:
    """Complete risk assessment"""
    cve_id: str
    cvss_score: float
    cvss_severity: str
    epss_score: float
    epss_probability: float
    business_impact_score: float
    business_impact_level: str
    
    # Combined scores
    overall_risk_score: float  # 0-10
    risk_priority: str  # Critical, High, Medium, Low
    
    # Components
    technical_risk: float  # CVSS weighted
    exploitation_probability: float  # EPSS weighted
    business_risk: float  # Business impact weighted
    
    # Metadata
    timestamp: str
    data_quality: str  # Complete, Partial, Estimated


class RiskEngine:
    """
    Unified risk scoring engine combining multiple factors:
    - CVSS (Technical severity)
    - EPSS (Exploit probability)
    - Business Impact (Asset value + Compliance)
    
    Formula:
    Overall Risk = (CVSS * 0.4) + (EPSS * 10 * 0.3) + (Business Impact * 0.3)
    """
    
    WEIGHTS = {
        "cvss": 0.40,
        "epss": 0.30,
        "business": 0.30,
    }
    
    def __init__(
        self,
        cvss_calculator: Optional[CVSSCalculator] = None,
        epss_client: Optional[EPSSClient] = None,
        impact_scorer: Optional[BusinessImpactScorer] = None
    ):
        self.cvss = cvss_calculator or CVSSCalculator()
        self.epss = epss_client or EPSSClient()
        self.impact = impact_scorer or BusinessImpactScorer()
        
        self.calculation_history: List[RiskScore] = []
    
    def calculate_risk(
        self,
        cve_id: str,
        cvss_vector: Optional[CVSSVector] = None,
        business_context: Optional[BusinessContext] = None,
        cve_data: Optional[Dict] = None
    ) -> RiskScore:
        """
        Calculate comprehensive risk score for a vulnerability
        """
        # 1. CVSS Score
        if cvss_vector:
            cvss_result = self.cvss.calculate_full(cvss_vector)
        elif cve_data:
            cvss_vector = self.cvss.estimate_from_cve(cve_data)
            cvss_result = self.cvss.calculate_full(cvss_vector)
        else:
            # Default if no data
            cvss_result = {"base_score": 5.0, "severity": "Medium"}
        
        cvss_score = cvss_result["base_score"]
        cvss_severity = cvss_result["severity"]
        
        # 2. EPSS Score
        epss_data = self.epss.get_score(cve_id)
        if epss_data:
            epss_score = epss_data.epss_score
            epss_prob = epss_data.probability_percentage
            data_quality = "Complete"
        else:
            # Estimate from CVSS
            epss_score = self.epss.estimate_score(cvss_score)
            epss_prob = epss_score * 100
            data_quality = "Estimated"
        
        # 3. Business Impact
        if business_context:
            impact_result = self.impact.calculate_impact(cvss_severity, business_context)
            business_score = impact_result["business_impact_score"]
            business_level = impact_result["impact_level"]
        else:
            # Default: assume medium impact
            business_score = 5.0
            business_level = "Medium Business Impact"
            data_quality = "Partial" if data_quality == "Complete" else data_quality
        
        # 4. Calculate Overall Risk
        technical_risk = cvss_score * self.WEIGHTS["cvss"]
        exploitation_risk = epss_score * 10 * self.WEIGHTS["epss"]
        business_risk_score = business_score * self.WEIGHTS["business"]
        
        overall_score = technical_risk + exploitation_risk + business_risk_score
        overall_score = min(round(overall_score, 1), 10.0)
        
        # Determine priority
        priority = self._get_priority(overall_score, epss_score, cvss_severity)
        
        risk_score = RiskScore(
            cve_id=cve_id,
            cvss_score=cvss_score,
            cvss_severity=cvss_severity,
            epss_score=epss_score,
            epss_probability=round(epss_prob, 1),
            business_impact_score=business_score,
            business_impact_level=business_level,
            overall_risk_score=overall_score,
            risk_priority=priority,
            technical_risk=round(technical_risk, 2),
            exploitation_probability=round(exploitation_risk, 2),
            business_risk=round(business_risk_score, 2),
            timestamp=datetime.now().isoformat(),
            data_quality=data_quality
        )
        
        self.calculation_history.append(risk_score)
        return risk_score
    
    def calculate_batch(
        self,
        cves: List[Dict],
        business_context: Optional[BusinessContext] = None
    ) -> List[RiskScore]:
        """
        Calculate risk for multiple CVEs
        """
        results = []
        
        # Batch fetch EPSS scores
        cve_ids = [cve["id"] for cve in cves]
        epss_batch = self.epss.get_scores_batch(cve_ids)
        
        for cve in cves:
            cve_id = cve["id"]
            cve_data = cve.get("data", {})
            
            # Use cached EPSS if available
            if cve_id in epss_batch:
                # Temporarily inject into client cache
                self.epss.cache[cve_id] = epss_batch[cve_id]
            
            risk = self.calculate_risk(
                cve_id=cve_id,
                cve_data=cve_data,
                business_context=business_context
            )
            results.append(risk)
        
        # Sort by overall risk descending
        return sorted(results, key=lambda x: x.overall_risk_score, reverse=True)
    
    def _get_priority(
        self,
        overall_score: float,
        epss_score: float,
        cvss_severity: str
    ) -> str:
        """
        Determine risk priority considering all factors
        """
        # Critical: High CVSS + High EPSS
        if overall_score >= 8.0:
            return "Critical"
        
        # High: Either high CVSS or (medium CVSS + high EPSS)
        if overall_score >= 6.0:
            return "High"
        
        if cvss_severity == "High" and epss_score > 0.3:
            return "High"
        
        # Medium
        if overall_score >= 4.0:
            return "Medium"
        
        # Low
        if overall_score >= 2.0:
            return "Low"
        
        return "Minimal"
    
    def get_risk_distribution(self) -> Dict[str, int]:
        """Get distribution of risk priorities"""
        if not self.calculation_history:
            return {}
        
        distribution = {
            "Critical": 0,
            "High": 0,
            "Medium": 0,
            "Low": 0,
            "Minimal": 0
        }
        
        for score in self.calculation_history:
            priority = score.risk_priority
            if priority in distribution:
                distribution[priority] += 1
        
        return distribution
    
    def get_critical_cves(self, threshold: float = 7.0) -> List[RiskScore]:
        """Get CVEs above risk threshold"""
        return [
            score for score in self.calculation_history
            if score.overall_risk_score >= threshold
        ]
    
    def get_remediation_priority(self) -> List[Dict]:
        """Generate remediation priority list"""
        sorted_scores = sorted(
            self.calculation_history,
            key=lambda x: (x.overall_risk_score, x.epss_probability),
            reverse=True
        )
        
        priority_list = []
        for i, score in enumerate(sorted_scores[:20], 1):
            priority_list.append({
                "rank": i,
                "cve_id": score.cve_id,
                "priority": score.risk_priority,
                "overall_score": score.overall_risk_score,
                "cvss": score.cvss_score,
                "epss_percent": score.epss_probability,
                "business_impact": score.business_impact_level,
                "action": self._get_recommended_action(score)
            })
        
        return priority_list
    
    def _get_recommended_action(self, score: RiskScore) -> str:
        """Recommend action based on risk"""
        if score.risk_priority == "Critical":
            return "Immediate patching required - 24-48 hours"
        elif score.risk_priority == "High":
            return "Urgent remediation - 1 week"
        elif score.risk_priority == "Medium":
            return "Plan remediation - 30 days"
        elif score.risk_priority == "Low":
            return "Schedule during maintenance"
        else:
            return "Monitor only"
