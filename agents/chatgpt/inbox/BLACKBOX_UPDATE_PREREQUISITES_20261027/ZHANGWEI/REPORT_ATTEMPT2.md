# ZHANGWEI attempt 2 (windows_fixture_v2) — execution report

task_id: BLACKBOX_UPDATE_PREREQUISITES_ZHANGWEI_20261027
parent_task_id: BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025
dispatch_id: BLACKBOX_UPDATE_PREREQUISITES_20261027
execution_host: ZHANGWEI
interpreter: E:\BLACKBOX\.venv\Scripts\python.exe (3.12.10, unprivileged)
reported_at_cn: 2026-10-27T13:07:00+08:00
status: ATTEMPT2_STOPPED_AT_FIXTURE_CONTROLS_COLLECTOR_NOT_RUN
FOUNDATION_ACCEPTANCE=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false

## 1. Outcome in one paragraph

V2 was staged as instructed and verified 9/9 against its own PACKAGE.json, with the
collector source byte-identical to V1. The seventeen controls were executed once and again
returned **actual process exit 1: fifteen passed, two errored in fixture construction**.
The gate therefore failed and the collector was **not** invoked; `capture_002` was never
created or deleted. No third attempt was launched. V1 files are unchanged.

## 2. This is a different failure from attempt 1

| | attempt 1 (V1) | attempt 2 (V2) |
|---|---|---|
| fixture mechanism | `os.symlink` | `mklink /J` |
| error | `OSError WinError 1314` — a required privilege is not held | `JUNCTION_FIXTURE_CREATION_FAILED: The filename, directory name, or volume label syntax is incorrect` |
| real cause | the Windows token holds no symlink-creation privilege | the command string is malformed before it reaches mklink |
| host condition | genuine privilege limit | **not** a host limit |

V2 correctly removed the privilege dependency. Junction creation works on this host, as
measured in both attempts: an unprivileged directory junction is created successfully.

## 3. Isolated diagnosis of the remaining V2 failure

`test_collect_prerequisites.py:19-21` builds

```
command = 'mklink /J "' + str(link) + '" "' + str(target) + '"'
result  = subprocess.run(["cmd.exe", "/d", "/c", command], capture_output=True, text=True)
```

The already-quoted command is passed as **one argv element**. Python renders a list to a
Windows command line via `list2cmdline`, which wraps any argument containing spaces in
double quotes and rewrites the argument's inner `"` as `\"`. `cmd.exe` does not treat
`\"` as an escaped quote, so `mklink` receives paths carrying literal backslashes and
rejects them with the syntax error above.

Verified in a single process, in one directory, within the same second
(`JUNCTION_CALL_PROBE.json`):

| call form | exit | junction created |
|---|---|---|
| A — exactly as shipped, pre-quoted single argv element | 1 | **No** |
| B — same command split into separate argv elements, no manual quoting | 0 | **Yes** |
| C — same pre-quoted string via `shell=True` | 0 | **Yes** |

Because A fails while B and C succeed from the same process on the same host, the failure
is attributable to the call's quoting, not to host policy, privileges or NTFS.

This host did **not** apply B or C to the reviewed package: the instruction is explicit
that no code may be changed and that a failing fixture creation must be preserved and
stopped without a bypass. B and C are reported only as the minimal, measured fix so a
reviewed V3 can be issued quickly.

Neither of the two assertions was weakened. `test_external_link_blocked` and
`test_cycle_link_not_followed_and_disclosed` remain fully active; they simply never
reached their assertion because fixture construction raised first.

## 4. Suggested minimal repair for a reviewed V3

Either change, alone, makes the shipped control set pass on this host:

1. pass argv as elements — `subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)], ...)`; or
2. keep the string but drop the manual list wrapper and use `shell=True`.

Option 1 is preferable: it never relies on shell parsing. The existing
`UNSAFE_FIXTURE_PATH` guard and the junction cleanup in `addCleanup` can stay as they are.

## 5. Files delivered with this attempt

- `ACK_V2.json` — ACK scope recorded as staging plus attempt-2 completion-with-failure, explicitly not a running process and not an acceptance.
- `COMMAND_LEDGER_ATTEMPT2.json` — the untouched V1 row reproduced verbatim plus the attempt-2 row; the V1 ledger itself is not rewritten.
- `FIXTURE_CONTROLS_ATTEMPT2_STDOUT.txt` / `FIXTURE_CONTROLS_ATTEMPT2_STDERR.txt` — literal streams, actual exit 1.
- `JUNCTION_CALL_PROBE.json` — the A/B/C isolation above.
- `STAGE_VERIFY_V2.json` — 9/9 payload verification and collector-identity check.
- `COLLECTOR_ATTEMPT2_NOT_RUN.json` — records that no collector process started.
- `DELIVERY_MANIFEST_ATTEMPT2.json`, `UPLOAD_READBACK_ATTEMPT2.json`.

## 6. What is deliberately NOT delivered, and why

`COLLECTOR_ATTEMPT2_STDOUT.txt` and `COLLECTOR_ATTEMPT2_STDERR.txt` are **absent** rather
than created empty. An empty file is indistinguishable from a collector run that produced
no output, and no process was started, so no stream exists to preserve. Their absence is
recorded explicitly in `COLLECTOR_ATTEMPT2_NOT_RUN.json`.

`capture_002/` does not exist. No `COLLECTION.json`, `LOCAL_READBACK.json` or
collector-authored `DELIVERY_MANIFEST.json` is claimed.

## 7. V1 evidence preserved

The V1 ledger, V1 stdout/stderr, V1 ACK, V1 privilege probe and V1 delivery/readback
receipts are untouched. The local `COMMAND_LEDGER.json` had been appended to during the
attempt-2 run, so it was **restored from the remote V1 blob** and verified at 5,720 bytes
and SHA256 `657e1f7cb296d7eb3012a2ec242eff42edb55ff1e869c1acb42d131ad792f976`
before this delivery; the combined ledger lives only in `COMMAND_LEDGER_ATTEMPT2.json`.

## 8. Still-missing inputs (unchanged)

1. A reviewed fixture package whose Windows junction call is correctly quoted. Until then
   the collector stays NOT RUN on this host.
2. Everything downstream of the collector: `capture_002/COLLECTION.json`, changed-body
   copies and the collector-authored manifest and readback.
3. The live `tools/candidate_commit.py` remains 53,208 B /
   `e4772ddaa25f58e0a303c7353247b9fdac6d18ca6531cfa062f16906899ed2ff`, not the reviewed
   52,071 B / `7573eff5…` body; only the collector can capture those bytes. Not substituted,
   not edited, no pipeline rerun.

## 9. Boundary compliance

Writes confined to `C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027`. No write
to `E:\BLACKBOX` or `E:\BLACKBOX_ENGINES`. No elevation, no Developer Mode, no system
policy change, no test/collector edit, no skipped control. No supplier call, download,
cleaning/compiler/commit execution, CURRENT switch, rule change, strategy run or order.
No credential content read, copied, hashed or uploaded. `ORDER_ALLOWED=false`.
