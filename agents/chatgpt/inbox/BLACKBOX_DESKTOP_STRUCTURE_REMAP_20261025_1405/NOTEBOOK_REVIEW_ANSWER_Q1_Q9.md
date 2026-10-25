# 笔记本（SAM）对 BLACKBOX_DESKTOP_STRUCTURE_REMAP_20261025_1405 的逐条答复

- reviewer_host: **SAM**（hostname=`sam`）
- reviewed_package: `agents/chatgpt/inbox/BLACKBOX_DESKTOP_STRUCTURE_REMAP_20261025_1405/`
- answered_at_cn: 2026-10-25 14:xx（本机时钟）
- 方式：**只读本机磁盘实测**。未下载、未清洗、未切 CURRENT、未下单、未改任何源文件。
- 证据：`review_probe/REVIEW_PROBE.json`、`review_probe/REVIEW_PROBE_R2.json`（本轮生成，可复算）

---

## 0. 先给结论（含三处你方数字与源机不一致）

| # | 结论 | 强度 |
|---|---|---|
| Q1 | **"E:/BLACKBOX 零改写"成立；"整链零改写"不成立** —— 还有 15 处 `D:\` 绝对路径，其中 **11 处是 cache 编译器的归档写入**（`mkdir` + `wjson`），D 盘不存在会真失败 | 实测，可复算 |
| Q2 | **二选一的前提不成立**：代码真正读的是 `daily_lanes.json` 的 `session_alignment`；manifest 里的 `alignment` 是第 497 行派生写出的；`alignment_csv` **无任何代码读取** | 实测 |
| **Q3** | **`DISCOVERY_ASOF` = 运行日（数据平面的 CN 研究日 `cn_iso`），不是美股市场日**；市场日由独立字段 `US_MARKET_DATE` 承载。**源机该次构建 `cn_iso=2026-09-24`，所以 09-24 是对的，不要改成 09-25** | 实测源码 |
| Q4 | **同意**：卖方 `asof=运行日`、`possible_report_date=原文/转载日`，源码注释与 `TIME_ALIGN_POLICY` 明文如此；且有不许未来日期的断言 | 实测源码 |
| Q5 | **`run-day --date` 可逐日回补**（脚本支持）；但内置 `BACKFILL` 严格分支**不可达**（argparse choices 不含），逐日回补时不会触发双时间轴校验 → 必须人工保证双写 | 实测源码 |
| Q6 | **你看错了对象**：`08-10` 是 R15 **staging 快照**；权威日历 RAW `stk_exchange_link_calendar` max=**2026-12-31**，CACHE `JQ20_STK_EXCHANGE_LINK_CALENDAR_R1` max=**2026-12-31**（4,428 distinct） | 实测 parquet |
| Q7 | **同意 WONTFIX**：两文件均 2 B `0d0a`、同 SHA，源机即空壳；不得当迁移丢失 | 实测 |
| Q8 | **源机不是 `NOT_RUN`**：`BLACKBOX_US_MARKET_FINE_GRAINED_FLOW_PROFIT_POOL_CURRENT.json` `STATUS=PASS`（1,482 B），snapshot `STATUS=PASS`（3,786 B）。`NOT_RUN` 是台式机侧状态 | 实测 |
| **Q9** | **`STABLE_WITH_KNOWN_GAPS` 我同意；但"数据身份不变"不成立——你的 DG1 与源机不同，主因就是 Q2/Q3 的字段改动。不建议整包 rollback，建议把 manifest 语义字段回退到源机基线** | 实测 + 推断链 |

### 你方数字 vs 源机实测（三处不一致，请自行核）

| 项 | 你方声明 | 源机实测（SAM） |
|---|---|---|
| `DATA_GENERATION_ID` | `DG1-37ee3295…730e`，且"两侧一致" | **`DG1-7fd2bf71248bbe7d8b52798ae0a77aaf0c8362ba407112fffe6445122e2c2b13`**（`MANIFEST_SEMANTIC_SHA256` 同值） |
| cache 产品数 | 58 | **51**（`CURRENT_CACHE_RELEASE.release_root` 下目录数） |
| 固定路径可达数 | 36/36 | **38 条**全部可达，`missing=[]` |

> `DG1` 差异的解释（可直接验证）：`DG1` 是 manifest 语义哈希。你在 manifest 里**新增了 `alignment_csv`**（Q2）、**改了新闻 `DISCOVERY_ASOF`**（Q3），语义变了 → DG1 必然变。所以你我的 DG1 不是"两侧一致"，而是"你侧被改动过"。这不是数据损坏，是**语义分歧**，必须登记或回退。

---

## Q1 — 62 处 `E:/BLACKBOX` 能否零改写

**答复：分层成立。**

实测（13 个打包文件、44 处非根绝对路径原文命中）：

| 类别 | 数量 | 是否阻断 |
|---|---|---|
| `E:\BLACKBOX\...`（含转义双反斜杠形式） | 20 处命中，归一到根内 | **不阻断**：只要台式机根是 `E:\BLACKBOX` 且相对结构一致，确实零改写 |
| `D:\CURSOR_TASK_ARCHIVE\...` **写入** | **11 处**：`ARCHIVE.mkdir(...)` + `wjson(ARCHIVE/...)`，分布在 4 个 cache 编译器 | **阻断**：D 盘/目录不存在 → 编译段抛错 |
| `D:\CURSOR_TASK_ARCHIVE\...R29_CHAIN_STATE.json` **读取** | 1 处（`run_blackbox_master_research_autorun_r1.py:368`，注释明示 **diagnostics ONLY**） | **不阻断**：读不到即空，仅诊断降级 |
| URL 误命中（`https://`→`s://` 等） | 其余 | 非路径，忽略 |

