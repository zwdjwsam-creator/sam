# R5 Stage A — exact host-rule binding (no acquisition)

task_id: BLACKBOX_RAW_NONE_INCREMENT_20261027_R5_RULE_BINDING_A
requested_continuation: BLACKBOX_RAW_NONE_INCREMENT_20261027_R5_ISOLATE_RESUME
execution_host: ZHANGWEI
stage: A_ONLY
report_utc: see PREFLIGHT_RUN.json / CAPTURE_RUN.json
language: English (as required)

## Authorization actually held

| flag | value |
|---|---|
| SUPPLIER_CALLS_ALLOWED | false |
| ORDER_ALLOWED | false |
| CLEANING_ALLOWED | false |
| CURRENT_SWITCH_ALLOWED | false |
| B-gate | not entered |
| E: R5 staging output | not created |
| trading | not touched |

Stage A was executed strictly as a read-only rule-body handoff. No supplier, quota, auth or login call was made. No E: staging directory was created. No rule/control source was edited. No cleaning, no CURRENT switch, no order.

## Pre-run state check (no stop, no duplicate)

Before doing anything I checked for an existing Stage A ACK, result, or process. All were absent (HTTP 404 on ACK_R5_RULE_BINDING_A.json, PACKAGE_VERIFY.json, PREFLIGHT_RUN.json, CAPTURE_RUN.json, REPORT.md). `capture_001` did not exist and was not pre-created. `E:\BLACKBOX\STAGING\BLACKBOX_RAW_NONE_INCREMENT_20261027_R5` did not exist. Nothing was stopped and nothing was duplicated.

## Package staging and verification

The six package files were staged unchanged to
`C:\LAN_SHARE_REPORT\BLACKBOX_R5_RULE_BINDING_20261028\package`
and every staged file was read back locally.

Five payload identities against PACKAGE.json: 5/5 match on both byte length and SHA256, and every staged file equals the downloaded bytes.

| file | bytes | sha256 | verdict |
|---|---|---|---|
| capture_rules.py | 2471 | 1155922293075129b3e38455c6e84ebef0468c3ccc0763530551237be886c788 | MATCH |
| test_capture_rules.py | 1702 | 86d45876b227f662e7594bda8bb385592b0d55a700761ce6a1e1d6009387acdf | MATCH |
| OFFLINE_STDOUT.txt | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 | MATCH |
| OFFLINE_STDERR.txt | 627 | 4e6085e8c1038e63c07c7842baef79cc310a390ab043677bfc3c60772408a2aa | MATCH |
| TASK.md | 7212 | 9cc562e4a83e257e02f3c1e9b57789bbffe06a99e535f65b146ae2829cebefd9 | MATCH |

PACKAGE.json itself is the manifest, not a payload; it is delivered for completeness only. The git blobs of all six staged files equal the blobs in the review folder, so what was staged is byte-identical to what was reviewed.

## Source identity (preparatory read, not permission)

| source | expected | raw live on ZHANGWEI | verdict |
|---|---|---|---|
| `E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py` | 3bb85023387ce976aaf03694073936b0da5b5ef710f80f6284e8347f067fe217 | 3bb85023387ce976aaf03694073936b0da5b5ef710f80f6284e8347f067fe217 | MATCH |
| `E:\BLACKBOX\脚本\_base.py` | b8cc60746f92dc63049e8e6b6b6f39c6553dd98b69374b9f797d49b2654f2258 | b8cc60746f92dc63049e8e6b6b6f39c6553dd98b69374b9f797d49b2654f2258 | MATCH |

Decision: SOURCE_IDENTITY_MATCH, so the reviewed original preflight was allowed to run exactly once. No `SOURCE_IDENTITY_REVIEW_PENDING` was needed and no identity drift was observed.

## Six exact inputs (read/hash only, no directory search)

All six paths listed in `capture_rules.PATHS` exist on this host. No path was guessed and no directory traversal was authorised or performed.

| relative path | bytes | sha256 (first 16) | status |
|---|---|---|---|
| 契约/必读/BLACKBOX_ACQUISITION_MUST_READ.md | 2467 | 64ad956ee1dd44f0 | PRESENT |
| .cursor/rules/blackbox_jq_incremental_download_hand_rule.mdc | 2008 | 4de93c0737b52799 | PRESENT |
| 运行/BLACKBOX_JQ_INCREMENTAL_DOWNLOAD_RULE_CURRENT.json | 9100 | 2084f9683f1aa838 | PRESENT |
| 脚本/blackbox_must_read_preflight_r1.py | 11767 | 3bb85023387ce976 | PRESENT |
| 脚本/_base.py | 11800 | b8cc60746f92dc63 | PRESENT |
| 契约/必读/MUST_READ_MANIFEST_CURRENT.json | 2943 | 572309831371bd51 | PRESENT |

TASK.md states that three of the six are missing mandatory rule/control originals. That was true of the offline archive GPT inspected, not of this host: on ZHANGWEI all six are present. This is reported as measured, not as a dispute, and it does not widen the capture scope — only these six were touched.

No credentials were read, no HAND.txt was read globally, no unknown module was imported, and no sixth-slot directory was searched.

## Original preflight execution

Command, run exactly once, no retry, from `C:\LAN_SHARE_REPORT\BLACKBOX_R5_RULE_BINDING_20261028`:

```
& "E:\BLACKBOX\.venv\Scripts\python.exe" -X utf8 "E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py" --task-class ACQUISITION
```

No `--acceptance`, no `--write-manifest`, no repair flag. Separate raw stdout and stderr were captured plus the actual waited-for OS exit code.

Result: `MUST_READ_PRECHECK = PASS`, `TASK_CLASS = ACQUISITION`, `AUTHORITY_READY = YES`, `TASK_EXECUTION = ALLOWED`, `TASK_EXECUTION_FORBIDDEN = FALSE`, actual OS exit 0. KERNEL verified at `b05a69958e29f7c90cf1ea794a4c437d36120bb960515ce9e26d3f4d5bdf197a` (1167 bytes). BOOTSTRAP, DATA_ACCESS and ACQUISITION rule bodies all VERIFIED with expected equal to actual.

`HAND_READ = NOT_SUFFICIENT` is present in the output, and it was **not** treated as a failure. As the dispatch states, that line is emitted unconditionally after `ok` is computed; it means reading HAND alone is not sufficient authority, not that a manual-reading test failed. The preflight verdict is PASS with exit 0.

This run does not retroactively validate R4 and is not a substitute for the package tests. It is only the reviewed normal preflight path.

## Read-only body collector

Command, run exactly once, no retry, no extra argv:

```
& "E:\BLACKBOX\.venv\Scripts\python.exe" -X utf8 "C:\LAN_SHARE_REPORT\BLACKBOX_R5_RULE_BINDING_20261028\package\capture_rules.py"
```

`capture_001` did not pre-exist and was not pre-created. The collector created only `C:\LAN_SHARE_REPORT\BLACKBOX_R5_RULE_BINDING_20261028\capture_001`. stdout and stderr were both empty; actual OS exit 0.

`capture_001/RULE_BODIES.json`: 55850 bytes, sha256 `50379bcdf5b94c67aef6010de52b387074a62a4f76e250aee5fba54336ffe6f7`. Header fields: host ZHANGWEI, supplier_calls 0, source_written false, order_allowed false.

All 6 records are `CAPTURED` with zero `error_type`. For each record the base64 payload was decoded and compared twice: against the declared sha256, and against the live file on disk. Both comparisons passed 6/6, so the preserved bodies are byte-exact originals including line endings and BOM. Nothing was imported or evaluated from the captured sources.

Exit 0 here means exact-body handoff only. It is not a B-gate result and not supplier execution.

Raw streams, argv and the actual exit code are in `PREFLIGHT_RUN.json`, `CAPTURE_RUN.json`, `run_preflight/` and `run_capture/`.

## Unbound claims and open points (not resolved by Stage A)

- `SIX_SLOT_COUNT = UNBOUND_COUNT_CLAIM`. No sixth-slot directory path exists in any existing report, so the native "six slots" count is unsupported and is not asserted here. The original 5-slot policy is unchanged. The only six in this report is the collector's exact-input count.
- The four percentage pairs in the owner draft remain numerical candidate signatures only. No board rule, ST rule or suspension proof is claimed from them, and no coverage or legal-suspension conclusion is derived from them.
- ETF wording remains contradictory: the isolation range includes ETF while later text says any ETF old-gate failure stops. `ETF_WORDING = UNRESOLVED_BY_STAGE_A`, defaulting to the ETF hard stop. Stage A takes no position.
- The remaining 1784-set / old-batch bindings, the isolated 79+1 admission and the no-refetch plan are GPT's next code work. Native AI did not implement them.

## Quota and cost

supplier_calls = 0. quota_spent_by_stage_A = 0. No login, no auth, no quota-consuming call. The R4 cumulative figure 175858 is unchanged by this stage. The proposed 150000 new cap and cumulative 700000 permit no Stage A supplier use, and none was attempted.

## Incident: one misplaced upload, self-reported

My first upload attempt reused an existing helper whose return directory was hard-coded to `agents/chatgpt/inbox/BLACKBOX_UPDATE_PREREQUISITES_20261027/ZHANGWEI`. Combined with a prefixed relative name, one file (`capture_rules.py`, 2471 B) landed at the nested path
`.../BLACKBOX_UPDATE_PREREQUISITES_20261027/ZHANGWEI/agents/chatgpt/inbox/BLACKBOX_RAW_NONE_INCREMENT_20261027_R1/ZHANGWEI/r5_rule_binding_A/package/capture_rules.py`.
The readback then failed on the intended path, which exposed the mistake before any further file was written. The misplaced blob was deleted through the contents API (DELETE 200) and the nested tree re-checked as absent. A temporary probe file was also deleted and confirmed absent. All Stage A outputs were then written with an explicit full-path putter and byte-verified. No duplicated or conflicting artifact remains.

## Scope of this delivery

Delivered to `agents/chatgpt/inbox/BLACKBOX_RAW_NONE_INCREMENT_20261027_R1/ZHANGWEI/r5_rule_binding_A/`: ACK, package copy, package verification, preflight source identity and raw streams, collector argv and raw streams, `capture_001/RULE_BODIES.json`, this report, delivery manifest, local readback and upload readback.

Hold after upload. No B-gate, no R5 acquisition, no new login, no quota call, no source or package modification, no dependency installation, no cleanup, no terminal or watchdog action, no cleaning, no CURRENT switch, no trading.
