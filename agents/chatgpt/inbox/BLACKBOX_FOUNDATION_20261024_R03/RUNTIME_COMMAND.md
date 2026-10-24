# R03 dedicated runtime -- reproducible launch commands

All commands assume the recovery tree `E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024`.

## Interpreter

- Executable: `E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\runtime\.venv\Scripts\python.exe`
- Python: 3.12.10
- pandas: 2.3.3
- pyarrow: 21.0.0
- numpy: 2.5.4
- Dependency lock: `runtime/REQUIREMENTS_LOCK.txt`

The interpreter is isolated. System Python 3.12 and the historical project `.venv`
(whose `pyvenv.cfg` points at a foreign path) are untouched.

## Creation (already executed; reproducible)

```powershell
$py = "C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe"
$W  = "E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024"
& $py -m venv "$W\runtime\.venv"
& "$W\runtime\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "$W\runtime\.venv\Scripts\python.exe" -m pip install "numpy>=1.26,<3" "pandas>=2.2,<3" "pyarrow>=15,<22"
& "$W\runtime\.venv\Scripts\python.exe" -m pip freeze > "$W\runtime\REQUIREMENTS_LOCK.txt"
```

Network access was used only for this package installation (explicitly authorized this cycle).

## Run the conformance suite (writes TEST_RESULTS.json)

```powershell
Set-Location "E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024"
.\runtime\.venv\Scripts\python.exe -u tests\test_conformance_r3.py
```

## Rebuild the English registry (reads parquet footer statistics once, then caches)

```powershell
.\runtime\.venv\Scripts\python.exe -u build_registry_r3.py
.\runtime\.venv\Scripts\python.exe -u eco_query_r3.py --validate
.\runtime\.venv\Scripts\python.exe -u eco_query_r3.py --coverage
```

## Rebuild the structure map

```powershell
.\runtime\.venv\Scripts\python.exe -u build_system_structure.py
```

## Direct read (bounded, read-only)

```powershell
.\runtime\.venv\Scripts\python.exe -u -c "from candidate.r3.provider import LocalValueProvider; p=LocalValueProvider(); e=p.get_price('000001.XSHE','2026-06-01','2026-06-30',fields=['open','close'],fq='none'); print(e['status'], e['row_count'], p.trade_days('2026-06-01','2026-06-30').__len__())"
```

## Engine-contract adapter (leaf load, no engine core activation)

```powershell
.\runtime\.venv\Scripts\python.exe -u -c "from candidate.r3.engine_adapter import EngineLocalValueProvider; a=EngineLocalValueProvider(); df=a.get_price('000001.XSHE','2026-06-01','2026-06-03',fq='none',fill_paused=False); print(type(df).__name__, df.index.__class__.__name__, list(df.columns), df.attrs['bb_status'])"
```

`formal_backtest_active` and `engine_core_active` remain `false`; nothing was switched on.
