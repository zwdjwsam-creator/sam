# REPORT — CURSOR_BLACKBOX_WORKSPACE_HISTORY_MOVE_20261020_1728

host: ZHANGWEI
observed_at: 2026-10-20T17:35:11+08:00

## Mapping
- D source (retained): `D:\CursorDualRouteConfig`
- E ops dest: `E:\BLACKBOX\_OPS\CURSOR_WORKSPACE`
- Cursor main root intended: `E:\BLACKBOX` via `E:\BLACKBOX\BLACKBOX.code-workspace`
- C frozen evidence: left in place under `C:\LAN_SHARE_REPORT\` (no 8GB move)

## Copy
- 136 regular project files hash-matched (`COPY_HASH_MANIFEST.json` all_match=true)
- secrets excluded; D secrets not uploaded
- history readable copies + hashes: `HISTORY_COPIES_HASH.json`

## History retrieval from E
- PASS 4/4 (INDEX entities count, FINAL acceptance, COPY completeness, AGENTS pointer)
- See `HISTORY_RETRIEVAL_CHECK.json`

## Communication (separate verdicts)
| Channel | Result | Notes |
|---|---|---|
| HUB file | PASS | Unique ACK+package uploaded; inbox updated (this REPORT) |
| Official Browser GPT page | PASS (visibility) | Existing chat `接管迁移核验` visible; composer present; no browser test message sent |
| New E-root Agent auto-dock | NOT_CLAIMED | Opening brand-new Agent on E:\BLACKBOX was not substituted for this session; user may open `BLACKBOX.code-workspace` once |
| LiteLLM/API | NOT_RUN | Out of scope |

## File history vs GUI chat
- File/migration history: PASS (indexed under _OPS)
- Original Cursor GUI chat / login auto-follow: NOT automatic by copying project files

## Boundary vs 16:25 R9 acceptance
- No R9 re-execute / full hash / business data rewrite
- New _OPS management tree only; do not treat as EXTRA against frozen acceptance

## Rollback
See `CONFIG_DIFF_AND_ROLLBACK.md`
