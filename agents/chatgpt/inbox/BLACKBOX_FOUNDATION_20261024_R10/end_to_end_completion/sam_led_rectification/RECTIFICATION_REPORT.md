# RECTIFICATION_REPORT — SAM 主导的台式机底座整顿（R1）

- task: `BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025`
- dispatch: `SAM_LED_DESKTOP_RECTIFICATION_20261025`
- lead: SAM（笔记本）· target: ZHANGWEI `E:\BLACKBOX`
- status: **SAM_HANDOFF_READY_FOR_DESKTOP_REVERIFY**
- 授权边界：`NEW_DATA_ACQUISITION_AUTHORIZED=false`、`CURRENT_SWITCH_ALLOWED=false`、`ORDER_ALLOWED=false`、`FULL_MIGRATION=false`

---

## 0. 一句话

**R15 → 原编译器 → 候选提交 → 原发布门探针，在 SAM 上首次作为「同一产物」贯通，12/12 verdicts PASS**；两个已批准的 D1/D2 修复已落地台式机并通过语义验证。卡死问题（junction 环）已定性并根治。

**但**：`LOCAL_RUN_EVIDENCE` 是在 **SAM 本机**跑出来的。按执行令第三节，台式机「运行成功」必须来自 ZHANGWEI 本机进程，所以这份证据**不能冒充**台机运行，台式机必须自己跑一次 `RUN_CHAIN_R1.py`。

---

## 1. 改了什么（全部可回滚）

| # | 文件（台式机路径） | 改动 | 理由 | 备份 |
|---|---|---|---|---|
| 1 | `candidate/run_r15_cleaning_replay.py` | 新增 junction 安全的**定向物化**；不再调用会跟环的 `hardlink_tree`；新增写路径 junction 硬门 | 原版 `hardlink_tree` 用 `rglob`，生产 `standard/` 有 junction 环 → 永不终止 | `.bak_sam_led_r6` |
| 2 | `tools/run_connected_pipeline.py` | R15 产物**成为**编译器的 `--cleaning-json`；新增 `LINEAGE` 同产物校验；`compiler_read_r15_tree`/`lineage_same_artifact` 进入 verdicts | 原版编译器读的是合成 `candidate/cc/CC_REPLAY_20260924`，pipeline 从未调用 R15 runner → 只是「各组件分别能跑」 | `.bak_sam_led_r7` |
| 3 | `脚本/run_blackbox_daily_incremental_data_plane_r1.py` | **D1** `--date` 只接受 `YYYYMMDD`/`YYYY-MM-DD`，非法在写入前非零退出；**D2** `--mode status` 改为只读（不跑 collector、不 publish），并对外部 9 个 CURRENT/STATE 做前后 digest 断言 | `--date 2026-09-24` 曾被切成 `2026--0-9-` 并建出坏目录；`--mode status` 曾重写 manifest/plane/pack/6 STATE/DAILY | `.bak_sam_led_20261025` |
| 4 | `sam_led_rectification/RUN_CHAIN_R1.py` / `.cmd` | 一次性台机执行包 | 让台式机不依赖笔记本会话即可复现 | 新增 |

文件字节：`run_r15_cleaning_replay.py` 25832 B / `sha256 2719c17ee…da1be1`；`run_connected_pipeline.py` 28893 B / `sha256 4964f27cc…b4e4ced6`；data-plane 41183→46492 B / `sha256 949e95c758…2849c7`。

---

## 2. 发现的两个真实缺陷（不是我的改动引入）

### 2.1 生产 cleaning release 是 junction 复合体，且存在真实环

实测（只读，`fsutil reparsepoint` + 单层列举）：

- `R33_…_20260924\standard` 的 9 个子项中 **8 个是 junction** → `R45_…_20260924`
- `R45` 的 7 个子项又 junction 回 `R33_…_20260923`，如此**倒退约 32 跳**，`factor` 终止于 `R39_ASOF_20260902`
- **分钟 parquet 层有真环**：`R33_…_20260923\price\A股_stock_1m\<…09-11…>.parquet` → `R45_…_20260910` → `R45_…_20260911` → 回到 `R45_…_20260910`（2 环）

后果：任何跟随 reparse point 的递归（`Path.rglob`、`Get-ChildItem -Recurse`、`os.walk` 默认）都会永久自旋。
**实测证据**：第一次跑 R15 时 PID 1624 单核满转 **25 分钟**、输出目录始终未创建、日志仅命令行 200 B。

⇒ 这解释了为什么「R15 的 `hardlink_tree` 从未在此环境跑通」。这是**既有结构缺陷**，不是迁移丢失。

### 2.2 传输会静默把 CRLF 归一成 LF

同一份 `run_connected_pipeline.py`，SAM 侧 28893 B（591 行全 CRLF）、台式机侧 28302 B（591 行全 LF），**文本完全一致**，差值恰好 591 B。

后果：我第一次的 data-plane 补丁用 LF 锚点去打 CRLF 文件 → `ANCHOR_FAIL`。已改为 EOL 自适应锚点。
⇒ 后续任何跨机字节比对都必须先归一化 EOL，否则会把「换行差异」误判成「版本差异」。

---

## 3. 贯通结果（SAM 本机，660 s，exit 0）

