# ZHANGWEI｜按现有合同重建覆盖层候选，交回代码与测试
task_id: BLACKBOX_COVERAGE_RECONSTRUCTION_CANDIDATE_20261020_1925
execution_host: ZHANGWEI
workspace: E:\BLACKBOX
status: READY_ISOLATED_IMPLEMENTATION
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED
COPY_AUTHORIZED=false

## 已定事实，不再重复搜索
两端2B模块SHA相同，R9源计划size=2；这是源目标一致的既有状态，不是传输丢失。在已检索范围无非空同名候选。不能由写入时戳推断内容自某日一直为空；调用者引用符号也只证明接口预期，不能单独证明完整实现曾存在。
日线实际消费者是Cache产品路径+Parquet，resolver推测reader不是缺失组件；不新增cache_stock_daily_pit_r1_reader_r1，不再全盘搜备份。
SAM最新证据：
agents/chatgpt/inbox/BLACKBOX_NOTEBOOK_COVERAGE_SOURCE_CHECK_20261020_1914/SOURCE_CHECK.md
规则学习交接已具第一版，本轮开始具体实现修复候选，不继续只写“建议下一步”。

## 授权工作
在独立 C:\LAN_SHARE_REPORT\BLACKBOX_COVERAGE_RECONSTRUCTION_CANDIDATE_20261020_1925\candidate 下，重建 blackbox_data_coverage_common_r1.py 和 blackbox_cache_coverage_non_regression_gate_r1.py 的候选实现，以及必要测试/适配。这是新重建版本，不冒称恢复到原文。
不覆盖E原代码/Manifest/业务数据，不改CURRENT/RAW/sealed/索引/发布，不部署、不启动日增/研究/策略。原2B件和R9证据保留。无需让用户先批准可逆候选工作。

## 连续完成到可审代码
1. 先从全部实际import/函数调用、现行数据合同/规则，抽取函数签名、返回结构、状态语义和副作用；有矛盾明确列出。
   重点：resolver、coverage_control_plane_build、coverage_diagnose、现有non-regression调用；不要只凭三个函数名补默认返回。
   原D归档 BLACKBOX_DATA_COVERAGE_AND_CACHE_NON_REGRESSION_GATE_R1 的coverage/qa/report现映射到E引擎归档，可取其既有窗口/ledger/QA预期作为兼容依据，但报告“ACCEPTED”不能替代源码或当前门通过。
2. CONTRACT_MATRIX.md说明“API/来源调用位置/语义与证据/本轮支持范围/未知时如何拒绝”。若完整API涉及其它资产，明确能力范围；未实现必须显式拒绝，不能空集合/默认READY伪装支持。
3. 最小重建优先保证本地STOCK_DAILY覆盖判定和release覆盖不退化门。读取真实交易日历和既有数据元信息，不用周一至周五近似；区分全产品日期覆盖、请求证券覆盖、上市/停牌/非交易日、缺数据/未知，具体语义以现合同为准。不静默把min/max当中间完整，不读无界全表，不生成假覆盖索引。
   calendar/required字段/契约缺失或时间语义不明时保留UNKNOWN_STOP；不得修改源数据known_at/null或价格标识来过门。
4. 必要验证应直接检验风险：
   - 完整小窗与端点语义；
   - 中间缺交易日即使min/max相同也不可误判完整；
   - 真实非交易日处理；
   - 缺calendar/字段、异常/不支持产品时不返回READY；
   - release fat→thin覆盖退化拒绝、恢复覆盖允许，沿用旧QA合同而非自定义阈值。
   兼容性测试核实际调用的参数/返回结构，不只测试新函数自己写的预期。
5. 由候选resolver工作副本加载候选coverage模块，记录实际__file__/SHA，确保没有误导入E空模块。DATA预检沿现规则；原规则SHA不更新。使用本机现成Python3.12.10与已验证兼容的必要依赖进行隔离测试可行，明确这不等于正式业务venv已修复；不批量拷包、不猜装最新版。
6. 若候选门依据充分且通过，沿已有实际Parquet消费者读取000001.XSHE 2026-09-01..09-10，记录覆盖状态、端点定义、日期与7行样本差异。known_at=null/RAW_NONE只允许按现行查询合同作历史事实读取，不宣称因果回测/策略可用。若现合同不足以判定，保持阻塞，并交已完成代码/明确缺失证据。
7. 用实际业务消费者验证，不把编译/构建脚本跑起来生成新控制面或发布CURRENT；调用前静态核无业务写入/外部请求。

## 交付（必须含代码，非仅文字报告）
此前PROVENANCE_REVIEW称“全文副本已附”，但1910 HUB目录可见的交付仅报告/摘要，没有可读代码目录；本轮补齐并读回确认。
agents/chatgpt/inbox/BLACKBOX_COVERAGE_RECONSTRUCTION_CANDIDATE_20261020_1925/
- CONTRACT_MATRIX.md
- code/候选两个模块及必要适配、测试
- evidence/当前resolver、直接调用者/相关合同的必要脱敏代码，足够ChatGPT独立复核；太大则按依赖分片并给索引，不能只写C盘路径
- TEST_RESULTS.json（命令、环境、通过/失败、样本结果、仍不支持范围）
- REVIEW_PACKAGE.md（实际改动、已有逻辑依据、候选结果、生产未改、风险与最小部署diff建议）
代码/规则若含秘密先脱敏，不上传凭据或完整私有聊天。HUB逐项读回，核候选SHA和路径，再更新INBOX_FOR_CHATGPT。
状态CANDIDATE_READY_FOR_REVIEW或BLOCKED_WITH_CANDIDATE，不写PRODUCTION_READY或全部BLACKBOX恢复。用户不需要跨机传话，SAM本轮已交证据，无新增源机工作。
