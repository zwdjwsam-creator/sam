# NOTEBOOK_HANDOVER — BLACKBOX 原运行约定（源机 SAM 只读）

task_id: BLACKBOX_NOTEBOOK_RUNTIME_RULES_HANDOVER_20261020_1900  
execution_host: SAM  
computername: SAM  
user: ThinkPad  
observed_at_local: 2026-10-20T19:00+08 (approx delivery)  
work_root: E:\BLACKBOX  
COPY_AUTHORIZED=false  
R9LP_RO cleanup: NOT_RUN（另有 pending_task，本交接不执行）

Evidence class legend: **FILE** = 磁盘文件/日志证实；**HABIT** = 原操作习惯（口令/惯例）；**UNKNOWN** = 本轮未证实。

---

## 0. 主机核验

| 项 | 值 | 类 |
|---|---|---|
| COMPUTERNAME | SAM | FILE |
| 工作区 | E:\BLACKBOX（存在 HAND.txt / AGENTS.md / .venv） | FILE |
| 冒充风险 | 本机 hostname=SAM，非 ZHANGWEI | FILE |

---

## 1. 现行启动 / 必读顺序 / Cache-First / 日期价格口径 / 研究续跑

### 权威入口（现行，非归档聊天）

| 层级 | 路径 | 作用 | 类 |
|---|---|---|---|
| Kernel（唯一 alwaysApply） | `E:\BLACKBOX\.cursor\rules\BLACKBOX_KERNEL_ALWAYS_APPLY.mdc` | 磁盘 HAND/CURRENT/Resolver 权威；先 TASK_CLASS→Manifest 预检；禁止下单/猜路径/打印密钥 | FILE |
| Agent 入口指针 | `E:\BLACKBOX\AGENTS.md` | 按任务类指向 MUST_READ / 回测门 / 日增 / Research OS / FREEZE R2 等 | FILE |
| HAND 顶层索引 | `E:\BLACKBOX\HAND.txt` | append-only 指针；含 FULL_DATA_UPDATE_SCOPE、CACHE_CURRENT、日增 SW_L123 等 | FILE |
| Manifest | `E:\BLACKBOX\契约\必读\MUST_READ_MANIFEST_CURRENT.json` | 任务类必读清单（Kernel §3） | FILE |
| 预检 | `E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py --task-class <CLASS>` | 未 PASS 禁止执行 | FILE |
| 存在性 | `E:\BLACKBOX\脚本\blackbox_data_absence_gate_r1.py` | 空表 ≠ NO_DATA | FILE |

### 数据 / Cache-First / 日增

| 主题 | 权威 | 类 |
|---|---|---|
| 「每日增量」六 Lane 唯一含义 | `.cursor/rules/blackbox_daily_incremental_data_plane.mdc` + `研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json` | FILE |
| 全量/增量范围 CURRENT | `运行/BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json`（本机 asof/`data_asof`=**2026-09-24**；cache_release=`BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_...`） | FILE |
| Cache 发布指针 | HAND → `数据/回测缓存/CURRENT_CACHE_RELEASE.json` | FILE |
| 清洗必须防穿越 | HAND / `blackbox_download_must_clean_antileak` 规则链 | FILE |
| Research OS 状态入口 | `脚本/run_blackbox_research_os.py --mode status`；日增 `--mode daily_incremental [--run]` | FILE |
| 研究策略自动跑 | `脚本/run_blackbox_master_research_autorun_r1.py`；摘要仅 `研究系统/CURRENT/MASTER_RESEARCH/MASTER_RESEARCH_SUMMARY.txt` | FILE |
| FREEZE | `研究系统/BLACKBOX_MASTER_RESEARCH_OS_FREEZE_R2.md`（R2 SUPERSEDES R1） | FILE |
| 连续研究记忆 | `DAILY_RESEARCH/CURRENT/CURRENT_RESEARCH_BRIEF.md`（次日先读） | FILE |
| 回测因果 | `KNOWN_AT <= SIGNAL_TIME < FILL_TIME`（AGENTS §4） | FILE |
| 价格平面 | `blackbox_backtest_price_plane_gate_r1.py`：历史 PRE_PIT；实盘另字段 RAW_REAL_PRICE | FILE |

### 现行 vs 归档 / 记忆盘

