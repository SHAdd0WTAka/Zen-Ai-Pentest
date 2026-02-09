#!/usr/bin/env python3
"""Test API Endpoints"""

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    print(f"Health Check: {response.status_code}")
    if response.status_code == 200:
        print(f"  Response: {response.json()}")
    return response.status_code == 200


def test_login():
    response = client.post("/auth/login", json={"username": "admin", "password": "admin"})
    print(f"Login: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Token: {data['access_token'][:30]}...")
        return data["access_token"]
    else:
        print(f"  Error: {response.text}")
    return None


def test_scans_no_auth():
    response = client.get("/scans")
    print(f"Scans (no auth): {response.status_code}")
    return response.status_code


def test_scans_with_auth(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/scans", headers=headers)
    print(f"Scans (with auth): {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        count = len(data) if isinstance(data, list) else data.get("total", "N/A")
        print(f"  Count: {count}")
    return response.status_code


def test_tools(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/tools", headers=headers)
    print(f"Tools: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        tools = data.get("tools", [])
        print(f"  Available: {len(tools)} tools")
    return response.status_code


def test_stats(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/stats/overview", headers=headers)
    print(f"Stats Overview: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Total Scans: {data.get('total_scans', 0)}")
        print(f"  Total Findings: {data.get('total_findings', 0)}")
    return response.status_code


def main():
    print("=" * 50)
    print("Testing Zen AI Pentest API")
    print("=" * 50)

    # Test 1: Health
    test_health()
    print()

    # Test 2: Login
    token = test_login()
    print()

    # Test 3: Scans (no auth)
    test_scans_no_auth()
    print()

    if token:
        # Test 4: Scans (with auth)
        test_scans_with_auth(token)
        print()

        # Test 5: Tools
        test_tools(token)
        print()

        # Test 6: Stats
        test_stats(token)
        print()

    print("=" * 50)
    print("Tests completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
