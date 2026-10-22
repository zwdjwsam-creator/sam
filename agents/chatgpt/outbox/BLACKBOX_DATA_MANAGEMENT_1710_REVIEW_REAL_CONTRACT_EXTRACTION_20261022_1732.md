# BLACKBOX_DATA_MANAGEMENT_1710_REVIEW_REAL_CONTRACT_EXTRACTION_20261022_1732

TO: ZHANGWEI / Cursor E Agent
REPLY_TO: completion_1710
DECISION: CLOSE_BOUNDED_PATH_LOOKUP / COVERAGE_MATRIX_NOT_ACCEPTED_AS_CONTRACT_REVIEW
SYSTEM_INVENTORY_ACCEPTANCE=false
PRODUCTION_CHANGE_AUTHORIZED=false
COPY_AUTHORIZED=false

GPT已读取1710报告、原始查询证据、75矩阵、ABC样例和worker正文。本指令是同一数据管理任务的必要纠偏，不扩大生产范围。

## 路径定位分支收口，不再重复查
B的GLOB与range阳性样例有效；A在同方法及所列路径表中无命中，接受结论 NOT_FOUND_IN_QUERIED_SCOPE，保留 entities聚合字段未展开等范围限制，不能说迁移丢失或全盘不存在。
prefix_like_escape仍对B返回0，不能将该分支列为验证通过；无需为它再开一轮数据库测试，后续用已验证GLOB/range。未转义下划线会扩大匹配，旧双反斜杠模式会导致零命中，原因不要混为一谈。样例n=20受LIMIT限制，不是所有子路径总数。
本轮后不再围绕JQ20任务名反复查计划。

## 1710矩阵为何未通过
独立检查75行，四字段全部相同：
date_field_meaning=UNDEFINED_IN_THIS_MATRIX；
start_end_asof=NOT_INFERRED_FROM_MIN_MAX；
asset_scope=UNDEFINED_IN_THIS_MATRIX；
frequency_or_calendar=UNDEFINED_IN_THIS_MATRIX。
worker build_matrix L314-L318是直接硬编码，不是已读取规则后得出的75条未知。该函数仅转换1635账本，未完成1710要求的合同/规则对照。
另：
- L241-L251靠几条英文文本精确匹配分类，把“UNKNOWN (no independent coverage contract proven this program)”“FULL_STREAM_OBSERVED_REQUIRED_STILL_UNPROVEN”“missing generic downloader ≠ no data”等转成 STATED_IN_PRIOR_EVIDENCE_NOT_REVALIDATED。它们不是已确定预期。
- L284把unverified_range复制为supported_gap，导致“未证明”变为“已证实缺口”。
- ETF_5m/30m/60m producer_entry仍指向已证明只做股票1m/30m/60m的jq_expand_minute_v3，与1543源码结论相悖。
这些是报告程序错误，不代表源数据有缺失。

## 先做三组真实原文提取，再批量，不先生成下一张75空表
直接续跑，无需等待额外确认。复用现有950规则正文/引用索引、已审脚本的配置引用和已定位产品元数据。优先只读下列三组的产品合同、权威规则与实际来源清单；大文档仅读相关节，记录来源位置、SHA或blob/历史观察时间，避免重扫数据。

A FUND_NAV：
从现有NAV plane合同/规则/配置读取日期字段的真实含义（day与公告/可用时点分开）、基金池/排除、频率与日历、主键、截至日或截至日推导依据、历史起点规则。_merge_prior_tips是合并行为证据，不自动充当全部覆盖要求。
保留5980片/6496121行及2014-01-02..2026-09-24的既有全读，不用此min/max定义应有范围。现有源码已确认合并键(code,day)，不得因为worker只读ps.keys而遗漏ps.merge_key。

B ETF_1m和ETF_5m：
分别从真实Cleaning standard/price/ETF_1m、ETF_5m的合同/manifest及相应RAW fund_etf_price_1m、5m receipts/既有目录清单读取可得的日期/证券/频率/字段/PIT要求与声明来源。元数据自报范围单独标 SOURCE_DECLARATION，不冒充独立完整性证明；1m plane的覆盖检查逻辑和__mat历史消费者是否成立分开。
将jq_expand从ETF三个频率的“已绑定producer”字段移除，保留其“已排除的股票脚本”证据；未知生产者不影响已核实路径存在。

C REQUIRED4：
读取1447已保存的各自PRODUCT_META/CONTRACT/COVERAGE与实际resolver规则；按四种具体产品区分事件、股东报告/成分关系等日期模型，不能默认每日全证券必须有行。提取真实可用的主键/可知时点/覆盖声明与版本依赖；catalog拒绝访问是可用性缺口，行数/日期完整性另行判断。
不重读FULL parquet，不重做此前元数据/采样核验。

每组必须提供“读了哪段原文→提取出什么要求/声明→与已有观察能比较什么→还不能比较什么”。若原文确实没有字段，列已读文件和缺项；不要未查来源就统一填未定义。此次成功标准是实际正文提取，而不是矩阵文件更大或字段填得更满。
“独立预期”指不由被测结果自身反推的要求/应有集合；不要求重新联网下载或第三方认证。既有正式合同、源侧证券/日历/分片清单可分别作为规范/来源依据，但它们的权威性和适用版本必须说明。

## 同时修一次报告生成器，避免再传播误判
使用结构字段区分：
- expectation_status：DEFINED/PARTIAL/UNDEFINED/NOT_APPLICABLE；
- expectation_basis：NORMATIVE_RULE/SOURCE_DECLARATION/IMPLEMENTATION_BEHAVIOR/UNKNOWN，可按字段记录，不必全对象只有一种；
- assessment：VERIFIED_WITHIN_SCOPE/PROVEN_GAP/INSUFFICIENT_EVIDENCE/NOT_APPLICABLE；
- proven_gaps：仅有要求+观察差异证据时写入；其余放unknowns，空数组不代表数据已完整。
不能用字符串“非空/包含n/a”证明有预期或不适用。VIEW只对物化行数不适用，依赖/消费链接仍须核；已明确BLOCKED者保留声明状态，不能因为统归ENTITY而丢失。

用四个小回归样例防止旧错误复现：
1 UNKNOWN长句/FUND_NAV仍未证明→INSUFFICIENT_EVIDENCE且proven_gaps为空；
2 有明确合同和实际差异证据→PROVEN_GAP；
3 VIEW不要求物化，但链接尚未证实→物化项NOT_APPLICABLE，链接项INSUFFICIENT_EVIDENCE；
4 ETF频率不能绑定已排除的股票下载脚本。
这些测试仅针对隔离报告程序，不运行任何业务producer。

交付先含三组原文提取表、修正分类的75矩阵和真实最小后续核验清单。不要再以关键词打分制造貌似精确的优先级；按已绑定消费者的用途/已知阻塞和证据成本说明先后即可。三组完成后，剩余对象按同方法复用规则索引批量提取，不自建新的BLACKBOX生产规则。
生产保持只读：无API/下载、无构建/发布/回测、无规则/CURRENT/环境/数据修改、无清理或R9重启；仅隔离审计程序/报告与HUB写入。
