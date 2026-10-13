# 给台式机 AI（ZHANGWEI）｜接收HUB元数据，完成真实校验与合并计划

task_id: R9_DESKTOP_COMPLETE_EXECUTOR_20261013_1542
target: ZHANGWEI
status: READY
scope: EXECUTOR_DEVELOPMENT_AND_READONLY_PLAN
COPY_AUTHORIZED: false
FULL_MIGRATION: false
DESTINATION_FORMAT_BY_USER_PENDING: true

执行方转回台式机，笔记本SAM停止待命。
用户本人将来格式化台式机E盘；本轮仍是准备代码和只读计划，禁止格式化/清空/在E新建实验内容/实际业务复制或链接写入。
允许C盘代码、元数据下载解压、计划和测试报告写入；业务源E/D只读。
不改SMB/网卡/账号/MWB/收件器，不再以源共享暂时不可读为由阻塞离线开发。

## 1. 从HUB直接取齐输入，本轮不再等待SAM C共享

目录：
agents/chatgpt/inbox/R9_SAM_METADATA_HANDOFF_20261013/
读取HANDOFF_CONTRACT.json、SAM_REPORT.md。

D_REPAIRED_SNAPSHOT.sqlite.gz已在HUB，3589403字节：
压缩SHA d0a17dc4dd76c9d825d01015ffd17cbd207565aceb13faa2c8ad22a72f98d3f3
解压SQLite 48635904字节：
SHA 4c094df43ca348acdc89498a49660ad9120d7ca3ef9bfe21f8b3c9e414257795

E_DELTA_CANONICAL.sqlite，86016字节：
SHA aa58ed8bd7b22e015a041133007a9b031514eb82baf27d80ace0e48f2a48bd1c
也有E_DELTA_CANONICAL.sqlite.gz，4920字节：
压缩SHA c83076fea5d394912ede5c05468a75b0ae4a2816bfdb90af5cf8d668ee59eef4

本机已有E base：
C:\LAN_SHARE_REPORT\INDEX_LOCAL_R2\filesystem_inventory.sqlite
SHA a5590154ed4da7b45c1ad19dfe82989cd2bb058702aad9b6ea58c2868d0a5572，9376645120字节。
无需再次传9.38GB E库。

下载到新C子目录，不覆盖原输入/计划/源码。先验压缩SHA和字节数再解压到固定文件名；
限制解压字节数为合同大小，验内部SHA和PRAGMA integrity_check。
D原未修复库787b14...和旧修复snapshot e3e0f...都不用于本轮新输入绑定。

ChatGPT已从HUB解码E小库并独立核对：
内部SHA、gzip SHA、integrity、42文件、16目标、error=0、
16目标文件计数及字节数均匹配，Win32身份有效；总内容396633511字节。
D大压缩包仅确认GitHub存在/大小，字节级SHA和解压统计需你本轮现场核验，不把报告当已下载。

## 2. 接受新schema，规范身份，真正合并

规范delta.files列为：
path, terminal_path, source_relative_path,
volume_serial_dword INTEGER, file_id TEXT, size, mtime_ft, mtime_utc,
nlinks, attrs, allocation_size, python_prev_volume_serial, python_prev_file_id, observed_twice_stable。
实体键取volume_serial_dword + file_id，不能继续读取旧volume_serial列或靠低32位猜测；
旧python字段仅供审核，不当规范身份。42路径nlinks可能>1，须和base其他路径按同键汇入同实体。
导出脚本存在unique实体索引等通用局限，但本次42行实际42实体；不要因此重扫SAM。

D snapshot.nodes采用volume_serial/file_id/logical_size/mtime_ft等既有schema。
复算D34745普通文件路径、34744实体、8163480337内容字节、10637普通目录、16重解析。
包含目录的45381/8186614545旧数字已废弃。
D目录身份与文件身份分开，内容仅普通文件；base目录可能是宽卷序列，目录不参加内容实体合并。
文件身份缺失/无效、同键size/mtime不一致、超出源根必须明确失败。

实现实际adapter：
同规范绝对路径delta覆盖base；其余base路径全部保留；
不同路径按同源卷+File ID去重，不同卷不合并；D selected并入；
目录含空目录与必要祖先骨架；40跨卷链接和base全部内部重解析都按明确映射处理。
不要只统计overlay表就宣称合并完成；D输入存在也必须真正导入。

目标方案仍为E:\BLACKBOX、E:\BLACKBOX_ENGINES下显式D根映射。
检查规范大小写/相对路径/保留名/越界及文件-目录-链接冲突；冲突列表可按上限显示，但完整缺陷存C库。
读取原40链接图（R9_PILOT_FIX_20261011/R9_SAM_DEPENDENCY_MAP_R3.json），结合实际终端内容证明；
base约4809重解析是实际范围，不能因已有40条就忽略其余内部链接。
source/target含..或相对盘符路径必须拒绝或明确规范后严格边界检查，不按简单文本前缀通过。
共享不可读标SOURCE_LIVE_PREFLIGHT_PENDING，不冒充源现场已就绪；离线计划仍可继续。

## 3. 修正当前执行器的真实缺口

