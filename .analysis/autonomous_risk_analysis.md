# Zen AI Pentest - Autonomous & Risk Analysis Engine

## Executive Summary

This document provides a comprehensive analysis of the autonomous agent system, risk scoring engine, memory management, and safety guardrails in the Zen AI Pentest framework. The codebase implements a sophisticated AI-driven penetration testing platform with ReAct-based reasoning, multi-factor risk scoring, and robust safety controls.

---

## 1. ReAct Agent Implementation

### 1.1 Architecture Overview

The ReAct (Reasoning + Acting) pattern is implemented across multiple files:

| Component | File | Purpose |
|-----------|------|---------|
| Core ReAct Loop | `autonomous/react.py` | Base reasoning loop implementation |
| KI Analysis Agent | `autonomous/ki_analysis_agent.py` | AI-powered autonomous agent |
| Agent Loop | `autonomous/agent_loop.py` | State machine-driven execution |
| Main Agent | `autonomous/agent.py` | Unified agent interface |

### 1.2 ReAct Pattern Implementation (`autonomous/react.py`)

```python
class ReActLoop:
    # Cycles through: REASON → ACT → OBSERVE → LEARN
    - max_iterations: int = 50
    - human_in_the_loop: bool = False
    - history: List[Dict]  # Complete execution trace
```

**Key Classes:**
- `Thought`: Reasoning step with context
- `Action`: Action with type, tool_name, parameters
- `Observation`: Result of action execution
- `ActionType`: Enum (THINK, TOOL_CALL, SEARCH_MEMORY, ASK_HUMAN, REPORT, TERMINATE)

**ReAct Flow:**
1. **_reason()**: Generate assessment using LLM with context
2. **_decide_action()**: Choose action from available tools
3. **_execute_action()**: Perform tool execution
4. **Update memory**: Store experience for learning

### 1.3 KI Autonomous Agent (`autonomous/ki_analysis_agent.py`)

**State Machine:**
```
IDLE → PLANNING → EXECUTING → OBSERVING → REFLECTING → COMPLETED
              ↓__________________________________________↑
```

**Analysis Phases:**
1. `RECONNAISSANCE` - Initial target discovery
2. `SCANNING` - Port and service enumeration
3. `ENUMERATION` - Detailed asset mapping
4. `VULNERABILITY_ANALYSIS` - Finding vulnerabilities
5. `EXPLOITATION` - Validating exploits (controlled)
6. `POST_EXPLOITATION` - Lateral movement analysis
7. `REPORTING` - Final report generation

**Key Features:**
- Integration with `kimi-cli` for AI analysis
- Fallback analysis when KI unavailable
- Human-in-the-loop for critical actions
- Self-correction with retry logic (3 attempts, exponential backoff)

### 1.4 Agent Loop with Tools (`autonomous/agent_loop.py`)

**Available Tools (ToolType Enum):**
| Tool | Description | Safety Level |
|------|-------------|--------------|
| `NMAP_SCANNER` | Port scanning | Read-only |
| `NUCLEI_SCANNER` | Vulnerability detection | Non-destructive |
| `EXPLOIT_VALIDATOR` | Exploit validation | Controlled |
| `REPORT_GENERATOR` | Report generation | Read-only |
| `SUBDOMAIN_ENUMERATOR` | Subdomain discovery | Read-only |

**Plan Generation Logic:**
```python
if "port" in goal or "service" in goal:
    plan.append(NMAP_SCANNER)
if "subdomain" in goal or "enumerate" in goal:
    plan.append(SUBDOMAIN_ENUMERATOR)
if "vulnerability" in goal or "scan" in goal:
    plan.append(NUCLEI_SCANNER)
if "exploit" in goal:
    plan.append(EXPLOIT_VALIDATOR)
```

---

## 2. Autonomous Decision-Making Logic

### 2.1 Decision Framework

**Multi-Layer Decision Process:**

