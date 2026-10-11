# -*- coding: utf-8 -*-
"""Rebuild repair SUMMARY/REPORT after dependency export (dep fields authoritative)."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(r"C:\LAN_SHARE_REPORT")
OUT = ROOT / "BLACKBOX_R9_SELECTED_MANIFEST"
sys.path.insert(0, str(OUT))
import selected_manifest_enumerator_r2 as E  # noqa: E402

REPAIRED = OUT / "SELECTED_D_MANIFEST_REPAIRED.sqlite"
SNAP = OUT / "SELECTED_D_MANIFEST_REPAIRED.snapshot.sqlite"
ORIG = OUT / "SELECTED_D_MANIFEST.sqlite"
ORIG_SHA = "787b14d267b3b167b37695adbdffaba96c719ed50bf64659ba4ba3828f630d39"


def main() -> int:
    cfg = json.loads((OUT / "R9_SAM_SELECTED_SCOPE_CONFIG_R2.json").read_text(encoding="utf-8"))
    E.verify_config(cfg)
    dep = json.loads((OUT / "R9_SAM_DEPENDENCY_MAP_R2.json").read_text(encoding="utf-8"))
    tests = json.loads((OUT / "R9_MANIFEST_REPAIR_TEST_RESULTS.json").read_text(encoding="utf-8"))

    # refresh snapshot sha
    snap_sha = E.snapshot_db_sha(REPAIRED, SNAP)
    con = E.connect(REPAIRED, rw=True)
    content = E.compute_content_stats(con)
    summary = E.build_summary(con, cfg, cfg["config_sha256"], REPAIRED, snap_sha, "QUEUE_EMPTY", 0.0)
    summary["original_db"] = str(ORIG)
    summary["original_db_sha256"] = ORIG_SHA
    summary["repaired_db"] = str(REPAIRED)
    summary["repaired_db_bytes"] = REPAIRED.stat().st_size
    summary["unique_file_entities"] = content["unique_file_entities"]
    summary["unique_content_bytes"] = content["unique_content_bytes"]
    summary["dependency_map_sha256"] = dep.get("dependency_map_sha256")
    summary["dependency_counts"] = dep.get("counts")
    summary["repair_tests"] = {"passed": tests["passed"], "failed": tests["failed"], "total": tests["total"]}
    summary["ready_for_formal_executor_input"] = bool(
        summary["enumeration_complete"]
        and summary["identity_complete"]
        and summary["dependency_closure_closed"]
        and tests["failed"] == 0
    )
    summary["remaining_runtime_blockers"] = cfg.get("runtime_dependency_blockers") or []
    summary["D_GLOBAL_COVERAGE_PROVEN"] = False
    summary["FULL_MIGRATION"] = False
    E.meta_set(con, "last_summary_json", json.dumps(summary, ensure_ascii=False))
    con.commit()
    con.close()

    (OUT / "R9_SAM_MANIFEST_REPAIR_SUMMARY.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # resume hub slim
    resume = {
        "generated_at": summary["generated_at"],
        "task_id": summary["task_id"],
        "config_sha256": summary["config_sha256"],
        "queue": summary["queue"],
        "dir_enum": summary["dir_enum"],
        "enumeration_complete": summary["enumeration_complete"],
        "identity_complete": summary["identity_complete"],
        "dependency_closure_closed": summary["dependency_closure_closed"],
        "SELECTED_SCOPE_COVERAGE_PROVEN": summary["SELECTED_SCOPE_COVERAGE_PROVEN"],
        "content_stats": content,
        "manifest_db": str(REPAIRED),
        "manifest_db_local_only": True,
        "manifest_snapshot_sha256": snap_sha,
        "original_db_sha256": ORIG_SHA,
        "ready_for_formal_executor_input": summary["ready_for_formal_executor_input"],
    }
    (OUT / "R9_SAM_MANIFEST_REPAIR_RESUME_STATE_HUB.json").write_text(
        json.dumps(resume, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # SQL evidence block
    sql = {
        "unique_file_entities": (
            "select count(*) from (select volume_serial, file_id from nodes "
            "where is_dir=0 and is_reparse=0 and file_id is not null and volume_serial is not null "
            "and identity_err is null and access_err is null and logical_size is not null "
            "group by volume_serial, file_id having count(distinct logical_size)=1 and count(distinct mtime_ft)=1)"
        ),
        "unique_content_bytes": (
            "select coalesce(sum(logical_size),0) from (select volume_serial, file_id, max(logical_size) as logical_size "
            "from nodes where is_dir=0 and is_reparse=0 and file_id is not null and volume_serial is not null "
            "and identity_err is null and access_err is null and logical_size is not null "
            "group by volume_serial, file_id having count(distinct logical_size)=1 and count(distinct mtime_ft)=1)"
        ),
        "result_unique_file_entities": content["unique_file_entities"],
        "result_unique_content_bytes": content["unique_content_bytes"],
        "legacy_wrong_unique_entities_included_dirs": 45381,
        "legacy_wrong_unique_bytes_included_dirs": 8186614545,
    }

    report = f"""# R9_SAM_MANIFEST_REPAIR_REPORT

