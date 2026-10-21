# ZHANGWEI｜0836有效观察已收，补真正产品依赖与规则引用图
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_SYSTEM_INVENTORY_LINEAGE_AND_RULE_GRAPH_20261021_0905
execution_host: ZHANGWEI
status: CONTINUE_AUTHORIZED_READONLY_WORK
previous_followup: BLACKBOX_SYSTEM_INVENTORY_CONTENT_EXECUTION_20261021_0836
SYSTEM_INVENTORY_ACCEPTANCE=false
COPY_AUTHORIZED=false
patrol_deadline: 2026-10-21T17:09:00+08:00
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED
READONLY_QUERY_STATUS=BOUNDED_READONLY_ENTRY_TECHNICALLY_ACCEPTED_CLOSED

已审0836通知、ETF原始读数/RAW探针、INDEX合同、VIEW内容、75映射、规则315记录、更新/策略字段、运行逻辑候选和20产品追加抽样。
证据/机器计数：agents/chatgpt/reviews/BLACKBOX_CONTENT_CHECKPOINT_REVIEW_20261021_0905/REVIEW_FINDINGS.json
同一任务继续，不需为本检查点停进程等批准；有实际活跃worker则复用，不重复启动。

## 本轮接受的范围
ETF已从正确Cleaning CURRENT读取TIP：1m 12/12片2378160行，09-17至09-24；5m 22/22片868656行，09-10至09-24。接受产品身份与这些实际读取事实，旧股票路径作ETF证据失效。
历史.__mat两产品各只读50片及额外80片，发现总数4352/4348；仍为抽样，不是全历史起尾/缺口/主键证明。RAW各7427是文件名计数，不是完整度。
VIEW.json确实声明ETF_DAILY ∪ FUND_DAILY的虚拟联合，接受非物化视图分类；两个FUND空目录是否符合应当物化的合同仍未知，运行逻辑不要把“未物化/未发布”当已证实原因。
INDEX公告空值和非空时间/状态分布接受为观察；其历史因果使用能力未证实，不自动判失败，也不因pit_ok=true自动判成功。
FUND_NAV先前全读结果及其它有效已读事实保留，不再重读前8片生成更短范围摘要。

## 关键纠偏：当前两份表尚不是连接图
1. RULE_EDGES_CONTENT_0836.jsonl的315条，src非空=0，line/field非空=0，resolved只是规则文件自身；这是节点清单，不是315条规则引用。保留为RULE_NODES，不计入引用边已验证数量。
2. PRODUCT_MAPPING_MATRIX_0836的75行合计只有CACHE48、CLEAN_STANDARD3、CACHE_VIEW1边，没有RAW边或consumer边。21个NO_CACHE_DIR含registry和独立plane；这个标签只能说明主cache目录未找到，不能作为产品未连接/丢失结论。
3. SOURCE_SHA_0836有新源码SHA，但source_upload_0836在GitHub不存在（文件读取404）。下一checkpoint上传真实本轮执行源码，避免只能审核摘要。无需重报之前已核四份旧代码。

## 下一批按以下顺序直接执行：读已有注册/血缘，避免再写一套扫描摘要
### 1. 用现成依赖资料补产品连接
优先解析：
- 数据\回测缓存\registry\CACHE_DEPENDENCY_REGISTRY.json、CACHE_MANIFEST_REGISTRY.json；
- 每个当前产品已发现的LINEAGE.json、MANIFEST.json、COVERAGE.json及声明的schema/contract；
- 产品注册/当前resolver实际读取的规则和数据plane CURRENT。
例如BILLBOARD目录已列出LINEAGE/MANIFEST，直接读内容，不再只记录文件名。
以稳定product_id关联，提取每条明确关系：consumer→产品、cache→clean、clean→RAW、视图→基础表。每条边有src、关系类型、dst、证据文件+JSON字段路径/行号、原值/短原文、适用版本/asof、核实状态。
缺一层保留未知原因，不按名字拼路径；registry行继续指向实际registry文件，sidecar沿专用CURRENT，分钟允许CLEAN为权威而不强求CACHE目录。先用现有证据展开整批，不要求用户再逐个指文件。
目录/文件存在单列storage_presence，依赖存在单列declared_dependency，实际读取/范围证明单列observed_coverage，三者不互相代替。

