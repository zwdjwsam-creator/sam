# RELEASE_BINDING_AND_INDEX_CLOSURE_FIX — 第二轮收口

- 追加于 `COMPILER_READ_CLOSURE_FIX.md` 之后
- 三个缺陷：① 提交按目录名猜产物 ② 闭包只比数量 ③ 指数 `canonical_code` 未识别（1464 文件从未读入）
- 全部已在 SAM 实跑验证：`CONNECTED_PIPELINE_RESULT = PASS`，12/12 verdicts

---

## 0. 一句话

**`INDEX_DAILY_R1` 2026 从 273 行修到 106,822 行（新增 106,549，移除 0）**——这不是调参，是那 1464 个 RAW 指数文件从来没被读进来过。

---

## 1. 缺陷① 提交绑定了错误的产物

### 事实

```python
def newest_release(out_root):
    rels = sorted([p for p in out_root.iterdir() if p.is_dir()], key=lambda p: p.name)
    return rels[-1]          # 按目录名字典序取最后
```

`_prev_archived_*` / `_bad_*` / `zz_*` 这些归档目录与真实 release 混排，字典序可能排在后面 → 选中归档。
后果：**新内容没被提交，但运行返回 `IDEMPOTENT_NOOP`，看起来"成功"**。

移走归档只是环境修正，代码不改就还会复发。

### 修改

编译器自己已经写了一个显式身份文件：

```python
wjson(OUT / "TIP_REBASE_LAST.json", {"pointer": pointer, "seal": seal, "no_publish": args.no_publish})
# pointer.cache_release_id + pointer.release_root
```

改为以它为唯一来源：

1. 编译前把旧的 `TIP_REBASE_LAST.json` 移到 `.prev_<pid>.json`（旧文件不可能被当成本次输出）
2. 编译后硬校验，任一不满足即 `PipelineStop` → 顶层非零、候选提交引用不变：
   | 校验 | 内容 |
   |---|---|
   | 存在且新鲜 | 文件存在，`mtime >= 启动时刻 - 1s` |
   | 路径自洽 | `Path(release_root).name == cache_release_id` |
   | 目录真实 | `release_root` 是目录 |
   | 封版自洽 | `SEAL.json.release_id` 相同、`all_pass is True` |
   | 清单自洽 | `RELEASE.json.cache_release_id` 相同 |
   | asof 自洽 | `pointer.asof == 本次 ASOF` |
   | 输入自洽 | `pointer.source_cleaning_release == 本次传入的 cleaning.release_id` |
3. `newest_release()` **降级为抛错桩**（`NEWEST_RELEASE_FORBIDDEN`），调用点归零——旧调用者会立刻炸，而不是静默猜错

实测绑定结果：

```
bound_release_id   = BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20261026_170228
bound_release_root = ...\candidate\cc_out\releases\BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20261026_170228
binding_source     = ...\candidate\cc_out\acceptance\TIP_REBASE_LAST.json
```

同输入第二次编译产出 `..._171847`（新 root、同内容）→ `IDEMPOTENT_NOOP`，`commit_id` 不变 `c87b3a56…`。

> 965 行数 / 六日代码数只作为**本次 R3 重放的回归夹具**，没有写成任何未来增量的通用门。

---

## 2. 缺陷② 闭包只比数量

`assert_read_closure` 原来只比三个整数。等数量换一个文件、少读一个补一个，都能蒙过。

改为**文件集合身份**：

```
expected_files    ← cc.scan_parquet_independent()   ← 独立遍历，不复用被测枚举
enumerated_files  ← find_parquets() 输出
read_files        ← READ_REPORT 中 status == READ
```

- 报告 `missing_enumerated` / `extra_enumerated` / `missing_read` 及样本，计数仅作摘要
- **期望集绝不能由同一个枚举生成**（避免自证），所以单独写了独立遍历
- `SKIPPED_*` 属结构性排除，必须由调用方**显式**通过 `allow_excluded` 传入，并在结果里列 `excluded_reasons`；`READ_FAILED` 才判失败

负控实测：

