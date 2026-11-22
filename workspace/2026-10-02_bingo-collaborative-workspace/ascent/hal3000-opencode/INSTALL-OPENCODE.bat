@echo off
rem Installs OpenCode for the Ascent on this PC (no administrator rights, no internet).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-OpenCode.ps1" %*
set "RC=%ERRORLEVEL%"
if "%~1"=="" pause
exit /b %RC%
