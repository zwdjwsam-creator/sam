#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SAM 答复执行后的终态只读核验 R1（不写任何生产文件）。"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
TASK = ROOT / "任务" / "BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1"
OUT = TASK / "输出"
MANIFEST = ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_DATA_MANIFEST_CURRENT.json"
PLANE = ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_DATA_PLANE_CURRENT.json"
PACK = ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_RESEARCH_INPUT_PACK_CURRENT.json"
SRC = Path(r"\\192.168.100.2\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion"
           r"\source_workflow_from_SAM\config\研究系统\数据平面\CURRENT\DAILY_DATA_MANIFEST_CURRENT.json")
META = ("DATA_GENERATION_ID", "MANIFEST_SEMANTIC_SHA256", "DATA_GENERATION_ID_ISSUER", "BUILD_TIME")


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8-sig"))


def flat(o, pre="") -> dict:
    r = {}
    if isinstance(o, dict):
        for k, v in o.items():
            r.update(flat(v, f"{pre}.{k}"))
    elif isinstance(o, list):
        r[pre] = json.dumps(o, ensure_ascii=False)
    else:
        r[pre] = o
    return r


def main() -> int:
    sys.path.insert(0, str(ROOT / "脚本"))
    from blackbox_run_identity_r1 import attach_data_generation_to_manifest

    man, plane, pack = load(MANIFEST), load(PLANE), load(PACK)
    src = load(SRC)

    dg1 = attach_data_generation_to_manifest({k: v for k, v in man.items() if k not in META})["DATA_GENERATION_ID"]

    def walk(o, p=""):
        out = []
        if isinstance(o, dict):
            for k, v in o.items():
                out += walk(v, f"{p}.{k}" if p else k)
        elif isinstance(o, str) and o.startswith("E:"):
            out = [(p, o)]
        return out

    pm = load(ROOT / "研究系统" / "数据平面" / "CONFIG" / "DATA_PLANE_PATH_MAP.json")
    ents = walk(pm)
    missing = [(k, v) for k, v in ents if not Path(v).exists()]

    cur = load(ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json")
    croot = Path(cur["release_root"])
    n_dirs = sum(1 for c in croot.iterdir() if c.is_dir())
    n_files = sum(1 for c in croot.iterdir() if c.is_file())

    fs, fm = flat(src), flat(man)
    residual = [
        {"key": k, "source": fs.get(k), "desktop": fm.get(k)}
        for k in sorted(set(fs) | set(fm))
        if fs.get(k) != fm.get(k)
        and k not in (".DATA_GENERATION_ID", ".MANIFEST_SEMANTIC_SHA256", ".BUILD_TIME")
    ]

    checks = {
        "DG1_recomputed_matches_file": dg1 == man.get("DATA_GENERATION_ID"),
        "DG1_file_matches_plane": man.get("DATA_GENERATION_ID") == plane.get("DATA_GENERATION_ID"),
        "manifest_id_matches_plane": man.get("manifest_id") == plane.get("DATA_MANIFEST_ID"),
        "pack_id_matches_manifest": pack.get("DATA_MANIFEST_ID") == man.get("manifest_id"),
        "cn_date_manifest": man.get("CN_RESEARCH_DATE"),
        "cn_date_plane": plane.get("CN_RESEARCH_DATE"),
        "cn_date_pack": pack.get("CN_RESEARCH_DATE"),
        "cn_dates_all_0924": {man.get("CN_RESEARCH_DATE"), plane.get("CN_RESEARCH_DATE"),
                              pack.get("CN_RESEARCH_DATE")} == {"2026-09-24"},
        "alignment_csv_absent": "alignment_csv" not in (man.get("US_MARKET", {}).get("FIXED_PATHS") or {}),
        "alignment_present": "alignment" in (man.get("US_MARKET", {}).get("FIXED_PATHS") or {}),
        "lane_c_discovery_asof": man["GLOBAL_SELLSIDE"].get("DISCOVERY_ASOF"),
        "lane_d_discovery_asof": man["DOMESTIC_RESEARCH"].get("DISCOVERY_ASOF"),
        "lane_e_discovery_asof": man["US_NEWS"].get("DISCOVERY_ASOF"),
        "us_market_date": man["US_MARKET"].get("US_MARKET_DATE"),
        "fine_grained_status": man["US_MARKET"].get("US_FINE_GRAINED_STATUS"),
        "mapping_prior_status": man["US_MARKET"].get("A_SHARE_MAPPING_PRIOR_STATUS"),
        "path_map_entries": len(ents),
        "path_map_missing": missing,
        "cache_product_dirs": n_dirs,
        "cache_top_files": n_files,
        "cache_dir_plus_files": n_dirs + n_files,
        "dg1_equals_source": man.get("DATA_GENERATION_ID") == src.get("DATA_GENERATION_ID"),
        "residual_diff_vs_source": residual,
    }
    hard = [
        checks["DG1_recomputed_matches_file"], checks["DG1_file_matches_plane"],
        checks["manifest_id_matches_plane"], checks["pack_id_matches_manifest"],
        checks["cn_dates_all_0924"], checks["alignment_csv_absent"], checks["alignment_present"],
        not missing,
    ]
    rep = {
        "schema": "BLACKBOX_AFTER_SAM_Q1_Q9_VERIFY_R1",
        "verified_at_cn": datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S%z"),
        "checks": checks,
        "verdict": "PASS" if all(hard) else "FAIL",
        "dg1_state": "DIVERGENT_MODE_ONLY" if residual and all(
            d["key"].endswith(".MODE") for d in residual) else ("IDENTICAL" if not residual else "MULTI_KEY"),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "AFTER_SAM_Q1_Q9_VERIFY.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0 if rep["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