| 用例 | 结果 |
|---|---|
| 集合完全一致 | `CLOSURE_OK=True` |
| **等数量但换一个键**（expected A,B / enumerated A,C） | **`READ_CLOSURE_BROKEN`**（`FILE_SET_IDENTITY` 分支拦截，`failed=0` 也拦） |
| 少读一个（234 vs 222） | **`READ_CLOSURE_BROKEN`** |

---

## 3. 缺陷③ 指数 1464 个文件从未读入

### 这是新闭包门抓出来的，不是猜的

```
RuntimeError: READ_CLOSURE_BROKEN: {"product": "INDEX_DAILY_R1",
  "semantics": "FILE_SET_IDENTITY",
  "expected": 1501, "enumerated": 1501, "read_ok": 37,
  "missing_read": 1464, "missing_enumerated": 0, "extra_enumerated": 0, "failed": 0}
```

### 根因

RAW 全历史指数 parquet 的证券代码列叫 **`canonical_code`**：

```
cols = ['canonical_index_id','canonical_code','provider_native_code','trade_date','open','high','low','close',...]
canonical_code = '000001.XSHG'
```

而 `read_price_frame` 只认：

```python
c_code = pick("code", "security", "order_book_id", "symbol")   # 不含 canonical_code
...
if c_code is None:
    continue        # ← 静默跳过，连 READ_REPORT 都不写
```

⇒ 1464 个文件全部被静默丢弃，`INDEX_DAILY_R1` 2026 实际只有 37 个清洗增量文件贡献的 **273 行（7 核心指数 × 39 日）**。

### 1501 与 273 是不同口径，现已查清

| 项 | 值 | 说明 |
|---|---|---|
| `expected` / `enumerated` | 1501 | `RAW_FULL_HISTORY=1464` + `CLEANING_CURRENT_INDEX_DAILY=37` |
| `read_ok`（修前） | 37 | 只有清洗增量被真正读入 |
| 输出 2026 行数（修前） | 273 | 7 code × 39 日（2026-07-30…09-24） |
| **读入失败原因** | — | **1464 个 = `SKIPPED_NO_CODE_COLUMN`（列名不匹配）** |

### 只读模拟先量影响（改码前）

| | 2026 keys | codes | dates |
|---|---|---|---|
| A 现状 | 273 | 7 | 39 |
| B 接受 `canonical_code` | **106,822** | **732** | **176** |
| 差值 | **+106,549** | +725 | +137 |

- **移除 0 key** → 不是替换，是补齐
- B 的 **732 codes** 与清洗完整平面 `std/index_daily` 2026 的 732 code 完全吻合（交叉验证）

### 修改

1. `pick` 增加 `canonical_code`（优先级最低：`code > security > order_book_id > symbol > canonical_code`）
2. `read_price_frame` 四个静默 `continue` 全部记账，各自带理由：

   | 状态 | 触发 |
   |---|---|
   | `SKIPPED_EMPTY_FRAME` | 空表 |
   | `SKIPPED_NO_DATE_COLUMN` | 无日期类列 |
   | `SKIPPED_NO_CODE_COLUMN` | 无代码类列（本次 1464 个的来源） |
   | `SKIPPED_NO_PRICE_COLUMN` | 无 close 且无 nav |
   | `READ_FAILED` | 读取异常（唯一判失败者） |

3. `READ_REPORT` 在函数开头即绑定本轮（原先只在末尾赋值，中途抛异常会残留上一轮报告）

### 修后实测

```
READ_CLOSURE INDEX_DAILY_R1:
  expected=1501 enumerated=1501 read_ok=1501 excluded=0 skipped_rows=0
  missing_enumerated=0 extra_enumerated=0 missing_read=0
  counts_equal=true  CLOSURE_OK=true
  sources={"RAW_FULL_HISTORY":{"files":1464},"CLEANING_CURRENT_INDEX_DAILY":{"files":37}}
  selected_files=1501

KEY_CHECK INDEX_DAILY_R1:
  status=MATCH  expected_keys=106822  written_keys=106822  missing=0  extra=0
```

---

## 4. 键集合对账（不是只比行数）

`KEY_CHECK` 从真实输入导出去重后的 `(date, code)` 键集合，与实际写出的 parquet 比对：

