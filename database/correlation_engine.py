"""
ReNgine-inspired correlation engine for pentest findings.

Groups, deduplicates, scores, and correlates findings across hosts,
links them to Asset records, and produces structured correlation reports.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("ZenAI.Correlation")

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
SEVERITY_LABELS = ("critical", "high", "medium", "low", "info")


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class CorrelatedGroup:
    """A group of deduplicated/correlated findings sharing a common key."""

    key: str
    findings: List[Dict[str, Any]] = field(default_factory=list)
    max_severity: str = "info"
    max_cvss: float = 0.0
    hosts_affected: int = 0
    is_widespread: bool = False


@dataclass
class CorrelationResult:
    """Top-level result produced by the correlation engine."""

    original_findings_count: int = 0
    correlated_count: int = 0
    groups: List[CorrelatedGroup] = field(default_factory=list)
    widespread: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _severity_rank(sev: str) -> int:
    return SEVERITY_ORDER.get(sev.strip().lower(), -1)


def _to_dict(finding: Any) -> Dict[str, Any]:
    """Normalise a Finding ORM object or raw dict into a plain dict."""
    if isinstance(finding, dict):
        return finding
    try:
        return {
            "id": finding.id,
            "scan_id": finding.scan_id,
            "title": finding.title,
            "description": finding.description,
            "severity": finding.severity,
            "cvss_score": finding.cvss_score,
            "cve_id": finding.cve_id,
            "evidence": finding.evidence,
            "remediation": finding.remediation,
            "tool": finding.tool,
            "target": finding.target,
            "port": finding.port,
            "service": finding.service,
            "created_at": str(finding.created_at) if finding.created_at else None,
            "verified": finding.verified,
        }
    except AttributeError:
        raise TypeError("Unsupported finding type — expected dict or ORM object.")


def _any_field_matches(finding: Dict[str, Any], field_names: List[str], value: str) -> bool:
    """Return True if *any* of the given fields on *finding* equals *value*."""
    value_lower = value.strip().lower()
    for name in field_names:
        raw = finding.get(name)
        if raw and str(raw).strip().lower() == value_lower:
            return True
    return False


def _max_cvss_in(items: List[Dict[str, Any]]) -> float:
    scores = [f.get("cvss_score") or 0.0 for f in items]
    return max(scores)


def _list_hosts(items: List[Dict[str, Any]]) -> List[str]:
    seen: set = set()
    hosts: List[str] = []
    for f in items:
        h = f.get("target")
        if h and h not in seen:
            seen.add(h)
            hosts.append(h)
    return hosts


def _dedup_key(finding: Dict[str, Any]) -> str:
    """Produce a deterministic deduplication key for a finding.

    Priority:
      1. CVE identifier (if present) → returns the CVE string.
      2. SHA-256 of ``host:port:service:vulnerability_name``.
    """
    cve = (finding.get("cve_id") or "").strip()
    if cve:
        return cve.upper()

    host = finding.get("target") or ""
    port = str(finding.get("port") or "")
    service = (finding.get("service") or "").strip()
    vuln = (finding.get("title") or "").strip()
    raw = f"{host}:{port}:{service}:{vuln}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# CorrelationEngine
# ---------------------------------------------------------------------------


class CorrelationEngine:
    """ReNgine-inspired engine that deduplicates, correlates and scores
    pentest findings, and links them to Asset records."""

    def __init__(self, db_session=None):
        self.db = db_session
        self.logger = logger

    # ---- public API -------------------------------------------------------

    def correlate_findings(self, scan_id: int) -> CorrelationResult:
        """Retrieve all findings for *scan_id*, group them by dedup key,
        and return a ``CorrelationResult`` with deduplicated groups,
        severity counts, and widespread-vulnerability markers."""
        if self.db is None:
            self.logger.warning("No DB session available — using empty findings.")
            return CorrelationResult()

        from database.models import get_findings

        raw = get_findings(self.db, scan_id)
        findings = [_to_dict(f) for f in raw]
        result = self._correlate_findings_internal(findings)
        self.logger.info(
            "Correlated scan %d: %d findings → %d groups (risk=%.1f)",
            scan_id,
            result.original_findings_count,
            result.correlated_count,
            result.risk_score,
        )
        return result

    def correlate_findings_in_memory(self, findings: List[Dict[str, Any]]) -> CorrelationResult:
        """Correlate an already-loaded list of finding dicts (no DB call)."""
        return self._correlate_findings_internal([_to_dict(f) for f in findings])

    def link_to_assets(self, scan_id: int) -> Dict[str, Any]:
        """Match findings for *scan_id* against Asset records and return a
        mapping of ``{asset_label: [finding_dict, ...]}``."""
        if self.db is None:
            return {}

        from database.models import Asset, get_findings

        assets = self.db.query(Asset).all()
        raw = get_findings(self.db, scan_id)
        findings = [_to_dict(f) for f in raw]

        mapping: Dict[str, List[Dict[str, Any]]] = {}
        for asset in assets:
            candidates: List[Dict[str, Any]] = []
            ip = (asset.ip_address or "").strip()
            hostname = (asset.hostname or "").strip()
            for fd in findings:
                tgt = (fd.get("target") or "").strip()
                if not tgt:
                    continue
                if tgt == ip or tgt == hostname:
                    candidates.append(fd)
            label = asset.name or asset.hostname or asset.ip_address or f"asset-{asset.id}"
            if candidates:
                mapping[label] = candidates

        self.logger.info("Linked %d assets for scan %d", len(mapping), scan_id)
        return mapping

    def calculate_risk_score(self, scan_id: int) -> float:
        """Compute a risk score (0‑10) for the given scan based on correlated
        findings.  See ``_compute_risk_score`` for the formula."""
        result = self.correlate_findings(scan_id)
        return result.risk_score

    def generate_correlation_report(self, scan_id: int) -> str:
        """Produce a human-readable Markdown summary of the correlation."""
        result = self.correlate_findings(scan_id)
        return self._format_report(scan_id, result)

    def write_correlation_metadata(self, scan_id: int, result: CorrelationResult = None) -> bool:
        """Persist correlation results into the Scan's ``correlation_metadata``
        JSON column if the column exists.  Returns ``True`` on success."""
        if self.db is None:
            return False

        from database.models import get_scan

        scan = get_scan(self.db, scan_id)
        if scan is None:
            self.logger.warning("Scan %d not found — cannot write metadata.", scan_id)
            return False

        if result is None:
            result = self._correlate_findings_internal([_to_dict(f) for f in scan.findings.all()])

        payload = {
            "correlated_at": datetime.now(timezone.utc).isoformat(),
            "original_findings_count": result.original_findings_count,
            "correlated_count": result.correlated_count,
            "risk_score": result.risk_score,
            "severity_breakdown": {
                "critical": result.critical_count,
                "high": result.high_count,
                "medium": result.medium_count,
                "low": result.low_count,
                "info": result.info_count,
            },
            "widespread": list(result.widespread),
            "groups": [
                {
                    "key": g.key,
                    "max_severity": g.max_severity,
                    "max_cvss": g.max_cvss,
                    "hosts_affected": g.hosts_affected,
                    "is_widespread": g.is_widespread,
                    "finding_ids": [fd.get("id") for fd in g.findings if fd.get("id")],
                }
                for g in result.groups
            ],
        }

        try:
            scan.correlation_metadata = payload
            self.db.commit()
            self.logger.info("Wrote correlation metadata for scan %d", scan_id)
            return True
        except (AttributeError, Exception) as exc:
            self.logger.warning("Could not write correlation_metadata (column may not exist): %s", exc)
            self.db.rollback()
            return False

    # ---- internal logic ---------------------------------------------------

    def _correlate_findings_internal(self, findings: List[Dict[str, Any]]) -> CorrelationResult:
        """Core dedup-and-group logic (shared by public methods).

        Widespread detection works as follows:
          - For CVE-keyed groups: if the same CVE appears on ≥3 hosts,
            the group is marked as widespread.
          - For non-CVE findings: vulnerability *titles* are compared
            across groups.  If the same title appears on ≥3 distinct
            hosts, **all** groups sharing that title are marked as
            widespread.
        """
        result = CorrelationResult()
        result.original_findings_count = len(findings)

        if not findings:
            return result

        # 1. group by dedup key
        buckets: Dict[str, List[Dict[str, Any]]] = {}
        for fd in findings:
            key = _dedup_key(fd)
            buckets.setdefault(key, []).append(fd)

        groups: List[CorrelatedGroup] = []
        for key, bucket in buckets.items():
            group = CorrelatedGroup(key=key, findings=bucket)
            group.max_cvss = _max_cvss_in(bucket)
            severities = [fd.get("severity", "info") for fd in bucket]
            group.max_severity = _max_severity_among(severities)
            hosts = _list_hosts(bucket)
            group.hosts_affected = len(hosts)
            groups.append(group)

        # 2. widespread detection — two passes

        # 2a. CVE-keyed groups: widespread if same CVE on ≥3 hosts
        cve_widespread: set = set()
        for g in groups:
            if g.key.startswith("CVE-") and g.hosts_affected >= 3:
                g.is_widespread = True
                cve_widespread.add(g.key)

        # 2b. Non-CVE groups: same title on ≥3 hosts → mark all such groups
        title_host_map: Dict[str, set] = {}
        title_to_groups: Dict[str, List[CorrelatedGroup]] = {}
        for g in groups:
            if g.key.startswith("CVE-"):
                continue
            title = g.findings[0].get("title", "") if g.findings else ""
            if not title:
                continue
            title_to_groups.setdefault(title, []).append(g)
            for h in _list_hosts(g.findings):
                title_host_map.setdefault(title, set()).add(h)

        non_cve_widespread: set = set()
        for title, hosts in title_host_map.items():
            if len(hosts) >= 3:
                for g in title_to_groups.get(title, []):
                    g.is_widespread = True
                    g.hosts_affected = len(hosts)
                non_cve_widespread.add(title)

        widespread_vulns = sorted(cve_widespread | non_cve_widespread)

        # 3. aggregate severity counts
        all_sevs = [fd.get("severity", "info") for fd in findings]
        for label in SEVERITY_LABELS:
            setattr(result, f"{label}_count", _count_severities(all_sevs, label))

        # 4. risk score
        result.risk_score = self._compute_risk_score(
            all_sevs,
            len(groups),
            max((b.max_cvss for b in groups), default=0.0),
            len(widespread_vulns),
        )

        result.groups = groups
        result.correlated_count = len(groups)
        result.widespread = widespread_vulns
        return result

    @staticmethod
    def _compute_risk_score(
        severities: List[str],
        group_count: int,
        max_cvss: float,
        widespread_count: int,
    ) -> float:
        """Weighted risk score in the range [0.0, 10.0].

        Formula
        -------
        *base* = highest CVSS in any finding (or 5.0 if none recorded)
        +1.0  if any critical-severity finding exists
        +0.5  if any type (dedup group) has ≥5 individual findings
        +1.0  if ≥3 distinct hosts are affected (widespread)
        """
        base = max_cvss if max_cvss > 0.0 else 5.0
        score = base

        if any(s.lower() == "critical" for s in severities):
            score += 1.0

        if group_count >= 5:
            score += 0.5

        if widespread_count > 0:
            score += 1.0

        return round(min(score, 10.0), 1)

    @staticmethod
    def _format_report(scan_id: int, result: CorrelationResult) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            f"# Correlation Report — Scan #{scan_id}",
            f"**Generated:** {now}  ",
            "",
            "## Summary",
            "",
            f"- Original findings: **{result.original_findings_count}**",
            f"- Correlated groups: **{result.correlated_count}**",
            f"- Risk score: **{result.risk_score}/10**",
            f"- Widespread vulnerabilities (≥3 hosts): **{len(result.widespread)}**",
            "",
            "### Severity Breakdown",
            "",
            "| Severity | Count |",
            "|----------|-------|",
            f"| Critical | {result.critical_count} |",
            f"| High     | {result.high_count} |",
            f"| Medium   | {result.medium_count} |",
            f"| Low      | {result.low_count} |",
            f"| Info     | {result.info_count} |",
            "",
            "---",
            "",
            "## Correlated Groups",
            "",
        ]

        wids = set(result.widespread)
        for i, g in enumerate(result.groups, 1):
            tag = " ⚠ WIDESPREAD" if g.is_widespread else ""
            lines.append(f"### {i}. `{g.key}`{tag}")
            lines.append("")
            lines.append(f"- Max severity: **{g.max_severity.upper()}**")
            lines.append(f"- Max CVSS: **{g.max_cvss}**")
            lines.append(f"- Hosts affected: **{g.hosts_affected}**")
            lines.append(f"- Findings in group: **{len(g.findings)}**")
            lines.append("")

            if g.is_widespread:
                hosts_str = ", ".join(sorted(_list_hosts(g.findings)))
                lines.append(f"  _Present on hosts: {hosts_str}_")
                lines.append("")

        if result.widespread:
            lines.append("---")
            lines.append("")
            lines.append("## Widespread Vulnerabilities")
            lines.append("")
            for wid in sorted(result.widespread):
                lines.append(f"- `{wid}`")

        lines.append("")
        lines.append("---")
        lines.append(f"*Report auto-generated by ZenAI Correlation Engine at {now}*")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module-level convenience helpers (for use outside the class)
# ---------------------------------------------------------------------------


def max_severity(severities: List[str]) -> str:
    """Return the highest-severity label from a list of severity strings."""
    return _max_severity_among(severities)


def severity_score(severity: str) -> int:
    """Map a severity label to an integer rank (4 = critical … 0 = info)."""
    return _severity_rank(severity)


# ---------------------------------------------------------------------------
# Internal helpers (shared)
# ---------------------------------------------------------------------------


def _max_severity_among(severities: List[str]) -> str:
    best = "info"
    best_rank = -1
    for s in severities:
        r = _severity_rank(s)
        if r > best_rank:
            best_rank = r
            best = s
    return best


def _count_severities(severities: List[str], target: str) -> int:
    return sum(1 for s in severities if s.strip().lower() == target.lower())


# ---------------------------------------------------------------------------
# Demo / smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s",
    )

    logger.info("=" * 72)
    logger.info("  Correlation Engine — Demo  (in-memory, no DB required)")
    logger.info("=" * 72)

    def _mkf(id_, title, severity, cvss, cve, target, port, service, tool):
        return {
            "id": id_,
            "scan_id": 42,
            "title": title,
            "description": "",
            "severity": severity,
            "cvss_score": cvss,
            "cve_id": cve,
            "target": target,
            "port": port,
            "service": service,
            "tool": tool,
        }

    demo_findings: List[Dict[str, Any]] = [
        # CVE dedup — two scanners report same CVE
        _mkf(1, "Apache Struts RCE", "critical", 9.8, "CVE-2024-1234", "10.0.0.1", 8080, "http", "nmap"),
        _mkf(2, "Apache Struts RCE", "critical", 9.8, "CVE-2024-1234", "10.0.0.1", 8080, "http", "nikto"),
        # Non-CVE dedup on same host:port:service
        _mkf(3, "Weak SSL Cipher", "medium", 5.0, "", "10.0.0.1", 443, "https", "sslscan"),
        _mkf(4, "Weak SSL Cipher", "medium", 5.0, "", "10.0.0.1", 443, "https", "testssl"),
        # Widespread across 4 hosts
        _mkf(5, "OpenSSH Banner Grab", "low", 2.5, "", "10.0.0.1", 22, "ssh", "nmap"),
        _mkf(6, "OpenSSH Banner Grab", "low", 2.5, "", "10.0.0.2", 22, "ssh", "nmap"),
        _mkf(7, "OpenSSH Banner Grab", "low", 2.5, "", "10.0.0.3", 22, "ssh", "nmap"),
        # Standalone high
        _mkf(8, "SQL Injection", "high", 7.5, "CVE-2024-5678", "10.0.0.4", 443, "https", "sqlmap"),
        # 4th host for widespread
        _mkf(9, "OpenSSH Banner Grab", "low", 2.5, "", "10.0.0.5", 22, "ssh", "nmap"),
    ]

    engine = CorrelationEngine()
    result = engine.correlate_findings_in_memory(demo_findings)

    logger.info(
        "Original: %d → Correlated: %d | Risk: %s/10 | Widespread: %s",
        result.original_findings_count,
        result.correlated_count,
        result.risk_score,
        result.widespread,
    )
    logger.info(
        "Severity: critical=%d high=%d medium=%d low=%d info=%d",
        result.critical_count,
        result.high_count,
        result.medium_count,
        result.low_count,
        result.info_count,
    )

    for g in result.groups:
        tag = " [WIDESPREAD]" if g.is_widespread else ""
        logger.info(
            "  [%8s] %s%s  CVSS=%s hosts=%d findings=%d",
            g.max_severity.upper(),
            g.key,
            tag,
            g.max_cvss,
            g.hosts_affected,
            len(g.findings),
        )

    logger.info("\n%s", engine._format_report(42, result))
