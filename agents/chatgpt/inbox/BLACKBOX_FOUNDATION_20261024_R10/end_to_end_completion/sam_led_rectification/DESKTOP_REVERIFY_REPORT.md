# DESKTOP_REVERIFY_REPORT — 台式机（ZHANGWEI）本机独立复验

- from: ZHANGWEI（台式机）
- to: SAM（笔记本）
- dispatch: `SAM_LED_DESKTOP_RECTIFICATION_20261025`
- in_reply_to: `HANDOFF_TO_DESKTOP.md` / status `SAM_HANDOFF_READY_FOR_DESKTOP_REVERIFY`
- **结论：PASS**
- 证据来源：`LOCAL_RUN_EVIDENCE.json`，**ZHANGWEI 本机进程产出**，未使用笔记本那份
- 独立核验：`DESKTOP_INDEPENDENT_VERIFY.json` — **47/47 通过**（不复用 runner 的 verdict 布尔，全部从产物与文件系统重新推导）

---

## 1. 运行身份（证明是台机自己跑的）

| 项 | 值 |
|---|---|
| hostname | `ZHANGWEI` |
| interpreter | `E:\BLACKBOX\.venv\Scripts\python.exe` |
| python | 3.12.10 (MSC v.1943 64 bit) |
| started | 2026-10-25T19:17:59+0800 |
| finished | 2026-10-25T19:20:24+0800 |
| runner | `sam_led_rectification/RUN_CHAIN_R1.py` |
| runner exit | **0** |

## 2. 四步步骤结果

| 步骤 | exit | 耗时 | 判定 |
|---|---|---|---|
| A chain（R15 → 原编译器 → 提交 → 发布预演） | 0 | 104.2 s | PASS |
| B status `--date 2026-09-24` | 0 | 0.1 s | 接受 ISO，只读 |
| C status `--date 2026--0-9-` | **1** | 0.1 s | **fail-closed**，含 `INVALID_DATE_FAIL_CLOSED` |
| D status `--date 20260924` | 0 | 0.1 s | 接受紧凑格式，只读 |

`digests`：`after_status_iso == after_chain`、`after_bad_date == after_status_iso`、`end == after_bad_date` —— 9 个被监视文件（3 个 CURRENT + 6 个 STATE）**前后完全一致**，status 确实不写盘。

runner verdicts **8/8 true**。

## 3. 原链同产物（HANDOFF §3 逐项）

| 字段 | 期望 | 实测 |
|---|---|---|
| `CONNECTED_PIPELINE_RESULT` | PASS | **PASS** |
| verdicts true 数 | 全部 | **12/12** |
| `verdicts.lineage_same_artifact` | true | **true** |
| `verdicts.compiler_read_r15_tree` | true | **true** |
| `stages.compiler.seal_all_pass` | true | **true** |
| `stages.cleaning_r15.release_id` | `R15_REPLAY_20260924_R3` | **一致** |
| `LINEAGE.retained_batches[*].retained_equals_r15_sealed` | 全 true | **2/2 true** |
| `stages.commit.status` | PASS | **PASS**（`COMMITTED`，`seq=3`） |
| `stages.same_input_replay.status` | PASS | **PASS**（`IDEMPOTENT_NOOP`，commit_id 未变） |
| `PRODUCTION_CURRENT_WRITE` | NONE | **NONE** |
| `NEW_DATA_ACQUISITION` | — | **NONE** |

**关键边已真实存在**：编译器的 `--cleaning-json` 指向本次新建的 `R15_REPLAY_20260924_R3/RELEASE.json`，`compiler_read_standard_root` 指向同一 release 的 `standard`。不再是「清洗产物另放一处」的断链。

- R15 清洗：约 2 s，`release_content_root_sha256 = 3b88a0432158d11d…`
- 原编译器：44.2 s，exit 0，`seal_all_pass=True`
- `valuation READY rows=222,042`（48 源文件）；`SW_L1/L2/L3 READY parts=13`
- 发布门：`EVALUATED_NOT_PUBLISHED`，`published=false`，`production_CURRENT_written=false`

三个负控全部 `BLOCKED_AS_EXPECTED`：
- 篡改日期 → `SESSION_DATE_MISMATCH`
- 自证完整性 → `ACQUISITION_COMPLETENESS_UNPROVEN`
- 编译器硬阻断 → `exit_code=2`（日志在案）

## 4. R15 产物物理核验（防「看起来成功」）

| 子树 | 文件数 | 是否真实目录 | 说明 |
|---|---|---|---|
| `price/stock_ohlcv_daily` | 222 | 是（非 junction） | 硬链，抽样 `st_nlink=51`；文件名最新日 **20260924 = asof** |
| `price/ETF_daily` | 37 | 是 | 硬链 |
| `reference/index_daily` | 37 | 是 | 硬链 |
| `factor/valuation` | 65 | 是 | 硬链 |

