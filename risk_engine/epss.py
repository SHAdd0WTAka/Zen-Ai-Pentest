"""
EPSS (Exploit Prediction Scoring System) Client

Fetches exploit probability scores from FIRST EPSS API.
https://www.first.org/epss/
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests


class EPSSClient:
    """
    Client for FIRST EPSS API.

    EPSS provides the probability that a vulnerability will be exploited
    in the wild within the next 30 days.
    """

    API_URL = "https://api.first.org/data/v1/epss"

    def __init__(self, cache_duration: int = 24):
        """
        Initialize EPSS client.

        Args:
            cache_duration: Hours to cache results
        """
        self.cache: Dict[str, Dict] = {}
        self.cache_duration = timedelta(hours=cache_duration)
        self.logger = logging.getLogger(__name__)

    def get_score(self, cve_id: str) -> float:
        """
        Get EPSS score for a CVE.

        Args:
            cve_id: CVE ID (e.g., "CVE-2021-44228")

        Returns:
            EPSS score 0.0-1.0 (probability of exploitation)
        """
        cve_id = cve_id.upper()

        # Check cache
        if cve_id in self.cache:
            cached = self.cache[cve_id]
            if datetime.now() - cached["timestamp"] < self.cache_duration:
                return cached["score"]

        # Fetch from API
        try:
            score = self._fetch_epss(cve_id)
            self.cache[cve_id] = {"score": score, "timestamp": datetime.now()}
            return score

        except Exception as e:
            self.logger.warning(f"Failed to fetch EPSS for {cve_id}: {e}")
            return 0.0

    def _fetch_epss(self, cve_id: str) -> float:
        """Fetch EPSS score from API."""
        try:
            response = requests.get(self.API_URL, params={"cve": cve_id}, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get("data") and len(data["data"]) > 0:
                epss_data = data["data"][0]
                return float(epss_data.get("epss", 0))

            return 0.0

        except requests.RequestException as e:
            self.logger.error(f"EPSS API request failed: {e}")
            raise

    def get_batch_scores(self, cve_ids: List[str]) -> Dict[str, float]:
        """
        Get EPSS scores for multiple CVEs in one request.

        Args:
            cve_ids: List of CVE IDs

        Returns:
            Dict mapping CVE ID to EPSS score
        """
        if not cve_ids:
            return {}

        try:
            response = requests.get(
                self.API_URL,
                params={"cve": ",".join(cve_ids[:100])},  # API limit
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            results = {}

            for item in data.get("data", []):
                cve = item.get("cve", "").upper()
                score = float(item.get("epss", 0))
                results[cve] = score

                # Update cache
                self.cache[cve] = {"score": score, "timestamp": datetime.now()}

            # Fill in missing CVEs with 0
            for cve in cve_ids:
                if cve.upper() not in results:
                    results[cve.upper()] = 0.0

            return results

        except Exception as e:
            self.logger.error(f"Batch EPSS fetch failed: {e}")
            return {cve.upper(): 0.0 for cve in cve_ids}

    def get_percentile(self, cve_id: str) -> Optional[float]:
        """
        Get EPSS percentile for a CVE.

        Indicates how this CVE ranks compared to all others.
        """
        try:
            response = requests.get(self.API_URL, params={"cve": cve_id.upper()}, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get("data") and len(data["data"]) > 0:
                percentile = data["data"][0].get("percentile")
                return float(percentile) if percentile else None

            return None

        except Exception as e:
            self.logger.warning(f"Failed to fetch EPSS percentile: {e}")
            return None

    def interpret_score(self, score: float) -> str:
        """
        Provide human-readable interpretation of EPSS score.
        """
        if score >= 0.5:
            return "Very High - Active exploitation likely"
        elif score >= 0.3:
            return "High - Exploitation probable"
        elif score >= 0.1:
            return "Medium - Some exploitation risk"
        elif score >= 0.05:
            return "Low - Limited exploitation risk"
        else:
            return "Very Low - Unlikely to be exploited"

    def should_prioritize(self, cve_id: str, threshold: float = 0.2) -> bool:
        """
        Determine if a CVE should be prioritized based on EPSS.

        Args:
            cve_id: CVE to check
            threshold: EPSS threshold for prioritization (default 20%)

        Returns:
            True if should prioritize
        """
        score = self.get_score(cve_id)
        return score >= threshold
