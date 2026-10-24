# R03 review and GPT-authored safety patch

Decision: PARTIAL_PROGRESS_ACCEPTED; ENGINE_INGESTION_NOT_ACCEPTED; FOUNDATION_ACCEPTANCE=false.
Reviewed delivery: agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R03/.
This review does not consume a separate task cycle.

## Evidence read

R03 DELTA_REPORT, ROUND_STATUS, TEST_RESULTS, SYSTEM_STRUCTURE, RUNTIME_COMMAND; complete provider.py, engine_adapter.py, file_index.py, securities.py, errors.py, test_conformance_r3.py and build_registry_r3.py.

Reused earlier evidence:
- completion_1814/ENGINE_DATA_INTERFACE_R1.json and completion_1803/ENGINE_BASELINE_CHECK.json under agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/.
- Complete completion_1618/source_reads/FINAL_BACKTEST_ENGINE_AUTHORITATIVE_HANDOFF_R1.md.
- Complete completion_1507/source_reads/BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_HANDBOOK_CURRENT.md.
- Complete contract_scope_1145/CONTRACT_SCOPE_1145.json under the existing correction_0650 inventory.
- The repository tree listing is complete, not truncated (2,361 entries at observation).

The actual engine base/API/core source and master admission CSV/JSON bodies are NOT present in the inspected HUB tree. Summaries and method-name checks are not substitutes for those bodies. This is why this review does not prescribe an adjustment formula, event unit conversion, new engine factory or production gate relaxation.

## Accepted progress, within demonstrated scope

The desktop reports an isolated runtime and two bounded real-data checks (test checks 8 and 9). The daily June result is 21 rows against its loaded calendar. This is useful read-plane evidence, not all-domain completeness or PRE_INGESTION acceptance.

Important correction: the 10-bar intraday example and the synthetic event case come from check_3_time_filters(fixture_provider()), not from the real provider. DELTA_REPORT places the intraday result in a real-data section; that attribution is unsupported. Do not silently promote fixture evidence to a production data observation.

## Confirmed defects

1. engine_adapter._envelope_or_raise defaults to allowing PARTIAL, while strict_partial defaults false. Ordinary engine consumers are not required to inspect pandas attrs, and attrs may be lost by transformations. Incomplete prices can therefore reach consumers. This also violates the preceding R03 command's reject-before-return requirement.
2. provider.get_split_dividend excludes missing announcement dates under asof but never compares a known announcement date to asof. A future-announced row is admitted. The engine adapter calls this method with no asof at all; its event conversion cannot be declared PIT-safe.
3. The event reader records budget_skipped but did not put it into incomplete_reasons.
4. Requested optional fields such as factor can be unadmitted while status remains OK. More importantly, the existing daily admission row requires factor and pre_close; selecting only close does not waive the domain gate.
5. The June proof cannot establish other windows. Coverage expectations are clipped to observed_start/observed_end; a request beyond the observed watermark can hide its unserved tail. Intraday coverage checks dates, not the expected session/bar grid.
6. get_all_securities ignores its date argument and can report OK despite unreadable reference files; get_index_stocks reads only the final two entries, can swallow read failures and cannot establish historical membership.
7. Day/narrower-file priority over a year file is an implementation choice, not authoritative revision provenance. Earlier contract-scope evidence already records FAIL_CLOSED conflicts, not day-over-year. Newest build alone also does not establish historical knowledge.
8. Historical handoff declares several clock semantics NOT_DEFINED/PARTIAL. R03's 15:00/end-label policies must be reconciled with actual current contracts before engine admission. Do not mistake a plausible convention for an implemented contract.

## GPT-owned bounded patch

build_r04_patch.py and PATCH_INPUTS.json create candidate/r4 from exact normalized R03 inputs; R03 is preserved.
- Engine boundary always rejects non-OK/incomplete envelopes, failed field admission, unproven coverage and file-accounting failures. Caller flags cannot relax it.
- Reference-frame reads pass through that boundary.
- Engine index membership and corporate events explicitly reject pending their full historical/PIT/unit contracts. Direct diagnostic envelopes remain available.
- Event diagnostics exclude announcements after the supplied asof and report event file-budget failures.

This is a safety patch, NOT a complete engine gate or final provider integration. Coverage, adjustment, field joins, clock/session semantics and revision authority remain open. An OK diagnostic envelope is not a MASTER admission decision.

## Independent verification performed by GPT

verify_safety_patch.py extracts the actual methods with AST and uses synthetic pandas frames and parquet/index stubs. It does not import the engine, access Windows paths, contact a service or read business data.

Observed before patch: PARTIAL envelope returned; two events returned with one announced after asof.
Observed after patch: PARTIAL rejected even with allow_partial=True; only the already-announced event returned.
Nine focused checks passed: partial guard, future announcement, unadmitted requested field, unproven coverage, file budget, successful-envelope control, event budget reason, index quarantine and event quarantine.

Run the same supplied test on the desktop runtime and record scope honestly. Native engine import, full runtime validation and full contract reconciliation have NOT been performed by GPT here.

## Direction

Do not activate the factory or start an incremental append based solely on a dataset maximum date. Reuse the accepted R9 and 26 file-list checks. Recover the full applicable authoritative contract closure, interface/consumer source and existing update rules in one bounded R04 delivery. GPT will author the semantic fixes after reading those bodies; the local operator may inventory, copy evidence and execute this exact patch/test contract only.
