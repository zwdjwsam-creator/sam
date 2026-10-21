# -*- coding: utf-8 -*-
"""0836 continue — expand product mapping matrix + rules edge batch + update-chain fields."""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
OUT = Path(
    r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650"
)
HUB = Path(
    r"E:\BLACKBOX\运行\外部大脑信箱\agents\chatgpt\inbox\BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150\v2\continue_0010\correction_0650"
)
SHARDS = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\shards")
LOG = OUT / "content_0836_continue.log"
CACHE_REL = ROOT / "数据" / "回测缓存" / "releases" / "BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439"
CLEAN_CUR = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
UPDATE_SCOPE = ROOT / "运行" / "BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json"
JQ_RULE = ROOT / "运行" / "BLACKBOX_JQ_INCREMENTAL_DOWNLOAD_RULE_CURRENT.json"
DAILY = ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_DATA_MANIFEST_CURRENT.json"


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def log(msg: str) -> None:
    line = f"{now()} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def write_json(p: Path, o) -> None:
    p.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")


def sync(name: str) -> None:
    src = OUT / name
    if src.exists():
        HUB.mkdir(parents=True, exist_ok=True)
        (HUB / name).write_bytes(src.read_bytes())


def map_products_from_ledger() -> list[dict]:
    led = OUT / "PRODUCT_STAGE_LEDGER_75.csv"
    rows = list(csv.DictReader(led.open("r", encoding="utf-8-sig", newline="")))
    clean = json.loads(CLEAN_CUR.read_text(encoding="utf-8-sig"))
    std = Path(clean["standard_root"])
    out = []
    for r in rows:
        pid = r.get("product_id") or r.get("PRODUCT_ID") or ""
        if not pid:
            continue
        cache_p = CACHE_REL / pid
        # authority hints from prior columns
        auth = r.get("authority_path") or r.get("content_0836_path") or ""
        row = {
            "product_id": pid,
            "cache_dir": str(cache_p),
            "cache_exists": cache_p.exists(),
            "cache_entries": [x.name for x in cache_p.iterdir()][:12] if cache_p.exists() else [],
            "cache_has_parquet": bool(list(cache_p.rglob("*.parquet"))[:1]) if cache_p.exists() else False,
            "prior_authority_path": auth,
            "prior_authority_exists": Path(auth).exists() if auth else False,
            "content_0836_status": r.get("content_0836_status") or "",
            "mapping_status": "PENDING",
            "edges": [],
        }
        # classify
        if pid == "FUND_LIKE_ASSET_VIEW_R1":
            row["mapping_status"] = "LOGICAL_VIEW"
            row["edges"] = [
                {
                    "layer": "CACHE_VIEW",
                    "path": str(cache_p / "VIEW.json"),
                    "evidence": "VIEW.json unions ETF_DAILY+FUND_DAILY",
                }
            ]
        elif row["cache_has_parquet"]:
            row["mapping_status"] = "CACHE_MATERIALIZED"
            row["edges"] = [{"layer": "CACHE", "path": str(cache_p), "evidence": "parquet_or_partition"}]
        elif row["cache_exists"] and not row["cache_has_parquet"]:
            row["mapping_status"] = "CACHE_DIR_EMPTY_OR_VIEW_ONLY"
        else:
            row["mapping_status"] = "NO_CACHE_DIR"
        # cleaning relative guess for minute/daily names
        for rel in (
            f"price/{pid}",
            f"finance/{pid}",
            "price/ETF_1m" if "ETF_MINUTE_1M" in pid else None,
            "price/ETF_5m" if "ETF_MINUTE_5M" in pid else None,
            "price/A股_stock_1m" if "STOCK_MINUTE_1M" in pid or "A股" in pid else None,
        ):
            if not rel:
                continue
            p = std / rel
            if p.exists():
                row["edges"].append(
                    {
                        "layer": "CLEAN_STANDARD",
                        "path": str(p),
                        "resolved": str(p.resolve()),
                        "evidence": "path_exists_under_CURRENT_standard",
                    }
                )
                if row["mapping_status"] in {"NO_CACHE_DIR", "CACHE_DIR_EMPTY_OR_VIEW_ONLY", "PENDING"}:
                    row["mapping_status"] = "CLEAN_PRESENT_CACHE_PARTIAL"
        out.append(row)
    return out


def rules_edge_batch(limit: int = 315) -> dict:
    files = sorted(SHARDS.glob("RULES_ACTIVE_SHARD_*.jsonl"))
    status = Counter()
    edges = []
    unresolved = []
    for sf in files:
        with sf.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                st = row.get("edge_status") or row.get("status") or "NO_STATUS"
                status[st] += 1
                item = {
                    "shard": sf.name,
                    "edge_status": st,
                    "src": row.get("src") or row.get("source"),
                    "resolved": row.get("resolved") or row.get("path"),
                    "raw_token": (row.get("raw_token") or "")[:200],
                    "line": row.get("line"),
                    "field": row.get("field"),
                }
                if st in {
                    "RESOLVED",
                    "EXISTS",
                    "OK",
                    "BROKEN_CONFIRMED",
                    "DYNAMIC_OR_PLACEHOLDER",
                    "RULE_ID_OR_STATUS_UNRESOLVED",
                    "NOT_A_PATH",
                    "LEGACY_HOST_SPECIFIC",
                    "EXTERNAL",
                }:
                    edges.append(item)
                else:
                    unresolved.append(item)
                if len(edges) + len(unresolved) >= limit:
                    break
        if len(edges) + len(unresolved) >= limit:
            break
    # write shard edges jsonl
    outp = OUT / "RULE_EDGES_CONTENT_0836.jsonl"
    with outp.open("w", encoding="utf-8") as f:
        for e in edges + unresolved:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return {
        "shard_files": [f.name for f in files],
        "status_counts": dict(status),
        "edges_written": len(edges) + len(unresolved),
        "path": str(outp),
        "note": "Full 315-line shard dump as content edges; not V4 summary alone",
    }


