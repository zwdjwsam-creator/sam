# SAM笔记本｜只读查询源端SMB失败登录证据

task_id: R9_NOTEBOOK_SMB_AUTH_EVENT_READONLY_20261013_2101
target: SAM
status: READY
phase: SOURCE_AUTH_READONLY_DIAG
desktop_ZHANGWEI: HOLD
supersedes: R9_DESKTOP_FREEZE_BINDING_AND_SMB_DIAG_20261013_2035
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true

## 调度与已核验状态

本轮执行电脑改为SAM，ZHANGWEI停止待命，不再次连接UNC。
桌面2035包41项纯测试已由ChatGPT独立复跑通过；修改common会改变运行code digest；
WAL提交变更被PLAN_NOT_FROZEN拒绝；D_DRIVE无需D$，相关修复保留。
代码纯模拟结果不等于实盘验收，IMPLEMENTATION_READY仍false。

源事实已核验：
SAM=192.168.100.2，E_DRIVE->E:\、D_DRIVE->D:\存在，
16条D本体数字tag=0xA0000003，与R3目标一致。
桌面曾一次只读访问\\192.168.100.2\E_DRIVE\BLACKBOX返回1326，此后没有重试。
ZHANGWEI当前Windows身份zhangwei\admin，没有匹配SAM/.2的SMB映射和已保存凭据；
Get-SmbConnection、SMBClient日志NOT_AVAILABLE。没有这些凭据并不能直接证明具体拒绝原因。
需要SAM上既有失败登录事件，区分账号/密码/限制；本轮只读，不修改认证。

补充包记录，SAM本轮不修桌面代码：
2035 FILE清单36项，其中31项存在且SHA/大小匹配；
SOURCE_INPUT_CONTRACT、D_TYPE_JOIN_AUDIT、FINAL_PLAN_BINDING、QUERY_PLAN_AUDIT、READONLY_SOURCE_PREFLIGHT仅列在清单，实际可从2016历史目录取得。
后续桌面须规范历史引用或完整补包。此项不妨碍本轮源端事实读取。

## 1. 查询已有源端事件，不制造新登录

在SAM读取Security事件4625及既有SMBServer相关日志；
重点时间窗口：2026-10-13 20:10–20:40 +08:00（UTC12:10–12:40）。
只筛与ZHANGWEI/桌面网络访问相关，LogonType=3、WorkstationName=ZHANGWEI或源直连IP相关；
历史桌面直连IP192.168.100.1仅筛选参考，以事件实际IP为准。
最多读该窗口相关80条；不全量dump日志，不主动从桌面重现1326，不开启/修改审计策略。

用Get-WinEvent的FilterHashtable时间/EventID或等效只读API，从事件XML按字段名读取：
TimeCreated、EventID、RecordID、TargetUserName、TargetDomainName、
WorkstationName、IpAddress、LogonType、Status、SubStatus、
FailureReason、AuthenticationPackageName、LogonProcessName。
提供最接近本次请求的原始字段与少量上下文，缺字段明确null。
不要依赖本地化message的文字位置，不将日志解析失败说成事件不存在。

如果Security权限不足，可在已有授权范围执行只读管理员查询；无法读取就记录精确AccessDenied/权限状态，不改ACL或日志配置。
如果窗口无相关事件，明确NO_MATCHING_EVENT；SMBServer日志禁用/不存在、审计未记录、查询失败分别报告，不编造根因。
可只读查看日志是否存在/启用及相关审计项状态，不能启用/更改它们。
参考官方字段/状态说明：
https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4625
仅有通用Status而SubStatus=0/缺失时保持原因UNKNOWN，不把1326硬判成密码错。
若有明确SubStatus，则指出它支持“账号不存在/密码错误/账号禁用或限制”等哪项，并保留原码。

## 2. 核查涉及账号的只读事实

读取SAM当前Windows登录用户名/域；
对事件实际TargetUserName及SAM当前使用账号，读取本机账号是否存在、Enabled、PrincipalSource（Local/MicrosoftAccount等）和可见的PasswordRequired字段。
不要枚举并上传所有用户详情，不读密码/凭据明文/密码hash，不输出SID/完整私人配置。
PasswordRequired=false不单独证明密码为空；没有实际证据就UNKNOWN。

只读查看E_DRIVE/D_DRIVE现有共享访问条目中与候选账号相关的Read/Change/Full/Deny，供选择正确来源账号；不改权限。
明确以下区别：
- zhangwei\admin是桌面登录身份，不自动等于SAM认可的来源账号；
- Codex CLI登录不是Windows SMB登录；
- SAM本地共享可见不等于桌面已完成认证。
如事件账号不存在，给出目前真实存在且适用于来源共享的账号格式候选（如SAM\实际名/正确MicrosoftAccount格式），依据写明。
如事件明确密码错误，说明需要该来源账号Windows网络登录凭据；不收密码、不重置密码、不新建临时用户。
不要将PIN当网络密码，亦不要推定用户已知密码。

## 3. 最小下一步候选与回传

报告只列证据支持的原因与候选，不执行凭据修复：
AUTH_FAILURE_CAUSE（或UNKNOWN）
AUTH_FAILURE_EVIDENCE（事件时间+原Status/SubStatus）
SOURCE_ACCOUNT_CANDIDATE（如无法证明则null）
USER_LOCAL_SECRET_ENTRY_NEEDED（true/false/UNKNOWN）
NEXT_MINIMAL_ACTION（正确账号+Windows原生本地凭据输入流程，或缺哪项信息）

不要弹登录框、执行net use、添加/删除cmdkey、清空SMB会话、调整密码/ACL/共享/Guest/NTLM/防火墙/网络/MWB；
不降级不安全Guest、不创建临时共享用户、不改源数据。
本轮只能写C:\LAN_SHARE_REPORT内的诊断脚本/过滤后的JSON及日志。
不在E/D源盘写入，不访问桌面目标E，不复制业务数据。

回传：
agents/chatgpt/inbox/R9_NOTEBOOK_SMB_AUTH_EVENT_READONLY_20261013/
SAM_REPORT.md
SMB_SERVER_AUTH_EVENTS.json（仅匹配事件及查询状态）
SOURCE_ACCOUNT_AUTH_INFO.json（相关账号元数据及现有共享访问摘要）
AUTH_NEXT_ACTION.json（证据/UNKNOWN/候选）
只读查询脚本、FILE_SHA256.json。
所有清单条目实际上传，SHA按上传原始字节生成；不能只列本机路径。
10–15分钟完成有限查询，有日志/权限阻塞也准确回传，不开展长扫描或无关网络排查。

本轮不自行给桌面发任务。只更新INBOX_FOR_CHATGPT.md指向回执，等待ChatGPT审核后下一调度。
执行电脑=SAM；ZHANGWEI=HOLD。
SOURCE_ACCESS_VALID=false、DESKTOP_SMB_ACCESS_VERIFIED=false保持，除非有已存在真实认证成功证据（不能凭共享列表置true）。
COPY_AUTHORIZED=false；FORMAT_DONE=false；FULL_MIGRATION=false；Windows业务写入NOT_RUN。
仍准备期，不格式化、不复制、不做实盘链接试验。用户未来格式化的是台式机E，本轮无格式化动作。
保留有价值HUB输入、代码和证据。
