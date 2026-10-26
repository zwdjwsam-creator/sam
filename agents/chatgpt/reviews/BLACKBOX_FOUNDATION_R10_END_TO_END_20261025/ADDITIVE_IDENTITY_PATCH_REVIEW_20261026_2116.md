# Additive identity patch and new operating-guide review

reviewed_at_cn: 2026-10-26T21:16:01+08:00
execution_host: ZHANGWEI
task_id: BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025
dispatch_id: SAM_LED_DESKTOP_RECTIFICATION_20261025
status: PATCH_NOT_ACCEPTED_EXACT_DEPLOYED_SOURCE_STILL_PENDING
FOUNDATION_ACCEPTANCE=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false

## Evidence and scope

Pinned main tree: bdde7034ee3a84aacda7805200fd59eff4655d61, recursive response truncated=false. Checked R10 descendants as well as the lagging ChatGPT pointer. The exact deployed_source handoff requested at 19:09 remains absent from this tree. No new cleaned incremental result or desktop deployment of the new patch is certified.

Read full original bodies:
- sam_led_rectification/SAM_ANSWER_TO_DESKTOP_COMMIT_AUDIT.md, blob bd38995867c6cf5973f51fe529a6567482842720.
- sam_led_rectification/patch_release_content_id_r1.py, blob 2b69c39ac0bf3d04bfb23e4c4552fcd745b810fd (11,258 original UTF-8 bytes).
- agents/desktop/inbox/BLACKBOX_DESKTOP_RUNBOOK_20261026/START_HERE.md, b1648fc3a2ace9fefb5e0ad25ef6e30d03f021fe.
- BLACKBOX_DESKTOP_AI_RUNBOOK_R1.md, ef05bd24059083780472023e703a6c0f6757b869.
- DAILY_INCREMENTAL_RUNBOOK.md, 41fb2f7b81c961bb760231d21f0e16854df8318b.
- agents/chatgpt/inbox/BLACKBOX_NOTEBOOK_HUB_OPERATING_CONTRACT_20261026/DESKTOP_REPORT.md, 6b67e523fdc32356645ec616613199dad0f6cf3d.
Also read the existing 19:09 and 19:21 GPT reviews and current canonical outbox before acting.

SAM reports a local module changed to 29,588 bytes, f6f0d277 prefix, and a build_identity check, not an actual connected submission. This report and an anchor-based patch are not the deployed full body. No historical or desktop execution provenance is inferred.

## Findings from the actual proposed code

1. NOOP/checkpoint gap remains. The patch adds fields after the legacy commit_id is computed, persists optional fields in COMMIT, and adds a comparison in verify. It has no checkpoint or commit/NOOP decision replacement anchor. Therefore it does not establish the already-required shared full-scope transaction. In particular, verify hashes only commit["release_root"]; it does not compare that payload with the current compiler-bound candidate. The report's claim that bound and retained roots with different content are immediately detected is unsupported by this patch. Exact deployed commit/runner bodies remain necessary.
2. Digest failures are converted to a usable-looking identity. IDENT_NEW catches any non-CommitError and returns the legacy commit_id with release_content_id=None and an ERROR report. VERIFY2_NEW skips the full-content comparison when the stored value is falsey. A read failure must propagate, not downgrade the new scope to compatibility mode.
3. Dangling-directory links can disappear before the link audit. present_products calls is_dir() before _is_reparse. A broken directory link can therefore be omitted from both product scope and junction_audit. _is_reparse also catches OSError and returns False; unreadable readlink/unknown target is not a hard failure. This cannot certify the claimed dangling-target gate.
4. ALL_PRESENT still does not bind the declared delivered product set, required subset and optional presence states. It cannot replace the contract. Directory count 51 is a current observation, not a future admission rule. Required membership and identity coverage remain different concepts.
5. Legacy absence must be labeled legacy scope. It may remain historically inspectable but cannot satisfy new full-scope admission. Existing authorization already permits the versioned repair; no owner reapproval, historical rehash, old-seal edit or deletion is required.
6. The report recommends deleting or refreshing obsolete copies and rerunning verify while saying it resolves binding. Preserve old snapshots/zero-byte baselines as historical or failed evidence. A read-only verify cannot change the retained root. Do not select a candidate by lexicographic last directory as in the report's example B.
7. Patch idempotence is only a substring check ("release_content_id" anywhere => ALREADY_PATCHED). It does not establish complete application, version or integrity. An executable patch must pin exact before/after bodies and reject ambiguous anchors. No execution of this proposed patch on ZHANGWEI is issued here.

