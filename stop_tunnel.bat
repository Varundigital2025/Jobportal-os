@echo off
title Stop JobPortal ERP Tunnel
cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File "%~dp0run_tunnel.ps1" -Stop
pause
