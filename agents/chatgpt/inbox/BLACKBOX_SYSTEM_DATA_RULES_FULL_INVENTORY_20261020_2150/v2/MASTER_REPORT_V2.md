# MASTER_REPORT_V2 — 2150/2345 实质盘点纠偏（PARTIAL）

- status: **PARTIAL_V2_REWORK_IN_PROGRESS**（纠正 V1 元数据错误；非全核验完成）
- host: ZHANGWEI · 2026-10-20T23:55:56+08:00
- V1 保留: `E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\deliverables`（SOURCE_OBSERVATIONS）
- 2145 只读入口: **未碰** · R9: **不重跑** · 无下载/策略执行

## 现在能用什么
- Cache CURRENT release: `BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439` asof=`2026-09-24`
- 规范产品枚举: **69**（catalog + release 目录）；含 **STOCK_DAILY_PIT_R1** 等真实产品行
- 优先产品逻辑抽样探针: `STOCK_DAILY_PIT_R1, STOCK_DAILY_RAW_PIT_R1, INDEX_DAILY_R1, ETF_DAILY_PIT_R1, FUND_NAV_PIT_R1, ADJUST_FACTOR_PIT_R1, STOCK_FACTOR_DAILY_R1, SW_L1_MEMBERSHIP_PIT_R1, SW_L2_MEMBERSHIP_PIT_R1, SW_L3_MEMBERSHIP_PIT_R1, FINANCIAL_INDICATOR_PIT_R1, MARKET_UNIVERSE_PIT_R1`（见 PRODUCT_COVERAGE_PROBES；粒度=样本文件，非全证券）
- 有限只读入口 STOCK_DAILY 双端点: 仍可用（2145 结案）

## 缺什么 / 不能宣称
- **不能**写 71/71 已下载齐全：item 层 DOWNLOADED=70，另有 FUND_PORTFOLIO_STOCK=`NOT_DOWNLOADED_MISCLASSIFIED_NAV_POINTER`；summary.downloaded=71 **与明细冲突**
- 多数产品尚未做完整日期/字段/证券覆盖；分钟/外源全量仍 UNKNOWN/索引级
- tip≈2026-09-24 vs 今天 2026-10-20 = 待增量，≠自动丢数
- catalog 有目缺失目录: **18**

## V1 错误纠正
1. AGENTS/Kernel 状态: V2=`ACTIVE` / `ACTIVE` · regression PASS=`True`
2. 链接解析: 分行+分类 edge_status；分布 `{'RESOLVED': 1410, 'RELATIVE_UNRESOLVED': 412, 'BROKEN_CONFIRMED': 72, 'NOT_A_PATH': 10, 'EXTERNAL': 25}`
3. 产品表: 与 V1 245 条观测分离；规范表见 CANONICAL_PRODUCTS.csv
4. 规则图: ACTIVE/CANDIDATE 全量分片在 `v2/shards/`（非仅 400 样本）

## 规则覆盖
- 索引规则: **8097** · 状态 `{'ACTIVE': 4, 'ACTIVE_CANDIDATE': 311, 'ARCHIVED_OR_SUPERSEDED': 90, 'UNDETERMINED': 7692}`
- 已扫含 **记忆盘** / **BLACKBOX_ENGINES**: `{'记忆盘': True, 'BLACKBOX_ENGINES': True, 'hand_hard_rules': True, 'data_dictionary': True, '契约': True}`
- ACTIVE 边 broken_confirmed: **72**

## 先修哪批（只规划）
1. 数据覆盖/分母: 纠正对外口径 70(+1 misclassified)；补 PRODUCT 逻辑核验队列；tip 增量另授权
2. 规则: 消化 BROKEN_CONFIRMED；统一权威
3. 策略/回测: 在 STRATEGIES_STATIC 上加深解析（本轮未跑）
4. 更新下载: 按 UPDATE_SOURCES_STATIC 受控验证（本轮未跑）

## 仍需多少核验
- 全产品日历对齐缺口、known_at、RAW_NONE 边界：未完成
- 归档规则全量正文：未完成（本地 V1 大文件仍在）
- 策略参数/宇宙逐项：STATIC 目录级

## 产物
- `E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\deliverables`
- shards: `E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\shards`
- tests: `E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\tests\parser_regression_2345.json`
