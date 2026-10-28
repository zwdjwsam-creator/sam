# Independent raw-body decoding review — 2026-10-28

Task: BLACKBOX_R5_PARQUET_BODY_HANDOFF_20261028
Execution host: ZHANGWEI. This is a GPT review, not a new local execution instruction.
Reviewed native snapshot: f9341ec274d2f344cfcfb2140c6ce548ab696a3d.

## Decision and scope

The exact four ZIP archives and both retained HUB-body references were independently read as real binary bytes, CRC/hash/length checked, and all1504 original Parquet bodies decoded. The accepted scope is raw storage identity, source field representation, code/date keys, actual nulls and source-to-ADMISSION position conservation. It is not external supplier quote truth, historical PIT admission, formal Cleaning or a release certificate.

The four ZIPs contain exactly1502 planned members,23448612 original payload bytes. No duplicate, missing or unplanned member was accepted. The other2 bodies are the retained R1 first80 and R4 failed80 originals; their exact hashes were verified, not regenerated or fetched from the supplier.

Decoded input117461 rows =117460 admitted +1 explicitly quarantined. All51 product/date cells remain accounted for. No duplicate product/date/code key, integer date axis, extra column, infinite numeric value or admitted live-OHLC null was found. All1504 frames have time datetime64[ns], code string representation, and12 float64 supplier fields. The only nulls are open/high/low in the retained600621.XSHG row for2026-10-27. Close, volume, money, paused, limits, avg, pre_close and factor contain no nulls. Raw paused observations:192 flagged and117269 unflagged; these are supplier values, not independently verified legal trading states.

All405 new quality receipts and1097 successful R4 quality receipts were independently reconciled against decoded bodies (row counts, returned keys, field null counts and paused observations). ADMISSION positions exactly partition every original source row. The retained failed R4 receipt has a failure schema rather than a successful quality object; only this exact known batch is handled through the existing79-admitted/1-quarantined contract. Its original remains untouched. A first extension of the GPT audit adapter failed on that schema; the failure is preserved in DECODE_R4_QUALITY_ADAPTER_FAILED.txt. The corrected full audit actually exited0, with the1097 successful R4 comparisons still required.

No new availability timestamp, suspension conclusion, price fill, factor adjustment or duplicate suppression was applied. The excluded600621 row is not a new usable price and is not an unrequested source gap.

## Native execution and delivery limit

The previously reviewed exact package, original DATA preflight,10 native byte-transfer controls and one capture all retain their observed exit0. Capture exit0 means byte handoff only. At this pinned snapshot REPORT, DELIVERY_MANIFEST and LOCAL_READBACK are present and the18 content-file identities declared by the delivery manifest match actual bytes. Native UPLOAD_READBACK.json has not yet arrived. GPT's own successful binary readback does not fabricate that missing native receipt or imply that the native chat has ended. Leave the current handoff active; do not rerun capture, interrupt upload or issue a duplicate task.

## Original R15 source review: candidate design must use actual behavior

Read original formal_cleaning_r15_build_and_seal_r1.py, blob3f79d833d2c469033ac119b26af20a2504a23e37, and r15_antileak_and_ssot_r1.py, blobec3e3a2b8473376219b8881cd4e14ca4a64dc79a, from the existing R05/R10 source handoff. No global inventory or source-absence inference was performed.

The original daily ingest_item places an existing raw/staged file under standard using the provided clean_rel and emits lineage. It does not decode/filter individual rows or supply an independently validated field/PIT transformation. Its full main hardcodes the2026-08-10 cutoff and an R14 parent, carries the parent's standard/quarantine tree, and includes optional CURRENT/HAND mutation. Its helper place_file can unlink an existing destination. Therefore executing that old full entry unchanged would violate the exclusive candidate and original preservation requirements. Reusing its bounded reviewed ingest semantics requires an exclusive destination and explicit handling of the already authorized row-position exclusion; it must not be described as proof of a newer coherent full release.

The old antileak checker passes on triple date equality when prior index PIT evidence is absent. It also reads CURRENT and its main requires a switched CURRENT before updating SSOT. This is not independent observation-availability/PIT evidence and must not be used to advance unrelated finance cutoffs or force PASS. It will not be run against CURRENT for this candidate preparation.

Next GPT work is the scoped candidate adapter and meaningful offline controls, bound to the retained actual dictionary/clean_rel/consumer contracts and original source hashes. The candidate must preserve admitted values and original lineage; record the one exclusion; reconcile input/output/excluded keys and dates; avoid assigning historical PIT from current capture time; and leave all production pointers unchanged. Only after that work is complete will GPT issue the separate reviewed native candidate command. Seven RCID publication defects and coherent-generation/non-regression/admission remain open; no publication is authorized here.

## Reproduction artifacts

RAW_DECODE_SUMMARY.json contains the source blob index, all51 cell totals, exact field/dtype/null observations and the deterministic per-file result digest. decode_all.py is the executed GPT-only analysis script referencing the already retained local R4/R5 receipts, immutable plan and binary archives. It is not a native task, does not query suppliers, and does not write production data. No new local-AI task was issued by this review.
