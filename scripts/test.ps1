#requires -Version 5.1
<#
.SYNOPSIS
    Run the SentinelOps AI backend test suite.
.DESCRIPTION
    Activates the backend virtual environment and runs pytest.
#>
[CmdletBinding()]
param(
    [switch]$Watch
)

$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$backendDir = Join-Path (Resolve-Path (Join-Path $scriptRoot "..")) "backend"
$venvActivate = Join-Path $backendDir ".venv" "Scripts" "Activate.ps1"

if (-not (Test-Path $venvActivate)) {
    Write-Error "Backend venv not found. Run .\scripts\setup.ps1 first."
    exit 1
}

Push-Location $backendDir
& $venvActivate | Out-Null

if ($Watch) {
    python -m pytest -q -p no:cacheprovider --looponfailroots "$PWD"
} else {
    python -m pytest -q
}
$exitCode = $LASTEXITCODE
Pop-Location

exit $exitCode
