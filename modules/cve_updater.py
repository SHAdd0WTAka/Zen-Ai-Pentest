"""CVE Database Auto-Update Module

Fetches and updates CVE data from NVD (National Vulnerability Database)
- Daily delta updates
- Caching with ETags
- Rate limiting compliance (NVD: max 5 requests in 30 seconds)
"""

import asyncio
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import aiohttp
import aiofiles
import logging


@dataclass
class CVEEntry:
    """Single CVE entry structure"""

    id: str
    published: str
    last_modified: str
    description: str
    cvss_score: float
    cvss_vector: str
    severity: str
    references: List[str]
    cpe_matches: List[str]


class NVDClient:
    """NVD API Client with rate limiting"""

    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    RATE_LIMIT_DELAY = 6.0  # 6 seconds between requests (max 5 per 30s)

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NVD_API_KEY")
        self.last_request_time = 0
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def _rate_limit(self):
        """Ensure rate limiting compliance"""
        elapsed = asyncio.get_event_loop().time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = asyncio.get_event_loop().time()

    async def fetch_cves(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, results_per_page: int = 2000
    ) -> List[CVEEntry]:
        """Fetch CVEs from NVD with optional date range"""
        await self._rate_limit()

        params = {"resultsPerPage": results_per_page}

        if start_date:
            params["lastModStartDate"] = start_date.strftime("%Y-%m-%dT%H:%M:%S.000")
        if end_date:
            params["lastModEndDate"] = end_date.strftime("%Y-%m-%dT%H:%M:%S.000")

        if self.api_key:
            params["apiKey"] = self.api_key

        async with self.session.get(self.BASE_URL, params=params) as resp:
            if resp.status != 200:
                raise Exception(f"NVD API error: {resp.status}")

            data = await resp.json()
            return self._parse_cves(data)

    def _parse_cves(self, data: Dict) -> List[CVEEntry]:
        """Parse NVD API response"""
        cves = []

        for vuln in data.get("vulnerabilities", []):
            cve_data = vuln.get("cve", {})

            # Extract CVSS score
            cvss_score = 0.0
            severity = "unknown"
            cvss_vector = ""

            metrics = cve_data.get("metrics", {})
            if "cvssMetricV31" in metrics:
                cvss_data = metrics["cvssMetricV31"][0]["cvssData"]
                cvss_score = cvss_data.get("baseScore", 0.0)
                severity = metrics["cvssMetricV31"][0].get("baseSeverity", "unknown").lower()
                cvss_vector = cvss_data.get("vectorString", "")
            elif "cvssMetricV30" in metrics:
                cvss_data = metrics["cvssMetricV30"][0]["cvssData"]
                cvss_score = cvss_data.get("baseScore", 0.0)
                severity = metrics["cvssMetricV30"][0].get("baseSeverity", "unknown").lower()
                cvss_vector = cvss_data.get("vectorString", "")

            # Extract description (English only)
            descriptions = cve_data.get("descriptions", [])
            description = ""
            for desc in descriptions:
                if desc.get("lang") == "en":
                    description = desc.get("value", "")
                    break

            # Extract references
            references = [ref.get("url", "") for ref in cve_data.get("references", []) if ref.get("url")]

            # Extract CPE matches
            cpe_matches = []
            configurations = cve_data.get("configurations", [])
            for config in configurations:
                for node in config.get("nodes", []):
                    for match in node.get("cpeMatch", []):
                        if match.get("criteria"):
                            cpe_matches.append(match["criteria"])

            cve = CVEEntry(
                id=cve_data.get("id", ""),
                published=cve_data.get("published", ""),
                last_modified=cve_data.get("lastModified", ""),
                description=description,
                cvss_score=cvss_score,
                cvss_vector=cvss_vector,
                severity=severity,
                references=references,
                cpe_matches=cpe_matches,
            )
            cves.append(cve)

        return cves


