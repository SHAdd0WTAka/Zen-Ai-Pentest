"""False Positive Reduction Module

Uses ML-based heuristics and rule-based filters to reduce false positives.
Addresses Issue #14
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re


class ConfidenceLevel(Enum):
    HIGH = "high"      # > 90% confidence
    MEDIUM = "medium"  # 70-90% confidence
    LOW = "low"        # 50-70% confidence
    UNKNOWN = "unknown"  # < 50% confidence


@dataclass
class Finding:
    """Security finding structure"""
    title: str
    description: str
    severity: str
    cvss_score: float
    evidence: List[str]
    tool: str
    confidence: float = 0.5


class FalsePositiveFilter:
    """Filter false positives from security findings"""

    name = "false_positive_filter"
    version = "1.0.0"

    # Known false positive patterns
    FALSE_POSITIVE_PATTERNS = [
        r"(?i)self-signed certificate",  # Often intentional in dev
        r"(?i)directory listing.*empty",
        r"(?i)missing.*header.*not applicable",
        r"(?i)information disclosure.*version.*normal",
        r"(?i)cookie.*without.*secure.*localhost",
    ]

    # Keywords that indicate likely false positive
    FP_KEYWORDS = [
        "test", "localhost", "127.0.0.1", "example.com",
        "documentation", "intentional", "expected behavior"
    ]

    def __init__(self):
        self.rules_applied = 0
        self.ml_model_loaded = False

    def apply_rule_based_filter(self, finding: Finding) -> Tuple[bool, str]:
        """
        Apply rule-based filtering
        Returns: (is_false_positive, reason)
        """
        # Check against known FP patterns
        combined_text = f"{finding.title} {finding.description}"
        
        for pattern in self.FALSE_POSITIVE_PATTERNS:
            if re.search(pattern, combined_text):
                return True, f"Matched FP pattern: {pattern}"

        # Check for FP keywords
        for keyword in self.FP_KEYWORDS:
            if keyword.lower() in combined_text.lower():
                return True, f"Contains FP keyword: {keyword}"

        # Check confidence score
        if finding.confidence < 0.3:
            return True, "Confidence below threshold (0.3)"

        return False, ""

    def apply_ml_filter(self, finding: Finding) -> float:
        """
        ML-based false positive probability
        Returns: probability (0.0 - 1.0) that this is a false positive
        """
        # In production, this would use a trained model
        # For now, use heuristics as proxy
        
        fp_score = 0.0
        
        # Low evidence count = higher FP probability
        if len(finding.evidence) == 0:
            fp_score += 0.3
        elif len(finding.evidence) < 2:
            fp_score += 0.1
        
        # Generic titles = higher FP probability
        generic_patterns = [r"(?i)vulnerability", r"(?i)issue", r"(?i)problem"]
        for pattern in generic_patterns:
            if re.search(pattern, finding.title) and len(finding.title) < 30:
                fp_score += 0.15
        
        # Low severity + low confidence = likely FP
        if finding.severity == "low" and finding.confidence < 0.5:
            fp_score += 0.2
        
        return min(fp_score, 1.0)

    def filter_findings(
        self,
        findings: List[Finding],
        fp_threshold: float = 0.7
    ) -> Dict[str, List[Finding]]:
        """
        Filter findings and separate true positives from false positives
        """
        true_positives = []
        false_positives = []
        
        for finding in findings:
            # Rule-based filter
            is_fp_rule, reason = self.apply_rule_based_filter(finding)
            
            # ML filter
            fp_probability = self.apply_ml_filter(finding)
            
            # Combine filters
            if is_fp_rule or fp_probability > fp_threshold:
                false_positives.append({
                    'finding': finding,
                    'fp_probability': fp_probability,
                    'reason': reason if is_fp_rule else f"ML score: {fp_probability:.2f}"
                })
            else:
                true_positives.append(finding)
        
        return {
            'true_positives': true_positives,
            'false_positives': false_positives,
            'reduction_rate': len(false_positives) / len(findings) if findings else 0
        }

    def get_info(self) -> Dict:
        """Get module info"""
        return {
            'name': self.name,
            'version': self.version,
            'description': 'ML-based false positive reduction',
            'rules_count': len(self.FALSE_POSITIVE_PATTERNS),
            'threshold': 0.7
        }
