# 给笔记本 AI（SAM）｜修复清单统计与恢复，闭合40条链接映射

任务ID：R9_NOTEBOOK_MANIFEST_REPAIR_20261011_1415
状态：待执行。
取代：R9_NOTEBOOK_SELECTED_MANIFEST_20261011_1354（已回传，有实质成果但未通过代码审核）。
执行方：笔记本SAM。台式机ZHANGWEI仍保留1GiB样本待命。
本轮在C盘修代码/清单副本、做合成测试和必要定点只读核验；不复制业务数据，不重做1GiB，不扩大全D/E扫描。

## 1. ChatGPT已审核的事实

选定12根已报告10637目录枚举完成，普通文件身份OK=34745，节点45398。
现有DB与逐条40链接材料有价值，全部保留，不从零重建。
但45381实体/8186614545字节不能当普通文件内容总量；SQL把目录一起按File ID计入。
报告把MIN_sandbox/全ARCHIVE/QMT尚未扫描自动当作选定运行范围阻塞，也缺证据。
本轮目标是修真实代码缺陷并取得可用于正式执行器的清单，不继续抽样，不把可选资料扩大成无限核查。

ChatGPT本地运行了你上传的enumerator源代码，使用临时SQLite和模拟身份输入（非Windows现场测试），复现：
A. 只有1项in_progress、pending=0、dir_enum_done=0时，run_batch返回QUEUE_EMPTY、enumeration_complete=true，且in_progress未恢复。
B. 一个目录logical_size=4096和一个普通文件size=100，当前unique_bytes SQL输出4196，正确文件内容应为100。
因此当前“4/4合成测试”未覆盖这些失败点，不能关闭问题。

现有重要依据：
R9_SAM_SELECTED_MANIFEST_REPORT.md / SUMMARY.json
selected_manifest_enumerator.py / export_dependency_map.py / run_selected_manifest_synth_tests.py
R9_SAM_DEPENDENCY_MAP.json
R9_SAM_SELECTED_RESUME_STATE_HUB.json（10637队列项都标done）
原DB SHA：787b14d267b3b167b37695adbdffaba96c719ed50bf64659ba4ba3828f630d39。

## 2. 修复内容统计（优先直接查询现有DB）

内容实体及字节只统计普通文件：
is_dir=0 AND is_reparse=0，并要求有效volume_serial、file_id、size，identity_err/access_err无错误。
目录数、链接数、文件路径数、唯一普通文件实体数、逻辑路径字节、去重内容字节分别列。
目录ByHandle“size”没有文件内容意义，不能加进unique_content_bytes。
同卷+File ID组的size/mtime若不一致要标冲突，不能用max(size)隐藏错误。
给出实际SQL、分组一致性检查与修正后的真实总量；不能沿用8186614545或45381冒充文件指标。
按源卷+File ID去重；不同卷不合并。同卷范围外硬链接不强制迁移，但所有范围内路径必须完整列出。

## 3. 一次修完恢复与完成状态

在原DB独立副本上迁移schema/修复状态，保留原版SHA，不直接覆盖历史。

具体缺陷与要求：
1. 启动恢复把上次in_progress恢复成pending；完成计算统计pending/in_progress/error/changed全部状态。非空根配置逐根有完整账本才能完成。
2. 当前run_batch忽略enum_one_dir返回值，ERROR和PENDING_CHANGED也被queue标done。改为明确映射；错误/变化保留未解决状态，不能QUEUE_EMPTY=>完成。
3. 目录前/后稳定身份、类型、mtime读取任何失败均不算稳定ENUM_DONE；文件属性/身份失败要独立记录。全局枚举完成、身份完整、依赖闭合分字段计算，再由程序统一生成summary，禁止事后手工改proven字段。
4. 真正中断发生在scandir中途或子项处理中也须可恢复，不仅预算到后重启。未完成目录可从头重枚举，事务保证幂等且不漏子项。
5. 重新枚举不会清除nodes中已删除的旧子项。用枚举generation/实际child集合在完整成功后刷新该目录的当前视图；历史删除另记diff，不能残留成当前文件。未完成时不能把部分节点误当当前完整结果。
6. 旧对账需比较精确path、普通文件/目录/重解析类型、卷+File ID、size、mtime；mtime旧ISO与新FILETIME按实际精度规范化。重复批次diff幂等，不无限重复计数。
7. 不改只读旧inventory的journal_mode。新清单数据库使用SQLite一致性快照/backup，提交并正确处理WAL后再计算SHA；不能给会受WAL改变的主DB文件单独哈希当完整快照。
8. 当前export把含自身hash的配置连续hash两次，run只相信JSON里的config_sha256。改为明确规范：对去掉config_sha256的规范化配置计算并核验，或者实际文件SHA存sidecar；不能信任自报字段。依赖表digest也核验，配置改根但保留旧hash必须拒绝恢复。
9. source_host和实际源卷绑定必须核验，不仅覆盖写meta。生产源卷UNKNOWN/主机不符停止；合成测试按合成根卷绑定，不能硬查D盘当C盘测试绑定。所有路径用声明源根/主机，选定根边界严格验证。
10. 预算包括初始化/对账/报告，目录内也有检查点；最多30分钟，异常退出须有可续接状态。失败/未完成CLI返回非成功码，不能main固定0掩盖结果。

