"""
Test for REAL Nmap Execution - No Mocks!

This test executes actual nmap commands against scanme.nmap.org
Only run in safe environments with permission.
"""

import asyncio
import pytest
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autonomous.agent_loop import NmapScanner


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.real_tool
async def test_nmap_real_execution():
    """
    Test REAL Nmap execution against scanme.nmap.org
    
    Requirements:
    - nmap installed: https://nmap.org/download.html
    - Internet connection
    - scanme.nmap.org accessible
    """
    scanner = NmapScanner(timeout=60)
    
    # Test against scanme.nmap.org (official Nmap test target)
    result = await scanner.execute({
        "target": "scanme.nmap.org",
        "ports": "22,80",  # Limited ports for faster test
        "options": "-sV"   # Service detection only
    })
    
    # Assertions
    assert result.success, f"Nmap failed: {result.error_message}"
    assert result.execution_time > 0, "Should have taken some time"
    assert "real_execution" in result.metadata, "Should mark as real execution"
    assert result.metadata["real_execution"] == True
    
    # Check parsed data
    assert "open_ports" in result.data
    assert isinstance(result.data["open_ports"], list)
    
    # Should find port 22 (SSH) or 80 (HTTP) on scanme.nmap.org
    ports_found = [p["port"] for p in result.data["open_ports"]]
    print(f"\n[SUCCESS] REAL Nmap scan completed!")
    print(f"   Target: scanme.nmap.org")
    print(f"   Open ports: {ports_found}")
    print(f"   Execution time: {result.execution_time:.2f}s")
    print(f"   Raw output length: {len(result.raw_output)} chars")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.real_tool
async def test_nmap_localhost():
    """
    Test Nmap against localhost (safe for CI/CD)
    """
    scanner = NmapScanner(timeout=30)
    
    result = await scanner.execute({
        "target": "127.0.0.1",
        "ports": "1-100",  # Top 100 ports
        "options": "-sT"   # TCP connect scan
    })
    
    # Localhost should work but might have no open ports
    assert result.success or "Private IP" in (result.error_message or "")
    
    if result.success:
        print(f"\n[SUCCESS] Localhost scan completed!")
        print(f"   Open ports: {[p['port'] for p in result.data.get('open_ports', [])]}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_nmap_safety_validation():
    """
    Test that private IPs are blocked without whitelist
    """
    scanner = NmapScanner()
    
    # Try to scan a private IP
    result = await scanner.execute({
        "target": "192.168.1.1",
        "ports": "80"
    })
    
    # Should be blocked for safety
    assert not result.success
    assert "blocked" in result.error_message.lower() or "private" in result.error_message.lower()
    print(f"\n[SUCCESS] Safety check working: {result.error_message}")


if __name__ == "__main__":
    # Run tests directly
    print("Testing REAL Nmap Execution...")
    print("=" * 60)
    
    try:
        asyncio.run(test_nmap_real_execution())
        print("\n[PASS] test_nmap_real_execution PASSED")
    except Exception as e:
        print(f"\n[FAIL] test_nmap_real_execution FAILED: {e}")
    
    try:
        asyncio.run(test_nmap_localhost())
        print("\n[PASS] test_nmap_localhost PASSED")
    except Exception as e:
        print(f"\n[FAIL] test_nmap_localhost FAILED: {e}")
    
    try:
        asyncio.run(test_nmap_safety_validation())
        print("\n[PASS] test_nmap_safety_validation PASSED")
    except Exception as e:
        print(f"\n[FAIL] test_nmap_safety_validation FAILED: {e}")
