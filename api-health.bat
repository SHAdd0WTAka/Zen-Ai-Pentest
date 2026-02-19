@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0zen-api.ps1" -Endpoint health
pause