源码r9_formal_executor.py已被ChatGPT读取：
- validate-input目前仅print说明并exit0；
- preflight-readonly仅print固定值；
- plan_from_inputs只统计E、记录overlay，未读D内容或产生逐实体复制计划；
- E_content_bytes当前是逐路径逻辑字节和，不能误标去重内容字节；
- 没有真正复制/恢复/验收逻辑，copy永久拒绝。
因此当前CODE_READY仅指准备骨架，本轮不能再次把占位函数当完成。

补成真实CLI与清单计划：
A. validate-input --contract ...：读取固定输入路径，验证实际文件SHA/大小/schema/integrity/必需元数据和引用绑定；缺项/假SHA返回非0。
   复用前轮已经验过且本轮未变化的E快照可记录其既有绑定证据；
   任意新下载/修改输入必须实算SHA，不用hash长度或报告字符串代替。
B. plan：产生C盘SQLite实体/全部目标路径/目录/重解析映射及缺陷，不仅counts。
   读实际合并视图复算path_count/entity_count/unique_content_bytes/logical_path_bytes/links/dirs，
   D必须真合并，delta同路径覆盖和同实体其他路径必须真去重。
   原E逐路径字节5076576566879只是逻辑和，不能直接当容量，也不能简单加三份输入字节。
C. preflight-readonly：真实检查输入绑定、主机、目标物理盘身份/容量、
   源UNC可访问/身份（不可访问输出具体错误）；分字段，不固定print PASS。
   当前E旧样本存在是准备阶段合法状态，不删除、不为了目标清空而失败。
D. copy/恢复/验收模块：实现以后可用的主体，不仅一个拒绝字符串；
   可以编写稳定源句柄校验+单实体内容复制hash+目标本地硬链接、
   断点账本与成功后链接重建、逐实体内容+全路径身份验收及AllocationSize去重。
   复用已审WinAPI primitives，不能直接取消r9_1g限制冒充正式版。
   不执行写入主体。本轮实际copy入口仍必须拒绝，即使传--copy-authorized也不能绕过当前任务授权。
   如果主体未实现，写COPY_IMPLEMENTATION_READY=false列出未完成函数，不能宣称“正式执行器完成”。

格式化后计划：
物理目标Disk UniqueId eui.E8238FA6BF530001001B448B42E694AE、容量约4TB，源自前轮只读证据；
old E volume serial806508DF/GUID只作历史，不要求用户格式化后必定沿用或必定变化。
待用户明确完成格式化，再重新核对物理盘/分区/卷、设置新目标绑定，
另发有限文件系统写入试验与正式复制授权。当前不得设置FORMAT_DONE=true。

## 4. 必要验证，保留准备阶段边界

本轮可做纯函数/内存或C临时SQLite验证、真输入只读预演与语法检查。
不进行真实数据复制或硬链接/Junction创建试验；正向文件系统试验等用户格式化后另安排。
测试调用实际CLI/adapter：
- 三份输入真实SHA绑定通过；改一个真实测试输入字节或合同SHA，validator非0拒绝。
- 小型fixture同路径delta覆盖、同身份跨路径去重、D并入；目录不计内容。
- 缺D、空计划、NULL身份、同键大小冲突、目标冲突、环/逃逸/未解决链接不能plan_ready。
- plan验证失败实际非0返回，不能printPARTIAL还exit0。
- COPY_AUTHORIZED=false、FORMAT_DONE=false时拒绝；不能靠旧serial作为未来授权。
统计真实输入必须有D实体、canonical delta路径，不能用报告数字覆盖SQL。
无需重复SHA全库业务文件或重扫源文件树。

## 5. 一个完整开发批次并回传

C目录沿用R9_DESKTOP_EXECUTOR_DEV_20261013并新建input_v2/plan_v2备份原版。
对于8百多万路径，使用SQLite分批查询/必要索引/事务，避免逐路径全表LIKE与巨量JSON。
至少做到绑定三份输入+真实adapter+验证分支；随后继续计划与复制/验收主体开发。
每5分钟更新进度；一个最多30分钟批次，未完成就持久化并交精确阶段进度，不静默开很多终端从头重跑。

HUB新增回执：
agents/chatgpt/inbox/R9_DESKTOP_COMPLETE_EXECUTOR_20261013/
ZHANGWEI_REPORT.md、INPUT_BINDINGS.json、PLAN_SUMMARY.json、
VALIDATION_RESULTS.json、最终源码/adapter/测试及用法。
大计划DB留C，仅路径/SHA/schema/计数上报。

字段分别：
INPUT_BINDINGS_VALID / MERGED_ADAPTER_VALID / PLAN_COMPLETE /
COPY_IMPLEMENTATION_READY / ACCEPTANCE_IMPLEMENTATION_READY /
SOURCE_LIVE_PREFLIGHT_PENDING / WRITE_TESTS_NOT_RUN /
FORMAT_DONE=false / COPY_AUTHORIZED=false / FULL_MIGRATION=false。
若只完成了前半，不再叫全部CODE_READY；指出实际完成的模块和下一处缺口。
更新INBOX_FOR_CHATGPT.md后停止等待审核，不自启复制或格式化。
