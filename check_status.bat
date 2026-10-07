@echo off
title JobPortal ERP Status Check
cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File "%~dp0run_tunnel.ps1" -Status
pause
