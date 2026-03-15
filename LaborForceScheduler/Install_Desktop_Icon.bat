@echo off
setlocal
cd /d "%~dp0"

set "SHORTCUT_NAME=LaborForceScheduler.lnk"
set "TARGET=%~dp0Run_LaborForceScheduler.bat"
set "WORKDIR=%~dp0"
set "ICON=%~dp0assets\petroserve.png"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$Desktop=[Environment]::GetFolderPath('Desktop');" ^
"$ShortcutPath=Join-Path $Desktop '%SHORTCUT_NAME%';" ^
"$WScriptShell=New-Object -ComObject WScript.Shell;" ^
"$Shortcut=$WScriptShell.CreateShortcut($ShortcutPath);" ^
"$Shortcut.TargetPath='%TARGET%';" ^
"$Shortcut.WorkingDirectory='%WORKDIR%';" ^
"if (Test-Path '%ICON%') { $Shortcut.IconLocation='%ICON%' };" ^
"$Shortcut.Save()"

if %errorlevel%==0 (
    echo Desktop shortcut created: %SHORTCUT_NAME%
) else (
    echo Failed to create desktop shortcut.
    exit /b 1
)

endlocal
