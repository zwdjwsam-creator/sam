# TIP_1814 收口报告 — 字典字段对应 / 基线后范围 / 引擎真实接口
- at: 2026-10-24T13:55:08.739158+08:00
- FOUNDATION_ACCEPTANCE=false  PRODUCTION_CHANGE_AUTHORIZED=false

## 0. 已接受、本轮不再做
- 26 域 RAW 文件集：1803 逐路径 exists，missing=0（不复扫、不重计数）
- 目录分支：已由 GPT 压缩为 66 条，本轮不迭代

## 1. 字典字段对应（按数据集/模式版本分组）
| 组 | 范围 | 契约必需字段 | 源实读列数 | 引擎准入域 | 结论 |
|---|---|---|---|---|---|
| G01_SECURITY_MASTER | security_master / securities_* / fund_etf_master / index_master | 5 | 6 | benchmark_data | MATCHED |
| G02_STOCK_DAILY_OHLCV | stock_ohlcv_daily (P2_stock_daily) | 12 | 14 | daily_bar,tradable_status,adjustment_factor,matching_requirements | MATCHED_WITH_PROVEN_CONFLICTS |
| G03_STOCK_MINUTE | A股_stock_1m/5m/30m/60m (P7_*) | 14 | 8 | minute_bar,matching_requirements | MATCHED_WITH_PROVEN_CONFLICTS |
| G04_ETF_PRICE | ETF_1m/5m/30m/60m + ETF 日线 | 12 | 8 | daily_bar,minute_bar,tradable_status | MATCHED_WITH_PROVEN_CONFLICTS |
| G05_INDEX_PRICE | index_components/weights + 指数日线/分钟 | 12 | 15 | benchmark_data | MATCHED_WITH_PROVEN_CONFLICTS |
| G06_ADJUST_FACTOR | adjust_factor (P1_adjust_factor / P2_security_state) | 2 | 4 | adjustment_factor | MATCHED |
| G07_TRADABLE_STATUS | stock_st_status / stock_limit_pause_status | 4 | 5 | tradable_status | MATCHED_WITH_PROVEN_CONFLICTS |
| G08_VALUATION | valuation (P6_factor_reference/valuation, 52 files) | 11 | 19 | - | MATCHED |
| G09_FINANCE_PIT | fundamentals_pit (P3_finance_pit income/balance/cash_flow/indicator) | 15 | 9 | - | MATCHED_WITH_UNRESOLVED_CONTRACT_GAP |
| G10_ETF_FUND_NAV | ETF_NAV / open_fund / QDII / other + ETF_SHARE | 4 | 4 | - | MATCHED_WITH_PROVEN_CONFLICTS |
| G11_INDEX_MEMBERSHIP | index_components / index_weights | 6 | 3 | benchmark_data | MATCHED_WITH_UNRESOLVED_CONTRACT_GAP |
| G12_INDUSTRY_CONCEPT | industry_concept / industry_concept_events | 4 | 2 | - | MATCHED |
| G13_MTSS_MONEYFLOW_BILLBOARD | mtss / money_flow / billboard | 8 | 9 | - | MATCHED_WITH_UNRESOLVED_CONTRACT_GAP |
| G14_CORPORATE_ACTIONS | corporate actions / XR_XD event | 11 | 4 | - | EVIDENCE_INSUFFICIENT |
| G15_FACTOR_260 | factor dictionary/formula/cleaning/pit (260) | 4 | 10 | factor_dictionary,factor_formula,factor_cleaning_rules,factor_pit_rules | ADMITTED_DICTIONARY_ONLY_BY_ORIGINAL_RULE |

