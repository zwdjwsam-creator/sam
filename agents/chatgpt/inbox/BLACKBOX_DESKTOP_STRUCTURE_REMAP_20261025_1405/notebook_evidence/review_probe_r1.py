# -*- coding: utf-8 -*-
"""Read-only evidence probe for BLACKBOX_DESKTOP_STRUCTURE_REMAP review (Q1-Q9).

Writes REVIEW_PROBE.json and prints a human-readable digest.
No writes outside this task dir. No network. No CURRENT switch.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import traceback
from pathlib import Path

ROOT = Path(r"E:\BLACKBOX")
PKG = Path(r"C:\LAN_SHARE_REPORT\BLACKBOX_FOUNDATION_R10_SAM_SOURCE_HANDOFF_20261025")
OUT = PKG / "review_probe"
OUT.mkdir(parents=True, exist_ok=True)

ABS_PAT = re.compile(r"[A-Za-z]:[\\/][^\s\"'\),;\]]*")


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p)


def sh(b: bytes) -> str:
    import hashlib

    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------- Q1
def q1_absolute_paths():
    """Which packaged files contain absolutes outside E:\\BLACKBOX (breaks zero-rewrite)."""
    idx = json.loads((PKG / "SOURCE_INDEX.json").read_text(encoding="utf-8"))
    code = [c["rel"] for c in idx["code_files"]]
    entry_names = {e["rel"].replace("\\", "/") for e in idx["entries"] if e.get("exists")}
    hits = []
    for relpath in code:
        p = PKG / "code" / relpath
        if not p.is_file():
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            for m in ABS_PAT.finditer(line):
                val = m.group(0)
                norm = val.replace("\\", "/").lower()
                if norm.startswith("e:/blackbox"):
                    continue
                hits.append(
                    {
                        "file": relpath,
                        "line": i,
                        "value": val[:160],
                        "is_entry": relpath in entry_names,
                        "snippet": line.strip()[:160],
                    }
                )
    by_root = {}
    for h in hits:
        key = h["value"].split("/")[0].split("\\")[0].upper()
        by_root[key] = by_root.get(key, 0) + 1
    entry_hits = [h for h in hits if h["is_entry"]]
    return {
        "files_with_any_abs": len({h["file"] for h in hits}),
        "total_non_root_abs": len(hits),
        "by_drive_prefix": by_root,
        "entry_file_hits": entry_hits,
        "all_hits": hits,
    }


# ---------------------------------------------------------------- Q2
def q2_alignment_key():
    """Which key name is actually consumed by code: 'alignment' vs 'alignment_csv'."""
    pats = {
        "alignment_csv": re.compile(r"alignment_csv"),
        "alignment_plain": re.compile(r"\[\s*[\"']alignment[\"']\s*\]|\.get\(\s*[\"']alignment[\"']"),
        "session_alignment": re.compile(r"session_alignment"),
        "US_NEWS_MARKET_ALIGNMENT": re.compile(r"US_NEWS_MARKET_ALIGNMENT"),
        "US_TO_CN_SESSION_ALIGNMENT": re.compile(r"US_TO_CN_SESSION_ALIGNMENT"),
    }
    rows = []
    scopes = [ROOT / "脚本", ROOT / "任务"]
    for sc in scopes:
        for p in sc.rglob("*.py"):
            if not p.is_file() or p.stat().st_size > 400_000:
                continue
            if any(x in str(p).lower() for x in (".venv", "__pycache__", "\\cache\\", "\\raw\\")):
                continue
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            found = {}
            for name, rx in pats.items():
                n = len(rx.findall(t))
                if n:
                    found[name] = n
            if found:
                rows.append({"file": rel(p), "hits": found})
    rows.sort(key=lambda r: -sum(r["hits"].values()))
    return {"consumers": rows[:25], "consumer_count": len(rows)}


# ---------------------------------------------------------------- Q3
def q3_discovery_asof():
    """How DISCOVERY_ASOF is produced in the data plane (market day vs run day)."""
    targets = [
        ROOT / "脚本" / "run_blackbox_daily_incremental_data_plane_r1.py",
        ROOT / "脚本" / "run_blackbox_us_l1_news_open_close_collector_r1.py",
    ]
    out = []
    for p in targets:
        if not p.is_file():
            continue
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        hits = []
        for i, line in enumerate(lines, 1):
            if "DISCOVERY_ASOF" in line or "US_MARKET_DATE" in line or "CN_RESEARCH_DATE" in line:
                ctx = "\n".join(lines[max(0, i - 3) : i + 2])
                hits.append({"line": i, "text": line.strip()[:200], "ctx": ctx[:600]})
        out.append({"file": rel(p), "hits": hits[:40]})
    manifest = json.loads(
        (ROOT / "研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json").read_text(
            encoding="utf-8-sig"
        )
    )
    keys = {}
    for lane in ("JQ", "T_EXTERNAL", "GLOBAL_SELLSIDE", "DOMESTIC_RESEARCH", "US_NEWS", "US_MARKET"):
        d = manifest.get(lane, {})
        keys[lane] = {
            k: d.get(k)
            for k in ("DISCOVERY_ASOF", "SOURCE_ASOF", "US_MARKET_DATE", "CN_RESEARCH_DATE")
            if k in d
        }
    return {"code": out, "manifest_lane_asofs": keys, "manifest_id": manifest.get("manifest_id")}


# ---------------------------------------------------------------- Q4
def q4_sellside_asof():
    p = ROOT / "任务" / "BLACKBOX_SELLSIDE_THESIS_TIMELINE_R1" / "脚本" / "run_sellside_daily_incremental_r1.py"
    if not p.is_file():
        return {"exists": False}
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    hits = []
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if re.search(r"(asof|report_date|run_date|trade_date)", s, re.I) and (
            "=" in s or "def " in s or "datetime" in s or "today" in s
        ):
            hits.append({"line": i, "text": s[:200]})
    return {"exists": True, "size": p.stat().st_size, "hits": hits[:50]}


# ---------------------------------------------------------------- Q5
def q5_research_memory():
    p = ROOT / "脚本" / "run_blackbox_daily_incremental_research_memory_r1.py"
    out = {"script": rel(p) if p.is_file() else None}
    if p.is_file():
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        arg_hits, date_hits = [], []
        for i, line in enumerate(lines, 1):
            s = line.strip()
            if "add_argument" in s or "choices" in s:
                arg_hits.append({"line": i, "text": s[:200]})
            if re.search(r"(--date|backfill|逐日|for d in|date_list|缺|gap)", s):
                date_hits.append({"line": i, "text": s[:200]})
        out["args"] = arg_hits[:40]
        out["date_logic"] = date_hits[:60]

    # actual day coverage
    for sub in ("DAILY_RESEARCH/DAILY_BRIEF", "DAILY_RESEARCH/RESEARCH_TRACE", "DAILY_RESEARCH"):
        d = ROOT / sub
        if not d.is_dir():
            out[sub] = "MISSING"
            continue
        names = []
        for x in d.iterdir():
            if x.is_dir() and re.fullmatch(r"\d{8}", x.name):
                names.append(x.name)
        out[sub] = {"dir_count": len(names), "days": sorted(names)[-30:]}
    return out


# ---------------------------------------------------------------- Q6
def q6_calendar():
    out = {}
    # RAW
    raw = ROOT / "数据/原始只读/JQData_9999_official_raw/P5_jq20_extension/stk_exchange_link_calendar"
    if raw.is_dir():
        files = sorted(raw.rglob("*.parquet"))
        out["raw_dir"] = str(raw.relative_to(ROOT))
        out["raw_files"] = [{"name": f.name, "size": f.stat().st_size} for f in files[-5:]]
        try:
            import pandas as pd

            df = pd.concat([pd.read_parquet(f) for f in files])
            for col in ("calendar_date", "date", "trade_date"):
                if col in df.columns:
                    s = pd.to_datetime(df[col], errors="coerce")
                    out[f"raw_{col}_min"] = str(s.min())
                    out[f"raw_{col}_max"] = str(s.max())
                    out[f"raw_{col}_distinct"] = int(s.nunique())
                    break
            out["raw_columns"] = list(df.columns)[:30]
            out["raw_rows"] = int(len(df))
        except Exception as e:  # noqa: BLE001
            out["raw_read_error"] = f"{type(e).__name__}: {e}"
    else:
        out["raw_dir"] = "MISSING"

    # CACHE product
    cur = json.loads((ROOT / "数据/回测缓存/CURRENT_CACHE_RELEASE.json").read_text(encoding="utf-8-sig"))
    relroot = Path(cur["release_root"])
    cand = [d for d in relroot.iterdir() if d.is_dir() and "CALENDAR" in d.name.upper()]
    out["cache_release"] = cur.get("cache_release_id")
    out["cache_calendar_dirs"] = [d.name for d in cand]
    for d in cand[:2]:
        files = sorted(d.rglob("*.parquet"))
        out.setdefault("cache_files", {})[d.name] = [
            {"name": f.name, "size": f.stat().st_size} for f in files[-4:]
        ]
        try:
            import pandas as pd

            if files:
                df = pd.concat([pd.read_parquet(f) for f in files])
                for col in ("calendar_date", "date", "trade_date"):
                    if col in df.columns:
                        s = pd.to_datetime(df[col], errors="coerce")
                        out.setdefault("cache_range", {})[d.name] = {
                            "col": col,
                            "min": str(s.min()),
                            "max": str(s.max()),
                            "distinct": int(s.nunique()),
                            "rows": int(len(df)),
                        }
                        break
        except Exception as e:  # noqa: BLE001
            out.setdefault("cache_read_error", {})[d.name] = f"{type(e).__name__}: {e}"
    return out


# ---------------------------------------------------------------- Q7
def q7_stubs():
    rows = []
    for name in ("blackbox_data_coverage_common_r1.py", "blackbox_cache_coverage_non_regression_gate_r1.py"):
        p = ROOT / "脚本" / name
        b = p.read_bytes() if p.is_file() else b""
        rows.append(
            {
                "file": f"脚本/{name}",
                "exists": p.is_file(),
                "bytes": len(b),
                "hex": b.hex() if len(b) <= 8 else None,
                "sha256": sh(b) if b else None,
            }
        )
    return {"stubs": rows, "identical": len({r["sha256"] for r in rows}) == 1}


# ---------------------------------------------------------------- Q8
def q8_us_fine():
    out = {}
    for relp in (
        "运行/BLACKBOX_US_MARKET_FINE_GRAINED_FLOW_PROFIT_POOL_CURRENT.json",
        "数据/美国市场/细粒度利润池/CURRENT/US_FINE_GRAINED_SNAPSHOT_CURRENT.json",
        "数据/美国市场/细粒度利润池/CURRENT/A_SHARE_MAPPING_PRIOR_CURRENT.json",
        "数据/美国市场/CONFIG/US_L234_PROFIT_POOL_TAXONOMY.json",
        "数据/美国市场/CONFIG/US_L1_TAXONOMY.json",
    ):
        p = ROOT / relp
        rec = {"exists": p.is_file(), "size": p.stat().st_size if p.is_file() else None}
        if p.is_file() and p.suffix == ".json" and p.stat().st_size < 200_000:
            try:
                d = json.loads(p.read_text(encoding="utf-8-sig"))
                if isinstance(d, dict):
                    rec["keys"] = sorted(d.keys())[:25]
                    for k in ("STATUS", "status", "ASOF", "asof", "RUN_STATUS", "MODE", "generated_at_cn"):
                        if k in d:
                            rec[k] = d[k]
            except Exception as e:  # noqa: BLE001
                rec["parse_error"] = f"{type(e).__name__}"
        out[relp] = rec
    return out


# ---------------------------------------------------------------- Q9
def q9_stability():
    man_p = ROOT / "研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json"
    man = json.loads(man_p.read_text(encoding="utf-8-sig"))
    clean = json.loads((ROOT / "数据/清洗成品/CURRENT_CLEANING_RELEASE.json").read_text(encoding="utf-8-sig"))
    cache = json.loads((ROOT / "数据/回测缓存/CURRENT_CACHE_RELEASE.json").read_text(encoding="utf-8-sig"))
    scope = json.loads((ROOT / "运行/BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json").read_text(encoding="utf-8-sig"))
    lane_a = json.loads((ROOT / "研究系统/数据平面/STATE/JQ_INCREMENTAL_STATE.json").read_text(encoding="utf-8-sig"))

    relroot = Path(cache["release_root"])
    products = sorted([d.name for d in relroot.iterdir() if d.is_dir()])

    pathmap = json.loads(
        (ROOT / "研究系统/数据平面/CONFIG/DATA_PLANE_PATH_MAP.json").read_text(encoding="utf-8-sig")
    )
    fixed, missing = [], []
    for lane, body in (pathmap.get("lanes") or {}).items():
        for k, v in body.items():
            if isinstance(v, str) and re.match(r"^[A-Za-z]:\\", v):
                (fixed if Path(v).exists() else missing).append(f"{lane}.{k}")

    return {
        "SAM_DATA_GENERATION_ID": man.get("DATA_GENERATION_ID"),
        "SAM_MANIFEST_ID": man.get("manifest_id"),
        "SAM_CN_RESEARCH_DATE": man.get("CN_RESEARCH_DATE"),
        "lane_a_state": {k: lane_a.get(k) for k in ("SOURCE_ASOF", "CLEAN_ASOF", "CACHE_ASOF", "PIT_PASS", "STATUS", "reason_code")},
        "three_way_equal": lane_a.get("SOURCE_ASOF") == lane_a.get("CLEAN_ASOF") == lane_a.get("CACHE_ASOF"),
        "scope_data_asof": scope.get("data_asof"),
        "scope_operational_readiness": scope.get("operational_readiness"),
        "cleaning_release_id": clean.get("release_id"),
        "cleaning_as_of": clean.get("cleaning_as_of"),
        "cleaning_standard_root_exists": Path(clean.get("standard_root", "")).exists(),
        "cleaning_ledger_exists": Path(clean.get("ledger_path", "")).exists(),
        "cache_release_id": cache.get("cache_release_id"),
        "cache_asof": cache.get("asof"),
        "cache_products_count": len(products),
        "cache_products": products,
        "fixed_paths_ok": len(fixed),
        "fixed_paths_missing": missing,
        "ALL_LANES_READY": man.get("ALL_LANES_READY"),
        "DEGRADED_LANES": man.get("DEGRADED_LANES"),
        "desktop_audit_dir_on_SAM": str(ROOT / "_OPS/FOUNDATION_RECOVERY_20261024/desktop_structure_audit_20261025"),
        "desktop_audit_dir_exists": (ROOT / "_OPS/FOUNDATION_RECOVERY_20261024/desktop_structure_audit_20261025").is_dir(),
    }


def main() -> int:
    result = {"probe_id": "DESKTOP_STRUCTURE_REMAP_REVIEW_PROBE_R1", "host": os.environ.get("COMPUTERNAME")}
    for name, fn in (
        ("Q1_absolute_paths", q1_absolute_paths),
        ("Q2_alignment_key", q2_alignment_key),
        ("Q3_discovery_asof", q3_discovery_asof),
        ("Q4_sellside_asof", q4_sellside_asof),
        ("Q5_research_memory", q5_research_memory),
        ("Q6_calendar", q6_calendar),
        ("Q7_stubs", q7_stubs),
        ("Q8_us_fine", q8_us_fine),
        ("Q9_stability", q9_stability),
    ):
        try:
            result[name] = fn()
        except Exception:  # noqa: BLE001
            result[name] = {"ERROR": traceback.format_exc()[-1500:]}
        print(f"== {name} done", flush=True)

    (OUT / "REVIEW_PROBE.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\nWROTE", OUT / "REVIEW_PROBE.json", flush=True)

    # digest
    q1 = result.get("Q1_absolute_paths", {})
    print(f"Q1 non_root_abs={q1.get('total_non_root_abs')} drives={q1.get('by_drive_prefix')}")
    for h in (q1.get("entry_file_hits") or [])[:12]:
        print(f"   ENTRY {h['file']}:{h['line']} {h['value'][:90]}")
    q2 = result.get("Q2_alignment_key", {})
    print(f"Q2 consumers={q2.get('consumer_count')}")
    for r in (q2.get("consumers") or [])[:6]:
        print(f"   {r['file']} {r['hits']}")
    q9 = result.get("Q9_stability", {})
    print(f"Q9 DG1={q9.get('SAM_DATA_GENERATION_ID')} three_way={q9.get('three_way_equal')} "
          f"products={q9.get('cache_products_count')} fixed_ok={q9.get('fixed_paths_ok')} "
          f"missing={q9.get('fixed_paths_missing')} desktop_dir={q9.get('desktop_audit_dir_exists')}")
    q7 = result.get("Q7_stubs", {})
    print(f"Q7 {q7.get('identical')} {q7.get('stubs')}")
    q6 = result.get("Q6_calendar", {})
    print(f"Q6 raw_max={q6.get('raw_calendar_date_max') or q6.get('raw_date_max') or q6.get('raw_trade_date_max')} "
          f"cache_range={q6.get('cache_range')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
