# run_tunnel.ps1 - JobPortal Cloudflare Edge Launcher
param(
    [int]$Port = 5000
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
    $FlaskJob = Start-Process -FilePath $PythonExe -ArgumentList "app.py" -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 2
} else {
    Write-Host "[+] Flask application is already running on port $Port." -ForegroundColor Green
}

# 4. Start Cloudflare Tunnel
Write-Host "[+] Connecting to Cloudflare Edge Network..." -ForegroundColor Green
& $CloudflaredExe tunnel --url "http://127.0.0.1:$Port"
