# P3 native candidate implementation: offline review complete, native execution pending

Task: BLACKBOX_R5_NATIVE_CANDIDATE_P3_20261101
Execution host: ZHANGWEI
Reviewed main baseline: 6cb1acef90e8b110948252bfd8877fad96049d6c
Original-body baseline: cd20535c23c99d6d3d1c9ea868117a8e91088caf

P1/P2 remain closed and cannot be rerun. This review grants exactly the separate candidate build in TASK.txt; it grants no supplier, P1 real-data activation, formal dictionary completeness, backtest, CURRENT, release or order permission.

## Package and real offline evidence

Stage only PACKAGE.json and its twelve payloads. PACKAGE.json: 1930 bytes, SHA256 937b37a3e467dce0ba7684bbe33cadf65fb4e339b524eeb2b18c6529e4f51b65. TASK.txt and this review are not runtime payloads. The outbox TXT and TASK.txt are identical.

Final source package passed 35 portable fixtures, no skip, actual process exit 0; a separate 42-test suite passed with actual process exit 0. The latter builds from all 1504 independently handed-off originals and independently compares all fourteen output fields and all 117460 admitted source-row lineage positions. Conservation: 117461 = 117460 + 1, stock 88811 / ETF 28530 / index 119, exactly 51 cells. Quarantine source bytes, physical position and null/value pattern remain exact. The original pure read_price_frame function, extracted from the pinned source without running/importing its entry, gives identical eight-field projections for all three products; no engine or observation/tradability admission follows.

The final native reader host/path branch was modeled against all 1504 actual pinned bodies. This is not native Windows execution. The frozen 51 full-value Arrow IPC hashes agree. The actual supplied packer produced six ZIP_STORED archives, 39441872 bytes in this offline run; all 125 members were independently reread and byte-compared to the candidate. Every archive is below 7500000 bytes. Native generation metadata/root can change Parquet bytes, so native archive sizes/hashes are measured anew; the invariant is full cell values plus source/manifest/receipt identity.

Manifest and failure controls reject source drift, dictionary-key drift, ns/unit mismatches, saved-index mismatch, non-JQ names, admitted nulls/infinities, duplicate keys, arbitrary quarantine exemptions, existing output, source-contained output, reparse paths, generation relocation and non-QA reads. A second-output injected failure is retained with FAILED and no BUILD_COMPLETE. The source-body audit records actual write-open events in the GPT process only; this is not a native system-wide audit.

## Development failures retained and fixed

The first 35-fixture run had five failures and three errors because a synthetic pandas fixture produced Arrow large_string. It is preserved under DEVELOPMENT_FAILURE streams. No actual subprocess exit receipt was retained for that initial run, so no OS exit is invented. The fixture now explicitly uses the already reviewed Arrow string/ns schema; production schema checks were not relaxed. Corrected and final signed-package runs pass.

The original acquire_r5.py source blob 498f7b9bc001a68dc544336aa283a985e29163e5 was desk-checked through its put() helper, not only call sites. put() appends _R5: E: ADMISSION_R5.json and REUSE_MANIFEST_R5.json are correct. A draft without the suffix was corrected before dispatch. No local source search or alias creation is needed.

## Semantic decisions and limits

The exact E: stock_daily domain row supplies twelve required names and symbol+trade_date keys; the 14-field native record additionally carries avg/pre_close. The stock view is an explicit reversible mapping of time/code, with every value retained. The CSV does not define numeric units or formal physical types: those remain UNBOUND. ETF/index normative dictionary rows are unbound; their candidate output is native-value QA only. lookahead_risk=false and date equality are not historical availability evidence.

No factor arithmetic, prices, timestamps, statuses or observations are filled. All 192 paused=1 OHLC/pre_close zero-volume/money rows remain tagged in measured per-cell facts; they are not inferred trades. The one 600621 row is retained as quarantine; two other admitted ETF zero-trade observations are not silently discarded. Factor=1 is a measured fact, not an adjustment or PIT certificate.

All four CURRENT JSON bytes are pinned and reread, but full CURRENT shard coverage remains uncertified. This candidate consumes no CURRENT prices and performs no merge, so it cannot silently double-stack historical keys. No publication permission is granted. The seven RCID defects remain open.

P1's signed modeling policy is not actual historical availability. P1 fixture acceptance remains sixteen PRESUMED plus 2026-10-27 UNRESOLVED; this task creates no P1 sidecar and cannot admit any strategy/backtest. Existing source/calendar/universe evidence is reused; no missing-data determination, new scan, supplier request or date extension occurs.

## Native execution contract

TASK_CLASS=DATA is an existing original manifest category, already exercised in P1/P2. Original preflight source and _base pins are unchanged. The launcher runs preflight, then all 35 supplied fixtures, then the actual E: candidate; every actual subprocess exit and UTC interval is captured. Markers outside result/candidate enforce single execution. Package/code/root bind generation. Existing output, a pin mismatch, reparse path, failed test or value hash discrepancy stops without repair/retry. Code and required original positions remain unchanged on the executor.

The executor must upload/read back ACK before launch, return every actual new receipt and candidate archive, read back every upload including its final readback receipt, and end Cursor with exactly END. Publication is not ACK/execution; only a later independent GPT audit can accept returned candidate results.

## R10 pointer-lag check

The stored R10 end_to_end_completion tree observation was stale. The current REPORT.md is the already reviewed R13 round-2 body c0ee01d8d1b6f33debfde3c62382fabe179f0fca, and ACCEPTANCE.json is already indexed in prior source reviews. Current B1/B7 status, final matrix, command ledger, run result, connected pipeline and package index were read again at the pinned baseline. R13 remains partial/blocked, supplier completeness UNKNOWN; the old R11 COMPLETED run is preserved history, not admission. No later foundation PASS, P3 ACK or native P3 result was inferred from those older files, and no R15 replay, factor repair, download or release is enabled by this task.
