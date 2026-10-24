# R10 continuation receipt — registered factor generations and original writer candidates

Append-only executor receipt. New file this round; no earlier report is amended.
Task: `R10_FACTOR_GENERATION_BASIS_AND_ORIGINAL_WRITER_20261025`.
Executor: ZHANGWEI (local desktop, Cursor agent).
Status returned by the supplied driver: `FACTOR_GENERATION_BASIS_MEASURED`.
This is R10 continuation. It is not R11 and not system acceptance.

---

## 1. Package verification, before any execution

The package manifest `agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R10_FACTOR_BASIS_20261025/PACKAGE.json`
(1,489 B, sha256 `c0235be75fc415ef239919fb5ff25076fe63f12e603a2199e6783dbc540b5fa6` recorded in
`PACKAGE_VERIFICATION.json`) declares 8 members. All 8 were checked by exact byte count **and** exact SHA256
before anything was executed. Result: `all_pins_match = true`, `mismatch_stop_triggered = false`.

The three reused helpers are byte-identical to the accepted reconciliation round:

    r10_factor_input_contract.py   4,046 B   e30acaddecf03e0abd4360f60a74bae53525373e55feb51cf76d409beebe67c5   identical
    r10_factor_desktop_check.py    7,495 B   76693d0834086e22b2afa62c70c4973b8271e14242ccae5c7f2a3f269d3cfed0   identical
    r10_factor_reconcile.py       11,223 B   171146f589fe1dbaf6903a1a5b631718732175705cb25ccf81e08a657145ae33   identical

No source edit, no newline normalisation, no pin regeneration, no substitute test and no alternative harness
was used. Downloads were compared byte-for-byte against the staged copies and are identical.

## 2. Supplied offline controls

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\factor_basis\test_r10_factor_basis.py

Literal stdout: `{"tests_run": 12, "passed": true, "scope": "FACTOR_RATIO_INVARIANCE_OFFLINE_ONLY", "supplier_calls": 0, "FOUNDATION_ACCEPTANCE": false}`
Literal stderr: `Ran 12 tests in 0.141s` / `OK`. Exit code 0. 12 of 12 pass. Dependent steps were therefore run.

## 3. Registered factor-generation comparison

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\factor_basis\r10_factor_basis.py --desktop-check

Executed exactly once, exit code 0, 1,341,456 bytes of stdout
(sha256 `afbdaee971741a6d635e493b3c03fd6417af6125d9f026223b3a2abac19d6303`), empty stderr, 106.7 s.
The supplied driver invoked the genuine preflight
`reviews/R10/operating_entry/blackbox_operate_r10.py describe --product ADJUST_FACTOR_PIT_R1`
(exit 0, `MUST_READ_PRECHECK=PASS`, `task_class=CACHE`). `source_files_changed=false`,
`supplier_calls=0`, `all_layer_search_performed=false`. No data was written.

Enumeration stayed inside the one registered R26 factor root
`数据/清洗成品/releases/BLACKBOX_FORMAL_CLEANING_R26_ADJFACTOR_PIT_ASOF_20260814_20260816_044000/standard/fundamentals/adjust_factor`
with its 13-partition layout. No alternative root was guessed. CACHE identities are prior pins; the 2014–2025
R26 identities are newly measured and explicitly `NEW_MEASURED_NOT_ADMITTED`, while R26 2026 carries a prior
content pin (`PRIOR_PIN_MATCH`). Every partition is `SHAPE_VALID_ONLY_NOT_ADMITTED`.

### 3.1 Per-year tuple comparison

| year | clean rows | cache rows | shared | clean_only | cache_only | unequal on shared | tested | no common anchor | after anchor | mismatched |
|---|---|---|---|---|---|---|---|---|---|---|
| 2014 |   620,803 |   620,803 |   620,803 | 0 | 0 | 10,884 |   564,517 | 56,286 | 0 | 0 |
| 2015 |   665,913 |   665,913 |   665,913 | 0 | 0 | 12,211 |   609,333 | 56,580 | 0 | 0 |
| 2016 |   704,876 |   704,876 |   704,876 | 0 | 0 | 12,910 |   647,986 | 56,890 | 0 | 0 |
| 2017 |   799,798 |   799,798 |   799,798 | 0 | 0 | 13,487 |   742,367 | 57,431 | 0 | 0 |
| 2018 |   857,319 |   857,319 |   857,319 | 0 | 0 | 14,336 |   800,130 | 57,189 | 0 | 0 |
| 2019 |   890,482 |   890,482 |   890,482 | 0 | 0 | 15,081 |   834,886 | 55,596 | 0 | 0 |
| 2020 |   951,992 |   951,992 |   951,992 | 0 | 0 | 16,270 |   899,692 | 52,300 | 0 | 0 |
| 2021 | 1,062,380 | 1,062,380 | 1,062,380 | 0 | 0 | 17,721 | 1,014,781 | 47,599 | 0 | 0 |
| 2022 | 1,149,235 | 1,149,235 | 1,149,235 | 0 | 0 | 19,009 | 1,109,371 | 39,864 | 0 | 0 |
| 2023 | 1,211,865 | 1,211,865 | 1,211,865 | 0 | 0 | 19,879 | 1,182,213 | 29,652 | 0 | 0 |
| 2024 | 1,236,214 | 1,236,214 | 1,236,214 | 0 | 0 | 20,101 | 1,217,944 | 18,270 | 0 | 0 |
| 2025 | 1,251,439 | 1,251,439 | 1,251,439 | 0 | 0 | 20,816 | 1,243,478 | 7,961 | 0 | 0 |
| 2026 |   774,406 |   863,710 |   774,406 | 0 | **89,304** | 13,199 |   772,570 | 1,836 | 0 | 0 |
| **total** | **12,176,722** | **12,266,026** | **12,176,722** | **0** | **89,304** | **205,904** | **11,639,268** | **537,454** | **0** | **0** |

