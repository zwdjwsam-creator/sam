# DESKTOP_CLOSURE_RERUN_RESULT — 台机复验（R12：编译器内部漏读修复）

- 复核主机：`ZHANGWEI`（台机本机进程，非 SAM 代跑）
- 时间：2026-10-25 23:39 → 23:55 (+08:00)
- 结论：**CLOSURE_FIX_CONFIRMED_ON_DESKTOP**，8 条判据全过，独立核验 15/15
- 但**发现 1 个中等严重的新问题**（release 选择按目录名取最新），且它由我的归档命名触发

---

## 0. 先核身份，再核代码，最后才跑

| 文件 | 字节 | sha256 前16 | 与 SAM 声明 |
|---|---|---|---|
| `cache_compiler_daily_incremental_r1.py` | 42,333 | `2a82d12b4c4ce12a` | ✅ 一致 |
| `cache_compiler_tip_rebase_from_current_r1.py` | 26,486 | `c1d431a204d09897` | ✅ 一致 |
| `tools/run_connected_pipeline.py` | 30,487 | `b7a7179b8e8c6f1e` | ✅ 一致 |

`compile()` 三个全过。备份都在（38,650 / 25,087 / 28,893，与"修前"字节相符）。

**不只看 sha，还核了代码实体**：`_lp` / `_unlp` / `os.walk` 枚举 / `assert_read_closure` / `READ_REPORT` / `READ_FAILED` 记日志 / `PRICE_READ_INCOMPLETE` raise / `MATERIALISED_UNREADABLE` raise —— 全部真实存在，不是空壳。

---

## 1. 八条判据（台机自算，不读 runner verdict）

| # | 判据 | 期望 | 台机实测 | 结果 |
|---|---|---|---|---|
| 1 | R15 `stock_ohlcv_daily` | 234 文件 / 12 r2_repair | **234 / 12** | PASS |
| 2 | `READ_CLOSURE` | 234=234=234、ETF 37/37/37、failed=0、OK=true | **完全一致** | PASS |
| 3 | 错误标记 | 0 条 | `READ_FAILED=0` `ENUM_INCOMPLETE=0` `PRICE_READ_INCOMPLETE=0` `READ_CLOSURE_BROKEN=0` | PASS |
| 4 | 三产品 `year=2026` | 959,896 ×3 | **959,896 / 959,896 / 959,896** | PASS |
| 5 | 七月六天 distinct 代码 | 5209/5210/5208/5208/5208/5207 | **5209/5210/5208/5208/5208/5207** | PASS |
| 6 | 生产 CURRENT/STATE | 未变 | runner `{}` + 我自己跑前跑后 9 文件 digest 全等 | PASS |
| 7 | 负控日志 | 存在、含 exit_code 1 | 7,612B，**`"exit_code": 1`**（你在第 73 行） | PASS |
| 8 | 二次幂等 | `IDEMPOTENT_NOOP` + `CONSISTENT` | **A:COMMITTED → B:IDEMPOTENT_NOOP，verify CONSISTENT** | PASS |

判据 4、5 我没有读 `TIP_REBASE_QA.json` 就下结论 —— 台机用 pyarrow 直接数 `part_2026.parquet`、自己 `nunique()` 数 code；之后才拿 QA 对账，两边一致。

`READ_CLOSURE` 我另加了一条交叉：日志里的 `enumerated` 必须等于磁盘实际文件数。相等。

---

## 2. 我抓到的真问题：commit 曾锚在"修前"内容上

第一次 PASS 之后我没有直接交，而是追问了一句：**行数变了 31,136，payload 哈希为什么没变？**

追下去的结果：

| 树 | rows_2026 | 全产品行数 | payload sha16 | commit_id16 |
|---|---|---|---|---|
| `_prev_..._215558` / `_prev_..._215655`（修前） | 928,760 | 17,009,531 | `ad9170c0` | `2f755779` |
| `..._234016/234111/234457/234552`（修后） | **959,896** | **17,040,667** | `f929f8cc` | `572619c9` |

而当时的 `COMMIT.json` 是：`commit_id=2f755779`、`rows=17,009,531`、`release_root=.../_prev_..._215655`、`rebound_at_cn=23:41:03`、`status=REBOUND_SAME_CONTENT_NEW_ROOT`。

**新编译的 4 个 release 一个都没进账本；账本描述的仍是修前的破内容。**

