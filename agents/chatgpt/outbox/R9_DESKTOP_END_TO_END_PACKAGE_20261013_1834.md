# ZHANGWEI 台式机｜闭合实际执行链并交付完整包

task_id: R9_DESKTOP_END_TO_END_PACKAGE_20261013_1834
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
supersedes: R9_DESKTOP_REAL_IO_AND_ACCEPTANCE_FIX_20261013_1743
SAM: HOLD
FORMAT_DONE=false
COPY_AUTHORIZED=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true

## 审核结果与本轮目标

执行电脑仍是台式机 ZHANGWEI，SAM 停止待命。
上轮的缺字段、ADS/NUL 拒绝、流式结果含 SHA 已修复，ChatGPT 独立复跑 HUB test_r9_copy_body.py 的 7 项测试全通过。
但是 COPY_IMPLEMENTATION_READY=true、ACCEPTANCE_IMPLEMENTATION_READY=true 仍不采纳。当前审核两项均 false。
本轮目标是把上轮已要求的真实后端、计划读取、调度、恢复、验收与 CLI 一次接通，交付完整可下载包；不要仅完成几项 helper 后自报 READY。

现有上轮包：
agents/chatgpt/inbox/R9_DESKTOP_REAL_IO_AND_ACCEPTANCE_FIX_20261013/
完整目录已查：只有 7 个代码/测试文件和 5 份报告 JSON/MD。
FILE_SHA256.json 列出的 r9_formal_executor.py、r9_adapter.py、r9_pilot_common_r9fix.py、test_r9_formal_executor.py 未在本轮目录交付，因而报告的 24 项测试无法从该包完整复跑。
TEST_RESULTS_FULL.json 只有汇总，没有逐项输出。

具体缺口：
- r9_winio.py 只有 declarations_ready、stream_copy_handles、ctypes_buf，未实现实际文件打开/身份核验/关闭、临时创建与无覆盖提交、硬链接/junction、观察器等后端。
- r9_scheduler.run_batch 依赖 backend.copy_entity/hardlink/calls；当前唯一满足接口的类是 FakeBackend，实际 Windows 后端不满足这些接口。
- 没有从真实计划 SQLite 流式产生 entities 的代码，没有持久化恢复、目录/链接调度或磁盘验收驱动。
- accept_batch 是调用外部 observe 的字典遍历，不是完整磁盘验收；hardlink_groups_ok 也未接入验收，且 seen 列表在百万实体下会造成平方复杂度。
- write_entity_bytes 要求 expected_sha256，但冻结清单的元数据证据不等于逐文件内容 hash。必须核对实际字段，给出能使用当前输入的哈希合同。
- plan_validate_links.py 依赖未上传的新 adapter.walk_reparse；只统计 status/映射数量/循环，未提供目标缺失及冲突核查实现。

ChatGPT 独立复现的新失败用例，加入回归测试：
1. accept_batch([], lambda row:{}) -> checked=0, ok=true。
   空计划/部分验收绝不能报完整 PASS。
2. planned 具有 dest_file_id="expected", dest_volume_serial="target"；
   observed 改为 dest_file_id="wrong", dest_volume_serial="other"，其它字段相同；
   accept_on_disk 仍返回 ok=true。目标绑定与目的实体记录不应被忽略。
3. write_chunk 返回 0、commit 不做任何操作，write_entity_bytes 仍返回 3 bytes+sha 成功。
   必须由实际后端完整写入与目标 hash/大小复核共同证明落盘成功，不能以源读 hash 代替目标证据。
以上复现纯函数，没有实际文件复制。
保留正确修复与映射成果，不全量重建计划、不重扫数据。

## 一、实际生产调用链

提供一套满足统一接口的 WindowsBackend，方法可用不同名称但必须在接口矩阵中对应，并实际接到调度器：
- stable_open_source / get_handle_identity / close_handle；
- create_temp_exclusive / write_all / flush；
- copy_entity（用同一稳定源 HANDLE、流式哈希、前后 identity/size/mtime，目标重读 hash，随后无覆盖提交）；
- commit_no_replace / verify_existing_for_resume；
- ensure_normal_directory；
- hardlink（实际 CreateHardLinkW、实际目标卷核验、创建后目标 FileId 分组检查）；
- rebuild_reparse（类型明确的 junction/symlink 实现及创建后目标/类型检查）；
- observe_destination（普通文件/目录/重解析类型、目标卷/FileId、size/AllocationSize、hash/链接目标）；
- enumerate_destination_no_follow（用于缺失/意外对象验收）。

