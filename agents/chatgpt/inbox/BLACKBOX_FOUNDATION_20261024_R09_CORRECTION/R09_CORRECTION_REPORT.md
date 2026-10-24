# R09 CORRECTION — tempdir repair executed, requested deliverables completed

Round: R09/10 correction (NOT R10). Host: ZHANGWEI. Date: 2026-10-24.
Consumes: `agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R09_PREFLIGHT_FIX_20261024_2140` and `REVIEW_R09_CORRECTION.md`.

This report answers the review point by point. It adds records only. It does not promote a candidate,
publish a release, start an engine, acquire data, or touch any business file, seal, pointer or credential.

```
FOUNDATION_ACCEPTANCE=false
ORDER_ALLOWED=false
CURRENT_SWITCH_ALLOWED=false
PRODUCTION_CHANGE_AUTHORIZED=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
```

## S1. Executable correction — ran on this host

Supplied package pins verified byte-for-byte before use (3/3 match `R09_TEMP_DIR_FIX_PACKAGE.json`).

- `fix_r09_preflight_tempdir.py --source reviews/R09/control_2100/r09_control_runtime.py` → exit 0,
  `FIXED_ENTRY_CREATED`, sha256 `f52236648c37eb91944fd7e03e545f18ed887dc0e2c7ec12f2dcdeb6895d9d24`,
  which equals the package's declared `fixed_runtime_sha256`. Re-run → `ALREADY_FIXED_VERIFIED`.
- The original runner stayed at `87ff01f3…`, the four successor modules stayed at their build SHAs,
  `production_modified=false`, `write_exceptions_added=0`.
- The guard's denial predicate is byte-identical between original and fixed entry (asserted, not asserted-by-eyeball).
- **Corrected real ordered entry executed end-to-end:** `r09_control_runtime_preflight_fixed.py` → exit 0,
  all four steps ran (`1_MUST_READ`, `2_PINNED_SOURCE_AND_RULE_BINDING`, `3_BOUNDED_CANDIDATE_READ`,
  `4_SHADOW_AND_PUBLISH_BLOCK_CONTROLS`), and step 1 returned a real `MUST_READ_PRECHECK` = `PASS`
  with kernel `b05a6995…` (1167 bytes, 21 lines) and both rules `VERIFIED` against the live manifest.
  0 write exceptions, 0 supplier calls, 0 network.
  Retained: `executed_code/DESKTOP_FIXED_ENTRY.txt` (sha recorded in `R09_FIXED_ORDERED_ENTRY_EVIDENCE.json`).

**The supplied ten-control test, unmodified, does not reach ten green controls on Windows.** It stops at its own
line 78 (`assert after.returncode==0`) after five controls pass. This is a fixture newline defect, not a repair
defect: the fixture derives the expected digest from `read_bytes()` after `write_text('fixture\n')`, which on
Windows stores CRLF (`sha256 = 5bd17a4a…`), while the child's `read_text()` returns LF (`sha256 = e80b71cd…`).
The child in fact got past the import probe, installed the guard, executed the real successor preflight and
rejected the fixture on SHA — i.e. the very path under test is live; only the fixture's own expectation cannot
match on this platform.

To close that portability gap without editing the supplied file, `additive_win_completion_test_r09_tempdir.py`
replays the identical ten invariants with byte-exact fixture writes: **10/10 PASS**, guard bytes identical,
`guard_write_exceptions=0`, and the rejection strings (`R09_PREFLIGHT_WRITE_BLOCKED`,
`R09_PREFLIGHT_SIDE_EFFECT_BLOCKED:*`, `SHA_AUTHORITY_MISSING_KERNEL`) unchanged.
The supplied file's sha256 is recorded unmodified in `R09_TEMP_DIR_FIX_DESKTOP_RESULTS.json`.

## S2. Stage-1 substitution withdrawn; conservation number corrected

- The stage-1 substituted diagnostic is retained only as non-authoritative history. Its `1_MUST_READ`
  step was never executed by that harness and is **not counted**. No gate was substituted again, no
  `ok=True` fabricated, no harness re-run.
- The genuine end-to-end PASS that was missing now exists — see S1, from the corrected entry.
- Literal conservation for this command's two selected frames: `parent_keys = 959896`,
  `candidate_keys = 959896`, `lost_keys = 0`, `lost close observations = 0`, scope
  `EXACT_INPUT_FRAMES_ONLY_NOT_GLOBAL_COVERAGE_OR_ENGINE_ADMISSION`.
  The earlier prose `949,470 → 959,896` belongs to a different factor-gate comparison and is **withdrawn**
  for this command. The two recovered request rows still do not upgrade CURRENT and do not prove
  full-universe usability.

