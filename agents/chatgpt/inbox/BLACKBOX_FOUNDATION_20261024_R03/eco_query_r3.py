"""Query entry for ECOLOGY_REGISTRY_R3 (English, executable).

Usage:
  python eco_query_r3.py --datasets
  python eco_query_r3.py --dataset PRICE_STOCK_DAILY
  python eco_query_r3.py --layers PRICE_STOCK_DAILY
  python eco_query_r3.py --coverage
  python eco_query_r3.py --validate
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REG = HERE / "ECOLOGY_REGISTRY_R3.json"
REQUIRED = ["dataset_id", "title_en", "supplier", "layers", "scope", "authority_rule"]


def load() -> dict:
    return json.loads(REG.read_text(encoding="utf-8"))


def validate(reg: dict) -> dict:
    problems, warnings = [], []
    ds = reg.get("datasets") or []
    if not ds:
        problems.append("datasets is empty")
    seen = set()
    for d in ds:
        missing = [k for k in REQUIRED if k not in d]
        if missing:
            problems.append(f"{d.get('dataset_id')}: missing {missing}")
        if d["dataset_id"] in seen:
            problems.append(f"duplicate dataset_id {d['dataset_id']}")
        seen.add(d["dataset_id"])
        sc = d.get("scope") or {}
        if sc.get("coverage_basis") == "OBSERVED_PARQUET_TIME_STATISTICS":
            a, b = sc.get("observed_start"), sc.get("observed_end")
            if not a or not b:
                problems.append(f"{d['dataset_id']}: observed coverage missing bounds")
            elif a > b:
                problems.append(f"{d['dataset_id']}: observed_start > observed_end")
            if not sc.get("watermark"):
                warnings.append(f"{d['dataset_id']}: observed but no watermark block")
        elif sc.get("scope_undefined") is not True:
            problems.append(f"{d['dataset_id']}: unobserved coverage must be explicitly undefined")
    return {"registry": str(REG), "n_datasets": len(ds),
            "n_observed": reg.get("counts", {}).get("datasets_with_observed_coverage"),
            "problems": problems, "warnings": warnings,
            "status": "OK" if not problems else "FAIL"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", action="store_true")
    ap.add_argument("--dataset")
    ap.add_argument("--layers")
    ap.add_argument("--coverage", action="store_true")
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    reg = load()
    by_id = {d["dataset_id"]: d for d in reg["datasets"]}
    if a.datasets:
        for d in reg["datasets"]:
            print(f"{d['dataset_id']:32s} {d['scope']['coverage_basis']:32s} {d['title_en']}")
        return 0
    if a.dataset:
        print(json.dumps(by_id.get(a.dataset, {"error": "UNKNOWN_DATASET"}), ensure_ascii=False, indent=1))
        return 0
    if a.layers:
        d = by_id.get(a.layers, {})
        print(json.dumps(d.get("layers", {"error": "UNKNOWN_DATASET"}), ensure_ascii=False, indent=1))
        return 0
    if a.coverage:
        print(json.dumps({k: v for k, v in reg.get("observed_read_plane", {}).items()},
                         ensure_ascii=False, indent=1))
        return 0
    if a.validate:
        print(json.dumps(validate(reg), ensure_ascii=False, indent=1))
        return 0
    print(json.dumps({"registry_id": reg["registry_id"], "version": reg["version"],
                      "counts": reg["counts"], "hint": "use --datasets/--dataset/--layers/--coverage/--validate"},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
