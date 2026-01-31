"""
Autonomous Agent - Main Entry Point

Combines ReAct reasoning, tool execution, and memory into a unified agent.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .react import ReActLoop, Thought, Action, Observation
from .tool_executor import ToolExecutor, ToolRegistry, SafetyLevel
from .memory import MemoryManager


@dataclass
class AgentConfig:
    """Configuration for the autonomous agent."""
    max_iterations: int = 50
    safety_level: SafetyLevel = SafetyLevel.NON_DESTRUCTIVE
    human_in_the_loop: bool = False
    enable_memory: bool = True
    use_docker: bool = False
    timeout: int = 300
    output_dir: Optional[str] = None


class AutonomousAgent:
    """
    Fully autonomous penetration testing agent.
    
    Capabilities:
    - Goal-directed hacking
    - Real tool execution
    - Persistent memory
    - Self-correction
    - Safety controls
    
    Example:
        agent = AutonomousAgent(
            llm_client=my_llm,
            config=AgentConfig(safety_level=SafetyLevel.READ_ONLY)
        )
        
        result = await agent.run(
            goal="Find all open ports on 192.168.1.1",
            target="192.168.1.1"
        )
    """
    
    def __init__(
        self,
        llm_client,
        config: Optional[AgentConfig] = None,
        tool_registry: Optional[ToolRegistry] = None,
        memory_manager: Optional[MemoryManager] = None
    ):
        self.llm = llm_client
        self.config = config or AgentConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.tools = ToolExecutor(
            registry=tool_registry,
            safety_level=self.config.safety_level,
            use_docker=self.config.use_docker,
            output_dir=self.config.output_dir
        )
        
        self.memory = memory_manager or MemoryManager(
            enable_embeddings=False
        )
        
        self.react = ReActLoop(
            llm_client=llm_client,
            tool_executor=self.tools,
            memory_manager=self.memory,
            max_iterations=self.config.max_iterations,
            human_in_the_loop=self.config.human_in_the_loop
        )
        
        self.execution_history: List[Dict] = []
    
    async def run(
        self,
        goal: str,
        target: Optional[str] = None,
        scope: Optional[Dict] = None,
        callbacks: Optional[Dict[str, Callable]] = None
    ) -> Dict[str, Any]:
        """
        Execute an autonomous penetration test.
        
        Args:
            goal: High-level objective (e.g., "Find RCE vulnerability")
            target: Target system (IP, URL, etc.)
            scope: Scope limitations and rules
            callbacks: Optional callbacks for events
            
        Returns:
            Complete execution result with findings
        """
        self.logger.info(f"Starting autonomous execution: {goal}")
        
        # Prepare context
        context = {
            'target': target,
            'scope': scope or {},
            'safety_level': self.config.safety_level.name,
            'start_time': datetime.now().isoformat()
        }
        
        # Execute ReAct loop
        result = await self.react.run(goal, context)
        
        # Record episode
        await self.memory.record_episode(
            outcome=result.get('execution_trace', ''),
            success=result.get('completed', False)
        )
        
        # Compile final report
        report = self._compile_report(result, target)
        
        self.execution_history.append(report)
        
        return report
    
    def _compile_report(
        self,
        result: Dict,
        target: Optional[str]
    ) -> Dict[str, Any]:
        """Compile execution result into a comprehensive report."""
        
        # Extract findings
        findings = []
        for entry in result.get('history', []):
            if entry.get('type') == 'observation':
                obs_result = entry.get('result', {})
                if isinstance(obs_result, dict):
                    if 'findings' in obs_result:
                        findings.extend(obs_result['findings'])
                    if 'open_ports' in obs_result:
                        for port in obs_result['open_ports']:
                            findings.append({
                                'type': 'open_port',
                                'severity': 'info',
                                'details': port
                            })
        
        # Calculate statistics
        tools_used = set()
        for entry in result.get('history', []):
            if entry.get('type') == 'action' and entry.get('tool'):
                tools_used.add(entry.get('tool'))
        
        return {
            'summary': {
                'goal': result.get('goal'),
                'target': target,
                'completed': result.get('completed'),
                'steps_taken': result.get('steps_taken'),
                'tools_used': list(tools_used),
                'findings_count': len(findings),
                'duration': self._calculate_duration(result)
            },
            'findings': findings,
            'execution_trace': result.get('history', []),
            'timestamp': datetime.now().isoformat(),
            'agent_version': '2.0.0'
        }
    
    def _calculate_duration(self, result: Dict) -> float:
        """Calculate execution duration from history."""
        history = result.get('history', [])
        if not history:
            return 0.0
        
        # This is a simplified calculation
        # In production, track actual timestamps
        return result.get('steps_taken', 0) * 5.0  # Estimate 5s per step
    
    async def scan_target(
        self,
        target: str,
        scan_type: str = 'comprehensive'
    ) -> Dict[str, Any]:
        """
        Quick scan method for common use cases.
        
        Args:
            target: Target to scan
            scan_type: 'quick', 'standard', or 'comprehensive'
            
        Returns:
            Scan results
        """
        goals = {
            'quick': f"Quick reconnaissance of {target}",
            'standard': f"Standard vulnerability assessment of {target}",
            'comprehensive': f"Comprehensive penetration test of {target}"
        }
        
        goal = goals.get(scan_type, goals['standard'])
        
        return await self.run(
            goal=goal,
            target=target,
            scope={'depth': scan_type}
        )
    
    async def exploit_target(
        self,
        target: str,
        vulnerability: str
    ) -> Dict[str, Any]:
        """
        Attempt to exploit a specific vulnerability.
        
        Requires SafetyLevel.EXPLOIT or higher.
        """
        if self.config.safety_level.value < SafetyLevel.EXPLOIT.value:
            return {
                'error': 'Safety level too low for exploitation',
                'required': SafetyLevel.EXPLOIT.name,
                'current': self.config.safety_level.name
            }
        
        return await self.run(
            goal=f"Exploit {vulnerability} on {target}",
            target=target,
            scope={'exploitation': True, 'target_vuln': vulnerability}
        )
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about agent capabilities."""
        return {
            'version': '2.0.0',
            'safety_level': self.config.safety_level.name,
            'max_iterations': self.config.max_iterations,
            'available_tools': self.tools.get_available_tools(),
            'features': [
                'ReAct reasoning loop',
                'Real tool execution',
                'Persistent memory',
                'Self-correction',
                'Safety controls'
            ]
        }