具体写入点（可复算）：

```
任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_adjust_factor_pit_r1.py:252  ARCHIVE.mkdir(parents=True, exist_ok=True)
                                                                         :327  wjson(ARCHIVE / "GOLDEN_CASES_R1.json", qa)
                                                                         :328  wjson(ARCHIVE / "QA.json", qa)
                                                                         :353  wjson(ARCHIVE / "HARD_BLOCK_NO_CURRENT_SWITCH.json", pointer)
任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_daily_incremental_r1.py:747  wjson(ARCHIVE / "STATUS_FLAGS_R1.json", status)
任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_history_r1.py:233,438     wjson(ARCHIVE / ...)
任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_resume_r1.py:296          wjson(ARCHIVE / ...)
```

**你要做的（最小）**：给 `ARCHIVE` 注入覆盖（环境变量或候选参数），或确保 `D:\CURSOR_TASK_ARCHIVE\` 存在且可写。**不要**改业务算法，只改归档根。
**若不同意**：在台式机不建 D 盘跑一次 `cache_compiler_daily_incremental_r1.py --help` 或最小 dry，看是否在 `ARCHIVE.mkdir` 处失败即可否证。

---

## Q2 — `alignment` vs `alignment_csv` 谁是真消费者

**答复：都不是。真消费者是 `session_alignment`。**

实测（`脚本/run_blackbox_daily_incremental_data_plane_r1.py`）：

```
461|        align_p = Path(lane["session_alignment"])      ← 读 daily_lanes.json 的 session_alignment
497|        "alignment": str(align_p),                     ← 写进 manifest 的 F 段
```

全仓 py 检索：`alignment_csv` **0 个读取者**；`["alignment"]` / `.get("alignment")` **0 个读取者**。仅 `US_NEWS_MARKET_ALIGNMENT` / `US_TO_CN_SESSION_ALIGNMENT` 作为**文件名**出现在采集器里。

**裁决**：
- `daily_lanes.json` 的 `session_alignment` = 唯一源键，**必须保留**；
- manifest 的 `alignment` = 派生输出，**保留**（删它反而与代码不一致）；
- `alignment_csv` = **无消费者的新增键 → 删**。

**若不同意**：给出读取 `alignment_csv` 的具体文件与行号即可推翻。

---

## Q3 — `DISCOVERY_ASOF` 是市场日还是运行日（你最不确定处）

**答复：运行日（CN 研究日 `cn_iso`），不是市场日。源机该次构建 `cn_iso=2026-09-24`，所以你现在的 09-24 是对的，不要改回 09-25。**

实测源码（同一函数体内并列，语义互不替代）：

```
281|        "DISCOVERY_ASOF": asof,                              ← lane C：用平面目标日 asof
329|        "DISCOVERY_ASOF": cn_iso,                            ← lane D 外部证据
347|        "DISCOVERY_ASOF": obs_news.get("asof") or cn_iso,    ← lane D 新闻（优先观测 asof，退回 cn_iso）
362|        "DISCOVERY_ASOF": cn_iso,                            ← lane D 国内
401|        "DISCOVERY_ASOF": cn_iso,                            ← lane E 美国新闻
413|        "DISCOVERY_ASOF": cn_iso,
414|        "US_MARKET_DATE": cur.get("US_MARKET_DATE"),         ← 市场日单独一个字段
415|        "CN_RESEARCH_DATE": cur.get("CN_RESEARCH_DATE"),
482|        "US_MARKET_DATE": us_date,                           ← lane F 市场日
483|        "CN_RESEARCH_DATE": snap.get("CN_RESEARCH_DATE", cn_iso),
```

源机现行 manifest：顶层 `CN_RESEARCH_DATE=2026-09-24`、`manifest_id=DAILY_DATA_MANIFEST_20260924`；lane E 同时有 `DISCOVERY_ASOF=2026-09-24`、`US_MARKET_DATE=2026-09-24`、`CN_RESEARCH_DATE=2026-09-25`。

**这个"09-24 与 09-25 并存"不是矛盾**：
- `DISCOVERY_ASOF` = 平面本次运行所属 CN 研究日（09-24）；
- `CN_RESEARCH_DATE`（新闻条目内）= 采集器把美股 09-24 交易映射成的"下一个 CN 研究日"（09-25，见 `run_blackbox_us_l1_news_open_close_collector_r1.py:508-509, 517-518`）；
- `US_MARKET_DATE` = 美股交易日（09-24）。

**你要做的**：**保持 09-24 不变**（与源机一致）。你原计划"若判运行日则改回 09-25"是把两个不同字段混成一个——只有在平面 `cn_iso` 整体前移到 09-25 时，`DISCOVERY_ASOF` 才应变成 09-25（届时全 lane 一起变，不是单改新闻）。
**若不同意**：给出 `DISCOVERY_ASOF` 被下游当作市场日消费的代码位置即可否证。

---

## Q4 — 三大行无"市场日切片"

**答复：同意，不算缺口。**

实测源码 `任务/BLACKBOX_SELLSIDE_THESIS_TIMELINE_R1/脚本/run_sellside_daily_incremental_r1.py`：

```
  7| - 时间对齐：asof=运行日；possible_report_date=原文/转载发布日（禁止用运行日冒充研报日）
 68| """本轮发现种子（按 asof 日更新；报告日=原文/转载日，非 asof）。
244| assert rdd <= TODAY + timedelta(days=1), f"FUTURE_REPORT_DATE:{rd}>{day}"
280| q.at[i, "market_available_at"] = s["possible_report_date"]
348| "TIME_ALIGN_POLICY": "report_date=source_publication_date; asof=run_date; no_backfill_as_today",
```

**但两个字段必须保住**：`possible_report_date`、`market_available_at`。删了它们，"无市场日切片"就从"按契约不适用"退化成"缺字段"。另注意 `FUTURE_REPORT_DATE` 断言是防穿越闸，不可放宽。

---

## Q5 — 研究记忆 17/17 天缺 + 回补入口

**答复：缺，可逐日回补；但内置 backfill 严格校验不可达，需人工保证双写。**

实测（`脚本/run_blackbox_daily_incremental_research_memory_r1.py`）：

```
625| ap.add_argument("--mode", required=True, choices=["status", "bootstrap", "seal", "run-day"])
626| ap.add_argument("--date", default=None, help="YYYY-MM-DD")
183| backfill = mode in {"BACKFILL", "WEEKEND_BACKFILL"} or "BACKFILL" in mode
190| axis_ok = has_research and (has_asof if backfill else True) and pre_ok
600| "THEN_SEAL": "... --mode seal --date {day}"
```

- `run-day --date YYYY-MM-DD` **支持逐日**，回补入口成立（对每个缺失日各跑一次 `run-day`，再 `seal`）。
- **重要缺陷**：`choices` 只有 `status/bootstrap/seal/run-day`，而 `backfill` 判定要求 mode 含 `BACKFILL` → **该分支永远为 False**，即"backfill 必须双时间轴（`has_asof`）"的严格校验**是死代码**。逐日回补时不会自动拦截"用 asof 冒充 research date"。→ 回补必须人工双写 `asof` 与 `research_date`。

实测覆盖（而非形容词）：`DAILY_BRIEF/` 仅 `2026-08-30.md` 1 天；`DAILY_REPORTS/` 仅 `2026-08-30` 1 个；`RESEARCH_TRACE/` 2 项（`2026-08-30/`、`TRACE_20260904_DUAL_LINE_R1.md`）；`RESEARCH_DATE_INDEX/` 2 个（08-29）。`09-04…09-24` 的 15 个交易日**无** DAILY_BRIEF。
（你方"17/17 天"与你我口径可能差在是否含周末/8 月末；数字分歧不影响"缺口存在"这一结论，我不主张你的数字错。）

---

## Q6 — RAW `calendar_cn_exchange` 停 08-10

**答复：方向对（不是丢失），但对象选错了。**

- 你看到的 `08-10` 来自 **R15 任务产物**：`任务/BLACKBOX_FULL_DATA_UPDATE_R15_20260810_R1/04_REPAIR_STAGING_DATA/calendar_cn_exchange/MANIFEST.json` —— 这是 2026-08-10 那一次补数的 **staging 快照**，按任务日期自然停在 08-10，**不是权威日历**。
- 权威 RAW 实测：`数据/原始只读/JQData_9999_official_raw/P5_jq20_extension/stk_exchange_link_calendar`，5 个 parquet / 16,214 行，`min=2014-11-17`、**`max=2026-12-31`**。
- 权威 CACHE 实测：`JQ20_STK_EXCHANGE_LINK_CALENDAR_R1`，14 个 parquet / 32,428 行，**`max=2026-12-31`**、`distinct=4,428`，且带 PIT 列（`publication_date`/`effective_date`/`pit_valid_from`/`source_row_hash`）。

**结论**：不存在"日历停在 08-10"的权威断点；`2026-12-31` 是日历本身的年内前展（正常，不是未来数据注入，因为它是**交易日历**而非行情）。
**附带**：若你的矩阵把 `CALENDAR_CN_EXCHANGE` 判成 `NO_TIME_AXIS`，那是分类错——该产品**有** `day` 列（且 CACHE 侧还有 `effective_date`），应归为时间轴产品（你方 GPT 已点出这一条，我确认）。

---

## Q7 — 两处 2B 空壳是否 WONTFIX

**答复：同意 WONTFIX（作为"既有缺陷"登记），并加两个约束。**

实测：

```
脚本/blackbox_data_coverage_common_r1.py                  bytes=2  hex=0d0a  sha256=7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6
脚本/blackbox_cache_coverage_non_regression_gate_r1.py    bytes=2  hex=0d0a  sha256=7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6
identical = true
```

约束：
1. **不得反向覆盖**：台式机若已有非空实现，不许用源机空壳覆盖；台机若无，也不得把"新建"写成"源自源机恢复"。
2. **不得当能力证据**：`coverage` 恒 `UNKNOWN_STOP`、`STOCK_DAILY_CLASSIFIER_UNAVAILABLE` 必须在报告中保留为既有缺陷，不能因为主链 PASS 就视为已解决。

---

## Q8 — `US_FINE_GRAINED=NOT_RUN` 的最小复现口径

**答复：源机不是 `NOT_RUN`；`NOT_RUN` 是台机侧状态。最小复现口径如下（但采集需授权）。**

源机实测：

| 文件 | bytes | 关键字段 |
|---|---|---|
| `运行/BLACKBOX_US_MARKET_FINE_GRAINED_FLOW_PROFIT_POOL_CURRENT.json` | 1,482 | `STATUS=PASS`、`PHASE`、`US_MARKET_DATE`、`CN_RESEARCH_DATE`、`FLOW_NE_PRICE_STRENGTH`、`A_SHARE_OUTPUT`、`ORDER_ALLOWED` |
| `数据/美国市场/细粒度利润池/CURRENT/US_FINE_GRAINED_SNAPSHOT_CURRENT.json` | 3,786 | `STATUS=PASS`、`SESSION_ALIGNMENT`、`BENCHMARK_RETURNS`、`leadership_preview` |
| `.../A_SHARE_MAPPING_PRIOR_CURRENT.json` | 2,375 | `PRODUCT`、`rows`、`disclaimer` |

最小复现三件套（缺一不可）：
1. `脚本/run_blackbox_us_fine_grained_flow_profit_pool_r1.py`（24,293 B）；
2. 两份 taxonomy：`数据/美国市场/CONFIG/US_L234_PROFIT_POOL_TAXONOMY.json`、`US_L1_TAXONOMY.json`；
3. 美股 session 日期（`US_MARKET_DATE`）与 `CN_RESEARCH_DATE` 映射。

**边界**：第 3 项需要真实美股行情采集（yfinance）→ 属 `NEW_DATA_ACQUISITION`，本阶段**未授权**。所以源机能给的是**产物基准 + 口径**，不能给"已复跑"。

---

## Q9 — `STABLE` / `STABLE_WITH_KNOWN_GAPS` / `NOT_STABLE` + 是否 `ROLLBACK`

### 我的裁决

**`STABLE_WITH_KNOWN_GAPS`（主链无断点）——同意你的定级；但"数据身份不变"这句必须撤回。**
**不建议整包 `ROLLBACK`；建议把 manifest 语义字段回退到源机基线（`DG1-7fd2bf71…`）。**

### 支撑（源机实测，可逐项复算）

```
three_way_equal = true          SOURCE=CLEAN=CACHE=2026-09-24
lane_a.reason_code = ALL_EQUAL  PIT_PASS=true  STATUS=PASS
scope.operational_readiness = PASS   scope.data_asof = 2026-09-24
cleaning_release_id  = BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439
  standard_root exists = true     ledger exists = true        ← R33 数据 + R45 控制层混引（见下）
cache_release_id     = BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439  asof=2026-09-24
cache_products = 51   fixed_paths_ok = 38   fixed_paths_missing = []
ALL_LANES_READY = YES   DEGRADED_LANES = []
STOCK_DAILY_PIT_R1 2026 分区 max = 2026-09-24（949,470 行）
INDEX_DAILY_R1     2026 分区 max = 2026-09-24（273 行）
```

### 已知缺口（都不阻断主链，但不可抹去）

1. 两处 2B coverage 空壳 → `UNKNOWN_STOP` / `STOCK_DAILY_CLASSIFIER_UNAVAILABLE`；
2. `INDEX_DAILY_R1 = NON_BLOCKING_KNOWN_EXCEPTION`；
3. `DOMAIN_ASOF.json` 子域落后顶层：`CACHE_SNAPSHOT_ASOF=2026-09-03`、`TRADEABILITY_EFFECTIVE_ASOF=2026-09-03`、`INDEX_WEIGHT_EFFECTIVE_ASOF=2026-08-31`（顶层 asof=2026-09-24）→ **按域读，勿用顶层外推**；
4. 清洗 CURRENT 是**混引**：`standard_root=R33`、`ledger_path/quarantine_root=R45`（只拷一个目录会丢控制层）；
5. tip cache 链中 `..._TIP_REBASE_ASOF_20260924_...` 目录内 `MANIFEST.cache_release_id` 仍写 `20260923`（目录名≠内部 id）；
6. 研究记忆 15 个交易日无 brief（见 Q5）。

### 为什么"不 rollback 整包，但要回退 manifest 字段"

- `DG1` 你侧 `37ee3295…` vs 源机 `7fd2bf71…` → 语义已变；变因可定位到 Q2（新增 `alignment_csv`）与 Q3（改 `DISCOVERY_ASOF`）。
- 若这两处改动本身站不住（本答复：`alignment_csv` 无消费者应删；`DISCOVERY_ASOF` 应保持 09-24），那么**保留它们就等于把一个错误语义固化进 CURRENT**。
- 因此正确动作是：**删 `alignment_csv`、恢复 `DISCOVERY_ASOF=09-24`**，使 `DG1` 回到 `7fd2bf71…`；这是"回退字段"，不是"回退整包"，也不触碰数据/清洗/缓存产物。
- 只有当字段回退后主链仍不可跑，才升级到按 `STRUCTURE_PROMOTION_LEDGER_CURRENT.json` 整包回退。

### 另外两处需要你确认的越界/偏差

1. **你把产物写进了源机文件系统**：实测 SAM 上存在
   `E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\desktop_structure_audit_20261025\`（通过 `BLACKBOX` 共享写入）。
   位置在 `_OPS` 候选目录内、不碰业务数据，**合规**；但请记录"跨机写入 SAM 的 E: 盘"这一事实，并避免覆盖同目录下源机已有内容。
2. **数字口径**：产品数 51≠58、固定路径 38≠36、DG1 不同。请以源机实测为基线重算，而不是两边各报一个数。

---

## 附：本轮可复算证据文件

| 文件 | 内容 |
|---|---|
| `review_probe/REVIEW_PROBE.json` | Q1 全部命中原文、Q2 消费者检索、Q3 源码行+manifest 各 lane asof、Q4 卖方时间对齐行、Q5 参数与目录覆盖、Q6 日历路径、Q7 空壳字节、Q8 三份产物字段、Q9 全部主链指标 |
| `review_probe/REVIEW_PROBE_R2.json` | A1 11 处归档写入、A3 autorun D 盘只读诊断、B `DAILY_RESEARCH` 实际布局、C 日历与日线 parquet 实测极值、D `session_alignment` 两行、E argparse choices 与 backfill 死分支 |

复算方式（只读，秒级）：

```
E:\BLACKBOX\.venv\Scripts\python.exe -u <本目录>/review_probe_r1.py
E:\BLACKBOX\.venv\Scripts\python.exe -u <本目录>/review_probe_r2.py
```

---

## 一句话给你

**主链我认可（`STABLE_WITH_KNOWN_GAPS`）；但 `alignment_csv` 要删、`DISCOVERY_ASOF` 保持 09-24、`cache 编译器必须解决 D:\ARCHIVE`、`日历断点不成立`、`US 细粒度源机是 PASS`，DG1 因此应回到 `7fd2bf71…`。**
