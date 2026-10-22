# 数据管理阶段报告（1519）— PARTIAL / 具体语义落表 + 范围账本

at: 2026-10-22T15:24:51+08:00
SYSTEM_INVENTORY_ACCEPTANCE: **false**
PRODUCTION_CHANGE_AUTHORIZED: false

## 接受
AST 正文、publish_atomic 绑定、NAV navc 绑定、手册/inventory、REQUIRED4/orchestrator 诊断 — 保持；不重采样。

## 具体语义结论（已落 FINDINGS_LEDGER）
1. **KNOWN_GAP `MULTI_FILE_PUBLISH_FAILURE_WINDOW`**：多文件顺序写，单文件 replace≠整体原子；实验室三断言成立。不宣称生产已混代。
2. **CONFIRMED_BEHAVIOR `PRIOR_TIP_OVERRIDES_NEW_DUPLICATE`**：`(code,day)` keep=last 使旧 tip 覆盖新值（fixture 2→出1）。不擅自改生产；不宣称历史已错。
3. **ADJUST**：overlap/dirty/全历史回刷规则 **CONFIRMED_BEHAVIOR**；`publish_successor` 绕过 `publish_atomic`/FACTS → **KNOWN_GAP**；覆盖门完整阻断 **OPEN_TO_VERIFY**；恢复控制流已静态描述，运行 **NOT_RUN**。

外源 `EXTERNAL_PHASE_ACCEPTANCE_MATRIX`：字段→条件→动作（含 PARTIAL 永不升 PASS、PIT_GATE、硬编码 GATE PASS 等）。

## 75 对象账本（纠正 1507 缩略问题）
- 自 `PRODUCT_MASTER.csv` 重建；**保留 FUND_NAV prior full_read 6496121行 / 5980片**；`content_this_round_ran=NO` ≠ 历史未读。
- 按家族/共享入口合并绑定 update_axis（非 75 次重复读同文档）。
- 统计：{"n": 75, "update_axis": {"STATIC_REVIEWED": 75}, "update_tag": {"KNOWN_GAP_BYPASS_PUBLISH_ATOMIC": 1, "FAMILY_ORCHESTRATOR_POST_DOWNLOAD": 35, "N_A_META": 2, "KNOWN_GAP_CATALOG": 4, "N_A_MINUTE": 8, "FAMILY_SHARED_NAV_PLANE_OR_ORCHESTRATOR": 3, "CONFIRMED_BEHAVIOR_PRIOR_OVERRIDES_NEW": 1, "CONFIRMED_MANAGED_CHECK": 1, "N_A_CACHE_CATALOG_ENTRY": 20}, "entity_axis": {"STATIC_REVIEWED": 75}, "family": {"ADJUST_FACTOR": 1, "BILLBOARD": 1, "META_REGISTRY": 2, "REQUIRED4_CATALOG_ORPHAN": 4, "ETF_FAMILY": 3, "MINUTE_NOT_DAILY_CACHE": 8, "FINANCE_FAMILY": 2, "FUND_FAMILY": 4, "INDEX_FAMILY": 4, "JQ20_ENTRY_NOT_CACHE_CATALOG": 20, "OTHER": 7, "SW_FAMILY": 5, "CBOND_FAMILY": 14}, "known_gaps_catalog": 4}

## 主表引用
见 `MASTER_TABLE_REFS.json`（PRODUCT_MASTER / REQUIRED4 / handbook / inventory / independent review）。

## 剩余
见 `REMAINING_PRIORITIZED.json`。本轮**不**实施业务修复。数据完整性仍未证明；已审项有据关闭，未查项不靠「需运行」结案。
