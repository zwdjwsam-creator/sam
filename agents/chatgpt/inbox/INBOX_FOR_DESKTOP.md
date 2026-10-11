# 给台式机 AI（ZHANGWEI）｜结束已识别的挂起日志查询，再做单次1GiB实测

任务ID：R9_DESKTOP_FINISH_STALE_QUERY_20261011_1227
取代：R9_DESKTOP_AUTHORIZED_VISIBILITY_20261011_1220（诊断完成，不重复）
执行方：台式机 Cursor。笔记本 SAM 待命。
状态：待执行。

## 审核依据与本轮授权

ChatGPT已读取管理员进程原始JSON和管理员预检：
- cmd PID20440，StartTime=2026-10-10T17:33:54.7809759+08:00，
  Windows system32 cmd.exe，Owner=ZHANGWEI\Admin，父PID3348（sshd）。
- findstr PID34324，StartTime=2026-10-10T17:33:54.8014005+08:00，
  父PID20440，Windows system32 findstr.exe，Owner=ZHANGWEI\Admin。
- 命令行为 findstr 查询
  C:\LAN_SHARE_REPORT\BLACKBOX_MIGRATION_RUN_20261010_173201_R8_3B85D677\DESKTOP_PREFLIGHT.json，
  含DESKTOP_READY/RUN_ID，现有引号异常可能使其等待输入；不能把“实际已读完文件”当事实。
- 这是挂起的旧日志查询，不是ln复制/wrapper/watchdog；现有门禁因RUN_ID匹配拦截。
本轮在重新核对身份后，允许结束这一个废弃日志查询及其cmd外壳。不是全局进程清理授权。
先前仅只读的任务已完成；本任务明确新增上述限定停止动作，不允许绕过Windows权限或把旧只读UAC当作本次停止批准。

## 1. 定点结束：先子后父，保留证据

1. 在C盘保存一个小型、可审阅的处理脚本，脚本名用 R9_FINISH_STALE_QUERY.ps1，不把旧RUN_ID放入启动命令行，避免当前预检把本次工具误认作R8。
2. 若停止操作需要提升，通过正常Windows UAC请求用户批准：
   “结束已确认挂起的旧findstr日志查询及其cmd外壳，不停止SSH服务，不删除文件。”
   不静默提升、不自动点UAC、不使用凭证/SYSTEM任务绕过限制。
3. 在执行停止的同一上下文，重新读取并核对：
   PID、精确创建时间、可执行路径、Owner、父子关系及完整命令行，
   与 R9_ZHANGWEI_ADMIN_PROCESS_DETAIL.json 一致。
   PID已不存在则记录已退出；PID复用、身份不同、出现额外业务子进程则停止该动作并报告，不沿用历史PID盲杀。
4. 仅对身份匹配的findstr PID34324定点停止。短暂等待cmd自然退出（最多数秒）。
   若cmd PID20440仍在，再次核对其同一身份及子进程状态；确认仍是同一个旧 /c findstr 外壳才定点停止它。
5. 不使用 /T 扩大进程树停止；不按进程名批量杀。
   不主动终止sshd PID3348/28700/5892或其他SSH/Cursor/PowerShell，
   不主动终止conhost，允许其随旧外壳自行退出。
6. 保存停止前快照、执行动作、退出码/错误与停止后复核。不要删除原日志、源文件或实验目录。
   如需用户批准而未获批准：WAITING_FOR_LOCAL_UAC，结束本轮等待，不反复弹窗。

## 2. 普通本地会话重跑原预检

停止脚本退出后，从台式机普通本地Cursor会话执行原 --preflight-only，
不带复制开关，不设置skip，不修改门禁代码。
检查旧RUN_ID命中/ln/监控残留，记录真实结果。
若仍失败，报告具体新阻塞；不得继续扩大停止范围或改成白名单。
若只有管理员会话可以预检通过，本次停止UAC不自动授权管理员复制；回报上下文差异。

## 3. 普通上下文原预检通过后，接续单次1GiB实测

此前已授权的普通上下文单次隔离实验继续有效，不需要重复向ChatGPT申请同一阶段。
执行前简短核对：
- ZHANGWEI；E NTFS serial806508DF；
  Volume GUID b8545ee8-e403-48c6-9d3f-09afd3e0349f。
- 固定目标 E:\BLACKBOX_MANIFEST_PILOT_R9_1G 不存在且路径检查通过。
- 三份PY为HUB FIX2b，记录文件哈希，不修改逻辑。
- 清单SHA=cfb831ecc0a85fec0137b74a12162e169828d708ff57961df906deffb185c041。
- 662实体 / 22998路径 / 1064950668唯一字节，上限1073741824。
- 源仅 \\192.168.100.2\E_DRIVE\BLACKBOX；真实旧停止报告及当前进程预检通过。

不重复已完成的662实体UNC全文探测。
运行copy_executor_r9_1g.py，带现有 --enable-copy --i-accept-pilot-copy、
固定 --confirm-dest、本机真实 --r8-stopped-evidence，不带limit。
代码内实时源卷/文件ID/大小/mtime/稳定句柄检查全部保留。
COPY_OK后，使用本次copy-record运行完整acceptance，不用结构或局部模式。

任何失败立即停止，保留现场，不自动重试、不覆盖、不清理；全量迁移、重扫E/D、网络调整、格式化均禁止。

## 4. HUB交付

提交 R9_ZHANGWEI_STALE_QUERY_STOP_AND_PILOT_REPORT.md 到原R9包。
包含：
- 精确停止身份、动作和结果；SSH服务/其他会话未被主动停止。
- 普通上下文预检。
- COPY_STARTED / COPY_OK / ACCEPTANCE_PASS / FULL_MIGRATION=FALSE。
- 若完成复制：本次copy-record、复制日志、完整验收JSON，内容与链接检查计数、
  唯一内容字节、实际分配空间、卷空闲差、耗时。
更新INBOX_FOR_CHATGPT.md指向新报告。
未执行项明确NOT_RUN，上传成功不等于复制成功。

本轮新增管理员诊断证据有保留价值，不删除。
之前清理的3个重复测试输出无需重传。
