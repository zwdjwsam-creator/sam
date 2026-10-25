# OPERATION_MANUAL — 台式机（ZHANGWEI）可照做的操作手册

- 适用：`E:\BLACKBOX`，解释器 `E:\BLACKBOX\.venv\Scripts\python.exe`
- 全部命令**在本机**执行（不要用笔记本的 Python 去读共享来冒充台机运行）
- 带 ⛔ 的动作**当前未授权**，不要执行

---

## 1. 环境自检（10 秒）

```cmd
cd /d E:\BLACKBOX
.venv\Scripts\python.exe -c "import sys,pandas,pyarrow;print(sys.version);print(pandas.__version__,pyarrow.__version__)"
```
预期：`3.12.x` + 两个版本号。
失败：`.venv` 损坏 → 按 `pyvenv.cfg` 记录的 Admin 解释器重建，**不要**只改 `home` 字段。

---

## 2. 只读状态查询（安全，随时可跑）

```cmd
.venv\Scripts\python.exe -X utf8 脚本\run_blackbox_daily_incremental_data_plane_r1.py --mode status --date 2026-09-24
```
预期：JSON 含 `"READ_ONLY": true`、`"WATCHED_UNCHANGED": true`，末行 `STATUS_MODE_READ_ONLY_OK`，exit 0。
**关键**：这条命令已改为**绝不写盘**。若你看到 CURRENT/STATE 的 mtime 变了，那是回归，立即停。

紧凑格式等价：
```cmd
.venv\Scripts\python.exe -X utf8 脚本\run_blackbox_daily_incremental_data_plane_r1.py --mode status --date 20260924
```

### 非法日期必须 fail-closed（这是验收项，不是可选项）

```cmd
.venv\Scripts\python.exe -X utf8 脚本\run_blackbox_daily_incremental_data_plane_r1.py --mode status --date 2026--0-9-
```
预期：**exit 非 0**，stderr/stdout 含 `INVALID_DATE_FAIL_CLOSED`，且 `E:\BLACKBOX\数据`、`运行` 下**没有**新建 `2026--*` 目录。
若 exit 0 或建出目录 → D1 未生效，停下报我。

---

## 3. 原链同产物流转（核心验收项）

```cmd
cd /d E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\sam_led_rectification
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 RUN_CHAIN_R1.py
```
或双击 `RUN_CHAIN_R1.cmd`。

预期（约 10–15 分钟，主要耗时在编译器 300 s 量级）：
- `LOCAL_RUN_EVIDENCE.json` 生成，`identity.hostname` 是 `ZHANGWEI`
- `verdicts` 里这 5 项必须为 true：`chain_exit_zero`、`status_iso_accepted`、`status_wrote_nothing`、`bad_date_failed_closed`、`bad_date_wrote_nothing`
- `digests.after_status_iso == digests.after_chain`（status 没写东西）
- 日志在 `logs\A_chain.log` 等

详细证据看 `..\deliverables\CONNECTED_PIPELINE.json`，必须满足：
| 字段 | 期望 |
|---|---|
| `CONNECTED_PIPELINE_RESULT` | `PASS` |
| `verdicts.lineage_same_artifact` | `true` |
| `verdicts.compiler_read_r15_tree` | `true` |
| `stages.compiler.seal_all_pass` | `true` |
| `stages.cleaning_r15.release_id` | `R15_REPLAY_20260924_R3` |
| `LINEAGE.retained_batches[*].retained_equals_r15_sealed` | 全 `true` |
| `stages.commit.status` | `PASS` |
| `stages.same_input_replay.status` | `PASS` |
| `PRODUCTION_CURRENT_WRITE` | `NONE` |

### 常见失败与处置

| 现象 | 原因 | 处置 |
|---|---|---|
| `HARD_BLOCK: candidate release exists` | 上一次已产出同 rid | 把 `candidate\r15_releases\R15_REPLAY_20260924_R3` 移到 `_prev_*` 再跑（**移动，不删除**） |
| 卡住 >5 分钟且 CPU 满、输出目录为空 | 又走了跟随 junction 的递归 | 立即停，报我；确认 `run_r15_cleaning_replay.py` 的 sha256 = `2719c17e…da1be1` |
| `FAIL missing=['VALUATION_PIT_R1']` | 定向物化没拿到 valuation 源 | 确认 `standard\factor\valuation` 存在（48 个 parquet）；确认 runner 版本正确 |
| `tip_ok=False stock_max=2026-09-01` | 只重放了 2 天、没物化历史 | 同上，检查 `standard\price\stock_ohlcv_daily` 是否有 232 个文件 |
| 编译器 exit 2 且日志 `SKIP_NO_SOURCE` | 源目录缺失 | 报我，附 `pipeline_runs\compiler_*.log` |

---

## 4. 单步调试（需要时）

只跑清洗：
```cmd
.venv\Scripts\python.exe -X utf8 _OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\candidate\run_r15_cleaning_replay.py --asof 2026-09-24 --rid R15_REPLAY_MANUAL
```
- 默认**定向物化**（只硬链 4 个产品子树）
- `--full-carry-forward` 会物化整树（慢，含分钟产品，**一般不要用**）
- `--no-carry-forward` 仅诊断用（会让 valuation 缺失 → 编译器必失败）

只跑编译器：
```cmd
.venv\Scripts\python.exe -X utf8 _OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\tools\run_original_compiler_candidate.py ^
  --cleaning-json <R15 的 RELEASE.json> --parent-root <sealed parent> ^
  --out-root <candidate cc_out\releases> --acceptance-out <...> ^
  --run-target-date 2026-09-24 --receipt <...json>
```

---

## 5. ⛔ 未授权动作（不要做）

| 动作 | 原因 |
|---|---|
| `.venv\...\run_blackbox_daily_incremental_data_plane_r1.py --mode run` | 会触发 Lane 采集（新增供应商数据） |
| `--mode full_day` | 同上 + 采集 |
| 任何 `publish_atomic(dry_run=False)` 指向生产 `CURRENT` | 生产发布未授权 |
| 覆盖 `数据\清洗成品\CURRENT_*` / `数据\回测缓存\CURRENT_*` | CURRENT 切换未授权 |
| 删除/覆盖 RAW、sealed release | 硬边界 |
| 用 `D:\CURSOR_TASK_ARCHIVE` 不存在的盘跑 compiler | 会抛错（归档写入点） |

---

## 6. 回滚

同目录 `.bak_sam_led_r6` / `.bak_sam_led_r7` / `.bak_sam_led_20261025` 覆盖回原名即可。
`_OPS` 下的候选产物（`candidate\r15_releases`、`candidate\cc_out\releases`）可直接移走，不影响生产。
