@echo off
REM Zen-AI Pentest Aliase fuer CMD
REM Verwendung: zen-alias.bat [command] [args]

set "ZEN_HOME=%USERPROFILE%\zen-ai-pentest"

if /i "%1"=="zki" goto :kimi
if /i "%1"=="zrecon" goto :recon
if /i "%1"=="zexploit" goto :exploit
if /i "%1"=="zreport" goto :report
if /i "%1"=="zaudit" goto :audit
if /i "%1"=="zsetup" goto :setup
if /i "%1"=="zcheck" goto :check
if /i "%1"=="zswitch" goto :switch
if /i "%1"=="help" goto :help
if /i "%1"=="" goto :help

echo Unbekannter Befehl: %1
goto :help

:kimi
python "%ZEN_HOME%\tools\kimi_helper.py" %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:recon
python "%ZEN_HOME%\tools\kimi_helper.py" -p recon %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:exploit
python "%ZEN_HOME%\tools\kimi_helper.py" -p exploit %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:report
python "%ZEN_HOME%\tools\kimi_helper.py" -p report %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:audit
python "%ZEN_HOME%\tools\kimi_helper.py" -p audit %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:setup
python "%ZEN_HOME%\scripts\setup_wizard.py" %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:check
python "%ZEN_HOME%\scripts\check_config.py"
goto :eof

:switch
python "%ZEN_HOME%\scripts\switch_model.py" %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:help
echo.
echo Zen-AI Pentest Aliase
echo =====================
echo.
echo Verwendung: zen-alias.bat [Befehl] [Argumente]
echo.
echo Befehle:
echo   zki      [args]  - Kimi Helper (allgemein)
echo   zrecon   [args]  - Recon Persona
echo   zexploit [args]  - Exploit Persona
echo   zreport  [args]  - Report Persona
echo   zaudit   [args]  - Audit Persona
echo   zsetup   [args]  - Setup Wizard
echo   zcheck           - Config Check
echo   zswitch  [args]  - Model Switcher
echo   help             - Diese Hilfe
echo.
echo Beispiele:
echo   zen-alias.bat zki -p recon "Scan target.com"
echo   zen-alias.bat zexploit "SQLi scanner"
echo   zen-alias.bat zcheck
echo.
goto :eof
