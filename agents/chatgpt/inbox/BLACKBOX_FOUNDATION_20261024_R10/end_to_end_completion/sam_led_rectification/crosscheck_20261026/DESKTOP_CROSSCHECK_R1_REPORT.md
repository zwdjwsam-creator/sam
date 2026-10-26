# DESKTOP_CROSSCHECK_R1 — 台机对 SAM 三项基准的复核结论

- 主机 `ZHANGWEI`，只读复核，未改任何代码、未切 CURRENT、未下载。
- 被核基准：`WORKFLOW_COMPARISON_COMMIT_AND_COVERAGE.md`（12,724 B，
  `sha256=fc617c3f671314030497d67ac143a194f6b4866cd796d64716f28efcdda8729b`）

| 项 | 台机判定 |
|---|---|
| A 提交模块 | **PASS** |
| B 产品覆盖 | **BLOCKED_ON_DECISION**（`PRODUCT_COVERAGE=3_OF_51`） |
| C 调用版本 | **PASS_WITH_VERSION_DEVIATION** |
| **总结论** | **BLOCKED_ON_DECISION** —— 不得作为进入全链复验的通行证 |

---

## A. 提交模块 — PASS，但 SAM 的表格漏了三个边缘

`--action verify` 实测：`status=CONSISTENT`，四个布尔
`checkpoint_sha_matches=true`、`checkpoint_identity_matches=true`、
`payload_matches=true`、`payload_root_missing=false`，`rc=0`。

`payload_detail` 的键**恰好只有 3 个**（三只股票产品）——与 B 段缺口自洽。

**A2 五条决策顺序与代码逐条对上**（行号为本机现行）：

| # | 守卫 | 行 | 状态 |
|---|---|---|---|
| 1 | `same_root and same_release_id` | 204 | `IDEMPOTENT_NOOP` |
| 2 | `same_root and not same_release_id` | 211 | `REPAIRED_SAME_ROOT_FIELD_DRIFT` |
| 3 | `old_root.exists() and not same_root` | 257 | `IDEMPOTENT_NOOP` |
| 4 | （落到）重绑 | 318 | `REBOUND_SAME_CONTENT_NEW_ROOT` |
| 5 | 内容不同 | 378 | `COMMITTED` |

`SEAL` 硬门确认：第 95 行**只读 `all_pass`**；第 97 行校验 `REQUIRED_PRODUCTS` 存在。SAM 的 A5 描述属实。

### 表格未覆盖的三处

**A-EDGE-1（LOW）** 规则 3 的守卫对空值失效。
第 203 行 `old_root = Path(str(current.get("release_root") or ""))`；`Path("") == Path(".")`，
`.exists()` **恒为 True**。于是 `release_root` 为空/损坏时会走规则 3 返回
`IDEMPOTENT_NOOP (duplicate root)`，而不是规则 4 的重绑 —— 一个"引用已失效"的账本会被判成"正常重复"。

**A-EDGE-2（MEDIUM）** 空产品 = 缺失产品。
第 97 行用 `.exists()` 判必需产品，**空目录也通过**；`product_digest()`（第 78–79 行）对无 parquet 返回
`{"parts":0,"rows":0,"sha256":None}`，在 `commit_id` 里与"产品不存在"不可区分。

**A-EDGE-3（HIGH）** `commit_id` 跨机不可复现。
`content`（第 110–114 行）纳入了 `source_cleaning_release` 与 `parent_release_id`：

| | 值 |
|---|---|
| 台机 `source_cleaning_release` | `R15_REPLAY_20260924_R3` |
| 台机 `commit_id` | `572619c945d48f1b…` |
| SAM `commit_id` | `c87b3a56…83bc4` |

⇒ **即便三只股票产品字节完全一致，两岸 `commit_id` 也必然不同。**
第 104–108 行的注释自己写着"构建期字符串不得进哈希"，这两个字段把同一缺陷从另一条路放了回来。

> 因此 `commit_id` 的真实语义是 **"同一台机、同一 lineage 下的三产品内容"**，不是内容指纹。
> 与 SAM 的结论叠加后，`commit_id` 在两个方向都失效：
> **内容变→id 不变**（3/51 覆盖），**内容同→id 可变**（血统字段）。

