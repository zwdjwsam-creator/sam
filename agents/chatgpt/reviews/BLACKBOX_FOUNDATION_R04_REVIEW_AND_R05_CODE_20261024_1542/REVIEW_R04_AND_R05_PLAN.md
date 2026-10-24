# R04 receipt and GPT-authored R05 execution code

Decision: accept bounded R04 patch execution and evidence delivery; FOUNDATION_ACCEPTANCE=false.
R04 plus its access supplement consumed one existing slot, not two. Next delivery is R05/10; six cycles remain before it, five after it.

## What was actually reviewed

R04 patch execution and delta, access supplement status, source register, access runbook, acquisition matrix and authority addendum.
Full bodies read for this decision: engine DataProvider base, domain/PIT admission matrices, ingestion gate, AMEND_R3, its CURRENT permission-seal summary, JQ download base and scope-refresh script.
The actual API source was retrieved and its injection, import initialization, auth, price forwarding, relevant exception handlers and settings paths inspected. This is not a claim that all 98 contract bodies or the complete engine have been semantically certified.

## Accepted and unresolved observations

- R04 normalized patch hashes match GPT outputs; the nine synthetic tests and three-day native diagnostic succeeded as recorded. Diagnostic reads are not MASTER admission.
- JQ and Tushare credential locators are documented on the desktop. This is not current authentication. JQ is CONFIGURED_NOT_VERIFIED; Tushare remains HISTORICAL_ACCESS_ONLY.
- RAW possesses both questioned dates (2026-08-31 and 2026-09-01). Do not re-download them.
- The CLEAN omission is observed in the reported scope. ACCESS_EVIDENCE EV-05 says 'CLEAN (and therefore CACHE)' lacks the dates: dependency alone is not a direct CACHE query. Correct that claim or attach direct existing CACHE evidence; do not invent independent confirmation.
- The runbook calls the historical E:\\BLACKBOX\\.venv interpreter without carrying the already-known broken desktop binding forward. Package directories existing there do not prove that interpreter works.
- The scope-refresh command writes SCOPE and a CURRENT child summary. It is not a read-only inspection command and must not be executed as the runbook's scope-selection step.
- HIST_END/asof in a summary is not the sole runtime download authority: the existing daily invariants say RUN_TARGET_TRADE_DATE governs runtime target and summary is not data-readiness authority. Do not permanently freeze latest-data updates to an old CURRENT asof.
- 'current_proof_count=4' mixes static inventory, policy text and actual local reads. None is current supplier authentication. Seven matrix entries marked VERIFIED_CURRENT_ACCESS are local rule/derived sources, not seven functioning remote data feeds.
- QMT live exclusion is policy scope, not supplier incapability; 'live only / not a history source' was not established by this inventory. Avoid that unsupported generalization.
- The factor amendment target and the August 13 permission-seal summary are not inherently contradictory: target requirement and denied capability can coexist. Retrieve the exact referenced permission receipt to establish the seal evidence. Keep target, current access and engine permission separate. No paid-domain reprobe or purchase is authorized here.
- R04-C06 overstates absence of conversion code: the candidate adapter has a conversion body behind a quarantine. Disabled/unverified is not the same as no implementation. Do not enable it based on the report alone.

## New independently reproduced API defect

Actual api.py has object injection in set_data_provider(). A new factory branch is not inherently required.
However api.py constructs a default remote provider at import, and get_price catches generic exceptions. Its _raise_if_not_implemented only propagates NotImplementedError.
Independent execution of those exact functions with a failing local provider returns an EMPTY DataFrame. This can mask the provider's fail-closed decision.

api_boundary_probe.py constructs a helper-only candidate source and executes exact API functions with controlled settings/logging and explicit provider injection. The fix propagates exceptions marked bb_admission_error.
Offline result: original rejection -> EMPTY_FRAME; patched rejection -> PROPAGATED; success control -> FRAME; factory calls=0.
This is a FUNCTION-PATH harness, not full API package initialization, a live engine, or all MASTER gate implementation.

## R05 reader changes, with exact R04 input hashes

build_r05.py creates a new candidate, preserving R04:
- ProviderReject gets a stable admission-error marker for the API boundary.
- File selection retains all overlapping builds; filename family/build time alone is not authority to discard a version.
- Differences across rank/build groups are exposed as conflicts, not only differences at the top rank.
- Unknown/unreadable coverage is not silently dropped before accounting.
- Expected dates are not clipped to the observed data watermark.

verify_reader_r05.py passed four independent synthetic counterexamples: version suppression, unreadable unknown footer omission, invisible unserved tail and different-rank conflicting values.
These changes can reveal more rejections than before. That is evidence to trace, not an instruction to choose the convenient file or fake a PASS.
Source identity, full domain-required field joins, adjusted prices, clock-grid coverage and all MASTER admission remain pending.

## Bounded source-access code

jq_bounded_access.py supports offline selftest and the separately authorized --live run:
- local credential parser handles current two-line and labelled formats, including colons inside a plain password;
- no original secret store or downloader is modified;
- at most one SDK auth invocation, one quota query and one ordinary RAW_NONE daily-bar call;
- no factor-value probe, no broad table query, no retry loop, no production data write;
- a 45-second subprocess deadline; only sanitized structured results retained;
- five offline controls passed, including no data call under the operational quota reserve and no exception-message leak.

The live check has NOT been run by GPT. It is the desktop's next explicitly contracted operation.
