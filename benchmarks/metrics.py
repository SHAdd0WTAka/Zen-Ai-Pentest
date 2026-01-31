"""
Zen-AI-Pentest Benchmark Metrics Module

Comprehensive metrics collection for security testing benchmarks.
Provides statistical analysis and performance tracking.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json
import math
import statistics
from collections import defaultdict


class SeverityLevel(Enum):
    """Severity levels for vulnerabilities."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingType(Enum):
    """Types of security findings."""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    SSRF = "ssrf"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    AUTH_BYPASS = "auth_bypass"
    INFO_DISCLOSURE = "info_disclosure"
    MISCONFIGURATION = "misconfiguration"
    OUTDATED_COMPONENT = "outdated_component"
    WEAK_CRYPTO = "weak_cryptography"


@dataclass
class FindingMetrics:
    """Metrics for individual findings."""
    finding_type: FindingType
    severity: SeverityLevel
    confidence: float  # 0.0 - 1.0
    exploitability: float  # 0.0 - 1.0
    detection_time_ms: int
    verification_time_ms: Optional[int] = None
    false_positive: Optional[bool] = None
    verified: bool = False
    exploited: bool = False
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None


@dataclass
class TokenUsage:
    """Track API token consumption."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    model: str = ""
    
    def __post_init__(self):
        self.total_tokens = self.prompt_tokens + self.completion_tokens


@dataclass
class PerformanceMetrics:
    """Performance-related metrics."""
    scan_start_time: datetime = field(default_factory=datetime.utcnow)
    scan_end_time: Optional[datetime] = None
    total_duration_ms: int = 0
    mean_time_to_detect_ms: float = 0.0
    detection_rate_per_minute: float = 0.0
    memory_peak_mb: float = 0.0
    cpu_usage_avg: float = 0.0
    network_requests: int = 0
    network_errors: int = 0
    
    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        if self.scan_end_time:
            return (self.scan_end_time - self.scan_start_time).total_seconds()
        return 0.0


@dataclass
class ClassificationMetrics:
    """
    Binary classification metrics for security findings.
    
    True Positives: Correctly identified vulnerabilities
    False Positives: Incorrectly flagged as vulnerabilities
    True Negatives: Correctly identified as safe
    False Negatives: Missed vulnerabilities
    """
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    
    @property
    def precision(self) -> float:
        """Precision = TP / (TP + FP)"""
        denominator = self.true_positives + self.false_positives
        if denominator == 0:
            return 0.0
        return self.true_positives / denominator
    
    @property
    def recall(self) -> float:
        """Recall = TP / (TP + FN)"""
        denominator = self.true_positives + self.false_negatives
        if denominator == 0:
            return 0.0
        return self.true_positives / denominator
    
    @property
    def specificity(self) -> float:
        """Specificity = TN / (TN + FP)"""
        denominator = self.true_negatives + self.false_positives
        if denominator == 0:
            return 0.0
        return self.true_negatives / denominator
    
    @property
    def f1_score(self) -> float:
        """F1-Score = 2 * (Precision * Recall) / (Precision + Recall)"""
        precision = self.precision
        recall = self.recall
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
    
    @property
    def f2_score(self) -> float:
        """F2-Score weights recall higher than precision."""
        precision = self.precision
        recall = self.recall
        if precision + recall == 0:
            return 0.0
        return 5 * (precision * recall) / ((4 * precision) + recall)
    
    @property
    def accuracy(self) -> float:
        """Accuracy = (TP + TN) / (TP + TN + FP + FN)"""
        total = self.true_positives + self.true_negatives + \
                self.false_positives + self.false_negatives
        if total == 0:
            return 0.0
        return (self.true_positives + self.true_negatives) / total
    
    @property
    def balanced_accuracy(self) -> float:
        """Balanced accuracy for imbalanced datasets."""
        sensitivity = self.recall
        specificity = self.specificity
        return (sensitivity + specificity) / 2
    
    @property
    def matthews_correlation(self) -> float:
        """Matthews Correlation Coefficient (-1 to +1)."""
        tp, tn, fp, fn = self.true_positives, self.true_negatives, \
                         self.false_positives, self.false_negatives
        
        denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
        if denominator == 0:
            return 0.0
        return ((tp * tn) - (fp * fn)) / denominator


@dataclass
class CoverageMetrics:
    """Coverage metrics for security testing."""
    total_endpoints: int = 0
    scanned_endpoints: int = 0
    total_parameters: int = 0
    tested_parameters: int = 0
    total_attack_vectors: int = 0
    tested_attack_vectors: int = 0
    owasp_categories_covered: List[str] = field(default_factory=list)
    
    @property
    def endpoint_coverage(self) -> float:
        """Percentage of endpoints scanned."""
        if self.total_endpoints == 0:
            return 0.0
        return (self.scanned_endpoints / self.total_endpoints) * 100
    
    @property
    def parameter_coverage(self) -> float:
        """Percentage of parameters tested."""
        if self.total_parameters == 0:
            return 0.0
        return (self.tested_parameters / self.total_parameters) * 100
    
    @property
    def attack_vector_coverage(self) -> float:
        """Percentage of attack vectors tested."""
        if self.total_attack_vectors == 0:
            return 0.0
        return (self.tested_attack_vectors / self.total_attack_vectors) * 100
    
    @property
    def owasp_coverage(self) -> float:
        """Percentage of OWASP categories covered."""
        # OWASP Top 10 categories
        owasp_top10 = [
            "A01:2021-Broken Access Control",
            "A02:2021-Cryptographic Failures",
            "A03:2021-Injection",
            "A04:2021-Insecure Design",
            "A05:2021-Security Misconfiguration",
            "A06:2021-Vulnerable and Outdated Components",
            "A07:2021-Identification and Authentication Failures",
            "A08:2021-Software and Data Integrity Failures",
            "A09:2021-Security Logging and Monitoring Failures",
            "A10:2021-Server-Side Request Forgery (SSRF)"
        ]
        if not owasp_top10:
            return 0.0
        return (len(self.owasp_categories_covered) / len(owasp_top10)) * 100


@dataclass
class ExploitMetrics:
    """Metrics for exploit attempts."""
    total_exploits_attempted: int = 0
    successful_exploits: int = 0
    failed_exploits: int = 0
    blocked_exploits: int = 0
    exploit_types: Dict[str, int] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Percentage of successful exploits."""
        if self.total_exploits_attempted == 0:
            return 0.0
        return (self.successful_exploits / self.total_exploits_attempted) * 100
    
    @property
    def safety_score(self) -> float:
        """Safety score based on controlled exploitation."""
        if self.total_exploits_attempted == 0:
            return 100.0
        # Higher is better - fewer unexpected successes
        return ((self.total_exploits_attempted - self.blocked_exploits) / 
                self.total_exploits_attempted) * 100


