# R10 factor-basis receipt review and writer regression repair

Reviewed snapshot: 5ce735ba37063119ec089c58baf5f53a6b8d93cb. Executor remains ZHANGWEI.
The 26 members of factor_basis/DELIVERY_MANIFEST.json were fetched and independently checked by exact bytes and SHA256: 26 match, zero mismatch. The manifest itself is 4,758 bytes, SHA256 499282fb471bb7e70c721fcd6c58e1072a92951cb5893de57228464d656ccdfe. The large stdout was retrieved by immutable Git blob 467f59c9e79fc437eb8ff9e7f2e78f82e98bafb4 (the contents endpoint supplied an empty body for that large file; this was a retrieval limitation, not an empty desktop result). Its SHA256 matches afbdaee971741a6d635e493b3c03fd6417af6125d9f026223b3a2abac19d6303.

## Accepted measured scope

Literal controls report 12 tests and exit 0. The actual comparison JSON reports FACTOR_GENERATION_BASIS_MEASURED, real CACHE preflight PASS, no supplier call and unchanged source files. Clean rows 12,176,722, cache rows 12,266,026, clean-only keys 0, cache-only keys 89,304, unequal shared values 205,904. All 2014-2025 key sets match; the 2026 extra keys are measured separately. At anchor 2026-08-14, 11,639,268 shared keys were tested, zero normalized mismatches; 537,454 lack a common anchor and were not tested. Cross-year observed scale is constant within tolerance for 5,465 codes. This establishes numerical relationships on measured keys only, not provenance, precedence, historical PIT or completeness.

83,503 remains physical_minus_declared. It is not lost rows. The newly reported same-folder coverage count equals the measured Cleaning count, but aggregate equality alone is not key/value or source-hash lineage proof.

## Receipt defects to correct without rerunning measurements

1. COMMAND_LEDGER seq 1 pin verification started 00:45:43, whereas tests started 00:30:27 and comparison 00:30:51. The receipt says verification was before any execution. These conflict. Preserve originals; append retained staging evidence if it exists, otherwise state pre-test ordering unproved. The comparison driver itself verifies package hashes before its real preflight, which is relevant but does not retroactively prove the separately reported chronology.
2. The five same-task receipts in ORIGINAL_WRITER_CANDIDATE are described and hashed, but their complete original bodies are absent from the current 26-member package. Their assertions are not independently verified source execution. A program path plus a same-folder self-report does not establish exact executed code identity.
3. FINAL_BYTE_READBACK.json was absent from the earlier snapshot and arrived during review (blob 2d0260ace3c3eedaa84973777128d799954f4367). Reuse the completed finisher; do not restart any measurements or delivery cycle.
4. The writer lookup covered only two literals in Python/PowerShell files <=2 MiB in three roots. No tip-field match in that bounded lookup is not proof that no tip writer exists in those roots, other scripts, other languages, or elsewhere.
5. The wrapper was decoded and its 723-byte SHA256 d236dacb2e6033bac09737c0bf6da20f8c5155dbb751a0181d087d5d704c3553 independently verified. It calls guarded_run; it can transitively cause supplier calls and writes. The claim that the wrapper itself contains no supplier call does not make invoking it safe/read-only.

## Source findings and bounded repair

The reused original incremental_backward_refresh_r1.py is byte-exact at 11,537 bytes, SHA256 1df97ec81882243716cece03afb786638a05028642f97309cf71a3bcea3456f0.

- Lines 254-260 decide have_ud from date presence alone. One code on a date satisfies the predicate even if other required codes are unserved. A pinned-AST fixture reproduces this exact expression without importing the writer.
- Lines 242-246 remove all parent rows for dirty codes then concatenate refreshed data, with no local key-conservation check. A truncated or empty refreshed response can discard prior observations. If update_date predates the parent tip, the replacement also has an incomplete revision horizon.
- publish_successor writes CURRENT directly at line 184, while this function has no explicit external publication-gate invocation. This is a function-level finding, not proof that every outer wrapper gate is absent. The wrapper/base contract must still be respected.
- main calls auth before its selftest branch. Do not execute this source or its wrapper, including --selftest.
These are source-level failure mechanisms, not proof that either caused the observed 2026 pattern.

The new r10_factor_candidate_merge.py is a pure offline merge guard. It checks explicit expected keys, refuses unauthorized value conflicts and dirty-history key regression, and blocks revisions ending before a dirty code's parent tip. It never generates a calendar/universe grid, selects revision authority or proves provenance. Every returned receipt explicitly denies publication and foundation acceptance. It must not be wired into production until source, revision-basis and expected-key contracts are established.

Thirteen offline controls pass on the review host, including the pinned original AST, partial-day completion, missing requested keys, truncated replacement, valid full replacement, incomplete revision horizon, conflicts, duplicate keys, idempotence, ordinal dates and legitimate factor=1. No supplier-facing code was imported or invoked.

## Status

B1 stays OPEN; B2 through B7 remain OPEN. Formal engine, full update pipeline, CURRENT promotion and overall foundation acceptance are not granted.
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false
