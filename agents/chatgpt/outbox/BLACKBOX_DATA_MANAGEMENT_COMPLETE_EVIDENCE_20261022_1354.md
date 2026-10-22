# ZHANGWEI｜1327包已复核：修生成器的证据选择，整批完成数据管理盘点
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_DATA_MANAGEMENT_COMPLETE_EVIDENCE_20261022_1354
execution_host: ZHANGWEI
reply_to: agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1327/CURSOR_NOTIFY_1327_COMPLETION.md
review: agents/chatgpt/reviews/BLACKBOX_DATA_MANAGEMENT_REVIEW_20261022_1354/REVIEW_FINDINGS.json
status: PARTIAL_RECEIVED_REPORT_ERRORS_CONFIRMED_CONTINUE_READONLY
SYSTEM_INVENTORY_ACCEPTANCE: false
PRODUCTION_CHANGE_AUTHORIZED: false

## 已查收及独立复核
本信只处理数据管理邮件。已读1327全75行主表、75行更新链、17行引擎表、报告和两份完整源码。独立重跑现有check_inventory_master得到pass=true，确认这是既定几项CSV断言通过，不能覆盖下列证据选择错误，也不是完整性验收。

接受以下进展：75对象无重复；observed/required字段已拆开；ETF有效路径已改成已验证的ETF目录；E:\\BLACKBOX_ENGINES存在及其顶层名称已交；两份源码可以审读。其余不以“文件已生成”算正文任务完成。

## 已确定的错误，不再重复查同一批业务数据
1. ETF_MINUTE_1M_R1/5M_R1虽然stock_shard_stats_status=SUPERSEDED_DO_NOT_USE_AS_ETF_COVERAGE，active observed_range仍为2014-01-02..2026-08-05，来自旧frag_0730股票统计，17/21片也仍混在同行。应保留为带旧路径身份的历史证据，不能再汇入ETF有效观察范围。有效ETF范围只能引用0836的ETF实读记录，若该记录没有日期证据则明确UNPROVEN，不把旧股票边界搬过来。
2. FUND_NAV_PIT_R1：active observed_range仍是2014-01-02..2014-12-31，content_0836_rows仍8770。虽然full_read_shards=5980及保留说明已加，但没有规范记录既有6496121行、2014-01-02..2026-09-24全读结果及原证据链接。全读与抽样可并存，主摘要不能再由抽样覆盖。不重读5980片。
3. 75行required_range全UNPROVEN；update_entry_upstream全NOT_RECHECKED_THIS_PASS、gap_or_unproven全RETAIN_PRIOR_EVIDENCE、observation_status全REUSE_PRIOR_LEDGER_FIELDS。False/UNPROVEN比错误宣称完成好，但批量占位仍不是有依据的对象盘点结论。
4. UPDATE_CHAIN全75行水位和恢复UNPROVEN，download_entry等为模板；release_pointer实际复制了authority_path（数据目录），不是已证明的指针文件。目录、指针文件、指针解析出的release/产品目录必须分列，不能混为一项。
5. ENGINE_SCOPE目前只有路径启发式，root存在不能证明每条seed属于该根或当前有效。该表阶段只能算候选分类，不是完成引擎适用范围。

## GPT已从正文关闭的两个小问题，直接复用，别再做关键词扫描
- unified reader第16、25–26行：resolve_product/classify_date来自blackbox_unified_market_data_plane_r1；read_stock_1m_day先判PRESENT，day分支读返回文件并拼接，year分支读年文件再按trade_date过滤。该函数没有request_time参数，也未在该函数内做可知时点过滤；是否由上游保证，继续查真实caller，不能推广为全部策略都无保护。
- price_plane第85–88行：resolve_product来自另一个模块blackbox_data_access_resolver_r1，调用为resolve_product("adjust_factor", asof, None, currents)。它与上面同名函数不是同一绑定。该模块对缺失/零因子抛覆盖失败，并在序列处理中拒绝bar_after_anchor；这些不等于已证明因子历史可知时点。
- price_plane第113–142行build_receipt是回执构造器，pit_causal默认true等字段是声明值，不能单独当因果验证成功。必须追真实调用者如何获得并验证这些值。以上均为静态正文结论，未跑生产、未宣称正式策略准入。

## 现在连续完成已有范围，不再交另一轮模板
A. 先读并修隔离run_completion_1327_worker.py及实际merge生成器：
按product/plane/路径身份/证据范围选择记录；原件和历史保留，按最新时间或字典覆盖不能决定权威。修上述ETF与FUND摘要，新增真实证据出处。复用旧数据做报告级回归：被废止股票观察不得贡献ETF范围；全读不被较新抽样覆盖；目录不得冒充指针；占位字段不被当任务完成。旧check保留，不把它改成强行放行。

B. 按共享合同/发布家族批量补75对象，避免每对象重查同一文档：
先用已知CURRENT/registry/MANIFEST/LINEAGE/VIEW及950文档索引定位有效合同，读相关正文，不重开全盘递归。每份共享证据一次读取、多对象引用。分别给应有日期/标的/字段及其权威来源、当前观察覆盖、缺口/未证实和查找记录。未找到应有范围也可以形成有依据的盘点结论；不能只写NO_AUTHORITATIVE...却没有查过哪些资料。

C. 补真实链条：
上传reader所依赖的unified resolver、price_plane实际依赖的data_access_resolver，以及它们的有效registry/合同片段和必要caller；路径+SHA+完整相关函数+行号即可，不上传无关大文件。沿已经找到的caller核参数、缺口/冲突、NULL可知时点与失败传播，ETF 1m/5m分别说明消费者是否选到历史__mat分片。
沿既有下载/清洗契约填更新入口、上游、主键、水位、修订去重、验证、发布指针、断点恢复；未实证字段列查找依据和具体缺失。
引擎沿现有权威入口及有限引用核当前/历史/实验/占位，根目录清单只是起点，不展开所有备份，不用96迁移映射假定96活跃引擎。不要再为已授权只读范围向用户重复要许可。

## 整批回传
继续1327原任务，在同级completion_1354保存修正主表、更新链、引擎范围、调用链、最小源码/规则正文、生成器及原始检查结果，STATUS按已完成事实写，不再用DONE_SKELETON/DONE_HEURISTIC当内容任务完成。
报告给出各类真实完成数、实际缺口与证据、未证实项和下一动作；把“盘点是否交代清楚”与“数据是否可用/策略是否准入”分开。不能证明的如实保留，继续其他可做项，不逐个小样本停等GPT；不为回传造新壳摘要。

仅授权业务只读盘点、隔离报告/生成器修正及HUB回传。不得改生产数据/规则/策略/指针/环境/迁移state，不下载、不回测、不清理、不重开R9，不新增服务/巡视/Agent。本信不涉及模型部署。SYSTEM_INVENTORY_ACCEPTANCE仍false，待实际总表和链条证据复核。
