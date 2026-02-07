#!/usr/bin/env python3
"""
Zen AI Hybrid Orchestrator
Multi-LLM Routing System with Penetration Testing Capabilities
Enhanced with Autonomous Agent Loop, Risk Engine, and Exploit Validation

Author: SHAdd0WTAka
"""

import asyncio
import logging
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp

# Apply Windows/asyncio fixes before any other imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.async_fixes import apply_windows_async_fixes, safe_close_session  # noqa: E402

apply_windows_async_fixes()

# Import new components (with graceful fallback)
try:
    from autonomous import AutonomousAgentLoop, AgentState, AgentMemory
    from autonomous import ExploitValidator, ExploitValidatorPool, ExploitType
    from autonomous import ScopeConfig, SandboxConfig, ExploitResult

    AUTONOMOUS_AVAILABLE = True
except ImportError as e:
    AUTONOMOUS_AVAILABLE = False
    logging.warning(f"Autonomous components not available: {e}")
    AutonomousAgentLoop = None
    AgentState = None
    AgentMemory = None
    ExploitValidator = None
    ExploitValidatorPool = None
    ExploitType = None
    ScopeConfig = None
    SandboxConfig = None
    ExploitResult = None

try:
    from risk_engine import FalsePositiveEngine, BusinessImpactCalculator
    from risk_engine import Finding, FindingStatus, ValidationResult
    from risk_engine import ConfidenceLevel, ComplianceType, DataClassification

    RISK_ENGINE_AVAILABLE = True
except ImportError as e:
    RISK_ENGINE_AVAILABLE = False
    logging.warning(f"Risk engine components not available: {e}")
    FalsePositiveEngine = None
    BusinessImpactCalculator = None
    Finding = None
    FindingStatus = None
    ValidationResult = None
    ConfidenceLevel = None
    ComplianceType = None
    DataClassification = None

try:
    from integrations import load_integrations_from_config

    INTEGRATIONS_AVAILABLE = True
except ImportError:
    INTEGRATIONS_AVAILABLE = False
    load_integrations_from_config = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/zen_ai.log"), logging.StreamHandler()],
)
logger = logging.getLogger("ZenAI")


class QualityLevel(Enum):
    """Quality levels for LLM responses"""

    LOW = "low"  # Fast, free (DDG)
    MEDIUM = "medium"  # OpenRouter Free Tier
    HIGH = "high"  # Direct API (ChatGPT/Claude Web)


@dataclass
class LLMResponse:
    """Standardized LLM response"""

    content: str
    source: str
    latency: float
    quality: QualityLevel
    metadata: Dict = None


class BaseBackend(ABC):
    """Abstract base class for LLM backends"""

    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await safe_close_session(self.session)

    @abstractmethod
    async def chat(self, prompt: str, context: str = "") -> Optional[str]:
        """Send prompt to backend and return response"""
        pass

    async def health_check(self) -> bool:
        """Check if backend is available"""
        return True


