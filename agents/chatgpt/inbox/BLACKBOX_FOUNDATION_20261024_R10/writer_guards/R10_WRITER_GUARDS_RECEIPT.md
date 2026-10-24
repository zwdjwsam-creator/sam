# R10 continuation receipt — offline writer guards and the five exact retained receipts

Append-only executor receipt. New file this round; no earlier report is amended.
Round: `R10_WRITER_GUARDS_AND_EXACT_RECEIPTS_20261025`. This continues R10. It is not R11 and not acceptance.
Executor: ZHANGWEI (local desktop, Cursor agent).

---

## 1. Reuse of the completed prior delivery

The 26 members of `factor_basis/DELIVERY_MANIFEST.json` were already byte/hash verified by the reviewer.
`FINAL_BYTE_READBACK.json` arrived during review as blob `2d0260ace3c3eedaa84973777128d799954f4367` and is
reused as the completed finisher. No second finisher was started, no measurement was repeated, and the original
ledger, receipt and manifest of that round are untouched.

## 2. Pre-execution pin verification, with the actual clock

Stage dir: `reviews/R10/writer_guards/`. The 5 `PACKAGE.json` members were staged byte-exact and the fixture was
fetched from the published HUB body, decoded and hash-checked:

    r10_factor_candidate_merge.py              2,656 B  f375f523d857811019008e2c7b89f360f43b156ec41c4b74059bbd2c9b7d2fd5  OK
    test_r10_factor_writer_regressions.py      4,889 B  862433eba05f3e51a30194b7df42d0b5602ce357fadf5cf0648249b27585e84c  OK
    r10_factor_input_contract.py               4,046 B  e30acaddecf03e0abd4360f60a74bae53525373e55feb51cf76d409beebe67c5  OK
    REVIEW.md                                  5,619 B  797e742fe7268e96d50b74a5bc47ea141dd1c1c2bdd4d7c0a97e417ec337d1bc  OK
    OFFLINE_TEST_RECEIPT.json                    231 B  83e5acaff7e208c0a7a56566d2da4eede01469d71fbc6a4dfb58df5a1c23b410  OK
    source_incremental_backward_refresh_r1.py 11,537 B  1df97ec81882243716cece03afb786638a05028642f97309cf71a3bcea3456f0  OK

The fixture came from
`agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1507/source_reads/incremental_backward_refresh_r1.py`
and is byte-identical to the local original on disk. Check ran **00:58:12 to 00:58:13 +08**, i.e. before the
controls, recorded in `PRE_EXECUTION_PIN_CHECK.json` with real timestamps. No line-ending normalisation, no source
change, no pin regeneration, no substitute test.

## 3. Supplied offline controls

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\writer_guards\test_r10_factor_writer_regressions.py

Literal stdout: `{"tests_run": 13, "passed": true, "scope": "PINNED_AST_AND_OFFLINE_MERGE_ONLY", "supplier_calls": 0, "FOUNDATION_ACCEPTANCE": false}`
Literal stderr: `Ran 13 tests in 0.068s` / `OK`. Exit 0, 00:58:18 to 00:58:19. **13 of 13 pass.**

The run imports only the pure input and merge guards and parses one hash-verified AST. It does not import or
execute the original writer, the wrapper, auth, the publisher or any supplier SDK. The guards were not applied to
business data and no production function was replaced.

## 4. Genuine read-only preflight

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\operating_entry\blackbox_operate_r10.py describe --product ADJUST_FACTOR_PIT_R1

Exit 0, 00:58:24 to 00:58:25, 6,632 B stdout, empty stderr. `real_preflight.ok = true`,
`MUST_READ_PRECHECK = PASS`, `task_class = CACHE`, `BOOTSTRAP` and `DATA_ACCESS` both `VERIFIED`, `problems = []`,
`AUTHORITY_READY = YES`. Catalog `ACTIVE`, 13 parquet files, 12,266,026 rows, 2014-01-02..2026-09-24, 3097 of 3097
expected sessions, `missing_session_count 0`. `use_for_formal_backtest = false`,
`source_absence_claim_allowed = false`. No substituted preflight.

## 5. The five exact receipt originals

