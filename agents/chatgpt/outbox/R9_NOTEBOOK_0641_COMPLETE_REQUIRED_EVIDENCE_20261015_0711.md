# SAM｜0641补齐未交证据，同时交付可更新清单

task_id: R9_NOTEBOOK_RESOLVE_234_DELTA_AND_HANDOFF_20261015_0641
followup_id: R9_NOTEBOOK_0641_COMPLETE_REQUIRED_EVIDENCE_20261015_0711
execution_host: SAM
review_status: PARTIAL_REQUIRED_EVIDENCE_MISSING
ZHANGWEI: HOLD
这是0641原任务的退回补齐，不是新一轮扫描/试验。继续原C工作目录。
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
CANDIDATE_EXECUTABLE=false
full_plan_acceptance=false

## 已接受

已直接读取并重算SAM_REPORT、classified JSON、42 JSON、handoff、script refs和两个scanner脚本的SHA/字节数，匹配清单。源码的no-follow枚举、普通文件才比较大小等已审阅。
42条全部baseline_source=delta，祖先本身有junction，现场可见File，且当前普通清单有同身份候选。故无证据支持“42实体丢失”；不再将这些行叫数据删除。
新增51分类合理（49邮箱、1规则、1根目录），不用继续试验。
140小文件全为程序/资料：92 py、23 md、17 json、7 csv、1 mdc；旧大小合计2790949字节。本发现不等于行情parquet丢失，也不需要重读365GB。

## 未接受：COMPLETE/BLOCK none 与交付证据冲突

当前classified只给live_size/live_class/live_exists，未给所要求的两个独立取数值、实际读取字节/SHA/前后身份/mtime；核查代码也未上传。两个scanner脚本是原扫描代码，不能替代本轮独立核查证据。
42表只给字符串路径候选，没有live/baseline/候选的实际volume/file id，也未给普通来源代表与链接视图的最终计划处理。handoff仍写unresolved，blocks却是[]。不要再用COMPLETE/none掩盖这些缺项；无需反复修文案，只补实际证据。

## 一次补齐并向前推进

1. **140条小文件，独立实读即可定案。**
在SAM本机以只读方式核对这140条，不复用同一个identity_for_path结果充当两种方法。给出os.stat/fstat大小与正确声明的Win32 GetFileSizeEx（或独立文件枚举长度）的两个原始值；类型/属性/volume/file id/mtime附上。
只读打开普通文件，读到EOF，累计实际字节数和SHA256，前后再次检查同一对象身份/大小/mtime。当前0/2字节无需大流量；若现场变大，限制单文件最多1MiB读量，超限报告，不扩全量内容hash。
不输出文件正文、mcp凭据或原始敏感字节。内容类别可写EMPTY/CRLF/EMPTY_JSON/OTHER，不必贴内容。
上传本次实际核查脚本与每行原始证据。实读稳定且确为0/2，就结论“当前来源确为小文件，原因/版本正确性未知”；不要继续再发一轮证明它小，也不要自动恢复/覆盖源。
若两方法/实读不一致，指出最小取数错误和影响边界，只修相关C元数据，不启动整树扫描。

2. **42条收口为链接视图与普通实体映射。**
利用已读基线/当前数据库和已有现场句柄结果，补齐原路径baseline volume/file id/size、live volume/file id/size、选定一个普通来源代表及其volume/file id/size和是否在选定范围。这里只做42条有界核对。
原路径经过junction可见File，并不说明该路径应当作为nofollow物理普通文件行。记录祖先junction/终点/后缀映射；候选代表需是现有清单的普通路径，确认其祖先不是待跟随的junction。不要在重解析目录下面额外创建重复实体/硬链接，不把42条从数据保留需求里删掉。
输出42条具体操作建议：物理清单使用普通实体代表，逻辑访问路径由目标修复后的junction保留；是否导致entity path_count调整，分别列出。若有个别无法证明则逐项阻塞，不笼统全42未决。

3. **只对现有9.8GB C数据库做一次字段完整性聚合。**
不读整树。汇总nodes的access_err/identity_err、普通文件缺volume/file id/size/mtime、重解析缺tag/target数量，D16历史缺身份与当前缺身份分开。源码compare_one在D16/reparse分支提前return，部分缺字段比较为条件跳过；不能只凭delta没有CURRENT_READ_ERROR就断言所有字段齐。若有缺项，精确列路径，再有限补取；不要扩大重扫。

4. **给能落地的来源计划更新候选，不再只写原则。**
在现有SOURCE_PLAN_UPDATE_HANDOFF旁新增机器可读SOURCE_PLAN_PATCH.json/CSV：
- 51新增及mcp现值等真实变化的具体新metadata。
- 42链接视图→普通来源实体代表的具体映射和计数规则。
- 140若确认小文件，按“当前来源原样保留，SUSPECT_VERSION待选择”列入候选，不把它们标成已验证正确版本、不静默跳过、不用猜的旧size覆盖实际。保留旧大小和全部证据。
历史版本是否恢复是独立选择，不要把恢复历史内容当复制程序开发继续扩任务。允许继续准备其他部分；当前仍不执行业务复制。
仅在已知的git/备份索引/原有明确备份目录内，按140个精确路径查是否有完整旧副本，输出备份是否存在、路径/版本/大小/mtime线索即可。不全盘搜索、不新建业务备份、不恢复/覆盖来源；没有就如实报告。找备份不能阻塞上述实读和patch交付。

回传仍用 agents/chatgpt/inbox/R9_NOTEBOOK_RESOLVE_234_DELTA_AND_HANDOFF_20261015/。
先ACK本补充，完成交：TINY_140_READ_PROOF.json/csv、MISSING_42_BINDINGS.json/csv、CURRENT_FIELD_COMPLETENESS.json、SOURCE_PLAN_PATCH.json、执行脚本和准确hash、简洁SAM_REPORT及明确的remaining_decisions/blockers。
真实0/2内容若证实，报告需要用户选择“原样迁移并标记”还是“先找旧版本”，不代替用户决定、不自行格式化/迁移；但无需在本轮向用户索要技术操作。
不要再复跑原scanner、重复hash/传递大基线、测速或复制试验。SOURCE_SCAN_STABILITY/HISTORICAL_CONTENT_MATCH继续UNPROVEN。
所有输出C；来源E/D只读；不改共享/会话、不问密码。ZHANGWEI仍HOLD。
