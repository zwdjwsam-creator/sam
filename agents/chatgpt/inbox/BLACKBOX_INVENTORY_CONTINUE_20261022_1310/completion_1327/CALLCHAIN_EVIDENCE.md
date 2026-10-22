# CALLCHAIN_EVIDENCE

at: 2026-10-22T13:44:19+08:00
SYSTEM_INVENTORY_ACCEPTANCE: false

## Files
[
  {
    "path": "脚本\\blackbox_unified_market_data_plane_reader_r1.py",
    "exists": true,
    "sha256": "58139dd92df1e457be6e4abfcf79ee37382a75a5c6abe3c5dca21ac24c24f3ba",
    "bytes": 3873,
    "n_lines": 101,
    "call_sites_n": 7
  },
  {
    "path": "脚本\\blackbox_backtest_price_plane_r1.py",
    "exists": true,
    "sha256": "62beda130e6213f59b6f33a5066c5dae0f1b670f5761081537ec6d1d07af739a",
    "bytes": 6595,
    "n_lines": 161,
    "call_sites_n": 6
  },
  {
    "path": "脚本\\blackbox_unified_market_data_plane_r1.py",
    "exists": true,
    "sha256": "6826c1cf7c0e2d227f6e639f88897bd896bc380fb323ec5a1d9ccd400aefd9ce",
    "bytes": 20104,
    "n_lines": 508,
    "call_sites_n": 48
  }
]

## resolve_product defs
[
  {
    "path": "脚本\\blackbox_unified_market_data_plane_r1.py",
    "line": 161,
    "sha256": "6826c1cf7c0e2d227f6e639f88897bd896bc380fb323ec5a1d9ccd400aefd9ce"
  }
]

## Separation
- 规则要求: HAND causal + plane contracts (locate via existing indexes; missing single path ≠ absent rule)
- 代码行为: see call_sites_sample in CALLCHAIN_EVIDENCE.json / source_fragments
- 正式入口是否调用 HAND gate: **UNPROVEN** this pass

## Limits
- line citations only; no production edits
- keyword/line presence ≠ runtime HAND gate proof
- 1m evidence ≠ 5m evidence
