@echo off
cd /d "%~dp0"
setlocal

echo =====================================================
echo Over-Ordering Sentinel - Online Admin
echo =====================================================
echo.
echo Opening local admin console...
echo Admin page: http://127.0.0.1:8502
echo Public users will access the normal app UI through a Cloudflare link.
echo.
echo Keep this CMD window open.
echo Closing this CMD window stops admin/backend/tunnel processes.
echo.

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python scripts\launcher_online.py
    if %ERRORLEVEL% EQU 0 exit /b 0
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        py scripts\launcher_online.py
        if %ERRORLEVEL% EQU 0 exit /b 0
    ) else (
        echo [ERROR] Python was not found.
        echo Please install Python 3.10+ and tick "Add Python to PATH".
    )
)

echo.
pause
