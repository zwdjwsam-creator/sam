# R5 ISOLATE_RESUME — blocked at the second gate, no supplier call

task_id: BLACKBOX_RAW_NONE_INCREMENT_20261027_R5_ISOLATE_RESUME
execution_host: ZHANGWEI
outcome: BLOCKED_AT_TESTS / GATE_R5 NOT WRITTEN / EXECUTION NOT RUN
language: English (as required)

## Bottom line

The original host preflight passed. The package control suite did not: 125 ran, 123 ok, 1 failure, 1 error, real OS exit 1. The wrapper therefore returned actual OS exit 2 with `TESTS_EXIT_NONZERO_OR_TIMEOUT`, `GATE_R5.json` was never written, and `acquire_r5.py --execute` was **not** run. Supplier calls 0, quota spent 0, `E:\BLACKBOX\STAGING\BLACKBOX_RAW_NONE_INCREMENT_20261027_R5` does not exist.

Both failures have one cause and it is a defect in the two controls, not in the acquisition logic. Details and proof below. I did not patch, skip, weaken or rerun anything.

## What ran, with real exits

| step | actual OS exit | verdict |
|---|---|---|
| package staging + identity | — | 19/19 payloads match bytes and SHA256, 0 CRLF conversions |
| ACK + PACKAGE_VERIFY uploaded, byte read back | — | both byte-equal, before any command |
| `precheck_r5.py` (wrapper), 1 run only | 2 | `BLOCKED_NO_SUPPLIER_CALL` / `TESTS_EXIT_NONZERO_OR_TIMEOUT` |
| inner `blackbox_must_read_preflight_r1.py --task-class ACQUISITION` | 0 | `MUST_READ_PRECHECK = PASS` |
| inner `-m unittest -v test_acquire_daily test_r3_code_and_reuse test_r4_empty_slots test_r5_resume` | 1 | `Ran 125 tests`, `FAILED (failures=1, errors=1)` |
| `acquire_r5.py --execute` | NOT RUN | second gate never existed |

The inner preflight printed PASS/VERIFIED with KERNEL `b05a6995…197a` and BOOTSTRAP/DATA_ACCESS/ACQUISITION all VERIFIED, 1157-byte stdout, empty stderr, real exit 0. `HAND_READ = NOT_SUFFICIENT` appears as the known unconditional informational line and is not a failure.

The wrapper's own streams were captured externally with `Start-Process -Wait` and are preserved as real files, including the two zero-byte streams kept as zero-byte streams. stderr was never copied into stdout.

## The two failing controls and their single cause

```
ERROR test_exact_raw_read_only                    package/test_r5_resume.py:100
  acquire_daily.Blocked: EXTERNAL_LINK_TARGET
FAIL  test_failed_hash_corruption_refused         package/test_r5_resume.py:96
  AssertionError: "IDENTITY_DRIFT" does not match "EXTERNAL_LINK_TARGET"
```

Both build their fixture in `tempfile.TemporaryDirectory()` and then call `acquire_r5.read_exact`, which calls `acquire_daily.require_allowed_read(path.resolve(strict=True))`. That guard is:

```python
def allowed_windows_path(text):
    value = text.removeprefix('\\\\?\\').casefold()
    return value.startswith(('e:\\blackbox\\', 'e:\\blackbox_engines\\'))

def require_allowed_read(physical):
    require(os.name != 'nt' or allowed_windows_path(str(physical)), 'EXTERNAL_LINK_TARGET')
```

On this host the fixture resolves to `C:\Users\Admin\AppData\Local\Temp\tmpXXXX\body`, which is outside the allowed roots, so the guard fires before either test reaches its assertion. The second control wants `IDENTITY_DRIFT`, but the path guard raises `EXTERNAL_LINK_TARGET` first.

**Why GPT's offline run saw 125/125.** OFFLINE_RECEIPT.json records python `3.12.14 (main, Aug 25 2026) [Clang 22.1.3]`, a non-Windows interpreter. `require_allowed_read` is a no-op when `os.name != 'nt'`, so the system temp path is never inspected and both controls pass. The defect is invisible offline and deterministic on the real Windows execution host. This is exactly the class of divergence the dispatch asked native execution to surface.

**Proof the acquisition logic itself is sound.** Read-only revalidation of the real failed body inside the allowed root:

```
read_exact(E:\BLACKBOX\STAGING\BLACKBOX_RAW_NONE_INCREMENT_20261027_R4\raw\stock\2026-10-27_03360_R4.parquet,
           {bytes: 15489, sha256: fb1a0ccb4918e6035d7e6a3695d6fbac6cbf9818c3ea2ca01bcf7928b2e8b2c7})
-> OK, 15489 bytes, sha256 match true, allowed_windows_path true
```

So the guard, the pin and the reader all behave as designed; only the tests' choice of fixture directory is wrong. The 123 passing controls include every quarantine-cap, four-numeric-pair, ETF/index hard-stop, gate-evidence, quota-reserve and reuse control that constrains R5 behaviour.

## What I deliberately did not do

No edit to any package or rule file. No relaxation of `allowed_windows_path`. No skip, no `-k`, no interpreter switch, no dependency install, no second run to obtain a different outcome. No Stage A recapture. No `acquire_daily.py --execute`. No cleanup, no deletion of remote artifacts, no mailbox routing change, no watchdog/AUTOHUB action, no CURRENT switch, no order.

## Repair is GPT's, not the executor's

The controls need a fixture path inside an allowed root, for example `TemporaryDirectory(dir=root)` under `E:\BLACKBOX`, or a documented allowed-root seam, or an assertion on a path already inside the allowed roots. Any of these keeps the path guard intact and makes the control mean what it intends on Windows.

## State left behind

`E:` untouched; no R5 output directory exists (verified after the run). R0–R4 evidence unchanged. Inherited quota 175858 unchanged, R5 spend 0. `GATE_R5.json` absent. Four CURRENT pointers not switched. SAM still HOLD and untouched.

## Deliverables in this folder

ACK, package verification, both inner run receipts and all six raw streams, wrapper receipt and both raw streams, `DIAGNOSIS_TESTS_R5.json`, `NOT_RUN_R5.json`, this report, and the acyclic manifest with local and upload readbacks.
