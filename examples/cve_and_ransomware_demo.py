#!/usr/bin/env python3
"""
CVE and Ransomware Database Demo
Demonstrates the capabilities of the CVE and SQL Injection databases
Author: SHAdd0WTAka
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.cve_database import CVEDatabase
from modules.sql_injection_db import (DBType, SQLInjectionDatabase,
                                      SQLITechnique)
from utils.helpers import colorize


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 60)
    print(colorize(f"  {title}", "bold"))
    print("=" * 60 + "\n")


def demo_cve_database():
    """Demonstrate CVE Database features"""
    print_section("CVE & RANSOMWARE DATABASE DEMO")

    cve_db = CVEDatabase()

    # 1. Search for EternalBlue
    print(colorize("[1] Searching for EternalBlue (CVE-2017-0144)...", "cyan"))
    cve = cve_db.search_cve("CVE-2017-0144")

    if cve:
        print(f"  CVE ID: {cve.cve_id}")
        print(f"  Name: {cve.name}")
        print(f"  CVSS Score: {cve.cvss_score}")
        print(f"  Severity: {colorize(cve.severity, 'red')}")
        print(f"  Description: {cve.description}")
        print(
            f"  Ransomware using this: {', '.join(cve.ransomware_used_by) if cve.ransomware_used_by else 'None documented'}"
        )
        print(f"  Mitigation: {cve.mitigations[0] if cve.mitigations else 'N/A'}")

    # 2. Search for WannaCry
    print(colorize("\n[2] Searching for WannaCry ransomware...", "cyan"))
    ransomware = cve_db.search_ransomware("WannaCry")

    if ransomware:
        print(f"  Name: {ransomware.name}")
        print(f"  First Seen: {ransomware.first_seen}")
        print(f"  Type: {ransomware.type}")
        print(
            f"  Decryptable: {colorize('YES', 'green') if ransomware.decryptable else colorize('NO', 'red')}"
        )
        print(f"  File Extensions: {', '.join(ransomware.file_extensions)}")
        print(f"  Ransom Note: {ransomware.ransom_note}")
        print(f"  Associated CVEs: {', '.join(ransomware.cves)}")

        # Show IOCs
        print("\n  IOCs:")
        for key, values in ransomware.ioc.items():
            if isinstance(values, list) and values:
                print(f"    {key}:")
                for v in values[:3]:  # Show first 3
                    print(f"      - {v}")

    # 3. Check system indicators
    print(
        colorize(
            "\n[3] Checking system indicators against ransomware database...", "cyan"
        )
    )

    # Simulate system indicators
    test_indicators = {
        "files": ["C:\\Windows\\tasksche.exe", "C:\\Windows\\perfc.dat"],
        "hashes": ["ed01ebfbc9eb5bbea545af4d01bf5f1071661840480439c6e5babe8e080e41aa"],
    }

    matches = cve_db.check_system_for_ransomware(test_indicators)

    if matches:
        for match in matches:
            print(f"  [!] Potential match: {match['ransomware']}")
            print(f"      Confidence: {match['confidence']}%")
            print(f"      Recommendation: {match['recommendation']}")
    else:
        print("  [OK] No ransomware indicators detected")

    # 4. List all ransomware
    print(colorize("\n[4] Available ransomware in database:", "cyan"))
    all_ransomware = cve_db.list_all_ransomware()
    for rw in all_ransomware:
        status = "[DECRYPTABLE]" if rw["decryptable"] else "[LOCKED]"
        print(f"  {status} {rw['name']} ({rw['first_seen']}) - CVEs: {len(rw['cves'])}")

    # 5. List critical CVEs
    print(colorize("\n[5] Top Critical CVEs:", "cyan"))
    critical_cves = cve_db.get_critical_cves()
    for cve in critical_cves[:5]:
        print(f"  [{cve.severity}] {cve.cve_id} - {cve.name} (CVSS: {cve.cvss_score})")


def demo_sql_injection_database():
    """Demonstrate SQL Injection Database features"""
    print_section("SQL INJECTION DATABASE DEMO")

    sqli_db = SQLInjectionDatabase()

    # 1. Get MySQL payloads
    print(colorize("[1] MySQL Error-Based Payloads:", "cyan"))
    mysql_payloads = sqli_db.get_payloads(
        db_type=DBType.MYSQL, technique=SQLITechnique.ERROR_BASED
    )

    for payload in mysql_payloads[:3]:
        print(f"\n  {payload.name}:")
        print(f"    Payload: {colorize(payload.payload, 'yellow')}")
        print(f"    Expected: {payload.expected_result}")

    # 2. Get Time-Based payloads
    print(colorize("\n[2] MSSQL Time-Based Payloads:", "cyan"))
    mssql_payloads = sqli_db.get_payloads(
        db_type=DBType.MSSQL, technique=SQLITechnique.BLIND_TIME
    )

    for payload in mssql_payloads:
        print(f"\n  {payload.name}:")
        print(f"    Payload: {colorize(payload.payload, 'yellow')}")
        print(f"    Description: {payload.description}")

    # 3. WAF Bypass variants
    print(colorize("\n[3] WAF Bypass Variants:", "cyan"))
    test_payload = "' UNION SELECT password FROM users--"
    variants = sqli_db.generate_waf_bypass_variants(test_payload)

    print(f"  Original: {test_payload}")
    print("  Variants:")
    for i, variant in enumerate(variants[:5], 1):
        print(f"    {i}. {variant}")

    # 4. Get cheatsheet
    print(colorize("\n[4] MySQL Injection Cheatsheet (excerpt):", "cyan"))
    cheatsheet = sqli_db.get_cheatsheet(DBType.MYSQL)
    # Print first 10 lines
    for line in cheatsheet.split("\n")[:10]:
        if line.strip():
            print(f"  {line}")
    print("  ...")

    # 5. MongoDB NoSQL
    print(colorize("\n[5] MongoDB NoSQL Injection Payloads:", "cyan"))
    nosql_payloads = sqli_db.get_payloads(
        db_type=DBType.MONGODB, technique=SQLITechnique.ERROR_BASED
    )

    for payload in nosql_payloads:
        print(f"\n  {payload.name}:")
        print(f"    Payload: {colorize(payload.payload, 'yellow')}")
        print(f"    Description: {payload.description}")


def demo_statistics():
    """Show database statistics"""
    print_section("DATABASE STATISTICS")

    cve_db = CVEDatabase()
    sqli_db = SQLInjectionDatabase()

    # CVE Stats
    all_cves = cve_db.list_all_cves()
    ransomware_list = cve_db.list_all_ransomware()

    print(colorize("CVE Database:", "cyan"))
    print(f"  Total CVEs: {len(all_cves)}")
    print(
        f"  Critical CVEs: {len([c for c in all_cves if c['severity'] == 'Critical'])}"
    )
    print(f"  Ransomware Families: {len(ransomware_list)}")

    # Calculate total damage
    total_damage = sum(
        [
            cve_db.search_ransomware(rw["key"]).estimated_damage
            for rw in ransomware_list
            if cve_db.search_ransomware(rw["key"])
        ]
    )
    print(f"  Estimated Total Damage: ${total_damage:,}")

    # SQL Injection Stats
    print(colorize("\nSQL Injection Database:", "cyan"))
    total_payloads = 0
    for db in DBType:
        for tech in SQLITechnique:
            payloads = sqli_db.get_payloads(db, tech)
            total_payloads += len(payloads)

    print(f"  Total Payloads: {total_payloads}")
    print(f"  Database Types: {len(list(DBType))}")
    print(f"  Techniques: {len(list(SQLITechnique))}")


async def main():
    """Main demo function"""
    print(
        colorize(
            """
===============================================================
           Zen AI Pentest - Database Demo
                  CVE | Ransomware | SQLi
===============================================================
    """,
            "bold",
        )
    )

    try:
        # Run demos
        demo_cve_database()
        demo_sql_injection_database()
        demo_statistics()

        print_section("DEMO COMPLETED")
        print(
            colorize(
                "For more information, see the README.md and data/README.md files",
                "green",
            )
        )

    except KeyboardInterrupt:
        print(colorize("\n[!] Interrupted by user", "yellow"))
    except Exception as e:
        print(colorize(f"\n[!] Error: {e}", "red"))
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