1. **Goal Analysis**: Parse natural language goal
2. **Plan Creation**: Generate step-by-step execution plan
3. **Tool Selection**: Choose appropriate security tools
4. **Execution Monitoring**: Track progress and errors
5. **Reflection**: Evaluate success and adjust strategy

### 2.2 Tool Execution Framework (`autonomous/tool_executor.py`)

**Safety Levels:**
| Level | Value | Description | Example Tools |
|-------|-------|-------------|---------------|
| READ_ONLY | 1 | Passive reconnaissance | nmap -sS, subfinder |
| NON_DESTRUCTIVE | 2 | Active but safe scanning | nuclei, ffuf, gobuster |
| DESTRUCTIVE | 3 | May modify state | sqlmap --dump |
| EXPLOIT | 4 | Full exploitation | metasploit |

**Tool Registry:**
- 14+ pre-configured security tools
- Command template system
- Automatic parameter sanitization (shlex.quote)
- Docker execution option for isolation

### 2.3 Exploit Validation System (`autonomous/exploit_validator.py`)

**ExploitType Enum:**
- `WEB_SQLI`, `WEB_XSS`, `WEB_LFI`, `WEB_RFI`, `WEB_RCE`
- `WEB_CMD_INJECTION`, `WEB_CSRF`, `WEB_SSRF`, `WEB_XXE`
- `WEB_PATH_TRAVERSAL`, `SERVICE`, `PRIVESC`, `POST_EXPLOITATION`, `LOCAL`

**Safety Features:**
- Docker-based sandboxing
- Scope validation (allowed/blocked hosts)
- Rate limiting (5 concurrent exploits max)
- Kill switch for emergency stop
- Evidence collection (screenshots, HTTP capture, PCAP)

**Chain of Custody:**
```python
chain_of_custody = [
    {"action": "validation_started", "timestamp": "...", "hash": "..."},
    {"action": "scope_validated", "timestamp": "..."},
    {"action": "execution_completed", "timestamp": "...", "exit_code": 0},
]
```

---

## 3. Risk Scoring (CVSS, EPSS, Business Impact)

### 3.1 CVSS Calculator

**Implementation:** `risk/cvss.py`, `risk_engine/cvss.py`

**CVSS v3.1 Weights:**
```python
WEIGHTS = {
    "AV": {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2},
    "AC": {"L": 0.77, "H": 0.44},
    "PR": {"N": 0.85, "L": 0.62, "H": 0.27},
    "UI": {"N": 0.85, "R": 0.62},
    "S": {"U": 6.42, "C": 7.52},
    "CIA": {"N": 0.0, "L": 0.22, "H": 0.56},
}
```

**Score Calculation:**
```python
ISS = 1 - ((1 - C) * (1 - I) * (1 - A))
Impact = 6.42 * ISS (unchanged) or 7.52 * (ISS - 0.029) - 3.25 * (ISS - 0.02)^15 (changed)
Exploitability = 8.22 * AV * AC * PR * UI
Base Score = min(Impact + Exploitability, 10.0)
```

### 3.2 EPSS Integration

**Implementation:** `risk/epss.py`, `risk_engine/epss.py`

**FIRST EPSS API Integration:**
- API Endpoint: `https://api.first.org/data/v1/epss`
- Caching: 24-hour cache duration
- Batch queries: Up to 100 CVEs per request

**EPSS Risk Levels:**
| Score Range | Risk Level | Interpretation |
|-------------|------------|----------------|
| ≥ 0.5 | Very High | Active exploitation likely |
| 0.3 - 0.5 | High | Exploitation probable |
| 0.1 - 0.3 | Medium | Some exploitation risk |
| 0.05 - 0.1 | Low | Limited exploitation risk |
| < 0.05 | Very Low | Unlikely to be exploited |

### 3.3 Business Impact Calculator

**Implementation:** `risk_engine/business_impact_calculator.py`

