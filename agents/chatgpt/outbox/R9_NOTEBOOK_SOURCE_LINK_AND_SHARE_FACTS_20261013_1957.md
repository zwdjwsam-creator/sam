# SAM笔记本｜只读补齐16条D链接类型与源共享事实

task_id: R9_NOTEBOOK_SOURCE_LINK_AND_SHARE_FACTS_20261013_1957
target: SAM
status: READY
phase: SOURCE_METADATA_READONLY
desktop_ZHANGWEI: HOLD
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true

## 调度与审核现态

下一轮执行电脑改为笔记本SAM。台式机ZHANGWEI停止当前任务、保留代码/计划/状态，等待新指令。
本轮仅补源端客观事实，不复制业务文件、不迁移、不格式化、不创建试验链接、不修改SMB账号/密码/网络/MWB/P7。

桌面1934包已审核：
37项纯测试独立复跑通过，正常验收/A-B-C/严格缺字段反例/FILETIME转换/模拟隔离修复保留；真实Windows IO仍NOT_RUN。
FILE清单24项里22项存在且SHA/大小匹配；RESUME_TEST_TRACE.json、FULL_ACCEPTANCE_TRACE.json只列清单未上传到本轮目录，桌面后续补齐。
IMPLEMENTATION_READY仍false，未准许实盘。

尚有代码收尾，记录以防遗漏，但本轮SAM不修改桌面执行器：
1. plan_digest只hash表计数/stat计数，修改entities.mtime但不改行数时digest不变，full_acceptance仍true。后续桌面需绑定真实内容/语义摘要、验证同计数改动被拒绝。
2. 全计划schema与源metadata的最终绑定、类型sidecar尚待本轮事实；本轮完后回桌面适配。
这些不妨碍SAM进行16条只读元数据核验。不要因37项PASS宣称完整实施/实盘已通过。

## 输入和精确范围

使用现有HUB：
agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9_SAM_DEPENDENCY_MAP_R3.json
文件SHA256 1c00ece5db519bf39de33473b5cbb81728cbdd65d8d38d6e00532f4a136084fe
筛选direction=D_TO_E、id25–40，恰好16条source_path。
R3内部dependency_map_sha256不是文件SHA。仅读取路径/目标参考，不继承历史closure/serial/READY结论。

这些来源在SAM本地D：
D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_20260903_SUCCESSOR_BUILD_AND_ATOMIC_PUBLISH_R1\pit_products\
FLOATING_TOP10/TOP10产品data、indexes共4条；INDEX_WEIGHT产品year2014…2025共12条。
以地图具体全路径为准，不手写猜测产品全名。
现有修复D快照SHA=4c094df43ca348acdc89498a49660ad9120d7ca3ef9bfe21f8b3c9e414257795，
E canonical delta SHA=aa58ed8bd7b22e015a041133007a9b031514eb82baf27d80ace0e48f2a48bd1c；
它们保持不变，不重新导出/覆盖，不重hash大E索引。
D的object_class=Reparse不足以判junction。桌面统计E base4809数字tag都是2684354563，本轮不再扫E全树。

## 一、只读核验16条链接本体

对每条读取链接本身，不递归/遍历其目标树：
- 实际hostname、查询UTC/本地时间、source_path；
- Win32 attributes、数字reparse_tag（十进制及hex）、由tag确定kind；
- 原始substitute/print name及Flags（若symlink），实际读取target规范化结果；
- 链接本体卷serial/FileId/mtime_ft（能够取得则记录），卷为SAM源D而非桌面；
- GetFileInformationByHandleEx(FileAttributeTagInfo)或FSCTL_GET_REPARSE_POINT的实际读取结果及错误；
- 对照R3 current_readlink_target/final_resolved_target是否一致。只为存在/类型做目标元数据查询，不枚举目录内容，不hash业务文件。

