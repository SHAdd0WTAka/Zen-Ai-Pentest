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
from .react import ReActLoop, Thought, Action, Observation
from .tool_executor import ToolExecutor, ToolRegistry
from .memory import MemoryManager, WorkingMemory, LongTermMemory

# Exploit Validator components
from .exploit_validator import (
    ExploitValidator,
    ExploitValidatorPool,
    ExploitResult,
    ExploitType,
    ExploitStatus,
    SafetyLevel,
    Evidence,
    ScopeConfig,
    SandboxConfig,
    validate_sql_injection,
    validate_xss,
    validate_command_injection,
)

# Autonomous Agent Loop components
from .agent_loop import (
    AutonomousAgentLoop,
    AgentState,
    AgentMemory,
    ToolResult,
    PlanStep,
    ToolType,
    BaseTool,
    NmapScanner,
    NucleiScanner,
    ExploitValidator as ExploitValidatorTool,
    ReportGenerator,
    SubdomainEnumerator,
    ToolRegistry as AgentToolRegistry,
    create_agent_loop,
)

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
