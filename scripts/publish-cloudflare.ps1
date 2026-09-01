# PowerShell Publish Script for CPBL Umpire Scorecard to Cloudflare Pages
param(
    [string]$ProjectName = "cpbl-umpire-scorecard",
    [string]$Branch = "main",
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

function Assert-Command($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Error "[Error] Command not found: $name"
        exit 1
    }
}

function Run-Step($desc, [scriptblock]$action) {
    Write-Host "
>>> [Step] $desc..." -ForegroundColor Cyan
    & $action
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[Failed] $desc failed with exit code $LASTEXITCODE. Stopping publish."
        exit $LASTEXITCODE
    }
}

# 1. Environment check
Assert-Command "pnpm"
Assert-Command "uv"

$repoRoot = (git rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0 -or -not $repoRoot) {
    Write-Error "[Error] Current directory is not a Git repository."
    exit 1
}
$repoRoot = $repoRoot.Trim()
Set-Location $repoRoot

# 2. Export & strict verify
Run-Step "Exporting static JSON from SQLite" {
    pnpm run export:static
}

Run-Step "Verifying static snapshot contract" {
    uv run python -m server.verify_static --input .static-export/data
}

# 3. Static build with root base path
Run-Step "Running Vite static production build (base path: /)" {
    $env:VITE_BASE_PATH = "/"
    pnpm run build:pages
}

# 4. Validate dist directory
$distPath = Join-Path $repoRoot "dist"
$manifestPath = Join-Path $distPath "data\manifest.json"

if (-not (Test-Path $manifestPath)) {
    Write-Error "[Error] manifest.json was not found in dist/data!"
    exit 1
}

Run-Step "Verifying dist/data final snapshot contract" {
    uv run python -m server.verify_static --input (Join-Path $distPath "data")
}

# Read manifest games count
$manifestContent = [System.IO.File]::ReadAllText($manifestPath, [System.Text.Encoding]::UTF8)
$manifestJson = $manifestContent | ConvertFrom-Json
$totalGames = if ($manifestJson.games) { $manifestJson.games.Length } else { 0 }

Write-Host "
>>> All verification passed! Preparing to publish $totalGames games to Cloudflare Pages ($ProjectName)..." -ForegroundColor Green

if ($DryRun) {
    Write-Host "
[DryRun OK] Dry-run mode: build and verification succeeded. Skipping deployment." -ForegroundColor Green
    exit 0
}

# 5. Deploy to Cloudflare Pages via Wrangler
Run-Step "Deploying to Cloudflare Pages via Wrangler" {
    npx --yes wrangler pages deploy dist --project-name $ProjectName --branch $Branch
}

Write-Host "
=======================================================" -ForegroundColor Green
Write-Host "[Publish SUCCESS] Successfully published $totalGames games to Cloudflare Pages!" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Green
