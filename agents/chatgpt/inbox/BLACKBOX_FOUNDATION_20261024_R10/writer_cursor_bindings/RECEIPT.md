# R10 receipt — acquisition writer / cursor / transform bindings (static)

Task: `BLACKBOX_FOUNDATION_R10_WRITER_CURSOR_AND_TRANSFORM_BINDINGS_20261025`
Executor host: ZHANGWEI. Round: R10 continuation.
Method: inert byte reads, name scans and hash measurement. No analysed module was imported, executed, helped, self-tested or resumed. No supplier call, no credential value, no download, no merge, no CURRENT write, no order.

## 1. Concrete problem addressed

The captured June checkpoint is not a proven daily cursor; six-lane Lane A is an observer; `blackbox_daily_increment_orchestrator_r1.py` is post-download; a CLI target is not supplier availability.

This round binds the exact source call graph and names the unresolved edges. It is not another plan and not a new test suite.

## 2. Source citations

| Row | Callable | Body | Span | Hash-verified |
|---|---|---|---|---|
| A stock/ETF/index daily | `download_universe_daily` | `post_seal_daily_download_r8.py` (R05 body, sha `e4081da69c0a6892…`) | L124–144 | yes |
| B adjustment factor | `download_adjust_factor_day` | `aux_billboard_adjust_index_minute_r15.py` (sha `767c73c7a5c17e01…`) | L102–147 | yes |
| C RAW_NONE minute | guarded P7 loop | `p7_guarded_1m_download.py` (sha `9fd0b3060c73086b…`) | L296–335 | yes |
| C declared entry | — | `jq_download_execution_r1.py` (sha `bcbfd68d04402ce9…`) guards L1–14, L16–29 | — | yes |
| D finance/event | `fetch_finance_paginated` | `blackbox_acquisition_finance_adapter_r1.py` (sha `9d14fddeef036291…`) | L94–176 | yes |
| D pagination engine | `paginate_in_memory` | `blackbox_acquisition_pagination_engine_r1.py` (sha `978aedee181eac78…`) | L77–149 | yes |
| E external evidence | `main` | `blackbox_external_evidence_materialization_r2.py` (sha `028f301c5d9e6a11…`) | L1716–1878 | yes |
| E invoker | `collect_lane_b` | `run_blackbox_daily_incremental_data_plane_r1.py` (sha `deb363bcb1a71860…`) | L238–262 | yes |

## 3. Findings that drive the next round

1. **No retained entry is bound to the stock/ETF/index daily writer.** `main()` L292–496 of `post_seal_daily_download_r8.py` is its only caller. A bounded name scan over `脚本` and `任务` returned **0** referencing files. Recorded as `NOT_BOUND_IN_RETAINED_SOURCE`, not as absence of a local entry.
2. **Its window is not a cursor.** `GAP_START` and `GAP_END` are both `'2026-08-05'` (L32–33), `AS_OF = date(2026,8,5)` (L34). Advancing the date requires editing module constants.
3. **`jq_download_execution_r1.py` is unreachable by design.** Two unconditional module-top guards (L1–14, L16–29) make import raise `SystemExit(0)` and `__main__` exit 1, so all 57 callables including `run_t7` L2644–2729 never execute. The credential path literal at L65 is inside this blocked body and was not opened.
4. **The declared P7 replacement entry does not resolve.** `guard/jq_p7_minute_guarded_download_entry_r1.py`, named in the guard comment at L10, is not present under `脚本`. Two archived copies exist under RAW `_manifest/.../guard/` and `.../guard_fix/`, neither on the declared path. Bounded observation only.
5. **Minute writes keep the axis in the parquet index.** `result.to_parquet(str(out_path), index=True)` at L321 and L323, with `fields` excluding `code` and `time`, is the shape that yields an index-derived date column downstream.
6. **Adjustment factor has no checkpoint and no basis tag.** Batch failures are logged and skipped (L115–116) while the run can still return `PASS`; output columns are `date, code, factor, sec_type` only (L128).
7. **The only content-sealed cursor found is index-minute align.** `read_previous_cutoff` L356–368 reads `SEAL.json['cutoff']`; the pointer names `release_id BLACKBOX_INDEX_MINUTE_ALIGN_R1_ASOF_20260924_20260925_033441` with a `previous_release_id` chain.
8. **The daily cache stage mounts SW alignment, it does not compute it.** `inject_sw` L355–416 copies `SW_L{1,2,3}_MEMBERSHIP_PIT_FULL.parquet` and `partitions/year=*` from a sealed release pointer.
9. **Finance has a bound caller but no production writer.** The only bound edge is `main --live-canary-no-write` → `run_live_canary` → `fetch_finance_paginated`, which declares `raw_write: False, download_ops: 0` (L224–225) and writes one canary JSON.
10. **The pagination engine is arithmetic only.** It is imported by the finance adapter (L19–27) and has no SDK import, no auth and no write; `--allow-live-canary` returns `LIVE_CANARY_BLOCKED_UNTIL_P2_PIPELINE_AUTHORIZES` with exit 2.

## 4. Which reviewed entry initiates acquisition after all gates

- Bound invocation edges exist for: row B (self-contained R15 aux script), row C (self-contained guarded P7 script whose declared entry is unresolved), row E (data-plane Lane B invoking the external materialisation script).
- Row D has a bound caller that is explicitly no-write.
- Row A has no bound caller.

This is a binding result. It is not an assertion that no local entry exists, and `SOURCE_ABSENCE_CLAIM_ALLOWED` stays false.

## 5. Separately stated ambient states

Checkpoint authority (June `JQ_DATA_DOWNLOAD_EXECUTION_R1` batch state), supplier publication lag, local calendar horizon, expected historical universe and factor-basis authority remain separately stated and unresolved. None is converted into a current fact, and B1..B7 stay open. Stale PASS summaries were not reused as verdicts.

## 6. Permitted source handoff

`E:\BLACKBOX\脚本\blackbox_acquisition_pagination_engine_r1.py` was read as inert bytes only: 7,786 bytes, sha256 `978aedee181eac7815daed14a5b057f4ab3f8c663afa6f8c18e541561a02beae`, UTF-8 with BOM, 222 lines. A literal scan for token/bearer/ghp_/gho_/github_pat_/password/passwd/secret/api_key/apikey/聚宽账号/CRED_FILE/secrets returned no matches. The complete original bytes are carried base64 with a verified round trip (decoded 7,786 bytes, identical SHA256, byte-equal). This is a newly measured source identity, not a prior pin and not proof of execution.

## 7. Artifacts in this delivery

`ACQUISITION_WRITER_CURSOR_BINDINGS.json` (6 rows), `TRANSFORM_CALL_BINDINGS.json` (6 stages), `PAGINATION_ENGINE_ORIGINAL_BYTES.json`, `PROVENANCE_REUSED_VS_NEW.json`, `RECEIPT.md`, `DELIVERY_MANIFEST.json` (self-excluded).

## 8. Not done

No reopened accepted comparisons, no repeated controls, no annual reconciliation, no inventory, no RAW schema scan, no substitute source search, no `status` invocation of the six-lane runner, no import/run/resume/help of `jq_download_execution_r1.py`, no production patch, no factor/date fill, no engine construction.

FOUNDATION_ACCEPTANCE=false
FORMAL_ENGINE_ADMISSION=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false
SOURCE_ABSENCE_CLAIM_ALLOWED=false

END
