# 长路径停止：保留已复制数据，精确定位后准备最小恢复方案

task_id: R9_DESKTOP_TRIAGE_OVERLONG_MANIFEST_PATH_20261019_1826
execution_host: ZHANGWEI
SAM: HOLD_SOURCE_UNCHANGED
status: READY_READONLY_TRIAGE
USER_FULL_MIGRATION_AUTHORIZATION=STILL_VALID_WITHIN_ORIGINAL_SCOPE
COPY_AUTHORIZED=false
FULL_MIGRATION=false
NO_SECOND_COPY=true

## 已审核停机事实
已读8e1ee9报告及当前INBOX_FOR_CHATGPT。
旧run=R9_FULL_RESUME_AFTER_ROOT_FIX_ZHANGWEI_20261015_1400，pid32636已退出，PHASE_STOP/exit4，full_plan_acceptance=false。
entity DONE1083975/1223767，alias DONE6689430，dir DONE233668，stream_write_bytes348928107919，预算365004696055。
不是完成，也不能将stream_write_bytes/预算直接宣称完整验收百分比。
报告称源路径33770字符、manifest_backup336次，WinError206，末文件jq_pre_download_experiment_cleanup_r0_manifest.json。

## 本轮只读定位，不启动复制
先ACK。保留两个E目标根、已复制实体/alias、旧run_bind/state/日志/候选。禁止格式化、删除、改名、重扫来源、直接跳过失败文件或把失败当完成。旧1406 READY启动令撤销为暂停，不重复原失败命令。
本轮只读本机C候选/state/现有日志及少量明确来源/目标元数据；写C脱敏证据/HUB。不要新建执行state、修改code/contract/plan/run_bind，也不要把百万DONE重置重抄。

1. 精确提取实际失败实体：
   解析execute_1400 stdout最终结构化错误与现有state，不要把整段异常/JSON序列化长度当source_path长度。
   输出entity_key、source volume/file_id、logical_size、inventory_path、传给open_source_stable的实际source_path、dest_path、该实体所有aliases（可保存完整到C，HUB仅有界样本/长度摘要）。
   从原字符串分别计Python字符数、UTF-16 code units、组件数、最大组件长度；说明33770与336的取数对象。文件名、前缀/末尾和路径SHA可用于追踪，不上传整条3万字符长串。
   定位是源代表、alias、内容回读temp还是恢复hash调用失败；证明不是误解析错误文本。
   比较旧代码与当前模块digest是否仍62aff763e4c12d782039e067ea12985e36d2164af41564453249774c89d84ae3，若不同先记录实际，不启动任何代码。

2. 优先查同一(volume,file_id)的短路径：
   只在本机冻结候选按实体查paths，给path_count、最短/最长路径及各自source/target映射长度；查同实体是否已有DONE目标/alias。
   若有不超限的短来源路径，用现有生产稳定只读句柄打开查询volume/file_id/size后关闭，不读payload；只有三项匹配才能说是相同实体，不能靠同名/相同size/哈希猜等同。
   当前reader选择ORDER BY path第一条代表，源与目标代表相联：短来源可能解决源open，不自动解决超长目标/alias。必须分别分析copy/create_hardlink/observe/hash/独立验收所需路径，不能只换source宣称整个问题解决。
   禁止拿manifest文件名相同的其他文件替代原实体，禁止更改源目录。

3. 核对重复嵌套与目录阶段的矛盾：
   仅对失败路径的少量关键祖先/重复段入口检查计划paths/links及metadata，核对是否reparse展开、实际普通备份嵌套、路径拼接/清单错误，或其他原因。
   说明为何dir DONE233668时对应目标父链却可能超限：真实目录行存在否、最长目录长度、是否映射与源不同、实际API是否接收了同样长度。不要先认定循环或文件损坏。
   不递归枚举manifest_backup树、不跟随重解析循环、不扫描整个E/D。
   如果短祖先元数据无法判定，仅列待笔记本SAM本地定点核实的具体路径与最小读取字段，经HUB交接；不要让用户来回传话。不自行部署目录句柄相对访问的新后端。

4. 本机C候选做一次有界SQL/流式统计：
   全部计划内存在超长或超长组件风险的file/dir/link数量、distinct实体数、总唯一字节、最短可用别名实体数量、实际源与目标映射后的长度风险。前缀\\.?\不能修复已超过扩展路径/组件上限的路径；以实际API字符串UTF16口径为准，明确判定阈值与边界，不仅以len(inventory_path)>260筛选。
   这是扫既有本地SQLite，不是重扫来源；保留冻结plan不写索引/DDL，不重建6GB。只保留≤10条代表样例，避免大规模输出。
   在旧state只读汇总kind/phase、实体DONE的SUM(logical_size)及剩余实体/INTENT数量、已绑定run字段；记录查询时间，别把stream计数直接当唯一DONE内容。

5. 提交最小恢复方案，不实施：
   优先不丢失语义、复用已有DONE证据的方案。若只是有验证的短source别名，说明如何保留既定target/alias与验收；若清单虚假展开，先交具体坏行/重解析事实，不能自行删行；若确为无法用当前API访问的真实超长结构，明确后续需相对目录句柄等方案或用户对例外范围的选择，不能静默省略。
   任何后续代码/plan摘要变更均需兼容迁移已有state：原state不可直接改run_bind换摘要，不用全新空state忽略108万实体（否则触发UNKNOWN_TARGET_EXISTS或重新拷贝）。本轮仅说明副本/绑定迁移与目标身份/SHA复用的可审阅办法，保留原件；不要现在全量读取349GB做重复验证。
   用户原全量授权仍有效；只要不改变保留范围、删除来源或丢弃异常，技术修复无需再次问用户是否迁移。排除/截短/改名造成保留范围变化则须单独明确决策，不能自行授权。

## 回传
agents/chatgpt/inbox/R9_DESKTOP_TRIAGE_OVERLONG_MANIFEST_PATH_20261019/
ACK.md、ZHANGWEI_REPORT.md、FAILED_ENTITY_FACTS.json、OVERLONG_SCOPE_SUMMARY.json、STATE_PRESERVATION_SUMMARY.json、MINIMAL_RESUME_PROPOSAL.md、实际只读查询/探测脚本。
更新INBOX_FOR_CHATGPT为TRIAGE_REPORT_READY。完成停止，不复制、不改原数据/代码/state/plan。若已有本任务在跑只接续，不重复启动。
