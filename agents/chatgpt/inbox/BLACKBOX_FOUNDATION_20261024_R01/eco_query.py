# -*- coding: utf-8 -*-
"""
ROUND 1 — query entry for ECOLOGY_REGISTRY.

Answers the operator questions directly:
  what is this data / who is the supplier / is it cleaned / where is the dictionary /
  who can read it / how is it updated

Usage
-----
  python eco_query.py --datasets
  python eco_query.py --dataset PRICE_STOCK_DAILY
  python eco_query.py --answer "这是什么数据" PRICE_STOCK_1M
  python eco_query.py --layers CLEAN
  python eco_query.py --conflicts
  python eco_query.py --unknown
  python eco_query.py --validate
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REG = HERE / "ECOLOGY_REGISTRY.json"

LAYERS = ["RAW", "CLEAN", "CACHE", "FACTOR_DICTIONARY", "FACTOR_VALUE", "STRATEGY_OUTPUT", "EVIDENCE"]
REQUIRED = ["dataset_id", "title", "supplier", "source_identity", "lineage", "layers",
            "authority_rule", "dictionary", "fields", "scope", "relations", "status"]


def load() -> dict:
    return json.loads(REG.read_text(encoding="utf-8"))


def find(reg: dict, key: str) -> list:
    k = key.upper()
    exact = [d for d in reg["datasets"] if d["dataset_id"].upper() == k]
    if exact:
        return exact
    return [d for d in reg["datasets"] if k in d["dataset_id"].upper() or key in d["title"]]


def human(d: dict) -> dict:
    L = d.get("layers") or {}
    raw, clean, cache = L.get("RAW") or {}, L.get("CLEAN") or {}, L.get("CACHE") or {}
    dic = d.get("dictionary") or {}
    dic_targets = []
    for k, v in dic.items():
        if isinstance(v, dict):
            dic_targets.append({"role": k, "path": v.get("path"), "exists": v.get("exists")})
        elif isinstance(v, str):
            dic_targets.append({"role": k, "ref": v})
    return {
        "这是什么数据": d["title"],
        "dataset_id": d["dataset_id"],
        "供应商来源": f'{d["supplier"]} / lineage={d["lineage"]}',
        "是否清洗": ("CLEAN 层存在 → " + str(clean.get("root"))) if clean.get("root")
                    else "该数据集无 CLEAN 层（只有 RAW 或其它层）",
        "RAW在哪": raw.get("root"),
        "CLEAN在哪": clean.get("root"),
        "CACHE在哪": cache.get("root"),
        "发布版本": {"cleaning_release": clean.get("release_id"), "asof": clean.get("asof") or raw.get("asof")},
        "字典在哪": dic_targets or "该数据集无独立字段字典（见 authority_rule / 供应商自有契约）",
        "谁能读": ("只读候选：candidate/local_plane_provider.py（LocalPlaneProvider）；"
                   "引擎正式接入=未接通（formal_backtest_active=false）"),
        "PIT/可知时点": clean.get("pit_rule") or raw.get("pit_rule") or "未在注册表登记",
        "复权": clean.get("adjust_note") or raw.get("adjust_note") or "不适用",
        "怎样更新": d.get("scope", {}).get("increment_rule"),
        "游标": d.get("scope", {}).get("cursor"),
        "排除项": d.get("scope", {}).get("exclusions"),
        "准入阶段": (d.get("authority_rule") or {}).get("admission_stage"),
        "状态": d.get("status"),
    }


def validate(reg: dict) -> dict:
    errors, warns = [], []
    ids = [d["dataset_id"] for d in reg["datasets"]]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        errors.append(f"DUPLICATE_DATASET_ID: {sorted(dup)}")
    for d in reg["datasets"]:
        miss = [k for k in REQUIRED if k not in d]
        if miss:
            errors.append(f"{d.get('dataset_id')}: MISSING_KEYS {miss}")
        for L in (d.get("layers") or {}):
            if L not in LAYERS:
                errors.append(f"{d['dataset_id']}: ILLEGAL_LAYER {L}")
        if d["supplier"] != "JQData" and (d.get("dictionary") or {}).get("schema_contract"):
            warns.append(f"{d['dataset_id']}: 外源引用了聚宽 20_freeze 契约（血统风险）")
        if d["supplier"] == "JQData" and not (d.get("dictionary") or {}):
            warns.append(f"{d['dataset_id']}: 聚宽数据集未登记字典引用")
        for L, v in (d.get("layers") or {}).items():
            if v.get("root") and v.get("exists") is False:
                errors.append(f"{d['dataset_id']}.{L}: ROOT_MISSING {v['root']}")
    return {"n_datasets": len(ids), "errors": errors, "warnings": warns,
            "verdict": "PASS" if not errors else "FAIL"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", action="store_true")
    ap.add_argument("--dataset")
    ap.add_argument("--answer")
    ap.add_argument("--layers")
    ap.add_argument("--conflicts", action="store_true")
    ap.add_argument("--unknown", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    reg = load()

    if a.validate:
        print(json.dumps(validate(reg), ensure_ascii=False, indent=1))
        return 0
    if a.datasets:
        for d in reg["datasets"]:
            print(f'{d["dataset_id"]:38s} {"/".join(sorted((d.get("layers") or {}).keys())):22s} {d["supplier"]:18s} {d["title"]}')
        return 0
    if a.layers:
        L = a.layers.upper()
        for d in reg["datasets"]:
            if L in (d.get("layers") or {}):
                print(f'{d["dataset_id"]:38s} {(d["layers"][L].get("root") or d["layers"][L].get("file") or "(no path)")}')
        return 0
    if a.conflicts:
        for d in reg["datasets"]:
            c = (d.get("status") or {}).get("conflict") or []
            if c:
                print(f'[{d["dataset_id"]}] {c}')
        print("--- 全局冲突 ---")
        print(json.dumps(reg["field_facts"]["index_weights_correction"]["verdict"], ensure_ascii=False))
        return 0
    if a.unknown:
        for d in reg["datasets"]:
            u = (d.get("status") or {}).get("unknown") or []
            if u:
                print(f'[{d["dataset_id"]}] {u}')
        return 0
    target = a.dataset or a.answer
    if not target:
        print(json.dumps(reg["counts"], ensure_ascii=False, indent=1))
        return 0
    hits = find(reg, target)
    if not hits:
        print(json.dumps({"status": "REJECTED", "reject_reason": "UNKNOWN_DATASET", "requested": target,
                          "known": [d["dataset_id"] for d in reg["datasets"]]}, ensure_ascii=False, indent=1))
        return 1
    out = [human(d) if not a.json else d for d in hits]
    print(json.dumps(out if len(out) > 1 else out[0], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
