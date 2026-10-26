> GPT handoff review (2026-10-26 18:04 CN), same SAM_LED_DESKTOP_RECTIFICATION_20261025 dispatch: read agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R10_END_TO_END_20261025/SAM_RELEASE_INDEX_HANDOFF_REVIEW_20261026_1804.md. New SAM release/index report and manual received; independent acceptance is pending exact deployed compiler/runner bodies and retained run/closure/key/commit evidence specified there. Complete the existing handoff only; do not restart, duplicate or stop desktop verification, rescan, download, change CURRENT or issue orders. Preserve all failed outcomes and the valid earlier stock baseline. Upload and read back every file; final Cursor message exactly END.

> **[GPT 当前执行 2026-10-26：SAM 修复 release 绑定与指数读取校验]**
> 用户已授权，沿用 SAM_LED_DESKTOP_RECTIFICATION_20261025。完整执行令最高优先级已更新：
> https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/outbox/BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025.md
> 台机R12长路径漏读修复及572619c9正确提交保留，不再等待该轮回报。SAM现在直接修改台机E盘实际代码：本次compiler返回的release身份直接传到校验/identity/commit，禁止按目录排序或mtime猜最新；指数加入真实读取闭包和输出键校验；股票/ETF已有数量门核实并补齐集合比较。无新扫描/迁移/下载，不重新交接整条链。
> SAM落地补丁、精确命令和手册后直接通知ZHANGWEI；台机只在交付后本机顺序复验受影响入口、归档干扰/失败阻断、文件与键集合、固定股票基线及幂等。双方不并发改同一文件，不让用户传话；历史正确commit无需人为变更或清账。
> V4本次不触碰，仍BLOCKED_INPUT_INCOMPLETE；供应商分页仍UNKNOWN；生产CURRENT切换、生产发布、新下载、下单均未授权。交付后集中回GPT审核，不能预先宣布完成。
>
> 以下旧记录保留，仅供历史参考。

---

> **[DESKTOP R12 CLOSURE REVERIFY 20261025] RESULT = PASS（8/8 判据 + 15/15 独立核验）— 但发现 1 个中等问题**
> 台机 ZHANGWEI 本机跑完 `tools\run_connected_pipeline.py --r15-rid R15_REPLAY_20260924_R3`，全程无 `allow_skip`。
> 证据：`agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/sam_led_rectification/r12_desktop_closure_reverify/`（15 文件，逐字节回读一致；共享盘 `\\192.168.100.2\BLACKBOX\运行\外部大脑信箱\staging\r12_desktop_closure_reverify`）
> 报告：[DESKTOP_CLOSURE_RERUN_REPORT.md](https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/sam_led_rectification/r12_desktop_closure_reverify/DESKTOP_CLOSURE_RERUN_REPORT.md)
> 判据实测：R15 **234/12**；`READ_CLOSURE` **234=234=234**（ETF 37/37/37），failed=0；错误标记 0 条；三产品 `year=2026` 各 **959,896**；七月六天 **5209/5210/5208/5208/5208/5207**；`production_digest_changed={}` 且我跑前跑后 9 文件 digest 全等；负控 7,880B 含 `"exit_code": 1`；A=COMMITTED → B=`IDEMPOTENT_NOOP` + verify `CONSISTENT`。
> **新问题（MEDIUM）**：`newest_release()` = `sorted(by name)[-1]`。我把归档命名为 `_prev_*` 留在 `releases/` 内，`_`(0x5F) 排在 `B`(0x42) 之后，于是归档树被当成最新 release，`build_identity` 在**修前树**上算 identity → `REBOUND_SAME_CONTENT_NEW_ROOT` → 假 `IDEMPOTENT_NOOP`（`commit_id=2f755779`、rows=17,009,531，而实编译 17,040,667）。我把归档移出 `releases/` 后重跑才得到真 commit `572619c9`。**任何排序在 `BLACKBOX_*` 之后的目录名（`_prev_`/`_bad_`/`zz_`/小写）都能顶替最新 release** —— 建议加白名单前缀并断言 `identity.products.rows` 不低于已知下界。
> 指数闭包缺口**核实为真**：`READ_CLOSURE` 只有 STOCK/ETF 两键，日志另有一行 `read stock files=234 etf=37 index=1501` 但无三元组、无 `CLOSURE_OK`。
> 补你 §7 的 UNVERIFIED：台机 `LongPathsEnabled = 0`（`HKLM\SYSTEM\CurrentControlSet\Control\FileSystem`，OS 10.0.26200）。
> 反讽一条：我自己的取证脚本用 `pathlib.read_bytes()` 读那 12 个 `r2_repair` 也直接 `FileNotFoundError` —— 不走 `_lp` 的新代码都会复现，建议收一个公共 `lp/lstat` 工具。
> `V4 BLOCKED_INPUT_INCOMPLETE` 未变，本轮未触碰；`PRODUCTION_CURRENT_WRITE=NONE`、无新下载、未删任何文件、`ORDER_ALLOWED=false`。
> 以下旧记录保留，仅供历史参考。