Twelve year partitions have identical tuple keys and identical row counts. Only 2026 differs:
`clean_only=0`, `cache_only=89,304`, `row_delta_cache_minus_clean=89,304`. R26 Cleaning 2026 ends at
2026-08-14; CACHE 2026 continues to 2026-09-24, and the `cache_only_sample` starts exactly at 2026-08-17.
So the row delta is an extension of the date range, not a hole on shared dates.

### 3.2 Explicit 2026-08-14 normalised comparison

Anchor `2026-08-14`, relative tolerance `1e-12`, applied to every year:

    normalisation_mismatched_keys = 0 in all 13 years
    normalisation_max_relative_error = 2.220446049250313e-16 in all 13 years
    shared_keys_after_anchor_not_tested = 0 in all 13 years
    shared_keys_at_or_before_anchor_without_common_anchor = 537,454 total (counted, never filled)

The last line is the honest limit: 537,454 shared keys sit at or before the anchor but have no common anchor
observation for their security, so they are **untested**, not equal and not unequal.

### 3.3 Cross-year per-security scale

`cross_year_scale_summary` covers 5,465 securities, each with multiple observations:
`constant_scale_within_tolerance = 5,465`, `non_constant_scale = 0`, `single_observation_codes = 0`.
The largest relative scale span across 2014–2026 is `4.440892098500626e-16`, i.e. floating-point noise.

So on measured shared keys the two generations differ by one constant per security. Because
`pre(d|T) = raw(d) * factor(d) / factor(T)` with `d <= T`, a per-security constant cancels in the ratio; this is
algebra, not a vendor-provenance assumption. The equality claim is limited to tested shared keys. It does not
extend to untested dates, to the 537,454 keys without a common anchor, to keys absent from both generations, or
to any source/PIT completeness claim. A `factor` value of 1.0 in R26 2026 (e.g. `2026-01-05`) is a valid
observation, not a provenance certificate.

## 4. The two count discrepancies, kept separate

    physical_minus_declared = 83,503        (12,266,026 physical rows - 12,182,523 declared)
    tuple row delta, 2026                  = 89,304   (CACHE 2026 863,710 - Cleaning 2026 774,406)

`83,503` is a physical-minus-declared difference of counts. It is **not** 83,503 missing source rows and no
year is identified as faulty by it. The accepted reconciliation already showed the declared and measured 2026
counts agree at 863,710; this round adds the Cleaning baseline per year, and Cleaning 2026 has 774,406 rows
because it stops at 2026-08-14. Neither number is rewritten to match the other.

Also measured here: R26 Cleaning total `12,176,722` equals `SOURCE_COVERAGE.json total_rows 12,176,722` in the
writer task directory, so the cleaning generation and its own source coverage agree exactly.

## 5. Scoped original-source lookup

    rg -n --hidden --no-ignore --fixed-strings --max-filesize 2M --glob "*.py" --glob "*.ps1" --glob "!**/.git/**" --glob "!**/.venv/**" --glob "!**/node_modules/**" --glob "!**/__pycache__/**" -e "BACKWARD_DIRTY_FULL_HISTORY_REPLACE" -e "n_rows_year_2026" -- "E:\BLACKBOX\脚本" "E:\BLACKBOX\任务" "E:\BLACKBOX\运行"

Exit code `0` with `2` hits, 452 bytes of stdout, 0 bytes of stderr, existing rg
(`C:\cursor\resources\app\node_modules\@vscode\ripgrep\bin\rg.exe`). No other tool installed, no other root
searched, no link followed.

    hit 1  ORIGINAL SOURCE
           E:\BLACKBOX\任务\BLACKBOX_ADJUST_FACTOR_PIT_R1_FULL_REBUILD_AND_BACKWARD_REFRESH_R1\incremental_backward_refresh_r1.py
           line 246  pub = publish_successor(new_df, "BACKWARD_DIRTY_FULL_HISTORY_REPLACE")
           11,537 B   sha256 1df97ec81882243716cece03afb786638a05028642f97309cf71a3bcea3456f0
    hit 2  LOCAL HUB CHECKOUT COPY, byte-identical to hit 1
           E:\BLACKBOX\运行\外部大脑信箱\agents\chatgpt\inbox\BLACKBOX_INVENTORY_CONTINUE_20261022_1310\completion_1507\source_reads\incremental_backward_refresh_r1.py
           line 246, same 11,537 B, same SHA256

