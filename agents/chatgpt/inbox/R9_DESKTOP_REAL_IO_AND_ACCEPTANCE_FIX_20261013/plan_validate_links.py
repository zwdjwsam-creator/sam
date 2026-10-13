import json, sqlite3
from pathlib import Path
import r9_adapter as adapter
plan=Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite")
c=sqlite3.connect(f"file:{plan.as_posix()}?mode=ro", uri=True)
c.row_factory=sqlite3.Row
stats=dict(c.execute("select key,value from stats"))
audit=[dict(r) for r in c.execute("select * from link_overlay_audit order by map_id")]
status=dict(c.execute("select status, count(*) n from links group by status"))
edges=[]
for row in c.execute("select path, target, migrated_link_path, migrated_target from links"):
    if row[1]:
        edges.append((row[0], row[1]))
    if row[2] and row[3]:
        edges.append((row[2], row[3]))
cycles=0
for src,_dst in edges:
    if adapter.walk_reparse(src, edges):
        cycles += 1
        break
out={
  "baseline": {k: stats.get(k) for k in ("file_paths","entity_count","unique_content_bytes","logical_path_bytes","dir_paths","links","plan_ready")},
  "link_status": status,
  "overlay_rows": len(audit),
  "overlay_mapped": sum(1 for r in audit if r["status"]=="MAPPED"),
  "delta_files_sum": sum(r["delta_files"] or 0 for r in audit),
  "cycles": cycles,
  "algorithm": "longest ancestor link plus remainder; repeated path is a cycle",
}
Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\PLAN_VALIDATION.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False))
