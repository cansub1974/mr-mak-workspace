@echo off
title BCW - give BMT01 the ICPM role again
setlocal
set "PY=%~d0\BCW-V0.16\BCW-release\windows\python\python.exe"
if not exist "%PY%" for /d %%R in (C:\BCW\releases\*) do if exist "%%R\windows\python\python.exe" set "PY=%%R\windows\python\python.exe"
if not exist "%PY%" (echo Could not find BCWs Python on this USB or in C:\BCW\releases. & pause & exit /b 2)
echo BCW ICPM REPAIR - this window first shows what it would change. Nothing changes until you answer Y.
echo.
"%PY%" -I -B "%~dp0repair_icpm.py" --account bmt01
if errorlevel 1 (echo. & pause & exit /b 1)
echo.
choice /c YN /m "Give BMT01 the ICPM role now (a backup is taken first)"
if errorlevel 2 (echo Cancelled. Nothing changed. & pause & exit /b 0)
echo.
"%PY%" -I -B "%~dp0repair_icpm.py" --account bmt01 --execute
echo.
pause
