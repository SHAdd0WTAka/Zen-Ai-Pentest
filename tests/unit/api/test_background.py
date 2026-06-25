"""
Tests for api/background.py — background task functions.
"""

import sys
from datetime import datetime, timezone
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Inject a mock module for agents.react_agent before any background imports
_mock_react_mod = ModuleType("agents.react_agent")
_mock_react_mod.ReActAgent = MagicMock()
_mock_react_mod.ReActAgentConfig = MagicMock()
sys.modules["agents.react_agent"] = _mock_react_mod


# ============================================================================
# parse_tool_findings
# ============================================================================


class TestParseToolFindings:
    def test_empty_result_returns_empty_list(self):
        from api.background import parse_tool_findings

        result = parse_tool_findings("nmap", "127.0.0.1", "")
        assert result == []

    def test_short_result_returns_empty_list(self):
        from api.background import parse_tool_findings

        result = parse_tool_findings("nmap", "127.0.0.1", "short")
        assert result == []

    def test_meaningful_result_creates_finding(self):
        from api.background import parse_tool_findings

        result = parse_tool_findings("nmap", "192.168.1.1", "Open ports: 22, 80, 443. Vulnerable service detected.")
        assert len(result) == 1
        finding = result[0]
        assert "nmap" in finding["title"].lower()
        assert finding["target"] == "192.168.1.1"
        assert finding["tool"] == "nmap"

    def test_critical_keyword_sets_high_severity(self):
        from api.background import parse_tool_findings

        result = parse_tool_findings("sqlmap", "example.com", "CRITICAL: SQL injection found at /login")
        assert len(result) == 1
        assert result[0]["severity"] == "critical"

    def test_high_severity_keywords(self):
        from api.background import parse_tool_findings

        result = parse_tool_findings("nikto", "example.com", "CVE-2024-1234 detected")
        assert len(result) == 1
        assert result[0]["severity"] == "high"

    def test_info_severity_for_no_match(self):
        from api.background import parse_tool_findings

        result = parse_tool_findings("tshark", "example.com", "Gathering network statistics...")
        assert len(result) == 1
        assert result[0]["severity"] == "info"


# ============================================================================
# save_finding_to_db
# ============================================================================


class TestSaveFindingToDb:
    def test_successful_save(self):
        from api.background import save_finding_to_db

        db = MagicMock()
        finding = {
            "title": "Open port 22",
            "description": "SSH port is open",
            "severity": "medium",
            "evidence": "port 22 open",
            "tool": "nmap",
            "target": "10.0.0.1",
        }

        result = save_finding_to_db(db, scan_id=1, finding=finding)
        assert result is not None
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_db_error_rolls_back(self):
        from api.background import save_finding_to_db

        db = MagicMock()
        db.commit.side_effect = Exception("DB failure")

        finding = {"title": "Test finding", "description": "desc"}

        with pytest.raises(Exception, match="DB failure"):
            save_finding_to_db(db, scan_id=1, finding=finding)
        db.rollback.assert_called_once()

    def test_minimal_finding_data(self):
        from api.background import save_finding_to_db

        db = MagicMock()
        finding = {}

        result = save_finding_to_db(db, scan_id=42, finding=finding)
        assert result is not None
        db.add.assert_called_once()
        db.commit.assert_called_once()


# ============================================================================
# calculate_next_run
# ============================================================================


class TestCalculateNextRun:
    def test_once_frequency_future_time(self):
        from api.background import calculate_next_run

        future_hour = (datetime.now(timezone.utc).hour + 1) % 24
        next_run = calculate_next_run("once", f"{future_hour}:00")
        assert next_run > datetime.now(timezone.utc)

    def test_once_frequency_past_time_adds_day(self):
        from api.background import calculate_next_run

        next_run = calculate_next_run("once", "00:01")
        assert next_run > datetime.now(timezone.utc)

    def test_daily_frequency(self):
        from api.background import calculate_next_run

        next_run = calculate_next_run("daily", "12:00")
        assert next_run.hour == 12
        assert next_run.minute == 0

    def test_weekly_frequency_with_day(self):
        from api.background import calculate_next_run

        next_run = calculate_next_run("weekly", "10:30", day=0)
        assert next_run.weekday() == 0
        assert next_run.hour == 10
        assert next_run.minute == 30

    def test_monthly_frequency(self):
        from api.background import calculate_next_run

        next_run = calculate_next_run("monthly", "08:00")
        assert next_run.hour == 8
        assert next_run.minute == 0


# ============================================================================
# run_scan_task
# ============================================================================


