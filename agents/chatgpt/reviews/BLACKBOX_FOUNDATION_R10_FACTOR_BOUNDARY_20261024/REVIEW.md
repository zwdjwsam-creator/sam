# R10 rework review and factor boundary correction

Read receipt scope: agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/rework_2256/.

## Rework evidence assessed

Eleven retrieved files were independently checked against REWORK_DELIVERY_MANIFEST.json by exact UTF-8 bytes, SHA256 and byte count. All eleven matched: six top-level result/reference files, three stdout files, guide installation receipt, original AGENTS backup. The capture-directory listing also carries three zero-byte stderr blobs. No independent check of a final upload-readback receipt is claimed: that receipt was not present in the inspected directory at review time. Finish the existing upload/readback before starting this successor; do not restart or duplicate the previous task.

The actual 2026 query requested all six fields and returned 4/4 keys. The 2025 query returned 3/3 keys from the inherited 2025 partition. The stock update-plan ran in non-executing mode. Their real preflights report PASS.

The installation receipt reports the guide at E:\BLACKBOX\_OPS\CURSOR_WORKSPACE\BLACKBOX_LOCAL_OPERATIONS_R10.md with the reviewed guide hash, and preservation of the original 10991-byte AGENTS prefix. Its uploaded original backup has the independently verified hash 83a6c4aba8231a9ea2169990be2a7708eec9e1651d11acc03d05ece1f0a6d26b. The new AGENTS after-image was not independently downloaded, so prefix preservation is the local measured claim, not a reviewer re-measurement.

These are accepted bounded receipts. Whole-foundation, formal engine, pipeline and latest-update acceptance remain false/not verified.

## Correct over-broad statements without another inventory

B4's phrase "candidate does" must be scoped to stock daily and the particular demonstrated products. The two successful queries do not prove ETF, index, valuation or fund candidates have been materialized. Do not use a single raw_present=true for that entire mixed list.

The identified JQ strategy template and its readme satisfy identification for those artifacts only. Choosing/reconstructing an old strategy is not a new blocker to the present data-foundation repair.

The G5 local guide path includes an extra _OPS below the recovery work directory. Use the canonical installation receipt path above. No document reinstall or repeat query is needed for that reporting typo.

The update-plan carries historical copied labels, including a factor-derived calendar description and old gap language. The verified asof-versioned exchange calendar is the actual session authority. R07/R08 superseding evidence and the recovered stock candidate take precedence for those questions. Do not treat a historical plan field as a new missing-source verdict or executable permission.

## Concrete factor compiler defects found in an existing full body

The original cache_compiler_adjust_factor_pit_r1.py is already on HUB. Full-body review establishes:
1. flatten_factor and load_p1_history call pd.to_datetime on their date field without rejecting integer axes. Pandas interprets page ordinals as nanoseconds near 1970. Existing R08 evidence separately records ordinal-axis RAW units. This proves the parser is unsafe; it does not establish that this particular old compiler produced every later malformed cache.
2. jq_refresh_stock_factor calls get_price(fields=["factor"]) without an explicit fq argument. The applicable hard rule requires fields=["factor"], fq="pre" explicitly and prohibits relying on the omitted default. This is a contract violation even if a vendor's then-default happened to be pre.
3. Dropping invalid observations and drop_duplicates(keep="last") are not proof of a revision-precedence contract. The successor boundary rejects them instead of guessing.

The supplied pure successor rejects numerical/mixed/compact-numeric date axes, timezone/intraday ambiguity, null/nonpositive/nonfinite factors, alias conflicts and duplicate keys. Its request-spec function emits explicit fq="pre" but performs NO supplier call.

All-one factor values can be legitimate. They are not rejected solely because they equal one. Conversely a valid shape or all-one series establishes neither fq provenance nor historical PIT correctness. The helper adds no PIT/authority flag.

Sixteen offline controls passed, including two actual Parquet round-trips. These are review-host tests, not desktop proof.

## Fixed desktop verification

The supplied driver checks only three already identified RAW files and one CACHE 2026 factor partition. Paths and full SHA256 are fixed in code from existing R08 evidence. It runs the reviewed actual CACHE preflight via describe, then allows no side-effecting operation in the checking process. No credentials, supplier calls, date guessing, tree search, source writes or current switch. It reads only date/code/factor, uses a captured byte snapshot, and rechecks hashes afterward.

This check is deliberately not an all-layer absence search or a full count reconciliation. The ordinal files should be explicitly rejected at the new boundary; the valid-date tip may pass shape only. Cache date/code/field density remains a recorded observation rather than a universe-completeness certificate.

The original compiler is preserved and is not activated or hot-patched. This package supplies the tested reusable replacement boundary and measures it on existing inputs. Actual compiler integration, affected-history rebuild, 83503-row reconciliation and historical provenance remain open pending the measured results and the applicable source/transform contract. Do not mistake completion of this check for B1 closure.

## Next ownership and permissions

GPT owns substantive integration code and all rule decisions. Local AI stages exact files, runs the exact supplied commands and uploads literal results. It does not design replacement tests, repair sources, choose a duplicate winner or expand a scan.

All seven integration groups remain open at this review. New incremental acquisition stays forbidden until the required prerequisites are accepted. No schema-validation PASS, synthetic test, single-symbol read or exhausted round budget grants acquisition or publication permission.
