# COMPILER_READ_CLOSURE_FIX — 编译器内部漏读修复（第二轮）

- 追加于 `READ_PLANE_DIFF.md` 之后。第一轮只修了**物化器**，这一轮修**编译器自己**。
- 结论前置：**上一轮我的修复不完整。** 物化器交出 234 个文件后，台式机的编译器 `find_parquets()` 仍会把它们砍到 222。

---

## 1. 我上一轮漏掉的第二个漏读点

`cache_compiler_daily_incremental_r1.py` 里还有两处，与物化器同源：

### 1.1 `find_parquets()` 用 `is_file()` 过滤

```python
def find_parquets(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted([p for p in root.rglob("*.parquet") if p.is_file()])
```

`Path.is_file()` 吞掉 `OSError` 返回 `False`。所以即使物化器正确写入 234 个文件，编译器仍只"看见" 222 个，且**不报错**。

**实测**：台机 `find_parquets` 返回 222；补丁后返回 **234**（含 12 个 `r2_repair`，最长路径 271 字符）。SAM 因 `LongPathsEnabled=1` 侥幸不受影响——这也解释了为什么我在 SAM 上"没复现"。

### 1.2 `read_price_frame()` 读失败继续跳过

```python
    for p in use:
        try:
            df = pd.read_parquet(p)
        except Exception as e:
            log(f"skip unreadable {p.name}: {e}")
            continue        # ← 静默漏读 + 不计数
```

文件读不出来 → 该文件的行全部消失 → 仍然"成功"返回，行数只少不多。**这与 `is_file()` 是同一类缺陷的两个入口**，只修一个不够。

---

## 2. 修改（已落地台式机三处，均带备份）

| 文件 | 改动 |
|---|---|
| `任务/.../cache_compiler_daily_incremental_r1.py` | ① 新增 `_lp()` / `_unlp()`：stat 与读盘走 `\\?\` 扩展长度前缀；② `find_parquets` 改为 `os.walk` + 显式 `os.stat`，**任何 stat 失败即收集并 `raise`**（不再 `is_file()` 过滤）；③ `read_price_frame` 读盘走长路径，失败**记入 `READ_REPORT` 并默认 `raise`**；④ 新增 `assert_read_closure()`；⑤ 暴露 `READ_REPORT` / `_ENUM_REPORT` |
| `任务/.../cache_compiler_tip_rebase_from_current_r1.py` | `rebuild_price_2026` 在三个 `read_price_frame` 之后、**写任何产品之前**断言闭包；并把 `read_closure` 与 `july_distinct_codes` 写入返回值 |
| `_OPS/.../tools/run_connected_pipeline.py` | ① `production_current_untouched` 由**硬编码 true** 改为 8 个生产 CURRENT/STATE 文件的**前后 digest 实测比对**；② 负控编译器日志改名，避免与主编译日志撞名被覆盖 |

字节（BEFORE → AFTER）：

```
cache_compiler_daily_incremental_r1.py   38,650 → 42,333   c8ddf805… → 2a82d12b…
cache_compiler_tip_rebase_from_current_r1.py 25,087 → 26,486  0be0f4f1… → c1d431a2…
run_connected_pipeline.py                28,893 → 30,487   4964f27c… → b7a7179b…
```

---

## 3. 三集合闭包门（提交前，写盘之前）

```
materialised  = 清洗标准目录里实际存在的 .parquet 数（os.scandir，不带 is_file 过滤）
enumerated    = find_parquets 返回的文件数
read_ok       = READ_REPORT 中 status == "READ" 的数量
```

三者必须相等且 `failed == 0`，否则 `raise READ_CLOSURE_BROKEN`，**在任何产品写入之前**中止。

SAM 实测（日志原文）：

```json
READ_CLOSURE {"STOCK_DAILY_PIT_R1": {"materialised": 234, "enumerated": 234, "read_ok": 234,
                                     "failed": 0, "CLOSURE_OK": true},
              "ETF_DAILY_PIT_R1":   {"materialised": 37,  "enumerated": 37,  "read_ok": 37,
                                     "failed": 0, "CLOSURE_OK": true}}
