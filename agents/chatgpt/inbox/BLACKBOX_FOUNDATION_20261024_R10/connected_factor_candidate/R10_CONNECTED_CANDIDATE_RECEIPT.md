# R10 continuation — validated responses connected to history-preserving candidate assembly

Executor: ZHANGWEI. Round: `BLACKBOX_FOUNDATION_R10_CONNECTED_FACTOR_CANDIDATE_20261025` (R10 continuation).
Instruction: `outbox/BLACKBOX_FOUNDATION_R10_CONNECTED_FACTOR_CANDIDATE_20261025.md`.
Window: 2026-10-25 02:27:30 – 02:31 +08:00. Host ZHANGWEI, cwd `E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024`,
`PYTHONUTF8=1`, `PYTHONDONTWRITEBYTECODE=1`, interpreter `runtime/.venv/Scripts/python.exe`.

Append-only. Nothing from the accepted `factor_response_gate` delivery was rerun or re-uploaded: the standalone
20-control suite, the earlier AST tests, the source searches, the parquet/schema checks, the annual comparisons and
the catalog inventory were all left alone.

FOUNDATION_ACCEPTANCE=false · FORMAL_ENGINE_ADMISSION=false · NEW_DATA_ACQUISITION_AUTHORIZED=false ·
CURRENT_SWITCH_ALLOWED=false · ORDER_ALLOWED=false · SOURCE_ABSENCE_CLAIM_ALLOWED=false · B1..B7 OPEN.

---

## 1. Staged and pinned before execution

`PIPELINE_PACKAGE.json` staged first (1,232 B, sha256 `52c616a0670b21b1…`), then every pinned member. All declared
byte counts and sha256 match the staged bytes:

| member | bytes | sha256 | note |
| --- | --- | --- | --- |
| `r10_factor_candidate_pipeline.py` | 2,711 | `bef2208a5c87decf…` | new: the connected path |
| `test_r10_factor_candidate_pipeline.py` | 5,058 | `da9e0c85d6ffd8c2…` | new: the 11 connected controls |
| `r10_factor_response_gate.py` | 3,878 | `bfe4b45f9d1d056a…` | **reused**, identical to prior-round copy |
| `r10_factor_input_contract.py` | 4,046 | `e30acaddecf03e0a…` | **reused**, identical to prior-round copy |
| `r10_factor_refresh_assembly.py` | 1,026 | `c816843ba597f2b4…` | new to this round |
| `r10_factor_candidate_merge.py` | 2,656 | `f375f523d8578110…` | new to this round |
| `PIPELINE_OFFLINE_RECEIPT.json` | 340 | `2b2d1a9ba708f9a0…` | GPT's own offline receipt |

The two reused modules were compared against **both** the new manifest and the already-staged prior-round files and
are byte-identical in both directions, so this round consumed the accepted validator rather than a local substitute.
No re-pin, no BOM or line-ending conversion, no test edit, no alternate harness.

## 2. Genuine pinned preflight

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\operating_entry\blackbox_operate_r10.py describe --product ADJUST_FACTOR_PIT_R1
    exit 0   02:27:30.6040703 -> 02:27:31.6223449 +08:00   stdout 6,632 B   stderr 0 B

    real_preflight.ok = true · MUST_READ_PRECHECK = PASS · task_class = [CACHE] · problems = []
    BOOTSTRAP / DATA_ACCESS = VERIFIED (expected == actual)
    KERNEL_SHA256 = b05a69958e29f7c90cf1ea794a4c437d36120bb960515ce9e26d3f4d5bdf197a
    TASK_EXECUTION = ALLOWED · TASK_EXECUTION_FORBIDDEN = FALSE

Read-only describe. No acquisition, no CURRENT switch. Dependent work proceeded.

## 3. The one authorized connected check

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\connected_factor_candidate\test_r10_factor_candidate_pipeline.py
    exit 0   02:27:35.2015700 -> 02:27:36.2183978 +08:00   stdout 141 B   stderr 115 B

stdout, verbatim:

    {"tests_run": 11, "passed": true, "scope": "CONNECTED_CANDIDATE_GATES_SYNTHETIC_ONLY", "supplier_calls": 0, "FOUNDATION_ACCEPTANCE": false}

stderr, verbatim:

    ...........
    ----------------------------------------------------------------------
    Ran 11 tests in 0.090s

    OK

Expected 11 / passed / exit 0; observed 11 / true / exit 0. Executed once, not rerun for capture, no warning. The
previous standalone 20-control suite was not re-executed.

## 4. What the chain actually connects

`candidate_pipeline` calls, in this order:

1. `r10_factor_response_gate.assemble_responses(plan, replies, required_fq=…)` — the accepted gate;
2. overlap/date boundary: `flatten_factor(prior_overlap)` and `require(history.date.lt(asof).all())`, so a prior
   overlap at or after the requested day is `OVERLAP_MUST_PRECEDE_REQUEST_DAY`; duplicate-day precedence is not
   guessed anywhere;
