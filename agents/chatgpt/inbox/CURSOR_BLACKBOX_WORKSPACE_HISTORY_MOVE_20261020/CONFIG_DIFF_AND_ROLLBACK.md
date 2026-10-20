# CONFIG_DIFF

## paths.ps1
- D original: DualAIRoot = D:\CursorDualRouteConfig (unchanged on D)
- E copy: DualAIRoot = E:\BLACKBOX\_OPS\CURSOR_WORKSPACE
- secrets path still under cursor_ai_stack\secrets — secrets NOT copied; scripts needing secrets must use D secrets or re-provision locally (not uploaded)

## AGENTS.md (E:\BLACKBOX)
- Added 4-line pointer to _OPS\CURSOR_WORKSPACE README + HISTORY_INDEX; original rules preserved

## New files
- E:\BLACKBOX\BLACKBOX.code-workspace (folders: . and _OPS/CURSOR_WORKSPACE)
- E:\BLACKBOX\_OPS\CURSOR_WORKSPACE\README.md
- E:\BLACKBOX\_OPS\CURSOR_WORKSPACE\MIGRATION_HISTORY_INDEX.md
- E:\BLACKBOX\_OPS\CURSOR_WORKSPACE\migration_history_copies\*

## Rollback
1. Continue opening D:\CursorDualRouteConfig
2. Optional: delete only E:\BLACKBOX\_OPS\CURSOR_WORKSPACE and revert AGENTS.md pointer + workspace file
3. Do not delete D; do not touch C:\LAN_SHARE_REPORT frozen evidence
