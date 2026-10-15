# 认证原因已定位｜停止诊断，等待来源账号的有效认证方式

review_id: R9_AUTH_USERNAME_CONFIRMED_20261015_1102
SAM: COMPLETE_REVIEWED_HOLD
ZHANGWEI: HOLD_PENDING_SOURCE_CREDENTIAL_DECISION
COPY_AUTHORIZED=false
FULL_MIGRATION=false
PILOT_WRITE_AUTHORIZED=false
SOURCE_ACCESS_VALID=false

## 已审核证据
SAM正常UAC后已运行固定脚本，10:56:41+08 elevated=true，身份SAM\ThinkPad。
原窗口唯一匹配Security4625：
2026-10-15T10:19:30.5609148+08
TargetDomain=ZHANGWEI，TargetUser=Admin，Workstation=ZHANGWEI，SourceIP=192.168.100.1，LogonType=3。
Status=0xC000006D，SubStatus=0xC0000064。
Microsoft官方4625文档定义0064为用户名不存在/错误账户，006A才是密码错误：
https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4625

结论边界：本次默认身份ZHANGWEI\Admin在来源端认证失败，不是“已证实SAM\ThinkPad密码错误”。SAM\ThinkPad是来源已确认存在且启用的本地账户。正确账号尚未完成成功认证；不能只改字符串便声称解决，不能把台式机Admin密码或SAM保存的.1/admin凭据套给ThinkPad。
两侧已查当前上下文没有可复用的.2/SAM来源凭据。ThinkPad密码最后设置时间只证明设置事实，不给出密码值。Windows PIN/已登录状态不能冒充可用SMB账号密码。
不再追加事件查询、凭据遍历、来源扫描或试空密码/变体。

## 下一步已准备的最小方式（尚未启动交互）
若用户记得SAM\ThinkPad现有密码，可在台式机Windows原生凭据窗口本地输入一次，明确账户SAM\ThinkPad、目标\\192.168.100.2\E_DRIVE。
可复用已审核旧r9_native_smb_login.py的Windows拥有UI方式（不获取密码缓冲、不写秘密），但为新任务独立C状态路径，不自动重放旧2137任务。旧代码只验根，不替代恢复后生产同上下文E/D各一个正式文件稳定句柄元数据验证。
由于用户之前明确要求不再手输，本轮只准备/等待其选择，不擅自重新弹密码窗口。
若用户不记得现有密码，当前无可自动复用凭据；需要单独明确选择账户恢复/专用迁移账号等方案后再改动，不能重置现有ThinkPad密码、建账号或降级安全策略。保留现有配置/代码/候选。
不向聊天/HUB索要或发送密码。

## 邮箱结束状态
SAM1005及1040/1051只读核查完成，SAM停止；不因HUB查询重新弹UAC。
ZHANGWEI保持等待账号认证方式；没有新登录尝试、没有复制授权。
下一次用户明确选定后再发布一次准确任务，不无限诊断。
