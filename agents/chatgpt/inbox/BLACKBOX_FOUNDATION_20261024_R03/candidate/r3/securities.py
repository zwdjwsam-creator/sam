"""Security classification used for dataset routing.

Routing must not send every code to the stock plane. Classification comes from the
published SECURITY_MASTER reference plane (``type`` plus listing start/end), cached once.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .file_index import INDEX_DIR, dir_signature, list_parquet

CACHE = INDEX_DIR / "security_master_index.json"

# asset class -> candidate dataset prefix per frequency
ASSET_FAMILY = {
    "stock": "STOCK",
    "etf": "ETF",
    "lof": "ETF",
    "fund": "ETF",
    "index": "INDEX",
}
SUPPORTED_ASSET_CLASSES = sorted(set(ASSET_FAMILY.values()))


def _norm(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v)[:10]
    return s if len(s) == 10 and s[4] == "-" else s


def build(root: str, *, force: bool = False) -> Dict[str, Any]:
    if not root:
        return {"root": None, "signature": None, "n_codes": 0, "by_type": {}, "codes": {},
                "n_files": 0, "note": "no SECURITY_MASTER root bound"}
    if os.path.isdir(root):
        sig = dir_signature(root)
    else:
        sig = {"dirs": {}, "n_parquet": 0}
    if not force and CACHE.is_file():
        try:
            c = json.loads(CACHE.read_text(encoding="utf-8"))
            if c.get("root") == root and c.get("signature") == sig:
                return c
        except Exception:
            pass
    import pyarrow.parquet as pq
    table: Dict[str, Dict[str, Any]] = {}
    files = sorted(list_parquet(root))
    for p in files:
        try:
            t = pq.read_table(p)
        except Exception:
            continue
        names = t.column_names
        code_col = next((c for c in ("index", "code", "security_code") if c in names), None)
        if not code_col:
            continue
        ty = t.column("type").to_pylist() if "type" in names else [None] * t.num_rows
        sd = t.column("start_date").to_pylist() if "start_date" in names else [None] * t.num_rows
        ed = t.column("end_date").to_pylist() if "end_date" in names else [None] * t.num_rows
        nm = t.column("display_name").to_pylist() if "display_name" in names else [None] * t.num_rows
        for code, typ, s, e, disp in zip(t.column(code_col).to_pylist(), ty, sd, ed, nm):
            if not code:
                continue
            prev = table.get(code)
            rec = {"type": (str(typ).lower() if typ else None), "start": _norm(s), "end": _norm(e),
                   "display_name": disp, "source_file": os.path.basename(p)}
            if prev is None:
                table[code] = rec
            else:
                # keep the earliest listing start and the widest end; keep a known type
                if rec["start"] and (not prev["start"] or rec["start"] < prev["start"]):
                    prev["start"] = rec["start"]
                if rec["end"] and (not prev["end"] or rec["end"] > prev["end"]):
                    prev["end"] = rec["end"]
                if not prev["type"] and rec["type"]:
                    prev["type"] = rec["type"]
    out = {"root": root, "signature": sig, "n_codes": len(table),
           "by_type": _count_types(table), "codes": table,
           "n_files": len(files)}
    CACHE.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def _count_types(table: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for v in table.values():
        k = v.get("type") or "unknown"
        out[k] = out.get(k, 0) + 1
    return out


def classify(map_doc: Dict[str, Any], codes: List[str]) -> Dict[str, Any]:
    """Return per-code classification plus explicit unknown codes."""
    table = map_doc.get("codes", {})
    per: Dict[str, Dict[str, Any]] = {}
    unknown: List[str] = []
    for c in codes:
        rec = table.get(c)
        if rec is None:
            unknown.append(c)
            per[c] = {"asset_class": None, "known": False}
            continue
        typ = rec.get("type")
        fam = ASSET_FAMILY.get(typ or "")
        per[c] = {"asset_class": fam, "master_type": typ, "known": True,
                  "listing_start": rec.get("start"), "listing_end": rec.get("end")}
    fams = {v["asset_class"] for v in per.values() if v.get("asset_class")}
    return {"per_code": per, "unknown_codes": unknown,
            "asset_classes": sorted(f for f in fams if f), "mixed": len(fams) > 1}