## S3. Per-catalog-product operating matrix — all rows, joined from existing records

`CATALOG_PRODUCT_OPERATING_MATRIX.json` carries **41 of 41** catalog rows (previously 14 were summarized).
No Parquet file was reopened and no root was re-scanned: every cell is a join of records produced by R04,
R06, R07 and R08, each cited with path and sha256 in the file's `inputs`.

Catalog accounting (`CATALOG_ACCOUNTING.json`): 4020 bytes, no BOM, LF only, trailing newline,
**43 lines = 1 header + 41 data rows + 1 blank line (index 41) + 0 comment lines**.
Earlier "42 rows" was a miscount; header/blank are now explicit and the balance is asserted.

State distribution across the 41 rows:

| operating_state | rows |
|---|---|
| SEPARATE_NAMESPACE_RESOLVED (Tushare CBOND) | 14 |
| CURRENT_DECLARED_GAP | 11 |
| NOT_MEASURED_IN_REVIEWED_EVIDENCE | 6 |
| CURRENT_PRODUCT_EMPTY | 3 |
| CURRENT_SERVES_MEASURED_WINDOW | 3 |
| REGISTRY_METADATA_PRODUCT | 2 |
| SEPARATE_NAMESPACE_UNRESOLVED_BINDING (minute 1m) | 2 |

Layer totals: L1 25, L2 12, L3 2, META 2 (sum 41). Three measured pairs carry an identical measured tuple
in the R07 record (`STOCK_DAILY_PIT_R1`/`STOCK_FACTOR_DAILY_R1`, `ETF_DAILY_PIT_R1`/`ETF_FACTOR_DAILY_R1`,
`INDEX_DAILY_R1`/`INDEX_FACTOR_DAILY_R1`), consistent with a shared partition set per asset class; the matrix
flags those six rows with `measurement_caveat` and does not read the duplicates as proof of distinct coverage.

## S4. ADJUST_FACTOR — sidecar, not a supplier receipt; reconciliation left open

`ADJUST_FACTOR_SIDECAR_RECONCILIATION.json`:

- `COVERAGE.json` is classified `PRODUCT_PUBLICATION_OR_COVERAGE_SIDECAR`, **not** a supplier
  request/page/acquisition receipt.
- Declared rows `12,182,523` vs physically measured `12,266,026` → difference `+83,503` (physical − declared).
  Status `UNRESOLVED_SIDECAR_VS_CONTENT`. Neither count is adopted as truth; possible roles (build-time
  declaration, partition exclusion, key-vs-row counting) are listed as hypotheses only.
- A 3,097-date union proves date presence at that grain only. It does not prove every symbol, every valid
  factor observation, or completeness of a `factor=1` series. Nothing was repaired from filenames.
- Honest content note: on the two requested dates the product carries 5,208 rows (2026-08-31) and **11 rows**
  (2026-09-01). Date presence and session content are clearly different facts; the 11-row session is recorded
  as such.
- Source linkage remains product-level only (`tip_source`, `tip_extended_at`, `reason`); the per-date
  RAW→CLEANING→CACHE ledger rows were not produced.

## S5. SW — route and bounded observations separated from inheritance and admission

`SW_ROUTE_VS_INHERITANCE.json` keeps four distinct layers:

1. `ROUTE` — `TIP_COMPILER.inject_sw` present; three pointer-driven routes.
2. `BOUNDED_OBSERVATION` — measured only: pointer sha256 + gate_pass for L1/L2/L3, standard root exists,
   `FULL` membership and structure files exist, 13 partition-year directories per plane, footer row counts
   (membership 12,587,795 / 12,575,466 / 12,564,290; structure 90,046 / 351,502 / 825,939), and derived
   max date 2026-09-24 matching the pointer on all three.
3. `INHERITANCE_INTO_CURRENT_CACHE` — `REFERENCE_ONLY_NOT_BYTE_VERIFIED` (release `RELEASE.json` declares
   `READY_INTEGRATED`; the R08 candidate carries the six SW products as preserved references).
4. `ADMISSION` — `NONE`.

No SW Parquet was re-read this round.

## S6. Writer/producer claim replaced with a cited search identity

