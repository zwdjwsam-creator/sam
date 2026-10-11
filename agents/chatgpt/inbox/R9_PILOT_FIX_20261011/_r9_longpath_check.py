# -*- coding: utf-8 -*-
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\LAN_SHARE_REPORT")
import r9_pilot_common_r9fix as C

con = sqlite3.connect(r"C:\LAN_SHARE_REPORT\BLACKBOX_R9_MANIFEST\PILOT_1G_MANIFEST.sqlite")
root = Path(r"E:\BLACKBOX_MANIFEST_PILOT_R9_1G")
missing_plain = 0
missing_long = 0
exist_long_only = 0
samples = []
for (rel,) in con.execute("select source_relative_path from hardlink_paths"):
    dp = C.dest_under_root(root, rel)
    plain = dp.exists()
    longp = C.to_win_long_path(str(dp))
    # GetFileAttributesW via ctypes
    import ctypes
    from ctypes import wintypes

    INVALID = 0xFFFFFFFF
    attrs = ctypes.windll.kernel32.GetFileAttributesW(longp)
    long_ok = attrs != INVALID
    if not plain:
        missing_plain += 1
    if not long_ok:
        missing_long += 1
        if len(samples) < 5:
            samples.append((rel, str(dp), len(str(dp))))
    if (not plain) and long_ok:
        exist_long_only += 1

print("missing_plain", missing_plain)
print("missing_long", missing_long)
print("exist_long_only", exist_long_only)
print("samples_still_missing_long:")
for s in samples:
    print(s)

# entity primary
miss_ent_plain = miss_ent_long = 0
for (eid,) in con.execute("select entity_id from entities"):
    row = con.execute(
        "select source_relative_path from hardlink_paths where entity_id=? order by source_relative_path limit 1",
        (eid,),
    ).fetchone()
    dp = C.dest_under_root(root, row[0])
    if not dp.exists():
        miss_ent_plain += 1
    attrs = ctypes.windll.kernel32.GetFileAttributesW(C.to_win_long_path(str(dp)))
    if attrs == INVALID:
        miss_ent_long += 1
print("entities_primary_missing_plain", miss_ent_plain)
print("entities_primary_missing_long", miss_ent_long)
