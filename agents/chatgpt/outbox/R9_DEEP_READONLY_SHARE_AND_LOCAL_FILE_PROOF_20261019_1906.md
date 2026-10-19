# 消除SMB路径前缀限制：源端本地证明与临时深层只读共享

review_id: R9_DEEP_READONLY_SHARE_AND_LOCAL_FILE_PROOF_20261019_1906
primary_execution_host: ZHANGWEI
source_assist_host: SAM
USER_FULL_MIGRATION_AUTHORIZATION=STILL_VALID
COPY_AUTHORIZED=false
FULL_MIGRATION=false

## 审核事实
已读950e3d报告、REAL_SOURCE_CAPABILITY及r9_relative_open.py。
原BLACKBOX共享比E_DRIVE\BLACKBOX仅短8字符；133条近限文件129可读、4仍206；relative NtCreateFile读通3个，最后844424930324643/816B于file阶段0xC0000039/161。
该状态只说明本次路径打开失败，不能证明文件损坏/不存在。helper已核对：传相对末分量，RootDirectory为父句柄，FILE_OPEN、不跟reparse。SMB内部仍可能受完整服务端路径约束，不能假设多次同样调用能解决。
计划无历史内容SHA，三个SHA是本轮来源实测值；“与计划一致”只适用于volume/file_id/size，不能声称SHA与计划历史hash匹配。
保持IMPLEMENTATION_READY=false；原state/code/plan不动。

## 方案与许可边界
将现有深层普通目录作为新的临时SMB只读入口，保持原来源文件与逻辑目录不变。新入口比根BLACKBOX更短，避免最后分量仍处SMB内部长度边界。
这是原迁移范围内可撤销的访问配置，不增加要迁移的数据、不改源文件/NTFS ACL/账号/密码/安全策略/网络端口。1840中“不得新建share”的工作约束对此唯一明确临时share解除；其他共享不改。不靠空密码/Guest或Everyone扩大访问。
Microsoft New-SmbShare支持-Path/-ReadAccess/-Temporary：
https://learn.microsoft.com/en-us/powershell/module/smbshare/new-smbshare
本方案须实测，不先宣称能解决。

## 笔记本SAM执行
task_id: R9_NOTEBOOK_DEEP_READONLY_SHARE_PROOF_20261019_1906
status: READY
先ACK。旧1005凭据/UAC诊断任务已结束，本任务替代旧邮箱认证HOLD，仅执行本限定方案。

A. 只读核对来源卷2387166462及现存普通祖先（不创建目录）：
E:\BLACKBOX\数据\原始只读\JQData_reference_dictionary\31_jq_pre_download_experiment_cleanup_dryrun\manifest_backup\数据\原始只读\JQData_reference_dictionary\31_jq_pre_download_experiment_cleanup_dryrun\manifest_backup
此路径是1826已查普通祖先，约205字符；本机仍须查身份与非reparse，不从相似名字猜。
检查每个祖先普通目录/卷。路径不同、缺失、reparse则停，不自动换任意目录。
记录anchor本机完整路径、volume/file_id、长度，以及固定共享UNC与原prefix的可核验映射。

B. 先做816B文件的本机真实只读证明：
可用本机E卷的OpenFileById按已给file_id=844424930324643打开，或本机分段目录句柄；不在SMB上试OpenFileById（微软接口不支持SMB3），不修改文件。
核volume/file_id/size=816、普通file；同句柄读完SHA并查前后identity/mtime。不因只知道fileid就假定是同文件，不上传内容到公共HUB，只交metadata/hash/原始状态。
若本地也失败，报告真实错误；不认定坏数据、不改名、不恢复复制。继续共享步骤仅在anchor真实有效时允许。