`n_rows_year_2026`: **0 hits** inside the three searched roots. The string exists only in product
`COVERAGE.json` metadata, which no searched source emits.

Because hit 2 is a HUB-mirrored copy, the body is already published and was reused rather than re-uploaded. The
remote blob was fetched and verified byte-identical:
`agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1507/source_reads/incremental_backward_refresh_r1.py`,
blob sha `95d6704f08f8d02d5dc76dc63671a7745f04487a`, 11,537 B, sha256 `1df97ec8...`. Evidence: `HUB_REUSE_CHECK.json`.

Genuinely new original body, not previously on HUB, uploaded as a BASE64 carrier with round-trip verification:

    E:\BLACKBOX\脚本\blackbox_adjust_factor_incremental_backward_refresh_r1.py
    723 B   sha256 d236dacb2e6033bac09737c0bf6da20f8c5155dbb751a0181d087d5d704c3553
    carrier original_bodies/blackbox_adjust_factor_incremental_backward_refresh_r1.BASE64_ORIGINAL_BYTES.json
    decoded length and SHA256 re-verified after writing: identical

It is the registered permanent entry that resolves the task script and refuses (`HARD_BLOCK`) if the engine is
missing, then runs it under `guarded_run`. It makes no supplier call.

### 5.1 What the located source states

`publish_successor(new_factor, reason)` writes into `COVERAGE.json`: `product_id`, `date_min`, `date_max`,
`n_codes`, `n_rows = int(len(new_factor))`, `fq`, `reason`; and writes the release pointer with `cache_release_id`,
`release_root`, `asof`, `parent_release_id`, `mode`, `ADJUST_FACTOR_PIT_R1`, `notes`. That is the mechanism behind
both literals: the reason is the backward-refresh label and the declared count is the in-memory frame length at
publish time.

`AUTHORITY_GATES.json` in the same directory binds `BACKWARD_REFRESH_ENGINE` to this exact path and
`BACKWARD_REFRESH_SCRIPT` to the wrapper above, with `source_min_date 2014-01-02` and `SOURCE_MAX_DATE 2026-08-14`.

An execution receipt binding this program to a real run was retained and is included:
`INCREMENTAL_RECEIPT.json` — `update_date 2026-09-02`, `backward_dirty_count 7`,
`full_history_refreshed_count 7`, `factor_revision_rows 7`, `resolver_release BLACKBOX_CACHE_R1_ADJFACTOR_PIT_INCR_20260903_010456`,
`fq pre`, `raw_fallback_used false`, `silent_factor_one_used false`, `AUTHORITY_READY true`.

### 5.2 Link status: PARTIAL, stated as measured

The current COVERAGE.json also carries `tip_extended_at`, `tip_source` and `n_rows_year_2026`. This program does
not emit any of them. So the located file is the writer of the `reason` label and of the base declared count, and
one backward refresh is proven to have run on 2026-09-02 for 7 codes — but this file is **not** a proven writer of
the tip-extension fields on the currently mounted release
`BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439`. A string match is a source candidate; it is not
proof of execution, and no matched source was imported, executed or patched this round.

Exit code 0 means two literal matches inside a bounded search. It is **not** an all-layer data-absence diagnosis,
it does not claim which writer produced 2014–2025, and it does not claim the current release's tip fields have no
writer elsewhere; they simply have no writer inside the three roots searched.

## 6. Status

    B1_ADJUSTMENT_RECONCILIATION             OPEN  (measured numerically, not closed)
    B2..B7                                   OPEN  (preserved, none reclassified here)
    FULL_GOAL_MET                            false
    FOUNDATION_ACCEPTANCE                    false
    FORMAL_ENGINE_ADMISSION                  false
    INCREMENTAL_PIPELINE_READINESS           NOT_ACCEPTED
    LATEST_FULL_UPDATE                       NOT_VERIFIED
    NEW_DATA_ACQUISITION_AUTHORIZED          false
    CURRENT_SWITCH_ALLOWED                   false
    ORDER_ALLOWED                            false
    SOURCE_ABSENCE_CLAIM_ALLOWED             false

No business-data write, historical refresh, login, supplier call, download, candidate promotion, CURRENT change,
engine construction or order occurred in this round. Nothing found by the source lookup was invoked.

GPT owns the next data, contract and compiler decisions. All required preconditions must pass before an
incremental acquisition command is issued.
