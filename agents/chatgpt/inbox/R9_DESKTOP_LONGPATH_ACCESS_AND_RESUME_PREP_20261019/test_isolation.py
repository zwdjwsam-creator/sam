# -*- coding: utf-8 -*-
import sqlite3
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_LONGPATH_ACCESS_AND_RESUME_PREP_20261019")
from r9_temp_name import temp_path, api_chars
from r9_state_migrate import migrate_copy, REAL_STATE

short = r"E:\BLACKBOX\data\one.txt"
assert temp_path(short) == short + ".partial"

parts = ["E:", "BLACKBOX"]
while True:
    candidate = "\\".join(parts + ["n" * 200 + ".json"])
    if api_chars(candidate + ".partial") > 32760:
        long_dest = candidate
        break
    parts.append("d" * 40)
bounded = temp_path(long_dest)
assert bounded != long_dest + ".partial"
assert api_chars(bounded) <= 32760
assert len(bounded.rsplit("\\", 1)[1]) <= 255

root = Path(tempfile.mkdtemp(prefix="r9_temp_", dir=r"C:\LAN_SHARE_REPORT\R9_DESKTOP_LONGPATH_ACCESS_AND_RESUME_PREP_20261019"))
folder = root / "parent"
folder.mkdir()
dest = folder / "sample.txt"
dest.write_bytes(b"abc")
temp = Path(temp_path(str(dest)))
temp.write_bytes(b"abc")
temp.replace(dest)
assert dest.read_bytes() == b"abc"
assert not temp.exists()

state_src = root / "synthetic.sqlite"
state_dst = root / "synthetic_copy.sqlite"
conn = sqlite3.connect(state_src)
conn.execute("CREATE TABLE run_bind (run_id TEXT, plan_digest TEXT, inputs_digest TEXT, code_digest TEXT, dest_volume TEXT, dest_root TEXT)")
conn.execute("CREATE TABLE stage (item_key TEXT, kind TEXT, phase TEXT, dest_path TEXT, sha256 TEXT, file_id TEXT, volume_serial TEXT, object_type TEXT, link_target TEXT, logical_size INTEGER, parent_key TEXT)")
conn.execute("INSERT INTO run_bind VALUES ('OLD', 'plan', 'plan', 'olddigest', '2694002743', 'E:\\BLACKBOX')")
conn.execute("INSERT INTO stage VALUES ('k1', 'entity', 'DONE', 'E:\\BLACKBOX\\a', 'abc', '1', '2387166462', 'file', '', 3, '')")
conn.commit()
conn.close()
result = migrate_copy(state_src, state_dst, "NEW", "newdigest")
assert result["rows"] == 1
original = sqlite3.connect(f"file:{state_src.resolve().as_posix()}?mode=ro", uri=True)
assert original.execute("SELECT run_id, code_digest FROM run_bind").fetchone() == ("OLD", "olddigest")
original.close()
copied = sqlite3.connect(f"file:{state_dst.resolve().as_posix()}?mode=ro", uri=True)
assert copied.execute("SELECT run_id, code_digest FROM run_bind").fetchone() == ("NEW", "newdigest")
copied.close()
try:
    migrate_copy(REAL_STATE, root / "nope.sqlite", "X", "Y")
    raise SystemExit("real state was not refused")
except RuntimeError as exc:
    assert str(exc) == "REFUSING_REAL_STATE"
print("ISOLATION_OK")
print("fixture", root)
