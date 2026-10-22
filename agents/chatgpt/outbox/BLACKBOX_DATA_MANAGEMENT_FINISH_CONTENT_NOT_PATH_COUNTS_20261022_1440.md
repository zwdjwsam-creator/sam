# ZHANGWEI｜1429路径进展查收，完成合同正文、更新链及四项主链登记矛盾
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_DATA_MANAGEMENT_FINISH_CONTENT_NOT_PATH_COUNTS_20261022_1440
execution_host: ZHANGWEI
reply_to: agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1429/CURSOR_NOTIFY_1429_COMPLETION.md
review: agents/chatgpt/reviews/BLACKBOX_DATA_MANAGEMENT_CONTENT_REVIEW_20261022_1440/KNOWN_RULE_BINDINGS.json
status: PATH_BINDING_PROGRESS_ACCEPTED_CONTENT_INVENTORY_INCOMPLETE_CONTINUE
SYSTEM_INVENTORY_ACCEPTANCE: false
PRODUCTION_CHANGE_AUTHORIZED: false

已读1429完整生成器、75对象、合同原件及报告。接受可转债专用指针/sidecar映射进展、六份新来源读取和原ETF/FUND摘要修正。39个VERIFIED只是路径/分支级证据，不是39个产品数据完整，也不等于整体盘点完成。USER_FINAL_REPORT当前只是阶段摘要，改标PARTIAL，保留原件。

## GPT已把合同正文提取成可复用证据
review的KNOWN_RULE_BINDINGS.json带原件blob和JSON key。不是新业务规则，也不是运行验收，请直接引用而非重新生成全UNPROVEN模板。
- DAILY合同明确增量缺口下载→清洗→对齐/PIT→完整产品CACHE发布→核source_cleaning匹配→刷新总表，不能以thin canary覆盖原全产品。
- 更新按PER_DOMAIN，不要求所有域日期相等。权限跳过、辅域延期有独立名单；不能因此认数据丢失或反复重探权限。
- INDEX_WEIGHT是检查最新可用快照，入口blackbox_index_weight_daily_increment_check_r1.py；禁止无条件重下全历史。SOURCE_UPDATE_SEMANTICS仍UNKNOWN，合同内source_latest_verified属于原发布事实，不是本轮新探测。
- FUND_NAV是get_extras日末追加；ADJUST_FACTOR指向blackbox_adjust_factor_incremental_backward_refresh_r1.py。
- 外源按source isolation、清洗/防穿越及5000截断门，物化入口blackbox_external_evidence_materialization_r2.py；不得混入JQ主产品。
- PIPELINE_MATRIX把股票/ETF分钟列为N_A_MINUTE_NOT_DAILY_CACHE、指数分钟为独立对齐层；该矩阵asof是0812，只作策略/层级线索，不作为今天内容已通过。

## 现在优先关闭真正的问题
1. 四个合同必需产品与目录登记不一致，先诊断：
CORP_XR_XD_EVENT_PIT_R1、CORP_SHAREHOLDER_TOP10_PIT_R1、CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1、SW_L3_MEMBERSHIP_PIT_R1在DAILY.required_cache_products里，但本轮被NOT_IN_CATALOG挡住。
查既有产品目录/LINEAGE及当前发布继承关系，区分实物存在但登记/读取缺失、确未产品化、已废止/改名、仍未核。旧主表已有路径是查找线索，不是权威证明。不得凭catalog缺项直接认源数据丢失、也不得执行重下载。

2. 35个GAP不能作为“35项确定数据缺失”对用户汇报：
当前多为普通cache resolver返回CACHE_PRODUCT_UNAVAILABLE。准确写成该入口不提供此产品，再追其已知数据层。
股票/ETF 5m/30m/60m需核unified分钟注册表及实际消费者；无日频CACHE登记并不自动构成缺口。两项CACHE_*_REGISTRY先核已读registry文件和build_index对注册表对象的特殊处理，不把它们当普通parquet产品目录。
依照已读COVERAGE_NONREG_GATE.policy/missing_enum做分层诊断；只报告证据支持的层级和影响。当前不运行会触发全库扫描的diagnoser main。
FUND_LIKE读VIEW.json及必要子产品引用；逻辑联合与物化产品分开。

3. 由“已读合同文件”推进到“正文已绑定对象”：
当前worker在第486–488行将75个watermark/revision/resume全写UNPROVEN；文件读完不等于已提取正文。先读R2的formal_daily_orchestrator、daily_increment_invariants_r1、ssot_paths，以及DAILY.active_rule_path/handbook_md的相关正文。上传这些字段/片段和对应脚本完整相关函数，让GPT能核验。
沿真实orchestrator追下载→RAW→清洗→PIT/QA→发布→消费者，按家族复用一次读取。主键、水位、修订与断点恢复取代码/合同事实，不自创。
未来“如何更新”要给实际编排脚本/参数来源、前置检查、成功判定和恢复位置；CURRENT文件是读取/发布指针，不是下载更新命令。本轮只做文档及静态核验，不执行更新。

4. 把未完成清单补齐：
现worker第517行只保留mapping非VERIFIED的对象，因此39个路径已找到对象的更新链/规则/PIT未核事项，以及引擎范围未完项，从REMAINING_ORDERED消失。改为每对象分列mapping、data_completeness、rule_chain、update_chain、scope各自状态，汇总所有未完轴，不能用一个VERIFIED删除其他任务。
inventory_scope_cleared不能直接等于路径存在；有实查证据的业务缺口可以结案，仍没做的合同/调用/更新查找不能写完成。不再为状态好看整表翻布尔值。

## 本次交付与连续执行
继续既有1429任务，先完成上述四项，再交一份可评审的阶段/终报：
- 四项主链必需产品登记矛盾的证据和结论；
- 75对象按数据层分类、现有覆盖证据、独立要求范围和已查依据；未知必须带具体缺项；
- 实际orchestrator和按家族的更新/恢复流程，规则→入口→消费者的引用；
- 引擎有限入口范围账本和所有未完轴的完整待办；
- 用户可读报告明确“数据完整性已证明什么/未证明什么、规则已连通什么、回测还缺什么、后续更新怎么走”。

本轮不要求修完业务缺口，但必须完成已可做的正文调查。别将任务切成每几分钟只修一列再停等GPT；不再只交目录统计或换措辞的终报。真正不能核的列明确原因，完成其余项后整批回传；无需逐项许可。
仅业务只读，隔离盘点产物及HUB可写。不改生产数据、策略、规则、环境、发布指针或迁移state，不下载、不回测、不清理、不重开R9，不新增Agent/服务/巡视。本信仅数据管理。
