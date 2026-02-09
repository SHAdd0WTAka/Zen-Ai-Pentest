# Prompt Engineering Guide - Zen AI Pentest

This document outlines the universal prompt engineering techniques integrated into Zen AI Pentest, derived from the original system prompt research.

## 🎯 Core Prompt Engineering Principles

### 1. Multi-Context Prompting

The system uses layered prompts that combine technical context with AI reasoning:

```python
# Example from recon.py
prompt = f"""
Analyze this target for penetration testing:
Target: {target}
IP: {target_info['ip']}
DNS Records: {target_info['dns_records']}

Provide a structured reconnaissance plan including:
1. Potential attack vectors
2. Suggested tools (nmap, gobuster, etc.)
3. Likely vulnerabilities based on common patterns
4. OSINT sources to check
"""
```

**Key Elements:**
- Structured data input
- Specific output format requirements
- Numbered deliverables
- Context-aware analysis

### 2. Chain-of-Thought Prompting

For complex security analysis, prompts are designed to guide the LLM through reasoning steps:

```python
# Example from vuln_scanner.py
prompt = f"""
Analyze this nmap scan output and identify vulnerabilities:

```
{nmap_output}
```

For each vulnerability found, provide:
1. Name
2. Severity (Critical/High/Medium/Low/Info)
3. Description
4. Evidence from scan
5. Remediation steps
6. CVE IDs if applicable

Format each finding as:
[VULN]
Name: <name>
Severity: <severity>
...
[/VULN]
"""
```

### 3. Role-Based Prompting

Different modules use role-specific prompts:

```python
# From openrouter.py - Security Expert Role
system_message = "You are a cybersecurity expert and penetration testing assistant."

# From exploit_assist.py - Educational Context
prompt = """
For educational and authorized penetration testing purposes only.
Provide detection methods for defenders...
"""
```

### 4. Few-Shot Prompting

Examples embedded in prompts guide output format:

```python
# SQL Injection Database examples
payloads = {
    "detection": "' OR 1=1--",
    "extraction": "UNION SELECT password FROM users--"
}
```

### 5. Constrained Output Prompting

Strict format requirements for machine parsing:

```python
# Standardized formats used throughout:
[VULN]...[/VULN]       # Vulnerability blocks
[EXPLOIT]...[/EXPLOIT] # Exploit suggestions
- Item 1               # Bullet lists
1. Step one           # Numbered steps
```

## 🔧 Universal Prompt Patterns

### Pattern 1: Context + Task + Format

```python
def generate_prompt(context_data, task, output_format):
    return f"""
Context:
{context_data}

Task:
{task}

Output Format:
{output_format}
"""
```

**Used in:**
- `recon.py` - Target analysis
- `vuln_scanner.py` - Nmap analysis
- `report_gen.py` - Report generation

### Pattern 2: Hierarchical Analysis

```python
prompt = """
Analyze {target} for {purpose}:

1. High-level assessment
2. Detailed findings
3. Specific recommendations
4. Implementation steps
"""
```

**Used in:**
- Executive summary generation
- Remediation roadmaps
- Compliance mapping

### Pattern 3: Comparative Analysis

```python
prompt = """
Compare {option_a} vs {option_b}:
- Pros/Cons
- Risk assessment
- Resource requirements
- Recommended choice
"""
```

**Used in:**
- Multi-LLM consensus mode
- Exploit technique comparison
- Tool selection

### Pattern 4: Progressive Disclosure

```python
prompt = """
Basic analysis: {summary}

If {condition}:
  - Provide detailed technical info
Else:
  - Suggest next steps
"""
```

**Used in:**
- Quality-based routing (LOW/MEDIUM/HIGH)
- Fallback mechanisms
- Error handling

## 🛡️ Security-Specific Prompt Engineering

### Responsible Disclosure Prompts

```python
# From exploit_assist.py
RESPONSIBLE_DISCLOSURE = """
FOR AUTHORIZED SECURITY TESTING ONLY

Requirements:
- Safe for testing (non-destructive)
- Clearly demonstrates vulnerability
- Includes detection method
- Explains mitigation

DO NOT generate payloads for malicious use.
"""
```

### IOC Analysis Prompts

```python
# From cve_database.py
IOC_ANALYSIS = """
Analyze these system indicators:
{indicators}

Match against known ransomware IOCs:
- File paths
- Registry keys
- Process names
- Network signatures

Provide:
1. Match confidence score
2. Matched ransomware family
3. Recommended actions
"""
```

## 🔄 Multi-LLM Optimization

### Quality-Based Routing

