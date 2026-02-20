# Technical Penetration Testing Report

## Assessment Information

- **Client:** {{ client_name }}
- **Project:** {{ project_name }}
- **Assessment Type:** {{ assessment_type }}
- **Start Date:** {{ start_date }}
- **End Date:** {{ end_date }}
- **Assessors:** {{ assessors }}
- **Scope:** {{ scope_description }}

---

## Methodology

This assessment followed the Penetration Testing Execution Standard (PTES):

1. **Pre-engagement Interactions**
2. **Intelligence Gathering**
3. **Threat Modeling**
4. **Vulnerability Analysis**
5. **Exploitation**
6. **Post Exploitation**
7. **Reporting**

---

## Findings

{{ findings_details }}

### Vulnerability Details

{% for finding in findings %}
#### {{ finding.title }}

| Field | Value |
|-------|-------|
| **Severity** | {{ finding.severity }} |
| **CVSS Score** | {{ finding.cvss_score }} |
| **Affected Host** | {{ finding.host }} |
| **Port/Service** | {{ finding.port }} |
| **Status** | {{ finding.status }} |

**Description:**
{{ finding.description }}

**Evidence:**
```
{{ finding.evidence }}
```

**Remediation:**
{{ finding.remediation }}

**References:**
{{ finding.references }}

---

{% endfor %}

## Appendix

### A. Tools Used
{{ tools_used }}

### B. Testing Windows
{{ testing_windows }}

### C. Exclusions
{{ exclusions }}

### D. Limitations
{{ limitations }}

---

*Confidential - {{ client_name }}*
*Report Version: {{ report_version }}*
