# ETF_CALLCHAIN_STATIC_1118

at: 2026-10-21T11:29:20+08:00
SYSTEM_INVENTORY_ACCEPTANCE: false
history: UNPROVEN

## Source SHA
- unified: 6826c1cf7c0e2d227f6e639f88897bd896bc380fb323ec5a1d9ccd400aefd9ce
- etf_1m: cadddb88549b36ee971fd5463d90a71cf40f90d35969bed15ccb6745f14ab316

## Unified plane chain
resolve_product → _scan_cleaning_dir / _scan_raw_year_envelope → coverage_window / list_files_for_window

## ETF 1m chain
cleaning_etf_1m_dir → scan_root → build_shard_manifest → overlapping_shards → read_overlapping → filter_request / dedupe_canonical

## Fragment select
STATIC_LOCATED_NEED_ISOLATED_READONLY_SAMPLE（未跑写入口；覆盖声明≠实际读取）

JSON: continuation_1118/ETF_CALLCHAIN_STATIC_1118.json
