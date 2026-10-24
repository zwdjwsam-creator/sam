# BLACKBOX_FOUNDATION_ACCEPT_26_FILESETS_AND_FINISH_SCHEMA_INTERFACE_20261022_1814

TO: ZHANGWEI / Cursor E Agent
execution_host: ZHANGWEI
parent: BLACKBOX_FOUNDATION_ACCEPTANCE_SCOPE_AND_EXECUTION_20261022_1745
mode: CONTINUE_SAME_TASK
FOUNDATION_ACCEPTANCE=false
PRODUCTION_CHANGE_AUTHORIZED=false

已查收1803已上传文件并读worker。目录/清单对照已有实质成果；本指令关闭已完成项，只补底座未完成部分。

## 已接受，禁止重复检查
DOMAIN_SAMESET_DIFF按26份真实CANONICAL_FILE_LIST.parquet的absolute_path逐项exists，对26域均得到expected=matched、missing=0。接受“这26份原封存清单所列路径全部在”的范围结论，不再扫描或计数这些目录。
结合已通过R9迁移保真，这批文件保留有依据；但不升级为下载本身从未截断、全部字段/单位/PIT正确、7月底后增量全部完整或所有外源已覆盖。
ADDITIONAL仅浅层索引且部分按文件名token筛选，是候选附加项，不作全量额外数据清单，不清理、不据此判损坏。

DIRECTORY_OVERVIEW_L4.md实际有4011行，虽不超过4级，仍违反用户“只要大类、不要海量目录”的意图。GPT已直接复用该文件压缩为66条，无需你重扫/重新生成：
agents/chatgpt/reviews/BLACKBOX_FOUNDATION_REVIEW_20261022_1813/DIRECTORY_OVERVIEW_COMPACT.md
后续目录定位先用此表和已有索引，原大表保留作证据即可。目录分支在此收口，不再做目录展示版本迭代。

## 余项一：把字典字段对应真正完成
已有字典根下存在：
13_local_schema_header_final_check
20_unified_data_schema_contract_freeze_full_R1
以及03_field_dictionary、05_pit_field_dictionary、06_unit_dictionary、07_mapping_reference。
先读其现成结果/注册表及已审引擎规则引用，复用已有schema指纹/字段审计和R9保真，不从26域逐文件重新读一遍。
按原合同的数据集/模式版本分组，给“原字典要求→源字段及类型/单位/复权/日期语义→清洗/标准映射→引擎准入要求”对照。保留必需/可选区别；金融事件类不能硬套逐日全证券网格。
seal SCHEMA只有domain键不能算字段已核。仅对没有既有有效schema证据或确实冲突的组，读一个有代表性的具体schema/必要列；若该组模式变化没有枚举依据，就写适用范围不足，不把一次抽样推广全组。
不要求历史策略调用证明、收益重现或找回每个历史下载脚本。

## 余项二：封存基线之后与外源范围
复用SCOPE_COVERAGE_MAP的21个增量dataset及各自raw_rel/clean_product/cache_product，不再按猜测的旧D任务名找RAW。
对P5_jq20_extension、FUND_ETF_NAV增量及已知外源各自现有manifest/收据清单做同样的有界对照，能复用已有全读/检查就复用。明确这是基线补充，不把21和26直接相减。
目录概览还显示：途施可转债官方原始_R1/R2、外部补充只读、外部证据、美国市场，以及独立窗口/旧RAW分类。用既有vendor registry、权威清单和血缘记录将它们归为本轮原要求内、正式继承/替代、已有历史版本或原规则排除；未确定的记录范围缺口，不全盘扫描每个旧目录。
外源按真实供应商字典，不硬套聚宽；原可转债静态审核直接复用，未做的原文件集合/字段核验才补。不要因为清单没覆盖就宣称数据缺失，也不要把未确定来源静默遗漏。

## 余项三：引擎实际数据接口，不再用关键词找路径
runtime_attempted=false/NOT_RUN_STATIC_ONLY标注正确。数据侧read_schema只证明样本schema可读，不是引擎已接通。
当前type_to_local_entry把minute/tradable_status/matching等按关键词猜成同一个ETF_1m RAW路径，adapter_function全部null。保留为未绑定，去掉猜测路径的“正式绑定”含义。
不要继续扫描broker/qmt、Jupyter/server或provider联网测试找本地底座。定向从：
- pyproject.toml声明入口与包初始化；
- MASTER_RULE_LIBRARY_REGISTRY_R1、DATA_INGESTION_GATE_RULES_R1的完整策略/激活字段；
- 已有data provider注册/基类与实际本地reader/adapter引用
读取真实调用链（类方法也需识别，不仅top-level def）。
如果原合同明确dictionary_only_no_value_ingest或formal_backtest/engine_core尚未激活，记录它是原交付阶段/准入边界，不当迁移丢失，也不擅自绕过激活。
若已有可用纯读取适配层，只对该实际调用链静态查副作用后按1745做一次隔离少量读取。一个env_loader.py含dotenv不等于整个代码树都不能检查/隔离；不读取.env，不导入带副作用的生产入口。
若本地值数据adapter本来就没有或需路径适配，给出明确“缺哪一层、依据哪条调用/配置”的结论和最小隔离适配方案；先不改生产，也不再把“文件存在但未连接”笼统写成数据底座缺失。

## 本轮收口结果
复用既有26域路径通过项，不要再检查它们；目录分支也已关闭。最终只更新三方面结论：
1 原规则范围内RAW文件保留：已通过哪些清单，尚未覆盖哪份后续/外源清单；
2 字典/原始/清洗/标准数据对应：匹配、具体冲突、证据不足；
3 引擎本体保留与值数据通用接口：原交付范围、当前已接通/原本未接通/迁移路径需适配分别写。
已知缺口可作为盘点发现登记后关闭调查，不为了追求每项PASS无限返工。关键是报告准确到范围，而不是重复生成大包。

在现有链路内完成一轮后整包回传；先上传并读回关键件再改INBOX。生产不下载/API、不发布、不改规则/数据/CURRENT/环境、不清理、不重启R9、不跑旧策略。