**Key Enums:**
```python
DataClassification: PUBLIC(0.1), INTERNAL(0.3), CONFIDENTIAL(0.6), RESTRICTED(0.9)
AssetCriticality: MINIMAL(1, 0.1), LOW(2, 0.3), MEDIUM(3, 0.5), HIGH(4, 0.8), CRITICAL(5, 1.0)
ComplianceFramework: PCI_DSS(0.95), HIPAA(0.9), GDPR(0.85), SOX(0.8), ISO27001(0.75), NIST(0.7)
ReputationImpact: LOW(0.1), MODERATE(0.4), HIGH(0.7), SEVERE(1.0)
```

**Financial Impact Calculation:**
- Direct costs (response, forensics)
- Indirect costs (outage time)
- Regulatory fines (GDPR: €20M, HIPAA: $1.5M, etc.)
- Legal costs
- Reputation costs (5-15% of annual revenue)

**Industry Multipliers:**
| Industry | Compliance | Reputation | Financial |
|----------|------------|------------|-----------|
| Healthcare | 1.2 | 1.3 | 1.1 |
| Finance | 1.3 | 1.2 | 1.2 |
| Government | 1.4 | 1.0 | 0.9 |
| Technology | 1.0 | 1.2 | 1.1 |

### 3.4 Unified Risk Scoring

**Implementation:** `risk_engine/scorer.py`, `risk/risk_engine.py`

**Weight Distribution:**
```python
WEIGHTS = {
    "cvss": 0.25,      # Technical severity
    "epss": 0.25,      # Exploit probability
    "business": 0.35,  # Business impact (highest weight)
    "validation": 0.15, # Confirmed exploitation
}
```

**Severity Levels with SLA:**
| Level | Score Range | SLA |
|-------|-------------|-----|
| CRITICAL | 9.0 - 10.0 | 24h |
| HIGH | 7.0 - 8.9 | 72h |
| MEDIUM | 4.0 - 6.9 | 14d |
| LOW | 1.0 - 3.9 | 30d |
| INFO | 0.0 - 0.9 | Best effort |

---

## 4. False Positive Reduction Mechanisms

### 4.1 False Positive Engine (`risk_engine/false_positive_engine.py`)

**Multi-Factor Validation:**

1. **Historical Data Analysis**
   - `FalsePositiveDatabase` with SHA256 hashing
   - Bayesian Filter for pattern learning
   - User feedback integration

2. **Multi-LLM Voting** (`LLMVotingEngine`)
   - Consensus threshold: 60%
   - Minimum confidence: 50%
   - Pluggable LLM clients

3. **EPSS Scoring**
   - Exploit probability weighting
   - CVE prioritization

4. **Risk Factor Analysis**
   - Context-aware scoring
   - Asset criticality
   - Network exposure

**FindingStatus Enum:**
```python
CONFIRMED = "confirmed"      # High confidence real vulnerability
LIKELY = "likely"            # Probably real
SUSPECTED = "suspected"      # Needs investigation
FALSE_POSITIVE = "false_positive"  # Likely FP
UNDER_REVIEW = "under_review"
SUPPRESSED = "suppressed"
```

**Bayesian Filter Implementation:**
```python
class BayesianFilter:
    - word_probs_fp: Dict[str, float]  # False positive word probabilities
    - word_probs_tp: Dict[str, float]  # True positive word probabilities
    - fp_count, tp_count: int          # Training counts
    
    def train(text: str, is_false_positive: bool)
    def predict(text: str) -> Tuple[bool, float]
```

### 4.2 Risk Factor Weighting

```python
weights = {
    "cvss": 0.25,
    "epss": 0.20,
    "business_impact": 0.20,
    "exploitability": 0.15,
    "asset_criticality": 0.15,
    "context": 0.05,
}

# Context multipliers
if internet_exposed: +0.3
if exploit_code_available: +0.2
if active_exploitation_observed: +0.4
if not patch_available: +0.1
if not authentication_required: +0.2
```

