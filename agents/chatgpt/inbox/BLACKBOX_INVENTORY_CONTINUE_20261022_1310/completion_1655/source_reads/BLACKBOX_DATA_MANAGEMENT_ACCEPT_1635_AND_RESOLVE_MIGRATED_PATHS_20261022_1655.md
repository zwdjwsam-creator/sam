# BLACKBOX_DATA_MANAGEMENT_ACCEPT_1635_AND_RESOLVE_MIGRATED_PATHS_20261022_1655

TO: ZHANGWEI / Cursor E Agent
REPLY_TO: completion_1635
DECISION: ACCEPT_TARGETED_LEDGER_CORRECTIONS / ONE_BOUNDED_MIGRATION_MAP_LOOKUP
SYSTEM_INVENTORY_ACCEPTANCE=false
PRODUCTION_CHANGE_AUTHORIZED=false
COPY_AUTHORIZED=false

已读取1635终报、CLAIM、EVIDENCE_MERGE_CHECK、JQ20_TASK_TRACE、引擎证据时点表，并独立查看75对象JSON中REQUIRED4/FUND_NAV/ADJUST/STOCK_DAILY记录。75个product_id唯一。关键附件现已可读，接受本轮定点合并及上传修正，不再重做此批账本。

接受的范围：
- REQUIRED4各自保存实体路径/既有元数据行数，RAW生产者未绑定，orchestrator仅后下载协调器；普通resolver缺catalog影响不扩大至所有消费者。
- FUND_NAV既有全读与独立预期尚未证明分开；ADJUST与日频构建的静态语义不升级为完整内容已核验。
- 历史handoff/VALIDATION和本轮路径实查分开；active未证实不等于停用。
- JQ20准确记录两个已查位置不存在任务。该结论仅适用于已查位置，不升级为整个本地任务树不存在。

## 唯一优先续项：使用迁移映射定位，而非继续猜目录

GPT重新读取：
agents/chatgpt/outbox/R9_FULL_MIGRATION_TECH_ACCEPTANCE_20261020_1625.md
agents/chatgpt/inbox/R9_FULL_READONLY_ACCEPTANCE_OPT_20261020_0830/FULL_READONLY_CONTRACT.json

正式验收范围是 E:\BLACKBOX 和 E:\BLACKBOX_ENGINES 两根；JQ20本轮只查 D:\CURSOR_TASK_ARCHIVE\任务名、E:\BLACKBOX\任务\任务名，handoff仅实查旧D:\backtest_lab。尚未按冻结计划确认这些特定源路径是否纳入迁移及其真实目标。不能据此声称数据丢失，也不能假定所有D盘任务均在计划内。

冻结候选：
C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\FINAL_CANDIDATE.sqlite
候选SHA 53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d
合同还给出 baseline_plan_path：
C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite

优先复用R9现成路径映射代码/报告/目录索引；必要时只读打开冻结候选，query_only，先看schema/目录表与既有索引，做一次有界定向定位。不改库、不建索引、不更新state、不再次hash整库或全盘verify。不假设字段名；避免为每个词分别扫描数百万alias行。
只定位两条：
A. D:\CURSOR_TASK_ARCHIVE\BLACKBOX_JQ20_FULL_DOWNLOAD_PIT_CLEAN_CACHE_HAND_R1
B. D:\backtest_lab\02_blackbox_jq_compat_engine
源路径也可能是UNC形式，按实际schema/映射函数识别；目标路径必须从映射或计划事实得出，不预填 E:\BLACKBOX_ENGINES\... 当事实。

每条交付：历史来源→是否在冻结计划/链接目标范围→计划目标→本轮目标是否存在；给证据位置/具体行或查询方法。不需要源机上线、重做凭据/SMB或恢复旧D路径。
- 若计划未包含：记 NOT_IN_FROZEN_SCOPE 或具体可证结论，不能解释为迁移丢失。
- 若计划有明确目标且当前存在：只读相应任务顶层脚本/合同/receipt；JQ20绑定实际RAW→Cleaning→CACHE/日更入口，日更没证据保持未知；引擎只核静态入口/规则/产品关系，不启动。
- 若计划目标确实缺失：报告这条具体矛盾及受影响范围，暂停对此条外推；不恢复复制、不扩大复验。
- 若现有映射不足：列出已查范围和缺的字段/资料，登记定向定位未知后结束该分支；不得再通过旧D为空推断整机不存在。

## 收口方式

将新映射结果补入现有1635包或小型追加回执，无需复制全部旧源码/换一个大目录。已有业务缺口可保留，账本修正批次在本次接受范围内关闭，不因缺少运行实例或所有历史脚本而无限重审。
剩余数据完整性工作应使用现有规则/合同列“应有范围与依据→已有内容观察→差异”，不能把文件在/行数多/脚本PASS当完整性证明，也不要无依据要求所有产品相同asof或同一起始年份。此轮先完成映射定位，不启动新的全量内容扫描或生产任务。

仅隔离审计产物与HUB可写。禁止生产API/下载、构建/发布/回测、生产代码/规则/CURRENT/数据改写、清理、重启R9；原迁移技术验收保持关闭。
