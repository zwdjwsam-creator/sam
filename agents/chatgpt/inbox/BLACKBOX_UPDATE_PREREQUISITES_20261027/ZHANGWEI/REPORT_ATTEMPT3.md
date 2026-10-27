# ZHANGWEI attempt 3 (windows_fixture_v3) — execution report

task_id: BLACKBOX_UPDATE_PREREQUISITES_ZHANGWEI_20261027
parent_task_id: BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025
dispatch_id: BLACKBOX_UPDATE_PREREQUISITES_20261027
execution_host: ZHANGWEI
hostname: ZHANGWEI
interpreter: E:\BLACKBOX\.venv\Scripts\python.exe (3.12.10, unprivileged, no environment change)
reported_at_cn: 2026-10-27T13:33:00+08:00
status: GATE_PASSED_23_OF_23_COLLECTOR_EXIT_0_CAPTURE_COMPLETE
FOUNDATION_ACCEPTANCE=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false

## 1. Result

| step | requirement | actual |
|---|---|---|
| package staging | 12 files, 11 declared payloads verified | 12 staged, **11/11 bytes+SHA256 match**, none missing, none extra |
| collector identity | unchanged `3e20395e…dc96858` | **identical** |
| native gate | ALL 23, zero fail/error/skip, exit 0 | **23 ok, 0 fail, 0 error, 0 skip, actual exit 0** (`Ran 23 tests in 0.248s` / `OK`) |
| collector | once, only after the gate | **ran once, actual exit 0** |
| capture_003 | must not pre-exist or be deleted | created by the collector itself; never pre-created, never deleted |

Collector stdout, verbatim:

```
{"guard_changes": 0, "host": "ZHANGWEI", "records": 28, "search_limits": false, "unresolved": 0}
```

`unresolved = 0`, `search_limits = false`, `guard_changes = []`.

## 2. The V3 fix is the one that was measured, and it holds natively

`windows_junction_fixture.py` passes argv as separate elements —
`["cmd.exe", "/d", "/c", "mklink", "/J", link_text, target_text]` — which is exactly the
form measured as working on this host in `JUNCTION_CALL_PROBE.json` (form B). It adds
metacharacter rejection, `stdin=DEVNULL`, a 15 s timeout, and raw-byte hex diagnostics on
failure.

One point worth stating plainly: on the reviewer's Linux run the two real-junction
controls could not prove native junction behaviour, and that limitation was disclosed. Here
they **actually executed against real Windows junctions** and passed — `test_external_link_blocked`
and `test_cycle_link_not_followed_and_disclosed` are both `ok` on this host. So native
junction proof now exists, which it did not before.

V1 and V2 failures both remain preserved and are not represented as passes.

## 3. What the collector captured

28 records across the 24 declared plan paths plus the four bound metadata files resolved
from `COMMIT.json`:

- **15 × `REUSED_HUB_BODY`** — byte-identical to a pinned HUB original, so no duplicate was uploaded.
- **13 × `READ`** — new or changed bytes, copied to `capture_003/bodies/` with a readback.

`LOCAL_READBACK.json` reports `matches: true` for all 14 entries (13 bodies + `COLLECTION.json`).

### The primary target

`tools/candidate_commit.py` was captured as **`bodies/0015.py`, 53,208 bytes,
SHA256 `e4772ddaa25f58e0a303c7353247b9fdac6d18ca6531cfa062f16906899ed2ff`**, and I verified
it is byte-identical to the live file. Raw deployed hash governs the binding, as
instructed; the LF-normalised equality to the reviewed 52,071-byte `7573eff5…` body is a
supplementary relationship only and is not substituted for the raw identity.

### Bound execution metadata (all `REUSED_HUB_BODY`, all under `…_181019`)

| record | file | bytes | sha256 (prefix) |
|---|---|---|---|
| 25 | `cc_commit/versions/572619c945d48f1b/CHECKPOINT.json` | 2,145 | `7efc2779…` |
| 26 | `.../releases/…_181019/RELEASE.json` | 1,344 | `158dd9dd…` |
| 27 | `.../releases/…_181019/SEAL.json` | 12,849 | `b79ed73c…` |
| 28 | `.../releases/…_181019/MANIFEST.json` | 244 | `afa93d19…` |

