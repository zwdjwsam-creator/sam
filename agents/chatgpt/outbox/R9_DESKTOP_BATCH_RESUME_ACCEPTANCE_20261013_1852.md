# 台式机 ZHANGWEI｜正式计划适配、目录链接、恢复与全计划验收

task_id: R9_DESKTOP_BATCH_RESUME_ACCEPTANCE_20261013_1852
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
supersedes: R9_DESKTOP_PRODUCTION_CHAIN_REWORK_20261013_1842
SAM: HOLD
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true

## 已审核进展

本轮回执 PARTIAL、IMPLEMENTATION_READY=false 与源码一致。
ChatGPT 独立复跑 test_chain_reader_runner_backend，非空测试链 reader -> production_run -> WindowsBackend(VirtualSyscalls) 通过。
真实 WinAPI 模块没有执行；复跑时仅替换 common 导入，未替换 reader/runner/backend 逻辑。小型 SQLite 是测试元数据，业务文件全在内存。
copy_entity(entity) 签名已统一、默认 Win32Syscalls 已有实际打开/读写入口、目标记录不再直接复用源 FileId，这些成果保留。
下一轮仍由 ZHANGWEI 执行，SAM 无任务。

还没有闭合的实际缺口：
- WindowsBackend.hardlink 只观察代表文件并返回 alias 的身份字典，没创建别名；独立观察 alias 返回 MISSING。测试只断言返回字典，未观察别名对象。
- Win32Syscalls 没有 observe 方法，copy_entity 提交后调用 self.sc.observe 会报错；真实 observer/硬链接/junction/目录仍待实现。
- read_executable 查询 paths.source_path/dest_path；HUB 已发布正式 plan schema 只有 paths.path/source 等列。按此真实 schema 的夹具复现 OperationalError: no such column: source_path。
  目前测试另造 source_path/dest_path/mtime 列，不能证明已有 6GB 正式计划已适配。先核对本机 PRAGMA 实际列；若本机已做派生改造，上传该迁移与证据。
- Win32 common.handle_identity 的时间字段与当前 mtime 字段须规范化；当前 copy_entity 缺读取后源身份核对，不能只检复制前一次。
- runner 的已有 done 项直接信任，不观察目标；没有三种中断恢复。
- allows_write 仅按 SIMULATED_CHAIN+任意 volume 字符串判断，未限制必须注入虚拟 syscall，存在模拟合同误接真实后端的路径。准备期需先封住这条路径。
- 全计划验收/目录批次及 CLI 完整包仍未交付。状态继续 PARTIAL，不自报 READY。

## 1. 正式计划 reader 适配（先完成，防止继续只测假 schema）

保持现有：
C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite
不得 unlink/重建此库，不重新扫描源树。三份输入与 R3 地图 SHA 沿用前任务。
输出本机 PRAGMA table_info(paths/entities/links) 和现有索引的有限证据。
基于实际列写 reader：从路径来源 E/D/delta、实体 key、绑定输入的 size/mtime、原始 path 派生 source_path、dest_path、别名目的路径。
E:\BLACKBOX -> 已知 E 源 UNC / 目的 E:\BLACKBOX；
选定 D 范围 -> 目的 E:\BLACKBOX_ENGINES；D 源共享未知作为合同阻塞，不能猜 D_DRIVE。
保持源和目的身份分开，统一 mtime_ft 的类型/精度，并核验复制前后同一稳定 HANDLE 的 source identity/size/mtime。
必要 C 派生表/索引先检查备份空间、事务更新，或只读 join 输入；不要把整个库重新复制/扫描用于凑进展。
测试夹具必须采用实际 plan schema，测试 metadata 加载/路径映射/代表路径选取/硬链接别名数。缺身份/mtime或实体无路径明确报 deficit，不静默 continue。
生产查询有合适索引或排序流；禁止按每个实体全表扫描或一次 list 全计划。
真实库只读验证路径/实体总数，以及 E、D、delta 各有限代表样例和 query plan。

基线：files=8715067、entities=1223721、unique_bytes=365007198749、logical_bytes=5085136765894、dirs=233660、links=4825。
不硬编码 PASS，统计变动须说明来源；16 映射和42文件覆盖保留。

## 2. 目录/硬链接/重解析真实实现及批次

补全同一 Win32Syscalls/VirtualSyscalls 协议：
ensure_directory、hardlink、create_reparse/read_reparse、observe、enumerate_no_follow、dest_volume_identity，以及实际无覆盖提交。
Win32 方法实际实现，虚拟方法产生真实可观察的虚拟对象，不能仅计数或返回身份字典。
明确 CreateHardLinkW 参数顺序、MoveFileW 的 ctypes 声明/错误、文件句柄关闭；创建后实际观察检查。
硬链接调用后观察 alias 必须 PRESENT，目标 FileId+volume 与代表一致；不同源实体不能错误共享目标实体。
目录和重解析类型分别观察；已有非本任务对象冲突拒绝，不盲目覆盖。普通对象写入路径祖先 reparse 检查在生产路径执行。
重解析链接按完整迁移后路径/目标创建，校验对应 NTFS 类型，不能回指 SAM UNC/旧 D；不跟随链接复制实体。
生产顺序：普通目录 -> 实体复制 -> 硬链接 -> 重解析链接 -> 验收。
状态记录分清实体/路径/目录/链接；prepare gate 阻止本轮任何实盘写入。
hash 为源稳定读流与目标实际重读匹配后记录，目标缺失/尾部额外字节/不同 hash 都失败。
1KiB 循环只是当前测试用配置；生产使用合适块大小，保持 bounded streaming，不能缓存全实体。

