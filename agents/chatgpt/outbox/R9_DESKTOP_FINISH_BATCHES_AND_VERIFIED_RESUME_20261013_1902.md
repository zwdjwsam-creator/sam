# ZHANGWEI 台式机｜完成剩余批次、核验恢复及全计划验收

task_id: R9_DESKTOP_FINISH_BATCHES_AND_VERIFIED_RESUME_20261013_1902
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
supersedes: R9_DESKTOP_BATCH_RESUME_ACCEPTANCE_20261013_1852
SAM: HOLD
IMPLEMENTATION_READY=false
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true

## 审核与当前进展

仍由台式机执行，SAM 停止待命。1852 回执 PARTIAL 如实，不转为 READY。
ChatGPT 独立复跑本轮 test_chain_reader_runner_backend 通过：
path 列映射到 E 源 UNC/目的路径，虚拟硬链接 alias=PRESENT，缺路径=MISSING，正常重复运行不再重写。
这些已完成成果保留，不重跑源导出/扫描，不重新 build 6GB 计划。

但正常重复执行不是中断恢复证明。ChatGPT 独立模拟：
首次运行后把代表目标的内容/FileId 改坏，再把 alias 改为另一个卷/另一个 FileId 的无关文件；
第二次 production_run 仍从 done 表直接返回旧 hash/id，并将无关 alias 标 skipped，无错误。
当前已有实体不观察、已有 alias 只按 PRESENT 跳过，仍会放行坏结果。
因此三种中断恢复都需要证据，不把普通二次运行算作其中一种。

本轮沿用1852详细要求，只完成剩余代码和已发现的恢复缺口。执行范围连续授权，不为每个函数等待下一条指令。

## 先修准备期模拟隔离

r9_runner.allows_write 当前只按 SIMULATED_CHAIN+任意 volume 字符串判定。
在任何实体读写前验证 backend.sc 必须是允许的虚拟协议；SIMULATED_CHAIN 与默认真实 Win32Syscalls 相接应拒绝。
PREPARATION_ONLY（即使两个 bool=true）和 SIMULATED_CHAIN+真实后端均须写入 syscall=0。
真实 IO 完整实现可以编写，但本轮所有实盘调用仍 NOT_RUN，不以模拟合同打开真实后端。

## 一、目录及重解析批次

补 production runner 的普通目录 -> 实体 -> 硬链接 -> 重解析 -> 验收顺序，
实际及虚拟协议都实现目录创建、重解析创建/读取、no-follow 枚举。
虚拟方法产生可观察对象，测试观察目录/链接类型和目标，不能只断言返回字典。

保留已新增的 CreateHardLinkW 真实调用；补真实观察器：
Win32Syscalls.observe 现在只有 status/path，必须实际取得类型、目标 FileId/volume、size、AllocationSize、必要内容hash及重解析类型/目标。
非 FILE_NOT_FOUND/PATH_NOT_FOUND 的权限或 IO 错误应为 ERROR，不能所有 OSError 都算 MISSING。
hardlink 创建/恢复后必须比较 alias 与代表的实际目标 FileId+volume，不以 PRESENT 算通过。
junction/symlink 按类型实现、校验目标不回指 SAM UNC/旧 D；不得跟随链接复制内容。
生产路径检查目标范围及既有祖先 reparse，未知对象/错误类型拒绝覆盖。
MoveFileW 等调用补 ctypes 参数及错误处理；稳定源句柄在读取结束后再次核验 identity/size/mtime。
源/目标mtime统一 common 的实际 FILETIME 字段，reader 不得以 ABSENT_IN_PLAN 静默跳过源漂移核验：
从绑定输入实际列补只读metadata查询/派生索引，缺证据列成明确 deficit。
禁止重扫源树或将数据库 SHA 用作文件内容 SHA。

## 二、恢复状态与三个中断点

新运行状态绑定 run_id、计划/四份输入/代码摘要、目标卷和根。
错绑定、错目标对象、源变更均拒绝复用。
不盲信 done 表；重启后观察实际目标的 hash/size/type/id/volume，与成功记录及任务意图核对。
已有 alias 核验同实体分组；无关对象拒绝，不能 skipped。没有任务意图的对象不得认领/覆盖。

