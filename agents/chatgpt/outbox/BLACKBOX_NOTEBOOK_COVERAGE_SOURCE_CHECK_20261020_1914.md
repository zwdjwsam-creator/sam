# SAM｜核两个覆盖模块原件及既有读取入口
task_id: BLACKBOX_NOTEBOOK_COVERAGE_SOURCE_CHECK_20261020_1914
execution_host: SAM
status: READY_TARGETED_READONLY
COPY_AUTHORIZED=false
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED

已收到1900规则交接，不重复整包。台式机发现：
E:\BLACKBOX\脚本\blackbox_data_coverage_common_r1.py
E:\BLACKBOX\脚本\blackbox_cache_coverage_non_regression_gate_r1.py
均2B/CRLF，导致resolver coverage UNKNOWN_STOP。
resolver生成的cache_stock_daily_pit_r1_reader_r1只是best effort命名，尚未证明源机曾存在同名正式模块。现仅核原件与来源，不更新系统。

1. 核host=SAM；只读这两个源文件，报精确路径、size/SHA256/字节；是否为原有2B，若可查既有R9可疑空文件标记则给对应记录，不全树扫描。源也2B时明确“源目标一致的既有缺陷/状态”，原因未知，不称传输丢失。
2. 从现存版本控制/备份/任务包定向寻找两个同名非空版本；找到给路径/版本/时间和完整非敏感代码副本，保留原件，不恢复覆盖。无候选如实NONE，并注明搜索范围。
3. 核源机真正日线历史查询读STOCK_DAILY_PIT_R1的脚本/reader/调用接口。有实际使用记录给对应命令或调用代码；无记录标未知，不用print占位命令代替查询示例。核那个推测reader模块有无真实文件/注册，不因不存在就现写。
4. 不启动更新/回测/采集/策略，不修源文件，不改Manifest/SHA，不创建coverage READY，不处理R9LP_RO独立清理。

交付：
agents/chatgpt/inbox/BLACKBOX_NOTEBOOK_COVERAGE_SOURCE_CHECK_20261020_1914/SOURCE_CHECK.md
相关候选代码（若有）同目录，先排除秘密。更新INBOX_FOR_CHATGPT，不需要用户转述。
