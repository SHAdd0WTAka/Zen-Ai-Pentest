# End-to-End Demo 🎬

Complete demonstration of Zen-AI-Pentest showing all components working together.

---

## Quick Start

```bash
# Run the demo with default settings (scanme.nmap.org)
python demo_e2e.py

# Scan a specific target
python demo_e2e.py --target example.com

# Use different risk levels
python demo_e2e.py --risk-level 0  # SAFE (recon only)
python demo_e2e.py --risk-level 1  # NORMAL (scanning allowed)
python demo_e2e.py --risk-level 2  # ELEVATED (exploitation)
python demo_e2e.py --risk-level 3  # AGGRESSIVE (everything)
```

---

## What This Demo Shows

### 1️⃣ Workflow Orchestration
- Creates a pentest workflow with multiple steps
- Manages state transitions (PENDING → RUNNING → COMPLETED)
- Distributes tasks to agents

### 2️⃣ Security Guardrails
- Validates targets (blocks private IPs, localhost)
- Enforces risk levels (blocks tools based on level)
- Shows VPN recommendations

### 3️⃣ Agent Simulation
- Mock agent connects to orchestrator
- Receives tasks via WebSocket simulation
- Executes security tools (nmap, whois, dns)

### 4️⃣ Real Tool Execution
When available, executes **real** tools:
- `whois` - Domain registration info
- `dig` - DNS resolution
- `nmap` - Port scanning (if installed)

If tools aren't installed, falls back to simulation.

### 5️⃣ Report Generation
- Generates Markdown penetration test report
- Includes findings summary with severity levels
- Saves report to file

---

## Demo Output Example

```
======================================================================
🎯 ZEN-AI-PENTEST END-TO-END DEMO
======================================================================

📋 Step 1: Initializing Workflow Orchestrator
----------------------------------------------------------------------
✅ Orchestrator initialized (Risk Level: NORMAL)

🤖 Step 2: Creating Mock Agent
----------------------------------------------------------------------
✅ Agent demo-agent-1 connected

🚀 Step 3: Starting Workflow (Target: scanme.nmap.org)
----------------------------------------------------------------------
🛡️  Target 'scanme.nmap.org' passed guardrails validation
⚠️  WARNING: Scanning without VPN protection!
💡 Recommendation: Connect to ProtonVPN before scanning
✅ Workflow started: wf_abc123

⚙️  Step 4: Executing Tasks
----------------------------------------------------------------------
🔧 Agent demo-agent-1 executing: whois on scanme.nmap.org
✅ Task completed: success
🔧 Agent demo-agent-1 executing: dns on scanme.nmap.org
✅ Task completed: success
🔧 Agent demo-agent-1 executing: nmap on scanme.nmap.org
✅ Task completed: success
✅ Workflow completed with state: completed

📊 Step 5: Generating Report
----------------------------------------------------------------------
✅ Report saved to: pentest_report_wf_abc123_20240218_143022.md

======================================================================
📈 DEMO SUMMARY
======================================================================
Workflow ID:        wf_abc123
Target:             scanme.nmap.org
Final State:        completed
Completed Steps:    3
Tasks Completed:    5
Total Findings:     4
Report File:        pentest_report_wf_abc123_20240218_143022.md

🎯 Sample Findings:
   [INFO] WHOIS: scanme.nmap.org
   [MEDIUM] Open ports on scanme.nmap.org
   [HIGH] Potential security issue

======================================================================
✨ DEMO COMPLETED SUCCESSFULLY!
======================================================================
```

---

## Architecture Flow

