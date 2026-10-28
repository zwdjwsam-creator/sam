# OWNER REVIEW AID — NOT PART OF THE DELIVERY SET

This subfolder was added by the owner (ZHANGWEI) after the delivery closed, for
item-by-item checking of the R5 dispatch contract. It is deliberately kept out of
the return root so that `DELIVERY_MANIFEST_R5.json` still covers *exactly* the
delivered set (17 control files + 1,309 staging JSONs = 1,326 content files).

Nothing here is tool output. No gate, stream, exit code or staged file was
modified to produce it; every number in it was read back off the files that were
already delivered.

## What it contains

- `SECTION4_HUB_RETURN_CHECKLIST.md` — human-readable table
- `SECTION4_HUB_RETURN_CHECKLIST.json` — same content, machine-readable

## Numbering note

`TASK.md` has seven sections. "Section 4" is *Exactly one continuation command,
only after both gates*. The file return list is the seventh section, *Results,
uploads and END*. The checklist covers both.

## Self-reported gaps (stated up front, not hidden)

1. `WRAPPER_RUN_R5.json` did not exist when the delivery first closed: the
   precheck wrapper's own OS exit had been observed at run time but no separate
   external-capture receipt had been written. It was added afterwards under
   `../WRAPPER_RUN_R5.json`, carrying its own `provenance` block. The gate, the
   four streams and every exit code were left untouched and were not rewritten.
2. When the ledgers were first refreshed, `UPLOAD_READBACK_R5.json` was fetched
   before `DELIVERY_MANIFEST_R5.json` / `LOCAL_READBACK_R5.json` reached the
   remote, so those two rows briefly read `false`. They were re-fetched after
   upload and now read `true`; the final ledger is 1,328/1,328 `BYTE_EQUAL`.
3. Contract items 4.6 and 4.7 have no standalone pre-auth verification receipt.
   Their evidence exists only inside `BASELINE_R5.json`, `PLAN_R5.json`,
   `REUSE_MANIFEST_R5.json`. The R4 counts 3363 / 1098 / 1097 likewise have no
   summary field and must be counted from the reuse manifest. These are real
   gaps against the contract wording, reported rather than papered over.
