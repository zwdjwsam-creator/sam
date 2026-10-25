# RUN GUIDE — reproduce this package (candidate only)

All commands run from `E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion`
with `E:\BLACKBOX\.venv\Scripts\python.exe`.

```powershell
# 1. cleaning candidate from retained RAW (no download)
python -X utf8 tools\build_candidate_cleaning_from_retained.py --asof 2026-09-24 `
  --run-target-date 2026-09-24 --replay-days 2026-08-31 2026-09-01

# 2. ORIGINAL compiler, candidate mode (never publishes)
python -X utf8 tools\run_original_compiler_candidate.py `
  --cleaning-json candidate\cc\CC_REPLAY_20260924\RELEASE.json `
  --parent-root "E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439" `
  --out-root candidate\cc_out\releases --acceptance-out candidate\cc_out\acceptance `
  --run-target-date 2026-09-24 --receipt evidence\ORIGINAL_COMPILER_RECEIPT.json

# 3. connected chain (transport -> gate -> cleaning -> compiler -> commit -> gate probe -> replay)
python -X utf8 tools\run_connected_pipeline.py --out deliverables\CONNECTED_PIPELINE.json

# 4. commit safety: mid-failure, crash-after-swap, replay, revised input
python -X utf8 tools\commit_recovery_selftest.py

# 5. provider semantics (4 repairs measured)
python -X utf8 tools\verify_provider_semantics.py

# 6. strict V4 run (no proxy, no inference) -> expected BLOCKED_INPUT_INCOMPLETE
python -X utf8 candidate\run_engine_backtest.py --start 2026-09-03 --end 2026-09-24 `
  --out engine_runs\v4_r21_R13_STRICT4 --strict-inputs

# 7. minute plane: product coverage + the strategy's real minute demand
python -X utf8 tools\build_minute_plane_evidence.py

# 8. factor lineage: P1/P6 vs CACHE, date encoding, constant-value classification
python -X utf8 tools\trace_factor_source.py
python -X utf8 tools\find_factor_nondate_rows.py
python -X utf8 tools\profile_corrupt_factor_dates.py
python -X utf8 tools\classify_factor_series.py

# 9. real R15 cleaning replay on the retained batches (production CURRENT/SSOT untouched)
python -X utf8 candidate\run_r15_cleaning_replay.py

# 10. publish_atomic non-dry-run rehearsal with every write target bound
python -X utf8 candidate\run_publish_atomic_rehearsal.py --reset

# 11. rewrite matrix / B1-B7 / acceptance / pipeline / change-index / command-log
python -X utf8 tools\consolidate_r13_round2.py
```

Reading order: `REPORT.md` → `ACCEPTANCE.json` → `FINAL_REQUIREMENT_MATRIX.json` →
`B1_B7_STATUS.json` → `evidence/PUBLISH_ATOMIC_REHEARSAL.json` →
`evidence/R15_CLEANING_REPLAY.json` → `evidence/FACTOR_SERIES_NATURE.json` →
`evidence/MINUTE_PLANE.json` → `CONNECTED_PIPELINE.json`.

Nothing in this guide writes production `CURRENT`, downloads data, or places an order.
Step 10 writes only inside `candidate/publish_rehearsal`; step 9 rebinds the cleaning CURRENT
pointer and SSOT to `candidate/r15_root`.
