# CURSOR_NOTIFY_1814_COMPLETION

TO: ChatGPT (WEB)
FROM: ZHANGWEI / Cursor E Agent
tip: BLACKBOX_FOUNDATION_ACCEPT_26_FILESETS_AND_FINISH_SCHEMA_INTERFACE_20261022_1814
status: COMPLETED
checkpoint: COMPLETION_1814
FOUNDATION_ACCEPTANCE=false
PRODUCTION_CHANGE_AUTHORIZED=false

## 做了什么（只做余项三项，未重复 1803）

1. **字典字段对应**：15 组（按数据集/模式版本），复用 13 清单的 schema 枚举 + 20 契约 17 份 + 引擎 5 张 admission matrix。新读只有 26 域 parquet header（按 prefix 枚举，非逐文件）与少量 sidecar。
2. **基线后与外源范围**：P5 20/20 带 RAW_MANIFEST；FUND_ETF_NAV 13775 parquet；14 个外源/历史根按 own-contract 归类（正式继承 / 原规则排除 / 历史实验 / 字典证据 / 审计试验 / 未定）。
3. **引擎真实接口**：读 pyproject + MASTER_RULE_LIBRARY_REGISTRY_R1 + DATA_INGESTION_GATE_RULES_R1 + providers/base + `_create_provider` + local_dictionary_registry，并做**一次隔离纯读取 smoke**。

## 关键结论

- 分钟组：26 域实读 **8 列**，缺 factor/high_limit/low_limit/paused → 日频 join 派生，不是丢失。
- 13 清单 12 列分钟 schema 来自标注 DO_NOT_USE_AS_MASTER 的试验窗口 → **适用范围已更正**。
- index_weights 缺 member_code（PK 缺口）+ 单快照；mtss 缺 4 字段；finance 命名不一致 + statDate.1 重复 + 无 revision_version。
- 引擎：`formal_backtest_active=false` / `engine_core_active=false` / `PRE_INGESTION_ONLY` = 原交付边界；`_create_provider` 无本地值数据分支；local_dictionary_registry 拒绝 E:\（smoke 已证）。
- 缺的一层 = 本地值数据 provider + 路径绑定；给最小隔离方案，不改生产。

## 关键件

- `FOUNDATION_FINAL_VERDICT_R1.json`
- `DICTIONARY_FIELD_MAPPING_R1.md` / `.json`
- `POST_BASELINE_SCOPE_SUPPLEMENT_R1.json`
- `ENGINE_DATA_INTERFACE_R1.json`
- `isolation_smoke/LOCAL_DICT_ADAPTER_SMOKE.json`
- `REUSE_NOTE.json` / `USER_FINAL_REPORT.md` / `run_completion_1814_worker.py`

## 未做

逐文件重读、财务正文、历史脚本找回、收益重现、下载/API、生产改动、清理、R9 重启、旧策略运行。
