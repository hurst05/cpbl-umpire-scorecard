# PowerShell Publish Script for CPBL Umpire Scorecard to GitHub Pages
param(
    [string]$RemoteUrlOverride = $null,
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
    Write-Host "`n>>> [Step] $desc..." -ForegroundColor Cyan
    & $action
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[Failed] $desc failed with exit code $LASTEXITCODE. Stopping publish."
        exit $LASTEXITCODE
    }
}

function Invoke-Git([string[]]$GitArgs) {
    & git @GitArgs
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "[Git Error] Git command failed with exit code $exitCode."
    }
}

# 1. Environment check
Assert-Command "git"
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

# 3. Test & Lint
Run-Step "Running Python lint" {
    pnpm run lint:py
}

Run-Step "Running backend tests" {
    pnpm run test:backend-core
}

Run-Step "Running frontend unit tests" {
    pnpm run test:frontend
}

Run-Step "Running frontend ESLint" {
    pnpm exec eslint .
}

# 4. Static build
Run-Step "Running Vite static production build" {
    pnpm run build:pages
}

# 5. Validate dist directory
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
$today = (Get-Date).ToString("yyyy-MM-dd")
$commitMsg = "Publish static scorecards: $totalGames games ($today)"

Write-Host "`n>>> All verification passed! Preparing to publish $totalGames games to gh-pages..." -ForegroundColor Green

# 6. Safe publish to gh-pages
$targetBranch = "gh-pages"
$remote = "origin"

$remoteUrl = if ($RemoteUrlOverride) { $RemoteUrlOverride } else { (git remote get-url $remote 2>$null) }
if ($LASTEXITCODE -ne 0 -or -not $remoteUrl) {
    Write-Error "[Error] Failed to get Git remote URL for '$remote'."
    exit 1
}
$remoteUrl = $remoteUrl.Trim()

Write-Host ">>> Target Remote URL: $remoteUrl" -ForegroundColor Yellow
Write-Host ">>> Target Branch: $targetBranch" -ForegroundColor Yellow

if ($DryRun) {
    Write-Host "`n[DryRun OK] Dry-run mode: all verifications and build passed. Skipping push." -ForegroundColor Green
    exit 0
}

# Check if branch exists on remote
$lsRemoteOutput = git ls-remote --heads $remoteUrl $targetBranch 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "[Git Remote Error] Failed to connect to remote: $lsRemoteOutput"
    exit $LASTEXITCODE
}
$branchExistsOnRemote = [bool]($lsRemoteOutput -match "refs/heads/$targetBranch")

$tempDeployDir = Join-Path $env:TEMP ("gh-pages-deploy-" + [System.Guid]::NewGuid().ToString())
try {
    if ($branchExistsOnRemote) {
        Write-Host ">>> Remote branch $targetBranch exists. Cloning branch..." -ForegroundColor Cyan
        git clone --branch $targetBranch --single-branch $remoteUrl $tempDeployDir
        if ($LASTEXITCODE -ne 0) {
            Write-Error "[Error] Failed to clone branch $targetBranch."
            exit $LASTEXITCODE
        }
        Push-Location $tempDeployDir
        # Clean existing files except .git
        Get-ChildItem -Path $tempDeployDir -Exclude ".git" | Remove-Item -Recurse -Force
    } else {
        Write-Host ">>> Remote branch $targetBranch does not exist. Initializing new orphan branch..." -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $tempDeployDir -Force | Out-Null
        Push-Location $tempDeployDir
        Invoke-Git @("init")
        Invoke-Git @("checkout", "--orphan", $targetBranch)
        Invoke-Git @("remote", "add", "origin", $remoteUrl)
    }

    # Copy dist contents to staging
    Copy-Item -Path "$distPath\*" -Destination $tempDeployDir -Recurse -Force

    Invoke-Git @("add", "-A")
    $changes = git status --porcelain
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[Git Error] Failed to check git status."
        exit $LASTEXITCODE
    }

    if ($changes) {
        Invoke-Git @("commit", "-m", $commitMsg)
        Write-Host ">>> Pushing update to $remoteUrl ($targetBranch)..." -ForegroundColor Cyan
        Invoke-Git @("push", "origin", $targetBranch)

        Write-Host "`n=======================================================" -ForegroundColor Green
        Write-Host "[Publish SUCCESS] Successfully published $totalGames games to gh-pages!" -ForegroundColor Green
        Write-Host "=======================================================" -ForegroundColor Green
    } else {
        Write-Host "`n[Publish OK] No changes detected. gh-pages is already up-to-date." -ForegroundColor Green
    }
} finally {
    Pop-Location
    if (Test-Path $tempDeployDir) {
        Remove-Item -Recurse -Force $tempDeployDir -ErrorAction SilentlyContinue
    }
}
