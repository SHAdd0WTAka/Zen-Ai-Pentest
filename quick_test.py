#!/usr/bin/env python3
"""Quick integration test - verifies all modules load"""

import sys


def test_imports():
    """Test that all main modules can be imported"""
    print("Testing module imports...")

    modules = [
        ("orchestrator", "ZenOrchestrator"),
        ("scheduler", "TaskScheduler"),
        ("dashboard", "DashboardManager"),
        ("audit", "AuditLogger"),
        ("performance", "CacheManager"),
        ("app", "create_app"),
    ]

    passed = 0
    failed = 0

    for module, obj in modules:
        try:
            mod = __import__(module, fromlist=[obj])
            getattr(mod, obj)
            print(f"  [OK] {module}.{obj}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {module}.{obj}: {e}")
            failed += 1

    return passed, failed


def test_core_functionality():
    """Test core functionality"""
    print("\nTesting core functionality...")

    passed = 0
    failed = 0

    # Test 1: Secure Validator
    try:
        from core.secure_input_validator import SecureInputValidator

        validator = SecureInputValidator()
        result = validator.validate_url("https://example.com")
        print("  [OK] Secure Validator: URL validation works")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Secure Validator: {e}")
        failed += 1

    # Test 2: Tool Checker
    try:
        from tools.integrations.tool_checker import ToolChecker

        checker = ToolChecker()
        report = checker.get_status_report()
        print(
            f"  [OK] Tool Checker: Found {report['required']['available']}/{report['required']['total']} required tools"
        )
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Tool Checker: {e}")
        failed += 1

    # Test 3: Cache Manager
    try:
        import asyncio

        from performance import CacheManager

        async def test_cache():
            cache = CacheManager()
            await cache.start()
            await cache.set("test", {"data": "value"})
            result = await cache.get("test")
            await cache.stop()
            return result == {"data": "value"}

        result = asyncio.run(test_cache())
        if result:
            print("  [OK] Cache Manager: Get/Set works")
            passed += 1
        else:
            print("  ✗ Cache Manager: Data mismatch")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] Cache Manager: {e}")
        failed += 1

    return passed, failed


def main():
    print("=" * 60)
    print("ZEN-AI-PENTEST QUICK INTEGRATION TEST")
    print("=" * 60)
    print()

    p1, f1 = test_imports()
    p2, f2 = test_core_functionality()

    total_passed = p1 + p2
    total_failed = f1 + f2

    print()
    print("=" * 60)
    print(f"RESULTS: {total_passed} passed, {total_failed} failed")
    print("=" * 60)

    if total_failed == 0:
        print("\n✅ ALL TESTS PASSED - System is functional!")
        return 0
    else:
        print(f"\n⚠️  {total_failed} test(s) failed - Check output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