---

> **[GPT 当前执行：修复编译器长路径漏读，沿用 SAM_LED_DESKTOP_RECTIFICATION_20261025]**
> R11 BLOCKED 已审阅，优先于下方旧PASS/停止记录。完整执行令新增顶部“当前最高优先级：修复已定位的编译器长路径漏读，台机一次复验”：
> https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/outbox/BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025.md
> **SAM唯一主导直接改台机实际导入的原compiler**：find_parquets用长路径安全枚举/stat；read_price_frame实际读取也用扩展路径，必需输入禁止异常后continue。增加物化期望文件集合=枚举集合=成功读取集合及去重后键/行数硬门，失败必须在commit前顶层非零COMPILER_READ_INCOMPLETE。已知928760候选不得复用冒充通过。
> **ZHANGWEI等SAM交付后本机复验**：234/12，三产品959896，六日代码5209/5210/5208/5208/5208/5207；随后同输入二次IDEMPOTENT_NOOP及CONSISTENT。加长路径与漏读阻断的小样本验证。不重扫、不重新交接运行链、不重建数据、不依赖缩短根或注册表开关；备份说明/walk吞错随同修正。
> SAM直接落地一次性复跑入口与文档并通知台机，双方在同任务连续处理，不让用户转述。新增下载/生产CURRENT/下单仍关闭；本条不触碰V4，也不预先宣布已修好。
>
> 以下旧记录保留，仅供历史参考。

---

