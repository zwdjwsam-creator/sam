# R9_SAM_MANIFEST_REPAIR_REPORT

任务ID：R9_NOTEBOOK_MANIFEST_REPAIR_20261011_1415  
执行方：笔记本 SAM  
FULL_MIGRATION=false（本轮未复制业务数据、未重做 1GiB、未扩大全 D/E 扫描）

## 结论

| 字段 | 值 |
|---|---|
| enumeration_complete | True |
| identity_complete | True |
| dependency_closure_closed | True |
| SELECTED_SCOPE_COVERAGE_PROVEN | True |
| ready_for_formal_executor_input | True |
| unique_file_entities | 34744 |
| unique_content_bytes | 8163480337 |
| logical_path_bytes | 8163565504 |
| dir_count | 10637 |
| reparse_count | 16 |
| file_path_count | 34745 |
| fid conflicts | 0 |
| runtime_dependency_blockers | 0 |
| repair tests | 9/9 PASS |

原版 DB SHA（保留未覆盖）：`787b14d267b3b167b37695adbdffaba96c719ed50bf64659ba4ba3828f630d39`  
修复副本 snapshot SHA：`e3e0f653114782067fcc1df1d5e6d9a6c0f2d2f992f6c93649dae5831b3977a7`  
修复副本路径（本机）：`C:\LAN_SHARE_REPORT\BLACKBOX_R9_SELECTED_MANIFEST\SELECTED_D_MANIFEST_REPAIRED.sqlite`

## 修复项

1. **内容统计**：仅普通文件（`is_dir=0 AND is_reparse=0` + 有效 volume/file_id/size/无 err）；目录 ByHandle size 不计入 `unique_content_bytes`。旧值 45381 / 8186614545 作废。
2. **恢复**：启动将 `in_progress→pending`；`enum_one_dir` 返回值映射 queue（ENUM_DONE→done / PENDING_CHANGED→pending / ERROR→error）；禁止 QUEUE_EMPTY 掩盖未解决状态。
3. **完成字段分立**：`enumeration_complete` / `identity_complete` / `dependency_closure_closed` 分算，再合成 `SELECTED_SCOPE_COVERAGE_PROVEN`。
4. **配置 SHA**：对去掉 `config_sha256` 的规范化 JSON 计算并核验；根变更保留旧自报 hash 必须失败。
5. **快照 SHA**：SQLite backup 一致性快照后再哈希（非直接哈希 WAL 主文件）。
6. **依赖闭包**：规范化 `\\?\E:\BLACKBOX\...`；16 条 D→E 全部 `target_in_migration_scope=true`；提出台式机 `E:\BLACKBOX_ENGINES\...` / `E:\BLACKBOX\...` 映射（仅方案，未建链）。
7. **可选目录**：MIN_sandbox / 整棵 ARCHIVE / QMT 列为 optional，无引用证据不自动 runtime blocker。

## SQL（权威）

```sql
-- unique_file_entities
select count(*) from (select volume_serial, file_id from nodes where is_dir=0 and is_reparse=0 and file_id is not null and volume_serial is not null and identity_err is null and access_err is null and logical_size is not null group by volume_serial, file_id having count(distinct logical_size)=1 and count(distinct mtime_ft)=1);

-- unique_content_bytes
select coalesce(sum(logical_size),0) from (select volume_serial, file_id, max(logical_size) as logical_size from nodes where is_dir=0 and is_reparse=0 and file_id is not null and volume_serial is not null and identity_err is null and access_err is null and logical_size is not null group by volume_serial, file_id having count(distinct logical_size)=1 and count(distinct mtime_ft)=1);
```

结果：entities=34744 bytes=8163480337

## ChatGPT 复现修复验证

见 `R9_MANIFEST_REPAIR_TEST_RESULTS.json`（9/9）：
- A：sole `in_progress` 恢复后完整枚举，非假 QUEUE_EMPTY
- B：dir size=4096 + file=100 → unique_content_bytes=100（非 4196）
- 硬链接去重、中断恢复、删除重枚举、config SHA 篡改失败、`\\?\E:\BLACKBOX` 纳入、mtime 变化不完成、CLI 非 0

## 正式执行器输入契约（草案，本轮不改 r9_1g）

```
manifest_db = C:\LAN_SHARE_REPORT\BLACKBOX_R9_SELECTED_MANIFEST\SELECTED_D_MANIFEST_REPAIRED.sqlite
manifest_snapshot_sha256 = e3e0f653114782067fcc1df1d5e6d9a6c0f2d2f992f6c93649dae5831b3977a7
config = R9_SAM_SELECTED_SCOPE_CONFIG_R2.json
config_sha256 = 50769adf29c5cdf1889d7bef0b43a6cbb0b67560795f84603a88cd7a340f2eb5
dependency_map = R9_SAM_DEPENDENCY_MAP_R2.json
dependency_map_sha256 = 1bd356b8e69ed2df1138866835908d1072a72530dee770211ee4ca391dfaafaa
content_filter = normal files only (is_dir=0, is_reparse=0, identity ok)
desktop_E_serial_required = 806508DF
ORDER / copy = NOT THIS ROUND
```

## 产物

- `selected_manifest_enumerator_r2.py` / `export_dependency_map_r2.py` / `pathutil_r2.py`
- `repair_from_existing_db.py` / `run_manifest_repair_tests.py` / `finalize_repair_summary.py`
- `R9_SAM_MANIFEST_REPAIR_SUMMARY.json` / 本报告
- `R9_SAM_DEPENDENCY_MAP_R2.json` / `R9_SAM_SELECTED_SCOPE_CONFIG_R2.json`
- 原报告 `R9_SAM_SELECTED_MANIFEST_REPORT.md` 保留不覆盖
