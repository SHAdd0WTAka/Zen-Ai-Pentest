"""
Zen-AI-Pentest Benchmark Comparison Module

Compare Zen-AI-Pentest performance against other security tools.
Supports both AI-based and traditional security scanners.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import json
import statistics
from abc import ABC, abstractmethod


class ToolCategory(Enum):
    """Categories of security tools."""
    AI_PENTEST = "ai_pentest"
    TRADITIONAL_SCANNER = "traditional_scanner"
    STATIC_ANALYZER = "static_analyzer"
    DYNAMIC_ANALYZER = "dynamic_analyzer"
    NETWORK_SCANNER = "network_scanner"
    WEB_SCANNER = "web_scanner"


@dataclass
class ToolCapabilities:
    """Capabilities of a security testing tool."""
    # Core capabilities
    supports_web_scanning: bool = False
    supports_network_scanning: bool = False
    supports_api_scanning: bool = False
    supports_mobile_scanning: bool = False
    supports_cloud_scanning: bool = False
    supports_container_scanning: bool = False
    
    # AI/ML features
    uses_ai: bool = False
    supports_autonomous_testing: bool = False
    supports_contextual_analysis: bool = False
    supports_attack_chain_building: bool = False
    
    # Exploitation
    supports_exploitation: bool = False
    supports_post_exploitation: bool = False
    supports_lateral_movement: bool = False
    
    # Reporting
    supports_pdf_reports: bool = False
    supports_json_output: bool = False
    supports_xml_output: bool = False
    supports_sarif: bool = False
    supports_cicd_integration: bool = False
    
    # Integration
    has_api: bool = False
    has_webhook_support: bool = False
    has_slack_integration: bool = False
    has_jira_integration: bool = False


@dataclass
class ToolMetadata:
    """Metadata about a security tool."""
    name: str
    version: str
    vendor: str
    category: ToolCategory
    license_type: str  # "open_source", "commercial", "freemium"
    pricing_model: str = ""
    website: str = ""
    documentation_url: str = ""
    github_url: Optional[str] = None
    
    # Capabilities
    capabilities: ToolCapabilities = field(default_factory=ToolCapabilities)
    
    # Performance characteristics
    avg_scan_time_web: Optional[int] = None  # minutes
    avg_scan_time_network: Optional[int] = None
    max_concurrent_scans: Optional[int] = None
    requires_internet: bool = True


@dataclass
class ToolBenchmarkResult:
    """Benchmark result for a specific tool."""
    tool_metadata: ToolMetadata
    scenario_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Core metrics
    scan_duration_seconds: float = 0.0
    vulnerabilities_found: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    
    # Coverage metrics
    endpoints_scanned: int = 0
    total_endpoints: int = 0
    parameters_tested: int = 0
    total_parameters: int = 0
    
    # Quality metrics
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    accuracy: float = 0.0
    
    # Cost metrics
    total_cost_usd: Optional[float] = None
    tokens_used: Optional[int] = None
    
    # Detailed results
    findings: List[Dict[str, Any]] = field(default_factory=list)
    raw_output: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class CompetitorTool(ABC):
    """Abstract base class for competitor tools."""
    
    def __init__(self, metadata: ToolMetadata):
        self.metadata = metadata
    
    @abstractmethod
    async def run_scan(
        self, 
        target: str, 
        scenario_config: Dict[str, Any]
    ) -> ToolBenchmarkResult:
        """Run a scan and return results."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the tool is available/installed."""
        pass
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return self.metadata


# =============================================================================
# PENTESTGPT COMPETITOR
# =============================================================================

PENTESTGPT_METADATA = ToolMetadata(
    name="PentestGPT",
    version="2.0",
    vendor="Gelei Deng et al.",
    category=ToolCategory.AI_PENTEST,
    license_type="open_source",
    website="https://github.com/GeleiDeng/PentestGPT",
    github_url="https://github.com/GeleiDeng/PentestGPT",
    capabilities=ToolCapabilities(
        supports_web_scanning=True,
        supports_network_scanning=True,
        uses_ai=True,
        supports_autonomous_testing=True,
        supports_contextual_analysis=True,
        supports_attack_chain_building=True,
        supports_exploitation=True,
        supports_json_output=True
    )
)


