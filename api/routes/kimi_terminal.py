"""
🤖 Kimi CLI Terminal Integration (PROTECTED)
Ermöglicht echte Kimi CLI Befehle über das Web-Interface
🔒 AUTH REQUIRED - Nur für autorisierte Benutzer
"""

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from api.auth_simple import verify_token

# Security
security = HTTPBearer(auto_error=False)

router = APIRouter(prefix="/kimi", tags=["Kimi Terminal"])


class KimiCommand(BaseModel):
    """Kimi CLI Command"""

    command: str
    args: list = []
    cwd: Optional[str] = None
    timeout: int = 60


class KimiCommandResponse(BaseModel):
    """Response from Kimi CLI"""

    success: bool
    stdout: str
    stderr: str
    returncode: int
    execution_time: float
    timestamp: str


# Verfügbare Kimi CLI Befehle (Whitelist für Sicherheit)
# Hinweis: kimi 1.17.0 hat andere Befehle als ältere Versionen
# Die 'ask', 'code', etc. Befehle existieren nicht mehr - nutze stattdessen 'kimi chat'
ALLOWED_COMMANDS = {
    "login": "Login zu Kimi",
    "logout": "Logout von Kimi",
    "info": "Zeige Version und Info",
    "mcp": "MCP Server verwalten",
    "help": "Zeige Hilfe",
}


def check_kimi_installed() -> bool:
    """Prüfe ob Kimi CLI installiert ist"""
    import shutil

    return shutil.which("kimi") is not None


