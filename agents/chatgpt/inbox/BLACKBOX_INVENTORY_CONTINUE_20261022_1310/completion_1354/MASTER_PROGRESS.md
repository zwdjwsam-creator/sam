# MASTER_PROGRESS_1354

at: 2026-10-22T14:14:49+08:00
reply_to: BLACKBOX_DATA_MANAGEMENT_COMPLETE_EVIDENCE_20261022_1354
SYSTEM_INVENTORY_ACCEPTANCE: **false**
status: PARTIAL_CONTENT_FIXES_APPLIED

## What this pass actually completed
1. **Generator evidence selection fixed** (`run_completion_1354_worker.py`):
   - ETF 1m/5m: active `observed_range=UNPROVEN`; stock frag bounds moved to `historical_stock_*` only; tip day span cited from `ETF_TRUE_PATH_READ_0836` without claiming full history.
   - FUND_NAV: canonical active observed = deepen_0000 full stream `2014-01-02..2026-09-24` rows=`6496121` shards=`5980`; sample 8770 retained side-by-side.
2. **UPDATE_CHAIN**: `data_directory` vs `release_pointer_file` vs `release_resolved_product_dir` separated — authority_path no longer copied as pointer.
3. **CALLCHAIN**: uploaded unified + data_access_resolver fragments; documented distinct `resolve_product` bindings.
4. **ENGINE_SCOPE**: explicitly `CANDIDATE_ONLY_NOT_SCOPE_COMPLETE`.
5. Old `check_inventory_master` retained (not loosened).

## Counts
{
  "products": 75,
  "etf_stock_bounds_excluded_active": 2,
  "fund_full_read_canonicalized": 1,
  "required_range_unproven": 75,
  "update_pointer_file_unproven": 75,
  "engine_rows_candidate_only": 17
}

## Consistency (old checker)
{
  "rows": 75,
  "unique_ids": 75,
  "issue_counts": {},
  "report_consistency_pass": true,
  "system_inventory_acceptance": false
}

## Remaining
[
  {
    "bucket": "数据缺口",
    "object": "ETF active date envelope",
    "evidence": "0836 path verified; tip day span only; mat full envelope not dated in evidence",
    "impact": "ETF observed_range stays UNPROVEN (correct)",
    "next": "bounded mat year-header read OR cite existing dated ledger — not stock frag"
  },
  {
    "bucket": "数据缺口",
    "object": "required_range still UNPROVEN for 75/75",
    "evidence": "shared contract pass logged; no product-specific envelope cited",
    "impact": "cannot claim completeness",
    "next": "per-family contract pages already indexed under 950/MANIFEST — continue cite-only"
  },
  {
    "bucket": "更新流程",
    "object": "release_pointer_file / watermark / resume",
    "evidence": "pointer_file UNPROVEN=75; data_directory separated",
    "impact": "ops resume undocumented",
    "next": "bind CURRENT pointer files without mutating them"
  },
  {
    "bucket": "引擎",
    "object": "ENGINE_SCOPE candidate-only",
    "evidence": "path heuristic; root listing accepted as discovery only",
    "impact": "not engine-scope complete",
    "next": "entry-point proof from existing authority indexes only"
  }
]

## Separation of claims
| Claim | Status |
|---|---|
| Inventory evidence selection honest | improved this pass |
| Data usable for strategy | **not claimed** |
| Strategy admission | **not claimed** |
| SYSTEM_INVENTORY_ACCEPTANCE | **false** |