`COMMIT.json` itself (`bodies/0020.json`, 1,674 B) hashes to
`6d52646095e5d8509ba7fa5076ee0bbaed843f668e5f72fc95805fa10c500820`, which matches the
digest the reviewer reported. So the COMMIT body was not mutated by any of my earlier work,
confirmed from bytes rather than asserted.

## 4. Boundary values recorded by the collector

```
credential_locator_present_only = true
credential_contents_read        = false
supplier_calls                  = 0
business_modules_imported       = false
acquisition_authorized          = false
current_switch_authorized       = false
order_allowed                   = false
guard_changes                   = []
task_lookup                     = null
```

No credential content was read, copied, hashed or uploaded. No supplier was called. No
business module was imported.

## 5. Remaining gaps, stated exactly

1. **`rcid` side file is not in this capture.** `cc_commit/rcid/<release_id>.json` appears
   neither in the 24 plan paths nor in the bound metadata set, so the collector did not
   read it. Its content was read directly in the V1 pass and described in
   `EXECUTION_BINDINGS.json`, but its raw bytes are still not delivered. If raw bytes are
   wanted, the exact path needs to be added to a plan — I did not add it unilaterally.
2. **Pointer divergence remains unreconciled.**
   `TIP_REBASE_LAST.pointer.cache_release_id` is `…_181756` while `COMMIT.json.release_root`
   is `…_181019`. Both bodies are now captured; the divergence itself is still unexplained.
   It is a binding gap, not evidence of content divergence.
3. **15 bodies were not re-uploaded by design** — they are byte-identical to pinned HUB
   originals. Their identity is recorded; their duplication was correctly avoided.
4. **`task_lookup` returned null.** The explicitly bounded SAM task lookup produced no
   result. That is a lookup gap, not a source-absence conclusion.
5. **Factor admission still unresolved** — unchanged by this attempt, and no cause is
   inferred here.
6. **Two staging manifests** (`08_DAILY_SOURCE_HANDOFF`, `08_FINANCE_SOURCE_HANDOFF`) were
   `READ` and are now captured as `bodies/0005.json` and `bodies/0006.json`, so their bytes
   are delivered for the first time.

Nothing in this capture supports a source-missing or download-range conclusion. No data
absence is inferred anywhere.

## 6. Receipts

- `ACK_V3.json` — published **before** execution, uploaded and read back at 3,434 B / `2fac7da7…`.
- `STAGE_VERIFY_V3.json` — 12 files staged, 11 declared payloads verified, collector identity check.
- `COMMAND_LEDGER_ATTEMPT3.json` — both processes with exact argv, cwd, executable, hostname, start/end, literal returncode, raw stream byte counts, UTF-8 validity and SHA256 of each raw stream.
- `FIXTURE_CONTROLS_ATTEMPT3_STDOUT.txt` / `_STDERR.txt` — raw process bytes (stdout is empty: unittest writes its report to stderr).
- `COLLECTOR_ATTEMPT3_STDOUT.txt` / `_STDERR.txt` — raw process bytes; the collector did start, so these exist for real, not as placeholders.
- `capture_003/COLLECTION.json`, `capture_003/DELIVERY_MANIFEST.json`, `capture_003/LOCAL_READBACK.json`.
- `capture_003/bodies/` — only the 13 actually changed bodies.

## 7. Reproducibility caveat on the gate

`FIXTURE_CONTROLS_ATTEMPT3_STDOUT.txt` is 0 bytes and that is correct, not a missing
stream: `unittest -v` writes its report to stderr. The raw stdout was retained verbatim as
zero bytes rather than being replaced by a copy of stderr.

## 8. Boundary compliance

Writes confined to `C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027`. No write
to `E:\BLACKBOX` or `E:\BLACKBOX_ENGINES`. V1 and V2 package directories and all their
receipts are intact. No elevation, no Developer Mode, no policy change, no environment
change, no package edit, no skipped control, no improvised diagnostic script, no fourth
attempt planned. No download, cleaning/compiler/commit/emit/rebind, CURRENT switch,
release publication, historical D:-chain execution, V4 reconstruction, deletion or order.
`ORDER_ALLOWED = false`.
