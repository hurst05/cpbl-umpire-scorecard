@echo off
setlocal

cd /d "%~dp0"

echo [CPBL Scorecard] GitHub Pages Publish Tool
echo ==========================================
echo.

REM 1. Check prerequisites
where git >nul 2>&1
if errorlevel 1 (
    echo [ERROR] git was not found. Please install Git first.
    goto :error
)

where pnpm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pnpm was not found. Please install pnpm first.
    goto :error
)

where uv >nul 2>&1
if errorlevel 1 (
    echo [ERROR] uv was not found. Please install uv first.
    goto :error
)

where powershell >nul 2>&1
if errorlevel 1 (
    echo [ERROR] powershell was not found.
    goto :error
)

REM 2. Step 1: Dry-run
echo [Step 1/2] Running publish dry-run [Export, Verify, Tests, Lint, Build]...
echo --------------------------------------------------------------------------
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\publish-pages.ps1 -DryRun
set "DRY_EXIT=%ERRORLEVEL%"
if not "%DRY_EXIT%"=="0" (
    echo.
    echo [ERROR] Dry-run failed with exit code %DRY_EXIT%. Please fix issues before publishing.
    goto :error
)

echo.
echo --------------------------------------------------------------------------
echo [SUCCESS] Dry-run checks and build passed!
echo --------------------------------------------------------------------------
echo.

REM Check for auto-confirm argument (-y or --yes)
if /i "%~1"=="-y" goto :publish
if /i "%~1"=="--yes" goto :publish

choice /C YN /M "Proceed with actual publish to GitHub Pages [gh-pages]?"
if errorlevel 2 (
    echo.
    echo [CANCELLED] Publish cancelled by user.
    goto :end
)

:publish
echo.
echo [Step 2/2] Publishing to GitHub Pages [gh-pages]...
echo --------------------------------------------------------------------------
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\publish-pages.ps1
set "PUB_EXIT=%ERRORLEVEL%"
if not "%PUB_EXIT%"=="0" (
    echo.
    echo [ERROR] Publish failed with exit code %PUB_EXIT%.
    goto :error
)

echo.
echo ==========================================================================
echo [SUCCESS] Scorecard successfully published to GitHub Pages!
echo ==========================================================================
goto :end

:error
echo.
echo [ABORTED] Publish process terminated with errors.
if not defined CPBL_SKIP_PAUSE pause
exit /b 1

:end
echo.
if not defined CPBL_SKIP_PAUSE pause
exit /b 0
