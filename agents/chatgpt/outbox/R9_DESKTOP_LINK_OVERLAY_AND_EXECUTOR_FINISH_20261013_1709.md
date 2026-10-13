# ZHANGWEI 台式机 AI｜补齐链接计划并完成执行器代码

task_id: R9_DESKTOP_LINK_OVERLAY_AND_EXECUTOR_FINISH_20261013_1709
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
supersedes: R9_DESKTOP_COMPLETE_EXECUTOR_20261013_1542
notebook_SAM: HOLD
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false

## 本轮范围与结论

继续在台式机 ZHANGWEI 工作，不转笔记本。用户已明确：正式迁移前的台式机 E 盘真实试验，要在用户本人手动格式化后开展；现在仍是准备阶段。
本轮允许 C 盘代码、C 盘计划库更新、只读元数据核验和纯函数/小型 SQLite 合成测试。
禁止格式化、向 E 写入任何试验或业务数据、执行真实复制、创建实际硬链接/重解析链接。不要运行 copy 即使加 --copy-authorized --format-done；两个人工 CLI 开关不能代表用户授权。
不修改 SAM 源 E/D，不重扫业务树，不启动交易/P7。不修改账号密码、SMB、网络或 MWB。

1542 报告已审核：三份输入本机 SHA 核验通过，合并库存在；但 16 个 D 重解析节点的目标未读入，四个写入/验收主体尚未完成。
缺目标并非必须新扫描：HUB 已有 R3 依赖地图记录这 16 条 D_TO_E 映射。
本轮连续完成映射适配、计划核验、复制及验收代码；不要每完成一个函数就停止等待新任务。

## 一、绑定现有三份输入及第四份映射

继续使用上轮已核验的只读输入，禁止覆盖它们：
- E base SHA256 a5590154ed4da7b45c1ad19dfe82989cd2bb058702aad9b6ea58c2868d0a5572，9376645120 字节。
- E canonical delta SHA256 aa58ed8bd7b22e015a041133007a9b031514eb82baf27d80ace0e48f2a48bd1c，86016 字节，42 文件、16 目标。
- D repaired snapshot SHA256 4c094df43ca348acdc89498a49660ad9120d7ca3ef9bfe21f8b3c9e414257795，48635904 字节。
旧 D SHA 787b14… / e3e0f… 仍拒绝。不要仅为重复统计重建 9GB 输入快照或整张 6GB 计划。

新增映射输入：
agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9_SAM_DEPENDENCY_MAP_R3.json
Git blob SHA: 2a40ed660cd12dfb4b8c80e7d7896fc3c4687397
文件原始 UTF-8 SHA256: 1c00ece5db519bf39de33473b5cbb81728cbdd65d8d38d6e00532f4a136084fe
注意：JSON 内 dependency_map_sha256=2fa725f6… 是内部摘要，不是文件原始 SHA，不混用。
下载到 C，核对原始字节后作为第四份输入记录来源、SHA 和时间。若字节不同，先报精确差异，不使用未经绑定的新版本。

仅使用 R3 的链接路径和目标映射，不继承其历史 dependency_closure_closed、内容覆盖、READY、目标 E serial 断言。
当前内容证据以本轮三份输入和实际计划核验为准；历史 806508DF 是历史值，不能成为格式化后的授权。

## 二、补入 16 个 D 目标，修现有计划而非全量重建

现有计划：
C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite
上轮大小 6024241152 字节。先做 C 盘可恢复备份，再以事务更新派生计划；不要调用会 unlink 计划的 _init/build_plan 重跑全部 870 万行。
备份检查 C 可用空间；空间不足则报告，不损坏现有库。

从地图筛出 direction=D_TO_E 的 id 25–40，以 Windows 路径规范化后 source_path 精确匹配本轮 D snapshot 中 16 个 reparse 行，并匹配计划的 D 来源行。记录 source_path、原始目标、最终目标、迁移后 link_path、迁移后 target、映射出处。
缺失、多对一冲突、重复不同目标、非选定范围、无法匹配均保留具体 deficit，不能直接删掉 LINK_UNRESOLVED 或填状态使其通过。

这 16 条来源是：
D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_20260903_SUCCESSOR_BUILD_AND_ATOMIC_PUBLISH_R1\pit_products\
下 FLOATING_TOP10 与 TOP10 产品的 data/indexes 共 4 条，以及 INDEX_WEIGHT 产品 year=2014…2025 共 12 条。
目标在：
E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260903_20260903_180234\
对应 FLOATING_TOP10、TOP10 和 INDEX_WEIGHT 子目录。
迁移后 D 链接位置移到 E:\BLACKBOX_ENGINES\CURSOR_TASK_ARCHIVE\…，目标仍在 E:\BLACKBOX\…。
以地图具体全路径为准，不按上面的缩略描述手写猜测。

核验每一目标在当前 base+delta 中的目录/文件覆盖；42 文件 delta 是内容证据，不能只见到目录壳就称全树已覆盖。需要的确定性父目录可由已绑定目录/文件记录派生，注明出处；无法证明的内容仍阻塞。
检验全体 4825 条计划链接的目标范围、路径冲突、缺目标、目标解析和循环，解析时考虑链接祖先及剩余路径；E→D 与 D→E 双向关系不自动等于循环。
区分原始 source_path、迁移后 link_path、迁移后 target；现有 links.mapped_dest 仅存目标，不足以独立驱动创建链接。
必须使用路径分隔边界和 Windows 大小写语义，不能用任意字符串 startswith 接受越界目标。D 路径只能映射已选定 D 范围，不能一概放行整个 D 盘。

