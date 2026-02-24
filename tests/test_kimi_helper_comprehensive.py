"""
Comprehensive Tests for Kimi Helper Module

Tests for tools/kimi_helper.py
Target: 80%+ coverage
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Mock rich modules before importing kimi_helper
sys.modules["rich"] = MagicMock()
sys.modules["rich.console"] = MagicMock()
sys.modules["rich.markdown"] = MagicMock()
sys.modules["rich.panel"] = MagicMock()

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.kimi_helper import (
    PERSONAS,
    check_kimi_cli,
    check_kimi_logged_in,
    get_api_key,
    main,
    query_kimi_api,
    query_kimi_cli,
)

# ============================================================================
# Test Personas
# ============================================================================


class TestPersonas:
    """Test persona definitions"""

    def test_all_personas_exist(self):
        """Test that all 6 personas are defined"""
        expected_personas = [
            "recon",
            "exploit",
            "report",
            "audit",
            "network",
            "redteam",
        ]
        for persona in expected_personas:
            assert persona in PERSONAS

    def test_persona_structure(self):
        """Test each persona has required fields"""
        required_fields = ["name", "emoji", "desc", "prompt"]

        for key, persona in PERSONAS.items():
            for field in required_fields:
                assert (
                    field in persona
                ), f"Persona '{key}' missing field '{field}'"

    def test_recon_persona_content(self):
        """Test recon persona has appropriate content"""
        recon = PERSONAS["recon"]
        assert "OSINT" in recon["name"] or "Recon" in recon["name"]
        assert "Subdomain" in recon["desc"] or "OSINT" in recon["desc"]
        assert "OSINT" in recon["prompt"]
        assert "REGELN" in recon["prompt"]

    def test_exploit_persona_content(self):
        """Test exploit persona has appropriate content"""
        exploit = PERSONAS["exploit"]
        assert "Exploit" in exploit["name"]
        assert "Python" in exploit["desc"] or "POC" in exploit["desc"]
        assert "CODE-REGELN" in exploit["prompt"]

    def test_report_persona_content(self):
        """Test report persona has appropriate content"""
        report = PERSONAS["report"]
        assert "Report" in report["name"]
        assert "CVSS" in report["desc"] or "Technical" in report["name"]
        assert "STRUKTUR" in report["prompt"]

    def test_audit_persona_content(self):
        """Test audit persona has appropriate content"""
        audit = PERSONAS["audit"]
        assert "Audit" in audit["name"] or "Auditor" in audit["name"]
        assert "Code" in audit["name"] or "Review" in audit["desc"]
        assert "FOKUS" in audit["prompt"]

    def test_network_persona_content(self):
        """Test network persona has appropriate content"""
        network = PERSONAS["network"]
        assert "Network" in network["name"]
        assert "AD" in network["desc"] or "Active Directory" in network["desc"]
        assert "SPEZIALISIERUNG" in network["prompt"]

    def test_redteam_persona_content(self):
        """Test redteam persona has appropriate content"""
        redteam = PERSONAS["redteam"]
        assert "Red" in redteam["name"] or "RedTeam" in redteam["name"]
        assert "APT" in redteam["desc"] or "Adversary" in redteam["desc"]
        assert "APT" in redteam["prompt"]


# ============================================================================
# Test CLI Checks
# ============================================================================


class TestCLIChecks:
    """Test CLI availability checks"""

    @patch("tools.kimi_helper.subprocess.run")
    def test_check_kimi_cli_installed(self, mock_run):
        """Test CLI detection when installed"""
        mock_run.return_value = MagicMock(returncode=0)
        assert check_kimi_cli() is True
        mock_run.assert_called_once_with(
            ["kimi", "--version"], capture_output=True, check=True
        )

    @patch("tools.kimi_helper.subprocess.run")
    def test_check_kimi_cli_not_installed(self, mock_run):
        """Test CLI detection when not installed"""
        mock_run.side_effect = FileNotFoundError()
        assert check_kimi_cli() is False

    @patch("tools.kimi_helper.subprocess.run")
    def test_check_kimi_cli_called_process_error(self, mock_run):
        """Test CLI detection with CalledProcessError"""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "kimi")
        assert check_kimi_cli() is False

    @patch("tools.kimi_helper.Path")
    def test_check_kimi_logged_in_true(self, MockPath):
        """Test login check when logged in"""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        MockPath.home.return_value.__truediv__.return_value = mock_path

        assert check_kimi_logged_in() is True

    @patch("tools.kimi_helper.Path")
    def test_check_kimi_logged_in_false(self, MockPath):
        """Test login check when not logged in"""
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        MockPath.home.return_value.__truediv__.return_value = mock_path

        assert check_kimi_logged_in() is False


# ============================================================================
# Test API Key Retrieval
# ============================================================================


class TestAPIKey:
    """Test API key retrieval"""

    @patch.dict("os.environ", {"KIMI_API_KEY": "test-key-123"}, clear=True)
    def test_get_api_key_from_env(self):
        """Test getting API key from environment"""
        assert get_api_key() == "test-key-123"

    @patch.dict("os.environ", {}, clear=True)
    @patch("tools.kimi_helper.Path.exists")
    def test_get_api_key_from_file(self, mock_exists):
        """Test getting API key from .env file"""
        mock_exists.return_value = True
        with patch(
            "builtins.open",
            mock_open(read_data='export KIMI_API_KEY="file-key-456"'),
        ):
            key = get_api_key()
        assert key == "file-key-456"

    @patch.dict("os.environ", {}, clear=True)
    @patch("tools.kimi_helper.Path.exists")
    def test_get_api_key_not_found(self, mock_exists):
        """Test when API key is not found"""
        mock_exists.return_value = False
        assert get_api_key() is None

    @patch.dict("os.environ", {}, clear=True)
    @patch("tools.kimi_helper.Path.exists")
    def test_get_api_key_file_no_match(self, mock_exists):
        """Test .env file without API key"""
        mock_exists.return_value = True
        with patch("builtins.open", mock_open(read_data="OTHER_VAR=value\n")):
            key = get_api_key()
        assert key is None


# ============================================================================
# Test API Query
# ============================================================================


class TestAPIQuery:
    """Test API query functionality"""

    @patch("tools.kimi_helper.get_api_key")
    @patch("tools.kimi_helper.requests.post")
    def test_query_kimi_api_success(self, mock_post, mock_get_key):
        """Test successful API query"""
        mock_get_key.return_value = "test-key"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = query_kimi_api("test prompt", "system prompt")

        assert result == "Test response"
        mock_post.assert_called_once()

    @patch("tools.kimi_helper.get_api_key")
    def test_query_kimi_api_no_key(self, mock_get_key):
        """Test API query without key"""
        mock_get_key.return_value = None

        result = query_kimi_api("test prompt", "system prompt")

        assert result is None

    def test_query_kimi_api_no_requests(self):
        """Test API query when requests not available"""
        with patch("tools.kimi_helper.REQUESTS_AVAILABLE", False):
            with patch(
                "tools.kimi_helper.get_api_key", return_value="test-key"
            ):
                result = query_kimi_api("test prompt", "system prompt")

        assert result is None

    @patch("tools.kimi_helper.get_api_key")
    @patch("tools.kimi_helper.requests.post")
    def test_query_kimi_api_openrouter(self, mock_post, mock_get_key):
        """Test API query with OpenRouter key"""
        mock_get_key.return_value = "sk-or-test123"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "OpenRouter response"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = query_kimi_api("test prompt", "system prompt")

        assert result == "OpenRouter response"
        # Check OpenRouter-specific headers
        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert "HTTP-Referer" in headers
        assert "X-Title" in headers

    @patch("tools.kimi_helper.get_api_key")
    @patch("tools.kimi_helper.requests.post")
    def test_query_kimi_api_error(self, mock_post, mock_get_key):
        """Test API query with error"""
        mock_get_key.return_value = "test-key"
        mock_post.side_effect = Exception("Network error")

        result = query_kimi_api("test prompt", "system prompt")

        assert result is None

    @patch("tools.kimi_helper.get_api_key")
    @patch("tools.kimi_helper.requests.post")
    def test_query_kimi_api_with_custom_model(self, mock_post, mock_get_key):
        """Test API query with custom model"""
        mock_get_key.return_value = "test-key"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = query_kimi_api(
            "test prompt",
            "system prompt",
            model="custom-model",
            temperature=0.5,
        )

        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert data["model"] == "custom-model"
        assert data["temperature"] == 0.5


# ============================================================================
# Test CLI Query
# ============================================================================


class TestCLIQuery:
    """Test CLI query functionality"""

    @patch("tools.kimi_helper.check_kimi_cli")
    def test_query_kimi_cli_not_installed(self, mock_check):
        """Test CLI query when not installed"""
        mock_check.return_value = False

        result = query_kimi_cli("test prompt", "recon")

        assert result is None

    @patch("tools.kimi_helper.check_kimi_cli")
    @patch("tools.kimi_helper.check_kimi_logged_in")
    def test_query_kimi_cli_not_logged_in(self, mock_logged_in, mock_check):
        """Test CLI query when not logged in"""
        mock_check.return_value = True
        mock_logged_in.return_value = False

        result = query_kimi_cli("test prompt", "recon")

        assert result is None

    @patch("tools.kimi_helper.check_kimi_cli")
    @patch("tools.kimi_helper.check_kimi_logged_in")
    @patch("tools.kimi_helper.subprocess.run")
    def test_query_kimi_cli_success(
        self, mock_run, mock_logged_in, mock_check
    ):
        """Test successful CLI query"""
        mock_check.return_value = True
        mock_logged_in.return_value = True
        mock_run.return_value = MagicMock(stdout="CLI response")

        result = query_kimi_cli("test prompt", "recon")

        assert result == "CLI response"
        mock_run.assert_called_once()

    @patch("tools.kimi_helper.check_kimi_cli")
    @patch("tools.kimi_helper.check_kimi_logged_in")
    @patch("tools.kimi_helper.subprocess.run")
    def test_query_kimi_cli_with_persona(
        self, mock_run, mock_logged_in, mock_check
    ):
        """Test CLI query with persona system prompt"""
        mock_check.return_value = True
        mock_logged_in.return_value = True
        mock_run.return_value = MagicMock(stdout="Response with persona")

        result = query_kimi_cli("test prompt", "recon")

        # Check that system prompt was prepended
        call_args = mock_run.call_args
        prompt_input = call_args[1]["input"]
        assert "OSINT" in prompt_input

    @patch("tools.kimi_helper.check_kimi_cli")
    @patch("tools.kimi_helper.check_kimi_logged_in")
    @patch("tools.kimi_helper.subprocess.run")
    def test_query_kimi_cli_timeout(
        self, mock_run, mock_logged_in, mock_check
    ):
        """Test CLI query timeout"""
        import subprocess

        mock_check.return_value = True
        mock_logged_in.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired("kimi", 120)

        result = query_kimi_cli("test prompt", "recon")

        assert result is None


# ============================================================================
# Test Main Function
# ============================================================================


class TestMainFunction:
    """Test main function with various arguments"""

    @patch("tools.kimi_helper.sys.argv", ["kimi_helper.py"])
    def test_main_no_args(self):
        """Test main with no arguments"""
        # Should not raise exception
        main()

    @patch(
        "tools.kimi_helper.sys.argv",
        ["kimi_helper.py", "-p", "recon", "scan target"],
    )
    @patch("tools.kimi_helper.query_kimi_api")
    def test_main_api_mode(self, mock_query):
        """Test main in API mode"""
        mock_query.return_value = "Scan results"

        main()

        mock_query.assert_called_once()

    @patch(
        "tools.kimi_helper.sys.argv",
        ["kimi_helper.py", "--cli", "-p", "recon", "scan target"],
    )
    @patch("tools.kimi_helper.query_kimi_cli")
    def test_main_cli_mode(self, mock_query):
        """Test main in CLI mode"""
        mock_query.return_value = "CLI results"

        main()

        mock_query.assert_called_once()

    @patch("tools.kimi_helper.sys.argv", ["kimi_helper.py", "--check"])
    @patch("tools.kimi_helper.check_kimi_cli")
    @patch("tools.kimi_helper.check_kimi_logged_in")
    @patch("tools.kimi_helper.get_api_key")
    def test_main_check_cli_installed(
        self, mock_get_key, mock_logged_in, mock_check
    ):
        """Test main check command - CLI installed and logged in"""
        mock_check.return_value = True
        mock_logged_in.return_value = True
        mock_get_key.return_value = "test-key"

        main()

    @patch("tools.kimi_helper.sys.argv", ["kimi_helper.py", "--check"])
    @patch("tools.kimi_helper.check_kimi_cli")
    @patch("tools.kimi_helper.get_api_key")
    def test_main_check_not_installed(self, mock_get_key, mock_check):
        """Test main check command - CLI not installed"""
        mock_check.return_value = False
        mock_get_key.return_value = None

        main()

    @patch("tools.kimi_helper.sys.argv", ["kimi_helper.py", "--list"])
    def test_main_list(self):
        """Test main list command"""
        # Should print all personas without error
        main()

    @patch("tools.kimi_helper.sys.argv", ["kimi_helper.py", "--login"])
    @patch("tools.kimi_helper.check_kimi_cli")
    @patch("tools.kimi_helper.subprocess.run")
    def test_main_login(self, mock_run, mock_check):
        """Test main login command"""
        mock_check.return_value = True

        main()

        mock_run.assert_called_once_with(["kimi", "login"])

    @patch("tools.kimi_helper.sys.argv", ["kimi_helper.py", "--login"])
    @patch("tools.kimi_helper.check_kimi_cli")
    def test_main_login_not_installed(self, mock_check):
        """Test main login when CLI not installed"""
        mock_check.return_value = False

        main()

    @patch(
        "tools.kimi_helper.sys.argv",
        [
            "kimi_helper.py",
            "-p",
            "exploit",
            "create exploit",
            "-t",
            "0.5",
            "-m",
            "custom-model",
        ],
    )
    @patch("tools.kimi_helper.query_kimi_api")
    def test_main_with_options(self, mock_query):
        """Test main with temperature and model options"""
        mock_query.return_value = "Results"

        main()

        call_args = mock_query.call_args
        assert call_args[1]["temperature"] == 0.5
        assert call_args[1]["model"] == "custom-model"


# ============================================================================
# Test Error Handling
# ============================================================================


class TestErrorHandling:
    """Test error handling"""

    def test_keyboard_interrupt_main(self):
        """Test handling KeyboardInterrupt in main"""
        with patch(
            "tools.kimi_helper.sys.argv",
            ["kimi_helper.py", "-p", "recon", "test"],
        ):
            with patch(
                "tools.kimi_helper.query_kimi_api",
                side_effect=KeyboardInterrupt,
            ):
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
