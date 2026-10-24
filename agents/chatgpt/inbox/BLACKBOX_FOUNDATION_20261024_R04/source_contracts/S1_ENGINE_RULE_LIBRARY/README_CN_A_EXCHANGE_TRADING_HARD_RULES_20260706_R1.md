# CN A 股交易所交易硬规则 R1（2026-07-06）

## 概述

本目录为 **D 盘回测引擎** 独立硬规则层，生效时点 **2026-07-06**。

- **规则库 ID**: `CN_A_EXCHANGE_TRADING_HARD_RULES_20260706_R1`
- **任务**: `D_BACKTEST_ENGINE_CN_A_EXCHANGE_TRADING_HARD_RULES_WRITE_20260706_R1`
- **范围**: 沪深（SSE + SZSE）；北交所暂缓项单独标注
- **状态**: `rule_library_active=true`，`engine_core_active=false`，`formal_backtest_active=false`

## 硬边界

```text
E:\BLACKBOX 只读，未修改
engine core 未改、未接入
master_registry 暂未挂接（独立层）
正式回测未启动
```

## 2026-07-06 起启用（7 条）

| # | 规则 ID | 内容 |
|---|---------|------|
| 1 | `CN_A_EXCH_POST_CLOSE_FIXED_PRICE_SSE_R1` | 上交所盘后固定价格：A股+ETF；委托 9:30-11:30/13:00-15:30；成交 15:05-15:30 |
| 2 | `CN_A_EXCH_POST_CLOSE_FIXED_PRICE_SZSE_R1` | 深交所盘后固定价格：A股+ETF；委托 9:15-11:30/13:00-15:30；成交 15:05-15:30 |
| 3 | `CN_A_EXCH_ST_PRICE_LIMIT_MAINBOARD_SSE_R1` | 上交所主板 ST/*ST：±5% → ±10% |
| 4 | `CN_A_EXCH_ST_PRICE_LIMIT_MAINBOARD_SZSE_R1` | 深交所主板 ST/*ST：±5% → ±10% |
| 5 | `CN_A_EXCH_ST_PRICE_LIMIT_UNCHANGED_STAR_CHINEXT_BSE_R1` | 科创板/创业板/北交所 ST 涨跌幅本次不变（20%/20%/30%） |
| 6 | `CN_A_EXCH_SSE_FUND_CLOSE_CALL_AUCTION_R1` | 上交所基金收盘价：连续竞价 → 收盘集合竞价 14:57-15:00 |
| 7 | `CN_A_EXCH_SZSE_CHINEXT_BLOCK_TRADE_CONFIRM_R1` | 创业板大宗成交确认：15:00-15:30 → 9:30-15:30 |

## 7 月 6 日不启用（2 条 pending）

| 规则 ID | 内容 |
|---------|------|
| `CN_A_EXCH_BSE_POST_CLOSE_FIXED_PRICE_PENDING_R1` | 北交所盘后固定价格交易暂缓 |
| `CN_A_EXCH_BSE_ST_DAILY_BUY_LIMIT_PENDING_R1` | 北交所 ST 单日净买入 20 万股限制暂缓 |

## 文件清单

| 文件 | 说明 |
|------|------|
| `cn_a_exchange_trading_hard_rules_20260706_R1.json` | 主硬规则（9 条） |
| `cn_a_exchange_trading_hard_rules_date_switch_R1.json` | 日期切换 profile |
| `cn_a_exchange_trading_hard_rules_exclusion_R1.csv` | 排除/不变/暂缓清单 |
| `cn_a_exchange_trading_hard_rules_registry.json` | 本层注册表 |

## 参考输入

- 用户信息图：`D:\backtest_lab\10_reference_inputs\cn_a_exchange_trading_hard_rules_20260706_R1\USER_INFOGRAPHIC_A_SHARE_TRADING_RULE_20260706.png`
- BLACKBOX 只读对照：`E:\BLACKBOX\规则库\exchange_rules\CN_A_EXCHANGE_TRADING_RULE_20260706_R1`
