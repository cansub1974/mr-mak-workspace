@echo off
rem Installs the HAL3000 tools for this Windows user (no administrator rights, no internet).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Tools.ps1" %*
set "RC=%ERRORLEVEL%"
if "%~1"=="" pause
exit /b %RC%