class ZenOrchestrator:
    """
    Central orchestrator for multi-LLM management
    Routes requests to appropriate backends based on quality requirements

    Enhanced with:
    - Autonomous Agent Loop integration
    - False Positive Engine
    - Exploit Validation
    - CI/CD Integrations
    """

    def __init__(self):
        self.backends: List[BaseBackend] = []
        self.results_cache = {}
        self.request_count = 0

        # Initialize new components
        self._autonomous_loop: Optional[Any] = None
        self._fp_engine: Optional[Any] = None
        self._exploit_validator: Optional[Any] = None
        self._business_impact: Optional[Any] = None
        self._integrations: Dict[str, Any] = {}

        # Initialize if available
        self._initialize_components()

    def _initialize_components(self):
        """Initialize optional components."""
        if AUTONOMOUS_AVAILABLE:
            try:
                self._autonomous_loop = AutonomousAgentLoop(max_iterations=50)
                logger.info("AutonomousAgentLoop initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize AutonomousAgentLoop: {e}")

        if RISK_ENGINE_AVAILABLE:
            try:
                self._fp_engine = FalsePositiveEngine()
                self._business_impact = BusinessImpactCalculator()
                logger.info("Risk engine components initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Risk Engine: {e}")

        if AUTONOMOUS_AVAILABLE and ExploitValidator:
            try:
                self._exploit_validator = ExploitValidator()
                logger.info("ExploitValidator initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize ExploitValidator: {e}")

        if INTEGRATIONS_AVAILABLE and load_integrations_from_config:
            try:
                self._integrations = load_integrations_from_config()
                logger.info(f"Loaded {len(self._integrations)} integrations")
            except Exception as e:
                logger.warning(f"Failed to load integrations: {e}")

    def add_backend(self, backend: BaseBackend):
        """Register a new backend"""
        self.backends.append(backend)
        # Sort by priority (lowest first = faster/free)
        self.backends.sort(key=lambda x: x.priority)
        logger.info(f"[Zen] Backend '{backend.name}' registered with priority {backend.priority}")

    async def process(self, prompt: str, required_quality: QualityLevel = QualityLevel.MEDIUM) -> LLMResponse:
        """
        Process a prompt through available backends
        Tries backends in priority order with automatic fallback
        """
        self.request_count += 1
        start_time = asyncio.get_event_loop().time()

        logger.info(f"[Zen] Request #{self.request_count} | Quality: {required_quality.value}")

        # Filter candidates based on quality requirement
        if required_quality == QualityLevel.LOW:
            candidates = [b for b in self.backends if b.priority == 1]
        elif required_quality == QualityLevel.MEDIUM:
            candidates = [b for b in self.backends if b.priority <= 2]
        else:
            candidates = self.backends

        # Try sequentially (faster than parallel for different tiers)
        for backend in candidates:
            logger.info(f"[Zen] Trying {backend.name}...")

            try:
                result = await backend.chat(prompt)

                if result and len(result) > 10:
                    latency = asyncio.get_event_loop().time() - start_time

                    quality = (
                        QualityLevel.HIGH
                        if backend.priority == 3
                        else (QualityLevel.MEDIUM if backend.priority == 2 else QualityLevel.LOW)
                    )

                    logger.info(f"[Zen] Success from {backend.name} in {latency:.2f}s")

                    return LLMResponse(
                        content=result,
                        source=backend.name,
                        latency=latency,
                        quality=quality,
                        metadata={"model": getattr(backend, "current_model", "unknown")},
                    )

            except Exception as e:
                logger.error(f"[Zen] Backend {backend.name} failed: {e}")
                continue

        # Complete failure
        logger.error("[Zen] All backends failed")
        return LLMResponse(
            content="All backends failed. Check logs.",
            source="None",
            latency=0,
            quality=QualityLevel.LOW,
        )

    async def parallel_consensus(self, prompt: str) -> Dict[str, Any]:
        """
        For critical tasks: Query multiple backends simultaneously
        Returns consensus and alternative responses
        """
        logger.info("[Zen] Parallel consensus mode activated")

        tasks = []
        for backend in self.backends[:2]:  # Top 2 (DDG + OpenRouter)
            tasks.append(backend.chat(prompt))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid = []
        for backend, result in zip(self.backends[:2], results):
            if isinstance(result, str) and len(result) > 50:
                valid.append({"source": backend.name, "content": result})

        return {
            "responses": valid,
            "consensus": valid[0] if valid else None,
            "alternative": valid[1] if len(valid) > 1 else None,
        }

    # ==================== NEW METHODS ====================

    async def run_autonomous_scan(self, target: str, goal: str, scope: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run an autonomous scan using the AutonomousAgentLoop.

        Args:
            target: Target URL/IP/Domain
            goal: Scan goal (e.g., "Find vulnerabilities", "Enumerate subdomains")
            scope: Optional scope configuration

        Returns:
            Scan results with findings and execution details
        """
        if not AUTONOMOUS_AVAILABLE or not self._autonomous_loop:
            return {"success": False, "error": "Autonomous Agent Loop not available", "findings": []}

        logger.info(f"[Zen] Starting autonomous scan on {target}")

        try:
            result = await self._autonomous_loop.run(goal=goal, target=target, scope=scope or {})

            logger.info(f"[Zen] Autonomous scan completed: {result.get('state', 'unknown')}")

            # Validate findings if risk engine is available
            if RISK_ENGINE_AVAILABLE and self._fp_engine and result.get("findings"):
                validated_findings = await self.validate_findings(result["findings"].get("items", []))
                result["validated_findings"] = validated_findings

            return result

        except Exception as e:
            logger.error(f"[Zen] Autonomous scan failed: {e}")
            return {"success": False, "error": str(e), "findings": []}

    async def validate_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate findings using the False Positive Engine.

        Args:
            findings: List of raw findings from scanners

        Returns:
            List of validated findings with confidence scores
        """
        if not RISK_ENGINE_AVAILABLE or not self._fp_engine:
            logger.warning("[Zen] Risk Engine not available, returning unvalidated findings")
            return findings

        validated = []

        for finding_data in findings:
            try:
                # Convert dict to Finding object
                finding = Finding(
                    id=finding_data.get("id", ""),
                    title=finding_data.get("title", "Unknown"),
                    description=finding_data.get("description", ""),
                    severity=finding_data.get("severity", "medium"),
                    target=finding_data.get("target", ""),
                    source=finding_data.get("source", ""),
                )

                # Validate
                result = await self._fp_engine.validate_finding(finding)

                validated.append(
                    {
                        "original": finding_data,
                        "validation": result.to_dict() if hasattr(result, "to_dict") else result,
                        "is_false_positive": getattr(result, "is_false_positive", False),
                        "confidence": getattr(result, "confidence", 0.0),
                        "priority": getattr(result, "priority", 999),
                    }
                )

            except Exception as e:
                logger.error(f"[Zen] Finding validation failed: {e}")
                validated.append({"original": finding_data, "validation": None, "is_false_positive": False, "error": str(e)})

        # Sort by priority (highest first)
        validated.sort(key=lambda x: x.get("priority", 999))

        return validated

    async def execute_exploit(self, exploit: Dict[str, Any], target: str, safe_mode: bool = True) -> Dict[str, Any]:
        """
        Execute an exploit with validation and safety controls.

        Args:
            exploit: Exploit definition with code, type, etc.
            target: Target URL/host
            safe_mode: If True, run in controlled/safe mode

        Returns:
            Exploit execution result with evidence
        """
        if not AUTONOMOUS_AVAILABLE or not ExploitValidator:
            return {"success": False, "error": "Exploit Validator not available"}

        logger.info(f"[Zen] Executing exploit on {target} (safe_mode={safe_mode})")

        try:
            # Create validator with appropriate safety level
            safety = "controlled" if safe_mode else "full"
            validator = ExploitValidator(
                safety_level=safety,
                scope_config=ScopeConfig(allowed_hosts=[target]),
                sandbox_config=SandboxConfig(
                    use_docker=False,  # Default to local for compatibility
                    timeout=300,
                ),
            )

            # Get exploit details
            exploit_code = exploit.get("code", "")
            exploit_type_str = exploit.get("type", "web_rce")

            # Map string to enum
            type_map = {
                "sqli": ExploitType.WEB_SQLI,
                "sql_injection": ExploitType.WEB_SQLI,
                "xss": ExploitType.WEB_XSS,
                "rce": ExploitType.WEB_RCE,
                "lfi": ExploitType.WEB_LFI,
                "command_injection": ExploitType.WEB_CMD_INJECTION,
            }
            exploit_type = type_map.get(exploit_type_str.lower(), ExploitType.WEB_RCE)

            # Execute
            result = await validator.validate(exploit_code=exploit_code, target=target, exploit_type=exploit_type)

            return {
                "success": result.success,
                "exploitable": result.success,
                "evidence": result.evidence.to_dict() if result.evidence else {},
                "output": result.output,
                "error": result.error,
                "severity": result.severity,
                "remediation": result.remediation,
                "execution_time": result.execution_time,
            }

        except Exception as e:
            logger.error(f"[Zen] Exploit execution failed: {e}")
            return {"success": False, "error": str(e), "exploitable": False}

    async def calculate_business_impact(
        self, finding: Dict[str, Any], asset_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate business impact for a finding.

        Args:
            finding: Security finding details
            asset_context: Optional asset context information

        Returns:
            Business impact assessment
        """
        if not RISK_ENGINE_AVAILABLE or not self._business_impact:
            return {"error": "Business Impact Calculator not available", "overall_score": 0.5}

        try:
            from risk_engine import AssetContext, AssetCriticality, DataClassification

            # Create asset context
            if asset_context:
                ctx = AssetContext(
                    asset_id=asset_context.get("id", "unknown"),
                    asset_name=asset_context.get("name", "Unknown Asset"),
                    asset_type=asset_context.get("type", "unknown"),
                    criticality=AssetCriticality[asset_context.get("criticality", "MEDIUM")],
                    data_classification=DataClassification[asset_context.get("data_classification", "INTERNAL")],
                    internet_exposed=asset_context.get("internet_exposed", False),
                    user_count=asset_context.get("user_count", 0),
                    revenue_dependency=asset_context.get("revenue_dependency", 0.0),
                )
            else:
                ctx = AssetContext(
                    asset_id="unknown",
                    asset_name="Unknown Asset",
                    asset_type="unknown",
                    criticality=AssetCriticality.MEDIUM,
                    data_classification=DataClassification.INTERNAL,
                )

            result = self._business_impact.calculate_overall_impact(
                asset_context=ctx, finding_type=finding.get("type", "unknown"), severity=finding.get("severity", "medium")
            )

            return {
                "overall_score": result.overall_score,
                "risk_category": result.get_risk_category(),
                "financial_impact": {
                    "total_costs": result.financial_impact.total_costs,
                    "direct_costs": result.financial_impact.direct_costs,
                    "indirect_costs": result.financial_impact.indirect_costs,
                },
                "compliance_impact": {
                    "frameworks": [f.name for f in result.compliance_impact.frameworks],
                    "violated_controls": result.compliance_impact.violated_controls[:5],
                    "max_fine": result.compliance_impact.get_max_fine(),
                },
                "recommendations": result.get_prioritized_remediation(),
            }

        except Exception as e:
            logger.error(f"[Zen] Business impact calculation failed: {e}")
            return {"error": str(e), "overall_score": 0.5}

    async def notify_integrations(self, event: str, data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Send notifications to configured integrations.

        Args:
            event: Event type (scan_started, scan_completed, finding, etc.)
            data: Event data

        Returns:
            Status of each integration notification
        """
        results = {}

        for name, integration in self._integrations.items():
            try:
                if event == "scan_started" and hasattr(integration, "notify_scan_started"):
                    await integration.notify_scan_started(
                        target=data.get("target", "unknown"), scan_type=data.get("scan_type", "security")
                    )
                    results[name] = True

                elif event == "scan_completed" and hasattr(integration, "notify_scan_completed"):
                    await integration.notify_scan_completed(results=data, target=data.get("target", "unknown"))
                    results[name] = True

                elif event == "finding" and hasattr(integration, "notify_finding"):
                    await integration.notify_finding(data)
                    results[name] = True

                else:
                    results[name] = False

            except Exception as e:
                logger.error(f"[Zen] Failed to notify {name}: {e}")
                results[name] = False

        return results

    def get_stats(self) -> Dict:
        """Get orchestrator statistics"""
        return {
            "backends_registered": len(self.backends),
            "backends": [b.name for b in self.backends],
            "requests_processed": self.request_count,
            "autonomous_available": AUTONOMOUS_AVAILABLE,
            "risk_engine_available": RISK_ENGINE_AVAILABLE,
            "integrations_available": INTEGRATIONS_AVAILABLE,
            "integrations_loaded": list(self._integrations.keys()),
        }

    def get_capabilities(self) -> Dict[str, bool]:
        """Get available capabilities."""
        return {
            "autonomous_scan": AUTONOMOUS_AVAILABLE and self._autonomous_loop is not None,
            "false_positive_validation": RISK_ENGINE_AVAILABLE and self._fp_engine is not None,
            "exploit_validation": AUTONOMOUS_AVAILABLE and self._exploit_validator is not None,
            "business_impact": RISK_ENGINE_AVAILABLE and self._business_impact is not None,
            "slack_notifications": "slack" in self._integrations,
            "github_integration": "github" in self._integrations,
            "jira_integration": "jira" in self._integrations,
        }
