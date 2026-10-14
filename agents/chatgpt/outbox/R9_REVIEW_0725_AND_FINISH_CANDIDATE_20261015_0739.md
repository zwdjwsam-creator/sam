# 0725审核及最终候选补齐｜双机分工

review_id: R9_REVIEW_0725_AND_FINISH_CANDIDATE_20261015_0739
status: READY
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
CANDIDATE_EXECUTABLE=false
full_plan_acceptance=false
VERSION_CHOICE: AS_IS_MIGRATE_MARKED
user_decision: agents/chatgpt/outbox/R9_USER_VERSION_CHOICE_AS_IS_20261015_0727.md

## 审核结论
已读取0725的ZHANGWEI_REPORT、CANDIDATE_BUILD、FINAL_PLAN_CONTRACT、GATE_RESULT、PROBE_52、r9_formal_chain.py及test_binding_0725.py。
候选341d7b19…为阶段性交付，仍不具备完整范围。140现值、42视图处理、3694 overlay及零目标写入已有回报；不据此宣称最终内容/链接全通过。
版本选择已由用户明确作出，不得再以PENDING_USER或等待选择停止。本决定不等于正式复制授权。
52项读取52/52报1326是台式机现场事实，不能把它们当补齐；改由来源电脑本地取数，不依赖SMB。

审码复现具体缺口：
r9_formal_chain.inspect_plan 中 closure = audit_bench_links(conn) if scope == "BENCH" else {"ok": True}。
我抽取实际inspect_plan和_scope_violation，用1实体/1普通路径及links指向E:\BLACKBOX\NONEXISTENT的临时SQLite复测：scope=FULL仍ok=true；闭合函数未调用。
因此dry_audit.ok只证明当前有限检查，不证明FULL链接闭合。不能把它升级为全计划审核通过。96条E:\BLACKBOX_ENGINES目标应经实际D→目标映射核验，不能因原D目录存在或候选标签而直接通过。
报告把目标根不存在列在“不能开始”中也需澄清：这不是需用户预建/再格式化的阻塞；授权后的统一执行器按父先子后创建即可。历史mtime/hash缺失、USN ABSENT继续如实披露，不能补造；不是要求再找历史证据或重扫。

## 执行电脑1：笔记本SAM｜仅本地补52项
task_id: R9_NOTEBOOK_LOCAL_52_METADATA_HANDOFF_20261015_0739
status: READY
先ACK。输入为以下两个已发布文件，核对路径集合恰为51新增+mcp一条，去重52：
- agents/chatgpt/inbox/R9_NOTEBOOK_RESOLVE_234_DELTA_AND_HANDOFF_20261015/SOURCE_PLAN_PATCH.json
- agents/chatgpt/inbox/R9_DESKTOP_BUILD_FINAL_PLAN_PENDING_VERSION_CHOICE_20261015/PROBE_52.json
直接在本机SAM读取各自真实E:\BLACKBOX、D:\路径，不走UNC。不递归、不全盘扫描、不读业务内容、不改来源。采用已有可信metadata读取方法，逐条记录路径、观察时间、成功/错误、类型、volume serial、file id、size、mtime、nlinks/分配空间（如现有计划所需）、reparse tag/target（如有）和必要祖先检查。来源卷E2387166462、D3187598165；缺字段/访问失败保留明确错误，不能补0或推定。
邮箱活动文件记录本次值和观察时刻，不承诺一致时点；140和42无需复查，不找旧版本。
小型结果/读取脚本/文件hash发布到：
agents/chatgpt/inbox/R9_NOTEBOOK_LOCAL_52_METADATA_HANDOFF_20261015/
包含LOCAL_52_METADATA.json、SAM_REPORT.md及SHA清单。只上传metadata，不上传文件内容/凭据或大库。
完成通知台式机在HUB领取，并回传INBOX_FOR_CHATGPT；本机停止。此轮允许SAM执行以上有限只读任务，覆盖旧HOLD；不授权其他工作。

## 执行电脑2：台式机ZHANGWEI｜合并+修正FULL审核
task_id: R9_DESKTOP_COMPLETE_ASIS_FINAL_CANDIDATE_20261015_0739
status: READY
先ACK，明确已领取用户决定AS_IS_MIGRATE_MARKED。原0725已回传的版本保留为证据，不改旧报告冒充当时已接收。
1. 不等SAM即可在本机C继续修正版本侧表/合同/报告，以及下面的FULL审核。原94e6、旧e6c49、341d候选及试验状态不覆盖；在新C候选中做最终合并。140全部按现值纳入，保留SUSPECT_VERSION及证据；不恢复、不跳过。
2. SAM结果到达后从HUB取小型JSON，核SHA/52路径集/来源卷/字段完整性；应用52实际metadata，目录不得误作文件，mcp按实际值，受影响实体及全部alias的size/identity/计数重聚合。若观察值变动记录边界，不伪造一致时点。无需通过失败SMB重取52。
3. FULL检查须基于reader实际生成的目标路径、目标链接边、源代表及别名映射，检查父目录闭合、链接终点/循环、路径冲突和普通创建路径不在目标reparse祖先下，覆盖42逻辑视图仍落同实体、JSON CLEAN只为目标alias，以及96条D来源映射后的目标普通目录。不要直接给FULL closure={"ok":True}，也不要原封套用BENCH根规则。采用流式/索引查询或目录集合，避免无必要把约870万文件对象装入Python大字典。
4. 做本次改动的有意义隔离测试：FULL缺终点、循环、缺父目录/普通路径穿reparse应拒绝；有效D→BLACKBOX_ENGINES映射应通过；选择AS_IS但无copy授权仍拒绝。不再实盘BENCH、不新建E试验根。
5. 本次完整候选重算统计及预计分配口径（精确/估算分开），冻结quick_check、无非空WAL/journal、SHA/bytes；新合同绑定准确新SHA/当前完整代码digest、目标盘UniqueId eui.E8238FA6BF530001001B448B42E694AE、NTFS D86AEE82/3630886530。使用新run/state，不借用旧DONE。COPY各项保持false。
6. 交真实的完整候选静态审核结果、统一入口dry-run和未授权execute零目标写入证据。仅从现有已验证来源会话各E/D选1条必要metadata探针核读，若仍1326如实报告“正式复制来源会话未恢复”；不要重复52失败请求、不新建登录、不改凭据/网络/活动SMB会话、不要求用户重复做版本选择。恢复来源访问是后续真实前提，不因本地metadata齐了就宣称UNC可用。
7. 上传候选构建/修补脚本、本次修改代码、FULL静态审核/测试脚本及输出、合同/统计/代码摘要清单，给出准确执行命令。6GB计划继续留本地C，不经SMB传大库；不需要重扫来源来证明历史一致。
回传目录：
agents/chatgpt/inbox/R9_DESKTOP_COMPLETE_ASIS_FINAL_CANDIDATE_20261015/
ZHANGWEI_REPORT.md明确已消除的“版本待选”、52/52处理结果、FULL各项审核计数、网络来源会话是否可读、真实剩余阻塞，一次写全。完成停止待审。

## 协调
两个任务是分工接续，不重复扫同一范围。SAM先交metadata；ZHANGWEI先做不依赖它的修正，随后合并。不要自动无限轮询或重复启动。不格式化、不删除源/旧试验、不写目标E、不启动正式迁移。
