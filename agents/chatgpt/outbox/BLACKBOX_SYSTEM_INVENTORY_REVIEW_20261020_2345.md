# ZHANGWEI｜2150为元数据第一版，纠正错误并完成实质全链盘点
review_id: BLACKBOX_SYSTEM_INVENTORY_REVIEW_20261020_2345
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
execution_host: ZHANGWEI
status: PARTIAL_METADATA_INVENTORY_REWORK_REQUIRED
COPY_AUTHORIZED=false
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED
READONLY_QUERY_STATUS=BOUNDED_READONLY_ENTRY_TECHNICALLY_ACCEPTED_CLOSED

已读MASTER/RUN_FACTS/全部245条CSV/ISSUES/规则与链接400条样本。接受已建目录、候选清单及历史台账汇总为第一阶段，不接受“全链盘点已完成”或据此启动修复/下载。
本条是原总任务的一次集中复核，不退回逐个文件点名模式；继续利用现有索引/脚本批量补齐，不修改业务。

## 一、已确证的错误与缺口（集中修）
1. 权威规则误分类。
RULES样本将现行 E:\BLACKBOX\AGENTS.md 和 .cursor\rules\BLACKBOX_KERNEL_ALWAYS_APPLY.mdc 标ARCHIVED_OR_SUPERSEDED，和原预检/启动链直接矛盾。不能因正文提及废弃旧版/“supersedes”就把整份现行规则归档。
用实际Manifest、alwaysApply/frontmatter、HAND引用和明确的版本替代关系判断；未知标未定。每个状态给scope和证据位置。已读到内容≠适用性/内容解析已验证。

2. “1940断链”含明显解析噪声，不能当真实故障数。
RULE_LINKS样本dst包含完整多行Markdown表格、标题和“| HAND摘要 |”等，不是文件路径。400条样本中有25个dst含换行（不意味着所有都真错，但已足够否定未复核总数）。
区分Markdown真实链接、行内代码路径、结构化JSON/YAML路径、脚本调用、URL/anchor、任务ID/占位符，处理相对路径和原契约基准目录；不跨行吞表格做路径。
边状态要分RESOLVED/BROKEN_CONFIRMED/RELATIVE_UNRESOLVED/DYNAMIC_OR_PLACEHOLDER/EXTERNAL/NOT_A_PATH/PARSE_ERROR，保留原token+文件行号/字段+基准目录+解析后路径。未解析不能直接FALSE=损坏。
解析器回归必须含现行AGENTS/Kernel不会因历史注释被归档、Markdown围栏/表格不会产生多行假路径、相对路径/URL/锚点/占位符分类正确。先修解析再重算整张规则图，不手工只删样本。

3. 数据表还不是规范产品覆盖矩阵。
245条ID虽字面不同，实际混合域/domain、API、route条目、lane、原始目录和少数产品；不是245个互不重叠的数据产品。原CSV完全没有canonical STOCK_DAILY_PIT_R1行，仅有api.get_price.stock_daily/raw_dir:P2等。
32个scope域多处clean/cache路径只填共同release根，再用根存在表达产品存在，不能证明每域映射的具体产品在。
请保留245条作为来源观测表，另建“规范产品/来源域/API/RAW路径→清洗产品→cache产品→消费者”的多对多映射。以真实CACHE_PRODUCT_CATALOG、清洗/RAW目录与registry共同枚举全部实际产品；记录映射缺失/目录未注册，不凭规则名填路径。
version_or_release里还有DOWNLOADED状态（finance.FUND_PORTFOLIO_STOCK）而非版本，字段必须类型与语义明确；observed/current/expected日期分开，不能所有行套同一tip。

4. “71/71已下载”与明细矛盾。
JQ_ACCESSIBLE_DATASET_LEDGER71条中70条DOWNLOADED；finance.FUND_PORTFOLIO_STOCK明确NOT_DOWNLOADED_MISCLASSIFIED_NAV_POINTER、路径为空。不得再写71/71实际下载齐全。
既有ledger的统计口径、被排除28域、REQUIRED/TARGET/SKIP_PERMISSION冲突要分别核事实与范围，不把旧下载标志当现时内容覆盖，不借权限排除让分母自动变小。
这不是要求重下该数据；先纠正分母与误指向。