class PentestGPTCompetitor(CompetitorTool):
    """PentestGPT competitor wrapper."""
    
    def __init__(self):
        super().__init__(PENTESTGPT_METADATA)
    
    def is_available(self) -> bool:
        """Check if PentestGPT is available."""
        # In real implementation, check for pentestgpt command
        return False  # Placeholder
    
    async def run_scan(
        self, 
        target: str, 
        scenario_config: Dict[str, Any]
    ) -> ToolBenchmarkResult:
        """Run PentestGPT scan."""
        # Placeholder implementation
        return ToolBenchmarkResult(
            tool_metadata=self.metadata,
            scenario_id=scenario_config.get("scenario_id", "unknown")
        )


# =============================================================================
# AUTOPENTEST-DRL COMPETITOR
# =============================================================================

AUTOPENTEST_METADATA = ToolMetadata(
    name="AutoPentest-DRL",
    version="1.0",
    vendor="Li et al.",
    category=ToolCategory.AI_PENTEST,
    license_type="open_source",
    website="https://github.com/crond-jaist/AutoPentest-DRL",
    github_url="https://github.com/crond-jaist/AutoPentest-DRL",
    capabilities=ToolCapabilities(
        supports_network_scanning=True,
        uses_ai=True,
        supports_autonomous_testing=True,
        supports_exploitation=True,
        supports_post_exploitation=True,
        supports_json_output=True
    )
)


class AutoPentestDRLCompetitor(CompetitorTool):
    """AutoPentest-DRL competitor wrapper."""
    
    def __init__(self):
        super().__init__(AUTOPENTEST_METADATA)
    
    def is_available(self) -> bool:
        """Check if AutoPentest-DRL is available."""
        return False  # Placeholder
    
    async def run_scan(
        self, 
        target: str, 
        scenario_config: Dict[str, Any]
    ) -> ToolBenchmarkResult:
        """Run AutoPentest-DRL scan."""
        return ToolBenchmarkResult(
            tool_metadata=self.metadata,
            scenario_id=scenario_config.get("scenario_id", "unknown")
        )


# =============================================================================
# TRADITIONAL SCANNERS
# =============================================================================

NESSUS_METADATA = ToolMetadata(
    name="Nessus",
    version="10.7",
    vendor="Tenable",
    category=ToolCategory.TRADITIONAL_SCANNER,
    license_type="commercial",
    pricing_model="subscription",
    website="https://www.tenable.com/products/nessus",
    capabilities=ToolCapabilities(
        supports_web_scanning=True,
        supports_network_scanning=True,
        supports_api_scanning=True,
        supports_cloud_scanning=True,
        supports_exploitation=True,
        supports_pdf_reports=True,
        supports_json_output=True,
        supports_xml_output=True,
        has_api=True,
        has_jira_integration=True
    ),
    avg_scan_time_network=30,
    max_concurrent_scans=10
)

OPENVAS_METADATA = ToolMetadata(
    name="OpenVAS",
    version="22.4",
    vendor="Greenbone",
    category=ToolCategory.TRADITIONAL_SCANNER,
    license_type="open_source",
    website="https://www.greenbone.net/openvas",
    github_url="https://github.com/greenbone/openvas",
    capabilities=ToolCapabilities(
        supports_web_scanning=True,
        supports_network_scanning=True,
        supports_api_scanning=True,
        supports_pdf_reports=True,
        supports_xml_output=True,
        supports_sarif=True,
        has_api=True
    ),
    avg_scan_time_network=45,
    max_concurrent_scans=5
)

BURP_SUITE_METADATA = ToolMetadata(
    name="Burp Suite Professional",
    version="2024.1",
    vendor="PortSwigger",
    category=ToolCategory.WEB_SCANNER,
    license_type="commercial",
    pricing_model="perpetual_license",
    website="https://portswigger.net/burp",
    capabilities=ToolCapabilities(
        supports_web_scanning=True,
        supports_api_scanning=True,
        supports_mobile_scanning=True,
        supports_autonomous_testing=True,  # With Burp Scanner
        supports_exploitation=True,
        supports_pdf_reports=True,
        supports_xml_output=True,
        supports_sarif=True,
        has_api=True,
        has_jira_integration=True
    ),
    avg_scan_time_web=20,
    max_concurrent_scans=5
)

