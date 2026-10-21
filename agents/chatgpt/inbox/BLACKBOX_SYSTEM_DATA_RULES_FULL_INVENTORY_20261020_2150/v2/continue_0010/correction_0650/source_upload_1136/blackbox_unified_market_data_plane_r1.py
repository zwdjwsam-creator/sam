# -*- coding: utf-8 -*-
"""BLACKBOX Unified Market Data Plane Resolver R1.

rule_id: BLACKBOX_HAND_UNIFIED_MARKET_DATA_PLANE_RESOLVER_R1

Purpose
-------
Deterministic multi-plane resolution for minute (and similar hybrid) products.
Agents must NOT hard-code a single RAW directory. Production read authority:

  CLEANING day partition  >  CLEANING year batch  >  RAW year batch

Usage
-----
  python blackbox_unified_market_data_plane_r1.py --build-index
  python blackbox_unified_market_data_plane_r1.py --product STOCK_MINUTE_1M_R1 --coverage-start 2026-08-03 --coverage-end 2026-08-12
  python blackbox_unified_market_data_plane_r1.py --product STOCK_MINUTE_1M --list-files --coverage-start 2026-08-03 --coverage-end 2026-08-03
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "规则库" / "data_dictionary" / "unified_market_data_plane_registry_r1.json"
CURRENT_PATH = ROOT / "运行" / "BLACKBOX_UNIFIED_MARKET_DATA_PLANE_CURRENT.json"
RULE_PATH = ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_UNIFIED_MARKET_DATA_PLANE_RESOLVER_R1.json"

CN_TZ = timezone(timedelta(hours=8))


def now_cn() -> str:
    return datetime.now(CN_TZ).isoformat()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry() -> dict:
    if not REGISTRY_PATH.is_file():
        raise FileNotFoundError(f"REGISTRY_MISSING: {REGISTRY_PATH}")
    return _load_json(REGISTRY_PATH)


def load_cleaning_pointer() -> dict:
    p = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
    return _load_json(p)


def load_cache_pointer() -> dict:
    p = ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"
    return _load_json(p)


def normalize_product_id(name: str, registry: Optional[dict] = None) -> str:
    registry = registry or load_registry()
    key = name.strip()
    products = registry["products"]
    if key in products:
        return key
    upper = key.upper()
    for pid, meta in products.items():
        if upper == pid.upper():
            return pid
        aliases = [str(a).upper() for a in meta.get("aliases", [])]
        if upper in aliases or key in meta.get("aliases", []):
            return pid
    raise KeyError(f"UNKNOWN_PRODUCT: {name}")


def _daterange(start: str, end: str) -> List[str]:
    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    if e < s:
        raise ValueError(f"bad_range: {start}..{end}")
    out = []
    cur = s
    while cur <= e:
        out.append(cur.isoformat())
        cur += timedelta(days=1)
    return out


def _scan_cleaning_dir(cleaning_dir: Path, day_re: re.Pattern, year_re: re.Pattern) -> dict:
    day_files: Dict[str, List[str]] = defaultdict(list)
    year_files: Dict[str, List[str]] = defaultdict(list)
    if not cleaning_dir.is_dir():
        return {
            "exists": False,
            "day_dates": [],
            "day_file_count": 0,
            "year_batches": {},
            "day_files_by_date": {},
        }
    for f in cleaning_dir.glob("*.parquet"):
        name = f.name
        m = day_re.search(name)
        if m:
            day_files[m.group("date")].append(str(f))
            continue
        m = year_re.search(name)
        if m:
            year_files[m.group("year")].append(str(f))
    return {
        "exists": True,
        "day_dates": sorted(day_files),
        "day_file_count": sum(len(v) for v in day_files.values()),
        "year_batches": {y: len(v) for y, v in sorted(year_files.items())},
        "year_files_by_year": {y: v for y, v in year_files.items()},
        "day_files_by_date": {d: v for d, v in day_files.items()},
    }


def _scan_raw_year_envelope(raw_dir: Path, year: str, glob_tmpl: str, start_key: str, end_key: str) -> dict:
    if not raw_dir.is_dir():
        return {"year": year, "n_sidecars": 0, "start_min": None, "end_max": None}
    pattern = glob_tmpl.format(year=year)
    starts: List[str] = []
    ends: List[str] = []
    n = 0
    for pq in raw_dir.glob(pattern):
        side = Path(str(pq) + ".sidecar.json")
        if not side.is_file():
            # some layouts use path.with_suffix chain
            side2 = pq.with_suffix(pq.suffix + ".sidecar.json")
            side = side2 if side2.is_file() else side
        if not side.is_file():
            continue
        n += 1
        try:
            j = _load_json(side)
        except Exception:
            continue
        s = j.get(start_key)
        e = j.get(end_key)
        if s:
            starts.append(str(s)[:10])
        if e:
            ends.append(str(e)[:10])
    if n > 0 and (len(starts) < n or len(ends) < n):
        # incremental sidecars must not shrink a year that also has undated v2 batches
        if not starts:
            starts.append(f"{year}-01-01")
        if not ends:
            ends.append(f"{year}-12-31")
    return {
        "year": year,
        "n_sidecars": n,
        "start_min": min(starts) if starts else None,
        "end_max": max(ends) if ends else None,
    }


def resolve_product(product_id: str, registry: Optional[dict] = None) -> dict:
    registry = registry or load_registry()
    pid = normalize_product_id(product_id, registry)
    meta = registry["products"][pid]
    cleaning = load_cleaning_pointer()
    standard_root = Path(cleaning["standard_root"])
    raw_root = ROOT / registry["pointers"]["raw_root"]

    cplane = meta["planes"]["CLEANING_CURRENT"]
    rplane = meta["planes"]["RAW_REPLACEMENT"]
    cleaning_dir = standard_root / cplane["relative_under_standard"]
    raw_dir = raw_root / rplane["relative_under_raw_root"]

    day_re = re.compile(cplane["day_name_regex"])
    year_re = re.compile(cplane["year_batch_regex"])
    cscan = _scan_cleaning_dir(cleaning_dir, day_re, year_re)

    years = sorted(set(cscan.get("year_batches", {}).keys()) | set())
    # also discover raw years via glob of year token if cleaning empty
    if raw_dir.is_dir() and not years:
        for f in raw_dir.glob("*.parquet"):
            m = re.search(r"__(20\d{2})__", f.name)
            if m:
                years.append(m.group(1))
        years = sorted(set(years))

    raw_envelopes = {}
    for y in years:
        raw_envelopes[y] = _scan_raw_year_envelope(
            raw_dir,
            y,
            rplane["year_batch_glob"],
            rplane.get("sidecar_start_key", "start_date"),
            rplane.get("sidecar_end_key", "end_date"),
        )

    # cleaning year envelope: inherit raw sidecar envelope when same replacement lineage
    cleaning_year_envelope = {}
    for y, nfiles in (cscan.get("year_batches") or {}).items():
        env = raw_envelopes.get(y) or {}
        cleaning_year_envelope[y] = {
            "n_files": nfiles,
            "start_min": env.get("start_min"),
            "end_max": env.get("end_max"),
            "envelope_source": "RAW_SIDECAR_LINEAGE" if env.get("end_max") else "YEAR_FILES_ONLY_NO_DATE_ENVELOPE",
        }

    return {
        "product_id": pid,
        "aliases": meta.get("aliases", []),
        "asset": meta.get("asset"),
        "freq": meta.get("freq"),
        "fq_tag": meta.get("fq_tag"),
        "cleaning_release_id": cleaning.get("release_id"),
        "cleaning_as_of": cleaning.get("cleaning_as_of") or cleaning.get("daily_asof"),
        "planes": {
            "P1_CLEANING_CURRENT": {
                "dir": str(cleaning_dir),
                "exists": cscan["exists"],
                "day_dates": cscan["day_dates"],
                "day_file_count": cscan["day_file_count"],
                "year_batches": cscan.get("year_batches", {}),
                "year_envelope": cleaning_year_envelope,
                "day_files_by_date": cscan.get("day_files_by_date", {}),
                "year_files_by_year": cscan.get("year_files_by_year", {}),
            },
            "P2_RAW_REPLACEMENT": {
                "dir": str(raw_dir),
                "exists": raw_dir.is_dir(),
                "year_envelope": raw_envelopes,
                "glob": rplane["year_batch_glob"],
            },
        },
        "authority_priority": [
            "CLEANING_DAY_PARTITION",
            "CLEANING_YEAR_BATCH",
            "RAW_YEAR_BATCH",
        ],
    }


def _date_in_envelope(d: str, start_min: Optional[str], end_max: Optional[str]) -> bool:
    if not start_min or not end_max:
        return False
    return start_min <= d <= end_max


def classify_date(resolved: dict, d: str) -> dict:
    p1 = resolved["planes"]["P1_CLEANING_CURRENT"]
    p2 = resolved["planes"]["P2_RAW_REPLACEMENT"]
    day_map = p1.get("day_files_by_date") or {}
    if d in day_map and day_map[d]:
        return {
            "date": d,
            "status": "PRESENT",
            "authoritative_plane": "CLEANING_DAY_PARTITION",
            "files": day_map[d],
            "n_files": len(day_map[d]),
        }
    year = d[:4]
    cenv = (p1.get("year_envelope") or {}).get(year) or {}
    if (p1.get("year_batches") or {}).get(year) and _date_in_envelope(d, cenv.get("start_min"), cenv.get("end_max")):
        return {
            "date": d,
            "status": "PRESENT",
            "authoritative_plane": "CLEANING_YEAR_BATCH",
            "files": (p1.get("year_files_by_year") or {}).get(year, []),
            "n_files": (p1.get("year_batches") or {}).get(year, 0),
            "envelope": {"start_min": cenv.get("start_min"), "end_max": cenv.get("end_max")},
        }
    renv = (p2.get("year_envelope") or {}).get(year) or {}
    if p2.get("exists") and _date_in_envelope(d, renv.get("start_min"), renv.get("end_max")):
        return {
            "date": d,
            "status": "PRESENT",
            "authoritative_plane": "RAW_YEAR_BATCH",
            "files": [],
            "n_files": renv.get("n_sidecars", 0),
            "envelope": {"start_min": renv.get("start_min"), "end_max": renv.get("end_max")},
            "note": "Cleaning day/year miss; RAW envelope covers date — use RAW read path",
        }
    # year files exist but envelope unknown and no day file — REVIEW not automatic miss
    if (p1.get("year_batches") or {}).get(year) and not cenv.get("end_max"):
        return {
            "date": d,
            "status": "REVIEW_REQUIRED_NO_DATE_ENVELOPE",
            "authoritative_plane": "CLEANING_YEAR_BATCH_UNBOUNDEDED",
            "files": (p1.get("year_files_by_year") or {}).get(year, []),
            "n_files": (p1.get("year_batches") or {}).get(year, 0),
        }
    return {
        "date": d,
        "status": "MISSING",
        "authoritative_plane": None,
        "files": [],
        "n_files": 0,
        "probed_planes": ["CLEANING_DAY_PARTITION", "CLEANING_YEAR_BATCH", "RAW_YEAR_BATCH"],
    }


def coverage_window(product_id: str, start: str, end: str, registry: Optional[dict] = None) -> dict:
    registry = registry or load_registry()
    resolved = resolve_product(product_id, registry)
    # weekends included; caller may filter by calendar — presence still reported
    days = _daterange(start, end)
    rows = [classify_date(resolved, d) for d in days]
    present = [r for r in rows if r["status"] == "PRESENT"]
    missing = [r for r in rows if r["status"] == "MISSING"]
    review = [r for r in rows if r["status"].startswith("REVIEW")]
    planes_used = sorted({r["authoritative_plane"] for r in present if r.get("authoritative_plane")})
    false_miss_guard = "PASS"
    # Guard: if any cleaning day exists in window, forbidding single-raw miss claims
    if any(r.get("authoritative_plane") == "CLEANING_DAY_PARTITION" for r in present):
        false_miss_guard = "PASS_CLEANING_DAY_AUTHORITY_ACTIVE"
    return {
        "product_id": resolved["product_id"],
        "cleaning_release_id": resolved["cleaning_release_id"],
        "window": {"start": start, "end": end},
        "n_calendar_days": len(days),
        "n_present": len(present),
        "n_missing": len(missing),
        "n_review": len(review),
        "authoritative_planes_for_window": planes_used,
        "FALSE_MISS_GUARD": false_miss_guard,
        "DATA_PLANE_READY": "YES" if not missing and not review else ("REVIEW" if review and not missing else "NO"),
        "present_dates": [r["date"] for r in present],
        "missing_dates": [r["date"] for r in missing],
        "review_dates": [r["date"] for r in review],
        "by_date": rows,
        "planes_summary": {
            "cleaning_dir": resolved["planes"]["P1_CLEANING_CURRENT"]["dir"],
            "cleaning_day_dates_available": resolved["planes"]["P1_CLEANING_CURRENT"]["day_dates"],
            "raw_dir": resolved["planes"]["P2_RAW_REPLACEMENT"]["dir"],
        },
    }


def list_files_for_window(product_id: str, start: str, end: str, registry: Optional[dict] = None) -> dict:
    cov = coverage_window(product_id, start, end, registry)
    units = []
    for row in cov["by_date"]:
        if row["status"] != "PRESENT":
            continue
        plane = row["authoritative_plane"]
        files = row.get("files") or []
        if plane == "RAW_YEAR_BATCH":
            # resolve concrete raw year files via glob
            resolved = resolve_product(product_id, registry)
            year = row["date"][:4]
            raw_dir = Path(resolved["planes"]["P2_RAW_REPLACEMENT"]["dir"])
            glob_tmpl = resolved["planes"]["P2_RAW_REPLACEMENT"]["glob"]
            files = [str(p) for p in raw_dir.glob(glob_tmpl.format(year=year))]
        units.append(
            {
                "date": row["date"],
                "authoritative_plane": plane,
                "files": files,
                "n_files": len(files),
            }
        )
    return {
        "product_id": cov["product_id"],
        "window": cov["window"],
        "DATA_PLANE_READY": cov["DATA_PLANE_READY"],
        "read_units": units,
    }


def diagnose(product_id: str, start: str, end: str) -> dict:
    cov = coverage_window(product_id, start, end)
    root_cause = "OK_MULTI_PLANE"
    if cov["n_missing"] == 0 and cov["n_review"] == 0:
        action = "USE_UNIFIED_PLANE_READ_UNITS"
        download_required = False
    elif cov["n_missing"] > 0 and cov["n_present"] > 0:
        root_cause = "PARTIAL_WINDOW_GAP"
        action = "HYBRID_READ_PRESENT_DATES_ONLY_OR_INCREMENTAL_DOWNLOAD_MISSING"
        download_required = True
    elif cov["n_missing"] > 0:
        root_cause = "TRUE_MISS_AFTER_ALL_PLANES"
        action = "DOWNLOAD_THEN_CLEAN_THEN_REBUILD_INDEX"
        download_required = True
    else:
        root_cause = "ENVELOPE_REVIEW"
        action = "PROBE_YEAR_BATCH_CONTENT_OR_REFRESH_SIDECAR_ENVELOPE"
        download_required = False

    # classic false-alarm signature
    cleaning_days = set(cov["planes_summary"]["cleaning_day_dates_available"])
    win_days = set(_daterange(start, end))
    if cleaning_days & win_days and any(
        "replacement" in (cov["planes_summary"]["raw_dir"] or "").lower() for _ in [0]
    ):
        note = (
            "If a research script read only RAW replacement year-batches, "
            "it may false-miss dates that Cleaning day partitions already hold."
        )
    else:
        note = ""

    return {
        "DATA_COVERAGE_DIAGNOSIS": True,
        "dataset": cov["product_id"],
        "generated_at": now_cn(),
        "rule_id": "BLACKBOX_HAND_UNIFIED_MARKET_DATA_PLANE_RESOLVER_R1",
        **cov,
        "root_cause": root_cause,
        "download_required": download_required,
        "action": action,
        "false_alarm_class_if_single_raw_only": "LAYER_MISMATCH_CLEANING_HAS_DAY_BUT_RESEARCH_READ_STALE_RAW",
        "note": note,
    }


def build_index(products: Optional[Iterable[str]] = None) -> dict:
    registry = load_registry()
    cleaning = load_cleaning_pointer()
    cache = load_cache_pointer()
    pids = list(products) if products else list(registry["products"].keys())
    resolved_products = {}
    for pid in pids:
        r = resolve_product(pid, registry)
        # shrink CURRENT: drop full file path lists (too large); keep counts + day dates
        p1 = r["planes"]["P1_CLEANING_CURRENT"]
        resolved_products[pid] = {
            "product_id": r["product_id"],
            "aliases": r["aliases"],
            "asset": r["asset"],
            "freq": r["freq"],
            "fq_tag": r["fq_tag"],
            "cleaning_release_id": r["cleaning_release_id"],
            "planes": {
                "P1_CLEANING_CURRENT": {
                    "dir": p1["dir"],
                    "exists": p1["exists"],
                    "day_dates": p1["day_dates"],
                    "day_file_count": p1["day_file_count"],
                    "year_batches": p1["year_batches"],
                    "year_envelope": p1["year_envelope"],
                },
                "P2_RAW_REPLACEMENT": {
                    "dir": r["planes"]["P2_RAW_REPLACEMENT"]["dir"],
                    "exists": r["planes"]["P2_RAW_REPLACEMENT"]["exists"],
                    "year_envelope": r["planes"]["P2_RAW_REPLACEMENT"]["year_envelope"],
                },
            },
            "authority_priority": r["authority_priority"],
        }
    index = {
        "index_id": "BLACKBOX_UNIFIED_MARKET_DATA_PLANE_CURRENT_R1",
        "rule_id": "BLACKBOX_HAND_UNIFIED_MARKET_DATA_PLANE_RESOLVER_R1",
        "generated_at": now_cn(),
        "registry_path": str(REGISTRY_PATH),
        "cleaning_release_id": cleaning.get("release_id"),
        "cleaning_as_of": cleaning.get("cleaning_as_of") or cleaning.get("daily_asof"),
        "cache_release_id": cache.get("cache_release_id"),
        "product_count": len(resolved_products),
        "products": resolved_products,
        "ag_forced": {
            "before_claim_missing": "run blackbox_unified_market_data_plane_preflight_r1.py",
            "forbid_single_raw_path": True,
            "production_minute_default": "CLEANING_CURRENT with day>year merge",
        },
    }
    CURRENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CURRENT_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return index


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="BLACKBOX Unified Market Data Plane R1")
    ap.add_argument("--build-index", action="store_true")
    ap.add_argument("--product", default="")
    ap.add_argument("--coverage-start", default="")
    ap.add_argument("--coverage-end", default="")
    ap.add_argument("--list-files", action="store_true")
    ap.add_argument("--diagnose", action="store_true")
    args = ap.parse_args(argv)

    if args.build_index:
        idx = build_index()
        print(json.dumps({"ok": True, "current": str(CURRENT_PATH), "product_count": idx["product_count"], "cleaning_release_id": idx["cleaning_release_id"]}, ensure_ascii=False, indent=2))
        return 0

    if not args.product:
        ap.error("--product required unless --build-index")
    if not args.coverage_start or not args.coverage_end:
        # resolve-only
        body = resolve_product(args.product)
        # drop huge file lists for stdout
        p1 = body["planes"]["P1_CLEANING_CURRENT"]
        p1.pop("day_files_by_date", None)
        p1.pop("year_files_by_year", None)
        print(json.dumps(body, ensure_ascii=False, indent=2))
        return 0

    if args.diagnose:
        print(json.dumps(diagnose(args.product, args.coverage_start, args.coverage_end), ensure_ascii=False, indent=2))
        return 0
    if args.list_files:
        print(json.dumps(list_files_for_window(args.product, args.coverage_start, args.coverage_end), ensure_ascii=False, indent=2))
        return 0
    print(json.dumps(coverage_window(args.product, args.coverage_start, args.coverage_end), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
