@echo off
chcp 65001 >nul
echo ==========================================
echo   Zen-AI-Pentest API - Schnellzugriff
echo ==========================================
echo.

if "%~1"=="" goto :MENU
if /I "%~1"=="status" goto :STATUS
if /I "%~1"=="health" goto :HEALTH
if /I "%~1"=="docs" goto :DOCS
if /I "%~1"=="logs" goto :LOGS
if /I "%~1"=="help" goto :HELP

echo Unbekannter Befehl: %~1
goto :HELP

:MENU
echo Verfügbare Befehle:
echo   1. status  - Container-Status anzeigen
echo   2. health  - API Health Check
echo   3. docs    - API Dokumentation öffnen
echo   4. logs    - Logs anzeigen
echo   5. help    - Hilfe anzeigen
echo.
echo Beispiel: start-api.bat health
echo.
choice /C 12345 /N /M "Wähle eine Option (1-5): "
if errorlevel 5 goto :HELP
if errorlevel 4 goto :LOGS
if errorlevel 3 goto :DOCS
if errorlevel 2 goto :HEALTH
if errorlevel 1 goto :STATUS
goto :EOF

:STATUS
echo.
echo Container Status wird abgerufen...
powershell -ExecutionPolicy Bypass -File "%~dp0zen-api.ps1" -Status
pause
goto :EOF

:HEALTH
echo.
echo API Health Check wird durchgeführt...
powershell -ExecutionPolicy Bypass -File "%~dp0zen-api.ps1"
pause
goto :EOF

:DOCS
echo.
echo Öffne Zen-AI-Pentest Frontend im Browser...
echo   Frontend: http://localhost:8080/
echo   API Docs:  http://localhost:8080/docs
start http://localhost:8080/
goto :EOF

:LOGS
echo.
echo Verfügbare Services: api, nginx, db, redis, agent
set /p service="Service eingeben (default: api): "
if "%service%"=="" set service=api
powershell -ExecutionPolicy Bypass -File "%~dp0zen-api.ps1" -Logs -Service %service%
pause
goto :EOF

:HELP
echo.
echo Verwendung: start-api.bat [Befehl]
echo.
echo Befehle:
echo   status  - Zeigt den Status aller Container an
echo   health  - Führt einen Health Check der API durch
echo   docs    - Öffnet die API Dokumentation im Browser
echo   logs    - Zeigt Logs eines Services an
echo   help    - Zeigt diese Hilfe an
echo.
echo Beispiele:
echo   start-api.bat status
echo   start-api.bat health
echo   start-api.bat docs
echo   start-api.bat logs
echo.
pause
goto :EOF
