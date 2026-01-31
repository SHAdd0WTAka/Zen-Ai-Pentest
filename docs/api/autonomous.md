# Autonomous Module API

## ReAct Loop

### Class: `ReActLoop`

Main autonomous reasoning and acting loop.

```python
from autonomous.react import ReActLoop, AgentConfig

config = AgentConfig(
    max_iterations=50,
    safety_level=SafetyLevel.NON_DESTRUCTIVE,
    tools=["nmap", "nuclei"]
)
loop = ReActLoop(llm_client=client, memory=memory, config=config)
```

#### Methods

##### `async run(goal: str, target: Optional[str] = None, human_in_the_loop: bool = False) -> Dict`

Execute the ReAct loop to achieve a goal.

**Parameters:**
- `goal` (str): The penetration testing goal
- `target` (str, optional): Target URL/IP
- `human_in_the_loop` (bool): Enable human approval for actions

**Returns:**
- Dictionary with `success`, `findings`, `actions_taken`, `reasoning_chain`

### Class: `AgentConfig`

Configuration for the ReAct agent.

```python
@dataclass
class AgentConfig:
    max_iterations: int = 50
    safety_level: SafetyLevel = SafetyLevel.NON_DESTRUCTIVE
    tools: Optional[List[str]] = None
```

### Enum: `ActionType`

Types of actions the agent can take:

- `SCAN`: Network/service scanning
- `EXPLOIT`: Exploitation attempts
- `ENUMERATE`: Information gathering
- `ANALYZE`: Result analysis
- `REPORT`: Generate reports
- `TERMINATE`: End the session

## Tool Executor

### Class: `ToolExecutor`

Execute security tools with safety controls.

```python
from autonomous.tool_executor import ToolExecutor, SafetyLevel

executor = ToolExecutor(
    safety_level=SafetyLevel.NON_DESTRUCTIVE,
    use_docker=True,
    timeout=300
)
```

#### Methods

##### `async execute(tool_name: str, target: str, options: Optional[Dict] = None) -> ToolResult`

Execute a security tool.

**Parameters:**
- `tool_name` (str): Name of the tool
- `target` (str): Target to scan
- `options` (dict, optional): Tool-specific options

**Returns:**
- `ToolResult` with `success`, `output`, `parsed_output`, `execution_time`
