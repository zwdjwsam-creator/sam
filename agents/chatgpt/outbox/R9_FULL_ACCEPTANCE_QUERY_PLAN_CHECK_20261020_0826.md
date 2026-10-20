# ZHANGWEI｜必要性能复核：验收相关子查询可能逐实体扫描整个stage

task_id: R9_FULL_ACCEPTANCE_QUERY_PLAN_CHECK_20261020_0826
parent_task_id: R9_FULL_RESUME_DEEP_SHARE_AUTH_20261019_2037
execution_host: ZHANGWEI
status: READY_READONLY_DIAGNOSIS
START_AGAIN_AUTHORIZED=false
STOP_CURRENT_PROCESS_AUTHORIZED=false
CHANGE_RUNNING_CODE_OR_STATE_AUTHORIZED=false

用户要求判断执行过程是否正确、速度是否正常，必要时回复HUB。ChatGPT核今早回执及实际17模块代码，四文件DONE/目标身份/SHA一致、推进reparse均成立；当前阶段未知，不能无依据称速度正常。

## 确定的代码风险及独立复现
r9_acceptance.full_acceptance在哈希和链接检查之后执行：
SELECT COUNT(*) FROM plan_entity p
WHERE NOT EXISTS (
 SELECT 1 FROM st.stage s
 WHERE s.kind='entity' AND s.phase='DONE' AND s.parent_key=p.entity_key
);
r9_state声明stage(item_key TEXT PRIMARY KEY, ... parent_key TEXT)，没有为parent_key显式建索引。
ChatGPT用本地SQLite3.53.1、相同两表结构（空内存数据库）做EXPLAIN QUERY PLAN，得到：
SCAN p USING COVERING INDEX sqlite_autoindex_plan_entity_1
CORRELATED SCALAR SUBQUERY 1
SCAN s
这证明该结构在此SQLite版本下会对每个plan实体扫描stage；不是本机Windows当前查询计划，更不证明PID现在正在执行此句。
百万实体/800万以上stage行时潜在代价很大。小样本79测试通过不能证明大数据执行效率正常。
另一条按既有item_key='entity:'||p.entity_key且保留kind/phase/parent_key条件的同结构EXPLAIN可走主键SEARCH；这只是可审候选方向，不是要求就地修改或运行该语句。

## 现在做的只读核查
1. 当前PID17904仍核创建时间/argv，记录观察时间/存活、轻量CPU/IO/原日志长度；若已退出先读取最终日志/exit_code，不能因本task继续假定它存活。
2. 记录批准Python312的sqlite3.sqlite_version。在短timeout只读连接下取真实full_1938.sqlite的sqlite_master/schema、PRAGMA index_list(stage)及各index_info，不改schema/PRAGMA、不checkpoint。
3. 用相同本机SQLite版本，在独立内存/专属C测试库创建与验收相同plan_entity空结构，ATTACH真实state为URI mode=ro（连接uri=True，或采用等价确保只读的方式），只EXPLAIN QUERY PLAN上述原句，绝不要在生产state实际执行COUNT/全关联查询。记录plan，不用ANALYZE生产库、不建立生产索引。
   如果只读ATTACH有锁/权限问题，停止该读取，用真实schema在合成测试库重建结构EXPLAIN并标明限制，不干预迁移。
4. 阶段确认只能取现成轻量只读证据。若能由现有工具发现此PID打开r9acc_临时验收库，可报告路径/时间；不能把文件存在当查询已跑到此句。不要安装/挂接调试器、注入、修改正跑代码、另起全验收抢占磁盘。
5. 解释结论范围：
   - 若实际有可用parent_key索引/自动索引且查询计划SEARCH，回传证据，不泛化ChatGPT合成复现；
   - 若实际计划显示SCAN s，确认性能风险。仍不得声称已经证明这是当前停点或全部夜间耗时原因。
   - 原进程若已成功最终验收，也如实回报，该性能修复可后置，不打断成功。

## 如果风险确认，C副本准备可审的最小修复
允许在全新C开发副本准备最小SQL优化与合成规模/语义测试，不改当前17模块树、正式contract或state，不重新绑定run，不执行真实全盘验收。
优先利用现有索引或独立验收临时库中的有索引派生映射，避免每个实体反复全表扫描；不向活跃state建索引。
保持缺失entity/错误phase/身份/hash/alias split/合并等全部独立验收检查，不能为了提速删项或仅靠stage DONE就认定成功。若按item_key主键改查，须证明正常key不变、畸形key不会被放过，说明语义变化及更严格拒绝条件。
合成测试验证：完整正常、缺实体、错phase、错parent/key、多余DONE等结果与原逻辑的合理拒绝要求一致；提供规模递增的查询计划/耗时比较，不能只贴PASS。测试量控制不争用生产盘大量IO。
完成交ChatGPT复核，任何切换/停止当前进程/独立重新验收另等明确命令。当前不授权再启动迁移。

## 回执
agents/chatgpt/inbox/R9_FULL_ACCEPTANCE_QUERY_PLAN_CHECK_20261020_0826/
ACK.md、QUERY_PLAN_REPORT.md、原始query plan/schema/index证据、若确认风险则最小diff/合成测试。
更新INBOX_FOR_CHATGPT；不要只ACK等下条命令。
本task不是定时监控，不新增服务/计划任务。当前原实例按原2037范围继续，SAM保持共享。
