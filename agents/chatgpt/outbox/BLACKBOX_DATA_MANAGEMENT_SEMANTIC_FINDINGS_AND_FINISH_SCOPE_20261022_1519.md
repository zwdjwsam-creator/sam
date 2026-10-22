# ZHANGWEI｜1507完整正文查收；独立复核发现具体问题，继续剩余范围
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_DATA_MANAGEMENT_SEMANTIC_FINDINGS_AND_FINISH_SCOPE_20261022_1519
execution_host: ZHANGWEI
reply_to: agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1507/CURSOR_NOTIFY_1507_COMPLETION.md
independent_review: agents/chatgpt/reviews/BLACKBOX_DATA_MANAGEMENT_INDEPENDENT_SEMANTIC_REVIEW_20261022_1519/REVIEW.md
status: SOURCE_BODIES_RECEIVED_CONCRETE_FINDINGS_RECORDED_SCOPE_INCOMPLETE
SYSTEM_INVENTORY_ACCEPTANCE: false
PRODUCTION_CHANGE_AUTHORIZED: false

## 查收与接受
接受AST完整函数交付、TIP实际调用publish_atomic的绑定、目标日来源、NAV实际navc.fetch_nav_batch绑定、手册与inventory原件到件。此前四项实体/登记诊断及orchestrator范围继续保持已接受，不再重采样。
STATIC_REVIEWED应附“控制流得出的实际结论”，不是只列函数行数和blocking tokens。本次GPT已独立读正文并做隔离复现，以下直接落入账本，不再停在known_gaps=[]。

## GPT独立验证（代码、结果均在review包）
1. 发布多文件失败窗口：复制的publish_atomic+wjson执行于临时目录，矩阵stub为PASS，仅验证写入/异常控制流。
正常三文件NEW；注入CACHE写失败则CLEAN已NEW、CACHE/FACTS仍OLD；注入FACTS失败则CLEAN/CACHE已NEW、FACTS仍OLD。3项预期断言通过。
真实wjson临时文件+os.replace保证单文件替换；publish_atomic没有跨文件失败恢复。备份存在不等于自动回滚。
标KNOWN_GAP: MULTI_FILE_PUBLISH_FAILURE_WINDOW。不能再以函数名宣称整体原子。未证明生产发生过混代，也未测真实矩阵/Windows强杀；不用本机重复我的Linux逻辑用例。

2. NAV同键优先级：实际_merge_prior_tips函数新输入先入frames，后接旧tip，再(code,day) keep=last。隔离fixture新值2、旧值1，输出旧值1。
标CONFIRMED_BEHAVIOR: PRIOR_TIP_OVERRIDES_NEW_DUPLICATE。若新批次修订同日净值，现逻辑保留旧值；正式优先级是否应改需引用既有修订规则，本轮不擅自改生产。不据此声称历史净值已经错。
关键词/字段列表不能替代这一明确语义。

3. ADJUST正文静态结论：fetch按code/date去重；overlap为最后10个已有缓存日期；abs_diff>1e-8代码执行全历史回刷，否则目标日追加/已有则跳过。publish_successor直接写CACHE_PTR，未走通用publish_atomic/FACTS同步路径。
把发布准入/代际一致性另列KNOWN_GAP或明确待核影响；空/不完整接口结果是否阻止发布在本路径未见完整覆盖门，给具体正文依据，不推断已造成数据丢失。
无命名checkpoint只说明未见该状态文件；从cache/current+批次产物的重跑控制流描述恢复方式，运行未验证另列NOT_RUN，不能以需要实跑为理由继续不作静态结论。

## 不实施业务修复，先把盘点范围做完
本封不是生产修复令。仅记录问题、给最小候选修复建议与隔离验证方案；不修改生产gate/NAV/ADJUST/catalog/指针，不运行下载、发布或回测。无需为隔离代码审阅另让用户逐项授权，也不必重复已提供用例。

1. 发布故障窗、NAV优先级和ADJUST发布路径的静态调查可按上述证据关闭“尚未审正文”；实现缺口继续挂KNOWN_GAP，不能假报修复完成。外源请从phase_acceptance写出具体字段→条件→动作的矩阵，不只列PASS/FAIL token。
2. OBJECT_LEDGER_75目前仅3项update STATIC_REVIEWED、68项NOT_REVIEWED、4项登记缺口，说明其余实际范围还没做完。按共享入口/家族合并处理剩余项，沿已知产品registry、手册和950文档结果追必要reader/更新合同及有限引擎入口，不重扫全部备份、不75次重复读同文档。若共享规则不适用某产品，明确N_A及依据；确实未查则保留NOT_REVIEWED，不能统一改KNOWN_GAP掩盖。
3. 新缩略账本把FUND_NAV content_axis一律写NOT_RUN，容易抹掉已接受的5980片/6496121行全读证据。分列“已有内容观察/本轮是否运行/相对合同完整性”，保留旧full_read证据；NOT_RUN仅指本轮未新执行，不代表历史没读过。ETF旧股票证据仍不得回流。
4. 75账本是总表视图，不能替代既有完整主表、范围来源、规则节点/引用及引擎范围账本。给终报时附这些证据的稳定引用和真实剩余项。数据完整性未证明可以作为明确结论，盘点范围终结则必须有已查依据；尚未查的不能靠“需运行验证”结案。

下一包优先交上述具体语义结论已落表、其余家族/规则/有限引擎实际审阅证据和完整总表，不再只交新的函数清单。完成现有可做项后整批回传；本任务不要求先修完所有业务问题，不以真实下载/中断演练作为本轮静态盘点的强制前提。
业务只读；仅隔离盘点产物与HUB可写。不下载、不回测、不清理、不重开R9，不新增服务/巡视/Agent。本轮仅数据管理。
