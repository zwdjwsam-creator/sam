# TIP_1814 收口 — 三方面结论（不含重复检查）

FOUNDATION_ACCEPTANCE=false  PRODUCTION_CHANGE_AUTHORIZED=false  ORDER_ALLOWED=false

## 一、原规则范围内 RAW 文件保留

- **已通过**：26 份 CANONICAL_FILE_LIST.parquet 逐路径 exists（1803），missing=0。本轮不再复扫、不重计数。
- **已通过**：26 域同集对照 expected=matched。结合 R9 迁移保真，文件保留有依据。
- **已通过**：21 个 JQ 增量 dataset 全部在盘（P5_jq20_extension 20/20 带 RAW_MANIFEST.json；FUND_ETF_NAV 增量 13775 parquet + 13775 sidecar + 13750 checksum，日期 20260713–20260924）。
- **尚未覆盖**：7 月底之后逐日增量完整性未对账；外源除 Tushare 可转债 R1/R2 外的供应商清单未核；外部证据平面各 PRODUCT_META 内容完整性未核。
- **明确不升级**：不宣称下载从未截断、全部字段/单位/PIT 正确、所有外源已覆盖。

## 二、字典 / 原始 / 清洗 / 标准数据对应

15 组：4 组完全匹配、9 组匹配但有已定性冲突、1 组证据不足、1 组按原规则仅字典准入。

**具体冲突（已定性，不再返工）**

1. **26 域全部分钟 RAW = 8 列**（time,code,open,close,high,low,volume,money）。20 契约 minute_price 与引擎 minute_bar / matching 均要求 `factor`，另需 high_limit/low_limit/paused → 必须由日频平面 join 派生，不是数据丢失。
2. **13 清单的 12 列分钟 schema 适用范围错误**：取自 `JQData_9999_WINDOW_FULL_RAW_20260325_20260501`（该目录自带 DO_NOT_USE_AS_MASTER），不能作为 26 域字段依据。
3. **index_weights 缺 member_code**（实读仅 date,weight,display_name），PK 契约不可满足；且仅 1 个快照（20260831）。
4. **mtss 缺 fin_refund_value / margin_value / margin_sell_value / margin_refund_value**。
5. **finance 表命名不一致**：income/balance/indicator 用 statDate/pubDate，cash_flow 用 pub_date/report_date/report_type；且 statDate.1 为重复列。PK 契约的 revision_version 在 RAW 中不存在（restatement 链是契约而非已实现）。
6. **dtype 偏离**：volume=double（契约 int64）、date=timestamp[ns]（契约 date）、NAV day=large_string。
7. **is_st 双表示**：P2_security_state/is_st 为宽表（列名=代码），stock_st_status 为长表；clean 取长表。
8. **G14 公司行为证据不足**：已枚举 schema 中无 announce_date/ex_date/action_type 长表 → adj_factor 的 ex_date 可追溯性无法验证，按 adj factor 方法学规则 2 记 review_required。

## 三、引擎本体保留与值数据通用接口

- **原交付范围**：字典层交付（master_registry_active=true，15 道 PRE_INGESTION gate）。值数据接入未交付。
- **已接通**：字典快照纯读取层（local_dictionary_registry，拒绝 E:\，隔离 smoke 在非 E 根读通 5587 个交易日，未导入 dotenv/网络客户端）；准入矩阵 domain/field/frequency/pit/matching/code 齐全。
- **原本未接通**：`_create_provider` 只有 jqdata / tushare / qmt / miniqmt / remote_qmt 五支，**无本地值数据 provider**；adapter_function 全部 null。
- **激活边界**：`formal_backtest_active=false`、`engine_core_active=false`、`admission_stage=PRE_INGESTION_ONLY` → 原交付阶段与准入边界，**不是迁移丢失**。
- **迁移需适配**：E:\ 路径策略（字典层显式拒绝 E:）、PHASE1_CURRENT_ENGINE_REGISTRY 仍指 D:\backtest_lab_backups、pyproject 包名 bullet_trade 与目录 blackbox_jq_engine 不一致。
- **缺的一层**：本地值数据 provider + 路径绑定。最小隔离方案已给出（只读 LocalPlaneProvider，显式注入，不改 formal_backtest_active）。

## 登记后关闭的盘点发现

| ID | 发现 | 处置 |
|---|---|---|
| D1 | 分钟缺 factor/limit/paused | 登记为 join 派生要求，不再返工 |
| D2 | index_weights 无 member_code | 契约缺口，需补列或明确契约变更 |
| D3 | mtss 四字段缺 | 源字段缺口 |
| D4 | fund_etf_price_1m 6B×1/3633、index_minute 4B×1/133968 | 个别空壳文件，**不下结论为数据缺失** |
| D5 | 13 清单分钟 schema 越界 | 适用范围已更正 |

## 未做（按指令）

26 域逐文件重读、财务正文读取、历史下载脚本找回、收益重现、任何下载/API、生产改动、清理、R9 重启、旧策略运行。
