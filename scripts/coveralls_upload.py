#!/usr/bin/env python3
"""
Coveralls Upload Helper
Nutzt den gespeicherten Token für Coverage Uploads
"""

import os
import subprocess
import sys
from pathlib import Path


def get_coveralls_token():
    """Holt Token aus gespeicherter Datei"""
    token_path = Path.home() / ".coveralls_token"
    if token_path.exists():
        return token_path.read_text().strip()
    return None


def upload_to_coveralls(repo_path="/root/.openclaw/workspace/Zen-Ai-Pentest"):
    """Lädt Coverage zu Coveralls hoch"""
    token = get_coveralls_token()

    if not token:
        print("❌ Kein Coveralls Token gefunden")
        return False

    # Prüfe ob coverage.xml existiert
    coverage_file = Path(repo_path) / "coverage.xml"
    if not coverage_file.exists():
        print("❌ coverage.xml nicht gefunden")
        print("💡 Führe zuerst aus: pytest --cov --cov-report=xml")
        return False

    print("📊 Lade Coverage zu Coveralls hoch...")

    # Installiere coveralls wenn nicht vorhanden
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "coveralls", "-q"],
        capture_output=True,
    )

    # Setze Token als Env Variable
    env = os.environ.copy()
    env["COVERALLS_REPO_TOKEN"] = token

    # Upload
    result = subprocess.run(
        [sys.executable, "-m", "coveralls", "--service=github"],
        cwd=repo_path,
        env=env,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ Coveralls Upload erfolgreich!")
        print(result.stdout)
        return True
    else:
        print(f"❌ Upload fehlgeschlagen: {result.stderr}")
        return False


def run_coverage_and_upload():
    """Führt Coverage aus und uploaded zu Coveralls"""
    repo_path = "/root/.openclaw/workspace/Zen-Ai-Pentest"

    print("🧪 Führe Tests mit Coverage aus...")

    # Coverage run
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/smart/",
            "tests/unit/agents/",
            "tests/integration/test_agent_self_healing.py",
            "--cov=core",
            "--cov=agents",
            "--cov=tools",
            "--cov-report=xml:coverage.xml",
            "--cov-report=term",
            "-q",
        ],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    # Zeige Coverage Summary
    for line in result.stdout.split("\n"):
        if "TOTAL" in line or "%" in line:
            print(line)

    # Upload
    return upload_to_coveralls(repo_path)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--upload-only":
        upload_to_coveralls()
    else:
        run_coverage_and_upload()
