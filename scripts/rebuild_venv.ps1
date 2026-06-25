param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $root ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

Write-Host "Using Python command: $Python"
& $Python --version

if (Test-Path $venvPath) {
    Write-Host "Removing existing .venv..."
    Remove-Item -LiteralPath $venvPath -Recurse -Force
}

Write-Host "Creating .venv..."
& $Python -m venv $venvPath

Write-Host "Installing dependencies..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $root "requirements.txt")

Write-Host "Done. Test with:"
Write-Host "  .\scripts\extract_after_recording.cmd"
