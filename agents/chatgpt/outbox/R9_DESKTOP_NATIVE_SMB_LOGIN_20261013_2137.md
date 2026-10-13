# ZHANGWEI台式机｜Windows原生凭据认证与只读源核验

task_id: R9_DESKTOP_NATIVE_SMB_LOGIN_20261013_2137
target: ZHANGWEI
status: READY
phase: SOURCE_AUTH_INTERACTIVE_READONLY
SAM: HOLD
supersedes: R9_NOTEBOOK_SMB_AUTH_EVENT_READONLY_20261013_2101
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true

## 已审核结果与最小下一步

SAM本轮5份报告/JSON/只读脚本的原始SHA与大小已独立核对全部匹配。
20:10–20:40窗口Security4625无匹配事件；SMBServer元数据读取Unauthorized。
Unauthorized不能记为“日志不存在”，读取状态是UNKNOWN/ACCESS_DENIED。
具体1326根因仍未证实，不再为了这个窗口重复查相同日志或扩大无关扫描。

已确认：
SAM当前Windows账号SAM\ThinkPad；
本地ThinkPad存在、Enabled=true、PrincipalSource=Local；
PasswordRequired=false不证明密码为空。
E_DRIVE/D_DRIVE共享级Everyone Allow Full，不等于桌面已认证，也不能证明NTFS/网络登录有效。
桌面当前zhangwei\admin没有匹配来源凭据，不自动等于SAM认可的来源账号。

下一步使用已存在的SAM\ThinkPad候选，通过Windows原生凭据UI建立一次普通SMB会话。
本轮允许这一正常认证动作和只读源metadata核验；不修改任何账号密码、共享/ACL、Guest/NTLM策略或网络。
所有复制/目标写入授权仍false，认证成功绝不触发复制。

## 现成脚本（直接使用，不重写一套登录器）

HUB：
agents/chatgpt/outbox/R9_DESKTOP_NATIVE_SMB_LOGIN_20261013_2137/r9_native_smb_login.py
原始UTF-8 SHA256：
0a0d2821cec0d923b27b931de0c23197e235f8f3d8daeb99b6ce4155c78f4376

脚本已由ChatGPT语法检查并使用假Windows API分别验证成功、取消、1326失败、错误来源卷。
这些是模拟验证；Windows真实调用由本轮执行。
它只在Windows ZHANGWEI运行：
WNetUseConnectionW，指定SAM\ThinkPad、\\192.168.100.2\E_DRIVE，
CONNECT_INTERACTIVE|CONNECT_PROMPT，lpPassword=NULL；
密码由Windows提供者的原生GUI处理，脚本无密码参数/缓冲区/凭据读取接口。
不映射盘符，不设置保存凭据/更新profile标志，不访问密码库，不调用cmdkey/net use。
成功后只读取E BLACKBOX与D共享根的attrs/卷serial/FileId，不读业务内容、不创建业务对象。

官方调用说明：
https://learn.microsoft.com/en-us/windows/win32/api/winnetwk/nf-winnetwk-wnetuseconnectionw

下载脚本到：
C:\LAN_SHARE_REPORT\R9_DESKTOP_NATIVE_SMB_LOGIN_20261013\
核对字节SHA，再启动一次独立后台Python进程，让原生窗口能在本机前台显示。
使用本机实际Python解释器和正确路径引号；不往参数/环境/日志里放密码。
不要因工具等待用户UI而卡住Agent：脚本先写STATUS.json的LOCAL_WINDOWS_INPUT_PENDING，再等待原生UI。
最多启动一个进程，不并发弹两个框，不自动循环重试。
若窗口被后台遮挡，只说明切到Windows“网络凭据/登录”窗口；不要改为聊天收密或自制密码输入框。

## 本地用户输入与等待状态

窗口账号候选为SAM\ThinkPad；用户在原生窗口输入该笔记本账号的Windows密码（不是PIN）。
不猜测、不自动填空密码、不尝试其他账号、不重置密码、不建临时共享用户。
用户不知道密码或取消，就如实USER_ACTION_PENDING/USER_CANCELLED，不能改Guest/空密码策略来绕过。
只有用户自己在Windows原生UI选择的操作才处理其凭据；Agent不读取/截图密码字段，不上传密文/明文/密码长度。

窗口打开后，如尚未输入，先更新HUB回执为USER_LOCAL_INPUT_PENDING，明确：
“请在台式机Windows原生窗口填写SAM\ThinkPad来源账号密码；不要发到HUB/聊天。”
本任务继续等待本地输入，不为输入一个密码再要求新任务授权；不要反复重启登录进程。
原生函数失败/取消后记录WinError，不再自动尝试第二次。
如1219会话身份冲突，记录已知相关会话元数据；不清空所有SMB会话或删除用户凭据。

## 认证后只读核验与状态

STATUS.json由脚本写到：
C:\LAN_SHARE_REPORT\R9_DESKTOP_NATIVE_SMB_LOGIN_20261013\STATUS.json
记录用户名候选/返回码/根元数据；不含密码。
默认E/D源卷serial分别2387166462/3187598165，来源是SAM现场事实。
SOURCE_ROOT_METADATA_OK只证明两根metadata可读且来源卷匹配，不等于业务稳定读取、全计划无漂移或实盘验收。

认证成功且根metadata匹配后，使用已绑定计划取E/D各一个普通文件代表：
只读metadata HANDLE核验vol/FileId/size/mtime，不读payload、不hash业务文件、不扫描整树。
D必须通过\\192.168.100.2\D_DRIVE，仅读既有selected D路径，不使用桌面本地D。
不改/重hash6GB计划或9GB输入，不创建复制/链接试验。
把“认证成功、根metadata可读、代表metadata匹配”分别列出。
任何只读失败准确记录路径/阶段/WinError，不扩大自动重试。
SOURCE_ACCESS_VALID只有真实E/D只读核验成功才true；
SOURCE_LIVE_STABLE_FILE_READ_VALID仍NOT_RUN（无稳定业务读取试验）。
COPY_AUTHORIZED/FORMAT_DONE/FULL_MIGRATION一直false。

## 交付与调度

回传：
agents/chatgpt/inbox/R9_DESKTOP_NATIVE_SMB_LOGIN_20261013/
ZHANGWEI_REPORT.md、NATIVE_AUTH_STATUS.json、SOURCE_METADATA_PREFLIGHT.json、
使用脚本副本/FILE_SHA256.json（所有条目实际存在）。
窗口等待时先回传PENDING；完成/取消后在同一目录更新结果并更新INBOX_FOR_CHATGPT.md。
如密码输入是唯一阻塞，明确USER_LOCAL_INPUT_PENDING，不再交付一堆网络扫描TODO。
SAM保持待命，桌面不要自行发SAM改密码/共享任务。

本轮实际Windows调用范围只有原生网络认证与源只读metadata；
无业务复制/写入、无目标E盘试验。认证成功也仅等待ChatGPT下一阶段审核。
不格式化、不复制、不创建真实hardlink/junction，不改账号/密码/网络/MWB/P7或源数据。
用户本人未来手动格式化台式机E后才进入真实迁移试验。
执行电脑=ZHANGWEI；SAM=HOLD。有后续任务，本文件即桌面下一轮。