### 具体冲突（已定性，不返工）
- **C16_VOLUME_DTYPE**（DTYPE_DEVIATION）：RAW volume=double，09 dtype 契约要求 int64 且 forbidden float
- **C17_DATE_TYPE**（DTYPE_DEVIATION）：RAW date=timestamp[ns]，契约要求 date/YYYY-MM-DD
- **C18_PAUSED_BOOLEAN**（CLEAN_LAYER_DERIVATION_NOT_CONFLICT）：RAW paused=double(0/1)；12_status 契约禁止 clean 层强制 boolean，最终语义用 halt_status/risk_warning
- **C1_MINUTE_MISSING_FACTOR_LIMIT_PAUSED**（DERIVATION_REQUIRED_FROM_DAILY_PLANE）：26域分钟 RAW 实读全部 8 列 (time,code,open,close,high,low,volume,money)；20_freeze minute_price 要求 factor/high_limit/low_limit/paused，引擎 minute_bar 要求 factor，matching 要求 factor
- **C2_MINUTE_SCHEMA_EVIDENCE_ROOT_MISMATCH**（EVIDENCE_SCOPE_OVERREACH_CORRECTED）：13 清单的 12 列分钟 schema 取自 JQData_9999_WINDOW_FULL_RAW_20260325_20260501（该目录自带 DO_NOT_USE_AS_MASTER），与 26 域 P7 分钟的 8 列不同
- **C3_ETF_MINUTE_SAME_AS_STOCK**（DERIVATION_REQUIRED_FROM_DAILY_PLANE）：ETF 1m/5m/30m/60m 同为 8 列，缺 factor/limit/paused
- **C4_INDEX_MINUTE_8_COLS_PLUS_FQ**（DOCUMENTED_LIMIT_NOT_GAP）：指数分钟 9 列（8 价格列 + fq），仍缺 factor/limit；指数无 tradable_status 语义，不作缺口
- **C15_IS_ST_WIDE_VS_LONG**（LEGACY_DUAL_REPRESENTATION_CLEAN_TAKES_LONG）：P2_security_state/is_st 宽表（列名=代码，数千列）；stock_st_status 为长表 (date,code,is_st)
- **C5_FINANCE_NAMING_INCONSISTENT**（CLEAN_ALIAS_REQUIRED）：income/balance/indicator 用 statDate/pubDate，cash_flow 用 pub_date/report_date/report_type；契约统一为 pubDate/statDate
- **C6_FINANCE_DUPLICATE_STATDATE**（DUPLICATE_COLUMN_DEDUPE_REQUIRED）：balance/indicator 同时存在 statDate 与 statDate.1
- **C7_REVISION_CHAIN_NOT_IN_RAW**（CONTRACT_AHEAD_OF_RAW）：PK 契约 symbol+report_period+type+revision_version，RAW 无 revision_version；08_restatement_schema 为契约而非已实现链路
- **C8_NAV_TWO_NAMING_FAMILIES**（CLEAN_ALIAS_REQUIRED）：fund_etf_nav/open_fund/qdii = unit_net_value+acc_net_value；fund_fund_net_value = net_value+sum_value+factor+acc_factor+refactor_net_value
- **C9_DAY_IS_STRING**（DTYPE_DEVIATION）：day 实际为 large_string，dtype 契约要求 date/YYYY-MM-DD 且禁止 string_mixed
- **C10_INDEX_WEIGHTS_NO_MEMBER_CODE**（CONTRACT_GAP_BLOCKING_PK）：index_weights 实读仅 (date,weight,display_name)，无 component_code/member；PK 契约要求 index_code+member_code+weight_date
- **C11_INDEX_WEIGHTS_SINGLE_SNAPSHOT**（COVERAGE_BOUNDED）：P3_index/index_weights 仅 1 个 snapshot 文件 (20260831)，无历史序列
- **C12_MTSS_FIELDS_INCOMPLETE**（SOURCE_FIELD_GAP）：stk_mt_total 缺 fin_refund_value / margin_value / margin_sell_value / margin_refund_value（契约 mtss 必需）
- **C13_MONEYFLOW_PAID_MODULE**（KNOWN_GAP_KG18）：KG18 money_flow 基础版为 paid_module；本轮未见 money_flow RAW
- **C14_NO_LONG_FORMAT_CA_TABLE**（EVIDENCE_INSUFFICIENT）：以已枚举 schema 无法确认 announce_date/ex_date/action_type 长表；adj factor 的 ex_date 可追溯性因此无法验证（13_adj_factor_methodology 规则2 → review_required）

### 证据不足
- G14_CORPORATE_ACTIONS：已枚举 schema 中无 announce_date/ex_date/action_type 长表，adj_factor 的 ex_date 可追溯性无法验证 → 按 13_adj_factor_methodology 规则2 记 review_required

## 2. 基线后与外源范围
- P5_jq20_extension：20 个 dataset 目录，全部有 receipt/sidecar/checksum 结构；与 21 增量清单比对：缺 无，多 无
- FUND_ETF_NAV 增量：13775 parquet / 13775 sidecar / 13750 checksum，日期 token 20260713..20260924