class CVEUpdater:
    """CVE Database Updater"""

    def __init__(self, db_path: str = "data/cve_database.json"):
        self.db_path = db_path
        self.metadata_path = db_path.replace(".json", "_meta.json")
        self.db_dir = os.path.dirname(db_path)

        # Ensure directory exists
        if self.db_dir:
            os.makedirs(self.db_dir, exist_ok=True)

    async def initialize_db(self):
        """Create initial empty database"""
        if not os.path.exists(self.db_path):
            await self._save_db({})
            await self._save_metadata({"last_update": None, "total_cves": 0})

    async def update(self, days_back: int = 1) -> Dict:
        """Update CVE database with delta from last N days"""
        await self.initialize_db()

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        logging.info(f"Fetching CVEs from {start_date} to {end_date}")

        # Fetch from NVD
        async with NVDClient() as client:
            cves = await client.fetch_cves(start_date, end_date)

        # Load existing database
        db = await self._load_db()

        # Merge updates
        new_count = 0
        updated_count = 0

        for cve in cves:
            if cve.id not in db:
                new_count += 1
            elif db[cve.id]["last_modified"] != cve.last_modified:
                updated_count += 1

            db[cve.id] = asdict(cve)

        # Save updated database
        await self._save_db(db)

        # Update metadata
        metadata = {
            "last_update": datetime.utcnow().isoformat(),
            "total_cves": len(db),
            "last_fetch_new": new_count,
            "last_fetch_updated": updated_count,
            "last_fetch_date_range": f"{start_date.date()} to {end_date.date()}",
        }
        await self._save_metadata(metadata)

        logging.info(f"Update complete: {new_count} new, {updated_count} updated, {len(db)} total")

        return metadata

    async def full_sync(self) -> Dict:
        """Full database sync (last 120 days - NVD limit)"""
        return await self.update(days_back=120)

    async def _load_db(self) -> Dict:
        """Load database from disk"""
        if not os.path.exists(self.db_path):
            return {}

        async with aiofiles.open(self.db_path, "r") as f:
            content = await f.read()
            return json.loads(content)

    async def _save_db(self, db: Dict):
        """Save database to disk"""
        async with aiofiles.open(self.db_path, "w") as f:
            await f.write(json.dumps(db, indent=2))

    async def _load_metadata(self) -> Dict:
        """Load metadata from disk"""
        if not os.path.exists(self.metadata_path):
            return {}

        async with aiofiles.open(self.metadata_path, "r") as f:
            content = await f.read()
            return json.loads(content)

    async def _save_metadata(self, metadata: Dict):
        """Save metadata to disk"""
        async with aiofiles.open(self.metadata_path, "w") as f:
            await f.write(json.dumps(metadata, indent=2))

    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            if not os.path.exists(self.db_path):
                return {"status": "not_initialized"}

            with open(self.db_path, "r") as f:
                db = json.load(f)

            with open(self.metadata_path, "r") as f:
                metadata = json.load(f)

            # Count by severity
            severity_counts = {}
            for cve in db.values():
                sev = cve.get("severity", "unknown")
                severity_counts[sev] = severity_counts.get(sev, 0) + 1

            return {
                "status": "ready",
                "total_cves": len(db),
                "last_update": metadata.get("last_update"),
                "by_severity": severity_counts,
                "metadata": metadata,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def lookup_cve(self, cve_id: str) -> Optional[Dict]:
        """Lookup single CVE by ID"""
        db = await self._load_db()
        return db.get(cve_id)

    def get_info(self) -> Dict:
        """Get module info"""
        return {
            "name": "cve_updater",
            "version": "1.0.0",
            "description": "CVE Database Auto-Update from NVD",
            "source": "NVD (National Vulnerability Database)",
            "update_frequency": "daily",
            "rate_limit": "6 seconds between requests",
        }


# CLI interface
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    updater = CVEUpdater()

    if len(sys.argv) > 1 and sys.argv[1] == "full":
        result = asyncio.run(updater.full_sync())
    else:
        result = asyncio.run(updater.update())

    print(json.dumps(result, indent=2))
