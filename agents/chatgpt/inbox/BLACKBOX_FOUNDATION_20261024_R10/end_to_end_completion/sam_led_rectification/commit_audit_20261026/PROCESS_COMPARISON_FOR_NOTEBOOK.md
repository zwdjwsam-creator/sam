# 流程对照表 FOR NOTEBOOK（笔记本请逐段回答右侧问题）

台机结论先给：**全链 `PASS`，12/12 verdicts 为真，生产零写入。** 但流程上有 **3 处"两个名字指同一堆字节"的分叉**（第 5、6、7 段），需要笔记本对照确认是设计还是本地差异。

- 台机：`ZHANGWEI` / `E:\BLACKBOX\.venv\Scripts\python.exe`
- 本次 run 产物：`deliverables\CONNECTED_PIPELINE.json`
- 绑定的编译器 release：`BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20261026_181638`
- `COMMIT.json` 实际引用：`..._20261026_181019`（**不是 181638**，见第 6 段）

---

## 第 1 段｜传输门（transport_gate）

| 项 | 台机值 |
|---|---|
| 入口 | `tools/run_connected_pipeline.py:212 response_gate()` |
| 决定 | 这批增量字节能不能进清洗（PROVENANCE 来源、行带、日期是否被篡改） |
| 台机结果 | `PASS`；`SUPPLIER_COMPLETENESS=UNKNOWN`；`ACQUISITION_RELEASED=false` |
| 样本会话 | `2026-08-31` / 5,212 行 / `sha256=553bad19…b063` / `request_evidence_origin=SIDECAR` |
| 负控 | `tampered_date_blocked=true`、`self_cert_blocked=true` |

**笔记本请回答**
1. 你们那批会话的 `request_evidence_origin` 也是 `SIDECAR` 吗？`SUPPLIER_COMPLETENESS` 也是 `UNKNOWN` 还是拿到了值？
2. 你们是否也跑了"篡改日期"和"自证"两个负控？结果是否同样为 `true`？

---

## 第 2 段｜R15 清洗重放（cleaning_r15）

| 项 | 台机值 |
|---|---|
| 入口 | `tools/run_connected_pipeline.py:310 run_r15_cleaning()` |
| 产物 | `candidate\r15_releases\R15_REPLAY_20260924_R3\standard` |
| 耗时 | **1.0 s** |
| carry-forward（实测，不是记忆值） | `price/stock_ohlcv_daily` **232 → 232**，`absent 0`；`price/ETF_daily` **37 → 37**，`absent 0` |
| 真实来源 | `数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R45_DAILY_TIP_ASOF_20260924_20260925_034534` |

**笔记本请回答**
3. 你们 carry-forward 的 `src_files / dst_files` 是 **232 / 37** 这两个数吗？（若不同，是清洗口径差异还是母本 release 不同 —— 请给出你们的 R45 母本 id）
4. 你们的 R15 重放耗时量级？若显著长于 1 s，是物化了整棵树还是只搬 SELECTED_SUBTREES？

---

## 第 3 段｜编译器调用（compiler）

| 项 | 台机值 |
|---|---|
| 入口 | `tools/run_connected_pipeline.py:322 compile_release()` |
| 实际子进程 | `run_original_compiler_candidate.py --cleaning-json …R15…RELEASE.json --parent-root …FUND_NAV_PIT_ASOF_20260924… --run-target-date 2026-09-24` |
| 上游实现 | `任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1\cache_compiler_tip_rebase_from_current_r1.py:528 main()` |
| 耗时 | **59.1 s** |
| 结果 | `PASS`，`bound_release_root=..._181638` |

**声明式绑定（R13 起，禁止 `newest_release`）**，`run_connected_pipeline.py` 内四步：

| 行 | 动作 |
|---|---|
| 333–338 | 把旧 `TIP_REBASE_LAST.json` 改名成 `TIP_REBASE_LAST.prev_<pid>.json`（**先搬走，防止读到上一次的声明**） |
| 345–356 | 跑完读新声明；读不到或与本次不一致 → `PipelineStop("compiler","DECLARED_OUTPUT_STALE")` |
| 417 | 把经 7 项校验的 `root` 写入 `rc["bound_release_root"]` |
| 423–433 | `newest_release()` 改为直接 `raise PipelineStop(..., "NEWEST_RELEASE_FORBIDDEN")` |

