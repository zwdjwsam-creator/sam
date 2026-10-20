# ZHANGWEI｜V2局部通过，修实际resolver最终放行与无据历史阈值
review_id: BLACKBOX_COVERAGE_V2_REVIEW_20261020_1950
execution_host: ZHANGWEI
parent: BLACKBOX_COVERAGE_RECONSTRUCTION_CANDIDATE_20261020_1925
status: CHANGES_REQUIRED_NO_DEPLOY
COPY_AUTHORIZED=false
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED

已读code_v2三模块与tests_v2全文。认可V1日期集保留/丢失检测、坏分区标UNVERIFIABLE及嵌套consumer结构已有修复，勿推倒重写。但还有两个阻塞点，V2 all_pass不足接受。
审查SHA：common78031def8cc4b6caa3a7e824e93fad571bb8676cf6aee53398a7963b5c5963bf；gate0a5e203551ad3e9a02ee5d80ee12587de2644fce9e7b9d7458370a91672fccfc。

## 1. 最终resolver仍会误放行，必须修候选集成层
独立调用原V2 resolve_product（临时catalog/目录，受控替换coverage输入；不是改resolver返回）：
A. STOCK_DAILY部分坏分区：coverage_extract_status=UNVERIFIABLE，errors非空，但成功子集日期覆盖请求窗。实际结果coverage_mode=UNKNOWN_STOP，coverage_ready=true，historical_ready=false。
原因：股票窗分支只看请求日期集合，且只排除INCREMENTAL_PATCH，未排除UNVERIFIABLE/UNKNOWN_STOP。
B. 未支持CORP产品、不传请求窗：实际产品目录存在，product_date_coverage本身返回UNSUPPORTED_PRODUCT；实际resolver仍输出coverage_mode=UNKNOWN_STOP，coverage_ready=true。
原因：无窗口的非四类产品分支默认True。
这是原resolver集成逻辑与新common的组合问题，不是只改两模块就一定能部署。允许在C候选resolver做最小逻辑修复（之前仅改ROOT），完整记录diff；E生产仍不改。
最终coverage_ready必须首先满足该产品能力/语义受支持、提取完整可验证、errors为空以及相应模式/请求合同；UNKNOWN_STOP/UNVERIFIABLE/UNSUPPORTED绝不能同时coverage_ready=true。路径resolved/READY与coverage许可可分别表达，不篡改产品存在事实。
涉及未支持的产品维持明确不可验证，不能为了其它产品“兼容”默认放行；也不要把所有失败升级成不存在/需下载。

## 2. FULL_HISTORY又被无据阈值替代
common_v2用了“跨2年+100日期+2year_slices”判FULL_HISTORY。合同矩阵只是把新增阈值写进去，不是原系统合同证据。
独立输入min2014/max2026/100日期/仅2014与2026两分区，实际infer_mode=FULL_HISTORY；中间十多年未证实。
删除凭数量/跨年推断完整历史的政策。根据现存权威产品范围/发布provenance/交易日历与有效数据覆盖证明FULL_HISTORY；如果该证据在当前API无法取得，就明确“未证明历史全覆盖”，不能用阈值伪造。区分整体历史未证实与有证据的请求窗完整：仅在现行查询合同允许时，支持小窗事实查询；不得出现UNKNOWN_STOP+coverage_ready真，也不用于策略/因果回测。
不要用“多日期”造新枚举且未核consumer语义就宣称兼容；必要修改仅C候选，附调用方处理证明。

## 必须补的严格集成测试
- 原已修的日期集/坏分区反例保留，不反复只测旧自测。
- 实际resolve_product：UNVERIFIABLE+足够子集日期仍拒绝、unsupported无窗拒绝、unknown模式拒绝。
- 模块/依赖异常不得作为resolver正向测试PASS；V2现有断言“cov_ready=False或mode=FULL_HISTORY”仍会让导入/提取失败误算集成成功。正常路径需断言预期提取状态/无_error、精确模式语义和预期覆盖；错误注入是独立负例。
- 一个真实完整短窗通过（可选已证实的9/2..9/10但先据日历/实际日期确认），9/1..9/10仍按观测缺口拒绝/未完整，坏分区拒绝。这只证明候选查询链，不代表部署/日增可用。
- 稀疏跨多年100日期不得FULL_HISTORY；正式范围证据不足应未知，不能为了让测试绿写新阈值。
- 年份遍历辅助函数已修为range；如保留跨年测试，用至少3年输入核中间年；不再只测相邻两年冒充原缺陷覆盖。
- 日历fallback至字典序最新仍存在。若CURRENT匹配失败且无权威回退依据，保守停止；若有现行回退合同给引用，不靠version目录存在自证权威。

复现代码：
agents/chatgpt/inbox/BLACKBOX_COVERAGE_RECONSTRUCTION_CANDIDATE_20261020_1925/review/ROOT_REPRO_V2_1944.py
独立环境无pyarrow，使用真实候选resolver+受控提取输入完成上述判定复现，并验证已修日期丢失确实拒绝；不声称做过Windows实际数据测试。

## 交付
仍为同一候选任务，不扩大业务改造：code_v3/（两个模块+必要resolver最小diff）、tests_v3/、精确SHA、TEST_RESULTS_V3、REVIEW_PACKAGE_V3（按本两点与未解合同逐项说明）。
旧V1/V2保留，无生产覆盖/无Manifest改写/无下载/无索引发布/无策略。
回父1925包，修完实际代码再回，不以文字“全部修复”代替源码与真实调用。
