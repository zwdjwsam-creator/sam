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
