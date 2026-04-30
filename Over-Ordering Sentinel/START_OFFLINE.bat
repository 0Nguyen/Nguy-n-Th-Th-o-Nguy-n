@echo off
cd /d "%~dp0"
setlocal
title Over-Ordering Sentinel - Offline
set "ROOT=%~dp0"
set "LAUNCHER=%ROOT%scripts\launcher_offline.py"
set "LOGFILE=%ROOT%launcher_offline_error.log"
set PYTHONUTF8=1

if not exist "%LAUNCHER%" (
    echo Missing scripts\launcher_offline.py in project folder.
    pause
    exit /b 1
)

where wscript.exe >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    wscript.exe "%ROOT%START_OFFLINE_HIDDEN.vbs"
    exit /b 0
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python "%LAUNCHER%" > "%LOGFILE%" 2>&1
    if %ERRORLEVEL% EQU 0 exit /b 0
    goto launcher_failed
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py "%LAUNCHER%" > "%LOGFILE%" 2>&1
    if %ERRORLEVEL% EQU 0 exit /b 0
    goto launcher_failed
)

echo Python is required. Please install Python 3.10+ and add it to PATH.
pause
exit /b 1

:launcher_failed
echo [ERROR] Launcher failed. See "%LOGFILE%" for details.
pause
exit /b 1
