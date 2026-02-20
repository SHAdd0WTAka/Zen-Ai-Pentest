#!/usr/bin/env python3
"""
Integration Tests für Zen-AI-Pentest Database
==========================================
End-to-End Tests für Datenbankoperationen
"""

import os
import sqlite3
import sys
import tempfile
from datetime import datetime

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytestmark = [pytest.mark.integration, pytest.mark.database]


class TestDatabaseConnection:
    """Integration Tests für Datenbankverbindung"""

    @pytest.fixture
    def db_path(self):
        """Temporäre Datenbankdatei"""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)

    def test_database_initialization(self, db_path):
        """Integration: Datenbank wird initialisiert"""
        from core.database import DatabaseManager

        db = DatabaseManager(f"sqlite:///{db_path}")
        db.initialize()

        # Prüfe ob Tabellen erstellt wurden
        tables = db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [t["name"] for t in tables]

        assert "scans" in table_names
        assert "findings" in table_names
        assert "agents" in table_names

    def test_database_connection_pool(self, db_path):
        """Integration: Connection Pooling funktioniert"""
        from core.database import DatabaseManager

        db = DatabaseManager(f"sqlite:///{db_path}")
        db.initialize()

        # Mehrere gleichzeitige Verbindungen
        connections = []
        for _ in range(5):
            conn = db.get_connection()
            connections.append(conn)

        # Alle Verbindungen sollten funktionieren
        for conn in connections:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1

        # Verbindungen zurückgeben
        for conn in connections:
            db.release_connection(conn)


class TestCRUDOperations:
    """Integration Tests für CRUD-Operationen"""

    @pytest.fixture
    def db(self):
        """Fixture für initialisierte Datenbank"""
        from core.database import DatabaseManager

        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        db = DatabaseManager(f"sqlite:///{path}")
        db.initialize()

        yield db

        db.close()
        os.unlink(path)

    def test_create_scan(self, db):
        """Integration: Scan erstellen"""
        scan_data = {
            "scan_id": "scan-123",
            "target": "example.com",
            "scan_type": "reconnaissance",
            "status": "queued",
            "created_at": datetime.now().isoformat(),
        }

        scan_id = db.create_scan(scan_data)

        assert scan_id is not None

        # Scan abrufen
        scan = db.get_scan(scan_id)
        assert scan["target"] == "example.com"

    def test_update_scan(self, db):
        """Integration: Scan aktualisieren"""
        # Scan erstellen
        scan_id = db.create_scan({"scan_id": "scan-456", "target": "test.com", "status": "queued"})

        # Status aktualisieren
        db.update_scan(scan_id, {"status": "running", "progress": 50})

        # Prüfen
        scan = db.get_scan(scan_id)
        assert scan["status"] == "running"
        assert scan["progress"] == 50

    def test_delete_scan(self, db):
        """Integration: Scan löschen"""
        # Scan erstellen
        scan_id = db.create_scan({"scan_id": "scan-789", "target": "delete.com"})

        # Löschen
        result = db.delete_scan(scan_id)

        assert result is True

        # Sollte nicht mehr existieren
        scan = db.get_scan(scan_id)
        assert scan is None

    def test_list_scans_with_pagination(self, db):
        """Integration: Scans mit Pagination auflisten"""
        # Mehrere Scans erstellen
        for i in range(20):
            db.create_scan({"scan_id": f"scan-{i}", "target": f"target{i}.com", "created_at": datetime.now().isoformat()})

        # Seite 1 (10 Einträge)
        scans_page1 = db.list_scans(limit=10, offset=0)
        assert len(scans_page1) == 10

        # Seite 2 (10 Einträge)
        scans_page2 = db.list_scans(limit=10, offset=10)
        assert len(scans_page2) == 10

    def test_create_finding(self, db):
        """Integration: Finding erstellen"""
        finding_data = {
            "finding_id": "finding-123",
            "scan_id": "scan-123",
            "title": "Test Vulnerability",
            "severity": "high",
            "description": "Test description",
        }

        finding_id = db.create_finding(finding_data)

        assert finding_id is not None

        # Finding abrufen
        finding = db.get_finding(finding_id)
        assert finding["title"] == "Test Vulnerability"

    def test_findings_by_severity(self, db):
        """Integration: Findings nach Schweregrad filtern"""
        # Findings mit verschiedenen Schweregraden erstellen
        severities = ["critical", "high", "medium", "low", "info"]

        for i, severity in enumerate(severities):
            db.create_finding(
                {"finding_id": f"finding-{i}", "scan_id": "scan-123", "title": f"Finding {i}", "severity": severity}
            )

        # Nur kritische Findings
        critical = db.get_findings_by_severity("critical")
        assert len(critical) == 1

        # High und Critical
        high_critical = db.get_findings_by_severity(["high", "critical"])
        assert len(high_critical) == 2


