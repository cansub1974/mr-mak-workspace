@echo off
rem Installs Blender 5.2.4 LTS with the MCP for Blender add-on (no administrator rights, no internet).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Blender.ps1" %*
set "RC=%ERRORLEVEL%"
if "%~1"=="" pause
exit /b %RC%
