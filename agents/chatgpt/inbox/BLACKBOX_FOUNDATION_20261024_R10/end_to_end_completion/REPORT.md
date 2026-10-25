# BLACKBOX R10 端到端完成 — R12 修订（输入面逐格修复 + 复核回应）

任务: `BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025`  
生成时间: 2026-10-25T11:22:19+08:00  
总判定: **BLOCKED_PARTIAL_EXECUTION**（阶段 1 = BLOCKED；16 日回测 = COMPLETED，成交 2 笔，绩效**不可准入**）

## 0. 本轮定位

阶段 1 仍是 **BLOCKED**，不是措辞问题：B1（逐日因子血缘）、B3（基金产品 0 行）、
B4（CURRENT 不服务 08-31/09-01）、B6（生产游标）、B7（全库 RAW↔CACHE 等价门）都还开着。
本轮只做两件事：把上一版被指出的**静默缺输入**与**分类错误**修到底，并把一个新暴露的
**「COMPLETED 但 0 交易」** 缺陷定位到具体代码行、修好、再复跑取证。

- 上一版的真实问题不是「跑没跑完」，而是引擎报 `COMPLETED` 时策略逻辑其实没执行：
  09:05「昨日涨停名单」因 `high_limit` 缺失抛 `boolean value of NA is ambiguous` 而中止。
- 本轮先把限价/状态从保留 RAW 复原（逐格对账），再让缺输入**硬失败**；
  修完后第一次重跑出现 `COMPLETED` + **0 交易**，本文 2.5 节记录了抓到根因、
  修复、以及修复后同一探针从 5 次取数失败降到 0 次的全过程。
- 结论不改：**阶段 1 = BLOCKED / 部分执行**，绩效数字不作为业绩。不重开清单、
  不做源码导出轮、不申请采集授权。

## 1. 交付一：数据面（分类错误已修，按产品口径测量）

- 54 datasets / 75 层实测 / 合同豁免 12 /
  BLOCKED 8 / 范围未定 1 /
  可读但游标未绑定 33
- `CALENDAR_CN_EXCHANGE`：`calendar_date` 识别为 **CALENDAR_AXIS**，RAW 2014-01-01~2026-08-10，
  CLEAN 2014-01-01~2026-09-02，不再是 `NO_TIME_AXIS`
- 时间列改为「抽样 schema 并集」判定，混合族根不再整体丢轴
- 族根目录不再冒充单产品口径：解析到产品子目录才测量；解析不出的 9 层显式标
  `PRODUCT_DIR_UNRESOLVED`（PRICE_ETF_DAILY RAW、PRICE_INDEX_DAILY RAW、SECURITY_MASTER RAW 等）
- `FACTOR_VALUE` → **BLOCKED_NO_ADMITTED_PRODUCT**（挂载发布里没有可准入产品，这是缺席事实，不是合同豁免）
- `UNDETERMINED_SCOPE` → **UNRESOLVED_SCOPE**（无层、无身份、无控制性定义）
- 页脚极值只作为外边界，不产生完整性结论

断点/续跑绑定（`CANDIDATE_CHECKPOINT_BINDINGS.json`）：

- 已验证：`STOCK_DAILY_PIT_R1` — 本地候选断点 `R12_CANDIDATE_CHECKPOINT_1`，
  同日重放幂等、部分日替换而非跳过
- 有保留批次但未绑定验证：22 个产品
- 无保留批次：31 个产品 → 明确 BLOCKED，不猜起始日

## 2. 交付二：真实查询 + 原引擎（缺输入改为硬失败）

### 2.1 交易状态面从保留 RAW 复原

- 保留日线批次 42 个，日期 20260713~20260924，
  其中 40 个批次 `paused/high_limit/low_limit` 完整无空值
- 重建候选 `STOCK_TRADEABILITY_PIT_R1`：198109 行 / 38 日 /
  2026-08-04~2026-09-24，去重 10440 行
- 与封装面重叠核对：41656 个 (date,code) 键，
  paused 差异 35、high_limit 差异 35、
  low_limit 差异 35
