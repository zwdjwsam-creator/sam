# SAM笔记本｜补充BLACKBOX原运行约定（有文件依据）
task_id: BLACKBOX_NOTEBOOK_RUNTIME_RULES_HANDOVER_20261020_1900
execution_host: SAM
status: READY_READONLY_HANDOVER
related_desktop_task: BLACKBOX_DESKTOP_RULES_AND_DATAFLOW_HANDOVER_20261020_1834
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED
COPY_AUTHORIZED=false

用户希望台式机E工作区AI继承BLACKBOX原规则与数据库逻辑。台式机已自行读文件，不需要重新发明规则或全量再搬。请源机AI用现存文件/日志解释以下五项；先核实际hostname和工作区，不能由ZHANGWEI冒充SAM。笔记本未上线则任务保持待领，不能宣称已经激活。

先读适用AGENTS/Kernel/HAND及原必读索引，仅只读，回答：
1. 现行启动/必读顺序、Cache-First/数据缺失/日期与价格口径/研究续跑的权威文件是哪些？记忆盘中哪些包真正影响运行？给精确路径/章节及必要摘录。指出现行与归档的区别，不把AI记忆当规则。
2. 日增六Lane→清洗→cache发布→研究的实际调度：手动口令、Windows任务、其它调度或当前停用？给已有任务定义/启动脚本/最近有效run证据。原来哪些启动或环境配置在E:\BLACKBOX外？不要启动任务、导出密钥或照搬源机计划任务到台式机。
3. 原Python环境/依赖的可复现依据：现行解释器版本、项目requirements/lock/安装说明的路径，若无正式清单如实说无。源机.venv带ThinkPad绝对路径，说明原约定；不现场安装、重建或输出凭据配置。
4. 台式机看到cache/data tip=2026-09-24，DAILY_RESEARCH简报LAST_OK=2026-08-30。源机对应文件现在是什么、分别属于哪条流程？是否有停更记录/替代入口/明确续跑规则？按已有日志证实，不推测为迁移问题。给最近已知正常的小样本行情查询方式，说明它的数据版本/日期，不要求此轮联网更新。
5. E:\BLACKBOX_ENGINES与业务链的实际依赖；根下“杩愯/浠诲姟”等疑似编码目录在源机是否也存在、类型与来源可否确认？只读说明，不递归遍历其全部数据，不改名/删目录。

每项区分“文件/日志证实”“仅原操作习惯”“未知”，给来源路径/时间、台式机可对照位置和应避免的操作。若某项可由台式机文件解决，指出精确文件，不只答NONE。给简洁操作说明即可，不写宏大新规范，不重做全量迁移/全量扫描，不改源业务数据。

交付：
agents/chatgpt/inbox/BLACKBOX_NOTEBOOK_RUNTIME_RULES_HANDOVER_20261020_1900/NOTEBOOK_HANDOVER.md
必要脱敏摘录可放同包EVIDENCE.md，不上传token/cookie/.env/私有聊天全文。更新INBOX_FOR_CHATGPT；原R9LP_RO共享收尾另有任务，保留原状态，不混入本次只读交接执行。
