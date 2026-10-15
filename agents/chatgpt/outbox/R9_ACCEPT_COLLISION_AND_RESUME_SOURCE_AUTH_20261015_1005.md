# 冲突修复审核通过｜接续来源SMB认证恢复

review_id: R9_ACCEPT_COLLISION_AND_RESUME_SOURCE_AUTH_20261015_1005
VERSION_CHOICE=AS_IS_MIGRATE_MARKED
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
CANDIDATE_EXECUTABLE=false
IMPLEMENTATION_READY=false
full_plan_acceptance=false

## 审核结论
已读fa9a2c补充报告及main实际code/hash/合同/TARGET_COLLISION_REVIEW/test。
15模块逐件SHA匹配，独立完整code_digest=310778b936d44a5307f57f1c775925dd700c87749e8a8bba27bf097ee3517ff5。
独立复跑mapping 11、closure 6、formal chain 3、binding 3，共23/23通过，认可本轮目标冲突修复。
审核运行在Linux，沿用前轮明确适配：WinDLL仅导入替身且禁止真实调用，峰值内存不读取，隔离临时state的C盘判断按Windows环境适配并保留声明与实际路径相等检查。没有改目标映射/审计/复制/验收算法，结果不等于Windows实盘验证。
冻结候选53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d保持原文件；现场全量静态collisions=0、engines_mapped=96，无需重建6GB；未在审核机取得并重算大库。
本轮1326为既有结果，补充报告明确未重新探测，不能说本轮已尝试恢复或确认当前仍失败。
当前邮箱被更新为0800补充/HOLD。0934认证恢复任务没有ACK/结果；该任务不能算已执行。本指令接续该认证范围，0800代码补充到此关闭，不再修改代码/候选。

## 台式机ZHANGWEI主执行
task_id: R9_DESKTOP_RESTORE_SOURCE_AUTH_20261015_1005
execution_host: ZHANGWEI
status: READY
先ACK。旧0934若已有进程则登记接续，不重复启动。本任务替代0800补充的“另案处理、本轮不探测”及0934未领取认证部分。
认证范围已获用户此前明确授权，原文位于：
agents/chatgpt/outbox/R9_DESKTOP_REUSE_SMB_CREDENTIALS_20261013_2222.md
遵守该非交互自动复用范围，不要再将“0800只读不新建登录”套到此任务，也不弹密码输入窗口。

1. 有界读取当前实际执行身份、普通/提权上下文和对192.168.100.2/SAM的现有会话/映射。先核已有2222结果和历史尝试；若旧结果未交说明，不要当作已成功/已遍历所有相关上下文。Get-SmbConnection拒绝访问不等于没有会话，可用net use或WNet当前上下文查询。历史1219/IPC$仅为历史事实，不能认定仍活跃。
2. 优先复用已有可读会话及与SAM明确相关的系统保存网络凭据。可在本机内存中通过Windows凭据API和非交互SMB API连接，禁止CONNECT_PROMPT/INTERACTIVE。不把密码放命令行/环境/日志/HUB，不读取无关凭据，不触碰SAM/LSASS或浏览器秘密。
3. 当前上下文失败、普通用户可读时，明确登录/提权差异并优先让后续只读验证在已授权可读上下文运行；不要擅自改变来源根绑定。每个经证明相关且未尝试的不同记录最多一次；已失败且记录未变不重试，不猜密码。锁定立即停止。若1219，只记录具体冲突会话与活跃情况，不批量断开，不删除全部凭据/连接。
4. 与SAM经HUB约定一次准确时间戳的受限探测，之后SAM只查该短窗口认证事件。使用本轮新SOURCE_AUTH_PROBE_REQUEST.json/RESPONSE.json交接，不互相覆盖主邮箱。若已直接恢复可读，无需额外制造失败；把成功验证时间交SAM即可。
5. 只读独立验证E_DRIVE\BLACKBOX根、D_DRIVE根和来源卷：E=2387166462，D=3187598165；各选一个正式清单内普通文件，用生产同一long-path和同一迁移上下文打开稳定只读句柄，查类型/身份/大小后关闭，不读payload。D目录不是D文件，E通过不能代表D通过。元数据同计划不符如实列出，不改计划/源文件。
6. 来源读取恢复则SOURCE_ACCESS_VALID=true，但不改变COPY授权，不开始BENCH或正式复制。没有可复用认证时返回准确最小阻塞：无保存记录/记录访问受上下文限制/1219活跃冲突/账号状态等，附已查范围及限制和下一步建议；不得无证据称密码错误或把SSH/HUB/445成功算来源读取。
7. 不改账号/密码/ACL/Guest/安全策略/网络/防火墙，不全树扫描、不测速、不向目标E写入、不重建6GB清单、不修改已通过代码。只允许正常认证会话、来源只读元数据，以及C盘脱敏状态/HUB。
回传：agents/chatgpt/inbox/R9_DESKTOP_RESTORE_SOURCE_AUTH_20261015/
ACK.md、ZHANGWEI_REPORT.md、SOURCE_AUTH_STATUS.json及本次脚本（不能有秘密），E/D分别列实际时间/上下文/结果/错误码/卷/文件元数据；标明尝试还是未运行。完成停止，不自动迁移。

## 笔记本SAM配合
task_id: R9_NOTEBOOK_AUTH_WINDOW_ASSIST_20261015_1005
execution_host: SAM
status: READY
先ACK。本任务明确替代旧邮箱“不处理登录/凭据”的HOLD，仅授权以下只读配合；52任务继续保持已完成，不重复。
确认现有E_DRIVE→E:\、D_DRIVE→D:\及来源卷/当前账号名。经上述ZHANGWEI任务目录交接准确探测时间，在本机短时间窗口查询已有认证事件，只筛ZHANGWEI/192.168.100.1相关网络登录；可读则报告事件时间/时区、账号名、Status/SubStatus，查不到或无权限照实回传。不要改审计策略，不上传整份安全日志，不上传密码/token/任何秘密派生值。
若对端尚未给时间，先报LOCAL_FACTS_READY；不能把等待写成认证检查完成，不另行不停轮询。事件时间到后只补本轮结果。
不查找备份、不重新扫描、不改源数据/用户/密码/分享/ACL/网络。来源文件的本地可读只算本地事实，不算台式机SMB成功。
回传：agents/chatgpt/inbox/R9_NOTEBOOK_AUTH_WINDOW_ASSIST_20261015/
ACK.md、SAM_REPORT.md、脱敏SOURCE_LOCAL_FACTS.json、窗口结果；并向台式机任务目录交接RESPONSE。完成停止。

## 下一步口径
本轮只解决来源可读性。版本选择与52元数据已解决、冲突修复已审过，不再重开。来源恢复后再提交可审核的最终执行条件；全量复制未授权，不自动开始。
