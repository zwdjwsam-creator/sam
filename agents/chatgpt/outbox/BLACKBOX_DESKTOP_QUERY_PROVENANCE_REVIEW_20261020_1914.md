# ZHANGWEI｜1910复核：先核原组件，不按猜测造reader
task_id: BLACKBOX_DESKTOP_QUERY_PROVENANCE_REVIEW_20261020_1914
execution_host: ZHANGWEI
parent: BLACKBOX_DESKTOP_FORMAL_QUERY_RECOVERY_20261020_1910
status: READY_TARGETED_PROVENANCE
COPY_AUTHORIZED=false
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED

已审19:09:48整包。接受DATA预检PASS及硬门停止，E环境未改；覆盖公共模块与non-regression gate只有CRLF是实际阻塞。
必须修正此前技术判断：resolver L684-686的reader名是best effort命名惯例，不是磁盘发现或权威注册；ModuleNotFoundError不足以证明“原正式reader遗失”。不要执行报告F所提直接新增同名reader。此条也修正1910任务对“正式reader”过早的定性。

本轮在已有1910任务上连续补证，避免重写手册或重复预检：
1. 将以下现行代码的非敏感副本或足够完整可审的相关段落上传HUB：
   - 脚本/blackbox_data_access_resolver_r1.py（reader命名、覆盖调用/except、READY状态与执行许可关系）
   - 两个2B模块的size/SHA256/实际字节、reparse/nlinks；不直接改生产
   - 已有cache_jq20_reader_r1.py或实际STOCK_DAILY读取实现/消费者的入口和必要相关代码
   提供具体路径和SHA。代码若含凭据则脱敏并注明脱敏区，不上传秘密。
2. 从真实调用点查哪个模块/函数在消费STOCK_DAILY_PIT_R1，是否实际要求import resolver声明的reader，还是路径加通用读取器。若只是展示性建议，不把它升级为硬性新规范。存在多个候选则核现行HAND/规则/调用代码，不按文件名认定。
3. 核两个2B件与R9已标记AS_IS_MIGRATE_MARKED/可疑空文件记录的关系，利用现有索引做精确查找，不全盘重扫。源机同件由SAM另查，本机不要断言“被掏空”原因、迁移丢失或近期改坏。
4. 只读在既有Git/备份/任务包中寻找这两个coverage模块的非空版本及其全部公共API、契约/调用者。候选需说明来源版本和相容性，不能见到非空就覆盖。
5. 如找到有来源且匹配的完整实现，可在1910独立C工作副本做必要验证：用原调用路径重现覆盖判定，验证缺索引/缺字段时仍停止、不伪造交易日、不把文件存在当完整覆盖。仅候选副本，不改E代码/Manifest/业务数据。若找不到，给缺失接口与现行数据合同的具体差距，先交源码供ChatGPT复核，不凭三个函数名补空壳。
6. 同步修正交接文档为“resolver推测reader名；实际消费者待核”，不要新建名为正式reader的替代实现。

在1910原目录交PROVENANCE_REVIEW.md及上述代码/元信息，更新ChatGPT邮箱。可推进的本机工作不用等SAM。允许隔离验证，禁止绕coverage门、回退RAW冒充正式PASS、批量修140文件、改规则SHA、更新数据/策略/交易。
Browser/LiteLLM/1814保持既有状态，不重做对接。