```
STOCK_DAILY_PIT_R1      MATCH  expected=959896 written=959896 missing=0 extra=0
STOCK_DAILY_RAW_PIT_R1  MATCH  expected=959896 written=959896 missing=0 extra=0
STOCK_FACTOR_DAILY_R1   MATCH  expected=959896 written=959896 missing=0 extra=0
INDEX_DAILY_R1          MATCH  expected=106822 written=106822 missing=0 extra=0
```

不匹配即 `KEY_SET_MISMATCH` → 写盘后仍阻断，不产生新提交。

---

## 5. 语义变化（必须明示，不得当"没变"）

| 产品 | 2026 行数 修前 | 修后 | 说明 |
|---|---|---|---|
| STOCK_DAILY_PIT_R1 / RAW / FACTOR | 959,896 | **959,896** | 不变（回归不倒退） |
| ETF_DAILY_PIT_R1 / FACTOR | 63,204 | **63,204** | 不变 |
| **INDEX_DAILY_R1 / FACTOR** | **273** | **106,822** | **补齐 1464 个 RAW 指数文件，移除 0** |
| MARKET_STRUCTURE_DAILY_R1 | 178 | 178 | 不变 |

**任何依赖"指数 2026 只有 7 个核心指数"的下游结论都必须重算。** 这是修读取带来的覆盖扩展，不是算法改动。

**未改动、仍存在问题**：`std/index_daily`（22 个年分区、732 code、2.9M 行）**仍然没有被 tip-rebase 使用**——它用的是 `std/reference/index_daily`（37 个增量）。这是**源选择**问题，属业务语义决策，本轮不动，单独标出。

---

## 6. 台式机复验判据

```bat
cd /d E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 tools\run_connected_pipeline.py --r15-rid R15_REPLAY_20260924_R3
```

| # | 判据 | 期望 |
|---|---|---|
| 1 | `stages.compiler.binding_source` | 指向 `...\acceptance\TIP_REBASE_LAST.json` |
| 2 | `stages.compiler.bound_release_id` | 与本次目录名一致，且 `SEAL.all_pass=true` |
| 3 | `newest_release` 触发 | **0 次**（若触发会以 `NEWEST_RELEASE_FORBIDDEN` 硬失败） |
| 4 | `READ_CLOSURE` | STOCK 234=234=234、ETF 37=37=37、**INDEX 1501=1501=1501**，三者 `CLOSURE_OK=true` |
| 5 | `KEY_CHECK` | 四项全 `MATCH`，`missing=0 extra=0` |
| 6 | 行数 | STOCK 三产品 959,896；ETF 63,204；**INDEX 106,822** |
| 7 | 六日代码 | 5209/5210/5208/5208/5208/5207 |
| 8 | `production_digest_changed` | `{}` |
| 9 | 二次幂等 | `IDEMPOTENT_NOOP` + verify `CONSISTENT` |

**隔离 fixture 负控**（指令要求，不用真实 sealed 目录）：
- 在 `_prev_` / `_bad_` / `zz_` 目录放诱饵 release → 本次仍绑定到真产物
- 故意少一个文件、或等数量换一个文件 → `READ_CLOSURE_BROKEN`，且不产生新提交

**阻断**：命中 `READ_CLOSURE_BROKEN` / `KEY_SET_MISMATCH` / `DECLARED_OUTPUT_INVALID` / `NEWEST_RELEASE_FORBIDDEN` 任一，贴日志并按 §6 上报，不得放宽。

**运行时长提示**：指数纳入 1464 个文件后，编译器阶段明显变长（SAM 实测全链 ~30 分钟，其中编译 ~12 分钟）。台式机请把超时放到 ≥40 分钟，不要因为比之前慢就判卡死。

---

## 7. 仍未证明

1. **V4** 仍 `BLOCKED_INPUT_INCOMPLETE`（复权同日输入、基准/锚点、历史池/ST）；本轮只修读取与绑定。
2. **供应商分页** 仍 `UNKNOWN`。
3. **`std/index_daily` 未被使用**（源选择，非读取缺陷），未改。
4. 台机 `LongPathsEnabled` 实际值仍未读（修复不依赖它）。
5. 指数覆盖扩展后，**依赖指数的既有研究结论需重算**——本轮未重算任何策略结论。
