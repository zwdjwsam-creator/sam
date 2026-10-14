# ZHANGWEI｜只在C准备目标链接修复候选计划，保留全部来源

task_id: R9_DESKTOP_PREP_DESTINATION_LINK_REPAIR_PLAN_20261014_2212
execution_host: ZHANGWEI
SAM: HOLD
status: READY
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

## 2157 审核通过，问题已收敛

10份上传文本SHA已独立核对；离线解析测试6/6通过。全量解析记录2,881,815字节留C，本审查连接器未直接读取，需本轮现场核对SHA03318d69ce1db041b34c314e3c2b8244df6fa92efe8341916e7162386c45ef82。
分类4825=目录终点4824+文件终点1；无missing/cycle/escape/resource_limit。1007条超过32步仍到目录，数学闭合不等于Windows都可跟随。64步BILLBOARD代表来源跟随WinError1921；唯一文件终点的junction跟随WinError267。两次只读代表探针不是全部1007条的现场测量。
原计划94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba与生产摘要a1ce1ae5e2d0490d6b6c415917200f7c84bb502d9befb397a38fe974e43e5bfd均不改。
不再追加测速。下面授权的是C盘候选计划/隔离验证，任何业务目标写入仍未授权。

## 目标修复原则

保留源链接和源文件，也保留原冻结计划、旧试验、原始解析和异常证据。
仅设计目标侧修复：当前数据的终点不变、普通数据实体不增、不重复制同一release；保持链接路径与对外查询路径尽量不变。动态发布入口不能被无说明地固定到旧release。

### 1. 历史目录链缩短到同一普通目录

读取全部4824个CLOSED_DIRECTORY记录；核对link/terminal与真实计划映射和终点普通目录身份/路径依据一致。
对历史版本release内部目录链接，准备迁移目标直接指向其已解析出的同一计划内普通目录（用终点消除多层重解析），不创建数据副本，不删除对外目录名。
优先在有版本号/ASOF/时间戳的历史release节点缩短；CURRENT/LATEST/活动发布头等动态入口保留原间接关系，再检查所指历史节点缩短后路径是否短且闭合。记录静态/动态判断依据，不能仅凭CURRENT字样决定整个对象类型。
任何动态角色不明的节点，保留原边并单列，不为了把跳数变小就改变后续发布更新语义。
输出 DEST_DIRECTORY_LINK_OVERLAY.json，逐项包括原源链接/原target、目标link、原migrated_target、拟用普通目录终点、原解析链长度、修复依据与动态语义说明。所有新目标必须在E:\BLACKBOX/E:\BLACKBOX_ENGINES，不能指UNC/源D:/旧F:/试验根。
重新解析拟迁移目标图，统计最大长度/长链残余/循环与缺失；这是候选图证明，不冒充Windows实盘成功。若仍有无法保证的动态长链，列具体最小缺口，不自动扩范围/改源。

### 2. 单个失效JSON指针规划为文件硬链接

原目录型junction（来源保留）：
E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_ADJFACTOR_PIT_CLEAN_ASOF_20260814_20260816_044000\CURRENT_POINTER_COPY.json
实际终点普通文件：
E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_ADJFACTOR_PIT_ASOF_20260814_20260816_034243\CURRENT_POINTER_COPY.json

先从原计划核对终点确是已纳入普通文件，取得真实卷/file id/大小/父实体和已有别名。准备“目标同名路径=终点已复制实体的硬链接”的精确转换记录，使用现有hardlink/alias方法。这样恢复文件访问，不继续创建指向文件的目录junction，不复制额外内容、不使用需新权限的文件symlink。
仅此一个精确路径。记录原目录型重解析元数据、WinError267、转换理由，不能称源已修好，也不能把修复后的文件类型当成原源现场事实。
如终点未入计划/身份不明/别名数已不支持追加，停止这个转换并报具体原因，不能伪造身份或另抄release。
新的alias属于目标修复记录，不是新源文件：SOURCE_CURRENT核对仍以原94e6计划和来源事实为基线。

### 3. 派生候选计划与现有执行链隔离验证

将原6GB计划只读复制到本轮C目录后派生候选SQLite，原文件始终不写、不checkpoint。
应用已确认的目标目录link overlay；对上述一个失效junction，用真实终点实体关联的目标alias替代。将来源原始事实/目标修复差异留在明确manifest/meta，不能无来源标记地伪造源普通文件。
如果用普通paths/实体path_count表示这个目标alias，源读取代表必须仍是原已存在正常文件，绝不能因按路径排序选中来源那个无法跟随的broken路径；用实际reader.read_executable独立核对该实体的source_path和alias列表。原终点ASOF普通路径应能作为合法来源。
保持普通实体集合和唯一内容365007198749字节不变。目录数量应不变；链接数量预计4824，文件目标路径预计原8715067+1（区分来源路径数与修复后目标路径数），如实际差异需逐项解释。原始invalid链接元数据保留在修复清单。
新候选计划无未合并WAL，记录新SHA及完整派生diff：实体/源代表无变化、目标alias恰新增1、junction恰移除1、目录边仅overlay变化，其余集合不动。

生产runtime不修改。本轮候选 plan_sha 与原FULL常量不同，现入口尚不能将它当已批准FULL计划；明确CANDIDATE_EXECUTABLE=false，不修改门禁绕过。后续先来源当前核对，再据审核后的最终计划绑定正式合同/代码。
用C隔离小计划和现有reader/runner/WindowsBackend虚拟syscalls/acceptance验证目录终点不变、JSON目标alias与代表同目标身份/内容、没有多复制实体、第二次不重写。测试覆盖计划外终点/错误身份/仍作为目录junction/错误来源代表拒绝；不尝试真实目标写入，不造全量虚拟365GB数据。
没有引入新Win32写入API，不重做预取/提交/复制链，不重选1GiB或新建试验根。

## 来源核对交接与成果

明确下一阶段仍需SAM本机no-follow检查准确选定来源的新增/删除/身份/大小/可用mtime；无USN连续锚点不能用摘要不变替代。本轮SAM仍HOLD，不擅自远端重扫/启动源业务任务。
更新SOURCE_RECONCILE_HANDOFF.md，区分原来源基线94e6、目标修复overlay与候选SHA，保证后来发现源变更时可重放同一修复策略，不沿用过期候选当来源已冻结。
范围仍E:\BLACKBOX和已选D子树，CURSOR_TASK_ARCHIVE只选pit_products。不扩大其他D/整个归档，不要求用户重新格式化/密码或管理专业细节。

先ACK。回传 agents/chatgpt/inbox/R9_DESKTOP_PREP_DESTINATION_LINK_REPAIR_PLAN_20261014/ZHANGWEI_REPORT.md，附转换脚本、overlay/JSON指针修复manifest、原与候选SHA/diff、全候选图分类/最长链、关键实体真实reader输出、针对性隔离测试日志、当前来源交接。
巨型DB和完整明细留本机C并报SHA；HUB传可审查代码/摘要/差异/证据，必要拆文本，不上传6GB计划。
分别报告 DEST_LINK_REPAIR_PLAN_PREPARED、DIRECTORY_TERMINALS_PRESERVED、JSON_FILE_ALIAS_VALIDATED 的真实结果；CANDIDATE_EXECUTABLE=false、SOURCE_CURRENT_MATCH=NOT_RUN、full_plan_acceptance=false、COPY_AUTHORIZED=false、IMPLEMENTATION_READY=false。
完成停止待审。本轮E/源完全不写，原broken链接和长链不删除/改写；所有实际迁移/格式化授权仍为false。
