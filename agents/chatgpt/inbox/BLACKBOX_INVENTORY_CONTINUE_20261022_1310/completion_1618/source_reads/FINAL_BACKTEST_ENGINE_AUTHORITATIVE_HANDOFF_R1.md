# FINAL — Backtest Engine Authoritative Handoff R1

- **handoff_id**: `BACKTEST_ENGINE_AUTHORITATIVE_HANDOFF_R1`
- **generated_at**: `2026-07-31T04:13:35+08:00`
- **handoff_status**: `READY_FOR_BLACKBOX_REVIEW`
- **conclusion**: `BACKTEST_ENGINE_HANDOFF_PACKAGE_READY_FOR_BLACKBOX_REVIEW`

## 1. 执行摘要

D 盘独立回测引擎当前为 `STRUCTURE_READY_DATA_WAITING`：规则库与 MASTER 总索引/PRE_INGESTION 门控已就绪，正式回测与真实因子值关闭。本交接包只整理现有文件证据，供 BLACKBOX 核对，不宣称正式回测就绪。

## 2. 项目身份与路径

- project_root: `D:\backtest_lab`
- engine_base_path: `D:\backtest_lab\02_blackbox_jq_compat_engine`
- project_type: `INDEPENDENT_BACKTEST_ENGINE`
- blackbox_is_separate_project: true
- jq_is_reference_behavior_not_source_code: true
- qmt_is_downstream_and_disconnected: true
- engine_base_origin_status: `NOT_VERIFIED`

## 3. 当前引擎状态

| 项 | 状态 |
|---|---|
| current_engine_status | STRUCTURE_READY_DATA_WAITING |
| rule_layer_status | READY |
| master_registry_status | READY |
| formal_backtest_status | CLOSED |
| factor_layer_status | CLOSED_OR_DICTIONARY_ONLY |
| handoff_status | READY_FOR_BLACKBOX_REVIEW |

## 4. 已完成模块

- completed_modules: ['single_channel', 'matrix_channel', 'parquet_input', 'matching_rule_gateway', 'archive_manager', 'test_memory', 'capability_registry', 'watchdog', 'rule_library', 'master_registry', 'pre_ingestion_gate']
- structure_ready_modules: ['output_metric_schema', 'output_builder_vnext', 'task_gate_scheduler', 'stop_failure_report', 'contract_prelayout']
- query_ready_modules: ['artifact_query']
- blocked_modules: ['formal_backtest', 'factor_layer']
- not_ready_modules: ['cleaning_window', 'execution_profile_registry', 'backtest_time_entry']

完整 module_inventory 见 HANDOFF JSON。

## 5. 规则库与 MASTER 总索引

| rule_library_id | active | count | formal_backtest | engine_core |
|---|---:|---:|---:|---:|
| JQ_OFFICIAL_CANONICAL_R1 | True | 11 | False | False |
| JQ_OFFICIAL_MATCHING_BEHAVIOR_R1 | True | 16 | False | False |
| JQ_OFFICIAL_DAILY_MINUTE_BACKTEST_R1 | True | 10 | False | False |
| BLACKBOX_CURRENT_DICTIONARY_R1 | True | 18 | False | False |
| BLACKBOX_FACTOR_260_CURRENT_R1 | True | 260 | False | False |
| MASTER_RULE_LIBRARY_REGISTRY_R1 | True | 5 | False | False |
| DATA_INGESTION_GATE_RULES_R1 | True | 15 | False | False |

MASTER 门控确认：

- data_ingestion_requires_master_rule_match = `True`
- non_matching_data_admission_policy = `BLOCK`
- admission_stage = `PRE_INGESTION_ONLY`
- post_ingestion_judgement_allowed = `False`

附加层（未挂入 MASTER 列表）: `CN_A_EXCHANGE_TRADING_HARD_RULES_20260706_R1` exists=True master_linked=False

## 6. 数据准入与禁止清单

### allowed_data_contract
- `minute_bar` — DICTIONARY_ADMISSION_DEFINED — ADMIT_IF_MATCHED; dictionary_only_no_value_ingest until real data gate pass
- `execution_profile` — STRUCTURE_DEFINED — registry/schema exist; formal use requires task gate
- `matching_rule` — RULE_LIBRARY_DEFINED — reference-only until engine core connected
- `result_ledgers_structure` — STRUCTURE_READY — query existing artifacts only; no new formal ledger generation in this handoff
- `archive_structure` — READY — query_existing_artifacts
- `test_memory_structure` — READY — query_existing_artifacts
- `JQData_official_dictionary` — READY_DICTIONARY_ONLY — schema/dictionary reference; no live API
- `factor_dictionary_metadata_only` — ADMIT_DICTIONARY_ONLY — metadata only; values forbidden
- `factor_formula_metadata_only` — ADMIT_DICTIONARY_ONLY — metadata only
- `factor_pit_rules_metadata_only` — ADMIT_DICTIONARY_ONLY — metadata only
- `factor_engine_mapping_metadata_only` — ADMIT_DICTIONARY_ONLY — metadata only

