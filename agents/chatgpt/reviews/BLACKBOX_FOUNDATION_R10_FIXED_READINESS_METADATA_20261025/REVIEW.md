# R10 connected candidate desktop evidence review
execution_host=ZHANGWEI
Reviewed 2026-10-25, after the 02:30 delivery.

All 23 delivery members and the original manifest match the separately readable final byte-readback receipt: 24/24 lengths and SHA256 match. Literal stdout/stderr agree with the ledger: 11 tests, pass, exit 0, with genuine CACHE preflight PASS. No prior standalone suite rerun is required.
The guide preserves the entire 5,333-byte prefix and appends 1,432 bytes, producing 6,765 bytes. This documents a recovery-only synthetic diagnostic.
The actual response -> assembly -> merge source chain has been read. No publisher is called; PUBLICATION_NOT_AUTHORIZED is a deliberate boundary, not a production publish-gate result.

Reporting correction: receipt section 4 says assembly "drops non-dirty observed rows". Its actual source retains observed.loc[~observed.code.isin(dirty)]: it retains non-dirty observations and replaces dirty histories. Preserve the original receipt; carry this correction forward without code or historical-data edits.
The guide's caret continuation is cmd.exe syntax, not a PowerShell continuation. No execution failure is observed; do not replay tests or edit the guide just for formatting.

B1..B7 remain open. The next dependency is actual acquisition/cleaning metadata and checkpoint binding, rather than more synthetic gate checks. The existing R06 binding prohibits inferring a cursor from max(date); R08 says supplier lag is unmeasured. GPT cannot choose an increment range from the old cache tip.
The reviewed legacy jq_download_execution_r1.py contains unconditional P7 guard exits before its imports. Preserve those guards. Its checkpoint path is evidence only and is not automatically the active daily cursor.
The reviewed daily data-plane runner's status/default path still calls archive_daily and publish_current; it must not be used as a read-only status probe.

The fixed metadata-only capture package reads four identified JSON files and exports safe original bytes to a new recovery delivery. It does not import an updater, enumerate business data, follow paths inside metadata, determine source absence, select a cursor/target or call a supplier. Eight offline controls pass.
FOUNDATION_ACCEPTANCE=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false