使用OPEN_EXISTING、FILE_FLAG_OPEN_REPARSE_POINT、FILE_FLAG_BACKUP_SEMANTICS，仅只读/元数据访问。
禁止任何FSCTL_SET、CreateHardLink、CreateSymbolicLink、写目录/文件业务树操作。
可写C:\LAN_SHARE_REPORT本轮脚本/JSON/日志。不能在D/E源树写副文件。
unknown tag/不存在/AccessDenied应如实逐条ERROR，不能默认junction。2/3与其他错误区分。
每条16项都保留；匹配失败不丢行、不删除原地图。LINK_TYPES_VERIFIED只有16项全部取得有效数字tag并匹配范围才true。
不要推导D全局完整性/今日全源内容覆盖，也不全局重扫。

输出独立sidecar，供桌面之后按规范路径join，不修改旧D SQLite：
D_REPARSE_TYPE_OVERLAY.json
含schema_version、task_id、host、queried_at、map_file_sha256、d_snapshot_sha256、
records数组，每条map_id/source_path/reparse_tag/kind/raw_target/normalized_target/expected_target/matches_map/source_volume_serial/link_file_id/mtime_ft/status/errors。
顶层统计expected=16、observed、ok/errors。sidecar记录原始字段，不只汇总布尔值。
读取程序和SHA一并回传，便于审核。

## 二、只读源共享/端点核验

在SAM本地读取当前已有共享信息及本机直连端点，不修改任何配置：
- E_DRIVE是否存在，其实际本地根、是否覆盖E:\BLACKBOX；
- 是否已有共享覆盖选定D路径（可为D盘共享或上级目录共享），实际共享名及本地路径；
- SAM实际hostname与当前直连IP，192.168.100.2是否仍在本机；
- 推导共享映射示例：给每个不同共享根选一条选定D路径，source_local -> UNC。
  只基于已存在共享名，不猜D_DRIVE，不新建共享。
- 权限/访问状况仅报告只读可见的事实和错误。SAM本地看见共享不等于ZHANGWEI已经能认证访问；DESKTOP_SMB_ACCESS_VERIFIED=false保持。
- 源E/D卷serial用于交叉核验（历史E2387166462、D3187598165仅参考，不是修改盘授权）。

使用Get-SmbShare或现有可读取管理API即可；不读取凭据库，不上传密码/token/MWB密钥，不要求用户现在输入密码。
不执行net use连/断会话、不改密码/ACL/防火墙/共享/网络，不关闭WiFi或改变网口。
如果普通权限不足，记录阻塞，可按已有授权用只读管理员查询；不能为查询安装服务或改共享。
未发现D共享，就明确D_SHARE_EXISTS=false、D_SOURCE_UNC_RESOLVED=false，而不是新建。
本轮不解决WinError1326；只是确定source事实，为之后桌面一次性认证/只读预检提供正确合同。
不要对桌面E进行访问/写入试验。

输出SOURCE_SHARE_FACTS.json：
host/IP、已验证的E共享根、D可用共享根、选定路径UNC映射、卷serial、
D_SOURCE_UNC_RESOLVED、DESKTOP_SMB_ACCESS_VERIFIED=false、errors、observed_at。
仅输出与迁移范围有关的共享/接口，不上传全机私人配置。

## 三、回传与完成

回传目录：
agents/chatgpt/inbox/R9_NOTEBOOK_SOURCE_LINK_AND_SHARE_FACTS_20261013/
SAM_REPORT.md
D_REPARSE_TYPE_OVERLAY.json
SOURCE_SHARE_FACTS.json
本轮只读读取脚本、简要原始日志、FILE_SHA256.json。
不要上传大DB/业务数据。JSON和脚本SHA按实际上传字节生成。
README/报告说明：数字tag来源、16项匹配、共享事实、真实桌面访问未测、精确阻塞。

完成条件是16条数字tag/目标证据及已有共享事实查明，或每项有具体错误；不以“待用户说下一步”结束已授权只读范围。
20分钟内可上传精确结果或阻塞，不进行无关长扫描。
只更新INBOX_FOR_CHATGPT.md指向结果；不自行给桌面发写入任务、不覆盖其他inbox。等ChatGPT审核后再调度。

执行电脑=SAM；ZHANGWEI=HOLD。
COPY_AUTHORIZED=false；FORMAT_DONE=false；FULL_MIGRATION=false。
未格式化、未复制，源E/D保持只读。用户未来格式化的是台式机E，本轮与格式化无关。
有价值HUB输入/代码/证据保留。