OWASP_ZAP_METADATA = ToolMetadata(
    name="OWASP ZAP",
    version="2.14",
    vendor="OWASP",
    category=ToolCategory.WEB_SCANNER,
    license_type="open_source",
    website="https://www.zaproxy.org",
    github_url="https://github.com/zaproxy/zaproxy",
    capabilities=ToolCapabilities(
        supports_web_scanning=True,
        supports_api_scanning=True,
        supports_autonomous_testing=True,
        supports_exploitation=True,
        supports_pdf_reports=True,
        supports_json_output=True,
        supports_xml_output=True,
        supports_sarif=True,
        supports_cicd_integration=True,
        has_api=True,
        has_jira_integration=True
    ),
    avg_scan_time_web=25,
    max_concurrent_scans=3
)

NIKTO_METADATA = ToolMetadata(
    name="Nikto",
    version="2.5",
    vendor="CIRT",
    category=ToolCategory.WEB_SCANNER,
    license_type="open_source",
    website="https://cirt.net/Nikto2",
    github_url="https://github.com/sullo/nikto",
    capabilities=ToolCapabilities(
        supports_web_scanning=True,
        supports_json_output=True,
        supports_xml_output=True,
        supports_cicd_integration=True
    ),
    avg_scan_time_web=15,
    requires_internet=False
)

NUCLEI_METADATA = ToolMetadata(
    name="Nuclei",
    version="3.1",
    vendor="ProjectDiscovery",
    category=ToolCategory.WEB_SCANNER,
    license_type="open_source",
    website="https://nuclei.projectdiscovery.io",
    github_url="https://github.com/projectdiscovery/nuclei",
    capabilities=ToolCapabilities(
        supports_web_scanning=True,
        supports_network_scanning=True,
        supports_api_scanning=True,
        supports_cloud_scanning=True,
        supports_exploitation=True,
        supports_json_output=True,
        supports_sarif=True,
        supports_cicd_integration=True,
        has_api=True
    ),
    avg_scan_time_web=5,
    max_concurrent_scans=50,
    requires_internet=False
)

SQLMAP_METADATA = ToolMetadata(
    name="SQLMap",
    version="1.7",
    vendor="SQLMap Project",
    category=ToolCategory.WEB_SCANNER,
    license_type="open_source",
    website="https://sqlmap.org",
    github_url="https://github.com/sqlmapproject/sqlmap",
    capabilities=ToolCapabilities(
        supports_web_scanning=True,
        supports_exploitation=True,
        supports_json_output=True,
        supports_xml_output=True,
        supports_cicd_integration=True
    ),
    avg_scan_time_web=30,
    requires_internet=False
)


# =============================================================================
# COMPARISON FRAMEWORK
# =============================================================================

