"""
EPSS (Exploit Prediction Scoring System) Client

Integration mit der EPSS API von FIRST (Forum of Incident Response and Security Teams).
EPSS liefert die Wahrscheinlichkeit (0-100%), dass eine CVE in den nächsten 30 Tagen
ausgenutzt wird.

API: https://api.first.org/data/v1/epss
Dokumentation: https://www.first.org/epss/
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.request import Request, urlopen

# Optional: requests für erweiterte Features
try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


@dataclass
class EPSSScore:
    """EPSS Score für eine CVE"""

    cve_id: str
    score: float  # 0.0 - 1.0 (Wahrscheinlichkeit)
    percentile: float  # 0.0 - 1.0 (Rang innerhalb aller CVEs)
    date: str  # Datum des Scores (YYYY-MM-DD)
    cached: bool = False  # Ob der Wert aus dem Cache kam
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def percentage(self) -> float:
        """Gibt die Wahrscheinlichkeit als Prozent zurück."""
        return self.score * 100

    @property
    def risk_level(self) -> str:
        """Klassifiziert das Risiko basierend auf dem EPSS Score."""
        if self.score >= 0.5:
            return "CRITICAL"
        elif self.score >= 0.3:
            return "HIGH"
        elif self.score >= 0.1:
            return "MEDIUM"
        elif self.score >= 0.05:
            return "LOW"
        return "VERY_LOW"

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "cve_id": self.cve_id,
            "score": round(self.score, 4),
            "percentage": round(self.percentage, 2),
            "percentile": round(self.percentile, 4),
            "date": self.date,
            "risk_level": self.risk_level,
            "cached": self.cached,
            "timestamp": self.timestamp.isoformat(),
        }


class EPSSCache:
    """
    Cache für EPSS Scores mit 24h TTL.

    Speichert Scores lokal um API-Requests zu reduzieren.
    """

    def __init__(self, cache_duration_hours: int = 24, cache_file: Optional[str] = None):
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.memory_cache: Dict[str, EPSSScore] = {}
        self.cache_file = cache_file or self._get_default_cache_file()
        self.logger = logging.getLogger(__name__)
        self._load_cache()

    def _get_default_cache_file(self) -> str:
        """Ermittelt den Standard-Cache-Pfad."""
        cache_dir = Path.home() / ".zen-ai-pentest" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return str(cache_dir / "epss_cache.json")

    def _load_cache(self):
        """Lädt den Cache aus der Datei."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    data = json.load(f)

                for cve_id, score_data in data.items():
                    self.memory_cache[cve_id.upper()] = EPSSScore(
                        cve_id=cve_id.upper(),
                        score=score_data.get("score", 0.0),
                        percentile=score_data.get("percentile", 0.0),
                        date=score_data.get("date", ""),
                        cached=True,
                        timestamp=datetime.fromisoformat(score_data.get("timestamp", datetime.now().isoformat())),
                    )
                self.logger.debug(f"EPSS Cache geladen: {len(self.memory_cache)} Einträge")
            except Exception as e:
                self.logger.warning(f"Fehler beim Laden des EPSS Caches: {e}")

    def _save_cache(self):
        """Speichert den Cache in die Datei."""
        try:
            data = {
                cve_id: {
                    "score": score.score,
                    "percentile": score.percentile,
                    "date": score.date,
                    "timestamp": score.timestamp.isoformat(),
                }
                for cve_id, score in self.memory_cache.items()
            }

            with open(self.cache_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Fehler beim Speichern des EPSS Caches: {e}")

    def get(self, cve_id: str) -> Optional[EPSSScore]:
        """
        Holt einen Score aus dem Cache wenn gültig.

        Returns:
            EPSSScore wenn im Cache und nicht abgelaufen, sonst None
        """
        cve_id = cve_id.upper()

        if cve_id not in self.memory_cache:
            return None

        score = self.memory_cache[cve_id]
        age = datetime.now() - score.timestamp

        if age > self.cache_duration:
            self.logger.debug(f"Cache-Eintrag für {cve_id} abgelaufen")
            del self.memory_cache[cve_id]
            return None

        self.logger.debug(f"Cache-Hit für {cve_id} (Alter: {age.total_seconds() / 3600:.1f}h)")
        return score

    def set(self, score: EPSSScore):
        """Speichert einen Score im Cache."""
        self.memory_cache[score.cve_id.upper()] = score
        self._save_cache()

    def clear(self):
        """Leert den Cache."""
        self.memory_cache.clear()
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        self.logger.info("EPSS Cache geleert")

    def get_stats(self) -> Dict[str, Any]:
        """Gibt Cache-Statistiken zurück."""
        now = datetime.now()
        valid_entries = sum(1 for score in self.memory_cache.values() if (now - score.timestamp) <= self.cache_duration)
        return {
            "total_entries": len(self.memory_cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.memory_cache) - valid_entries,
            "cache_file": self.cache_file,
            "cache_duration_hours": self.cache_duration.total_seconds() / 3600,
        }


class EPSSClientFull:
    """
    Vollständiger EPSS Client mit Caching.

    Features:
    - Abfrage von EPSS Scores für einzelne CVEs
    - Batch-Abfrage für mehrere CVEs
    - 24h Caching
    - Automatische Retry-Logik
    - Fallback bei API-Fehlern

    Usage:
        client = EPSSClientFull()

        # Einzelne CVE
        score = client.get_score("CVE-2021-44228")
        print(f"EPSS: {score.percentage:.1f}%")

        # Batch-Abfrage
        scores = client.get_batch_scores(["CVE-2021-44228", "CVE-2017-0144"])
    """

    API_URL = "https://api.first.org/data/v1/epss"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3

    def __init__(
        self,
        cache_duration_hours: int = 24,
        cache_file: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialisiert den EPSS Client.

        Args:
            cache_duration_hours: Wie lange Scores im Cache bleiben (Standard: 24h)
            cache_file: Pfad zur Cache-Datei (optional)
            api_key: API Key für FIRST (optional, meist nicht benötigt)
        """
        self.cache = EPSSCache(cache_duration_hours, cache_file)
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)

        # Session nur wenn requests verfügbar
        if HAS_REQUESTS:
            self.session = requests.Session()
            self.session.headers.update(
                {
                    "Accept": "application/json",
                    "User-Agent": "Zen-AI-Pentest/3.0",
                }
            )
        else:
            self.session = None

    def get_score(self, cve_id: str) -> EPSSScore:
        """
        Holt den EPSS Score für eine CVE.

        Args:
            cve_id: CVE ID (z.B. "CVE-2024-1234")

        Returns:
            EPSSScore mit Wahrscheinlichkeit und Percentile

        Example:
            >>> client = EPSSClientFull()
            >>> score = client.get_score("CVE-2021-44228")
            >>> print(f"Wahrscheinlichkeit: {score.percentage:.1f}%")
            Wahrscheinlichkeit: 97.42%
        """
        cve_id = cve_id.upper()

        # Prüfe Cache
        cached = self.cache.get(cve_id)
        if cached:
            return cached

        # Hole von API
        try:
            score = self._fetch_single(cve_id)
            self.cache.set(score)
            return score
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen von EPSS für {cve_id}: {e}")
            # Return default score on error
            return EPSSScore(
                cve_id=cve_id,
                score=0.0,
                percentile=0.0,
                date=datetime.now().strftime("%Y-%m-%d"),
                cached=False,
            )

    def _fetch_single(self, cve_id: str) -> EPSSScore:
        """Holt einen einzelnen Score von der API."""
        url = f"{self.API_URL}?cve={cve_id}"

        if HAS_REQUESTS and self.session:
            response = self.session.get(url, timeout=self.DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        else:
            # Fallback zu urllib
            req = Request(url, headers={"Accept": "application/json"})
            # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
            # nosemgrep
            with urlopen(req, timeout=self.DEFAULT_TIMEOUT) as response:  # nosec B310
                data = json.loads(response.read().decode("utf-8"))

        if not data.get("data") or len(data["data"]) == 0:
            self.logger.warning(f"Keine EPSS-Daten für {cve_id}")
            return EPSSScore(
                cve_id=cve_id,
                score=0.0,
                percentile=0.0,
                date=data.get("model", {}).get("date", datetime.now().strftime("%Y-%m-%d")),
                cached=False,
            )

        epss_data = data["data"][0]

        return EPSSScore(
            cve_id=cve_id,
            score=float(epss_data.get("epss", 0)),
            percentile=float(epss_data.get("percentile", 0)),
            date=epss_data.get("date", datetime.now().strftime("%Y-%m-%d")),
            cached=False,
        )

    def get_batch_scores(self, cve_ids: List[str]) -> Dict[str, EPSSScore]:
        """
        Holt EPSS Scores für mehrere CVEs in einer Anfrage.

        Args:
            cve_ids: Liste von CVE IDs

        Returns:
            Dictionary: {cve_id: EPSSScore}

        Note:
            Die API hat ein Limit von ~100 CVEs pro Anfrage.
            Größere Listen werden automatisch aufgeteilt.
        """
        if not cve_ids:
            return {}

        # Normalisiere CVE IDs
        cve_ids = [c.upper() for c in cve_ids]

        # Prüfe Cache
        results = {}
        to_fetch = []

        for cve_id in cve_ids:
            cached = self.cache.get(cve_id)
            if cached:
                results[cve_id] = cached
            else:
                to_fetch.append(cve_id)

        if not to_fetch:
            return results

        # API Limit: 100 CVEs pro Request
        BATCH_SIZE = 100

        for i in range(0, len(to_fetch), BATCH_SIZE):
            batch = to_fetch[i : i + BATCH_SIZE]

            try:
                batch_results = self._fetch_batch(batch)
                results.update(batch_results)

                # Speichere im Cache
                for score in batch_results.values():
                    self.cache.set(score)

            except Exception as e:
                self.logger.error(f"Fehler beim Batch-Fetch: {e}")
                # Fallback: Einzelne Abfragen
                for cve_id in batch:
                    try:
                        score = self._fetch_single(cve_id)
                        results[cve_id] = score
                        self.cache.set(score)
                    except Exception as e2:
                        self.logger.error(f"Fehler bei {cve_id}: {e2}")
                        results[cve_id] = EPSSScore(
                            cve_id=cve_id,
                            score=0.0,
                            percentile=0.0,
                            date=datetime.now().strftime("%Y-%m-%d"),
                        )

        return results

    def _fetch_batch(self, cve_ids: List[str]) -> Dict[str, EPSSScore]:
        """Holt mehrere Scores von der API."""
        url = f"{self.API_URL}?cve={','.join(cve_ids)}"

        if HAS_REQUESTS and self.session:
            response = self.session.get(url, timeout=self.DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        else:
            req = Request(url, headers={"Accept": "application/json"})
            # nosemgrep
            # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
            with urlopen(req, timeout=self.DEFAULT_TIMEOUT) as response:  # nosec B310
                data = json.loads(response.read().decode("utf-8"))

        results = {}

        model_date = data.get("model", {}).get("date", datetime.now().strftime("%Y-%m-%d"))

        for item in data.get("data", []):
            cve_id = item.get("cve", "").upper()
            if cve_id:
                results[cve_id] = EPSSScore(
                    cve_id=cve_id,
                    score=float(item.get("epss", 0)),
                    percentile=float(item.get("percentile", 0)),
                    date=item.get("date", model_date),
                    cached=False,
                )

        # Fülle fehlende CVEs mit 0.0
        for cve_id in cve_ids:
            if cve_id not in results:
                results[cve_id] = EPSSScore(
                    cve_id=cve_id,
                    score=0.0,
                    percentile=0.0,
                    date=model_date,
                    cached=False,
                )

        return results

    def get_percentile(self, cve_id: str) -> Optional[float]:
        """
        Holt nur das Percentile für eine CVE.

        Das Percentile zeigt, wie diese CVE im Vergleich zu allen anderen
        CVEs eingestuft wird (0-100%).
        """
        score = self.get_score(cve_id)
        return score.percentile if score else None

    def should_prioritize(
        self,
        cve_id: str,
        threshold: float = 0.2,
        cvss_score: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """
        Bestimmt, ob eine CVE priorisiert werden sollte.

        Args:
            cve_id: Die CVE ID
            threshold: EPSS Schwellenwert (Standard: 0.2 = 20%)
            cvss_score: Optional CVSS Score für kombinierte Bewertung

        Returns:
            Tuple von (soll_priorisiert_werden, grund)
        """
        score = self.get_score(cve_id)

        if score.score >= 0.5:
            return (
                True,
                f"Kritischer EPSS Score: {score.percentage:.1f}% - Aktive Ausnutzung wahrscheinlich",
            )

        if score.score >= threshold:
            if cvss_score and cvss_score >= 7.0:
                return (
                    True,
                    f"Hoher EPSS ({score.percentage:.1f}%) + Hoher CVSS ({cvss_score})",
                )
            return True, f"EPSS über Schwellenwert: {score.percentage:.1f}%"

        if cvss_score and cvss_score >= 9.0 and score.score >= 0.1:
            return (
                True,
                f"Kritischer CVSS ({cvss_score}) mit EPSS ({score.percentage:.1f}%)",
            )

        return False, f"EPSS ({score.percentage:.1f}%) unter Schwellenwert"

    def interpret_score(self, score: float) -> Dict[str, str]:
        """Gibt eine menschenlesbare Interpretation des EPSS Scores."""
        if score >= 0.5:
            return {
                "level": "CRITICAL",
                "description": "Sehr hohe Wahrscheinlichkeit der Ausnutzung",
                "recommendation": "Sofortige Behebung erforderlich",
                "action": "Patch innerhalb 24h oder Isolierung",
            }
        elif score >= 0.3:
            return {
                "level": "HIGH",
                "description": "Hohe Wahrscheinlichkeit der Ausnutzung",
                "recommendation": "Schnelle Behebung empfohlen",
                "action": "Patch innerhalb 72h",
            }
        elif score >= 0.1:
            return {
                "level": "MEDIUM",
                "description": "Mittlere Ausnutzungswahrscheinlichkeit",
                "recommendation": "Standard-Patch-Zyklus",
                "action": "Patch innerhalb 14 Tagen",
            }
        elif score >= 0.05:
            return {
                "level": "LOW",
                "description": "Geringe Ausnutzungswahrscheinlichkeit",
                "recommendation": "Optional patchen",
                "action": "Patch wenn möglich",
            }
        else:
            return {
                "level": "VERY_LOW",
                "description": "Sehr unwahrscheinlich, dass diese CVE ausgenutzt wird",
                "recommendation": "Keine Eile",
                "action": "Standard-Patch-Zyklus",
            }

    def compare_with_cvss(self, cve_id: str, cvss_score: float) -> Dict[str, Any]:
        """
        Vergleicht EPSS mit CVSS für eine CVE.

        Returns:
            Analyse der Priorität basierend auf beiden Scores
        """
        epss = self.get_score(cve_id)

        # Prioritätsmatrix
        if epss.score >= 0.5 and cvss_score >= 7.0:
            priority = "CRITICAL"
            action = "SOFORTIGE AKTION - Hohe technische Schwere + Hohe Ausnutzungswahrscheinlichkeit"
        elif epss.score >= 0.3 or cvss_score >= 9.0:
            priority = "HIGH"
            action = "Schnelle Behebung erforderlich"
        elif epss.score >= 0.1 or cvss_score >= 7.0:
            priority = "MEDIUM"
            action = "Standard-Patch-Zyklus"
        else:
            priority = "LOW"
            action = "Optionale Behebung"

        return {
            "cve_id": cve_id,
            "epss_score": epss.score,
            "epss_percentage": epss.percentage,
            "cvss_score": cvss_score,
            "cvss_severity": (
                "CRITICAL" if cvss_score >= 9 else ("HIGH" if cvss_score >= 7 else "MEDIUM" if cvss_score >= 4 else "LOW")
            ),
            "priority": priority,
            "recommended_action": action,
            "epss_percentile": epss.percentile,
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        """Gibt Cache-Statistiken zurück."""
        return self.cache.get_stats()

    def clear_cache(self):
        """Leert den Cache."""
        self.cache.clear()


# Convenience Functions
def get_epss_score(cve_id: str) -> float:
    """
    Schneller Zugriff auf EPSS Score als float.

    Returns:
        EPSS Score als float (0.0 - 1.0)
    """
    client = EPSSClientFull()
    score = client.get_score(cve_id)
    return score.score if score else 0.0


def get_epss_batch(cve_ids: List[str]) -> Dict[str, float]:
    """
    Batch-Abfrage von EPSS Scores.

    Returns:
        Dictionary: {cve_id: score}
    """
    client = EPSSClientFull()
    scores = client.get_batch_scores(cve_ids)
    return {cve: score.score for cve, score in scores.items()}
