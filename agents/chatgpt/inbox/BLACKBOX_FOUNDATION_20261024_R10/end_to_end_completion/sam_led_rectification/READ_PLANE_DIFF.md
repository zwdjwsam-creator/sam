# READ_PLANE_DIFF — 两端读取差异：定位 → 修改 → 恢复

- task: `BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025`
- dispatch: `SAM_LED_DESKTOP_RECTIFICATION_20261025`（本轮收敛段：由 SAM 纠正目标端读取差异）
- 方法：**同一段测量代码，同一请求，两端各跑一次**；再用文件名集合比对定位到单个文件
- 边界：未新增采集、未切换生产 CURRENT、未改 sealed 数据、未下单

---

## 1. 未解释的两个数字，已逐个拆开

| 指标 | SAM | 台式机（修前） | 判定 |
|---|---|---|---|
| 清洗源 `standard/price/stock_ohlcv_daily` | 232 文件 | 232 文件，**逐文件 sha256 全等** | **无差异** → 不是清洗层 |
| CURRENT cache `STOCK_DAILY_PIT_R1` 2026 | 949,470 行 / 13 文件 / 176 日 / 5,535 代码 / max 09-24 | **完全相同**，13/13 文件 sha16 全等 | **无差异** → 不是 CURRENT 读取 |
| 编译候选 `year=2026` | **959,896** 行 | **928,760** 行 | **差 31,136** |
| 2014–2025 十三个分区 | — | — | **rows / dates / codes / sha16 全部一致** |
| R15 编译器输入目录文件数 | **234** | **222** | **差 12** |

结论：差异**不在**数据源、不在 CURRENT、不在历史分区，**只在"R15 清洗产物 → 编译器输入"这一跳的文件集合**。

---

## 2. 逐日拆解：6 个交易日、31,136 行、全部是"代码被截断"

`year=2026` 分区按日对比：

| 日期 | SAM 行数/代码数 | 台式机 行数/代码数 | 差 |
|---|---|---|---|
| 2026-07-03 | 5,209 / 5,209 | **19 / 19** | 5,190 |
| 2026-07-06 | 5,210 / 5,210 | **19 / 19** | 5,191 |
| 2026-07-07 | 5,208 / 5,208 | **19 / 19** | 5,189 |
| 2026-07-08 | 5,208 / 5,208 | **19 / 19** | 5,189 |
| 2026-07-09 | 5,208 / 5,208 | **19 / 19** | 5,189 |
| 2026-07-10 | 5,207 / 5,207 | **19 / 19** | 5,188 |
| 合计 | | | **31,136** |

- `dates_only_in_A = []`、`dates_only_in_B = []`、`codes_only_in_B = 0`
- ⇒ **日期键全部存活，代码被截断**。任何"日期覆盖完整"的检查都会通过而漏掉它。

**19 这个数字是关键线索**：清洗层里覆盖该窗口的只有 14 个文件——
12 个 `r2_repair` 单日文件（XSHE 2,890/2,891 码 + XSHG 2,303/2,304 码）
＋ 2 个 `gapfill_codes` 文件（10 码 + 9 码 = **正好 19**）。

⇒ 台式机那 6 天**只有 `gapfill_codes` 的行存在，12 个 `r2_repair` 的行完全缺失**。

---

## 3. 定位到文件：缺的正是那 12 个，且是最长路径的 12 个

R15 编译器输入目录 `standard/price/stock_ohlcv_daily` 文件名集合比对：

```
only_in_SAM = 12   only_in_DESKTOP = 0   size_diff = 0   sha_diff = 0
common_identical = 222
```

12 个缺失文件 = `XSHG`/`XSHE` × `2026-07-03, 07-06, 07-07, 07-08, 07-09, 07-10` 的 `r2_repair`。

路径长度（同一命名，两端目标目录不同）：

| 侧 | 目录 | 全路径长度 | 结果 |
|---|---|---|---|
| SAM | `...\candidate\r15_releases\R15_REPLAY_20260924_R3\standard\price\stock_ohlcv_daily` | **271** | 全部落盘 |
| 台式机 | 同上（UNC 形式） | **289** | **12 个未落盘** |
| 台式机现存 222 个文件 | — | 最长 **261** | 全部落盘 |

`LongPathsEnabled` 在 SAM = 1（`RtlAreLongPathsEnabled=1`）。
**台式机侧无法直接读注册表**，因此"主机策略=0"这一层只能标 `UNVERIFIED`；但**长度相关性是实测的**：≤261 全成功、289 全失败。

---

## 4. 真正的原因在我的代码里，不在 Windows

上一版 `materialize_selected()`：

```python
for f in sorted(real.iterdir()):
    if not f.is_file():      # ← 缺陷
        continue
    tgt = dst / f.name
    ...
    os.link(f, tgt)  except OSError: shutil.copy2(f, tgt)
```

`Path.is_file()` **吞掉 `OSError` 并返回 `False`**（CPython 行为）。当 `os.stat` 因路径长度/策略失败时，该文件被当作"不是文件"**静默跳过**——不报错、不计数、不影响退出码。于是：

