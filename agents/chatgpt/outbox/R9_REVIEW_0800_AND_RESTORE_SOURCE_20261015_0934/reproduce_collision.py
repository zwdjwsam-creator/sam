"""Read-only audit fixture. No target I/O; run with reviewed modules on PYTHONPATH."""
import json
import sqlite3
import r9_formal_chain as chain

db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE paths(path TEXT PRIMARY KEY,is_dir INTEGER,is_reparse INTEGER)")
db.execute("CREATE TABLE links(path TEXT,target TEXT,migrated_link_path TEXT,migrated_target TEXT)")
db.executemany("INSERT INTO paths VALUES(?,?,?)", [
    (r"E:\BLACKBOX", 1, 0),
    (r"E:\BLACKBOX\A", 1, 0),
    (r"E:\BLACKBOX\a", 0, 0),
])
result = chain.audit_full_plan(db)
print(json.dumps(result, sort_keys=True))
assert not result["ok"], "CASE_INSENSITIVE_FILE_DIRECTORY_COLLISION_NOT_REJECTED"
