# ZHANGWEI｜接受V2纠偏进展，继续同一总任务至实质盘点
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_SYSTEM_INVENTORY_CONTINUE_20261021_0010
execution_host: ZHANGWEI
status: CONTINUE_READONLY_QUEUE_WITH_CHECKPOINT
COPY_AUTHORIZED=false
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED
READONLY_QUERY_STATUS=BOUNDED_READONLY_ENTRY_TECHNICALLY_ACCEPTED_CLOSED

已审V2 MASTER/RUN_FACTS、69产品目录、12个优先样本探针、解析器源码/回归、72 broken明细和策略/更新表。
认可已纠正AGENTS/Kernel状态、70 downloaded+1 misclassified口径，且如实标PARTIAL；保留这部分，不重跑重复摘要。
但当前约3分钟脚本仅交元数据修订，不能替代原2345要求的完整数据/规则核查。现在继续同一总任务，勿每次只交一个PARTIAL表就待命等用户HUB。

## 先消除会误导批量核查的三项口径
1. 路径路由而非主cache目录拼接：
目前load_cache_products把catalog全拼在主Cache release，18个MISSING_DIR含CACHE_MANIFEST_REGISTRY/CACHE_DEPENDENCY_REGISTRY、TUSHARE_CBOND_*、ETF_MINUTE_1M、STOCK_MINUTE_1M。
这些可能是registry文件、独立cbond CURRENT/映射、Cleaning CURRENT分钟路径，而不是主cache子目录。沿现有resolver对分钟/cbond分支、catalog manifest和专用CURRENT/sidecar映射核真实authority及存在性。仅在主根没找到，状态是NOT_IN_MAIN_CACHE_ROOT，不是数据丢失。
这也是69的范围限制：69是本轮主cache catalog+目录产品枚举，不等于所有RAW、清洗、外源和数据库产品总数。
补RAW→clean→cache/独立plane→consumer真实多对多映射；当前PRODUCT_SOURCE_MAP只是重复cache_path而缺RAW/clean映射，不算完成。未知保留证据和reason，不能猜补。

2. 72条BROKEN仍含假确认：
- 明细首条“数据/研究报告/日增量/<asof>/”是模板；源码_classify_token先标DYNAMIC，随后exists分支又覆盖为BROKEN。ChatGPT独立调用该函数已复现。动态/占位符分类须终结返回，不再走“确认缺失”。
- 明细含E:\BLACKBOX\经验卡;E:\BLACKBOX\记忆盘的两个路径被当一个、HAND文字路径含U+FFFD替换字符。修分隔符处理与文本解码审计，未知编码/原文已损坏不得直接判目标缺失。当前read_text(errors="replace")不适合提供“确认断链”证据；改严格解码，记录成功编码或DECODE_UNVERIFIED，保留原字节位置，不修改原文本/文件名、不凭猜测恢复文字。
- 源机旧D路径先记host-specific/legacy reference，并关联R9目标映射，不直接判整个规则死链；动态参数路径/本地秘密路径仅核引用状态，不读密钥。
补上述真实反例到解析测试，重算BROKEN_CONFIRMED，不手工只调整72这个数字。
规则标ACTIVE_CANDIDATE不是全链已验证；继续从现行入口递归核被引用的未定文件，不仅解析315个当前候选。8097与V1的26736覆盖范围差异要有逐根计数/排除/未核对账。

3. 覆盖抽样不能作为实际起尾：
股票日线样本仅前6个year文件2014..2019，不能反映其2026 tip。保留SAMPLE标签，队列处理全部相关分区的最少日期/代码/必需字段。
FINANCIAL_INDICATOR只有pubDate/statDate/pit_available_from等就停止为NO_DATE_COL，是抽取器未使用事件/财务合同；需按该产品时间语义核，不统一强求date字段。
事件/成分/财务等避免按普通日线误判；应有范围仍来自独立合同，不自证。

## 实际执行队列，不再元数据跑完即停
- 以规范产品+其它plane发现项为队列，逐项：权威定位→格式/schema→应有范围→实际覆盖/字段/证券或事件维度→依赖/风险。持久化PENDING/RUNNING/VERIFIED_PARTIAL/VERIFIED_WITHIN_DECLARED_SCOPE/BLOCKED及证据，失败一项继续下一项。
- 全部产品先完成authority/schema/范围证据，再对日频/财务/行业等批量做最少关键列的流式覆盖，分钟/巨量外源用有效索引并明确未验证范围。不要只处理12个固定优先样本后把其它产品长期EXISTS_ONLY。
- 资源/会话需要长跑时，可启动一个本任务专属只读盘点进程，保存精确PID/argv/开始时间/解释器/日志/检查点，不新建服务、定时器或Agent；同一任务已有进程则复用，不启动重复实例。后台脚本必须只写本任务报告/工作库，不写原业务。
- 在HUB给STATUS_PROGRESS.json：当前阶段、产品总分母与各状态数、实际正在跑的产品/阶段、PID或前台执行证据、已做/未做/阻塞、检查点、时间。不要无执行证据写“持续运行中”。
- 按用户本机现有巡视期限工作，不擅自延长；若即将超过可运行窗口，保留可续跑状态、明确部分完成，不能靠force_complete变更权限或掩盖未完成。

## 后续矩阵继续完成（静态，不启动业务）
策略表目前多数是TASK_DIR且version/universe/products均UNKNOWN，更新表多数watermark=NOT_IN_RULE_ROW、overlap=PER_CLASS_CONTRACT。这些是发现线索而非依赖盘点完成。
按原总任务读取真实策略注册/入口/config/引用规则，记录版本、参数、宇宙、数据依赖与输出；读取每种更新class真实水位/去重/修订/失败恢复规则及代码出处。
缓存编译器、修复任务、实盘任务归档不都当策略；类别分清，未知给具体已查范围。不要执行策略、回测、采集、外部API或下载。
前两层尚未查完不阻碍静态映射可做部分；最终统一问题表按影响和依赖分批建议，不自行修原环境或数据。

## 回传与完成标准
沿2150/v2维护，不再重写一套无关任务。下一次应交持续执行证据/真实覆盖增长/已纠正确认断链，而不只是换版摘要。
补盘点脚本改动和严格回归；批量结果可分片+checkpoint上传，HUB至少完整主产品路由/状态/异常表，原数据/私有聊天/秘密不上传。
仍PARTIAL直到原2150/2345范围逐项完成或明确不可验证且给原因/成本；不能以UNKNOWN填满全表冒充完整。
原R9、已结案查询、原业务规则/环境/数据库一律不改。无需用户逐文件提醒或跨机传话。更新INBOX_FOR_CHATGPT，默认继续授权范围内只读盘点，不自动切到修复阶段。