---

## 5. Memory System Architecture

### 5.1 Memory Types

**Implementation:** `memory/` directory

| Type | Purpose | Persistence | Class |
|------|---------|-------------|-------|
| Working Memory | Current session context | No | `WorkingMemory` |
| Short-term | Recent actions (N=100) | No | `AgentMemory` |
| Long-term | Vector storage | Yes | `LongTermMemory` |
| Episodic | Complete attack chains | Yes | `EpisodicMemory` |
| Conversation | Multi-turn dialogue | Optional | `ConversationMemory` |

### 5.2 Working Memory (`autonomous/memory.py`, `memory/working.py`)

```python
class WorkingMemory:
    - max_size: int = 100
    - entries: List[MemoryEntry]
    - current_goal: Optional[str]
    - context: Dict[str, Any]
    - scratchpad: Dict[str, Any]
```

**Features:**
- Context window management for LLM
- Simple text search
- Goal tracking
- Context updates

### 5.3 Long-Term Memory

**Vector Storage (Simplified Hash Embedding):**
```python
def _simple_hash_embedding(self, text: str) -> List[float]:
    # 128-dimensional bag-of-words embedding
    # Uses MD5 hash for word indexing
    # Cosine similarity for search
```

**Note:** Production should use proper embeddings (OpenAI, HuggingFace, ChromaDB, Pinecone)

### 5.4 Episodic Memory

```python
class EpisodicMemory:
    def record_episode(goal, steps, outcome, success, lessons_learned)
    def get_similar_episodes(goal) -> List[Dict]
    # Uses Jaccard similarity for goal matching
```

### 5.5 Storage Backends (`memory/storage.py`)

**SQLiteStorage:**
```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    metadata TEXT,
    importance REAL DEFAULT 1.0
);
CREATE INDEX idx_type_time ON memories(memory_type, timestamp);
```

**RedisStorage:**
- TTL based on importance (up to 1 week)
- Key format: `memory:{type}:{id}`
- Optional Redis dependency

---

## 6. Safety Guardrails

### 6.1 Safety Pipeline (`safety/pipeline.py`)

**4-Layer Protection:**

1. **Output Guardrails** - Pattern-based hallucination detection
2. **Output Validator** - Schema and format validation
3. **Fact Checker** - CVE, port, version verification
4. **Confidence Scorer** - Overall confidence calculation

### 6.2 Output Guardrails (`safety/guardrails.py`)

**Safety Levels:**
```python
PERMISSIVE = "permissive"    # Development/testing
STANDARD = "standard"        # Default production
STRICT = "strict"            # High-stakes operations
PARANOID = "paranoid"        # Critical security contexts
```

**Hallucination Patterns:**
| Category | Examples | Penalty |
|----------|----------|---------|
| Uncertainty | maybe, perhaps, I think, probably | 0.2 each |
| Fabrication | I remember, I recall, typically | 0.3 each |
| Over-confidence | definitely, absolutely, 100% | 0.25 |
| Vague refs | some, certain, various | 0.15 each |

**Security Falsehoods (Always Flagged):**
- "impossible to exploit"
- "completely secure"
- "no vulnerability"
- "100% safe"
- "unhackable"

### 6.3 Fact Checker (`safety/fact_checker.py`)

**Verifiable Claims:**
| Type | Pattern | Source |
|------|---------|--------|
| CVE | `CVE-\d{4}-\d{4,}` | CVE database |
| Port | `port \d{1,5} is (open\|closed\|filtered)` | Scan results |
| Version | `(Apache\|Nginx\|OpenSSH)[/\s]+\d+\.\d+` | Service detection |
| Severity | `(critical\|high\|medium\|low)` severity | Standard levels |

