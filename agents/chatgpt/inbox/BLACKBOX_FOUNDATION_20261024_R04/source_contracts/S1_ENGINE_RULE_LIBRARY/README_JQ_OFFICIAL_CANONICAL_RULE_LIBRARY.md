# JQ Official Canonical Rule Library R1

## 概述

本目录是 **D 盘回测引擎**（`D:\backtest_lab`）的正式规则库之一：`JQ_OFFICIAL_CANONICAL_R1`。

- **来源**：`E:\BLACKBOX\规则库` 中聚宽官方规则 / JQData 字典材料（只读导入，未修改 BLACKBOX）。
- **用途**：统一聚宽官方字段、数据域、别名、资产代码格式、可交易状态、复权与撮合数据需求口径。
- **状态**：`rule_library_active=true`，`formal_backtest_active=false`。

## 重要说明

1. 官方字段 **不再标记为 candidate**；使用 `JQ_OFFICIAL_CANONICAL` / `JQ_OFFICIAL_DERIVED_FROM_DOC` 等正式状态。
2. `E:\BLACKBOX` 只读访问，写入任务未修改 BLACKBOX 或 `E:\BLACKBOX\规则库`。
3. **未修改 engine core**（`bullet_trade` 源码未触碰）。
4. **当前未激活正式回测**（`FORMAL_BACKTEST_ALLOWED=NO`）。
5. **因子层仍关闭**（`FACTOR_LAYER_ALLOWED=NO`）。

## Shadow 实验流程

真实数据下载完成后：

1. 使用封板备份复制 shadow engine（例如 `D:\backtest_lab_shadow_experiments\experiment_YYYYMMDD_xxx`）。
2. 在 shadow 中验证本规则库与真实数据对齐。
3. 试验规则按四类标注：`JQ_DOC_EXPLICIT` / `JQ_DOC_DERIVED` / `JQ_PROBE_DERIVED` / `LOCAL_ENGINE_ASSUMPTION`。
4. 人工审批通过后再考虑主引擎迁移计划。

## 文件清单

| 文件 | 说明 |
|---|---|
| jq_official_canonical_field_dictionary.json | 官方 canonical 字段字典 |
| jq_official_canonical_data_domain_map.csv | 数据域映射 |
| jq_official_canonical_field_alias_map.csv | 字段别名 |
| jq_official_asset_code_format_map.csv | 资产代码格式 |
| jq_official_tradable_status_field_map.csv | 可交易状态 |
| jq_official_adjustment_field_map.csv | 复权字段 |
| jq_official_matching_data_requirements.csv | 撮合数据需求 |
| jq_official_rule_library_registry.json | 注册表 |

## 《JQ 官方撮合行为规则 R1》

文件：`jq_official_matching_behavior_rules.json`

1. **回测市价单成交量限制** = 当日总成交量 × `order_volume_ratio`。
2. **模拟交易市价单**全部成交，不受成交量限制。
3. **限价单挂单后分钟级撮合** = 本分钟 bar 成交量 × `order_volume_ratio`。
4. **回测盘口撮合默认关闭**（`match_with_order_book_default=false`）。
5. **未启用盘口撮合**时按 `latest_price + slippage` 撮合。
6. **启用盘口撮合**时按盘口逐档撮合，成交量加权均价。
7. **涨停方向买单不成交**；市价单取消，限价单挂单。
8. **跌停方向卖单不成交**；市价单取消，限价单挂单。
9. **停牌不可交易**（`paused` / `is_suspended`）。
10. **停牌行情字段**仍有 OHLC/pre_close 值，但 `volume=0`，`money=0`。
11. **停牌估值**为本地可配置假设（`LOCAL_ENGINE_ASSUMPTION_CONFIGURABLE`），不作为聚宽官方明确规则。

- `formal_backtest_active=false`；未修改 engine core。
- 真实数据就绪后在 shadow engine 验证，不直接开正式回测。

## 《JQ 官方撮合行为规则 R1B 补丁》

文件：`jq_official_matching_behavior_rules.json`（补丁后 16 条规则）

1. **挂单限价单分钟 Bar 撮合条件**：
   - 买入：委托价 > 本分钟 Bar 最低价；
   - 卖出：委托价 < 本分钟 Bar 最高价。
2. **tick 级挂单限价单**不检查成交量，满足价格条件后剩余部分全部以委托价成交。
3. **超出成交量限制时**：市价单超出部分撤单，限价单超出部分挂单继续撮合。
4. **盘口撮合仅模拟交易可启用**。
5. **回测环境不支持启用盘口撮合**，默认 `latest_price + slippage`。
6. **启用盘口撮合但无盘口数据时**，降级为 `latest_price + slippage`。

- `formal_backtest_active=false`；未修改 engine core。

## 《JQ 日线 / 分钟线回测规则 R1》

文件：`jq_official_daily_minute_backtest_rules.json`（10 条规则，全部 `JQ_DOC_EXPLICIT`）

1. **日线回测市价单成交价** = 当日开盘价 + 滑点。
2. **分钟线回测市价单成交价** = 上一分钟最后价格 + 滑点。
3. **日线回测市价单成交量限制** = 当日总成交量 × `order_volume_ratio`。
4. **分钟线回测市价单成交量限制** = 当日总成交量 × `order_volume_ratio`。
5. **限价单挂单**后在分钟 Bar 结束时继续撮合。
6. **买入限价单条件**：委托价 > 本分钟 Bar 最低价。
7. **卖出限价单条件**：委托价 < 本分钟 Bar 最高价。
8. **限价单挂单成交量限制** = 本分钟 Bar 成交量 × `order_volume_ratio`。
9. **回测不启用盘口撮合**，默认 `latest_price + slippage`。
10. **停牌不可交易**。
11. **停牌行情字段**：open/close/high/low/pre_close 等于停牌前收盘价，`volume=0`，`money=0`。
12. 本文件**不包含猜测规则**，**不包含 LOCAL_ENGINE_ASSUMPTION**。

- 本文件为日线/分钟线回测专用规则层；与 `jq_official_matching_behavior_rules.json` 并存，不覆盖旧文件。
- `formal_backtest_active=false`；未修改 engine core。
