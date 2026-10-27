# ZHANGWEI prerequisites child task — execution report

task_id: BLACKBOX_UPDATE_PREREQUISITES_ZHANGWEI_20261027
parent_task_id: BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025
dispatch_id: BLACKBOX_UPDATE_PREREQUISITES_20261027
execution_host: ZHANGWEI
hostname: ZHANGWEI
interpreter: E:\BLACKBOX\.venv\Scripts\python.exe (3.12.10)
reported_at_cn: 2026-10-27T12:26:00+08:00
status: STOPPED_AT_FIXTURE_CONTROLS_COLLECTOR_NOT_RUN
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false
FOUNDATION_ACCEPTANCE=false

## 1. What was actually done

| step | result |
|---|---|
| ACK.json uploaded before execution, read back byte-identical | DONE |
| Reviewed package staged to `C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027\package` | DONE |
| Every payload byte length and SHA256 checked against PACKAGE.json | 9/9 MATCH |
| 17 fixture controls executed once | 15 PASS, 2 ERROR, actual exit 1 |
| Collector executed | NOT RUN — the task says a failed test stops collection |
| Tests or code modified | NO |
| Retry | NO |
| Elevation attempted | NO |

Actual literal process exit for the control run was `1`. That exit is the real
`subprocess` return code, retained in `COMMAND_LEDGER.json`; it was not derived from any
later JSON artifact.

## 2. Why the controls stopped, and why it is not a code defect

The two errors are raised while **building the disposable fixture**, not while asserting
behaviour. Both call sites attempt `os.symlink`:

- `test_cycle_link_not_followed_and_disclosed`, `test_collect_prerequisites.py:63`
  `(t/"loop").symlink_to(t, target_is_directory=True)`
- `test_external_link_blocked`, `test_collect_prerequisites.py:47`
  `(self.root/"x.py").symlink_to(outside)`

Both fail with `OSError: [WinError 1314] 客户端没有所需的特权`
("a required privilege is not held by the client").

Measured on this host (`ENV_PRIVILEGE_PROBE.json`):

- the process is **not elevated** (`IsElevated = False`, identity `ZHANGWEI\Admin`)
- the `AppModelUnlock` key is **absent**, i.e. Developer Mode is off, so symlink creation
  needs elevation
- symbolic-link evaluation policy is **local-to-local ENABLED**, so the filesystem is not
  the obstacle
- a live attempt confirms the split: **symbolic link FAIL**, **directory junction OK**

So the blocker is a host privilege condition. It is not evidence that the delivered
collector is wrong, and it is not a test-logic defect: the failing statement is fixture
setup. In this pass the collector was never executed at all, so its real-host behaviour
remains unmeasured.

Because the package is reviewed and closed, this host did **not** rewrite the fixtures,
did **not** substitute junctions for symlinks on its own initiative, and did **not**
re-run anything. Any fixture variant using junctions would require a newly reviewed
package authored by GPT.

### Exact unblock options (none executed here)

1. Run the same unmodified package under a context that holds
   `SeCreateSymbolicLinkPrivilege`.
2. Enable Developer Mode on this host, then re-run the same unmodified package.
3. Have GPT issue a reviewed fixture variant that builds fixtures with directory
   junctions instead of symbolic links. Junctions succeed here; this host will not
   author that change unilaterally.

## 3. What is therefore NOT claimed

- The collector was **not** run. `capture_001/` was never created; `COLLECTION.json`,
  `LOCAL_READBACK.json` and a collector-produced `DELIVERY_MANIFEST.json` do not exist.
- No new/changed body was copied to `bodies/`. Copying them is collection, which the
  stop condition forbids. The 15 bodies that differ from the pinned HUB set are
  **identified and hashed** in `EXECUTION_BINDINGS.json` but their bytes are **not
  uploaded** by this task.
- Nothing here is foundation acceptance, acquisition acceptance, or an ACK of the
  22:55 / 23:21 reviews.
- No percentage of completeness is asserted. Directory presence, readable content
  identity and data-quality admission are three different things and are reported
  separately.

## 4. Read-only evidence that WAS captured from the 24 pinned paths

All 24 exact ZHANGWEI paths from `CAPTURE_PLAN.json` were readable; **no path was
missing**. Nine bodies match a pinned HUB original by SHA256 (`REUSED_HUB_BODY`, no
duplicate needed). Fifteen differ from the pinned set and are marked
`NEW_OR_CHANGED_NOT_IN_PINNED_SET`.

`COMMIT.json` binding is internally consistent: `commit_id = 572619c945d48f1b`, the
declared `release_root` resolves inside the authorised candidate tree, and the referenced
`CHECKPOINT.json` SHA256 agrees with `checkpoint_sha256`. `COMMIT.json` carries **no**
top-level `release_content_id`; the side file
`cc_commit/rcid/BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20261026_181019.json` is present
and readable.