- 差异全部是「封装面为空、RAW 有价值」的停牌键（35 例），以及 2026-09-03 上 6 例 `paused` 取值冲突；
  两组都登记为待裁决，未回写封装面
- `is_st` 不在 RAW 日线 schema 内：保持空值 + UNKNOWN，**不推断**

### 2.2 缺输入不再静默

- provider 新增严格门：`high_limit/low_limit/paused` 出现空值即
  `REQUIRED_INPUT_MISSING`，请求不得报成正常完成
- 引擎侧新增「标记价饥饿」计数器：任何空/全 NaN 价格返回都记账（这正是上一版持仓估值会冻住的静默失败路径）
- 回测结束后回读日志统计 `[昨日涨停名单]` 中止、`limit_up_flag_missing`、`ambiguous_na` 次数，
  任一非零即把状态从 `COMPLETED` 降为 `BLOCKED_INPUT_INCOMPLETE`

### 2.3 本轮回测

- 状态 **COMPLETED**；窗口 2026-09-03~2026-09-24（16 个交易日），
  **REQUESTED_SCOPE_CLEAN**
- 输入阻断项：无
- 成交笔数：2（0 笔即证明策略逻辑没有真正执行，见 2.5）
- 标记价饥饿查询次数：0
- 策略输入告警计数：{"yesterday_limit_up_step_aborted": 0, "limit_up_flag_missing": 0, "ambiguous_na": 0, "lines": 902}
- 日志残留告警计数（如实保留）：{"event_cash_patrol_float_none": 152, "light_probe_path_not_string": 34, "price_fetch_failed": 0, "yesterday_limit_up_aborted": 0, "limit_up_flag_missing": 0, "ambiguous_na_boolean": 0}
- 交易状态绑定（**最后一次查询窗口**的口径，非全程合计）：{"sealed_rows": 0, "sealed_dates": 0, "candidate_extension_rows": 5222, "candidate_extension_dates": 1, "sealed_authoritative": true, "override_scope": "sealed values win; the candidate only supplies cells the sealed plane leaves null and keys it does not carry at all", "reconciled_rows": 5222}
- 指标（引擎自报，仅诊断参考）：{"策略收益": "-4.66%", "策略年化收益": "-52.57%", "最大回撤": "-5.47%", "夏普比率": "-8.53", "日胜率": "18.75%", "交易胜率": "0.00%", "交易天数": "16", "初始资金": "1,000,000.00", "最终资金": "953,384.16"}

### 2.4 输入面修复（上一版 8 条 `REQUIRED_INPUT_MISSING` 的收口）

上一版回测被降级，是因为 8 次 `high_limit` 查询返回空：2026-09-03 的 3 个键、2026-09-07 的 5 个键。
本轮不是解释掉它，而是分因修复：

| 日期 | 键 | 成因 | 处理 |
|---|---|---|---|
| 2026-09-03 | 002731.XSHE / 002870.XSHE / 600929.XSHG | 封装面 `paused=0` 但限价为空；候选扩展因「该日已被封装面服务」而被整日排除 | 改为按 (date,code) **逐格**对账：封装面有值就用封装面，封装面为空才取候选面同字段值 |
| 2026-09-07 | 603037~603041.XSHG | 候选分区正在被重写（非原子 `to_parquet`），引擎读到的瞬间为空 | 候选发布改原子（临时文件 + `os.replace`），读方永不可能看到半截分区 |

全窗口复检（`evidence/INPUT_PLANE_REPAIR.json`）：16 个交易日，
逐日比对「价格面服务的证券数」与「交易状态面可用限价的键数」，
结论 **GATE_SWEEP_PASS**；空限价行 0、空 `paused` 行 0、缺失键 0。

口径必须说清：这是**同字段、同日、同证券的本地 RAW 实测值替换**，
不是由价格反推限价，也没有推断 ST（`is_st` 全窗口仍为空）；`limit_prices_inferred=0`、`st_flags_inferred=0`、采集调用 0。
封装面与 RAW 在 2026-09-03 有 6 个 `paused` 取值冲突，按「封装面优先」保留并在绑定里计数，不静默改写。