- release 总体：368 文件 / 356,881,775 B，`.BLACKBOX_SEALED` 在位
- 重放日文件都在：`2026-08-31` ✓、`2026-09-01` ✓
- `production/CURRENT` 未被写；`switch_current=NOT_CALLED`、`patch_hand=NOT_CALLED`
- 台机 `数据` / `运行` 下 **无 `2026--*` 目录**（复验后再次全盘扫描确认）

## 5. 交付文件身份（含 EOL 归一）

| 文件 | 声明 sha16 | 台机实测 | 判定 |
|---|---|---|---|
| `candidate/run_r15_cleaning_replay.py` | `2719c17eec5589ac` | raw/CRLF = `2719c17eec5589ac` | 一致 |
| `tools/run_connected_pipeline.py` | `4964f27cc325c8e8` | raw/CRLF = `4964f27cc325c8e8` | 一致 |
| `脚本/run_blackbox_daily_incremental_data_plane_r1.py` | `949e95c758b2064c` | `949e95c758b2064c` | 一致 |

印证你说的 CRLF→LF 静默归一：这两个文件按 **LF 归一**算出来是 `014466be...` / `48b1192b...`（正是你 `CHANGE_INDEX` 里的值），按原始字节/CRLF 算与 `HANDOFF` 表格一致。**同一个文件两种算法给出「两个 sha」，以后核身份必须声明算法。**

三份回滚备份均在位：`.bak_sam_led_r6` / `.bak_sam_led_r7` / `.bak_sam_led_20261025`。

## 6. 我在台机侧做的两个动作（都已留痕）

1. **移走半成品 R15 release**：第一次启动被工具层中断，但 R15 清洗实际已在 19:12:00–19:12:02 完成并封版（368 文件）。按 `OPERATION_MANUAL §3` 把它移入
   `candidate/r15_releases/_prev_R15_REPLAY_20260924_R3_from_aborted_run_1911/`（**移动，未删除**），使本次通过的证据来自一次不中断的完整运行。这是 `HARD_BLOCK: candidate release exists` 的真实原因，不是代码回归。
2. **新增独立核验器** `DESKTOP_INDEPENDENT_VERIFY_R1.py`：不读 runner 的 verdict，自己重算 47 项（证据身份、9 文件 digest、交付 JSON 每一字段、R3 磁盘事实、坏目录扫描、备份在位、文件身份）。结果 47/47，`exit 0`。

## 7. 给你的三点观察（不影响本次 PASS）

1. `carry_forward.missing` 里记了 `price/stock_ohlcv_daily OSError FileNotFoundError`，但该子树最后以 222 个真实硬链文件落地了。**异常被吞掉，整体仍报成功** —— 建议把这个分支改成显式 `resolved_with_error`，否则以后「部分失败」会被当成「全成功」。
2. `OPERATION_MANUAL` 故障排查表写 `stock_ohlcv_daily 有 232 个文件`，台机实测 **222**。若 232 是含 sidecar/json 的口径，请在手册里写明。
3. 编译器台机 44.2 s、你 302 s。同机不同负载可以解释，但**别用耗时当判据**，判据应始终是 `seal_all_pass` / verdict。

## 8. 仍未解决（沿用你的清单，未擅自改）

1. 供应商分页完整性 `UNKNOWN`（retained 语料无请求记录；不得据此断言缺数）
2. 复权因子 2026-08-10 起恒 1.0、17 份文件日期为整数 0..299，成因未分离
3. **V4 `BLOCKED_INPUT_INCOMPLETE`**（`diagnostic_only=true`，0 成交 0 订单）—— 正式回测**未通过**，本次未触碰
4. 08-31 / 09-01 仅候选分区，生产 `CURRENT` 未切换（未授权）
5. `is_st` / 历史成分未绑定
6. `BLACKBOX_DEST` 卸载后仍可匿名读，建议收紧（未擅自改）

## 9. 权限边界（本次遵守）

`PRODUCTION_CURRENT_WRITE=NONE`、`NEW_DATA_ACQUISITION=NONE`、`published=false`、`ORDER_ALLOWED=false`。未跑 `--mode run` / `--mode full_day`，未调用 `publish_atomic(dry_run=False)`，未覆盖任何 `CURRENT_*`，未删除任何 release。

---

**verdict：台式机独立复验 PASS。** 证据 `LOCAL_RUN_EVIDENCE.json`（hostname=ZHANGWEI，runner exit 0）+ `DESKTOP_INDEPENDENT_VERIFY.json`（47/47）。V4 仍未通过，不并入本结论。
