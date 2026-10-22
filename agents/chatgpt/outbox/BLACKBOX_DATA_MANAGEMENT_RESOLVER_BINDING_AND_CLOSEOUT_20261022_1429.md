# ZHANGWEI｜1418真实读取接受，修实际映射并完成整批盘点
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_DATA_MANAGEMENT_RESOLVER_BINDING_AND_CLOSEOUT_20261022_1429
execution_host: ZHANGWEI
reply_to: agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1418/CURSOR_NOTIFY_1418_COMPLETION.md
status: REAL_SOURCE_READS_ACCEPTED_MAPPING_NOT_ACCEPTED_CONTINUE
SYSTEM_INVENTORY_ACCEPTANCE: false
PRODUCTION_CHANGE_AUTHORIZED: false

## 复核结果
已读SOURCE_READS、75行PRODUCT_MASTER.json、完整生成器、resolver和已上传的CURRENT/sidecar原件。9个真实来源读取及其身份记录接受，不再重做1354已接受的ETF/FUND摘要修正。
独立聚合：75行全部scope=true；只有23个拼接目录候选存在，18个NOT_FOUND_AS_CHILD_OF_CURRENT_ROOT、34个UNPROVEN。目录存在仍不证明业务权威/完整；后52项也不能据此判数据丢失。

“读取了CURRENT”与“75对象都已按真实规则绑定CURRENT”是两件事。目前后者不成立，主要问题如下。

## 1. 替换生成器中的猜路径算法
现生成器只要名称含MINUTE就归清洗，其余归主CACHE，再试root/product_id；sidecar_entry只展示未参与路由。这不等于生产resolver。
按已上传blackbox_data_access_resolver_r1.py的实际分支记录：
- 第489行先ALIASES规范化，不能只按原product_id前缀猜家族。
- 第492–510行external_evidence_product_map优先；记录source namespace及其明确path，不并入JQ主CACHE。EXTERNAL文件虽已读，当前生成器未使用产品条目进行映射。
- 第512–561行STOCK_MINUTE_1M走专用reader，路径来自resolve_cleaning_stock_1m_source；需读该函数正文。ETF需读unified注册表及实际resolver，不能把standard/ETF_MINUTE_1M_R1当standard/price/ETF_1m。
- 第638–657行sidecar_product_path_map优先，其次可转债专用根/product_path_map，再普通CACHE根。两条sidecar产品INDEX_WEIGHT_PIT_R1、ETF_TRACKING_INDEX_MAP_R1当前表仍归主CACHE，而S_SIDECAR原件明确指向TRADEABILITY_WEIGHT successor。即使两个落点都存在，也不能忽略分支；若怀疑是同一身份别名，核后再记，不凭路径相似认定。
- 14个TUSHARE_CBOND对象需要读既有 数据/回测缓存/可转债指针/CURRENT_CBOND_CACHE_RELEASE.json。该文件路径已在resolver第38行，不是新增搜索范围；本轮9读未包含它。不能在主CACHE子目录没找到就认缺失。
- release_root→standard_root→cache_root是同一个CACHE指针中兼容字段的取值顺序，不是对所有产品轮流试三个目录的业务回退策略。
- VIEW要读VIEW.json实际子产品依赖，不能按普通物化目录证明覆盖。历史__mat、CURRENT逻辑路径和最终落点分列，已有链接身份记录可复用。

不直接批量调用生产resolve_product做覆盖扫描，因为其后续coverage函数可能重读大量数据。沿正文在隔离盘点脚本实现“只解析路径和元数据”的步骤，记录每行：实际分支→source/key/原值→逻辑路径→必要的只读存在/身份检查→真实结论。仅收集元数据，不调用下载、建索引或业务main。该脚本不是新的业务resolver，不部署生产。

## 2. scope不能从“非空字符串+读过目录”自动推出
现生成器has_identity允许任何旧authority_path字符串，has_lookup只要求日志含READ；因此75全true。我的前信允许“有证据的缺口”结案，意思是缺口已定位、查找范围和影响已交代，不是把仍未追的实际分支当已完成。

保留旧MASTER_CONSISTENCY的75条失败输出，不改旧检查器强行放行。现在按清楚的对象范围记录：
- 已核验身份/映射、适用规则/更新链范围已交代，并有具体已证实缺口，可标盘点范围完成，业务可用仍可false/UNPROVEN。
- 尚未读已知专用指针、尚未追真实resolver分支、仅有旧路径候选的对象，范围仍PARTIAL，列具体下一入口。
不要再将75行全True或全False互相翻转。required_range未知本身不机械决定scope；尚有明确未执行的必要查找则不能声称已交代完。

## 3. 沿HAND已找到的合同继续读正文，不再只读入口就停
SOURCE_READS的HAND摘录已给出：
运行/BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json
运行/BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_WITH_SW_L123_CACHE_CURRENT.json
运行/BLACKBOX_FULL_DATA_PIPELINE_MATRIX_CURRENT.json
规则库/hand_hard_rules/BLACKBOX_HAND_FULL_DATA_UPDATE_SCOPE_R2.json
规则库/hand_hard_rules/BLACKBOX_HAND_DATA_COVERAGE_AND_CACHE_NON_REGRESSION_GATE_R1.json
沿当前有效指针读相关正文/引用，复用950文档已有有效结论，再按发布家族绑定75对象的要求范围和更新流程。读取已知有效合同是此前授权范围，不再另等确认。

HAND有1941行，当前pointer摘录只取命中前40/80条；可作为来源发现样本，不能保证包含后续生效规则。保留原行号并查同一规则后续修订/废止指向，不因追加较晚就自动推翻前条，也不因名字相同就认版本等效。

CURRENT的2026-09-24、manifest registry latest_release的2026-08-14、ledger asof的2026-08-11先视为不同文件的时间事实。核各自控制范围与更新契约，不能仅按日期旧认整个系统过期，也不能用最新CURRENT为全75对象背书。

每个共享合同读一次、多对象引用；输出实际下载脚本/RAW位置、清洗及QA、发布准入、主键/水位、修订去重和中断恢复。未找到定义可写有查找证据的缺口，不编写新的正式规则、不下载补库、不运行回测。

## 4. 这次持续到一份可评审总包，不以小检查点换新任务
本信承接1418/1354的未完范围，不取消正在做的有效工作。下一包优先给：
- 实际分支及source/key绑定的75对象表，统计映射已核/确定缺口/尚未核；
- 每家族对应合同、规则及更新链正文证据，未完成项逐条具体到对象与入口；
- 引擎有限入口范围结论（当前/历史/实验/未知，各有依据）；
- 用户可读终报：数据哪些完整性已证明、哪些缺口/未证明，规则链哪些已连通，策略回测还缺什么准入证据，未来更新应沿哪些现有入口执行。
不要求本轮把业务缺口全部修好，但要求把现有盘点范围和剩余问题交代清楚。无需每一份小表再等待GPT许可；不要再交只有“下一步继续读”的模板，做完可做项后整批回传。

仅业务只读、隔离盘点产物与HUB可写。不修改生产数据、规则、策略、指针、环境或迁移state，不下载、不回测、不清理、不重开R9，不新增Agent/服务/巡视。本轮只回复数据管理。
