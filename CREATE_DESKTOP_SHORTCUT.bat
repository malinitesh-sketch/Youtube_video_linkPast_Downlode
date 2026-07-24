@echo off
setlocal
title Create AnyDownloader Desktop Shortcut

:: Get the project directory
set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

:: Get desktop path
set "DESKTOP=%USERPROFILE%\Desktop"

:: Check if shortcut already exists
if exist "%DESKTOP%\AnyDownloader.lnk" (
    echo A shortcut already exists on your desktop.
    choice /M "Do you want to overwrite"
    if errorlevel 2 exit /b
)

:: Create shortcut using PowerShell (single-line command)
echo Creating desktop shortcut...
powershell -Command "$WScriptShell = New-Object -ComObject WScript.Shell; $Shortcut = $WScriptShell.CreateShortcut([string]'%DESKTOP%\AnyDownloader.lnk'); $Shortcut.TargetPath = '%PROJECT_DIR%\RUN_ANYDOWLOADER.bat'; $Shortcut.WorkingDirectory = '%PROJECT_DIR%'; $Shortcut.Description = 'AnyDownloader - YouTube Downloader'; $IconPath = [Environment]::SystemDirectory + '\imageres.dll'; $Shortcut.IconLocation = $IconPath + ',179'; $Shortcut.Save()"
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to create shortcut.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo    ✓ Desktop shortcut created!
echo    📌 Double-click "AnyDownloader" on your
echo       desktop to run anytime!
echo ==========================================
echo.
echo Shortcut location: %DESKTOP%\AnyDownloader.lnk
echo.
pause