数据处置：
先审计现有DB的queue/dir_enum/nodes是否存在in_progress、错误、缺身份、类型不确定、残留节点等具体风险。
现有成功枚举成果复用，不全树再扫。只对审计发现的目录或确需验证修复的数据做定点只读重枚举。
若没有现场中断/残留异常，可直接用现有节点修正统计、补账本验证和快照，不为了测试而重跑全部12根。

## 4. 修正链接闭包：当前确实未完成的是D→E映射

依赖JSON的16条D_TO_E（id25–40）已读到真实目标：
均为\\?\E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260903_20260903_180234\... 下目录。
它们被写成target_in_migration_scope=false、new_link_suggestion=null，
又因未规范化\\?\前缀而标POSSIBLE_ESCAPE_OR_OTHER_VOLUME。
这是导出实现缺口，不是证明存在16个真正逃逸。

要求：
- 规范化本地/UNC扩展前缀与大小写，再以精确目录边界判包含。不能用“包含CURSOR_TASK_ARCHIVE文字”充当允许范围或循环检测。
- 区分recorded_target/current_readlink_target/final_resolved_target；readlink失败只能UNKNOWN/错误，不能用旧记录当已核验目标。
- 链接alive需源确为期望重解析类型、当前目标能实际解析打开；lexists仅说明入口存在，不能证明悬空链目标可访问。当前目标错误时也不能OR旧目标存在而PASS。
- 24条E→D映射到E:\BLACKBOX_ENGINES\CURSOR_TASK_ARCHIVE\...；
  16条D→E链接位置也按同一D根映射到台式机E:\BLACKBOX_ENGINES\...，目标按E BLACKBOX相对路径映射到台式机E:\BLACKBOX\...。
  全部只写方案，不创建链接，不保留笔记本UNC作为新目标。
- 利用E既有索引精确查16个目标及其实体/重解析记录，证明目标属于将迁移的E清单；缺失只对这些目标定点核验，不全E重扫。
- 检查真实路径图中的链式跳转/祖先重解析和最终内容是否纳入，不能把“跨卷回来”当循环，也不能只看D/E盘符就排除循环。
- 查新选定清单所有is_reparse=1节点（报告45398节点与10637目录计数推测17个重解析，实际以SQL为准），对每个节点有链接类型/目标/迁移后映射。也处理D旧库存22条中的其余6条：不在选定范围可标OUT_OF_SCOPE，不能遗漏已纳入节点。
- 依赖闭包针对当前E BLACKBOX+选定D范围；未知资料是否保存与运行闭包分开。

## 5. 不再用“没扫描可选目录”制造运行阻塞

MIN_sandbox、整棵ARCHIVE、QMT安装树未纳入本轮明确配置，并不自动导致已选定范围coverage=false。
只有存在具体入口/配置/实际链接引用而目标未纳入，才列运行依赖阻塞：source_path、引用类型、target_path、证据一条条给出。
没有引用证据的候选列“可选研究存档/待决定”，不能声称已证明无关，也不能自动删掉。
文件系统覆盖通过≠应用运行独立性通过；分别给字段，未知就unknown，不把目录名猜测写成硬阻塞。
复用已有启动/配置资料做有界精确路径检索；最多10分钟，不遍历所有业务内容、凭证或全E。
不要求本轮证明整个D完整；D_GLOBAL_COVERAGE_PROVEN仍false。

## 6. 验证必须覆盖实际失败模式

C盘独立合成目录，直接调用修订run_batch/实际CLI和真实SQLite：
- 目录有非零ByHandle size、同组多硬链接：文件内容总量准确，目录不入内容实体。
- 保留in_progress的异常退出后恢复完整；测试须实际制造中断，不用“1秒可能没停”代替。
- scandir/目录前后身份失败及mtime变化不会完成或静默done。
- 文件删除后重枚举无需测试脚本手动DELETE nodes，当前视图自动去掉并保留删除diff。
- 修改roots但保留旧自报hash、源卷UNKNOWN/不符必须失败。
- 合法\\?\E:\BLACKBOX反向目标纳入且映射正确；真正环/悬空/边界逃逸继续拒绝。
原>40项/深度>2/不跟junction用例保留，不重复无关pilot测试。
提交源码、逐项实际输入/计数/verdict。测试不能先手改DB删除节点来绕过被测缺陷。

## 7. HUB回传与结束

新增而非覆盖原报告：
- R9_SAM_MANIFEST_REPAIR_REPORT.md：各项修复、修正文件实体/字节、当前是否可用于正式执行器、真实剩余阻塞。
- R9_SAM_MANIFEST_REPAIR_SUMMARY.json：自动生成，覆盖/身份/依赖分字段，原版与新快照SHA。
- 修订enumerator/export程序、代码diff、修复测试源码和逐项结果。
- 修订依赖图、配置、快照schema/SQL、resume HUB摘要。
大SQLite留本机，上传路径/SHA及完整状态计数。旧DB和原报告保留。
若补核超预算上传PARTIAL与完整队列，停止，不从零再扫。
更新INBOX_FOR_CHATGPT.md，FULL_MIGRATION=false。
修复后可给正式执行器输入契约与精确参数草案；本轮不改r9_1g、不开始正式复制、不启用P7。
