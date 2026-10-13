# 台式机 ZHANGWEI｜完成重解析批次、持久化恢复与全计划验收

task_id: R9_DESKTOP_CLOSE_REPARSE_RESUME_ACCEPTANCE_20261013_1910
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
supersedes: R9_DESKTOP_FINISH_BATCHES_AND_VERIFIED_RESUME_20261013_1902
SAM: HOLD
IMPLEMENTATION_READY=false
FORMAT_DONE=false
COPY_AUTHORIZED=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true

## 本轮审核通过的进展

1902 的 PARTIAL 状态正确。
ChatGPT 独立复跑当前非空 reader/runner/backend 测试通过，并分别注入四种篡改：
主文件内容 -> RESUME_DEST_MISMATCH；
主文件 FileId -> RESUME_DEST_MISMATCH；
alias FileId / alias volume -> RESUME_ALIAS_MISMATCH。
准备期真实后端、SIMULATED_CHAIN误接真实后端均拒绝；Win32写入次数0。
普通目录在模拟合同中创建可观察。这些修复保留，不重新改已经通过的流程。

下一轮仍由ZHANGWEI执行，SAM停止待命。
范围沿用1902任务，集中完成剩余三项；不要重扫源树、重建6GB计划或重复hash9GB输入。
真实Windows实现可以编写并以底层模拟测试，但本轮真实业务复制、硬链接/junction试验全部NOT_RUN。

## 1. 重解析批次接入生产链

为reader增加绑定plan.links的迁移后link_path、target及类型迭代器，链接目标来自已绑定映射，不猜测路径。
Win32Syscalls与VirtualSyscalls都实现create/read reparse及no-follow枚举；
WindowsBackend封装实际创建后类型/目标查验；
production runner在目录、实体、硬链接完成后按依赖序创建重解析并保存路径状态。
保持4825计划链接、16条D→E overlay与42文件覆盖；循环/目标缺失/范围冲突仍阻塞，不只看数据库status。
实际Win32/NTFS junction/symlink实现必须存在；虚拟实现创建可观察链接对象，不能仅return字典。
链接目标只到目的E:\BLACKBOX / 选定E:\BLACKBOX_ENGINES，不能回指SAM源UNC/旧D。
观察与枚举不跟随链接，不把链接指向内容再次复制。

普通目录批次还需由绑定plan生成，不仅靠测试合同directories手填。
存在对象必须检查类型；已有file不能ensure_directory成功。生产路径祖先reparse检查照1902要求接入。

## 2. A/B/C持久化中断恢复

当前done表仅记录正常复制完成，没有run绑定、提交意图及链接阶段。
添加简单C盘SQLite状态模块即可，不引入服务/权限平台。

run绑定：run_id、plan/四份输入/code摘要、目的盘和根。错绑定拒绝。
阶段至少能表达：实体复制意图/临时对象、提交、实体完成、每个alias及重解析意图/完成。
在外部动作前持久化本任务意图；动作后核验并提交阶段完成事务。

真实生产runner内注入故障并恢复：
A. 代表目标已无覆盖提交，但实体完成事务尚未提交。
B. 代表实体完成已提交，但只有部分alias创建。
C. alias或重解析链接已创建，但该路径完成事务尚未提交。

恢复根据本任务持久化意图及实际hash/size/type/目标FileId+volume/重解析目标核验。
缺意图的对象未知，拒绝认领/覆盖；有意图但对象坏也拒绝。
恢复成功不能重复复制已核验实体或重建已核验链接；只补确实未完成部分。
正常二次零写入和篡改拒绝保留，但不能替代A/B/C故障点验证。
状态DB与所有句柄异常finally关闭；生产流式计数，不存百万copied/linked列表。

## 3. 全计划验收driver完成并接CLI/runner