**笔记本请回答**
5. 你们 `TIP_REBASE_LAST.json` 的"先搬走再跑"这步在吗？如果只做"跑完再读"，那读到上一轮声明的窗口就还在。
6. 你们 `bound_release_root` 与 `COMMIT.json.release_root` 是否相等？（台机**不相等**，见第 6 段 —— 这题最关键）

---

## 第 4 段｜编译器内部 5 个门

| 门 | 位置 | 台机语义 |
|---|---|---|
| 源选择 | `tip_rebase_from_current_r1.py:150-196` | 指数同时登记两个源：`RAW_FULL_HISTORY`（:155）与 `RAW_NONE`（:159，`cc.scan_parquet_independent`） |
| 读闭包 | `:206` → `daily_incremental:334 assert_read_closure(...)` | `semantics="FILE_SET_IDENTITY"`，`expected_files`（独立 walk）/`enumerated_files`/`read_files` 三者**集合相等** |
| 列名兼容 | `daily_incremental:463` | `pick("code","security","order_book_id","symbol","canonical_code")` ← 本轮"找回 1,464 个指数文件"就靠这个别名 |
| KEY_CHECK | `tip_rebase_from_current_r1.py:398` | 逐产品键集比对，写入 `:414 key_check` |
| 封版 | `:665-677` `SEAL.json` + `_qa/TIP_REBASE_QA.json`；`:683` 写 `TIP_REBASE_LAST.json` | 台机 `SEAL.all_pass=true`，`formal_required_missing=[]` |

**未修（台机上轮已报，仍在）**
- `assert_read_closure` 的 `expected_files==[]` 无守卫：源目录缺失时 `0=0=0` 静默通过 → `DATA_ABSENCE_GATE` 意义上的"空不算齐"没落实。
- `expected_keys_from_frames` 内的 `report.append({"file": str(p), …})` 是死代码，一旦被喂空帧就 `NameError`。

**笔记本请回答**
7. 你们的 `assert_read_closure` 有没有 `expected==0` 守卫？有没有那个死代码 `report.append`？
8. 你们的指数源也是 `RAW_FULL_HISTORY` + `RAW_NONE` 两个都登记吗，还是一个？

---

## 第 5 段｜提交（commit）

| 项 | 台机值 |
|---|---|
| 入口 | `tools/run_connected_pipeline.py:616 import candidate_commit as cc` |
| 模块字节 | `candidate_commit.py` **20,732 B**，`sha256[:16]=7cb9417cdb96be7f` |
| `REQUIRED_PRODUCTS` | **3 个**：`STOCK_DAILY_PIT_R1`、`STOCK_DAILY_RAW_PIT_R1`、`STOCK_FACTOR_DAILY_R1` |
| 返回值 | `status=IDEMPOTENT_NOOP`，`commit_id=572619c945d48f1b…ec0876`，`note="duplicate root with identical content; reference unchanged"` |
| `COMMIT.json` sha256 | `6d52646095e5d850…c500820` |

> 台机实测：`verify` 只遍历 `COMMIT.json["products"]`。release 里 **51 个产品，账本只含 3 个**；未覆盖 48 个、**1.377 亿行（占 74.8%）**。指数本轮变了 106,549 个键，`commit_id` 一字未动。

**笔记本请回答**
9. 你们 `candidate_commit.py` 的字节数与 `sha256[:16]` 是多少？是否也是 **20,732 / 7cb9417c**？
10. 你们 `REQUIRED_PRODUCTS` 也是 3 个，还是已扩到编译器的 10 个？
11. 如果你们的覆盖率也是 3/51，那么"提交一致/幂等"对那 48 个产品是否也属于**结构上不可能失败**？请明示是否接受。

---

## 第 6 段｜同名异构分叉 ①：绑定根 ≠ 提交引用根

| 主体 | release |
|---|---|
| pipeline `stages.compiler.bound_release_root` | `…_20261026_181638` |
| `COMMIT.json.release_root` | `…_20261026_181019` |

