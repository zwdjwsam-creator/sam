# 台式机实施回执 — rcid 正式参与判断（R3）

生成时间：2026-10-26
主机：DESKTOP / ZHANGWEI
依据：你（主人）的实施决策 + SAM R2 交付的 4 补丁与 `PENDING_candidate_commit_v2.py`
范围：安装记账模块、落地当前批次完整指纹、修正「未验证却报正常」
**未做**：未跑全链、未改 `COMMIT.json`、未改生产 `CURRENT`、未开下载权限、未删任何目录

---

## 一、先认你指出的两处说过头

### 1.1 「C 最干净、下游谁都不用改」——不成立

代码核查：`tools/run_connected_pipeline.py` 是唯一真实调用方，它这样消费：

```
L617  commit_rc = cc.commit(rel, note=...)
L618  verify    = cc.verify()
L620  "status": "PASS" if verify.get("consistent") else "FAIL"
L652  "status": "PASS" if commit2.get("status") == "IDEMPOTENT_NOOP" else "FAIL"
```

它只看 `verify.consistent` 和 `status`，**不看 `release_content_id`**。
所以：写进 `COMMIT.json` 不会让任何现有下游自动获得保护。**你说得对，撤回该表述。**

### 1.2 「改错所有下游当场读不到」——没有依据

实测范围：

| 项 | 实测 |
|---|---|
| 本任务树内 `candidate_commit` 调用方 | **1 个**（`run_connected_pipeline.py`） |
| 该调用方读取方式 | `cc.verify()` / `cc.commit()` 直读 `COMMIT.json` |
| 是否存在独立的「切换指针」机制 | **无**。`COMMIT.json` 本身就是唯一引用（单次 `os.replace`） |
| 生产 `CURRENT_CACHE_RELEASE.json` | 本模块**从不写入**（`PRODUCTION_CURRENT_WRITE=NONE`） |

准确表述应为：**写坏 `COMMIT.json` 会让本任务树的 commit 阶段报 FAIL，并让任何走 `_read_commit()` 的校验读到不一致；生产 `CURRENT` 不受影响。** 我之前拿「最严重后果」代替核查，是我的错。

---

## 二、实施结果（已落地）

| 事项 | 状态 | 证据 |
|---|---|---|
| 安装记账模块 | **已装** | `tools/candidate_commit.py` 20,732 → **52,071 B**，sha `7cb9417c…bf2` → `7573eff5…33e9` |
| 旧版备份 | **已备** | `tools/_backup/candidate_commit.py.20261026_231040.v2.orig`（sha 校验一致） |
| 当前批次完整指纹 | **已落地** | `candidate/cc_commit/rcid/<release_id>.json`，`rcid=45c896f8…83a3` |
| 没 rcid 却报正常 | **已修** | emit 前 `CONTENT_IDENTITY_UNVERIFIED` / `consistent=false`；emit 后 `CONSISTENT` |
| 写进 `COMMIT.json` | **未做（按你要求）** | sha 全程 `6d526460…0820` 未变 |
| 生产指针 | **未动** | 同上 |

### 2.1 关键点：**v2 原样装上达不到你的要求，所以我装的是 v3**

你的判据是「`commit_id` 相同但 `rcid` 不同，就不能再判内容相同或走 NOOP」。
`PENDING_candidate_commit_v2.py` **做不到**：

```
L578-588  if current.commit_id == identity.commit_id and same_root and same_release_id:
              return {"status": "IDEMPOTENT_NOOP"}     ← 只看 commit_id
```

所以 v3 = v2 + 11 处收紧（每处都用断言式补丁，命中次数必须恰为 1，否则构建失败）：

