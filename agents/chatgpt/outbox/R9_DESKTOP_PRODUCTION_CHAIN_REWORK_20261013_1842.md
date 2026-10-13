# ZHANGWEI 台式机｜真实后端及生产链返工

task_id: R9_DESKTOP_PRODUCTION_CHAIN_REWORK_20261013_1842
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
supersedes: R9_DESKTOP_END_TO_END_PACKAGE_20261013_1834
SAM: HOLD
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true

## 审核结论

1834 回执“CLI gate、plan reader、scheduler、WindowsBackend 接到同一条链”的结论不成立。
本轮代码仍 PARTIAL；COPY_IMPLEMENTATION_READY=false、ACCEPTANCE_IMPLEMENTATION_READY=false。
已经修好的空验收/错目标绑定/短写判断保留，16 链接映射及普通统计保留。

禁止实盘执行不等于禁止实现真实 IO 代码。
准备期应由入口 gate 阻止实际调用；不能用缺少真实实现、或 _real_blocked 永久抛异常来替代权限控制。
本轮完成真实实现和整个调用链，真实文件复制/链接试验仍 NOT_RUN。
前任务 R9_DESKTOP_END_TO_END_PACKAGE_20261013_1834 的既有范围继续生效，这里列明确未做到的部分及验收证据。

## 可复现的生产链失败

审核源码目录：
agents/chatgpt/inbox/R9_DESKTOP_END_TO_END_PACKAGE_20261013/

1. run_batch 调用 backend.copy_entity(entity)，但 WindowsBackend.copy_entity 必需参数为 entity,payload,identity。
ChatGPT 用 VirtualSyscalls、模拟 WRITE_AUTHORIZED 合同和一个非空实体连接两者，得到：
TypeError: WindowsBackend.copy_entity() missing 2 required positional arguments: 'payload' and 'identity'
测试 test_virtual_backend_hashes_destination 是直接传 payload 调单个函数；没有测 reader -> scheduler -> WindowsBackend。

2. WindowsBackend() 的默认 sc 是字符串 "REAL_NOT_RUN"。stable_open_source -> _real_blocked -> RuntimeError REAL_IO_NOT_RUN。
当前真实后端不存在；r9_winio.stream_copy_handles 未被 WindowsBackend 使用。
copy_entity 操作 self.sc.files 并以 len(payload) 控制，仍是内存模拟，而非通用生产路径。
hardlink/rebuild_reparse 仅计数后返回字典，没有系统调用。

3. ChatGPT 给实体 logical_size=999，却注入 3 字节 payload，copy_entity 返回 bytes=3 成功。
copy 结果 dest_identity 直接复用了源 identity，不是目标句柄观察结果。
observe_destination("不存在的路径") 返回正常 file/size0/空内容 hash，未报告 MISSING。

4. reader.iter_entities 只产 entity_key/volume/file_id/size/path_count/source_unc_note，
没有 representative、source_path、dest、extra_paths、mtime；无法驱动当前 scheduler/backend。
“LIMIT 3 表头抽样”只证明 entities 表能读取，不能证明实体及路径已可执行。

5. CLI copy 实际只调用 run_batch(iter(()), FakeBackend(), PREPARATION_ONLY) 后拒绝，未使用 reader 或 WindowsBackend。
入口拒绝是正确的，但不能据此称未来获授权的生产路径已接通。

6. 没有运行状态 SQLite、恢复实现、普通目录/重解析批次调度、全量磁盘观察/验收驱动。
accept_batch 把 planned_rows 转 list，全量内存化；默认 expected_count=len(rows)，仍可把任意非空子集称 overall_full_acceptance。
目录/junction 还套用文件 hash 必需字段；完整组验收尚未接到 driver。

## 本轮必须交付的实现

一、统一真实后端协议
提供 Win32Syscalls（真实调用）与 VirtualSyscalls（测试注入）共享相同协议，WindowsBackend 默认选真实协议；
实际 task gate 在外层首个写入前拒绝，本轮不执行真实协议。
Win32Syscalls 中实现真实 open stable/read identity/create exclusive temp/write all/flush/close/hash observer/no-replace commit/mkdir/hardlink/reparse/read-reparse/no-follow enumeration。
所有函数有具体 WinAPI 或明确的 Windows 本地实现，不能调用不存在的方法、留下 TODO 或仅返回成功字典。
可复用最新 pilot common 的底层 helpers，实际上传 common 或提供精确已上传路径+SHA且下载脚本可自动取得；
历史 manifest、1GiB cap、806508DF/旧 READY 都不能作为正式授权。

WindowsBackend 只通过该协议操作，不访问 VirtualSyscalls.files，不接收整文件 payload。
统一 copy_entity(entity) 签名；源文件由 source_path 打开，大小来自绑定计划、identity/mtime 与实际源 HANDLE 对照。
稳定句柄同一读流分块计算源 hash；目标临时对象实际写入、Flush、关闭并重读 hash/大小，核对后无覆盖提交。
没有预存业务 hash 的清单允许读流计算并绑定成功记录，不强制 metadata 表提供不存在的 hash，不把 DB 文件 hash 当内容 hash。
所有 HANDLE finally 关闭，EOF 错误/短写/源变化/hash 失败阻断成功；返回实际目标身份，不能拷贝源身份冒充。
hardlink 真正创建并查验目标卷和 FileId；reparse 真正创建对应类型并查验目标；不存在路径观察返回 MISSING。
路径检查及祖先 reparse 防逃逸必须在生产路径执行，不能只有独立 helper 的测试。

