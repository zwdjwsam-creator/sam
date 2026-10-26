# -*- coding: utf-8 -*-
"""台机自证：提交模块身份 / 产品覆盖范围 / 调用版本。只读，不写任何产品。"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import struct
import sys

E2E = pathlib.Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
TOOLS = E2E / "tools"
RECT = E2E / "sam_led_rectification"
ARCH = E2E / "candidate" / "cc_out" / "_archive_r12_round_20261026_181002"
CO = E2E / "candidate" / "cc_out" / "releases"

R: dict = {"schema": "DESKTOP_COMMIT_MODULE_AND_COVERAGE_AUDIT_R1"}


def sha(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def rows_total(p: pathlib.Path) -> int:
    """长路径安全：对每个文件路径都加 \\\\?\\ 前缀（只给 root 加不够——嵌套层已经超 260）。"""
    import os
    import pyarrow.parquet as pq

    def lp(s: str) -> str:
        s = os.path.abspath(s)
        if s.startswith("\\\\?\\"):
            return s
        return "\\\\?\\" + s if len(s) >= 150 else s

    n, failed = 0, []

    def onerr(e: OSError) -> None:
        # os.walk 默认静默吞掉 scandir 错误 → 少读整棵子树而"看起来成功"。
        failed.append({"walk_error": f"{type(e).__name__}: {e}"[:160]})

    for dirpath, _dn, fns in os.walk(lp(str(p)), onerror=onerr):
        for fn in fns:
            if not fn.lower().endswith(".parquet"):
                continue
            f = lp(os.path.join(dirpath, fn))
            try:
                n += int(pq.ParquetFile(f).metadata.num_rows)
            except Exception as e:  # noqa: BLE001
                failed.append({"file": f, "len": len(f), "error": f"{type(e).__name__}: {e}"[:120]})
    if failed:
        R.setdefault("_row_count_failures", {})[p.name] = {
            "count": len(failed), "sample": failed[:3]}
    return n


def classify(p: pathlib.Path) -> dict:
    """判断该产品是实体目录还是 junction（借用生产数据）。"""
    out = {"kind": "REAL_DIR", "junction_targets": []}
    import os
    for dirpath, dirnames, _fns in os.walk(p):
        for d in list(dirnames):
            fp = os.path.join(dirpath, d)
            try:
                if os.path.islink(fp) or (hasattr(os.path, "isjunction") and os.path.isjunction(fp)):
                    tgt = os.path.realpath(fp)
                    out["junction_targets"].append({"at": os.path.relpath(fp, p), "target": tgt})
            except OSError:
                pass
        if len(out["junction_targets"]) >= 6:
            break
    if out["junction_targets"]:
        out["kind"] = "CONTAINS_JUNCTION"
    return out


# ---------------------------------------------------------------- 1. 模块身份
sys.path.insert(0, str(TOOLS))
import candidate_commit as cc  # noqa: E402

mod_path = pathlib.Path(cc.__file__)
pyc = TOOLS / "__pycache__" / "candidate_commit.cpython-312.pyc"
pyc_src_size = struct.unpack("<I", pyc.read_bytes()[12:16])[0] if pyc.exists() else None

copies = []
for root in (pathlib.Path(r"E:\BLACKBOX\任务"), pathlib.Path(r"E:\BLACKBOX\_OPS"),
             pathlib.Path(r"E:\BLACKBOX\脚本")):
    for p in root.rglob("candidate_commit*.py"):
        copies.append({"path": str(p), "bytes": p.stat().st_size, "sha16": (sha(p) or "")[:16],
                       "is_live_module": p.resolve() == mod_path.resolve()})

R["module_identity"] = {
    "loaded_file": str(mod_path),
    "loaded_sha256_16": (sha(mod_path) or "")[:16],
    "loaded_bytes": mod_path.stat().st_size,
    "pyc_source_size_field": pyc_src_size,
    "pyc_matches_source": pyc_src_size == mod_path.stat().st_size,
    "import_sites": [],  # filled below
    "tools_is_package": (TOOLS / "__init__.py").exists(),
    "tools_init_bytes": (TOOLS / "__init__.py").stat().st_size
    if (TOOLS / "__init__.py").exists() else None,
    "all_copies_on_disk": copies,
    "shadowing_check": {
        "BB_脚本_on_sys_path": True,
        "candidate_commit_in_BB_脚本": any(str(p).startswith(r"E:\BLACKBOX\脚本") for p in
                                        [c["path"] for c in copies]),
    },
}

import re  # noqa: E402

sites = []
for f in list(TOOLS.glob("*.py")) + [E2E / "run_connected_pipeline.py"]:
    if not f.is_file():
        continue
    for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if re.search(r"^\s*(import candidate_commit|from candidate_commit)", line):
            sites.append({"file": f.name, "line": i, "code": line.strip()})
R["module_identity"]["import_sites"] = sites

# ---------------------------------------------------------------- 2. 产品覆盖
rel = max([d for d in CO.iterdir() if d.is_dir() and (d / "RELEASE.json").exists()],
          key=lambda d: d.stat().st_mtime) if any(
    (d / "RELEASE.json").exists() for d in CO.iterdir() if d.is_dir()) else None
# 用 deliverable 里绑定的那个更准
dg = json.loads((E2E / "deliverables" / "CONNECTED_PIPELINE.json").read_text(encoding="utf-8"))
bound = pathlib.Path(dg["stages"]["compiler"]["bound_release_root"])
if bound.is_dir():
    rel = bound

release_json = json.loads((rel / "RELEASE.json").read_text(encoding="utf-8"))
seal = json.loads((rel / "SEAL.json").read_text(encoding="utf-8"))
commit = json.loads((E2E / "candidate" / "cc_commit" / "COMMIT.json").read_text(encoding="utf-8"))

META = {"RELEASE.json", "SEAL.json", "_qa", "CURRENT_POINTER_COPY.json",
        "PRODUCT_CAPABILITY_FACTS_CANDIDATE.json"}
present = []
for d in sorted(rel.iterdir()):
    if not d.is_dir() or d.name in META:
        continue
    cls = classify(d)
    present.append({"product": d.name, "rows_total": rows_total(d),
                    "kind": cls["kind"], "junction_targets": cls["junction_targets"],
                    "in_identity": d.name in cc.REQUIRED_PRODUCTS,
                    "in_commit_json": d.name in (commit.get("products") or {})})

# 编译器自己的 required 列表（写入 SEAL 前置条件）
comp_src = pathlib.Path(r"E:\BLACKBOX\任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1"
                        r"\cache_compiler_tip_rebase_from_current_r1.py").read_text(
    encoding="utf-8", errors="replace")
m = re.search(r"required = \[(.*?)\]", comp_src, re.S)
compiler_required = re.findall(r'"([A-Z0-9_]+)"', m.group(1)) if m else []

identity_products = list(cc.REQUIRED_PRODUCTS)
covered = [p for p in present if p["in_identity"]]
uncovered = [p for p in present if not p["in_identity"]]

R["product_coverage"] = {
    "release": rel.name,
    "identity_schema": cc.build_identity(rel)["content_scope"]["hashed"],
    "identity_products_hash_scope": identity_products,
    "compiler_required_products": compiler_required,
    "products_present_in_release": present,
    "count_present": len(present),
    "count_in_identity": len(covered),
    "count_uncovered": len(uncovered),
    "uncovered_products": [p["product"] for p in uncovered],
    "uncovered_rows_total": sum(p["rows_total"] for p in uncovered),
    "products_borrowing_production": [p for p in present if p["kind"] == "CONTAINS_JUNCTION"],
    "row_count_failures": R.get("_row_count_failures", {}),
    "seal_all_pass": seal.get("all_pass"),
    "seal_required_missing": release_json.get("formal_required_missing"),
    "verdict_scope_note": (
        "verify(deep=True) 只遍历 COMMIT.json['products']；不在其中的产品既不参与 "
        "commit_id，也不参与 payload_matches。"),
}

# ---------------------------------------------------------------- 3. ETF/指数 动态证据
def prod_digest(d: pathlib.Path) -> dict:
    return cc.product_digest(d)


old_rels = [d for d in ARCH.iterdir() if d.is_dir() and (d / "INDEX_DAILY_R1").exists()]
dyn = []
for pid in ("ETF_DAILY_PIT_R1", "INDEX_DAILY_R1"):
    if not (rel / pid).exists():
        continue
    new_d = prod_digest(rel / pid)
    for d in old_rels[:2]:
        if not (d / pid).exists():
            continue
        o = prod_digest(d / pid)
        dyn.append({"product": pid, "old_release": d.name[-6:],
                    "old_rows": o["rows"], "new_rows": new_d["rows"],
                    "content_changed": o["sha256"] != new_d["sha256"],
                    "old_sha16": (o["sha256"] or "")[:16],
                    "new_sha16": (new_d["sha256"] or "")[:16]})
R["dynamic_evidence"] = {
    "pairs": dyn,
    "note": "若 content_changed=True 而两个 release 的 commit_id 相同，即证明身份盲区。",
}

# commit_id 是否相同（同一 identity 覆盖集下）
ids = {}
for d in [rel, *old_rels]:
    try:
        ids[d.name] = cc.build_identity(d)["commit_id"][:16]
    except Exception as e:  # noqa: BLE001
        ids[d.name] = f"ERR {type(e).__name__}"
R["commit_ids_by_release"] = ids
R["commit_ids_all_equal"] = len(set(ids.values())) == 1

# ---------------------------------------------------------------- 4. 判据
checks = {}
checks["single_importable_module"] = sum(1 for c in copies if c["bytes"] > 0) == 1
checks["pyc_matches_source"] = R["module_identity"]["pyc_matches_source"]
checks["no_package_shadowing"] = not any(
    "tools.candidate_commit" in s["code"] for s in sites)
checks["identity_covers_all_release_products"] = len(uncovered) == 0
checks["identity_covers_compiler_required"] = set(compiler_required) <= set(identity_products)
R["checks"] = checks
R["blockers"] = [k for k, v in checks.items() if not v]
R["status"] = "PASS" if not R["blockers"] else "GAPS_FOUND"

out = RECT / "DESKTOP_COMMIT_MODULE_AND_COVERAGE_AUDIT.json"
out.write_text(json.dumps(R, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps({"status": R["status"], "blockers": R["blockers"],
                  "release": rel.name,
                  "present": len(present), "covered": len(covered),
                  "uncovered": len(uncovered)}, ensure_ascii=False, indent=2))
print("\n--- module ---")
for k, v in R["module_identity"].items():
    if k != "all_copies_on_disk":
        print(f"  {k}: {v}")
print(f"\n--- coverage ---")
print(f"  identity covers      : {identity_products}")
print(f"  compiler required    : {compiler_required}")
print(f"  missing from identity: {sorted(set(compiler_required) - set(identity_products))}")
print(f"  {'product':<34}{'rows_total':>14}  {'kind':<20} in_identity")
for p in present:
    print(f"  {p['product']:<34}{p['rows_total']:>14}  {p['kind']:<20} {p['in_identity']}")
print("\n  --- products borrowing production bytes via junction ---")
for p in present:
    if p["kind"] == "CONTAINS_JUNCTION":
        for j in p["junction_targets"][:3]:
            print(f"   {p['product']} :: {j['at']}  ->  {j['target'][:110]}")
if R.get("_row_count_failures"):
    print("\n  --- row-count failures (long path) ---")
    for k, v in R["_row_count_failures"].items():
        print(f"   {k}: {v['count']} unreadable, e.g. len={v['sample'][0]['len']} "
              f"{v['sample'][0]['error'][:60]}")
print("\n--- dynamic (same commit_id, changed content?) ---")
for d in dyn:
    print(f"  {d['product']:<22} old={d['old_rows']:>9} new={d['new_rows']:>9} "
          f"changed={d['content_changed']}  old_sha={d['old_sha16']} new_sha={d['new_sha16']}")
print("\n  commit_ids:", R["commit_ids_by_release"], "all_equal=", R["commit_ids_all_equal"])
print("\nsaved", out.name)