| 补丁 | 收紧内容 |
|---|---|
| P1 | 新增契约文件与侧文件位置常量 |
| P2 | 指纹改按**冻结契约的 51 个产品**计算；声明有而缺 → `MISSING` 标记参与哈希且 `complete=False` |
| P3 | 指纹算不出**不再吞异常置 None**，改 fail-closed 抛错 |
| P4 | **NOOP 判据改为 `commit_id AND rcid`**；同 `commit_id` 不同 `rcid` → `CONTENT_DIVERGENCE_SAME_COMMIT_ID` |
| P5 | 重复目录分支：内容不同时**拒绝**登记为"等价副本" |
| P6 | rebind 分支：内容不同时**拒绝**移动引用（原注释"equal commit_id 证明同内容"已删） |
| P7 | 新增 `resolve_committed_rcid()` / `emit_release_content_id()`（不可覆盖） |
| P8 | `verify()` 无指纹 → **显式未验证**，不再静默跳过 |
| P9 | 未验证/不完整/绑定不符 → `consistent=False`，**不给 PASS** |
| P10 | CLI 增加 `--action emit-rcid` |

---

## 三、你要求的针对性验证（13/13 PASS）

| # | 用例 | 结果 |
|---|---|---|
| T1 | 相同内容重复计算，rcid 一致 | PASS |
| T2 | **只改指数** → rcid 变 | PASS `00b3f6b7…` → `d90cd2cf…` |
| T3 | **只改 ETF** → rcid 变 | PASS `d90cd2cf…` → `38c5994d…` |
| T4 | **等数量换键** → rcid 变（索引行数仍 3） | PASS `38c5994d…` → `4370c4db…` |
| T5 | 声明有而缺 → `INCOMPLETE` 且列出缺项 | PASS `missing_declared=["ETF_FACTOR_DAILY_R1"]` |
| T6 | 旧 `commit_id` 兼容（v2 == v3，fixture） | PASS 两者均 `9ad83abf…` |
| T7 | **生产 release `commit_id` 仍 `572619c9`**（只读） | PASS |
| T8 | 无 rcid → 明确未验证且不给 PASS | PASS `CONTENT_IDENTITY_UNVERIFIED` |
| T9 | emit 后 verify 读侧文件且 `CONSISTENT` | PASS `source=SIDE_FILE` |
| T10 | **emit 不改 `COMMIT.json`**（sha 前后一致） | PASS |
| T11 | emit 重复调用 → `ALREADY_SAME`（不可覆盖） | PASS |
| T12 | 旧账本无 rcid → 拒绝 NOOP、不写文件 | PASS |
| T13 | **`commit_id` 同但 rcid 不同 → 拒绝 NOOP** | PASS `CONTENT_DIVERGENCE_SAME_COMMIT_ID`，`COMMIT.json` 未变 |

T13 是这次的核心判据，实测：

```
commit_id_same = True     (9ad83abf5d4f6051，两态相同)
rcid_A         = 00b3f6b7…
rcid_B         = 7bac5766…   (只动指数)
commit_status  = CONTENT_DIVERGENCE_SAME_COMMIT_ID
commit_json_unchanged = True
```

---

## 四、v2 里另外两个缺陷（我核出来的，v3 已一并修）

### 4.1 `coverage` 里的「合同部分」是死代码

```
L436  ident_js = Path(release_dir) / "SEAL.json"
L438  compiler_req = (seal_for_cov.get("formal_required_missing") is not None and ...)
```

`SEAL.json` 的实际键是 `release_id/all_pass/asof/price/sw/valuation/inherited/finance/finance_applied/sealed_at` —— **没有 `formal_required_missing`**（那字段在 `RELEASE.json`）。
所以 `compiler_req` **恒为 `False`**，`compiler_required=[]`。
即所谓「3/51 覆盖」里关于交付合同的那一半**从未生效**。

### 4.2 指纹失败被静默吞掉

```
L449  except CommitError: raise
L451  except Exception as e:
L452      identity["release_content_id"] = None
L453      identity["coverage"] = {"ERROR": ...}
```