```

负控（`materialised=234, enumerated=222`）→ 正确抛 `READ_CLOSURE_BROKEN`。

---

## 4. 关于你纠正的那个判据 —— 我接受，并已改

> 行数不超过源上界不够，漏读同样满足上界，必须核对去重后的预期键集合。

完全同意。这就是为什么这三种检查必须分开：

| 检查 | 能否发现"漏读" | 说明 |
|---|---|---|
| `rows <= 源上界` | **不能** | 漏读只会让行数变少，仍在上界内 |
| 日期覆盖完整 | **不能** | 正是本次事故：6 天日期键全在，代码从 5,208 掉到 19 |
| **文件集合闭包**（物化=枚举=读取） | **能** | 直接证明没有文件被丢 |
| **去重后每日 distinct 键集合** | **能** | 证明读进来的键确实齐 |

所以落地的门是**前两者之外**的后两者：文件集合闭包 + 每日 distinct 代码数。后者已写入 `_qa/TIP_REBASE_QA.json` 的 `july_distinct_codes` 与 release 返回值，可直接核。

---

## 5. 台式机复验判据（更新版，取代 `RERUN_AFTER_FIX.md` 中的数字）

```bat
cd /d E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 tools\run_connected_pipeline.py --r15-rid R15_REPLAY_20260924_R3
```

| # | 判据 | 期望 |
|---|---|---|
| 1 | R15 `standard\price\stock_ohlcv_daily` | **234** 个 parquet，含 **12** 个 `r2_repair` |
| 2 | 编译器日志 `READ_CLOSURE` | `materialised=enumerated=read_ok=234`，`CLOSURE_OK=true`；ETF 为 37/37/37 |
| 3 | 日志中 `READ_FAILED` / `ENUM_INCOMPLETE` / `PRICE_READ_INCOMPLETE` / `READ_CLOSURE_BROKEN` | **0 条** |
| 4 | 三产品 `year=2026` 行数 | `STOCK_DAILY_PIT_R1` / `STOCK_DAILY_RAW_PIT_R1` / `STOCK_FACTOR_DAILY_R1` 各 **959,896** |
| 5 | 去重后每日 distinct 代码 | 07-03=**5209**、07-06=**5210**、07-07/08/09=**5208**、07-10=**5207**（**不是 19**） |
| 6 | `production_digest_changed` | `{}`（8 个指针/STATE 前后一致） |
| 7 | 负控日志 | `pipeline_runs\compiler_HARD_BLOCK_negative_control.log` 存在，内含 `exit_code: 1` |
| 8 | 二次幂等 | 再跑一次 commit+verify：`IDEMPOTENT_NOOP` + `CONSISTENT` |

**阻断**：任一 `READ_CLOSURE_BROKEN` 或 `PRICE_READ_INCOMPLETE` 即为修复生效但源侧真缺/真坏——此时应贴出日志里的 `failed_sample`（含 `path_len`），而不是继续跑。

---

## 6. 一个必须预告的行为变化

`read_price_frame` 现在**默认 fail-closed**。任何此前"侥幸通过"的**部分物化** release，下一次 tip rebase 会直接 `PRICE_READ_INCOMPLETE` 硬失败。

这是**预期**的（把静默缺口变成可见错误），但请台机知情：如果它还有更早的历史候选 release 处于部分状态，会在下次跑时暴露。届时按 §5 阻断条目上报，而不是放宽 `allow_skip`。

---

## 7. 仍未证明（不变）

1. 台机 `LongPathsEnabled` 的**实际值**仍未读到（只能读文件、不能在它机器上跑命令）。但修复不再依赖该策略（`\\?\` 前缀），所以这一项不再阻塞。
2. **V4 同条件成功**仍未证明：`BLOCKED_INPUT_INCOMPLETE` 未变（复权同日输入、基准/锚点、历史池/ST）。
3. 供应商分页完整性仍 `UNKNOWN`。
4. 指数读取（1501 RAW + 清洗 idx）**尚无自己的闭包探针**，只有股票与 ETF 有。这是已知覆盖缺口，不假装已覆盖。
