#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 SAM 答复回退 manifest 语义字段 R1（默认 dry-run）。

SAM 裁决:
  Q2 -> 删 US_MARKET.FIXED_PATHS.alignment_csv（0 消费者）；保留 alignment（497 行派生写出）
  Q3 -> DISCOVERY_ASOF 保持 09-24（运行日口径），不改回 09-25
  Q9 -> 回退语义字段让 DG1 回到 DG1-7fd2bf71…

本脚本只做三件（其余字段不动）:
  1. 删 alignment_csv
  2. US_FINE_GRAINED_STATUS / A_SHARE_MAPPING_PRIOR_STATUS 改由**实际产物**派生（不是硬写 PASS）
  3. 重算 DG1，报"与源机是否已一致 / 还剩哪些键"

不写生产 CURRENT，除非 --apply。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
TASK = ROOT / "任务" / "BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1"
OUT = TASK / "输出"
CAND = TASK / "候选" / "CURRENT"
BAK = TASK / "备份"
SRC_MANIFEST = Path(
    r"\\192.168.100.2\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024"
    r"\end_to_end_completion\source_workflow_from_SAM\config\研究系统\数据平面\CURRENT"
    r"\DAILY_DATA_MANIFEST_CURRENT.json"
)
PROD_MANIFEST = ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_DATA_MANIFEST_CURRENT.json"
PROD_PLANE = ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_DATA_PLANE_CURRENT.json"
PROD_PACK = ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_RESEARCH_INPUT_PACK_CURRENT.json"
FG_ROOT = ROOT / "数据" / "美国市场" / "细粒度利润池" / "CURRENT"
FG_FLOW = ROOT / "运行" / "BLACKBOX_US_MARKET_FINE_GRAINED_FLOW_PROFIT_POOL_CURRENT.json"

META_KEYS = ("DATA_GENERATION_ID", "MANIFEST_SEMANTIC_SHA256", "DATA_GENERATION_ID_ISSUER", "BUILD_TIME")


def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S%z")


def stamp() -> str:
    return datetime.now(CN).strftime("%Y%m%d_%H%M%S")


def load(p: Path) -> Any:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8-sig"))


