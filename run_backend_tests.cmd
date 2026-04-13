@echo off
setlocal
echo Running backend tests...
echo.

where python >nul 2>nul
if not errorlevel 1 (
    python -m unittest discover -s backend\tests -v
    set EXIT_CODE=%errorlevel%
    goto :finish
)

where py >nul 2>nul
if not errorlevel 1 (
    py -m unittest discover -s backend\tests -v
    set EXIT_CODE=%errorlevel%
    goto :finish
)

echo No supported Python interpreter was found on PATH.
echo Install Python or update your PATH, then run this script again.
set EXIT_CODE=1
goto :finish

:finish
if not defined EXIT_CODE set EXIT_CODE=0
echo.
if "%EXIT_CODE%"=="0" (
    echo Backend tests passed.
) else (
    echo Backend tests failed with code %EXIT_CODE%.
)
echo Press any key to close this window.
pause >nul
exit /b %EXIT_CODE%
