# Thin launcher — pinned Anaconda py3.10.20; force UTF-8 stdio
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$Py = "D:\Anaconda3\envs\blackbox_bt_py310\python.exe"
$Entry = Join-Path $PSScriptRoot "query_stock_daily_bounded_r1.py"
if (-not (Test-Path $Py)) { Write-Error "INTERPRETER_MISSING: $Py"; exit 2 }
& $Py -u $Entry @args
exit $LASTEXITCODE