Win32 FFI 的 argtypes/restype、失败返回、短读/短写、EOF 失败、Flush/Close/finally、长路径处理必须实际正确。已有 stream_copy_handles 可保留复用。
不能将上述方法留 TODO、NotImplemented、仅声明 WinAPI 存在或转给尚不存在的回调。
利用现有最新 pilot 的底层助手即可；保留历史 pilot，不改其 1GiB cap、不继承历史 serial/READY/manifest 为正式授权。
helper 的源读 hash 属于源内容证据，目标重读匹配后才能记录成功；失败的临时对象只能按本任务记录识别，不覆盖/删除未知对象。

从 CLI -> gate -> plan entity iterator -> production scheduler -> WindowsBackend -> run-state SQLite -> final observer/acceptance 的完整代码必须存在。
准备期 gate 依旧在第一次 IO 写入前拒绝；两个 bool 和一个任意 dest_binding_id 字符串不能代替实际盘绑定及未来用户确认的新任务合同。
本轮真实后端保持 NOT_RUN；代码可以完整，实际调用不授权。

## 二、与当前计划接通，不另造测试专用计划作为正式输入

继续使用已有：
C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite
实体=1223721、file_paths=8715067、unique_content_bytes=365007198749、
logical_path_bytes=5085136765894、normal_dirs=233660、links=4825。
不要重新 build_plan/unlink 现有 6GB 库。必要派生索引/表事务更新、先确保 C 有备份空间。

编写真正的 SQLite plan reader：
- 从 paths/entities 以及绑定输入实际列取得 source volume+file ID、size、mtime、代表源路径、全部目的路径、目录及链接目标。
- 使用批量流式游标、合适索引或排序流；不得一次读取所有路径/按每个实体全表扫描。
- 明确 E 源 UNC 已知为 \\192.168.100.2\E_DRIVE\BLACKBOX；D 源共享合同未知就单列阻塞，不猜测 D_DRIVE。
- 本轮只验证输入与读取元数据，不访问认证失败源进行业务复制，不重新枚举源树。
- 现有三份 SQLite SHA 及地图 SHA 与前任务一致；package/plan/run-state 记录实际绑定。
- 数据清单若没有每实体预期内容 SHA，采用源稳定同句柄读时计算 SHA、目标重读核对、成功记录保存 SHA、验收按绑定记录核对。不要把数据库文件 SHA 当业务文件 SHA，也不强制事先把全源 hash 一遍导致无法开始。
- 源 metadata ID/size/mtime 对照不能跳过；源实时变化仍为正式阶段阻塞，不宣称旧快照等于现在冻结。

复制调度器实现：普通目录 -> 每源实体一次复制 -> 别名硬链接 -> 重解析链接 -> 完整验收。
实体复制的返回记录必须提供实际目标代表路径及目标身份，硬链接应指向该目标代表文件，不能把源 UNC/源 volume 身份直接用作目的硬链接身份。
保存 SQLite run-state，支持复制后中断、提交后记录前中断、硬链接阶段中断的恢复；重复运行只复核本任务已完成对象，不盲目重做或覆盖未知路径。
处理百万实体的恢复查询与身份分组必须使用索引/set/流式分组；无平方复杂度。

## 三、完整验收

修空输入/部分验收/目标绑定用例。
验收报告必须绑定 run_id、plan digest、四份输入、代码包、实际目标盘身份，检查 expected vs checked 数量及 unfinished state。
SOURCE_ID、DEST_ID 分开，新目标文件不要求与源 FileId 相同；目标身份须与已绑定复制记录相符。
同一源实体的所有目的路径要共享目标 FileId+volume；不同源实体不能误合并。分组检查实际接入完整验收。
普通文件 SHA 是 64 位 hex，记录身份/size 等无效值失败；目录/junction 用对应类型的必需字段，不能强求目录提供文件内容 hash。
空的局部“检查列表”可以无错误返回，但 overall_full_acceptance 必须 false；有计划实体但没检查到不能 PASS。
目标 AllocationSize 按目标实体去重，与源分配空间不要求相等；内容字节/分配空间/空闲差额分列。
实际只读观察器检查缺路径、意外路径、错误类型、链接目标、硬链接分组和全部唯一实体 hash。不得仅通过比较 caller 填的字典宣称完整验收。

