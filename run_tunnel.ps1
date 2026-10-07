# run_tunnel.ps1 - JobPortal Cloudflare Edge Launcher
param(
    [int]$Port = 5000,
    [switch]$AutoDeploy = $true
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   JobPortal ERP - Cloudflare Edge Deployment Launcher    " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 1. Check Python virtual environment
$PythonExe = Join-Path $ScriptDir "venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host "[!] Virtualenv python not found at $PythonExe. Using system python." -ForegroundColor Yellow
    $PythonExe = "python"
}

# 2. Check / download cloudflared.exe
$CloudflaredExe = Join-Path $ScriptDir "cloudflared.exe"
if (-not (Test-Path $CloudflaredExe)) {
    Write-Host "[*] Downloading Cloudflare tunnel binary..." -ForegroundColor Yellow
    curl.exe -L -o $CloudflaredExe https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
}

# 3. Check if Flask app is already running on target port
$Conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if (-not $Conn) {
    Write-Host "[*] Starting Flask application on port $Port..." -ForegroundColor Cyan
    Start-Process -FilePath $PythonExe -ArgumentList "app.py" -WorkingDirectory $ScriptDir -WindowStyle Hidden
    Start-Sleep -Seconds 3
} else {
    Write-Host "[+] Flask application is already running on port $Port." -ForegroundColor Green
}

# 4. Start Cloudflare Tunnel and capture URL
Write-Host "[+] Connecting to Cloudflare Edge Network..." -ForegroundColor Green
$LogFile = Join-Path $ScriptDir "tunnel.log"
if (Test-Path $LogFile) { Remove-Item -Force $LogFile }

$TunnelProc = Start-Process -FilePath $CloudflaredExe -ArgumentList "tunnel", "--url", "http://127.0.0.1:$Port" -RedirectStandardError $LogFile -PassThru -NoNewWindow

$TunnelUrl = $null
$TimeoutSec = 20
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

if ($TunnelUrl) {
    Write-Host "[+] Cloudflare Tunnel established: $TunnelUrl" -ForegroundColor Green
    
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
    
    Write-Host "`n==========================================================" -ForegroundColor Green
    Write-Host " [✓] Deployment Complete & Active!" -ForegroundColor Green
    Write-Host " Cloudflare Worker URL: https://jobportal-erp.varundigitaluiux.workers.dev" -ForegroundColor Cyan
    Write-Host " Tunnel Target URL:    $TunnelUrl" -ForegroundColor Gray
    Write-Host " Status Endpoint:      https://jobportal-erp.varundigitaluiux.workers.dev/cloudflare-status" -ForegroundColor Cyan
    Write-Host "==========================================================`n" -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop the tunnel." -ForegroundColor Yellow
    $TunnelProc.WaitForExit()
} else {
    Write-Host "[!] Could not detect tunnel URL automatically. Waiting on process..." -ForegroundColor Red
    $TunnelProc.WaitForExit()
}
