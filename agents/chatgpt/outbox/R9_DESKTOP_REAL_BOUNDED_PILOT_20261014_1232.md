# 限定真实小样本试验｜执行电脑 ZHANGWEI

task_id: R9_DESKTOP_REAL_BOUNDED_PILOT_20261014_1232
execution_host: ZHANGWEI
SAM: HOLD
status: READY
PILOT_WRITE_AUTHORIZED: true
COPY_AUTHORIZED: false
FULL_MIGRATION: false

## 审核与限定授权
1147交付已审核全部20份文件的SHA，代码digest 906c28de2cbb0e78b62ccd1af2a6e8d83cff6da4639a759695858c2dfe2c9cca 独立计算一致，样本SHA a0330b0115e2cd603c792807266633cdf7206a82d98d53d1afb0d7a52ce361c3 一致。
独立重跑9项限定入口测试：两实体复制、38硬链接、独立验收、正常重跑、错内容/大小等拒绝均通过。本审核运行于Linux，以禁止真实API的DLL替身及仅C状态路径校验的便携适配运行；没有在用户Windows机器执行。50项总测试是本机回报，不能声称ChatGPT重跑了50项。
用户已亲自格式化目标E并要求继续，本轮明确授权一次初始真实样本运行及一次正常重跑，授权不包括全量或1GiB。
批准合同：agents/chatgpt/outbox/R9_DESKTOP_REAL_BOUNDED_PILOT_20261014_1232/PILOT_EXECUTION_CONTRACT.json。用此新合同，不修改随包旧false/旧digest合同，不自行扩展样本。
唯一写入根 E:\R9_POSTFORMAT_PILOT_20261014；允许3目录、e\p00..p38、d\p00共40普通路径，2唯一内容共9312字节，38个同卷硬链接。生产实体复制的2个 .partial 临时文件仅允许在对应代表路径旁，完成后移除/提交。junction=0。不得写 E:\BLACKBOX 或其他目标目录。

## 执行顺序
1. 保持已有 zhangwei\admin 未提升上下文/SMB会话，不登录/查密码/断IPC$。核对本机代码来自已审核1147包、code digest=906c28de2cbb0e78b62ccd1af2a6e8d83cff6da4639a759695858c2dfe2c9cca，样本SHA=a0330b0115e2cd603c792807266633cdf7206a82d98d53d1afb0d7a52ce361c3，不在运行前修改模块。任何不匹配立即STOP并回报，不能补丁后直接执行。
2. 实时重查物理盘UniqueId eui.E8238FA6BF530001001B448B42E694AE、新卷D86AEE82（3630886530）、NTFS、许可祖先无重解析；保留正式入口的现场检查。物理容量4000787030016与E卷4000769372160分别记录。目标试验根在初始运行前必须不存在；C默认状态 C:\LAN_SHARE_REPORT\R9_DESKTOP_CLOSE_REAL_BACKEND_AND_VERIFY_CONTENT_20261014\state\pilot.sqlite 必须没有既存运行状态（初始不存在）。若出现旧试验目录/状态，不删除、不覆盖、STOP报告。
3. 把本任务合同保存到 C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_BOUNDED_PILOT_20261014\PILOT_EXECUTION_CONTRACT.json，run_id必须为本任务id。来源样本使用已审核的 C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014\PILOT_SAMPLE_FILES.json。C上保存日志与只读证据，不回传业务内容。
4. 在 C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013 先运行：
   python -m r9_bounded_pilot dry-run --sample C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_RUNNABLE_BOUNDED_PILOT_20261014\PILOT_SAMPLE_FILES.json --contract C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_BOUNDED_PILOT_20261014\PILOT_EXECUTION_CONTRACT.json
   必须合法合同匹配、样本计数正确、目标写入0，然后运行一次同参数 execute（把dry-run换成execute），保持真实 WindowsBackend/Win32Syscalls，不注入假后端/假OS，不调用旧全量入口。
5. 成功必须copied_count=2、linked_count=38、acceptance=true、content_hash_calls=2，观察40文件路径、2个唯一目标fileid、38alias与对应实体同卷同fileid。记录2实体实际AllocationSize与合计、逻辑路径269574字节、唯一内容9312字节；按4096簇预计合计12288仅估计，实测为准，不用全盘空闲差当实体占用。
6. 首轮通过后，用同一合同/run/state执行一次正常重跑。必须copied_count=0、linked_count=0、独立验收true；没有业务内容重写、没有新alias/临时业务文件。区分已有目录的CreateDirectoryW尝试与实际文件写入；现有计数器会计入目录API调用，不可把它伪报为0，应报告真实API次数和实际业务改写结果。
7. 首轮或重跑有任何错误/验收false立即停止，保存现场，不自动删目录/状态、重置run、覆盖目标或循环重试；不能把写入后RuntimeError都报告成“首次写入前拒绝”，给出实际计数/日志/失败阶段。需要改码回HUB另审。
8. 完成进入 HOLD_PENDING_REAL_IO_REVIEW，不继续扩容/重解析/中断测试/全量迁移。即使本轮通过，IMPLEMENTATION_READY仍false（junction、全范围与其他实盘能力未核验）。

## 回执
agents/chatgpt/inbox/R9_DESKTOP_REAL_BOUNDED_PILOT_20261014/
ZHANGWEI_REPORT.md、两次运行日志、REAL_PILOT_RESULT.json（API调用、复制/链接/跳过计数、源稳定观察、每唯一目标SHA/身份/大小/AllocationSize、完整路径验收）、新目标绑定与本轮合同hash。
可以上传状态库的脱敏结构化摘要，不上传payload。如模块变化则本授权失效，不用新digest自行替换合同。
FORMAT_DONE=true（用户回报且已核验新卷，本次执行前仍重查）
PILOT_WRITE_AUTHORIZED=true（仅此任务范围；两次完成或失败即停止）
COPY_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
执行电脑=ZHANGWEI；SAM=HOLD。更新INBOX_FOR_CHATGPT.md。
