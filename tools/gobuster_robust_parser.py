"""
Robuster Gobuster Parser mit Deduplizierung und Soft-404-Erkennung
Zukünftige Version - wird aktiviert sobald Smart-Test Rot zeigt
"""

import json
import os
import re
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional

from core.tool_executor import get_executor


@dataclass
class GobusterResult:
    """Ein einzelnes Scan-Ergebnis"""

    url: str
    status_code: int
    size: int
    redirect_location: Optional[str] = None
    is_soft_404: bool = False  # ← Wichtig für Deduplizierung
    fingerprint: str = ""  # ← Size-basierter Hash


class RobustGobusterScanner:
    """
    Gobuster-Scanner mit JSON-Parsing und Soft-404-Erkennung

    Features:
    - JSON-Output für strukturierte Daten
    - Size-Fingerprinting für Soft-404-Erkennung
    - Deduplizierung gleicher Fehlerseiten
    - Keine Abstürze bei komplexen Status-Texten
    """

    # Regex für ANSI-Codes (für Legacy-Fallback)
    ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="gobuster_")

    def scan(
        self,
        target: str,
        wordlist: str,
        extensions: Optional[List[str]] = None,
    ) -> List[GobusterResult]:
        """
        Führt Gobuster-Scan durch mit robustem Parsing
        """
        import uuid

        temp_json = f"{self.temp_dir}/gobuster_{uuid.uuid4().hex}.json"

        # Baue Kommando mit JSON-Output
        cmd = [
            "gobuster",
            "dir",
            "-u",
            target,
            "-w",
            wordlist,
            "-o",
            temp_json,
            "--format",
            "json",
            "--no-color",
            "-k",  # Skip SSL verification
        ]

        if extensions:
            cmd.extend(["-x", ",".join(extensions)])

        # Führe aus
        result = get_executor().execute_sync(cmd)

        if not result.success:
            return []  # Resilience: Nie crashen, leere Liste zurückgeben

        # Parse Ergebnisse
        return self._parse_results(temp_json)

    def _parse_results(self, json_path: str) -> List[GobusterResult]:
        """
        Parsed JSON-Output mit Deduplizierung
        """
        results = []

        try:
            # Lade JSON-Zeilen
            with open(json_path, "r") as f:
                for line in f:
                    if not line.strip():
                        continue

                    data = json.loads(line)

                    # Extrahiere Felder (robust gegen fehlende Keys)
                    url = data.get("Url", data.get("url", ""))
                    status = data.get("Status", data.get("status", 0))
                    size = data.get("Length", data.get("length", 0))

                    # Create fingerprint for deduplication
                    fingerprint = f"{status}_{size}"

                    results.append(
                        GobusterResult(
                            url=url,
                            status_code=int(status) if status else 0,
                            size=int(size) if size else 0,
                            fingerprint=fingerprint,
                        )
                    )

            # Deduplizierung: Identifiziere Soft-404s
            results = self._deduplicate_soft_404s(results)

            # Sortiere nach Relevanz (Status 200 zuerst, dann nach Size)
            results.sort(key=lambda r: (r.status_code != 200, -r.size))

            return results

        except (json.JSONDecodeError, FileNotFoundError, KeyError):
            # Resilience: Bei Parse-Fehler leere Liste
            return []
        finally:
            # Cleanup
            try:
                if os.path.exists(json_path):
                    os.remove(json_path)
            except Exception:
                pass

    def _deduplicate_soft_404s(self, results: List[GobusterResult]) -> List[GobusterResult]:
        """
        Erkennt Soft-404s durch Size-Fingerprinting

        Logik: Wenn mehrere Pfade dieselbe Size haben,
        ist das wahrscheinlich dieselbe Fehlerseite
        """
        # Zähle Size-Vorkommen
        size_counter: Dict[str, int] = defaultdict(int)
        for r in results:
            size_counter[r.fingerprint] += 1

        # Markiere Soft-404s
        for r in results:
            if size_counter[r.fingerprint] >= 3:
                # Wenn 3+ Pfade dieselbe Size haben → Soft-404
                r.is_soft_404 = True

        return results

    def get_interesting_findings(self, results: List[GobusterResult]) -> List[GobusterResult]:
        """
        Filtert auf wirklich interessante Ergebnisse

        Kriterien:
        - Status 200 mit Size > 0 (und nicht Soft-404)
        - Status 301/302 (Redirects zu anderen Seiten)
        - Status 403 (Geschützte Ressourcen)
        """
        interesting = []

        for r in results:
            # Ausschlusskriterien
            if r.is_soft_404:
                continue

            if r.size == 0:
                continue

            # Einschlusskriterien
            if r.status_code == 200:
                interesting.append(r)
            elif r.status_code in (301, 302, 307, 308):
                interesting.append(r)
            elif r.status_code == 403:
                interesting.append(r)
            elif r.status_code == 401:  # Auth required - sehr interessant
                interesting.append(r)

        return interesting

    def generate_summary(self, results: List[GobusterResult]) -> Dict:
        """
        Erstellt Zusammenfassung für den Agenten
        """
        total = len(results)
        soft_404s = sum(1 for r in results if r.is_soft_404)
        interesting = len(self.get_interesting_findings(results))

        # Status-Code-Verteilung
        status_counts = defaultdict(int)
        for r in results:
            status_counts[r.status_code] += 1

        return {
            "total_scanned": total,
            "interesting_findings": interesting,
            "soft_404s_detected": soft_404s,
            "status_distribution": dict(status_counts),
            "top_findings": [
                {"url": r.url, "status": r.status_code, "size": r.size} for r in self.get_interesting_findings(results)[:10]
            ],
        }


