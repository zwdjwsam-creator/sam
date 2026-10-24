# Source-batch chain: independent desktop evidence review

Reviewed at 2026-10-25 01:35 +08:00. Execution host: ZHANGWEI.
Parent task: BLACKBOX_FOUNDATION_R10_DECLARED_SOURCE_BATCH_CHAIN_20261025.

## Verified evidence

All 30 DELIVERY_MANIFEST.json members were independently fetched from main. Recomputed UTF-8 byte lengths and SHA256 match every manifest entry, including original CRLF command captures. The delivered SUPPLIED_SOURCES package member hashes agree with PACKAGE.json and the existing reviewed package. Original source and input contract bodies were read, not executed against business data on the review host.

All four raw stdout/stderr captures agree with COMMAND_LEDGER.json lengths and hashes. The ledger reports successful staging, one 8-control run and one driver run; all exits are zero. Driver stdout and DRIVER_OUTPUT.json are byte-identical. Nested preflight capture exit is zero; decoded real_preflight equals the driver's reported object, with CACHE preflight PASS and verified BOOTSTRAP/DATA_ACCESS identities. Driver control flow installs the no-side-effects hook before declared business input reads and rechecks their identities at completion.

The delivered eight offline controls were independently rerun on the review host: 8 tests, PASS, exit 0. This supplemental run is offline only, not another desktop measurement or acceptance certificate.

Independently checked all 13 year results: exactly 2014..2026; source_rows = clean_rows = shared_keys for each; source-only, Cleaning-only and unequal shared factors all zero. The 182 batch observations sum to 12,176,722 rows, equal to the source and Cleaning year totals. Both original metadata documents parse identically to the driver output. Fifteen batches are empty, not certified complete.

Measured conclusion: the declared staged source and byte-pinned R26 Cleaning have identical validated date/code/factor content through 2026-08-14. The corresponding source-to-Cleaning content link is supported within that measured scope. No source data needs to be re-downloaded to establish this link.

## Limits and reporting correction

This does not establish supplier execution, historical expected daily universe, later-date coverage, factor known-at authority, or closure of the physical-minus-declared 83,503-row difference. Counts, file identities and the historical READY booleans are not substitutes for those distinct predicates.

C5 says Cleaning has no keys in the empty batch ranges. The supplied metadata does not bind a complete requested-code list per batch. Zero Cleaning-only keys in the full-year comparison establishes equality of the measured source and Cleaning; it cannot independently identify the securities requested by an empty batch or establish completeness of that batch. Preserve C5 as originally delivered and use this narrower interpretation. Do not reconstruct missing batch membership or infer source absence.

The earlier R08 cache_compiler_adjust_factor_pit_r1.py body is a different compiler: it reads legacy P1 plus a refresh and omits fq in the call despite the later hard rule requiring explicit pre. Its existence does not identify the producer of these R26 staged-source tuples. No execution, repair or historical metadata relabeling is authorized on that basis.

## Delivery status and deduplication

The INBOX pointer reports complete 31/31 byte readback. The 30 manifest members and manifest are accessible, but source_batch_chain/FINAL_BYTE_READBACK.json returned NOT_FOUND when checked in this review. This is a pending delivery observation, not a source-data failure. Do not duplicate, stop or restart the existing upload/finisher and do not rerun the successful desktop measurement.

No new executable task is issued while the existing delivery is still pending. Next: read its actual final readback when available, then reuse the existing R04-R10 universe/tradeability and acquisition/cleaning contracts to advance the remaining integration predicates. Do not order another factor inventory or repeat the 13-year source or basis comparisons.

FOUNDATION_ACCEPTANCE=false
FORMAL_ENGINE_ADMISSION=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false