### 2.5 「COMPLETED + 0 交易」不是干净结果（本轮自己抓出来的）

修好限价空值后第一次重跑：状态 `COMPLETED`、输入阻断 0，但全程 **0 笔交易**、资金不动。
这不接受。抓真实栈后定位到**本轮自己引入的缺陷**：

- 位置：`candidate/local_plane/provider.py` → `merged["paused"].astype("boolean")`
- 原因：封装交易状态面在不同快照 tip 里 `paused` 一半是 `0.0/1.0`（float）、一半是 `bool`，
  拼接后是 `object` 混合类型，pandas 拒绝转 boolean（`Need to pass bool-like values`）
- 后果链：引擎 `get_price` 捕获异常 → 记一行 `获取价格数据失败` → **返回空 DataFrame** →
  09:20 选股价格表为空（漏斗 `l3=0`）→ 无候选 → 无交易 → 引擎仍报 `COMPLETED`
- 修复：显式 `0/1/True/False/NA` 归一化（`_as_nullable_bool`），在交易状态面对账后统一做一次、
  `get_price` 再做一次；出现非二值（如 0.77）立即抛错，**不允许降级成空行情**

修复后的证据（`evidence/PRICE_FETCH_FAILURE.json`）：同一 3 日探针由 5 次价格取数失败 → **0 次**，
且策略真实成交（期末资金≠期初）。随后整窗口重跑结果：

- 状态 **`COMPLETED`**，输入阻断 0、`required_input_failures` 0、标记价饥饿 0
- 日志 `获取价格数据失败` = 0；
  `[昨日涨停名单]` 中止 = 0；
  `ambiguous_na` = 0
- 成交笔数 = 2（策略逻辑真的执行了）
- 绩效口径：**不作为可准入业绩**（B1 逐日因子血缘、B7 全库等价门未闭），只作为「输入与执行链正确」的证明

仍然如实保留的日志噪声：`事件资金巡查异常` 152 次、
`轻探针 激活确认异常 | path 必须是字符串` 34 次，
均为策略自身探针的 `float(None)`/路径类型问题，不影响选股与成交，未在本轮修改策略源码。

## 3. 交付三：连接式更新/清洗/发布管线

`CONNECTED_PIPELINE.json`（verdict **PASS**）：

| 阶段 | 实际动作 | 证据 |
|---|---|---|
| 本地重放传输 | 读保留 RAW 批次 + sidecar + 因子增量，携带请求日/载荷日/批次指纹 | provenance |
| 响应门 | 载荷日=请求日、sidecar 覆盖声明齐全且区间匹配、行数带、索引日期在序列化后存活 | response_gate |
| 清洗 + 防穿越 | 日期强转、重复键、OHLC 一致性、空价、非正价、未来/异日行 | cleaning_antileak |
| 因子刷新 | 合同要求 `code/factor`；物理 `fq` 列非合同要求，缺列不判违规 | factor_refresh |
| 编译 | 按 (date,code) 合并，重复键即停 | compiler |
| 断点 | 已提交日不再提交；同日重放为 no-op | checkpoint |
| 隔离发布 | 候选指针+注册表双写（两次 `os.replace`，**不声明为事务**），一致性回读 | publication |

控制结果：

- 4 个负控（短批、日期错位、覆盖未声明、索引日期不可解析）全部在合并前停下，
  且候选分区哈希不变：True
- 既有部分日被完整替换而非跳过：True
- 同输入重放幂等（分区哈希不变、无重复键、断点无重复条目）：True
- 上一轮两日重建比对（10,426 行 / 0 单元格差异）作为既有证据复用：REPRODUCES_R06_CANDIDATE

## 4. B1–B7