# Legacy-Fallback: Text-Parsing (falls JSON nicht verfügbar)
def parse_gobuster_text_legacy(stdout: str) -> List[GobusterResult]:
    """
    Robuster Text-Parser als Fallback
    Filtert ANSI-Codes und parsed mit Regex
    """
    results = []

    # Entferne ANSI-Codes
    clean = RobustGobusterScanner.ANSI_ESCAPE.sub("", stdout)

    # Pattern: URL gefolgt von Status und Size
    # Beispiel: /admin  301  178B  ->  Location: /admin/
    pattern = r"^(/\S+)\s+(\d{3})\s+(\d+)(?:[a-zA-Z]+)?"

    for line in clean.splitlines():
        match = re.match(pattern, line.strip())
        if match:
            results.append(
                GobusterResult(
                    url=match.group(1),
                    status_code=int(match.group(2)),
                    size=int(match.group(3)),
                )
            )

    return results


# Beispiel-Nutzung für den Agenten
def example_agent_usage():
    """
    Zeigt wie der Agent den Scanner nutzt
    """
    scanner = RobustGobusterScanner()

    # Scan durchführen
    results = scanner.scan(
        target="http://target.com",
        wordlist="/usr/share/wordlists/dirb/common.txt",
        extensions=["php", "txt", "bak"],
    )

    # Nur interessante Ergebnisse
    interesting = scanner.get_interesting_findings(results)

    # Zusammenfassung
    summary = scanner.generate_summary(results)

    print(f"Gefunden: {summary['interesting_findings']} interessante Pfade")
    print(f"Soft-404s herausgefiltert: {summary['soft_404s_detected']}")

    for finding in interesting[:5]:
        print(f"  {finding.url} [{finding.status_code}] {finding.size}B")

    return interesting


if __name__ == "__main__":
    print("Robuster Gobuster Parser")
    print("=" * 50)
    print("Diese Version wird aktiviert sobald Smart-Test Rot zeigt")
    print("Features:")
    print("  - JSON-Output für strukturierte Daten")
    print("  - Size-Fingerprinting für Soft-404-Erkennung")
    print("  - Deduplizierung gleicher Fehlerseiten")
    print("  - Keine Abstürze bei komplexen Status-Texten")