`PRODUCER_SEARCH_EVIDENCE_BINDING.json` retracts `writer_files_found = []` from the previous bundle: it was
not a measured exhaustive search and cited no ledger. Replacement statement:
**`PRODUCER_UNBOUND_IN_REVIEWED_EVIDENCE`**, supported by:

- R04 `TRADABLE_STATUS` row — declared `REQUIRED` (`security_state_daily_include=true` →
  `STOCK_TRADEABILITY_PIT_R1`), RAW `P2_security_state` (956 files), CLEAN `stock_limit_pause_status` (3 files),
  possession `PRESENT_COVERAGE_UNVERIFIED`, acquisition `CONFIGURED_NOT_VERIFIED`.
- R06 `NEXT_UPDATE_BINDINGS` — `PERMISSION_OK_DOWNLOAD_GAP`, observed product coverage
  `2026-07-13..2026-08-12 plus one 2026-09-03 tip`, i.e. a download gap, not a permission gap.
- R07 ledger scope and entries L08 (universe: `CACHE_COVERAGE_REGRESSION`, extend from pinned security state),
  L09 (tradeability: `CLEANING_COMPLETE_CACHE_MISSING`, materialize from RAW fields), L11 (namespace
  classification map), with the recorded searched roots and index used.
- Consumer references located earlier: resolver name map and PIT policy; external-evidence agent reading a
  tradeability release root.

Not claimed: that no producer exists anywhere, that RAW is absent, any acquisition. The two minute-1m
products keep only what L11 records.

## S7. Generation identities — roles separated, nothing relabelled

`GENERATION_IDENTITY_ROLES.json` records that the differing IDs are distinct metadata roles by design:
selection pointer (`CURRENT_CACHE_RELEASE.json`) / release generation record (`RELEASE.json`) / product
addition record (`MANIFEST.json`) / minimal acceptance stamp (`SEAL.json`, carrying only `accepted` and
`sealed_at` — it cannot name what it sealed) / cleaning pointer-plus-inheritance (product-bearing release id
plus daily-tip parent fields) / capability generation declaration.

No old seal, id or pointer is rewritten. The stale capability-generation mismatch stays **rejected**
(`CAPABILITY_FACTS_GENERATION_STALE`); it is not solved by relabelling historical content. A future serving
envelope must bind the chosen manifest plus each actual source and version while retaining these identities.

## S8. Engine runtime — declarations, not a proven startup requirement

`ENGINE_RUNTIME_REQUIREMENT_CLASSIFICATION.json` uses the actual packaging declaration plus a static AST
import trace of the delivered engine sources (no execution, no install):

| package | class |
|---|---|
| matplotlib | guarded `try/except` at import in the package `__init__` → warns and continues |
| python-dotenv | lazy `from dotenv import load_dotenv` inside `load_env`, wrapped in `except ImportError` |
| filelock, plotly, pyecharts, tabulate, jupyterlab, ipykernel | **zero import references** in the delivered sources → declared-only, startup need unproven |

All eight do appear in `[project] dependencies`, so the honest reading is: declared core, but the delivered
code neither requires six of them nor hard-fails on the other two. Counts: 8 missing = 1 guarded-optional +
1 lazy-optional + 6 declared-only-unproven. No notebook stack was installed as an inferred repair. A real
engine start trace and MASTER admission remain unproven separately, and the R08 verdict is retained but
relabelled `RUNTIME_INVENTORY_VERDICT__NOT_A_PROVEN_STARTUP_FAILURE`.

## S9. Mapping and command/exit evidence

`CORRECTION_FILE_MAPPING.json` supplies the exact repo-relative path for every file of the previous R09 bundle
(23 entries), correcting the defect where `DELIVERY_MANIFEST.remote` held bare basenames for files that live
under `executed_code/` and `tools/`. The remote bytes were already correct; only the manifest text was wrong.

`COMMAND_AND_EXIT_LEDGER.json` is a command/exit ledger, not "literal stdout is the evidence": each of the 16
commands carries argv, cwd, interpreter, exit code, and either a retained stdout file with sha256/bytes or the
explicit value `NOT_RETAINED` with the reason. Where a first capture was overwritten by an identical-exit
re-run, that is stated rather than reconstructed.

## Decision compliance

Still R09. No R10 task, no candidate promotion, no production publication, no engine startup, no acquisition,
no trading. All business files, historical evidence, pointers, seals and credentials unchanged.
