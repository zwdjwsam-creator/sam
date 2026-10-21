# ZHANGWEI｜有限修正已复核，进入实质内容盘点并连续完成剩余队列
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_SYSTEM_INVENTORY_CONTENT_EXECUTION_20261021_0836
execution_host: ZHANGWEI
status: CONTINUE_AUTHORIZED_READONLY_WORK
previous_followup: BLACKBOX_SYSTEM_INVENTORY_AUTHORITY_AND_NEXT_STAGE_20261021_0815
SYSTEM_INVENTORY_ACCEPTANCE=false
COPY_AUTHORIZED=false
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED
READONLY_QUERY_STATUS=BOUNDED_READONLY_ENTRY_TECHNICALLY_ACCEPTED_CLOSED

## 审阅结果：接受有限修正，不重开已修项目
四份上传源码原始字节SHA与SOURCE_SHA_0815全部一致。
独立隔离运行：ETF/股票1m、5m四例均正确；ETF目录缺失而股票存在时返回UNKNOWN；../实际目标正确；cursor与.cursor不再无依据合并，共5项资产/3项路径检查通过。
复核附件：agents/chatgpt/reviews/BLACKBOX_INVENTORY_LIMITED_FIX_REVIEW_20261021_0836/independent_review.json（同目录有复核脚本）。
0730源码已确认含Arrow分批读取、day支持及按行配对；保留FUND_NAV5980分片和有效股票/ETF日频读取事实。不要再重复这些修正或重扫相同起尾。

真实ETF候选已经找到：
清洗CURRENT所属standard\price\ETF_1m 与 standard\price\ETF_5m；
旧路径是standard\finance\A股_stock_*。接受新候选的发现，但还需读取新候选并核身份后才算ETF证据。

## 当前缺口是未做内容工作，不是再改一轮摘要
STAGE_LEDGER_0815_CONTINUE的plane_manifests/strategy_static_refs只有exists、bytes、mtime。不能证明已读其运行逻辑/产品映射。
0730 main在fragment Pass A/B后return，0815b也在回归与报告后return。文件里写CONTINUOUS/PARTIAL_CONTINUE不等于实际后续工作。已有35828/40928是否仍有生产性任务请核实；尚存有效worker则复用，不复制实例，不热改运行树。
同一总任务继续下述A→B→C，检查点自动进入下一未完成事项，不交一份not_done列表后等新口令。授权截止仍为本轮已固定17:09+08，不重置、不新建服务/Agent。若原用户已另设本轮截止，给出处并沿实际有效截止，不因此卡住只读工作。

## A. 先完成已找到产品的真实核查
1. 在上述两个ETF候选路径读取schema/片段清单，结合现有清洗manifest/registry核asset_type、代码域、频率与版本；真正支持混合数据时给明确资产筛选谓词，不凭目录名或代码前缀单独证明。与旧股票路径的结果分开，旧错误ETF读数永久保留为失效历史，不再使用。
对真实分片按需要流式读必要列：日期集合/起尾、行数、键空值、合同主键、预期证券范围/交易日对照。巨量情况按片断点续跑并给实际增量，不只取year首片；未知应有范围明示未知。已有效读过的物理文件可复用读取事实，但不能省去不同产品身份/筛选的证明。
2. INDEX_CONSTITUENT：已有实测announcement_date全空、effective_from/available_from_ts/source_date非空。读取本产品合同/registry和生成逻辑，区分成分生效、来源日期、可知时点；给字段实际范围及pit_status/pit_ok/current_backfill的状态分布和含义。非空available_from_ts不能单凭字段名就当历史当时可用，回填/入库时间不能冒充披露时点。不补填或改数据。
3. FUND_LIKE_ASSET_VIEW存在.json，直接读该JSON与产品注册/consumer；核它是虚拟视图/引用还是物化表，追实际引用。其它两个NO_PARQUET也按manifest/合同核应当物化与否。只发现无parquet不判数据丢失，不自动修/下载。
所有范围按各产品声明asof核，不把“今天10/21”强行当历史冻结产品应更新到的日期。KEY/EXPECTED_SCOPE等证据不够仍标未证实。

