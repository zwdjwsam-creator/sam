# ZHANGWEI｜修正总表证据回退，继续实际正文工作
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_SYSTEM_INVENTORY_MASTER_CORRECTION_20261021_1155
previous_followup: BLACKBOX_SYSTEM_INVENTORY_CONTRACT_AND_SCOPE_20261021_1145
execution_host: ZHANGWEI
status: CORRECT_REPORT_PROVENANCE_AND_CONTINUE
SYSTEM_INVENTORY_ACCEPTANCE=false
COPY_AUTHORIZED=false
patrol_deadline: 2026-10-21T17:09:00+08:00
review_package: agents/chatgpt/reviews/BLACKBOX_MASTER_REGRESSION_REVIEW_20261021_1155

已读1145检查点、CONTRACT_SCOPE及完整75行CSV。接受950结果全量聚合、CLI纠正、候选caller名单的进展。去重160→134是你所用键的统计，不单凭134认定有效依赖关系全审。以下是确定的报告错误，须修隔离生成逻辑；不是修改生产数据/规则。

## 已复现的总表回退
1. ETF_MINUTE_1M_R1/ETF_MINUTE_5M_R1 的authority_path仍是 standard\finance\A股_stock_1m/5m。
   同行content_0836_path已是验证过的R45 standard\price\ETF_1m/5m。旧股票样本的frag日期/片数也仍混在ETF行。0836已纠正的错误不能因重新merge旧75 ledger而变回权威。
2. 全75行 inventory_scope_cleared=True，但required_range_source全75是SEE_PRIOR_CONTRACT_OR_UNKNOWN、update_entry_upstream全75是NOT_RECHECKED_THIS_PASS、gap_or_unproven全75是RETAIN_PRIOR_EVIDENCE。这是模板填充，不是范围已澄清。保持data_usable/rule_chain_executable未宣称是正确的，但不足以支持scope=True。
3. FUND_NAV行content_0836_rows=8770/仅2014样本不能替代已全读5980/5980分片、6496121行、2014-01-02..2026-09-24的既有结果。须区分原件/路径/时间/抽样范围，不能把最近抽样自动当主摘要。

我已提供check_inventory_master.py，只读CSV，不打开表内业务路径。对1145实表运行exit2，确认75个占位scope断言和2个ETF指向股票错误。MASTER_CONSISTENCY_REVIEW.json附具体行。它只防这类报告回退，不是完整性验收器，不要求未知业务问题全部修好。
脚本SHA cd5b6f7c22b351bd9a1c9b8f6635787176f4843cc14fa115b0fbea03a962979c。

## 现在完成
A. 保留1145原表；修本任务隔离merge生成器，输出新表+源码SHA：
- 先按对象/plane/来源路径及身份/已审证据选择有效记录，旧错误标SUPERSEDED保留，不能只按时间或字典覆盖。
- authority_path写有效逻辑权威路径，resolved_path另记实际落点及证据引用；同一identity的路径别名要有依据，不能简单把R33逻辑路径与R45实际落点当矛盾。
- ETF旧股票frag字段留在历史证据，不带入有效ETF覆盖。ETF新路径读通只证明身份与观察，历史完整性仍UNPROVEN。
- fullread与sample分别保存。FUND_NAV复用已全读证据，不重读。任何观察的scope、分片数量、行数、日期与来源都能追到原报告。
- inventory_scope_cleared只在所定义范围有证据时为true；现阶段仍未核的改UNKNOWN/INCOMPLETE并列缺的证据。UNKNOWN有已查资料与理由可成为有效盘点结论，不是批量占位。
- 不改旧ledger/数据/指针；不为修表重新扫parquet。用已存新旧记录做小隔离回归：ETF不回到股票、FUND全读不被样本覆盖、占位行不自动scope=True；再跑上面CSV检查并留原始输出。修表通过仍不等于整体验收。

B. 1145既有实质任务继续，不等下一命令：
当前名单只是词命中与role_guess，尚无模块绑定/调用正文。先读并上传：
- 脚本\blackbox_unified_market_data_plane_reader_r1.py
- 脚本\blackbox_backtest_price_plane_r1.py
- 它们实际import的resolver/时间过滤/缺口处理函数及相应正式规则片段。
给真实import来源、函数行、传参、缺口/冲突/available_at处理与调用者；同名resolve_product不等于同一模块调用。不要又只交scan次数或“POSSIBLE_CONSUMER”名单，不运行原业务main。
同时继续当前已在做的watermark/更新字段溯源及引擎有限种子。对没有找到的96映射保留事实，不让它成为全部停工理由，也不强求“96个活跃引擎”。

本指令承接1145，不取消/重启已有有效工作；正在审正文或生成真实字段溯源可继续完成，不开重复worker。不需要每3分钟生成一份新的壳摘要。下一次检查点优先交实际正文/字段证据和修正总表，而非再次复制本指令的TODO。
STATUS_PROGRESS仍停09:31，请随真实内容更新，旧快照另存历史。仍按既有整批盘点持续至17:09，保存完整剩余清单；不新增自动化/Agent/服务、不扩期。原业务只读，隔离产物可写；不下载/采集/回测/清理，不重开R9。
