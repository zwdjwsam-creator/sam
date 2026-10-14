# ZHANGWEI｜整理最终迁移计划，等待140文件版本选择

task_id: R9_DESKTOP_BUILD_FINAL_PLAN_PENDING_VERSION_CHOICE_20261015_0725
execution_host: ZHANGWEI
status: READY
SAM: HOLD
VERSION_CHOICE: PENDING_USER
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
CANDIDATE_EXECUTABLE=false
full_plan_acceptance=false

## 审核已收口

来源SAM的0641+0711证据已补齐。目录：
agents/chatgpt/inbox/R9_NOTEBOOK_RESOLVE_234_DELTA_AND_HANDOFF_20261015/
本轮审核直接读取并独立重算7份关键报告/JSON/核查代码的SHA/字节数；140逐项验证两取数法/实读字节/已知内容SHA/前后身份一致，127 CRLF、13 EMPTY，140个不同实体。全部mtime为2026-10-14的观察值，但原因未判定，不归因于复制程序。
42条baseline/live/普通代表的volume、file id和size逐项一致，所选代表没有reparse祖先警告。是旧delta记录的junction视图，不是实体丢失，不能再派SAM重复证明。当前字段聚合ordinary缺vol/fid/size/mtime=0，access_err/identity_err=0，4825reparse均有tag/target；D16旧NULL身份已单列。
51新增为49邮箱+1规则+1根；mcp配置size930→1201。
140全部脚本/文档/配置（92py、23md、17json、7csv、1mdc），旧合计2790949字节，当前总254字节。原样迁移或先找旧版由用户决定；本轮只准备元数据候选，不预先选择，不复制业务数据。

## 本轮目标

将已完成真实复制/断点试验的执行器与更新后的来源/目标修复计划接好，交出具体、可审阅的最终迁移准备包。不要继续测速或真实试验，不再做全源扫描。所有新文件仅ZHANGWEI本机C。不要改原94e6来源库、e6c49候选或旧试验状态。

## 输入及有限读取

原本地来源库：
C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite
SHA94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba，bytes6025072640。
使用台式机已有冻结副本核本机身份，不再经SMB重传/重hash这6GB。

从HUB读取当前版本的SOURCE_PLAN_PATCH.json、TINY_140_READ_PROOF.json、MISSING_42_BINDINGS.json、CURRENT_FIELD_COMPLETENESS.json、SAM_REPORT.md及FILE_SHA256.json，校验实际字节/清单。SOURCE_PLAN_PATCH只是候选操作集，其中51新增和mcp条目缺完整metadata，不能当已具备字段直接填0。

为补这52条允许通过现有已验证来源会话，做**最多51新增+mcp 1条的只读metadata探测**（含必要有限祖先检查），不读文件内容、不递归扫描。E来源映射\\192.168.100.2\E_DRIVE\BLACKBOX；D映射\\192.168.100.2\D_DRIVE。来源卷E2387166462/D3187598165，电脑SAM。只读取得类型、volume/file id/size/mtime、reparse若有tag/target。邮箱是活动资料，可记录本次值及观察时刻；其他路径读取失败/身份变化逐项阻塞，不改凭据/会话、不要求密码、不连D$。
140及42已交证据可直接使用，不再读它们内容。如果SAM现有会话访问失败，先完成不依赖这52条的C盘准备并回报具体阻塞；不自动新建登录/权限。

## 新来源候选与目标候选

