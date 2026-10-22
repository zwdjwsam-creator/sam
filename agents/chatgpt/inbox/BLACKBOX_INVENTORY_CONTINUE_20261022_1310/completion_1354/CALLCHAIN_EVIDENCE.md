# CALLCHAIN_EVIDENCE_1354

at: 2026-10-22T14:14:49+08:00
SYSTEM_INVENTORY_ACCEPTANCE: false

## Binding (static)
- unified reader resolve_product ← `blackbox_unified_market_data_plane_r1`
- price_plane resolve_product ← `blackbox_data_access_resolver_r1` (**distinct**)
- build_receipt defaults ≠ causal verification success

## Files
[
  {
    "path": "脚本\\blackbox_unified_market_data_plane_reader_r1.py",
    "exists": true,
    "sha256": "58139dd92df1e457be6e4abfcf79ee37382a75a5c6abe3c5dca21ac24c24f3ba",
    "bytes": 3873,
    "n_lines": 101
  },
  {
    "path": "脚本\\blackbox_unified_market_data_plane_r1.py",
    "exists": true,
    "sha256": "6826c1cf7c0e2d227f6e639f88897bd896bc380fb323ec5a1d9ccd400aefd9ce",
    "bytes": 20104,
    "n_lines": 508
  },
  {
    "path": "脚本\\blackbox_backtest_price_plane_r1.py",
    "exists": true,
    "sha256": "62beda130e6213f59b6f33a5066c5dae0f1b670f5761081537ec6d1d07af739a",
    "bytes": 6595,
    "n_lines": 161
  },
  {
    "path": "脚本\\blackbox_data_access_resolver_r1.py",
    "exists": true,
    "sha256": "88ec468f5b18bf7eec2002d605e7922d7ff085f6bbf9fb69d0d57d6d3716f6f5",
    "bytes": 43924,
    "n_lines": 938
  }
]

## Limits
- static line+SHA only; no production run
- build_receipt defaults ≠ causal verification success
- 1m consumer path ≠ 5m consumer path