- 产物目录少了 12 个文件，`linked/copied` 计数照常，`GATE_RESULT` 照常 PASS；
- 下游编译器读不到那 12 个文件 → 该 6 天只剩 `gapfill_codes` 的 19 码 → 31,136 行消失；
- 日期键仍由 `gapfill_codes` 提供 → **覆盖检查通过**。

这是一类"静默部分成功"，比直接报错危险得多。

---

## 5. 修改（已落地台式机，全部带备份）

| # | 文件 | 改动 | 备份 |
|---|---|---|---|
| 1 | `candidate/run_r15_cleaning_replay.py` | ① 新增 `_lp()`：对 stat/link/copy 使用 `\\?\`（UNC 用 `\\?\UNC\`）扩展长度前缀；② `_stat_file()` 显式 stat，失败**记录**而非跳过，非普通文件即抛错；③ 枚举后做**源/目标文件名集合比对**，任何缺失/多余/数量不等 → `gate_ok=False`；④ `carry_forward` 失败即 `SystemExit`，并落 `MATERIALIZE_INCOMPLETE.json`；⑤ 新增 gate `materialize_complete` | `.bak_sam_led_r6/r9/r10` |
| 2 | `tools/run_connected_pipeline.py` | R15 产物作为编译器 `--cleaning-json`；新增 `LINEAGE` 同产物校验与 `lineage_same_artifact` / `compiler_read_r15_tree` verdicts | `.bak_sam_led_r7` |
| 3 | `tools/candidate_commit.py` | ① `verify()` 增加 `PAYLOAD_ROOT_MISSING` 状态与 `payload_root_missing` 字段（不再把"树被移走"混同为"内容不一致"）；② `commit()` 决策顺序：同内容同根同标签→`IDEMPOTENT_NOOP`；同内容同根标签过期→`REPAIRED_SAME_ROOT_FIELD_DRIFT`；同内容且引用根仍在→`IDEMPOTENT_NOOP`；**引用根已消失→`REBOUND_SAME_CONTENT_NEW_ROOT`** | `.bak_sam_led_20261025(_v2/_v3/_v4)` |

**为什么重绑是安全的**：`CC_COMMIT_IDENTITY_V2` 只哈希 `asof / source_cleaning_release / parent_release_id / 每产品 sha256+rows`，**排除** `release_id / release_root / RELEASE.json / SEAL.json / _qa/*`。因此 `commit_id` 相等 ⇒ 数据相同；重绑只改"指向"，不改"内容"，并写 `rebound_from_release_root` 留痕。

**没有放宽的**：`SEAL.all_pass` 必须为真、必需产品必须齐全，否则 `build_identity()` 直接抛错。引用根仍存在时**不会**重指向。

---

## 6. 台式机原失败请求如何恢复

修后（SAM 已实跑，作为参照）：

```
CONNECTED_PIPELINE_RESULT = PASS
verdicts: 12/12 true   （含 commit_consistent=true、same_input_replay_noop=true）
R15 standard/price/stock_ohlcv_daily = 234 parquet，其中 r2_repair = 12
compiled year=2026 = 959,896 行
2026-07-03..07-10 每日代码数 = 5,209 / 5,210 / 5,208 / 5,208 / 5,208 / 5,207（不再是 19）
幂等：连跑两次均 IDEMPOTENT_NOOP，verify = CONSISTENT
```

台式机复现命令（本机执行，非笔记本代跑）：

```bat
cd /d E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 tools\run_connected_pipeline.py --r15-rid R15_REPLAY_20260924_R3
```

通过判据：
- R15 `standard\price\stock_ohlcv_daily` = **234**（含 **12** 个 `r2_repair`）
- 编译 `year=2026` = **959,896** 行
- 那 6 个交易日代码数 ≈ 5,208（**不是 19**）
- `verdicts.same_input_replay_noop = true`，`verify` = `CONSISTENT`
- `PRODUCTION_CURRENT_WRITE = NONE`

阻断判据：命中 `HARD_BLOCK: MATERIALIZE_INCOMPLETE` 即为修复生效但源侧真缺文件——此时应贴 `MATERIALIZE_INCOMPLETE.json` 的 `absent` 列表，而不是继续跑。

---

## 7. 仍未证明（不得外推）

1. **台式机 `LongPathsEnabled` 值**：无法直接读取。长度相关性是实测，主机策略层 `UNVERIFIED`。修后代码不再依赖该策略（`\\?\` 前缀），但请台机跑完后回报该值以便归档。
2. **V4 同条件成功**：仍未证明。本轮修的是读取差异与链完整性，不改变 V4 的 `BLOCKED_INPUT_INCOMPLETE`（复权同日输入、基准/锚点、历史池/ST 未满足）。
3. **供应商分页完整性**：仍 `UNKNOWN`，未自填 YES。
4. **`BLACKBOX_DEST` 权限**：实测卸载后只要当前登录身份在 ACL 内仍可访问，且对 `Authenticated Users` 给的是 `Modify`；建议收紧（SAM 未擅自改）。
5. **两端同请求的 V4 结果对照**：无笔记本成功样本，因此按规则不预设其成功。
