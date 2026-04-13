@echo off
setlocal
echo Starting Coding Platform Study Solver backend...
echo.

where python >nul 2>nul
if not errorlevel 1 (
    python -m backend.server %*
    set EXIT_CODE=%errorlevel%
    goto :finish
)

where py >nul 2>nul
if not errorlevel 1 (
    py -m backend.server %*
    set EXIT_CODE=%errorlevel%
    goto :finish
)

echo No supported Python interpreter was found on PATH.
echo Install Python or update your PATH, then run this script again.
set EXIT_CODE=1
goto :finish

:finish
if not defined EXIT_CODE set EXIT_CODE=0
if not "%EXIT_CODE%"=="0" (
    echo.
    echo Backend exited with code %EXIT_CODE%.
    echo Press any key to close this window.
    pause >nul
)
exit /b %EXIT_CODE%
