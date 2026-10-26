# Pending v2 and desktop round-two review

execution_host: ZHANGWEI
task_id: BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025
dispatch_id: SAM_LED_DESKTOP_RECTIFICATION_20261025
reviewed_at_cn: 2026-10-26T22:55:00+08:00
status: PENDING_V2_REJECTED_NOT_DEPLOYED_NO_NEW_OWNER_DECISION
FOUNDATION_ACCEPTANCE=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false

## Evidence

Pinned main tree cb362efa20cc1d3786d5f2a52d522dd16456b4e9, recursive listing complete. Current outbox and both machine inboxes read before this amendment. No requested deployed_source handoff is present.

Read the full PENDING_candidate_commit_v2.py, blob 9c4619b710945f2d35d00cf2617372d484f116b1, exact UTF-8 bytes=37725, independently calculated SHA256=f39f474caed658857984e6c551425cc0628b5f9d9657937e905870a747b1c79d. This is proposed code, not desktop live code.

Read RECONCILE_AND_FIX_DESKTOP_DEVIATION.md (06f3998644174e665a283f1a2b95c372b760ca7a), all three newly uploaded patch-generator bodies (cfba291dba6596cc0554b8b07f735cfd094a9703, 31c8c42a2f71f3012cdb82a2efe687bb0733c05f, 241a10029848a6573dcf979c98313f93c676db48), all seven desktop_verify_round2 manifest members and manifest 7bde5157f854883780e710fca7804cd8ecd0bf3a.

Independent UTF-8 byte length/SHA256 reconciliation is 7/7 MATCH (see adjacent JSON receipt). Hash computation ran in reviewer JavaScript with the standard SHA256("abc") known-answer check; it was not a Python pipeline/control execution. No new Python/NTFS/runtime integration test was executed this run. This distinction is deliberate.

Returned scripts do not retain a literal process command/exit ledger. The manifest's live module and COMMIT hash fields are null, and its commit_json_path omits end_to_end_completion relative to the script's actual COMMIT_FILE path. Its untouched=true flag alone is not a before/after digest proof.

## What the source establishes

1. Desktop's main blocker is correct. commit() lines 578-588, 612-622, 689-699 still decide/rewrite using the legacy three-product commit_id. Only the fresh-commit constructor persists the optional release_content_id. Rerunning identical stock content cannot make this a full-scope authoritative transaction. Build_identity additivity and equal fingerprints on four current roots do not test commit/NOOP or corruption detection. Preserve the decision not to rerun the whole chain.

2. More serious: v2's claimed full-content fingerprint omits linked content. Lines 102-129 explicitly do NOT hash junction bytes: they return target path, target_exists and an optional target release label, with sha256/rows/parts=None. Lines 185-192 hash kind + (sha256 OR target path) + rows + target_release_id. Thus changing a linked parquet while retaining its path and label produces the same contributed identity. target_exists is not hashed either. This is a static consequence of the exact function; no runtime mutation was performed. Thirty-six linked products are therefore reference-identity coverage, not verified content coverage. CONTENT_PROVEN must not be inferred from this rcid.

3. The physical-directory branch also weakens evidence: os.walk has no onerror callback; nested reparse directories are silently pruned; traversal stops at cap=200000 without a hard failure; metadata errors are ignored; byte-read failures hash the literal UNREADABLE marker. capped is not included in the outer identity. Different unreadable contents may become equal. Do not label this conservative fail-closed hashing.

4. Prior defects persist: present_products() follows is_dir before reparse detection; unreadable reparse/readlink becomes False/None; build_identity catches errors and returns release_content_id=None; verify bypasses full-content checking for a falsey stored ID. The 21:16 rejection remains applicable.

5. ALL_PRESENT still cannot substitute for declared product/partition membership. Excluding known _qa/build metadata is correct, and 52 directories including _qa reconcile to 51 data products. This does not justify retaining a three-product-only admission decision.

6. New duplicate-root records assert content_identical_to_reference=True on legacy commit_id equality (lines 224-233 and 638 onward), with no full-content equality check. Metadata-only scan_equivalent_dirs does not even filter by all_pass; it reports that field. Treat both as diagnostics, never identity admission. Adding sibling scans, duplicate logs or a sidecar does not repair the transaction.

7. HOST_SCOPE_MISMATCH tests drive existence, not host identity (lines 257-260). It rejects absent Q:, but two hosts both having E: still pass. A missing-drive example does not establish cross-host protection.

8. Existing checkpoint rewrite is a separate correctness concern in the actual proposed body: repair/rebound branches rewrite versions/<same legacy id>/CHECKPOINT.json before replacing COMMIT. The old COMMIT references that same path/digest. A failure in between can invalidate the prior reference. The new versioned transaction must use a fresh immutable checkpoint generation and one authoritative candidate reference swap; preserve legacy generations. This does not authorize production CURRENT.

## Interpreting the desktop report

One rebind followed by NOOPs is consistent with the retained fields; three different output roots are not three committed hops. The sandbox source explicitly calls build_identity/release_content_digest, not commit. Its JSON reports equal rcid for four outputs; due to item 2 this is not proof that all linked bytes were checked.

SAM_ROUND2_VERIFY_R1 uses regex/keyword existence checks; missing checks do not make its process exit nonzero. This is delivery/static screening, not semantic tests. DESKTOP_SCAN_EQUIV_PROBE reads nonexistent equivalent_count/count fields, leaving its own equiv_count=null despite nested identity_equivalent_count=3; Q-drive guard output is printed but not retained in the JSON.

The original seven-body exact source handoff remains necessary. PENDING v2 is a complete proposed file, so it need not be requested again. Desktop report says live candidate_commit.py remains 20732 bytes/7cb9417c; do not silently treat v2 as the deployment baseline.

## Same-dispatch disposition

No A/B/C owner selection is needed. The existing authorization covers a versioned full-data candidate identity while preserving old IDs/seals. A standalone RELEASE_CONTENT_ID.json is not sufficient unless the authoritative candidate checkpoint/reference and every verify/NOOP decision require and bind its exact version/digest. Waiting for incidental future data change also leaves today's defect open. Do not create that sidecar or install v2 under this review.

ZHANGWEI continues the same exact identified handoff requested at 19:09: actual deployed commit/runner/two compiler bodies and existing bound RELEASE/SEAL/CHECKPOINT, reusing matching already-delivered bytes. Finish an in-progress upload, do not restart or duplicate it. Supply actual source and existing receipts, not another source-search report, proposed identity-policy patch, sibling inventory, compile run or Cleaning replay. Preserve old failed evidence and pending patches without installation.

GPT will prepare the precise fail-closed patch and meaningful offline controls once execution-bound source/contract inputs are available. Do not expand into duplicate-directory management or rewrite SAM's working source flow. Do not run a 40-minute chain to populate optional fields. No supplier/download, production CURRENT/release, deletion, dependency upgrade or orders are authorized.

Upload results and read back every file before ending Cursor chat with exactly END. All new HUB prose must be English; exact original identifiers and paths may remain.