Cleaning callsites were located by `ast.parse` only — the original module was never
imported or executed. In `candidate/run_r15_cleaning_replay.py`:
`load_staging()` at line 450 (0 args), `ingest_item(item, release_root)` at line 498,
`seal_release(release_root, rid, f"{rid}_SEAL", results)` at line 505.
`tools/run_connected_pipeline.py` and `tools/run_original_compiler_candidate.py` contain
**no** callsites of those three functions.

The wrapper's own body documents a material fact: carry-forward **hard-links** real
files, so a candidate path shares an inode with production; `switch_current` and
`patch_hand` are never called; production CURRENT and production SSOT are only read. The
retained replay receipt records all 18 gates true, `GATE_RESULT = PASS`, 371 files linked,
0 copied, and production sample inodes unchanged before/after.

`ADJUST_FACTOR_PIT_R1` admission remains **UNRESOLVED**. The retained cause statement is
`NOT_ESTABLISHED` across four indistinguishable candidates. `factor = 1.0` is recorded as
an observation only and is **not** declared wrong; ordinal `date` values were **not**
relabelled; no factor was filled; no overlap window was chosen. Dependent adjusted
products are listed separately from the independently specified `RAW_NONE` scope.

## 5. Related review amendment received (parent task, no new execution)

`reviews/BLACKBOX_FOUNDATION_R10_END_TO_END_20261025/INSTALLED_V3_REVIEW_20261026_2321.md`
rejects the installed v3 content-identity work and lists counterexamples. Received and
recorded. Nothing was rolled back, deleted, re-emitted, re-committed or re-run, per that
review's own instruction.

Preservation state verified present:

- `tools/candidate_commit.py` — live, 53,208 B
- `tools/_backup/candidate_commit.py.20261026_231040.v2.orig` — 20,732 B
- `candidate/cc_commit/RCID_PRODUCT_CONTRACT_R1.json` — 3,471 B
- `candidate/cc_commit/rcid/BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20261026_181019.json` — 1,145 B
- `sam_led_rectification/INSTALL_V3_SHA_LEDGER_R1.json` — 1,659 B
- `sam_led_rectification/RCID_V3_TARGETED_TESTS_R1.json` — 4,193 B
- `sam_led_rectification/candidate_commit_v3.py` — 52,071 B (the reviewed body)

### One identity fact the reviewer needs

The **live** `tools/candidate_commit.py` is **not** byte-identical to the reviewed v3
body. Measured:

- live: 53,208 B, SHA256 `e4772ddaa25f58e0a303c7353247b9fdac6d18ca6531cfa062f16906899ed2ff`,
  mtime 2026-10-27 10:46:29 CN
- reviewed v3: 52,071 B, SHA256 `7573eff5e78933e96cabefaabc9b93f6694c1f8d585ff7716e0d597895df1b7f`

The difference is **exactly 1,137 bytes = exactly 1,137 CRLF line endings**. Live has
1,137 CRLF and 0 bare LF; v3 has 0 CRLF and 1,137 bare LF. After LF normalisation the two
are byte-identical and hash to `7573eff5…`. So the live module's **logic is unchanged**;
only line endings were converted to CRLF after the 23:10:40 install.

Consequence, stated plainly: a hash-based binding to `7573eff5…` does **not** match the
current live body. Any future receipt must report `e4772dda…` as the deployed identity and
cite the normalised relationship, rather than claiming `7573eff5…` is what is deployed.
This is reported as a fact, not as a repair, and no attempt was made to normalise it back.

## 6. Remaining exact missing inputs

1. A permission-holding or Developer-Mode execution context for the 17 controls, or a
   reviewed junction-based fixture variant. Until one exists the collector stays NOT RUN.
2. `capture_001/COLLECTION.json`, `capture_001/bodies/*`, `capture_001/DELIVERY_MANIFEST.json`
   and `LOCAL_READBACK.json` — all blocked by item 1.
3. Per-unit request/key/page/exhaustion receipts for **future** acquisition. The retained
   R15 acceptance records requested/returned counts only, which are insufficient going
   forward.
4. A HUB-pinned original for the two staging manifests, which are currently
   `NEW_OR_CHANGED_NOT_IN_PINNED_SET`.
5. Reconciliation of `TIP_REBASE_LAST.pointer.cache_release_id` (`…_181756`) against
   `COMMIT.json.release_root` (`…_181019`). Known same-commit-id NOOP binding gap, not a
   content divergence.

## 7. Boundary compliance

- Writes confined to `C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027`.
- No write to `E:\BLACKBOX` or `E:\BLACKBOX_ENGINES`.
- No supplier login, call or quota probe. No credential content was read, copied, hashed
  or uploaded.
- No download, no cleaning/compiler/commit/emit/rebind execution, no CURRENT or rule
  change, no strategy run, no global inventory, no full-library hash, no deletion, no
  rollback, no formatting.
- `scope_refresh`, `research_os status`, the data-plane default/VERIFY_ONLY entry, the
  original R15 `main`, and the attachment's unreviewed comparison script were **not**
  invoked.
- `ORDER_ALLOWED = false` throughout.
