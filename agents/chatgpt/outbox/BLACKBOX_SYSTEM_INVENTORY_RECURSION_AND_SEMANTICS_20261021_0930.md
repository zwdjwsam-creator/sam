# ZHANGWEI｜接收0905来源证据，完成真正递归与依赖语义核查
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_SYSTEM_INVENTORY_RECURSION_AND_SEMANTICS_20261021_0930
execution_host: ZHANGWEI
status: CONTINUE_SAME_READONLY_QUEUE
previous_followup: BLACKBOX_SYSTEM_INVENTORY_LINEAGE_AND_RULE_GRAPH_20261021_0905
SYSTEM_INVENTORY_ACCEPTANCE=false
COPY_AUTHORIZED=false
patrol_deadline: 2026-10-21T17:09:00+08:00
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED
READONLY_QUERY_STATUS=BOUNDED_READONLY_ENTRY_TECHNICALLY_ACCEPTED_CLOSED

已完整读0905血缘、规则汇总与2327条原始引用记录、ETF消费者调查、0836/0905两份源码，SHA均匹配。
接收有明确来源的注册依赖/RAW-CLEAN/VIEW关系和实际正文引用记录，当前有实质增量；保留成果。
独立复核：agents/chatgpt/reviews/BLACKBOX_LINEAGE_REVIEW_20261021_0930/REVIEW_FINDINGS.json。
不暂停活跃有效工作，不重读全套已验起尾；以下直接融入同一队列继续，无需等批准。

## 一次修准计数与递归，不再重复上一层发现
1. 2327原始记录的状态确实为2018 resolved/269 broken/13 legacy/23 dynamic/4 external。
按(src,line,raw_token,resolved)去重后1846，481条为backtick/pathish等重复命中；同时保留原始提取数和去重引用数，不把重复当新连接。
NODE_NO_TOKEN=127是节点计数，另表列出，不能混进边状态总数。RESOLVED先解释为“路径存在/引用已定位”，不是规则语义适用或执行通过。

2. phase_rule_true_edges当前“recurse”只visited_extra.add(res)，没有将目标加入待处理队列、也没有读它正文；extra_targets_visited=495应叫targets_discovered，不能报告递归已完成。
改本任务隔离函数为真实工作表/队列：
- 用315种子初始化pending，按规范路径+适用版本记录身份；
- 取一个未读文件，严格解码读正文，保存read状态及内容摘要/hash；
- 解析真实引用，保存来源/定位/原文；将属于规则/文档范围且未排队/未读的目标追加pending；
- 标记该源已读并checkpoint，然后取下一项；visited用于去重，不能替代读取。
记录discovered/queued/read/failed/excluded/pending，遇环终止重复路径；被引用数据parquet/可执行程序不作为规则正文执行，目录先按已知入口/索引处理，不全盘递归。
按规则索引及JSON rule_id等显式字段建立ID→文件表，把裸规则ID纳入引用解析；当前extract_tokens只接收带斜杠/后缀的token，遗漏BACKTEST_MANDATORY_PRECHECK_R1这类ID。普通状态码/公式另列。
当前315种子与8097候选分母继续对账，不以发现495目标当查完其它候选。

3. 269 broken还含命令示例：
AGENTS第26行“E:\BLACKBOX\.venv\Scripts\python.exe -u ...py”被整个当一个文件；第37/41等含python、--mode、参数枚举也如此。
命令示例本身记COMMAND_EXAMPLE_STATIC，静态提取明确可执行/脚本/配置引用再核路径，绝不执行命令。Markdown显示标签不等于链接目标，先解析真正href及其基准；MIGRATION_HISTORY_INDEX.md等无明确基准时标UNRESOLVED_BASE，不臆测根。
规则正文现在errors=replace须改严格解码并记录编码失败；不根据替换字符确认断链。修正这些实际反例的回归，重用已读正文缓存避免为解析变化重读原盘大包。
输出真实去重边+未解析/失败清单。269仍是待分类候选，不能拿来批量修原规则。

## 血缘169先按语义整理，再连接消费者
这169目前是“提取的字段记录”，不是169条全部已证明依赖：
- 至少8个dst为list/dict/NoneType等Python类型名，属于未展开结构，不是目标实体；
- source_latest_asof日期、transform表达式、transform_version是覆盖/变换元数据；
- registry明确from/to、source_dataset、clean_path、VIEW union等才可按其语义建边。
保留全部原值，将覆盖/版本/变换属性与实体依赖分列；复杂对象递归展开真实目标或保留UNRESOLVED_STRUCTURE，不造“list”节点。
边明确方向与关系（输入→产物、consumer consumes 产品、view unions 基础表），产品/文件/版本等实体有类型；PATH_EXISTS不等于DEPENDENCY_USABLE。
逐个产品汇总“已声明上游/已观察存储/已核覆盖/使用入口/未知项”，专用sidecar/registry沿真实权威继续，不又回主cache拼目录。
先把注册表已能确定的整批边规范化，再沿真实引用读consumer配置/入口；不要因字段计数增加就停止。

## ETF历史消费者：改成沿调用链定位，而非只搜字面__mat
HISTORY_CONSUMER_LINK_UNPROVEN是合适当前结论，保留，不推断成不存在或需重下载。
当前搜索只收__mat_或同文件同时含ETF_1m+year_batch；通用registry驱动读取器可能都不含这些字面量。
从unified registry读取代码/适配器/相关现行调用者出发，搜索relative_under_standard、RAW_REPLACEMENT、year_batch_regex的实际读取位置，静态追到路径构造和fragment选择逻辑；记录已查文件/函数/行及未接上的调用点。如果仍找不到，列阻塞与范围，继续其它产品/策略/更新，不重复同样窄搜索。
.__mat历史、RAW替代、TIP覆盖与重叠优先级必须有现行消费者/合同依据，不自行把旁边目录合并成新权威。未证实时保持完整历史查询不可宣称可用。
原脚本目录里已知2字节旧模块不是当前可执行入口证据；本轮只读调查，不改已结案查询或新建生产loader。

## 本轮的工作终点是实际推进，不是再次列同一not_done
上述规则工作表推进后，接着完成原总任务的策略实例/更新类静态链、适用应有范围/日期缺口与依赖问题表，不得永久只做报表口径。
只对有独立合同且已确定使用范围的数据继续关键列核查；保留采样/未知，不能自证完整。原业务不修、不下载、不跑回测。

下一次回传优先交：
- 规则真正递归已读/新增待读/未解析数量及真实多跳样例，去重边和候选断链分类；
- 规范化实体依赖与属性数量、已经连接的真实consumer/策略或更新入口；
- ETF通用读取调用链的发现或明确已查阻塞；
- 当前正在处理项、实际日志/进程或真实退出、checkpoint及剩余范围。
不要只交0.4秒同摘要，或用HUB轮询证明本地工作持续。数据读数无变化的引用旧证据即可。
同一任务checkpoint后继续，17:09固定截止；仅范围明确完成/阻塞、真实错误或截止才结束，不新建WAIT/服务/Agent，不延长窗口。新增本任务实现源码上传便于核查。
边界不变：只读业务，只写隔离盘点脚本/报告/工作库；不改原规则/数据/环境/迁移state，不清理/采集/下载/策略/回测；R9与已结案查询不重开。
