# ZHANGWEI 台式机｜严格验收及真实 Win32 接口修复

task_id: R9_DESKTOP_STRICT_ACCEPTANCE_WIN32_FIX_20261013_1934
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
supersedes: R9_DESKTOP_CLOSE_REPARSE_RESUME_ACCEPTANCE_20261013_1910
SAM: HOLD
IMPLEMENTATION_READY=false
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true

## 已审核成果

本轮完整包比此前交付完整，FILE_SHA256.json 中20个文件的SHA与字节全部匹配。
ChatGPT独立复跑全部33项测试通过：在Linux审阅环境禁止任何原生WinAPI调用，仅为模块加载模拟DLL声明，并将winio路径解析设为PureWindowsPath以符合Windows语义。真实IO未测。
A/B/C故障恢复、重解析/目录模拟、正常零写入、篡改拒绝、准备期隔离已有实现和通过证据，保留不回退。
SIMULATED_COMPLETE_PENDING_REVIEW准确，仍IMPLEMENTATION_READY=false，尚不能进实盘。

下一轮仍由ZHANGWEI执行，SAM待命。只修下述源码里已复现/可直接定位的缺口，不增加源扫描或新的业务功能。

审核基线：
agents/chatgpt/inbox/R9_DESKTOP_CLOSE_REPARSE_RESUME_ACCEPTANCE_20261013/
r9_acceptance.py SHA256 d3fe77b0754b82a83556bd044e4f306c15a34d83435628a6db90ec854c8fac52
r9_runner.py SHA256 7c14f2148ae893e0bddb66e91805393d9e5bdbd77de03a21a9d7f44ab3bc38db
common SHA256 bc969b160ca161b682637e839f283370ff1e41b4cf4f94ae1d8c208334259a87

## 1. 修四类完整验收误通过

复现方法使用test_r9_close._plan/_contract/_backend，先正常production_run，再对虚拟对象或plan做单一修改，调用full_acceptance：
A. a.bin与z-link.bin都移除file_id/volume_serial；
B. realdir的object_type设None；
C. jump的reparse_target设None；
D. 给entities增加('X','orphan',99,1,'t1')，不给paths。
四种当前都返回full_acceptance=true、reasons=[]。

原因与要求：
- SQL != NULL 的结果不会计入WHERE。类型/目标/身份等必需字段先显式验证非NULL/非空/有效值，再比较。缺字段必须失败，不能依赖COUNT DISTINCT忽略NULL。
- 普通文件必需实际sha256、有效目标FileId/volume、size、AllocationSize、type；目录/重解析按对应类型定义必需字段。ERROR/MISSING与PRESENT缺字段分开失败。
- 每个目标卷须对照run.dest_volume；不能只要求各alias相互相等。
- 每个实体目标身份/hash/size对照stage成功记录，不能只比较hash、不核验目标身份。
- expected_entities来自完整entities表，孤立实体必须PLAN_ORPHAN_ENTITY，不通过WHERE EXISTS把它排除；reader没有paths不能静默continue。
- 实际路径数与实体path_count、普通文件数量等完整计划计数核对；遇映射冲突/重复目的路径不可INSERT OR REPLACE覆盖后缩小预期。
- state完成项不能按数量顶替：逐实体/路径匹配计划key，拒绝缺项/额外完成实体；run缺失/字段空值必须失败，bind_run(None)不能形成可“完整验收”的无绑定运行。
- wrong run/plan/code/目标根/卷拒绝；计划摘要必须有实际计算/绑定证据，不能仅比较caller重复传入的"plan"字面量。

新增上述四个回归测试，再补同内容替换目标FileId、全体目标换错卷、缺run、缺AllocationSize、path_count不一致及非计划DONE实体顶替缺项。
保持正常A/B/C及无错完整验收通过，不通过删除原断言或减少必需字段来放行。

## 2. 修实际句柄时间/身份与metadata连接

当前Win32Syscalls.identity直接返回common.handle_identity；
common返回mtime_ft，没有mtime；copy_entity比较ident.get("mtime")，而reader.lookup_mtime优先返回mtime_utc/mtime_iso字符串。
因此虚拟"t1"测试可通过，实际正确文件会出现字段/表示不一致；读取后时间核验也可能None==None。

统一canonical Win32句柄证据与清单时间对比：
- 将FILETIME、ISO UTC/时区格式按已有common.compare_mtime_manifest_vs_handle / filetime_to_utc_datetime等助手正确比较，避免重复造不一致转换。
- 单一规范源identity（vol DWORD/FileId/size/mtime_ft），保留来源字段。前后同HANDLE比较实际mtime_ft，缺mtime字段必须失败。
- reader从真实绑定schema取字段，schema解析/表名/列名缓存，路径查询走索引；不每实体反复PRAGMA，不重扫业务树。
- E base/delta/D的实际mtime取有限样例并在底层假WinAPI真实返回shape上验证，不再用人为"t1"证明真实接口匹配。
- 参考用例：2026-10-13T00:00:00+00:00 对应 FILETIME 134363232000000000，等价应通过；同时间+08:00/Z也应通过；真实漂移/缺字段失败。按原记录精度比较，不任意放宽2秒。
- 不将DB文件SHA当实体内容SHA。