## B. 批量读内容，交出真实映射和规则连接
保留现有发现索引作为输入，不再做一遍exists摘要。当前已知锚点可直接开始：
- 运行\BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json
- 研究系统\数据平面\CURRENT\DAILY_DATA_MANIFEST_CURRENT.json
- 运行\BLACKBOX_JQ_INCREMENTAL_DOWNLOAD_RULE_CURRENT.json
- AGENTS.md、.cursor/rules中的当前启动/查询/回测/更新入口，以及它们实际引用的规则、契约、记忆盘/经验卡与注册表。
对这些文件解析真实字段/段落及引用，沿明确依赖追踪并批量继续：
canonical product → RAW来源/状态 → clean产物 → cache/独立plane → consumer入口，
每条边给源文件、JSON字段路径或行/段、实际值、版本/适用asof、已核/未知原因。不要仅复制同一cache_path到所有列。75是当前对象队列，不等于全部BLACKBOX产品；其它plane按原2150范围继续发现、去重、对账。

规则分片并非必然为零：已上传0650源码recompute_broken_v4从本任务v2\shards\RULES_ACTIVE_SHARD_*.jsonl读315个候选；原V2还有8097索引项。
先核此真实路径和索引结构，修本任务脚本的查找口径，不能因在另一目录glob不到就写0并放弃。找不到则报告所查路径和具体原因，可用原索引/现行入口继续解析，不重扫百万数据路径。
以修后解析器对现行规则/被引用文档继续图遍历：已读、待查、重复、历史/停用、动态、规则ID未解析、编码/基准不明分别记账。明确根相对/文档相对依据；文本中的任意inline code仍不自动是路径。规则ID与普通状态码要区分，确认断链需证据。只修盘点脚本，不修原规则。
交逐边结果（可分片）和未解析事项，不能一直只挂V4汇总847；8097与315的包含/排除/未读范围要对账，不能宣称全部规则已链通。

## C. 在这些真实内容上整理策略与更新链
读取实际策略注册/入口/config/依赖，区分业务策略、前置门禁、工具、历史任务；静态提取版本、参数、宇宙、必需产品/字段、时间语义、输出与缺失前提。不启动回测、策略或采集。
按各更新class实际合同/代码追：上游API/文件 → 覆盖水位或游标 → 重叠回拉/修订规则 → 去重主键 → RAW落地 → 清洗 → cache发布/CURRENT → 失败恢复。published/generated_at、asof_target与实测covered_through分列。找不到给已查位置/原因，不整表UNKNOWN当完成。
笔记本来源AI的历史解释可列待核问题，但当前能从本地现有文件确定的先自主完成；不要另发跨机任务或要求用户转述。现有事实不足以推出的运行规则不自行创造。

## 执行方式和下一回传
A/B/C是同一任务连续队列。可按上述顺序执行，每处理一个产品/文档存断点。选择下一有实际收益的未完成项；单项缺合同/读取失败标阻塞后继续其它项。
checkpoint是进度保存点，不是停止点。只有队列在明确范围内全部完成/阻塞、窗口截止、真实错误或必须用户作取舍才退出；禁止仅sleep/改状态假装仍执行。
不需要重写大型通用框架；复用现有Scanner/索引、增加本任务的阶段推进即可。新增执行驱动保存源码/digest并给启动与实际增量证据，不反复重报已审四份源码。
下一checkpoint应包含真实ETF新路径读取结果或明确正在读的片段；INDEX/视图合同实际摘取；至少一批产品映射和规则边内容；随后连续扩大到其它产品/策略/更新。不能再次只交0.5秒回归结果、几个文件mtime和未完成清单。
维护同一correction_0650目录中的总报告/75对象分阶段表/新增发现范围及问题表。附一份隔离候选BLACKBOX运行逻辑说明，按“数据从哪来→各层如何转换→规则入口如何约束查询/策略→更新如何落地”组织，逐条引用证据，未知明示；不创造新业务规则，不写入AGENTS/生产入口。
保持原业务数据/规则/环境/迁移state不变，只写本任务隔离脚本、报告、工作库；不清理、不下载、不接外部API、不执行策略/回测，R9与结案查询不重开。
