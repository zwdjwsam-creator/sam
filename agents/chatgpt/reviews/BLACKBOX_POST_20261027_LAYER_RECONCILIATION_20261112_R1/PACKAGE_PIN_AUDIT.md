# Independent Package Pin Audit — R1

Review time: 2026-11-12 11:54 UTC
Repository: zwdjwsam-creator/sam
Branch: main
Head reviewed: d673a6f80728122d837cd6988ae4269292d19c09

## Decision

The published R1 execution package is internally inconsistent with the exact bytes currently stored in the reviewed GitHub package. The required PowerShell package-pin loop must stop with PACKAGE_PIN_MISMATCH before the offline tests, local preflight, or metadata capture if the executor stages the current reviewed files.

This is a packaging/identity failure, not evidence of a source-data or runtime failure. Preserve the R1 task and its pending state. Do not replay the capture, replace the task in flight, or stop any process. Await the executor's literal status. If R1 has already started, preserve its actual outcome and do not interrupt it.

## Exact byte and hash verification

The three files were fetched from the current GitHub branch using base64 content. Decoded byte lengths were checked, and each Git blob SHA-1 was independently recomputed over the Git object header plus the exact decoded bytes; all three matched the GitHub blob SHA. SHA-256 was then computed over those same exact bytes. The SHA-256 implementation was checked against the standard `abc` and 56-byte multi-block test vectors.

| File | Bytes | Current Git blob SHA | SHA-256 of current GitHub bytes | SHA-256 declared by R1 |
|---|---:|---|---|---|
| `capture_registered_layer_metadata_r1.py` | 13,128 | `c988acb7d89bbf11919065c830e264e2a95f3b7c` | `fabd15af5662343655f9723f599509311a11085d10e0b8c4ba8d29444f737dac` | `f40b762e97cefee39d6746fcf2c6f4d380ff537b0089a87071ba0825f8bf049c` |
| `test_capture_registered_layer_metadata_r1.py` | 5,564 | `5d733ec7145e2090ca8845321021eec1a1a40f95` | `8e1907b354dca7e8fb52bcf8a48896e9ae79a376c9c6c0e445d063b742d178b3` | `a205813cd4640dc02879eef2dffc6d65acd3d785d7ffe48bc8f8c74d2ad64cc4` |
| `PACKAGE.json` | 711 | `ca50a94ebcd8beddd4c9f391f2d450edd3df567a` | `699bd2f00439a62f8413688683b19774def816a1d68073d08056a327323b165b` | `2c6fb962e3fae26bc1b44eb618b71d1c20ede4ebca8dfce258818adc5465142d` |

All byte counts match the R1 task. All three SHA-256 values differ from the task's declared values. The current `PACKAGE.json` also embeds the two stale code/test SHA-256 values, so the manifest does not repair the mismatch.

The task's exact verification loop therefore cannot pass against the current reviewed GitHub files. No test, preflight, or capture command should be attempted after this mismatch.

## Code and scope review

The full current capture script and test source were read. The script fixes 11 exact registered metadata/dictionary inputs and 11 literal candidate session dates. It does not glob or recursively enumerate directories, invoke network/supplier APIs, read credentials, read Parquet, or write to E:. It records literal metadata references only and explicitly disclaims row-level coverage and source-absence conclusions. The path-prefix literals resolve to single Windows separators at runtime.

The existing R1 review reports 12/12 offline fixture tests passing on authored source. This audit did not rerun those tests or claim ZHANGWEI native execution. The stale package hashes are outside the existing test coverage and are caught by the task's pre-execution PowerShell pin check.

## Outstanding execution evidence

- Current R1 task: `agents/chatgpt/outbox/BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1.md`, blob `c2d564ba1f7d8be970a76e9818cd9cf9a58e55be`.
- Current review: `agents/chatgpt/reviews/BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1/REVIEW.md`, blob `de3c18b3f0b8b7c17f7d3af2be1dc9ad7d007ede`.
- Current package: `ca50a94ebcd8beddd4c9f391f2d450edd3df567a`; code: `c988acb7d89bbf11919065c830e264e2a95f3b7c`; tests: `5d733ec7145e2090ca8845321021eec1a1a40f95`.
- `INBOX_FOR_CHATGPT.md` blob `f71a852ca705325cdd27a67496dbf5c89d7cdb23` does not mention R1; the R10 root directory has no new R1 return member.
- The exact R1 inbox return directory and its `ZHANGWEI` child both return 404. The state records R1 as `ISSUED_ACK_PENDING`; no ACK or native return is present in HUB.

## Foundation and continuation boundary

R10 operating-entry acceptance remains bounded observation only. R10 full-foundation acceptance remains false. R5 acquisition through 2026-10-27 and P3's bounded candidate remain closed and must not be replayed. R4 remains an independent outstanding diagnostic and must not be stopped or duplicated.

This audit authorizes no supplier call, acquisition, Cleaning, alignment, PIT transformation, CURRENT switch, release, backtest, or order. R6 remains unissued pending verified registered calendar coverage, measured supplier availability/lag, a new task-specific quota, and a complete product-specific acquisition/Cleaning contract.

## Required next handling

1. Preserve R1 as issued; do not retry it under changed pins.
2. Await its native ACK/status or literal package-pin failure receipt. Do not infer execution from task publication.
3. After the R1 outcome is known, issue a separate, corrected one-shot metadata-capture task only if still needed. Its package manifest and task must be generated from exact current GitHub bytes, and all corrected hashes must be independently read back before publication.
4. Keep `ORDER_ALLOWED=false`, `CURRENT_SWITCH_ALLOWED=false`, and `FORMAL_RELEASE_ALLOWED=false`.
