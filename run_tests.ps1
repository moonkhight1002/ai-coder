$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCommand) {
    & $pythonCommand.Source "$PSScriptRoot\test_runner.py" @args
    exit $LASTEXITCODE
}

$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($pyLauncher) {
    & $pyLauncher.Source "$PSScriptRoot\test_runner.py" @args
    exit $LASTEXITCODE
}

Write-Error "No supported Python interpreter was found on PATH. Install Python or update your PATH."
exit 1
