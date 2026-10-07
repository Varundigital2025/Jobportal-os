# run_tunnel.ps1 - JobPortal Cloudflare Edge Launcher
param(
    [int]$Port = 5000,
    [switch]$AutoDeploy = $true,
    [switch]$Background = $false,
    [switch]$Stop = $false,
    [switch]$Status = $false
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$TunnelPidFile = Join-Path $ScriptDir ".tunnel.pid"
$FlaskPidFile = Join-Path $ScriptDir ".flask.pid"
$LogFile = Join-Path $ScriptDir "tunnel.log"
$PythonExe = Join-Path $ScriptDir "venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) { $PythonExe = "python" }
$CloudflaredExe = Join-Path $ScriptDir "cloudflared.exe"

# ----------------------------------------------------
# 1. Handle -Stop
# ----------------------------------------------------
if ($Stop) {
    Write-Host "Stopping JobPortal services and Cloudflare Tunnel..." -ForegroundColor Yellow
    if (Test-Path $TunnelPidFile) {
        $tPid = Get-Content $TunnelPidFile -ErrorAction SilentlyContinue
        if ($tPid) { Stop-Process -Id $tPid -Force -ErrorAction SilentlyContinue }
        Remove-Item -Force $TunnelPidFile -ErrorAction SilentlyContinue
    }
    Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

    if (Test-Path $FlaskPidFile) {
        $fPid = Get-Content $FlaskPidFile -ErrorAction SilentlyContinue
        if ($fPid) { Stop-Process -Id $fPid -Force -ErrorAction SilentlyContinue }
        Remove-Item -Force $FlaskPidFile -ErrorAction SilentlyContinue
    }
    Write-Host "[+] Cloudflare Tunnel and Flask application have been stopped." -ForegroundColor Green
    return
}

# ----------------------------------------------------
# 2. Handle -Status
# ----------------------------------------------------
if ($Status) {
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "             JobPortal Edge & Tunnel Status               " -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Cyan

    $cfProcesses = Get-Process cloudflared -ErrorAction SilentlyContinue
    if ($cfProcesses) {
        Write-Host "[+] Cloudflare Tunnel daemon: RUNNING (PID: $($cfProcesses.Id -join ', '))" -ForegroundColor Green
    } else {
        Write-Host "[-] Cloudflare Tunnel daemon: STOPPED (Causes Error 1033!)" -ForegroundColor Red
    }

    $flaskConn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($flaskConn) {
        Write-Host "[+] Flask backend application: RUNNING on port $Port (PID: $($flaskConn.OwningProcess -join ', '))" -ForegroundColor Green
    } else {
        Write-Host "[-] Flask backend application: NOT RUNNING on port $Port" -ForegroundColor Red
    }

    if (Test-Path $LogFile) {
        $Content = Get-Content $LogFile -Raw -ErrorAction SilentlyContinue
        if ($Content -match 'https://([a-zA-Z0-9\-]+\.trycloudflare\.com)') {
            Write-Host "[*] Active Quick Tunnel URL:  $($Matches[0])" -ForegroundColor Cyan
        }
    }
    Write-Host "[*] Cloudflare Worker Gateway: https://jobportal-erp.varundigitaluiux.workers.dev" -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan
    return
}

# ----------------------------------------------------
# 3. Startup Header
# ----------------------------------------------------
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   JobPortal ERP - Cloudflare Edge Deployment Launcher    " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

# ----------------------------------------------------
# 4. Check / Download cloudflared.exe
# ----------------------------------------------------
if (-not (Test-Path $CloudflaredExe)) {
    Write-Host "[*] Downloading Cloudflare tunnel binary..." -ForegroundColor Yellow
    curl.exe -L -o $CloudflaredExe https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
}

# ----------------------------------------------------
# 5. Check / Start Flask app
# ----------------------------------------------------
$Conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if (-not $Conn) {
    Write-Host "[*] Starting Flask application on port $Port..." -ForegroundColor Cyan
    $FlaskProc = Start-Process -FilePath $PythonExe -ArgumentList "app.py" -WorkingDirectory $ScriptDir -WindowStyle Hidden -PassThru
    if ($FlaskProc) {
        $FlaskProc.Id | Out-File -FilePath $FlaskPidFile -Encoding ascii
    }
    Start-Sleep -Seconds 3
} else {
    Write-Host "[+] Flask application is already running on port $Port." -ForegroundColor Green
}

# ----------------------------------------------------
# 6. Stop any stale cloudflared instances
# ----------------------------------------------------
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
if (Test-Path $TunnelPidFile) { Remove-Item -Force $TunnelPidFile -ErrorAction SilentlyContinue }

# ----------------------------------------------------
# 7. Start Cloudflare Quick Tunnel
# ----------------------------------------------------
Write-Host "[+] Connecting to Cloudflare Edge Network..." -ForegroundColor Green
if (Test-Path $LogFile) { Remove-Item -Force $LogFile }

$TunnelProc = Start-Process -FilePath $CloudflaredExe -ArgumentList "tunnel", "--url", "http://127.0.0.1:$Port" -RedirectStandardError $LogFile -PassThru -WindowStyle Hidden
if ($TunnelProc) {
    $TunnelProc.Id | Out-File -FilePath $TunnelPidFile -Encoding ascii
}

$TunnelUrl = $null
$TimeoutSec = 30
$Elapsed = 0

Write-Host "[*] Waiting for Cloudflare quick tunnel to establish..." -ForegroundColor Yellow
while ($Elapsed -lt $TimeoutSec -and -not $TunnelUrl) {
    Start-Sleep -Seconds 1
    $Elapsed++
    if (Test-Path $LogFile) {
        $Content = Get-Content $LogFile -Raw -ErrorAction SilentlyContinue
        if ($Content -match 'https://([a-zA-Z0-9\-]+\.trycloudflare\.com)') {
            $TunnelUrl = $Matches[0]
        }
    }
}

if (-not $TunnelUrl) {
    Write-Host "[!] Could not detect tunnel URL automatically within $TimeoutSec seconds." -ForegroundColor Red
    Write-Host "    Check $LogFile for details." -ForegroundColor Yellow
    return
}

Write-Host "[+] Cloudflare Tunnel established: $TunnelUrl" -ForegroundColor Green

# ----------------------------------------------------
# 8. Deploy / Sync Cloudflare Worker
# ----------------------------------------------------
if ($AutoDeploy) {
    Write-Host "[*] Updating Cloudflare Worker backend config..." -ForegroundColor Cyan
    $WranglerJson = Join-Path $ScriptDir "cloudflare-worker\wrangler.jsonc"
    $IndexJs = Join-Path $ScriptDir "cloudflare-worker\src\index.js"

    if (Test-Path $WranglerJson) {
        (Get-Content $WranglerJson) -replace 'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', $TunnelUrl | Set-Content $WranglerJson
    }
    if (Test-Path $IndexJs) {
        (Get-Content $IndexJs) -replace 'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', $TunnelUrl | Set-Content $IndexJs
    }

    Write-Host "[*] Deploying Worker to Cloudflare..." -ForegroundColor Cyan
    Set-Location (Join-Path $ScriptDir "cloudflare-worker")
    npx wrangler deploy
    Set-Location $ScriptDir
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " [OK] Deployment Complete and Active!" -ForegroundColor Green
Write-Host " Cloudflare Worker URL: https://jobportal-erp.varundigitaluiux.workers.dev" -ForegroundColor Cyan
Write-Host " Tunnel Target URL:     $TunnelUrl" -ForegroundColor Gray
Write-Host " Status Endpoint:       https://jobportal-erp.varundigitaluiux.workers.dev/cloudflare-status" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""

if ($Background) {
    Write-Host "[+] Tunnel and Flask are now running in the BACKGROUND." -ForegroundColor Green
    Write-Host "    To check status:  .\run_tunnel.ps1 -Status" -ForegroundColor Cyan
    Write-Host "    To stop:          .\run_tunnel.ps1 -Stop" -ForegroundColor Yellow
} else {
    Write-Host "[!] NOTE: Keep this terminal open to keep the tunnel alive." -ForegroundColor Yellow
    Write-Host "    Closing this terminal terminates the tunnel and causes Cloudflare Error 1033." -ForegroundColor Yellow
    Write-Host "    (Tip: Run with -Background to run silently in the background: .\run_tunnel.ps1 -Background)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press Ctrl+C to stop the tunnel." -ForegroundColor Yellow
    $TunnelProc.WaitForExit()
}
