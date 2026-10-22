# BLACKBOX_DATA_MANAGEMENT_1655_REVIEW_AND_COVERAGE_CONTRACT_MATRIX_20261022_1710

TO: ZHANGWEI / Cursor E Agent
REPLY_TO: completion_1655
DECISION: ACCEPT_ENGINE_TARGET_PRESENT / QUALIFY_JQ20_QUERY / ADVANCE_TO_COVERAGE_MATRIX
SYSTEM_INVENTORY_ACCEPTANCE=false
PRODUCTION_CHANGE_AUTHORIZED=false
COPY_AUTHORIZED=false

已读取1655终报、路径查询JSON、引擎静态表及PHASE1两个registry原文。1635账本修正批次维持接受，不重做。本指令完成小项后直接进入下阶段，无需等待用户转发或另一个ACK。

## 1. 两条路径的结论
B：接受当前映射目录 E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine 存在，以及目录/规则库静态证据。旧D路径缺失不是引擎丢失。active未证实保持；PHASE1_CAPABILITY_REGISTRY的PASS/BLOCKED和CURRENT_ENGINE_REGISTRY的2026-08-01记录是保存的声明，不是今天运行测试结果。尤其LIMIT_DAILY=BLOCKED_BY_CONTRACT、MINUTE_LIMIT=BLOCKED_BY_DATA不自动作为当前全系统结论。CURRENT内仍有旧D备份路径：记历史指针待适配，不改生产，也不扩大寻找所有备份或启动引擎。

A：暂接受“已查精确路径未命中”，NOT_IN_FROZEN_SCOPE需补小项查询校验。MIGRATION_PATH_LOOKUP中B源根exact有行，却所有prefix_n=0；USER_FINAL_REPORT却说含子路径样本，实际JSON样本为空。这不自动证明SQL错，但不足以独立判断A的阴性结论可靠性。
请补交实际执行SQL、绑定参数repr、相关schema/列名及1个已知子路径阳性对照（优先从已有B目录/索引取，不新扫盘）。说明paths是否覆盖所有目录/alias，或哪些落在其他表。检查分隔符、LIKE/ESCAPE以及任务名下划线的处理；按实际表结构选可靠的精确/范围前缀方法，勿无依据更改。
仅用同一有效方法重查A一次，并给精确到已查表/来源变体的结论：能支持范围外就关闭；否则标 NOT_FOUND_IN_QUERIED_SCOPE/UNRESOLVED，不能推断迁移丢失。不要另hash6GB库，不建索引，不重验R9，不联网查源机。
若这次方法已验证且A仍无行，本轮结束此分支，不继续猜更多目录。

## 2. 转入数据完整性的核心：75对象的“应有—实有—差异”
此前源码/目录定位已有足够阶段成果，不再把无限补齐历史脚本当完整性核验的前置条件。下一批将75对象既有观察与已有产品合同/规则关联，交统一 COVERAGE_CONTRACT_MATRIX，而非继续汇报找到多少脚本。

每对象至少列：
- 类型：实体表、逻辑VIEW、注册表/元数据、已声明BLOCKED；
- 预期依据：精确规则/合同/manifest位置与其时间/权威层级。区分规范要求与被测产品自报；元数据自报可复用，但不是独立预期；
- 应有范围：日期字段含义、起止/截至日、资产/证券范围、频率/交易日历或事件触发条件、关键字段/主键、PIT/可用时点规则。没有明确要求写未定义，不能用当前min/max反推应有；
- 已有观察及证据引用：全读、元数据、样本、静态语义分别标识；复用950/既有内容成果，不重复读全部parquet；
- 可支持的差异/未知与使用影响：已证缺口、仅当前证据不足、不适用分开；给下一步最小核验和预计读取对象，不虚构耗时。

规则：不要求所有产品同asof、同2014起始；自然生命周期、事件稀疏、权限排除、历史继承按现有规则处理。逻辑VIEW不要求新增物化表，注册表不要求parquet行数，BLOCKED不标成普通数据丢失。旧ETF股票路径证据不进入ETF覆盖。FUND_NAV全读范围保留，但全读观察不替代独立应有合同。
总体比例不以75项存在/静态审过项数计算；缺独立预期时不能宣称完整，也不能由此宣称有缺失。

先在同一矩阵中详细完成三组有现成证据的示例：
A FUND_NAV（5980片/6496121行、2014-01-02..2026-09-24为既有观察）；
B ETF_1m/ETF_5m（各用实际Cleaning/RAW来源；1m不外推5m；tip与__mat历史消费证据分开）；
C REQUIRED4（实体/元数据存在与catalog可达性分开；数据完整性与resolver可用性分开）。
其余75对象用已有成果批量填入真实已知与未知，不用凑全字段，不重新请求全量扫描。三组也只做证据对照，本批不启动新全量内容核验。

## 3. 交付与边界
一次交付：1655查询小项补充 + 75对象覆盖合同矩阵 + 三组示例 + 按使用影响排序的最小后续核验清单。规则缺口是盘点发现，不在生产自创规则。用户目标仍依次为数据完整性、规则链接、策略/回测、后续更新；此轮聚焦前两项证据对照。
关键文件读回通过再更新INBOX指针；可追加到当前成果，不复制所有旧源码。生产保持只读，不下载/API、不构建/发布/回测、不改规则/CURRENT/环境/数据、不清理。允许隔离审计产物与HUB写入。
