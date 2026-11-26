@echo off
rem Installs FreeCAD 1.1.4 and the FreeCAD MCP add-on for this Windows user (no administrator rights, no internet).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-FreeCAD.ps1" %*
set "RC=%ERRORLEVEL%"
if "%~1"=="" pause
exit /b %RC%