```python
class QualityLevel(Enum):
    LOW = "low"      # Quick queries, minimal context
    MEDIUM = "medium" # Standard analysis
    HIGH = "high"    # Complex reasoning

# Prompt adaptation based on quality:
if quality == QualityLevel.LOW:
    prompt = "Brief answer: {question}"
elif quality == QualityLevel.HIGH:
    prompt = "Detailed analysis with reasoning: {question}"
```

### Backend-Specific Optimization

```python
# DuckDuckGo - Simple, direct prompts
DDG_PROMPT = "Answer concisely: {query}"

# OpenRouter - Structured prompts  
OR_PROMPT = """
System: You are a security expert
User: {query}
Provide structured JSON response.
"""

# Direct APIs - Complex reasoning
DIRECT_PROMPT = """
Context: {full_context}
Task: {complex_task}
Think step by step...
"""
```

## 📊 Prompt Effectiveness Metrics

### Response Quality Indicators

1. **Structured Output Compliance**
   - Parse success rate
   - Format adherence
   - Data completeness

2. **Relevance Scoring**
   - Keyword matching
   - Context relevance
   - Actionability

3. **Latency Optimization**
   - Prompt length vs response time
   - Backend selection impact
   - Caching effectiveness

## 🎓 Best Practices Implemented

### 1. Prompt Templates

All prompts use consistent templates:

```python
TEMPLATE = """
{header}
{context}

{task}

{format_requirements}

{constraints}
"""
```

### 2. Dynamic Context Injection

```python
# Runtime context updates
context = {
    "target": target,
    "findings": findings,
    "history": previous_results
}
prompt = template.format(**context)
```

### 3. Error Recovery Prompts

```python
# When parsing fails
RECOVERY_PROMPT = """
Previous response could not be parsed.
Original request: {original}

Please reformat following this exact structure:
{structure}
"""
```

## 🔬 Research-Based Techniques

### From Original Conversation Analysis

1. **Multi-Agent Consensus**: Parallel querying with cross-validation
2. **Progressive Enhancement**: Starting simple, adding complexity
3. **Feedback Loops**: Using previous outputs to refine prompts
4. **Context Window Management**: Truncating while preserving meaning

### Implemented Patterns

```python
# Parallel consensus (from conversation)
async def parallel_consensus(prompt):
    tasks = [backend.chat(prompt) for backend in backends[:2]]
    results = await asyncio.gather(*tasks)
    return cross_validate(results)

# Progressive enhancement
async def progressive_analysis(target):
    # Phase 1: Quick recon (LOW quality)
    overview = await process(target, QualityLevel.LOW)
    
    # Phase 2: Deep analysis (HIGH quality)
    if has_interesting_findings(overview):
        detailed = await process(target, QualityLevel.HIGH)
```

## 📚 Prompt Library

### Reconnaissance Prompts

```python
RECON_BASIC = """
Analyze {target} for penetration testing:
- IP: {ip}
- DNS: {dns}

Provide attack vectors and tool suggestions.
"""

RECON_ADVANCED = """
Deep reconnaissance analysis of {target}:
1. Technology fingerprinting
2. Service enumeration
3. Potential vulnerabilities
4. Recommended exploitation path
"""
```

### Vulnerability Analysis Prompts

```python
VULN_BASIC = """
Identify vulnerabilities in:
{scan_output}

List findings with severity.
"""

VULN_DETAILED = """
Comprehensive vulnerability analysis:
1. CVE identification
2. CVSS scoring
3. Exploitability assessment
4. Remediation roadmap
5. Compensating controls
"""
```

### Report Generation Prompts

```python
EXEC_SUMMARY = """
Generate executive summary for C-level:
- Total findings: {count}
- Critical: {critical}
- High: {high}

Focus on business impact and priorities.
Length: 300-500 words
"""

TECHNICAL_REPORT = """
Technical findings report for security team:
{findings}

Include:
1. Detailed descriptions
2. Evidence
3. Reproduction steps
4. Remediation code
"""
```

## 🔮 Future Enhancements

### Planned Improvements

1. **Adaptive Prompts**: Self-optimizing based on success rates
2. **Multi-Language Support**: Localized prompts for global teams
3. **Voice Interface**: Conversational prompt engineering
4. **Visual Analysis**: Image-based vulnerability assessment

### Research Directions

- Chain-of-Verification for security claims
- Constitutional AI for ethical constraints
- Toolformer integration for automated tool usage
- RAG (Retrieval-Augmented Generation) for CVE data

---

**Note**: This prompt engineering approach is based on the universal principles discussed in the original system prompt research, adapted specifically for penetration testing workflows.

**Author**: SHAdd0WTAka  
**Version**: 1.0.0
