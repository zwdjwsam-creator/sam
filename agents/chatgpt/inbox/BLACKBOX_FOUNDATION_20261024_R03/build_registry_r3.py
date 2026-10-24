"""Build the R03 English ecology registry from the R01 executable registry.

Differences from R01:
  * English field names, English titles and notes (source paths/ids preserved literally).
  * Per-dataset observed coverage and watermark come from parquet footer statistics of the
    bound read plane. Undefined ranges stay explicitly undefined; no universal 2014 start
    and no global cleaning-as-of cursor are assumed.
  * Read-plane bindings record which dataset/layer the candidate provider actually serves.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from candidate.r3 import file_index, securities  # noqa: E402

R01 = HERE / "ECOLOGY_REGISTRY.json"
OUT = HERE / "ECOLOGY_REGISTRY_R3.json"
OUT_INDEX = HERE / "ECOLOGY_REGISTRY_R3_INDEX.json"

TITLES = {
    "PRICE_STOCK_DAILY": "A-share stock daily OHLCV (raw and cleaned)",
    "PRICE_STOCK_1M": "A-share stock 1-minute bars",
    "PRICE_ETF_DAILY": "ETF daily OHLCV",
    "PRICE_ETF_1M": "ETF 1-minute bars",
    "PRICE_INDEX_DAILY": "Index daily OHLCV",
    "PRICE_INDEX_MINUTE": "Index minute bars",
    "CALENDAR_CN_EXCHANGE": "China exchange trading calendar",
    "SECURITY_MASTER": "Security master (type, name, listing window)",
    "ADJUST_FACTOR": "Adjustment factor plane",
    "TRADABLE_STATUS": "Tradable / limit / pause status",
    "INDEX_COMPONENTS": "Index constituents",
    "INDEX_WEIGHTS": "Index weights (component code preserved; historical backtest ineligible)",
    "XR_XD": "Ex-rights / ex-dividend events",
    "FUND_ETF_NAV": "Fund and ETF NAV / premium plane",
    "VALUATION": "Valuation metrics",
    "FINANCE_PIT": "Point-in-time financial statements",
    "FACTOR_260_DICTIONARY": "Factor 260 dictionary metadata",
    "FACTOR_260_SEMANTICS": "Factor 260 semantics metadata",
    "FACTOR_260_FORMULA": "Factor 260 formula metadata",
    "FACTOR_260_PIT_RULES": "Factor 260 point-in-time rules",
    "FACTOR_260_CLEANING_RULES": "Factor 260 cleaning rules",
    "FACTOR_260_ENGINE_MAPPING": "Factor 260 engine mapping",
    "FACTOR_VALUE": "Factor value plane (permission-blocked in R01 evidence)",
    "STRATEGY_OUTPUT": "Strategy output plane (not an input)",
}

OBSERVE = [
    "PRICE_STOCK_DAILY", "PRICE_STOCK_1M", "PRICE_ETF_DAILY", "PRICE_ETF_1M",
    "PRICE_INDEX_DAILY", "PRICE_INDEX_MINUTE", "CALENDAR_CN_EXCHANGE", "SECURITY_MASTER",
    "XR_XD", "INDEX_COMPONENTS", "ADJUST_FACTOR", "TRADABLE_STATUS",
]

READ_PLANE = {
    "PRICE_STOCK_DAILY": "stock daily bars for stock-class codes",
    "PRICE_STOCK_1M": "stock 1-minute bars for stock-class codes",
    "PRICE_ETF_DAILY": "ETF daily bars for ETF/LOF/fund codes",
    "PRICE_ETF_1M": "ETF 1-minute bars",
    "PRICE_INDEX_DAILY": "index daily bars for index-class codes",
    "PRICE_INDEX_MINUTE": "index minute bars",
    "SECURITY_MASTER": "asset-class routing and listing window",
    "CALENDAR_CN_EXCHANGE": "expected trade-day derivation",
    "XR_XD": "ex-rights / ex-dividend events",
    "INDEX_COMPONENTS": "index membership",
}


def english_title(ds_id: str, supplier: str) -> str:
    if ds_id in TITLES:
        return TITLES[ds_id]
    return f"{ds_id} dataset (supplier: {supplier or 'unrecorded'}); identifier and lineage preserved"


def main() -> int:
    src = json.loads(R01.read_text(encoding="utf-8"))
    datasets = []
    observed = {}
    for ds in src["datasets"]:
        ds_id = ds["dataset_id"]
        layers = {}
        for lname, lrec in (ds.get("layers") or {}).items():
            layers[lname] = {
                "root": lrec.get("root"),
                "exists": bool(lrec.get("exists")),
                "n_parquet": lrec.get("n_parquet"),
                "kind": lrec.get("kind"),
                "release_id": lrec.get("release_id"),
                "asof": lrec.get("asof"),
                "time_visibility": {
                    "RAW": "bar visible after its trade date close",
                    "CLEAN": "bar visible after its trade date close",
                    "CACHE": "derived; read through the cache product name, not the directory",
                }.get(lname, "not stated in this candidate"),
                "adjustment_identity": "RAW_NONE; factor is a separate column, never folded into close; "
                                       "a missing factor is not admitted as 1.0",
            }
        scope = {
            "coverage_basis": "NOT_OBSERVED_THIS_CYCLE",
            "observed_start": None, "observed_end": None,
            "declared_range": None,
            "scope_undefined": True,
            "increment_cursor": None,
            "note": "No universal 2014 start and no global as-of cursor is assumed here. "
                    "An updater must read the observed watermark once it exists; until then the "
                    "range stays explicitly undefined.",
        }
        if ds_id in OBSERVE:
            lay = "CLEAN" if (layers.get("CLEAN") or {}).get("root") else "RAW"
            root = (layers.get(lay) or {}).get("root")
            idx = file_index.build_index(ds_id, lay, root) if root else None
            if idx and idx.get("n_files") and idx.get("observed_start"):
                observed[ds_id] = {"layer": lay, "root": root,
                                   "observed_start": idx.get("observed_start"),
                                   "observed_end": idx.get("observed_end"),
                                   "n_files": idx["n_files"],
                                   "index_cache": f"runtime/file_index_{ds_id}_{lay}.json"}
                scope = {
                    "coverage_basis": "OBSERVED_PARQUET_TIME_STATISTICS",
                    "observed_start": idx.get("observed_start"),
                    "observed_end": idx.get("observed_end"),
                    "declared_range": None,
                    "scope_undefined": False,
                    "watermark": {"start": idx.get("observed_start"), "end": idx.get("observed_end")},
                    "n_files_indexed": idx["n_files"],
                    "increment_cursor": None,
                    "note": "Coverage is the union of per-file time statistics, not filename tokens "
                            "and not build timestamps. The cursor stays undefined until the updater "
                            "publishes one.",
                }
            elif idx and idx.get("n_files"):
                cols = sorted({c for e in file_index.load_entries(idx) for c in e.columns})
                scope = {
                    "coverage_basis": "NO_TIME_AXIS_OBSERVED",
                    "observed_start": None, "observed_end": None,
                    "declared_range": None,
                    "scope_undefined": True,
                    "n_files_indexed": idx["n_files"],
                    "time_columns_present": cols,
                    "increment_cursor": None,
                    "note": "Reference/event family without a single bar time axis; per-row validity "
                            "or event columns are listed in time_columns_present. No synthetic range "
                            "is invented.",
                }
        datasets.append({
            "dataset_id": ds_id,
            "title_en": english_title(ds_id, ds.get("supplier")),
            "supplier": ds.get("supplier"),
            "lineage": ds.get("lineage"),
            "source_identity": ds.get("source_identity"),
            "layers": layers,
            "scope": scope,
            "read_plane_role": READ_PLANE.get(ds_id),
            "authority_rule": ds.get("authority_rule"),
            "language_note": "Original Chinese layer notes are preserved in the R01 registry artifact "
                             "and deliberately not duplicated or bulk-translated here.",
        })

    sm_root = None
    for d in datasets:
        if d["dataset_id"] == "SECURITY_MASTER":
            layers_d = d.get("layers") or {}
            for lname in ["CLEAN", "RAW"] + [k for k in layers_d if k not in ("CLEAN", "RAW")]:
                rec = layers_d.get(lname) or {}
                if rec.get("root"):
                    sm_root = rec["root"]
                    break
    sm = securities.build(sm_root) if sm_root else {"n_codes": 0, "by_type": {}}
    out = {
        "registry_id": "BLACKBOX_ECOLOGY_REGISTRY_R3",
        "version": "R3_20261024",
        "built_at": file_index.time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "predecessor": "ECOLOGY_REGISTRY.json (R01)",
        "round": "R03_OF_10",
        "budget_slot": "3/10",
        "budget_remaining_after_delivery": 7,
        "FOUNDATION_ACCEPTANCE": False,
        "ORDER_ALLOWED": False,
        "production_write": False,
        "language": "en",
        "scope_policy": {
            "coverage_source": "parquet footer statistics of the actual time column",
            "filename_rule": "build stamps YYYYMMDD_HHMMSS are stripped and are never coverage",
            "undefined_ranges": "kept explicitly null; no invented 2014 start",
            "version_rule": "same family + same coverage => newest build wins; different coverage => "
                            "complementary segments are both kept",
        },
        "security_classification": {
            "source_dataset": "SECURITY_MASTER",
            "n_codes": sm.get("n_codes"),
            "by_type": sm.get("by_type"),
            "asset_class_map": securities.ASSET_FAMILY,
        },
        "observed_read_plane": observed,
        "datasets": datasets,
        "counts": {
            "datasets": len(datasets),
            "datasets_with_observed_coverage": len(observed),
            "layers": sorted({l for d in datasets for l in d["layers"]}),
        },
        "counts_note": "Counts are generated from this build, not hand-written.",
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    index = {
        "registry": str(OUT),
        "datasets": {d["dataset_id"]: {"title_en": d["title_en"], "supplier": d["supplier"],
                                       "layers": list(d["layers"]),
                                       "coverage_basis": d["scope"]["coverage_basis"],
                                       "observed_start": d["scope"].get("observed_start"),
                                       "observed_end": d["scope"].get("observed_end"),
                                       "read_plane_role": d["read_plane_role"]}
                     for d in datasets},
    }
    OUT_INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"datasets": len(datasets), "observed": len(observed),
                      "sm_codes": sm.get("n_codes"), "out": str(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
