# R10 reconciliation review and factor-generation comparison

## Accepted receipt, exact scope

All 16 manifest members of factor_reconciliation/ plus DELIVERY_MANIFEST.json were fetched and independently verified by exact byte count and SHA256 (17 identities). The supplied source matches the published package. Literal stdout/stderr and the two exit codes support the 17-control PASS and FIXED_FACTOR_RECONCILIATION_MEASURED. The driver used the real CACHE preflight and left source files unchanged.

The current 13 partitions contain 12,266,026 physical rows and distinct date/code keys. The COVERAGE declaration is 12,182,523. Their difference is physical_minus_declared=83,503, not 83,503 proved missing source rows. The declared and measured 2026 counts agree at 863,710. Subtracting that common subtotal assigns the aggregate discrepancy to the 2014-2025 residual, but does not identify a bad year or its cause. No count should be rewritten merely to match another count.

R26 Cleaning 2026 shares all 774,406 keys with CACHE 2026; CACHE has 89,304 extra keys. There are 13,199 unequal shared factors. These are two independent comparisons, not a causal explanation of the 83,503 discrepancy. Unequal factor levels do not by themselves prove unequal PRE_PIT prices.

## Contract-based numerical question

The already registered adjustment contract in R08/R09_IMPLEMENTATION_BINDINGS.json specifies:

    pre(d|T) = raw(d) * factor(d) / factor(T), d <= T

If, for a given security, f_cache(d)=k*f_clean(d) at every compared date and at the common anchor T, the constant k cancels. This is algebra, not a vendor provenance assumption. Conversely time-varying k can change normalized ratios. A common price is not needed to measure whether the factor ratios agree.

The new code measures, rather than assumes, the scale ratio for each security across observed common keys, including cross-year changes. It separately compares normalized factors at the explicit common anchor 2026-08-14. A floating relative tolerance of 1e-12 is declared. Missing common anchors are counted as untested, never filled. Records after T are also untested, so an August comparison cannot certify September data. A single common observation cannot establish constancy over time.

The code compares the same registered R26 factor product against the already pinned current factor product over their 13 observed year partitions. This adds a concrete Cleaning baseline per year for the historical count question. It never chooses a duplicate winner, modifies factors or proves acquisition history. Current CACHE hashes are all pinned by the newly accepted reconciliation. Only R26 2026 has a prior reviewed content pin; older R26 identities are explicitly newly measured, not admitted.

The old 2026-only comparison is not being repeated as a new discovery. It is the anchor and consistency control for the cross-year comparison.

## Source lookup boundary corrected

The last local lookup scanned 317 retained files. Its nine hits were quoted metadata, and it found no original source-body hit for the two literal strings. That evidence does not mean all 950 previously discussed source reads were present in that corpus, nor does it prove that no writer exists locally. Base64 body carriers also need decoding before a text search can inspect their payloads.

The next local instruction therefore allows one scoped source-code lookup in the three already identified code roots (scripts, tasks and runtime), for those same two literals. This is a newly explicit narrow lookup after the retained corpus did not bind the writer. It does not authorize a data-tree, catalog or whole-drive scan. A string hit is a source candidate, not proof of execution. Return original bytes or an existing HUB body reference and any already retained execution receipt; do not run a matched source.

## Controls and remaining requirements

Twelve offline controls pass, including real in-memory Parquet, constant scales, time-varying scales, per-security scale differences, cross-year scale changes, missing anchors, later dates, duplicate rejection and legitimate one-valued factors.

This evidence package can resolve numerical relationships and baseline identities. It cannot by itself close B1, grant historical PIT/fq authority, decide precedence or materialise an update. B2 through B7 remain tracked in the existing FINAL_BLOCKERS.json; none is erased or reclassified by this factor work. Acquisition, CURRENT changes, formal engine admission and orders remain disabled.
