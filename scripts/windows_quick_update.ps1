param(
    [string]$RepoDir = "",
    [string]$Branch = "main",
    [string]$TaskName = "TelethonFancifier",
    [switch]$ForceUpdate,
    [switch]$RestartStartupTask,
    [switch]$SkipSmokeTest
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

function Step([string]$Message) {
    Write-Host "STEP: $Message" -ForegroundColor Cyan
}

if (-not $RepoDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepoDir = Resolve-Path (Join-Path $scriptDir "..")
}

if (-not (Test-Path $RepoDir)) {
    Fail "Repository directory not found: $RepoDir"
}

Step "Switching to repository directory"
Set-Location $RepoDir

if (-not (Test-Path ".git")) {
    Fail "Git repository not found in: $RepoDir"
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Fail "git command not found in PATH"
}

Step "Updating code from GitHub (origin/$Branch)"
git fetch origin
if ($LASTEXITCODE -ne 0) { Fail "git fetch failed" }

if ($ForceUpdate) {
    Step "Force update enabled: discarding local changes and syncing to origin/$Branch"
    git checkout -f $Branch
    if ($LASTEXITCODE -ne 0) { Fail "git checkout -f failed for branch: $Branch" }

    git reset --hard "origin/$Branch"
    if ($LASTEXITCODE -ne 0) { Fail "git reset --hard failed for origin/$Branch" }

    git clean -fd
    if ($LASTEXITCODE -ne 0) { Fail "git clean -fd failed" }
}
else {
    git checkout $Branch
    if ($LASTEXITCODE -ne 0) { Fail "git checkout failed for branch: $Branch" }

    git pull --ff-only origin $Branch
    if ($LASTEXITCODE -ne 0) { Fail "git pull failed for branch: $Branch" }
}

$venvPython = Join-Path $RepoDir ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Step "Creating virtual environment .venv"
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3 -m venv .venv
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        python -m venv .venv
    }
    else {
        Fail "Python is not available (neither py nor python)."
    }
}

if (-not (Test-Path $venvPython)) {
    Fail "python.exe not found in .venv after environment creation"
}

Step "Upgrading pip and project dependencies"
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { Fail "pip upgrade failed" }

& $venvPython -m pip install -e .
if ($LASTEXITCODE -ne 0) { Fail "project install failed" }

if (-not $SkipSmokeTest) {
    Step "Running smoke-check (show-config)"
    & $venvPython -m telethon_fancifier.cli show-config
    if ($LASTEXITCODE -ne 0) { Fail "smoke-check failed" }
}

if ($RestartStartupTask) {
    Step "Checking startup task '$TaskName'"
    schtasks /Query /TN $TaskName > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        Step "Restarting startup task '$TaskName'"
        schtasks /End /TN $TaskName > $null 2>&1
        schtasks /Run /TN $TaskName
        if ($LASTEXITCODE -ne 0) { Fail "failed to run startup task: $TaskName" }
    }
    else {
        Write-Host "WARN: startup task '$TaskName' was not found, skip restart" -ForegroundColor Yellow
    }
}

Write-Host "Done: quick update/deploy finished successfully." -ForegroundColor Green
