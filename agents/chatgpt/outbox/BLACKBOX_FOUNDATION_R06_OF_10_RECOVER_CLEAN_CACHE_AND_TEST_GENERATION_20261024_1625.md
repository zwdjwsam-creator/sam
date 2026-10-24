# R06/10: recover the two known dates in a candidate and validate inherited data

HOST: ZHANGWEI
PREDECESSOR: BLACKBOX_FOUNDATION_20261024_R05
BUDGET_SLOT: 6/10
REMAINING_CYCLES_BEFORE_THIS_TASK: 5
REMAINING_CYCLES_AFTER_DELIVERY: 4
FOUNDATION_ACCEPTANCE: false
ORDER_ALLOWED: false
PRODUCTION_CHANGE_AUTHORIZED: false

## 1. Objective and authority

Execute the GPT-authored repair and tests below. The local operator may inventory/query the named evidence and execute exact supplied code; no autonomous code repair, new business semantics, version-winner selection or gate relaxation.

The two existing RAW dates must be restored to a NEW candidate CLEAN daily view and two candidate CACHE partitions, while retaining parent files and all non-target rows. Do not re-download them. This is a bounded repair, not an authorization to declare the entire foundation ready.

Read:
agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R05_REVIEW_R06_REPAIR_20261024_1625/REVIEW_R05_AND_R06.md

Stage the exact three supplied scripts into:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\reviews\R06
- r06_gap_repair.py
- r06_bundle_store.py
- test_r06.py

Verify git blob identity against HUB. Copy the exact predecessor GAP_REPAIR_INPUTS.json into reviews\R06\GAP_REPAIR_INPUTS_R05.json. Do not regenerate or edit its paths/hashes to make a test pass.

No network/API call, authentication, paid-module probe, purchase, global/historical environment change or production publish is authorized in R06. Reuse the successful bounded JQ evidence and dedicated runtime; do not spend quota again.

## 2. Run the supplied fixture suite before business reads/writes

From the fixed working root E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024:

```powershell
.\runtime\.venv\Scripts\python.exe reviews\R06\test_r06.py
```

Expected: 11 synthetic Arrow/parquet controls PASS. The suite writes only disposable temporary fixtures. No real data, engine or credentials are used. Save stdout/exit code/runtime versions.

It checks two-date recovery, inherited parent files, unchanged other product, non-target row preservation, candidate registry binding, idempotence, source preservation before fixture corruption, injected before/after-commit failures, stale-parent rejection and corruption rejection.

These are fixture failure tests, not a claim of actual Windows process-kill/power-loss recovery.

## 3. Run the exact bounded candidate repair

Only after the fixture suite passes:

```powershell
.\runtime\.venv\Scripts\python.exe reviews\R06\r06_gap_repair.py --gap-inputs reviews\R06\GAP_REPAIR_INPUTS_R05.json
```

The output is fixed under:
candidate_releases\R06\R06_TWO_DAY_RECOVERY_20261024

The script:
- snapshots the actual CLEAN and CACHE CURRENT bytes and verifies their logical pairing;
- resolves CURRENT standard_root rather than assuming that R45 is the active logical release;
- checks the exact RAW/sidecar hashes for 2026-08-31 and 2026-09-01;
- validates schemas, dates, row counts, duplicate keys and the existing unadjusted source identity;
- validates cache mapping against the observed adjacent 2026-09-02 unit, excluding only the lineage ID changed by this new candidate;
- carries forward the entire current stock-daily directory and adds exact RAW bytes using evidenced clean_rel paths;
- creates only the two changed year=2026 CACHE partitions, retaining all parent non-target rows;
- preserves unchanged products/years through explicit parent references in a candidate view;
- writes a diagnostic ecology registry and final candidate manifest only after the stated checks pass;
- leaves derived-factor/market-structure products DIRTY and other dependencies unverified.

If the recorded 949470-row parent partitions remain current, each new partition should contain 959896 rows (949470+5212+5214). Report actual conservation evidence rather than hardcoding the expected count into a success assertion. The supplied code derives conservation from the actual source/parent tables.

If source hashes, CURRENT pairing, adjacent mapping, unknown schema fields, parent duplicates, directory structure or pre-existing targets fail a guard, preserve the exact rejection and input evidence. Do not change code, fill unknown columns, delete a partial candidate, choose a convenient source revision or publish partial data. Continue the independent source collection in section 6.

This is a sparse candidate view: base data remain necessary. It is NOT a formal sealed full release. No original seal/certificate, quarantine, ledger or CURRENT file is rewritten. No file inherited by hardlink may be opened for writing or have its attributes changed. No cleanup of source, parents, temp, old candidates or evidence.

## 4. Idempotent replay and real diagnostic reader

If the candidate build succeeds, execute the same repair command ONCE more. Expected: ALREADY_BUILT_VERIFIED, no duplicate rows or new generation. Record output and unchanged artifact hashes.

Then use the candidate registry through the existing R05 diagnostic adapter:

