# R10 writer-guard delivery review and dirty-branch assembly repair

## Independently verified receipt
All 27 writer_guards manifest members were fetched and independently checked by exact byte count and SHA256: 27 match, zero mismatch. DELIVERY_MANIFEST.json is 4,976 bytes, SHA256 7ba03dda6c66acfa7156a8113defc601405205c70798a8d7f9d23a0e800a4a55. Separate FINAL_BYTE_READBACK.json reports completion. Four raw command captures match ledger hashes; the 13 controls and genuine CACHE preflight both have exit 0. The source bodies match the reviewed guard and original fixture identities.

All five original BASE64 carriers were independently decoded, length/SHA256 checked, and compared byte-exact to the additional originals/ files. They establish what the historical records say, not exact source-code execution:
- SOURCE_COVERAGE and CLEAN_ANTILEAK_QA describe 12,176,722 rows through 2026-08-14. They do not certify later dates.
- TASK_CLOSED binds the named R26 Cleaning generation to the August task and explicitly says ALL_BLACKBOX_DATA_GAPS_CLOSED=false and finish_gate=NOT_RUN_NO_BOOTSTRAP. Do not reopen this old closure or treat it as current full acceptance.
- AUTHORITY_GATES names the wrapper/engine and carries NH120_POPULATION_EXACT_SET_MATCH=false plus a residual RAW_NONE-vs-PRE class. Its READY booleans do not independently resolve that price-basis issue.
- INCREMENTAL_RECEIPT reports update_date 2026-09-02, seven dirty codes, seven full-history refreshes, FULL_HISTORY_REFRESHED_DIRTY_CODES, and successor BLACKBOX_CACHE_R1_ADJFACTOR_PIT_INCR_20260903_010456. Its seven-code list is now available byte-exact.

## More direct source defect
The pinned original writer's dirty branch (lines 242-246) fetches only dirty codes, keeps prior non-dirty history, and concatenates these two frames. It does not concatenate the already obtained live observations for non-dirty codes. On a new date, this can publish only the dirty codes even when live holds the other codes. A separate later date-presence shortcut can then prevent completion.

The new regression extracts and executes only the original three in-memory assignments from the SHA256-pinned AST. It never imports or invokes the original module, fetcher, auth or publisher. A two-security fixture shows the old branch emits one security on the new day despite having both in live.

assemble_candidate now retains validated non-dirty overlap and combines it with complete dirty-history replacements before applying the existing key/value guards. No filling or synthetic observation is introduced. Missing non-dirty source observations block the expected-key check. Source authority, factor basis, expected-key generation and publication remain separate unmet prerequisites.

20 review-host offline controls pass: the prior 13, four branch/assembly controls and three receipt-set controls. The fixed desktop reader compares only the pinned current 2026 partition's 2026-09-02 code set against the pinned original receipt's seven dirty codes. Equal sets would support consistency with this mechanism; it would not prove this exact source ran, explain every sparse day, or close B1.

## Chronology correction accepted only in limited scope
RETAINED_STAGING_LOG timestamps support files existing before the tests. They do not prove a pin checker executed then. CORRECTIONS_APPEND_ONLY mixes 2026-10-24T16:30:27Z with 2026-10-25T00:30:27Z; the latter is the Beijing wall-clock value mislabeled as UTC. The correct equivalence is 2026-10-24T16:30:27Z = 2026-10-25T00:30:27+08:00. Record FIRST_VERIFY_EXECUTION_TIME_NOT_RETAINED / ORDER_NOT_PROVEN for that first verification; no more lookup or rerun is needed for this reporting issue. The factor comparison's internal hash check remains valid within its own measured scope.

## Next provenance link
The original writer imports flatten_factor from one exact same-task source, download_source_fq_pre_r1.py. Retrieve that complete existing source by exact path for review, without importing/running it. This can identify the original full-history source directory, date semantics and request-output chain. Do not infer data absence from the P1 files or select another source from a filename. No scan or supplier call is authorized.

B1..B7 remain OPEN. No production patch, data merge, CURRENT change, historical refetch, new acquisition, formal engine admission or order is allowed in this package. The pure assembly is a tested candidate component, not an installed production repair.
