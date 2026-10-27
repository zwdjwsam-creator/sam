# HUB evidence review and bounded two-host follow-up — 2026-10-27 R1

dispatch_id: BLACKBOX_FORENSIC_READONLY_20261027_R1
parent_dispatch: BLACKBOX_UPDATE_PREREQUISITES_20261027
execution_baseline: ZHANGWEI
SAM_role: historical-source peer
status: HUB_PRECHECK_COMPLETE_BOUNDED_LOCAL_EVIDENCE_PENDING

FOUNDATION_ACCEPTANCE=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false

## Already checked in HUB — do not request repeated capture

1. The desktop owner baseline ACK **exists** at `agents/chatgpt/inbox/BLACKBOX_UPDATE_PREREQUISITES_20261027/ZHANGWEI/ACK_OWNER_BASELINE_20261027.json`, `acked_at_cn=2026-10-27T16:04:07+0800`, `status=OWNER_BASELINE_ACKED_CLOSURE_ALREADY_COMPLETED`. Its actual filename is noncanonical relative to the earlier requested `OWNER_BASELINE_ACK.json`, but this is a naming deviation, **not a missing acknowledgment**. Do not rename, re-upload, or rerun the closure.

2. Actual SAM source `source_closure_001/bodies/0001_run_unattended_catchup_r1.py` has default `target_end="2026-09-24"` and reads an overriding `TARGET_END.txt`. The actual `TARGET_END.txt` was `2026-09-24`. Thus **this driver** was configured not to iterate days after 2026-09-24; this does not prove no other acquisition workflow attempted those dates. A historical `FINAL_STATUS=PASS` tests aligned source/clean/cache date strings, not data completeness.

3. In currently captured source, the terminal branch is `ALL_CAUGHT_UP` -> `subprocess.run([..., run_blackbox_research_os.py, --mode, daily_incremental, --run, --date, ...])` -> `FINAL_STATUS.json` -> lock removal. This ordering supports a conditional historical invocation inference **if** the same source and branch executed and no external writer generated `FINAL_STATUS.json`. The returned code and resulting business state are **unproven**; `subprocess.run` is not `check=True`. The matching marker in original `UNATTENDED.log` is needed before treating the branch as historically observed. Neither FINAL_STATUS nor a lock-file absence independently proves a successful child process.

4. The prior retained `RELEASE_PROVENANCE_R33_R45.md` states the exact NAV implementation `now_ts() = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")`, generating R33 suffix `20260924_200439`. On that source basis this is an UTC build stamp, corresponding to 2026-09-25 04:04:39 China time; **not** the asof. The historical production-attribution and invocation proof must still be constrained to specific receipts and logs. This is stronger than a mere timezone guess but not independent proof of every actual historical execution byte.

5. The original `download_daily_r1.py` constructs filenames as `{domain}__incremental_gap_{GAP_START}_{GAP_END}__...__{ts_stamp()}.parquet` with `ts_stamp() = datetime.now().strftime(...)`. `20260924` in the suffix is the local build-time date, while the earlier tokens represent the requested range. Actual historical per-day files were produced from date-token-substituted templates, and the R10 `RAW_STATUS_FIELD_INVENTORY.json` explicitly records `batch_date=20260914` and actual `distinct_dates=["2026-09-14"]` for `stock_daily__incremental_gap_20260914_20260914__full__20260924_082242.parquet`. The existing watchdog filename filter `20260924` therefore matches builds on 09-24 across many data dates, NOT only 09-24 trading data. P4 hit an unordered 10,000-item cap out of 14,024 files: partial biased enumeration, no extrapolation or row-duplicate conclusion.

6. The retained `RELEASE_PROVENANCE_R33_R45.md` describes 26 `START FULL_CHAIN` lines for 09-24. Twenty-six starts do NOT alone prove 26 successful downloads or 26 independent orphan RAW outputs. The actual `run_unattended_catchup_r1.py` modifies `PARENT_ID` when the outer loop revisits an existing progressed day; it does not necessarily rewrite `PARENT_ID` on each inner `RETRY_DAY`. Require chronological marker evidence, not inference from a run count.

7. The desktop `D:\CURSOR_TASK_ARCHIVE\JQ_TIP_CATCHUP_UNATTENDED_R1` exact source folder was not found. The original SAM writer's configured `E:\BLACKBOX\...\P2/P3/P4` destination and desktop RAW filenames alone do not establish whether desktop bytes were copied, synchronized or independently generated. Existing R10 local RAW inventories identify bytes/file dates/writer code but do NOT, as yet, establish the specific cross-host transfer chain. Keep provenance `NOT_ESTABLISHED`, and do not rerun migration or search entire disks. A later stage may need only precise provenance receipts for selected files.

8. ZHANGWEI watchdog `AUTOHUB_LOCAL_WATCHDOG_ZHANGWEI` remains enabled/running with `proven_kind=null`; the task name suggests a HUB utility, not a proven identity. It MUST NOT be stopped based on name alone. One bounded task-definition read is authorized to determine its action target, with no action/control change.

9. SAM's old Cursor parent terminal was reported wedged. These tasks do not authorize terminal restart, process termination or Python-driver action. Existing V3 and source closures are complete in their bounded scopes; do not redo them.

## Scope reserved for GPT after returns

Offline-only exact code/contract review: define a per-product RAW_NONE gate for requested/returned `(date, code)` keys, code universe, time axis, fields, paging/exhaustion, nullable/paused semantics, and archive/provenance receipts. Preserve legal EMPTY for billboard where warranted by the original contract, not as a blanket daily-price exception. Isolated RCID/checkpoint/commit tests must close seven reproduced counterexamples before promotion. Use an independently pinned calendar covering later dates before defining any 2026-09-25+ acquisition range. No supplier login/call, CURRENT publication, business write or Stage2 launch follows from this review.

## Follow-up handoffs

- SAM: `agents/chatgpt/outbox/BLACKBOX_FORENSIC_READONLY_SAM_20261027_R1.md`
- ZHANGWEI: `agents/chatgpt/outbox/BLACKBOX_FORENSIC_READONLY_ZHANGWEI_20261027_R1.md`

This review closes only HUB precheck and task design; publication is not local ACK or execution.