def execute_kimi_command(cmd: str, args: list = None, cwd: str = None, timeout: int = 60) -> KimiCommandResponse:
    """Führe Kimi CLI Befehl aus"""
    start_time = datetime.now(timezone.utc)

    if not check_kimi_installed():
        return KimiCommandResponse(
            success=False,
            stdout="",
            stderr="Kimi CLI nicht installiert. Installiere mit: curl -sSL https://cli.getkimi.com/install.sh | bash",
            returncode=-1,
            execution_time=0,
            timestamp=start_time.isoformat(),
        )

    # Baue Befehl
    command_parts = ["kimi", cmd]
    if args:
        command_parts.extend(args)

    try:
        result = subprocess.run(
            command_parts,
            capture_output=True,
            text=True,
            cwd=cwd or os.getcwd(),
            timeout=timeout,
        )

        end_time = datetime.now(timezone.utc)
        execution_time = (end_time - start_time).total_seconds()

        return KimiCommandResponse(
            success=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
            execution_time=execution_time,
            timestamp=end_time.isoformat(),
        )

    except subprocess.TimeoutExpired:
        return KimiCommandResponse(
            success=False,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            returncode=-1,
            execution_time=timeout,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        import logging

        logging.getLogger(__name__).error(f"Kimi command execution failed: {e}")
        return KimiCommandResponse(
            success=False,
            stdout="",
            stderr="Command execution failed",
            returncode=-1,
            execution_time=0,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


def get_local_kimi_token() -> str:
    """Lese lokalen Kimi Token"""
    try:
        home = Path.home()
        credential_paths = [
            home / ".kimi" / "credentials" / "kimi-code.json",
            home / ".config/kimi/credentials.json",
        ]

        for cred_path in credential_paths:
            if cred_path.exists():
                with open(cred_path, "r") as f:
                    data = json.load(f)
                    token = data.get("access_token") or data.get("token")
                    if token:
                        return token

        return os.getenv("KIMI_ACCESS_TOKEN")
    except Exception:
        return None


@router.get("/status")
async def kimi_status(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    # 🔒 AUTH REQUIRED
    # SECURITY: Verify valid JWT token (not just presence)
    verify_token(credentials)
    """Prüfe Kimi CLI Status"""
    installed = check_kimi_installed()

    if not installed:
        return {
            "installed": False,
            "message": "Kimi CLI nicht installiert",
            "install_command": "curl -sSL https://cli.getkimi.com/install.sh | bash",
        }

    # Get version
    version_result = execute_kimi_command("--version", timeout=5)

    # Check if authenticated (prüfe ob kimicli verfügbar ist)
    # Da 'status' Befehl nicht existiert, nutzen wir --version als Proxy
    # Echte Authentifizierung prüfen - Token vorhanden?
    token = get_local_kimi_token()
    is_logged_in = token is not None

    return {
        "installed": True,
        "version": (version_result.stdout.strip() if version_result.success else "unknown"),
        "authenticated": is_logged_in,
        "available_commands": list(ALLOWED_COMMANDS.keys()),
        "message": ("Kimi CLI ready" if is_logged_in else "Bitte zuerst einloggen: kimi login"),
    }


@router.post("/execute", response_model=KimiCommandResponse)
async def execute_command(
    request: KimiCommand,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    # 🔒 AUTH REQUIRED - Protect command execution
    # SECURITY: Verify valid JWT token (not just presence)
    verify_token(credentials)
    """Führe Kimi CLI Befehl aus"""
    # Validierung
    if request.command not in ALLOWED_COMMANDS:
        raise HTTPException(
            status_code=400,
            detail=f"Command '{request.command}' nicht erlaubt. Erlaubte Befehle: {', '.join(ALLOWED_COMMANDS.keys())}",
        )

    # Sicherheit: Blockiere gefährliche Argumente
    blocked_patterns = [";", "&&", "||", "|", ">", "<", "$", "`", "$(", "${"]
    for arg in request.args:
        for pattern in blocked_patterns:
            if pattern in arg:
                raise HTTPException(
                    status_code=400,
                    detail=f"Potenziell gefährliches Zeichen in Argumenten gefunden: {pattern}",
                )

    result = execute_kimi_command(request.command, request.args, request.cwd, request.timeout)

    return result


@router.websocket("/terminal")
async def kimi_terminal_websocket(websocket: WebSocket, token: str = None):
    # Auth check for WebSocket
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return
    """WebSocket für interaktives Kimi Terminal"""
    await websocket.accept()

    # Sende Willkommensnachricht
    await websocket.send_json(
        {
            "type": "system",
            "message": "🤖 Kimi Terminal verbunden",
            "installed": check_kimi_installed(),
        }
    )

    try:
        while True:
            # Warte auf Befehl vom Client
            data = await websocket.receive_json()
            command = data.get("command", "").strip()

            if not command:
                continue

            # Parse Befehl
            parts = command.split()
            cmd = parts[0] if parts else ""
            args = parts[1:] if len(parts) > 1 else []

            # Überprüfe ob Befehl erlaubt ist
            if cmd not in ALLOWED_COMMANDS and cmd != "clear":
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": f"❌ Befehl '{cmd}' nicht erlaubt. Verwende: {', '.join(ALLOWED_COMMANDS.keys())}",
                        "prompt": "kimi> ",
                    }
                )
                continue

            # Spezialbefehl: clear
            if cmd == "clear":
                await websocket.send_json({"type": "clear"})
                continue

            # Führe Befehl aus
            await websocket.send_json({"type": "status", "message": f"⏳ Führe aus: kimi {cmd}..."})

            result = execute_kimi_command(cmd, args)

            # Sende Ergebnis
            if result.success:
                await websocket.send_json(
                    {
                        "type": "output",
                        "stdout": result.stdout,
                        "stderr": result.stderr if result.stderr else None,
                        "execution_time": result.execution_time,
                        "prompt": "kimi> ",
                    }
                )
            else:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": result.stderr or "Unbekannter Fehler",
                        "stdout": result.stdout if result.stdout else None,
                        "prompt": "kimi> ",
                    }
                )

    except WebSocketDisconnect:
        logger = logging.getLogger(__name__)
        logger.info("Kimi Terminal WebSocket disconnected")
    except Exception as e:
        logger.exception(f"Kimi Terminal Error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": f"Server Error: {str(e)}"})
        except Exception:
            pass


@router.get("/commands")
async def list_commands(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    # 🔒 AUTH REQUIRED
    # SECURITY: Verify valid JWT token (not just presence)
    verify_token(credentials)
    """Liste alle verfügbaren Kimi Befehle"""
    return {"commands": ALLOWED_COMMANDS, "installed": check_kimi_installed()}


@router.post("/ask")
async def kimi_ask(
    question: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    # 🔒 AUTH REQUIRED
    # SECURITY: Verify valid JWT token (not just presence)
    verify_token(credentials)
    """Schnelle Frage an Kimi (kein Chat-Context)"""
    result = execute_kimi_command("ask", [question], timeout=120)

    if result.success:
        return {
            "success": True,
            "answer": result.stdout,
            "timestamp": result.timestamp,
        }
    else:
        raise HTTPException(status_code=500, detail=result.stderr)


@router.post("/code")
async def kimi_code(
    description: str,
    language: str = "python",
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    # 🔒 AUTH REQUIRED
    # SECURITY: Verify valid JWT token (not just presence)
    verify_token(credentials)
    """Generiere Code mit Kimi"""
    prompt = f"Generate {language} code: {description}"
    result = execute_kimi_command("code", [prompt], timeout=120)

    if result.success:
        return {
            "success": True,
            "code": result.stdout,
            "language": language,
            "timestamp": result.timestamp,
        }
    else:
        raise HTTPException(status_code=500, detail=result.stderr)
