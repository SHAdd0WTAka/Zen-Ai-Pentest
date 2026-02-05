"""
ReAct (Reasoning + Acting) Pattern Implementation

The ReAct loop allows the agent to:
1. Think about the current situation (Reasoning)
2. Decide what to do (Action)
3. Observe the result (Observation)
4. Repeat until goal is achieved

Based on: https://arxiv.org/abs/2210.03629
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class ActionType(Enum):
    """Types of actions the agent can take."""
    THINK = auto()          # Internal reasoning
    TOOL_CALL = auto()      # Execute a security tool
    SEARCH_MEMORY = auto()  # Recall past information
    ASK_HUMAN = auto()      # Request clarification
    REPORT = auto()         # Deliver findings
    TERMINATE = auto()      # End the session


@dataclass
class Thought:
    """A reasoning step in the agent's thought process."""
    content: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    step_number: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'type': 'thought',
            'content': self.content,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'step': self.step_number
        }


@dataclass
class Action:
    """An action the agent decides to take."""
    type: ActionType
    tool_name: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    step_number: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'type': 'action',
            'action_type': self.type.name,
            'tool': self.tool_name,
            'parameters': self.parameters,
            'reasoning': self.reasoning,
            'timestamp': self.timestamp.isoformat(),
            'step': self.step_number
        }


@dataclass
class Observation:
    """The result of executing an action."""
    action: Action
    result: Any
    success: bool = True
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    step_number: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'type': 'observation',
            'action': self.action.to_dict(),
            'result': self.result,
            'success': self.success,
            'error': self.error_message,
            'timestamp': self.timestamp.isoformat(),
            'step': self.step_number
        }


