@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_training_workspace.ps1" %*
