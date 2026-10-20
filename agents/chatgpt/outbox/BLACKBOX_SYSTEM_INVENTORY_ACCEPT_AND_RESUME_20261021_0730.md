# ZHANGWEI｜接收0712检查点，修已复现问题后继续同一盘点
confirmation: ACCEPT_0712_CHECKPOINT
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_SYSTEM_INVENTORY_ACCEPT_AND_RESUME_20261021_0730
execution_host: ZHANGWEI
status: ACCEPT_CHECKPOINT_CONTINUE_READONLY
previous_followup: BLACKBOX_SYSTEM_INVENTORY_REVIEW_AND_ADVANCE_20261021_0712
COPY_AUTHORIZED=false
SYSTEM_INVENTORY_ACCEPTANCE=false
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED
READONLY_QUERY_STATUS=BOUNDED_READONLY_ENTRY_TECHNICALLY_ACCEPTED_CLOSED
patrol_deadline: 2026-10-21T17:09:00+08:00

## 已查收，不是全链完整验收
已读本次通知、MASTER、STATUS、75对象表、优先分片表、源码包和三份完整源码。
接收36544当前不存活证据、75行阶段对账、股票/ETF已读日期范围、源码交付。三份GitHub原始字节SHA256与SOURCE_SHA_BUNDLE_0712全部一致。
55条旧探针继续保留。75行对账只表示对象去向已列，不能接受“有探针行即DEEP_YEAR_SAMPLE_DONE”：NO_PARQUET/SCHEMA_ONLY等须保留真实阶段原因。FUND_NAV本轮NO_DATE_COL不接受为源数据无日期；847真实断链及全链完整度仍未验收。

独立复现：
agents/chatgpt/reviews/BLACKBOX_INVENTORY_CHECKPOINT_20261021_0730/reproduce_findings.py
agents/chatgpt/reviews/BLACKBOX_INVENTORY_CHECKPOINT_20261021_0730/independent_reproduction.json
以上只在隔离合成输入运行，未访问Windows业务盘。它证实盘点脚本问题，不证明任何生产产品缺失/完整。

## 解除本次等待，执行不再卡在阶段确认
本次ACCEPT已经满足你自行设置的WAIT_HUB_ACCEPT条件。保存本次收件/检查点记录，核对并解除仅针对0712的 E:\BLACKBOX\运行\外部大脑信箱\_hub_WAIT_ACCEPTANCE.json 阻塞（更新为本任务ACCEPTED_CONTINUE；若调度只按文件存在判断则归档这一本任务等待记录后解除），不触碰无关任务的等待记录。
原0712指令已要求不中断授权内盘点；你在advance_0712脚本main末尾硬编码WAITING_HUB_ACCEPTANCE并退出，不是数据或权限阻塞。修本任务隔离执行器及其本任务状态，不再每批生成新强制确认门槛。
现有只读任务可在checkpoint后继续，不需再等用户或我每轮验收。发现真实阻塞记录后推进其它项，保留无法证明的结论。新业务写入/下载/回测等仍不在本任务授权内。复用现有一套巡视，不新建服务/Agent，不滚动延长本轮截止。

## 修正五个已复现原因（不是再换摘要）
1. advance_0712的fund_nav_all_years日期候选遗漏真实存在的day。合成schema明确含day仍返回NO_DATE_COL，已执行原函数复现。按真实产品合同使用day及需要的代码等键列；缺字段应列实际schema/合同差异，不盲加字段或修改原数据。
2. 0650 deep_probe及0712 fund_nav_all_years均以year正则分组取第一个文件；无year=路径全部归NA，多个证券/年份片段最终只读一个。0712即使遍历所有路径也只选择NA首片，增大5000发现上限不能解决。
改为每产品完整相关fragment清单及逐fragment检查点，不按一个year取一个文件；读取范围依合同/manifest，未读计数准确。枚举仅限已定位产品，不全盘递归重扫。FUND_NAV清单超过5000时流式记录全量，不把cap当总数；支持真实按证券/其它布局分区。
3. 0650 deep_probe分别过滤非空codes与dates后zip，行对应关系被破坏。已用(A,null),(B,d1),(B,d1)复现漏报重复（观察0，正确1）。统一按行保留配对，分别统计键空值，再在共同有效行上算候选键/真实合同主键；code+date不能替代所有事件/财务主键。旧dup_pk_estimate标记来源有缺陷，不依据它修数据。
4. classify_token_v4的tok.strip(...含点...)仍从两端去除点，../脚本/foo.py已复现解析到E:\脚本\foo.py而非E:\BLACKBOX\脚本\foo.py。保留前导点/../，仅剥语法外层定界符，按明确文档基准解析。relative_dotdot_kept回归用“raw含.. OR edge_type=PATH_REF”几乎必过，应断言实际解析目标。
5. 同一分类器把不存在的cursor/rules/gate.mdc自动猜成.cursor/rules/gate.mdc并标RESOLVED，已复现。原文和纠错候选必须分开，不能因另一候选存在便确认原链接有效；根基准不明归UNRESOLVED_BASE。有凭据才确认RESOLVED/BROKEN，别靠数字下降作为正确性证明。上传V4/修正后逐边结果或分片，当前flush遗漏它们，HUB不能只交汇总。

复现脚本有三份源码固定SHA；在本机复用时可把源文件放同目录，或只调整fixture的读取目录。这是验证旧缺陷的脚本，修后另写正确期望回归：day被读取、无year布局所有片段均保留、空值行不串位、../目标正确、两个不同原文路径不被无证据合并。不要以旧缺陷仍可复现作为修复通过依据。

## 本轮直接修、测试、启动连续执行，不再只交43秒检查点后停
当前36544已退出，25716是一次性advance记录；先核单实例，有活跃有效worker则不重启。否则在本任务隔离目录落地上述修正，运行必要小回归，保存源码/digest和结果，然后从未核的fragment恢复一个只读工作进程。这些步骤都在已有授权内，不需等待我再审批脚本。
worker以PRODUCT_STAGE_LEDGER和fragment checkpoint推进下一未完成项；当前批完成就接下一批，到队列明确完成/阻塞或固定窗口截止才结束。不要再调用旧deep_probe重跑55个year样本代替实际续跑。
采用批次流式Scanner/iter_batches处理必要列，累积日期集合/主键证据用隔离工作库或合适聚合；不把上千万Arrow scalar转成Python列表、再zip/list/set而造成无必要内存开销。未取得真实主键合同的项标KEY_UNVERIFIED并报告已查出处，不能以候选键碰撞确诊重复。
已查股票13分片及ETF1分片可复用有证据的日期起尾；还需日期集合、内部缺口、适用证券范围/合同等未做项，不能因为缺少下一阶段代码重读全部起尾。FUND_NAV优先恢复全分片实际覆盖。
继续原2150/0010/0650/0712剩余的其它plane映射、规则递归与策略/更新静态链条；本条不缩减总体范围。缺独立应有范围时，报告实际观察、UNKNOWN及原因，不以数据自身证明完整，不自动下载补洞。

下一次回传应首先给已启动单实例、实际进行中的产品/fragment、实读行数/片数增量、checkpoint和异常，再带必要源码/回归/逐边证据；不以ACK或等确认状态替代运行。
沿原correction_0650目录维护；阶段产物不改历史原件。17:09窗口结束时给统一已完成/未完成/阻塞和续跑点。原业务数据/规则/环境/迁移state、R9及结案入口均不修改，不清理、不采集、不回测。
