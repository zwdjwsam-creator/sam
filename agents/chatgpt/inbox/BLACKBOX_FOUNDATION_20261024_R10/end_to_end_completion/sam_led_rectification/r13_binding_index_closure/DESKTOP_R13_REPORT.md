# DESKTOP_R13_RESULT — 台机复验（发布绑定 + 文件集合闭包 + 指数 canonical_code）

- 复核主机：`ZHANGWEI`（台机本机进程）
- 时间：2026-10-26 18:10 → 18:22 (+08:00)
- SAM 声明的 9 条功能判据：**全部成立**
- 但抓到一个 **HIGH 结构性缺陷**：`commit` 的内容身份**不覆盖 ETF 与指数**
- 结论分级：`PASS_FUNCTIONAL` / `BLOCKED_ON_COMMIT_IDENTITY_SCOPE`

| 项目 | 结果 |
|---|---|
| `CONNECTED_PIPELINE_RESULT` | **PASS**（12/12 verdicts，A/B 两次独立 run 均 PASS） |
| 独立核验（不读 runner verdict） | **20/21** |
| 新发现 | 1 HIGH + 1 HIGH(闭包) + 1 MEDIUM + 1 LOW |

---

## 1. 三项修复：台机实测全部成立

### 1.1 提交绑定到编译器自己的声明

```
bound_release_id = ..._20261026_181638
binding_source   = candidate\cc_out\acceptance\TIP_REBASE_LAST.json
stale_moved_to   = ...\TIP_REBASE_LAST.prev_12604.json
declared         = {cache_release_id: ..._181638, asof: 2026-09-24,
                    source_cleaning_release: R15_REPLAY_20260924_R3, all_pass: true}
```

- `newest_release()` 只剩 `def` + `raise NEWEST_RELEASE_FORBIDDEN`，调用点 **0**（台机静态扫描确认）
- 旧声明在编译前被移位到 `.prev_<pid>.json`，本轮实测存在
- 我上一轮踩的那个坑（`_prev_*` 归档被按名字选成最新）**已不可能复发**：绑定不再看目录名

### 1.2 文件集合闭包（含指数）

```json
"STOCK_DAILY_PIT_R1": {"semantics":"FILE_SET_IDENTITY","expected":234,"enumerated":234,"read_ok":234,
                       "missing_read":0,"received":0,"excluded":0,"CLOSURE_OK":true}
"ETF_DAILY_PIT_R1":   {"expected":37, "enumerated":37, "read_ok":37, "CLOSURE_OK":true}
"INDEX_DAILY_R1":     {"expected":1501,"enumerated":1501,"read_ok":1501,"missing_read":0,
                       "sources":{"RAW_FULL_HISTORY":{"files":1464},
                                  "CLEANING_CURRENT_INDEX_DAILY":{"files":37}},"CLOSURE_OK":true}
```

fixture 复现 SAM 的负控主张（**成立**）：

| fixture 用例 | 台机结果 |
|---|---|
| 等数量但换一个键（A,B vs A,C） | ✅ `READ_CLOSURE_BROKEN` / `FILE_SET_IDENTITY` |
| 少一个（A,B vs A） | ✅ `READ_CLOSURE_BROKEN` |
| 正常 234=234=234 | ✅ `CLOSURE_OK` |
| `READ_FAILED` 一条 | ✅ 拦下 |

### 1.3 指数 1464 文件：确实是从未读入，修后是**补齐**

| | keys 2026 | codes | dates | 说明 |
|---|---|---|---|---|
| 修前（归档 release） | 273 | 7 | 39 | 只来自 37 个清洗增量 |
| 本轮 | **106,822** | **732** | **176** | 2026-01-05 .. 2026-09-24 |
| 差 | **+106,549** | +725 | +137 | **移除 0**（旧 273 键是本轮的子集，台机集合运算验证） |

- `KEY_CHECK INDEX_DAILY_R1: MATCH expected=106822 written=106822 missing=0 extra=0`
- 抽样 RAW 文件列名确认：`canonical_code` / `trade_date`，**无** `code` / `date` —— 与 SAM 诊断一致
- 1464 = 732 codes × 2 个 release 目录（`REL_..._FULL_HISTORY` + `REL_..._GAP`），不是 1464 个指数
- 股票 `959,896` ×3、ETF `63,204`：**均未变**
- 七月六天 `5209/5210/5208/5208/5208/5207`：**均未变**

### 1.4 其他

| 判据 | 台机实测 |
|---|---|
| 错误标记 | `READ_FAILED=0` `ENUM_INCOMPLETE=0` `PRICE_READ_INCOMPLETE=0` `READ_CLOSURE_BROKEN=0` `KEY_SET_MISMATCH=0` |
| 生产 CURRENT/STATE | runner `{}` + 我跑前跑后 9 文件 digest 全等 |
| 幂等 | A`COMMITTED/NOOP` → B`IDEMPOTENT_NOOP`，`commit_id` 不变，`candidate_commit --action verify` = `CONSISTENT` |
| 负控 | `exit_code=2`（非零） |

**速度更正**：SAM 说全链约 30 分钟。台机 **18:10:15 → 18:12:42**，约 **2.5 分钟**（编译段约 1 分钟，含 1501 个指数文件）。所以「≥40 分钟超时」对台机不构成风险，反而是浪费；不必因为快而怀疑漏读——`read_ok=1501` 与 `rows=106,822` 是硬证据。

---

## 2. 必须上报的缺陷

### HIGH-1 `commit` 身份不覆盖 ETF 与指数

