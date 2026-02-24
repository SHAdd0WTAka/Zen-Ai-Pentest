"""
Tests for OSINT Super Module
Username, Email & Domain Investigation
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from modules.osint_super import OSINTSuperModule, OSINTSuperResult


# Fixtures
@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def osint_module(temp_output_dir):
    """Create an OSINTSuperModule instance"""
    with (
        patch("modules.osint_super.SherlockIntegration") as mock_sherlock,
        patch("modules.osint_super.IgnorantIntegration") as mock_ignorant,
        patch("modules.osint_super.SubfinderIntegration") as mock_subfinder,
        patch("modules.osint_super.AmassIntegration") as mock_amass,
        patch("modules.osint_super.WhatWebIntegration") as mock_whatweb,
    ):

        # Setup mocks
        mock_sherlock.return_value = Mock()
        mock_ignorant.return_value = Mock()
        mock_subfinder.return_value = Mock()
        mock_amass.return_value = Mock()
        mock_whatweb.return_value = Mock()

        module = OSINTSuperModule(output_dir=temp_output_dir)
        yield module


@pytest.fixture
def mock_sherlock_result():
    """Create a mock Sherlock result"""
    result = Mock()
    result.success = True
    result.username = "testuser"
    result.found_sites = [
        {"site": "twitter", "url": "https://twitter.com/testuser"},
        {"site": "github", "url": "https://github.com/testuser"},
    ]
    result.total_sites = 400
    return result


@pytest.fixture
def mock_ignorant_result():
    """Create a mock Ignorant result"""
    result = Mock()
    result.success = True
    result.email = "test@example.com"
    result.username = "testuser"
    result.domain = "example.com"

    platform = Mock()
    platform.platform = "twitter"
    platform.url = "https://twitter.com/testuser"
    platform.exists = True
    result.found_platforms = [platform]
    result.total_checked = 120
    return result


@pytest.fixture
def mock_subfinder_result():
    """Create a mock Subfinder result"""
    result = Mock()
    result.subdomains = [
        "www.example.com",
        "api.example.com",
        "mail.example.com",
    ]
    return result


@pytest.fixture
def mock_amass_result():
    """Create a mock Amass result"""
    result = Mock()
    result.subdomains = [
        "dev.example.com",
        "staging.example.com",
        "admin.example.com",
    ]
    return result


@pytest.fixture
def mock_whatweb_result():
    """Create a mock WhatWeb result"""
    result = Mock()

    tech1 = Mock()
    tech1.name = "Apache"
    tech1.version = "2.4.41"
    tech1.category = "Web Server"

    tech2 = Mock()
    tech2.name = "PHP"
    tech2.version = "7.4"
    tech2.category = "Programming Language"

    result.technologies = [tech1, tech2]
    return result


# OSINTSuperModule Tests
class TestOSINTSuperModule:
    """Tests for OSINTSuperModule class"""

    def test_initialization(self, temp_output_dir):
        """Test OSINTSuperModule initialization"""
        with (
            patch("modules.osint_super.SherlockIntegration"),
            patch("modules.osint_super.IgnorantIntegration"),
            patch("modules.osint_super.SubfinderIntegration"),
            patch("modules.osint_super.AmassIntegration"),
            patch("modules.osint_super.WhatWebIntegration"),
        ):

            module = OSINTSuperModule(output_dir=temp_output_dir)
            assert module.output_dir == Path(temp_output_dir)
            assert module.output_dir.exists()

    @pytest.mark.asyncio
    async def test_investigate_username(
        self, osint_module, mock_sherlock_result
    ):
        """Test username investigation"""
        osint_module.sherlock.search = AsyncMock(
            return_value=mock_sherlock_result
        )

        result = await osint_module.investigate_username("testuser")

        assert result.target == "testuser"
        assert result.target_type == "username"
        assert result.social_media["success"] is True
        assert result.social_media["total_found"] == 2
        assert result.social_media["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_investigate_username_error(self, osint_module):
        """Test username investigation with error"""
        osint_module.sherlock.search = AsyncMock(
            side_effect=Exception("Search failed")
        )

        result = await osint_module.investigate_username("testuser")

        assert result.target == "testuser"
        assert result.target_type == "username"
        assert result.social_media["success"] is False
        assert "error" in result.social_media

    @pytest.mark.asyncio
    async def test_investigate_email(
        self, osint_module, mock_ignorant_result, mock_sherlock_result
    ):
        """Test email investigation"""
        osint_module.ignorant.check_email = AsyncMock(
            return_value=mock_ignorant_result
        )
        osint_module.sherlock.search = AsyncMock(
            return_value=mock_sherlock_result
        )

        result = await osint_module.investigate_email("test@example.com")

        assert result.target == "test@example.com"
        assert result.target_type == "email"
        assert result.email_check["success"] is True
        assert result.email_check["username"] == "testuser"
        assert result.social_media["success"] is True

    @pytest.mark.asyncio
    async def test_investigate_email_no_username(self, osint_module):
        """Test email investigation when no username can be extracted"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.username = None
        mock_result.found_platforms = []
        mock_result.total_checked = 120

        osint_module.ignorant.check_email = AsyncMock(return_value=mock_result)

        result = await osint_module.investigate_email("test@example.com")

        assert result.target == "test@example.com"
        assert result.target_type == "email"
        assert result.email_check["success"] is True
        # Should not try social media search without username
        assert result.social_media == {}

    @pytest.mark.asyncio
    async def test_investigate_email_ignorant_error(self, osint_module):
        """Test email investigation when Ignorant fails"""
        osint_module.ignorant.check_email = AsyncMock(
            side_effect=Exception("API Error")
        )

        result = await osint_module.investigate_email("test@example.com")

        assert result.target == "test@example.com"
        assert result.target_type == "email"
        assert result.email_check["success"] is False
        assert "error" in result.email_check

    @pytest.mark.asyncio
    async def test_investigate_domain(
        self,
        osint_module,
        mock_subfinder_result,
        mock_amass_result,
        mock_whatweb_result,
    ):
        """Test domain investigation"""
        osint_module.subfinder.enumerate = AsyncMock(
            return_value=mock_subfinder_result
        )
        osint_module.amass.enumerate = AsyncMock(
            return_value=mock_amass_result
        )
        osint_module.whatweb.scan = AsyncMock(return_value=mock_whatweb_result)

        result = await osint_module.investigate_domain("example.com")

        assert result.target == "example.com"
        assert result.target_type == "domain"
        # Should combine subdomains from both tools
        assert (
            result.subdomains["total"] == 6
        )  # 3 from subfinder + 3 from amass
        assert result.subdomains["success"] is True
        assert result.technologies["success"] is True
        assert len(result.technologies["technologies"]) == 2

    @pytest.mark.asyncio
    async def test_investigate_domain_subfinder_error(
        self, osint_module, mock_amass_result, mock_whatweb_result
    ):
        """Test domain investigation when Subfinder fails"""
        osint_module.subfinder.enumerate = AsyncMock(
            side_effect=Exception("Subfinder failed")
        )
        osint_module.amass.enumerate = AsyncMock(
            return_value=mock_amass_result
        )
        osint_module.whatweb.scan = AsyncMock(return_value=mock_whatweb_result)

        result = await osint_module.investigate_domain("example.com")

        assert result.target == "example.com"
        assert result.target_type == "domain"
        # Should still have subdomains from Amass
        assert result.subdomains["total"] == 3

    @pytest.mark.asyncio
    async def test_investigate_domain_amass_error(
        self, osint_module, mock_subfinder_result, mock_whatweb_result
    ):
        """Test domain investigation when Amass fails"""
        osint_module.subfinder.enumerate = AsyncMock(
            return_value=mock_subfinder_result
        )
        osint_module.amass.enumerate = AsyncMock(
            side_effect=Exception("Amass failed")
        )
        osint_module.whatweb.scan = AsyncMock(return_value=mock_whatweb_result)

        result = await osint_module.investigate_domain("example.com")

        assert result.target == "example.com"
        assert result.target_type == "domain"
        # Should still have subdomains from Subfinder
        assert result.subdomains["total"] == 3

    @pytest.mark.asyncio
    async def test_investigate_domain_whatweb_error(
        self, osint_module, mock_subfinder_result, mock_amass_result
    ):
        """Test domain investigation when WhatWeb fails"""
        osint_module.subfinder.enumerate = AsyncMock(
            return_value=mock_subfinder_result
        )
        osint_module.amass.enumerate = AsyncMock(
            return_value=mock_amass_result
        )
        osint_module.whatweb.scan = AsyncMock(
            side_effect=Exception("WhatWeb failed")
        )

        result = await osint_module.investigate_domain("example.com")

        assert result.target == "example.com"
        assert result.target_type == "domain"
        assert result.subdomains["success"] is True
        assert result.technologies["success"] is False
        assert "error" in result.technologies