- **现行**：磁盘 `HAND.txt` / `*/CURRENT/*` / Manifest SHA 一致产物。  
- **归档**：`任务\` 下历史任务包、旧 sealed、agent-transcripts — **不自动注入**（Kernel）。  
- **禁止**：把聊天/AI 记忆当规则；`HAND_READ=YES` 不能覆盖 SHA FAIL_CLOSED。

### 记忆盘中真正影响运行的包（本机可见）

- `数据/回测缓存/` + CURRENT_CACHE_RELEASE（Cache 切片）  
- `研究系统/数据平面/CURRENT/`（日增 Manifest）  
- `运行/*_CURRENT.json`（范围/权限/日增看板）  
- `DAILY_RESEARCH/CURRENT/`（连续研究短文）  
- `.cursor/rules/*.mdc` + `规则库/hand_hard_rules/`  

类：FILE（存在）+ HABIT（运行时优先读 CURRENT 而非全历史）。

---

## 2. 日增六 Lane → 清洗 → cache → 研究：实际调度

### 命令入口（文件证实）

```
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\run_blackbox_research_os.py --mode status
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\run_blackbox_research_os.py --mode daily_incremental [--run]
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\run_blackbox_unified_data_research_orchestrator_r2.py --mode status|night
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\run_blackbox_master_research_autorun_r1.py --mode run --today-first-run
```

### Windows 计划任务

本轮 `schtasks /Query` 用 BLACKBOX/research/daily/master/incremental 过滤，**未见专用 BLACKBOX 日增计划任务名**（仅系统无关命中）。  
→ 调度形态结论：**以 Cursor/人工口令 + 脚本入口为主**；计划任务 **UNKNOWN（未证实有活跃 BLACKBOX 任务）**。

### E:\BLACKBOX 外的启动/环境

| 位置 | 证据 | 类 |
|---|---|---|
| `E:\BLACKBOX\cursor_ai_stack\START_DOUBLE_AI_TASK.ps1` | IDE 曾执行双 AI 启动（终端可见） | FILE/HABIT |
| `C:\LAN_SHARE_REPORT\` | R9/HUB 旁路产物，非业务日增调度器 | FILE |
| 源机 `.venv` | 解释器绑定在 `E:\BLACKBOX\.venv`（ThinkPad 用户机历史路径习惯） | FILE |

**不要**：把源机计划任务/密钥导出到台式机；不要本轮启动日增或策略。

### 最近有效 run 证据（文件）

- Manifest：`DAILY_DATA_MANIFEST_CURRENT.json` — `CN_RESEARCH_DATE=2026-09-24`，`BUILD_TIME=2026-09-25T04:08:21+0800`，`ALL_LANES_READY=YES`  
- FULL_DATA_SCOPE CURRENT：`generated_at_cn=2026-09-25T04:07:35+0800`，`data_asof=2026-09-24`，`operational_readiness=PASS`  

类：FILE。

---

## 3. Python 环境 / 依赖可复现依据

| 项 | 值 | 类 |
|---|---|---|
| 解释器 | `E:\BLACKBOX\.venv\Scripts\python.exe` → **Python 3.12.10** (MSC v.1943, 64-bit) | FILE |
| venv | 存在于 `E:\BLACKBOX\.venv` | FILE |
| 项目根 `requirements*.txt` / `uv.lock` / `poetry.lock` | 本轮浅扫 **未见项目根正式清单**（仅 venv site-packages 内模板 pyproject） | FILE → **无正式根清单** |
| 原约定 | 源机用固定 `.venv`；路径含本机盘符/用户习惯；台式机应自建 venv，勿复制绝对路径硬编码 | HABIT + FILE |

不安装、不重建、不输出凭据。

---

## 4. cache tip 2026-09-24 vs DAILY_RESEARCH LAST_OK=2026-08-30

### 源机当前对应文件

| 流 | 文件 | 日期字段 | 类 |
|---|---|---|---|
| 日增数据平面 / Cache tip | `研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json` | `CN_RESEARCH_DATE=2026-09-24`；`manifest_id=DAILY_DATA_MANIFEST_20260924` | FILE |
| 全量范围 CURRENT | `运行/BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json` | `data_asof=2026-09-24`；cache_release 同 tip 族 | FILE |
| 研究连续短文 | `DAILY_RESEARCH/CURRENT/CURRENT_RESEARCH_BRIEF.md` | **`LAST_OK=2026-08-30`**；`RESEARCH_DATE=2026-08-30`；`AS_OF_MARKET_DATE=2026-08-28`；文内有 `CORRECTION_20260903` 附录 | FILE |
| BRIEF 文件 mtime | 同上 | LastWriteTime ≈ 2026-09-10（磁盘） | FILE |

### 是否同一流程？

- **否**：日增六 Lane→清洗→Cache 发布 推进到 **2026-09-24**。  
- 研究 BRIEF/连续记忆停在 **2026-08-30 LAST_OK**（周末回填 MODE），之后仅有 09-03 校正附录，**不等于** cache tip 同日研究已跑完。  
- 硬门（章程）：JQ tip=清洗=Cache 对齐后才允许 RESEARCH；外源须 `aligned_to_jq_asof`。故 tip 新、BRIEF 旧 = **研究续跑未跟上数据平面**，不是“迁移丢了 BRIEF”。  
- 停更记录：无单独“停研公告”文件被本轮读到；以 BRIEF 字段与 Manifest 日期差为证。类：FILE + 规则 FILE。

### 台式机对照

- 对照同路径 CURRENT 文件：Manifest/SCOPE tip 与 BRIEF LAST_OK **允许不同**；勿把 BRIEF 旧说成 cache 失败。  
- 续跑：先读 FREEZE R2 + `run_blackbox_master_research_autorun_r1.py` 门，勿抢跑摘要。

### 小样本行情查询（不联网更新）

建议只读本地（Cache-First / 禁止默认连聚宽拉日线）：

```
E:\BLACKBOX\.venv\Scripts\python.exe -u -c "print('use local cache resolver / DAILY_DATA_MANIFEST CN_RESEARCH_DATE=2026-09-24')"
```

具体 OHLC：经 `blackbox_data_access_resolver` / 本地日线优先规则（`blackbox_local_daily_ohlc_first`）查 **asof≤2026-09-24** 的 cache/清洗产物；**本轮未执行实查**（只读交接、不启动更新）。类：规则 FILE；样本数值 UNKNOWN（未跑）。

---

## 5. BLACKBOX_ENGINES 与「杩愯/浠诲姟」类目录

### E:\BLACKBOX_ENGINES

- 本机：`Path('E:/BLACKBOX_ENGINES').exists() == **False**`  
- 类：FILE（源机当前无此根）。  
- 说明：R9 台式机目标映射里曾把 D 源映到 `E:\BLACKBOX_ENGINES\...`；那是**目标机布局**，不是源机 SAM 现存依赖树。业务链依赖以 `E:\BLACKBOX` 内 数据/缓存/脚本/研究系统 为准。

### 疑似编码目录（杩愯 / 浠诲姟）

- 控制台/错误解码下可见乱码名；UTF-8 下列出存在正常中文业务目录，例如 **`任务`** 明确存在。  
- 同时存在若干显示异常的顶层名（控制台 mojibake），**未对本轮做全树递归**。  
- 类型/来源：多为历史 GBK/控制台代码页显示问题或旧写入；**不能**在未核对身份前改名/删除。  
- 类：FILE（存在中文业务目录）+ UNKNOWN（每个乱码项的精确 NTFS 名与是否 junction 未逐条 OpenFile 证明）。

**应避免**：批量改名“修复编码”、删除疑似乱码目录、把台式机 ENGINES 路径硬套回源机。

---

## 操作说明（给台式机 AI，简洁）

1. 先读台式机已落盘的同名 CURRENT/HAND 副本；缺则对照本交接路径，勿发明第二套日增含义。  
2. 数据 tip 用 Manifest/SCOPE 的 **2026-09-24**；研究续跑看 BRIEF **LAST_OK=2026-08-30** 与 FREEZE 门，二者分开陈述。  
3. 用 Python 3.12 + 本地 venv；不要假设源机 `.venv` 可拷贝即用。  
4. 不要创建/依赖源机不存在的 `E:\BLACKBOX_ENGINES`。  
5. 不要执行 R9LP_RO 清理（pending 另任务）；本包只读交接。  
6. COPY_AUTHORIZED=false；不启动日增/策略/下单。

---

## pending（明确未做）

- `R9_NOTEBOOK_REMOVE_TEMP_R9LP_RO_20261020_1625`：本交接 **NOT_RUN**，保留 READY_LIMITED_SHARE_CLEANUP_AWAITING_ACK。
