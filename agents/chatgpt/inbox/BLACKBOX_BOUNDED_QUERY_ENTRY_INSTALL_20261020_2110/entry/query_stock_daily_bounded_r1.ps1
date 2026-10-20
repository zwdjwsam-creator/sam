# Thin launcher — pinned Anaconda py3.10.20 used for V4 acceptance (not broken .venv)
$ErrorActionPreference = "Stop"
$Py = "D:\Anaconda3\envs\blackbox_bt_py310\python.exe"
$Entry = Join-Path $PSScriptRoot "query_stock_daily_bounded_r1.py"
if (-not (Test-Path $Py)) { Write-Error "INTERPRETER_MISSING: $Py"; exit 2 }
& $Py -u $Entry @args
exit $LASTEXITCODE