# Summary Generation Tests
class TestSummaryGeneration:
    """Tests for summary generation methods"""

    def test_generate_username_summary_high_risk(
        self, osint_module, mock_sherlock_result
    ):
        """Test username summary with high risk (many accounts)"""
        result = OSINTSuperResult(
            target="testuser",
            target_type="username",
            timestamp=datetime.now().isoformat(),
        )
        # Create many found accounts
        result.social_media = {
            "found_accounts": [{"site": f"site{i}"} for i in range(25)],
        }

        summary = osint_module._generate_username_summary(result)

        assert summary["target_type"] == "username"
        assert summary["target"] == "testuser"
        assert summary["risk_level"] == "high"
        assert summary["accounts_found"] == 25
        assert len(summary["recommendations"]) > 0

    def test_generate_username_summary_medium_risk(self, osint_module):
        """Test username summary with medium risk"""
        result = OSINTSuperResult(
            target="testuser",
            target_type="username",
            timestamp=datetime.now().isoformat(),
        )
        result.social_media = {
            "found_accounts": [{"site": f"site{i}"} for i in range(10)],
        }

        summary = osint_module._generate_username_summary(result)

        assert summary["risk_level"] == "medium"
        assert summary["accounts_found"] == 10

    def test_generate_username_summary_low_risk(self, osint_module):
        """Test username summary with low risk"""
        result = OSINTSuperResult(
            target="testuser",
            target_type="username",
            timestamp=datetime.now().isoformat(),
        )
        result.social_media = {
            "found_accounts": [{"site": "twitter"}],
        }

        summary = osint_module._generate_username_summary(result)

        assert summary["risk_level"] == "low"
        assert summary["accounts_found"] == 1

    def test_generate_username_summary_no_accounts(self, osint_module):
        """Test username summary with no accounts found"""
        result = OSINTSuperResult(
            target="testuser",
            target_type="username",
            timestamp=datetime.now().isoformat(),
        )
        result.social_media = {"found_accounts": []}

        summary = osint_module._generate_username_summary(result)

        assert summary["risk_level"] == "low"
        assert summary["accounts_found"] == 0
        assert summary["recommendations"] == []

    def test_generate_email_summary_high_risk(self, osint_module):
        """Test email summary with high risk"""
        result = OSINTSuperResult(
            target="test@example.com",
            target_type="email",
            timestamp=datetime.now().isoformat(),
        )
        result.email_check = {"total_found": 15}
        result.social_media = {"total_found": 12}

        summary = osint_module._generate_email_summary(result)

        assert summary["risk_level"] == "high"
        assert summary["email_platforms"] == 15
        assert summary["social_accounts"] == 12

    def test_generate_email_summary_medium_risk(self, osint_module):
        """Test email summary with medium risk"""
        result = OSINTSuperResult(
            target="test@example.com",
            target_type="email",
            timestamp=datetime.now().isoformat(),
        )
        result.email_check = {"total_found": 5}
        result.social_media = {"total_found": 0}

        summary = osint_module._generate_email_summary(result)

        assert summary["risk_level"] == "medium"

    def test_generate_email_summary_low_risk(self, osint_module):
        """Test email summary with low risk"""
        result = OSINTSuperResult(
            target="test@example.com",
            target_type="email",
            timestamp=datetime.now().isoformat(),
        )
        result.email_check = {"total_found": 0}
        result.social_media = {"total_found": 0}

        summary = osint_module._generate_email_summary(result)

        assert summary["risk_level"] == "low"
        assert summary["recommendations"] == []

    def test_generate_domain_summary_high_risk(self, osint_module):
        """Test domain summary with high risk"""
        result = OSINTSuperResult(
            target="example.com",
            target_type="domain",
            timestamp=datetime.now().isoformat(),
        )
        result.subdomains = {"total": 150}
        result.technologies = {
            "technologies": [{"name": "Apache"}, {"name": "PHP"}]
        }

        summary = osint_module._generate_domain_summary(result)

        assert summary["risk_level"] == "high"
        assert summary["subdomains"] == 150
        assert summary["attack_surface"] == "large"
        assert len(summary["recommendations"]) > 0

    def test_generate_domain_summary_medium_risk(self, osint_module):
        """Test domain summary with medium risk"""
        result = OSINTSuperResult(
            target="example.com",
            target_type="domain",
            timestamp=datetime.now().isoformat(),
        )
        result.subdomains = {"total": 30}
        result.technologies = {"technologies": [{"name": "Nginx"}]}

        summary = osint_module._generate_domain_summary(result)

        assert summary["risk_level"] == "medium"
        assert summary["attack_surface"] == "medium"

    def test_generate_domain_summary_low_risk(self, osint_module):
        """Test domain summary with low risk"""
        result = OSINTSuperResult(
            target="example.com",
            target_type="domain",
            timestamp=datetime.now().isoformat(),
        )
        result.subdomains = {"total": 5}
        result.technologies = {"technologies": []}

        summary = osint_module._generate_domain_summary(result)

        assert summary["risk_level"] == "low"
        assert summary["attack_surface"] == "small"
        assert summary["recommendations"] == []


