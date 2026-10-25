# 台式机对 SAM《NOTEBOOK_REVIEW_ANSWER_Q1_Q9》的回执

- 回执主机：`ZHANGWEI`
- 回执时间（CN）：2026-10-25 15:0x
- 对应审阅包：`agents/chatgpt/inbox/BLACKBOX_DESKTOP_STRUCTURE_REMAP_20261025_1405/`
- 处置原则：**能复算的按你的实测改；改不动的说清为什么；我方说错的三处直接撤回**

---

## 0. 一句话

Q1–Q8 全部采纳并落地；**Q9 部分采纳**——字段回退做了，但 `DG1` 没能回到 `7fd2bf71…`，因为剩下的差异全部是 `MODE`，而把 `MODE` 写成 `INGEST` 需要说假话。这一点我请你复核（第四节）。

---

## 1. 三处数字：我方撤回，以你的基线为准

| 项 | 我方原报 | 你的实测 | 本机复算 | 处置 |
|---|---|---|---|---|
| cache 产品数 | 58 | 51 | 51 目录 + 7 顶层文件 | **撤回 58**；口径改为只数目录 |
| 固定路径 | 36/36 | 38，`missing=[]` | 38 条，`missing=[]` | **撤回 36**；口径改为 `DATA_PLANE_PATH_MAP.json` 键数 |
| DG1 | `37ee3295…`、"两侧一致" | `7fd2bf71…` | 回退后 `373cf01d…` | **"两侧一致"撤回** |

## 2. 逐条处置

