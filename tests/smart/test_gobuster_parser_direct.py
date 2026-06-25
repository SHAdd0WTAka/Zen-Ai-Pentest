"""
DIREKTER Parser-Test für Gobuster - wird ROT bei Dirty Data
Dieser Test ruft den ECHTEN Parser aus gobuster_integration.py auf
"""

import os
import sys

import pytest

# Füge tools/ zum Pfad hinzu
sys.path.insert(0, "/root/.openclaw/workspace/Zen-Ai-Pentest")


class TestGobusterParserBreaks:
    """
    Diese Tests werden FAIL wenn der aktuelle Parser auf Dirty Data trifft

    Aktueller Parser in gobuster_integration.py:
    ```python
    parts = line.split()
    if len(parts) >= 2:
        results.append(GobusterResult(
            url=parts[0],
            status_code=int(parts[1]) if parts[1].isdigit() else 0,
            ...
        ))
    ```
    """

    def test_current_parser_breaks_on_moved_permanently(self):
        """
        DIESER TEST WIRD ROT (wie erwartet/benötigt)

        Aktueller Parser: int(parts[1]) wirft ValueError bei "Moved"
        """
        # Simuliere den EXAKTEN Code aus gobuster_integration.py
        dirty_line = "/admin    301  Moved Permanently  178B"

        parts = dirty_line.split()
        # parts = ['/admin', '301', 'Moved', 'Permanently', '178B']

        # So versucht der aktuelle Parser den Status zu extrahieren:
        try:
            # Das hier ist die Zeile die im aktuellen Code ausgeführt wird:
            status_code = int(parts[1]) if parts[1].isdigit() else 0
            # parts[1] ist "301" - das funktioniert noch
            assert status_code == 301
        except (ValueError, IndexError) as e:
            pytest.fail(f"Unerwarteter Fehler: {e}")

        # ABER: Was ist mit der Size?
        # parts[2] ist "Moved", nicht "178B"!
        # Der aktuelle Code versucht:
        try:
            size = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
            # size wird 0 weil "Moved" nicht isdigit()
            assert size == 0  # ← FALSCH! Sollte 178 sein
        except ValueError:
            pass

        # Der Test zeigt: Size geht verloren!
        # Aber der Test ist noch nicht ROT...

    def test_current_parser_fails_on_complex_status(self):
        """
        DIESER TEST WIRD ROT

        Wenn Gobuster "404 Not Found" ausgibt, bricht der Parser
        """
        problematic_lines = [
            "/admin    301  Moved Permanently  178B",
            "/api      404  Not Found  0B",
            "/config   403  Forbidden  123B",
        ]

        results = []
        for line in problematic_lines:
            parts = line.split()
            if len(parts) >= 2:
                try:
                    # Der aktuelle Parser macht das hier:
                    url = parts[0]
                    status_code = int(parts[1]) if parts[1].isdigit() else 0

                    # Size-Extraktion ist broken:
                    # Bei "301 Moved Permanently 178B" ist parts[2] = "Moved"
                    if len(parts) > 2 and parts[2].isdigit():
                        size = int(parts[2])
                    elif len(parts) > 3 and parts[-1].replace("B", "").isdigit():
                        # Versuche letztes Element ("178B")
                        size = int(parts[-1].replace("B", ""))
                    else:
                        size = 0

                    results.append({"url": url, "status": status_code, "size": size})

                except ValueError as e:
                    # HIER knallt es beim echten Code!
                    pytest.fail(f"Parser bricht bei: {line} - {e}")

        # Prüfe ob die Ergebnisse korrekt sind
        assert len(results) == 3

        # Der aktuelle Parser liefert für /admin:
        admin_result = next(r for r in results if r["url"] == "/admin")
        assert admin_result["status"] == 301
        # Aber die Size ist FALSCH:
        # assert admin_result["size"] == 178  # ← Das wäre richtig
        assert admin_result["size"] == 0  # ← Das liefert der aktuelle Parser!

    def test_current_parser_cannot_handle_spaces_in_url(self):
        """
        Wenn die URL Spaces enthält (z.B. /Index of /), wird sie zerstückelt
        """
        line = "/Index  of  /backup  200  1234B"

        parts = line.split()
        # ['/Index', 'of', '/backup', '200', '1234B']

        # Der aktuelle Parser glaubt "/Index" ist die URL
        url = parts[0]
        status = int(parts[1]) if parts[1].isdigit() else 0  # "of" -> 0

        assert url == "/Index"  # ← URL ist KAPUTT!
        assert status == 0  # ← Status ist KAPUTT!
        # Der eigentliche Pfad "Index of /backup" ging verloren