# Report Tests
class TestReports:
    """Tests for report generation"""

    def test_save_report(self, osint_module):
        """Test saving report to file"""
        result = OSINTSuperResult(
            target="testuser",
            target_type="username",
            timestamp=datetime.now().isoformat(),
            social_media={"total_found": 5},
        )
        result.summary = {"risk_level": "medium"}

        filepath = osint_module.save_report(
            result, filename="test_report.json"
        )

        assert filepath.exists()
        with open(filepath) as f:
            data = json.load(f)
            assert data["target"] == "testuser"
            assert data["target_type"] == "username"

    def test_save_report_auto_filename(self, osint_module):
        """Test saving report with auto-generated filename"""
        result = OSINTSuperResult(
            target="test@example.com",
            target_type="email",
            timestamp=datetime.now().isoformat(),
        )
        result.summary = {}

        filepath = osint_module.save_report(result)

        assert filepath.exists()
        assert "test_at_example_com" in filepath.name

    def test_save_report_with_special_chars(self, osint_module):
        """Test saving report with special characters in target"""
        result = OSINTSuperResult(
            target="user@domain.co.uk",
            target_type="email",
            timestamp=datetime.now().isoformat(),
        )
        result.summary = {}

        filepath = osint_module.save_report(result)

        assert filepath.exists()
        # Should replace dots and @
        assert "_at_" in filepath.name

    def test_print_report_username(
        self, osint_module, mock_sherlock_result, capsys
    ):
        """Test printing username report"""
        result = OSINTSuperResult(
            target="testuser",
            target_type="username",
            timestamp=datetime.now().isoformat(),
        )
        result.social_media = {
            "total_found": 2,
            "found_accounts": [
                {"site": "twitter", "url": "https://twitter.com/testuser"},
                {"site": "github", "url": "https://github.com/testuser"},
            ],
        }
        result.summary = {
            "risk_level": "medium",
            "recommendations": ["Check privacy settings"],
        }

        osint_module.print_report(result)

        captured = capsys.readouterr()
        assert "testuser" in captured.out
        assert "RISK LEVEL" in captured.out
        assert "twitter" in captured.out

    def test_print_report_email(self, osint_module, capsys):
        """Test printing email report"""
        result = OSINTSuperResult(
            target="test@example.com",
            target_type="email",
            timestamp=datetime.now().isoformat(),
        )
        result.email_check = {
            "total_found": 3,
            "found_platforms": [
                {"platform": "twitter", "url": "https://twitter.com"},
            ],
        }
        result.social_media = {"total_found": 2}
        result.summary = {"risk_level": "high"}

        osint_module.print_report(result)

        captured = capsys.readouterr()
        assert "test@example.com" in captured.out
        assert "Email Platforms" in captured.out

    def test_print_report_domain(self, osint_module, capsys):
        """Test printing domain report"""
        result = OSINTSuperResult(
            target="example.com",
            target_type="domain",
            timestamp=datetime.now().isoformat(),
        )
        result.subdomains = {"total": 25}
        result.technologies = {
            "technologies": [
                {"name": "Apache", "version": "2.4"},
                {"name": "PHP", "version": "7.4"},
            ],
        }
        result.summary = {"risk_level": "medium"}

        osint_module.print_report(result)

        captured = capsys.readouterr()
        assert "example.com" in captured.out
        assert "Subdomains" in captured.out
        assert "Apache" in captured.out


