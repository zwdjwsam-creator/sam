# ZHANGWEI｜修正完整链接审计的路径语义，再确定真实缺口

task_id: R9_DESKTOP_CORRECT_FULL_LINK_RESOLUTION_READONLY_20261014_2157
execution_host: ZHANGWEI
SAM: HOLD
status: READY
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

## 2123 审核结论

6份文本SHA已核对；冻结计划结构/统计报告一致。PLAN_STRUCTURE_OK=true继续成立，SOURCE_CURRENT_MATCH=NOT_RUN，USN增量锚点ABSENT。
当前FULL_LINK_CLOSURE尚未证明，但“32跳仍未闭合1434”不能解释成1434条真实损坏：
- 990条只是超过32跳，443条是当前精确路径查询unknown，1条被记为file；需要正确解析后分类。
- 审计closed()固定8跳。独立合成一条70节点、最终到普通目录的有限链，现脚本仍返回hops。报告提到32跳的追加计算没有随交付原始脚本/结果文件提供完整证据，不能仅凭摘要放行或判坏。
- D16条unmapped来自将migrated_link_path=E:\BLACKBOX_ENGINES\...再次送入map_inventory_path。独立合成D源+已迁移E_ENGINE+合法E目标，实际reader.iter_links产生kind=junction、blocked=false；再次映射迁移路径才报UNMAPPED。这是审计命名空间混用，不证明正式reader有这个缺口。
- 当前kind()只查完整路径，不解析目标路径中父级junction。例如A是junction，目标A\child可能应解析到A的真实目标\child，而不是要求库存里必须有A\child字面目录行。尚不能因此断言实际443条都有效或都缺失。

不修改生产reader仅为适配错误审计；不删/改源链接，不改冻结计划，不新复制或测速。

## 本轮实现与检查

仅在本轮C诊断脚本中改进离线解析，使用实际正式reader.iter_directories/iter_links映射构建一个统一的目标命名空间，再审计全部4825条。
源库存D路径、已迁移E_ENGINE路径、实际本地目标路径要区分。已迁移路径直接校验目标范围，不能再次当源库存映射。普通目录/文件/D链接使用同一映射规则，所有结果仍限制E:\BLACKBOX与E:\BLACKBOX_ENGINES。

按路径组件解析父级重解析点与残余后缀，然后继续解析；不能只查询整条目标是否字面存在。保留每条的原始目标、每次替换、最终终点/类型和依据。
用完整规范化解析状态检测重复/循环，对有限长链完成解析；不能只把8改成32/64再将超限报missing。若保护性资源限制确实触发，单列UNRESOLVED_RESOURCE_LIMIT，不伪称缺失或闭合。数学上闭合与Windows是否能实际跟随长链也是两件事，分别记录。
普通目录终点必须是计划内实际目录。目标真是文件、越界、缺实体、缺父目录或循环不能变绿。大小/身份/库存SHA不变也不能替代这项核对。
先做小型离线功能测试：有限链>32步、真循环、父junction+child后缀、已迁移D链接、普通目录/真文件/真缺失/越界。用对应测试说明与旧审计差异。
再基于原SHA94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba计划只读重新审计4825条。不能以inspect_plan的FULL默认closure.ok当证据。

输出明确分类：CLOSED_DIRECTORY、CYCLE、MISSING_TERMINAL、TARGET_FILE、SCOPE_ESCAPE、UNRESOLVED_RESOURCE_LIMIT；另外记录链长度和实际Windows可跟随性NOT_RUN/观察结果。全部分类数量应覆盖4825，无重复/遗漏。
把仍有问题的链接按独立终点/首个缺失祖先分组，避免将同一个缺目录复制成几百条不同问题；给准确路径与最小补证需求。

## 可选的极小现场补证（只读元数据）

离线仍有疑点时，可对不超过16个不同问题组代表做来源UNC元数据探测（E_DRIVE\BLACKBOX或已选定D_DRIVE）：
仅验证当前目录/文件类型、路径跟随是否失败及原WinError；不枚举子树、不读业务内容、不改共享/会话/身份、不重试登录或失败探针。
直接junction的no-follow观察和跟随打开结果区分记录；不会把最终节点看到的普通目录伪装成原路径没有重解析。链太长的Windows跟随失败要报告真实错误，不编造系统跳数上限。
若只读探测权限/接口不足，写NOT_AVAILABLE，留给后续SAM本机补证；不停止整个审计去要求用户输入密码。此小探针不是全范围SOURCE_CURRENT_MATCH证明。

## 范围与来源交接修正

保留当前冻结计划的精确纳入集合，不扩大D范围；CURSOR_TASK_ARCHIVE仅已选pit_products子树，18文件路径与16D链接。不要把9个一级前缀理解成9棵完整树。
范围历史材料已在HUB：
agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9_SAM_MIGRATION_SCOPE.json
agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9_SAM_ED_INPUT_CONTRACT.json
本机C找不到文件不代表HUB没有。读取这些材料以解释既有选择依据；其F目标/旧目标卷806508DF是历史，不得复用。历史未决建议不当新授权，更不能扩大MIN_sandbox/QMT/整个归档。
将“已纳入集合已定义”“选择理由历史证据”“真正需要用户业务取舍”分开；没有实质范围冲突就不反复要求用户确认技术细节。

USN无连续锚点，历史mtime/hash缺失，当前来源一致性仍需后续SAM本机no-follow核对；本轮只把正确解析后的异常组/准确范围与所需源本机材料写入SOURCE_RECONCILE_HANDOFF.md。
无需把所有完整数据复制进HUB。全量每链接解析记录可保留本机C的JSONL/SQLite并报SHA；HUB上传统计、完整异常组及代表证据、脚本/测试和交接，文本大于工具可读限制则拆小文件。不能只给前30例遮住其他类别。

## 回传停止

先ACK。回传 agents/chatgpt/inbox/R9_DESKTOP_CORRECT_FULL_LINK_RESOLUTION_READONLY_20261014/ZHANGWEI_REPORT.md，附原始离线测试、重算分类/问题组/链长度摘要、现场探针实际记录（如做）、完整文件SHA。记录计划与生产代码SHA前后未变。
报告CORRECTED_AUDIT_COMPLETE、FULL_LINK_GRAPH_CLOSED、WINDOWS_LONG_CHAIN_STATUS各自真实结果；有真实缺口列最小处置建议，不自动修改链接/计划、摊平链或补release，不做新试验目录。
SOURCE_CURRENT_MATCH=NOT_RUN，full_plan_acceptance=false，COPY_AUTHORIZED=false，IMPLEMENTATION_READY=false。SAM本轮HOLD，完成停止待审。
本轮只允许C诊断/日志写入及上述限定源元数据读取；E目标不写、不格式化、旧试验/原始证据保留。