```
CONNECTED_PIPELINE_RESULT = PASS
verdicts: 12/12 true
  transport_gate_pass, tampered_date_blocked, self_cert_blocked,
  r15_cleaning_pass, compiler_read_r15_tree, lineage_same_artifact,
  compiler_hard_block_propagated, original_compiler_all_pass,
  replay_days_present_in_release, commit_consistent,
  same_input_replay_noop, production_current_untouched
```

| 环节 | 实测 |
|---|---|
| transport/gate | PROVENANCE=PASS，`SUPPLIER_COMPLETENESS=UNKNOWN`（无保存的供应商请求记录，**不自填 YES**） |
| R15 cleaning | PASS，5.6s，`R15_REPLAY_20260924_R3`，antileak_pass=true，2 个 retained 单元 |
| 定向物化 | 4 个子树：`price/stock_ohlcv_daily`(232) + `price/ETF_daily`(37) + `reference/index_daily`(37) + `factor/valuation`(48) |
| 编译器 | PASS，302s，`BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20261025_184500`，`seal_all_pass=True` |
| tip 门 | `STOCK_DAILY_PIT_R1.date_max = 2026-09-24 = asof`，rows_2026=959,896 |
| valuation | READY，222,042 行 / 48 源文件 |
| **LINEAGE** | `LINEAGE_OK=True` — retained parquet sha256 == R15 封版文件 sha256（逐文件） |
| 重放日 | 08-31: 5,212 行；09-01: 5,214 行 |
| commit | `c87b3a56…3983bc4`，verify CONSISTENT |
| 同输入重放 | `IDEMPOTENT_NOOP`，commit_id 不变 |
| 负控 | 日期篡改 → `SESSION_DATE_MISMATCH`；自证完整 → `ACQUISITION_COMPLETENESS_UNPROVEN`；坏 cleaning → 编译器 exit 2。三者 `BLOCKED_AS_EXPECTED` |
| 发布门探针 | `OPERATIONAL_READINESS=PASS`、`CURRENT_PUBLISH=ALLOWED`、`published=false`（dry-run，未写生产） |

### D1/D2 语义验证（SAM，字节与台机补丁后文件一致 `949e95c7…`）

| 用例 | 结果 |
|---|---|
| `--date 2026-09-24` | exit 0，`STATUS_MODE_READ_ONLY_OK` |
| `--date 20260924` | exit 0，只读 |
| `--date 2026--0-9-` | **exit 1，`INVALID_DATE_FAIL_CLOSED`**，未建目录 |
| `--date 2026-13-45` | exit 1，fail-closed |
| `--date 2026-9-4` | exit 1，拒绝 |
| `--date ""` | exit 2，拒绝 |
| 外部 9 文件 digest | 前后一致（`ALL_PASS=true`，扫描 40,001 项，`bad_dirs=[]`） |

---

## 4. 没做到 / 仍需输入（如实）

| # | 项 | 状态 | 具体缺口 |
|---|---|---|---|
| 1 | 台机本机运行证据 | **BLOCKED（待台机跑）** | 需 ZHANGWEI 执行 `RUN_CHAIN_R1.py` 产出自己的 `LOCAL_RUN_EVIDENCE.json` |
| 2 | 供应商分页完整性 | `UNKNOWN` | retained 语料**没有**保存 `query_cap` / `terminal_page` / 请求全集；不得自填 YES |
| 3 | 复权因子有效性 | **未证明** | 08-10 起的增量面 `factor` 恒为 1.0（Observation），且 17 份文件 `date` 为整型 0..299。成因未分离（请求 `fq` 参数 / SDK 返回结构 / 本地序列化 / 供应商内容）。**不据此断言必须重下** |
| 4 | V4 | **BLOCKED_INPUT_INCOMPLETE** | 复权同日输入、基准/锚点、历史股票池/ST 未满足；`diagnostic_only=true`，0 成交 0 订单，**不得当策略结论** |
| 5 | 分钟面 | 部分 | 可用 2026-09-11…09-24；09-03…09-10 该 reader 分支 `NO_DAY_SHARDS`。V4 直接分钟调用为 0，但 `get_current_data` 9 次快照语义未定 |
| 6 | 研究记忆 | 缺口 | 权威交易日 08-31…09-24 共 **17** 日，已覆盖 1（09-04），**缺 16**（不是 17/17） |
| 7 | 月末两日 | 候选有、CURRENT 无 | 08-31 / 09-01 在候选分区，生产 `CURRENT` 未切换（未授权） |
| 8 | `is_st` / 历史成分 | 未绑定 | 本地无源 |
| 9 | DG1 | `DIVERGENT_MODE_ONLY` | 台机 `DG1-373cf01d…`、源机 `7fd2bf71…`；差异仅在 `MODE=VERIFY_ONLY`（真实值，**未改成 INGEST**）。未动 `MANIFEST_SEMANTIC_EXCLUDE` |
| 10 | `BLACKBOX_DEST` 共享权限 | **风险** | 实测卸载后仍可匿名读；建议收紧（未擅自改权限） |

---

## 5. 可恢复方式

每个被改文件都在同目录留 `.bak_sam_led_*`：`r6`（R15 runner）、`r7`（pipeline）、`20261025`（data-plane）。
回滚 = 把 `.bak_*` 覆盖回原名。所有改动均未触碰生产 `CURRENT` / RAW / sealed / HAND。
