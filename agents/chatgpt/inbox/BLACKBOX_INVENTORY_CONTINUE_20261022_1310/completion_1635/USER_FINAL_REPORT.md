# 数据管理阶段报告（1635）— 定向合并修正 / PARTIAL

时间: 2026-10-22T16:47:51+08:00
reply_to: tip_1635
SYSTEM_INVENTORY_ACCEPTANCE: **false**
status: PARTIAL

## 接受（不重读）
1618 对 FUND_NAV/ADJUST/BILLBOARD/STOCK_5M/JQ20文件分类/引擎文档声明的具体修正维持。

## 本轮修正
1. **REQUIRED4**：显式更新四对象（行数观察引用 completion_1447，非本轮重读）；orchestrator≠RAW；注册表两对象不再顶替
2. **语义字段**：停止 sample→independent_expectation / producer_entry→authority 自动填充；样例 FUND_NAV/ADJUST/STOCK_DAILY 已检查
3. **JQ20**：manifest 任务名 `BLACKBOX_JQ20_FULL_DOWNLOAD_PIT_CLEAN_CACHE_HAND_R1`；本地 D/E 任务树 **未命中**（D:\CURSOR_TASK_ARCHIVE 列表空/无该目录）；不读 FULL parquet；元数据行数保持历史声明
4. **引擎**：handoff D:\backtest_lab = 历史声明且 **当前不存在**；XVAL 路径 **当前存在** + 现算 sha；active_proven=false≠已停用
5. **上传**：先传齐关键件并 curl 读回，再更新 INBOX 指针

## 剩余确切未知（使用影响）
[
  {
    "id": "REQUIRED4_RAW_PRODUCER",
    "impact": "entity usable off-catalog paths; ordinary resolver rejects"
  },
  {
    "id": "JQ20_TASK_TREE_LOCAL",
    "impact": "cannot bind RAW scripts/receipts; cleaning/cache prior only"
  },
  {
    "id": "BILLBOARD_CLEANING_CACHE_DAILY",
    "impact": "RAW candidate only"
  },
  {
    "id": "ENGINE_ACTIVE_RUNTIME",
    "impact": "handoff/XVAL docs mapped; not live"
  },
  {
    "id": "INDEPENDENT_COVERAGE_CONTRACTS",
    "impact": "most products lack independent expectation proof"
  }
]

## 统计
{
  "REUSED_PRIOR": 3,
  "CANDIDATES_BOUND_STAGES_PARTIAL": 1,
  "PRODUCER_STATIC_REVIEWED_SEMANTICS": 16,
  "ENTITY_PRESENT_CATALOG_ORPHAN_RAW_UNPROVEN": 4,
  "PRODUCER_STATIC_REVIEWED_SEMANTICS_AS_PLANE_NOT_DOWNLOADER": 1,
  "KNOWN_UNLOCATED_DOWNLOADER": 2,
  "PATH_OR_PRIOR_PARTIAL": 1,
  "PRODUCER_LOCATED_BODY_PARTIAL": 4,
  "PRODUCER_STATIC_REVIEWED": 5,
  "LINEAGE_PARTIAL_TASK_DIR_UNLOCATED": 20,
  "RAW_PRESENT_ENTRY_PARTIAL": 1,
  "BLOCKED_CONFIRMED": 1,
  "UNLOCATED_WITH_SEARCH_EVIDENCE": 2,
  "STATIC_SCOPE_CLOSED": 14
}
