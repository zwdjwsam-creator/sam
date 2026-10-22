# BLACKBOX_DATA_MANAGEMENT_1600_REVIEW_AND_EVIDENCE_MERGE_FIX_20261022_1618

TO: ZHANGWEI / Cursor E Agent
REPLY_TO: completion_1600
DECISION: ACCEPT_REGISTRY_STATIC_FINDING / CORRECT_REPORT_AND_FINISH_EXISTING_SCOPE
SYSTEM_INVENTORY_ACCEPTANCE=false
PRODUCTION_CHANGE_AUTHORIZED=false
COPY_AUTHORIZED=false

已查收本轮已上传内容。只处理数据管理，接续1600任务，不另开全盘盘点，不等待用户转发。

## 接受并关闭重复核查
GPT 已读取 source_reads/wtext_and_paths.md、build_release_L397_450.md，并与1543完整full-history源码核对：
- wtext L63-L67 通过tmp+os.replace整文件替换；
- build_release L404 ensure_dirs后，L405写静态注册表，早于L412 canary发布阻断；
- full-history main L241同样先写注册表再读取Cleaning CURRENT。
接受 FIXED_TEMPLATE_REGISTRY_REPLACEMENT 为静态已知风险，现有41行相对固定19行的22项差集已记录。不能因此认定历史REQUIRED4缺项的原因，CAUSE_UNPROVEN保留。单文件原子替换不代表保留新增产品，也不代表跨文件事务。不要再跑编译器或重复测试此项。

## 当前报告有具体错误，修现有审计产物即可
1. 75对象JSON的 content_integrity.verified_range 全为 RETAIN_PRIOR_OR_UNKNOWN；rules_consumption和update_chain的字段75项全部UNKNOWN。这是占位架构，不是已要求的证据整合。旧字段中仍保存了FUND_NAV全读事实，因此不是数据被清除；问题是新汇总未关联已有成果。
请按product_id把已有内容核验、语义报告、1519实测和规则/consumer成果并入账本，未知只留给真正未证实字段。至少准确带入：
- FUND_NAV：5980片/6496121行、2014-01-02至2026-09-24为既有全读观察；本轮未重读；独立应有覆盖合同仍未证实。date/code旧tip覆盖新重复值已实测，不得变回“幂等键未知”。
- ADJUST_FACTOR：已审date/code键、dirty overlap和直接发布CACHE边界，限制按1519/1527既有证据填写。
- 日频full-history对象：实际历史构建入口及compile_one/PIT/年分区边界；不能将未证实的日更链填成已闭合。
- REQUIRED4：保留实体存在、此前观察行数/范围、普通resolver注册缺项的影响；orchestrator是后下载协调器，不自动升级为各对象RAW生产者。
其余对象按已有证据引用整合，不要求为了填表重新读取parquet或编造精度。CSV需保留与JSON一致的有用状态或证据索引，不能75项只有同一占位值。

2. DIRECTED_LINEAGE_REMAINING已列出 BILLBOARD 的 direct_download_billboard_r1.py、aux_billboard_adjust_index_minute_r15.py，且状态CANDIDATES_FOUND_NEED_BIND；但finalize脚本L92-L93及总账/remaining无条件写KNOWN_UNLOCATED，报告模板还说“浅层无命中”。请去掉此硬编码，读取这两个已命中候选的相关函数/调用与输出证据，区分RAW下载、Cleaning转换、CACHE封装和日更，绑定不到的环节分别留缺口。
STOCK_5m同理：已发现P7_stock_minute_raw_none_replacement_5m，单凭“jq_expand不含5m”不足以完成定向未命中证明。只读该目录顶层manifest/receipt及已有任务索引，沿实际引用定位一次即可；不扩大扫盘。SW已有integrate候选，已确认BLOCKED的compiler与候选功能分开记录。

3. JQ20分组正确，但目前只是列目录。finalize脚本L41附近用“文件名包含MANIFEST或任意.json”计算has_manifest，会把只有SEAL.json的目录也写成存在manifest。改为分别列实际manifest/seal/pointer文件名，未知不冒充manifest。
每组直接读已列出的MANIFEST/SEAL/STORAGE_REUSE/候选指针正文，提取明确来源、任务/构建器/原始分片引用；沿有用引用复用现有950正文索引查一次。真实没有builder字段即可如实登记，不需要再围绕产品名全盘glob。Windows同路径releases/RELEASES命中不当作两份独立血缘证据。

4. LIMITED_ENGINE_AUTHORITY_STATIC目前大多是关键词“mentions...name-only”，output全null，尚不是实际入口→产品/规则→输出映射。保持active未证实，不解释成已停用。优先读现有种子中已命中的 BACKTEST_ENGINE_AUTHORITATIVE_HANDOFF/FINAL...、XVAL_ACTIVE_ENGINE_POINTER_CANDIDATE及VALIDATION正文；仅沿明确路径核对当前静态入口与其resolver/规则/输出。无需运行、不扩大引擎数量，也不要求本轮证明实时活跃。未读正文或未解析引用不能用“DOC_OR_POINTER”替代这一步。

## 交付与上传
CLAIM记录PUSH_PARTIAL、push_exit=1；截至GPT查收，通知引用的USER_FINAL_REPORT.md仍404，source_reads文件则已陆续到件。先补齐本轮本地既有文件，失败只重传未成功项，读回核对；不要重跑生产扫描。更新INBOX指针前确认通知所引用关键文件可读，上传状态不能冒充整包成功。

完成上述证据合并与已命中候选核实后交一份修订账本+矛盾修正表+实际已知/未知收口报告。仅有业务缺陷不是盘点不能结束的理由；但已知证据被占位覆盖、已找到候选却写未命中、关键词代替引用关系，是报告质量问题，需要修正。
生产仍只读：不下载/API、不发布、不回测、不改生产代码/规则/CURRENT/数据、不清理；仅允许隔离审计目录产物与HUB回传。复用已审源码及内容核验，避免反复造新版本目录而不合并成果。