| 根目录 | 归类 | 依据 |
|---|---|---|
| 途施可转债官方原始_R1 | EXTERNAL_VENDOR_SERIES_OUTSIDE_JQ_FOUNDATION | 20_freeze KG06 可转债=out_of_scope（不在 9999 套餐）；本目录为 Tushare 供应商 receipt 序列，非 26 域 JQ 清洗输入 |
| 途施可转债官方原始_R2 | EXTERNAL_VENDOR_SERIES_OUTSIDE_JQ_FOUNDATION | 同上；R2 为 R1 续跑批（carryin_* receipt），属同一外源序列 |
| 外部补充只读 | DICTIONARY_EVIDENCE_SUPPORT_NOT_VALUE_DATA | 内容为字典交叉核验/冲突复核（01_inventory..06_evidence_consolidation），不含 26 域值数据；按 20 契约只作字典置信度补充 |
| 外部证据 | SEPARATE_EVIDENCE_PLANE_OUTSIDE_RAW_FOUNDATION | 每个产品自带 PRODUCT_META.json；属研究证据平面，不是 26 域 RAW 清洗输入；本轮不重扫 |
| 美国市场 | EXCLUDED_BY_ORIGINAL_RULES_KG02 | 20_freeze KG02 美股行情=out_of_scope；本目录为研究旁路，非 JQ 底座 |
| JQData_9999_WINDOW_FULL_RAW_20260325_20260501 | HISTORICAL_EXPERIMENTAL_WINDOW_DO_NOT_USE_AS_MASTER | 目录自带 EXPERIMENTAL_TRIAL_DATA_DO_NOT_USE_AS_MASTER.txt；仅作窗口/字段证据来源，不作 MASTER |
| strategy_data_plane_additions | FORMAL_POST_BASELINE_INHERITANCE | 每个产品含 REL_*/MANIFEST/COVERAGE/PROVENANCE/CHECKSUMS 发布结构；属基线后正式继承，非 26 域原始下载 |
| 聚宽行情_raw | LEGACY_PRE_BASELINE_RAW_CLASSIFICATION | 旧中文分类目录；26 域正式清单对应 P2_stock_daily/P7_stock_minute，本源不作正式输入 |
| 聚宽财务_raw | LEGACY_PRE_BASELINE_RAW_CLASSIFICATION | 26 域正式清单对应 P3_finance_pit |
| 聚宽ETF_raw | LEGACY_PRE_BASELINE_RAW_CLASSIFICATION | 26 域正式清单对应 P4_fund_etf/P4b_fund_expand |
| 聚宽因子_raw | LEGACY_FACTOR_REFERENCE_ONLY | 因子值下载按 DATA_INGESTION_GATE_RULES_R1 仍为 forbidden；仅字典/参考 |
| 聚宽行业指数_raw | LEGACY_PRE_BASELINE_RAW_CLASSIFICATION | 26 域正式清单对应 P0_meta + P3_index |
| _forensic_canary | AUDIT_ONLY_NOT_FOUNDATION | 审计用途，非数据底座 |
| 试验 | EXPERIMENTAL_NOT_FOUNDATION | canary 试验，不作正式输入 |

## 3. 引擎本体与值数据接口
- pyproject：`bullet-trade`，script `bullet_trade.cli.main:main`，包 `bullet_trade*` + `helpers*`，py-module `jqdata`
- provider 工厂 `_create_provider` 仅有：jqdata, tushare, qmt, miniqmt, qmt-remote, remote-qmt, remote_qmt；本地值数据分支=False
- local_dictionary_registry：字典快照纯读取，拒绝 E:\ 与 SEALED_SANDBOXES，CAN_BE_OFFICIAL_RULE_BASIS=False
- 隔离 smoke：模块按文件路径加载（绕过包 __init__/dotenv）→ True；E:\ 拒绝=E_DRIVE_FORBIDDEN_CONFIRMED；trade_calendar 读取=5587 个交易日
- 激活边界：formal_backtest_active=False，engine_core_active=False，admission_stage=PRE_INGESTION_ONLY
- 结论：引擎本体保留；**值数据接入层在原交付就未接通**（dictionary_only_no_value_ingest），不是迁移丢失。缺的一层 = 本地值数据 provider + 路径绑定
