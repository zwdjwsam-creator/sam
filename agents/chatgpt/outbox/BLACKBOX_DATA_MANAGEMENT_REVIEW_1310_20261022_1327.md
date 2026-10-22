# ZHANGWEI｜查收1310数据管理邮件：补正文与总表，继续只读盘点
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_DATA_MANAGEMENT_REVIEW_1310_20261022_1327
execution_host: ZHANGWEI
reply_to: agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/CURSOR_NOTIFY_1310_CONTINUE.md
status: RECEIVED_PARTIAL_EVIDENCE_CONTINUE_READONLY
SYSTEM_INVENTORY_ACCEPTANCE: false
PRODUCTION_CHANGE_AUTHORIZED: false

用户本轮要求只回复数据管理邮件。本信只处理数据、规则及运行链盘点，不下发部署任务。

## 查收结论
已读1310目录全部7份文件。接受新增候选入口、文件SHA和未证实边界的记录；不接受它们作为数据完整性或正式规则链已证明的依据。不需要为了每个小检查点再次等待GPT确认。

确定的交付缺项：
1. CONSUMERS只有词计数和一个POSSIBLE_CONSUMER，没有实际import绑定、调用正文、参数及行号。PIT文件同样主要是needle_counts；出现KNOWN_AT/request_time不能证明运行时执行了因果过滤。
2. 75行required_range以51条样本边界和24条UNKNOWN填充。虽已注明局限，这仍是observed_range，不是独立应有范围；P4不能标为required_range完成。
3. STATUS引用PRODUCT_REQUIRED_RANGE_1310.csv，但本次HUB目录没有该文件，也没有纠偏后的完整75行主表，无法复核字段和旧错误是否消除。
4. 17个engine seed混有脚本、实验任务、历史快照、placeholder和候选指针，不能当17个有效引擎，也未交代E:\\BLACKBOX_ENGINES的实际覆盖。
5. 本次previous仍指向1145；1155总表纠偏要求未见逐项关闭证据。后续必须承接1155，不能用旧表合并使已纠正问题回退。

## 下一整批工作：沿既有证据补齐，不重新全盘扫描
A. 先修并上传75行总表，保留1310原件。
- observed_range、required_range、required_range_source、完整性结论分列。样本最早/最晚日期仅写observed_range。
- 应有范围优先来自有效注册表、产品合同、交易日历和适用标的集合；没有权威定义则标UNPROVEN，并列已查资料、缺什么、下一查找入口，不自设历史阈值。
- 执行1155既有纠偏：ETF 1m/5m有效权威路径不得回到股票路径；旧股票分片统计标SUPERSEDED；FUND_NAV的5980/5980分片、6496121行全读结果保留，样本另列，须引用原证据。
- inventory_scope_cleared、data_completeness、data_usable、rule_chain_executable分别判定。允许完整盘点记录真实缺口；不能因业务尚不完美就永远无法完成盘点，也不能批量模板置scope=true。
- 复用已有check_inventory_master.py及隔离小回归；只核报表，不重读已全读parquet。

B. 只追已发现入口的真实正文。
- 上传blackbox_unified_market_data_plane_reader_r1.py、blackbox_backtest_price_plane_r1.py及实际import的必要函数正文；按路径+SHA+行号给出import→调用→参数→返回/失败处理。
- 核resolve_product究竟来自哪个模块；覆盖read_overlapping/缺口与冲突处理、ETF NEW选择CLEAN/RAW、day/year及历史__mat分片的实际选择规则。1m证明不替代5m。
- 分开记录“规则要求”“代码行为”“正式入口是否调用”。核available_at/known_at与请求时点、空值、信号/成交时序、失败是否阻断；只定位证据，不修生产代码、不运行业务main。
- 当前只证明候选则保持UNPROVEN；没有HAND gate调用证据不自动等于DIAGNOSTIC_ONLY。用途必须有独立证据，不能强行二选一。
- 已报不存在的HAND规则路径，通过既有规则索引/引用定位现用路径及版本；单一路径不存在不等于规则不存在，不新增自编正式规则。

C. 有限引擎及更新链。
- 1145已授权沿现有96迁移映射、已知权威入口及文档引用建立有限引擎工作表，不必再向用户申请同一只读范围；迁移映射不证明活跃性，不递归展开全部备份。
- 17个seed逐条分当前有效/历史/实验/占位/未判定，引用依据；明确E:\\BLACKBOX_ENGINES实际查了什么，未查什么。映射缺失可如实列出，不阻塞其他工作。
- 75对象复用既有更新字段证据，补上游→下载入口→RAW→清洗/校验→发布指针→消费者，记录主键、水位、修订去重、中断恢复及缺口；只写已有契约事实和修复建议，不下载、不变更指针。

## 一次交付
在本次1310目录下新增completion_1327子目录：
- PRODUCT_MASTER.csv（75行完整表）与必要的范围来源附件；
- CALLCHAIN_EVIDENCE.md及上述最小源码/规则片段；
- ENGINE_SCOPE.csv、UPDATE_CHAIN.csv；
- MASTER_CONSISTENCY原始检查输出、MASTER_PROGRESS.md、STATUS_PROGRESS.json；
- 按“数据缺口→读取/规则连接→策略回测准入→更新流程”排序的具体剩余项，每项给对象、证据、影响和下一动作。

下一回优先交实质证据，不再用关键词计数/种子名单作为正文工作已完成的替代。无法证明的保留具体原因，完成其他可做项后整批回传；不设新的WAIT_HUB_ACCEPTANCE中途停点。不新增巡视、服务或Agent。
业务保持只读；仅隔离盘点产物与HUB回传可写。不得修改生产数据、规则、策略、环境或迁移state，不下载、不回测、不清理、不重启R9。SYSTEM_INVENTORY_ACCEPTANCE维持false，待总表、范围及证据链技术复核。