### blocked_data_contract
- `real_factor_values` — BLOCK_FACTOR_VALUE
- `JQ260_factor_values` — BLOCK_FACTOR_VALUE
- `BBX_unverified_factor_values` — BLOCK_FACTOR_VALUE
- `data_not_matched_to_master_registry` — BLOCK_SOURCE_IDENTITY_GATE
- `unknown_fields` — BLOCK_FIELD_DICTIONARY_GATE
- `unknown_asset_types` — BLOCK_ASSET_TYPE_GATE
- `unsupported_frequencies` — BLOCK_FREQUENCY_GATE
- `PIT_undefined_data` — BLOCK_PIT_*
- `missing_matching_required_fields` — BLOCK_MATCH_*
- `QMT_live_broker_inputs` — BLOCK_QMT_LIVE_BROKER

### not_ready_data_contract
- `daily_bar` — NOT_READY
- `trade_calendar` — NOT_READY
- `session` — NOT_READY
- `tradable_status` — NOT_READY
- `benchmark_data` — NOT_READY
- `tick_formal_backtest` — NOT_READY

## 7. 日期、时间点、Bar 与可见性合同

| item | definition_status | evidence |
|---|---|---|
| backtest_start_date_semantics | NOT_DEFINED | N/A |
| backtest_end_date_semantics | NOT_DEFINED | N/A |
| signal_time_semantics | NOT_DEFINED | N/A |
| data_visibility_semantics | PARTIAL | data_visibility_contract.py |
| daily_bar_completion_time | NOT_DEFINED | N/A |
| minute_bar_completion_time | NOT_DEFINED | N/A |
| previous_minute_visibility | PARTIAL | jq_official_daily_minute_backtest_rules.json |
| current_bar_visibility | PARTIAL | data_visibility_contract.py |
| future_data_guard | PARTIAL | DataVisibilityContractConstants.lookahead_guard=true |
| PIT_enforcement | PARTIAL | PIT_VISIBILITY_ADMISSION_MATRIX_R1.csv / factor_260_pit_rules_CURRENT.json |
| timezone | PARTIAL | clock_contract.py time_zone field |
| trading_calendar_dependency | NOT_READY | formal_backtest_run_plan_blockers.json |
| session_dependency | NOT_READY | formal_backtest_run_plan_blockers.json |

说明：不得把规则库中的聚宽参考规则自动解释为 engine core 已实现。

## 8. 事件时钟

| item | rule_defined | contract_reserved | engine_core_implemented | verified_by_replay | formal_use_allowed |
|---|---:|---:|---:|---:|---:|
| initialize | False | True | False | False | False |
| before_trading | False | True | False | False | False |
| market_open | False | True | False | False | False |
| scheduled_callback | False | True | False | False | False |
| bar_event | False | True | False | False | False |
| order_event | False | True | False | False | False |
| trade_event | False | True | False | False | False |
| market_close | False | True | False | False | False |
| time_advance_policy | False | True | False | False | False |
| lookahead_guard | False | True | False | False | False |
| same_bar_order_policy | False | False | False | False | False |
| next_bar_order_policy | False | False | False | False | False |

## 9. 撮合与订单规则

| item | RULE_LIBRARY_DEFINED | ENGINE_CORE_IMPLEMENTED | SHADOW_VERIFIED | FORMAL_VERIFIED |
|---|---:|---:|---:|---:|
| daily_market_fill_price | True | False | False | False |
| minute_market_fill_price | True | False | False | False |
| daily_market_volume_limit | True | False | False | False |
| minute_market_volume_limit | True | False | False | False |
| pending_limit_buy_condition | True | False | False | False |
| pending_limit_sell_condition | True | False | False | False |
| pending_limit_volume_cap | True | False | False | False |
| market_excess_cancellation | True | False | False | False |
| limit_excess_remains_pending | True | False | False | False |
| limit_up_buy_behavior | True | False | False | False |
| limit_down_sell_behavior | True | False | False | False |
| suspension_no_trade_behavior | True | False | False | False |
| suspended_bar_fields | True | False | False | False |
| order_book_matching_scope | True | False | False | False |
| missing_order_book_fallback | True | False | False | False |
| tick_limit_order_behavior | True | False | False | False |