class TestRunScanTask:
    @pytest.mark.asyncio
    async def test_successful_scan_execution(self):
        mock_agent_cls = MagicMock()
        agent_instance = MagicMock()
        agent_instance.run.return_value = {
            "findings": [{"tool": "nmap", "result": "port 22 open"}],
            "final_message": "Scan completed",
            "iterations": 5,
        }
        mock_agent_cls.return_value = agent_instance

        sys.modules["agents.react_agent"].ReActAgent = mock_agent_cls

        with (
            patch("api.background.SessionLocal") as mock_session_local,
            patch("api.background.update_scan_status") as mock_update,
            patch("api.background.create_finding") as mock_create_finding,
        ):
            db = MagicMock()
            mock_session_local.return_value = db

            mock_ws = AsyncMock()
            with patch("api.main.ws_manager", mock_ws):
                from api.background import run_scan_task

                await run_scan_task(scan_id=1, scan_config={"target": "10.0.0.1", "objective": "test"})

            mock_update.assert_any_call(db, 1, "running")
            mock_update.assert_any_call(db, 1, "completed", {"result": "Scan completed", "iterations": 5})
            mock_create_finding.assert_called_once()
            db.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_scan_failure_updates_status(self):
        mock_agent_cls = MagicMock()
        agent_instance = MagicMock()
        agent_instance.run.side_effect = RuntimeError("Agent crashed")
        mock_agent_cls.return_value = agent_instance

        sys.modules["agents.react_agent"].ReActAgent = mock_agent_cls

        with (
            patch("api.background.SessionLocal") as mock_session_local,
            patch("api.background.update_scan_status") as mock_update,
        ):
            db = MagicMock()
            mock_session_local.return_value = db

            mock_ws = AsyncMock()
            with patch("api.main.ws_manager", mock_ws):
                from api.background import run_scan_task

                await run_scan_task(scan_id=2, scan_config={"target": "10.0.0.2"})

            call_args_list = mock_update.call_args_list
            assert any("failed" in str(c) for c in call_args_list)
            db.close.assert_called_once()


# ============================================================================
# execute_tool_task
# ============================================================================


class TestExecuteToolTask:
    @pytest.mark.asyncio
    async def test_tool_execution_success(self):
        with (
            patch("api.background.SessionLocal") as mock_session_local,
            patch("api.background.update_scan_status") as mock_update,
            patch("api.background.create_finding") as mock_create_finding,
            patch("tools.TOOL_REGISTRY", {"nmap": MagicMock(return_value="Scan results: OK")}),
        ):
            db = MagicMock()
            mock_session_local.return_value = db

            from api.background import execute_tool_task

            await execute_tool_task(scan_id=1, tool_name="nmap", target="10.0.0.1", parameters={})

            mock_update.assert_called_with(db, 1, "completed")
            mock_create_finding.assert_called_once()
            db.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_tool_not_found_raises_error(self):
        with (
            patch("api.background.SessionLocal") as mock_session_local,
            patch("api.background.update_scan_status") as mock_update,
            patch("tools.TOOL_REGISTRY", {}),
        ):
            db = MagicMock()
            mock_session_local.return_value = db

            from api.background import execute_tool_task

            await execute_tool_task(scan_id=1, tool_name="nonexistent", target="10.0.0.1", parameters={})

            db.close.assert_called_once()


# ============================================================================
# generate_report_task
# ============================================================================


class TestGenerateReportTask:
    @pytest.mark.asyncio
    async def test_pdf_report_generation(self):
        db = MagicMock()
        report_mock = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = report_mock

        with (
            patch("api.background.SessionLocal", return_value=db),
            patch("reports.generator.ReportGenerator") as mock_gen_cls,
        ):
            generator = MagicMock()
            generator.generate_pdf.return_value = "/tmp/report_1.pdf"
            mock_gen_cls.return_value = generator

            from api.background import generate_report_task

            await generate_report_task(report_id=1, scan_id=10, format="pdf")

            generator.generate_pdf.assert_called_once_with(10)
            assert report_mock.file_path == "/tmp/report_1.pdf"
            assert report_mock.status == "completed"
            db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_html_report_generation(self):
        db = MagicMock()
        report_mock = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = report_mock

        with (
            patch("api.background.SessionLocal", return_value=db),
            patch("reports.generator.ReportGenerator") as mock_gen_cls,
        ):
            generator = MagicMock()
            generator.generate_html.return_value = "/tmp/report_1.html"
            mock_gen_cls.return_value = generator

            from api.background import generate_report_task

            await generate_report_task(report_id=1, scan_id=10, format="html")

            generator.generate_html.assert_called_once_with(10)

    @pytest.mark.asyncio
    async def test_report_generation_failure_sets_status(self):
        db = MagicMock()
        report_mock = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = report_mock

        with (
            patch("api.background.SessionLocal", return_value=db),
            patch("reports.generator.ReportGenerator") as mock_gen_cls,
        ):
            generator = MagicMock()
            generator.generate_pdf.side_effect = RuntimeError("Generation failed")
            mock_gen_cls.return_value = generator

            from api.background import generate_report_task

            await generate_report_task(report_id=1, scan_id=10, format="pdf")

            assert report_mock.status == "failed"
            db.commit.assert_called_once()