```
┌─────────────────┐
│   User Input    │
│  (demo_e2e.py)  │
└────────┬────────┘
         ▼
┌─────────────────────┐
│ WorkflowOrchestrator│
│ ├─ Validate target  │
│ ├─ Check guardrails │
│ └─ Create workflow  │
└────────┬────────────┘
         ▼
┌─────────────────────┐
│   MockAgent         │
│ ├─ Connect          │
│ ├─ Receive tasks    │
│ └─ Execute tools    │
└────────┬────────────┘
         ▼
┌─────────────────────┐
│   Tool Execution    │
│ ├─ whois (real)     │
│ ├─ dig (real)       │
│ ├─ nmap (if avail)  │
│ └─ simulate (fallback)│
└────────┬────────────┘
         ▼
┌─────────────────────┐
│   ReportGenerator   │
│ └─ Markdown report  │
└─────────────────────┘
```

---

## Risk Levels Demo

### SAFE (Level 0)
```bash
python demo_e2e.py --risk-level 0
```
**Allows:** whois, dns, subdomain  
**Blocks:** nmap, nuclei, exploit

### NORMAL (Level 1) - DEFAULT
```bash
python demo_e2e.py --risk-level 1
```
**Allows:** + nmap, nuclei, web_enum  
**Blocks:** sqlmap, exploit

### ELEVATED (Level 2)
```bash
python demo_e2e.py --risk-level 2
```
**Allows:** + sqlmap, exploit  
**Blocks:** pivot, lateral

### AGGRESSIVE (Level 3)
```bash
python demo_e2e.py --risk-level 3
```
**Allows:** Everything including pivot, lateral

---

## Generated Report

The demo generates a Markdown report like this:

```markdown
# Penetration Test Report

## Executive Summary

**Target:** scanme.nmap.org  
**Workflow Type:** network_recon  
**Date:** 2024-02-18 14:30:22  
**Status:** completed

## Test Scope

- **Reconnaissance:** ✅
- **Scanning:** ✅
- **Enumeration:** ❌
- **Vulnerability Analysis:** ❌
- **Reporting:** ✅

## Agent Statistics

- **Agent ID:** demo-agent-1
- **Tasks Completed:** 5
- **Total Findings:** 4

## Findings Summary

| Severity | Count |
|----------|-------|
| 🔴 High | 1 |
| 🟠 Medium | 2 |
| 🟡 Low | 0 |
| 🔵 Info | 1 |

## Detailed Findings

### 1. WHOIS: scanme.nmap.org

**Severity:** 🔵 INFO  
**Type:** whois_info  
**Details:** Registrar: Example Registrar LLC

### 2. Open ports on scanme.nmap.org

**Severity:** 🟠 MEDIUM  
**Type:** open_ports  
**Details:** Ports: 22 (ssh), 80 (http)

---

## Conclusion

This automated penetration test was conducted using the Zen-AI-Pentest framework.
```

---

## Troubleshooting

### "nmap not installed"
Install nmap for real port scanning:
```bash
# Ubuntu/Debian
sudo apt install nmap

# macOS
brew install nmap

# Windows
choco install nmap
```

Demo works without nmap (uses simulation).

### "whois/dig not installed"
```bash
# Ubuntu/Debian
sudo apt install whois dnsutils

# macOS
brew install whois bind
```

### Workflow blocked by guardrails
Check that target is not:
- Private IP (192.168.x, 10.x, 172.16-31.x)
- Localhost
- Local domain (.local)

Use `scanme.nmap.org` for safe testing.

---

## Next Steps

After running the demo:

1. **View the report:**
   ```bash
   cat pentest_report_*.md
   ```

2. **Try different targets:**
   ```bash
   python demo_e2e.py --target your-authorized-target.com
   ```

3. **Test with VPN:**
   ```bash
   # Install and connect ProtonVPN
   pip install protonvpn-cli
   protonvpn-cli login
   protonvpn-cli connect
   
   # Run demo (no more VPN warning!)
   python demo_e2e.py
   ```

4. **Integrate into your workflow:**
   - Use `WorkflowOrchestrator` in your scripts
   - Connect real agents via WebSocket
   - Customize report templates

---

**Happy Testing! 🎯**
