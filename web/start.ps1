# ============================================================
#  Smart Hospital Room - Khoi dong web dashboard (offline)
#  Camera & MediaPipe yeu cau chay qua http://localhost
# ============================================================
$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot
$port = 8000
Write-Host ""
Write-Host " ====================================================" -ForegroundColor Cyan
Write-Host "  PHONG BENH THONG MINH - Web Dashboard"            -ForegroundColor White
Write-Host "  Server: http://localhost:$port"                   -ForegroundColor Green
Write-Host "  (Nhan Ctrl+C de dung)"                            -ForegroundColor DarkGray
Write-Host " ====================================================" -ForegroundColor Cyan
Write-Host ""
Start-Process "http://localhost:$port/index.html"
python serve.py $port
