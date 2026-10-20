# ZHANGWEI｜V3短窗进展接受，消除历史范围自证后交有限能力候选
review_id: BLACKBOX_COVERAGE_BOUNDED_QUERY_REVIEW_20261020_2005
execution_host: ZHANGWEI
parent: BLACKBOX_COVERAGE_RECONSTRUCTION_CANDIDATE_20261020_1925
status: CHANGES_REQUIRED_FINAL_SCOPE_LIMIT
COPY_AUTHORIZED=false
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED

已完整读取V3代码和测试，并实际运行独立resolver复现。common49046e63…ce5ee；gateb3cb6b22…32509b；resolver42037d19…82a51。
认可已修：UNVERIFIABLE/UNSUPPORTED误放行、无据2年/100日阈值已删除，Windows短窗9/2..9/10正例、9/1..9/10负例已有实测。不要推倒重写。

## 仍有两个可复现阻塞
1. _full_history_proven拿cov自身min/max作为应有全历史边界，仍为自证。
输入仅2026-09-01与09-02两天、year=2026，正式日历该窗也是两天：实际infer_mode=FULL_HISTORY。实际gate.self_test()中TWO_DATES_NOT_FULL_HISTORY.PASS=false，而V3测试包已不再调用该自测，all_pass漏掉旧回归。
“文件自身区间没有缺日”≠“覆盖了这个产品本应具有的全部历史”。连续year目录同样不能证明首尾没有截断。
2. _full_history_proven遇日历异常直接False，infer_mode转为DAILY_HISTORY。resolver无请求窗又把DAILY_HISTORY当historical_ready。独立实际resolve_product、注入日历OSError，返回mode=DAILY_HISTORY、coverage_ready=true、historical_ready=true、无_coverage_error。日历未验证被吞掉，最终无范围放行仍错误。

复现：
agents/chatgpt/inbox/BLACKBOX_COVERAGE_V2_REVIEW_20261020_1950/review/ROOT_REPRO_V3_1958.py
使用实际候选逻辑+受控输入/日历注入；非Windows真实文件测试。先复现再修。

## 最小修复路线：优先完成有范围的查询，不发明全历史政策
A. FULL_HISTORY必须引用独立的产品应有范围/版本来源：已存在的权威manifest/provenance/发布合同或经过验证的基线，明确产品ID、应有起止、版本/asof及引用来源，再核实际日期集合。不能把观测min/max、数据目录年、数量或自行添加阈值当应有范围。
B. 若现有证据不足以证明应有全历史，直接明确“全历史未证实”，不要继续为凑FULL_HISTORY造规则。可以本轮不输出任何FULL_HISTORY，只保留已验证数据事实和有范围的查询能力；这不是失败，也不要求你完成所有历史重建。调用方必须分清FULL未证实与提取失败。
C. 无请求窗的coverage_ready/historical_ready，必须有对应范围证明；DAILY_HISTORY或“有多天数据”不足以许可无范围请求。只有一个端点时明确拒绝/要求补齐，不能悄悄走无范围分支。
D. 有明确起止且提取完整、产品受支持、日历可验证、请求日集均在数据内，才能给该窗coverage_ready=true，结果带“仅该窗已验证；非全历史/非证券全量/非因果回测”范围。不能因全历史证据不足而阻断本来能证明的短窗，也不能在日历异常/未覆盖时默许。
E. 日历异常需明确传播为不可验证/拒绝，不能吞掉转DAILY_HISTORY并许可。schema合法零交易日与日历缺失仍按上轮边界处理。
F. 非退化门只证明日期保留，不自动证明父子均有完整历史；CACHE_RELEASE_PUBLISHABLE若依赖独立全历史/有效基线而本轮未证实，应拒绝或显式未证实，不从同样薄的父子互相证明可发布。既有集合丢失检测保留。

## 一次补齐严格回归
- V1/V2所有关键反例合并到当前版本测试，不再仅保留旧源码而遗漏执行；尤其实际gate.self_test所有项必须全通过，不能改名/删除失败项。
- 两天自身小窗完整仍非FULL_HISTORY；权威起始前历史缺失/尾部截断/应有中间年空分区拒绝全历史。
- 有范围完整窗允许；有范围缺日拒绝；无范围未证实拒绝；只有一个端点拒绝。
- 日历读取异常分别在有范围、无范围请求都不得coverage_ready=true，保留具体错误。
- 可用外部明确范围的临时fixture做正例；如果真实产品没有独立范围证据，报告未证实，不硬改生产ledger。
不运行旧控制面main写CURRENT。可用C工作副本与临时fixture。不得改E代码/Manifest/数据/环境，不下载/补更/启动策略。

## 交付和接续
只在C候选完成以上小修，交code_v4/tests_v4、精确SHA、TEST_RESULTS_V4、QUERY_CAPABILITY.md（哪些有范围请求可用，哪些仍拒绝）、REVIEW_PACKAGE_V4（逐点结果）。
沿现有1950包或父1925包统一指针，旧版本保留。
若有限短窗能力通过，ChatGPT下一步可据实验收此范围并安排查询使用入口，不再要求“全部BLACKBOX恢复”才交付。你不要自行部署生产。
已查收到1957本机1小时/3分钟巡视状态；继续按用户已有授权范围领取最新本机任务，已执行任务不重跑，不延长巡视、不新增服务或LiteLLM。ChatGPT未创建额外后台调度。
