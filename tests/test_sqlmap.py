"""
Test for REAL SQLMap Execution - SQL Injection Testing

Tests actual SQLMap execution against deliberately vulnerable targets.
ONLY run against targets you have permission to test!
"""

import asyncio
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autonomous.sqlmap_integration import SQLMapScanner


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.real_tool
@pytest.mark.slow
async def test_sqlmap_real_scan():
    """
    Test REAL SQLMap against testphp.vulnweb.com (deliberately vulnerable)

    Requirements:
    - sqlmap installed: https://sqlmap.org/
    - Internet connection
    - ~60-120 seconds execution time
    """
    scanner = SQLMapScanner(timeout=120, level=1, risk=1)

    # Test against deliberately vulnerable test site
    # This is a LEGAL test target maintained by Acunetix for testing
    result = await scanner.scan_target(
        target_url="http://testphp.vulnweb.com/artists.php?artist=1",
        method="GET"
    )

    # Assertions
    assert result.success, f"SQLMap failed: {result.error_message}"
    assert result.execution_time > 0

    # Should detect vulnerability on this test target
    # (but we don't assert vulnerable=True as it depends on the target state)
    print("\n[SUCCESS] REAL SQLMap scan completed!")
    print("   Target: testphp.vulnweb.com")
    print(f"   Vulnerable: {result.vulnerable}")
    print(f"   DBMS: {result.dbms or 'Unknown'}")
    print(f"   Execution time: {result.execution_time:.2f}s")
    print(f"   Parameters tested: {len(result.parameters)}")

    if result.vulnerable:
        print(f"   Payload: {result.payload[:100]}...")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sqlmap_safety():
    """Test safety validations."""
    scanner = SQLMapScanner()

    # Test invalid URL format
    result = await scanner.scan_target("not-a-url")
    assert not result.success
    assert "must start with http" in result.error_message.lower()

    # Test private IP blocking
    result = await scanner.scan_target("http://192.168.1.1/page.php?id=1")
    assert not result.success
    assert "blocked" in result.error_message.lower()

    print("\n[SUCCESS] Safety checks working correctly")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sqlmap_missing_tool():
    """Test behavior when SQLMap is not installed."""
    # This would require mocking or running on a system without sqlmap
    pass


if __name__ == "__main__":
    print("Testing REAL SQLMap Execution...")
    print("=" * 60)
    print("⚠️  WARNING: This tests against real targets!")
    print("   Target: testphp.vulnweb.com (legal test site)")
    print("   Estimated time: 60-120 seconds")
    print("=" * 60)

    try:
        asyncio.run(test_sqlmap_real_scan())
        print("\n[PASS] test_sqlmap_real_scan PASSED")
    except Exception as e:
        print(f"\n[FAIL] test_sqlmap_real_scan FAILED: {e}")

    try:
        asyncio.run(test_sqlmap_safety())
        print("\n[PASS] test_sqlmap_safety PASSED")
    except Exception as e:
        print(f"\n[FAIL] test_sqlmap_safety FAILED: {e}")