## 10. 成本、结算、现金与持仓

| item | status |
|---|---|
| CostModelContract | CONTRACT_RESERVED |
| SettlementContract | CONTRACT_RESERVED |
| RiskGatewayContract | CONTRACT_RESERVED |
| OrderFillSchemaContract | CONTRACT_RESERVED |
| cash_ledger | NOT_DEFINED |
| available_cash | CONTRACT_RESERVED |
| frozen_cash | CONTRACT_RESERVED |
| position_quantity | NOT_DEFINED |
| closeable_amount | PARTIAL |
| T+1_reservation | CONTRACT_RESERVED |
| ETF_T0_or_T1_status | CONTRACT_RESERVED |
| commission | CONTRACT_RESERVED |
| tax | CONTRACT_RESERVED |
| slippage | CONTRACT_RESERVED |
| minimum_commission | NOT_DEFINED |
| valuation_policy | NOT_DEFINED |
| suspended_position_valuation | LOCAL_CONFIGURABLE_POLICY_NOT_ACTIVATED |

## 11. 资产生命周期

| item | required_field | admission_status | implementation_status |
|---|---|---|---|
| listing_date | list_date | NOT_READY | NOT_IMPLEMENTED |
| delisting_date | delist_date | NOT_READY | NOT_IMPLEMENTED |
| new_stock | is_new_stock | NOT_READY | NOT_IMPLEMENTED |
| ST | is_st | ADMIT_IF_MATCHED_DICTIONARY | RULE_FIELD_DEFINED_DATA_NOT_READY |
| suspended | paused/is_suspended | ADMIT_IF_MATCHED_DICTIONARY | RULE_DEFINED_ENGINE_CORE_NOT_CONNECTED |
| high_limit | high_limit | ADMIT_IF_MATCHED_DICTIONARY | RULE_DEFINED_ENGINE_CORE_NOT_CONNECTED |
| low_limit | low_limit | ADMIT_IF_MATCHED_DICTIONARY | RULE_DEFINED_ENGINE_CORE_NOT_CONNECTED |
| asset_code_format | security_code pattern | ADMIT_IF_MATCHED | RULE_DEFINED |
| stock | asset_type=stock | ADMIT_IF_MATCHED | RULE_DEFINED |
| ETF | asset_type=etf | ADMIT_IF_MATCHED | RULE_DEFINED |
| fund | asset_type=fund | ADMIT_IF_MATCHED | RULE_DEFINED |
| index | asset_type=index | ADMIT_IF_MATCHED | RULE_DEFINED_DATA_NOT_READY |

## 12. 插件与输入输出接口

### 输入端
- `strategy_interface` — interface_defined=True schema_defined=True status=STRUCTURE_ONLY formal_use_allowed=False
- `data_adapter` — interface_defined=True schema_defined=False status=PARTIAL_OR_STRUCTURE formal_use_allowed=False
- `execution_profile` — interface_defined=True schema_defined=True status=REGISTRY_EXISTS_BUT_CAPABILITY_NOT_READY formal_use_allowed=False
- `benchmark_input` — interface_defined=True schema_defined=True status=NOT_READY formal_use_allowed=False
- `factor_input` — interface_defined=True schema_defined=True status=DICTIONARY_ONLY_VALUES_BLOCKED formal_use_allowed=False
- `external_data_port` — interface_defined=False schema_defined=False status=NOT_DEFINED formal_use_allowed=False

### 输出端
- `order_ledger` — interface_defined=True schema_defined=False status=STRUCTURE_READY_OR_PLANNING formal_use_allowed=False
- `trade_ledger` — interface_defined=True schema_defined=False status=STRUCTURE_READY_OR_PLANNING formal_use_allowed=False
- `position_ledger` — interface_defined=True schema_defined=False status=STRUCTURE_READY_OR_PLANNING formal_use_allowed=False
- `cash_ledger` — interface_defined=False schema_defined=False status=NOT_DEFINED formal_use_allowed=False
- `daily_portfolio` — interface_defined=True schema_defined=False status=STRUCTURE_READY_OR_PLANNING formal_use_allowed=False
- `metrics` — interface_defined=True schema_defined=True status=STRUCTURE_READY formal_use_allowed=False
- `ResultPackage` — interface_defined=True schema_defined=False status=READY_FOR_QUERY_EXISTING formal_use_allowed=False
- `archive` — interface_defined=True schema_defined=False status=READY formal_use_allowed=False
- `test_memory` — interface_defined=True schema_defined=False status=READY formal_use_allowed=False
- `artifact_index` — interface_defined=True schema_defined=True status=QUERY_READY formal_use_allowed=False
- `STOP_report` — interface_defined=True schema_defined=True status=STRUCTURE_READY formal_use_allowed=False

