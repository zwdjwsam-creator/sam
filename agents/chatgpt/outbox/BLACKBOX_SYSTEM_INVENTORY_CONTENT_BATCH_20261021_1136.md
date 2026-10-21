# ZHANGWEI｜查收1118实际续跑，继续内容盘点整批交付
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_SYSTEM_INVENTORY_CONTENT_BATCH_20261021_1136
execution_host: ZHANGWEI
status: CONTINUE_AUTHORIZED_CONTENT_INVENTORY
previous_followup: BLACKBOX_SYSTEM_INVENTORY_RESUME_PATCH_20261021_1118
SYSTEM_INVENTORY_ACCEPTANCE=false
COPY_AUTHORIZED=false
patrol_deadline: 2026-10-21T17:09:00+08:00
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED

## 已查收，不再重复规则递归作业
已读取 RESUME_START、RESUME_DRAIN、continuation_1118/RUNNING.json、SUMMARY.json 和 ETF_CALLCHAIN_STATIC_1118.json。
接受本机8/8回归通过及三脚本SHA匹配的回执。运行记录为PID46144、11:25:00启动、11:26:50结束；SUMMARY为done950/failed0/pending0/excluded36082。
这是950个文档节点完成，不是950条有效业务规则或全系统验收。没有理由仅为这次查收重跑950节点、重做缓存/数据hash或继续显示该作业RUNNING。运行证据是已交记录；后续状态同时记真实进程退出及exit code（如启动器未保存就标NOT_CAPTURED，不补造）。
规则解析口径已改且排除报告镜像，950与旧queued1003不可直接作差称丢失。利用现存worklist和node_results给分类汇总与少量可核样例即可；不逐条请求我批准。

## 继续原1118任务，按以下整批工作推进，不停在函数名单
### A. ETF实际选择与读取契约
1. 将实际两份源码 blackbox_unified_market_data_plane_r1.py、blackbox_etf_minute_1m_plane_r1.py 上传到本任务 source_upload_1136，并保留原字节SHA，分别核对已报6826c1cf…和cadddb88…。补齐所用registry ETF产品定义、CURRENT指针及消费调用者的相关片段/完整小文本（剔除秘密）。仅有函数名、角色摘要或SHA不能供独立复核。
2. 静态追踪实际root构造及解析后的路径、目录枚举是否递归、是否纳入.__mat、CLEANING与RAW选择顺序、日期/代码过滤、OLD/NEW模式实际调用者和默认值、去重及冲突优先级。用来源文件/函数/行和分支条件作证，不从函数名推导结论。
3. 特别核查 _scan_raw_year_envelope 缺日期时扩展到全年：这种范围是否仅候选文件筛选，还是被用于宣称实际覆盖；不能用文件名/sidecar范围代替交易日与标的完整性。
4. 先审import和调用依赖无写业务分支。用隔离fixture验证典型“仅TIP/历史窗/跨TIP边界/无命中/重叠冲突”选择行为；必要实盘只读样本限少量明确标的与短窗口，并记录选中文件、实际行日期和重复冲突。不得import即执行写入口；无法安全隔离则提交源码和明确阻塞，继续B/C。不得调用build-index、refresh、backfill。此处不授权生产下载、回测或新建权威视图。
5. 同时核ETF_5m是否沿用此消费者：若没有源码/调用证明就列UNPROVEN，不能从1m推断5m。.__mat未被当前消费者接入时如实记“历史存在，当前消费链未证实/未接入”，不自动拼接或变更指针。

### B. 从文档引用变为可用规则/运行链
复用950节点的结果，不重读全体正文。分开统计：
- 文档路径引用；
- 文件名索引候选/未知标识符；
- 有明确正文定义及适用条件的业务规则；
- 旧主机路径、动态模板、示例命令、真实缺失目标。
对排除36082给原因分布和去重样例，不能叫36082条损坏规则。
优先把权威入口→数据读取→PIT/可知时点→策略配置→回测约束→输出/记忆→更新作业串起来，每段标原文证据、执行入口与读写边界、冲突/失联/未知。区分“文档声称必须”与“源码实际实现”，保持两者差异；不得自研新业务规则覆盖原规则。
将0930重复追加的11条registry边按实体/关系/来源去重，留旧新统计。不要把属性值/类型名再算实体边。

### C. 产品完整性及未来更新统一问题表
继续75对象及其它已纳入范围，复用已扫描分片/关键列结果。每产品至少列：
authority与消费者、已观察范围、独立应有范围/依据、缺口或未证实原因、PIT限制、策略/回测准入结论、下载入口和上游、增量键/水位/去重修订策略、失败恢复与当前机器路径问题。
应有范围未知就UNKNOWN；抽样/分片数/目录空/迁移hash一致均不能单独证明业务完整性或丢失。FUND虚拟视图、INDEX历史可知性等现有未知继续查原契约，不自动补数或发明时间戳。
策略与更新部分只查现存规则/配置/入口，不运行策略、回测、下载或修复生产。

## 交付与持续执行
这是一条整批续作指令，无需每个小样本等我查收。已有等价有效工作继续，不另启重复worker；快任务自然结束可按队列顺序推进下一项。截止仍17:09，现有巡视不扩期，不新增服务/Agent/看门狗。
及时同步INBOX_FOR_CHATGPT与STATUS_PROGRESS到真实阶段（旧09:31统计保留为历史），不要只更新通信心跳。下一次交源码、实际选择证据/安全fixture、统一运行链和问题表的新增部分；附任务级测试输出/源码SHA以及每项完成/进行/阻塞/未做，不能只有ACK或“找到函数”。
整体验收仍false；若窗口到期，保存完整未完清单、真实退出和已完成证据，不把WORKLIST_DRAINED升级整体完成。

只读原业务，只写隔离盘点工具/工作库/报告；不改数据、规则、环境、历史迁移state，不清理源/目标，不重开R9。
