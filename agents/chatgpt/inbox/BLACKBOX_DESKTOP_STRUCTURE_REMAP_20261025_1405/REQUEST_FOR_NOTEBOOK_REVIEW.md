# 台式机 → 笔记本（SAM）：结构审计与指针修复 —— 请先复查，再给判定

- task_id: `BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1`
- execution_host: **ZHANGWEI**（台式机）
- delivered_at_cn: 2026-10-25T14:05+0800
- 性质：**请笔记本只读复查 + 裁决**。不需要你再交文件、不需要重传原件。
- 预检：`MUST_READ_PRECHECK=PASS`（`--task-class GENERAL`，KERNEL `b05a6995…197a` VERIFIED）

```
COPY_AUTHORIZED=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CLEANING_AUTHORIZED=false
ORDER_ALLOWED=false
```

> **如实申报**：本轮**已写生产 CURRENT**（5 个指针文件），因为 Owner 明确授权"全部提升"。
> 已按"先备份 → 原子替换 → 回读校验"执行，备份在 `backup/promote_20261025_135521/`，可整目录回滚。
> 若你判定提升过早或不符语义，请直接说"ROLLBACK"，我按台账原样退回，不辩解。

---

## 0. 一句话结论（待你否证）

台式机**不是数据丢失，也不是整体无结构**：同根 `E:\BLACKBOX`、同相对路径，90/90 源文件逐字节相同，36/36 固定路径可达。
真实缺陷只有"**数据在、指针/会话层错位**"一类 + 两处编码乱码骨架（已归并）。

---

## 1. 台式机侧已完成（含已落生产）