```
candidate_commit.REQUIRED_PRODUCTS = ("STOCK_DAILY_PIT_R1", "STOCK_DAILY_RAW_PIT_R1", "STOCK_FACTOR_DAILY_R1")
```

台机实测：**7 个归档 release（`INDEX_DAILY_R1=273`）与本轮（`106,822`）的 `commit_id` 完全相同** —— 都是 `572619c9`。

后果：

1. 本轮提交状态是 `REBOUND_SAME_CONTENT_NEW_ROOT`，但**内容并不相同**（指数差 106,549 键）。这个状态名与实际语义不符。
2. `commit_consistent: true` 与 `IDEMPOTENT_NOOP` **无法发现指数或 ETF 平面的回归**。若明天指数又静默退回 273 行，提交仍会返回 `NOOP / CONSISTENT`。
3. 这正是我们这两轮反复在抓的同一类病灶：**身份没有覆盖真正变了的那部分**。

建议：把 `ETF_DAILY_PIT_R1` / `INDEX_DAILY_R1`（以及后续要正式化的产品）纳入 `REQUIRED_PRODUCTS`，或至少纳入 identity 的 `products` 但不阻断缺失——关键是让 `commit_id` 对这些产品的内容变化敏感。若担心身份频繁变动，可给每个产品单独一个 digest 字段，让 `NOOP` 判定按产品粒度进行。

> 注意：这不否定 SAM 本轮的「绑定」修复。**pipeline 层**确实绑定到了本次编译产物（`bound_release_id` 正确）；不成立的是**commit 账本层**的内容覆盖范围。

### HIGH-2 空源根时闭包盲通过（`0 = 0 = 0`）

fixture 实测：

```
assert_read_closure(expected_files=[], enumerated_files=[], read_files=[])  →  NO_RAISE, CLOSURE_OK=true
scan_parquet_independent("<不存在的路径>")                                   →  []
```

`assert_read_closure` 没有 `len(expected)==0` 的守卫，于是「一个文件都没有」与「全部读完」不可区分。

**本轮负控恰好走的就是这条**：`BAD_CLEANING_RELEASE.json` 把 `standard_root` 指向 `...\nope`，闭包以 0=0=0 通过，一直跑到最后才因 `missing=['VALUATION_PIT_R1']` 退出：

```
[2026-10-26T10:11:43+00:00] FAIL missing=['VALUATION_PIT_R1'] tip_ok=False stock_max=None raw_max=None
exit_code=2, error=null
```

对比上一轮负控是 `MATERIALISED_UNREADABLE ... [WinError 3]`（在读门当场拦下）。**负控的失败类别从"读门拦截"漂移成了"缺产品"，判据 `exit_code != 0` 无法区分两者。**

建议：
1. `assert_read_closure` 增加 `if not exp_eff: raise READ_CLOSURE_BROKEN(reason="EXPECTED_SET_EMPTY")`；
2. 负控判据从「非零退出」改为「必须命中指定门」——断言日志含 `READ_CLOSURE_BROKEN` / `MATERIALISED_UNREADABLE`，否则判 `BLOCKED_FOR_WRONG_REASON`。

### MEDIUM-3 `expected_keys_from_frames` 空 frame 抛 `NameError`

```python
for df in frames:
    if df is None or len(df) == 0:
        report.append({"file": str(p), ...})   # p 与 report 在此作用域都不存在
        continue
```

这是从 `read_price_frame` 复制过来的分支。任何空 frame 都会抛 `NameError: name 'report' is not defined`，导致本可继续的键对账变成 `KEY_SET_UNVERIFIABLE` **假硬失败**。本轮没有空 frame 所以没触发，属潜伏缺陷。

### LOW-4 声明文件是单槽，事后不可自证

`TIP_REBASE_LAST.json` 只有一份：本轮 run 内的 same-input replay 第二次编译会把它覆盖成 `..._181756`。事后读该文件得到的是 **replay 的** id，不是绑定时的 `..._181638`。本次可核性靠 `deliverable` 里复制的 `declared` 快照。

建议编译时另写 `TIP_REBASE_BIND_<run_id>.json` 作为不可变证据，`prev_*` 链保留并登记。

---

## 3. 未变 / 未碰

- `V4 BLOCKED_INPUT_INCOMPLETE` 未变，本轮未触碰；读取与绑定完整 ≠ 策略可评估
- `std/index_daily`（732 code，完整平面）**仍未被 tip-rebase 使用**——确认属实：R15 release 里只有 `standard/reference/index_daily`（37 文件 / 273 行），没有 `standard/index_daily`。这是源选择，不是读取缺陷
- 供应商分页完整性 `UNKNOWN`
- 08-31/09-01 仅候选分区，生产 CURRENT 未切换
- `is_st` / 历史成分未绑定；复权因子 08-10 起恒 `1.0` 未分离

## 4. 台机状态

- 权威 commit：`572619c9`（3 个股票产品 17,040,667 行；`commit_id` 对指数变化不敏感，见 HIGH-1）
- `releases/` 内 4 个本轮 release（181019 / 181143 / 181638 / 181756），归档在 `cc_out/_archive_r12_round_20261026_181002`
- `PRODUCTION_CURRENT_WRITE=NONE`、无新数据下载、未删除任何文件、`ORDER_ALLOWED=false`、`PUBLISH_AUTHORIZED=false`
- 全程 **0 次** `allow_skip`（`allow_excluded` 仅用于结构性 `SKIPPED_*`，本轮计数为 0）
- 一次 R15 `HARD_BLOCK`（pass B 前未移开 R3），按设计 fail-closed，不是缺陷
