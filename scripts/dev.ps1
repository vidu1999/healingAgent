#requires -Version 5.1
<#
.SYNOPSIS
    Start the SentinelOps AI backend and frontend on Windows.
.DESCRIPTION
    Launches the FastAPI backend (uvicorn) and the Next.js frontend (npm run dev)
    in separate PowerShell windows. Activate the backend venv first if you want
    to run commands against it directly.
    Backend: http://localhost:8000   Frontend: http://localhost:3000
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRoot   = Resolve-Path (Join-Path $scriptRoot "..")
$backendDir = Join-Path $repoRoot "backend"
$webDir     = Join-Path $repoRoot "apps/web"

Write-Host "=== SentinelOps AI - dev server ===" -ForegroundColor Cyan

# Backend venv must exist.
$venvActivate = Join-Path $backendDir ".venv" "Scripts" "Activate.ps1"
if (-not (Test-Path $venvActivate)) {
    Write-Error "Backend venv not found. Run .\scripts\setup.ps1 first."
    exit 1
}

if (-not (Test-Path (Join-Path $webDir "node_modules"))) {
    Write-Warning "Frontend node_modules missing. Run .\scripts\setup.ps1 first."
}

Write-Host "Starting backend (uvicorn on :8000)..." -ForegroundColor Gray
Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$backendDir'; . .venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000"
) -WindowTitle "SentinelOps Backend"

Start-Sleep -Seconds 2

Write-Host "Starting frontend (Next.js on :3000)..." -ForegroundColor Gray
Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$webDir'; npm run dev"
) -WindowTitle "SentinelOps Frontend"

Write-Host "`nBoth services launched in separate windows." -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000/health/live" -ForegroundColor Gray
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Gray
Write-Host "  Docs:     http://localhost:8000/api/docs (dev only)" -ForegroundColor Gray