准备期模拟隔离：
SIMULATED_CHAIN 仅接受 VirtualSyscalls 或明确的测试注入协议，拒绝默认真实 Win32Syscalls，不因合同字典字符串打开真实后端。
PREPARATION_ONLY + 两个 bool、SIMULATED_CHAIN + 真实后端 两种入口均须在首次写入前拒绝，spy 写入次数=0。
未来真正授权分支需独立用户格式化确认与实际盘绑定，但本轮不启用。
真实实现可以写完整，真实 syscalls 不执行。

## 3. 三种中断恢复与状态绑定

用 C 的 SQLite run-state，绑定 run_id、plan/input/code digest、目标盘与目的根。错绑定拒绝复用。
三种故障点必须在 production runner 内注入并恢复：
A. 临时文件完成/无覆盖提交成功，但实体 done 事务未写。
B. 实体 done 已写，若干硬链接别名尚未完成。
C. 链接已实际创建，路径完成记录尚未写。
恢复观察实际对象的类型/身份/hash/目标，与本任务持久化 INTENT/COMMITTED 记录对照；
已完成项必须复核，错 hash/错 FileId/未知目标不能跳过或覆盖。
缺任务意图的目标仍未知；不能按“路径存在”就认领。
应有临时/意图阶段的可恢复记录，不能只能处理正常完成后 done 表。
每个阶段事务一致，异常 finally 关闭数据库和句柄。
使用流式统计而非 copied/linked 全量列表存百万结果。

## 4. 全计划验收 driver

完成实际 plan + run-state + backend observer 的验收驱动并接到 runner/CLI，不能仅调用外部传入字典。
expected 数量来自绑定完整计划，checked 与未完成状态完整核对；局部或空计划不得 overall_full_acceptance。
普通文件实体逐一 hash；所有目的路径核验覆盖与硬链接组；不同实体误合并失败。
目录、junction/symlink 用类型专属必需字段；不存在路径观察 MISSING，不能视为零字节文件。
额外对象/no-follow 枚举、错误类型、链接目标/类型、wrong run_id/plan/target volume、unfinished 状态纳入结果。
目标内容字节/AllocationSize 按实际目标实体去重，源/目标 AllocationSize 不要求相等。
保持百万规模 streaming/set/SQLite 索引，accept_batch 不应 list 全部路径。
LINK/PLAN 检查补完整：目标缺失/范围/冲突、祖先剩余路径循环，附源码和退出码，不仅检查已有 status。
源1326与D share未知只单列外部阻塞，不能宣称实时源已冻结或完整复制准备就绪。

## 5. 一次完整验证与交付

小型实际-schema SQLite + production reader/runner/backend(VirtualSyscalls) + run-state + 完整验收贯通。
包含普通目录、两个源实体（相同内容但源卷不同）、一个实体多别名、一个目录重解析链；
虚拟目的对象实际存在，实际观察身份/类型/hash，不能只检查方法返回值。
逐项覆盖上述三故障点及恢复、缺 alias、坏目标、源前后变化、不同源身份误合并、部分清单、空清单、未知目标、两个 gate拒绝场景。
底层模拟不执行业务文件复制、Windows hardlink/junction 实盘测试；小 SQLite/代码日志可写 C。
Windows 实盘 IO 一律 NOT_RUN，不在 E 写任何东西。

交付：
agents/chatgpt/inbox/R9_DESKTOP_BATCH_RESUME_ACCEPTANCE_20261013/
ZHANGWEI_REPORT.md、全部生产模块/common/配置/CLI/测试源码、
逐项 TEST_RESULTS_FULL.json（命令、各case、failure输出，不仅 PASS bool）、
FILE_SHA256.json、REAL_PLAN_SCHEMA.json、PLAN_READER_VALIDATION.json、
RESUME_TEST_TRACE.json、FULL_ACCEPTANCE_TRACE.json、EXECUTOR_READINESS.json。
大计划/state DB 留 C。包中的依赖完整可下载，干净目录可 import --help/跑纯测试；不能依赖未说明的 C:\LAN_SHARE_REPORT 中旧模块。
回传 current git commit/blob 或完整文件SHA，便于独立复跑绑定同版代码。

本轮既有代码范围内连续完成，30分钟可以上传进度检查点后继续，不为每个 helper 等下一条指令。
没做完就如本轮准确报告 PARTIAL/IMPLEMENTATION_READY=false，列清已实现/已测/未实现；不能把 NOT_RUN 误当未实现。
完成完整代码/模拟链后交 ChatGPT 审核，仍不得真实写入。
有价值输入、代码及历史证据保留，不清空 HUB。

执行电脑=ZHANGWEI；SAM=HOLD。
未格式化、未复制。COPY_AUTHORIZED=false；FORMAT_DONE=false；FULL_MIGRATION=false。
用户本人未来手动格式化台式机 E 后才开展真实试验。本轮不格式化、不真实文件复制、不在 C/E 做真实链接试验，不修改 SAM 源盘/凭据/网络/MWB/P7。
完成后更新 INBOX_FOR_CHATGPT.md 指向本轮报告。
