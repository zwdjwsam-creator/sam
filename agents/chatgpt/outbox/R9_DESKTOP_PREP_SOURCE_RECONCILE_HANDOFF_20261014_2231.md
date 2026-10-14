# ZHANGWEI｜准备源端本机核对的准确基线交接

task_id: R9_DESKTOP_PREP_SOURCE_RECONCILE_HANDOFF_20261014_2231
execution_host: ZHANGWEI
SAM: HOLD
status: READY
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

## 2212 审核情况

9份小型文本SHA已核对、隔离测试3/3通过。实际reader输出说明JSON源代表是ASOF正常文件file id281474980058594、大小1071，CLEAN路径仅目标alias；基本修复策略可作为草案保留。
报告的候选SHA=e6c49ecdf925c923351267883db7bfb2cf83ed7e02f2038ec4bd997ef2f43be2，6,025,261,056字节；3694历史目录边缩短、1130原直达边不改，候选4824目录终点/最大链1。实体/唯一字节/普通目录不变，目标文件路径+1，junction-1。
6GB候选与2.26MB overlay尚未由连接器直接核对；不把本次报告当已完成全部派生差异独立复核或Windows目标实盘。CANDIDATE_EXECUTABLE=false保持。
生产摘要a1ce1ae5e2d0490d6b6c415917200f7c84bb502d9befb397a38fe974e43e5bfd、原计划94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba保持原字节。当前来源匹配仍NOT_RUN；下一阶段需SAM本机核对，不再加复制/测速。

## 本轮唯一目标：让SAM后续能在本机核对当前源，不经SMB逐文件查871万路径

### 1. 构成准确基线/范围交接包

在C:\LAN_SHARE_REPORT\R9_SOURCE_RECONCILE_HANDOFF_20261014\share 建立只含本次允许材料的包：
- SOURCE_BASELINE.sqlite：原MERGED_PLAN.sqlite的只读冻结字节副本，SHA必须94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba。若已有本次同SHA副本可复用，不覆盖旧证据。不能拿候选e6c49e计划当来源事实。
- SOURCE_SCOPE.json：准确E根和D精确纳入根/子树（含空目录和原4825重解析点）；八个已选常规D目录与CURSOR_TASK_ARCHIVE的已选pit_products子树区分，附真实配置/计划依据。E来源为E:\BLACKBOX；不纳入E:\BLACKBOX_MIGRATION_AUDIT_R1等兄弟目录或未选D内容。
- SOURCE_BASELINE_CONTRACT.json：原基线文件SHA/字节、schema字段/源卷E2387166462/D3187598165、路径映射、准确普通文件/目录/链接计数，原输入Ebase/delta/Drepaired实际文件路径/SHA及SAM可复用位置。
- REPAIR_POLICY.json：目标repair仅在之后重放，3694目录边/唯一JSON alias的原始与修复身份分开。候选多出来的一个普通路径并非来源新文件，不用于来源差异比较。
- SOURCE_RECONCILE_HANDOFF.md：后续SAM读取基线、在本机no-follow核对新增/删除/类型/file id/大小/可用mtime/原tag与target的具体步骤。历史mtime/hash和USN锚点缺失如实记录；不能要求凭空证明历史内容完全相同。

原库无WAL后复制，副本校验SHA与quick_check，原文件SHA前后一致；生产代码/候选都不修改。6GB仅元数据，不上传HUB、不向业务根写任何内容。

### 2. 给SAM提供可读路径，优先复用既有共享/会话

