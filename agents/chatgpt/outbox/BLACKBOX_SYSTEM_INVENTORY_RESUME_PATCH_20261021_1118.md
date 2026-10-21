# ZHANGWEI｜停止只轮询，应用已验证的完整队列续跑修补
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_SYSTEM_INVENTORY_RESUME_PATCH_20261021_1118
execution_host: ZHANGWEI
status: APPLY_ISOLATED_RESUME_FIX_AND_CONTINUE
previous_followup: BLACKBOX_SYSTEM_INVENTORY_RECURSION_AND_SEMANTICS_20261021_0930
SYSTEM_INVENTORY_ACCEPTANCE=false
COPY_AUTHORIZED=false
patrol_deadline: 2026-10-21T17:09:00+08:00
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED

## 已审事实
11:11心跳仍引用旧phase，真实STATUS停09:31。0930源码SHA5f8393a5…核对一致：phase_true_recursion(max_reads=900)达到900后返回；main写检查点后return0；递归checkpoint只保存pending_head前30，没保存完整103待处理项。
接受900次正文读取/缓存及真实递归的进展，不能声称此后持续执行。
135906是当前解析记录量，不是135906条已核有效规则关系；71707个未知大写ID、21360个broken仍需分类。不要围绕数字再重做一轮摘要。

## 已交可运行修补（不是重建自动化）
GitHub目录：
agents/chatgpt/reviews/BLACKBOX_WORKLIST_RESUME_FIX_20261021_1118/
- durable_worklist.py：完整pending/done/failed持久化，原子保存，循环去重，截止前按未完队列继续；
- run_rule_resume.py：复用SHA固定的0930严格读取/缓存及V5解析，不调用旧main，不扫描parquet；
- test_durable_worklist.py；VALIDATION.json：8项隔离测试通过，含130项队列剩127跨重启不丢失、循环、失败继续、截止、进程中断、写出失败和适配器端到端。
尚未在ZHANGWEI实跑，须本机小回归后使用，不把这8项当生产完整验收。

## 本轮立即执行
1. 核当前任务精确PID/argv/创建时间，已退出就记真实退出；活跃有效worker不杀、不重复。若同一任务还有有效作业，先让其自然checkpoint再接；不把巡视进程当盘点worker。
2. 下载上述三份.py到本任务隔离工具目录并按VALIDATION核SHA，保留0930源码/历史报告不改。使用当前已工作的D:\Anaconda3\envs\blackbox_bt_py310\python.exe运行test_durable_worklist.py的8项回归。
3. 回归通过，启动一次run_rule_resume.py：
   --base-source E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650\source_upload_0930\run_inventory_recursion_0930_worker.py
   --output E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650\continuation_1118
   --deadline 2026-10-21T17:09:00+08:00
三个参数作为各自完整参数传入，使用绝对路径。模块durable_worklist.py须与适配器放同目录。本机若报V5导入缺失，仅修隔离导入路径至现有0730模块，不回退CLASSIFIER_MISSING假统计；修补有必要改动则留diff/新SHA并回归，依本任务授权继续，不另等我批准。
4. 适配器从315种子、已有RULE_READ_STATE和本地完整0930边恢复目标，复用旧正文缓存重新解析；不使用只保存的前30项来冒充全部103。原135k边本地文件即可，不上传正文cache或整份巨大边文件；按来源分片/增量同步。
5. 该修补排除本任务报告和HUB镜像作为业务规则源，限制原ROOT内文本；未知大写token放identifier_candidates，不计确认规则边；已知ID的文件名索引也只是候选，不能当定义已核。这些变化是盘点口径纠偏，历史结果保留。
6. 运行中从continuation_1118/worklist/worklist.json读取当前项、完整pending/done/failed。下一次HUB先交实际启动/PID/开始时间/源码SHA/日志、首批进展或真实错误，不能只有ACK。退出时交SUMMARY、失败/排除及剩余范围。WORKLIST_DRAINED仅表示这项工作表结束，不是全系统验收。
现有工作窗口与巡视不变；无需新建服务、Agent、看门狗或定时器，也不需要用户操作。若这个适配器确有本机不兼容，用相同完整队列与正确截止语义修其隔离实现，不能重新写成900后永久结束。

## 规则队列完毕后，继续已经授权的实质工作
当前ETF_READER_CALLCHAIN已找到真实入口，不再只重复“候选找到”：
- 脚本\blackbox_unified_market_data_plane_r1.py：
  resolve_product → _scan_cleaning_dir/_scan_raw_year_envelope → coverage_window/list_files_for_window
- 脚本\blackbox_etf_minute_1m_plane_r1.py：
  cleaning_etf_1m_dir/scan_root → build_shard_manifest/overlapping_shards → read_overlapping/filter_request/dedupe_canonical
读取这些函数正文和调用者，列实际root构造、片段选择、RAW替代及TIP/历史是否可接、覆盖声明与实际读取的区别。只做静态追踪，确有必要的隔离只读样本需先确认无写分支；不调用--build-index/refresh/backfill等原业务写入口。
把这两份实际源码和用到的registry产品定义作为审阅附件上传（不含秘密），给具体函数/行定位。历史仍保持UNPROVEN，直至调用与片段选择有证据；不自动读入.__mat作新权威。

再继续75产品/其它plane的实际consumer/策略配置/更新类主键与恢复链、独立应有范围核查，形成统一问题表与运行逻辑候选。不要再用相同schema/起尾样本替代下一阶段。0930语义代码重复追加11条registry边，160需要按实体/关系/来源定位去重；无需为此重读数据。
本次交付前确保“活跃/完成/暂停/阻塞”有对应进程和日志证据；若无可继续的实质项，明确BLOCKED和原因，不只让HUB心跳维持PARTIAL_CONTINUE。

只读业务，只写隔离盘点脚本/报告/工作库；原数据、规则、环境、迁移state与结案查询不改，不清理/下载/采集/策略/回测。R9结论不重开。
