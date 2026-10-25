# 台式机结构 vs 笔记本(SAM)结构 —— 审计与修复报告 R1

- task_id: `BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1`
- 生成: 2026-10-25T13:45+08:00
- 对象: `E:\BLACKBOX`（台式机 ZHANGWEI） ← 蓝图 `SAM` 交付包（`FOUNDATION_RUNTIME_MAP.md` + `SOURCE_INDEX.json` + `DESKTOP_ADAPTATION.md`）
- 授权边界: 未下载 / 未清洗 / 未采集 / 未发布 CURRENT / 未下单
- 预检: `MUST_READ_PRECHECK=PASS`（`--task-class GENERAL`，KERNEL `b05a6995…197a` VERIFIED）

---

## 0. 一句话结论

**不是数据丢失，也不是"整体无结构"。** 台式机已经有笔记本的同一套结构（同根 `E:\BLACKBOX`、90/90 源文件逐字节相同、36/36 固定路径可达）。
真正的结构问题只有一类：**"数据在、指针/会话层错位"**，外加两处编码乱码骨架。**路径不需要大规模重匹配**——因为根盘符与相对路径都和笔记本一致。

| 判定 | 结果 |
|---|---|
| 需要改写 62 个文件里的 `E:/BLACKBOX` 硬编码？ | **不需要**（同根；见 §2） |
| 需要重建 `.venv`？ | **不需要**（本机已是 3.12.10 / MSC v.1943 / 64-bit） |
| 数据目录是否按笔记本结构在？ | **在**（RAW 20 个正式分区 + 8 个基础设施目录） |
| 结构缺陷 | 3 类（均已修）：会话层错位（Manifest 08-31）、2 个域 CURRENT 指错切片、2 个乱码目录骨架 |

---

## 1. 逐项实测（`输出/STRUCTURE_AUDIT_R1.json`）

| 检查 | 状态 | 事实 |
|---|---|---|
| `ROOT_IDENTITY` | PASS | SAM `source_root=E:\BLACKBOX` = 本机 `E:\BLACKBOX` |
| `CODE_SHA` | PASS | 90 个代码文件 **same=90 / diff=0 / missing=0** |
| `CONFIG_SHA` | PARTIAL | 28 个配置 **same=26 / diff=2**：`DAILY_DATA_MANIFEST_CURRENT.json`、`DAILY_DATA_PLANE_CURRENT.json`（本机 2026-10-25 08:22 以 `--date 20260831` 重写过） |
| `PATH_MAP_RESOLVE` | PASS | `DATA_PLANE_PATH_MAP.json` 36 条绝对路径 **缺失 0** |
| `CLEANING_CHAIN` | PASS | `cleaning_as_of=2026-09-24`；R33(数据) + R45(ledger/quarantine) 双目录皆可达；`content_root_sha256=966e92d0…b431` |
| `CACHE_CHAIN` | PASS | `asof=2026-09-24`，`release_root` 可达，58 个产品目录（含 `FUND_NAV_PIT_R1`） |
| `CACHE_ID_VS_DIRNAME` | PASS | 本机该 release 目录名与 `MANIFEST.cache_release_id` 一致（笔记本的 TIP_REBASE 名≠id 问题不在此目录） |
| `SESSION_CONSISTENCY` | 已修→PASS | 修复前 `manifest_id=…20260831` / `CN_RESEARCH_DATE=2026-08-31` vs `JQ cache_asof=2026-09-24`；现为 `…20260924` / `2026-09-24` |
| `DOMAIN_CURRENT_VS_SLICE` | 已修→PASS | 修复前 `D_DOMESTIC_SELLSIDE→08-31`、`D_DOMESTIC_NEWS` `daily_slice=08-31` 而 `asof=09-25`；现均指 09-24 实切片 |
| `MOJIBAKE_DIRS` | 已修 | 修复前 2 个 → 修复后 0 |
| `EMPTY_TOP_DIRS` | INFO | `downloads / tools / 下载 / 导出 / 日志 / 沙盒 / 笔记本` 为空（占位，非缺陷） |

---

## 2. 路径匹配（`输出/PATH_REMAP_TABLE.json`，118 条）

原则：**同根 + 同相对路径 ⇒ 只换前缀，不改文件**。

