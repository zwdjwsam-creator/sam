# SAM V3 capture and original daily-chain source review (2026-10-27)

execution_host: ZHANGWEI
notebook_evidence_host: SAM
dispatch_id: BLACKBOX_UPDATE_PREREQUISITES_20261027
status: BOTH_NATIVE_FIXTURES_PASS_SAM_PARTIAL_CAPTURE_RETAINED_CHAIN_SOURCE_RECEIVED
FOUNDATION_ACCEPTANCE=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false

Snapshot: 5e4a4b0e5d2439e86eeeb121f33f6489ab462920. INBOX_FOR_CHATGPT remains the old Q1-Q9 pointer; actual child/R10 paths were checked. Existing desktop native23/capture acceptance is reused.

## Actual results and independent byte checks

SAM native23 passed with actual exit0, followed by one unchanged collector actual exit2, and a separately recorded source-export step exit0. The exit2 remains partial: two exact R45 MANIFEST/SEAL paths were not found; lookup disclosed depth limits and one undecodable retained log. These are metadata/search limitations, not source-data absence. Do NOT rerun the collector, expand the bounded lookup or fetch market data to turn this into exit0.

The35 top-level manifest payloads, six capture-manifest entries and thirteen chain-source bodies independently match raw byte length/SHA256. The14-path handoff is thirteen captured bodies plus a reference to existing jq_download_base.py. A filename-only index contains27 immediate entries, without unknown-body reads. V1/V2 failures remain preserved. ACK-first ordering was violated: SAM discloses that the native gate preceded ACK upload, and that a separate agent session launched the collector after its parent shell wedged. Preserve that provenance; no fake reordered ACK or rerun is requested. Actual commands/streams and source identities remain reviewable.

## Material correction: the original cleaning input is now in hand

The exact ROOT D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924\DOWNLOAD_ACCEPTANCE.json has four items: calendar, stock daily, ETF daily, index daily. It is NOT the previously supplied 10_ACCEPTANCE sixteen-unit summary. It matches the schema that clean_switch reads. The former inference that the actual cleaning input had no items array is withdrawn for this ROOT file.

It records September24 stock5222 rows, ETF1661, index7 and calendar3097; raw paths, clean_rel and price-file hashes are present. Quota200000000 to199983130 means16870 units for this particular record, not the larger unrelated summary. These are retained receipt facts, not proof of supplier key completeness or current coverage.

The current generator-family body download_daily_r1.py writes this four-item format, so its data-to-cleaning path can be understood without inventing a new global workflow. Current bytes still are not historical execution attestation. Prior clean_switch parent/snapshot concerns are retained rather than erased.

## Independent daily-source review

download_daily_r1.py uses jq.get_price, RAW_NONE, an80-code batch loop and twelve explicit fields. This function DOES NOT explicitly pass skip_paused; do not borrow the older R15 minute writer's skip_paused=true as this daily writer's contract. Its universe is obtained by get_all_securities(stock/etf,date=GAP_END), and its code/date range is fixed to September24. It retries/re-authenticates on exceptions and writes directly to production RAW/calendar locations. Never execute it now merely by replacing dates.

The function only rejects a batch when returned rows reach its hard-coded5000 threshold; it does not persist the sent-code set, compare returned keys with requested keys, or retain page/exhaustion evidence. save_unit marks any nonempty frame PASS. AST-isolated checks against the supplied functions reproduce an ordinal0 time becoming1970, and a foreign-code/previous-date response being accepted and saved as PASS. No supplier or Parquet executed in those checks. Preserve the existing truncation safeguard; an eventual repair must use the applicable measured supplier contract rather than deleting a gate or assuming one universal limit.

The specific calendar writer calls get_trade_days ending at GAP_END and writes that particular RAW calendar file. This is evidence about THIS writer/file only; it does not erase earlier independently pinned calendars extending further. No global calendar-missing or automatic refresh conclusion is authorized.

Other supplied entry points show why the historical shell cannot be replayed: billboard/xr/minute-ingest/SW/align/republish paths can modify live cleaning trees, CURRENT pointers or publications. The picker selects a newest matching directory, can fall back to a directory without RELEASE.json, and then CURRENT; it is not an invocation-bound coherent-generation certificate. Receipt/key/observation-state, append-only destinations and exact Cleaning/PIT transformations must be authored for a scoped future update.

## Exact next source selection and ownership

The27-name index identifies run_unattended_catchup_r1.py. Its body was intentionally not read; the header/name alone does not establish it is the generator. The following exact read-only handoff selects that ONE source, without reading log/pid/watchdog/cleanup scripts or running it.

For precise candidate identity/transaction repairs, current live RCID product-contract and committed side-file identities must be compared with already-supplied original bodies. These originals ALREADY EXIST in desktop_rcid_v3. Matching live bytes require a reference receipt only, not re-upload. No repeated candidate_commit.py/runner/compiler handoff is requested.

The same-child closure task below requests only these3 exact files across the hosts. Existing native gates/captures and fourteen-source handoff are complete within their disclosed scopes; do not repeat them. GPT owns code/contract fixes after these bodies, not the local AI. First-scope RAW_NONE acquisition must not wait circularly for an unperformed update, production CURRENT or V4; however neither historical PASS nor nonempty batch currently proves applicable acquisition prerequisites.

All task boundaries remain: no password work, authentication/quota/probe, supplier call, download, rule/SSOT/CURRENT change, business module execution, release, migration, formatting, deletion, trading or order. Existing local reads/exports/uploads only; final Cursor response exactly END after all files are uploaded and read back.
