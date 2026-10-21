# BLACKBOX 运行逻辑说明（隔离候选 · 0836）

generated_at: 2026-10-21T08:50:19+08:00
scope: inventory isolation candidate — NOT production AGENTS entry
SYSTEM_INVENTORY_ACCEPTANCE: false

## 1. 数据从哪来

- Cleaning CURRENT: `E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json` → standard_root = `E:\BLACKBOX\数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439\standard`
- 解析后 tip ETF 实际落点见各产品 `tip_resolved`（CURRENT 目录可指向 R45 tip release）
- Registry: `E:\BLACKBOX\规则库\data_dictionary\unified_market_data_plane_registry_r1.json` 中 ETF_MINUTE_* asset=ETF / relative_under_standard=price/ETF_*m
- RAW 替换根（registry）: P4_fund_etf_raw_none/fund_etf_price_*m
- Cache release（INDEX/FUND view）: `E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439`

### ETF 分钟（已读）

#### ETF_MINUTE_1M_R1
- tip_path: `E:\BLACKBOX\数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439\standard\price\ETF_1m`
- tip_resolved: `E:\BLACKBOX\数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R45_DAILY_TIP_ASOF_20260923_20260924_191823\standard\price\ETF_1m`
- tip files/rows/time: 12/2378160/2026-09-17 09:31:00→2026-09-24 15:00:00
- tip layout: {'day_shards': ['2026-09-17', '2026-09-18', '2026-09-21', '2026-09-22', '2026-09-23', '2026-09-24'], 'year_shards': [], 'name_token_sources': {'XSHE': 6, 'XSHG': 6}, 'layout_hint': 'DAY_TIP_SHARDS'}
- mat_path: `E:\BLACKBOX\数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439\standard\price\ETF_1m.__mat_13080` files=4352 sample_rows=10162799 time=2014-01-02 09:31:00→2026-09-16 15:00:00
- identity: tip=VERIFIED_ETF_CLEAN_PATH_READ predicate=`asset==ETF AND freq==1m AND fq_tag==raw_none AND path matches CLEANING_CURRENT relative_under_standard AND schema contains OHLCV keys; code-prefix NOT sole proof`
- old stock path: VOID — {'path_pattern': 'standard/finance/A股_stock_1m', 'status': 'VOID_HISTORY_DO_NOT_USE', 'reason': '0815 AUTHORITY_IDENTITY_UNVERIFIED stock minute misread for ETF'}
- coverage_note: TIP dir under CURRENT is day-tip shards (few files); .__mat_* holds year-batch history. Do not use tip file count as full history coverage.

#### ETF_MINUTE_5M_R1
- tip_path: `E:\BLACKBOX\数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439\standard\price\ETF_5m`
- tip_resolved: `E:\BLACKBOX\数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R45_DAILY_TIP_ASOF_20260923_20260924_191823\standard\price\ETF_5m`
- tip files/rows/time: 22/868656/2026-09-10 09:35:00→2026-09-24 15:00:00
- tip layout: {'day_shards': ['2026-09-10', '2026-09-11', '2026-09-14', '2026-09-15', '2026-09-16', '2026-09-17', '2026-09-18', '2026-09-21', '2026-09-22', '2026-09-23', '2026-09-24'], 'year_shards': [], 'name_token_sources': {'XSHE': 11, 'XSHG': 11}, 'layout_hint': 'DAY_TIP_SHARDS'}
- mat_path: `E:\BLACKBOX\数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439\standard\price\ETF_5m.__mat_8772` files=4348 sample_rows=2030226 time=2014-01-02 09:35:00→2026-09-09 15:00:00
- identity: tip=VERIFIED_ETF_CLEAN_PATH_READ predicate=`asset==ETF AND freq==5m AND fq_tag==raw_none AND path matches CLEANING_CURRENT relative_under_standard AND schema contains OHLCV keys; code-prefix NOT sole proof`
- old stock path: VOID — {'path_pattern': 'standard/finance/A股_stock_5m', 'status': 'VOID_HISTORY_DO_NOT_USE', 'reason': '0815 AUTHORITY_IDENTITY_UNVERIFIED stock minute misread for ETF'}
- coverage_note: TIP dir under CURRENT is day-tip shards (few files); .__mat_* holds year-batch history. Do not use tip file count as full history coverage.

## 2. 各层如何转换

- INDEX_CONSTITUENT: RAW strategy_data_plane_additions → Cache parquet；成分生效用 effective_from；announcement_date 实测全空；available_from_ts 非空但不得单凭字段名当历史可知时点。
- pit_status 分布（扫描 2592719 行）: {'ADMITTED_MONTH_END_SNAPSHOT': 2592719}
- current_backfill: {'False': 2592719}
- FUND_LIKE_ASSET_VIEW: VIEW.json 虚拟联合 ETF_DAILY_PIT_R1 ∪ FUND_DAILY_PIT_R1；非物化 parquet。
- view: {'unions': ['ETF_DAILY_PIT_R1', 'FUND_DAILY_PIT_R1'], 'preserves_asset_type': True, 'note': 'Consumer-side logical view; base tables keep ETF vs FUND'}
- FUND_DAILY_PIT_R1 / FUND_FACTOR_DAILY_R1: 空目录 NO_PARQUET ≠ 数据丢失（未物化/未发布）。

## 3. 规则入口如何约束查询/策略

- MUST_READ RULE_1 等: [{'line': 63, 'text': 'RULE_1 `INDEX_CONSTITUENT` ≠ `INDEX_WEIGHT` ≠ `FUND_PORTFOLIO_STOCK`。三者独立 product_id；成分表无 weight 不是异常，禁止生成 weight。'}, {'line': 68, 'text': 'RULE_6 官方权重不可用时禁止成交额/市值/相近指数/成分表代理。`WEIGHT_PROXY_FORBIDDEN=TRUE`。'}]
- Rules shards 真路径: `E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\shards` files=2 lines=315
- 0815 错 glob→0 已纠正: 0815 STAGE_LEDGER reported rules_shard_files=0 due to wrong glob root; true path E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\shards has 2 shards / 315 lines. 315 tip figure vs this count must be reconciled by candidate filter fields, not by absence.
- 策略静态依赖摘录见 STRATEGY_STATIC_0836.json（未启动回测）

## 4. 更新如何落地

- UPDATE_SCOPE edges: 28
- DAILY_MANIFEST edges: 55
- JQ incremental rule edges: 64
- published/generated_at vs asof_target vs covered_through: 见各 JSON 边 value；不足处标 UNKNOWN，不整表填满。

## 5. 未知 / 阻塞

- KEY/EXPECTED_SCOPE 全市场对照未在本轮穷尽 → 标未证实
- mat 年批全量流式续读可按断点继续（本轮已 sample）
- SYSTEM_INVENTORY_ACCEPTANCE 仍为 false

## 6. 续跑扩展（0836 continue）
- at: 2026-10-21T08:53:05+08:00
- product mapping matrix: n=75 status={'CACHE_MATERIALIZED': 48, 'NO_CACHE_DIR': 21, 'CLEAN_PRESENT_CACHE_PARTIAL': 3, 'CACHE_DIR_EMPTY_OR_VIEW_ONLY': 2, 'LOGICAL_VIEW': 1} → PRODUCT_MAPPING_MATRIX_0836.json
- rules edges content dump: 315 lines → RULE_EDGES_CONTENT_0836.jsonl
- update chain fields extracted from anchors → UPDATE_CHAIN_FIELDS_0836.json
