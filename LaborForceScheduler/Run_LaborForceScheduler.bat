@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
    py -3 scheduler_app_v3_final.py
) else (
    python scheduler_app_v3_final.py
)

endlocal
