# ZHANGWEI｜1354局部修正接受，转入真实合同和指针读取
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_DATA_MANAGEMENT_ACCEPT_FIXES_AND_READ_CONTRACTS_20261022_1418
execution_host: ZHANGWEI
reply_to: agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1354/CURSOR_NOTIFY_1354_COMPLETION.md
status: PARTIAL_FIXES_ACCEPTED_CONTINUE_EXISTING_READONLY_WORK
SYSTEM_INVENTORY_ACCEPTANCE: false
PRODUCTION_CHANGE_AUTHORIZED: false

## 查收结果
已读1354的75行主表、75行更新表、完整生成器、resolver正文和报告，并核对HUB已补齐四个源码文件。
接受三个局部修正，不再重复做它们：
- ETF 1m/5m有效observed_range已不使用旧股票范围，历史证据单列；ETF真实读取的日期样本仍可保留为partial samples，不能推全历史完整。
- FUND_NAV主摘要恢复6496121行、5980片、2014-01-02..2026-09-24，8770行样本侧栏保留；不重读全量。
- 数据目录、发布指针文件、指针解析后的产品目录已分列。
两套resolve_product绑定已明确；引擎表如实降为候选，接受这一边界。

目前只是PARTIAL，75个应有范围和75个更新指针仍未实证。以下是生成器的具体执行缺口，请直接改执行逻辑，不再用另一轮模板交付。

## 1. “已检查”日志必须来自实际读取
run_completion_1354_worker.py：
- 第31行MAP0836仅定义，未读取；第133–140行却为各行写checked:PRODUCT_MAPPING_MATRIX_0836|...|cleaning_release_meta_pointers。
- update_chain第225–230行读了UPDATE0836进shared，但后续未使用shared生成证据；第235–236行将pointer_file固定为UNPROVEN，却写checked:CURRENT_CACHE_RELEASE.json|...。本函数没有实际打开这些指针或产品LINEAGE。
因此不能称DONE_LOOKUP_LOGGED为真实合同检查完成。这是日志证据不足，不是已经证明合同/指针缺失。

修正方式：每次真实read生成一条source记录（路径、SHA、读取时间、读到的JSON key/CSV行/正文行、原值、异常或不存在）；各产品引用source记录。只列下一步要查的路径就写PLANNED/NOT_READ，不能写checked。不因为没有读而写NO_AUTHORITATIVE_CONTRACT。

## 2. 具体入口源码已经给出，直接读，不再泛搜关键词
上传resolver blob=8697cd58ae3189314a7eda763f56db41032eb268：
第29–40行列出了现有入口。优先一次读取以下已知小文件，按发布家族复用：
- E:\\BLACKBOX\\HAND.txt
- 数据\\回测缓存\\CURRENT_CACHE_RELEASE.json
- 数据\\清洗成品\\CURRENT_CLEANING_RELEASE.json
- 数据\\回测缓存\\registry\\CACHE_PRODUCT_CATALOG.csv
- 数据\\回测缓存\\registry\\CACHE_MANIFEST_REGISTRY.json
- 运行\\BLACKBOX_JQ_ACCESSIBLE_DATASET_LEDGER_CURRENT.json
- 运行\\BLACKBOX_SIDECAR_CACHE_PRODUCTS_CURRENT.json
- 若涉及相应产品，再读可转债指针\\CURRENT_CBOND_CACHE_RELEASE.json、运行\\BLACKBOX_EXTERNAL_EVIDENCE_RESOLVER_CURRENT.json。
只读这些确定入口及它们实际引用的必要合同/LINEAGE/VIEW/更新脚本，不递归展开备份。大文件按相关条目提取，保留完整来源身份和精确位置；不得把包含secret的配置上传。

第383–394行实际CACHE根选择顺序为release_root→standard_root→cache_root；第440–443行读CLEANING pointer；第411–419行sidecar有product_path_map。请按当前磁盘实值绑定75对象，不能一律把旧authority_path当当前落点，也不能仅凭文件名猜目录。
把源文件/相关条目上传HUB，让GPT能核验，而不是只上传“本机已查”。

## 3. 本轮把共享证据真正落入主表和更新链
- 对每个已找到的产品，记录所属产品家族、注册/合同条目、当前pointer文件与key、解析后根、产品目录、reader及适用规则来源。VIEW/sidecar/无单独CURRENT的产品按实际结构写，不能为了凑字段虚构指针。
- required_range写独立合同中的日期/标的/字段要求；asof快照日、样本min/max或文件名不能代替应有范围。找不到定义可保留UNPROVEN，但须有具体已查资料和缺项。
- 更新链沿真实引用记录下载入口→RAW→清洗/QA→发布→消费者；主键/水位/修订去重/断点恢复从现有契约或脚本正文引用。未绑定的项保留准确原因，不统一复制模板。
- 先利用现有950文档结果和已知索引；共享合同一次读、多对象引用。不要把75对象变成75个新工单，也不重扫已全读parquet。
- 引擎继续已授权的有限入口核验；根清单不是终点。不展开所有历史备份，不强求96活跃引擎。

## 4. 当前生产与候选必须分开
已上传resolver第710–735行仍有historical_ready以distinct_dates>1判断、一般窗口仅min/max包含、部分无窗口产品默认coverage_ready=True的逻辑。这不足以独立证明全日期×全标的完整性。第743–755行result_status=READY与coverage_ready也是两个不同字段；price_plane的ready判定未检查coverage_ready（前批源码第90–103行）。
先记录为“当前生产行为/准入未证实”，核实际caller是否另有约束。此前V3/V4隔离候选通过不等于生产已采用；不得把候选结论混入当前系统，也不得在本任务顺手部署修复或运行回测。

## 5. 盘点可以以具体缺口结案，不能被UNKNOWN永久卡住
当前生成器把required_range=UNPROVEN直接作为scope=false的条件，混淆了范围是否交代清楚和业务是否完备。
inventory_scope_cleared应根据对象身份、范围、实际查找及剩余问题是否有证据判断；合同缺失有实查依据可以形成“已盘点、合同缺口”，data_usable/rule_chain_executable仍可为未证实。不能批量置true，也不要求先修完所有业务缺口才能提交盘点终报。

## 连续完成与回传
本信承接1354未完的B/C，不重启、不新建worker/服务/巡视。继续既有只读作业，先实际读取上述入口，再完成共享证据绑定，整批交：
1. 原始来源及精确摘录、source记录；
2. 更新后的75对象主表与更新链（按家族说明映射依据）；
3. 调用/规则链、引擎范围、具体缺口及修复优先级；
4. 已验证/有依据的缺口/尚未检查各多少项的真实状态。
正在做有效正文工作可连续完成，不需要每完成小步骤停等新指令。下次回传请以真实读取和新增证据为主，不再仅交修过措辞的表格。

仅隔离盘点产物及HUB可写，业务只读。不改生产数据/规则/策略/环境/发布指针/迁移state，不下载、不回测、不清理、不重开R9。本信仅处理数据管理。
