# -*- coding: utf-8 -*-
"""决定性测试：对每个 cc_out release 重算 product_digest，定位 COMMIT 是否锚在旧(修前)内容。"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\tools")
import candidate_commit as cc  # noqa: E402

E2E = pathlib.Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
CO = E2E / "candidate" / "cc_out" / "releases"

print("=== COMMIT.json current ===")
cur = json.loads((E2E / "candidate" / "cc_commit" / "COMMIT.json").read_text(encoding="utf-8"))
print(" commit_id      =", cur["commit_id"])
print(" release_id     =", cur["release_id"])
print(" release_root   =", cur["release_root"])
print(" exists         =", pathlib.Path(cur["release_root"]).exists())
print(" products rows  =", {k: v["rows"] for k, v in cur["products"].items()})
print(" products sha   =", {k: v["sha256"][:16] for k, v in cur["products"].items()})
print()

print("=== each release on disk ===")
rows = []
for d in sorted(CO.iterdir()):
    if not d.is_dir():
        continue
    try:
        rj = json.loads((d / "RELEASE.json").read_text(encoding="utf-8"))
        rid = rj.get("cache_release_id")
    except Exception:
        rid = None
    try:
        pd = cc.product_digest(d / "STOCK_DAILY_PIT_R1")
    except Exception as e:  # noqa: BLE001
        pd = {"rows": None, "sha256": f"ERR {type(e).__name__}", "parts": 0}
    try:
        ident = cc.build_identity(d)
        cid = ident["commit_id"]
    except Exception as e:  # noqa: BLE001
        cid = f"ERR {type(e).__name__}: {str(e)[:40]}"
    f26 = d / "STOCK_DAILY_PIT_R1" / "year=2026" / "part_2026.parquet"
    r2026 = None
    if f26.exists():
        import pyarrow.parquet as pq
        r2026 = pq.ParquetFile(f26).metadata.num_rows
    rows.append((d.name, rid, pd.get("rows"), r2026, pd.get("sha256", "")[:16], str(cid)[:16]))
    print(f" {d.name[:58]:<58} rows_tot={pd.get('rows')} r2026={r2026}")
    print(f"    cache_release_id={rid}")
    print(f"    payload_sha16={pd.get('sha256','')[:16]}  commit_id16={str(cid)[:16]}")

print()
print("=== verdict ===")
match = [r for r in rows if r[4] == cur["products"]["STOCK_DAILY_PIT_R1"]["sha256"][:16]]
print(f" releases whose payload == COMMIT payload: {[m[0] for m in match]}")
print(f" releases with r2026 == 959896: {[r[0] for r in rows if r[3] == 959896]}")
