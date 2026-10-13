# ZHANGWEI台式机｜冻结绑定补漏与1326只读诊断

task_id: R9_DESKTOP_FREEZE_BINDING_AND_SMB_DIAG_20261013_2035
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
supersedes: R9_DESKTOP_BIND_SOURCE_FACTS_AND_FINAL_PREP_20261013_2016
SAM: HOLD
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true

## 审核结论

有后续任务，仍ZHANGWEI执行，SAM待命。
2016本轮40项纯测试独立复跑通过（禁止真实WinAPI，使用Windows路径语义；两个硬编码C路径的事实JSON由已核验HUB原文件提供为测试fixture）。
4825数字tag、冻结plan文件SHA、orphan查询ix_entity、一次1326后停止均有交付证据。
完整清单31项中27项存在且SHA/字节匹配，以下4项只列清单未在本轮目录上传：
PLAN_READER_VALIDATION.json、ADVERSARIAL_ACCEPTANCE_RESULTS.json、
WIN32_WRAPPER_TRACE.json、REAL_METADATA_BINDING_SAMPLES.json。
补实际文件或从清单移除并明确历史引用，不继续交付“清单有、文件没有”的完整包。

当前plan SHA 94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba、
6025072640字节、无WAL的本机证据收到；ChatGPT未获取6GB库，不冒称独立重hash。
但冻结条件在代码里还未强制，IMPLEMENTATION_READY仍未通过审核。保留既有40项/A-B-C/严格验收，不重新重建计划。

## 一、修非空WAL绕过与完整运行代码绑定

ChatGPT用当前代码在小型SQLite精确复现：
1. plan启用WAL，_contract绑定正常plan，正常production_run完成；
2. 保持writer连接，UPDATE entities SET mtime='changed-in-WAL'后COMMIT；
3. WAL4152字节，reader.connect只读连接调用plan_digest：
   PRAGMA wal_checkpoint(TRUNCATE)异常被吞掉，随后只hash main文件；
4. 摘要与旧run一样，full_acceptance仍true、reasons=[]。

修法：
- 冻结/检查点是准备工具的独立步骤，不在只读摘要函数中偷偷执行checkpoint。
- 只有已确认无待合并WAL/热journal/活动写事务的不可变计划才允许绑定。
- 非空WAL或无法确认冻结应明确PLAN_NOT_FROZEN拒绝；不能try/except后继续hash main。
- 如采用备份快照，hash/read必须同一个冻结快照，不hash main却查询main+WAL；不要不必要再复制6GB。
- 同计数变更测试保留，新增WAL已提交元数据变更、未提交写事务、checkpoint失败、零长度WAL与正常冻结计划。
- runner在首个写入前验证实际冻结plan/input/code绑定；验收复核同一身份，不只caller和state重复字符串。
- 主plan本轮不需改内容；无需反复重hash原9GB输入。现有无WALplan可保留一次冻结SHA证据。

另一个独立复现：
r9_source_contract.code_digest只列6个模块，修改r9_pilot_common_r9fix.py后摘要不变。
common是实际Win32读写/身份底层，不能漏。
CODE digest包括全部实际运行Python模块/common/CLI/adapter/source契约和影响执行配置；
测试源码可独立清单，不混为运行代码。模块集合/排序/长度边界确定，遗漏文件失败。
修改common、CLI、关键配置或缺模块均应拒绝旧run绑定；正常同版通过。
不建立签名服务等新基础设施，简单文件SHA清单+规范摘要即可。

## 二、修普通共享依赖及可移植测试

share_contract已验证D_DRIVE，但随后却要求存在D$才选择D_DRIVE。
只有E_DRIVE/D_DRIVE普通共享、没有D$的合法facts，当前会报D_DRIVE_NOT_PRESENT。
移除D$前置条件；选择已验证D_DRIVE->D:\即可，根路径不符失败，不能自动改用D$。
允许范围仍仅selected D计划/根，不扩大到全D。