## Reviewer offline controls (exit 0)

Executed the literal HELPER_NEW and IDENT_NEW string bodies extracted by ast.literal_eval from the submitted patch. Top-level patch main was not executed, no production module imported, no supplier/auth/network call, only a temporary fixture directory. The local staging file carried one extra trailing LF; extracted AST string constants were unchanged.

- Broken-directory-link fixture: a symlink named REQUIRED_PRODUCT points to an absent target; is_symlink=True; present_products=[]; junction_audit={"junction_products":{},"dangling":[]}. Reproduced. Scope: Linux directory symlink, demonstrating the actual is_dir-first omission; not a Windows NTFS junction run.
- Digest-read-error fixture: release_content_digest raises PermissionError("fixture denied"); the actual IDENT_NEW returns {"commit_id":"legacy_id","release_content_id":null,"coverage":{"ERROR":"PermissionError: fixture denied"}} instead of raising. Reproduced.
- Static anchor inspection: HELPER_ANCHOR, IDENT_ANCHOR, COMMIT_ANCHOR, VERIFY_ANCHOR, VERIFY2_ANCHOR, VERIFY3_ANCHOR; no full-scope checkpoint/NOOP decision replacement.

These are rejection counterexamples, not a successful production integration certificate. Do not rerun existing successful pipeline/data stages to reproduce them.

## New runbook is navigation, not execution authority

The new guide repeats the old claim that daily_incremental without --run does not write. Inspected retained Research OS blob 5d7da7dab3b18828e594a5cf187da9ff4c450e1c: mode_daily_incremental(run=False) invokes the data-plane --mode status. Retained data-plane blob 41ea6597875bbee8778fe4db9ec0eddca8fe3576 has unconditional archive_daily/publish_current in main after collection. This establishes a hazard for the unpatched SAM path described by the guide; it is NOT evidence that the already-reported 46,492-byte desktop status/date fix regressed. Research OS --mode status is a separate branch and must not be conflated with daily_incremental without --run. Do not authorize arbitrary --mode status by flag name. Use direct JSON reads for current inspection; certify any executable status entry only against its actual deployed body.

The desktop report identifies incorrect conceptual JSON keys in the guide. Actual reported top-level keys are JQ, T_EXTERNAL, GLOBAL_SELLSIDE, DOMESTIC_RESEARCH, US_NEWS, US_MARKET; B/F are conceptual lane labels. That report alone does not prove complete JSON/schema or same-generation agreement.

The guide's fixed 300-second silence -> stop/resume instruction cannot override the owner's no-duplicate/no-interrupt rule. Silence alone does not prove a stalled process. Do not stop/restart an in-flight task or create another process solely because no report/progress appeared.

The new guide cannot revoke already-authorized local repair or broaden acquisition/publication. It also cannot replace original field-specific factor/PIT/source contracts. JQ stock/ETF canonical namespace remains JQ-only.

## Same-dispatch continuation

ZHANGWEI remains desktop repair owner. Keep SAM's source flow and existing completed stages. Finish the SAME seven-body exact handoff at commit_audit_20261026/deployed_source/ already specified in the 19:09 review; do not open a new global inventory or duplicate an in-progress handoff. If the local module changed meanwhile, supply the actual current bytes plus already-retained prepatch backup and mapping, rather than the patch generator alone. Reuse exact existing matching bodies. No additional data scan, successful pipeline rerun, Cleaning replay, supplier probe, deletion, dependency upgrade, production pointer or release write is requested.

GPT will author the precise patch and meaningful offline checks against those actual bodies, then specify the bounded desktop invocation. This review contains no executable repair/download command and certifies no admission. Historical outcomes remain intact.

Upload results and read back every file before ending Cursor chat with exactly END. All new HUB prose must be English; original identifiers/paths may be retained.
