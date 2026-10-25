# DESKTOP_RERUN_AFTER_FIX — 台机本机复跑结果（R11 长路径修复后）

- from: ZHANGWEI（台式机）· to: SAM（笔记本）
- 依据: `RERUN_AFTER_FIX.md`（rev R11）
- 命令: `python -X utf8 tools\run_connected_pipeline.py --r15-rid R15_REPLAY_20260924_R3`
- 时间: 2026-10-25 21:56:55 起 · runner exit **0** · `CONNECTED_PIPELINE_RESULT = PASS` · **12/12 verdicts true**

## 结论：BLOCKED（物化修好了，编译读取没修好）

> **A 通过，B 不通过。** 按 §4「must match exactly, otherwise STOP」已停。

| 检查 | 期望 | 台机实测 | 判定 |
|---|---|---|---|
| **A** R15 `stock_ohlcv_daily` | 234 文件 / 12 个 r2_repair | **234 / 12** | ✅ 修复生效 |
| **B** 编译 `rows_2026` ×3 产品 | **959,896** | **928,760** | ❌ 差 **31,136** |
| C 二次同输入幂等 | IDEMPOTENT_NOOP | 未跑第二轮（B 已不匹配，按 §4 停） | — |

12/12 verdicts 全真、exit 0，**但它仍然是错的**。这一点很关键：现有门全是结构与身份门，**没有一项校验"编译器到底读到了几个文件 / 几行"**。

## 根因：编译器自己的 `is_file()`，和你修掉的是同一类缺陷

```
E:\BLACKBOX\任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1\cache_compiler_daily_incremental_r1.py:246
    return sorted([p for p in root.rglob("*.parquet") if p.is_file()])
```

你在物化器里换成了 `_lp` + 显式 `stat`，但**编译器仍用 `p.is_file()`**。台机 `LongPathsEnabled = 0`，所以它照旧把 stat 失败当成"不是文件"。

台机实测（R3 目录）：

```
files_on_disk             = 234
max_full_path_len         = 271        ← SAM 侧是 289，根不同，都 > 260
is_file() visible         = 222
is_file() dropped         = 12
stat(\\?\ prefixed) OK    = 234        ← 文件完好，能读
find_parquets() returns   = 222        ← 编译器实际只看到 222 个
read_parquet(\\?\ ...)    = 2,890 rows / 2,890 codes  ← 内容完全正常
```

`find_parquets() == 222` 就是铁证：**物化层给了 234，编译层又退回 222。**

编译产物里那 6 天依旧是 **每天 19 个代码**：

```
year=2026/part_2026.parquet  rows=928,760  (2026-01-05 → 2026-09-24)
2026-07-03 19   07-06 19   07-07 19   07-08 19   07-09 19   07-10 19
```

## 数字对得上，所以你原来的诊断是对的

被丢 12 个文件的行数：5,193 / 5,194 / 5,194 / 5,194 / 5,194 / 5,194 = **31,163**。

- 你那 6 天原有 19 个代码来自 `gapfill_codes`，其中 **27** 个 `(date,code)` 与 `r2_repair` 重叠
- 去重后净增 = 31,163 − 27 = **31,136** = 959,896 − 928,760 ✅ 完全自洽

## 你标 UNVERIFIED 的那一项，台机补上了

```
HKLM\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled = 0
OS 10.0.26200.0
```

**主机策略确实是 0。** 你的长度相关性推断成立；而且这解释了为什么**同一份 234 文件在 SAM 上是 959,896、在台机是 928,760**——SAM 侧 R3 路径更短，`is_file()` 恰好没触发。环境差异，不是数据差异。

## 需要你改的（两处，我不动业务代码）

1. **`find_parquets`**：枚举不要过 `is_file()`，改成 `scandir` + `os.stat(_lp(p))`，stat 失败就**抛错/计数**，禁止跳过。跟你物化器同一套 `_lp` 语义。

2. **补一道行数/文件数硬门**（这才是这次真正的教训）：编译后断言
   `tree_visible_parquet_count == materialize 报告的 dst_files`，且编译行数与源行数上界一致；不等即 `HARD_BLOCK: COMPILER_READ_INCOMPLETE`。否则 12/12 全真会继续掩盖行数缺口。

> **不建议**靠"把 R3 挪到更短的根"绕过 260：那只是躲开当前路径长度，换机/换目录立刻复现，属于掩盖。

## 三条附带发现

1. **回滚链是断的**：`run_r15_cleaning_replay.py.bak_sam_led_r11` 与当前文件**字节完全相同**（`f2c858e4...`），不是修前备份。真正的修前版本是 `.bak_sam_led_r10`（25,832 B, `2719c17e...`）。按 r11 备份回滚 = 回滚到同一个文件。
2. **遗留 `walk()` 仍静默吞错**：`run_r15_cleaning_replay.py` 里整树 walk 的 `except OSError: continue` 还在（仅 `--full-carry-forward` 走），建议一并 fail-closed。
3. **`candidate_commit --action verify` 返回 `CONSISTENT` / `payload_matches=true`，但 payload 就是那份错的 928,760。** 内容寻址只证明"没变"，不证明"对"，不能当正确性证据。
4. 顺带：`RERUN_AFTER_FIX.md` 已落台机（21:48）但**没推 HUB**，HUB 同名目录下只有 `READ_PLANE_DIFF.md`。

## 台机当前状态（未删任何东西）

- `R15_REPLAY_20260924_R3` — 在（234 文件，已封版，本次新建）
- `cc_out\releases\` — 1 个（`..._215655`）
- `cc_commit` — `CONSISTENT`，`commit_id 2f75577954f26ba6...`
- `PRODUCTION_CURRENT_WRITE=NONE`、`NEW_DATA_ACQUISITION=NONE`、`published=false`、`ORDER_ALLOWED=false`
- **V4 未触碰**，仍 `BLOCKED_INPUT_INCOMPLETE`

## 下一步

等你把 `find_parquets` 改好 + 行数门加上，给一次性脚本或直接落盘，台机立刻复跑同一条命令。判据就三条：`files 234 / r2_repair 12`、`rows_2026 = 959896 ×3`、6 天回到 5,20x。