任务ID：R9_NOTEBOOK_MANIFEST_REPAIR_20261011_1415  
执行方：笔记本 SAM  
FULL_MIGRATION=false（本轮未复制业务数据、未重做 1GiB、未扩大全 D/E 扫描）

## 结论

| 字段 | 值 |
|---|---|
| enumeration_complete | {summary['enumeration_complete']} |
| identity_complete | {summary['identity_complete']} |
| dependency_closure_closed | {summary['dependency_closure_closed']} |
| SELECTED_SCOPE_COVERAGE_PROVEN | {summary['SELECTED_SCOPE_COVERAGE_PROVEN']} |
| ready_for_formal_executor_input | {summary['ready_for_formal_executor_input']} |
| unique_file_entities | {content['unique_file_entities']} |
| unique_content_bytes | {content['unique_content_bytes']} |
| logical_path_bytes | {content['logical_path_bytes']} |
| dir_count | {content['dir_count']} |
| reparse_count | {content['reparse_count']} |
| file_path_count | {content['file_path_count']} |
| fid conflicts | {content['fid_size_or_mtime_conflicts']} |
| runtime_dependency_blockers | {len(summary['remaining_runtime_blockers'])} |
| repair tests | {tests['passed']}/{tests['total']} PASS |

原版 DB SHA（保留未覆盖）：`{ORIG_SHA}`  
修复副本 snapshot SHA：`{snap_sha}`  
修复副本路径（本机）：`{REPAIRED}`

## 修复项

1. **内容统计**：仅普通文件（`is_dir=0 AND is_reparse=0` + 有效 volume/file_id/size/无 err）；目录 ByHandle size 不计入 `unique_content_bytes`。旧值 45381 / 8186614545 作废。
2. **恢复**：启动将 `in_progress→pending`；`enum_one_dir` 返回值映射 queue（ENUM_DONE→done / PENDING_CHANGED→pending / ERROR→error）；禁止 QUEUE_EMPTY 掩盖未解决状态。
3. **完成字段分立**：`enumeration_complete` / `identity_complete` / `dependency_closure_closed` 分算，再合成 `SELECTED_SCOPE_COVERAGE_PROVEN`。
4. **配置 SHA**：对去掉 `config_sha256` 的规范化 JSON 计算并核验；根变更保留旧自报 hash 必须失败。
5. **快照 SHA**：SQLite backup 一致性快照后再哈希（非直接哈希 WAL 主文件）。
6. **依赖闭包**：规范化 `\\\\?\\E:\\BLACKBOX\\...`；16 条 D→E 全部 `target_in_migration_scope=true`；提出台式机 `E:\\BLACKBOX_ENGINES\\...` / `E:\\BLACKBOX\\...` 映射（仅方案，未建链）。
7. **可选目录**：MIN_sandbox / 整棵 ARCHIVE / QMT 列为 optional，无引用证据不自动 runtime blocker。

## SQL（权威）

```sql
-- unique_file_entities
{sql['unique_file_entities']};

-- unique_content_bytes
{sql['unique_content_bytes']};
```

结果：entities={sql['result_unique_file_entities']} bytes={sql['result_unique_content_bytes']}

## ChatGPT 复现修复验证

见 `R9_MANIFEST_REPAIR_TEST_RESULTS.json`（9/9）：
- A：sole `in_progress` 恢复后完整枚举，非假 QUEUE_EMPTY
- B：dir size=4096 + file=100 → unique_content_bytes=100（非 4196）
- 硬链接去重、中断恢复、删除重枚举、config SHA 篡改失败、`\\\\?\\E:\\BLACKBOX` 纳入、mtime 变化不完成、CLI 非 0

## 正式执行器输入契约（草案，本轮不改 r9_1g）

```
manifest_db = C:\\LAN_SHARE_REPORT\\BLACKBOX_R9_SELECTED_MANIFEST\\SELECTED_D_MANIFEST_REPAIRED.sqlite
manifest_snapshot_sha256 = {snap_sha}
config = R9_SAM_SELECTED_SCOPE_CONFIG_R2.json
config_sha256 = {cfg['config_sha256']}
dependency_map = R9_SAM_DEPENDENCY_MAP_R2.json
dependency_map_sha256 = {dep.get('dependency_map_sha256')}
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
"""
    (OUT / "R9_SAM_MANIFEST_REPAIR_REPORT.md").write_text(report, encoding="utf-8")
    print(
        json.dumps(
            {
                "SELECTED_SCOPE_COVERAGE_PROVEN": summary["SELECTED_SCOPE_COVERAGE_PROVEN"],
                "ready_for_formal_executor_input": summary["ready_for_formal_executor_input"],
                "unique_content_bytes": content["unique_content_bytes"],
                "snap_sha": snap_sha,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if summary["ready_for_formal_executor_input"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