def update_chain_fields() -> dict:
    """Extract published/asof/covered fields from update anchors — columnar, not UNKNOWN fill."""
    found = []
    for label, path in (
        ("UPDATE_SCOPE", UPDATE_SCOPE),
        ("JQ_RULE", JQ_RULE),
        ("DAILY_MANIFEST", DAILY),
        ("CLEAN_CURRENT", CLEAN_CUR),
    ):
        if not path.exists():
            found.append({"src": label, "path": str(path), "status": "MISSING"})
            continue
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        hits = []

        def walk(o, jpath=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    p2 = f"{jpath}.{k}" if jpath else k
                    kl = k.lower()
                    if any(
                        t in kl
                        for t in (
                            "asof",
                            "published",
                            "generated",
                            "covered",
                            "hist_end",
                            "cursor",
                            "watermark",
                            "overlap",
                            "tip",
                            "target",
                            "finance_asof",
                            "daily_asof",
                            "cleaning_as_of",
                        )
                    ):
                        hits.append(
                            {
                                "json_path": p2,
                                "value": v if not isinstance(v, (dict, list)) else type(v).__name__,
                            }
                        )
                    if isinstance(v, (dict, list)) and len(hits) < 80:
                        walk(v, p2)
            elif isinstance(o, list):
                for i, v in enumerate(o[:40]):
                    walk(v, f"{jpath}[{i}]")

        walk(data)
        found.append({"src": label, "path": str(path), "fields": hits, "n": len(hits)})
    return {"at": now(), "sources": found}


def main() -> int:
    t0 = time.time()
    log("CONTINUE_0836_START")
    mapping = map_products_from_ledger()
    write_json(OUT / "PRODUCT_MAPPING_MATRIX_0836.json", {"at": now(), "n": len(mapping), "rows": mapping})
    status_c = Counter(r["mapping_status"] for r in mapping)
    log(f"mapping n={len(mapping)} status={dict(status_c)}")

    rules = rules_edge_batch(315)
    write_json(OUT / "RULES_EDGE_BATCH_0836.json", rules)
    log(f"rules edges written={rules['edges_written']} status={rules['status_counts']}")

    upd = update_chain_fields()
    write_json(OUT / "UPDATE_CHAIN_FIELDS_0836.json", upd)
    log(f"update fields sources={len(upd['sources'])}")

    # append to runtime logic
    logic = OUT / "BLACKBOX_RUNTIME_LOGIC_CANDIDATE_0836.md"
    extra = [
        "",
        "## 6. 续跑扩展（0836 continue）",
        f"- at: {now()}",
        f"- product mapping matrix: n={len(mapping)} status={dict(status_c)} → PRODUCT_MAPPING_MATRIX_0836.json",
        f"- rules edges content dump: {rules['edges_written']} lines → RULE_EDGES_CONTENT_0836.jsonl",
        f"- update chain fields extracted from anchors → UPDATE_CHAIN_FIELDS_0836.json",
        "",
    ]
    with logic.open("a", encoding="utf-8") as f:
        f.write("\n".join(extra))

    # master progress bump
    master = OUT / "MASTER_PROGRESS_0836.md"
    master.write_text(
        f"""# CONTENT_0836_PROGRESS

status: **PARTIAL_CONTINUE_CONTENT**
phase: CONTINUE_MAPPING_RULES_UPDATE
worker_pid: {os.getpid()}
updated_at: {now()}
elapsed_sec: {round(time.time()-t0,1)}
SYSTEM_INVENTORY_ACCEPTANCE: false

## Continue deltas
- PRODUCT_MAPPING_MATRIX_0836.json — {len(mapping)} products; {dict(status_c)}
- RULE_EDGES_CONTENT_0836.jsonl — {rules['edges_written']} edges (315 shard lines)
- UPDATE_CHAIN_FIELDS_0836.json — asof/published/covered fields from anchors

local: `{OUT}`
""",
        encoding="utf-8",
    )
    for n in (
        "PRODUCT_MAPPING_MATRIX_0836.json",
        "RULES_EDGE_BATCH_0836.json",
        "RULE_EDGES_CONTENT_0836.jsonl",
        "UPDATE_CHAIN_FIELDS_0836.json",
        "BLACKBOX_RUNTIME_LOGIC_CANDIDATE_0836.md",
        "MASTER_PROGRESS_0836.md",
    ):
        sync(n)
    log(f"CONTINUE_0836_DONE elapsed={round(time.time()-t0,1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