必须在生产链内故障注入并恢复：
A. 目标无覆盖提交成功、实体完成事务尚未写。
B. 实体完成已写、部分硬链接未创建。
C. 链接已创建、路径完成事务尚未写。
复制意图/临时文件/提交/实体与路径阶段应有可持久化状态，使上述恢复有依据。
源句柄、目标句柄、数据库在异常后关闭；仅清理本任务记录的临时对象。
同时测恢复后内容/身份被篡改、别名坏分组、未知目标，全部明确失败且不覆盖。
正常二次运行可零写入，但只有目标核验通过才能复用。
使用SQLite索引/流式计数，生产不得累积百万 copied/linked 字典列表。

## 三、全计划验收

新增完整验收driver并接production runner/CLI。输入为绑定正式 plan + run-state + observer，不由caller自选子集充当全量。
expected 数量来自绑定plan；checked实体、全部目的路径、目录、链接与unfinished状态核对。
普通文件按唯一目标实体读取hash；同源实体目的路径目标FileId/volume一致，不同源实体不得误合并。
目录与重解析使用各自必需字段，缺对象/额外对象/错误类型/错误链接目标/未完成/错run-id/错plan/错目标卷失败。
局部检查即使无错误也 full_acceptance=false；空/部分清单不通过。
AllocationSize按目标实体去重，与内容字节、空闲变化分列；源/目标分配空间不要求相等。
no-follow目标枚举避免把junction展开计实体。按百万规模streaming/SQLite索引处理，不list全计划。

## 四、正式库适配及测试

reader已用实际path列，但需交付本机真实 PRAGMA/schema/索引及query plan证据：
实体/路径读取有效、mtime证据完整、目录与链接可执行迭代器可用。
E:\BLACKBOX -> \\192.168.100.2\E_DRIVE\BLACKBOX 的source；
选定D路径 -> E:\BLACKBOX_ENGINES目的，D源共享未定仍合同阻塞。不能将桌面的本地D路径当SAM源。
实体无路径、映射越界、缺mtime、路径数不一致均报deficit，不静默continue。
保留现有合并库/备份及16映射，普通统计不变：
files8715067、entities1223721、unique_bytes365007198749、logical_bytes5085136765894、dirs233660、links4825。
四份输入绑定沿用1852合同。不要为进展再次hash9GB输入或全量重建。
全体链接目标/类型/范围/冲突与祖先剩余路径循环检查源码及退出码须完整，不能仅读已有status。

模拟端到端：
真实schema小型SQLite -> production reader/目录链接迭代器 -> production runner -> WindowsBackend(VirtualSyscalls) -> run-state -> 完整验收。
包含两源卷相同内容不同实体、一个实体多硬链接别名、目录及一组重解析链；
目的虚拟对象真实可观察。不要用FakeBackend计数或拼结果字典代替。
逐项测试A/B/C中断、正常二次运行、篡改主文件/alias、缺目录/链接、wrong绑定、空/局部验收以及两种准备期gate。
只写C代码/日志/小型SQLite元数据，业务内容和链接均内存模拟；不做真实C/E文件复制或链接试验。

## 五、完整交付，不只回传几个增量PY

回传目录：
agents/chatgpt/inbox/R9_DESKTOP_FINISH_BATCHES_AND_VERIFIED_RESUME_20261013/
完整源码及全部依赖/common/config/CLI/测试源码；
ZHANGWEI_REPORT.md、FILE_SHA256.json、
逐项TEST_RESULTS_FULL.json（case名称、结果、命令、异常输出）、
RESUME_TEST_TRACE.json、FULL_ACCEPTANCE_TRACE.json、
REAL_PLAN_SCHEMA.json、PLAN_READER_VALIDATION.json、EXECUTOR_READINESS.json。
包在干净目录下载后可import/--help/纯测试，不能偷偷从 C:\LAN_SHARE_REPORT 导入未交付旧模块。
大计划/state DB留C，回传绑定/统计。

未完成任何必需批次、恢复或验收就PARTIAL/IMPLEMENTATION_READY=false；
完整实现及模拟测试完成后供ChatGPT审核，实盘状态仍NOT_RUN。
30分钟上传检查点后可继续同一任务，禁止把只做几行helper当本轮整体完成。
确有外部阻塞列精确项；UNC1326、D share未知、用户格式化尚未发生不妨碍上述离线代码。

不格式化、不真实复制、不真实硬链接/junction试验、不在E写入、不修改SAM源E/D/密码/网络/MWB/P7。
用户本人未来手动格式化台式机E后才进入真实试验。当前COPY_AUTHORIZED=false、FORMAT_DONE=false、FULL_MIGRATION=false。
保留有价值HUB文件，不清空证据。

执行电脑=ZHANGWEI；SAM=HOLD。完成更新INBOX_FOR_CHATGPT.md指向本轮报告。