`verify` 仍然 `PASS`，因为 **`commit_id` 只哈希数据**，两棵树内容相同。于是出现"pipeline 说绑了 B、账本指向 A、两边都算通过"。

同段还有：`same_input_replay` 产出第三棵 `…_20261026_181756`，同样 `IDEMPOTENT_NOOP`，`commit_id` 不变 —— 三棵 release 树、一个 commit_id、零新引用。

**笔记本请回答**
12. 你们的 `bound_release_root` 与 `COMMIT.json.release_root` 相等吗？
13. 你们是否把"三棵树同一 commit_id"当作幂等通过？还是要求**引用根必须等于本次绑定根**？

---

## 第 7 段｜同名异构分叉 ②（台机本轮新发现）：候选 release 借生产字节

4 个产品在候选 release 内是 **junction**，指向**别的生产 release**：

| 产品 | junction | 指向 |
|---|---|---|
| `CORP_SHAREHOLDER_TOP10_PIT_R1` | `data`、`indexes` | `BLACKBOX_CACHE_R1_PAIRED_R22_…` |
| `CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1` | `data`、`indexes` | 同上 |
| `FUND_NAV_PIT_R1` | `data\history` | `BLACKBOX_FORMAL_CLEANING_R39_ASOF_20260902_…` |
| `INDEX_WEIGHT_PIT_R1` | `year=2014/2015/2016` | `BLACKBOX_CACHE_R1_INDEX_WEIGHT_PIT_ASOF_20260702_…` |

后果：候选 release **不自包含**。生产那边归档/清理后，候选静默悬空，而 `SEAL.all_pass` 与 `commit.verify` 都不会报。

附带：`FUND_NAV_PIT_R1` 内部路径最深 **279 字符**，且有 **1 个同名 parquet 在两层深度各一份**（`ETF_NAV__incremental_get_extras__20260713_20260820__clean.parquet`）。

**笔记本请回答**
14. 你们那 4 个产品是**实体目录**还是 junction？
15. 你们 `SEAL` 是否记录每个 junction 的目标 release id？（台机**没有**记录，只写了目录名）

---

## 第 8 段｜发布门 + 生产只读（publish_gate_probe）

| 项 | 台机值 |
|---|---|
| 入口 | 原始 `blackbox_daily_increment_publish_gate_r1.publish_atomic`（未 dry-run bypass） |
| 结果 | `EVALUATED_NOT_PUBLISHED`，`OPERATIONAL_READINESS=PASS`，`CURRENT_PUBLISH=ALLOWED`，`published=false` |
| 生产 | `production_digest_changed={}`、`PRODUCTION_CURRENT_WRITE=NONE`、`NEW_DATA_ACQUISITION=NONE` |

**笔记本请回答**
16. 你们 `publish_atomic` 是"评估可信但不发布"，还是直接跳过/自填返回？

---

## 对照清单（笔记本逐项打勾）

| # | 项 | 台机 | 笔记本 |
|---|---|---|---|
| 1 | `candidate_commit.py` 字节 / sha16 | 20,732 / `7cb9417c` | ? |
| 2 | `REQUIRED_PRODUCTS` 个数 | 3 | ? |
| 3 | 账本覆盖产品数 / release 产品数 | 3 / 51 | ? |
| 4 | `bound_release_root` == `COMMIT.json.release_root` | **否** | ? |
| 5 | `assert_read_closure` 有 `expected==0` 守卫 | **否** | ? |
| 6 | R15 carry-forward 文件数 | 232 / 37 | ? |
| 7 | junction 产品个数 | 4 | ? |
| 8 | `SEAL` 记录 junction 目标 release id | **否** | ? |
| 9 | `publish_atomic` 真评估 | 是 | ? |
| 10 | 全链 verdicts | 12/12 true | ? |

---

## 台机这边的定位（供笔记本判断优先级）

- 台机认为**阻断级只有一条**：`commit` 身份不覆盖编译器自己 `required` 的 10 个产品（ETF、INDEX 已证会大幅变动）。
- 其余（第 6、7 段）属于"能通过但说不清"的分叉，建议先定性（设计/缺陷），不要急着改代码。
- 台机不改 `candidate_commit.py` 的 `REQUIRED_PRODUCTS` —— 这是接口契约变更，等笔记本对照后定口径。
