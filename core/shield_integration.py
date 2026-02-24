"""
Integration of Zen Shield with ZenOrchestrator
Adds security layer to LLM interactions
"""

import logging
from typing import Any, Dict, Optional

import aiohttp

from zen_shield.sanitizer import ZenSanitizer
from zen_shield.schemas import SanitizerRequest, SanitizerResponse

logger = logging.getLogger(__name__)


class ShieldedOrchestrator:
    """
    Wrapper for ZenOrchestrator that adds data sanitization.

    Pipeline:
    1. Raw tool output -> Zen Shield (local sanitization)
    2. Clean data -> Big LLM (GPT-4/Claude) for analysis
    3. Response -> Optional: Normalize through shield

    This ensures:
    - No secrets leak to cloud LLMs
    - Reduced token costs (90% noise reduction)
    - Compliance with data protection policies
    - Fallback if sanitization fails
    """

    def __init__(
        self,
        bridge_url: str = "http://integration-bridge:8080",
        shield_url: str = "http://zen-shield:9000",
        big_llm_api_key: Optional[str] = None,
        big_llm_provider: str = "openai",
    ):
        """
        Initialize shielded orchestrator

        Args:
            bridge_url: URL of integration bridge for tools
            shield_url: URL of Zen Shield sanitizer service
            big_llm_api_key: API key for big LLM (GPT-4/Claude)
            big_llm_provider: Provider name
        """
        self.bridge_url = bridge_url
        self.shield_url = shield_url
        self.big_llm_api_key = big_llm_api_key
        self.big_llm_provider = big_llm_provider

        self.session: Optional[aiohttp.ClientSession] = None

        # Local sanitizer as fallback
        self.local_sanitizer: Optional[ZenSanitizer] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()

        # Try to initialize local sanitizer as backup
        try:
            self.local_sanitizer = ZenSanitizer()
        except Exception as e:
            logger.warning(f"Could not initialize local sanitizer: {e}")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def analyze_tool_output(
        self, raw_output: str, source_tool: str, intent: str = "analyze"
    ) -> Dict[str, Any]:
        """
        Analyze tool output with security sanitization

        Args:
            raw_output: Raw output from pentesting tool
            source_tool: Name of tool (nmap, nuclei, etc.)
            intent: Purpose of analysis

        Returns:
            Analysis result with metadata
        """
        # Step 1: Sanitize through Zen Shield
        sanitized = await self._sanitize_through_shield(
            raw_output, source_tool, intent
        )

        if not sanitized:
            # Fallback: analyze locally without LLM
            logger.warning("Sanitization failed, using local analysis")
            return self._local_analysis(raw_output)

        if not sanitized.safe_to_send:
            # High risk data - analyze locally
            logger.warning(
                f"High risk data detected ({len(sanitized.redactions)} redactions), using local analysis"
            )
            return self._local_analysis(sanitized.cleaned_data)

        # Step 2: Send to big LLM with sanitized data
        analysis = await self._analyze_with_big_llm(
            sanitized.cleaned_data,
            metadata={
                "source_tool": source_tool,
                "redactions_count": len(sanitized.redactions),
                "compression_ratio": sanitized.compression_ratio,
                "tokens_saved": sanitized.tokens_saved,
                "fallback_used": sanitized.fallback_used,
            },
        )

        return {
            "analysis": analysis,
            "sanitization": {
                "redactions_count": len(sanitized.redactions),
                "risk_level": sanitized.risk_level.value,
                "compression_ratio": sanitized.compression_ratio,
                "tokens_saved": sanitized.tokens_saved,
                "fallback_used": sanitized.fallback_used,
            },
        }

    async def _sanitize_through_shield(
        self, raw_data: str, source_tool: str, intent: str
    ) -> Optional[SanitizerResponse]:
        """
        Send data to Zen Shield for sanitization
        Falls back to local sanitizer if service unavailable
        """
        request = SanitizerRequest(
            raw_data=raw_data, source_tool=source_tool, intent=intent
        )

        # Try remote shield service first
        if self.session:
            try:
                async with self.session.post(
                    f"{self.shield_url}/sanitize",
                    json=request.model_dump(),
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return SanitizerResponse(**result)
            except Exception as e:
                logger.warning(f"Remote shield unavailable: {e}")

        # Fallback to local sanitizer
        if self.local_sanitizer:
            try:
                return await self.local_sanitizer.process(request)
            except Exception as e:
                logger.error(f"Local sanitization failed: {e}")

        return None

    async def _analyze_with_big_llm(
        self, cleaned_data: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send sanitized data to big LLM for analysis
        """
        # This integrates with your existing LLM bridge
        # For now, returning placeholder

        tool = metadata.get("source_tool", "unknown")

        # Construct prompt for big LLM
        prompt = f"""Analyze the following {tool} scan output for security issues:

{cleaned_data}

Focus on:
1. Open ports and services
2. Potential vulnerabilities
3. Misconfigurations
4. Exploitation paths

Be concise and technical."""

        # Here you would call your existing LLM bridge
        # For now, return structure
        return {
            "prompt": prompt,
            "metadata": metadata,
            "provider": self.big_llm_provider,
            "note": "Integrate with your existing LLM bridge here",
        }

    def _local_analysis(self, data: str) -> Dict[str, Any]:
        """
        Local analysis without LLM
        Used when sanitization fails or risk is too high
        """
        # Simple keyword-based analysis
        findings = []

        # Check for common patterns
        if "open" in data.lower():
            findings.append("Open ports detected")
        if "vuln" in data.lower() or "vulnerable" in data.lower():
            findings.append("Potential vulnerabilities found")
        if "error" in data.lower():
            findings.append("Errors in scan output")
        if "unauthorized" in data.lower() or "401" in data:
            findings.append("Authentication may be required")

        return {
            "analysis": {
                "findings": findings,
                "note": "Local analysis (LLM bypassed due to security concerns)",
            },
            "sanitization": {
                "local_only": True,
                "reason": "security_fallback",
            },
        }

    async def comprehensive_scan_with_shield(
        self, target: str, tools: list[str], use_shield: bool = True
    ) -> Dict[str, Any]:
        """
        Run comprehensive scan with shield protection

        Args:
            target: Target to scan
            tools: List of tools to use
            use_shield: Whether to use sanitization
        """
        from modules.tool_orchestrator import ToolOrchestrator

        results = {
            "target": target,
            "tools_used": tools,
            "findings": [],
            "sanitization_applied": use_shield,
        }

        async with ToolOrchestrator(self.bridge_url) as orch:
            for tool in tools:
                try:
                    # Run tool scan
                    scan_result = await self._run_tool(orch, tool, target)
                    raw_output = scan_result.get("raw_output", "")

                    if use_shield and raw_output:
                        # Sanitize and analyze
                        analysis = await self.analyze_tool_output(
                            raw_output, tool, intent="analyze"
                        )
                        results["findings"].append(
                            {"tool": tool, "analysis": analysis}
                        )
                    else:
                        # Raw output without sanitization (not recommended)
                        results["findings"].append(
                            {"tool": tool, "raw": raw_output[:1000]}
                        )  # Truncate

                except Exception as e:
                    logger.error(f"Tool {tool} failed: {e}")
                    results["findings"].append({"tool": tool, "error": str(e)})

        return results

    async def _run_tool(
        self, orchestrator, tool: str, target: str
    ) -> Dict[str, Any]:
        """Run specific tool through orchestrator"""
        method_map = {
            "nmap": orchestrator.scan_with_nmap,
            "nuclei": orchestrator.scan_with_nuclei,
            "gobuster": orchestrator.scan_with_gobuster,
            "amass": orchestrator.enumerate_subdomains,
        }

        method = method_map.get(tool)
        if not method:
            raise ValueError(f"Unknown tool: {tool}")

        # Trigger scan
        if tool == "amass":
            result = await method(target, active=False)
        else:
            result = await method(target)

        scan_id = result.get("scan_id")

        # Wait for completion
        status = await orchestrator.wait_for_scan(scan_id)

        # Get results
        scan_results = await orchestrator.get_scan_results(scan_id)

        return {
            "scan_id": scan_id,
            "status": status.get("status"),
            "raw_output": str(scan_results.get("results", "")),
        }
