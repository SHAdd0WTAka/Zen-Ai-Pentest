"""
Integration Tests for API Endpoints
"""

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


class TestAPIHealth:
    """Test API Health Endpoints"""

    def test_health_endpoint(self):
        """Test health check endpoint"""
        import asyncio

        from api.routes.v1.health import health_check

        result = asyncio.run(health_check())
        assert result["status"] == "healthy"
        assert "version" in result

    def test_info_endpoint(self):
        """Test info endpoint"""
        import asyncio

        from api.routes.v1.health import api_info

        result = asyncio.run(api_info())
        assert "name" in result
        assert "version" in result


class TestAPITools:
    """Test API Tools Endpoints"""

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test list tools endpoint"""
        from api.routes.v1.tools import list_tools

        result = await list_tools()
        assert "tools" in result
        assert len(result["tools"]) > 0


class TestAPIStats:
    """Test API Stats Endpoints"""

    @pytest.mark.asyncio
    async def test_stats_overview(self):
        """Test stats overview endpoint"""
        from api.routes.v1.stats import get_stats_overview

        result = await get_stats_overview()
        assert "total_scans" in result
        assert "total_findings" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
