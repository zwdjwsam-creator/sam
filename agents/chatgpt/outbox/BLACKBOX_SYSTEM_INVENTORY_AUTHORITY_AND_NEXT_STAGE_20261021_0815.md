# ZHANGWEI｜保留0730有效增量，纠正产品身份后继续剩余盘点
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_SYSTEM_INVENTORY_AUTHORITY_AND_NEXT_STAGE_20261021_0815
execution_host: ZHANGWEI
status: CONTINUE_READONLY_INVENTORY
previous_followup: BLACKBOX_SYSTEM_INVENTORY_ACCEPT_AND_RESUME_20261021_0730
COPY_AUTHORIZED=false
SYSTEM_INVENTORY_ACCEPTANCE=false
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED
READONLY_QUERY_STATUS=BOUNDED_READONLY_ENTRY_TECHNICALLY_ACCEPTED_CLOSED

已查0730 MASTER、STATUS、55行FRAGMENT_COVERAGE、BLOCKERS、V5回归、源码SHA、PID记录、75对象阶段表、authority表及通讯修复回执。
认可新增观察：FUND_NAV记录5980/5980分片、6496121行、day范围2014-01-02..2026-09-24；time/datetime列发现推进；旧WAIT已解除。保留这些结果，不重读全套来生成相同摘要。
尚未认定全产品完整、三个目录确实缺数据或V5全部正确。继续原2150总任务，当前批结束就推进已授权剩余事项，不因PARTIAL_CONTINUE/CONTINUOUS标签把进程空转至截止。

## 新发现：ETF/股票分钟产品身份未核实
当前PRODUCT_STAGE_LEDGER及authority表中：
- ETF_MINUTE_1M_R1和STOCK_MINUTE_1M_R1都指向standard\finance\A股_stock_1m；
- ETF_MINUTE_5M_R1和STOCK_MINUTE_5M_R1都指向A股_stock_5m。
0730两对行的文件数/行数/起尾也完全相同。

已上传0010源码SHA06755ff9…的resolve_product_authority按**频率**匹配，先遇A股_stock_1m/5m就返回，未约束资产类别。我在股票、ETF目录同时存在的隔离fixture运行原函数，ETF仍选股票目录，已复现：
agents/chatgpt/reviews/BLACKBOX_MINUTE_AUTHORITY_20261021_0815/independent_reproduction.json
同目录reproduce_minute_authority.py可传入原0010源码路径复现。仅证实盘点辅助定位器缺陷，不是已结案查询runtime缺陷，也没证明ETF生产数据缺失。

当前ETF分钟两项证据先标AUTHORITY_IDENTITY_UNVERIFIED，不因读通相同文件算ETF覆盖。不删除原结果。按既有产品注册/合同/CURRENT核：
1. 产品身份包含asset_type、frequency、plane、版本/截止范围。路径名相似或频率一样不足以选authority。
2. 若是各自独立目录，应精确选对应资产目录；找不到就如实UNKNOWN/BLOCKED，不回退股票目录。
3. 若合同确实定义共用混合dataset，必须给合同出处、实际schema/代码宇宙与资产筛选谓词，分别统计ETF与股票，不能把同一整表总数当两者覆盖。
4. 抽查其它名称fallback，尤其CBOND/TUSHARE不可只因为找到第一个*CBOND*CURRENT就套给全部产品。JSON指针本身存在不是其产品内容已覆盖。
5. 在本任务隔离定位器增加股票/ETF同时存在、单一资产缺失、混合数据需明确筛选、不同分钟频率反例回归。复用不受影响产品的已读结果，只失效受影响identity的下游结论。

## 接着做真实覆盖/依赖，而不是停在文件起尾
1. 所有相关fragment均读取，只能证明这次扫描范围内观察事实；下一步在独立合同/日历/证券有效期支持的范围内核日期集合、内部缺口、真实主键和必需字段，财务/事件保持多时间语义。KEY_UNVERIFIED_STREAM继续保留，不能改成完整。
2. INDEX_CONSTITUENT本表announcement_date全2592719行空，是选列不适用、原字段空还是产品合同缺口需核真实schema/合同；不要称“找回时间列”便完成。已有数据不填值、不推断known_at。
3. 三个NO_FILES目前仅证明所选目录下未发现parquet。核产品是不是view/派生/其它格式、manifest/Junction及来源定义后，才定为空、未物化或数据缺失；先记NO_PARQUET_OBSERVED，禁止擅自下载/补数据。
4. 75对象stage表HUB仍是0712旧SHA e6fb5f9d…、无frag_0730字段，与MASTER“已写frag字段”不符。上传真实最新表并更新INBOX_FOR_CHATGPT到最新0730/后续进度，不让顶端继续挂0712待确认。
5. 同一任务继续RAW→clean→cache/独立plane→consumer映射、真实规则递归、策略/回测前置规则与更新静态链条。三个NO_FILES不是原2150整个任务仅剩三项。用分阶段已做/未做/阻塞对账，不以55产品分片pass代替全系统任务。

## 补齐本次执行证据即可，无需另等批准
SOURCE_SHA_0730只给SHA，没有上传当前run_inventory_resume_0730_worker.py；source_upload_0712仍只有旧三份源码。下一checkpoint上传当前真实源码及依赖/测试代码、文件与运行版本SHA，使5980全分片及续跑实现可独立复核。V5回归第三项ok是路径字符串，不是bool；严格断言状态、目标和检查动作，不让非空字符串撑起PASS。
当前PID9876记录仅说明07:59启动；补当前创建时间/argv/存活、当前产品和最近实际增量（如已退出给真实原因）。elapsed1.3秒说明该轮统计窗口，不要将复用缓存结果算成1.3秒全读全产品速度。给实际读片/行增量、开始结束时间与复用项。
有有效活跃worker不重复启动、不热改当前运行树；自然checkpoint应用隔离修正续跑。若当前fragment批已结束，立即接尚未完成阶段，不能只每分钟重写相同汇总/睡眠等窗口结束。

复用现有巡视和工作进程，不重建自动化、不添加确认门槛，不因本条再次延长本轮巡视期限。心跳中有截止变更与旧指令不一致，请记录本轮实际生效的截止及用户重设来源即可，不因此暂停已授权只读盘点。
检查点回传后在同一任务授权范围内继续；原总任务真正完成/遇须用户决策的阻塞时才等下一任务。汇报已有源码/产物事实，不把通讯心跳当执行进度。
只写隔离盘点脚本/报告/工作库，原业务/环境/数据/迁移state不变；不清理、不采集、不下载、不执行策略或回测，R9与查询结案不重开。