**Verification Status:**
```python
VERIFIED = "verified"        # Confirmed against source
CONTRADICTED = "contradicted" # Conflicts with known data
UNKNOWN = "unknown"          # No source to verify
PARTIAL = "partial"          # Partially verified
```

### 6.4 Confidence Scoring (`safety/confidence.py`)

```python
weights = {
    "guardrails": 0.25,
    "validation": 0.25,
    "fact_check": 0.30,
    "consistency": 0.20,
}
```

**Confidence Levels:**
| Score | Level | Action |
|-------|-------|--------|
| ≥ 0.9 | High | Accept |
| 0.7 - 0.9 | Medium | Accept with monitoring |
| 0.5 - 0.7 | Low | Alert, consider retry |
| < 0.5 | Critical | Reject, regenerate |

### 6.5 Self-Correction (`safety/self_correction.py`)

**Auto-Correction Rules:**
1. Apply factual corrections from fact checker
2. Remove uncertainty language (maybe → "")
3. Replace weak terms (probably → likely)
4. Remove absolute security claims

**Retry Prompt Generation:**
```python
def generate_retry_prompt(original, issues, confidence_breakdown):
    # Adds specific guidance based on failure mode
    # E.g., "Be more specific and avoid uncertainty language"
```

---

## 7. AI/LLM Integration Patterns

### 7.1 LLM Client Abstraction

**KIAnalyzer** (`autonomous/ki_analysis_agent.py`):
```python
class KIAnalyzer:
    def __init__(self, model: str = "kimi"):
        self.model = model
    
    async def analyze(prompt: str, context: str = "", max_tokens: int = 2000) -> str:
        # Uses kimi-cli subprocess
        # Fallback analysis if CLI unavailable
```

### 7.2 Prompt Engineering Patterns

**ReAct Prompt Template:**
```
Goal: {goal}
Current Context: {context}
Execution History: {history}
Step {n}: What is your assessment?
Provide your reasoning:
```

**Action Decision Prompt:**
```
Based on reasoning: "{thought}"
Available Tools: {tools}
Decide on next action in JSON format:
{
    "action_type": "TOOL_CALL|SEARCH_MEMORY|...",
    "tool_name": "...",
    "parameters": {},
    "reasoning": "..."
}
```

### 7.3 LLM Response Parsing

**JSON Extraction:**
```python
json_start = response.find("{")
json_end = response.rfind("}") + 1
if json_start >= 0 and json_end > json_start:
    decision = json.loads(response[json_start:json_end])
```

**Pattern-Based Parsing:**
```python
if "THOUGHT:" in response:
    thought = response.split("THOUGHT:")[1].split("\n")[0].strip()
if "ACTION:" in response:
    action = response.split("ACTION:")[1].split("\n")[0].strip()
```

### 7.4 Multi-LLM Voting (`risk_engine/false_positive_engine.py`)

```python
class LLMVotingEngine:
    def register_llm(name: str, client: Any)
    async def vote_on_finding(finding: Finding) -> Tuple[Dict[str, bool], float]:
        # Parallel LLM queries
        # Consensus calculation
        # Confidence based on agreement
```

---

## 8. Potential Issues and Improvements

### 8.1 Critical Issues

| Issue | Severity | Location | Recommendation |
|-------|----------|----------|----------------|
| Command Injection Risk | **HIGH** | `tool_executor.py:395` | Use list-based subprocess instead of shell |
| Docker Privilege Escalation | **HIGH** | `exploit_validator.py:852` | Validate container images, use non-root |
| No Input Validation on URLs | **MEDIUM** | Multiple | Implement URL parsing and whitelist validation |
| Hardcoded Credentials | **MEDIUM** | None found | Continue monitoring |

### 8.2 Security Improvements

1. **Command Execution Security**
   ```python
   # Current (vulnerable to injection):
   await asyncio.create_subprocess_shell(command)
   
   # Recommended:
   await asyncio.create_subprocess_exec(cmd, *args)
   ```

