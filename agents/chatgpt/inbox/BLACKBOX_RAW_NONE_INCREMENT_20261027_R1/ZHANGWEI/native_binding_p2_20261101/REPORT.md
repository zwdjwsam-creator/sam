# BLACKBOX_R5_NATIVE_BINDING_P2_20261101 — native runtime and read-only source binding handoff

- task_id: `BLACKBOX_R5_NATIVE_BINDING_P2_20261101`
- execution_host: `ZHANGWEI` (Windows 11, `Windows-11-10.0.26200-SP0`)
- executed_at_utc: 2026-11-01T06:22:08.916435Z → 2026-11-01T06:22:09.177957Z
- outcome: **`COMPLETE_HANDOFF_ONLY`**, outer actual OS exit **0**
- `ORDER_ALLOWED=false`, `supplier_calls=0`, `cleaning_run=false`, `current_switched=false`

## 1. What was and was not done

| Item | State |
|---|---|
| Bounded read-only host / runtime / rule / calendar handoff | **DONE** |
| Package staged from review folder, bytes unchanged | **DONE** (7 files, 6/6 payload pins) |
| ACK + PACKAGE_VERIFY uploaded and read back before execution | **DONE** (byte-equal) |
| Collector executed exactly once, attached and waited | **DONE** (1 run, no retry) |
| Native cleaning execution | **NOT DONE — not authorized** |
| Supplier acquisition / price read / directory scan | **NOT DONE — not authorized** |
| CURRENT publication or switch | **NOT DONE — not authorized** |
| P1 activation | **NOT DONE — not authorized** |
| Backtest admission / orders / scheduler change | **NOT DONE — not authorized** |
| GPT offline unit suite on Windows | **NOT RUN — the dispatch forbids it** |
| Interpreter install / repair / substitution | **NOT DONE** |

## 2. Runtime as measured on this host

The reviewed `ENVIRONMENT_PROBE` of 2026-10-25 described an earlier broken
launcher/system/isolated runtime. The values below are a fresh measurement from the
successful 2026-10-28-and-later R5 runtime and supersede that stale probe. No
interpreter was installed, repaired or substituted to obtain them.

| Field | Measured |
|---|---|
| `python` | `3.12.10 (tags/v3.12.10:0cc8128, Apr  8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)]` |
| `executable` | `E:\BLACKBOX\.venv\Scripts\python.exe` |
| `platform` | `Windows-11-10.0.26200-SP0` |
| pandas | `3.0.3` at `E:\BLACKBOX\.venv\Lib\site-packages` |
| pyarrow | `24.0.0` at `E:\BLACKBOX\.venv\Lib\site-packages` |
| numpy | `2.5.4` at `E:\BLACKBOX\.venv\Lib\site-packages` |

Versions come from installed distribution metadata only. No supplier library was
imported and no environment-variable dump or credential was read.

## 3. Source binding: 17 originals read from `E:`, bound by body and hash

All bodies were read from the `E:\BLACKBOX` originals with a pre/post
`(size, mtime_ns, inode)` and length check per file. Every file is a regular file
under the 2 MiB bound. After the collector finished, all 17 were re-read and
compared: no source changed. The 17 bodies total 57,240 bytes; base64 is carried
inside `capture_001/ENVIRONMENT_AND_BODIES.json` for GPT to bind against, not to
reconstruct a substitute evidence root.

| Bytes | Path (relative to `E:\BLACKBOX`) |
|---:|---|
| 1,160 | `数据/清洗成品/CURRENT_CLEANING_RELEASE.json` |
| 1,531 | `数据/回测缓存/CURRENT_CACHE_RELEASE.json` |
| 5,596 | `研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json` |
| 625 | `研究系统/数据平面/CURRENT/DAILY_DATA_PLANE_CURRENT.json` |
| 11,767 | `脚本/blackbox_must_read_preflight_r1.py` |
| 11,800 | `脚本/_base.py` |
| 1,167 | `.cursor/rules/BLACKBOX_KERNEL_ALWAYS_APPLY.mdc` |
| 2,943 | `契约/必读/MUST_READ_MANIFEST_CURRENT.json` |
| 1,570 | `契约/必读/BLACKBOX_BOOTSTRAP_MUST_READ.md` |
| 6,911 | `契约/必读/BLACKBOX_DATA_ACCESS_MUST_READ.md` |
| 2,467 | `契约/必读/BLACKBOX_ACQUISITION_MUST_READ.md` |
| 1,100 | `契约/必读/BLACKBOX_FACTOR_RESEARCH_MUST_READ.md` |
| 1,326 | `契约/必读/BLACKBOX_BACKTEST_MUST_READ.md` |
| 691 | `契约/必读/BLACKBOX_QMT_MUST_READ.md` |
| 914 | `STAGING/BLACKBOX_RAW_NONE_INCREMENT_20261027_R1/CALENDAR.json` |
| 4,182 | `数据/原始只读/JQData_reference_dictionary/20_unified_data_schema_contract_freeze_full_R1/02_domain_schema/domain_schema_contract.csv` |
| 1,490 | `数据/原始只读/JQData_reference_dictionary/20_unified_data_schema_contract_freeze_full_R1/04_pit_schema/pit_schema_contract.csv` |

Embedded pins, verified against the captured bodies:

| File | Pinned SHA-256 | Status |
|---|---|---|
| `脚本/blackbox_must_read_preflight_r1.py` | `3bb85023387ce976aaf03694073936b0da5b5ef710f80f6284e8347f067fe217` | `VERIFIED` |
| `脚本/_base.py` | `b8cc60746f92dc63049e8e6b6b6f39c6553dd98b69374b9f797d49b2654f2258` | `VERIFIED` |

