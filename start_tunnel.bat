@echo off
title JobPortal ERP - Cloudflare Edge Tunnel
cd /d "%~dp0"
echo ========================================================
echo  Launching JobPortal ERP and Cloudflare Tunnel...
echo  (Keep this window open while using the tunnel)
echo ========================================================
powershell.exe -NoExit -ExecutionPolicy Bypass -File "%~dp0run_tunnel.ps1"
