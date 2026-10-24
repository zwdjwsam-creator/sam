# R10 receipt — pinned offline pagination repair (static, offline only)

Task: `BLACKBOX_FOUNDATION_R10_PAGINATION_OFFLINE_REPAIR_20261025`
Execution host: ZHANGWEI. Workspace: `E:\BLACKBOX`. cwd for all commands: `E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024`
Environment names set: `PYTHONUTF8=1`, `PYTHONDONTWRITEBYTECODE=1`
`sanitized_for_share`: every path and hash in this file is a normal build artifact of the reviewed sources; no credential value and no secret-derived digest is present.

## 1. Stage exact bytes

`PACKAGE.json` was placed first, then the five members in the declared order:
`r10_pagination_candidate.py`, `test_r10_pagination_candidate.py`, `legacy_original.py`, `OFFLINE_RECEIPT.json`, `REVIEW.md`.

| Member | Declared bytes | Staged bytes | SHA256 match | Line endings |
|---|---|---|---|---|
| r10_pagination_candidate.py | 5,421 | 5,421 | yes | LF ×145 |
| test_r10_pagination_candidate.py | 4,325 | 4,325 | yes | LF ×79 |
| legacy_original.py | 7,786 | 7,786 | yes | **CRLF ×222 preserved** |
| OFFLINE_RECEIPT.json | 1,880 | 1,880 | yes | LF |
| REVIEW.md | 2,776 | 2,776 | yes | LF |

No re-pin, no newline conversion, no local source or test edit, no alternate harness.

## 2. Pinned CACHE preflight (before the test)

Pinned operating entry reused from the connected-factor delivery ledger: `reviews\R10\operating_entry\blackbox_operate_r10.py`, declared SHA256 `1b04bb3a373e2a4276563c62c2514905dde49910f69e519e8b3626090ef18ec9`, observed identical. No replacement was searched for.

```
.\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\operating_entry\blackbox_operate_r10.py describe --product ADJUST_FACTOR_PIT_R1
```

Exit 0. Raw streams in `CACHE_PREFLIGHT.stdout.txt` / `CACHE_PREFLIGHT.stderr.txt` (stderr empty, 0 bytes). Parsed: `ok=true`, `MUST_READ_PRECHECK=PASS`, `task_class=[CACHE]`, `problems=[]`, kernel and both must-read rules `VERIFIED`.

## 3. Pinned test — executed exactly once

```
.\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\pagination_offline_repair\test_r10_pagination_candidate.py
```

- Started `2026-10-25T06:00:54+0800` → finished `2026-10-25T06:00:54+0800`
- Exit `0`
- stdout `124` bytes, stderr `1582` bytes (raw in `TEST.stdout.txt` / `TEST.stderr.txt`)
- Parsed summary: `{"tests_run": 18, "passed": true, "scope": "OFFLINE_LIST_MODEL_ONLY", "supplier_calls": 0, "FOUNDATION_ACCEPTANCE": false}`
- stderr is normal unittest progress plus `OK`, not an empty stream

Against the reviewer's own `OFFLINE_RECEIPT.json`: same 18 test names in the same order, identical summary payload, identical exit 0. The only difference is the wall-clock figure in the `Ran N tests in X.XXXs` line. The reviewer capture is compared, never substituted for this host's raw streams.

## 4. What the 18 controls actually establish

The pinned pure AST of `legacy_original.py` reproduces the false PASS: two returned rows against a declared minimum of three with page size four yield `hard_gates_pass=True` while `REPLAY_IDENTICAL` stays `NOT_TESTED`. The isolated candidate:

- fails every below-minimum outcome, including empty input and a multi-page shortfall;
- blocks a single untested response;
- compares two independently supplied lists through `verify_replay`;
- rejects invalid page sizes and minimums, and missing or null keys, before looping;
- encodes composite keys as typed JSON arrays, so `a|b` + `c` differs from `a` + `b|c`, and `1` differs from `"1"`;
- retains the duplicate-key and full-last-page-without-authority blocks.

## 5. Measured limitations (unchanged by this run)

This is an in-memory sorted-list model, not a supplier pagination implementation. Equality proves equality only of the two supplied lists under the same spec. Not created or admitted: a trusted lower bound, real supplier exhaustion, deterministic server order, request identity, authoritative calendar or universe, checkpoint, supplier lag, factor basis, PIT, receipt persistence, finance adapter integration, a new production entry, or any publication. The legacy string-based order/content serialisation is retained; the candidate cannot certify arbitrary supplier types. The synthetic fixture specs are not business rules.

## 6. Three append-only reporting corrections (prior writer/cursor receipt)

1. **BOM** — the engine bytes carry **no UTF-8 BOM**; the earlier description was wrong. Bytes and SHA256 `978aedee181eac78…` are unchanged.
2. **Presence is not execution** — file presence was listed under an executed-historical-evidence key. Presence proves a file exists and nothing more; execution evidence would need a record tied to a specific invocation.
3. **`index=True`** — it preserves index metadata; it does **not** imply an ordinal or integer date. That causal sentence is withdrawn. The narrower observation stands: that writer requests neither `code` nor `time`, so both axes live only in the index.

Plus: missing scan artifacts (`CROSS_REFERENCE_HITS.json`, `ARTIFACT_PRESENCE_PROBE.json`) were not delivered, so citing them supports no claim and their absence supports no absence claim. Name scans and extra reads exceeded the prior handoff scope and are not repeated.

## 7. What this task does not do

No business write, merge, original overwrite or delete, re-migration, CURRENT switch, release publication, engine construction, money movement or order. No credential value read, no supplier probe, no quota use, no data download, no new inventory, no source search, no annual reconciliation, no duplicate suite. No absence or missing-range measurement. The P7 guards are untouched; the six-lane data-plane runner was not invoked even in status mode. The original module is not repaired or installed in production. Task publication is not an ACK; this receipt reports actual execution.

B1..B7 remain open.

FOUNDATION_ACCEPTANCE=false
FORMAL_ENGINE_ADMISSION=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false
SOURCE_ABSENCE_CLAIM_ALLOWED=false
