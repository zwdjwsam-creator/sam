# FACTOR_EVIDENCE_NOTE (SAM)

- child_task_id: `BLACKBOX_UPDATE_PREREQUISITES_SAM_20261027`
- generated_at_cn: 2026-10-27T12:46:00+0800
- collector_run: **NOT_RUN** (fixture gate failed 2/17; dispatch rule applied)
- basis: already-retained evidence only. No provider probe, no market-data scan, no factor fill.

## 1. What the retained R15 contract actually asks for

From `E:\BLACKBOX\任务\BLACKBOX_FULL_DATA_UPDATE_R15_20260810_R1\03_DOWNLOAD_CONTRACTS\DOWNLOAD_CONTRACT.json`:

- `source_API` = `jqdatasdk.get_price`
- `fq` = `None` (literal), `price_basis` = `RAW_NONE`
- `fields` = `['open', 'close', 'high', 'low', 'volume', 'money']`
- `skip_paused` = `True`, `panel` = `False`

So the retained R15 units are **RAW_NONE price rows**. They do not, by themselves, constitute an
adjustment-factor series.

## 2. Three things that must be kept apart

| concept | what it is | what this host has |
|---|---|---|
| raw price factor **column** | a `factor` column physically present in a price payload | only where a payload carried it; absence is not a violation when the contract does not require the column |
| separate **adjustment factor** product | `ADJUST_FACTOR_PIT_R1` in the cache release | exists as a product; its 2026 content has a measured anomaly (below) |
| **adjusted prices** (derived) | price x factor under a declared anchor basis | not produced or certified here |

## 3. Retained observations about the 2026 adjustment-factor plane

Measured earlier in this task chain on SAM's sealed cache (not re-measured here):

- `ADJUST_FACTOR_PIT_R1` 2026 partition: 44 sessions in 2026-07-25..09-26, of which **13 sessions
  have `nunique == 1`** (single distinct value, min == max == 1.0), while other sessions range up
  to 233 distinct values.
- Source: `C:\LAN_SHARE_REPORT\BLACKBOX_FOUNDATION_R10_SAM_SOURCE_HANDOFF_20261025\review_probe\SAM_DAILY_FACTOR_CHECK.json`
  (`factor.part_2026.parquet.sessions`).
- The desktop's R13 review additionally recorded 17 incremental files whose `date` column is an
  integer `0..299` rather than a timestamp.

**Cause is NOT established.** The observations are equally compatible with the requested `fq`
parameters and normalisation basis, the SDK return shape, local serialisation, or the supplier
content. This note does **not** assert supplier fabrication and does **not** conclude that a
re-download is required.

## 4. Consequence, stated as a boundary not a verdict

- Factor-basis uncertainty blocks **dependent adjusted-price uses**.
- It does **not** automatically block an independently specified `RAW_NONE` scope, because a
  RAW_NONE scope does not consume the adjustment factor.
- Any future receipt for an adjustment-dependent product must carry request/returned stable-key
  identities plus the applicable page/exhaustion/universe contract; requested/returned counts
  alone cannot certify completeness.

## 5. Explicit UNKNOWN / not done

- No provider call, no quota probe, no factor refresh, no factor value fill.
- No recomputation of adjusted prices.
- No claim about which process produced the current `ADJUST_FACTOR_PIT_R1` partition.