C. 创建唯一临时只读共享：
name=R9LP_RO
path=上述已验证现存anchor
ReadAccess仅SAM\ThinkPad；不授予Everyone/Guest/Anonymous、不新增FullAccess/ChangeAccess，不修改NTFS ACL。
优先New-SmbShare -Name R9LP_RO -Path <exact verified anchor> -ReadAccess 'SAM\ThinkPad' -Temporary -CachingMode None。
使用正常本机管理员通道；如需UAC，正常提示一次，由用户本机确认，不绕过、不安装服务/任务。
若同名share已存在，先核Path/ReadAccess/Temporary属性一致才复用，不删除/覆盖不一致share。创建后Get-SmbShare/Get-SmbShareAccess只读确认事实及权限。
不要创建源端hardlink/junction/新目录或staging副本，不搬动源文件。
此share用于迁移完成前保持可用，完成后再按明确清理任务只移除本task创建的share（不删除任何目录）；重启消失时回报，不静默切到别的根。
本轮若不支持Temporary参数或需策略变更，不自动去掉限制，报告确切错误。

D. 经HUB交付：
agents/chatgpt/inbox/R9_NOTEBOOK_DEEP_READONLY_SHARE_PROOF_20261019/
ACK.md、SAM_REPORT.md、DEEP_SHARE_FACTS.json、LOCAL_FILE_844424930324643.json。
DEEP_SHARE_FACTS包括真实hostname、sourceIP192.168.100.2、name/path、root identity/NTFS卷、ReadAccess/Temporary、创建或复用时间。不要上传任何密码/业务payload。
更新INBOX_FOR_CHATGPT，通知台式机原1840交接目录DEEP_SHARE_READY.json（只存指针/共享事实）。
若UAC等待或本地读取失败据实标记，不称完成。其他范围仍不动。

## 台式机ZHANGWEI接续原1840
task_id: R9_DESKTOP_LONGPATH_ACCESS_AND_RESUME_PREP_20261019_1840
followup_id: R9_DESKTOP_USE_DEEP_READONLY_SHARE_20261019_1906
status: READY_CONTINUE_PREP
先FOLLOWUP_ACK，不重复133条全量探测/SMB相同错误调用。
1. 读取SAM的DEEP_SHARE_FACTS；未到可先完成C目标temp/状态迁移代码与隔离测试，不能无证据虚构共享身份。
2. 通过固定\\192.168.100.2\R9LP_RO核对anchor volume/file_id与SAM本机一致；只允许该固定server/share/已验证anchor映射。
   从现有候选4个失败实体原始inventory提取anchor后相对尾部，禁止字符串全局replace、..、绝对覆盖或reparse跳转。清单源路径/目标路径/entity_key不变，访问别名另列绑定。
   精确计算新UNC API UTF16长度与节省量；预计缩短约200字符，但以实际值为准，需留下合理余量。新入口必须真实打开4个文件，分别核原plan volume/file_id/size及前后稳定identity、内容SHA；816B结果与SAM本地SHA一致。若一个仍失败立即回报阶段/NTSTATUS，不能把剩余一个静默跳过。
   133近限条目只在现有C候选复核它们是否在该anchor范围；范围外保持原访问或已证实方式，不能将任意实体重定向新share。可进行必要metadata一致性验证，不为此全源扫描。
3. 新share4文件全部读通后，优先用此受限源访问映射替代复杂通用SMB native fallback，保持正常路径行为不变；不把未成功native支路做全局默认。
   生产合同显式绑定original inventory prefix、aliasUNC、source root身份、来源卷及事实digest；canonical源与实际access_path区分记录，同句柄volume/file_id/size校验不能跳过或伪造。
4. 继续1840原目标侧最小temp basename、近限commit/observe/content_sha/list_nofollow与独立验收的完整C隔离验证。源短共享解决不代表目标路径已解决。真实目标E不写，原state不改。
5. 完成原1840的state一致性副本迁移脚本/合成测试、精确代码diff/完整hash（新增module入digest）、合同copy=false、新run/state及保留1083975 DONE证据方案。不要建空state重来、不直接改旧run_bind。
   准备不全量重读348.9GB；正式恢复原验证可能重hash DONE要如实说明，不私自取消校验。
6. 所有证据回原1840目录，给一个可审的最小集成交付，完成停待ChatGPT技术复核。用户原迁移授权有效，无需再次问用户是否继续，但当前没有正式恢复写入令。

## 不变边界
源E/D和真实目标E业务对象不新增、不删、不改名；只有本限定源端临时share配置与C开发/报告可写。
不改用户/密码/NTFS ACL/防火墙/SMB策略，不公开payload/密钥，不重建6GB，不跳过文件、不把部分能力称IMPLEMENTATION_READY。