3. dirty-code refresh validation on the requested day: dirty codes must be inside the day's reply
   (`DIRTY_CODE_OUTSIDE_REQUEST_DAY`), the refresh code set must equal the dirty set
   (`REFRESH_CODE_SET_NOT_DIRTY_SET`), nothing may exceed the as-of (`REFRESH_AFTER_ASOF`), and an outer
   `validate='one_to_one'` join requires `both` (`DIRTY_REQUEST_DAY_KEYS_CONFLICT`) with equal values
   (`DIRTY_REQUEST_DAY_VALUES_CONFLICT`);
4. `r10_factor_refresh_assembly.assemble_candidate`, which drops non-dirty observed rows, appends the revised full
   histories and calls `r10_factor_candidate_merge.candidate_merge`;
5. return the candidate with five stage names and every authority flag false.

`candidate_merge` itself keeps the parent intact: expected keys must be explicitly supplied (`EXPLICIT_EXPECTED_KEYS_REQUIRED`),
nothing after as-of is allowed, `DIRTY_CODES_OUTSIDE_PARENT` and `REVISION_END_BEFORE_PARENT_TIP` are enforced, a
replacement may never drop older keys (`DIRTY_HISTORY_KEY_REGRESSION`), a value conflict outside the dirty set is
`VALUE_CONFLICT_REQUIRES_REVISION_CONTRACT`, and the result must retain every parent key
(`PARENT_KEY_REGRESSION`) and serve every expected key (`REQUEST_KEYS_NOT_SERVED`).

Stage names returned, in fixed order:

    REQUEST_RESPONSES_VALIDATED
    OVERLAP_BOUNDARY_VALIDATED
    DIRTY_DAY_BOUNDARY_VALIDATED
    HISTORY_PRESERVING_MERGE_PASSED
    PUBLICATION_NOT_AUTHORIZED

The last stage is an intentional no-publication boundary. There is no publisher API in this component, so it
neither executes nor certifies the production publish gate.

## 5. Installation evidence — append-only guide section

Guide: `reviews/R10/operating_entry/BLACKBOX_LOCAL_OPERATIONS_R10.md`

    before   5,333 B   sha256 685e3b2097007cbd7981af504c8652be8842741c1bd62af86edd4482164b7c3c
    after    6,765 B   sha256 a5a189e9b3489c6a…
    appended +1,432 B  append_only=true (the after bytes start with the entire before bytes)

The appended section records the exact 11-check command, the actual `response_gate -> refresh_assembly ->
candidate_merge` chain, the five stage names, the sentence "Synthetic diagnostic only; no real-data authority,
publication or formal engine admission", and the unchanged global acquisition prohibition. Prior bytes are saved at
`GUIDE/BLACKBOX_LOCAL_OPERATIONS_R10.before.md`; the unified diff is `GUIDE/GUIDE_APPEND_DIFF.patch`.

Not patched: the pinned `blackbox_operate_r10.py` (entry pin still `1b04bb3a373e2a42…` after the append), normative
contracts, root must-read files, live updater, historical originals.

## 6. Measured scope, stated separately

| object | status this round |
| --- | --- |
| standalone source response gate | **prior 20-control result reused**, not re-executed |
| connected response/refresh/merge candidate | **actual new 11-control result**, calling the real staged modules including the real `candidate_merge` |
| production writer | not exercised, not patched |
| real-data source authority | not established |
| expected market universe | not established |
| production publish gate | not executed, not certified |
| formal engine | not admitted |

A synthetic in-memory pass is neither a repaired real-data source nor an admitted engine. No malformed RAW file was
supplied, no request binding was manufactured for one, no date was derived from a filename, no `fq=pre` was asserted
for a `None` request and no factor was filled.

B1..B7 keep their existing unresolved status; no inventory was rerun and no wholesale closure is declared.

## 7. Delivery contents

    SUPPLIED_SOURCES/    the eight supplied files at original bytes (incl. PIPELINE_PACKAGE.json)
    captures/            PREFLIGHT.stdout/stderr, TEST.stdout/stderr
    STAGE_AND_PIN_CHECK.json   manifest-first staging, per-member pins, reused-module identity, guide before-state
    EXECUTION_RECORD.json      both commands, windows, capture hashes, preflight block, verbatim stdout/stderr
    BODY_PROVENANCE.json       original path / bytes / sha256 / byte-identity, BOM and CRLF counts
    GUIDE_INSTALL_RECORD.json  before/after bytes and hashes, append flag, unified diff
    GUIDE/                     before copy, after copy, diff patch
    NOTES_APPEND_ONLY.json     N1..N8
    B1_B7_CARRY_FORWARD.json   unchanged carry-forward, no closure
    COMMAND_LEDGER.json        every step, exit and outcome
    DELIVERY_MANIFEST.json     every member except itself and the readback
    FINAL_BYTE_READBACK.json   separate readback written after the upload, then itself uploaded

No business-data write, no historical source repair, no supplier call, no download or refetch, no production patch,
no CURRENT change, no engine construction and no order.