输入是绑定完整plan+run-state+真实backend observer，不由caller自选列表定义“全量”。
expected entities/普通路径/目录/链接来自计划，checked和unfinished完整核对。
类型专属校验：
普通文件按唯一目标实体hash；所有alias检查同目标FileId+volume、不同源实体不误合并；
目录检查directory；
junction/symlink检查类型与迁移后目标；no-follow枚举额外/缺失/错误类型对象。
错run/plan/code/目的卷、空/部分验收、缺记录、unfinished、错误目标全部full_acceptance=false。
AllocationSize按目标实体去重，与内容字节、空闲变化分列，不要求源/目标AllocationSize相等。
正式百万规模streaming/SQLite索引；不要list全部实体/路径。

必须补真正Win32观察字段：当前Win32Syscalls.observe仅status/path，无法取得目的身份/hash/type/AllocationSize，不能支撑实盘复制记录或上述验收。
用实际WinAPI helper实现身份/时间/类型/必要hash及重解析读取，只有错误2/3算MISSING，权限/IO错误是ERROR。
观察器以底层WinAPI模拟测试输出字段，不能仅证明VirtualSyscalls的字典有字段。
copy同一源HANDLE在复制前后核验身份/大小/FILETIME；当前只有复制前核验，应接入后核验。
reader mtime=ABSENT_IN_PLAN不能静默跳过；从绑定输入实际schema补只读metadata查询/派生索引，缺证据明确阻塞。
这都是已要求的剩余完整性，不新增业务扫描。D share未知/UNC1326单列外部阻塞，不用本地D路径冒充SAM源。

## 验证与完整包

使用实际schema小型SQLite -> production reader/目录链接迭代器 -> runner -> WindowsBackend(VirtualSyscalls) -> run-state -> 全计划验收。
包含普通目录、两个跨源卷同内容不同实体、一实体多alias、有效重解析链；
观察虚拟目的对象真实存在、身份/类型/内容/目标匹配，不仅方法返回成功。
分别注入A/B/C、恢复后篡改、未知目标、目录类型错误、坏链接目标、缺alias、部分计划。
确保PREPARATION_ONLY和SIMULATED_CHAIN+真实Win32均首个写入前拒绝，spy syscall=0。
允许C代码/日志/小SQLite测试元数据，所有业务内容/链接内存模拟。禁止真实文件复制或链接试验。

真实库只读有限查询证据：PRAGMA/索引/query plan、metadata字段来源、实体/路径/目录/链接计数。
基线files8715067、entities1223721、unique_bytes365007198749、logical_bytes5085136765894、dirs233660、links4825。
不为了报告进展重建/重新hash大输入。派生改造必要时事务备份，保留已有输入。

回传完整目录：
agents/chatgpt/inbox/R9_DESKTOP_CLOSE_REPARSE_RESUME_ACCEPTANCE_20261013/
ZHANGWEI_REPORT.md、
全部模块/实际依赖common/配置/CLI/测试源码、
FILE_SHA256.json、
TEST_RESULTS_FULL.json（逐项case、结果、命令、错误输出）、
RESUME_TEST_TRACE.json、FULL_ACCEPTANCE_TRACE.json、
PLAN_READER_VALIDATION.json、EXECUTOR_READINESS.json。
依赖完整可下载，在干净目录可import、--help及复跑纯测试。不能只回传几个增量PY，或依赖C中未交付旧模块。
大plan/state DB留C，摘要绑定上传即可。

不必为每个helper结束任务等待下一轮。本轮连续完成上述剩余范围；
30分钟可上传检查点后继续，不以仍缺三项的状态称“整体完成”。
完成或真正被外部输入阻塞时回传。仍有未实现即PARTIAL/IMPLEMENTATION_READY=false；完整实现与模拟链完成也须ChatGPT审核。
实盘NOT_RUN独立写，不以实盘未授权代替真实函数实现。

执行电脑=ZHANGWEI；SAM=HOLD。
COPY_AUTHORIZED=false；FORMAT_DONE=false；FULL_MIGRATION=false。
不格式化、不真实复制、不在C/E做实盘链接试验、不在E写入，不改SAM源盘/密码/网络/MWB/P7。
用户本人未来手动格式化台式机E后才进入真实试验。
完成更新INBOX_FOR_CHATGPT.md。保留有价值输入、代码和验收历史。
