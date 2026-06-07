"""Unit tests for zen_cli.py with mocked dependencies."""

import sys
import types
from unittest.mock import AsyncMock, MagicMock

import pytest


def _inject_cli_mocks():
    """Pre-populate sys.modules with lightweight mocks for CLI dependencies."""
    packages = ["core", "core.auth", "agents"]
    for pkg in packages:
        if pkg not in sys.modules:
            mod = types.ModuleType(pkg)
            mod.__path__ = []
            sys.modules[pkg] = mod

    modules = {
        "core.auth.cli": {
            "AuthCLI": MagicMock(name="AuthCLI"),
        },
        "core.auth.token_store": {
            "is_logged_in": MagicMock(name="is_logged_in", return_value=False),
            "get_stored_token": MagicMock(name="get_stored_token", return_value=None),
        },
        "agents.cli": {
            "AgentCLI": MagicMock(name="AgentCLI"),
        },
    }
    for mod_name, attrs in modules.items():
        if mod_name not in sys.modules:
            mod = types.ModuleType(mod_name)
            for key, val in attrs.items():
                setattr(mod, key, val)
            sys.modules[mod_name] = mod


_inject_cli_mocks()

import zen_cli


@pytest.fixture
def cli_deps(monkeypatch):
    """Provide a ZenCLI module namespace with fully mocked dependencies."""
    # AuthCLI mock
    auth_instance = MagicMock()
    auth_instance.login = MagicMock(return_value=0)
    auth_instance.logout = MagicMock(return_value=0)
    auth_instance.status = MagicMock(return_value=0)
    auth_instance.print_help = MagicMock(return_value=None)
    auth_cls = MagicMock(return_value=auth_instance)
    zen_cli.AuthCLI = auth_cls

    # Token store mocks
    zen_cli.is_logged_in = MagicMock(return_value=False)
    zen_cli.get_stored_token = MagicMock(return_value=None)

    # asyncio mock (asyncio is imported late in zen_cli.py)
    mock_asyncio = MagicMock()
    mock_asyncio.run = MagicMock(return_value=0)
    monkeypatch.setattr(zen_cli, "asyncio", mock_asyncio, raising=False)

    # AgentCLI mock lives in agents.cli because zen_cli imports it locally
    agent_instance = MagicMock()
    agent_instance.run = MagicMock(return_value=MagicMock(name="coro"))
    agent_cls = MagicMock(return_value=agent_instance)
    sys.modules["agents.cli"].AgentCLI = agent_cls
    zen_cli.AgentCLI = agent_cls  # expose for assertions

    return zen_cli


class TestZenCLIInit:
    def test_initialization(self, cli_deps):
        instance = zen_cli.ZenCLI()
        assert instance.auth_cli is zen_cli.AuthCLI.return_value
        zen_cli.AuthCLI.assert_called_once()


class TestZenCLIPrint:
    def test_print_banner(self, cli_deps, capsys):
        instance = zen_cli.ZenCLI()
        instance.print_banner()
        out = capsys.readouterr().out
        assert "Zen AI Pentest" in out
        assert "3.0.0" in out

    def test_print_main_help_not_logged_in(self, cli_deps, capsys):
        zen_cli.is_logged_in.return_value = False
        instance = zen_cli.ZenCLI()
        instance.print_main_help()
        out = capsys.readouterr().out
        assert "not logged in" in out
        assert "auth login" in out

    def test_print_main_help_logged_in(self, cli_deps, capsys):
        zen_cli.is_logged_in.return_value = True
        instance = zen_cli.ZenCLI()
        instance.print_main_help()
        out = capsys.readouterr().out
        assert "logged in" in out


class TestZenCLIRun:
    def test_run_no_args(self, cli_deps, capsys):
        instance = zen_cli.ZenCLI()
        assert instance.run([]) == 0
        out = capsys.readouterr().out
        assert "Zen AI Pentest" in out

    def test_run_help(self, cli_deps, capsys):
        instance = zen_cli.ZenCLI()
        assert instance.run(["--help"]) == 0
        out = capsys.readouterr().out
        assert "Usage:" in out

    def test_run_version(self, cli_deps, capsys):
        instance = zen_cli.ZenCLI()
        assert instance.run(["--version"]) == 0
        out = capsys.readouterr().out
        assert "3.0.0" in out

    def test_run_unknown_command(self, cli_deps, capsys):
        instance = zen_cli.ZenCLI()
        assert instance.run(["foobar"]) == 1
        out = capsys.readouterr().out
        assert "Unknown command: foobar" in out


