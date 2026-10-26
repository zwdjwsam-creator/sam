# OPERATION_MANUAL — 台式机（ZHANGWEI）可照做的操作手册

- 适用：`E:\BLACKBOX`，解释器 `E:\BLACKBOX\.venv\Scripts\python.exe`
- 全部命令**在本机**执行。笔记本的 Python 读共享只能用于排查，**不能冒充台机运行**
- 带 ⛔ 的动作**未授权**，不要执行
- 本版：2026-10-26（更新：release 显式绑定 / 集合闭包 / 指数 `canonical_code`）

---

## 1. 环境自检（10 秒）

```cmd
cd /d E:\BLACKBOX
.venv\Scripts\python.exe -c "import sys,pandas,pyarrow;print(sys.version);print(pandas.__version__,pyarrow.__version__)"
```

预期：`3.12.x` + 两个版本号。
失败：`.venv` 损坏 → 按 `pyvenv.cfg` 记录的 Admin 解释器重建，**不要**只改 `home`。

可选：查长路径策略（不阻断，修复已用 `\\?\` 前缀）

```cmd
reg query "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled
```

---

## 2. 只读状态查询（安全，随时可跑）

```cmd
.venv\Scripts\python.exe -X utf8 脚本\run_blackbox_daily_incremental_data_plane_r1.py --mode status --date 2026-09-24
```

预期：JSON 含 `"READ_ONLY": true`、`"WATCHED_UNCHANGED": true`，末行 `STATUS_MODE_READ_ONLY_OK`，exit 0。
**若 CURRENT/STATE 的 mtime 变了，立即停**——那是回归。

非法日期必须 fail-closed（验收项）：

```cmd
.venv\Scripts\python.exe -X utf8 脚本\run_blackbox_daily_incremental_data_plane_r1.py --mode status --date 2026--0-9-
```

预期：**exit 非 0**，含 `INVALID_DATE_FAIL_CLOSED`，且 `数据`/`运行` 下**没有**新建 `2026--*` 目录。

---

## 3. 原链同产物流转（核心验收）

```cmd
cd /d E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 tools\run_connected_pipeline.py --r15-rid R15_REPLAY_20260924_R3
```

**超时请设 ≥40 分钟**：指数纳入 1464 个文件后，编译阶段明显变长（SAM 实测全链约 30 分钟）。

### 通过判据（逐项）

| # | 判据 | 期望 |
|---|---|---|
| 1 | R15 `standard\price\stock_ohlcv_daily` | 234 个 parquet（含 12 个 `r2_repair`） |
| 2 | `stages.compiler.binding_source` | `...\candidate\cc_out\acceptance\TIP_REBASE_LAST.json` |
| 3 | `stages.compiler.bound_release_id` | 与目录名一致；`SEAL.json.all_pass=true` |
| 4 | `READ_CLOSURE` | STOCK `234=234=234`、ETF `37=37=37`、**INDEX `1501=1501=1501`**；三者 `CLOSURE_OK=true` |
| 5 | `KEY_CHECK` | 四项全 `MATCH`，`missing=0 extra=0` |
| 6 | 行数 | STOCK 三产品 **959,896**；ETF **63,204**；**INDEX 106,822** |
| 7 | 六日代码 | 07-03=5209、07-06=5210、07-07/08/09=5208、07-10=5207 |
| 8 | `production_digest_changed` | `{}`（8 个 CURRENT/STATE 前后一致） |
| 9 | 二次幂等 | 再跑 commit+verify → `IDEMPOTENT_NOOP` + `CONSISTENT` |

### 阻断判据（命中任一即 BLOCKED，不要勉强判 PASS）

| 命中 | 处置 |
|---|---|
| `READ_CLOSURE_BROKEN` | 贴出完整 JSON（含 `missing_read_sample`、`skipped_sample`），停 |
| `KEY_SET_MISMATCH` | 贴出 `missing_sample` / `extra_sample`，停 |
| `DECLARED_OUTPUT_INVALID` | 贴 `problems` 列表，停 |
| `NEWEST_RELEASE_FORBIDDEN` | 说明还有旧代码路径在按目录名猜，停 |
| `status` 前后 digest 变化 | D2 回归，停 |
| 非法日期 exit 0 | D1 回归，停 |
| 需要联网下载才能继续 | 超授权，BLOCKED |

---

## 4. 隔离 fixture 负控（指令要求，不用真实 sealed）

装一次、跑一次，确认门真的会响：

1. 在 `candidate\` 下建 `_prev_bait\` / `_bad_bait\` / `zz_bait\`，各放一个假 release 目录（含最小 `RELEASE.json`、`SEAL.json`）
2. 正常跑 §3 → 必须仍绑定到**真产物**（`binding_source` 指向 `TIP_REBASE_LAST.json`，不是 bait）
3. 在某个产品的输入目录**临时少放一个文件**（或等数量换一个）→ 必须 `READ_CLOSURE_BROKEN` / `KEY_SET_MISMATCH`，且**候选提交引用不变**
4. 清掉 bait 与临时改动

**不要**用真实 sealed 目录做故障注入。

---

## 5. 单步调试

只跑清洗：

```cmd
.venv\Scripts\python.exe -X utf8 _OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\candidate\run_r15_cleaning_replay.py --asof 2026-09-24 --rid R15_REPLAY_MANUAL
```

- 默认**定向物化**（只硬链 4 个编译器输入子树）
- `--full-carry-forward` 物化整树（慢，含分钟产品，一般不要用）
- `--no-carry-forward` 仅诊断（会让 valuation 缺失 → 编译器必失败）

只跑编译器：

```cmd
.venv\Scripts\python.exe -X utf8 _OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\tools\run_original_compiler_candidate.py ^
  --cleaning-json <R15 的 RELEASE.json> --parent-root <sealed parent> ^
  --out-root <candidate cc_out\releases> --acceptance-out <...> ^
  --run-target-date 2026-09-24 --receipt <...json>
