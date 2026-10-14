# 已通过基础实盘；准备链接、长路径与恢复的闭合小样本

task_id: R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014_1242
execution_host: ZHANGWEI
SAM: HOLD
status: READY
phase: CAPABILITY_PILOT_BUILD_NO_TARGET_WRITE

## 本轮审核结论
已读1232真实试验报告和REAL_PILOT_RESULT.json，重新计算40文件路径、2实体、9312唯一内容字节、269574逻辑路径字节、12288实体分配字节一致。2目标fileid不同，E的39条路径共一个实体；源SHA与1055只读抽样相同。
首次copy2/link38/acceptance true，正常重跑copy0/link0/acceptance true，已通过基础真实流式复制与硬链接试验。目录API次数未采集不冒报0，接受其说明。
1232授权首轮+重跑已消费完毕，不能再次用旧合同执行。保留旧样本目录/状态/报告，不删除、不移为正式数据。
未验证：真实junction、长路径映射、A/B/C恢复、全范围当前源一致性。IMPLEMENTATION_READY仍false，不全量。

## 下一组样本一次构建完整
1. C上扩展既有production_run/WindowsBackend限定试验入口，接真实junction、长路径与A/B/C故障恢复；保留全量copy拒绝。禁止通过将SIMULATED_CHAIN放到真后端来开闸。旧1232样本/状态不得改。
2. 从冻结正式计划及源只读元数据选择1个E junction、1个D junction（tag 0xA0000003），明确原始路径、source卷/身份、实际tag/substitute target、映射ID及目标重映射。选一个位于junction目标目录内、大小稳定的小普通实体，使样本可从目标junction打开并读到同一实体。可以保留原计划目录骨架和少量文件；只是小样本，不宣称复制整个release/整个junction目标树。无法取得合适D样本就明确实际阻塞，不猜target、不伪造“来自正式计划”的链接。
3. 选一个正式计划内源长路径（>260字符），及同实体的至少1 alias，保持中文/多级目录特征重映射，使目标路径也>260字符，每路径组件合法。别用p00扁平映射代替长路径试验。文件优先小实体，超过预算则换样本，不扫描整个payload。
4. 样本每个场景<=4实体、唯一内容<=1MiB、<=64文件路径、<=24普通目录、2junction；原样本关联不到这些特性可以换实体，但必须给正式计划来源、源身份和只读选取规则。C上交付可重建JSON/SQLite+生成器及冻结SHA、code digest和精确allowlist。
5. 为四个场景分别拟定独立根 E:\R9_CAPABILITY_PILOT_20261014\NORMAL、\A、\B、\C；每场景单独run与C状态，总唯一复制内容<=4MiB。本轮目录仅字符串/计划，不创建E目录。junction substitute target必须映射至同场景本地目标，不能指源UNC/笔记本或旧试验目录；实际打开取对象身份，no-follow验收link标签/目标，不递归follow计数膨胀。
6. NORMAL计划首次完成、正常重跑不改业务内容。A为实体临时内容校验/提交后、DONE持久化前；B为一部分硬链接完成剩余尚缺；C为alias已创建、DONE事务前。具体插入点以实际调用链为准，必须附阶段持久化证据。受控异常/进程退出后使用同一run恢复：A核对完整内容/身份后补状态不重抄，B仅补缺alias，C仅完成缺事务；源或目标身份/内容变化不得跳过。原A恢复状态若缺fileid/volume导致无法安全认领，要修复持久化顺序，不放宽验证。
7. 通过同一公开execute、Win32Syscalls注入OS数据/假kernel测试上述场景，包括真实junction创建代码需要的CreateDirectory+GENERIC_WRITE/OPEN_EXISTING/OPEN_REPARSE_POINT+FSCTL_SET_REPARSE_POINT、no-follow读取tag/target，不能在虚拟字典里直接标“junction”当真实调用验证。还要测试错误目标/历史卷/未知祖先/错链接目标/目标文件坏/缺状态均不误通过。正常验收需精确目录/文件/links覆盖、身份、SHA与AllocationSize去重。每实体只做必要hash，不遍历重复链接树。
8. 合法现场检查应拒绝非计划reparse祖先；计划内junction只在专门link创建/验收处按精确allowlist处理，不全局允许reparse。长路径调用使用已有extended path helper，不改系统注册表策略。
9. 改动必须是可运行入口+完整新合同结构（pilot_write_authorized=false），给明确真实命令以及四场景一轮运行/故障/恢复步骤。C上跑必要针对性隔离测试。无需重复无变化的大套测试，不重复重新登录/查密码/断IPC$。

## 交付与停点
agents/chatgpt/inbox/R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014/
ZHANGWEI_REPORT.md、CAPABILITY_SAMPLE.json/生成器、RUNBOOK.md、合同(false)、所有改动运行模块/依赖、测试与结果、FILE_SHA256.json。
报告分别列junction原始事实/目标闭合范围、longpath源/目标字符数、A/B/C实际故障点、恢复写入计数与持久化证据。未执行真API不声称实盘通过。
本轮只C开发/计划/隔离测试及必要源/目标只读元数据，不进行新E写入。交付HOLD_PENDING_CODE_REVIEW；代码样本审核后HUB再发真实四场景限定授权，不等用户再次格式化。
COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
FORMAT_DONE=true
IMPLEMENTATION_READY=false
执行电脑=ZHANGWEI；SAM=HOLD。更新INBOX_FOR_CHATGPT.md。