class TestTransactions:
    """Integration Tests für Transaktionen"""

    @pytest.fixture
    def db(self):
        """Fixture für initialisierte Datenbank"""
        from core.database import DatabaseManager

        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        db = DatabaseManager(f"sqlite:///{path}")
        db.initialize()

        yield db

        db.close()
        os.unlink(path)

    def test_transaction_commit(self, db):
        """Integration: Transaktion wird committed"""
        with db.transaction() as tx:
            tx.execute("INSERT INTO scans (scan_id, target) VALUES (?, ?)", ("tx-scan-1", "tx-target.com"))

        # Sollte persistiert sein
        scan = db.get_scan("tx-scan-1")
        assert scan is not None

    def test_transaction_rollback(self, db):
        """Integration: Transaktion wird bei Fehler zurückgerollt"""
        try:
            with db.transaction() as tx:
                tx.execute("INSERT INTO scans (scan_id, target) VALUES (?, ?)", ("tx-scan-2", "tx-target.com"))
                # Fehler provozieren
                raise Exception("Test error")
        except Exception:
            pass

        # Sollte nicht persistiert sein
        scan = db.get_scan("tx-scan-2")
        assert scan is None

    def test_nested_transactions(self, db):
        """Integration: Verschachtelte Transaktionen"""
        with db.transaction() as tx1:
            tx1.execute("INSERT INTO scans (scan_id, target) VALUES (?, ?)", ("nested-1", "target1.com"))

            with db.transaction() as tx2:
                tx2.execute("INSERT INTO scans (scan_id, target) VALUES (?, ?)", ("nested-2", "target2.com"))

        # Beide sollten persistiert sein
        assert db.get_scan("nested-1") is not None
        assert db.get_scan("nested-2") is not None


class TestMigrations:
    """Integration Tests für Datenbank-Migrationen"""

    def test_migration_up(self):
        """Integration: Migration wird angewendet"""
        from core.database import run_migration

        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        try:
            db_url = f"sqlite:///{path}"

            # Migration ausführen
            result = run_migration(db_url, "upgrade", "head")

            assert result is True

            # Prüfen ob Schema aktualisiert wurde
            from core.database import DatabaseManager

            db = DatabaseManager(db_url)

            version = db.get_schema_version()
            assert version is not None

            db.close()
        finally:
            os.unlink(path)

    def test_migration_down(self):
        """Integration: Migration wird zurückgerollt"""
        from core.database import run_migration

        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        try:
            db_url = f"sqlite:///{path}"

            # Zuerst upgrade
            run_migration(db_url, "upgrade", "head")

            # Dann downgrade
            result = run_migration(db_url, "downgrade", "-1")

            assert result is True
        finally:
            os.unlink(path)


class TestBackupRestore:
    """Integration Tests für Backup und Restore"""

    @pytest.fixture
    def db(self):
        """Fixture für initialisierte Datenbank mit Daten"""
        from core.database import DatabaseManager

        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        db = DatabaseManager(f"sqlite:///{path}")
        db.initialize()

        # Testdaten einfügen
        for i in range(10):
            db.create_scan({"scan_id": f"backup-scan-{i}", "target": f"backup{i}.com"})

        yield db, path

        db.close()
        os.unlink(path)

    def test_database_backup(self, db):
        """Integration: Datenbank-Backup"""
        database, original_path = db

        backup_path = original_path + ".backup"

        # Backup erstellen
        result = database.backup(backup_path)

        assert result is True
        assert os.path.exists(backup_path)

        # Backup sollte gleiche Daten haben
        backup_db = sqlite3.connect(backup_path)
        cursor = backup_db.cursor()
        cursor.execute("SELECT COUNT(*) FROM scans")
        count = cursor.fetchone()[0]
        assert count == 10
        backup_db.close()

        os.unlink(backup_path)

    def test_database_restore(self, db):
        """Integration: Datenbank-Restore"""
        database, original_path = db

        backup_path = original_path + ".backup"
        database.backup(backup_path)

        # Original löschen
        database.execute("DELETE FROM scans")

        # Restore
        result = database.restore(backup_path)

        assert result is True

        # Daten sollten wieder da sein
        scans = database.list_scans()
        assert len(scans) == 10

        os.unlink(backup_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=core.database", "--cov-report=term-missing"])
