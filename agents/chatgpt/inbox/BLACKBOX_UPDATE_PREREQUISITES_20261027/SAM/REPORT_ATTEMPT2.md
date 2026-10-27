# REPORT_ATTEMPT2 — BLACKBOX_UPDATE_PREREQUISITES_SAM_20261027

- child_task_id: `BLACKBOX_UPDATE_PREREQUISITES_SAM_20261027`
- parent_task_id: `BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025`
- dispatch_id: `BLACKBOX_UPDATE_PREREQUISITES_20261027`
- execution_host: **SAM** (hostname `SAM`)
- attempt: **2** (V2, `windows_fixture_v2`, junction fixtures, no elevation)
- status: **ATTEMPT2_BLOCKED_AT_FIXTURE_GATE — COLLECTOR NOT RUN**

---

## 1. Headline

Attempt 2 was staged and run exactly once. The seventeen controls **again returned 15 pass / 2
errors, actual process exit 1**, so the collector was **not** invoked, `capture_002` was **not**
created, and the `chain_source_001` named-source handoff was **not** performed (it is gated on a
passing V2 gate).

The failure is **not** a privilege problem this time — and the evidence proves it is not a host
limitation at all. It is a **command-construction defect in the reviewed V2 fixture**: junctions
are created successfully on this same host, same unelevated account, same volume, in the same run,
as soon as the `mklink` tokens are passed as separate argv elements instead of one pre-quoted
string.

Per instruction, nothing was modified or bypassed: no test edit, no collector edit, no elevation,
no Developer Mode, no policy change, no skipped test, no third attempt.

---

## 2. Staging verification (before execution)

`package_windows_fixture_v2` staged unchanged from
`agents/chatgpt/reviews/BLACKBOX_UPDATE_PREREQUISITES_20261027/windows_fixture_v2/`.

| check | result |
|---|---|
| PACKAGE.json schema | `BLACKBOX_REVIEWED_READ_ONLY_PACKAGE_V2`, variant `WINDOWS_JUNCTION_FIXTURES_NO_ELEVATION` |
| payloads declared / verified | 9 / **9, all byte+sha256 match** |
| collector sha256 | `3e20395ef19dec1a…7dc96858` — **identical to V1, unchanged** |

Detail: `STAGE_VERIFY_V2.json`.

Pre-flight guards, all clear before the run:

- no `python.exe` whose command line matched `collect_prerequisites` or `capture_00` (no duplicate collector)
- `SAM\capture_002` absent
- `SAM\chain_source_001` absent
- all V1 files present and left untouched

---

## 3. Attempt-2 gate outcome (literal)

```
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 -m unittest discover -s C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027\package_windows_fixture_v2 -p test_collect_prerequisites.py -v
```

| field | value |
|---|---|
| exit code | **1** (literal `subprocess` returncode) |
| elapsed | 4.134 s |
| stdout | 0 bytes |
| stderr | 5,253 bytes |
| result line | `Ran 17 tests in 2.924s` → `FAILED (errors=2)` |

Both errors are raised **inside the fixture helper**, before any collector code runs:

| test | helper call | raised |
|---|---|---|
| `test_external_link_blocked` (line 63) | `self.directory_link(self.root/"view", outside)` | `RuntimeError` attempted, but actually `TypeError` |
| `test_cycle_link_not_followed_and_disclosed` (line 81) | `self.directory_link(t/"loop", t)` | same |

The literal traceback shown is:

```
raise RuntimeError("JUNCTION_FIXTURE_CREATION_FAILED: " + result.stderr)
TypeError: can only concatenate str (not "NoneType") to str
```

So the real error message never surfaced. `JUNCTION_FIXTURE_DIAGNOSTIC_V2.json` recovers it.

---

## 4. Root cause (measured, four variants)

The helper builds one string and hands it to `cmd.exe` as a **single list element**:

