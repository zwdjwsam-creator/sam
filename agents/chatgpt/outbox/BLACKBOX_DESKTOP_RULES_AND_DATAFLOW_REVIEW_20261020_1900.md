# ZHANGWEI｜1834第一轮复核：补实际数据入口，先不修生产
task_id: BLACKBOX_DESKTOP_RULES_AND_DATAFLOW_REVIEW_20261020_1900
execution_host: ZHANGWEI
parent: BLACKBOX_DESKTOP_RULES_AND_DATAFLOW_HANDOVER_20261020_1834
status: READY_READONLY_FOLLOWUP
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED
COPY_AUTHORIZED=false

已读1834整包。入口/运行地图可作为第一版索引接受；这还不是数据库可用性验收，三条链目前只核指针与文件存在。无需重写整包，补以下实质缺口。

1. 给可独立复核的规则依据：AGENTS/Kernel/HAND/Manifest里与必读门、Cache-First、数据缺失判定、日期对齐、只读/写入发布边界相关的必要脱敏摘录，附实际绝对路径与章节。核“记忆盘”入口中真正适用的运行约定，不能仅列目录。不要上传秘密或整段私有聊天。
2. 选一条确有官方/现行数据访问入口的历史行情查询，沿CURRENT解析到具体release/实际文件或库，记录适用的读取方法、格式/表、关键日期和价格口径、索引/分区选择、最终本机路径与依赖。核是否仍指向源机/旧盘，区分有意的D secrets引用。不要扫描全部文件；关键链路少量样本即可。若涉及junction/hardlink只读核指向/身份。
3. 先静态检查该入口及Manifest preflight的副作用。依赖和只读边界明确时，按原授权做一个证券、一个短历史区间的极小查询，记录确切调用/参数/解释器、返回行数和字段/日期范围、耗时及错误；不跑全表COUNT、全量hash或回测。若入口会写业务/连外部服务/触发更新，停止该入口，报告具体阻塞，不能为凑PASS而执行。
4. .venv里ThinkPad路径是“可能不可移植”的线索，不足以判环境坏或直接建议系统Python替代。只读核现有解释器可启动性、项目要求与已装相关依赖（只需本链路）；不安装/重建venv，不改启动器。修正START_HERE把“用系统Python”改为待核兼容性，保留明确证据。
5. 9/24的数据指针和8/30研究简报可能分属不同流程/有意停更。核各自对应的任务、run_id/status和时间字段含义，分开记录：数据覆盖日期、任务运行日期、研究简报日期。未核历史前不称迁移导致停更，不执行补更。
6. 提供涉及本链路的策略/引擎最小依赖证据；任务调度/乱码目录来源问题可由SAM补充，但台式机现有定义/文件类型可先查。目录名异常不等于迁移损坏，不改名/删除。无需等SAM回件才交本机可完成部分。

交付原1834 inbox目录 FOLLOWUP_RUNTIME_EVIDENCE.md（含必要规则摘录、实际数据入口/查询证据、明确阻塞及下一步最小修复建议）；同步修正本地_OPS文档的过强表述。只改本任务生成的交接文档，不改根AGENTS/原规则/业务代码/库/索引/计划任务。查询若要求前置日志，只允许本任务独立_OPS/C报告目录，不写业务CURRENT。
SAM来源说明已由ChatGPT另发HUB任务，不需用户转述，不自行启动其它Agent。1814 HOLD，LiteLLM不动，不再诊断Browser；不重复R9验收/迁移。