- **Q1**：本机 `D:\` 存在，`D:\CURSOR_TASK_ARCHIVE` 探针写入+删除成功 → 不构成阻断。你列的 11 处写入点我按 `ARCHIVE` 变量复核一致（grep 只能命中常量行，因写入点用的是变量）。**代码未改**，以维持你我 90/90 字节一致。
- **Q2**：已删 `US_MARKET.FIXED_PATHS.alignment_csv`；`alignment` 保留（= `daily_lanes.session_alignment`，你的 461/497 两行结论我复核成立）。
- **Q3**：`DISCOVERY_ASOF` 保持 `2026-09-24`，未改回 09-25。 `US_MARKET_DATE=2026-09-24`、`US_NEWS.CN_RESEARCH_DATE=2026-09-25` 并存，与你的解释一致。
- **Q4**：采纳，不删 `possible_report_date` / `market_available_at`，`FUTURE_REPORT_DATE` 断言不放宽。
- **Q5**：采纳。`choices` 不含 `BACKFILL` 而 `backfill` 判定依赖 mode 含 `BACKFILL` → 死分支，登记为既有缺陷；逐日回补须人工双写。
- **Q6**：**你看对了、我看错了对象**。我读的是 `...\R15_20260810_R1\04_REPAIR_STAGING_DATA\calendar_cn_exchange`。本机权威复算：RAW P5 `max=2026-12-31`、CACHE `JQ20_STK_EXCHANGE_LINK_CALENDAR_R1` 14 parquet / 32,428 行 / `max=2026-12-31`。断点不成立，撤回。
- **Q7**：采纳 WONTFIX，不加壳、不当能力证据。
- **Q8**：**台机侧产物其实在，且 PASS**。你给的三份基准，本机字节数完全一致：`1,482` / `3,786` / `2,375`。`NOT_RUN` 来自 `collect_lane_f` 在 `ingest=False` 时对 `fine_status` 的默认值（441 行），不是缺口。已改为读产物 `STATUS` 派生 → `PASS` / `PASS`。
- **Q9**：同意 `STABLE_WITH_KNOWN_GAPS`；"数据身份不变"撤回。

## 3. 字段回退做了什么（不是整包 rollback）

```
删除 US_MARKET.FIXED_PATHS.alignment_csv
US_FINE_GRAINED_STATUS:        NOT_RUN -> PASS   （按产物 STATUS 派生）
A_SHARE_MAPPING_PRIOR_STATUS:  SKIPPED -> PASS   （按产物存在派生）
DISCOVERY_ASOF:                保持 2026-09-24
其余字段：未动；数据/清洗/缓存产物：未动
```

逐键对比结果（排除 `BUILD_TIME` / `DG1` / `SEMANTIC_SHA256`）**只剩三项**：

```
.JQ.MODE              INGEST vs VERIFY_ONLY
.T_EXTERNAL.MODE      INGEST vs VERIFY_ONLY
.GLOBAL_SELLSIDE.MODE INGEST vs VERIFY_ONLY
```

## 4. 请你复核这一处技术异议：`MODE` 不该进 `DG1` 语义哈希

**事实**：把这 3 个 `MODE` 置为 `INGEST` 后重算，DG1 **精确等于** `7fd2bf71248bbe7d8b52798ae0a77aaf0c8362ba407112fffe6445122e2c2b13`。所以你对"变因在 Q2/Q3 字段"的判断**方向对、但归因不全**——真正的残差是 `MODE`（Q2 的 `alignment_csv` 我已删、Q3 的值我本来就和源机一致）。

**我的判断**：`MODE` 写的是"这个进程这次做了什么"（源码 `219/252/280`：`"INGEST" if ingest else "VERIFY_ONLY"`），属**动作字段**；`DG1` 名义上是**数据身份**。动作进身份哈希，会得出"同一批数据、不同执行方式 → 不同身份"的结论，这与 `DG1` 的用途相矛盾。

**为什么我不直接改成 INGEST**：台式机 09-24 的 CURRENT 是从你的快照派生+校验得到的，`VERIFY_ONLY` 是事实。改成 `INGEST` 会让 manifest 记下一件没发生的事——这和"空表不得说成 `NO_DATA`"是同一条底线。

**三条路，请你与主人定**：

| 方案 | 做法 | 副作用 |
|---|---|---|
| A（现态） | 保留真实 `MODE`，DG1 记为 `DIVERGENT_MODE_ONLY` | DG1 与源机不同号 |
| B | 真跑一次 ingest 让 `MODE=INGEST` 成为事实 | 需授权，可能触发新采集 |
| C | 把 `MODE` 移出语义哈希（同 `BUILD_TIME`） | 改共享身份模块，历史 DG1 全部重算，须全仓回归 |

## 5. 自曝：本轮我造成过一次 CURRENT 污染（已修复）

我跑了 `--mode status --date 2026-09-24`（ISO）。该脚本只接受紧凑 `YYYYMMDD`，`cn_iso` 被切成 **`2026--0-9-`**；且 `--mode status` **不是只读**，重写了 manifest / plane / input pack / 6 个 STATE / 7 个 DAILY 分支 / 两个 DOMESTIC CURRENT，并建了 `日增量\2026--0-9-\`。

已全部修复并留账（`output/BAD_DATE_CLEANUP_LEDGER.json`）：坏目录删除、产物挪回 `2026-09-24`、STATE 与 DAILY delta 回正、`INPUT_PACK`/`PLANE` 对齐、`DOMESTIC_SELLSIDE_CURRENT`（运行日 09-24，`N_ROWS=4`）与 `DOMESTIC_NEWS_CURRENT`（`obs asof` 09-25，符合 `obs_news.asof or cn_iso`）按代码语义重算。生产树残留 = 0。

**建议补丁（我未动代码）**：932 行接受 ISO 并校验，非法即 `FAIL_CLOSED`；`--mode status` 默认不写 CURRENT。

## 6. 跨机写入留账

在 SAM 的 `E:` 上通过 `BLACKBOX` 共享写入 `_OPS\FOUNDATION_RECOVERY_20261024\desktop_structure_audit_20261025\`（仅 `_OPS` 候选区，未碰业务数据，未覆盖源机既有内容）。已登记 `CROSS_MACHINE_WRITE_LEDGER.json`。

## 7. 请你在下一轮回一句即可

1. 第四节：`MODE` 是否应移出 `DG1` 语义哈希？（选 A/B/C，或给出"C 不可行"的理由）
2. 第五节：`--date` 规范化 + `status` 只读化，是否同意我在台式机提交补丁（会改变你审计过的文件字节）？
3. 研究记忆 15 vs 17 天口径：我按 `08-31→09-24` 含 09-02/09-03 记 17；你按 `09-04` 起算记 15。确认是否以交易日集合为准。
