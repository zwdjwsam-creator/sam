# MASTER Rule Library Registry R1

## 概述

本目录是 D 盘回测引擎 (`D:\backtest_lab`) **总规则索引**与**数据进入前门控规则**。

- **registry_id**: `MASTER_RULE_LIBRARY_REGISTRY_R1`
- **生成任务**: `D_BACKTEST_ENGINE_RULE_LIBRARY_MASTER_REGISTRY_R1`
- **生成时间**: 2026-06-19T08:06:09+08:00

## 核心原则

1. 本目录是 D 盘回测引擎总规则索引。
2. 所有数据进入回测引擎前，必须先匹配 `MASTER_RULE_LIBRARY_REGISTRY_R1`。
3. 数据进入前必须经过 `DATA_INGESTION_GATE_RULES_R1`。
4. **不允许「先进入、后判断」**（`post_ingestion_judgement_allowed=false`）。
5. 不符合字段、资产、频率、PIT、复权、撮合需求的，直接 **BLOCK**。
6. 所有 BLOCK 必须生成 `block_reason_code`。
7. 当前 `formal_backtest_active=false`。
8. 当前 engine core **未接入**该门控。
9. 后续如要让 engine core 调用该门控，必须单独授权。
10. 当前规则索引用于后续 shadow engine 数据准入验证。

## 已登记规则库

- `JQ_OFFICIAL_CANONICAL_R1` — 聚宽官方 canonical 字典
- `JQ_OFFICIAL_MATCHING_BEHAVIOR_R1` — 撮合行为规则
- `JQ_OFFICIAL_DAILY_MINUTE_BACKTEST_R1` — 日线/分钟线回测规则
- `BLACKBOX_CURRENT_DICTIONARY_R1` — BLACKBOX JQData CURRENT 字典
- `BLACKBOX_FACTOR_260_CURRENT_R1` — BLACKBOX 260 因子 CURRENT 字典

## 门控阶段

`admission_stage = PRE_INGESTION_ONLY`

`non_matching_data_admission_policy = BLOCK`
