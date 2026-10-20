# ZHANGWEI｜验收 MISSING_ENTITY 查询计划核查

task_id: R9_FULL_ACCEPTANCE_QUERY_PLAN_CHECK_20261020_0826
host: ZHANGWEI
observed_at: 2026-10-20T08:28+08:00
START_AGAIN_AUTHORIZED=false
STOP_CURRENT_PROCESS_AUTHORIZED=false
CHANGE_RUNNING_CODE_OR_STATE_AUTHORIZED=false

## 运行实例
PID 17904 仍是 2026-10-19T20:47:10 启动的原实例，argv 指向批准 contract。没有停止或重启。stdout/stderr 仍是 0 字节。本任务没有证明它当前正在执行验收 SQL。

本机 Python312 `sqlite3.sqlite_version` = 3.49.1。

## 生产 schema
`full_1938.sqlite` 只读打开成功。`stage` 仅有 `item_key` 主键自动索引，没有 `parent_key` 索引。原始 `sqlite_master` / `PRAGMA index_list(stage)` 见 QUERY_PLAN_RAW.json。

## 生产 EXPLAIN（未执行 COUNT）
在只读生产连接上，用常量行子查询代替 `plan_entity`，只跑 `EXPLAIN QUERY PLAN`：

原句（`parent_key=p.entity_key`）子查询：
`SCAN s`

候选句（`item_key='entity:'||p.entity_key` 且保留 kind/phase/parent_key）子查询：
`SEARCH s USING INDEX sqlite_autoindex_stage_1 (item_key=?)`

因此确认：在本机 SQLite 与真实 state schema 下，原验收相关子查询会对每个 plan 实体扫描整个 stage。这是性能风险。不能据此声称当前夜间耗时全部来自这里，也不能声称 PID 现在卡在这句。

生产库上没有实际执行 `COUNT(*)` / 全关联查询，没有 ANALYZE，没有建索引。

## 独立 C 副本准备的最小修复（未切换到运行）
目录：`C:\LAN_SHARE_REPORT\R9_FULL_ACCEPTANCE_QUERY_PLAN_CHECK_20261020_0826\code_opt\`
只改 `r9_acceptance.py` 的 MISSING_ENTITY 子查询，改为按主键 `item_key='entity:'||entity_key`，并继续要求 `kind='entity' AND phase='DONE' AND parent_key=entity_key`。

语义变化：仅有 `parent_key` 匹配、但 `item_key` 不是 `entity:{entity_key}` 的 DONE 行，原逻辑会放过，新逻辑会记为缺失。这更严，防止畸形 key。合成测试覆盖完整、缺实体、错 phase、错 parent、畸形 item_key、多余 DONE。

规模合成（内存库，complete 集）：
- 100 plan / ~1100 stage：旧 0.0003s，新 ~0s；旧 SCAN，新 SEARCH
- 1000 / ~11000：旧 0.027s，新 0.0004s
- 5000 / ~55000：旧 0.67s，新 0.0018s

完整语义与规模结果：SYNTHETIC_TEST.json。diff：r9_acceptance_MISSING_ENTITY.diff。

运行中的 17 模块树、contract、state、run_bind 未改。没有另开真实全验收，没有第二次启动。

## 结论范围
风险确认。优化副本已交审。是否停止当前进程、切换代码或重新独立验收，另等明确命令。当前阶段仍 UNKNOWN；full_plan_acceptance=false。