```

编译器会在 `--acceptance-out` 下写 `TIP_REBASE_LAST.json`，那就是它声明的产物身份。

---

## 6. 常见失败

| 现象 | 原因 | 处置 |
|---|---|---|
| `HARD_BLOCK: candidate release exists` | 上次已产出同 rid | 把 `candidate\r15_releases\R15_REPLAY_20260924_R3` 移到 `_prev_*`（**移动，不删除**）再跑 |
| 卡住 >5 分钟且 CPU 满、产物为空 | 又走了跟随 junction 的递归 | 停；确认 `run_r15_cleaning_replay.py` 含 `mirror_standard` / `materialize_selected` |
| `MATERIALIZE_INCOMPLETE` | 源/目标文件集合不一致 | 看 `MATERIALIZE_INCOMPLETE.json` 的 `absent` 列表；不要绕过 |
| `SKIPPED_NO_CODE_COLUMN` | 该文件没有可识别的代码列 | 若是新数据源，需在 `pick()` 里加列名（**属代码改动，先报 SAM**） |
| `PRICE_READ_INCOMPLETE` | 有文件读失败 | 附 `failed_sample`（含 `path_len`）；不要用 `allow_skip` |
| 编译变慢很多 | 指数 1464 文件已纳入 | 正常；超时放到 ≥40 分钟 |

---

## 7. ⛔ 未授权动作（不要做）

| 动作 | 原因 |
|---|---|
| `--mode run` / `--mode full_day` | 触发 Lane 采集（新增供应商数据） |
| `publish_atomic(dry_run=False)` 指向生产 `CURRENT` | 生产发布未授权 |
| 覆盖 `数据\清洗成品\CURRENT_*` / `数据\回测缓存\CURRENT_*` | CURRENT 切换未授权 |
| 删除/覆盖 RAW、sealed release | 硬边界 |
| 为通过门禁而加 `allow_skip` / 放宽 `allow_excluded` | 等于关掉证据 |

---

## 8. 回滚

同目录 `.bak_sam_led_*` 覆盖回原名即可。候选产物（`candidate\r15_releases`、`candidate\cc_out\releases`）可直接整体移走，不影响生产。

当前已有备份（台式机）：

```
任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1\cache_compiler_daily_incremental_r1.py.bak_sam_led_20261025
任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1\cache_compiler_daily_incremental_r1.py.bak_sam_led_20261026(_r2/_r3)
任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1\cache_compiler_tip_rebase_from_current_r1.py.bak_sam_led_20261025(_20261026/_r3)
_OPS\...\tools\run_connected_pipeline.py.bak_sam_led_20261025(_evidence/_20261026)
_OPS\...\candidate\run_r15_cleaning_replay.py.bak_sam_led_r6/_r9/_r10
脚本\run_blackbox_daily_incremental_data_plane_r1.py.bak_sam_led_20261025
```