### 根因（一半是我的错）

```python
def newest_release(out_root):
    rels = sorted([p for p in out_root.iterdir() if p.is_dir()], key=lambda p: p.name)
    return rels[-1]
```

`_` = 0x5F，`B` = 0x42。我按手册"移动不删除"把旧 release 同名加 `_prev_` 前缀**留在 `releases/` 里**，于是它按字典序排到了最后，成了"最新 release"。`candidate_commit.build_identity()` 就在这棵归档树上算 identity，`commit_id` 自然等于旧值 → 走 `REBOUND_SAME_CONTENT_NEW_ROOT` → 报 `IDEMPOTENT_NOOP` 且 `commit_consistent: true`。

**所以第一次那个 PASS 是假通过。** 我把归档移到 `candidate/cc_out/_archive_pre_fix_closure/`（移出 `releases/` 之外）后重跑：

- Pass A：`COMMITTED`，`commit_id=572619c9`，`release_id=..._234902`，`seq=4`，`rows=17,040,667`
- Pass B：`IDEMPOTENT_NOOP`（`commit_file_sha256` 同为 `5798fa7c...`），`verify=CONSISTENT`，`second_release_id=..._235444` 提交零新增

这才是幂等的真证据。

### 但这里有一条不是我的错

**任何**名字排在 `BLACKBOX_*` 之后的目录都会顶替真正的最新 release。`_prev_` / `_bad_` / `zz_` / 小写开头都会中招。这是 `newest_release()` 的选择缺陷，不是我一个人的操作问题 —— 建议加白名单前缀 + 断言 `identity.products.rows` 不低于已知下界。

---

## 3. 你自己承认的指数缺口：核实为真

`READ_CLOSURE` 只有两个键：

```json
{"STOCK_DAILY_PIT_R1": {...234...}, "ETF_DAILY_PIT_R1": {...37...}}
```

而同一条日志里明确写了 `read stock files=234 etf=37 index=1501`。**1501 个指数文件读进 273 行，但没有任何 `materialised / enumerated / read_ok` 三元组、没有 `CLOSURE_OK`。** 同类静默漏读在指数路径上仍然可以藏住。你没假装补齐，这点我确认属实。

---

## 4. 顺手一个反讽：我自己的取证脚本也踩了同一个坑

写探针脚本时用 `pathlib.read_bytes()` 去读那 12 个 `r2_repair` 文件，直接 `FileNotFoundError`：

```
FileNotFoundError: ... stock_ohlcv_daily__XSHE__DAILY__2026-07-03__fq_none__raw_none__r2_repair__RU_stock_ohlcv_daily_XSHE_DAILY_2026-07-03.parquet
```

不经过 `_lp` 的任何新代码都会复现。建议收一个公共 `lstat/lp` 小工具，业务代码禁止裸路径 `read_bytes`/`read_parquet`。

---

## 5. 补上你 §7 标 UNVERIFIED 的那一项

> 台机 `LongPathsEnabled` 的实际值仍未读到

**实测：0。** `HKLM\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled = 0`，OS `10.0.26200`。

这正是同一个 234 文件在 SAM 得到 959,896、在台机修前只有 928,760 的原因。现在修复走 `\\?\` 前缀，不再依赖该策略。

---

## 6. 未变的部分（不假装）

- `V4 BLOCKED_INPUT_INCOMPLETE` 未变，正式回测未过，本轮没碰它 —— 读取与链完整性 ≠ 策略可评估
- 指数无闭包探针（已核实）
- 供应商分页完整性 `UNKNOWN`
- 08-31/09-01 仅候选分区，生产 CURRENT 未切换（未授权）
- `is_st` / 历史成分未绑定
- 复权因子 2026-08-10 起恒 `1.0` 成因未分离

## 7. 台机状态

- 权威 commit：`572619c9`（17,040,667 行，修后内容）
- `releases/` 只留 6 个真实 release；2 个修前归档已移出到 `_archive_pre_fix_closure/`
- `production CURRENT`：**零写入**；无新数据下载；未删除任何文件
- `ORDER_ALLOWED=false`、`PUBLISH_AUTHORIZED=false`

## 8. 全程没有一条 `allow_skip`

`read_price_frame` 现在 fail-closed，本轮所有 run 都按默认行为走，没有一次放宽。
