"""Tests for Zen-AI-Pentest Bridge Service"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.bridge import ZenAIPentestBridge, zen_bridge


@pytest.fixture
def bridge():
    return ZenAIPentestBridge()


@pytest.mark.asyncio
async def test_health_check_success(bridge):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}
    bridge.client.get = AsyncMock(return_value=mock_response)

    result = await bridge.health_check()
    assert result["status"] == "connected"
    assert result["api_status"] == 200


@pytest.mark.asyncio
async def test_health_check_error(bridge):
    bridge.client.get = AsyncMock(side_effect=Exception("Connection refused"))
    result = await bridge.health_check()
    assert result["status"] == "disconnected"
    assert "Connection refused" in result["error"]


@pytest.mark.asyncio
async def test_health_check_non_200(bridge):
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.json.return_value = {}
    bridge.client.get = AsyncMock(return_value=mock_response)

    result = await bridge.health_check()
    assert result["status"] == "error"
    assert result["api_status"] == 503


@pytest.mark.asyncio
async def test_create_scan(bridge):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "scan-123"}
    bridge.client.post = AsyncMock(return_value=mock_response)

    result = await bridge.create_scan("example.com", scan_type="full")
    assert result["id"] == "scan-123"


@pytest.mark.asyncio
async def test_get_scan(bridge):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "scan-123", "status": "running"}
    bridge.client.get = AsyncMock(return_value=mock_response)

    result = await bridge.get_scan("scan-123")
    assert result["id"] == "scan-123"


@pytest.mark.asyncio
async def test_get_scan_results(bridge):
    mock_response = MagicMock()
    mock_response.json.return_value = {"findings": []}
    bridge.client.get = AsyncMock(return_value=mock_response)

    result = await bridge.get_scan_results("scan-123")
    assert "findings" in result


@pytest.mark.asyncio
async def test_list_scans(bridge):
    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": "scan-1"}]
    bridge.client.get = AsyncMock(return_value=mock_response)

    result = await bridge.list_scans()
    assert len(result) == 1


@pytest.mark.asyncio
async def test_list_scans_with_status(bridge):
    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": "scan-1", "status": "completed"}]
    bridge.client.get = AsyncMock(return_value=mock_response)

    result = await bridge.list_scans(status="completed")
    assert len(result) == 1


@pytest.mark.asyncio
async def test_cancel_scan(bridge):
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "cancelled"}
    bridge.client.post = AsyncMock(return_value=mock_response)

    result = await bridge.cancel_scan("scan-123")
    assert result["status"] == "cancelled"


@pytest.mark.asyncio
async def test_get_tools(bridge):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"name": "nmap"}]
    bridge.client.get = AsyncMock(return_value=mock_response)

    result = await bridge.get_tools()
    assert len(result) == 1
    assert result[0]["name"] == "nmap"


@pytest.mark.asyncio
async def test_get_tools_error(bridge):
    mock_response = MagicMock()
    mock_response.status_code = 500
    bridge.client.get = AsyncMock(return_value=mock_response)

    result = await bridge.get_tools()
    assert result == []


@pytest.mark.asyncio
async def test_run_tool(bridge):
    mock_response = MagicMock()
    mock_response.json.return_value = {"output": "pwned"}
    bridge.client.post = AsyncMock(return_value=mock_response)

    result = await bridge.run_tool("nmap", "example.com")
    assert result["output"] == "pwned"


@pytest.mark.asyncio
async def test_get_reports(bridge):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": "report-1"}]
    bridge.client.get = AsyncMock(return_value=mock_response)

    result = await bridge.get_reports()
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_reports_with_scan_id(bridge):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": "report-1", "scan_id": "scan-123"}]
    bridge.client.get = AsyncMock(return_value=mock_response)

    result = await bridge.get_reports(scan_id="scan-123")
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_reports_error(bridge):
    mock_response = MagicMock()
    mock_response.status_code = 500
    bridge.client.get = AsyncMock(return_value=mock_response)

    result = await bridge.get_reports()
    assert result == []


@pytest.mark.asyncio
async def test_generate_report(bridge):
    mock_response = MagicMock()
    mock_response.json.return_value = {"url": "http://report.pdf"}
    bridge.client.post = AsyncMock(return_value=mock_response)

    result = await bridge.generate_report("scan-123", format="pdf")
    assert result["url"] == "http://report.pdf"


@pytest.mark.asyncio
async def test_generate_report_with_template(bridge):
    mock_response = MagicMock()
    mock_response.json.return_value = {"url": "http://report.pdf"}
    bridge.client.post = AsyncMock(return_value=mock_response)

    result = await bridge.generate_report("scan-123", format="html", template="detailed")
    assert result["url"] == "http://report.pdf"


def test_global_bridge():
    assert zen_bridge is not None
    assert isinstance(zen_bridge, ZenAIPentestBridge)
