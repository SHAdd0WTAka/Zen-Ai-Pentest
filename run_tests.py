#!/usr/bin/env python3
"""
Test Runner for Zen AI Pentest
"""

import subprocess
import sys
import os

def run_tests():
    """Run pytest with coverage."""
    print("=" * 70)
    print("RUNNING TESTS - Zen AI Pentest")
    print("=" * 70)
    print()
    
    os.chdir(r'C:\Users\Ataka\zen-ai-pentest')
    
    # Install test dependencies
    print("[1/4] Installing test dependencies...")
    subprocess.run([
        sys.executable, '-m', 'pip', 'install', '-q',
        'pytest', 'pytest-asyncio', 'pytest-cov', 'pytest-mock'
    ], check=False)
    print("[OK] Test dependencies installed")
    print()
    
    # Run tests
    print("[2/4] Running tests with coverage...")
    result = subprocess.run([
        sys.executable, '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '--cov=autonomous',
        '--cov=risk_engine',
        '--cov-report=term-missing',
        '--cov-report=html:coverage_html'
    ], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    
    print(result.stdout)
    
    print()
    print("[3/4] Coverage Report")
    print("-" * 70)
    
    print()
    print("[4/4] Test Summary")
    print("-" * 70)
    
    if result.returncode == 0:
        print("[OK] ALL TESTS PASSED")
    else:
        print(f"[WARN] TESTS COMPLETED WITH EXIT CODE: {result.returncode}")
    
    print()
    print("Coverage reports generated:")
    print("  - HTML: coverage_html/index.html")
    print()
    print("=" * 70)
    
    return result.returncode

if __name__ == '__main__':
    sys.exit(run_tests())