> **[DESKTOP RERUN AFTER FIX R11 20261025] RESULT = BLOCKED（A 过 / B 不过）**
> 台机 ZHANGWEI 本机跑 `tools\run_connected_pipeline.py --r15-rid R15_REPLAY_20260924_R3`：exit 0、12/12 verdicts true，
> **但 `rows_2026 = 928,760 ≠ 959,896`（差 31,136），6 个交易日仍是每天 19 个代码。**
> **A 已修好**：R15 `stock_ohlcv_daily` = 234 文件 / 12 个 r2_repair ✅
> **B 未修好**：编译器 `find_parquets` 仍用 `p.is_file()`，台机 `LongPathsEnabled=0`、
> R3 全路径 271 字符 → `find_parquets()` 只返回 **222**，静默丢同一批 12 个文件。
> 台机实测：`is_file` 可见 222 / `\?\` 前缀 stat 234 全通过 / 被丢文件可正常读 2,890 行。
> 需 SAM 改 `find_parquets`（`_lp` + 显式 stat）+ 加"编译读到文件数/行数"硬门；台机不擅改业务代码。
> 另：`run_r15_cleaning_replay.py.bak_sam_led_r11` 与当前文件字节相同（回滚链断）；`RERUN_AFTER_FIX.md` 原先未推 HUB，本次已补。
> HUB 目录: https://github.com/zwdjwsam-creator/sam/tree/main/agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/sam_led_rectification
> 指针块，以下正文原样保留。

---

> **[DESKTOP REVERIFY 20261025] RESULT = PASS**
> 台机 ZHANGWEI 已用本机进程跑完 `RUN_CHAIN_R1.py`（2026-10-25T19:17:59 → 19:20:24，runner exit 0），
> 证据 `LOCAL_RUN_EVIDENCE.json` 的 `identity.hostname=ZHANGWEI`；另附独立核验 `DESKTOP_INDEPENDENT_VERIFY.json` 47/47。
> 结论：`sam_led_rectification` = **DESKTOP_REVERIFY_PASS**（12/12 chain verdicts、8/8 runner verdicts、`PRODUCTION_CURRENT_WRITE=NONE`）。
> 未通过项另列：V4 仍 `BLOCKED_INPUT_INCOMPLETE`（diagnostic_only），正式回测**未通过**。
> HUB 目录: https://github.com/zwdjwsam-creator/sam/tree/main/agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/sam_led_rectification
> 本块仅为交付指针；以下正文原样保留，未作删改。

---

# SAM 当前待办｜直接整顿台式机 BLACKBOX，完成后交手册并由台机复验

task_id: BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025
dispatch_id: SAM_LED_DESKTOP_RECTIFICATION_20261025
status: READY_SAM_DIRECT_RECTIFICATION
lead_agent: SAM 原 BLACKBOX Cursor
target_host: ZHANGWEI
target_root: E:\BLACKBOX
canonical_instruction: agents/chatgpt/outbox/BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025.md

用户已确认笔记本可读写修改台式机 E 盘，不再确认接入。请读完整执行令最新顶部并直接施工：SAM 唯一主导修改；台机必要时承担本机执行，最终独立复验。旧只读裁决、源机交接收口和R10自动返工停止不覆盖此次明确新授权。不要只回审计意见或等待用户转述。

直接复用迁移前约895万路径扫描：
agents/chatgpt/inbox/R9_NOTEBOOK_LOCAL_SOURCE_RECONCILE_20261014/SAM_REPORT.md 与 SOURCE_RECONCILE_SUMMARY.json；
SAM本地 C:\LAN_SHARE_REPORT\R9_LOCAL_SOURCE_RECONCILE_20261014\db\CURRENT_ENUM.sqlite、DELTA.sqlite。
234条差异沿用 R9_NOTEBOOK_RESOLVE_234_DELTA_AND_HANDOFF_20261015 已有解析；不重扫、不重传大库/全部源码。

交付台式机：
E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\sam_led_rectification\
至少含已落地修复、RECTIFICATION_REPORT.md、FOUNDATION_RUNTIME_MAP.md、OPERATION_MANUAL.md、本机运行证据和 HANDOFF_TO_DESKTOP.md。
HUB回传同名子目录：agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/sam_led_rectification/

完成后置 SAM_HANDOFF_READY_FOR_DESKTOP_REVERIFY，直接通知台机照手册独立复验；双方集中交GPT。普通代码修复与隔离既有批次清洗/编译/候选发布已授权。新增采集、生产CURRENT切换、下单仍关闭。台机结构整顿已完成成果保留，不按旧报告回滚，不改DG1身份语义凑一致。

---
以下为历史收件，优先级低于本节：


## 台机 E 盘只读共享已开通（2026-10-25T16:49:09+0800）

| 项 | 值 |
|---|---|
| UNC | `\\192.168.100.1\E_DRIVE` → `E:\` |
| 账号 | `ZHANGWEI\sam_ro`（普通用户，共享层 **Read**） |
| 凭据 | LAN 共享 `desktop_reply_Q1_Q9\secrets\sam_smb_readonly.TXT`（**不进 GitHub**） |
| 说明 | `agents/chatgpt/inbox/BLACKBOX_DESKTOP_STRUCTURE_REMAP_20261025_1405/desktop_reply_Q1_Q9/SMB_READONLY_ACCESS_FOR_SAM.md` |
| 防火墙 | Inbound TCP 445 仅 `192.168.100.0/24` |
| 实测 | `sam_ro` 读 `HAND.txt`=OK、写探针=DENIED |

---
# 台机副本整顿权 → SAM 端 Cursor（2026-10-25T16:32:21+0800）
task_id: BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1
execution_host: ZHANGWEI
status: RECTIFICATION_DELEGATED_TO_SAM_CURSOR | DESKTOP_READONLY_FREEZE
ORDER_ALLOWED=false / NEW_DATA_ACQUISITION_AUTHORIZED=false / COPY_AUTHORIZED=false

- 移交书：agents/chatgpt/inbox/BLACKBOX_DESKTOP_STRUCTURE_REMAP_20261025_1405/desktop_reply_Q1_Q9/HANDOFF_TO_SAM_CURSOR.md
- 台机快照：agents/chatgpt/inbox/BLACKBOX_DESKTOP_STRUCTURE_REMAP_20261025_1405/desktop_reply_Q1_Q9/output/DESKTOP_STATE_SNAPSHOT_FOR_SAM.json
- 冻结旗标：agents/chatgpt/inbox/BLACKBOX_DESKTOP_STRUCTURE_REMAP_20261025_1405/desktop_reply_Q1_Q9/output/BLACKBOX_DESKTOP_REPAIR_DELEGATION_CURRENT.json

台机已置写冻结（manifest/plane/CURRENT/业务代码/数据产物）。
请 SAM Cursor 就 D1(MODE 是否入 DG1) / D2(--date+status 是否修) / D3(记忆缺口口径) / D4(D: 归档根) 出裁决。
写入通道：\\\\192.168.100.1\\BLACKBOX_DEST -> E:\\BLACKBOX。

---

# 桌面机已按 SAM Q1–Q9 执行（2026-10-25T15:09:30+0800）
task_id: BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1
execution_host: ZHANGWEI
status: FIELDS_REVERTED | DG1=DIVERGENT_MODE_ONLY | VERDICT=PASS
COPY_AUTHORIZED=false / NEW_DATA_ACQUISITION_AUTHORIZED=false / ORDER_ALLOWED=false

- 回执：agents/chatgpt/inbox/BLACKBOX_DESKTOP_STRUCTURE_REMAP_20261025_1405/desktop_reply_Q1_Q9/REPLY_TO_SAM_Q1_Q9.md
- 终态：agents/chatgpt/inbox/BLACKBOX_DESKTOP_STRUCTURE_REMAP_20261025_1405/desktop_reply_Q1_Q9/REPORT_AFTER_SAM_Q1_Q9.md
- 复算：agents/chatgpt/inbox/BLACKBOX_DESKTOP_STRUCTURE_REMAP_20261025_1405/desktop_reply_Q1_Q9/output/AFTER_SAM_Q1_Q9_VERIFY.json

要点：删 `alignment_csv`、`DISCOVERY_ASOF` 保持 09-24、细粒度状态按产物派生 PASS；
DG1 只剩 3 个 `MODE` 差异（`MODE` 入身份哈希一事请 SAM 复核）。
另：本机 `--date ISO` 曾污染 CURRENT，已修复并留账（BAD_DATE_CLEANUP_LEDGER.json）。

---

# ZHANGWEI（台式机）｜结构审计与指针修复 —— 请笔记本复查后裁决

<!-- DESKTOP_STRUCTURE_AUDIT_REVIEW_REQUEST_20261025_1405 -->

task_id: `BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1`
execution_host: ZHANGWEI
delivered_at_cn: 2026-10-25T14:05+0800
status: **AWAITING_NOTEBOOK_REVIEW**（不是新轮次；请你只读复查，不要再交文件）

```
COPY_AUTHORIZED=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CLEANING_AUTHORIZED=false
ORDER_ALLOWED=false
CURRENT_POINTERS_WRITTEN = 5（Owner 已授权"全部提升"；已备份、可整目录回滚）
```

结论（待你否证）：**不是数据丢失，也不是整体无结构**。同根 `E:\BLACKBOX`、同相对路径；
90/90 源文件逐字节相同；36/36 固定路径可达。真实缺陷只有"数据在、指针/会话层错位" + 两处乱码骨架（已归并）。

已做：Manifest `20260831 → 20260924`；D/E `DISCOVERY_ASOF=2026-09-24`；`US_MARKET.FIXED_PATHS` 补 5 键；
国内卖方/新闻 CURRENT 指 09-24 实切片；乱码 `杩愯`(=`运行`) 心跳归位、`浠诲姟`(=`任务`) 空骨架删除。
提升后审计：PASS 12 / PARTIAL 1（配置 SHA，属预期）/ INFO 1。

**请你回答 9 个问题**（全部可从你本机磁盘直接核，无需采集）：
`Q1` 零改写硬编码是否成立 / `Q2` `US_MARKET.FIXED_PATHS` 应并存还是二选一 /
`Q3` `DISCOVERY_ASOF` 是市场日还是运行日（**最需你裁决**）/ `Q4` 三大行无市场日切片算不算缺口 /
`Q5` 研究记忆 17/17 天缺是否与你一致 + 正确回补入口 / `Q6` RAW 日历停 08-10 是否同样 /
`Q7` 两处 2B 空壳是否 `WONTFIX` / `Q8` `US_FINE_GRAINED=NOT_RUN` 的最小复现口径与授权 /
`Q9` **判定 `STABLE | STABLE_WITH_KNOWN_GAPS | NOT_STABLE`** + 缺口归属表 + 是否要求 `ROLLBACK`

回复格式（一行一条）：
```
Q1 PASS|DIFF <一句证据>
...
Q9 VERDICT=...  主链断点=<有/无>  ROLLBACK=<YES/NO>
```

包（23 文件，逐字节回读一致；`PACKAGE_MANIFEST.json` 含全部 SHA）：
`agents/chatgpt/inbox/BLACKBOX_DESKTOP_STRUCTURE_REMAP_20261025_1405/`
共享镜像：`\\192.168.100.2\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\desktop_structure_audit_20261025\`

主文档：[REQUEST_FOR_NOTEBOOK_REVIEW.md](https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/BLACKBOX_DESKTOP_STRUCTURE_REMAP_20261025_1405/REQUEST_FOR_NOTEBOOK_REVIEW.md)

---
（以下为既有内容）

# SAM｜整底座运行链路已补交（同一任务，非新一轮）

task_id: BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025
execution_host: SAM
delivered_at_cn: 2026-10-25
status: FOUNDATION_RUNTIME_MAP_DELIVERED
COPY_AUTHORIZED=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false

新增：`FOUNDATION_RUNTIME_MAP.md`（bytes=40784，sha256=c8ba25c16ae770d52596c394801da6c71149f1ce7dbfde9965f1b6172015f29a）
覆盖四段：启动/规则/字典预检 → 下载/续传/清洗/校验/缓存/发布 → 查询/研究/选股/策略/回测 → 触发/失败停止/恢复。
每条边标注 `[CODE]` 自动 / `[AG]` 人工串联 / `[JQ]` 聚宽云端 / `[NI]` 未实现。

本轮实测、与既有交接不重复的要点：
- R15 补数任务保留逐单元下载证据：`get_price`、`fq=None/RAW_NONE`、`skip_paused=true`、`panel=false`；19 单元 16 PASS + 3 LEGAL_EMPTY；配额 197,783,456→197,722,946；一例请求 2,895 只返回 2,894 只（短批次被显式记录）。
- 现行清洗 CURRENT 混引：`standard_root=R33`、`ledger_path/quarantine_root=R45`；迁移只拷一个目录会丢 ledger 与控制层。
- 现行 cache 链：R45 → `TIP_REBASE_ASOF_20260924_20260925_034907` → `FUND_NAV_PIT_ASOF_20260924_20260924_200439`；该 TIP_REBASE 目录内 `MANIFEST.cache_release_id` 仍写 20260923（目录名≠内部 id）。
- `DOMAIN_ASOF.json` 子域 asof 落后顶层（2026-09-03 / 08-31 vs 顶层 2026-09-24）；按域读，勿用顶层 asof 外推。
- 研究 registry 07/08/09/10/11/13 `script=null`；14 指向目录且 PARTIAL；`mode_close` 仅写 recap 模板。

https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/source_workflow_sam/FOUNDATION_RUNTIME_MAP.md

pending_not_run: R9_NOTEBOOK_REMOVE_TEMP_R9LP_RO_20261020_1625

---
（以下为既有内容）

# SAM｜R10 修订项：原流程交接已交付

task_id: BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025
execution_host: SAM
status: SOURCE_WORKFLOW_HANDOFF_DELIVERED
delivered_at_cn: 2026-10-25

90 代码原件 + 28 配置，逐文件 SHA256；15 条日增量记录（14 PASS / 1 PARTIAL）。
Lane A 不下载；cache_stock_daily_pit_r1_reader_r1 源机不存在；两个 coverage 模块源机即 2B 空壳。

共享：\\192.168.100.2\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\source_workflow_from_SAM\
HUB：agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/source_workflow_sam/

https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/source_workflow_sam/SOURCE_WORKFLOW_HANDOFF.md

pending_not_run: R9_NOTEBOOK_REMOVE_TEMP_R9LP_RO_20261020_1625

## 同一R10任务待补：整个底座运行链路
status: RUNTIME_MAP_SUPPLEMENT_REQUESTED
execution_host: SAM
原 SOURCE_WORKFLOW_HANDOFF_DELIVERED 成果保留；不是重交118个文件。
请读取 canonical task 最新“Owner clarification — 整个底座运行链路交接”一节，补 FOUNDATION_RUNTIME_MAP.md：启动/规则字典预检、采集清洗缓存、查询研究策略回测、输出消费、日增与恢复的真实入口/调用关系，区分代码、AG/人工、云端及未实现部分。引用既有原件与记录，只补实际缺少的必要文件。9月24日运行记录仅作样本；未保留记录明确写出，不全盘扫描、不重跑、不采集、不改CURRENT。
台式机继续，不等待此补充。
https://github.com/zwdjwsam-creator/sam/blob/main/agents/chatgpt/outbox/BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025.md

## Supplement uploaded (same task)

- HUB: `agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/source_workflow_sam/source_supplement/` (24 called-source files + SUPPLEMENT_INDEX.json + SOURCE_SUPPLEMENT_R2.zip)
- zip bytes=124113 sha256=d1f88bcecb80a65bba55e2c9b44f04fb3560734cccd56cd0cc7186969e660fd9
- Also mirrored to the OPS share dir under `source_workflow_from_SAM/source_supplement/`.
- Contents: R15 daily/minute/finance/aux download writers, R15 cleaning+antileak, R15 control/contract/acceptance,
  research module registry + OS state, sellside daily writer, lane-B materialization, morning selection validation,
  research memory, QMT dual-pool + Laotao route C, lane E/F collector, lane D news observer, module 04 ontology, 2 live json samples.
- Not included on purpose: the two 2B coverage stubs, market parquet, any credential contents.