@dataclass
class ComparisonResult:
    """Result of comparing multiple tools."""
    
    # Tool results
    zen_result: ToolBenchmarkResult
    competitor_results: List[ToolBenchmarkResult]
    
    # Scenario info
    scenario_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Comparison metrics
    metric_improvements: Dict[str, Dict[str, float]] = field(default_factory=dict)
    rankings: Dict[str, List[str]] = field(default_factory=dict)
    
    # Summary
    winner: Optional[str] = None
    statistical_significance: Dict[str, bool] = field(default_factory=dict)
    
    def calculate_improvements(self) -> None:
        """Calculate improvement percentages over competitors."""
        metrics_to_compare = [
            "precision", "recall", "f1_score", "accuracy",
            "vulnerabilities_found", "scan_duration_seconds"
        ]
        
        for metric in metrics_to_compare:
            zen_value = getattr(self.zen_result, metric, 0)
            
            for comp_result in self.competitor_results:
                comp_value = getattr(comp_result, metric, 0)
                
                if metric == "scan_duration_seconds":
                    # Lower is better for duration
                    if comp_value > 0:
                        improvement = ((comp_value - zen_value) / comp_value) * 100
                    else:
                        improvement = 0
                else:
                    # Higher is better for other metrics
                    if comp_value > 0:
                        improvement = ((zen_value - comp_value) / comp_value) * 100
                    else:
                        improvement = 100 if zen_value > 0 else 0
                
                tool_name = comp_result.tool_metadata.name
                if metric not in self.metric_improvements:
                    self.metric_improvements[metric] = {}
                self.metric_improvements[metric][tool_name] = improvement
    
    def calculate_rankings(self) -> None:
        """Calculate rankings for each metric."""
        all_results = [self.zen_result] + self.competitor_results
        
        metrics_to_rank = [
            ("precision", True),  # (metric_name, higher_is_better)
            ("recall", True),
            ("f1_score", True),
            ("accuracy", True),
            ("scan_duration_seconds", False),
        ]
        
        for metric, higher_is_better in metrics_to_rank:
            sorted_results = sorted(
                all_results,
                key=lambda r: getattr(r, metric, 0),
                reverse=higher_is_better
            )
            self.rankings[metric] = [
                r.tool_metadata.name for r in sorted_results
            ]
    
    def determine_winner(self) -> None:
        """Determine overall winner based on F1 score."""
        all_results = [self.zen_result] + self.competitor_results
        winner = max(all_results, key=lambda r: r.f1_score)
        self.winner = winner.tool_metadata.name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert comparison result to dictionary."""
        return {
            "scenario_id": self.scenario_id,
            "timestamp": self.timestamp.isoformat(),
            "zen_result": {
                "tool": self.zen_result.tool_metadata.name,
                "precision": self.zen_result.precision,
                "recall": self.zen_result.recall,
                "f1_score": self.zen_result.f1_score,
                "accuracy": self.zen_result.accuracy,
                "duration_seconds": self.zen_result.scan_duration_seconds,
                "vulnerabilities_found": self.zen_result.vulnerabilities_found
            },
            "competitor_results": [
                {
                    "tool": r.tool_metadata.name,
                    "precision": r.precision,
                    "recall": r.recall,
                    "f1_score": r.f1_score,
                    "accuracy": r.accuracy,
                    "duration_seconds": r.scan_duration_seconds,
                    "vulnerabilities_found": r.vulnerabilities_found
                }
                for r in self.competitor_results
            ],
            "improvements": self.metric_improvements,
            "rankings": self.rankings,
            "winner": self.winner
        }
    
    def generate_report_markdown(self) -> str:
        """Generate a markdown comparison report."""
        lines = [
            f"# Benchmark Comparison Report",
            f"**Scenario:** {self.scenario_id}",
            f"**Date:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Results Summary",
            "",
            "| Tool | Precision | Recall | F1-Score | Accuracy | Duration | Vulns Found |",
            "|------|-----------|--------|----------|----------|----------|-------------|"
        ]
        
        # Add Zen result
        z = self.zen_result
        lines.append(
            f"| **{z.tool_metadata.name}** | "
            f"{z.precision:.3f} | {z.recall:.3f} | {z.f1_score:.3f} | "
            f"{z.accuracy:.3f} | {z.scan_duration_seconds:.1f}s | {z.vulnerabilities_found} |"
        )
        
        # Add competitors
        for r in self.competitor_results:
            lines.append(
                f"| {r.tool_metadata.name} | "
                f"{r.precision:.3f} | {r.recall:.3f} | {r.f1_score:.3f} | "
                f"{r.accuracy:.3f} | {r.scan_duration_seconds:.1f}s | {r.vulnerabilities_found} |"
            )
        
        lines.extend([
            "",
            "## Improvements vs Competitors",
            ""
        ])
        
        for metric, improvements in self.metric_improvements.items():
            lines.append(f"### {metric.replace('_', ' ').title()}")
            lines.append("")
            for tool, improvement in improvements.items():
                emoji = "✅" if improvement > 0 else "❌"
                lines.append(f"- {emoji} vs {tool}: {improvement:+.1f}%")
            lines.append("")
        
        lines.extend([
            "## Rankings",
            ""
        ])
        
        for metric, ranking in self.rankings.items():
            lines.append(f"### {metric.replace('_', ' ').title()}")
            for i, tool in enumerate(ranking, 1):
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
                lines.append(f"{medal} {tool}")
            lines.append("")
        
        if self.winner:
            lines.extend([
                "## Winner",
                f"",
                f"🏆 **{self.winner}** achieved the best overall performance.",
                ""
            ])
        
        return "\n".join(lines)


class ComparisonFramework:
    """Framework for comparing Zen-AI-Pentest with competitors."""
    
    def __init__(self):
        self.competitors: Dict[str, CompetitorTool] = {}
        self.register_default_competitors()
    
    def register_default_competitors(self) -> None:
        """Register default competitor tools."""
        self.register_competitor(PentestGPTCompetitor())
        self.register_competitor(AutoPentestDRLCompetitor())
    
    def register_competitor(self, tool: CompetitorTool) -> None:
        """Register a competitor tool."""
        self.competitors[tool.metadata.name] = tool
    
    def get_available_competitors(self) -> List[str]:
        """Get list of available competitor tools."""
        return [
            name for name, tool in self.competitors.items()
            if tool.is_available()
        ]
    
    async def run_comparison(
        self,
        zen_result: ToolBenchmarkResult,
        scenario_config: Dict[str, Any],
        competitors: Optional[List[str]] = None
    ) -> ComparisonResult:
        """Run comparison between Zen-AI-Pentest and competitors."""
        
        # Determine which competitors to test
        if competitors is None:
            competitors = self.get_available_competitors()
        
        competitor_results = []
        target = scenario_config.get("target_url") or scenario_config.get("target_host")
        
        for comp_name in competitors:
            if comp_name in self.competitors:
                tool = self.competitors[comp_name]
                if tool.is_available():
                    result = await tool.run_scan(target, scenario_config)
                    competitor_results.append(result)
        
        # Create comparison result
        comparison = ComparisonResult(
            zen_result=zen_result,
            competitor_results=competitor_results,
            scenario_id=scenario_config.get("scenario_id", "unknown")
        )
        
        # Calculate comparisons
        comparison.calculate_improvements()
        comparison.calculate_rankings()
        comparison.determine_winner()
        
        return comparison
    
    def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """Get metadata for a tool by name."""
        # Built-in tools
        metadata_map = {
            "Zen-AI-Pentest": None,  # Special case
            "PentestGPT": PENTESTGPT_METADATA,
            "AutoPentest-DRL": AUTOPENTEST_METADATA,
            "Nessus": NESSUS_METADATA,
            "OpenVAS": OPENVAS_METADATA,
            "Burp Suite": BURP_SUITE_METADATA,
            "OWASP ZAP": OWASP_ZAP_METADATA,
            "Nikto": NIKTO_METADATA,
            "Nuclei": NUCLEI_METADATA,
            "SQLMap": SQLMAP_METADATA,
        }
        return metadata_map.get(tool_name)
    
    def compare_capabilities(
        self, 
        tools: List[str]
    ) -> Dict[str, Any]:
        """Compare capabilities of multiple tools."""
        result = {
            "tools": [],
            "capability_matrix": {},
            "unique_capabilities": {},
            "common_capabilities": []
        }
        
        all_capabilities = set()
        tool_capabilities = {}
        
        for tool_name in tools:
            metadata = self.get_tool_metadata(tool_name)
            if metadata:
                caps = metadata.capabilities
                caps_dict = {
                    k: v for k, v in vars(caps).items()
                    if not k.startswith('_')
                }
                tool_capabilities[tool_name] = caps_dict
                result["tools"].append({
                    "name": tool_name,
                    "category": metadata.category.value,
                    "license": metadata.license_type,
                    "capabilities": caps_dict
                })
                all_capabilities.update(caps_dict.keys())
        
        # Build capability matrix
        for cap in all_capabilities:
            result["capability_matrix"][cap] = {
                tool: tool_capabilities.get(tool, {}).get(cap, False)
                for tool in tools
            }
        
        return result


def calculate_cohen_d(group1: List[float], group2: List[float]) -> float:
    """
    Calculate Cohen's d effect size.
    
    Small effect: ~0.2
    Medium effect: ~0.5
    Large effect: ~0.8+
    """
    if len(group1) < 2 or len(group2) < 2:
        return 0.0
    
    mean1 = statistics.mean(group1)
    mean2 = statistics.mean(group2)
    
    std1 = statistics.stdev(group1)
    std2 = statistics.stdev(group2)
    
    # Pooled standard deviation
    n1, n2 = len(group1), len(group2)
    pooled_std = math.sqrt(
        ((n1 - 1) * std1 ** 2 + (n2 - 1) * std2 ** 2) / (n1 + n2 - 2)
    )
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std


# Import math here for calculate_cohen_d
import math
