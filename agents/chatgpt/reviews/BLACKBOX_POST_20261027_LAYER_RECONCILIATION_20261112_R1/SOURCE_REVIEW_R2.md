# Independent Source Review R2 — R1 Metadata Capture

Review time: 2026-11-12T20:12:00Z (2026-11-13 04:12:00 Asia/Shanghai)  
Repository: `zwdjwsam-creator/sam`  
Branch: `main`  
Head reviewed: `ff66d5f4de2d73e617512655c655bd8d364b467d`  
Execution host: `ZHANGWEI`

## Decision

The existing R1 task remains outstanding and must not be replayed, edited in flight, stopped, or duplicated. Its package-pin mismatch remains a blocking pre-execution condition. A separate source-level defect was found in the currently published capture code: the path-prefix literals contain doubled runtime separators, so normal JSON-decoded Windows paths are not recognized by `registered_path_references`.

This is a metadata-summary defect, not a source-data absence finding and not evidence that the one-shot capture has run. The R1 inbox return directory is absent on the reviewed branch; no ACK or native status is present.

## Exact reviewed source identities

| Artifact | Path | Git blob SHA |
|---|---|---|
| R1 task | `agents/chatgpt/outbox/BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1.md` | `c2d564ba1f7d8be970a76e9818cd9cf9a58e55be` |
| Capture code | `agents/chatgpt/reviews/BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1/capture_registered_layer_metadata_r1.py` | `c988acb7d89bbf11919065c830e264e2a95f3b7c` |
| Offline tests | `agents/chatgpt/reviews/BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1/test_capture_registered_layer_metadata_r1.py` | `5d733ec7145e2090ca8845321021eec1a1a40f95` |
| Package manifest | `agents/chatgpt/reviews/BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1/PACKAGE.json` | `ca50a94ebcd8beddd4c9f391f2d450edd3df567a` |
| Prior package-pin audit | `agents/chatgpt/reviews/BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1/PACKAGE_PIN_AUDIT.md` | `f6236f35cc252dc679e08355f4e3dbf8d949e62d` |
| R1 review | `agents/chatgpt/reviews/BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1/REVIEW.md` | `de3c18b3f0b8b7c17f7d3af2be1dc9ad7d007ede` |
| R10 report | `agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/R10_REPORT.md` | `3707e1d6b052bc4e27a85d7c230a409bfc82a71e` |
| R13 round-2 report | `agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/REPORT.md` | `c0ee01d8d1b6f33debfde3c62382fabe179f0fca` |
| R10 command ledger | `agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/R10_COMMAND_AND_EXIT_LEDGER.json` | `a9f5d8f94e4f98055d313923e431c76e87d0c321` |
| R10 full-goal assessment | `agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/R10_FULL_GOAL_ASSESSMENT.json` | `c2b1ee5e096d1682067bf065a226333a0019d588` |

## Finding: doubled separators in PATH_PREFIXES

The current source declares:

```python
PATH_PREFIXES = ("E:\\\\BLACKBOX\\\\数据\\\\","E:\\\\BLACKBOX\\\\_OPS\\\\","E:\\\\BLACKBOX\\\\运行\\\\","E:\\\\BLACKBOX\\\\研究系统\\\\")
```

These are ordinary Python string literals. Each source-level `\\\\` sequence evaluates to two actual backslash characters. By contrast, a Windows path decoded from JSON such as `E:\\BLACKBOX\\运行\\BLACKBOX_RAW_COVERAGE_LEDGER_CURRENT.json` contains one separator at each boundary.

A direct literal-semantics check reproduced:

- prefix representation: `'E:\\\\BLACKBOX\\\\运行\\\\'`
- canonical decoded path: `'E:\\BLACKBOX\\运行\\BLACKBOX_RAW_COVERAGE_LEDGER_CURRENT.json'`
- `path.startswith(prefix)`: `False`

