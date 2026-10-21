# BLACKBOX_INVENTORY_RECURSION_CHECKPOINT_20261021_0930

task: BLACKBOX_SYSTEM_INVENTORY_RECURSION_AND_SEMANTICS_20261021_0930
at: 2026-10-21T09:31:27+08:00
host: ZHANGWEI
SYSTEM_INVENTORY_ACCEPTANCE: false
status: PARTIAL_CONTINUE_CONTENT
elapsed_sec: 10.9

## Corrections applied
- 0905 edges dedup reconcile (expect ~1846 unique)
- True worklist recursion: enqueue+read targets (not visited-only)
- Rule ID index + bare ID tokens
- COMMAND_EXAMPLE_STATIC separation
- Lineage split: entity deps vs attributes vs unresolved structure
- ETF callchain via registry keys (not only __mat_ literal)

## Numbers
- semantic entity edges: 160 (attrs=12, unresolved_struct=8)
- recursion: queued=1003 read_ok=900 dedup_edges=135906 pending=103
- ETF: CALLCHAIN_CANDIDATES_FOUND_NEED_FRAGMENT_SELECT_PROOF (reader_like_files=2)

## Artifacts
local: `E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650`
hub tree: correction_0650/
