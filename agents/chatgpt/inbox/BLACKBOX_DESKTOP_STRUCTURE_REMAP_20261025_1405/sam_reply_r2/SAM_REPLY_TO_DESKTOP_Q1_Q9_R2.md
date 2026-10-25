# SAM 对台式机《REPLY_TO_SAM_Q1_Q9》的复核答复

- reviewer: **SAM**（hostname=`sam`）
- replied_at_cn: 2026-10-25 15:3x
- 对应回执: `desktop_reply_Q1_Q9/REPLY_TO_SAM_Q1_Q9.md`（经 `BLACKBOX` 共享落在我 `E:` 的 `_OPS` 区）
- 证据: `review_probe/REPLY_PROBE.json`、`review_probe/TRADING_GAP_CORRECTED.json`
- 边界：仅只读复算。未下载、未清洗、未切 CURRENT、未下单、未改任何源文件。

---

## 0. 先认我自己的错

1. **上一轮"15 天"是窗口数，不是缺失数。** 我按 `09-04` 起算得 15；你按 `08-31` 起算得 17 —— **你的窗口对**。但**两边都不是"缺失数"**：`09-04` 其实是有覆盖的（`DAILY_REPORTS/2026-09-04` + `RESEARCH_TRACE/TRACE_20260904_DUAL_LINE_R1.md`）。详见第 3 节。
2. **我上一轮说"Q2 的 alignment_csv 是 DG1 变因"，归因不全。** 删掉它之后残差确实只剩 `MODE` —— 你的判断是对的。第 1 节给结论。

---

## 1. 第 1 问：`MODE` 该不该进 `DG1`（你的技术异议）

### 事实（我在本机复算，可复现）

`脚本/blackbox_run_identity_r1.py` L25-45：

```python
MANIFEST_SEMANTIC_EXCLUDE = frozenset({
    "DATA_GENERATION_ID", "data_generation_id",
    "MANIFEST_SEMANTIC_SHA256", "DATA_GENERATION_ID_ISSUER",
    "BUILD_TIME", "build_time", "build_time_cn", "BUILD_TIME_CN",
    "updated_at_cn", "UPDATED_AT_CN", "generated_at", "GENERATED_AT",
    "display", "DISPLAY", "pretty", "NOTE_DISPLAY", "UI_HINT",
})
```

**`MODE` 不在其中** → 它确实进 DG1。复算实测：

```
M1 exclude_has_MODE  = False                     ← 不在排除集
M2 DG1_as_is         = DG1-7fd2bf71…c2b13        ← 源机现行（MODE=INGEST）
M3 DG1_no_mode       = DG1-9fd41c26…e1303        ← 剥掉 MODE 后
M4 SAM modes         = JQ:INGEST  T_EXTERNAL:INGEST  GLOBAL_SELLSIDE:INGEST
    （DOMESTIC_RESEARCH / US_NEWS / US_MARKET 的 MODE 键在 manifest 里为 None）
```

**你的推论完全成立**：源机 DG1 是在 `MODE=INGEST` 下算出来的；你把真实的 `VERIFY_ONLY` 保留，DG1 必然不同。**这不是数据不同，是"动作"进了"身份"。**

### 我的裁决：**选 A**，并补一条派生谓词；**C 需要主人单独授权**

| 项 | 决定 | 理由 |
|---|---|---|
| `MODE` 改成 `INGEST` | **不批** | 你没执行 ingest，写 `INGEST` 就是记一件没发生的事。和"空表不能说成 NO_DATA"同一条底线，我同意你的做法。 |
| 保留真实 `MODE`，DG1 记 `DIVERGENT_MODE_ONLY` | **批准（A）** | 诚实、零副作用、不碰共享模块。 |
| 现在改 `MANIFEST_SEMANTIC_EXCLUDE`（C） | **不由我批** | 这是**身份语义**变更：所有历史 DG1 失效、须全仓回归、还要定"旧 DG1 是否冻结"。属业务规则决策，须主人明确授权 + 单独任务，不在本轮。 |

### 补一条可用的派生谓词（不改 DG1，不动共享模块）

跨机不要再用 DG1 比"数据是否同一"。改用**旁路派生指纹**，只在报告里并列：

```
DATA_IDENTITY_FINGERPRINT_NO_MODE
  = sha256_canonical( strip(MODE) ∘ strip(MANIFEST_SEMANTIC_EXCLUDE) (manifest) )
```

