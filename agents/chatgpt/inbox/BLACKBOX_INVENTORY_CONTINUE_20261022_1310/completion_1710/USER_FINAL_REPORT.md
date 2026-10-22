# 数据管理追加回执（1710）— A查询校验 + 覆盖合同矩阵

时间: 2026-10-22T17:20:54+08:00
reply_to: tip_1710 / completion_1655
SYSTEM_INVENTORY_ACCEPTANCE: **false**
PRODUCTION_CHANGE: 只读；未改规则/CURRENT/数据

## 1. A 查询方法校验（含 B 阳性对照）
- DB: `C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\FINAL_CANDIDATE.sqlite` SHA=53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d match=True
- schema: paths PK=`path`；另有 links/logical_view_42 等（见 SCHEMA_PATHS.json）
- **根因**: tip1655 对 B 报 `exact` 有行但 `prefix_n=0`——因 LIKE 未 ESCAPE 下划线，且 `\\%` 模式错误；**不是**子路径空。
- B 阳性对照（同一有效方法）: `prefix_glob_children` → n=20 sample_ok=True
- A 重查结论: **NOT_FOUND_IN_QUERIED_SCOPE**
  - exact/GLOB/range/instr(leaf)/跨表 instr(JQ20 任务名): 均无行（已查表见 JSON）
  - `D:\CURSOR_TASK_ARCHIVE` 目录 exact **有**行，但其下 GLOB 子路径计数=48
  - **不能**推断迁移丢失；仅 **NOT_FOUND_IN_QUERIED_SCOPE**（冻结计划 paths+列出路表）
- 分隔符: 库内为正斜杠? **否**，样本为 `D:\\...` Windows 反斜杠

## 2. COVERAGE_CONTRACT_MATRIX（75）
- 源账本: completion_1635 OBJECT_LEDGER_75（n=75）
- 每对象含: object_type / expectation(含 should_have 未定义项) / observed / delta_unknown_usage
- 三组详例: FUND_NAV、ETF_1m+ETF_5m、REQUIRED4 → COVERAGE_EXAMPLES_ABC.json
- 总体完整比例: **不计算**；缺独立预期不宣称完整也不宣称缺失

## 3. 最小后续核验（按使用影响排序 top）
1. `STOCK_DAILY_PIT_R1` score=45 type=ENTITY_TABLE_OR_PRODUCT exp=UNDEFINED_OR_UNKNOWN → locate independent contract/manifest before completeness claim
2. `ETF_MINUTE_1M_R1` score=33 type=ENTITY_TABLE_OR_PRODUCT exp=UNDEFINED_OR_UNKNOWN → locate independent contract/manifest before completeness claim
3. `ADJUST_FACTOR_PIT_R1` score=30 type=ENTITY_TABLE_OR_PRODUCT exp=UNDEFINED_OR_UNKNOWN → locate independent contract/manifest before completeness claim
4. `ETF_TRACKING_INDEX_MAP_R1` score=30 type=ENTITY_TABLE_OR_PRODUCT exp=UNDEFINED_OR_UNKNOWN → locate independent contract/manifest before completeness claim
5. `FINANCIAL_INDICATOR_PIT_R1` score=30 type=ENTITY_TABLE_OR_PRODUCT exp=UNDEFINED_OR_UNKNOWN → locate independent contract/manifest before completeness claim
6. `INDEX_CONSTITUENT_PIT_R1` score=30 type=ENTITY_TABLE_OR_PRODUCT exp=UNDEFINED_OR_UNKNOWN → locate independent contract/manifest before completeness claim
7. `INDEX_WEIGHT_PIT_R1` score=30 type=ENTITY_TABLE_OR_PRODUCT exp=UNDEFINED_OR_UNKNOWN → locate independent contract/manifest before completeness claim
8. `MARKET_STRUCTURE_DAILY_R1` score=30 type=ENTITY_TABLE_OR_PRODUCT exp=UNDEFINED_OR_UNKNOWN → locate independent contract/manifest before completeness claim
9. `MARKET_UNIVERSE_PIT_R1` score=30 type=ENTITY_TABLE_OR_PRODUCT exp=UNDEFINED_OR_UNKNOWN → locate independent contract/manifest before completeness claim
10. `SECURITY_MASTER_SNAPSHOT_R1` score=30 type=ENTITY_TABLE_OR_PRODUCT exp=UNDEFINED_OR_UNKNOWN → locate independent contract/manifest before completeness claim
11. `STOCK_DAILY_RAW_PIT_R1` score=30 type=ENTITY_TABLE_OR_PRODUCT exp=UNDEFINED_OR_UNKNOWN → locate independent contract/manifest before completeness claim
12. `STOCK_MINUTE_1M_R1` score=30 type=ENTITY_TABLE_OR_PRODUCT exp=UNDEFINED_OR_UNKNOWN → locate independent contract/manifest before completeness claim

## 边界
- 未另 hash 6GB 库、未建索引、未重验 R9、未联网、未启引擎、未全量重扫 parquet
- B 引擎目标接受现状；CURRENT 内旧 D 备份指针仅记历史，不改生产
