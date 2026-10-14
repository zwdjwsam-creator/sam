# SAM｜仅核实234条差异，收敛来源交接

task_id: R9_NOTEBOOK_RESOLVE_234_DELTA_AND_HANDOFF_20261015_0641
execution_host: SAM
status: READY
ZHANGWEI: HOLD
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
CANDIDATE_EXECUTABLE=false
full_plan_acceptance=false

## 已审核，不再全盘扫描

上轮 agents/chatgpt/inbox/R9_NOTEBOOK_LOCAL_SOURCE_RECONCILE_20261014/ 的8份交付文本/CSV字节数和SHA已独立重算通过。完整CSV234行，51新增/42缺失/141大小差异；逐根计数和总数核对通过：8953552+51-42=8953561，目录233665、队列0、dirs_error=0。
原扫描02:14:46至03:58:26，已结束。父20796→worker22336的解释成立。接受“主扫描完成”，不接受报告把234条全都直接定性成真实来源变化。尚未取得可直接审阅的扫描代码。

本轮只核实这些差异并提供可用于更新迁移清单的来源交接，不重扫895万路径，不再校验/传递6GB基线、不新增测速、复制试验或迁移框架。

输入只读保留：
C:\LAN_SHARE_REPORT\R9_LOCAL_SOURCE_RECONCILE_20261014\db\CURRENT_ENUM.sqlite
SHA ffb4caa64c4b95e3fe60a5d071799530e8c32b4a4f80692d79aa976e967a01b6
C:\LAN_SHARE_REPORT\R9_LOCAL_SOURCE_RECONCILE_20261014\db\DELTA.sqlite
SHA 6f68cdb84eee5a70dd67b6fbf008bde79a2a8ea8325b050f8f9b8071a4f0e5d4
原94e6来源基线与contract/scope继续有效。全部新输出在SAM的C，不覆盖上轮数据库或原始差异。

## 1. 141条大小差异：确认到底是文件现状还是取数错误

独立解析CSV发现当前size=2有127条，size=0有13条，另1条为.cursor/mcp.json的930→1201。这种集中模式不能直接归为日常更新，也不能仅凭表格认定源损坏。
对141条做本机只读现场复核，记录no-follow身份/类型、大小、mtime；使用两个独立取数途径（例如正确声明的Win32 GetFileSizeEx与Python os.stat/目录枚举结果），核对GetFileInformationByHandle的结构/返回值及size高低位转换。不要改源。
- 对确认是普通文件且可稳定读取的对象，允许只读完整读取这些小文件并计算SHA/实际读字节数，记录前后身份/大小一致性。不打印文件正文，不输出配置、账户或令牌。2字节/空内容可仅给“换行/空JSON/BOM/其他”之类非敏感类别。
- 若真实仅0/2字节：作为“内容大幅缩小，原因未知”列出，不擅自恢复/覆盖，不静默接受为正式迁移的新正确版本。可从已有C盘元数据/日志寻找变化时间或旧副本是否存在的线索；不搜全盘、不修源、不宣布数据已丢失。
- 若扫描器读错：修最小取数/比较错误，仅修正受影响行；依据代码确认错误影响边界。若不能证明只影响这些行，先做现有数据库字段/聚合审查，明确影响范围；不未经HUB审核直接再起整树实盘扫描。
- 查所有源文件身份/类型/重解析目标比较是否真的实现，是否被“size先失败”的分支漏掉其他差异。可用现有两库SQL补完整比较，不重新读取整树。保留实际比较的字段与缺项，不能用“没有对应delta”反推该字段已验证。

## 2. 42条MISSING：先排除链接视图口径

42条全部在 E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260903_20260903_180234 下三个产品（CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1、CORP_SHAREHOLDER_TOP10_PIT_R1、INDEX_WEIGHT_PIT_R1）。
该数量/位置与历史E_DELTA补入路径有明显联系，目前只是待检验假设，不能直接删掉这42行。
只在基线/当前库中查42路径的source标签、祖先类型、raw reparse边、实体身份及当前普通实体代表路径：
- 是否是历史delta经链接跟随后记录的逻辑路径，而本轮no-follow故意不遍历对应junction？
- 按已记录的raw边作有界解析（检测循环，保留全部替换后缀）；必要时只读核查这42条和有限祖先/终点。不可扩展成整树扫描。Win1921/267或路径未枚举都不是实体内容丢失的直接证据。
- 区分 TRUE_MISSING / LOGICAL_ALIAS_NOT_ENUMERATED / LINK_CHANGED / ACCESS_ERROR / UNRESOLVED，给出证据。
- 若逻辑别名仍可映射到普通实体，列原逻辑路径→实际普通终点→volume/file id/size→该实体的有效本机来源代表，并检查终点是否在选定范围与现有普通实体内；目标别名如何保留单列。不要把真实内容重复复制成多个实体，不把目标alias当源普通文件。
- 未解析清楚就保留阻塞，不为使delta清零删记录或改源。

## 3. 51条ADDED与交接

现有CSV显示：1条为D pit_products根目录本身，49条在外部大脑信箱，1条是.cursor的HUB触发规则。
核对D根是否只是旧基线漏记根本身；邮箱/规则是运行管理资料新增，不等于新增行情数据。仍按既定全树范围保留事实，不擅自删除或排除。
邮箱在03:58后可能继续写入。本轮只允许对已知小邮箱目录及上述差异对象做有界补查，记录观察时刻，不再跑E/D整树。不要宣称全源冻结或历史内容相同。

## 一次交付，避免再拆小轮

回传 agents/chatgpt/inbox/R9_NOTEBOOK_RESOLVE_234_DELTA_AND_HANDOFF_20261015/
先ACK，完成后至少：
- SAM_REPORT.md：实际结论、可用于更新计划的变化、仍需决策/阻塞。若0/2字节属实突出列明，等待处理选择，不自动迁移。
- DELTA_CLASSIFIED.csv/json：234条逐项分类、独立现场大小/类型证据；小邮箱补查另表，不覆盖原234。
- MISSING_42_RESOLUTION.csv/json：42条完整解析与实体/别名映射。
- SOURCE_PLAN_UPDATE_HANDOFF.json：旧/新字段、真实普通实体来源代表、逻辑别名、目录新增/删除；明确仅元数据候选，未授权执行。不修改正式计划/候选/生产绑定。
- source_reconcile_r1.py、reparse_nofollow_r1.py及必要适配脚本的实际可读源码（目前HUB只有本地路径和hash）；任何修改前后SHA明确，不能只再给SCRIPT_REFS。
- summary、匹配上传字节的FILE_SHA256.json。大库留C，不传HUB，不再对大库反复全文件hash。

来源核对不需要先让旧SHA或所有差异消失。目标是识别哪些是真变化、哪些是链接/比较口径，再一次交给桌面更新最终计划。SOURCE_SCAN_STABILITY和HISTORICAL_CONTENT_MATCH继续UNPROVEN，COPY_AUTHORIZED等仍false。
不要求密码、不改共享/SMB会话、不停业务进程、不格式化、不写桌面E、不恢复/修改来源数据。
更新INBOX_FOR_CHATGPT；完成停止。ZHANGWEI本轮无执行任务，保持HOLD。