| 笔记本 | 台式机 | 动作 |
|---|---|---|
| `E:\BLACKBOX\脚本\…` | `E:\BLACKBOX\脚本\…` | NO_REMAP |
| `E:\BLACKBOX\任务\…` | `E:\BLACKBOX\任务\…` | NO_REMAP |
| `E:\BLACKBOX\研究系统\数据平面\CONFIG\daily_lanes.json` | 同 | NO_REMAP（改路径只改这里，不改代码） |
| `E:\BLACKBOX\配置\secrets\已验证\聚宽账号.txt` | 同路径，本机自备 | 绑定保留、内容不导出 |

> 早前 `桌面复刻包\HAND_REPLICATION_FROM_LAPTOP_R1\HAND_PATH_REMAP_PLAN.md` 写的是 `F:\BLACKBOX`，与现状不符（本机即 `E:`）。该文档已被本表覆盖，**不要按 F: 建目录**。

---

## 3. 本次已修（可回滚）

台账：`输出/STRUCTURE_REPAIR_LEDGER_CURRENT.json`；备份：`备份/hygiene_<时间戳>/`

| 项 | 原 | 处理 | 依据 |
|---|---|---|---|
| `杩愯<U+E511>`（= `运行` 的 UTF-8→GBK 误读） | 内含 `QMT_CONNECT/SESSION_HEARTBEAT_CURRENT.json`（174 B，2026-08-19，`order_attempted=false`） | 移入 `运行\QMT_CONNECT\`（目标原本不存在，无覆盖） | 内容为 QMT 会话心跳，属该目录 |
| `浠诲姟`（= `任务`） | 纯空目录骨架 `GITHUB_REPORT_UPLOAD_PACKAGE_NO_TOKEN_R1\repo_work\github_reports\20260708_074648\` | 删除；正式目录 `任务\GITHUB_REPORT_UPLOAD_PACKAGE_NO_TOKEN_R1\` 已含同名子树与全部真实文件 | 无文件损失 |

回滚：`python 脚本\repair_desktop_structure_r1.py --mode rollback --ledger 输出\STRUCTURE_REPAIR_LEDGER_<ts>.json`

---

## 4. 已授权并落地：CURRENT 指针提升（2026-10-25 13:55）

用户授权「全部提升」。执行：`--mode candidate` → `--mode promote --apply`（先备份 → 原子替换 → 回读校验）。
台账：`输出/STRUCTURE_PROMOTION_LEDGER_CURRENT.json`；备份：`备份/promote_<时间戳>/`

| 变更 | 原值 | 现值 |
|---|---|---|
| `manifest_id` | `DAILY_DATA_MANIFEST_20260831` | **`DAILY_DATA_MANIFEST_20260924`** |
| `CN_RESEARCH_DATE` | 2026-08-31 | **2026-09-24**（= JQ cache asof） |
| `DOMESTIC_RESEARCH.DISCOVERY_ASOF` | 2026-08-31 | **2026-09-24** |
| `US_NEWS.DISCOVERY_ASOF` | 2026-08-31 | **2026-09-24** |
| `US_MARKET.FIXED_PATHS` | 缺 5 键 | 按 `daily_lanes.json` 补齐（与笔记本 Manifest 同构） |
| `DOMESTIC_SELLSIDE_CURRENT` | `SOURCE_PATH→08-31` | **`→09-24`**（行数不变 4） |
| `DOMESTIC_NEWS_CURRENT` | `daily_slice→08-31` | **`→09-24`**，保留 `SOURCE_OBS_ASOF=2026-09-25` |

写入 5 个文件，全部先备份再 `os.replace` 原子替换：
`DAILY_DATA_MANIFEST_CURRENT.json`、`DAILY_DATA_PLANE_CURRENT.json`、`DAILY_RESEARCH_INPUT_PACK_CURRENT.json`、
`国内卖方/CURRENT/DOMESTIC_SELLSIDE_CURRENT.json`、`国内新闻/CURRENT/DOMESTIC_NEWS_CURRENT.json`

回读校验：`DG1-37ee3295…730e` 在 Manifest 与 Plane 两侧一致；`dg1_consistent=true`。
提升后重跑审计：`SESSION_CONSISTENCY=PASS`、`DOMAIN_CURRENT_VS_SLICE=PASS`，总体 **PASS 12 / PARTIAL 1（配置 SHA，属预期）/ INFO 1**。

Manifest 由生产函数 `build_manifest/build_input_pack` 生成，**未另写实现**；无数据内容改动。

---

## 5. 结构之外的真实缺口（不能靠"改路径"解决）

### 5.1 研究连续性矩阵（`输出/RESEARCH_CONTINUITY_GAP_R1.md`，只读）

交易日口径：CACHE `STOCK_DAILY_PIT_R1/year=2026` 实际 date（RAW `calendar_cn_exchange` 只到 2026-08-10，不可用）。

| 项 | 结果 |
|---|---|
| 窗口 | 2026-08-31 → 2026-09-24，17 个交易日 |
| 完全齐备 | **0 天** |
| 市场日数据缺口 | **2026-09-04（US 缺）、2026-09-10（全缺）、2026-09-17（US 缺）** |
| 研究记忆缺口 | **17/17 天全缺**（`DAILY_BRIEF` 仅 `2026-08-30.md`；`RESEARCH_TRACE` 仅 08-30 与 09-04 两处） |
| 三大行 | `研究报告/日增量` 仅 `…09-17 / 09-25`，无市场日切片；按其"运行日"语义不算缺口 |

### 5.2 其它缺口

1. **美股细粒度利润池 `NOT_RUN`**：`US_FINE_GRAINED_STATUS=NOT_RUN`，`数据\美国市场\细粒度利润池` 无 CURRENT 产物；笔记本侧是 `PASS`。需采集（未授权）。
2. **国内/US 新闻 `原始只读` 目录为空**：仅 `日增量` 有切片；回溯原文须回源采集。
3. **RAW 交易日历停在 2026-08-10**：`P0_meta/calendar_cn_exchange/*` 最大 08-10，而行情已到 09-24 → 日历产品滞后（派生品缺口，非迁移丢失）。
4. **既有缺陷（笔记本同样存在）**：两个 coverage 模块 2B 空壳；`cache_stock_daily_pit_r1_reader_r1` 本就不存在；registry `07/08/09/10/11/13 script=null`、`14` 指向目录。
5. **`DOMAIN_ASOF.json` 子域落后顶层**（09-03 / 08-31 vs 顶层 09-24）——按域读，勿外推。

### 5.3 补齐顺序（尚未执行）

1. 补市场日缺片（仅授权后）：Lane D/E/F 对应日 → 只写候选，不直接切 CURRENT。
2. 逐日补研究记忆：`脚本/run_blackbox_daily_incremental_research_memory_r1.py --mode run-day`，每日校验 `DAILY_BRIEF/<date>.md` + `RESEARCH_TRACE/<date>/` 双轨同时存在。
3. 全部补齐后 `--mode seal`，再跑 `研究 OS --mode premarket`。
4. 研究补齐**不得回改**数据平面 CURRENT（已对齐 09-24）。

---

## 6. 笔记本端口 5 问的台式机答案

1. **现行调度**：`schtasks` 仅 `BlackboxCheckTemp`，无 BLACKBOX 日增任务 → 与笔记本一致（人工/AG 口令驱动）。
2. **venv**：本机 `.venv` 已是 Python 3.12.10 / MSC v1943 / 64-bit，`pandas 2.3.3`、`pyarrow 21.0.0`；依赖快照在交付包 `meta/DEPENDENCIES_PIP_FREEZE.txt`。**无需重建**。
3. **BRIEF 停 08-30 vs tip 09-24**：数据平面到 09-24，研究记忆停在 08-30（`MODE=WEEKEND_BACKFILL`）；是"数据前进、研究未续跑"，不是有意停更。续跑入口：`脚本/run_blackbox_daily_incremental_research_memory_r1.py --mode run-day`（SSOT 见 HAND 第 15 条）。
4. **乱码目录**：`杩愯`=`运行`、`浠诲姟`=`任务`（UTF-8 字节被 GBK 解读）。前者 1 个孤儿心跳文件、后者纯空骨架，**均非重复 junction**，已按 §3 归并/清除。
5. **`E:\BLACKBOX_ENGINES` 硬依赖**：代码（`脚本/*.py` + `任务/**/*.py`）与配置/规则文本中 **0 命中 → NONE**。该目录存在（`backtest_lab` 等），但业务链路不依赖。

---

## 7. 复跑

```powershell
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 -u 任务\BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1\脚本\audit_desktop_vs_notebook_r1.py
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 -u 任务\BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1\脚本\repair_desktop_structure_r1.py --mode hygiene          # 计划
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 -u 任务\BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1\脚本\repair_desktop_structure_r1.py --mode candidate        # 生成候选
```
