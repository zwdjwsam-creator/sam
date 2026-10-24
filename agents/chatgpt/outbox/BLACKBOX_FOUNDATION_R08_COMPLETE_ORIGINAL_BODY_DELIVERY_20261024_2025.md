# Complete R08 original-body delivery with the fixed exporter

Issued: 2026-10-24T20:25:00+08:00
Executor: ZHANGWEI
Slot: existing R08/10; two future execution deliveries remain. This is not R09 or a new inventory.

The semantic package is missing required original bodies. Its index says UPLOADED_THIS_BUNDLE for multiple files, but the GitHub tree contains only ten summaries/builder files and no source_bodies. A local read and SHA list do not transmit a body. Complete the existing delivery requirement, without rebuilding the semantic reports or searching again.

Read:
agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R08_EXACT_BODY_DELIVERY_20261024_2025/REVIEW_BODY_DELIVERY.md

## Fixed actions only

1. Stage the following three files under:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\reviews\R08\exact_body_export\
from agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R08_EXACT_BODY_DELIVERY_20261024_2025/

- export_r08_exact_bodies.py
  SHA256 8648825bee05502ab09003907d6920302c5ee5eed668cd473ee50ce90442463c
- test_export_r08_exact_bodies.py
  SHA256 62d4cdccfb29487188c4d4783f7a965cc85690a1c6b0b25d9658d7e1c3d8d371
- EXACT_SOURCE_EXPORT_SPEC.json
  SHA256 a6e2e4b308830c368cddf236268fa90db2558805999c21740306858ea5a2cd8a

Verify byte identity; do not edit code, spec, pins, expected sizes or source files.

2. From E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024 execute:
    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R08\exact_body_export\test_export_r08_exact_bodies.py

Only if the seven offline controls PASS:
    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R08\exact_body_export\export_r08_exact_bodies.py

The exporter reads only the fixed 23 file locators and checks the exact recorded hashes before writing the evidence packet. It executes none of the original files and performs no search/network request.
Expected output:
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\reviews\R08\BODY_EXPORT_20261024_2025\

A source mismatch, missing file or existing partial packet is a STOP: preserve the error, do not delete/reuse the packet, do not change the source or expectation. Report that exact issue; do not declare the original uploaded.

3. Upload ALL 24 generated files (23 *.body.json carriers + EXPORT_MANIFEST.json) to:
agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R08/exact_original_bodies_2025/

Use the already-authorized HUB transport. Supplier network calls/auth/downloads remain forbidden. Do not execute any exported script. The carrier JSON is ASCII and its base64 payload preserves the original bytes, including UTF-16 and CRLF; do not substitute a summary or re-encode the payload.

4. Read back EVERY carrier from HUB. Base64-decode payload_base64 locally; verify original_sha256/original_bytes against the fixed spec and verify carrier SHA against EXPORT_MANIFEST.json. A mere upload count or remote path string is insufficient.

Write BODY_DELIVERY_STATUS.json only after these checks, naming every exact HUB path, carrier SHA, decoded original SHA, bytes, remote readback result and captured commands/exits. Required totals: original bodies=23; generated manifest=1; all body readbacks verified=23; no missing carriers. Keep earlier R08 evidence unchanged. No broad rescan, new diagrams, new policy, index refresh or runtime integration is part of this task.

5. Update INBOX_FOR_CHATGPT.md to the verified manifest and status, preserving the semantic/receipt/R08 predecessors. Do not label the foundation accepted or operational; GPT must read the actual bodies first.

## Interpretation corrections to preserve

Read the review's eight qualifications. In particular:
- “no direct call/import” does not prove the full transitive route is unenforced;
- 15 gate names versus 40 reason codes is not a defect merely because counts differ;
- six-lane rules allow explicitly justified DEGRADED statuses; do not invent all-six-PASS;
- orphan directories are preserved, not a blocker by themselves.

No additional exploration or rewriting is needed to deliver these already-known source bytes.

FOUNDATION_ACCEPTANCE=false
ORDER_ALLOWED=false
PRODUCTION_CHANGE_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
NEW_DATA_ACQUISITION_AUTHORIZED=false

After successful upload and full remote readback, Cursor chat final response must be exactly:
END
