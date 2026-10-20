# ZHANGWEI｜V4有限逻辑验收，交付可用的独立只读查询入口
task_id: BLACKBOX_BOUNDED_QUERY_ENTRY_INSTALL_20261020_2110
execution_host: ZHANGWEI
status: READY_INSTALL_OPS_READONLY_ENTRY
technical_review: V4_BOUNDED_QUERY_LOGIC_ACCEPTED
COPY_AUTHORIZED=false
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED

## 已审范围
已读取2005包V4三个源码及测试，独立实际执行候选逻辑12项检查通过：两天不FULL、self_test全项、完整短窗放行、缺日/坏分区/无窗/单端点/日历异常拒绝、丢父日期拒绝、集合保留不冒充可发布。
独立检查使用受控提取/日历输入，不声称替代本机Windows Parquet实测；Windows正负样本依据你已交报告。
验收仅“有范围、产品日期级、只读历史事实查询逻辑”，不是全历史完整/证券全量/时点回测/策略运行许可。
审定候选：
- common SHA256 0c018fb5f4cd31fc6fc05d783bf66f7bc54503e5464825259c462682fb980769
- gate SHA256 98faa2945ff9b056936ac87b5e39be87a1adf618120805c2f96e269169798fd3
- resolver SHA256 5d232abbded4043426a51b57b45afa3d799152c368f7b235a4fff2d9cb26c8d6
代码来源 agents/chatgpt/inbox/BLACKBOX_COVERAGE_BOUNDED_QUERY_REVIEW_20261020_2005/code_v4/
独立复测在同包review/ROOT_V4_BOUNDED_CHECKS.py及RESULTS.json。
1957/2059巡视用户已续航2h至22:59，按既有授权领取；不重复安装巡视服务。

## 目标与明确授权
把已审有限能力做成台式机AI可以重复调用的只读入口，而非覆盖原BLACKBOX生产脚本。
允许仅在 E:\BLACKBOX\_OPS\BLACKBOX_HANDOFF\READONLY_QUERY\ 下新增版本化管理代码/入口/说明，以及C本任务日志。COPY_AUTHORIZED=false仍表示不重启R9迁移；本条明确允许这些小型管理文件。
不改 E:\BLACKBOX\脚本\原件、原.venv、Kernel/HAND/Manifest、CURRENT/RAW/sealed、数据/索引/原计划任务；不启动更新、研究、回测、策略、下单或外部下载。

## 一次完成可用入口
1. 定位并记录V4实际测试的解释器绝对路径、sys.version、位数、相关包版本。你TEST_RESULTS_V4是Anaconda Python3.10.20，而之前为Python3.12.10，不能漏报或拿一边测试替代另一边兼容结论。
   首版可复用已测试的现成3.10.20环境，明确这是独立查询入口，不冒称原3.12.10业务.venv已修好；不用PATH默认python、不改全局环境，不批量拷包或装最新版。若选择3.12则须实际重跑同等检查。
2. 将上述精确SHA三模块放新版本子目录，例如READONLY_QUERY/runtime_v4/，核字节SHA相符；目录已有内容先核身份，不能覆盖其它任务文件。保留2005候选和原2B文件。
3. 新增一个单一查询入口（Python脚本，必要时很薄的.ps1启动器），参数至少证券代码、start/end双端点，首版仅支持STOCK_DAILY_PIT_R1。
   使用新目录候选resolver与common，打印/回执实际模块__file__/SHA和解释器，确保未导入E空模块或旧候选。每次请求使用新读的CURRENT快照/新currents，不复用上次诊断状态；不得调用fixture authority注入API来使FULL通过。
   先按现有必读规则/任务class满足前置，复用真实预检；有范围resolver coverage_ready=true且scope=BOUNDED_WINDOW_VERIFIED后再读请求数据。遇拒绝返回结构化原因、非零exit，不绕回RAW或替代读法凑成功。
4. 数据读取按已证实业务模式：解析产品路径→对应年份Parquet，使用最少列与证券/日期过滤；用日期类型，双端点含义明确。不为小窗把全年所有字段全部读入，不递归扫所有行情。
   CURRENT解析与读样本期间若指针变化，检测并拒绝混合两个release。不写数据或发布指针。
   输出实际证券行数/日期、OHLCV及所需口径字段、产品ID/release/asof/source、coverage_scope、缺失/不可验证项。产品日期覆盖通过不等于单证券每天都有数据；无证券行只说“本次过滤无匹配/需缺失门诊断”，不能直接称源没有数据或自动下载。
   known_at为空/RAW_NONE保留原值和“非因果回测许可”说明，不填充假时间或复权；不做交易建议。
5. 在同一个安装后的入口做实际Windows验证并交命令/原始结构化输出：
   - 正例000001.XSHE，2026-09-02..09-10：成功、有7行或解释真实差异，范围正确；
   - 负例09-01..09-10：缺日拒绝，未读业务结果绕过门；
   - 无窗/单端点/unsupported（若API暴露）拒绝；
   - 注入日历异常/坏分区在临时fixture里拒绝，不破坏真实文件。
   安装后SHA、解释器实际路径和结果一致；不只测试C副本后宣称E入口可用。
6. 更新本任务已生成的START_HERE/OPERATING_MAP/QUERY_CAPABILITY，并把使用入口连接到既有_OPS管理README/索引（根AGENTS已有_OPS指针），保证下一个E Agent沿原入口能找到。不修改根AGENTS、Manifest或原业务规则来“免预检”。
   给台式机AI一条自然语言用例和一个精确调用命令即可，无需让用户自己敲命令。写清当前仅该入口可用，原业务环境/日增/研究未验收。
7. 交付可复核成果，不以“等待批准安装”结束；本条已授权这个可逆、限_OPS的安装。若阻塞报精确原因并完成其它步骤。

## 验收与回退
状态OPs_READONLY_ENTRY_INSTALLED_AWAITING_REVIEW（或实际阻塞），不得宣称整个BLACKBOX恢复。原.venv问题独立保留；本轮不扩成修全部策略。
回退只停用/移出此次新增READONLY_QUERY版本目录和索引条目，保留证据；不删业务数据或恢复R9。
HUB：
agents/chatgpt/inbox/BLACKBOX_BOUNDED_QUERY_ENTRY_INSTALL_20261020_2110/
INSTALL_REPORT.md + INSTALLED_FACTS.json + 安装入口源码/启动器 + 最小实际正反例输出 + 文档diff，逐项读回后更新INBOX_FOR_CHATGPT。
