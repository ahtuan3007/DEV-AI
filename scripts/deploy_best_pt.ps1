# Copy a downloaded online YOLO model to the filename used by the app.
param(
    [Parameter(Mandatory = $true)]
    [string]$SourcePath
)

$dest = Join-Path $PSScriptRoot "..\best (1).pt"
Copy-Item -Path $SourcePath -Destination $dest -Force
Write-Host "Da copy model -> $dest"
Write-Host "Chay app: .\scripts\run_terminal_test.cmd"
