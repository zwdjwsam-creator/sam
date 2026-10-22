# BLACKBOX目录大类概览（压缩版）

依据：completion_1803/DIRECTORY_OVERVIEW_L4.md（2026-10-22 18:09:21，原表4011行）。
本表只重排已上传的目录记录，没有扫描本地磁盘；两个根分别按第0级计，最大第4级。目录存在不等于当前权威、内容完整或正在运行。

| 级 | 已观察路径 | 用途/证据边界 |
|---:|---|---|
| 0 | `E:\BLACKBOX` | 数据与规则主根；迁移范围已验收 |
| 1 | `E:\BLACKBOX\数据` | 数据各层容器 |
| 2 | `E:\BLACKBOX\数据\原始只读` | 原始来源数据；按域清单验收 |
| 3 | `E:\BLACKBOX\数据\原始只读\JQData_reference_dictionary` | 聚宽字典及字段、单位、PIT、映射等资料；权威版本待合同逐项对应 |
| 3 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw` | 26域封存清单所在聚宽RAW体系；不代表全部后续来源 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P0_meta` | 原始数据分类；具体频率/类型以原域清单为准 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P1_adjust_factor` | 原始数据分类；具体频率/类型以原域清单为准 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P2_security_state` | 原始数据分类；具体频率/类型以原域清单为准 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P2_stock_daily` | 原始数据分类；具体频率/类型以原域清单为准 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P3_finance_pit` | 原始数据分类；具体频率/类型以原域清单为准 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P3_index` | 原始数据分类；具体频率/类型以原域清单为准 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P3_index_minute` | 原始数据分类；具体频率/类型以原域清单为准 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P4_fund_etf` | 原始数据分类；具体频率/类型以原域清单为准 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P4_fund_etf_raw_none` | 已核ETF分钟RAW来源；各频率分别对照 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P4b_fund_expand` | 原始数据分类；具体频率/类型以原域清单为准 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P5_attributes_events` | 原始数据分类；具体频率/类型以原域清单为准 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P5_jq20_extension` | 增量规则列出的JQ20扩展来源；新增范围需单列 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P6_factor_reference` | 原始数据分类；具体频率/类型以原域清单为准 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P7_stock_minute` | 原始数据分类；具体频率/类型以原域清单为准 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P7_stock_minute_raw_none` | 股票30m/60m共用根；不得重复用整个根计数 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P7_stock_minute_raw_none_replacement_5m` | 已核股票5m正式RAW来源 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P7_stock_raw_none_replacement_1m` | 已核股票1m正式RAW来源 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P8_etf_fund` | 原始数据分类；具体频率/类型以原域清单为准 |
| 4 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P9_derivative_aux` | 原始数据分类；具体频率/类型以原域清单为准 |
| 3 | `E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw_manifest` | RAW清单相关资料；目录用途按名称归类，具体权威待正文 |
| 3 | `E:\BLACKBOX\数据\原始只读\JQData_9999_WINDOW_FULL_RAW_20260325_20260501` | 时间窗口RAW类别；与主RAW的继承/替代关系待核 |
| 3 | `E:\BLACKBOX\数据\原始只读\strategy_data_plane_additions` | 已审NAV/指数等补充平面的来源入口 |
| 3 | `E:\BLACKBOX\数据\原始只读\聚宽ETF_raw` | 另列RAW类别；是否正式/历史/重复以原权威清单判定 |
| 3 | `E:\BLACKBOX\数据\原始只读\聚宽因子_raw` | 另列RAW类别；是否正式/历史/重复以原权威清单判定 |
| 3 | `E:\BLACKBOX\数据\原始只读\聚宽行业指数_raw` | 另列RAW类别；是否正式/历史/重复以原权威清单判定 |
| 3 | `E:\BLACKBOX\数据\原始只读\聚宽行情_raw` | 另列RAW类别；是否正式/历史/重复以原权威清单判定 |
| 3 | `E:\BLACKBOX\数据\原始只读\聚宽财务_raw` | 另列RAW类别；是否正式/历史/重复以原权威清单判定 |
| 3 | `E:\BLACKBOX\数据\原始只读\途施可转债官方原始_R1` | 可转债外源R1；真实血统与聚宽分开 |
| 3 | `E:\BLACKBOX\数据\原始只读\途施可转债官方原始_R2` | 可转债外源R2；已审继承/增强静态范围，不能当全部日更已接通 |
| 2 | `E:\BLACKBOX\数据\中间层` | 数据层类别已观察；具体权威/用途待相应注册表确认 |
| 2 | `E:\BLACKBOX\数据\清洗成品` | 正式清洗层；按CURRENT及实际继承关系定位 |
| 2 | `E:\BLACKBOX\数据\回测缓存` | 已有75对象账本；不充当RAW全集 |
| 2 | `E:\BLACKBOX\数据\外部补充只读` | 数据层类别已观察；具体权威/用途待相应注册表确认 |
| 2 | `E:\BLACKBOX\数据\外部证据` | 外源证据类别；具体供应商以血缘登记为准 |
| 2 | `E:\BLACKBOX\数据\缓存` | 数据层类别已观察；具体权威/用途待相应注册表确认 |
| 2 | `E:\BLACKBOX\数据\美国市场` | 数据层类别已观察；具体权威/用途待相应注册表确认 |
| 2 | `E:\BLACKBOX\数据\自研因子` | 数据层类别已观察；具体权威/用途待相应注册表确认 |
| 1 | `E:\BLACKBOX\规则库` | BLACKBOX规则与字典注册表 |
| 2 | `E:\BLACKBOX\规则库\data_dictionary` | 已观察规则分类；适用版本由既有注册表/原文确认 |
| 2 | `E:\BLACKBOX\规则库\exchange_rules` | 已观察规则分类；适用版本由既有注册表/原文确认 |
| 2 | `E:\BLACKBOX\规则库\hand_hard_rules` | 已观察规则分类；适用版本由既有注册表/原文确认 |
| 2 | `E:\BLACKBOX\规则库\因子定义平面` | 已观察规则分类；适用版本由既有注册表/原文确认 |
| 1 | `E:\BLACKBOX\契约` | 合同资料类别；目录名不单独证明当前权威 |
| 1 | `E:\BLACKBOX\脚本` | 已审RAW、平面、解析器、构建/更新脚本所在 |
| 1 | `E:\BLACKBOX\运行` | 运行指针、manifest、覆盖与增量规则等资料 |
| 1 | `E:\BLACKBOX\_OPS` | 隔离审计与交接产物；不当作新增业务规则 |
| 0 | `E:\BLACKBOX_ENGINES` | 引擎及关联资产迁移根 |
| 1 | `E:\BLACKBOX_ENGINES\backtest_lab` | 回测实验室资产分类 |
| 2 | `E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine` | 已确认迁移后的引擎根 |
| 3 | `E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine\blackbox_jq_engine` | 引擎代码包存在；实际本地数据适配未完成验收 |
| 3 | `E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine\rule_library` | 已命中准入与字典规则库 |
| 4 | `E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine\rule_library\blackbox_current_dictionary_R1` | 引擎字典/准入/交易规则分类；不得把历史状态当今日运行结果 |
| 4 | `E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine\rule_library\jq_official_canonical_R1` | 引擎字典/准入/交易规则分类；不得把历史状态当今日运行结果 |
| 4 | `E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine\rule_library\master_registry_R1` | 引擎字典/准入/交易规则分类；不得把历史状态当今日运行结果 |
| 4 | `E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine\rule_library\cn_a_exchange_trading_hard_rules_20260706_R1` | 引擎字典/准入/交易规则分类；不得把历史状态当今日运行结果 |
| 1 | `E:\BLACKBOX_ENGINES\backtest_lab_backups` | 其它已观察引擎资产类别；历史/候选/影子及引用须区分，不全部视为当前运行 |
| 1 | `E:\BLACKBOX_ENGINES\backtest_lab_candidate_releases` | 其它已观察引擎资产类别；历史/候选/影子及引用须区分，不全部视为当前运行 |
| 1 | `E:\BLACKBOX_ENGINES\backtest_lab_shadow_experiments` | 其它已观察引擎资产类别；历史/候选/影子及引用须区分，不全部视为当前运行 |
| 1 | `E:\BLACKBOX_ENGINES\CURSOR_TASK_ARCHIVE` | 其它已观察引擎资产类别；历史/候选/影子及引用须区分，不全部视为当前运行 |
| 1 | `E:\BLACKBOX_ENGINES\JQ` | 其它已观察引擎资产类别；历史/候选/影子及引用须区分，不全部视为当前运行 |
| 1 | `E:\BLACKBOX_ENGINES\blackbox_data` | 其它已观察引擎资产类别；历史/候选/影子及引用须区分，不全部视为当前运行 |

共66条。任务、release版本、年份/证券/批次、日志、备份内部、运维内部不再展开；策略/研究/记忆类目录保留在原目录记录，本轮底座验收不逐项追溯。若后续需要一个具体合同，只沿其既有引用读取，不扩展本表到更深层。