## 四、计划校验与预检

将缺失的最新 adapter/CLI/测试一起交付。
plan_validate_links 做完整对象目标解析、范围/类型/路径冲突及祖先+剩余路径循环检查，接入计划判定与退出码；不能只查数据库已有 status。
16 条目标的覆盖以已绑定 delta targets 完整枚举状态/计数/文件集合为依据，不只 count>0；全体 4825 条目标解析至已绑定普通对象或有效链接。
独立保留离线闭包与实时源树有效性区别。
preflight 分列 INPUT_VALID、PLAN_VALID、SOURCE_ACCESS_VALID、DEST_BINDING_VALID、overall_copy_ready；SOURCE_ACCESS 1326 时不能总成功。
本轮 FORMAT_DONE=false，overall_copy_ready=false。不要让用户现在格式化来代替代码缺口。

## 五、用实际链路做模拟，完整上传

测试模拟层放在 Win32 系统调用/文件系统观察下面，生产 WindowsBackend、生产 plan reader、生产 scheduler、生产验收驱动都使用同一套实际代码。
使用内存虚拟文件/虚拟 HANDLE 与小型 C SQLite 元数据；不执行真实文件复制、hardlink/junction，不在 E 写任何东西。
不要仅以 FakeBackend.copies.append 来证明生产链路已通。
测试用专用合同注入模拟盘绑定；生产入口固定准备期任务状态，不得因模拟合同打开真实后端。
必测：分块实体、短写/EOF 错误、目标 hash 不同、源变化、同实体多路径、不同实体同内容、未知目标拒绝、祖先 reparse 逃逸、
断点恢复三种中断、wrong target binding、空/部分验收、硬链接分裂/误合并、目录/链接类型、未授权生产后端 syscall 次数=0。
不增设新服务/权限平台，个人双机简单本地脚本与 SQLite 状态即可。

回传：
agents/chatgpt/inbox/R9_DESKTOP_END_TO_END_PACKAGE_20261013/
- ZHANGWEI_REPORT.md（逐项接口/调用链/阻塞，不仅 PASS 汇总）。
- 全部生产模块、依赖、配置、测试源码、入口命令及逐项 TEST_RESULTS_FULL.json。
- FILE_SHA256.json，逐个文件真实 hash；清单中的文件全部上传。可附完整 zip，但不能只提供未上传文件的 SHA。
- BACKEND_INTERFACE_MATRIX.json：每项方法所在文件/符号、调用方、对应测试。
- PLAN_READER_VALIDATION.json：真实库只读查询计数/样例/索引查询计划（有限输出，不暴露凭据）。
- PLAN_VALIDATION.json 与可复跑检查脚本、EXECUTOR_READINESS.json、明确 SOURCE_PREFLIGHT_BLOCKERS.json。
大计划与运行 DB 留 C，回传摘要/绑定即可。

同一任务内持续完成以上既有范围。30 分钟回传检查点可以继续，纯代码未完成时不自报 READY、不等每个函数的新指令。
真正外部阻塞按项列出，源认证不影响离线代码完成。
代码完整且生产链路经底层模拟后可自报 IMPLEMENTATION_READY，等待 ChatGPT 审核；实盘永远另列 NOT_RUN。
用户本人未来手动格式化台式机 E 后才做真实试验。禁止自动格式化、真实复制、C/E 实盘复制或链接试验，禁止修改源盘/账号/网络/MWB/P7。
保留当前有价值 HUB 证据，仅更新任务入口。

执行电脑=ZHANGWEI；SAM=HOLD。
完成后更新 INBOX_FOR_CHATGPT.md。未格式化、未复制，COPY_AUTHORIZED=false。
