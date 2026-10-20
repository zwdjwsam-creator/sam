# R9 / BLACKBOX 迁移历史索引（可读）

更新: 2026-10-20（CURSOR_BLACKBOX_WORKSPACE_HISTORY_MOVE_20261020_1728）  
主机: ZHANGWEI（台式机） / 源笔记本: 192.168.100.2（SAM\ThinkPad）

## 用户目标与双机角色

- 将笔记本源数据迁入台式机 `E:\BLACKBOX` + `E:\BLACKBOX_ENGINES`
- 台式机执行；笔记本提供只读共享（含临时 `R9LP_RO`）
- 本索引供从 BLACKBOX 打开的新 Agent 查证，避免全盘扫描数百万路径

## FULL 技术验收（已结案）

| 项 | 值 |
|---|---|
| status | FULL_MIGRATION_TECHNICALLY_ACCEPTED |
| review | `agents/chatgpt/outbox/R9_FULL_MIGRATION_TECH_ACCEPTANCE_20261020_1625.md` |
| verification task | R9_FULL_READONLY_ACCEPTANCE_OPT_20261020_0830 |
| entities / checked / hash_calls | 1223767 |
| content_bytes | 365004696055 |
| file_paths | 8715072 |
| dirs / links | 233668 / 4824 |
| missing / extra / write_attempts | 0 / 0 / 0 |
| plan SHA | 53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d |
| copy digest | 27af138391d66219ebc6d03609cec6933aecfce3aacba48c215d5de9f14b2551 |
| verifier digest | 9e8c605df4a9cace1d048ffbade85f1b4684571983f88e2c43474058239ecbf0 |
| dest volume / unique id | 2694002743 / eui.E8238FA6BF530001001B448B42E694AE |

HUB review: https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/outbox/R9_FULL_MIGRATION_TECH_ACCEPTANCE_20261020_1625.md

## 关键修复与已知事项

1. FULL 来源映射与目标双根（BLACKBOX + BLACKBOX_ENGINES）  
2. WinError 1326 / 源会话与 deep share（`R9LP_RO`）  
3. 四个近极限长路径实体已 DONE（deep share + temp 工程边距）  
4. 验收 SQL：`MISSING_ENTITY` 由 parent_key SCAN 改为 item_key SEARCH（verifier 9e8）  
5. AS_IS_MIGRATE_MARKED：140 项版本疑点按原样迁移，不升级为“版本内容正确”

## 本机证据绝对路径（原位，勿搬 8GB 库）

- 冻结候选: `C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\FINAL_CANDIDATE.sqlite`  
- baseline plan: `C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite`  
- state（full_1938）: `C:\LAN_SHARE_REPORT\R9_DESKTOP_INTEGRATE_DEEP_SHARE_AND_STATE_CLONE_20261019\state\full_1938.sqlite`  
- 0830 包: `C:\LAN_SHARE_REPORT\R9_FULL_READONLY_ACCEPTANCE_OPT_20261020_0830\`  
- 可读副本（本目录）: `migration_history_copies\`

## 三条可核验真实记录（示例）

1. `migration_history_copies\FINAL_FULL_ACCEPTANCE.json` → `full_plan_acceptance=true`  
2. `migration_history_copies\COPY_COMPLETENESS_CHECK.json` → `missing_entity_count=0`，entity DONE=1223767  
3. `migration_history_copies\ACK_TECH_ACCEPTANCE_1625.md` → 技术验收结案 ACK

## 后续

- **不要**再跑全量 execute / verify-existing / 全盘 hash  
- 新业务写入或增量更新：单独任务、明确范围  
- R9LP_RO 临时 share 收尾：SAM 侧，不删业务文件