class ReActLoop:
    """
    ReAct Reasoning Loop implementation.
    
    Continuously cycles through:
    1. Reason about current state
    2. Decide on action
    3. Execute action
    4. Observe result
    5. Update state
    """
    
    def __init__(
        self,
        llm_client,
        tool_executor,
        memory_manager,
        max_iterations: int = 50,
        human_in_the_loop: bool = False
    ):
        self.llm = llm_client
        self.tools = tool_executor
        self.memory = memory_manager
        self.max_iterations = max_iterations
        self.human_in_the_loop = human_in_the_loop
        
        self.history: List[Dict] = []
        self.current_step: int = 0
        self.goal: Optional[str] = None
        
    async def run(self, goal: str, context: Optional[Dict] = None) -> Dict:
        """
        Execute the ReAct loop until goal is achieved or max iterations reached.
        
        Args:
            goal: The high-level objective
            context: Additional context (target info, scope, etc.)
            
        Returns:
            Final result with findings and execution trace
        """
        self.goal = goal
        self.current_step = 0
        self.history = []
        
        # Initialize with goal in memory
        await self.memory.add_goal(goal, context)
        
        print(f"[ReAct] Starting autonomous execution for goal: {goal}")
        
        while self.current_step < self.max_iterations:
            self.current_step += 1
            print(f"\n[ReAct] Step {self.current_step}/{self.max_iterations}")
            
            # 1. REASON: Think about current state
            thought = await self._reason()
            self.history.append(thought.to_dict())
            print(f"[Thought] {thought.content[:100]}...")
            
            # 2. ACT: Decide on action
            action = await self._decide_action(thought)
            self.history.append(action.to_dict())
            print(f"[Action] {action.type.name}" + (f" ({action.tool_name})" if action.tool_name else ""))
            
            # Check for termination
            if action.type == ActionType.TERMINATE:
                print("[ReAct] Goal achieved or terminated")
                break
            
            # 3. EXECUTE: Perform the action
            observation = await self._execute_action(action)
            self.history.append(observation.to_dict())
            
            if observation.success:
                result_str = str(observation.result)[:100] if observation.result else "None"
                print(f"[Observation] Success: {result_str}...")
            else:
                print(f"[Observation] Failed: {observation.error_message}")
            
            # 4. LEARN: Update memory
            await self.memory.add_experience(thought, action, observation)
            
            # Human checkpoint if enabled
            if self.human_in_the_loop and action.type in [ActionType.TOOL_CALL, ActionType.REPORT]:
                approved = await self._human_approval(action)
                if not approved:
                    print("[ReAct] Human rejected action, stopping")
                    break
        
        # Compile final result
        return self._compile_result()
    
    async def _reason(self) -> Thought:
        """Generate a thought about the current situation."""
        context = await self.memory.get_relevant_context(self.goal)
        
        prompt = f"""You are an autonomous penetration testing agent.
        
Goal: {self.goal}

Current Context:
{json.dumps(context, indent=2)}

Execution History (last 5 steps):
{json.dumps(self.history[-5:], indent=2)}

Step {self.current_step}: What is your assessment of the current situation? 
What have you learned? What should you do next?

Provide your reasoning:"""
        
        response = await self.llm.generate(prompt)
        
        return Thought(
            content=response,
            context={'goal': self.goal, 'step': self.current_step},
            step_number=self.current_step
        )
    
    async def _decide_action(self, thought: Thought) -> Action:
        """Decide on the next action based on reasoning."""
        available_tools = self.tools.get_available_tools()
        
        prompt = f"""Based on your reasoning: "{thought.content}"

Available Tools:
{json.dumps(available_tools, indent=2)}

Decide on the next action. Respond in JSON format:
{{
    "action_type": "TOOL_CALL|SEARCH_MEMORY|ASK_HUMAN|REPORT|TERMINATE",
    "tool_name": "name_of_tool_if_applicable",
    "parameters": {{}},
    "reasoning": "why this action"
}}

Rules:
- Use TOOL_CALL to execute security tools (nmap, nuclei, etc.)
- Use SEARCH_MEMORY to recall past findings
- Use REPORT when you have findings to deliver
- Use TERMINATE when goal is achieved or stuck"""
        
        response = await self.llm.generate(prompt)
        
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                decision = json.loads(response[json_start:json_end])
            else:
                decision = json.loads(response)
            
            action_type = ActionType[decision.get('action_type', 'THINK')]
            
            return Action(
                type=action_type,
                tool_name=decision.get('tool_name'),
                parameters=decision.get('parameters', {}),
                reasoning=decision.get('reasoning', ''),
                step_number=self.current_step
            )
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback to thinking if parsing fails
            return Action(
                type=ActionType.THINK,
                reasoning=f"Failed to parse action: {str(e)}",
                step_number=self.current_step
            )
    
    async def _execute_action(self, action: Action) -> Observation:
        """Execute the decided action."""
        try:
            if action.type == ActionType.TOOL_CALL and action.tool_name:
                result = await self.tools.execute(
                    action.tool_name,
                    action.parameters
                )
                return Observation(
                    action=action,
                    result=result,
                    success=True,
                    step_number=self.current_step
                )
            
            elif action.type == ActionType.SEARCH_MEMORY:
                query = action.parameters.get('query', self.goal)
                results = await self.memory.search(query)
                return Observation(
                    action=action,
                    result=results,
                    success=True,
                    step_number=self.current_step
                )
            
            elif action.type == ActionType.REPORT:
                findings = await self.memory.get_findings()
                return Observation(
                    action=action,
                    result={'findings': findings, 'ready': True},
                    success=True,
                    step_number=self.current_step
                )
            
            else:
                return Observation(
                    action=action,
                    result=None,
                    success=True,
                    step_number=self.current_step
                )
                
        except Exception as e:
            return Observation(
                action=action,
                result=None,
                success=False,
                error_message=str(e),
                step_number=self.current_step
            )
    
    async def _human_approval(self, action: Action) -> bool:
        """Request human approval for critical actions."""
        print("\n[Human Approval Required]")
        print(f"Action: {action.type.name}")
        print(f"Tool: {action.tool_name}")
        print(f"Parameters: {action.parameters}")
        print(f"Reasoning: {action.reasoning}")
        
        # In real implementation, this would be a UI prompt
        # For now, auto-approve in autonomous mode
        return True
    
    def _compile_result(self) -> Dict:
        """Compile the final execution result."""
        findings = [h for h in self.history if h.get('type') == 'observation']
        
        return {
            'goal': self.goal,
            'completed': self.current_step < self.max_iterations,
            'steps_taken': self.current_step,
            'history': self.history,
            'findings': findings,
            'execution_trace': f"Completed in {self.current_step} steps"
        }