- **B1** OPEN — PRE-adjustment price chain certifiable over the test window；失败谓词：factor sidecar vs physical row count +83,503 with no per-date lineage; pre/post not implemented；本轮动作：engine ran with fq='pre' and a piecewise factor fill anchored at end_date; no new lineage invented；仍需输入：per-date factor lineage (or the whole-table factor revision)
- **B2** PARTIALLY_REPAIRED — universe and tradeability cover the test window；失败谓词：sealed tradeability stopped at 2026-09-03 while prices run to 2026-09-24；本轮动作：rebuilt paused/high_limit/low_limit for 2026-08-04..2026-09-24 from 40 retained RAW batches; agreement on sealed overlap 41656 keys with 35 field-level disagreements；仍需输入：historical universe is still not covered (measured window ends 2026-07-20); is_st is not in the RAW daily schema and was not inferred
- **B3** OPEN — fund products materialised or explicitly excluded by contract；失败谓词：FUND_DAILY_PIT_R1 / FUND_FACTOR_DAILY_R1 / FUND_LIKE_ASSET_VIEW_R1 hold 0 parquet；本轮动作：no materialisation; source result kept as measured absence, no synthetic rows；仍需输入：materialisation run or a contract that permits exclusion
- **B4** OPEN — mounted CURRENT serves every session in the window；失败谓词：2026-08-31 and 2026-09-01 are still not served by the mounted CURRENT；本轮动作：the two days were rebuilt into a candidate partition and republished as candidate only；仍需输入：an authorised CURRENT switch (CURRENT_SWITCH_ALLOWED=false here)
- **B5** REPAIRED — formal engine run；失败谓词：the earlier run aborted the 09:05 step and skipped the limit check because limit/status inputs were missing; run status=COMPLETED；本轮动作：tradeability restored from retained RAW with per-cell reconciliation (sealed value wins, candidate only fills null cells), atomic candidate publish, strict input gate, non-binary paused normalisation; run status=COMPLETED, input blockers=0, mark-price starved lookups=0, executed trades=2；仍需输入：none for the requested window (performance stays non-admission-grade while B1/B7 are open)
- **B6** PARTIALLY_REPAIRED — writer / checkpoint / resume / non-regression；失败谓词：no production cursor; resume evidence did not exist for any product；本轮动作：local candidate checkpoint + resume implemented and exercised for STOCK_DAILY_PIT_R1 (verdict PASS, idempotent True); 53 other bindings reported blocked；仍需输入：a production writer that emits a cursor, or an authorised start date with overlap
- **B7** PARTIALLY_REPAIRED — equivalence / coverage / non-regression of the candidate vs its parent；失败谓词：the non-regression gate that would distinguish a regression from a missing product is unimplemented；本轮动作：compiler refuses duplicate keys; partial-day replacement proven; idempotent replay proven; no date lost vs the parent partition (rows only added for the two recovery days)；仍需输入：whole-CACHE RAW<->CACHE equivalence gate and a publish-time regression classifier

## 5. 用户五项要求

- **R1_data_ecology_dictionary_rules_lessons** → PARTIAL；实测：54 datasets, 75 measured layers, 12 contractually not applicable, 9 product dirs unresolved；未证：per-dataset increment cursor is still not emitted by any writer (NOT_BOUND)
- **R2_engine_data_contract_and_actual_runtime** → PARTIAL；实测：engine reached COMPLETED over 2026-09-03..2026-09-24 on the real local plane with zero input blockers and 2 executed trades；未证：performance admission grade: B1 per-date factor lineage and B7 whole-CACHE equivalence gate are still open
- **R3_strategy_artifact_identification** → PASS；实测：E:\BLACKBOX\参考资料\聚宽策略写法\聚宽范本_日频模拟盘_V4_R21_HOTSTART_R5.py sha256 8d9334dd6ed2053b；未证：nothing at identity level
- **R4_download_incremental_rules_and_access** → BLOCKED；实测：no acquisition was attempted or authorised in this round；未证：the increment cannot start without an authorised start date / supplier lag
- **R5_desktop_actual_running_latest_update** → BLOCKED；实测：local runtime, provider, engine and cleaning path all execute offline；未证：the latest incremental update has not been run (acquisition not authorised)

## 6. 改动代码

