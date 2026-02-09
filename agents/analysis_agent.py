#!/usr/bin/env python3
"""
Analysis Agent - Specializes in analyzing data and finding patterns
Part of the Multi-Agent Collaboration System
Author: SHAdd0WTAka
"""

import logging
from typing import Dict, List

from .agent_base import AgentMessage, AgentRole, BaseAgent

logger = logging.getLogger("ZenAI.Agents")


class AnalysisAgent(BaseAgent):
    """
    Analysis Agent - Analyzes findings, identifies patterns
    Correlates data from multiple sources to identify attack paths
    """

    def __init__(self, name: str, orchestrator=None, zen_orchestrator=None):
        super().__init__(name, AgentRole.ANALYST, orchestrator)
        self.zen_orchestrator = zen_orchestrator
        self.analysis_cache = {}

        # Register handlers
        self.register_handler("findings", self._handle_findings)
        self.register_handler("analysis_request", self._handle_analysis_request)

    async def _handle_findings(self, msg: AgentMessage):
        """Process findings from other agents"""
        findings = msg.context.get("findings", [])
        source = msg.sender

        logger.info(f"[AnalysisAgent:{self.name}] Analyzing {len(findings)} findings from {source}")

        # Perform analysis
        analysis = await self._analyze_findings(findings)

        # If critical patterns found, alert all agents
        if analysis.get("critical_patterns"):
            await self.send_message(
                content=f"⚠️ Critical patterns detected! Risk level: {analysis['risk_level']}",
                recipient="all",
                msg_type="alert",
                priority=4,  # Critical
                context={
                    "patterns": analysis["critical_patterns"],
                    "recommendations": analysis["recommendations"],
                },
            )

        # Send detailed analysis to requesting agent
        await self.send_message(
            content=f"Analysis complete: {analysis['summary']}",
            recipient=msg.sender,
            msg_type="analysis_result",
            context={"analysis": analysis},
        )

        # Update shared context
        self.update_context(f"analysis_{msg.id}", analysis, share=True)

    async def _handle_analysis_request(self, msg: AgentMessage):
        """Handle explicit analysis requests"""
        data = msg.context.get("data", [])
        analysis_type = msg.context.get("analysis_type", "general")

        result = await self._analyze_data(data, analysis_type)

        await self.send_message(
            content=f"Analysis of {analysis_type} complete",
            recipient=msg.sender,
            msg_type="response",
            context={"analysis": result},
        )

    async def _analyze_findings(self, findings: List[Dict]) -> Dict:
        """Analyze findings and identify patterns"""
        analysis = {
            "total_findings": len(findings),
            "by_type": {},
            "critical_patterns": [],
            "risk_level": "low",
            "recommendations": [],
            "summary": "",
        }

        # Categorize by type
        for finding in findings:
            f_type = finding.get("type", "unknown")
            if f_type not in analysis["by_type"]:
                analysis["by_type"][f_type] = []
            analysis["by_type"][f_type].append(finding)

        # Look for critical patterns
        cves = [f for f in findings if f.get("type") == "cve"]

        # Pattern 1: CVE associated with ransomware
        for cve in cves:
            cve_data = cve.get("data", {})
            if hasattr(cve_data, "ransomware_used_by") and cve_data.ransomware_used_by:
                analysis["critical_patterns"].append(
                    {
                        "type": "ransomware_cve",
                        "description": f"{cve_data.cve_id} is used by ransomware",
                        "affected": cve_data.ransomware_used_by,
                    }
                )
                analysis["risk_level"] = "critical"

        # Pattern 2: Multiple high-severity CVEs
        high_cves = [c for c in cves if c.get("data", {}).get("severity") == "Critical"]
        if len(high_cves) >= 3:
            analysis["critical_patterns"].append(
                {
                    "type": "multiple_critical_cves",
                    "description": f"Found {len(high_cves)} critical CVEs",
                    "count": len(high_cves),
                }
            )
            analysis["risk_level"] = "high"

        # Generate recommendations using LLM
        if self.zen_orchestrator and analysis["critical_patterns"]:
            prompt = f"""
            Analyze these security patterns and provide recommendations:
            {analysis["critical_patterns"]}

            Provide:
            1. Priority order for remediation
            2. Immediate actions
            3. Long-term security improvements
            """

            response = await self.zen_orchestrator.process(prompt)
            analysis["recommendations"] = response.content.split("\n")

        analysis["summary"] = f"Found {len(analysis['critical_patterns'])} critical patterns across {len(findings)} findings"

        return analysis

    async def _analyze_data(self, data: List, analysis_type: str) -> Dict:
        """Generic data analysis"""
        if analysis_type == "attack_path":
            return await self._analyze_attack_paths(data)
        elif analysis_type == "correlation":
            return await self._correlate_data(data)
        else:
            return {"status": "unknown_analysis_type"}

    async def _analyze_attack_paths(self, data: List) -> Dict:
        """Analyze potential attack paths through the system"""
        # This would use the LLM to chain together vulnerabilities
        if self.zen_orchestrator:
            prompt = f"""
            Analyze these vulnerabilities and identify potential attack paths:
            {data}

            Map out:
            1. Entry points
            2. Lateral movement possibilities
            3. Critical asset exposure
            4. Kill chain stages
            """

            response = await self.zen_orchestrator.process(prompt)

            return {
                "type": "attack_path_analysis",
                "paths": response.content,
                "agent": self.name,
            }

        return {"type": "attack_path_analysis", "paths": [], "agent": self.name}

    async def _correlate_data(self, data: List) -> Dict:
        """Find correlations between different data points"""
        correlations = []

        # Simple correlation: shared CVEs between findings
        cve_sets = []
        for item in data:
            if "cves" in item:
                cve_sets.append(set(item["cves"]))

        # Find common CVEs
        if len(cve_sets) >= 2:
            common = cve_sets[0].intersection(*cve_sets[1:])
            if common:
                correlations.append(
                    {
                        "type": "shared_cves",
                        "cves": list(common),
                        "significance": "high",
                    }
                )

        return {
            "type": "correlation_analysis",
            "correlations": correlations,
            "agent": self.name,
        }

    async def execute_task(self, task: Dict) -> Dict:
        """Execute analysis task"""
        task_type = task.get("type", "")
        context = task.get("context", {})

        logger.info(f"[AnalysisAgent:{self.name}] Executing task: {task_type}")

        if task_type == "vulnerability_analysis":
            findings = context.get("findings", [])
            analysis = await self._analyze_findings(findings)

            return {"status": "complete", "analysis": analysis, "agent": self.name}

        return {"status": "unknown_task"}