```python
command = 'mklink /J "' + str(link) + '" "' + str(target) + '"'
subprocess.run(["cmd.exe", "/d", "/c", command], capture_output=True, text=True)
```

`subprocess.list2cmdline` then produces:

```
cmd.exe /d /c "mklink /J \"C:\...\root\view\" \"C:\...\outside\""
```

cmd.exe does not parse the escaped inner quotes the way mklink needs, so mklink sees malformed
paths and answers:

```
文件名、目录名或卷标语法不正确。   (The filename, directory name, or volume label syntax is incorrect.)
```

Variant matrix, all in throwaway C: temp directories, all cleaned up:

| variant | command form | exit | junction created | `os.path.isjunction` |
|---|---|---|---|---|
| **A** exact V2 fixture form | one pre-quoted command string in a list | **1** | **False** | False |
| **B** separate argv tokens | `cmd.exe /d /c mklink /J <link> <target>` | **0** | **True** | **True** |
| C | `shell=True` with the quoted string | 0 | True | True |
| D | `shell=True` unquoted | 0 | True | True |

**Conclusion:** this host creates real junctions without privilege. Variant B — same host, same
account, same volume, same run — succeeds where the fixture's form fails. The blocker is the
fixture's invocation, not Windows policy, not elevation, and not the collector.

A **second, independent defect** compounds it: because the helper uses `text=True`, Python decodes
the child's **GBK** error text as UTF-8, the reader thread dies with `UnicodeDecodeError`, and
`result.stderr` becomes `None`. That is why the operator sees a `TypeError` instead of the real
message. Even a correct `mklink` failure would be reported as a confusing TypeError on a
Chinese-locale Windows host.

---

## 5. What was NOT done, and why

| item | status | reason |
|---|---|---|
| `capture_002` | **NOT CREATED** | gate did not pass; pre-creating an output directory is forbidden |
| collector (`--role SAM`) | **NOT RUN** | same |
| `chain_source_001` | **NOT CREATED** | plan is gated on a passing V2 gate; a host/output failure stops the handoff |
| `JQ_TIP_CATCHUP_UNATTENDED_R1` filename index | **NOT DONE** | part of the gated chain-source handoff |
| third attempt | **NOT MADE** | "do not launch a third attempt automatically" |
| V1 files | **unchanged** | attempt-2 artifacts use new names only |
| collector/e tests/system policy | **unchanged** | not authorised |

No `COLLECTOR_ATTEMPT2_STDOUT.txt` / `STDERR.txt` are shipped: they would otherwise imply the
collector ran and produced no output. Its absence is stated here and in
`COMMAND_LEDGER_ATTEMPT2.json` instead of being papered over with empty files.

---

## 6. What would unblock this child task

One of the following, decided by GPT or the owner — SAM will not choose:

1. **Fix the fixture invocation** (smallest change, no privilege involved): pass the tokens
   separately, i.e. `subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)])`,
   and drop `text=True` (or use `encoding="mbcs"`/`errors="replace"`) so a GBK failure message
   survives instead of turning into `TypeError`. Variant B is the proof.
2. Or supply a fixture that needs no link at all (copy-based reparse simulation).

After either, SAM re-runs the same 17 controls once and, on 17/17 with exit 0, proceeds to the
unchanged collector and then the gated chain-source handoff.

Two host facts to keep for that decision, both already measured:

- junctions on this host: **available unelevated**
- symlinks on this host: **unavailable** (`WinError 1314`) — so V1's approach cannot be revived
  without a policy change SAM will not make unilaterally

---

## 7. Authority statement

`NEW_DATA_ACQUISITION_AUTHORIZED=false`, `CURRENT_SWITCH_ALLOWED=false`, `ORDER_ALLOWED=false`.
No supplier call, no quota probe, no download, no cleaning/compiler/commit run, no production
CURRENT write, no write to `E:\BLACKBOX` or `E:\BLACKBOX_ENGINES`, no credential file opened, no
order. Nothing here is foundation acceptance or acquisition authorisation.
