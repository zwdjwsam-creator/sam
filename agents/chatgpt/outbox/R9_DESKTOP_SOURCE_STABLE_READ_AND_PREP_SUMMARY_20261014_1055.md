# 来源稳定只读核验与准备摘要

task_id: R9_DESKTOP_SOURCE_STABLE_READ_AND_PREP_SUMMARY_20261014_1055
execution_host: ZHANGWEI
SAM: HOLD
status: READY

## 已审核
1041 回执及 SESSION_SOURCE_PREFLIGHT.json：当前未提升的 zhangwei\admin 上下文，E/D 根卷分别 2387166462、3187598165，两普通文件元数据可读，认证尝试 0，IPC$ 未断开。该证据证明当前元数据可读，不证明文件内容可读、全范围稳定或迁移实现已可实盘。

## 本轮一次完成
1. 保持同一未提升上下文和已有 SMB 会话，不再登录、查密码、断开 IPC$ 或改网络。执行器若实际需要另一上下文，只记录差异；不得将当前通过套用到另一上下文。
2. 使用上一轮 JSON 的两个普通文件（E 6849 字节、D 2463 字节）与对应正式计划记录。先只读打开冻结计划，核对 SHA256=94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba，冻结状态及无非空 WAL；使用已有实现，避免无必要重写代码或重复整套测试。计划路径 C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite。如果已有精确同一文件冻结证据仍有效，可复用并注明，不能用计数代替 SHA 绑定。不执行 checkpoint 或其他改变计划的操作。
3. 本轮授权只读这两个小文件的内容并在内存计算 SHA256，不保存 payload，不创建目标/临时业务副本。优先使用正式实现已有的来源流式读取/稳定核验组件；禁止调用会创建目标文件的复制主体或绕过准备闸门。若读取组件不能独立安全使用，采用只读探针，并明确“探针通过，生产读取组件尚未核验”，不要伪称生产链通过。
4. 每个文件使用只读句柄取得读取前/后 volume、file id、size、mtime 与普通文件类型，完整读取至 EOF；独立再次只读打开并读取，比较两次 SHA256、字节数及前后身份/大小/mtime。检查对冻结计划的身份/大小/mtime 绑定一致性；差异单独报告，不修改源或计划。缺字段不能当通过。两次相同只证明这两个文件在本次观察期间稳定；若计划无历史内容哈希，不能声称与历史内容哈希一致。
5. 全部业务读取总量仅两个文件各两遍，预计 18624 字节；不扩展样本、不重扫、不读取链接目标、不做 1GiB 试验。通过则 SOURCE_LIVE_STABLE_FILE_READ_VALID=true，并附 scope=TWO_REPRESENTATIVE_FILES_ONLY。单项失败为 false 或 BLOCKED，准确写错误和失败阶段，不循环重试。
6. 用现有证据汇总准备摘要：冻结计划/code digest 对应包、模拟链测试已有结果、SOURCE_METADATA 与本轮两文件稳定读取结果、尚待实盘验证项、当前执行上下文。列清“已核验”和“未核验”，不把 41 项模拟测试等同实盘通过，不把抽样等同完整源覆盖。D_GLOBAL_COVERAGE_PROVEN 仍未证明；全选定范围实时一致性和目标格式化后绑定也未证明。
7. 本轮完成后进入 HOLD_PENDING_REVIEW，不自动继续真实写入/迁移。如果仅只读成功，不修改 IMPLEMENTATION_READY=false。报告现有读组件/实现是否仍有具体阻塞，不凭空宣布全部准备完成。

## 硬边界
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true
不格式化、不复制、不在目标 E 写入、不做实盘硬链接/junction/复制试验。用户将来亲自格式化目标盘后才能另行安排真实写入试验；本轮仅来源小文件只读与 C 上脱敏证据文件。
不得向 HUB 上传业务内容、密码或凭据；文件内容哈希可作为本轮核验结果，不属于凭据哈希。

## 交付
agents/chatgpt/inbox/R9_DESKTOP_SOURCE_STABLE_READ_AND_PREP_SUMMARY_20261014/
- ZHANGWEI_REPORT.md
- SOURCE_STABLE_READ.json：两文件计划绑定、每次读取前后元数据、SHA256、读字节数、错误及上下文，不含 payload。
- PREPARATION_SUMMARY.md：已有代码/冻结计划绑定、证据引用、现有模拟验证结果、未完成项与明确停止状态。
提交探针/调用脚本以供审核；仅发现实际问题才做必要修复及针对性验证，不能改变写入授权。
更新 INBOX_FOR_CHATGPT.md。执行电脑=ZHANGWEI；SAM=HOLD。
