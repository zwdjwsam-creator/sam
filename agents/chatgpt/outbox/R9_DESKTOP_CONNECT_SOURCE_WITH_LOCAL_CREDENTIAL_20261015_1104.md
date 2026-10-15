# ZHANGWEI｜用户本地提供密码，连接正确来源账号并验证读取

task_id: R9_DESKTOP_CONNECT_SOURCE_WITH_LOCAL_CREDENTIAL_20261015_1104
execution_host: ZHANGWEI
SAM: HOLD
status: READY
VERSION_CHOICE=AS_IS_MIGRATE_MARKED
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false

## 用户最新授权
用户：“已经在台式机开通密码，密码我会给到本地AI，你直接编辑任务就行”。
这明确允许台式机本地AI使用用户本地提供的来源登录凭据，或由用户在Windows原生窗口输入，建立迁移来源SMB认证。替代此前WAITING_SOURCE_CREDENTIAL_DECISION和“不弹输入窗口”的等待。
不需要用户再向ChatGPT复述密码或同意这一认证。密码不允许进入GitHub/HUB/报告/日志/源码/命令行/环境变量；只在本机安全输入或API内存中短暂使用，不记录密码长度/哈希。不要要求用户将密码发送到HUB。

## 准确对象
执行电脑：台式机ZHANGWEI。
来源服务器：笔记本SAM，192.168.100.2。
已确认来源本地账户：SAM\ThinkPad。
台式机的ZHANGWEI\Admin不作为来源账户。原事件0064证明默认用了错误来源账户，不能默认继续使用当前登录用户名。
用户“台式机开通密码”的文字不等于来源密码已确认；在本地接收凭据时核对它属于SAM\ThinkPad。若用户提供的是ZHANGWEI\Admin密码，只说明对应关系并等待正确来源凭据，不能拿它猜.2。不擅自改任何账号密码。

## 执行
1. 先ACK。检查用户是否已在本机成功连接.2；若已成功，复用现有会话直接验证，不强制重复密码输入。否则使用用户在本地明确提供的SAM\ThinkPad凭据，通过正常Windows网络API连接\\192.168.100.2\E_DRIVE；也可使用Windows原生本地凭据窗口，预填SAM\ThinkPad，由用户本机输入。用户尚未提供则立即报WAITING_LOCAL_CREDENTIAL，不重复诊断/搜凭据。
2. 尽量在正式迁移会使用的相同普通用户/提权/登录会话上下文执行，记录上下文不含秘密。可参考原已审核r9_native_smb_login.py的Windows拥有UI方式，但新任务用独立C状态路径，不自动复跑旧2137脚本/旧状态。通过程序API内存传凭据，不拼net use带密码的shell命令、不输出工具完整输入。默认不长期保存新密码；如用户已自行保存可正常复用。
3. 新凭据只尝试一次。若用户在本机明确纠正了密码，可再做一次纠正后尝试；不猜密码/空密码/变体、不循环。遇1219列出.2确切冲突连接及活跃状态，不能net use * /delete或全局删凭据。认证失败回报准确错误码及使用的账号（无秘密），停止，不自动重置密码、建账号、改ACL/Guest/策略/网络。
4. 连接后分别只读验证：
   - \\192.168.100.2\E_DRIVE\BLACKBOX：来源卷2387166462。
   - \\192.168.100.2\D_DRIVE：来源卷3187598165。
   - 在已冻结53551d…候选内，E和D各选一个普通文件（不是目录/重解析、尽量避活动邮箱），通过生产open_source_stable的long-path只读句柄查询身份、大小、类型并对照候选，然后关闭。不得读业务payload。E通过不代替D，根通过不代替文件稳定读取，普通Explorer可读不代替同一生产上下文。
   - 有界只读核对到.2的实际路由/网卡，记录是否直连2.5Gbps，不改路由/网卡/Wi-Fi、不测速、不复制。
5. 所有E/D项通过才SOURCE_ACCESS_VALID=true；失败分项如实记录。认证与来源只读成功不等于迁移完成/全量授权，COPY_AUTHORIZED仍false。
6. 成功后交付可供下一轮直接审阅的现有最终合同/路径/来源验证摘要：候选SHA=53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d，代码digest=310778b936d44a5307f57f1c775925dd700c87749e8a8bba27bf097ee3517ff5，目标E卷3630886530、disk eui.E8238FA6BF530001001B448B42E694AE。只读核对现有本机绑定，若已变报告实际值，不重建6GB，不静默改代码/候选，不将真实执行合同的copy位改true。已有完整静态核查不重复运行，除非绑定确实变化。
7. 不重复来源全盘扫描、日志排查、52/140/42核查、BENCH试验，不格式化、不写目标E、不复制业务文件、不创建junction/硬链接。本轮只C盘脱敏准备与HUB及正常认证会话。SAM待命，不另发笔记本任务。

## 回传
agents/chatgpt/inbox/R9_DESKTOP_CONNECT_SOURCE_WITH_LOCAL_CREDENTIAL_20261015/
ACK.md、ZHANGWEI_REPORT.md、SOURCE_AUTH_AND_READ_RESULT.json、可用最终合同引用及摘要。
字段：当前上下文、账户、auth_status、attempt_count、E/D根与各自文件的独立结果/卷/身份/大小、SOURCE_ACCESS_VALID、路由事实、copy未运行。
WAITING_LOCAL_CREDENTIAL/拒绝/成功分别准确说明；不要只因任务领取报认证成功。更新INBOX_FOR_CHATGPT，完成停止待审，不自动启动正式复制。
