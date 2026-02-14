@echo off
REM Kimi CLI mit Personas (Windows Batch Wrapper)
REM Usage: ask-kimi.bat [persona] [prompt...]

setlocal enabledelayedexpansion

if "%KIMI_PERSONA_DIR%"=="" (
    set "PERSONA_DIR=%USERPROFILE%\.config\kimi\personas"
) else (
    set "PERSONA_DIR=%KIMI_PERSONA_DIR%"
)

if "%~1"=="" (
    set "MODE=recon"
) else (
    set "MODE=%~1"
    shift
)

set "PERSONA_FILE=%PERSONA_DIR%\%MODE%.md"

if exist "%PERSONA_FILE%" (
    echo [Mode: %MODE% aktiviert]
    for /f "delims=" %%i in (%PERSONA_FILE%) do set "SYSTEM_PROMPT=!SYSTEM_PROMPT!%%i"
) else (
    echo [Warnung: Persona %MODE% nicht gefunden, nutze Standard]
    set "SYSTEM_PROMPT=Du bist ein hilfreicher Assistent."
)

REM Sammle restliche Argumente
set "USER_PROMPT="
:loop
if "%~1"=="" goto done
set "USER_PROMPT=%USER_PROMPT% %1"
shift
goto loop
:done

echo %SYSTEM_PROMPT%
echo.
echo ---
echo User Anfrage:
echo %USER_PROMPT%

where kimi >nul 2>nul
if %errorlevel% neq 0 (
    echo Fehler: kimi-cli nicht gefunden. Bitte installieren: pip install kimi-cli
    exit /b 1
)

echo %SYSTEM_PROMPT%^\n\n---^\nUser Anfrage:^\n%USER_PROMPT% | kimi ask -
