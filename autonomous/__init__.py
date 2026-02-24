"""
Autonomous Agent System for Zen AI Pentest (2026 Roadmap - Q1)

This module implements:
- ReAct/Plan-and-Execute reasoning loop
- Real tool execution framework
- Memory system with vector storage
- Self-correction capabilities
- Exploit validation with sandboxed execution

Usage:
    from autonomous import AutonomousAgent

    agent = AutonomousAgent(goal="Find RCE in target API")
    result = await agent.run()

    # Exploit Validation
    from autonomous import ExploitValidator, ExploitType

    validator = ExploitValidator()
    result = await validator.validate(
        exploit_code="...",
        target="https://example.com",
        exploit_type=ExploitType.WEB_SQLI
    )

    # Autonomous Agent Loop
    from autonomous import AutonomousAgentLoop, AgentState, AgentMemory

    agent_loop = AutonomousAgentLoop(max_iterations=50)
    result = await agent_loop.run(
        goal="Find vulnerabilities",
        target="example.com",
        scope={"depth": "comprehensive"}
    )
"""

# Core autonomous components
from .agent import AutonomousAgent

# Autonomous Agent Loop components
from .agent_loop import (
    AgentMemory,
    AgentState,
    AutonomousAgentLoop,
    BaseTool,
    NmapScanner,
    NucleiScanner,
    PlanStep,
    ReportGenerator,
    SubdomainEnumerator,
    ToolResult,
    ToolType,
    create_agent_loop,
)
from .agent_loop import ExploitValidator as ExploitValidatorTool
from .agent_loop import ToolRegistry as AgentToolRegistry

# Exploit Validator components
from .exploit_validator import (
    Evidence,
    ExploitResult,
    ExploitStatus,
    ExploitType,
    ExploitValidator,
    ExploitValidatorPool,
    SafetyLevel,
    SandboxConfig,
    ScopeConfig,
    validate_command_injection,
    validate_sql_injection,
    validate_xss,
)
from .memory import LongTermMemory, MemoryManager, WorkingMemory
from .react import Action, Observation, ReActLoop, Thought
from .tool_executor import ToolExecutor, ToolRegistry

__all__ = [
    # Core autonomous components
    "AutonomousAgent",
    "ReActLoop",
    "Thought",
    "Action",
    "Observation",
    "ToolExecutor",
    "ToolRegistry",
    "MemoryManager",
    "WorkingMemory",
    "LongTermMemory",
    # Exploit Validator components
    "ExploitValidator",
    "ExploitValidatorPool",
    "ExploitResult",
    "ExploitType",
    "ExploitStatus",
    "SafetyLevel",
    "Evidence",
    "ScopeConfig",
    "SandboxConfig",
    "validate_sql_injection",
    "validate_xss",
    "validate_command_injection",
    # Autonomous Agent Loop components
    "AutonomousAgentLoop",
    "AgentState",
    "AgentMemory",
    "ToolResult",
    "PlanStep",
    "ToolType",
    "BaseTool",
    "NmapScanner",
    "NucleiScanner",
    "ExploitValidatorTool",
    "ReportGenerator",
    "SubdomainEnumerator",
    "AgentToolRegistry",
    "create_agent_loop",
]

__version__ = "2.0.0"
