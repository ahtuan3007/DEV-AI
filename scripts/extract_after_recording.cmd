@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0extract_after_recording.ps1" %*
