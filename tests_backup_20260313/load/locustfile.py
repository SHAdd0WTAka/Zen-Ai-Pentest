"""
Locust Load Testing for Zen AI Pentest API
"""

import random

from locust import HttpUser, between, task


class APIUser(HttpUser):
    """Simulated API user"""

    wait_time = between(1, 5)

    def on_start(self):
        """Called when a user starts"""
        # Login and get token
        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            self.token = None

    @task(3)
    def get_health(self):
        """Test health endpoint"""
        self.client.get("/api/v1/health")

    @task(2)
    def get_tools(self):
        """Test tools endpoint"""
        self.client.get("/api/v1/tools/")

    @task(2)
    def get_stats(self):
        """Test stats endpoint"""
        self.client.get("/api/v1/stats/overview")

    @task(1)
    def create_scan(self):
        """Test scan creation"""
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
            self.client.post(
                "/api/v1/scans/",
                json={
                    "name": f"Load Test Scan {random.randint(1, 1000)}",
                    "target": "example.com",
                    "scan_type": "basic",
                },
                headers=headers,
            )


class FrontendUser(HttpUser):
    """Simulated frontend user"""

    wait_time = between(2, 10)

    @task(5)
    def load_dashboard(self):
        """Test dashboard loading"""
        self.client.get("/")

    @task(3)
    def load_scans_page(self):
        """Test scans page loading"""
        self.client.get("/scans")

    @task(2)
    def load_findings_page(self):
        """Test findings page loading"""
        self.client.get("/findings")
