"""Unit tests for tools/sqlmap_integration.py"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.sqlmap_integration import SQLMapScanner, run_sqlmap, run_sqlmap_form


class TestSQLMapScannerInit:
    @patch("tools.sqlmap_integration.subprocess.run")
    def test_init_default_path(self, mock_run):
        mock_run.return_value.stdout = "1.6.0"
        scanner = SQLMapScanner("sqlmap")
        assert scanner.sqlmap_path == "sqlmap"

    @patch("tools.sqlmap_integration.subprocess.run")
    def test_init_custom_path(self, mock_run):
        mock_run.return_value.stdout = "1.6.0"
        scanner = SQLMapScanner("/custom/sqlmap")
        assert scanner.sqlmap_path == "/custom/sqlmap"

    @patch("tools.sqlmap_integration.subprocess.run")
    def test_check_installation_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "1.6.0\n"
        mock_run.return_value = mock_result
        scanner = SQLMapScanner("sqlmap")
        assert scanner.sqlmap_path == "sqlmap"
        mock_run.assert_called_once_with(["sqlmap", "--version"], capture_output=True, text=True)

    @patch("tools.sqlmap_integration.subprocess.run")
    def test_check_installation_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        with pytest.raises(RuntimeError, match="sqlmap nicht gefunden"):
            SQLMapScanner("sqlmap")


class TestSQLMapScannerScanUrl:
    def test_scan_url_builds_command(self):
        scanner = SQLMapScanner("sqlmap")
        with patch("tools.sqlmap_integration.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "test output"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            with patch("tools.sqlmap_integration.tempfile.mkdtemp", return_value="/tmp/sqlmap_test"):
                result = scanner.scan_url("http://test.com/page.php?id=1", risk=1, level=1, batch=True, dump=False)

            assert result["url"] == "http://test.com/page.php?id=1"
            assert result["vulnerable"] is False
            mock_run.assert_called_once()

    def test_scan_url_vulnerable_detected(self):
        scanner = SQLMapScanner("sqlmap")
        with patch("tools.sqlmap_integration.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "sqlmap identified the following injection points"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            with patch("tools.sqlmap_integration.tempfile.mkdtemp", return_value="/tmp/sqlmap_test"):
                result = scanner.scan_url("http://test.com/page.php?id=1")

            assert result["vulnerable"] is True

    def test_scan_url_timeout(self):
        scanner = SQLMapScanner("sqlmap")
        with patch("tools.sqlmap_integration.subprocess.run") as mock_run:
            import subprocess

            mock_run.side_effect = subprocess.TimeoutExpired(cmd="sqlmap", timeout=300)
            result = scanner.scan_url("http://test.com/page.php?id=1")
            assert "error" in result
            assert "Timeout" in result["error"]

    def test_scan_url_general_exception(self):
        scanner = SQLMapScanner("sqlmap")
        with patch("tools.sqlmap_integration.subprocess.run") as mock_run:
            mock_run.side_effect = RuntimeError("Connection refused")
            result = scanner.scan_url("http://test.com/page.php?id=1")
            assert "error" in result
            assert "Connection refused" in result["error"]

    def test_scan_url_with_dump(self):
        scanner = SQLMapScanner("sqlmap")
        with patch("tools.sqlmap_integration.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            with patch("tools.sqlmap_integration.tempfile.mkdtemp", return_value="/tmp/sqlmap_test"):
                result = scanner.scan_url("http://test.com/page.php?id=1", dump=True)
                assert result["url"] == "http://test.com/page.php?id=1"

    def test_scan_url_stdout_truncated(self):
        scanner = SQLMapScanner("sqlmap")
        with patch("tools.sqlmap_integration.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "A" * 10000
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            with patch("tools.sqlmap_integration.tempfile.mkdtemp", return_value="/tmp/sqlmap_test"):
                result = scanner.scan_url("http://test.com/page.php?id=1")
                assert len(result["stdout"]) <= 5000


class TestSQLMapScannerScanForm:
    def test_scan_form_success(self):
        scanner = SQLMapScanner("sqlmap")
        with patch("tools.sqlmap_integration.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "sqlmap identified"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            result = scanner.scan_form("http://test.com/login", "user=test&pass=test")
            assert result["vulnerable"] is True

    def test_scan_form_not_vulnerable(self):
        scanner = SQLMapScanner("sqlmap")
        with patch("tools.sqlmap_integration.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "all tested parameters are not injectable"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            result = scanner.scan_form("http://test.com/login", "user=test&pass=test")
            assert result["vulnerable"] is False

    def test_scan_form_exception(self):
        scanner = SQLMapScanner("sqlmap")
        with patch("tools.sqlmap_integration.subprocess.run") as mock_run:
            mock_run.side_effect = RuntimeError("Error")
            result = scanner.scan_form("http://test.com/login", "user=test")
            assert "error" in result


class TestSQLMapScannerGetDatabases:
    def test_get_databases(self):
        scanner = SQLMapScanner("sqlmap")
        with patch("tools.sqlmap_integration.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "available databases [2]:\n[*] information_schema\n[*] mysql\n"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            result = scanner.get_databases("http://test.com/page.php?id=1")
            assert isinstance(result, list)

    def test_get_databases_exception(self):
        scanner = SQLMapScanner("sqlmap")
        with patch("tools.sqlmap_integration.subprocess.run") as mock_run:
            mock_run.side_effect = RuntimeError("Error")
            result = scanner.get_databases("http://test.com/page.php?id=1")
            assert result == []


class TestSQLMapFunctions:
    @pytest.mark.asyncio
    @patch("tools.sqlmap_integration.SQLMapScanner.scan_url")
    async def test_run_sqlmap(self, mock_scan_url):
        mock_scan_url.return_value = {"vulnerable": True, "url": "http://test.com"}
        result = await run_sqlmap("http://test.com", {"risk": 2})
        assert result["vulnerable"] is True

    @pytest.mark.asyncio
    @patch("tools.sqlmap_integration.SQLMapScanner.scan_form")
    async def test_run_sqlmap_form(self, mock_scan_form):
        mock_scan_form.return_value = {"vulnerable": True}
        result = await run_sqlmap_form("http://test.com", "data=test")
        assert result["vulnerable"] is True


class TestSQLMapScannerDirectUse:
    def test_scan_url_via_scan_url(self):
        scanner = SQLMapScanner("sqlmap")
        scanner.check_installation = MagicMock()
        with patch.object(scanner, "check_installation"):
            scanner.check_installation = MagicMock()
            with patch("tools.sqlmap_integration.subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.stdout = "sqlmap identified"
                mock_result.stderr = ""
                mock_run.return_value = mock_result
                with patch("tools.sqlmap_integration.tempfile.mkdtemp", return_value="/tmp/sqlmap"):
                    result = scanner.scan_url("http://test.com?id=1")
                    assert result["vulnerable"] is True

    def test_scan_url_not_vulnerable(self):
        scanner = SQLMapScanner("sqlmap")
        scanner.check_installation = MagicMock()
        with patch("tools.sqlmap_integration.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "all tested parameters are not injectable"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            with patch("tools.sqlmap_integration.tempfile.mkdtemp", return_value="/tmp/sqlmap"):
                result = scanner.scan_url("http://test.com?id=1")
                assert result["vulnerable"] is False

    def test_scan_url_error(self):
        scanner = SQLMapScanner("sqlmap")
        scanner.check_installation = MagicMock()
        with patch("tools.sqlmap_integration.subprocess.run") as mock_run:
            mock_run.side_effect = RuntimeError("Connection failed")
            with patch("tools.sqlmap_integration.tempfile.mkdtemp", return_value="/tmp/sqlmap"):
                result = scanner.scan_url("http://test.com?id=1")
                assert "error" in result
                assert "Connection failed" in result["error"]

    def test_scan_form_vulnerable(self):
        scanner = SQLMapScanner("sqlmap")
        scanner.check_installation = MagicMock()
        with patch("tools.sqlmap_integration.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "sqlmap identified"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            result = scanner.scan_form("http://test.com/login", "user=test")
            assert result["vulnerable"] is True

    def test_scan_form_not_vulnerable(self):
        scanner = SQLMapScanner("sqlmap")
        scanner.check_installation = MagicMock()
        with patch("tools.sqlmap_integration.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "not injectable"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            result = scanner.scan_form("http://test.com/login", "user=test")
            assert result["vulnerable"] is False
