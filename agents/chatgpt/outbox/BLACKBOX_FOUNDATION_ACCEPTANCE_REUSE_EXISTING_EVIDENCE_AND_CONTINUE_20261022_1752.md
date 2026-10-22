# BLACKBOX_FOUNDATION_ACCEPTANCE_REUSE_EXISTING_EVIDENCE_AND_CONTINUE_20261022_1752

TO: ZHANGWEI / Cursor E Agent
execution_host: ZHANGWEI
status: READY
parent_task: BLACKBOX_FOUNDATION_ACCEPTANCE_SCOPE_AND_EXECUTION_20261022_1745
mode: CONTINUE_SAME_TASK
FOUNDATION_ACCEPTANCE=false
PRODUCTION_CHANGE_AUTHORIZED=false

用户明确要求：先读已有成果再续作，禁止无依据从头扫描。GPT已核对HUB既有记录。本补充在1745同一任务中执行；若已领取/运行1745，直接并入，不另启第二实例。尚未领取则领取1745及本补充后直接推进。无需先报计划等待批准。

## 现成证据，必须复用
共同旧包：
agents/chatgpt/inbox/BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150/v2/continue_0010/correction_0650/
其当前本地对应根已在既有STATUS中：
E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650

1. continuation_1118/SUMMARY.json：
950文档done，failed=0，pending=0，worklist已排空。复用本地durable worklist/node_results/正文缓存、RULE_ID_INDEX_0930和引用索引。950是已处理文档节点，不是950条业务规则验收；不重新启动950文档读取或全盘文字递归扫描。
2. content_batch_1136/CONTENT_BATCH_1136.json：
已审数据入口、函数范围/SHA、RAW与Cleaning根及隔离探测引用。
其中ETF_1m RAW明确指向 P4_fund_etf_raw_none/fund_etf_price_1m；当前Cleaning来自CURRENT.standard_root。直接复用这个真实来源线索，1732的P4_fund_etf旧目录不能覆盖它。来源身份有新冲突时只查该项指针/manifest。
3. contract_scope_1145/CONTRACT_SCOPE_1145.json：
950结果全聚合、排除范围、134条去重实体依赖边、已有75对象表和接口静态结论已在，直接引用。过去隔离探测不因本轮改任务名再跑。
注意其旧优先队列中的“历史策略正式消费者”被用户此次范围收敛替代，不再作为底座验收前置项。
4. continue_1310/completion_1447、1519、1543、1635、1655、1710、1732：
复用实体/行数元数据、FUND_NAV全读、已审构建/更新语义、注册表风险、迁移路径、实际规则/合同提取、隔离回归与字典/血缘观察。不同观察时间和样本/全读/声明保持分开，不重新采集已验收项。
5. R9_FULL_MIGRATION_TECH_ACCEPTANCE_20261020_1625：
文件内容与链接的冻结迁移保真已通过，直接引用。不全库hash、不重启复制、不重新遍历867万路径。

## 已知引擎侧线索，定向补查而非再次“没找到”
1145 scope_ledger记录 ENGINE_SIDE_OUTSIDE_1118_ROOT 的93条排除候选，包括已封存引擎的 blackbox_current_dictionary_rule_registry.json。这是早期扫描边界，不是这些文件不存在，更不要求现在全读93条。
1655已经确认当前根：
E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine
顶层有PHASE1_CURRENT_ENGINE_REGISTRY、PHASE1_CAPABILITY_REGISTRY；
rule_library下已有 master_registry_R1、blackbox_current_dictionary_R1、jq_official_canonical_R1 等。
PHASE1 registry还声明R3 sealed backup；1145排除样本中有其规则字典注册表位置。沿当前根注册表/实际文件及必要的已封存版本引用核对权威，不重新找所有历史备份，不以旧D路径缺失判文件丢失。
仅补“数据类型/字段/时间/复权准入→当前数据适配入口”的规则映射，以及1745允许的隔离最小通用读取检查。旧策略、旧研究输出和收益验证全部跳过。

## 本轮真正需要新增的工作
A. 用已有规则索引和1745列出的原domain registry、canonical source manifest、domain seals/收据，批量拼出原RAW下载要求清单，再与现成RAW索引/来源/schema/覆盖观察join。原始下载域为范围，不以75个CACHE产品代替。
B. 对有具体差异或缺证据的条目，列明“缺哪一个证据→读哪个已知文件或必要列”；仅做该小范围读取。不存在有效原预期就标未证实，不能自动要求重新下载，也不能凭路径在就全部通过。
C. 引擎按上面的已知入口完成准入与通用接口检查。缺配置或依赖造成的未接通，与RAW文件缺失分别记账。

在现有任务内保存简短复用/差异清单：证据文件或观察ID、支持结论、是否本轮新增读取及理由。它是审计索引，不是另一轮等待审批计划；边复用边推进。
仅当旧证据损坏、源身份/内容变更、适用范围不同，才重读对应对象；要具体写理由，不能一句“为安全重扫”。

回传仍只要1745三件核心成果：FOUNDATION_LEDGER、ENGINE_BASELINE_CHECK、FOUNDATION_VERDICT，并附已完成/已证缺口/未证实的确切范围。无需复制所有旧源码或每个小问题另开新版本包。
若某分支阻塞，记录后继续其他分支，直到完整一轮底座对照结束再整包回传；禁止回到逐个策略追溯循环。

本补充不新增生产写入权限，1745的只读与隔离测试边界继续有效。关键文件上传并读回成功后再更新INBOX；领取回执说明承接1745及本补充，不能仅称READY任务已执行完成。