上轮基线用于差异核对，不能硬编码 PASS：
file_paths=8715067；entities=1223721；unique_content_bytes=365007198749；
logical_path_bytes=5085136765894；normal_dirs=233660；links=4825；
D files=34745、D entities=34744、D dirs=10637、D reparse=16。
16 条映射补丁本身不应改变普通文件/实体/字节统计。若需派生目录，单列数量与依据。
delta 的 42 条路径原来不在 base，但实体可能已通过其他硬链接路径存在；避免重复计内容字节。
PLAN_COMPLETE 只有真实闭包及路径核验全部通过才 true；这仅指绑定快照的离线计划，不能宣称今天源树无漂移或 D 全盘完整性已证明。

## 三、完成真正可调用的复制及验收主体（本轮禁止调用真实写入）

完成 r9_formal_executor.py / r9_adapter.py 中：
write_entity_bytes、create_local_hardlink、rebuild_reparse、accept_on_disk，
并从 CLI 到实际函数形成可检查的调用链。不能用占位 print、NotImplemented、永远拒绝的空实现替代主体。
本轮实际 copy 入口仍必须在首个写入前拒绝，理由是 PREPARATION_ONLY / 未格式化且无新阶段授权；主体实现与授权闸门分开。

沿用 HUB 现有迁移合同，至少落实：
- 一次复制一个源卷 serial + file ID 的普通文件实体，其他路径创建同一目标卷硬链接；源端不同卷实体不能按内容相同合并。
- 明确每个实体的可读源路径、mtime/大小/Win32 身份，复制前后核验源身份/大小/时间稳定；当前 plans.paths 不存 mtime，需补派生表或读取绑定只读输入，不可静默跳过漂移核验。
- 临时文件、内容校验、成功后原子提交、可恢复进度；重启核验已有结果，不盲目覆盖/删除未知目标。
- 目标路径只允许指定迁移根内，防止相对路径、祖先重解析导致逃逸；链接重建后不得指回 SAM 源 UNC 或旧 D。
- 对不支持的 reparse 类型、权限/空间失败、源变化明确失败，不降级为重复复制掩盖硬链接失败。
- 最终验收对照绑定计划：实体内容、路径覆盖、硬链接 FileId 分组、目录和链接目标、未完成/多余/冲突、AllocationSize；不能只做 exists/size 或抽样就宣称全量 PASS。内容 hash 策略写明并可审阅。
- 格式化后须重新绑定实际目标盘 UniqueId、卷信息、容量和根路径，核验源目标不是同一盘/同一位置；不要求卷 serial 一定改变，也不复用旧 READY。
- 用户格式化确认和下一阶段授权必须来自新的、可审计的任务合同；仅两个 CLI bool 不足以开启写入。

纯函数和 C 盘小型 SQLite/模拟 IO 测试验证边界、缺映射/冲突/循环、目标逃逸、源变化、同实体多路径、断点恢复、无授权拒绝及验收失败分支。
模拟 PASS 与 Windows 实盘功能未测分别报告；不做任何真实文件复制/硬链接/junction 试验。本轮只可写 C 的代码、日志和测试元数据。

## 四、源 UNC 与阶段状态

\\192.168.100.2\E_DRIVE\BLACKBOX 的 WinError 1326 是认证失败，单列 SOURCE_LIVE_PREFLIGHT_PENDING=true，不以离线输入 PASS 掩盖。
本轮不盲目重连、不改密码凭据、不删除共享会话或调整网络。不因它阻塞纯离线开发。
preflight 总结果应明确区分 INPUT_VALID 与 SOURCE_ACCESS_VALID；源访问失败不能返回“可复制”总 PASS。
当前冻结索引不是业务停止后的最终实时清单；正式复制前仍需源访问、源漂移核验和新阶段审核。
C/HUB 的有价值输入、依赖图、代码及历史验收证据保留；仅退休旧任务入口，不删除正在依赖的历史材料。

## 五、回传与完成条件

回传到：
agents/chatgpt/inbox/R9_DESKTOP_LINK_OVERLAY_AND_EXECUTOR_FINISH_20261013/
文件：
ZHANGWEI_REPORT.md
INPUT_BINDINGS.json
LINK_OVERLAY_AUDIT.json（16 条逐行，原始/迁移后链接与目标及内容证据）
PLAN_SUMMARY.json
VALIDATION_RESULTS.json
EXECUTOR_READINESS.json（4 个函数的模块/入口、实现状态、测试状态、剩余阻塞）
实际全部代码模块、配置、测试源码与测试结果，以及文件 SHA 清单。
大计划 SQLite 留 C，不把 6GB 库上传 HUB。

报告如实分别列：
INPUT_BINDINGS_VALID、LINK_MAPPING_COMPLETE、PLAN_COMPLETE、
COPY_IMPLEMENTATION_READY、ACCEPTANCE_IMPLEMENTATION_READY、
SOURCE_LIVE_PREFLIGHT_PENDING、WRITE_TESTS_NOT_RUN、
FORMAT_DONE=false、COPY_AUTHORIZED=false、FULL_MIGRATION=false。
本輪所有实际 E 写入测试必须是 NOT_RUN。不要将函数实现状态写成实盘已验证。

每约 5 分钟记录进展；30 分钟上传检查点但不用为了代码编写再次请示。
遇到真正无法继续的输入/空间/合同矛盾，上传精确阻塞和已完成代码；不要退回只有下一轮 TODO 的空壳交付。
完成后更新 INBOX_FOR_CHATGPT.md 指向新报告，并复述：执行电脑=ZHANGWEI；SAM=HOLD；仍未格式化/未复制。