- `candidate/local_plane/provider.py` (53563 bytes, sha256 630725cd6c0558f9) — candidate extension of the tradeability plane + strict required-input gate
- `candidate/run_engine_backtest.py` (21811 bytes, sha256 169b15a13773d356) — strict input mode, mark-price starvation counter, log-based strategy input counters
- `tools/build_dataset_state.py` (30694 bytes, sha256 49f9c03f0dd8c461) — time-axis roles, per-product subdir resolution, FACTOR_VALUE/UNDETERMINED_SCOPE reclassification
- `tools/build_tradeability_candidate.py` (9873 bytes, sha256 6412225c67794aee) — new: rebuild paused/high_limit/low_limit for the engine window from retained RAW
- `tools/run_connected_pipeline.py` (27263 bytes, sha256 f17a984cae7b73a3) — new: gate -> cleaning -> factor -> compiler -> checkpoint -> isolated publication
- `tools/build_checkpoint_bindings.py` (6081 bytes, sha256 9f1f72b937d35dd1) — new: validated vs blocked candidate checkpoint bindings
- `tools/raw_status_field_inventory.py` (3618 bytes, sha256 afa0533ae17cdb5e) — new: retained RAW status/limit field inventory
- `tools/record_commands.py` (6294 bytes, sha256 422cb82a3e871dce) — new: exact command/exit-code/log recorder
- `tools/build_input_plane_repair_evidence.py` (7199 bytes, sha256 d1993c8093cedcbc) — new: per-session sweep proving the input plane has no null limit/paused key over the window
- `tools/explain_price_fetch_failure.py` (5549 bytes, sha256 4372040b53006f0e) — new: captures the real traceback behind 获取价格数据失败 (owner: provider paused dtype cast)
- `tools/explain_required_input_gap.py` (5677 bytes, sha256 48106aa2884ecc91) — new: splits the 8 REQUIRED_INPUT_MISSING entries by cause instead of narrating them
- `tools/build_delivery_report_v2.py` (38071 bytes, sha256 c1f9759c58048061) — consolidated package builder; statuses are derived from run artefacts, not asserted

完整当前源码随包提供于 `changed_code/`。本轮未在上一版包里保留字节级基线，因此给出的是
完整改动源码 + 逐处插入说明，而不是伪造的 diff。

## 7. 命令、退出码、原始日志

| 步骤 | 退出码 | 日志 |
|---|---|---|
| must_read_preflight | 0 | `must_read_preflight.log` |
| environment_verify | 0 | `environment_verify.log` |
| raw_status_field_inventory | 0 | `raw_status_field_inventory.log` |
| build_tradeability_candidate | 0 | `build_tradeability_candidate.log` |
| build_dataset_state | 0 | `build_dataset_state.log` |
| run_connected_pipeline | 0 | `run_connected_pipeline.log` |
| build_checkpoint_bindings | 0 | `build_checkpoint_bindings.log` |
| v4_backtest_requested_scope | 0 | `run artefact` |
| input_plane_sweep | 0 | `run artefact` |

回测为长任务，退出码由其自身 `run_result.json` 状态换算（`COMPLETED`）；
完整原始 stdout/日志见 `evidence/command_logs/` 与 `engine_runs/` 对应目录。

## 8. 运行指南与回滚

见 `RUN_GUIDE.md`。回滚：删除 `candidate/data/R11_TRADEABILITY`、`candidate/data/R12_PIPELINE`、
`pipeline_runs/` 与 `engine_runs/v4_r21_20260903_20260924_R11_TRADEABILITY_RECON` 即可；
封装发布、CURRENT 指针、原始只读区均未被写入。

## 9. 仍未解决（需要输入，不是需要猜）

- 历史股票池（universe）覆盖止于 2026-07-20
- `is_st` 无本地权威来源，未推断
- 挂载 CURRENT 仍不服务 2026-08-31 / 2026-09-01（只做了候选）
- 逐日因子血缘（B1）与全库 RAW↔CACHE 等价门（B7）未实现
- 基金产品 B3 仍为 0 行
- 采集未授权，因此「最新一次增量更新已跑完」不能宣称

`FOUNDATION_ACCEPTANCE=false` · `FORMAL_ENGINE_ADMISSION=false` ·
`NEW_DATA_ACQUISITION_AUTHORIZED=false` · `CURRENT_SWITCH_ALLOWED=false` · `ORDER_ALLOWED=false`