二、完整 reader 与实际 scheduler/CLI
以现有6GB计划及三份绑定输入生成可执行实体：
entity_key、source identity/size/mtime、代表 source_path、代表 dest_path、全部别名 dest_paths；
普通目录与链接另有可执行迭代器。字段名称可以自选，reader/scheduler/backend 必须统一。
用真实计划 schema 的小型 SQLite 数据夹具验证，不能手工编一个跳过 reader 的 entity 就称端到端。
真实库有限抽样应显示目的路径和 metadata 实际查询；必要缺 mtime 的派生读取必须实现，不重新重建整个计划/扫描源树。
E/D 路径映射明确；D source share 未知保留合同阻塞，不猜。
生产 scheduler 正确使用 copy_entity 返回的目标代表路径及目标身份创建硬链接，不能把 source representative 当目标路径。
顺序：普通目录 -> 实体 -> 硬链接 -> 重解析 -> 完整验收。暂停后恢复记录与目录/链接完成状态保存 C 的 SQLite。
提交完成但状态未写、实体完成但别名未完、创建链接后中断这三种状态要能核验恢复，不覆盖未知对象。
百万实体流式读取/处理，SQLite 索引或排序流，不能一次 list 全部路径。
CLI 使用同一 production runner；准备期在进入任何写入前拒绝。测试注入模拟 syscalls/模拟目标绑定后，必须调用这一 production runner，不能换 FakeBackend。
不设计新的服务或权限平台，使用简单任务合同和本地 SQLite 即可。

三、真正验收 driver
输入是绑定 plan+run-state，不是 caller 自选的局部 rows。
统计 expected/checked 实体、路径、目录、链接与 unfinished；不能默认以局部列表长度充当全计划预期。
源 identity 与目的 identity 分开。绑定目标身份、同实体目标硬链接组、不同实体误合并实际接入 driver。
普通文件 hash、目录类型、junction/symlink 目标及类型分别定义必需字段；缺失/意外对象/错误类型必须失败。
按唯一目标实体读 hash 和 AllocationSize，逻辑字节/分配空间/空闲差额分列。
完整验收只对绑定完整计划 true；局部检查可以无错误但 full_acceptance=false。
不要为了让当前观察器通过而减少必需身份字段。

四、测试生产链及完整包
最低通过条件：小型 plan SQLite -> production reader -> production runner -> WindowsBackend(VirtualSyscalls) -> 虚拟目标观察器 -> 完整验收，实际运行成功。
然后在同一链路注入：
错误计划 size/源 mtime/身份、源变化、短写、EOF 失败、目标 hash 不同、缺目标、错目标身份、
同实体多路径、跨源卷同内容不同实体、错误硬链接组、目录/链接、部分计划、三种中断恢复、未知目标拒绝。
准备期用 WindowsBackend(真实协议) 的 spy 确认写入 syscall=0，不实际调用 Win32 写入。
不能以直接 backend.copy_entity(entity,payload,identity) 或 FakeBackend.copies.append 的成功代替此最低条件。

修 PLAN_VALIDATION：完整目标缺失/范围/冲突/祖先剩余路径循环校验，附可重跑源码和退出码。
1834 原有基线/16映射保留，不再重复大量hash/统计来替代代码完成。
SOURCE_LIVE_PREFLIGHT_PENDING、D share未知、格式化未做单列；这些外部阻塞不影响完成离线生产代码。

## 回传与状态

交付：
agents/chatgpt/inbox/R9_DESKTOP_PRODUCTION_CHAIN_REWORK_20261013/
ZHANGWEI_REPORT.md、完整全部模块/common/配置/下载或运行入口、
逐项测试源码及 TEST_RESULTS_FULL.json、FILE_SHA256.json、
PRODUCTION_CHAIN_TRACE.json（各阶段实际调用、输入输出字段、虚拟对象状态与恢复结果）、
PLAN_READER_VALIDATION.json、EXECUTOR_READINESS.json。
清单所有模块必须实际存在可下载，干净目录只下载该包即可 import --help 和跑纯测试。
生产链跟踪必须包括非空实体和硬链接/重解析，不能测试 empty iterator 就称“已接通”。
把总完成状态与“修了一个回归用例”区分，未完整即 PARTIAL，IMPLEMENTATION_READY=false。

同任务内继续完成，不每加几行就回报完成并等待下一轮。30分钟可上传检查点，继续已授权代码范围。
真正无法继续的外部输入/合同矛盾列精确阻塞；不要用永久 REAL_NOT_RUN 空实现解决准备期权限限制。
完成后等待 ChatGPT 代码审核，禁止进入写入阶段。

本轮及前任务的边界不变：
不格式化、不实际文件复制、不在 C/E 做真实硬链接或 junction 试验，不在 E 写入、不修改 SAM 源 E/D/凭据/网络/MWB/P7。
用户本人未来手动格式化台式机 E 后才能进入真实试验。
COPY_AUTHORIZED=false；FORMAT_DONE=false；FULL_MIGRATION=false；Windows 实盘写入 NOT_RUN。
执行电脑=ZHANGWEI；SAM=HOLD。更新 INBOX_FOR_CHATGPT.md 指向回执。