@dataclass
class BenchmarkMetrics:
    """Complete benchmark metrics container."""
    # Identification
    benchmark_id: str = ""
    scenario_name: str = ""
    tool_version: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Component metrics
    classification: ClassificationMetrics = field(default_factory=ClassificationMetrics)
    coverage: CoverageMetrics = field(default_factory=CoverageMetrics)
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    exploit: ExploitMetrics = field(default_factory=ExploitMetrics)
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    
    # Findings
    findings: List[FindingMetrics] = field(default_factory=list)
    
    # Raw data
    raw_output: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_aggregate_scores(self) -> Dict[str, float]:
        """Calculate aggregate benchmark scores."""
        return {
            "accuracy": self.classification.accuracy,
            "precision": self.classification.precision,
            "recall": self.classification.recall,
            "f1_score": self.classification.f1_score,
            "coverage": (
                self.coverage.endpoint_coverage +
                self.coverage.parameter_coverage +
                self.coverage.attack_vector_coverage
            ) / 3,
            "speed": self._calculate_speed_score(),
            "efficiency": self._calculate_efficiency_score(),
            "exploit_success": self.exploit.success_rate,
            "overall": self._calculate_overall_score()
        }
    
    def _calculate_speed_score(self) -> float:
        """Calculate speed score (0-100)."""
        duration = self.performance.duration_seconds
        if duration == 0:
            return 0.0
        # Faster is better, with diminishing returns
        return min(100.0, 1000.0 / max(duration, 10))
    
    def _calculate_efficiency_score(self) -> float:
        """Calculate efficiency score based on findings per token."""
        tokens = self.token_usage.total_tokens
        if tokens == 0:
            return 0.0
        findings = len(self.findings)
        return min(100.0, (findings / tokens) * 10000)
    
    def _calculate_overall_score(self) -> float:
        """Calculate overall benchmark score."""
        scores = self.calculate_aggregate_scores()
        weights = {
            "accuracy": 0.20,
            "precision": 0.15,
            "recall": 0.20,
            "f1_score": 0.15,
            "coverage": 0.15,
            "speed": 0.10,
            "efficiency": 0.05
        }
        
        overall = sum(scores.get(k, 0) * w for k, w in weights.items())
        return overall
    
    def get_severity_distribution(self) -> Dict[str, int]:
        """Get distribution of findings by severity."""
        distribution = defaultdict(int)
        for finding in self.findings:
            distribution[finding.severity.value] += 1
        return dict(distribution)
    
    def get_finding_type_distribution(self) -> Dict[str, int]:
        """Get distribution of findings by type."""
        distribution = defaultdict(int)
        for finding in self.findings:
            distribution[finding.finding_type.value] += 1
        return dict(distribution)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "benchmark_id": self.benchmark_id,
            "scenario_name": self.scenario_name,
            "tool_version": self.tool_version,
            "timestamp": self.timestamp.isoformat(),
            "classification": {
                "true_positives": self.classification.true_positives,
                "false_positives": self.classification.false_positives,
                "true_negatives": self.classification.true_negatives,
                "false_negatives": self.classification.false_negatives,
                "precision": self.classification.precision,
                "recall": self.classification.recall,
                "f1_score": self.classification.f1_score,
                "accuracy": self.classification.accuracy
            },
            "coverage": {
                "endpoint_coverage": self.coverage.endpoint_coverage,
                "parameter_coverage": self.coverage.parameter_coverage,
                "attack_vector_coverage": self.coverage.attack_vector_coverage,
                "owasp_coverage": self.coverage.owasp_coverage
            },
            "performance": {
                "duration_seconds": self.performance.duration_seconds,
                "mean_time_to_detect_ms": self.performance.mean_time_to_detect_ms,
                "memory_peak_mb": self.performance.memory_peak_mb,
                "cpu_usage_avg": self.performance.cpu_usage_avg
            },
            "exploit": {
                "success_rate": self.exploit.success_rate,
                "safety_score": self.exploit.safety_score,
                "total_attempts": self.exploit.total_exploits_attempted
            },
            "token_usage": {
                "prompt_tokens": self.token_usage.prompt_tokens,
                "completion_tokens": self.token_usage.completion_tokens,
                "total_tokens": self.token_usage.total_tokens,
                "cost_usd": self.token_usage.cost_usd
            },
            "findings_count": len(self.findings),
            "severity_distribution": self.get_severity_distribution(),
            "finding_type_distribution": self.get_finding_type_distribution(),
            "aggregate_scores": self.calculate_aggregate_scores()
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert metrics to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkMetrics":
        """Create metrics from dictionary."""
        metrics = cls(
            benchmark_id=data.get("benchmark_id", ""),
            scenario_name=data.get("scenario_name", ""),
            tool_version=data.get("tool_version", ""),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat()))
        )
        
        # Parse classification
        if "classification" in data:
            c = data["classification"]
            metrics.classification = ClassificationMetrics(
                true_positives=c.get("true_positives", 0),
                false_positives=c.get("false_positives", 0),
                true_negatives=c.get("true_negatives", 0),
                false_negatives=c.get("false_negatives", 0)
            )
        
        # Parse coverage
        if "coverage" in data:
            cov = data["coverage"]
            metrics.coverage = CoverageMetrics(
                endpoint_coverage=cov.get("endpoint_coverage", 0),
                parameter_coverage=cov.get("parameter_coverage", 0),
                attack_vector_coverage=cov.get("attack_vector_coverage", 0),
                owasp_coverage=cov.get("owasp_coverage", 0)
            )
        
        # Parse performance
        if "performance" in data:
            p = data["performance"]
            metrics.performance = PerformanceMetrics(
                total_duration_ms=p.get("duration_seconds", 0) * 1000,
                mean_time_to_detect_ms=p.get("mean_time_to_detect_ms", 0),
                memory_peak_mb=p.get("memory_peak_mb", 0),
                cpu_usage_avg=p.get("cpu_usage_avg", 0)
            )
        
        return metrics


