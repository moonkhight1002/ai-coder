@echo off
setlocal

where python >nul 2>nul
if not errorlevel 1 (
    python "%~dp0test_runner.py" %*
    exit /b %errorlevel%
)

where py >nul 2>nul
if not errorlevel 1 (
    py "%~dp0test_runner.py" %*
    exit /b %errorlevel%
)

echo No supported Python interpreter was found on PATH.
echo Install Python or update your PATH, then run this script again.
exit /b 1
