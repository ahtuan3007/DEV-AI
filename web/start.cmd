@echo off
REM ============================================================
REM  Smart Hospital Room - Khoi dong web dashboard (offline)
REM  Camera & MediaPipe yeu cau chay qua http://localhost
REM ============================================================
cd /d "%~dp0"
set PORT=8000
echo.
echo  ====================================================
echo   PHONG BENH THONG MINH - Web Dashboard
echo   Dang mo server tai: http://localhost:%PORT%
echo   (Nhan Ctrl+C de dung)
echo  ====================================================
echo.
start "" "http://localhost:%PORT%/index.html"
python serve.py %PORT%
