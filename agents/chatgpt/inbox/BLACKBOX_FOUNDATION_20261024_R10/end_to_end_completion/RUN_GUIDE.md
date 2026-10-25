# RUN GUIDE — R10 end-to-end (R12 revision)

Bound runtime: `E:\BLACKBOX\.venv\Scripts\python.exe`
Task root: `E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion`

## 1. Contracts preflight

```powershell
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py --task-class BACKTEST --json
```

## 2. Rebuild the matrix / tradeability / pipeline

```powershell
cd E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 tools\raw_status_field_inventory.py
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 tools\build_tradeability_candidate.py
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 tools\build_dataset_state.py
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 tools\run_connected_pipeline.py
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 tools\build_checkpoint_bindings.py
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 tools\build_input_plane_repair_evidence.py
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 tools\record_commands.py
```

## 3. Requested-scope backtest (diagnostic unless blockers are zero)

```powershell
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 candidate\run_engine_backtest.py ^
  --start 2026-09-03 --end 2026-09-24 --strict-inputs --allow-candidate-override ^
  --local-dictionary D:\BB_LOCAL_DICTIONARY\R10_ASOF_20260924 ^
  --out engine_runs\v4_r21_20260903_20260924_R11_TRADEABILITY_RECON
```

The candidate tradeability partition must be published atomically before the run starts;
`tools\build_tradeability_candidate.py` does that with a temp file plus `os.replace`.

## 4. Read the results

- report: `deliverables\REPORT.md`
- acceptance: `deliverables\ACCEPTANCE.json`
- matrix: `deliverables\DATASET_STATE.json`
- pipeline: `deliverables\CONNECTED_PIPELINE.json`
- input plane: `evidence\INPUT_PLANE_REPAIR.json`
- engine: `engine_runs\v4_r21_20260903_20260924_R11_TRADEABILITY_RECON\run_result.json`

## 5. Rollback / restore

No sealed release, CURRENT pointer, RAW root or production publication was modified.
To discard this round only:

```powershell
Remove-Item -Recurse -Force candidate\data\R11_TRADEABILITY, candidate\data\R12_PIPELINE, pipeline_runs
Remove-Item -Recurse -Force engine_runs\v4_r21_20260903_20260924_R11_TRADEABILITY_RECON
```

## 6. Guards

`NEW_DATA_ACQUISITION_AUTHORIZED=false` · `CURRENT_SWITCH_ALLOWED=false` · `ORDER_ALLOWED=false`
No supplier call, no broker adapter, no production `publish_atomic`.
