# BLACKBOX R10 端到端完成（实测结果）

任务: `BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025`  
生成时间: 2026-10-25T08:46:44+08:00  
总判定: **PASS**

## A. 可执行环境（先验证，再复用）

- verdict: **PASS_REAL_VENV_WITH_DATA_STACK**
- interpreter: `C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe` (3.12.10); venv prefix `E:\BLACKBOX\.venv`, base interpreter `C:\Users\Admin\AppData\Local\Programs\Python\Python312`
- data stack measured in-process: pandas 2.3.3, pyarrow 21.0.0, numpy 2.5.4
- real read: newest 2026 STOCK_DAILY partition footer = 871182 rows
- no project-tree import leak: True

复用的边界：标准 `.venv` 是 `python -m venv` 的真实产物（prefix 与 base_prefix 不同、site-packages 属于 venv 自己），并且用**真实 parquet 读取**验证，不是只改 `home` 就宣布修好。

## B. 数据面盘点（逐数据集实测范围）

- 54 datasets; 84 layer measurements; 14 NOT_APPLICABLE_WITH_CONTRACT; 3 BLOCKED
- readiness split: BLOCKED_NO_LAYER_MEASURED=3, NOT_APPLICABLE_WITH_CONTRACT=14, PARTIAL_READABLE_CURSOR_BLOCKED=37
- per-dataset increment cursor: NOT_APPLICABLE=14, NOT_BOUND=40
- 11 datasets point at the shared CACHE release root; their per-dataset figure is `cache_products`, and the root-level total is marked `MEASURED_RELEASE_ROOT_ONLY` so it is not mistaken for a per-dataset row count
- 8 readable datasets carry no usable time axis (CALENDAR_CN_EXCHANGE, SECURITY_MASTER, INDUSTRY_CONCEPT_EVENTS, MTSS, FUND_TRACKING_INDEX_MAPPING, TS_CBOND_R1, TS_CBOND_R2, EXTERNAL_EVIDENCE_PLANE); their update boundary has to come from a content identity, not a date, so they are explicitly listed instead of being given an inferred range.

要点：本交付**没有**把 CURRENT 的 asof 当成所有数据集的增量游标。每个数据集给出的是自己的一层一层实测 `min~max` 与行数；`increment_cursor` 在没有 writer 发出游标前保持 `NOT_BOUND`。

## C. 单日更新/清洗可运行性（真实批次重放）

- verdict: **REPRODUCES_R06_CANDIDATE**, compared rows 10426, value diffs all zero: True
- 2026-08-31: raw 5212 rows -> clean 5212 rows / 5212 codes; duplicates 0, OHLC violations 0, null prices 0, anti-leak True (max date 2026-08-31)
- 2026-09-01: raw 5214 rows -> clean 5214 rows / 5214 codes; duplicates 0, OHLC violations 0, null prices 0, anti-leak True (max date 2026-09-01)
- rebuilt year=2026 partition: 959896 rows / 178 dates / 5535 codes, window 2026-01-05..2026-09-24, missing exchange days 0, days outside calendar 0
- calendar source: 95 CALENDAR_TRADE_DAYS files under clean releases

这一步直接回应“文件齐全+预检通过≠单日更新可运行”：它把保留的原始批次按同一套清洗规则重跑，写进候选年分区，再与引擎实际读过的 R06 候选逐格比对。

## D. 原引擎 + V4 真实回测

- status **COMPLETED**, window 2026-09-03..2026-09-24, engine `E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine\blackbox_jq_engine`
- strategy `聚宽范本_日频模拟盘_V4_R21_HOTSTART_R5.py` sha256 `8d9334dd6ed2053b`
- daily records 16, trades 2 (成交笔), 持仓快照行 15
- `orders` 表 0 行：该引擎的 `_generate_results` 不导出订单表，成交只能由 `trades.csv` 重建；本期 1 个订单号拆成 2 笔成交（`order_id` + `trade_id`）
- network attempts blocked: 0
- provider bindings: CANDIDATE_OVERRIDE=1, CURRENT_SEALED=16