复制原94e6为新的C盘候选，保留原SHA；在副本中：
1. 增补51实际metadata行（区分普通目录/文件）；mcp使用实际本次metadata。不要只用detail文本或虚构mtime。
2. 140按实证current size254总字节、对应volume/fid/mtime/SHA保存；额外SUSPECT_VERSION侧表和VERSION_CHOICE=PENDING_USER。这是现状预览，不表示接受它们为正确版本。不得恢复旧内容、填写旧size冒充现值、默认跳过140或当用户已经选原样。生成待选择条款：AS_IS_MIGRATE_MARKED / FIND_OLD_VERSION_FIRST，合同执行必须因此保持关闭。
3. 42从“物理普通路径/alias列表”中剔除重复的junction视图，仅保留逻辑视图映射记录，实体保留、使用已验证的普通代表；不是删业务数据。逐实体重算path_count，确保普通来源代表不穿reparse祖先，逻辑访问由修复junction保持，不在junction目录下再建硬链接。
4. 对受影响实体全部别名保持identity/size一致，重新聚合entities与必要索引。不要改mtime字段缺失的旧事实：旧基线其他路径没有历史mtime时，保持未证实，不编造。COPY语义应为按授权合同读取当前来源，逐实体稳定句柄+复制SHA/目标验收；不宣称整个来源是一致时点快照。
5. 目标修复重放既有3694缩短边政策与JSON alias修复：原始来源raw links保持事实，目标边单独存储；动态发布政策未扩大。复用已审核的REPAIR_POLICY/overlay（原overlay SHA079537ac33b5b7bc3a9001c32c78eff0788ce5affe6f7d493402dcb8a651ea0e）。JSON CLEAN通过普通ASOF实体增加目标别名，不能作为源普通文件。重验目录链闭合/终点/循环与42逻辑视图可达相同实体。不能把候选文件标为来源证明。
6. 重算普通文件路径/目录/重解析/唯一实体/唯一字节/预计分配数（精确与估算分开）。参考：扫描时物理普通8715071、目录233665、重解析4825；这是观察值不是强行匹配目标。目标JSON别名另加1普通路径、reparse去1；目录父链可能另需补，分别列明。新增邮箱后续变更要标时间边界，不假装全源冻结。
7. 检查普通创建路径不位于目标reparse祖先下，所有目标都在批准BLACKBOX/BLACKBOX_ENGINES根；源与目标映射不交叉，不把SAM E当ZHANGWEI E。

## 接入已有统一执行链，始终闭闸

沿用最新统一runner/WindowsBackend/full_acceptance及4句柄有界来源prefetch，避免另写第二复制主体。新计划SHA必然变化，修复旧94e6硬编码绑定，使合同绑定**确切新冻结计划文件SHA、当前全部代码digest和目标身份**；不得通配接受任意计划、跳过摘要或复用旧run/DONE。
候选冻结后记录SHA/size/无非空WAL/journal/quick_check与代码digest，改完代码重新计算digest。新run/state与旧试验完全分开，新合同VERSION_CHOICE=PENDING_USER、COPY_AUTHORIZED=false。缺用户版本选择、缺明确复制授权时，无论dry-run或execute都不得产生目标写入；新候选不能沿用旧单次BENCH许可。
只读现场核ZHANGWEI目标E：磁盘UniqueId=eui.E8238FA6BF530001001B448B42E694AE，NTFS卷D86AEE82/DWORD3630886530，不能使用历史806508DF；目标根E:\BLACKBOX与E:\BLACKBOX_ENGINES。不创建目录、不格式化、不删旧试验。
做当前完整候选的结构/闭合/实体一致性静态检查、统一入口dry-run，并确认未授权execute仍在第一次写入前拒绝（真实Win32 write_calls=0）；不得为了显示通过把SOURCE_CURRENT_MATCH或full_plan_acceptance置true。后者只有真实迁移后全验收才可能成立。
必要隔离测试只覆盖本次metadata/绑定变更，不再建真实试验根、不跑新的1GiB BENCH。已通过的真实ABC等证据引用即可，不重复。

## 回传并停止

回传 agents/chatgpt/inbox/R9_DESKTOP_BUILD_FINAL_PLAN_PENDING_VERSION_CHOICE_20261015/
先ACK，完成后ZHANGWEI_REPORT.md应明确：
- SOURCE_RECONCILE_REVIEW_ACCEPTED=true；VERSION_CHOICE=PENDING_USER；COPY=false。
- 新来源/目标候选本地路径、SHA、大小、统计、冻结证据、patch/overlay归属及变动摘要。
- 42物理视图处理与JSON alias不重复；140版本风险保留。
- 52有限元数据探测结果与观察时刻；静态全计划检查/dry-run/未授权execute零写证据。
- 新运行合同/入口/准确命令/目标绑定/预期行为，所有执行授权关闭。
- 当前代码包、小型JSON/报告和hash上传；GB级计划留C。
- 版本选择之外真实剩余技术阻塞/所需下一步一次写全。IMPLEMENTATION_READY不得先自行标最终通过，交HUB审码判定。
准备完停止等审核和用户版本决定。不再自行复制。SAM已完成本机证据，本轮HOLD，无需继续取数/找备份。
