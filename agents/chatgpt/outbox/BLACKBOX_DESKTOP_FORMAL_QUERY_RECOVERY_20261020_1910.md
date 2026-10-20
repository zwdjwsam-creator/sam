# ZHANGWEI｜恢复正式只读查询链，保留现有业务与数据
task_id: BLACKBOX_DESKTOP_FORMAL_QUERY_RECOVERY_20261020_1910
execution_host: ZHANGWEI
workspace: E:\BLACKBOX
status: READY_MINIMAL_QUERY_RECOVERY
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED
COPY_AUTHORIZED=false

## 复核结论
已审1834 FOLLOWUP_RUNTIME_EVIDENCE、QUERY_SAMPLE，以及SAM 1900 NOTEBOOK_HANDOVER。
1. 台式机CURRENT→本地E盘缓存可读：000001.XSHE短窗返回7行，证明该样本文件能打开，不能外推全部业务已恢复。
2. 现有E .venv启动器因ThinkPad宿主路径缺失无法启动；pyarrow临时兼容方式能读，不是正式业务环境。
3. 正式reader尚未解析；resolver虽有READY，coverage_ready=false / UNKNOWN_STOP，不是允许忽略的门。
4. 必须读取规则的存在/ACTIVE不等于MUST_READ_PRECHECK=PASS，报告未提供该PASS证据。
5. 样本known_at全部null、price_adj_tag=RAW_NONE、pit_status=OK；静态标签不能证明因果/价格门已满足。不据此得出策略可用。9/1..9/10样本实际从9/2开始，先核过滤端点/证券覆盖，不判断缺失也不补数据。
6. SAM源机日期与台式机相同：数据tip9/24，简报LAST_OK8/30。按两条流程分别陈述，停研具体原因未证实。源机没有E:\BLACKBOX_ENGINES仅说明源机布局；台式机这个根是R9 D源映射目标，不能删除/忽略它。
源机说明：
agents/chatgpt/inbox/BLACKBOX_NOTEBOOK_RUNTIME_RULES_HANDOVER_20261020_1900/NOTEBOOK_HANDOVER.md

## 本轮目标
用现有正式规则和reader跑通一个可重复的小型本地历史查询。只允许修复本任务独立环境/适配入口与交接文档，不改原业务规则、库、缓存、CURRENT、sealed、RAW或策略，不启动日增/研究autorun/交易。
不需要重写运行地图，不重复迁移或再做全库验收。

## 连贯完成（能做的直接做，遇硬门具体报告）
A. 先静态读取TASK_CLASS候选与preflight输出/副作用。使用真实适用class，不凭空创造或借别类PASS。若只允许输出业务目录，先报告而不改其检查逻辑。允许日志落本任务C报告目录/_OPS独立目录。核Manifest引用SHA与必要规则；如不匹配给出哪份文件与具体差异，不自行更新/重签Manifest或放宽门。
B. 定位正式cache_stock_daily_pit_r1_reader_r1.read的实际代码、接口和调用依赖（从resolver声明/代码引用出发，核E:\BLACKBOX及已知E:\BLACKBOX_ENGINES关联，避免全盘搜索数据）。记录真正import路径与模块文件。不虚构模块、不直接把pyarrow临时代码改名成正式reader。研究/回测门与普通历史事实查询的适用范围按规则区分，不强加与本任务无关的交易要求。
C. 允许在 C:\LAN_SHARE_REPORT\BLACKBOX_DESKTOP_FORMAL_QUERY_RECOVERY_20261020_1910\env 建独立候选venv及最小只读查询适配脚本，保留原E .venv完全不动，不改全局PATH/注册表/原启动器。
   - 先核本机Python实际版本/位数，与源3.12.10及所需扩展ABI是否兼容；不能仅凭同为Python312断定全部兼容。
   - 先查项目现有依赖清单/相关包元数据，只取本链最小依赖及版本；源根没lock不等于整个项目无清单。
   - 可用本机已有匹配wheel缓存/现有可验证安装材料建立候选环境；无适用材料时，形成明确的最小版本清单和来源方案再报，不联网猜最新版、不批量拷site-packages作为正式修复、不安装整个未知工程。
   - 可在独立适配脚本中显式引入已定位的正式reader路径；不改原业务代码，不覆盖E .venv，不“修复”数据文件。
D. 在适用preflight和查询门满足后，用正式reader重复同一证券小窗。保存确切命令、解释器/模块路径、参数端点含义、字段/价格与时点口径、结果行数/日期、耗时。核与已有7行直读样本是否一致并解释边界差异。
   - coverage UNKNOWN_STOP或reader拒绝时如实停止正式查询，定位缺少的是覆盖索引/规则/接口/路径哪一项；只提供具体最小修复diff建议，不生成“全覆盖READY”，不绕回RAW或pyarrow取得PASS。
   - known_at为空时依据现行合同判断是否允许从EOD规则推导、是否必须字段补全；不自行填时间，不伪造因果PASS。可只证明历史事实读取，若无因果用途许可明确标不能用于回测/信号。
E. 将源机有据约定合并到START_HERE/OPERATING_MAP，并注明host差异及未知；保留其原文件引用，不把新手册升级成替代Kernel规则。记录新Agent需如何加载现有规则、记忆包；先不改根AGENTS/Manifest。
F. 若成功，给一条可复制的本地只读查询入口和候选环境回退方法，状态FORMAL_READONLY_SAMPLE_PASS；这不代表日增/研究/全部策略恢复。若阻塞，给精确检查输出和单一下一步，保留已完成工作，不泛化为“等SAM整个环境”。

## 交付
本机C报告目录及E:\BLACKBOX\_OPS\BLACKBOX_HANDOFF中仅新增/修正本任务管理文档。
HUB：
agents/chatgpt/inbox/BLACKBOX_DESKTOP_FORMAL_QUERY_RECOVERY_20261020_1910/
RECOVERY_REPORT.md + 最小非敏感命令/版本/门输出 + 查询结果（如允许）或精确阻塞。
更新INBOX_FOR_CHATGPT。1814 HOLD、LiteLLM不动，Browser不作为前置，不做网页巡检诊断。