---

## B. 产品覆盖 — BLOCKED_ON_DECISION

台机独立复算，与 SAM 同向且更全：

```
release 实有产品   51       账本覆盖 3     未覆盖 48
覆盖行数   46,443,546      未覆盖行数 137,706,659   (74.78%)
```

指数反例（台机侧）：`INDEX_DAILY_R1` 2026 行 **273 → 106,822**，
而 `cc_out\releases` 下 **10 个 release 的 `commit_id` 全为 `572619c9…`**。

按 SAM B5 要求：记 `BLOCKED_ON_DECISION`，**不判 PASS**。
P3 方案见 `RELEASE_CONTENT_ID_R1_DESIGN.md`（未实施）。

---

## C. 调用版本 — 7 个文件里 6 个字节一致，1 个按预测不同

| # | 文件 | 本机 | SAM | 结果 |
|---|---|---|---|---|
| 1 | `tools\candidate_commit.py` | 20,732 / `7cb9417c` | 同 | OK |
| 2 | `tools\run_connected_pipeline.py` | 35,051 / `6bea0313` | 同 | OK |
| 3 | `tools\run_original_compiler_candidate.py` | 4,138 / `6eef49f2` | 同 | OK |
| 4 | `candidate\run_r15_cleaning_replay.py` | 29,825 / `f2c858e4` | 同 | OK |
| 5 | `cache_compiler_daily_incremental_r1.py` | 47,910 / `a887f7c7` | 同 | OK |
| 6 | `cache_compiler_tip_rebase_from_current_r1.py` | 30,661 / `094eb6ef` | 同 | OK |
| 7 | `脚本\run_blackbox_daily_incremental_data_plane_r1.py` | **46,492 / `949e95c7`** | 41,183 / `deb363bc` | **按预测不同** |

第 7 号与 SAM 的预测**完全吻合**（46,492 B / `949e95c7`），确认为 D1/D2 已打补丁的本机版，不是差异。

### C-1 换行建议不要照做

SAM 建议"比对时先归一化 CRLF"。**本机实测：照做会产生 5 个假 DIFF。**

| 文件 | CRLF 数 | LF 数 | |
|---|---|---|---|
| 1–4、7 | 452/718/115/631/1093 | 与 CRLF 相等 | 全部 CRLF |
| 5–6 | 0 | 1156/719 | 纯 LF |

SAM 哈希的是**原始字节**。归一化后 `match_crlf = 2/7`，按原始字节 `match_raw = 6/7`。
**结论：按原始字节比对，勿归一化。**

### C-2 运行时版本不一致（需要先报差异）

| | 本机 | SAM 期望 |
|---|---|---|
| python | 3.12.10 | 3.12.10 |
| **pandas** | **2.3.3** | **3.0.3** |
| **pyarrow** | **21.0.0** | **24.0.0** |

SAM 自己写了"版本不同先报差异再跑——pandas 3.x 的 groupby/dtype 差异会影响 KEY_CHECK"。
台机本轮此前的全链结果是在 **pandas 2.3.3** 下产生的，**与 SAM 基线不构成同环境对照**。

### C-3 加载方式（已核）

`run_original_compiler_candidate.py:29-31` 的 `COMPILER_PATH` 硬编码指向
`E:\BLACKBOX\任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1\cache_compiler_tip_rebase_from_current_r1.py`（本机路径，正确）；
`spec_from_file_location("tip_rebase_candidate", COMPILER_PATH)`。
真编译器实际收到的 argv（来自 `evidence\ORIGINAL_COMPILER_RECEIPT.json`）末尾为 **`--no-publish`** ✅。

---

## D. 顺带：消息里那条 HUB 链接是 404

`agents/chatgpt/inbox/BLACKBOX_FOUNDATION_R10/...` → HTTP 404。
真实路径是 `agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/...`。
若 INBOX 指针也写错，别人点开即 404，建议一并修正。

---

## E. 下一步

1. **token 轮换**（安全，最高优先）——见同目录 `TOKEN_REDACTION_RECEIPT.json`
2. **B 的 P1/P2/P3 决策**
3. 运行时版本对齐（pandas/pyarrow），或明确声明本轮结果不可与 SAM 基线互比
