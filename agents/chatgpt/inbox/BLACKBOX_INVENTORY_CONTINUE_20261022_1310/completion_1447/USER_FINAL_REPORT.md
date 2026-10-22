# 数据管理阶段报告（1447）— PARTIAL

at: 2026-10-22T15:03:56+08:00
SYSTEM_INVENTORY_ACCEPTANCE: **false**
status: REQUIRED4_ENTITY_EVIDENCE_AND_UPDATE_CALLCHAIN_STATIC_PARTIAL
PRODUCTION_CHANGE_AUTHORIZED: false

## 1. 四项必需产品实体（非空壳目录）
| product | files_n | primary | rows_meta | main_enum | lineage |
|---|---|---|---|---|---|
| CORP_XR_XD_EVENT_PIT_R1 | 51 | `data/STK_XR_XD_EVENT_PIT_R1_FULL.parquet` | 129287 | CACHE_PRODUCT_UNAVAILABLE | ABSENT |
| CORP_SHAREHOLDER_TOP10_PIT_R1 | 18 | `data/STK_SHAREHOLDER_TOP10_PIT_R1_FULL.parquet` | 2694787 | CACHE_PRODUCT_UNAVAILABLE | ABSENT |
| CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1 | 18 | `data/STK_SHAREHOLDER_FLOATING_TOP10_PIT_R1_FULL.parquet` | 2653539 | CACHE_PRODUCT_UNAVAILABLE | ABSENT |
| SW_L3_MEMBERSHIP_PIT_R1 | 14 | `SOURCE_FULL.parquet` | 12564290 | CACHE_PRODUCT_UNAVAILABLE | ABSENT |

说明：
- 主枚举统一为有证据支持的 `CACHE_PRODUCT_UNAVAILABLE`（catalog 无行 → resolver 拒绝）。
- **不**写入生产枚举 `CLEANING_COMPLETE_CACHE_PRESENT_BUT_CATALOG_UNREGISTERED`；该说法仅作 diagnostic_detail 旁注且本轮明确 **不**宣称 CLEANING_COMPLETE。
- 行数来自 parquet footer metadata + row_group0 小样本；**不是**全日期×全标的内容验收。
- LINEAGE 文件名：均为 ABSENT（本轮未猜替代文件名）。

Resolver 拒绝层：`脚本/blackbox_data_access_resolver_r1.py` catalog 查找空 → `result_status=CACHE_PRODUCT_UNAVAILABLE`，`download_required=False`。范围限定：仅走该 resolver 的消费者；不推广为「磁盘对象对一切入口不可读」。

候选修复（只文档）：补 catalog 行 / 或证明另有正式直读入口 / 或走正式 cache 发布登记。本轮 **不**改 catalog、不改 resolver。

## 2. 更新编排器完整静态调用链
入口：`脚本/blackbox_daily_increment_orchestrator_r1.py`（全文已复制到 source_reads，附 SHA）。

实测步骤（正文）：
1. INDEX_WEIGHT managed check（失败则中止）
2. ETF_MINUTE_1M managed check（失败则中止）
3. TIP rebase = cache_compiler_tip_rebase_from_current_r1（失败则中止）
4. 非 `--no-publish` 时 scope refresh

**覆盖限制**：该入口 **不是**「一条命令更新全系统」下载器；11 步管线仍属契约/BINDINGS，下载主入口需沿 handbook/R2，本轮不补造。

| 主题 | 契约要求 | 实现证实 |
|---|---|---|
| INDEX_WEIGHT | 管理检查 | `apply_download=false`；**main 固定 return 0** — 退出码≠更新成功 |
| adjust_factor | 中断恢复 | wrapper 只转发；实现在 TASK_SCRIPT；state 关键词已定位，运行恢复未证 |
| external 物化 | phase 分发/接受 | 已列出 phase_* 与 main 行号；未调 API |
| FUND_NAV | get_extras 水位/去重/恢复 | 关键词命中已归档；未下载 |

详见 `UPDATE_CALLCHAIN_FULL.json` / `UPDATE_CHAIN.csv`。

## 3. 统计勿混
- remaining 轴条数继承 1440（约 304）= 多轴待办条数，**不是** 304 个独立数据缺口。
- 四项：实体证据已记；catalog 缺口仍在；内容全量未验收。

## 4. 回测/正式更新
仍不执行。ACCEPTANCE=false。
