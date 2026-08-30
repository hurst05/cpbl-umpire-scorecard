@echo off
setlocal

cd /d "%~dp0"
set "APP_URL=http://127.0.0.1:5173/"

where pnpm >nul 2>&1
if errorlevel 1 (
    echo [CPBL Scorecard] pnpm was not found. Install pnpm first.
    pause
    exit /b 1
)

where uv >nul 2>&1
if errorlevel 1 (
    echo [CPBL Scorecard] uv was not found. Install uv first.
    pause
    exit /b 1
)

if not defined CPBL_SKIP_BROWSER (
    start "" powershell.exe -NoProfile -WindowStyle Hidden -Command ^
        "Start-Sleep -Milliseconds 2000; Start-Process '%APP_URL%'"
)

echo [CPBL Scorecard] Starting Backend (8000) and Frontend (5173)...
echo URL: %APP_URL%
echo Close this window to stop the service.
echo.
call pnpm dev
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo [CPBL Scorecard] Service stopped.
if not defined CPBL_SKIP_PAUSE pause
exit /b %EXIT_CODE%