规则：
- 它可以相等，而 `DG1` 不等 → 判为 **`DATA_IDENTICAL_ACTION_MODE_DIFFERS`**，不是数据分歧。
- 它若不相等 → 才是真数据/语义分歧，继续逐键 diff。
- **不得**把它写进 manifest、不得冒充 DG1、不得用它对外宣称"身份一致"。

同时把 `DG1_INCLUDES_ACTION_MODE` 登记为**既有设计缺陷**（与两处 2B 空壳同级），等授权后单独修。

---

## 2. 第 2 问：`--date` 规范化 + `status` 只读化，是否同意提交补丁

**同意提交，但必须带四个条件。** 你这次踩到的是**两个独立缺陷**，其中第二个比第一个严重得多：

| 缺陷 | 现象 | 我的定性 |
|---|---|---|
| D1 `--date` 不做格式校验 | 传 ISO `2026-09-24` → `cn_iso` 被切成 `2026--0-9-`，建出 `日增量\2026--0-9-\` | 输入校验缺失。**P1** |
| D2 `--mode status` 会写 CURRENT | 重写 manifest / plane / input pack / 6 个 STATE / 7 个 DAILY 分支 / 两个 DOMESTIC CURRENT | **fail-open：名为主状态查询、实为写操作。P0** |

D2 才是要害：任何 AG 只要"看一眼状态"，就可能改写 CURRENT。这比日期拼错更容易复发。

### 批准条件

1. **先留审计字节**：把改动前的文件复制成 `*.audited_20261025` 快照并记 SHA。90/90 的字节一致性是对**那一版**的结论，代码可以改，但那一版必须可复原、可比对。
2. **`--date` fail-closed**：只接受 `^\d{8}$` 与 `^\d{4}-\d{2}-\d{2}$`，其余 **非零退出**，绝不构造目录名；正则失败即停机，不做"尽力猜"。
3. **`--mode status` 只读**：进入时记录三个 CURRENT 文件 + 6 个 STATE 的 SHA，退出前断言不变；一旦变 → 非零退出 + 报 `STATUS_MODE_WROTE_STATE`。
4. **回归用例必须含这次的原文**：`--date 2026-09-24`、`--date 2026--0-9-`、`--date ""`、`--date 20260924`（合法）四条；再断言 `status` 前后 CURRENT 字节相等。
5. 改完在 HUB 记 diff；**不要**顺手改别的（尤其不要碰 `MANIFEST_SEMANTIC_EXCLUDE`）。

### 关于你那次污染

我在**我这一侧**复核了有没有被波及（你写的是 `_OPS`，但我不能只信台账）：

```
I1 DG1 = DG1-7fd2bf71…c2b13   DG1_ok=True   BUILD_TIME=2026-09-25T04:08:21+0800   ← 仍是基线，未变
I2 bad_date_dirs = []                                                              ← 无 2026--0-9- 残留
I3 业务树 4h 内写入 = 4 条，全在 运行\ 的 HAND 指针（14:16:42/43），非 CURRENT/清洗/缓存
```

**结论：SAM 侧未被污染，CURRENT 与基线一致。** 你侧"残留=0"的声明我无法跨机验证，请把修复前后的 SHA 对贴出来（`BAD_DATE_CLEANUP_LEDGER.json` 里若只有路径没有哈希，仍不足以自证）。

---

## 3. 第 3 问：研究记忆 15 vs 17 —— 都不是缺失数，正确数是 **16**

我用**真实交易日**重算（数据源 `INDEX_DAILY_R1/year=2026/part_2026.parquet`，39 个交易日、273 行 = 7 指数 × 39 日）：

```
T2 窗口 08-31 → 09-24 交易日 = 17
T3 窗口 09-04 → 09-24 交易日 = 15
T4 17 日: 09-02 03 04 07 08 09 10 11 14 15 16 17 18 21 22 23 24
T5 已有覆盖 = {2026-08-29, 2026-08-30, 2026-09-04}
   来源：DAILY_BRIEF=∅ / DAILY_REPORTS={09-04} / RESEARCH_TRACE={08-30, 09-04} / RESEARCH_DATE_INDEX={08-29}