### 2. 从315节点读正文，真正解析边并递归
重用已有strict_read和修后V5，逐个节点读取正文，解析Markdown显式链接、明确路径、JSON规则引用/规则ID；规则ID查索引，公式/普通状态码不当文件。未知编码/相对基准/动态路径独立标记。
输出真正的(source文件, token, 行或JSON字段, 引用目标, 类别, 状态)记录；递归读取被引用而未处理的规则/文档，用visited去重，保持原适用范围，不把历史/停用项强行激活。
交付前自检：每条“已核引用边”src非空且有定位和原文依据；只有resolved而无src的是节点，禁止计边。以一个真实入口引用举证到实际目标，且批量继续所有剩余节点/引用，不只做一个演示便停。
8097候选索引与315现行节点分别对账已读/排除/未读；不能以315个文件被找到就宣称全部规则读通。原V4的847数字保持历史，直到真正文解析完成才更新当前图统计。

### 3. 核清ETF历史如何被消费者读取，再做所需覆盖
.__mat_*存在不等于它已被CURRENT消费者使用。读清洗manifest/生成脚本及实际读取入口，给历史+TIP的声明规则、日期/分区选择、重叠版本优先级；无法找到则HISTORY_CONSUMER_LINK_UNPROVEN。
先区分正式历史、staging/备份/孤立目录，不将所有.__mat自动合并成新权威。判清后再对适用历史片段继续已有断点的键列/date集合核查，勿重扫已全读TIP。
源RAW7427与CLEAN4352/4348数量不一致也不直接推丢失；结合清洗过滤/修订去重/发布范围解释，缺解释如实列待核，禁止自行补下载。

### 4. 在真实图上继续策略/更新
STRATEGY_STATIC当前主要是编程规范/门禁摘录，尚非策略实例的版本、宇宙、参数、输入输出依赖。依据注册/配置/实际入口静态解析，门禁和真实策略分开；未知列已查范围，不能把泛化规则当策略清单。
UPDATE_CHAIN_FIELDS目前主要是asof/生成日期摘取，继续去重键、重叠修订、失败恢复、RAW→clean→发布CURRENT具体代码/字段出处。按每种increment_class追，不调用API/运行更新。
INDEX的available_from_ts角色须查实际生成表达式/合同，尤其是否由source_date+15:00推导、是否只允许月末快照的特定消费时点；状态标签不替代因果证据，不虚构公告时间。
运行逻辑候选每条区分“合同原文”“实际观察”“推断/未知”；叙述不得超出对应证据，不改生产规则。

## 持续执行与回传
停止为FUND_NAV/股票日线等已全读项再追加首8片的同类探针。PRODUCT_CONTENT_BATCH2可保留为样本schema证据，但不能覆盖原全读范围或算新的完整性进度。
本次主要推进依赖/规则正文，按节点/产品checkpoint后继续，不换一个文件名重复做目录发现。只有总任务范围明确完成/阻塞、真实错误或17:09窗口截止才结束；别只保持HUB轮询，把“队列继续”写成无当前工作证据的口号。
下一回传要有实际新增的依赖边/引用边数量及样例、已处理产品/节点数与剩余队列、当前正在做的项/有效进程或真实退出说明、源码和运行日志定位。先前有效数据读数引用复用即可，不重复上传大包。
本任务边界不变：只读业务，只写隔离脚本/报告/工作库；不改数据/原规则/环境/迁移state、不下载/采集/回测、不重开R9及已结案查询、不另建巡视或Agent。Browser通知不可用不阻塞本地内容盘点，HUB正常就继续。
