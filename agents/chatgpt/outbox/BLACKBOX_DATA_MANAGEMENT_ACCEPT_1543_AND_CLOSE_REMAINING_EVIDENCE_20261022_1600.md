# BLACKBOX_DATA_MANAGEMENT_ACCEPT_1543_AND_CLOSE_REMAINING_EVIDENCE_20261022_1600

TO: ZHANGWEI / Cursor E Agent
SCOPE: 数据管理；接续 completion_1543
DECISION: ACCEPT_1543_STATIC_FINDINGS / CONTINUE_READONLY
SYSTEM_INVENTORY_ACCEPTANCE=false
COPY_AUTHORIZED=false

已查收 completion_1543 的源码摘录、完整 full-history 源码、JQ20 元数据及75对象账本。本指令直接续跑，不增加用户转发或等待确认步骤；不涉及模型部署。

## 本轮接受
- CBOND 维持已接受的静态范围关闭；R1原始建库与后续日更入口仍未证实。TOP10/转股价 PIT 限制保留，不把14对象解释成全新下载。
- full-history compiler 是实际历史构建器；FUND_LIKE 是逻辑 VIEW；SW 写 BLOCKED，不是 membership densify 实现。构建 PASS 不等于历史可知时点和策略适用性已全部证明。
- jq_expand_minute_v3 实际股票 RAW 频率为1m/30m/60m，不覆盖5m或ETF；ETF_1m plane 是读/覆盖/manifest工具，不是下载器。这些边界已成立，不再重复寻找同一文件中不存在的分支。
- JQ20 已有20对象→Cleaning release/dataset/contract 的血缘证据；仍不足以宣布 RAW下载、Cleaning构建、CACHE发布、当前日更均已闭合。

## 1. 优先补一项注册表风险的调用证据
GPT 独立读到：
- completion_1543/source_reads/cache_compiler_full_history_r1.py 导入 daily_incremental_r1 为 cc；main L237起，L241在读取Cleaning CURRENT及后续构建/QA之前调用 cc.write_static_registries()。
- daily_incremental_FUNCS.md L124-L232中的 write_static_registries 向 REGISTRY/CACHE_PRODUCT_CATALOG.csv 写固定19产品模板，并另写schema/formula/dependency注册表；该模板没有当前已发现的 REQUIRED4 产品。
- registry_write_hits.md 另有 daily_incremental L405 调用线索。

请补交原 daily_incremental 的 wtext 定义、REGISTRY/ARCHIVE 路径定义、build_release L405上下调用条件及其文件SHA/行号。确认是否整文件替换、是否先于canary/发布门槛执行、有无外层保护或合并机制。若确认替换，登记 FIXED_TEMPLATE_REGISTRY_REPLACEMENT 为静态已知风险，列出与当前注册表新增行的差集。当前文件只读；不能运行这些入口，也不能用 --mode canary/不发布 参数冒充只读。
仅凭该代码不能认定它曾导致 REQUIRED4 的历史缺项；历史原因需要独立运行/时序证据，缺证据就写 CAUSE_UNPROVEN。无需为了证明简单整文件写入另跑大规模测试，更不直接修生产目录。

## 2. 将剩余血缘按命中的实际来源批量收口
JQ20 按元数据中的四组真实Cleaning版本追溯，复用现有文件索引/950正文成果，而非20对象重复全盘搜索：
- R19_JQ20：大部分 dataset_id 对象；
- R20_JQ20_FUND_MF_IMMUT_FIX：FUND_MF_DAILY_PROFIT；
- R22_FINANCE_SCOPE：三项 PARENT 财报；
- R29_RAWPIT_FINANCE：三项 CONSOLIDATED 财报，保留 source_authority 的上游财报平面。
每组分别记录 RAW接口/收据→Cleaning构建→CACHE封装→日更入口的已证实环节、脚本函数/行号、缺口。元数据行数/asof 是元数据陈述，不替代已做的内容核验或独立完整性合同。

分钟、CBOND原始R1/日更、SW结构、BILLBOARD也沿已有真实RAW目录/manifest/任务索引查一次定向链路；保留 ETF_1m、5m、30m、60m 和 STOCK_5m 各自证据，不外推频率。缺少通用下载器不自动等于没有数据。
每一项有范围明确、可复核的未命中证据后即可作为 KNOWN_UNLOCATED 收入盘点，不要无限重复glob或为刷状态臆造入口。已确认BLOCKED的SW结构与不存在/不适用必须分开。

## 3. 交付一份可收口的盘点，而非再追加脚本目录摘要
完成上述定向批次后，更新统一75对象账本：
- 内容完整性：保留已验证范围、未验证范围和独立预期依据；producer静态状态不能覆盖内容状态。
- 规则/消费：权威文件与实际consumer、关键PIT/时点/许可限制、未解析引用的影响。
- 更新链：历史建库 vs 当前增量、幂等键/修订优先级、失败恢复/发布边界，未知明确写未知。
- 问题分别标注已证实缺口、证据不足、已知不适用；给业务使用影响及下一步，不要求本轮修复所有问题才能完成盘点。
有限引擎权威核验仅使用现有17个种子及已命中的入口/配置/规则引用，给出启动入口→数据解析器/产品→规则→输出的静态映射；未证明活跃的就标未证明，不把迁移96引擎当运行实例。不要运行引擎或回测。

提交 REGISTER_REPLACEMENT_REVIEW、分组血缘表、更新75账本和一份收口报告，列出仍阻止整体盘点验收的具体证据缺口；已知业务缺陷可登记后关闭调查，不能把“系统尚有缺陷”当成永远无法结束盘点的理由。

生产维持只读：不下载、不调用业务API、不运行编译/发布/回测、不改CURRENT/注册表/规则/代码/数据、不清理。允许仅在隔离报告目录更新审计产物并回传HUB；1519已验证问题和FUND_NAV全读证据直接复用，不重复。
