"""Zen-AI-Pentest Bridge Integration"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings


class ZenAIPentestBridge:
    """Bridge to Zen-AI-Pentest API for scan delegation and result retrieval"""

    def __init__(self):
        self.base_url = settings.ZAP_API_URL.rstrip("/")
        self.api_key = settings.ZAP_API_KEY
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(60.0, connect=10.0),
            headers={
                "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
                "Content-Type": "application/json",
            },
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check if Zen-AI-Pentest API is available"""
        try:
            response = await self.client.get("/health")
            return {
                "status": "connected" if response.status_code == 200 else "error",
                "api_status": response.status_code,
                "data": response.json() if response.status_code == 200 else None,
            }
        except Exception as e:
            return {
                "status": "disconnected",
                "error": str(e),
            }

    async def create_scan(
        self,
        target: str,
        scan_type: str = "full",
        name: Optional[str] = None,
        description: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new scan in Zen-AI-Pentest"""
        payload = {
            "target": target,
            "scan_type": scan_type,
            "name": name or f"Zen-Teams Scan {datetime.utcnow().isoformat()}",
            "description": description or f"Automated scan triggered by Zen-Teams for {target}",
            "options": options or {},
        }

        response = await self.client.post("/api/v1/scans/", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_scan(self, scan_id: str) -> Dict[str, Any]:
        """Get scan details and status"""
        response = await self.client.get(f"/api/v1/scans/{scan_id}")
        response.raise_for_status()
        return response.json()

    async def get_scan_results(self, scan_id: str) -> Dict[str, Any]:
        """Get scan results/findings"""
        response = await self.client.get(f"/api/v1/scans/{scan_id}/results")
        response.raise_for_status()
        return response.json()

    async def list_scans(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List scans from Zen-AI-Pentest"""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status

        response = await self.client.get("/api/v1/scans/", params=params)
        response.raise_for_status()
        return response.json()

    async def cancel_scan(self, scan_id: str) -> Dict[str, Any]:
        """Cancel a running scan"""
        response = await self.client.post(f"/api/v1/scans/{scan_id}/cancel")
        response.raise_for_status()
        return response.json()

    async def get_tools(self) -> List[Dict[str, Any]]:
        """Get available pentest tools"""
        response = await self.client.get("/api/v1/tools/")
        if response.status_code == 200:
            return response.json()
        return []

    async def run_tool(
        self,
        tool_name: str,
        target: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run a specific pentest tool"""
        payload = {
            "tool": tool_name,
            "target": target,
            "options": options or {},
        }
        response = await self.client.post("/api/v1/tools/run", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_reports(self, scan_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get reports from Zen-AI-Pentest"""
        params = {}
        if scan_id:
            params["scan_id"] = scan_id

        response = await self.client.get("/api/v1/reports/", params=params)
        if response.status_code == 200:
            return response.json()
        return []

    async def generate_report(
        self,
        scan_id: str,
        format: str = "pdf",
        template: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a report for a scan"""
        payload = {
            "scan_id": scan_id,
            "format": format,
            "template": template or "executive",
        }
        response = await self.client.post("/api/v1/reports/generate", json=payload)
        response.raise_for_status()
        return response.json()


# Global bridge instance
zen_bridge = ZenAIPentestBridge()