## 13. BLACKBOX 核对清单

| check_id | requirement | compatibility_status |
|---|---|---|
| BBX_CHK_001 | BLACKBOX 字段字典是否与 D 盘 MASTER 字段矩阵一致。 | PENDING_BLACKBOX_REVIEW |
| BBX_CHK_002 | BLACKBOX 资产代码是否符合 D 盘代码准入矩阵。 | PENDING_BLACKBOX_REVIEW |
| BBX_CHK_003 | BLACKBOX frequency 是否在准入矩阵中。 | PENDING_BLACKBOX_REVIEW |
| BBX_CHK_004 | BLACKBOX PIT / available_date 是否满足 D 盘可见性合同。 | PENDING_BLACKBOX_REVIEW |
| BBX_CHK_005 | BLACKBOX trade_calendar / session 是否可提供。 | PENDING_BLACKBOX_REVIEW |
| BBX_CHK_006 | BLACKBOX tradable_status 是否可提供。 | PENDING_BLACKBOX_REVIEW |
| BBX_CHK_007 | BLACKBOX adjustment mode 是否明确。 | PENDING_BLACKBOX_REVIEW |
| BBX_CHK_008 | BLACKBOX benchmark 是否可提供。 | PENDING_BLACKBOX_REVIEW |
| BBX_CHK_009 | BLACKBOX 因子只允许 metadata，真实因子值仍禁止。 | PENDING_BLACKBOX_REVIEW |
| BBX_CHK_010 | BLACKBOX 输出数据必须在进入 D 盘前通过 PRE_INGESTION gate。 | PENDING_BLACKBOX_REVIEW |
| BBX_CHK_011 | 不允许先进入后修复。 | PENDING_BLACKBOX_REVIEW |
| BBX_CHK_012 | 任一失败必须生成 block_reason_code。 | PENDING_BLACKBOX_REVIEW |

## 14. 当前阻塞项

- `real_data_not_ready` — ACTIVE — contract_registry.engine_state=STRUCTURE_READY_DATA_WAITING
- `daily_bar_not_ready` — ACTIVE — formal_backtest_run_plan_blockers.json
- `trade_calendar_not_ready` — ACTIVE — formal_backtest_run_plan_blockers.json
- `session_not_ready` — ACTIVE — formal_backtest_run_plan_blockers.json
- `tradable_status_not_ready` — ACTIVE — formal_backtest_run_plan_blockers.json / TradableStatusContract
- `benchmark_not_ready` — ACTIVE — formal_backtest_run_plan_blockers.json
- `factor_values_forbidden` — ACTIVE — bb_reg.factor_value_download_allowed / capability factor_layer BLOCKED
- `engine_core_not_connected_to_master_gate` — ACTIVE — master.engine_core_active=false; README
- `shadow_validation_not_run` — ACTIVE — HANDOFF_BACKTEST_ENGINE_PHASE_SEAL.md next-stage candidate
- `daily_minute_three_month_validation_not_run` — ACTIVE — no validation report found in inspected outputs

## 15. 正式启动条件

- `FSC_01` BLACKBOX 交接核对通过 — status=PENDING
- `FSC_02` 真实数据通过 MASTER PRE_INGESTION gate — status=PENDING
- `FSC_03` 必需数据域 READY（daily_bar/trade_calendar/session/tradable_status/benchmark） — status=PENDING
- `FSC_04` shadow engine 建立 — status=PENDING
- `FSC_05` 日线和分钟线至少三个月验证完成 — status=PENDING
- `FSC_06` 撮合差异已记录 — status=PENDING
- `FSC_07` 本地补充规则已明确标注 — status=PARTIAL
- `FSC_08` task gate 明确允许 — status=PENDING
- `FSC_09` 正式回测仍需单独授权 — status=REQUIRED

## 16. 交接结论

`BACKTEST_ENGINE_HANDOFF_PACKAGE_READY_FOR_BLACKBOX_REVIEW`

明确不宣称：`FORMAL_BACKTEST_READY` / `REAL_FACTOR_READY` / `PRODUCTION_READY`。

---

- HANDOFF_JSON: `D:\backtest_lab\06_outputs\authoritative_handoff_R1\BACKTEST_ENGINE_AUTHORITATIVE_HANDOFF_R1.json`
- SYSTEM_PY_USED: YES
- E_BLACKBOX_READ: NO
- ENGINE_SOURCE_MODIFIED: NO
- RULE_LIBRARY_MODIFIED: NO