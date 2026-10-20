# ZHANGWEI｜恢复实质盘点，纠正统计口径
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_SYSTEM_INVENTORY_EXECUTION_CORRECTION_20261021_0650
execution_host: ZHANGWEI
status: CONTINUE_READONLY_INVENTORY
supersedes_followup: BLACKBOX_SYSTEM_INVENTORY_CONTINUE_20261021_0010
COPY_AUTHORIZED=false
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED
READONLY_QUERY_STATUS=BOUNDED_READONLY_ENTRY_TECHNICALLY_ACCEPTED_CLOSED

继续2150总任务及2345/0010未完成项。用户要本地批量查清数据、规则、策略和更新链条，避免反复逐文件询问。这次是合并纠偏和继续执行，不是新的业务修复授权。

## 已审事实及立即处置
已审continue_0010下队列、覆盖探针、规则边、策略/更新表、日志、STATUS_PROGRESS和WORKER_PID。00:21:31状态为BATCH_PASS_COMPLETE_OR_BUDGET，elapsed396.4秒；06:46:03心跳仍引用同样计数。通讯正常不代表盘点进程持续工作，不能写“整夜扫描中”。
先核PID39980的当前存活/创建时间/精确argv，查实际工作日志和退出/暂停原因；PID文件本身不是存活证据。若仍有本任务工作进程，先确认正在处理什么及是否有进展，勿另开重复实例；若已退出，可在本轮改进脚本后启动一个可续跑的只读工作进程。不要仅发送ACK又待命。

保留现有队列和结果，查清为何只跑一次短批次便停。VERIFIED_PARTIAL、NOT_IN_MAIN_CACHE_ROOT及“只探针完毕”不能是总任务的完成条件。每产品分阶段checkpoint：authority/schema→应有范围证据→实际覆盖→依赖。浅探针已做的不重复空转，转入尚未核实的下一阶段；真正无法核实的项记BLOCKED及具体已查证据/原因，继续其它项。单批时间预算到达时保存并继续下一批，直到授权窗口结束或队列在明确范围内全部完成/阻塞。暂停/异常/自然结束均写真实原因。

## 数据核查优先取得实质增长
当前75是队列对象分母，含registry文件，不能写成75类业务数据全量。4项VERIFIED_WITHIN_DECLARED_SCOPE中两个是registry文件，另两个是sidecar产品；保留各自证据和“核了什么”，分开对象存在、实际覆盖已核、独立应有范围已核，不能汇总成4套数据完整。67项PARTIAL多数仍为分区抽样，不是数据完整度结论。

继续用现有权威CURRENT/catalog/resolver定位，各plane去重建规范产品映射；主cache外4个30/60m产品须追真实分钟合同/派生关系，未核前不判丢失，也不自造应当物化的产品。RAW/clean/cache/独立plane/consumer范围分别列发现数、已查数、未查数，75不冒充整个BLACKBOX总分母。

现在优先对已定位日频/财务/事件产品流式读取最少必要键列，覆盖全部相关分区，给出实际起尾、日期集合/内部缺口、主键重复/空值、证券/事件维度及合同要求字段。日频与现有独立交易日历/证券有效期及停复牌等适用合同对照；财务区分报告期、披露/可知时间；事件表按事件合同，不要求每天有行。不能只以min/max或year目录连续判完整。
例：CORP_XR_XD_EVENT已有report_date、implementation_pub_date、a_xr_date、publication_date等却标SCHEMA_ONLY_NO_TIME_COL，应读取本产品规则确定时间语义，不能因不在通用字段白名单就当无日期。应有范围找不到时保留UNKNOWN，报告观察事实及无法证明的部分，不用观察数据自证。
巨量分钟用现有索引/统计和必要关键列分批核，记录索引适用范围与未验证项；勿为本任务重跑全盘hash、8百多万路径递归或再接源机扫描。

## 规则图先纠正分类，再谈断链修复
1551条BROKEN_CONFIRMED不可作为已确认故障数。明细中534条raw_token只是全大写下划线标识符，39条以cursor/rules开头，还有明确的公式：
- AGENTS.md: BACKTEST_MANDATORY_PRECHECK_R1，被当根目录文件；
- AGENTS.md: KNOWN_AT <= SIGNAL_TIME < FILL_TIME，被当文件路径；
- 多条cursor/rules/...需对照原文检查是否丢失了.cursor的前导点。

修本任务解析器，不修改原业务文档：
1. 保留原文token、行/列、严格解码结果；不得strip掉路径开头的点、../或UNC语义。已损坏/不能解码另列。
2. inline code不等于路径；规则ID查规则标识索引，表达式/参数/状态码另分类，缺ID映射是规则引用未解析，不是文件确认不存在。
3. Markdown链接目标、实际文件路径、带锚点链接分开解析；相对路径按该文档明确基准解析，基准不明记UNRESOLVED_BASE，不猜根路径。
4. 保留0010要求的模板、分号多路径、host-specific、secret引用分类，不能后续exists覆盖；递归核真实引用，不截断成只查315个候选后宣称全规则。
5. 加上述真实反例及.cursor、../、相对基准、规则ID、公式到回归，并上传实际运行解析器/worker源码及测试。仅3个合成通过不足以证明分类正确。保留旧结果不销毁，重算分类和可确认故障清单；每条BROKEN_CONFIRMED需原文、基准、解析后路径、实际检查证据。

## 更新及策略表纠偏
更新表大多数watermark同为2026-09-25T04:04:43+0800。先逐类核真实JSON字段路径/代码语义，区分published_at/generated_at、covered_through、ingest_cursor；统一发布时间不能推成每源数据水位。若目前只有发布时间，数据水位写UNKNOWN，保留原字段值和出处。
继续读每类更新实际去重主键、重叠回拉/修订、失败恢复及RAW→clean→cache发布关系。仅静态检查，绝不调用外部API或下载。
策略表区分策略入口、门禁/工具、缓存编译/历史任务；仅名字像策略不算已识别策略。读取实际入口/config/规则引用，记录参数、宇宙、输入输出和因果时间约束；找不到则明确查了哪些位置，别全部STATIC_PARSED_HEAD/UNKNOWN后当完成。先把数据与规则未满足的依赖明确标出，不运行回测/策略。

## 执行、回传及边界
继续沿2150/v2/continue_0010写报告/工作库或其子目录，不另建一套摘要。上传本次实际worker/解析器源码、回归和修复前后差异，便于独立复核。
下一次回传应有：真实进程/退出证据；本轮实际读取产品/分区/键列数量及耗时；至少已推进产品的逐项覆盖证据；规则误判重算；更新水位字段出处；剩余队列。STATUS_PROGRESS包含当前产品/阶段、checkpoint时间、各阶段计数及最近实际增量；心跳可引用但不能替代这些证据。
在现有3分钟巡视通信节奏下定期上传有增量的checkpoint即可，不重复上传所有大表；无进展/进程退出要如实提示。已经授权继续只读盘点，无需等用户再发HUB才做下一批。
沿用现有窗口至2026-10-21T10:07:25+08:00，不延长、不新建服务/定时器/Agent。窗口到时保留续跑点，给完成/未完成/阻塞的统一实质报告。
只允许读原业务和写本任务隔离脚本/报告/工作库；原规则、数据、数据库、环境、迁移state/code不改，不清理，不运行采集/回测。R9及已结案只读查询不重开。
