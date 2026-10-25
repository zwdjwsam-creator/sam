# 执行 SAM Q1–Q9 裁决后的台式机终态（BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1）

- 执行主机：`ZHANGWEI`（台式机）
- 执行时间（CN）：2026-10-25 14:5x–15:0x
- 依据：`notebook_review\NOTEBOOK_REVIEW_ANSWER_Q1_Q9.md`（SAM，只读实测）+ `REVIEW_PROBE.json` / `REVIEW_PROBE_R2.json`
- 授权边界：本轮**只改 manifest 语义字段 + 修复我自己造成的一次写入事故**；未下载、未清洗、未切数据、未改业务代码、未下单
- 终态判定：`PASS`（8 项硬门全 true，见 `输出/AFTER_SAM_Q1_Q9_VERIFY.json`）

---

## 一、逐条执行结果

| # | SAM 裁决 | 台式机处置 | 终态 |
|---|---|---|---|
| Q1 | 整链零改写不成立：11 处 `D:\CURSOR_TASK_ARCHIVE` 写入 | **本机不成立为阻断**：`D:\` 存在、`D:\CURSOR_TASK_ARCHIVE` 探针写入+删除成功 | 非阻断；代码不动（保 90/90 字节一致） |
| Q2 | `alignment_csv` 无消费者，删；`alignment` 保留 | 已删 `US_MARKET.FIXED_PATHS.alignment_csv`；`alignment` 保留并复核 | 已执行 |
| Q3 | `DISCOVERY_ASOF` = 运行日，保持 09-24 | 保持 09-24（未改回 09-25）；市场日另看 `US_MARKET_DATE=2026-09-24` | 已符合 |
| Q4 | 三大行无市场日切片不算缺口；须保留 `possible_report_date` / `market_available_at` | 采纳，不删字段、不放宽 `FUTURE_REPORT_DATE` 断言 | 采纳不改 |
| Q5 | 可逐日回补；内置 `BACKFILL` 严格分支是死代码 | 采纳；登记为既有缺陷，回补须人工双写 `asof` / `research_date` | 采纳不改（不改生产脚本） |
| Q6 | 08-10 是 R15 staging；权威日历到 2026-12-31 | 我方看错对象，撤回；本机复算一致 | 已更正 |
| Q7 | 两处 2 B 空壳 WONTFIX | 采纳；不加壳、不当能力证据 | 采纳不改 |
| Q8 | 源机 `US_FINE_GRAINED=PASS`，`NOT_RUN` 是台机侧状态 | 台机产物实测本就在且 PASS → manifest 状态改由产物派生 | 已更正 |
| Q9 | 同意 `STABLE_WITH_KNOWN_GAPS`；撤回"数据身份不变"；回退 manifest 字段而非整包 rollback | 已回退字段（删 `alignment_csv` + 细粒度按产物派生成 PASS）→ **DG1 只差 3 个 MODE** | 部分达成，见第三节 |

---

## 二、三处数字口径：以源机为基线，我方全部撤回

| 项 | 我方原报 | 源机 | 本机复算 | 结论 |
|---|---|---|---|---|
| cache 产品数 | 58 | **51** | **51 个目录** + 7 个顶层文件 = 58 | 我方把文件也算进产品，撤回 58 |
| 固定路径可达 | 36/36 | **38**，`missing=[]` | `DATA_PLANE_PATH_MAP.json` **38 条**，`missing=[]` | 我方口径少 2 条，撤回 36 |
| `DATA_GENERATION_ID` | `DG1-37ee3295…` 且"两侧一致" | `DG1-7fd2bf71…c2b13` | 回退后 `DG1-373cf01d…` | "两侧一致"撤回，见第三节 |

> 计数口径固定为：产品数 = `release_root` 下**目录数**；固定路径 = `DATA_PLANE_PATH_MAP.json` 中 `E:` 绝对路径**键数**。

---

## 三、DG1 终态：`DIVERGENT_MODE_ONLY`（只剩 3 个 MODE 不同）

回退后与源机逐键对比（已排除 `BUILD_TIME` / `DG1` / `SEMANTIC_SHA256`）只剩：

```
.GLOBAL_SELLSIDE.MODE: source=INGEST      | desktop=VERIFY_ONLY
.JQ.MODE:              source=INGEST      | desktop=VERIFY_ONLY
.T_EXTERNAL.MODE:      source=INGEST      | desktop=VERIFY_ONLY
```

**成因已被证明，不是猜测**：把这三个 `MODE` 改成 `INGEST` 后重算，DG1 精确回到源机 `DG1-7fd2bf71248bbe7d8b52798ae0a77aaf0c8362ba407112fffe6445122e2c2b13`（见 `输出/DG1_REVERT_PROBE.json` → `probe_DG1`）。

**为什么没直接改成 INGEST**：`MODE` 是**动作字段**，代码在 `219/252/280` 行写的就是"本次进程是 ingest 还是 verify"。台式机这次 09-24 的 CURRENT 是我用源机快照派生+校验出来的（`VERIFY_ONLY` 是事实）；把它写成 `INGEST` 等于用一句假话去换一个哈希恒等，违反"空表不得说成 NO_DATA"的同一条底线。

**这是设计层问题，不只是口径问题**：`DG1` 名义上是**数据身份**（`DATA_GENERATION_ID`），却把**动作**（MODE）计入了语义哈希 → 同一批数据、不同执行方式，必然得出不同 DG1。三条可选路径：

| 方案 | 做法 | 代价 | 现状 |
|---|---|---|---|
| A | 保留真实 `MODE`，DG1 记为 `DIVERGENT_MODE_ONLY` 并登记 | DG1 与源机不同号 | **已落地（默认）** |
| B | 真跑一次 `--run`（ingest）让 `MODE=INGEST` 成为事实 | 需授权；可能触发新采集 | 未做 |
| C | 把 `MODE` 移出语义哈希（与 `BUILD_TIME` 同级） | 改共享身份模块，历史 DG1 全部重算，须全仓回归 | 未做，须主人+SAM 双签 |

> 结论：`data_identity` 与 `source` **语义上相等**（差异键只剩动作字段），但 **DG1 编号不相等**。这两句必须同时说，不能只说一句。

---

## 四、我在本轮执行中出过一次错（已修复，留账）

- 我执行 `--mode status --date 2026-09-24`（ISO 写法）。该脚本 `932` 行只接受紧凑 `YYYYMMDD`：
  `cn_iso = f"{cn_date[:4]}-{cn_date[4:6]}-{cn_date[6:8]}"` → 传入 ISO 得到 **`2026--0-9-`**。
- 更关键：`--mode status` **不是只读**，它重写了
  `CURRENT/DAILY_DATA_MANIFEST`、`DAILY_DATA_PLANE`、`INPUT_PACK`、6 个 `STATE/*`、7 个 `DAILY/*` 分支文件、两个 `DOMESTIC_*_CURRENT`，并新建了 `日增量\2026--0-9-\` 目录。
- 已修复（`输出/BAD_DATE_CLEANUP_LEDGER.json`）：产物挪回 `2026-09-24`、坏目录删除、STATE/DAILY delta 日期回正、`INPUT_PACK`/`PLANE` 对齐 manifest、两个 DOMESTIC CURRENT 按代码语义重算（卖方=运行日 09-24；新闻=`obs asof` 09-25）、`DAILY/2026-09-24/08_MANIFEST.json` 用现行 manifest 覆盖。
- 生产树残留 `2026--0-9-` = **0**；仅保留在 `备份/`、`输出/` 台账作为事故证据。
- **建议（未改代码，避免破坏 90/90 字节一致）**：932 行接受 ISO 并校验格式，非法即 `FAIL_CLOSED`；`--mode status` 默认不写 CURRENT。

---

## 五、本机 Q1 / Q6 / Q8 复算证据

```
D:\ 存在 = True        D:\CURSOR_TASK_ARCHIVE 可写 = True（写入后删除探针）
cache 日历  JQ20_STK_EXCHANGE_LINK_CALENDAR_R1: 14 parquet / 32,428 行 / max=2026-12-31（含 PIT 列）
RAW 权威日历 P5_jq20_extension/stk_exchange_link_calendar: 5 parquet / max=2026-12-31
US 细粒度   运行\BLACKBOX_US_MARKET_FINE_GRAINED_FLOW_PROFIT_POOL_CURRENT.json 1,482 B  STATUS=PASS
            ...\CURRENT\US_FINE_GRAINED_SNAPSHOT_CURRENT.json                    3,786 B  STATUS=PASS
            ...\CURRENT\A_SHARE_MAPPING_PRIOR_CURRENT.json                        2,375 B
```

`NOT_RUN` 的真实来源：`collect_lane_f` 在 `ingest=False` 时把 `fine_status` 默认成 `NOT_RUN`（441 行），**不是产物缺失**。已改为读产物 `STATUS` 派生 → `PASS/PASS`。

---

## 六、跨机写入登记（SAM 要求留账）

| 对象 | 方向 | 内容 | 合规判断 |
|---|---|---|---|
| `\\192.168.100.2\BLACKBOX\_OPS\...\desktop_structure_audit_20261025\` | 台机 → SAM 的 `E:` | 审计包 + 本轮回执（仅 `_OPS` 候选区） | 合规；未碰业务数据；不覆盖源机既有内容 |
| `...\notebook_review\` | SAM → 台机 | 只读读取答复与两份 probe | 只读 |

台账：`CROSS_MACHINE_WRITE_LEDGER.json`。

---

## 七、终态硬门（全 true）

```
DG1_recomputed == file == plane      True
manifest_id: manifest == plane == pack True
CN_RESEARCH_DATE: manifest/plane/pack 全 = 2026-09-24  True
alignment_csv 不存在 / alignment 存在 True / True
DATA_PLANE_PATH_MAP 38 条，missing=[] True
cache 产品目录 51                     True
verdict = PASS  | dg1_state = DIVERGENT_MODE_ONLY
```

## 八、仍未闭合（不阻断主链，台账保留）

1. `DG1` 与源机不同号 —— 差异仅 3 个 `MODE`，须主人选 A/B/C（第三节）。
2. `--date` 无格式校验 + `--mode status` 有写副作用 —— 建议补丁，未改。
3. 研究记忆：`DAILY_BRIEF` 仅 `2026-08-30`；`09-04…09-24` 15 个交易日无 brief（我方 17 天的口径含 09-02/09-03，SAM 15 天从 09-04 起算，两者均成立）。
4. `Q5` 的 `BACKFILL` 死分支、`Q7` 两处 2 B 空壳 —— 既有缺陷，不修。
5. `DOMAIN_ASOF.json` 子域落后顶层；清洗 CURRENT 混引 R33/R45；`TIP_REBASE` 目录名 ≠ 内部 id —— 均按域读，不外推。
