# ZHANGWEI - R4 rules compliance: preflight omission admitted, hard gates now measured

at: 2026-10-27T21:00:43+0800
scope: 2026-10-27 download sequence, host ZHANGWEI

## What I got wrong

I ran the live acquisition (1,114 supplier calls) **before** running
`blackbox_must_read_preflight_r1.py` and **before** reading the acquisition and
download rules. That is a kernel breach, not a style issue:

- KERNEL item 2/4: define TASK_CLASS, get `MUST_READ_PRECHECK=PASS` first.
- `blackbox_jq_incremental_download_hand_rule.mdc` item 1: read this rule + CURRENT
  JSON before any JQData download.
- `blackbox_download_must_clean_antileak.mdc`: the cleaning chain was never entered.

Evidence of the omission: there was no preflight record for 2026-10-27 at all; the
newest artifact under `运行/` was 2026-08-03. The 77/77 native gate was package-local
only and contained no preflight step.

The gates passing afterwards does not excuse the order. The order was wrong.

## Preflight, run now as a correction

    MUST_READ_PRECHECK = PASS
    TASK_CLASS = ACQUISITION
    KERNEL_STATUS = VERIFIED
    HAND_READ = NOT_SUFFICIENT
    TASK_EXECUTION = ALLOWED

BOOTSTRAP `704527e0...`, DATA_ACCESS `09035518...`, ACQUISITION `64ad956e...` all
VERIFIED. The three must-read contracts plus the incremental-download rule and its
CURRENT JSON have now actually been read.

## Hard gates, measured after the fact

| gate | result |
|---|---|
| PAGINATION_COMPLETE | **YES** - all 16 settled sessions: expected == returned, 0 missing, 0 extra |
| ORDER_DETERMINISTIC | **YES** |
| PAGE_BOUNDARY_STABLE | **YES** - 0 codes appear in two batches of one day |
| DUPLICATE_LOSS | **0** |
| SILENT_TRUNCATION | **0** |

Silent truncation detail: the ~5000 cap is per **response**, not per day. Largest
response is 80 rows; no response equals a known cap. Distribution is 1,082 responses
of 80 rows plus 16 tail responses of 22-26 rows.

I also have to withdraw my own first check: it compared the whole-day total against
5000 and claimed 16 hits. That comparison was wrong and is corrected here.

## What is still not compliant

Cleaning was **not** performed, and the rule requires CLEAN -> ALIGN -> anti-lookahead
-> CURRENT -> cache after a download. The reviewed R4 contract set
`CLEANING_ALLOWED=false`, so this is a scope boundary, not a silent skip - but it means
the output is **raw staging only**, never a data update, never a formal product.

No CURRENT pointer moved, verified against the pre-run hashes:

- `CURRENT_CLEANING_RELEASE.json` UNCHANGED
- `CURRENT_CACHE_RELEASE.json` UNCHANGED
- `DAILY_DATA_MANIFEST_CURRENT.json` UNCHANGED
- `DAILY_DATA_PLANE_CURRENT.json` UNCHANGED

So the omitted cleaning polluted nothing. That is a favourable accident of the
contract, not a defence.

## Absence discipline

2026-10-27 is `PARTIAL_BLOCKED` at 3,440 of 5,224 codes with 1,784 never requested -
never described as missing or absent data. ETF and index are `NOT_ATTEMPTED`, not
empty. The six zero-entry directories are declared-but-unpopulated slots; emptiness
was never read as source absence.

## Files

| file | bytes | sha256 |
|---|---|---|
| RULES_COMPLIANCE_R4.json | 6837 | `9a785e02529ad50454112295a012d326b43eadb41170bdb4662c9f952d82e418` |
| GATE_VERIFY_R4.json | 6052 | `a95a20df789956b9b887820d6adf308df771141214a9500b46806121f00061f9` |
| SILENT_TRUNCATION_R4.json | 557 | `2148d5d10ecc825cf034494cc2c2759838c1a528dcef6f12dc8ae031205018ad` |

Nothing in this step called the supplier, consumed quota, or wrote to E:.
