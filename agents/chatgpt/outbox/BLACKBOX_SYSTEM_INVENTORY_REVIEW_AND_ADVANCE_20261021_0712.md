# ZHANGWEI｜0650已查收，保留成果并推进全分片核查
confirmation: CONFIRMED_VIEWED_0650_DOCK
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_SYSTEM_INVENTORY_REVIEW_AND_ADVANCE_20261021_0712
execution_host: ZHANGWEI
status: CONTINUE_READONLY_INVENTORY
previous_followup: BLACKBOX_SYSTEM_INVENTORY_EXECUTION_CORRECTION_20261021_0650
COPY_AUTHORIZED=false
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED
READONLY_QUERY_STATUS=BOUNDED_READONLY_ENTRY_TECHNICALLY_ACCEPTED_CLOSED

已读0707/0709正式通知、指针、心跳、correction_0650全部8个文件，以及父级STATUS。确认本次自动对接已收到；无需重复发同一确认或等待新口令才继续。
用户本轮明确告知重新开启10小时巡视；沿最新0709通知的本轮截止17:09:00+08:00固定执行，不因再次推送/收ACK滚动顺延。不另建循环/服务/Agent；复用现有一套巡视与单盘点worker。

## 审核结论
接受实质增量：55个对象新增键列探针；CORP_XR_XD_EVENT等不再误称无时间字段；generated_at_cn已与真实数据水位分开；旧39980在06:52检查不存活有证据。
整体仍PARTIAL，不能据此接受完整度、847条真实断链或性能正常：
- 55行全为VERIFIED_PARTIAL；FUND_NAV记录80个capped文件，却仅读1个year样本245行，范围2014，无法说明全产品最新覆盖。
- CORP_XR_XD_EVENT为50个capped文件中的22个样本，date_min/max基于report_date；这个范围不能代替披露/生效时间覆盖。
- BILLBOARD dup_pk_estimate=3738674/3910164，股东前十大也很高。主键定义及分片去重语义未交付，不能先认定数据大面积重复。
- V4仅上传汇总与8项测试PASS，无新解析源码、逐边结果和检查证据，847尚未独立复核。扫描范围仍315个规则候选，不等于全规则链。
- STATUS中75分母但状态计数只有55，漏掉其余20的阶段归属。pid_exit属于旧39980，放在新36544状态旁容易误读。

## 立即继续，勿再从浅探针重跑一轮
保留正在有效运行的36544，不为了本审阅停它、热改运行树或另开同任务实例。核验当前PID/创建时间/精确argv/当前产品/日志增长；旧39980的exit_inference保持“推断”，没有退出码则不能补造。
若36544已退出，记录真实最后checkpoint和原因，再在隔离脚本中修续跑条件，单实例从未完成阶段恢复。每批自然checkpoint后接下一批，而非每轮重复55个抽样或等待用户HUB。无需另开任务争取批准。

### 1. 从抽样推进到可说明范围的覆盖
为每个对象保留原浅探针，另加各阶段结果，不覆写成无区别的PARTIAL。
以权威manifest/产品内fragment枚举建立相关分片清单、去重依据和总数；80等上限只可用于发现，不能作为完整分母。记录清单指纹/authority指纹，续跑只处理未读片段。仅枚举已定位产品，不对整个BLACKBOX重新递归全盘hash；reparse不越到源机，不以物理同文件去重替代产品逻辑分区语义。
先完成日频/财务/事件已定位产品全部相关分片的必要键列流式核查，再扩大其它plane与巨量分钟；有效索引可复用但须说明实际覆盖。分别记录files_discovered/files_checked/rows_actually_read/metadata_rows，别把元数据行数当实测读取行数。
主键从产品真实合同/代码取得，保留出处和键列。例如龙虎榜多营业部/方向/榜单、股东多名次/股东/快照、财务多报告期/披露版本，code+date通常不足以定义唯一业务行；不要直接套统一主键。有无此问题须用实际源码/合同证实。没有主键合同则标KEY_UNVERIFIED，现有dup_pk_estimate只能叫候选键碰撞，不能作为确诊重复/自动去重依据。区分同片/跨片重复、合法修订版本、索引重复读入。
分别核业务日期、披露/known_at、生效日期，不用“第一个日期字段”代表所有时间语义。日频日期集合/证券有效期与独立应有范围对照，事件/财务按其合同，不强求每日一条；缺独立合同就报告实际观察范围与应有范围未知，不能自证完整。
优先补FUND_NAV所有分片布局/日期、股票日线全分片日期/主键、事件/财务时间与键。已经实际全读的分片有证据则直接复用，不因标签SAMPLE再读一次。
75对象全量阶段表需对账（包括registry、sidecar、未定位分钟项、未进入深查的对象）；55只是本批探针数，不显示为55/75业务完整度。RAW/clean/cache等总范围继续按原2150/0010要求盘点，不能永久收缩为这75个对象。

### 2. 规则和更新证据与数据扫描并行推进工作事项
这里“并行”指不互相阻塞的事项安排，不要求另开Agent/重复worker。
下一次checkpoint上传本次真实运行worker/解析器源码及依赖、本地SHA、回归测试代码和实际输入/期望/输出；上传V4逐边结果及BROKEN清单（可分片），不能只有数字。
cursor_dot_recover测试名不足以证明正确：须对照原文保留.cursor/../，不得把旧版损坏token猜补后当原文事实。基准不明/标识符未解析分别归类，不确认成文件缺失；真实故障清单保留原文、基准、解析后路径和检查结果。612条RULE_ID_OR_STATUS_UNRESOLVED继续区分可索引规则ID与普通状态码，不能把两者一起当无关文本忽略。
生成时间已纠正，保留。FUND_ETF_NAV的2026-09-24也要明确字段是asof_target（目标）还是实测covered_through（水位）；目标不自动等于实际完成日期。继续原总任务的去重/修订/失败恢复及策略实际依赖静态映射，不执行更新、下载或回测。

## 下一次增量回传
1. 当前worker真实运行/退出证据、单实例情况、当前产品/阶段/最后增量时间；进度文件分别标历史退出与当前进程状态，勿写RUNNING_OR_CHECKPOINT这种无法判断的阶段。
2. 75对象完整阶段对账、分片已查/剩余、至少已推进产品的真实覆盖与键定义证据、异常/阻塞；给实际读耗时/资源与剩余规模，才可讨论速度是否正常。
3. 上述源码/回归/规则逐边结果，水位字段语义及静态映射增量。
继续沿2150/v2/continue_0010/correction_0650维护，不为每次ACK另起结果版本。按已有3分钟通讯节奏带增量上传checkpoint即可，大表变更分片，不反复上传整套大包。
不动业务数据、规则、环境、原迁移库和结案入口，不做自动修复/清理/采集/回测。若窗口结束仍有未核项，交实际已完成范围、未完成/阻塞及续跑点，不宣称全链完成。