## 3. 修重解析实际创建/读取及Win32包装

现有虚拟协议覆盖了算法，但底层假kernel测试没有验证真实wrapper的参数/句柄行为：
- apply_reparse用_RealKernel.CreateFileW，当前后者固定GENERIC_READ+OPEN_EXISTING。junction占位目录并未在真实创建路径建立；需明确本任务占位目录的独占创建/存在类型/归属检查及设置reparse所需访问权限。观察只读与创建写句柄分开。
- CreateDirectoryW、MoveFileW、DeviceIoControl（GET也包括）、CreateSymbolicLinkW等全部显式ctypes argtypes/restype，确保64位HANDLE不截断；目前GET调用可能发生在SET初始化声明之前。
- read_reparse固定raw[16:]，忽略SubstituteNameOffset；symlink有Flags且PathBuffer基址不同。按tag对应真实结构、offset/length/flags解析，验证缓冲区长度，未知tag拒绝，不全都称junction。
- iter_links当前kind固定junction，必须从绑定原始输入的reparse_tag/类型确定，或提供已核查全体确为junction的证据；不能把未知/symlink强改junction。缺类型应deficit。
- 目录symlink正确directory flags，相对symlink解析/迁移策略明确；不能在未知类型上静默转换。
- _find_children对FindNextFileW失败区分ERROR_NO_MORE_FILES和IO错误，不能将读目录失败当完整遍历结束。
- 正常目标祖先检查建议PureWindowsPath表示Windows路径、Path只用于真实C文件访问，便于跨平台纯测试；已有祖先reparse拒绝保留。

官方结构参考，仅用于实现核对：
https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_reparse_data_buffer
https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/b41f1cbf-10df-4a47-98d4-1c52a833d913
https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ni-winioctl-fsctl_set_reparse_point
测试必须在原生WinAPI函数替身这一层记录dwDesiredAccess、creation mode、HANDLE、FSCTL参数和原始返回缓冲区；不要绕过_RealKernel直接让高层Api返回完美字段。
仍禁止真实文件/链接写入测试，所有上述调用由假kernel接收。

## 4. 保持合理迁移开销

copy_entity当前写死1KiB块；生产使用可配置的合理块（如1MiB），测试仍可小块，不能为356GB形成数亿次Read/Write。
验收应每唯一目标实体读hash一次，alias枚举只查type/id/volume等metadata，再按组核验；当前observe/枚举每file都hash会反复读取同实体。
保留完整hash覆盖，不通过改成抽样提速。将metadata-only与内容hash观察分开并缓存到验收状态；异常必须失败。
验收的expected/observed全表目前放:memory:，8,715,067路径会占大量内存。改C盘SQLite临时/派生表或说明可控边界，流式枚举和批量事务/索引，不一次list全路径。
不跑全量业务数据测试。小型实体多alias测试统计hash次数=唯一实体数，普通SQL query plan足以验证结构。

## 交付及阶段

不重建6GB plan、不重复hash9GB输入、不重新扫描源树。普通计数与16映射保持原基线。
已通过33项/A/B/C及隔离保留，本轮完整回归加明确反例，出逐项结果。
回传：
agents/chatgpt/inbox/R9_DESKTOP_STRICT_ACCEPTANCE_WIN32_FIX_20261013/
完整源码/common/config/CLI/测试、ZHANGWEI_REPORT.md、
FILE_SHA256.json、TEST_RESULTS_FULL.json、
ADVERSARIAL_ACCEPTANCE_RESULTS.json、WIN32_WRAPPER_TRACE.json、
REAL_METADATA_BINDING_SAMPLES.json、EXECUTOR_READINESS.json。
干净目录可下载import/--help/复跑纯测试，不依赖未上传本机模块。
未修完即PARTIAL/IMPLEMENTATION_READY=false；完整模拟后仍供ChatGPT审核。
源UNC1326、D共享名未知保留外部阻塞；此轮仍不改凭据/网络，不因它们停止离线代码修复。
连续完成本轮范围，30分钟可报检查点后继续，不每个helper再要一条任务。

执行电脑=ZHANGWEI；SAM=HOLD。
FORMAT_DONE=false；COPY_AUTHORIZED=false；FULL_MIGRATION=false；WINDOWS_IO_EXECUTED=false。
不格式化、不真实业务复制、不在C/E做实际硬链接/junction试验、不在E写入，不改SAM源盘/MWB/P7。
用户本人未来手动格式化台式机E后才进入真实试验。
完成更新INBOX_FOR_CHATGPT.md。保留有价值历史证据。