Read only these five paths in
`E:\BLACKBOX\任务\BLACKBOX_ADJUST_FACTOR_PIT_R1_FULL_REBUILD_AND_BACKWARD_REFRESH_R1\`:

| file | bytes | sha256 | pin |
|---|---|---|---|
| `INCREMENTAL_RECEIPT.json` | 1,074 | `bbbec46fb07034506bdc74761e6e7d6de95edfb771d9b80314ff8eaa6f8b71ed` | MATCH |
| `AUTHORITY_GATES.json` | 1,148 | `e820afdd5ca726c27047a45c18958c56380a76e47f3212c715f1893ae6bbe360` | MATCH |
| `SOURCE_COVERAGE.json` | 714 | `dbe8df6287e8b24f705799c3e8c295bc9dc69d1462fc79d9345994b7b3a9c59a` | MATCH |
| `CLEAN_ANTILEAK_QA.json` | 735 | `5da57e4a5806017ae41264a916100c5ce4c57b0220bfe16dd25daf68d12f5679` | MATCH |
| `TASK_CLOSED.json` | 1,075 | `49286df9a8d6e74ba824efb18d635629d472f8b82f9d55822320e0919e0ba257` | MATCH |

No path differed, no alternate root was used, no re-pin. No directory enumeration of data roots and no drive
search was performed.

A single HUB repository tree listing (2,994 entries, `truncated = false`) was consulted only to test whether a
complete body of the same name is already published for byte-identical reuse. **None exists**, so all five are
returned as complete `BASE64_ORIGINAL_BYTES` carriers under `original_bodies/`, each containing the original
absolute path, byte count, SHA256 and the full body. Every carrier was decoded back and byte-compared at write
time (`CARRIER_RECEIPT.json`, `all_roundtrip_verified = true`). No credential value is embedded in any of them.

Boundary kept: a receipt sitting beside the program is a same-folder self-report. It does **not** establish exact
executed code identity, and `AUTHORITY_READY = true` inside it is **not** treated as proof that this program
produced the mounted release.

## 6. Append-only corrections

`CORRECTIONS_APPEND_ONLY.json`, five entries, originals left in place.

**C1 — package-verification chronology.** The prior ledger `seq 1` is timestamped 00:45:43 to 00:45:44, which
postdates the 12-control run at 00:30:27 and the comparison start at 00:30:51. Resolved from already retained
local artifacts only, in `RETAINED_STAGING_LOG.json`:

    download dir written           2026-10-24T16:27:58Z .. 16:28:11Z   (00:27:58 .. 00:28:11 +08)
    staged copies created          2026-10-24T16:30:05Z               (00:30:05 +08)
    verify tool written            2026-10-24T16:30:01Z               (00:30:01 +08)
    12-control capture started     2026-10-25T00:30:27Z               (00:30:27 +08)
    desktop capture started        2026-10-25T00:30:51Z               (00:30:51 +08)

The staged copies therefore existed 22 s before the controls began, and the verify tool 26 s before. So
`ORDER_STATUS = PRE_TEST_ORDERING_PROVEN_FOR_STAGING`. What the 00:45:43 entry actually is: a **second execution**
of the same `tools/verify_factor_basis_pins.py`, run only to redirect stdout into `PACKAGE_PIN_VERIFY.stdout.bin`
for delivery, producing the identical `ALL_PINS_MATCH` result. The first execution was not captured to a file, so
`FIRST_VERIFY_EXECUTION_TIME_NOT_RETAINED`. No timestamp is invented, the ledger is not reordered, and no
measurement is rerun to manufacture one. Noted for completeness: the comparison driver itself re-verifies package
hashes before its real preflight, so that output is self-protected independently of the chronology.

**C2** — the five bodies missing from `ORIGINAL_WRITER_CANDIDATE.json` are now shipped complete; the
self-report boundary above is restated.
**C3** — the prior writer lookup was bounded to two literals in `.py`/`.ps1` files up to 2 MiB in three roots.
No claim is made about other languages, other roots, larger files, or writers of `tip_extended_at`, `tip_source`
and `n_rows_year_2026`. `SOURCE_ABSENCE_CLAIM_ALLOWED` stays false.
**C4** — the 723 B wrapper dispatches the task script through `guarded_run`, so it can transitively cause supplier
calls and writes and is **not** read-only to invoke. Neither wrapper nor original writer was imported, executed or
selftested; a selftest is forbidden because the source authenticates before branching.
**C5** — the finisher arrived during review and is reused, not restarted.

## 7. Status

    B1_ADJUSTMENT_RECONCILIATION             OPEN
    B2..B7                                   OPEN
    production_integration                   NOT_AUTHORIZED
    FULL_GOAL_MET                            false
    FOUNDATION_ACCEPTANCE                    false
    FORMAL_ENGINE_ADMISSION                  false
    NEW_DATA_ACQUISITION_AUTHORIZED          false
    CURRENT_SWITCH_ALLOWED                   false
    ORDER_ALLOWED                            false

No production patch, business-data merge, historical refresh, login, supplier call, data download, CURRENT
change, engine construction or order occurred in this round. The source-level failure mechanisms reported by the
reviewer (date-presence-only `have_ud`, unguarded parent-row removal, publication inside `publish_successor`) are
failure mechanisms, not proof that they caused the observed 2026 pattern.

GPT will review the exact originals and decide production wiring.