Consequently, for ordinary canonical paths in the captured JSON objects, this condition in `summarize_json` does not append entries to `registered_path_references`:

```python
if k in ("path","root","measured_root","source_path","ledger_path","manifest_path") and x.startswith(PATH_PREFIXES):
```

The raw JSON bytes are still captured and preserved; product IDs, release IDs, layer pointers and candidate-date literal hits are unaffected. The defect is confined to the generated path-reference summary. However, the task's success/exit calculation does not require any path references to be found, so a successful capture could silently produce an incomplete path summary.

## Test-coverage gap

The published test file has 12 test methods and does not test `registered_path_references` or the separator semantics of `PATH_PREFIXES`. The existing 12/12 result is reported as authored-source fixture testing only; this review did not rerun the package suite or claim native ZHANGWEI execution.

A corrected, separately versioned package should:
1. Encode the prefixes so their runtime values use one Windows path separator (without modifying captured source values).
2. Add fixtures containing JSON-decoded paths under at least `E:\\BLACKBOX\\运行\\` and `E:\\BLACKBOX\\数据\\`.
3. Assert the exact JSON pointer and original path value appear in `registered_path_references`.
4. Recompute the code, test and manifest byte counts/SHA256 from the final frozen bytes; update the new task pins from those exact bytes; independently read back every published file.

## Existing R1 package-pin mismatch remains separate

The prior exact-byte audit already established that all three current GitHub package SHA256 values differ from the R1 task pins, despite matching byte counts:

- capture code: actual `fabd15af5662343655f9723f599509311a11085d10e0b8c4ba8d29444f737dac`, task `f40b762e97cefee39d6746fcf2c6f4d380ff537b0089a87071ba0825f8bf049c`
- tests: actual `8e1907b354dca7e8fb52bcf8a48896e9ae79a376c9c6c0e445d063b742d178b3`, task `a205813cd4640dc02879eef2dffc6d65acd3d785d7ffe48bc8f8c74d2ad64cc4`
- PACKAGE: actual `699bd2f00439a62f8413688683b19774def816a1d68073d08056a327323b165b`, task `2c6fb962e3fae26bc1b44eb618b71d1c20ede4ebca8dfce258818adc5465142d`

The R1 task explicitly requires stopping at this mismatch before tests, preflight and capture. Preserve its literal native outcome if already started. Do not repair or replace it in flight.

## R10 foundation and continuation boundary

The R10 operating entry remains accepted only as bounded observation. R10 full foundation remains `BLOCKED_PARTIAL_EXECUTION` / `FOUNDATION_ACCEPTANCE=false`. The R10 command ledger records 24 offline controls, 41 catalog entities, 13 explicit updater joins, one 4/4-key bounded query, six non-executing update plans, and a guarded engine import that blocked `os.mkdir("./logs")`; no engine was constructed. R13 round 2 still records the R15-to-compiler chain-integrity gap, unproven adjustment-factor input/basis, incomplete tradeability/universe and virtual-view requirements, and no production admission.

R5 acquisition through 2026-10-27 remains closed; P3 remains a bounded value-preserving candidate. R4 remains independently pending and must not be stopped or duplicated. R6 remains unissued because registered calendar binding, current local layer reconciliation, supplier availability/lag, a new task-specific quota, and exact product-specific acquisition/Cleaning/align/PIT contracts remain unresolved.

## Disposition

- Preserve R1 and await its literal native ACK/status or package-pin failure receipt.
- Do not publish a replacement capture task until the R1 outcome is known.
- If a new capture is still required, include the PATH_PREFIXES correction and regression tests in a separately versioned package.
- No supplier call, local command, E: write, Parquet read, Cleaning, alignment, PIT transformation, CURRENT switch, release, backtest, money movement or order was performed.
- `ORDER_ALLOWED=false`; `CURRENT_SWITCH_ALLOWED=false`; `FORMAL_RELEASE_ALLOWED=false`.
