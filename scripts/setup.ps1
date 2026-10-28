#requires -Version 5.1
<#
.SYNOPSIS
    One-time setup for SentinelOps AI on Windows 11.
.DESCRIPTION
    Installs/verifies prerequisites, provisions the Python backend virtual
    environment, applies database migrations, and seeds the dev database.
    Ollama must be installed separately (Ollama for Windows) and a coding
    model pulled manually, e.g. `ollama pull codellama:7b-instruct`.
    No secrets are written to disk: secrets live in backend/.env (from
    .env.example placeholders) and must be edited before production use.
.NOTES
    Target OS: Windows 11. PowerShell 5.1+ (or PowerShell 7).
    Run from an elevated prompt only if winget/choco installs are needed.
#>
[CmdletBinding()]
param(
    [switch]$SkipPrereq,
    [switch]$SkipOllamaCheck,
    [string]$PythonVersion = "3.11.*"
)

$ErrorActionPreference = "Continue"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRoot   = Resolve-Path (Join-Path $scriptRoot "..")
$backendDir = Join-Path $repoRoot "backend"
$webDir     = Join-Path $repoRoot "apps/web"

Write-Host "=== SentinelOps AI Windows setup ===" -ForegroundColor Cyan
Write-Host "Repo root: $repoRoot" -ForegroundColor Gray

# --------------------------------------------------------------------------- helpers
function Test-Command($name) {
    return (Get-Command $name -ErrorAction SilentlyContinue) -ne $null
}

function Ensure-Prereq {
    param([string]$Name, [string]$Cmd, [string]$Install)
    Write-Host "Checking $Name..." -ForegroundColor Gray
    if (Test-Command $Cmd) {
        Write-Host "  $Name already installed." -ForegroundColor Green
        return $true
    }
    Write-Warning "$Name not found ($Cmd). $Install"
    return $false
}

# --------------------------------------------------------------------------- 1. prerequisites
if (-not $SkipPrereq) {
    $missing = @()

    $pyOk = Ensure-Prereq "Python" "py" "Install Python 3.11+ (winget install Python.Python.3.11 or python.org). Add to PATH."
    if (-not $pyOk) { $missing += "python" }

    $nodeOk = Ensure-Prereq "Node.js" "node" "Install Node.js LTS (winget install OpenJS.NodeJS.LTS)."
    if (-not $nodeOk) { $missing += "node" }

    $dockerOk = Ensure-Prereq "Docker" "docker" "Install Docker Desktop (winget install Docker.DockerDesktop). Required for the sandbox worker and production DB."
    if (-not $dockerOk) { $missing += "docker" }

    if (-not $SkipOllamaCheck) {
        $ollamaOk = Ensure-Prereq "Ollama" "ollama" "Install Ollama for Windows (ollama.com), then run: ollama pull codellama:7b-instruct"
        if (-not $ollamaOk) { $missing += "ollama" }
    }

    if ($missing.Count -gt 0) {
        Write-Warning "Missing prerequisites: $($missing -join ', '). Install them, then re-run this script."
    } else {
        Write-Host "All prerequisites present." -ForegroundColor Green
    }
} else {
    Write-Host "Skipping prerequisite checks (-SkipPrereq)." -ForegroundColor Yellow
}

# --------------------------------------------------------------------------- 2. backend environment
Write-Host "`n=== Backend setup ===" -ForegroundColor Cyan
if (-not (Test-Command py)) {
    Write-Error "Python launcher 'py' not found; cannot create venv. Install Python and retry."
    exit 1
}

Push-Location $backendDir

# Copy environment template (never commit real .env).
$envExample = Join-Path $repoRoot ".env.example"
$envFile    = Join-Path $backendDir ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "Copying .env.example -> backend/.env (edit secrets before production!)"
    Copy-Item $envExample $envFile
} else {
    Write-Host "backend/.env already exists; leaving it untouched." -ForegroundColor Gray
}

# Create / refresh the virtual environment.
$venv = Join-Path $backendDir ".venv"
if (-not (Test-Path (Join-Path $venv "Scripts" "Activate.ps1"))) {
    Write-Host "Creating Python virtual environment (.venv)..."
    py -m venv .venv | Out-Null
    Write-Host "Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Gray
}

$activate = Join-Path $venv "Scripts" "Activate.ps1"
& $activate | Out-Null

Write-Host "Installing backend dependencies (requirements.txt + dev)..."
python -m pip install --upgrade pip | Out-Null
python -m pip install -r requirements.txt | Out-Null
python -m pip install -r requirements-dev.txt | Out-Null
Write-Host "Backend dependencies installed." -ForegroundColor Green

# --------------------------------------------------------------------------- 3. database
Write-Host "`n=== Database ===" -ForegroundColor Cyan
if (Test-Command alembic) {
    Write-Host "Applying Alembic migrations (alembic upgrade head)..."
    alembic upgrade head | Out-Null
    Write-Host "Migrations applied." -ForegroundColor Green
} else {
    Write-Warning "alembic not on PATH after venv activation; migrations not applied."
}

# Seed dev database (idempotent). Uses backend/.env DATABASE_URL (sqlite dev fallback).
Write-Host "Seeding development database..."
python scripts/seed_db.py | Out-Null
Write-Host "Database seeded." -ForegroundColor Green

Pop-Location

# --------------------------------------------------------------------------- 4. Ollama model reminder
if (-not $SkipOllamaCheck) {
    Write-Host "`n=== Ollama (local AI) ===" -ForegroundColor Cyan
    Write-Host "Ollama must be running and a coding model pulled before AI features work."
    Write-Host "  ollama serve                          # start Ollama (if not already running)"
    Write-Host "  ollama pull codellama:7b-instruct     # pull the local coding model"
    Write-Host "AI_CLOUD_FALLBACK=false is set in .env.example; no paid cloud AI is used." -ForegroundColor Yellow
}

# --------------------------------------------------------------------------- 5. frontend
Write-Host "`n=== Frontend setup ===" -ForegroundColor Cyan
if (Test-Command npm) {
    Push-Location $webDir
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing frontend dependencies (npm ci)..."
        npm ci | Out-Null
        Write-Host "Frontend dependencies installed." -ForegroundColor Green
    } else {
        Write-Host "node_modules already present; skipping npm ci." -ForegroundColor Gray
    }
    Pop-Location
} else {
    Write-Warning "npm not found; frontend setup skipped."
}

Write-Host "`n=== Setup complete ===" -ForegroundColor Green
Write-Host "Next: .\scripts\dev.ps1   (starts backend + frontend)"
Write-Host "      backend:  pytest -q              (run tests)"
Write-Host "      frontend: cd apps/web && npm run dev"
