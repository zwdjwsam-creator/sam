# SAM｜来源本机核对，正式迁移前准备

task_id: R9_NOTEBOOK_LOCAL_SOURCE_RECONCILE_20261014_2312
execution_host: SAM
status: READY
ZHANGWEI: HOLD
METADATA_TRANSFER_TO_SAM_C_AUTHORIZED=true
LOCAL_SOURCE_READONLY_ENUMERATION_AUTHORIZED=true
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
CANDIDATE_EXECUTABLE=false
full_plan_acceptance=false

## 上轮审核与本轮目标

已阅读 agents/chatgpt/inbox/R9_DESKTOP_PREP_SOURCE_RECONCILE_HANDOFF_20261014/ZHANGWEI_REPORT.md、contract、scope、handoff、repair policy、role review 和共享配置。独立重算六份交接文本及五份 overlay 分片的字节数/SHA，均与清单一致；解析全部3694条，分片计数一致，路径无重复，3678条在releases下，其余16条与policy逐项一致；3694条有ASOF/PIT日期祖先，1342条日期祖先含TIP。目录名有日期不证明它不会参与后续发布。6GB基线/候选数据库未通过HUB直接独立读取；桌面报告的hash和quick_check，必须由SAM领取时核实。仅接受交接准备完成，未接受候选可执行或当前来源已匹配。

本轮只做一件事：在SAM的本机E/D核对选定范围的当前元数据，给出相对原来源基线的真实差异。台式机停止复制/扫描，保留交接只读共享可访问。不再做测速、复制试验、目标修复或正式迁移。

## 领取基线

先在HUB ACK，核对电脑确为SAM，记录本轮目录、PID和日志。所有日志/程序/扫描数据库写入SAM的 C:\LAN_SHARE_REPORT\R9_LOCAL_SOURCE_RECONCILE_20261014，来源E/D不写。

交接包：agents/chatgpt/inbox/R9_DESKTOP_PREP_SOURCE_RECONCILE_HANDOFF_20261014/
只读共享：\\192.168.100.1\R9_SOURCE_BASELINE_20261014
本机若已有完整且SHA相同的94e6基线可直接复用；否则检查C空间够基线6025072640字节及后续清单，再把共享里的SOURCE_BASELINE.sqlite和小型交接材料复制到SAM的C。这是元数据传递授权，不是复制业务数据授权。

使用现有Windows会话/凭据。只尝试现有通道；不打开密码窗口、不要求用户输密码、不读/上传凭据、不新建登录、不断开IPC$/其他连接。访问失败就回传具体错误和阻塞，不循环重试或改共享权限。SAM_ACCESS_VERIFIED必须是本机实测。

基线必须：
- SHA256=94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba
- bytes=6025072640，冻结副本没有非空WAL/journal；只读quick_check=ok。
- SOURCE_SCOPE.json SHA=e03948d4a23aa2bd63c4d4b7644e3682e06a22c5fa64b1595892bdbcb284607f。
- SOURCE_BASELINE_CONTRACT.json SHA=46655c97069c19ad010faec358cc12f2c9f5b31615dc5280406b59fa7dd20d3d。
不得在源基线上checkpoint、修改或重建。候选e6c49...不能替代94e6来源事实，也不必传候选。基线缺失或校验失败则停在此处，报告阻塞，不另造一份历史基线。

## 一次本机no-follow核对

先记录来源E/D当前卷号，预期E=2387166462，D=3187598165；不匹配则停止，防止读错盘。这不是桌面目标E盘。

使用已有修复后的可靠本机枚举组件；只补完成本轮所必需的适配，不重建迁移框架。扫描只走SAM本机路径，不从台式机对几百万路径经SMB查询，不跟随junction，不读取全部业务文件内容或全量hash。

范围以SOURCE_SCOPE.json为准：
1. E:\BLACKBOX整树；不含其兄弟目录或E:\BLACKBOX_MIGRATION_AUDIT_R1。
2. D八个完整根：BLACKBOX_DESKTOP_INIT_R1、BLACKBOX_REMOTE_LINK_R1、JQ、backtest_lab、backtest_lab_backups、backtest_lab_candidate_releases、backtest_lab_shadow_experiments、blackbox_data。
3. D:\CURSOR_TASK_ARCHIVE仅 JQ_DAILY_20260903_SUCCESSOR_BUILD_AND_ATOMIC_PUBLISH_R1\pit_products；不扩大到其他档案目录。
4. 保留每个普通目录及空目录。旧基线空目录754只是旧数量，不要求当前数强行相同。

