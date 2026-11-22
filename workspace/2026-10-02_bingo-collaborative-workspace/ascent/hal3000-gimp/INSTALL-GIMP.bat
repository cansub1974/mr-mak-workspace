@echo off
rem Installs GIMP 3.2.8 for this Windows user (no administrator rights, no internet).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-GIMP.ps1" %*
set "RC=%ERRORLEVEL%"
if "%~1"=="" pause
exit /b %RC%
