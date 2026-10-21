# ZHANGWEI｜1136源码已复核，沿真实消费者和引擎范围完成统一盘点
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_SYSTEM_INVENTORY_CONTRACT_AND_SCOPE_20261021_1145
previous_followup: BLACKBOX_SYSTEM_INVENTORY_CONTENT_BATCH_20261021_1136
execution_host: ZHANGWEI
status: CONTINUE_AUTHORIZED_CONTENT_INVENTORY
SYSTEM_INVENTORY_ACCEPTANCE=false
COPY_AUTHORIZED=false
patrol_deadline: 2026-10-21T17:09:00+08:00
review: agents/chatgpt/reviews/BLACKBOX_CONTENT_CONTRACT_REVIEW_20261021_1145/REVIEW.md
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED

## 查收与复核
已查收1136源码与静态内容。两源码完整SHA一致，不再重复上传/重hash。
GPT对原函数正文做12项隔离探针，代码及结果在review目录。断言PASS是复现实际边界，不是生产通过；不需要本机为了取得新指令重复跑这12项或重新读950文档。真实Arrow/Windows/生产NOT_RUN已明确。
下列边界已经可复现，不再只列“待安全fixture”：
- unified空/坏sidecar可扩成全年并报PRESENT/READY=YES，尚无实际行证明；
- 有CLEANING年分片时RAW其它年份可能未发现；
- ETF默认NEW读取CLEANING，RAW列入manifest并不形成自动fallback；
- 部分窗口仅TIP返回仍DEDUPE_QA=PASS；冲突键被剔除并FAIL_CLOSED，未体现统一解析器day>year优先级；
- anti_lookahead_test无request_time参数，NaT可PASS；不构成真正请求时点过滤证明。
这些不是数据丢失/策略前视已发生的结论。保留原代码，先追真实caller和契约。

## 继续当前有效工作，不另启重复作业
A. 完成真实调用与准入边界：
- 静态查找实际import/调用 read_overlapping、overlapping_shards、coverage_window/list_files_for_window 的当前入口，引用函数正文、参数默认/覆盖、去重失败及缺口处理。若仅任务诊断脚本使用，明确它不是已证实的正式策略读取入口。
- 核真实策略/回测层如何执行 available_at<=request_time、bar时间约定、NULL可知时点、回测成交时序/成本/停牌等已有规则；沿已发现入口查，不从读函数名推断。缺caller就UNPROVEN，未见不能写“所有策略无防护”。
- ETF_5m先核已有unified注册和实际caller。没有专用5m文件不等于没有通用消费者；1m行为也不能替代5m。.__mat范围结论限制为已审两模块，不推广全系统。
- 补记ETF CLI实有--build-manifest/--coverage/--regression，main会写运行manifest与QA；1136空cli_modes应纠正。继续不运行原业务CLI。
- 既有静态证据足够的不用再读parquet；若必要短窗真实样本，仍仅无写函数、少量标的/日期，并记录实际文件/行/局限，不借此全历史读取。

B. 补齐引擎及规则适用范围，不重做950：
- 36082排除样例中E:\BLACKBOX_ENGINES是迁移系统的一部分。1118原ROOT限制是本工作表边界，不是全系统范围定义。保留旧worklist，不原地改policy重跑。
- 用既有96 engine映射/当前权威入口/950文档的实际引用，建立有限的引擎侧种子及完整待办；先判当前有效、历史备份/实验、路径别名或未能判定，再读有效规则/入口正文及必要引用。不得一把递归展开所有备份/快照。引擎登记数量≠全部都活跃；不能用迁移映射代替业务权威。
- 输出范围账本：原ROOT工作表、引擎侧工作表、任务报告镜像排除、其他目录/类型排除分别什么依据、多少去重目标、多少已核、未核与理由。若没有96映射可用，记录实际查过的已知入口和缺项，不全盘另扫/虚构数量。
- 复用node_results全量950的轻量JSON聚合而非只抽200，区分路径引用/标识符候选/已核正文规则。输出明确适用产品/策略/运行阶段与优先级、冲突/废止和来源；未核部分如实保留。
- 去重0930语义边重复11项，读取现存小报表即可，不重读数据。形成权威入口→数据→PIT→策略/回测约束→输出记忆→更新恢复的实际证据链；文档要求与代码行为分别列。

C. 交付一张覆盖既有范围的总表，而非又一个8行种子：
- 以原75对象映射为基础合并RAW/CLEAN/CACHE/VIEW/CONSUMER/ENGINE的已知范围，保留对象类型与映射，避免把8产品的minute注册表当全库范围。
- 逐对象填已观察/已全读/仅抽样/未观察、独立应有范围与来源、消费者/准入、数据缺口或未证实、更新入口/上游、键/水位/修订去重/中断恢复。未知须列查找过的权威资料与具体缺的证据，不能只批量填UNKNOWN。不重新读取已有全读分片。
- 把“盘点范围已交代清楚”“数据可用”“规则链可执行”分开。盘点可以得出某对象存在缺口；不要求本轮修完业务缺口才能形成盘点终报。当前整体仍false是范围/证据交付尚不齐，不是要求所有产品必须无缺口。
- 最终应能给用户明确下一阶段优先级：先哪些数据/读取问题、再哪些规则连接问题、何时允许策略回测、更新作业如何按已有契约执行；当前只给修复建议，不实施生产变更。

## 状态与整批交付
STATUS_PROGRESS仍为09:31旧内容，需更新真实阶段并保留历史版本。巡视旧worker_phase不当当前工作证据。若现在由Agent直接审正文而非后台worker，诚实记录execution_mode=AGENT_CONTENT_REVIEW与刚完成的文件/新增证据；不为状态显示而新建常驻进程。
现有1136未完项与本指令一起继续，无需等待每个小样本确认。下一回提交上述总表/运行链/范围账本/具体问题与证据，完成到哪里就交到哪里；不再以另一份函数名单或种子表当整批成果。
截止保持17:09；到期保存完整剩余清单及真实状态。原业务只读，仅隔离盘点产物可写；不改策略/规则/环境/指针/迁移state，不下载/采集/回测/清理，不新增服务、Agent或巡视，不重开R9。
