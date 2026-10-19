# 保留原路径修复近32K访问，准备保留DONE的恢复链（不启动真实复制）

task_id: R9_DESKTOP_LONGPATH_ACCESS_AND_RESUME_PREP_20261019_1840
execution_host: ZHANGWEI
SAM: HOLD_UNLESS_TARGETED_SHARE_FACTS_NEEDED
status: READY
USER_FULL_MIGRATION_AUTHORIZATION=STILL_VALID
COPY_AUTHORIZED=false
FULL_MIGRATION=false

## 审核结论与纠正
已核对a92dec定位报告/实体/范围/state及方案：
33770是GBK日志误按UTF8替换解码的错数，撤回“33770源路径超过上限”的原结论。
失败实体2387166462|844424930324628，1166字节，唯一普通路径nlinks1，实际源API32765，目标32742；实测CreateFileW仍206。
另一个816字节文件源API32769，目标32746，无可用短别名。至少1982字节，不能声称仅2条受影响（原统计仅>32767漏了实际失败32765）。
dir DONE233668与上述文件不矛盾：目标目录短于文件UNC，且UNC前缀不同。
DONE实体1083975、logical_size之和348928107919，原1400run/state/code62aff均保留，剩余139792；旧state nonDONE0。
这些不是可忽略重复文件/损坏证据；不能跳过、截短、改名、删计划行、改源目录或放松最终extra/missing检查。

## 官方依据（开发时阅读原文）
https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation
32767是近似上限，前缀在运行时展开亦计入，不能以<=32767保证CreateFileW成功。
https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile
NtCreateFile支持OBJECT_ATTRIBUTES.RootDirectory相对目录句柄，FILE_OPEN_REPARSE_POINT可避免自动重解析。该接口存在不证明此SMB重定向器端到端可用，必须做本机真实只读验证。

## 先证明可访问，再做最小集成
1. ACK。现有进程已停止，不能重启旧失败命令。所有开发/测试/状态副本只在C；源E/D不写，真实目标E不新增文件/链接，也不删已有对象。

2. 优先检查是否已有能缩短路径的来源共享入口，不修改共享/主机/凭据/ACL：
   仅查已知来源分享事实（历史BLACKBOX share是否确指E:\BLACKBOX或其普通祖先）；如ZHANGWEI无现成事实，可经HUB给SAM一项只读指定共享name→path/卷核对任务，用户不负责跨机传话。
   若存在同一192.168.100.2的现成短共享入口且能直接验证同volume/file_id/size，可作为明确绑定的受限访问别名。不得凭字符串相似、另一个同名manifest或切换不明主机代替；不能临时建share或junction、substitute写源来凑短名。
   只有真实短入口验证成功才采用；否则不要循环试变体，进入目录句柄方式。
   无论入口如何缩短，原清单inventory、逻辑目标路径、entity_key保持不变；访问别名须写入新合同精确绑定并在same-handle身份校验中验证，不默许任意分享根。

3. 若无现成短入口可用，实现小而独立的句柄相对open助手在C开发副本：
   从批准来源E_DRIVE\BLACKBOX的短目录句柄起，对分量/有界分段逐层NtCreateFile(FILE_OPEN，仅只读，保留生产稳定读取FILE_SHARE_READ、禁止WRITE/DELETE共享)，不提交整条近32K UNC。
   中间每步校验directory/非reparse、来源卷和路径分量，禁止..、ADS、绝对替换、隐式跟reparse。前后句柄生命周期正确，所有句柄异常也关闭，记录原NTSTATUS及转换WinError，不能将失败当不存在。
   在ZHANGWEI对这两个真实源文件只读打开，核对计划volume/file_id/size，再在同句柄读完各1166/816字节做SHA与前后identity（原迁移授权内的必要小读取），证明真实字节可读。不要写C业务副本/伪造DONE，不把模拟成功称SMB成功。
   如果SMB RootDirectory访问不支持或遇权限/重定向器问题，输出确切NTSTATUS与失败阶段并停止此支路，不擅自装驱动/开服务/改策略。不要把用户拖进native参数判断；报告最小替代方案供ChatGPT决定。

