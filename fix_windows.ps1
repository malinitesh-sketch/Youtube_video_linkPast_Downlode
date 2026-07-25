# Windows PowerShell fix script for YouTube Downloader App
# Right click this file -> Run with PowerShell
# Or run: powershell -ExecutionPolicy Bypass -File .\fix_windows.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "YouTube Downloader - Windows Fix Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Set-Location -Path $PSScriptRoot
Write-Host "Current folder: $PWD" -ForegroundColor Yellow

# If a venv is currently active, deactivate if possible
if (Get-Command deactivate -ErrorAction SilentlyContinue) {
    Write-Host "Deactivating old virtual environment..." -ForegroundColor Yellow
    deactivate
}

# Remove broken virtual environments
foreach ($folder in @(".venv", ".venv-2")) {
    if (Test-Path $folder) {
        Write-Host "Removing broken $folder ..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $folder
    }
}

# Find Python
$pythonCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} else {
    Write-Host "ERROR: Python not found. Install Python from https://www.python.org/downloads/" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Creating virtual environment..." -ForegroundColor Green
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    & $pythonCmd -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: venv create failed." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "Upgrading pip..." -ForegroundColor Green
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip

Write-Host "Installing packages..." -ForegroundColor Green
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: package install failed." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Checking system..." -ForegroundColor Green
& ".\.venv\Scripts\python.exe" check_system.py

Write-Host "" 
Write-Host "Starting server. Open browser: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "Keep this window open." -ForegroundColor Yellow
& ".\.venv\Scripts\python.exe" app.py

Read-Host "Press Enter to exit"