算不出指纹仍继续提交，`rcid=None`，随后 NOOP 判断又只看 `commit_id` —— 两处叠加即可产出「绿灯但没验」。

---

## 五、必须声明的已知限制

**`junction_content_proven = False`（不是 true）**

36 个 junction 产品的指纹取的是**目标身份**（路径 + 目标 `RELEASE.json` 的 id），不是借来的字节。
后果：**若目标 release 的文件被原地改写而 `RELEASE.json` 的 id 未变，rcid 不会变。**

本次事故涉及的两个产品是实体目录（`INDEX_DAILY_R1` / `ETF_DAILY_PIT_R1`，非 junction），所以能被 rcid 抓到。但这条限制我不藏着 —— 侧文件里 `junction_content_proven=False` 是显式写出的。

彻底解法（未做，需你定）：junction 目标也纳入内容哈希，或禁止原地改写目标 release。

---

## 六、契约冻结说明

`candidate/cc_commit/RCID_PRODUCT_CONTRACT_R1.json`

| 项 | 值 |
|---|---|
| `contract_id` | `RCID_C1_df7df8ba9f71ef72` |
| `declared_products` | **51** |
| `formal_required_products` | **10**（从编译器源码 `required=[...]` 正则抽取，非手抄） |
| 断言 | 10 ⊂ 51（不成立则拒绝生成契约） |
| 排除项 | `_` 前缀目录（含 `_qa`）+ 7 个元文件，附理由 |
| 重跑同值 | 是（确定性哈希） |

> 说明：`ETF_FACTOR_DAILY_R1` / `INDEX_FACTOR_DAILY_R1` **不在**编译器那 10 个正式必需里，但**在** 51 个声明里，所以改它们 rcid 会变。

---

## 七、回滚

```powershell
Copy-Item -LiteralPath "E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\tools\_backup\candidate_commit.py.20261026_231040.v2.orig" `
  -Destination "E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\tools\candidate_commit.py" -Force
```

删侧文件即可回到「未验证」状态（`COMMIT.json` 不受影响）：
```powershell
Remove-Item "E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\candidate\cc_commit\rcid\<release_id>.json"
```

台账：`INSTALL_V3_SHA_LEDGER_R1.json`

---

## 八、对下游的**实际**影响（核查结果，不是推断）

| 消费者 | 影响 |
|---|---|
| `tools/run_connected_pipeline.py` L620 | `verify.consistent` 现在依赖 rcid。**未 emit 时 commit 阶段会如实报 FAIL** |
| 同文件 L652 | `same_input_replay` 需 `IDEMPOTENT_NOOP`。已 emit 后仍成立（实测 `IDEMPOTENT_NOOP`） |
| 生产 `CURRENT_CACHE_RELEASE.json` | 不受影响（本模块从不写） |
| 其他仓内调用方 | 本任务树内无 |

**行为变化要点**：以前「`commit_id` 相同就静默 NOOP」，现在「无 rcid 就 `CONTENT_IDENTITY_UNVERIFIED` 并拒绝 NOOP」。
这是**故意**变严：宁可报未验证，不许猜相同。

---

## 九、复算命令

```powershell
cd E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\sam_led_rectification
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 MAKE_RCID_CONTRACT_R1.py
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 BUILD_CANDIDATE_COMMIT_V3_R1.py
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 RCID_V3_TARGETED_TESTS_R1.py
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 EMIT_PROD_RCID_R1.py
```

---

## 十、仍未做（等授权）

- 未跑全链（按 3.1 结论：现网 asof 未变 → 必 NOOP，跑了也写不进 `COMMIT.json`）
- 未把 rcid 写进 `COMMIT.json` 顶层（按你要求留到下一次真实提交）
- 未改生产 `CURRENT`
- 未删 3 个重复 release 目录
- 未处理 `junction_content_proven=False` 的彻底解法
- 唯一缺失分钟日 `2026-09-04` 仍未补
