# -*- coding: utf-8 -*-
"""沙盘只读：验 scan_equivalent_dirs 修复效果 + HOST_SCOPE_MISMATCH 守卫。"""
from __future__ import annotations

import importlib.util
import json
import pathlib

BASE = pathlib.Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
V2 = BASE / "sam_led_rectification" / "_sam_pending" / "PENDING_candidate_commit_v2.py"
spec = importlib.util.spec_from_file_location("cc_v2_probe", V2)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

commit = json.loads((BASE / "candidate" / "cc_commit" / "COMMIT.json").read_text(encoding="utf-8"))
ref = commit["release_root"]

# 解析 identity（新回落逻辑）
scr = prid = None
src = {}
cp = pathlib.Path(commit.get("checkpoint_path", ""))
if cp.is_file():
    ck = json.loads(cp.read_text(encoding="utf-8"))
    idt = ck.get("identity") or {}
    scr = idt.get("source_cleaning_release")
    prid = idt.get("parent_release_id")
    src = {"commit_json_identity": commit.get("identity") is not None,
           "checkpoint_identity": True}
else:
    src = {"checkpoint_missing": True}

print("=== identity 来源 ===")
print("  COMMIT.json 有 identity 键 :", commit.get("identity") is not None)
print("  checkpoint 有 identity 键  :", src.get("checkpoint_identity"))
print("  source_cleaning_release    :", scr)
print("  parent_release_id          :", prid)
print()

print("=== scan_equivalent_dirs（修复后）===")
sc = mod.scan_equivalent_dirs(ref, asof=commit.get("asof"),
                              source_cleaning_release=scr,
                              parent_release_id=prid)
print(json.dumps(sc, ensure_ascii=False, indent=1)[:1800])
n = sc.get("equivalent_count", sc.get("count"))
print(f"\n  equivalent count = {n}")

print("\n=== HOST_SCOPE_MISMATCH 守卫（Q:\\nonexistent）===")
try:
    r = mod.scan_equivalent_dirs(r"Q:\nonexistent", asof=commit.get("asof"),
                                 source_cleaning_release=scr, parent_release_id=prid)
    print(json.dumps(r, ensure_ascii=False)[:600])
except Exception as e:  # noqa: BLE001
    print(f"  raised {type(e).__name__}: {str(e)[:220]}")

out = {"identity_from_checkpoint": src, "scan": sc, "equiv_count": n,
       "ref": ref, "commit_id": commit.get("commit_id")}
dest = BASE / "sam_led_rectification" / "DESKTOP_SCAN_EQUIV_PROBE_R1.json"
dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nsaved", dest.name)
