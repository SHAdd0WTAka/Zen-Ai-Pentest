"""
Autonomous Agent System for Zen AI Pentest (2026 Roadmap - Q1)

This module implements:
- ReAct/Plan-and-Execute reasoning loop
- Real tool execution framework
- Memory system with vector storage
- Self-correction capabilities

Usage:
    from autonomous import AutonomousAgent
    
    agent = AutonomousAgent(goal="Find RCE in target API")
    result = await agent.run()
"""

from .agent import AutonomousAgent
from .react import ReActLoop, Thought, Action, Observation
from .tool_executor import ToolExecutor, ToolRegistry
from .memory import MemoryManager, WorkingMemory, LongTermMemory

__all__ = [
    'AutonomousAgent',
    'ReActLoop',
    'Thought',
    'Action',
    'Observation',
    'ToolExecutor',
    'ToolRegistry',
    'MemoryManager',
    'WorkingMemory',
    'LongTermMemory',
]

__version__ = '2.0.0'