class MetricsAggregator:
    """Aggregate metrics across multiple benchmark runs."""
    
    def __init__(self):
        self.metrics: List[BenchmarkMetrics] = []
    
    def add(self, metrics: BenchmarkMetrics) -> None:
        """Add metrics to aggregation."""
        self.metrics.append(metrics)
    
    def get_average_scores(self) -> Dict[str, float]:
        """Get average scores across all runs."""
        if not self.metrics:
            return {}
        
        all_scores = [m.calculate_aggregate_scores() for m in self.metrics]
        keys = all_scores[0].keys()
        
        return {
            key: statistics.mean(s.get(key, 0) for s in all_scores)
            for key in keys
        }
    
    def get_statistics(self) -> Dict[str, Dict[str, float]]:
        """Get statistical analysis of all metrics."""
        if not self.metrics:
            return {}
        
        scores = [m.calculate_aggregate_scores() for m in self.metrics]
        result = {}
        
        for key in scores[0].keys():
            values = [s[key] for s in scores]
            result[key] = {
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
                "min": min(values),
                "max": max(values)
            }
        
        return result
    
    def get_trend(self, metric_key: str = "overall") -> str:
        """Determine trend direction for a metric."""
        if len(self.metrics) < 2:
            return "insufficient_data"
        
        scores = [m.calculate_aggregate_scores().get(metric_key, 0) 
                  for m in self.metrics]
        
        # Simple linear regression
        n = len(scores)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(scores)
        
        numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        if slope > 0.5:
            return "improving"
        elif slope < -0.5:
            return "degrading"
        return "stable"