test_r9_bind当前直接读C:\LAN_SHARE_REPORT\…两个JSON，包在干净目录不可复跑。
把已核验小型事实JSON纳入fixtures或参数化明确fixture路径；
不改验收/绑定业务逻辑来适配测试，也不联网才发现fixture缺失。
FILE_SHA256清单所有条目实际上传/可下载，补上述4项或明确历史依赖。
干净目录运行全套纯测试，通过每次新增回归；不再以本机残留模块/文件证明包完整。

## 三、1326只读凭据状态诊断（不重新尝试连接）

已知SAM:
192.168.100.2，E_DRIVE->E:\、D_DRIVE->D:\均存在；
桌面20:xx只读GetFileAttributesW访问E_DRIVE\BLACKBOX返回1326。
这轮不重复UNC登录尝试，不自动输入任何密码。

只在ZHANGWEI读取以下与SAM/.2相关事实：
- 本机当前Windows登录用户名/域（whoami等），区分Windows身份与Codex CLI登录；
- 当前Get-SmbConnection/Get-SmbMapping中SAM、192.168.100.2的会话/账号/错误状态；
- Windows已保存凭据的相关目标名称及用户名/域元数据（cmdkey /list仅筛SAM/.2）；
- 已有SMBClient相关日志中最近这次请求的时间、server、错误码和可见账号信息。
只上传相关摘要；不要输出密码/token、读取凭据明文、dump全账户/全日志或私人配置。
没有相关会话/凭据/日志就明确NONE/NOT_AVAILABLE，不编原因。

本轮诊断不修改凭据，不执行cmdkey /delete或新增，不net use连/断，不清理全部SMB会话；
不改SAM/桌面账号密码、共享权限、访客/NTLM策略、网络/防火墙/MWB。
不建立临时共享用户/不启用不安全Guest来绕过。
1326不能只凭代码认定具体是密码错、用户名错、账号受限中的哪一个；按日志证据列“已证实/待SAM服务器日志”。
若桌面证据不足，报告精确需要源SAM的哪条只读服务器日志，供下一轮一次查询；不要自行给SAM发执行任务。
如必须用户输入密码，将所需账号/原生Windows输入位置作为具体候选流程报告；不能在HUB/聊天收密码，本轮不弹提示/执行登录变更。

代码离线修复照常完成；SMB诊断只做有限读取，不陷入长时间排查。
SOURCE_ACCESS_VALID=false、SOURCE_LIVE_PREFLIGHT_PENDING=true仍成立，除非另有真实访问证据；本轮不增加连接尝试。
认证成功也不会自动授权格式化或复制。

## 回传

agents/chatgpt/inbox/R9_DESKTOP_FREEZE_BINDING_AND_SMB_DIAG_20261013/
完整源码/config/fixtures/CLI/测试、ZHANGWEI_REPORT.md、
FILE_SHA256.json、TEST_RESULTS_FULL.json（逐case）、
FREEZE_BINDING_ADVERSARIAL.json、RUNTIME_CODE_BINDING.json、
SMB_AUTH_DIAG_READONLY.json、EXECUTOR_READINESS.json。
明确本轮代码准备结果与源认证阻塞分别；实盘NOT_RUN。
大plan/state留C，修代码不重建计划或重复hash大输入。
已有40项、A/B/C、严格验收、类型/UNC与时间转换不能回退。

本轮连续完成已授权离线修复和只读诊断，30分钟可报检查点后继续。
未修完即PARTIAL，不自报完整实施READY。完成交ChatGPT审核。
执行电脑=ZHANGWEI；SAM=HOLD。有后续任务，本文件即下一轮。
COPY_AUTHORIZED=false；FORMAT_DONE=false；FULL_MIGRATION=false。
不格式化、不复制、不在C/E做真实hardlink/junction试验、不在E写入，不修改源盘/账号/网络/MWB/P7。
用户本人未来手动格式化台式机E后才进入真实试验。保留有价值HUB证据。
完成更新INBOX_FOR_CHATGPT.md。
