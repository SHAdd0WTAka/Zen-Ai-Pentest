"""
Test for REAL Nuclei Execution - No Mocks!

This test executes actual nuclei commands against test targets.
Only run in safe environments with permission.
"""

import asyncio
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autonomous.agent_loop import NucleiScanner


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.real_tool
async def test_nuclei_real_execution():
    """
    Test REAL Nuclei execution against scanme.nmap.org
    
    Requirements:
    - nuclei installed: https://github.com/projectdiscovery/nuclei
    - Internet connection
    - Templates downloaded (nuclei -update)
    """
    scanner = NucleiScanner(timeout=120)
    
    # Test against scanme.nmap.org
    result = await scanner.execute({
        "target": "scanme.nmap.org",
        "templates": "technologies",  # Fast technology detection
        "severity": "info"
    })
    
    # Assertions
    assert result.success, f"Nuclei failed: {result.error_message}"
    assert result.execution_time > 0
    assert "real_execution" in result.metadata
    assert result.metadata["real_execution"] == True
    assert isinstance(result.data["findings"], list)
    
    print(f"\n[SUCCESS] REAL Nuclei scan completed!")
    print(f"   Target: scanme.nmap.org")
    print(f"   Findings: {result.data['count']}")
    print(f"   Execution time: {result.execution_time:.2f}s")
    
    if result.data["findings"]:
        print(f"   Sample finding: {result.data['findings'][0]['template']}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_nuclei_safety_validation():
    """Test that private IPs are blocked."""
    scanner = NucleiScanner()
    
    result = await scanner.execute({
        "target": "192.168.1.1",
        "templates": "technologies"
    })
    
    assert not result.success
    assert "blocked" in result.error_message.lower() or "private" in result.error_message.lower()
    print(f"\n[SUCCESS] Safety check working: {result.error_message}")


if __name__ == "__main__":
    print("Testing REAL Nuclei Execution...")
    print("=" * 60)
    
    try:
        asyncio.run(test_nuclei_real_execution())
        print("\n[PASS] test_nuclei_real_execution PASSED")
    except Exception as e:
        print(f"\n[FAIL] test_nuclei_real_execution FAILED: {e}")
    
    try:
        asyncio.run(test_nuclei_safety_validation())
        print("\n[PASS] test_nuclei_safety_validation PASSED")
    except Exception as e:
        print(f"\n[FAIL] test_nuclei_safety_validation FAILED: {e}")
