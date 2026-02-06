#!/usr/bin/env python3
import requests


BASE_URL = "http://localhost:8000"

def test_login():
    print("Testing Login API...")
    print("=" * 40)
    
    # Test 1: API Health
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Health Check: {resp.status_code}")
    except Exception as e:
        print(f"Health Check Failed: {e}")
        return False
    
    # Test 2: Login
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "admin", "password": "admin"},
            timeout=5
        )
        print(f"Login: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("access_token", "")
            print(f"Token: {token[:30]}..." if token else "No token!")
            return True
        else:
            print(f"Error: {resp.text}")
            return False
    except Exception as e:
        print(f"Login Failed: {e}")
        return False

def test_cors():
    print("\nTesting CORS...")
    print("=" * 40)
    
    try:
        resp = requests.options(
            f"{BASE_URL}/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            },
            timeout=5
        )
        print(f"CORS Preflight: {resp.status_code}")
        print(f"Allow-Origin: {resp.headers.get('access-control-allow-origin', 'N/A')}")
        return True
    except Exception as e:
        print(f"CORS Test Failed: {e}")
        return False

if __name__ == "__main__":
    test_login()
    test_cors()