# Data Class Tests
class TestDataClasses:
    """Tests for data classes"""

    def test_osint_super_result_defaults(self):
        """Test OSINTSuperResult default values"""
        result = OSINTSuperResult(
            target="test",
            target_type="username",
            timestamp="2024-01-01T00:00:00",
        )

        assert result.social_media == {}
        assert result.email_check == {}
        assert result.subdomains == {}
        assert result.technologies == {}
        assert result.summary == {}

    def test_osint_super_result_with_data(self):
        """Test OSINTSuperResult with data"""
        result = OSINTSuperResult(
            target="test@example.com",
            target_type="email",
            timestamp="2024-01-01T00:00:00",
            social_media={"found": True},
            email_check={"valid": True},
            subdomains={"count": 10},
            technologies={"count": 5},
            summary={"risk": "medium"},
        )

        assert result.social_media["found"] is True
        assert result.email_check["valid"] is True


# Integration Tests
@pytest.mark.asyncio
async def test_full_investigation_workflow(temp_output_dir):
    """Test complete investigation workflow"""
    with (
        patch(
            "modules.osint_super.SherlockIntegration"
        ) as mock_sherlock_class,
        patch(
            "modules.osint_super.IgnorantIntegration"
        ) as mock_ignorant_class,
        patch(
            "modules.osint_super.SubfinderIntegration"
        ) as mock_subfinder_class,
        patch("modules.osint_super.AmassIntegration") as mock_amass_class,
        patch("modules.osint_super.WhatWebIntegration") as mock_whatweb_class,
    ):

        # Setup all mocks
        mock_sherlock = Mock()
        mock_sherlock.search = AsyncMock(
            return_value=Mock(
                success=True,
                username="testuser",
                found_sites=[{"site": "twitter"}],
                total_sites=400,
            )
        )
        mock_sherlock_class.return_value = mock_sherlock

        mock_ignorant = Mock()
        mock_ignorant.check_email = AsyncMock(
            return_value=Mock(
                success=True,
                email="test@example.com",
                username="testuser",
                domain="example.com",
                found_platforms=[],
                total_checked=120,
            )
        )
        mock_ignorant_class.return_value = mock_ignorant

        mock_subfinder = Mock()
        mock_subfinder.enumerate = AsyncMock(
            return_value=Mock(
                subdomains=["www.example.com"],
            )
        )
        mock_subfinder_class.return_value = mock_subfinder

        mock_amass = Mock()
        mock_amass.enumerate = AsyncMock(
            return_value=Mock(
                subdomains=["api.example.com"],
            )
        )
        mock_amass_class.return_value = mock_amass

        mock_whatweb = Mock()
        mock_whatweb.scan = AsyncMock(
            return_value=Mock(
                technologies=[
                    Mock(name="Apache", version="2.4", category="Web Server")
                ],
            )
        )
        mock_whatweb_class.return_value = mock_whatweb

        # Create module and run investigations
        module = OSINTSuperModule(output_dir=temp_output_dir)

        # Username investigation
        username_result = await module.investigate_username("testuser")
        assert username_result.target_type == "username"

        # Email investigation
        email_result = await module.investigate_email("test@example.com")
        assert email_result.target_type == "email"

        # Domain investigation
        domain_result = await module.investigate_domain("example.com")
        assert domain_result.target_type == "domain"