```powershell
.\runtime\.venv\Scripts\python.exe -c "import json; from pathlib import Path; from candidate.r5.engine_adapter import EngineLocalValueProvider; m=json.loads(Path('candidate_releases/R06/R06_TWO_DAY_RECOVERY_20261024/CANDIDATE_MANIFEST.json').read_text(encoding='utf-8')); a=EngineLocalValueProvider(m['candidate_registry_path']); f=a.get_price('000001.XSHE','2026-08-28','2026-09-02',fields=['close'],fq='none',fill_paused=False); days=sorted({str(x.date()) for x in f.index}); assert '2026-08-31' in days and '2026-09-01' in days; print(json.dumps({'status':f.attrs.get('bb_status'),'dates':days,'rows':len(f),'scope':'candidate diagnostic; no MASTER admission'}))"
```

A legitimate additional revision/coverage rejection must remain a rejection, not an empty frame or a forced PASS. Do not relax the R05 reader. Preserve exact reason/details for GPT.

Do not activate the engine API helper as a whole package. Its remote import-time initialization is still uncorrected. R06 validates the candidate data path only, not full engine startup or formal ingestion.

## 5. Publication boundary stays candidate/fixture-only

r06_bundle_store.py implements one candidate manifest commit marker and coherent override resolution for consumers of that marker. Test it only through test_r06.py this cycle.

Do NOT invoke it on a real production location, legacy CURRENT files or the real R06 candidate store. No production pointer switch and no CANDIDATE_CURRENT switch on real business candidates this cycle. A candidate manifest is reviewable without making it the active system.

The original multi-file publisher remains unsafe until consumers are wired to a tested coherent generation boundary. A new manifest by itself does not make legacy independent-pointer readers atomic.

No claim that inherited factor products are fresh after filling missing price dates. No unconditional FULL_HISTORY_PRESENT, REQUIRED_FIELDS_OK, gap-free or all-product READY flags.

## 6. Batch the exact missing sources needed for R07

Use already-existing manifests/indexes and only the named source roots. No whole-database scan and no old-strategy reconstruction.

A. Upload the complete current body of:
E:\BLACKBOX\任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1\cache_compiler_daily_incremental_r1.py
The previous HUB file contains only excerpts. Record its actual hash; the earlier excerpt cites c8ddf805a6ddc998cda507f2aa5c92f27b13a43b5445e5bfed21477c5822f336, but a changed file must not be replaced by a pretend match.

Also include the directly referenced full helper(s) for read_price_frame, compute_factors, market_structure, source joins and write_static_registries if they live outside that body. Resolve exact imports/paths, not keywords.

B. Read the actual current dependency/product/schema/formula registries selected by that compiler and current resolver. Return:
- all registered product IDs and their actual root/sidecar/view status;
- dependencies affected by the two recovered stock dates, with lookbacks;
- the input columns and transforms needed for those derived products;
- whether RAW_PIT or another product carries required tradeability/factor/pre_close/ST fields and which domains remain unbound.
Copy only missing full normative/source bodies. Do not execute write_static_registries, the old compiler, its main/canary entry, capability fact generators, the old publication gate or any updater.

C. Provide NEXT_UPDATE_BINDINGS.json from existing source/configuration:
dataset/domain -> permitted endpoint/callable -> source credential locator ID -> local RAW scope/known watermark -> cleaning entry -> required CACHE product -> receipt/exception.
Reuse R03/R04/R05 findings and the successful JQ check. Missing dates/entitlement stay explicit. Do not infer universal starts, current availability for untested APIs, or a cursor from max(date).

The target for the later latest-data update must be derived from a verified trading calendar, the latest completed/available session and actual supplier lag. Do not use old CURRENT asof as a permanent upper bound. R06 only inventories that route; it does not download or choose arbitrary new APIs.

D. The existing August permission receipt now distinguishes paid-module denials from invalid factor/table names. Keep the paid-module skip seal and target requirement separate. Current access for skipped modules remains unverified; no entitlement change has been reported, so no repeat probe. Do not assign every abnormal/lock/subscribe leaf a paid denial based on a grouped summary.

E. Report the logical CURRENT release_id, standard_root, resolved realpath, cache source_cleaning_release and R45 parent relationship explicitly. Do not mistake the parent ledger/quarantine path for the active standard data source.

## 7. Single combined English delivery

Upload:
agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R06/
- ROUND_STATUS.json: slot 6/10, remaining_after_delivery=4.
- GPT_CODE_EXECUTION.json: exact supplied/source/output hashes, commands and exit codes.
- FIXTURE_TEST_RESULTS.json.
- REAL_REPAIR_RESULT.json with actual read/write scope and any guard failure.
- CANDIDATE_MANIFEST.json and small conservation/readback evidence (paths/hashes, not the large parquet files).
- IDEMPOTENCE_RESULT.json and REAL_DIAGNOSTIC_READ.json.
- DERIVED_DEPENDENCY_REPAIR_PLAN.json (facts/edges only; implementation_owner=GPT).
- NEXT_UPDATE_BINDINGS.json and complete missing sources from section 6.
- DELTA_REPORT.md: precisely what is repaired in the candidate and what remains dirty/unverified.

No additional round for individual missing artifacts. Complete independent branches and report blockers in this one package. Existing migration/26-domain evidence is reused, not rerun.

Update the top INBOX_FOR_CHATGPT latest/bundle/checkpoint to R06, upload and verify by readback. All new reports/comments/status are English; literal original paths/source evidence retain their language. Keep secrets local. Final Cursor response after successful HUB delivery/readback is exactly:

END