2. **Scope Validation Enhancement**
   - Implement CIDR range validation
   - Add DNS resolution validation
   - Block internal AWS metadata IPs

3. **Rate Limiting**
   - Per-target rate limiting implemented
   - Consider global rate limiting
   - Add exponential backoff for failures

### 8.3 Architecture Improvements

| Area | Current | Recommended |
|------|---------|-------------|
| Embeddings | Simple hash (128-dim) | Real embeddings (OpenAI/HF) |
| Vector DB | In-memory dict | ChromaDB/Pinecone |
| LLM Integration | Subprocess CLI | API client with retry logic |
| Storage | SQLite/Redis | PostgreSQL for production |
| Async | Basic asyncio | Structured with asyncio.Queue |

### 8.4 Performance Optimizations

1. **Caching**
   - EPSS scores cached (24h) ✓
   - Add CVE database caching
   - Add tool output caching

2. **Parallelization**
   - ExploitValidatorPool with semaphore ✓
   - Add parallel tool execution
   - Batch processing for findings

3. **Database**
   - Add connection pooling
   - Implement query optimization
   - Add indexes for common queries

### 8.5 Testing Gaps

- Unit tests for ReAct loop edge cases
- Integration tests for tool execution
- Security tests for sandboxing
- Performance tests for large-scale scanning

---

## 9. Code Quality Assessment

### 9.1 Strengths

✅ **Good Documentation**
- Comprehensive docstrings
- Usage examples in all modules
- Clear type hints

✅ **Modular Design**
- Clear separation of concerns
- Abstract base classes for extensibility
- Plugin architecture for tools

✅ **Error Handling**
- Try-catch blocks with logging
- Graceful fallbacks for missing dependencies
- Timeout handling for subprocesses

✅ **Configuration Management**
- Centralized configs
- Environment-specific settings
- Safety level configurations

### 9.2 Weaknesses

⚠️ **Inconsistent Language**
- Mix of German and English in comments/docstrings
- Some files use German variable names

⚠️ **Code Duplication**
- CVSS calculation in `risk/` and `risk_engine/`
- Memory implementations in `autonomous/` and `memory/`

⚠️ **Incomplete Implementations**
- Vector embeddings are simplified
- LLM integration uses subprocess (fragile)
- Some TODOs in evidence capture

⚠️ **Missing Tests**
- No visible test files in analyzed directories
- Test directories exist but not analyzed

---

## 10. Summary Statistics

### File Count by Directory
| Directory | Python Files | Lines of Code (est.) |
|-----------|-------------|---------------------|
| `autonomous/` | 8 | ~4,500 |
| `risk_engine/` | 8 | ~2,800 |
| `risk/` | 7 | ~1,500 |
| `memory/` | 8 | ~800 |
| `safety/` | 9 | ~1,200 |
| **Total** | **40** | **~10,800** |

### Key Components Summary
| Component | Implementation Quality | Security | Extensibility |
|-----------|----------------------|----------|---------------|
| ReAct Loop | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Tool Executor | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| Risk Scoring | ⭐⭐⭐⭐⭐ | N/A | ⭐⭐⭐⭐ |
| False Positive Engine | ⭐⭐⭐⭐⭐ | N/A | ⭐⭐⭐⭐⭐ |
| Memory System | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Safety Guardrails | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 11. Recommendations

### High Priority
1. Fix command injection vulnerability in tool execution
2. Implement proper vector embeddings
3. Add comprehensive test suite
4. Consolidate duplicate code (risk vs risk_engine)

### Medium Priority
5. Add API-based LLM integration
6. Implement proper database backend
7. Add metrics and monitoring
8. Create deployment documentation

### Low Priority
9. Standardize language (English)
10. Add more tool integrations
11. Implement distributed scanning
12. Create web UI for results

---

*Analysis generated on: 2026-02-09*
*Analyzed files: 40 Python modules*
*Total lines analyzed: ~10,800*