| 实测项 | 值 |
|---|---|
| n_days | 16 |
| initial_total_value | 1000000.0 |
| final_total_value | 953384.16 |
| total_return_pct | -4.6616 |
| max_drawdown_pct | -5.466 |
| distinct_positions_value | 12 |
| distinct_total_value | 12 |
| benchmark_columns | ['benchmark_price', 'benchmark_value', 'benchmark_returns_pct', 'excess_returns_pct'] |
| n_trade_fills | 2 |
| traded_securities | ['002701.XSHE'] |
| turnover_value | 998865.0 |
| n_order_ids_in_trades | 1 |
| position_rows | 15 |
| distinct_position_prices | 11 |

引擎自报（`run_result.json.metrics`，未经本任务改写）：

| 指标 | 值 |
|---|---|
| 策略收益 | -4.66% |
| 策略年化收益 | -52.57% |
| 最大回撤 | -5.47% |
| 夏普比率 | -8.53 |
| 日胜率 | 18.75% |
| 交易胜率 | 0.00% |
| 交易天数 | 16 |
| 初始资金 | 1,000,000.00 |
| 最终资金 | 953,384.16 |

引擎源码未修改：注入只发生在外部（provider 绑定、全局注入、网络拒绝）。资产白名单用的是 `D:\BB_LOCAL_DICTIONARY` 的派生快照，守卫本身仍在生效。

## D2. 实跑暴露的数据面覆盖缺口（不是猜测，是引擎日志）

| 数据集 | CACHE 产品 | 实测起始 | 实测终止 | 行数 |
|---|---|---|---|---|
| PRICE_STOCK_DAILY | STOCK_DAILY_PIT_R1 | 2014-01-02 | 2026-09-24 | 17030241 |
| PRICE_STOCK_DAILY | STOCK_DAILY_RAW_PIT_R1 | 2014-01-02 | 2026-09-24 | 12351786 |
| ADJUST_FACTOR | ADJUST_FACTOR_PIT_R1 | 2014-01-02 | 2026-09-24 | 12266026 |
| TRADABLE_STATUS | STOCK_TRADEABILITY_PIT_R1 | 2026-07-13 | 2026-09-03 | 249858 |

- 价格平面到 `2026-09-24`，可交易性平面只到 `2026-09-03`：窗口内最后一段没有涨跌停价与 ST 标记。
- 引擎因此记录 `limit_up_flag_missing` 2 次、`boolean value of NA is ambiguous` 14 次；即涨跌停市价撤单校验被跳过、`昨日涨停名单` 步骤中断。
- 这些是**数据缺口**（可交易性产品的 asof 落后于价格产品），不是引擎 bug；没有用任何默认值去伪造涨跌停或 ST 状态。补齐它们需要一次授权的增量下载，本次 `NEW_DATA_ACQUISITION_AUTHORIZED=false`，故不做。
- 因果侧：`avoid_future_data` 拦截次数 0（0 表示本次运行没有触发未来数据拦截）。
## E. 边界（本次未做）

- `NEW_DATA_ACQUISITION_AUTHORIZED` = `false`
- `CURRENT_SWITCH_ALLOWED` = `false`
- `ORDER_ALLOWED` = `false`
- `PUBLISHED_TO_CURRENT` = `false`
- `SEALED_DATA_MODIFIED` = `false`

## F. 本报告不能证明什么

- This is not a completeness certificate for the whole data plane: layer ranges are footer extrema, and `MIN_MAX_IS_NOT_COMPLETENESS` still holds.
- No dataset has a bound incremental cursor. `observed_max` is what the plane holds, not a cursor the writer maintains, so a daily update still needs an authorised per-dataset start date plus a validated overlap window.
- The engine run covers 16 trading days on sealed data. It proves the data plane and the engine are executable end to end; it says nothing about strategy edge over a longer window.
- The tradeability plane stops at 2026-09-03 while prices run to 2026-09-24: inside this window the engine could not validate limit-up/limit-down withdrawals or ST state. Closing that gap needs an authorised download, which this task does not have.
- The two recovered days are replayed from retained raw batches into a candidate partition. Nothing was merged into a sealed release and no CURRENT pointer moved.
- Intraday execution on a daily plane uses the same-day open as the fill price and the prior day's volume for the volume cap; that is a causal simulation, not tick-level execution.

## G. 复现入口

```
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 .\tools\verify_environment.py
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 .\tools\build_dataset_state.py
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 .\tools\replay_candidate_update.py
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 .\candidate\run_engine_backtest.py --start 2026-09-03 --end 2026-09-24 --out .\engine_runs\v4_r21_20260903_20260924
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 .\tools\build_delivery_report.py
```
