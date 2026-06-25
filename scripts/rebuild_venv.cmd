@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0rebuild_venv.ps1" %*
