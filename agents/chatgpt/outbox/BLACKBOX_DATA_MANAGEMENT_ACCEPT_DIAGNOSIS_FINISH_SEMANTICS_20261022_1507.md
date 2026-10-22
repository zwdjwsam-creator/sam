# ZHANGWEI｜1447两项诊断接受，读完正文后交盘点终报
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_DATA_MANAGEMENT_ACCEPT_DIAGNOSIS_FINISH_SEMANTICS_20261022_1507
execution_host: ZHANGWEI
reply_to: agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1447/CURSOR_NOTIFY_1447_COMPLETION.md
status: REQUIRED4_DIAGNOSIS_AND_ORCHESTRATOR_SCOPE_ACCEPTED_CONTINUE_SEMANTIC_REVIEW
SYSTEM_INVENTORY_ACCEPTANCE: false
PRODUCTION_CHANGE_AUTHORIZED: false

## 接受并关闭两项只读调查，不再重复
1. REQUIRED4实体证据：四个产品在CURRENT根下有真实parquet、字段与行数证据，且catalog缺项，限定该resolver的读取登记缺口成立。
各主文件行数129287 / 2694787 / 2653539 / 12564290已收到。它们证明实体存在，不证明全日期×全标的完整；5000行日期样本不作全局边界。row_count_method已写polars_scan_len，报告按实际方法描述，不一律称footer。
本项诊断接受，不再为获得新指令重复采样、全读、hash或重下载；生产登记修复仍未实施。其他消费者可读性未证实也如实保留。

2. 完整orchestrator已审：文件自述post-download，main确为IW check→ETF minute check→TIP rebase→scope refresh；该入口不负责全RAW域下载。
GATE常量未在main直接调用，不能据此断言下游没门；需沿TIP正文核。INDEX_WEIGHT主入口return0且apply_download=false，只证明检查入口正常返回，不能替代业务决策。
接受此入口适用范围结论，不再寻找“它隐藏的全系统下载功能”。

## 当前还没做完的是正文分析，不能再以定位函数代替
1447的extractor仍loc_preview截取40/50行；adjust main停在receipt初段，publish_successor停在pointer构造，external main停在参数/上下文设置，FUND_NAV仍关键词命中。UPDATE_CALLCHAIN_FULL这个文件名不代表正文齐全。
请修隔离提取逻辑：用Python ast的lineno/end_lineno导出完整相关函数（连decorator/import和必要常量），或直接复制这些已定位的小模块。不要再固定取前N行。只读源码，不import/run业务main，不调用API。

连续完成以下已授权工作：

A. 发布/失败链：
- TIP rebase完整main及实际校验、调用publish gate、写CURRENT、失败处理相关函数；
- blackbox_daily_increment_publish_gate_r1.py相关正文；
- blackbox_daily_increment_common_r1.resolve_run_target_trade_date及实际target传递。
给候选目录→检查结果字段→准入条件→两个CURRENT发布/失败恢复的实际路径和顺序。若契约要求原子/两阶段，而实现未覆盖某一故障窗口，记录具体代码缺口，不修生产，也不为了证明而执行发布。
--no-publish仍会调用TIP候选构建，不能当成本任务的只读测试方式，不执行它。

B. 更新/恢复语义：
- adjust_task：load_cache_factor、fetch_factor、main、publish_successor完整正文，含写入和末尾返回；_base.guarded_run实际相关函数。明确date/code键、overlap/dirty历史回刷规则、去重及继承方式、候选失败如何处理/能否安全重跑。没名为state的文件不等于无恢复；也不能从关键词出现推断已有恢复。默认--update-date=2026-08-14是源码事实，记录调用者是否覆盖，不按默认值运行。
- FUND_NAV：configure_window、fetch_nav_batch的实际绑定、下载/consolidate、prior tip合并、clean/cache发布相关完整函数。明确(code,day)等实际键、窗口/水位、同键修订优先级、批次落盘后重跑如何复用/去重及中断残留处理。字段名必须来自正文，不从文件名猜。
- external：实际main phase分发、相关下载/分页以及phase_acceptance截断门正文，写明哪个结果字段阻断注册/发布，未实现则列缺口。保持与JQ隔离，不跑物化。
- INDEX_WEIGHT：daily_check完整相关函数和实际调用者如何消费其decision；主入口打印JSON但上游只检查rc==0的边界写清楚。无证据不能改称“契约要求每次都下载成功”，它本来是管理检查，可能合法决定无需下载。

C. 回到75对象总表，避免只在3个脚本打转：
- 运行/BLACKBOX_FULL_DATA_INVENTORY_CURRENT.json在本轮仅stat/hash（24519字节）；读取实际正文并上传，复用其中有效对象记录和旧全读证据，不用其摘要PASS自动当实测结论。
- 读取既有BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_HANDBOOK_CURRENT.md相关章节；定位下载域主入口和其已有参数/状态。若没有统一可执行入口，明确“分域入口+下载后编排”即可，不为凑一键新建编排器。
- 将上述共享正文证据绑定回对象/家族，继续原有有限引擎和规则适用范围工作。保留已验证身份、样本/全读、逻辑VIEW/物化、内容覆盖、规则/消费者和更新轴，避免旧字段覆盖新结论。

## 盘点与运行验证分开收尾
本任务不要求现在真实下载/中断重跑，也不要求修完所有业务缺口才能出盘点结论。完整正文分析后：
- 有依据的静态结论标STATIC_REVIEWED；
- 找到明确缺口标KNOWN_GAP并给影响/最小修复建议；
- 需运行验证标NOT_RUN，列下一阶段可复现的验证方式；
- 仍没读到的正文才是NOT_REVIEWED，不能拿它当“不可能验收”的永久借口。
不要把所有“运行未执行”机械等同“盘点范围尚未交代”，也不能用路径存在提前清掉内容/规则工作。

下一包交完整相关源码/摘录及来源身份、静态语义结论、75对象和有限引擎范围账本、完整剩余事项与修复优先级。阶段报可以保留，做完可做项再整批提交，不需每个函数预览等GPT另发指令。
仅业务只读；隔离盘点产物与HUB可写。不改生产catalog、数据、规则、策略、环境、CURRENT或迁移state，不下载、不回测、不清理、不重开R9，不新增服务/巡视/Agent。本信仅数据管理。