只读列举本机现有共享/相关访问权限，优先复用已有能读到“本次单独metadata包”的只读路径，不改变既有业务共享权限、不暴露整棵C:\或全部LAN_SHARE_REPORT。
若无合适现成路径，本任务允许使用Windows原生能力创建一个临时、仅此share目录的只读共享，名字R9_SOURCE_BASELINE_20261014；只允许既有已认证账号读取，不给匿名/Everyone写权限，不新增账号或找密码。可以使用Authenticated Users读取本单独metadata包，保留本机管理员/SYSTEM原管理权限。不能共享令牌/业务内容/其他报告树，不能更改全盘ACL、防火墙/网卡或现有SMB会话。
需要权限时用现有已授权的本机管理员执行方法；遇到权限或会话阻塞如实报告，不反复弹原生登录窗要求用户输入密码、不断IPC$或删除凭据。
提供实际UNC（以实测本机直连地址/主机名为准，不猜地址），只读自检列表与文件SHA。台式机自检不证明SAM已认证访问，SAM_ACCESS_VERIFIED保持NOT_RUN，后续由SAM验证现有会话后才传入其本机C。
如果现有SAM端已保存相同SHA原基线可直接复用，则记录位置/来源事实；如共享受阻，给可复用原输入重建来源投影的具体信息及规范化记录digest，不伪造已传输。不要改成8百万次远端metadata查询。
本轮不唤醒/调用SAM执行扫描、也不让台式机代查来源全树；SAM仍HOLD。后续HUB会发独立SAM任务。

### 3. 把必要审阅证据拆成可读小文本

将已有DEST_DIRECTORY_LINK_OVERLAY.json按完整记录拆成每份<=512KiB的UTF-8 JSON/JSONL，HUB上传小分片及SHA清单/记录数，组合后证明对应原3694条完整overlay（不改变原2.26MB文件）。
汇总每条历史role的依据：是否确在具体有ASOF/版本/时间戳的release下，不能仅以路径含“RELEASE”或“PIT_”就宣称从不参与动态发布。若有不满足历史限定的记录，列出具体条目，本轮不改候选去隐藏问题。
本任务不另开发/重测复制器；这一步只为了完整审阅现有差异与后续重放策略。

## 给后续SAM的核对口径

先把原基线metadata拷入SAM本机C并核SHA，再本机no-follow枚举准确范围：重解析点只记原元数据、不向下遍历；可复用SAM已修枚举入口，避免新框架。来源数据不拷出、不修改，扫描日志/新metadata写C。
比较来源原始事实用94e6基线，目标e6c候选与repair alias不要混入。缺历史mtime/hash时仅能证明路径/身份/大小等有证据项；记录新的当前mtime、扫描时段与可用新USN锚点，供后续复制时一致性校验。发现新增/删除/改变就生成真实delta，之后更新来源计划并重放目标repair，不把差异藏起来或永远要求旧计划完全不变。
无历史USN不能免掉首次本地核对。扫描中变化/无法访问/覆盖未闭合要列出，不以相同总数或源没更新口述代替。后续不自动停止业务/交易应用或更改数据，不在本轮启动扫描。
这只是可执行交接要求，SOURCE_CURRENT_MATCH继续NOT_RUN；不能把共享成功/副本SHA匹配当当前来源核对成功。

## 回传停止

先ACK。本轮回传 agents/chatgpt/inbox/R9_DESKTOP_PREP_SOURCE_RECONCILE_HANDOFF_20261014/ZHANGWEI_REPORT.md，附SOURCE_BASELINE_CONTRACT、准确scope/repair-policy/交接说明、元数据传递路径及只读共享实际状态（含SAM_ACCESS_VERIFIED=NOT_RUN）、拆分overlay与完整SHA/记录数、原与副本/C候选SHA前后。
标注HANDOFF_PACKAGE_READY、SAM_BASELINE_ACCESS_PATH_READY真实结果；权限/位置不足具体说明，不把未验证的账号会话报成功。
只允许C metadata包/只读共享设置/报告写入，E目标/源业务数据完全不写，不改生产代码/原库/候选，不格式化、不复制业务数据、不清除旧试验。
CANDIDATE_EXECUTABLE=false、COPY_AUTHORIZED=false、FULL_MIGRATION=false、IMPLEMENTATION_READY=false、full_plan_acceptance=false。
完成停止待审。本轮执行电脑=ZHANGWEI，SAM=HOLD；下轮来源本机检查应明确改为SAM，不能在台式机经SMB慢扫代替。
