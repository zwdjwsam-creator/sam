# -*- coding: utf-8 -*-
"""沙盘：用 PENDING v2 的 build_identity 在现有 release 上只读复算，验 commit_id 不变 + rcid 开销。

不调用 commit()/publish()，不写 COMMIT.json。
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import time

BASE = pathlib.Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
V2 = pathlib.Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion"
                  r"\sam_led_rectification\_sam_pending\PENDING_candidate_commit_v2.py")
REL_ROOT = BASE / "candidate" / "cc_out" / "releases"

spec = importlib.util.spec_from_file_location("cc_v2_sandbox", V2)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

print("v2 loaded")
print("REQUIRED_PRODUCTS =", getattr(mod, "REQUIRED_PRODUCTS", None))
print("has release_content_digest :", hasattr(mod, "release_content_digest"))
print("COMMIT_FILE =", mod.COMMIT_FILE)
print()

out = {"commit_file_constant": str(mod.COMMIT_FILE),
       "required_products": list(getattr(mod, "REQUIRED_PRODUCTS", ())),
       "per_release": []}

for rel in sorted([d for d in REL_ROOT.iterdir() if d.is_dir()], key=lambda d: d.name):
    t0 = time.time()
    try:
        ident = mod.build_identity(rel)
        dt_build = time.time() - t0
        t1 = time.time()
        rcd = mod.release_content_digest(rel)
        dt_rcd = time.time() - t1
        rec = {
            "release": rel.name,
            "commit_id": ident.get("commit_id"),
            "release_content_id": ident.get("release_content_id"),
            "rcid_direct": rcd.get("release_content_id"),
            "products_in_identity": len(ident.get("products") or {}),
            "products_present": len(rcd.get("products_present") or {}),
            "identity_keys": sorted(ident.keys()),
            "build_identity_sec": round(dt_build, 2),
            "rcid_sec": round(dt_rcd, 2),
        }
    except Exception as e:  # noqa: BLE001
        rec = {"release": rel.name, "error": f"{type(e).__name__}: {e}"[:300]}
    out["per_release"].append(rec)
    print(json.dumps(rec, ensure_ascii=False, indent=1))

# 关键判定：commit_id 是否仍等于已记录值
KNOWN = "572619c945d48f1b14f41c6f8c94b66dbacab00da4303366bcf2687ff8ec0876"
cids = {r.get("commit_id") for r in out["per_release"] if r.get("commit_id")}
out["commit_id_unchanged"] = (cids == {KNOWN})
out["distinct_commit_ids"] = len(cids)
rcids = [r.get("release_content_id") for r in out["per_release"] if r.get("release_content_id")]
out["distinct_rcids"] = len(set(rcids))

print()
print(f"期望 commit_id       = {KNOWN[:16]}")
print(f"实测 distinct cids   = {len(cids)}  -> {[c[:16] for c in cids]}")
print(f"COMMIT_ID_UNCHANGED  = {out['commit_id_unchanged']}")
print(f"distinct rcid        = {len(set(rcids))} of {len(rcids)}")
print(f"total rcid time      = {sum(r.get('rcid_sec',0) for r in out['per_release']):.1f}s")

dest = V2.parents[1] / "DESKTOP_RCID_SANDBOX_R1.json"
dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("saved", dest.name)