保存路径、类型、volume/file id、普通文件logical_size、能获取的当前mtime(FILETIME)、重解析数字tag与原始target；metadata获取必须no-follow。记录任何无法读取/变化/枚举错误，不吞错。不要用目标身份代替来源身份。当前数据库持久化在C，流式处理、有界内存。队列空且全部范围完成才算完整；不可仅采样或数量相等就通过。需断点时保留队列和已处理标记，不丢已发现子目录、不并行重复启动同一轮。

归一比较：
- E普通文件的基线volume=2387166462。
- E普通目录/重解析的基线volume存为11708076955747828990；只对这项已知历史编码按低32位2387166462比较，保留原值。其他不明身份差异不能任意截断掩盖。
- D普通文件/目录volume=3187598165。
- D16条reparse在paths无volume/file id，links表也没有file-id列。可比路径、tag、原始target；基线文件身份记UNPROVEN，当前no-follow身份另存，不把NULL当变化，也不凭空证明相同。
- 比较原始来源重解析事实。已知CLEAN的CURRENT_POINTER_COPY.json在源上仍是坏junction；ASOF普通文件才是来源文件。候选新增CLEAN普通别名只属于目标，绝不能误报为源文件删除/类型差异。
- 长链只记录原始边，不跟随打开到WinError1921再宣称坏源。本轮不修来源链接，也不把目标flatten政策覆盖来源事实。

## 差异与扫描期间变化

逐项比较新增、删除、类型、可证身份、普通文件大小、reparse tag/target；按E和各D根汇总，详细差异留C的SQLite/分片，不上传GB数据库。记录当前唯一实体数、唯一码大小和别名数，实体大小不一致单列。

旧基线没有mtime/hash、历史USN锚点ABSENT。即使路径/身份/大小相同，HISTORICAL_CONTENT_MATCH=UNPROVEN；不得声称旧内容未改。当前mtime只是新观察值，供以后复制检查使用。

如权限已足够且卷支持只读查询，记录扫描开始/结束的JournalId、NextUSN及可用的扫描期间变更证据；不创建/重置journal，不修改卷。无日志或未核对期间变更时明确SOURCE_SCAN_STABILITY=UNPROVEN。有期间变更的路径列出，允许有界复查受影响对象，但不能无限整盘重扫。元数据遍历完成与单一时点稳定性分开报告。

发现真实delta是正常核对结果：SOURCE_CURRENT_MATCH=false并列出差异，不为了保持旧SHA忽略新文件。只有全部范围完成、无读取错误且已比较的字段无差异，才可写SOURCE_METADATA_MATCH=true；同时写明内容历史仍未证实及扫描稳定性限制。本轮不改正式/候选计划；后续根据真实delta更新来源计划，再重审目标修复。

不得停止交易/行情/业务进程、改源文件、删除现场、格式化、写桌面E、执行production copy、改授权或自动迁移。C空间不足/身份错误/基线失败要保留进度并回报，不能清理业务腾空间。

## 回传与停止

接单后上传ACK；扫描长时运行则回传RUNNING进度、PID/命令、已枚举目录/路径、队列量、日志位置，继续同一进程到完成，不把RUNNING报PASS。若环境要求后台运行，用可持续的单个任务并保留日志/恢复状态。

回传目录：agents/chatgpt/inbox/R9_NOTEBOOK_LOCAL_SOURCE_RECONCILE_20261014/
至少SAM_REPORT.md、SOURCE_RECONCILE_SUMMARY.json、程序/配置或准确引用、FILE_SHA256.json。小型差异样本可分片；完整当前清单及delta数据库留C，报告路径、大小、SHA、quick_check和完整性/错误计数。
报告SAM_ACCESS_VERIFIED、BASELINE_VERIFIED、SOURCE_ENUMERATION_COMPLETE、SOURCE_METADATA_MATCH、SOURCE_CURRENT_MATCH及判定范围、SOURCE_SCAN_STABILITY、HISTORICAL_CONTENT_MATCH、USN可用性、逐根新旧统计/真实delta、未完成/不稳定事项及下一步依据。
更新INBOX_FOR_CHATGPT.md。完成/明确阻塞后停止，等HUB审核。所有业务复制授权仍false；不要把本次源扫描通过等同正式迁移放行。