class TestZenCLIAuth:
    def test_handle_auth_help(self, cli_deps):
        instance = zen_cli.ZenCLI()
        assert instance._handle_auth([]) == 0
        instance.auth_cli.print_help.assert_called_once()

    def test_handle_auth_login(self, cli_deps):
        instance = zen_cli.ZenCLI()
        assert instance._handle_auth(["login"]) == 0
        instance.auth_cli.login.assert_called_once()

    def test_handle_auth_logout(self, cli_deps):
        instance = zen_cli.ZenCLI()
        assert instance._handle_auth(["logout"]) == 0
        instance.auth_cli.logout.assert_called_once()

    def test_handle_auth_status(self, cli_deps):
        instance = zen_cli.ZenCLI()
        assert instance._handle_auth(["status"]) == 0
        instance.auth_cli.status.assert_called_once()

    def test_handle_auth_unknown(self, cli_deps, capsys):
        instance = zen_cli.ZenCLI()
        assert instance._handle_auth(["foo"]) == 1
        out = capsys.readouterr().out
        assert "Unknown auth command: foo" in out
        instance.auth_cli.print_help.assert_called_once()


class TestZenCLIAgent:
    def test_handle_agent_not_logged_in(self, cli_deps, capsys):
        zen_cli.is_logged_in.return_value = False
        instance = zen_cli.ZenCLI()
        assert instance._handle_agent(["start"]) == 1
        out = capsys.readouterr().out
        assert "Not authenticated" in out

    def test_handle_agent_help(self, cli_deps, capsys):
        zen_cli.is_logged_in.return_value = True
        instance = zen_cli.ZenCLI()
        assert instance._handle_agent([]) == 0
        out = capsys.readouterr().out
        assert "agent start" in out

    def test_handle_agent_start(self, cli_deps):
        zen_cli.is_logged_in.return_value = True
        instance = zen_cli.ZenCLI()
        assert instance._handle_agent(["start"]) == 0
        zen_cli.AgentCLI.assert_called_once()
        agent_inst = zen_cli.AgentCLI.return_value
        zen_cli.asyncio.run.assert_called_once()
        agent_inst.run.assert_called_once()

    def test_handle_agent_status_with_token(self, cli_deps, capsys):
        zen_cli.is_logged_in.return_value = True
        zen_cli.get_stored_token.return_value = "tok"
        instance = zen_cli.ZenCLI()
        assert instance._handle_agent(["status"]) == 0
        out = capsys.readouterr().out
        assert "Agent status: Ready" in out
        assert "Yes" in out

    def test_handle_agent_status_no_token(self, cli_deps, capsys):
        zen_cli.is_logged_in.return_value = True
        zen_cli.get_stored_token.return_value = None
        instance = zen_cli.ZenCLI()
        assert instance._handle_agent(["status"]) == 0
        out = capsys.readouterr().out
        assert "Agent status: Ready" in out
        assert "No" in out

    def test_handle_agent_unknown(self, cli_deps, capsys):
        zen_cli.is_logged_in.return_value = True
        instance = zen_cli.ZenCLI()
        assert instance._handle_agent(["foo"]) == 1
        out = capsys.readouterr().out
        assert "Unknown agent command: foo" in out


class TestZenCLIScan:
    def test_handle_scan_not_logged_in(self, cli_deps, capsys):
        zen_cli.is_logged_in.return_value = False
        instance = zen_cli.ZenCLI()
        assert instance._handle_scan(["start"]) == 1
        out = capsys.readouterr().out
        assert "Not authenticated" in out

    def test_handle_scan_logged_in(self, cli_deps, capsys):
        zen_cli.is_logged_in.return_value = True
        instance = zen_cli.ZenCLI()
        assert instance._handle_scan(["start"]) == 0
        out = capsys.readouterr().out
        assert "coming soon" in out


class TestZenCLIConfig:
    def test_handle_config(self, cli_deps, capsys):
        instance = zen_cli.ZenCLI()
        assert instance._handle_config(["get"]) == 0
        out = capsys.readouterr().out
        assert "coming soon" in out


class TestZenCLIMain:
    def test_main_success(self, monkeypatch, cli_deps):
        monkeypatch.setattr(zen_cli.ZenCLI, "run", lambda self: 42)
        assert zen_cli.main() == 42

    def test_main_keyboard_interrupt(self, monkeypatch, cli_deps, capsys):
        def _raise(_):
            raise KeyboardInterrupt

        monkeypatch.setattr(zen_cli.ZenCLI, "run", _raise)
        assert zen_cli.main() == 130
        out = capsys.readouterr().out
        assert "Interrupted." in out
