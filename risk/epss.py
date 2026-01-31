"""
EPSS (Exploit Prediction Scoring System) Client
Integrates with FIRST EPSS API for exploit probability
"""
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
import requests


@dataclass
class EPSSScore:
    """EPSS Score data"""
    cve_id: str
    epss_score: float  # 0.0 - 1.0 (probability)
    epss_percentile: float  # 0.0 - 1.0 (ranking)
    date: str
    
    @property
    def probability_percentage(self) -> float:
        """Return as percentage"""
        return self.epss_score * 100
    
    @property
    def risk_level(self) -> str:
        """Categorize EPSS score"""
        if self.epss_score >= 0.5:
            return "Critical"
        elif self.epss_score >= 0.2:
            return "High"
        elif self.epss_score >= 0.05:
            return "Medium"
        else:
            return "Low"


class EPSSClient:
    """
    Client for FIRST EPSS API
    https://www.first.org/epss/
    """
    
    API_BASE = "https://api.first.org/data/v1/epss"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        self.cache: Dict[str, EPSSScore] = {}
        self.last_update: Optional[datetime] = None
    
    def get_score(self, cve_id: str) -> Optional[EPSSScore]:
        """
        Get EPSS score for a CVE
        """
        # Check cache
        if cve_id in self.cache:
            return self.cache[cve_id]
        
        try:
            params = {"cve": cve_id}
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = self.session.get(
                self.API_BASE,
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    item = data["data"][0]
                    score = EPSSScore(
                        cve_id=item.get("cve", cve_id),
                        epss_score=float(item.get("epss", 0)),
                        epss_percentile=float(item.get("percentile", 0)),
                        date=item.get("date", datetime.now().isoformat())
                    )
                    self.cache[cve_id] = score
                    return score
            
        except Exception as e:
            print(f"EPSS API error for {cve_id}: {e}")
        
        return None
    
    def get_scores_batch(self, cve_ids: List[str]) -> Dict[str, EPSSScore]:
        """
        Get EPSS scores for multiple CVEs
        """
        results = {}
        
        # Check cache first
        uncached = []
        for cve_id in cve_ids:
            if cve_id in self.cache:
                results[cve_id] = self.cache[cve_id]
            else:
                uncached.append(cve_id)
        
        if not uncached:
            return results
        
        try:
            # EPSS API supports batch requests
            cve_param = ",".join(uncached[:100])  # API limit
            params = {"cve": cve_param}
            
            response = self.session.get(
                self.API_BASE,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get("data", []):
                    cve = item.get("cve")
                    score = EPSSScore(
                        cve_id=cve,
                        epss_score=float(item.get("epss", 0)),
                        epss_percentile=float(item.get("percentile", 0)),
                        date=item.get("date", datetime.now().isoformat())
                    )
                    results[cve] = score
                    self.cache[cve] = score
        
        except Exception as e:
            print(f"EPSS batch API error: {e}")
        
        return results
    
    def estimate_score(self, cvss_score: float, has_exploit: bool = False) -> float:
        """
        Estimate EPSS score when API unavailable
        Rough approximation based on CVSS
        """
        # Higher CVSS = higher probability of exploit
        base_prob = cvss_score / 10.0 * 0.3  # Max 30% for CVSS alone
        
        if has_exploit:
            base_prob += 0.4  # +40% if exploit exists
        
        # Recent CVEs more likely to be exploited
        return min(base_prob, 0.95)
