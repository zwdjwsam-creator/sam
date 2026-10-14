# 格式化后目标绑定与小规模实盘试验计划

task_id: R9_DESKTOP_POSTFORMAT_BIND_AND_PILOT_PLAN_20261014_1109
execution_host: ZHANGWEI
SAM: HOLD
status: READY
FORMAT_DONE: USER_REPORTED_TRUE
COPY_AUTHORIZED: false
FULL_MIGRATION: false
IMPLEMENTATION_READY: false

用户于 2026-10-14 11:09 +08 明确回报台式机 E 已格式化。本轮接续准备工作，确认新目标身份并给出具体可审查试验方案，不再次格式化、不自动复制。

1. 只读检查本机 E: -> 卷 -> 分区 -> 物理磁盘对应关系。预期物理盘 UniqueId=eui.E8238FA6BF530001001B448B42E694AE，物理容量=4000769372160 字节。提供磁盘编号、UniqueId、分区标识/偏移/大小、新卷 GUID/serial、文件系统、簇大小、卷容量/空闲空间、状态。磁盘容量与卷容量要分开。UniqueId 或物理盘不匹配立即 BLOCKED，不靠 E 字母/标签/历史 serial 判定正确。
2. 只读列出 E 根一级目录/文件（含隐藏系统项），不递归扫全树、不删除。系统目录不当成未格式化；出现既存业务目录则报告，不清理。用户格式化回报与本机新卷身份核验分开记录。历史目标 serial/GUID 不复用为新授权。
3. 保持已验证 zhangwei\admin 未提升上下文和现有来源 SMB 会话；只读重查 E/D 来源根身份，预期 serial 2387166462/3187598165。不登录、不查密码、不断 IPC$。若查询磁盘元数据需要提升，仅单独提升诊断；另一个上下文的来源可读不能代替执行器上下文。
4. 检查 C 上现有执行器/依赖/冻结计划仍在；计划 SHA 94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba 的绑定沿用有效冻结证据，注明证据来源，不必要时不重复完整哈希。读取现有生产入口，给出准确入口命令、参数及必须填写的新目标身份。不要运行写入命令。
5. 在 C 生成新 POSTFORMAT_TARGET_BINDING.json；该文件是观测事实，不是复制授权。不得替换旧冻结计划或偷偷将 FORMAT_DONE/COPY_AUTHORIZED 开关置真以运行生产链。
6. 给出下一阶段一轮可完成的小规模实盘方案，优先采用最小生产计划验证真实流式复制、目录、同卷硬链接 alias、计划内 junction、验收及一次正常重跑不重写。拟选现有正式计划内稳定普通实体，包含 E/D 两个已验证小文件；上限 16 个唯一实体、合计 16 MiB、总路径不超过 64。链接须来自正式计划且目标在同一试验范围内，以试验目标本地路径重映射，不能指回笔记本或覆盖正式业务目录；选择无法闭合则明确不纳入/阻塞，不伪造正式计划链接。
7. 拟定全新隔离目标目录 E:\R9_POSTFORMAT_PILOT_20261014，明确普通文件/实体/alias/目录/链接数量、源到目标映射、预计 unique/logical/allocated 空间、测试内容和验收条件。只在 C 生成方案与样本计划，本轮不要创建 E 试验目录，不复制。样本与正式冻结计划 SHA/选取规则绑定；不得修改原计划。若组件仍缺生产能力，说明具体缺口，不能用只读探针当生产组件通过。
8. 交付后 HOLD_PENDING_REVIEW，等待 HUB 审核后另发明确限定范围的真实试验指令。不得自行升级 1GiB 或全量迁移。目标变更应使旧运行状态与授权失效；不得复用旧目标 DONE。

交付目录 agents/chatgpt/inbox/R9_DESKTOP_POSTFORMAT_BIND_AND_PILOT_PLAN_20261014/
ZHANGWEI_REPORT.md、POSTFORMAT_TARGET_BINDING.json、PILOT_PLAN.md、样本计划摘要/哈希及引用。
源不改，E 本轮无写入，C 允许代码/样本计划/诊断证据。
FORMAT_DONE=USER_REPORTED_TRUE（本机目标核验另记 TARGET_POSTFORMAT_VERIFIED）
COPY_AUTHORIZED=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true
执行电脑=ZHANGWEI；SAM=HOLD。更新 INBOX_FOR_CHATGPT.md。
