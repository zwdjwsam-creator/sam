# R08 receipt and source-schema review

Reviewed: 2026-10-24T18:55:00+08:00
Recipient: ZHANGWEI
Disposition: R08 EVIDENCE CORRECTION REQUIRED; R09 NOT RELEASED
Budget: slot 8/10 remains open for its missing required attachments. Two later execution deliveries remain. This correction is not a new inventory or an additional foundation round.

## What is supported

The supplied-file SHA values, CACHE preflight and offline controls are reported consistently. RAW presence in the explicitly opened index full-history plane is positive evidence. The seven-index patch/minute-only explanation for 2026 H1 must stay withdrawn. The 34,477-row observation-state accounting is arithmetically reconciled.

The candidate success, exact schema, complete input pins, and price conservation cannot yet be independently accepted from the summary alone. No data loss, migration-caused loss, formal engine readiness or current/latest data readiness is established.

## Required evidence corrections

1. R08 was explicitly required to upload the actual candidate manifest. The current tree contains no R08 CANDIDATE_MANIFEST.json. OBSERVATION_AND_NON_REGRESSION_EVIDENCE.json names its SHA as 89d2a903fe01701c43c6cf8a90906c096aede74db082012fb6bc31d31735787f. Supply its original bytes and independent physical reconciliation; do not reconstruct a manifest from the reports.
2. The replay description in DELTA_REPORT and LOCAL_REPAIR_RESULT is wrong. The supplied ALREADY_BUILT_VERIFIED branch checks parent source/artifact hashes and stored input/output hashes; it does not rebuild the panel, rederive the grid audit or perform the original R06 parent-fingerprint comparison. Correct the text, preserving the original raw stdout. A separate new readback can establish physical facts; do not relabel replay as that readback.
3. R07 reported a full-prefix input of 12,351,786; R08 reports 12,362,212, a difference of exactly 10,426 target-date rows. Reconcile against actual pinned input parquet footers and source history. The source-scope reporting discrepancy is not itself evidence of mutation or loss.
4. The R08 evidence sets price_plane_byte_conservation.row_conservation=false by comparing a 2014..2026 prefix against a 2026-only factor partition. This is an invalid comparison. Independently compare the source 2026 price keys/values with the 2026 output, and report full-prefix formula context separately.
5. R08 reports MARKET_STRUCTURE with 8 columns, whereas the earlier handoff described 14. The supplied writer projects exactly to the pinned parent's physical Arrow schema. Read both actual schemas and reconcile earlier statements. Do not add/drop columns merely to match either report.
6. Three reusable GitHub references point to nonexistent R04 source_contracts paths. Their real bodies are under R04/access_resources/source_bodies; use EXACT_EXISTING_SOURCE_BINDINGS.json in this review.
7. “Implementation-ready” is overstated while nine bindings remain unresolved and no newly required bodies were uploaded. The original R08 Section C requested those bodies now. Carry known facts from prior source packages forward, and supply only genuinely missing dependencies and their complete source bodies. Do not reset known stock RAW paths or validated credential locators to UNKNOWN.

## Source defect independently reproduced by GPT

The hash-pinned daily compiler's read_price_frame (c8ddf805..., function at line 249) looks for code/security/order_book_id/symbol, but not canonical_code. The R08 full-index schema has canonical_code and no recognized alias, so that exact reader skips the frame. It also recognizes money only, while the canonical source uses amount.

A fixture using the original function (AST extraction only; no compiler top-level import) returns zero rows. The supplied pure successor adapter preserves both rows, the null pre-inception quote, the canonical code, amount-to-money values and all remaining provenance. It does not create known_at or PIT/admission status. Ordinal dates, duplicate keys, ambiguous target aliases and incompatible price semantics fail closed.

This proves a code-path/schema incompatibility. It does NOT establish which exact historical publication used this function, or explain all missing consumer windows.

The supplied candidate adapter is not installed into production and does not authorize RAW fallback in backtests. R09 must integrate it into a contracted Cleaning successor with exact source manifests and anti-lookahead/coverage gates.

## Existing source bindings GPT resolved directly

The c8ddf805 daily compiler already contains build_release:
- ETF source branch at lines 422/439, PIT tagging and ETF output at 511.
- Full index source branch at 427/443, output INDEX_DAILY_R1 at 515.
The functions are located; the remaining question is their safe compatibility and the actual current writer's provenance, not absence of any writer body.

The full-history compiler (d72a74ad..., already on HUB) uses compile_one("INDEX",...) with an f"{name}_DAILY_PIT_R1" target, yielding INDEX_DAILY_PIT_R1 rather than catalog INDEX_DAILY_R1. That is a separate observable naming mismatch, not authority to silently alias products. It delegates parsing to the same incompatible reader. Neither legacy compiler may be rerun: both contain broad registry/publisher side effects.

## Scope and provenance cautions

Physical 732 files versus declared 154 files does not justify rewriting a sealed original MANIFEST from 154 to 732. First account for the original registered file/hashes and the additional files' provenance/authorization. Create an append-only reconciliation/successor if justified; no in-place correction is authorized. Likewise SET_CURRENT=false is not a grant to change authority merely because a gap release exists.

Do not repair ordinal factor dates from filenames alone, or treat constant factor=1 as proof of a valid adjusted-price series. Restore original request/sidecar or signed lineage evidence and exact per-symbol/time semantics before any factor repair.

## Supplied independent controls

r08_receipt_audit.py: independently reads the actual manifest, verifies its claimed SHA and all pinned files/artifacts, sums physical input footers, reads actual schemas, compares 2026 price values/keys and exact audit keys. It writes no data and invokes no build/replay.
test_r08_receipt_audit.py: six offline controls PASS.
canonical_index_schema_r1.py: pure candidate schema normalization, no I/O or publication.
test_canonical_index_schema_r1.py: nine offline controls PASS including the original-reader empty-result reproduction.
probe_canonical_index_r1.py: fixed, hash-pinned 399303.XSHE source read for local execution; no data writes.

FOUNDATION_ACCEPTANCE=false
ORDER_ALLOWED=false
NETWORK_ACQUISITION_AUTHORIZED=false
PRODUCTION_CHANGE_AUTHORIZED=false
