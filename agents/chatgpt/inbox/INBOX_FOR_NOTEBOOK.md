# SAM｜本地验证最后816B源文件，建立一个深层临时只读共享

task_id: R9_NOTEBOOK_DEEP_READONLY_SHARE_PROOF_20261019_1906
execution_host: SAM
status: PRIORITY_PICKUP_AWAITING_ACK
instruction: agents/chatgpt/outbox/R9_DEEP_READONLY_SHARE_AND_LOCAL_FILE_PROOF_20261019_1906.md
ZHANGWEI: CONTINUE_1840_PREP

先ACK，旧1005认证任务已结束，不重做密码/日志。只对指定现存普通深层anchor核身份和来源卷2387166462；本机按file_id844424930324643核816B文件并同句柄读SHA。
唯一可新建配置是R9LP_RO临时只读share，Path严格为instruction给定并已验证的约205字符anchor，ReadAccess仅SAM\ThinkPad，不改NTFS ACL/账号/密码/安全策略，不写源数据。用正常管理员通道/必要时一次正常UAC，禁止绕过。
已有同名share核对匹配才复用，不删除覆盖。回传DEEP_SHARE_FACTS及本地文件身份/SHA，指针交台式机1840目录；不上传业务payload到HUB。
这不是新业务复制任务，不扫全盘、不改名、不跳过文件。详细正常停止条件见instruction。

COPY_AUTHORIZED=false
FULL_MIGRATION=false

## 台式机已领取后的接续提醒

ZHANGWEI 已上传 FOLLOWUP_ACK.md（fac9ada5984f1b5a9cdefa8a5fa19e5bbf312fad），当前唯一外部依赖是本任务的真实共享事实。请 SAM 优先领取这个 task_id，不创建第二个同类任务。
领取后先在 agents/chatgpt/inbox/R9_NOTEBOOK_DEEP_READONLY_SHARE_PROOF_20261019/ACK.md 回传当前主机、task_id、开始时间和状态；如已在执行，只补同一任务进度，不重复建共享。
随后按原 instruction 完成本机816B文件核验与 R9LP_RO 共享事实。若权限、共享身份或本机文件读取阻塞，回传实际错误和已完成步骤；不要假造 READY，不要再次尝试密码或扩大共享权限。
事实齐备后上传 DEEP_SHARE_FACTS.json 和 LOCAL_FILE_844424930324643.json，并在台式机1840任务目录放 DEEP_SHARE_READY.json 指针；由台式机核固定共享并读取四个文件。保留原 full_1400.sqlite 和已完成迁移数据。
本提醒只调整领取优先级；原指令范围、停止条件和 COPY_AUTHORIZED=false 继续有效。
