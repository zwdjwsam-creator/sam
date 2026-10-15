# -*- coding: utf-8 -*-
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
import r9_source_contract as source_contract

rows = []
for name in source_contract.CODE_FILES:
    path = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013") / name
    data = path.read_bytes()
    rows.append({"name": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
out = {
    "code_digest": source_contract.code_digest(),
    "files": rows,
}
dest = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\CODE_HASHES.json")
dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(out["code_digest"])
print(len(rows))