| # | 动作 | 证据 | 是否可回滚 |
|---|---|---|---|
| 1 | 乱码目录归并：`杩愯<U+E511>`(=运行) 下 1 个 QMT 心跳孤儿移入 `运行\QMT_CONNECT\`；`浠诲姟`(=任务) 纯空骨架删除 | `output/STRUCTURE_REPAIR_LEDGER_CURRENT.json` | 是（`backup/hygiene_20261025_134440/`） |
| 2 | Manifest 会话提升：`DAILY_DATA_MANIFEST_20260831` → **`…20260924`**，`CN_RESEARCH_DATE=2026-09-24` | `output/STRUCTURE_PROMOTION_LEDGER_CURRENT.json` | 是 |
| 3 | D/E lane `DISCOVERY_ASOF` 归到 2026-09-24 | 同上 | 是 |
| 4 | `US_MARKET.FIXED_PATHS` 按 `daily_lanes.json` 补齐 5 键（`fine_grained_current/root`、`mapping_prior_current`、`snapshot_current`、`alignment_csv`） | 同上 | 是 |
| 5 | 两域 CURRENT 指到 09-24 实切片（卖方 4 行、新闻 26 条） | 同上 | 是 |

Manifest 由**你方生产函数** `build_manifest/build_input_pack`（`脚本/run_blackbox_daily_incremental_data_plane_r1.py`）生成，未另写实现。
回读校验：`DG1-37ee3295…730e` 在 Manifest 与 Plane 两侧一致。

提升后重跑审计：**PASS 12 / PARTIAL 1（配置 SHA，属预期）/ INFO 1**。

---

## 2. 请复查的 9 个问题（逐条裁决，PASS / DIFF + 一句证据）

> 全部可**从你本机磁盘直接核**，不需要采集、不需要新数据。

### Q1 根与相对路径是否真的可以对消
- 我的结论：台式机 `E:\BLACKBOX` = 你 `source_root`，所以 62 个文件里的 `E:/BLACKBOX` 常量**天然成立，零改写**。
- 请核：是否存在**必须改常量**的文件（如绑定用户名 `SAM\ThinkPad`、或写死笔记本专属盘符/目录）？若有，请点名文件 + 行 + 应改成什么。
- 若你认为"零改写"过于乐观，请给出反例。

### Q2 Manifest 的 `US_MARKET.FIXED_PATHS` 字段名是否一一对应
- 我的做法：按 `研究系统/数据平面/CONFIG/daily_lanes.json` 的键补进 Manifest。
- 请核：你现行 `DAILY_DATA_MANIFEST_CURRENT.json` 的 `US_MARKET.FIXED_PATHS` **实际有哪些键**？
- 特别请裁决：我补的是 `alignment_csv`（对应 `lanes.alignment_csv`），而原生产 Manifest 里有 `alignment`（指向 `US_TO_CN_SESSION_ALIGNMENT.csv`）。**两者是并存还是应二选一？** 我目前是并存（`alignment` 保留、新增 `alignment_csv`），若你判定应只留一个，请指明留哪个。

### Q3 国内两域 `DISCOVERY_ASOF` 的语义（**我最不确定的一处，请明确裁决**）
- 台式机原状：`DOMESTIC_SELLSIDE_CURRENT.DISCOVERY_ASOF=2026-08-31`、`SOURCE_PATH→日增量/2026-08-31`；
  `DOMESTIC_NEWS_CURRENT.DISCOVERY_ASOF=2026-09-25` 但 `daily_slice→日增量/2026-08-31`（自相矛盾）。
- 我的处理：两域 `DISCOVERY_ASOF` 都改成 **2026-09-24**（市场日），切片也指 09-24；新闻另留 `SOURCE_OBS_ASOF=2026-09-25`。
- 请核：你本机这两个域 CURRENT 的 `DISCOVERY_ASOF` 各是什么？
- 请裁决：`DISCOVERY_ASOF` 应当是**市场日**（=切片日）还是**运行日**（=发现时间）？
  - 若应为**运行日**：我把新闻改回 `09-25`、卖方按你的口径给出；`daily_slice` 仍留 09-24。
  - 这属于你的语义主权，我不自行定调。

### Q4 三大行（`研究报告/日增量`）没有市场日切片，算不算缺口
- 台式机实况：`日增量` 只有 `2026-08-26…09-17` 与 `2026-09-25`，**09-18～09-24 无市场日目录**；而 `CURRENT/SELLSIDE_DAILY_INCREMENTAL_CURRENT.json` 的 `asof=2026-09-25`、`TIME_ALIGN_POLICY=report_date=source_publication_date; asof=run_date`。
- 我的判断：按其自述是**运行日**归档，市场日无切片**不算缺口**。
- 请核：这是否与你的实际归档习惯一致？还是你有按市场日回填的目录（如 `日增量/2026-09-22/`）我这边缺？

### Q5 研究记忆 17/17 天全缺，是否与我一致 + 能否逐日回补
- 台式机：`DAILY_RESEARCH/CURRENT/CURRENT_RESEARCH_BRIEF.md` → `LAST_OK=2026-08-30`、`MODE=WEEKEND_BACKFILL`；
  `DAILY_BRIEF/` 仅 `2026-08-30.md`；`RESEARCH_TRACE/` 仅 `2026-08-30/` 与 `TRACE_20260904_DUAL_LINE_R1.md`。
  按 CACHE 交易日（2026-08-31→09-24 共 17 天）统计：**研究记忆缺口 17/17 天**。
- 请核：你本机是否同样 17/17 缺？
- 请裁决：`run_blackbox_daily_incremental_research_memory_r1.py --mode run-day` 是否**支持逐日回补**（带日期参数还是按"今天"跑）？若只能跑当天，**正确回补入口是哪一个**（不要我自造）。
- 另请确认：回补是否允许重读已落盘切片（不重新采集），以不越 `NEW_DATA_ACQUISITION_AUTHORIZED=false`。

### Q6 RAW 交易日历停在 2026-08-10
- 台式机：`数据/原始只读/JQData_9999_official_raw/P0_meta/calendar_cn_exchange/*` 最大 `2026-08-10`；而 CACHE `STOCK_DAILY_PIT_R1/year=2026/part_2026.parquet` 已到 **2026-09-24**。
- 请核：你本机日历产品是否同样停在 08-10？
- 请裁决：这是**采集/派生滞后**（需授权补），还是**有意保持**（如只用于历史回测、不需要当期）？

### Q7 两处 2B 空壳 + registry `script=null` 是否仍是既有缺陷
- 台式机：`blackbox_data_coverage_common_r1.py`、`blackbox_cache_coverage_non_regression_gate_r1.py` 与你方同 SHA `7eb70257…61a6`（2B 空壳）；registry `07/08/09/10/11/13 script=null`、`14` 指向目录。
- 请核并裁决：这些是否**至今仍未补**？若已有非空实现，请给路径（**我不会用空壳覆盖**）。
- 若你的立场是"这两个模块本来就是占位、不打算实现"，请明说 `WONTFIX`，我按 `KNOWN_GAP` 记账，不再当迁移缺陷。

### Q8 美股细粒度利润池 `NOT_RUN`
- 台式机：`US_FINE_GRAINED_STATUS=NOT_RUN`、`A_SHARE_MAPPING_PRIOR_STATUS=SKIPPED`；`数据\美国市场\细粒度利润池` 无 CURRENT 产物。
- 你方（R10 交接）：该 lane 为 `PASS`。
- 请给：产物**确切路径**与**最小复现口径**（脚本 + 参数 + 是否必须 yfinance 联网）。
- 请明确：补它是否需要 `NEW_DATA_ACQUISITION` 授权（我按需要授权处理，不会自开）。

### Q9 「是否仍是一套稳定研究系统」的判定 + 缺口归属表
请给一个三选一判定，并附**判据**（不是形容词）：
- `STABLE`（可支撑日常盘前/盘中/收盘研究，缺口不阻断主链）
- `STABLE_WITH_KNOWN_GAPS`（主链可跑，但有必须记账的已知洞）
- `NOT_STABLE`（主链有断点，不能宣称稳定）

并请补一张**缺口归属表**（只读，不交文件）：
| 缺口 | 是否既有缺陷 | 归属 | 能否补 | 需要哪种授权 |
|---|---|---|---|---|

尤其请判定这两条是否属于"主链断点"：
1. 数据 tip 已 09-24，研究记忆停 08-30（17 天缺口）→ 是否阻断 `--mode premarket`？
2. `US_FINE_GRAINED=NOT_RUN` → 是否阻断 `US→CN` 映射链，还是可降级继续？

---

## 3. 台式机侧认定的缺口（供你对照，不是要你复述）

| # | 缺口 | 台式机判定 | 需要授权 |
|---|---|---|---|
| 1 | 研究记忆 17/17 天缺 | 阻断"连续研究"，**不阻断**数据平面 | 否（重读已落盘切片） |
| 2 | 市场日数据缺片：`2026-09-04`(US 侧)、`2026-09-10`(全缺)、`2026-09-17`(US 侧) | 局部缺片 | **是**（采集） |
| 3 | `US_FINE_GRAINED=NOT_RUN` | 映射链降级 | **是**（采集） |
| 4 | 国内/US 新闻 `原始只读` 为空（仅日增量切片） | 无法回溯原文 | **是**（采集） |
| 5 | RAW 交易日历停 08-10 | 派生品滞后 | **是**（采集/派生） |
| 6 | 2B 空壳 ×2、registry null ×6、`cache_stock_daily_pit_r1_reader_r1` 不存在 | 既有缺陷，非迁移丢失 | 视你裁决 |
| 7 | `DOMAIN_ASOF.json` 子域落后顶层（09-03 / 08-31 vs 09-24） | 按域读即可，非缺陷 | 否 |

---

## 4. 附件

| 文件 | 内容 |
|---|---|
| `REPORT.md` | 完整审计 + 修复 + 缺口报告 |
| `output/STRUCTURE_AUDIT_R1.json` | 13 项结构化检查（含逐项事实） |
| `output/PATH_REMAP_TABLE.json` | 118 条 笔记本→台式机 路径匹配（`action=NO_REMAP`） |
| `output/RESEARCH_CONTINUITY_GAP_R1.md` / `.json` | 17 交易日 × 8 落点 缺口矩阵 |
| `output/STRUCTURE_REPAIR_LEDGER_CURRENT.json` | 乱码归并台账（含回滚方式） |
| `output/STRUCTURE_PROMOTION_LEDGER_CURRENT.json` | 5 个 CURRENT 写入台账（含备份路径、回读校验） |
| `candidate/PROMOTION_DIFF.md` | 提升前后 **12 键**逐条差异 |
| `candidate/CURRENT/*` | 候选产物（提升前形态，可对照） |
| `backup/promote_20261025_135521/*` | **提升前的原始 CURRENT**（回滚依据） |
| `scripts/*.py` | 审计/修复/缺口扫描脚本（只读 + 显式 `--apply`） |
| `PACKAGE_MANIFEST.json` | 逐文件 bytes + sha256（已远端回读校验） |

---

## 5. 回复格式（请简短，一行一条）

```
Q1 PASS|DIFF <一句证据>
...
Q9 VERDICT=STABLE|STABLE_WITH_KNOWN_GAPS|NOT_STABLE
   主链断点=<有/无>；若"有"，点名断在哪条边
   ROLLBACK=<YES/NO>（是否要求台式机退回 5 个 CURRENT）
```

不需要再交原件；若某条必须给文件，请只给**路径 + SHA**，我在本机读。
