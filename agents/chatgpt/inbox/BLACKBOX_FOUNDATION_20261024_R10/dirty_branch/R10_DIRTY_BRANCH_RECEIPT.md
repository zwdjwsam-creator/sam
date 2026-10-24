# R10 continuation receipt — dirty-branch content check and the original source generator

Append-only executor receipt. New file this round; no earlier report is amended.
Round: `R10_DIRTY_BRANCH_AND_SOURCE_GENERATOR_20261025`. Still R10, not acceptance.
Executor: ZHANGWEI (local desktop, Cursor agent).

---

## 1. Reuse of the completed prior delivery

The 27 `writer_guards` manifest members were already independently verified by the reviewer and its finisher is
reused. Nothing from that round was repeated: no writer-guard controls, no 13-year comparison, no prior source
lookup, no catalog query, no re-export of the five originals.

## 2. Staging and pre-execution pins

Stage dir: `reviews/R10/dirty_branch/`. All 10 `PACKAGE.json` members and the reused fixture were checked by
exact byte count **and** SHA256 at **01:09:18–01:09:19 +08**, before any control or preflight:

    r10_factor_refresh_assembly.py            1,026 B  c816843ba597f2b4f30a61c21c648b78efa5cd0351dff4df08b360e684ac7b5f  OK
    test_r10_factor_refresh_assembly.py       3,538 B  4c6a5a0da8065c23f175fcaa8f968dd6b0696da298b5dc49681f33bf796a10b3  OK
    r10_factor_dirty_receipt_check.py         4,840 B  e8491aa04f9e3bda4f7202eb2683056e32d97c879d5bcde90fd59929e2f8ed54  OK
    test_r10_factor_dirty_receipt_check.py    1,890 B  5df48ab92ce4763b83a05968fcc362ccfb57bf86d6bbe2c9f61eca74a60de5ed  OK
    r10_factor_candidate_merge.py             2,656 B  f375f523d857811019008e2c7b89f360f43b156ec41c4b74059bbd2c9b7d2fd5  OK
    r10_factor_input_contract.py              4,046 B  e30acaddecf03e0abd4360f60a74bae53525373e55feb51cf76d409beebe67c5  OK
    r10_factor_desktop_check.py               7,495 B  76693d0834086e22b2afa62c70c4973b8271e14242ccae5c7f2a3f269d3cfed0  OK
    test_r10_factor_writer_regressions.py     4,889 B  862433eba05f3e51a30194b7df42d0b5602ce357fadf5cf0648249b27585e84c  OK
    REVIEW.md                                 4,503 B  9f60dc0f06425b518e9b0761610bb54522c6ce7003475acb1b77fb6b30073f85  OK
    OFFLINE_TEST_RECEIPT.json                   224 B  d8d6b8b0851be552d4d986fe2e3c30fc1647df52a9b50561e977d5d5de00f25f  OK
    source_incremental_backward_refresh_r1.py 11,537 B  1df97ec81882243716cece03afb786638a05028642f97309cf71a3bcea3456f0  OK

The fixture was copied from the prior verified `writer_guards` stage and is byte-identical to it. No source edit,
no newline conversion, no re-pinning, no substitute harness.

## 3. Supplied controls

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\dirty_branch\test_r10_factor_dirty_receipt_check.py

Literal stdout: `{"tests_run": 20, "passed": true, "scope": "PINNED_AST_ASSEMBLY_AND_RECEIPT_SET_OFFLINE_ONLY", "supplier_calls": 0, "FOUNDATION_ACCEPTANCE": false}`
Literal stderr: `Ran 20 tests in 0.097s` / `OK`. Exit 0, 01:09:25–01:09:26. **20 of 20 pass**, including the prior
13 as regression coverage for the changed assembly. The original writer was not invoked.

## 4. Fixed dirty-receipt measurement — both attempts disclosed

**Attempt 1, exit 3, `STOP_STAGING_INCOMPLETE`** (01:09:32–01:09:33):
`{"status": "STOP", "reason": "FileNotFoundError", ...}`. The driver reads `PACKAGE.json` from its own directory
before anything else. My staging step had copied only the manifest *members*, so the supplied `PACKAGE.json` was
missing and the driver raised at that read. **No pinned input was opened, the preflight did not run, and no
measurement was produced.** Raw stdout/stderr are retained unchanged.

**Staging gap corrected**: the supplied `PACKAGE.json` was copied into the stage dir, 1,966 B,
`ba5711e74efdecb06df9c63c981e3520e4584f2f5ec660a6814a233fb50ab7b7`, byte-identical to the published copy. No
member, fixture or driver file was edited, re-pinned or replaced.

**Attempt 2, exit 0, `PINNED_DIRTY_RECEIPT_CONTENT_MEASURED`** (01:10:56–01:10:59) — the single fixed measurement:

- Internal package verification passed; original operating-entry hash `1b04bb3a...18ec9` verified.
- Genuine CACHE preflight PASS: `ok=true`, `MUST_READ_PRECHECK=PASS`, `task_class=CACHE`, `problems=[]`.
- The side-effect audit hook was installed before any data read; both pinned inputs were re-verified after reading;
  `source_files_changed=false`, `supplier_calls=0`.

Result, exactly as measured:

    receipt_date                      2026-09-02
    receipt_release                   BLACKBOX_CACHE_R1_ADJFACTOR_PIT_INCR_20260903_010456
    observed_codes_on_receipt_date    002891.XSHE 002895.XSHE 300773.XSHE 300888.XSHE
                                      301029.XSHE 301563.XSHE 688578.XSHG
    receipt_dirty_codes               002891.XSHE 002895.XSHE 300773.XSHE 300888.XSHE
                                      301029.XSHE 301563.XSHE 688578.XSHG
    sets_equal                        true
    observed_not_reported             []
    reported_not_observed             []
    observed rows on that date        7, all factor 1.0

So on 2026-09-02 the mounted 2026 partition holds **only** those seven codes, one row each, all at factor 1.0 —
exactly the seven the receipt reports as dirty-refreshed. That is content consistency with the reported dirty
branch, and it is consistent with the reviewer's finding that the branch can publish only the dirty codes on a new
date. It is **not** exact code-execution proof, not producer identity, and not a completeness certificate.

## 5. The one original source generator

Read only this exact path, without import, execution, CLI, help, auth, fetch, or following any path found inside it:

    E:\BLACKBOX\任务\BLACKBOX_ADJUST_FACTOR_PIT_R1_FULL_REBUILD_AND_BACKWARD_REFRESH_R1\download_source_fq_pre_r1.py
    7,131 B   sha256 8a49616147748b46d168542973020aed86cb1e70d09a09a45960cb641201bcea

This is newly measured identity, **not** a prior authority pin. A credential scan of the body returned 0 matches,
so the complete body is delivered as a `BASE64_ORIGINAL_BYTES` carrier with round-trip verification
(`original_bodies/download_source_fq_pre_r1.py.BASE64_ORIGINAL_BYTES.json`). A single HUB tree listing (3,041
entries, not truncated) shows no previously uploaded body of this name, so there is no reuse link.

Structure observed, for the reviewer's next step: module-level imports `json os sys time datetime pathlib numpy
pandas` plus `jq_download_base.auth` and `jq_download_base.quota_left`; definitions `now_cn`, `log`, `wjson`,
`flatten_factor`, `load_universe`, `year_end`, `main`. The original writer imports `flatten_factor` from this exact
file, which is why it is the right provenance link. Nothing beyond what the body itself declares is asserted here,
and its presence says nothing about the P1 files or about data absence. If this path had been absent, the report
would have been only "this exact path absent", not data or source missing.

## 6. Append-only reporting correction

`CORRECTIONS_APPEND_ONLY.json`, entry `C6_CHRONOLOGY_LABEL_AND_EXECUTION_ORDER`; the earlier C1 is left in place,
unedited.

- Label defect: C1 wrote `2026-10-25T00:30:27Z` and `2026-10-25T00:30:51Z` as if UTC. Those are +08:00 readings.
  Correct equivalence: `2026-10-24T16:30:27Z = 2026-10-25T00:30:27+08:00`, and likewise
  `2026-10-24T16:30:51Z = 2026-10-25T00:30:51+08:00`. The instants are unchanged; only the zone labels were wrong.
  The other C1 values (downloads 16:27:58Z–16:28:11Z, verify tool 16:30:01Z, staged copies 16:30:05Z) were
  already correct UTC.
- Scope defect: retained file times support that the staged files existed before the tests ran. They do not show
  that a pin checker executed at any moment. Therefore `ORDER_STATUS = ORDER_NOT_PROVEN` and
  `FIRST_VERIFY_EXECUTION_TIME = NOT_RETAINED` for that first verification.
- No further chronology lookup, no re-execution and no fabricated timestamp. The factor comparison's internal
  hash re-check remains valid within its own measured scope regardless of this reporting issue.

## 7. Status

    B1..B7                                    OPEN
    production_integration                    NOT_AUTHORIZED  (the pure assembly is a tested candidate component)
    FULL_GOAL_MET                             false
    FOUNDATION_ACCEPTANCE                     false
    FORMAL_ENGINE_ADMISSION                   false
    NEW_DATA_ACQUISITION_AUTHORIZED           false
    CURRENT_SWITCH_ALLOWED                    false
    ORDER_ALLOWED                             false
    SOURCE_ABSENCE_CLAIM_ALLOWED              false

No production patch, business-data write or missing-date filling, historical refresh, original-source selftest,
wrapper invocation, login, supplier call, data download, CURRENT promotion, engine construction or order occurred.
GPT decides the next actual source, cleaning and publishing integration after reviewing the new body.
