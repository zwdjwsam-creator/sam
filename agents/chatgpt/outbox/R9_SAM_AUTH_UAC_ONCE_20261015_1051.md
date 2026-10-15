# SAM｜现在发起一次正常UAC，读取既定历史日志

task_id: R9_NOTEBOOK_AUTH_WINDOW_ASSIST_20261015_1005
followup_id: R9_SAM_AUTH_UAC_ONCE_20261015_1051
execution_host: SAM
status: READY_AWAITING_AGENT_ACK
ZHANGWEI: HOLD
COPY_AUTHORIZED=false
FULL_MIGRATION=false
PILOT_WRITE_AUTHORIZED=false

已审核10:46:12报告：LOCAL_UAC_CONFIRMATION_REQUIRED，当前只是查明需要UAC，没有证据表明实际提示已发起。
ThinkPad启用且属于Administrators，但当前token为Medium；PasswordRequired=false不证明空密码，未获得LockedOut字段不能断言未锁定。
不再重复未提权查询、不再检查凭据、账户或扫描来源。

本轮具体动作：
1. 先ACK，然后将本指令随附固定脚本下载到C:\LAN_SHARE_REPORT\R9_SAM_AUTH_UAC_ONCE_20261015\query_auth_window_elevated.ps1。
   repo script: agents/chatgpt/outbox/R9_SAM_AUTH_UAC_ONCE_20261015/query_auth_window_elevated.ps1
   内容仅SAM主机、管理员上下文、指定历史窗口Security4625/SMBServer事件查询；只写C盘脱敏结果，不改任何系统设置。
   校验所下载blob为本轮发布的脚本，不从可变任意正文拼shell。脚本使用已限定窗口[02:19:30Z,02:19:33Z)且只筛ZHANGWEI/.1，解决旧脚本截止秒与任意admin匹配的问题。
2. 使用Windows正常ShellExecute/Start-Process -Verb RunAs，绝对路径系统Windows PowerShell，-NoProfile -File指向以上确切C脚本。只发起一次。父进程可不阻塞，记录本次发起时间、子PID（可得时）、等待UAC/取消/完成状态；不要弹多个提示。
   不使用管理员秘密、不安装服务/改计划任务、不绕过UAC、不要自动点击安全桌面的“是”、不关闭UAC、不修改ExecutionPolicy全局设置、不隐藏需要用户确认的提示。若脚本执行策略阻拦，准确报告，不擅自换成绕过策略。
3. 立即回报UAC_REQUESTED或确切启动错误。必须区分“已发起提示请求”和“用户已点是/管理员子进程已实际运行”。用户在笔记本正常UAC提示点“是”后，脚本只查原窗口，不制造新的网络登录。
   若用户取消或UAC不可交互，报告CANCELED/NOT_INTERACTIVE即停，不重试。不要声称提示必定已显示；以实际进程/状态为据。
4. 子进程结果写C:\LAN_SHARE_REPORT\R9_SAM_AUTH_UAC_ONCE_20261015\AUTH_UAC_QUERY_RESULT.json。现有HUB收件/Agent读取到结果后上传原任务目录，以新文件AUTH_UAC_QUERY_RESULT.json和SAM_AUTH_UAC_REPORT.md保留旧证据。
   不重新发认证、不改密码/账号/ACL/网络、不读业务payload、不写E/D。SOURCE_ACCESS_VALID仍false，不能因为日志读取成功改成true。
5. 回报status和可核验错误字段，若无事件如实说明，不自动扩窗/循环或新开诊断。最后由ChatGPT决定凭据恢复下一步。

本轮用户只需在真实Windows提示出现时点一次“是”。任务发布不等于已出现弹窗；请先交UAC_REQUESTED回执，避免用户等不存在的窗口。