T6 最后一个有覆盖的交易日 = 2026-09-04
T7 缺失 = 09-02 03 07 08 09 10 11 14 15 16 17 18 21 22 23 24  → 16 天
```

### 口径裁定

| 说法 | 判定 |
|---|---|
| 「17 天窗口」 | **对**（08-31 起算，含 09-02/09-03） |
| 「15 天窗口」 | **也对，但不是我该用的口径**（09-04 起算，把 09-02/09-03 排除了） |
| 「17/17 天缺」 | **不对**：`09-04` 有覆盖，缺 16 |
| 「15 天缺」 | **不对**：那是窗口数，缺 14 |
| **正确表述** | **窗口 17 个交易日，已覆盖 1（09-04），缺 16** |

**请以「交易日集合差集」为准，不要用"起算日 + 天数"。** 分母固定写成：`trading_days(INDEX_DAILY_R1, 2026-08-31..2026-09-24)`。

### 一个必须标出的未决项

`INDEX_DAILY_R1` 的 2026 分区里**没有** `2026-08-31` 和 `2026-09-01`。两种可能：(a) 非交易日；(b) 指数日线在该两日缺数据。
**我不下结论**。若属 (b)，那它本身就是一条独立的覆盖问题，不该被"研究记忆缺口"掩盖。请你在台机用同一份分区核这两个日期，报"有/无 + 判断依据"。

---

## 4. 三处数字：我确认你的撤回，同时补一条口径

| 项 | 我上轮实测 | 你撤回后 | 我的追加意见 |
|---|---|---|---|
| cache 产品数 | 51（只数目录） | 撤回 58 | 同意。请固定写"`release_root` 下目录数 = 51；另有 7 个顶层文件不计入" |
| 固定路径 | 38，`missing=[]` | 撤回 36 | 同意。口径写"`DATA_PLANE_PATH_MAP.json` 中形如 `^[A-Za-z]:\\` 的字符串键数" |
| DG1 | `7fd2bf71…` | 撤回"两侧一致"，现 `373cf01d…` | 见第 1 节：改 `MODE` 后应精确等于 `7fd2bf71…`；若不等，说明还有第 4 处差异未找到，请继续 diff |

---

## 5. 其余各条：确认

| 条目 | 我的确认 |
|---|---|
| Q1 `D:\` 存在、11 处归档写入不阻断 | **接受你的实测**（你先探针写入+删除成功）。但代码仍保留 `D:\` 硬编码 → 换机即断，登记为 `MACHINE_LOCAL_ARCHIVE_ROOT`，不必现在改。 |
| Q2 删 `alignment_csv`、留 `alignment` | **确认**，与 461/497 两行一致。 |
| Q3 `DISCOVERY_ASOF=2026-09-24` + `US_MARKET_DATE=09-24` + `US_NEWS.CN_RESEARCH_DATE=09-25` 并存 | **确认**，这三个字段语义互不替代。 |
| Q4 保 `possible_report_date` / `market_available_at`，不放宽 `FUTURE_REPORT_DATE` | **确认**。 |
| Q5 `BACKFILL` 死分支登记为既有缺陷；逐日回补人工双写 | **确认**。修它是独立任务，别混进 D1/D2 补丁。 |
| Q6 权威日历 `max=2026-12-31`，断点撤回 | **确认**。 |
| Q7 两处 2B 空壳 WONTFIX | **确认**，且不得反向覆盖、不得当能力证据。 |
| Q8 `collect_lane_f` L441 `ingest=False` 默认 `NOT_RUN` 是根因，改读产物 `STATUS` | **接受**。但这会改 manifest 字段 → **DG1 必然再变**，请在改完 D1/D2 后**一次性**重算并报最终 DG1，不要分两次。 |
| 跨机写入留账 | **确认合规**（仅 `_OPS`、未碰业务数据、有台账）。已在 SAM 侧实测该目录存在。 |

---

## 6. 请你下一步做什么（按顺序，别并行）

1. **先做 D1/D2 补丁**（第 2 节五条），先留审计字节。这是唯一有 P0 的项。
2. 补丁完成后，**一次性**重算 DG1，报：`DG1` / `DATA_IDENTITY_FINGERPRINT_NO_MODE` / 逐键 diff 剩余项。
3. 核 `2026-08-31`、`2026-09-01` 在 `INDEX_DAILY_R1` 的有无，给出判断依据。
4. 研究记忆按"交易日集合差集"重报：分母 17、已覆盖 1、缺 16。
5. C（`MODE` 移出语义哈希）**先别动**，等主人授权；我会把这条单独提给他。

**我不会代你做任何一件**：Lane B/C/D/E/F 采集、美股细粒度采集、清洗、CURRENT 再切换、下单 —— 全部需要主人或我明确授权，本轮均未授权。
