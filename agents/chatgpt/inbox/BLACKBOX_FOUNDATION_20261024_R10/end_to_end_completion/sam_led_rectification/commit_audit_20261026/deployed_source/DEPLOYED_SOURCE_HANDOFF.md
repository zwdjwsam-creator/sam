# DEPLOYED_SOURCE_HANDOFF_R1 — execution-bound bodies for the precise repair patch

- task_id: `BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025`
- dispatch_id: `SAM_LED_DESKTOP_RECTIFICATION_20261025`
- requested_by: `DESKTOP_COMMIT_AUDIT_REVIEW_20261026_1909` (seven bodies); `INSTALLED_V3_REVIEW_20261026_2321` closes body #1
- supplied_at_cn: 2026-10-27
- supplied_by: SAM, read over SMB **from the desktop deployment** (`\\192.168.100.1\BLACKBOX_DEST` = `E:\BLACKBOX`)
- status: `EXECUTION_BOUND_BODIES_DELIVERED_FOR_GPT_PATCH`
- boundaries held: no acquisition, no production CURRENT write, no publication, no order, no pipeline rerun, no data rescan, no deletion

## 0. What this handoff is, and is not

This delivers the **exact bytes the desktop is currently running**, so the repair patch can be
authored and offline-checked against the real bodies rather than against historical snapshots.

It is **not** an execution attestation. No literal process command, exit code, stdout or stderr
ledger is retained for these bodies; historical execution identity is therefore recorded as
`UNKNOWN` (see §5). Importing a file today does not prove what an earlier process executed.

It is also **not** a patch. Repair ownership remains with ZHANGWEI; SAM preserves its working data
flow. Nothing here authorises a deployment command.

## 1. Byte fidelity

All six bodies were copied with `shutil.copyfile` (raw bytes). **No newline normalisation, no
BOM stripping, no re-encoding.** Line-ending statistics are reported per file so a reviewer can
confirm the raw form was preserved rather than "normalised to claim byte equality".

| body | bytes | CRLF | bare LF | BOM | SHA256 |
|---|---|---|---|---|---|
| 2 `run_connected_pipeline.py` | 35,051 | 718 | 0 | false | `6bea0313483b1847…` |
| 3 `cache_compiler_daily_incremental_r1.py` | 47,910 | 0 | 1,156 | false | `a887f7c7498bc573…` |
| 4 `cache_compiler_tip_rebase_from_current_r1.py` | 30,661 | 0 | 719 | false | `094eb6ef32194c32…` |
| 5 `RELEASE.json` | 1,344 | 29 | 0 | false | `158dd9ddd290370d…` |
| 6 `SEAL.json` | 12,849 | 410 | 0 | false | `b79ed73cdf095e62…` |
| 7 `CHECKPOINT.json` | 2,145 | 52 | 0 | false | `7efc277999009999…` |

Full 64-hex digests and absolute desktop source paths are in `MANIFEST.json`.

Note the mixed conventions: the runner and the three metadata files are CRLF; both compiler
bodies are LF-only. That difference is real desktop state, not a transfer artifact — it is the
same asymmetry previously measured on `run_connected_pipeline.py` (28,893 CRLF vs 28,302 LF for
identical text).

## 2. Which release and checkpoint these metadata belong to

Resolved from the desktop's own `cc_commit/COMMIT.json`, not from a directory-name guess:

```
seq                = 4
commit_id          = 572619c945d48f1b14f41c6f8c94b66dbacab00da4303366bcf2687ff8ec0876
release_id         = BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20261026_181019
release_root       = E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\candidate\cc_out\releases\BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20261026_181019
checkpoint_path    = E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\candidate\cc_commit\versions\572619c945d48f1b\CHECKPOINT.json
release_content_id = absent (legacy CC_COMMIT_R1 record)
```

So body 5/6 come from the `_181019` release (the one the authoritative reference points at, which
is **not** the newest directory on disk — that is `_181756`), and body 7 is the checkpoint the
COMMIT actually references.

## 3. Body #1 is closed, but its deployed size differs from the review's figure

`INSTALLED_V3_REVIEW_20261026_2321` records v3 as **52,071 bytes / `7573eff5e78933e9…`** and asks
that it not be requested again. The live desktop module is now **53,208 bytes**:

```
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\tools\candidate_commit.py
  bytes  = 53,208
  sha256 = e4772ddaa25f58e0…
```

That is **not** 52,071 / `7573eff5…`. Two readings are possible and this handoff does not decide
between them:

1. a further local edit was installed on the desktop after the 23:21 review; or
2. the 23:21 review's size/hash refers to the uploaded candidate body rather than the installed one.

Per the 23:21 instruction, `candidate_commit.py` was **not re-uploaded and not requested again**;
it is referenced by path and SHA only. But the discrepancy is recorded here because a repair patch
written against 52,071 bytes may not match the 53,208-byte live module. The current deployed body
is available at the path above whenever GPT wants it re-fetched.

## 4. Deliberately excluded

| excluded | reason |
|---|---|
| current `candidate_commit.py` | v3 already supplied; referenced by SHA only per 23:21 |
| the 20,732-byte legacy module | backup; referenced by SHA only; must not overwrite the live module |
| the 13,930-byte `deliverables/changed_code` snapshot | historical; must not overwrite the live module |
| the zero-byte baseline | preserved as failed evidence, untouched |
| market data / parquet / credentials / CURRENT files | out of scope |

## 5. Explicit gaps

- **Historical execution identity: `UNKNOWN`.** No literal process command/exit/stdout ledger was
  retained for the runs that produced the current `_181019` release or the `572619c9` commit.
  The `FULL_CHAIN.log` retained on the desktop belongs to the 2026-09-24 cleaning chain, not to
  these candidate commits.
- **Line-ending form is reported, not certified as semantically equivalent** to any other copy.
- **Junction targets are not hashed** in this handoff; it carries bodies only.
- No statement is made here about whether the deployed bodies are correct, complete, or accepted.
  That is the reviewer's call.

## 6. Files in this handoff

```
MANIFEST.json
DEPLOYED_SOURCE_HANDOFF.md          (this file)
2_runner/run_connected_pipeline.py
3_compiler/cache_compiler_daily_incremental_r1.py
4_compiler/cache_compiler_tip_rebase_from_current_r1.py
5_metadata/RELEASE.json
6_metadata/SEAL.json
7_metadata/CHECKPOINT.json
```

Each file was read back from the remote after upload and its byte count and SHA256 compared to the
local copy before this chat ended; see `READBACK.json`.