# Convenience functions
def calculate_confidence_interval(
    values: List[float], 
    confidence: float = 0.95
) -> tuple:
    """Calculate confidence interval for a list of values."""
    if len(values) < 2:
        return (0.0, 0.0)
    
    mean = statistics.mean(values)
    stdev = statistics.stdev(values)
    
    # For 95% confidence, z-score is approximately 1.96
    z_score = 1.96 if confidence == 0.95 else 2.576  # 99%: 2.576
    
    margin = z_score * (stdev / math.sqrt(len(values)))
    return (mean - margin, mean + margin)


def compare_metrics(
    baseline: BenchmarkMetrics, 
    current: BenchmarkMetrics
) -> Dict[str, Any]:
    """Compare two benchmark runs and return differences."""
    baseline_scores = baseline.calculate_aggregate_scores()
    current_scores = current.calculate_aggregate_scores()
    
    comparison = {}
    for key in baseline_scores.keys():
        old_val = baseline_scores[key]
        new_val = current_scores.get(key, 0)
        
        if old_val != 0:
            pct_change = ((new_val - old_val) / old_val) * 100
        else:
            pct_change = 100.0 if new_val > 0 else 0.0
        
        comparison[key] = {
            "baseline": old_val,
            "current": new_val,
            "absolute_change": new_val - old_val,
            "percent_change": pct_change,
            "improved": new_val > old_val
        }
    
    return comparison