def dump(p: Path, o: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")


def atomic_write(p: Path, o: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + f".tmp_revert_{os.getpid()}")
    tmp.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def dg1(mod: Any) -> str | None:
    sys.path.insert(0, str(ROOT / "脚本"))
    from blackbox_run_identity_r1 import attach_data_generation_to_manifest

    body = {k: v for k, v in mod.items() if k not in META_KEYS}
    return attach_data_generation_to_manifest(body).get("DATA_GENERATION_ID")


def flat(o: Any, pre: str = "") -> dict[str, Any]:
    r: dict[str, Any] = {}
    if isinstance(o, dict):
        for k, v in o.items():
            r.update(flat(v, f"{pre}.{k}"))
    elif isinstance(o, list):
        r[pre] = json.dumps(o, ensure_ascii=False)
    else:
        r[pre] = o
    return r


def derive_fine_grained() -> dict[str, Any]:
    """由实际产物派生，不硬写。"""
    flow = load(FG_FLOW)
    snap = load(FG_ROOT / "US_FINE_GRAINED_SNAPSHOT_CURRENT.json")
    mapping_p = FG_ROOT / "A_SHARE_MAPPING_PRIOR_CURRENT.json"
    fine_status = flow.get("STATUS") or snap.get("STATUS") or "NOT_RUN"
    mapping_status = "PASS" if mapping_p.exists() and mapping_p.stat().st_size > 0 else "SKIPPED"
    return {
        "us_fine_grained_status": fine_status,
        "a_share_mapping_prior_status": mapping_status,
        "evidence": {
            "flow_current": {"path": str(FG_FLOW), "exists": FG_FLOW.exists(),
                             "bytes": FG_FLOW.stat().st_size if FG_FLOW.exists() else 0,
                             "STATUS": flow.get("STATUS")},
            "snapshot_current": {"path": str(FG_ROOT / "US_FINE_GRAINED_SNAPSHOT_CURRENT.json"),
                                 "exists": (FG_ROOT / "US_FINE_GRAINED_SNAPSHOT_CURRENT.json").exists(),
                                 "STATUS": snap.get("STATUS")},
            "mapping_prior": {"path": str(mapping_p), "exists": mapping_p.exists(),
                              "bytes": mapping_p.stat().st_size if mapping_p.exists() else 0},
        },
    }


def build(drop_alignment_csv: bool = True, force_fine_pass: bool = True) -> dict[str, Any]:
    prod = load(PROD_MANIFEST)
    src = load(SRC_MANIFEST)
    mod = json.loads(json.dumps(prod))
    acts: list[str] = []

    fg = derive_fine_grained()
    fpath = mod.setdefault("US_MARKET", {}).setdefault("FIXED_PATHS", {})
    if drop_alignment_csv and "alignment_csv" in fpath:
        fpath.pop("alignment_csv")
        acts.append("删除 US_MARKET.FIXED_PATHS.alignment_csv（0 消费者，Q2）")
    if "alignment" not in fpath:
        # 由 daily_lanes.session_alignment 派生（代码 461 读、497 写）
        lanes = load(ROOT / "研究系统" / "数据平面" / "CONFIG" / "daily_lanes.json")
        sa = (lanes.get("lanes", {}).get("F_US_MARKET_STATE_INCREMENTAL") or {}).get("session_alignment")
        if sa:
            fpath["alignment"] = sa
            acts.append("补回 US_MARKET.FIXED_PATHS.alignment（= daily_lanes.session_alignment）")
    if force_fine_pass:
        old = (mod["US_MARKET"].get("US_FINE_GRAINED_STATUS"), mod["US_MARKET"].get("A_SHARE_MAPPING_PRIOR_STATUS"))
        mod["US_MARKET"]["US_FINE_GRAINED_STATUS"] = fg["us_fine_grained_status"]
        mod["US_MARKET"]["A_SHARE_MAPPING_PRIOR_STATUS"] = fg["a_share_mapping_prior_status"]
        acts.append(
            f"US_MARKET 细粒度状态由产物派生 {old} -> "
            f"{(fg['us_fine_grained_status'], fg['a_share_mapping_prior_status'])}"
        )

    new_dg1 = dg1(mod)
    # 关键：meta 字段必须随语义一起重戳，否则写回的是旧 DG1（回读会不一致）
    if new_dg1:
        mod["DATA_GENERATION_ID"] = new_dg1
        mod["MANIFEST_SEMANTIC_SHA256"] = new_dg1.split("-", 1)[1]
        mod["DATA_GENERATION_ID_ISSUER"] = "DATA_PLANE"
    src_dg1 = src.get("DATA_GENERATION_ID")
    fs, fm = flat(src), flat(mod)
    residual = [
        {"key": k, "source": fs.get(k), "desktop": fm.get(k)}
        for k in sorted(set(fs) | set(fm))
        if fs.get(k) != fm.get(k) and k not in (".DATA_GENERATION_ID", ".MANIFEST_SEMANTIC_SHA256", ".BUILD_TIME")
    ]
    return {
        "manifest": mod,
        "actions": acts,
        "new_dg1": new_dg1,
        "source_dg1": src_dg1,
        "dg1_equal": new_dg1 == src_dg1,
        "residual_diff_keys": residual,
        "fine_grained_evidence": fg["evidence"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--keep-fine-status", action="store_true", help="不按产物派生细粒度状态（只删 alignment_csv）")
    args = ap.parse_args()

    r = build(drop_alignment_csv=True, force_fine_pass=not args.keep_fine_status)
    print("== actions ==")
    for a in r["actions"]:
        print("  -", a)
    print("\n== DG1 ==")
    print("  source :", r["source_dg1"])
    print("  desktop:", r["new_dg1"])
    print("  equal  :", r["dg1_equal"])
    print("\n== residual diff vs source ==")
    for d in r["residual_diff_keys"]:
        print(f"  {d['key']}: source={str(d['source'])[:70]} | desktop={str(d['desktop'])[:70]}")
    print("\n== fine grained evidence ==")
    print(json.dumps(r["fine_grained_evidence"], ensure_ascii=False, indent=2))

    CAND.mkdir(parents=True, exist_ok=True)
    dump(CAND / "DAILY_DATA_MANIFEST_AFTER_Q1_Q9.json", r["manifest"])
    dump(OUT / "DG1_REVERT_PROBE.json", {k: v for k, v in r.items() if k != "manifest"})

    if not args.apply:
        print("\nDRY-RUN（加 --apply 写生产 CURRENT）")
        return 0

    ts = stamp()
    bakdir = BAK / f"revert_{ts}"
    for p in (PROD_MANIFEST, PROD_PLANE, PROD_PACK):
        if p.exists():
            b = bakdir / p.relative_to(ROOT)
            b.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, b)
    atomic_write(PROD_MANIFEST, r["manifest"])
    plane = load(PROD_PLANE)
    plane["BUILD_TIME"] = now_cn()
    plane["DATA_GENERATION_ID"] = r["new_dg1"]
    plane["DATA_MANIFEST_ID"] = r["manifest"]["manifest_id"]
    atomic_write(PROD_PLANE, plane)

    # 回读
    back = load(PROD_MANIFEST)
    verify = {
        "dg1": back.get("DATA_GENERATION_ID"),
        "dg1_equal_source": back.get("DATA_GENERATION_ID") == r["source_dg1"],
        "alignment_csv_present": "alignment_csv" in (back.get("US_MARKET", {}).get("FIXED_PATHS") or {}),
        "fine_status": back.get("US_MARKET", {}).get("US_FINE_GRAINED_STATUS"),
        "mapping_status": back.get("US_MARKET", {}).get("A_SHARE_MAPPING_PRIOR_STATUS"),
        "plane_dg1": plane.get("DATA_GENERATION_ID"),
    }
    led = {
        "schema": "BLACKBOX_DG1_FIELD_REVERT_LEDGER_R1",
        "applied_at_cn": now_cn(),
        "backup_dir": str(bakdir),
        "actions": r["actions"],
        "verify": verify,
        "residual_diff_keys": r["residual_diff_keys"],
    }
    dump(OUT / f"DG1_FIELD_REVERT_LEDGER_{ts}.json", led)
    dump(OUT / "DG1_FIELD_REVERT_LEDGER_CURRENT.json", led)
    print("\n== applied ==")
    print(json.dumps(verify, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