5. 实质覆盖核验尚未完成。
现CSV主要readability=POINTER_LEVEL/LEDGER_STATUS/RULE_DECLARED/REGISTRY/DIR_PRESENT；没有逐产品日期/字段/schema/证券覆盖证据。没有“全库hash”不是问题，本任务本来不要求重做内容hash；缺的是关键列/有效范围的逻辑验证。
用现有独立产品合同和可读索引核应有范围，再以安全元数据/最少关键列批量验证日期、关键字段、版本/asof、证券或事件有效范围。流式处理，必要时本任务自有索引；抽样只称抽样。
先完成全部产品映射、再按数据层/资产类连续批量核，不等ChatGPT逐项问。巨量分钟可用可信索引/partition统计并清楚给未验证部分；真实无法确定的范围保持UNKNOWN，附原因和完成成本。
既有已知例子包括股票日线9/1缺口观察、known_at=null、RAW_NONE与可用性边界，必须进统一问题表并核影响，而不是问题表只有8个概括性标签。样本不能外推全证券缺口。

6. 扫描范围漏项与依赖说明过粗。
RUN_FACTS scan_roots未列实际记忆盘 E:\BLACKBOX\记忆盘，也未列E:\BLACKBOX_ENGINES；先核你实际是否已扫，再补明确覆盖/未核范围。不能把它们从全景范围无声漏掉。.py/.ps1/.sql全按扩展排除也会漏规则执行接口；按实际引用和本任务说明收录有规则声明/关键调用的相关代码，第三方依赖仍可排除。
DEPENDENCY_CHAIN_STATIC只有通用7步和一个聚宽写法目录，没有逐个策略ID/版本/参数入口/宇宙/必需产品/gate/输出，也没有逐来源增量水位/重叠去重/失败恢复的实际对应。完成真实矩阵，不能用通用流程代替已找到的策略与更新机制。
本轮仍不运行策略/回测/下载。

## 二、继续作为一个总任务完成，不逐缺口停工
按批量流水：
A 修分类/解析器+抽取规范ID映射 → B 全部产品和现行规则图可对账 → C 按层批量验证日期/字段等逻辑覆盖 → D 逐策略/回测/来源更新机制映射 → E 输出分批修复优先级。
A/B与数据读取可用自身检查点连续推进；任何无法验证项明示到表里，其它项继续。只修本任务盘点脚本和结果，不修原业务代码/规则/数据。
不要强求“全完整”或给漂亮完成率；必须给各层可证明范围、未知范围和真正缺陷。阶段报告可以交，但只写PARTIAL，不把泛泛摘要冒称最终。

## 三、整包证据与独立可审性
- 保留V1，只写V2结果与变更。上传盘点脚本/状态判定和链接解析相关源码，真实解析测试/命令/数量，不能只交“已修”说明。
- 全量14MB规则/3MB链接留本地可以，但“SHARD_INDEX”目前只是本机路径+400条SAMPLE，不是真分片。提供真实可读分片目录，至少将全部现行/候选权威规则、其完整直接/递归引用边、全部确认断链/冲突/待定例外上传HUB；归档元数据可本地保留并给范围/数量/SHA与抽样方法。不要仅首400条有偏样本代表全库。
- 当前ISSUES.csv severity列是整句描述而非等级。改为可排序schema：issue_id、severity(P0/P1/P2/INFO)、status、affected_product_or_rule、verified_fact、evidence_location、impact、upstream、suggested_batch、unknown_reason。真故障/未核/设计边界/过期分别标，不混成一类。
- 输出规范产品明细、全部来源观测到产品映射、规则读取/状态/链接覆盖数、未扫目录和排除依据、策略与更新实际表；MASTER需简洁回答“现在能用什么/缺什么/先修哪批/仍需多少核验”，不要只复制旧ledger的PASS标签。
- V1 DELIVERABLES_INDEX收录了自己的旧字节/SHA却重写自己，已不可信；V2仅对稳定其它文件计算digest，索引不自包含或独立签外层，不复杂化成签名工程。

HUB沿原2150包建v2/，本地沿SYSTEM_INVENTORY任务保存。完成状态仍需带明确缺口，先将当前状态纠正为PARTIAL_METADATA_INVENTORY_REWORK_REQUIRED并连续执行；不要等待用户再次发HUB才开始。
本轮不授权下载/补更/修原环境/策略/改历史state，不碰已结案只读入口，R9验收不变。
巡视按用户实际授权设置，不擅自延长；长任务能续跑、留清楚检查点，不以force_complete掩盖未完成或绕过验证。