## 4. Nested preflight: permitted to run, ran once, reported honestly

The collector ran the original preflight only because both pinned sources matched.
Exact internal argv, its own exit, and its own streams:

```
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py --task-class DATA
```

- actual exit: **0**
- `capture_001/PREFLIGHT_RUN.json` status: `RETURNED_FOR_GPT_REVIEW` (the collector
  returns the observation; it does not claim acceptance on GPT's behalf)
- stdout (`capture_001/preflight.stdout.txt`, 870 B) reports `MUST_READ_PRECHECK = PASS`,
  `TASK_CLASS = DATA`, `KERNEL_STATUS = VERIFIED`, `AUTHORITY_READY = YES`,
  `TASK_EXECUTION = ALLOWED`, with `BOOTSTRAP` and `DATA_ACCESS` rule hashes both `VERIFIED`
- stderr (`capture_001/preflight.stderr.txt`): 0 bytes, preserved as zero bytes
- no `--write-manifest`, `--acceptance` or repair flag was passed

Observed only, not interpreted as an approval: the preflight printed
`HAND_READ = NOT_SUFFICIENT` in the same run while still returning `PASS`. That is its
own notation about `HAND.txt` reading, reported here verbatim rather than smoothed over.

## 5. Once-only execution

- `RUN_ONCE.json` (95 B) and `capture_001/` were created by the supplied code itself;
  `RUN_ONCE.json` sits **outside** `capture_001`, so deleting the capture directory
  cannot reopen this task.
- Pre-execution duplicate check: control directory, `package/`, `capture_001`,
  `RUN_ONCE.json` and the return folder did **not** exist; no prior receipt for this
  task id existed.
- Control-directory path was confirmed ordinary/non-reparse (lstat reparse attribute,
  junction and symlink checks across every path component) before any write.
- One run, no retry, no local patch. `OUTER_RUN.json` records the single run.

## 6. Streams and receipts

| File | Bytes | Meaning |
|---|---:|---|
| `OUTER.stdout.txt` | 0 | outer process stdout, zero bytes preserved as zero bytes |
| `OUTER.stderr.txt` | 0 | outer process stderr, zero bytes preserved as zero bytes |
| `OUTER_RUN.json` | 1,467 | exact argv, cwd, start/end, single run, actual waited-for OS exit |
| `RUN_ONCE.json` | 95 | once marker written by collector before `capture_001` |
| `ACK.json` | 11,009 | pre-execution binding; explicitly does not claim execution |
| `PACKAGE_VERIFY.json` | 2,653 | staged-byte and pin verification |
| `capture_001/ENVIRONMENT_AND_BODIES.json` | 81,155 | runtime plus 17 bound bodies |
| `capture_001/PREFLIGHT_RUN.json` | 352 | nested preflight argv, streams, actual exit |
| `capture_001/preflight.stdout.txt` | 870 | nested preflight stdout |
| `capture_001/preflight.stderr.txt` | 0 | nested preflight stderr |
| `capture_001/LOCAL_READBACK.json` | 718 | exact readback of the four earlier capture files |

`capture_001/LOCAL_READBACK.json` deliberately covers only the four files written
before it. It does not hash itself. `PACKAGE.json` likewise does not carry its own
SHA; its raw SHA-256 is recorded in `ACK.json` and `PACKAGE_VERIFY.json` instead:
`7fe6fbc2e3b3a674cdc971bb622ad0833f2cbacdfca218bbb101a9a901852d0a`.

The outer exit and the nested preflight exit are separate observations from separate
processes. Neither is presented as the other.

## 7. Package provenance

Seven files were staged unchanged from
`agents/chatgpt/reviews/BLACKBOX_R5_NATIVE_BINDING_P2_20261101/` into
`C:\LAN_SHARE_REPORT\BLACKBOX_R5_NATIVE_BINDING_P2_20261101\package`. No newline
normalization, no rewrite, no substitution. All 6 payloads matched the length and
SHA-256 declared in `PACKAGE.json`; every staged byte was re-read locally and compared
to the received bytes.

## 8. Status separation

| Facet | State at the time of this report |
|---|---|
| Publication to HUB | performed, see `UPLOAD_READBACK.json` |
| ACK | written and read back **before** execution |
| Attempted execution | yes, exactly one attached run |
| Actual exit | outer **0**; nested preflight **0** |
| Handoff completion | `COMPLETE_HANDOFF_ONLY`, no problems recorded |
| GPT review | **still pending** — this report claims no review outcome |

## 9. Gaps this task did not close

Stated so that nothing here is read as native-cleaning readiness. From the review,
these remain open and are not addressed by an environment handoff:

1. Dictionary CSVs are handed over as bodies only. No semantic field/type/unit/null
   binding has been published, and unknown dictionary semantics remain unbound.
2. No native implementation was built; nothing here reads the handoff ZIPs at
   execution time. What this task does establish is that the `E:` originals named in
   `INPUTS` are directly readable, bounded and hash-stable before and after a run.
3. Windows reparse/junction rejection was exercised only along the control-directory
   path, not certified as a general guarantee.
4. `read_price_frame`'s eight-field projection was not touched and remains
   `NOT consumer-state`, `NOT backtest admission`.
5. The seven RCID publication defects and the original failed outcomes remain open.
6. The GPT Linux test log is review evidence only; it is not a native gate, and no
   Windows run of that suite is claimed.

No data was processed, no supplier was contacted, no price frame was read, no
directory was scanned, no CURRENT was touched, and no order or scheduler change was
made.