4. 同步处理目标创建/回读/提交/观察/最终验收：
   当前目标final API32742/32746虽短于source，旧temp是dest+临时后缀，可能再次溢出。必须明确测最终path、temp真实生成方式、commit、hash、metadata观察与独立验收枚举的近限行为。
   优先最小改动：若最终路径API可用，选择同一父目录内长度有界且碰撞安全的新临时basename（独占create，不能简单在最长文件名后追加后缀）；保持原最终文件名不变、同卷、flush/回读SHA/no-replace提交不变。不能在未知冲突时覆盖/删除。
   如本地目标也需目录句柄相对操作，用同一助手实现必要最小路径，不改整个普通路径后端。源/目标路径仍锁定原批准root与卷/物理盘。默认普通路径保持原行为；近限/206走确定且可测试fallback，不能捕获所有OSError忽略重试。
   回读不递归调用同一fallback造成循环；完整验收的observe/content_sha/list_nofollow及reparse安全同样覆盖近限对象。未知对象、错误类型/身份、source changed、漏/多对象仍拒绝。

5. 测试与范围：
   本地C隔离夹具含真实UTF16近32K长目录/文件、中文和代理对（字符数≠UTF16）、复制temp后缀溢出、父目录/重解析/..拒绝、句柄关闭、错误NTSTATUS传播、正常短路径无变化。
   同一正式reader/backend/runner/独立验收集成验证超长普通文件复制并正常重跑copy0，不能只测helper。可在C新隔离目录使用相对句柄创建测试夹具；不在真实E做试验。
   在已有C计划上只筛选API UTF16>=32000的边界项（不重扫来源），列出source/final/temp/alias风险数量与阈值；不要仅修恰好两个文件名或只按>32767判断。
   不重复开发无关功能、不新造监控/复制引擎，沿已有生产链集成。

## 保留108万DONE的状态兼容恢复准备
6. 原full_1400.sqlite及run_bind绝不直接更改。复制状态须用SQLite一致性备份API到独立C文件/新run，保留WAL一致性；先证明进程停、记录原schema/原run/plan/code/volume和各kindphase行数/sum。
   备份/迁移脚本必须核实原plan53551d…、code62aff…、卷2694002743、目标roots与新计划相同，新代码只改变路径访问能力而不改变entity/dest/alias映射和内容规则。
   仅在备份上有事务地建立新run/code绑定与迁移来源记录，所有stage行不丢失、不重置；核对前后行数、实体key/dest/size/fileid/sha与聚合/确定性行摘要一致，若不一致拒绝。原state保留可回溯。
   本轮可实现并在小合成state验证迁移脚本；真实大state备份仅在有足够C空间且不会修改原state时准备，阶段标记不能变DONE。不要建空state忽略108万实体。
   注意旧runner恢复DONE会调用content_sha；所以“保留DONE不重拷”不等于“恢复完全不读已有字节”。禁止为提速无证据取消验证；本轮准备不要全量读348.9GB，后续正式恢复/最终验收的既有验证如实说明，不谎称零读取。

7. 更新完整模块列表与digest（新助手必须纳入CODE_FILES），准备绑定新run/newstate/同plan同目标卷的新合同，copy=false。精确提交patch、修改模块、全部hash、测试输出、真实两源只读能力证据、状态迁移脚本及小合成state结果、恢复合同/流程。
   正式E复制及实际恢复要等ChatGPT复核新代码/状态迁移证据后发令；用户原全量授权仍有效，无需再问用户是否继续迁移。

## 交付与停止
agents/chatgpt/inbox/R9_DESKTOP_LONGPATH_ACCESS_AND_RESUME_PREP_20261019/
ACK.md、ZHANGWEI_REPORT.md、REAL_SOURCE_CAPABILITY.json（明确短共享或relative handle、identity/SHA/原始NTSTATUS）、NEAR_LIMIT_BOUNDARY_SUMMARY.json、精确代码diff/完整CODE_HASHES、模块/测试、STATE_MIGRATION_PROPOSAL与脚本、新contract。
如能力验证失败，先交准确阻塞，不冒称IMPLEMENTATION_READY；不要继续大量写无效后端。成功则一次交齐最小集成和保留state方案。完成停止，保持真实源/目标和旧state原样。
