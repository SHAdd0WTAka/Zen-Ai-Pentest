"""
Risk Report Generator
Creates comprehensive risk reports
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from .risk_engine import RiskScore


class RiskReportGenerator:
    """
    Generates various risk report formats
    """
    
    def __init__(self):
        self.templates = {
            "executive": self._generate_executive_summary,
            "technical": self._generate_technical_report,
            "remediation": self._generate_remediation_plan,
        }
    
    def generate(
        self,
        risk_scores: List[RiskScore],
        report_type: str = "executive",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate risk report
        """
        if report_type in self.templates:
            return self.templates[report_type](risk_scores, **kwargs)
        
        return self._generate_full_report(risk_scores)
    
    def _generate_executive_summary(
        self,
        risk_scores: List[RiskScore],
        organization: str = "Organization"
    ) -> Dict:
        """Generate executive summary"""
        
        # Calculate statistics
        total = len(risk_scores)
        critical = sum(1 for r in risk_scores if r.risk_priority == "Critical")
        high = sum(1 for r in risk_scores if r.risk_priority == "High")
        medium = sum(1 for r in risk_scores if r.risk_priority == "Medium")
        
        avg_cvss = sum(r.cvss_score for r in risk_scores) / total if total > 0 else 0
        avg_epss = sum(r.epss_probability for r in risk_scores) / total if total > 0 else 0
        
        # Top risks
        top_risks = sorted(
            risk_scores,
            key=lambda x: x.overall_risk_score,
            reverse=True
        )[:5]
        
        return {
            "report_type": "Executive Summary",
            "generated_at": datetime.now().isoformat(),
            "organization": organization,
            "summary": {
                "total_vulnerabilities": total,
                "critical_count": critical,
                "high_count": high,
                "medium_count": medium,
                "average_cvss": round(avg_cvss, 1),
                "average_epss": round(avg_epss, 1),
            },
            "risk_distribution": {
                "Critical": critical,
                "High": high,
                "Medium": medium,
                "Low": total - critical - high - medium,
            },
            "top_risks": [
                {
                    "cve_id": r.cve_id,
                    "priority": r.risk_priority,
                    "score": r.overall_risk_score,
                    "cvss": r.cvss_score,
                    "epss": r.epss_probability,
                }
                for r in top_risks
            ],
            "recommendations": self._generate_executive_recommendations(
                critical, high, medium
            )
        }
    
    def _generate_technical_report(
        self,
        risk_scores: List[RiskScore],
        include_details: bool = True
    ) -> Dict:
        """Generate detailed technical report"""
        
        return {
            "report_type": "Technical Report",
            "generated_at": datetime.now().isoformat(),
            "vulnerabilities": [
                {
                    "cve_id": r.cve_id,
                    "risk_score": r.overall_risk_score,
                    "risk_priority": r.risk_priority,
                    "cvss": {
                        "score": r.cvss_score,
                        "severity": r.cvss_severity,
                    },
                    "epss": {
                        "score": r.epss_score,
                        "probability_percent": r.epss_probability,
                    },
                    "business_impact": {
                        "score": r.business_impact_score,
                        "level": r.business_impact_level,
                    },
                    "component_scores": {
                        "technical": r.technical_risk,
                        "exploitation": r.exploitation_probability,
                        "business": r.business_risk,
                    },
                    "data_quality": r.data_quality,
                    "timestamp": r.timestamp,
                }
                for r in sorted(risk_scores, key=lambda x: x.overall_risk_score, reverse=True)
            ],
            "statistics": self._calculate_statistics(risk_scores)
        }
    
    def _generate_remediation_plan(
        self,
        risk_scores: List[RiskScore],
        max_items: int = 20
    ) -> Dict:
        """Generate prioritized remediation plan"""
        
        # Sort by overall risk
        sorted_scores = sorted(
            risk_scores,
            key=lambda x: (x.overall_risk_score, x.epss_probability),
            reverse=True
        )
        
        remediation_items = []
        for i, score in enumerate(sorted_scores[:max_items], 1):
            action = self._get_action_timeline(score.risk_priority)
            
            remediation_items.append({
                "priority": i,
                "cve_id": score.cve_id,
                "risk_level": score.risk_priority,
                "overall_score": score.overall_risk_score,
                "recommended_action": self._get_action_description(score),
                "timeline": action["timeline"],
                "effort_estimate": action["effort"],
            })
        
        return {
            "report_type": "Remediation Plan",
            "generated_at": datetime.now().isoformat(),
            "items": remediation_items,
            "summary": {
                "total_items": len(remediation_items),
                "critical_timeline": "24-48 hours",
                "high_timeline": "1 week",
                "medium_timeline": "30 days",
            }
        }
    
    def _generate_full_report(self, risk_scores: List[RiskScore]) -> Dict:
        """Generate comprehensive report"""
        return {
            "executive": self._generate_executive_summary(risk_scores),
            "technical": self._generate_technical_report(risk_scores),
            "remediation": self._generate_remediation_plan(risk_scores),
        }
    
    def _calculate_statistics(self, risk_scores: List[RiskScore]) -> Dict:
        """Calculate detailed statistics"""
        if not risk_scores:
            return {}
        
        total = len(risk_scores)
        
        return {
            "count": total,
            "cvss": {
                "min": min(r.cvss_score for r in risk_scores),
                "max": max(r.cvss_score for r in risk_scores),
                "avg": round(sum(r.cvss_score for r in risk_scores) / total, 1),
            },
            "epss": {
                "min": round(min(r.epss_probability for r in risk_scores), 1),
                "max": round(max(r.epss_probability for r in risk_scores), 1),
                "avg": round(sum(r.epss_probability for r in risk_scores) / total, 1),
            },
            "business_impact": {
                "avg": round(sum(r.business_impact_score for r in risk_scores) / total, 1),
            },
        }
    
    def _generate_executive_recommendations(
        self,
        critical: int,
        high: int,
        medium: int
    ) -> List[str]:
        """Generate executive recommendations"""
        recommendations = []
        
        if critical > 0:
            recommendations.append(
                f"IMMEDIATE ACTION: Address {critical} critical vulnerabilities within 24-48 hours"
            )
        
        if high > 0:
            recommendations.append(
                f"Urgent: Plan remediation for {high} high-risk vulnerabilities within 1 week"
            )
        
        if medium > 5:
            recommendations.append(
                f"Schedule {medium} medium-risk items for next maintenance window"
            )
        
        if critical == 0 and high == 0:
            recommendations.append(
                "Risk posture is manageable. Continue regular patching cycle."
            )
        
        return recommendations
    
    def _get_action_timeline(self, priority: str) -> Dict:
        """Get timeline and effort for priority"""
        timelines = {
            "Critical": {"timeline": "24-48 hours", "effort": "High"},
            "High": {"timeline": "1 week", "effort": "Medium-High"},
            "Medium": {"timeline": "30 days", "effort": "Medium"},
            "Low": {"timeline": "90 days", "effort": "Low"},
        }
        return timelines.get(priority, {"timeline": "As scheduled", "effort": "Low"})
    
    def _get_action_description(self, score: RiskScore) -> str:
        """Get specific action description"""
        if score.risk_priority == "Critical":
            return f"Emergency patch for {score.cve_id}. EPSS {score.epss_probability}% exploit probability."
        elif score.risk_priority == "High":
            return f"Prioritize patch for {score.cve_id}. Review exploitation risk."
        elif score.risk_priority == "Medium":
            return f"Schedule patch for {score.cve_id} in next maintenance."
        else:
            return f"Monitor {score.cve_id} and patch during routine updates."
    
    def export_json(self, report: Dict, filename: Optional[str] = None) -> str:
        """Export report to JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"risk_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        return filename
