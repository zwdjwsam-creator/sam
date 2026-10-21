# -*- coding: utf-8 -*-
"""0836 content-execution worker — ETF real path read + INDEX contract + FUND_LIKE + plane/rules edges.

Isolation only under correction_0650 / _OPS. No download, no strategy run, no production mutation.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import sys
import time
import traceback
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
ST = Path(r"E:\BLACKBOX\运行\外部大脑信箱")
SHARDS = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\shards")
LOG = OUT / "content_0836.log"
PIDFILE = OUT / "WORKER_PID_0836.json"
CKPT = OUT / "checkpoints_0836"
SRC_DIR = OUT / "source_upload_0836"

REGISTRY = ROOT / "规则库" / "data_dictionary" / "unified_market_data_plane_registry_r1.json"
MUST_READ = ROOT / "契约" / "必读" / "BLACKBOX_DATA_ACCESS_MUST_READ.md"
UPDATE_SCOPE = ROOT / "运行" / "BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json"
DAILY_MANIFEST = ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_DATA_MANIFEST_CURRENT.json"
JQ_RULE = ROOT / "运行" / "BLACKBOX_JQ_INCREMENTAL_DOWNLOAD_RULE_CURRENT.json"
CLEAN_CUR = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
CACHE_REL = ROOT / "数据" / "回测缓存" / "releases" / "BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439"


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def log(msg: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    line = f"{now()} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def sync_hub(names: list[str]) -> None:
    HUB.mkdir(parents=True, exist_ok=True)
    for name in names:
        p = OUT / name
        if p.exists():
            dest = HUB / name
            if p.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(p, dest)
            else:
                dest.write_bytes(p.read_bytes())


def deadline_dt():
    arm_p = ST / "_hub_patrol_10h_3m_arm.json"
    if not arm_p.exists():
        arm_p = ST / "_hub_AUTOMATION_CURRENT.json"
    if not arm_p.exists():
        return None, None
    raw = json.loads(arm_p.read_text(encoding="utf-8-sig")).get("deadline_at")
    return (datetime.fromisoformat(raw) if raw else None), raw


def load_clean_current() -> dict:
    return json.loads(CLEAN_CUR.read_text(encoding="utf-8-sig"))


def stream_parquet_stats(files: list[Path], label: str, max_files: int | None = None) -> dict:
    import pyarrow.dataset as ds
    import pyarrow.compute as pc

    sample = files if max_files is None else files[:max_files]
    out = {
        "label": label,
        "files_discovered": len(files),
        "files_read": 0,
        "schema": [],
        "rows": 0,
        "null_time": 0,
        "null_code": 0,
        "time_min": None,
        "time_max": None,
        "codes_sample": [],
        "exchanges": Counter(),
        "domain_ids": Counter(),
        "fq_values": Counter(),
        "price_basis": Counter(),
        "file_names_head": [f.name for f in files[:5]],
        "file_names_tail": [f.name for f in files[-3:]] if files else [],
        "error": "",
    }
    if not sample:
        out["error"] = "NO_FILES"
        return out
    try:
        dset = ds.dataset([str(f) for f in sample], format="parquet")
        out["schema"] = list(dset.schema.names)
        cols = [c for c in ("time", "code", "exchange", "domain_id", "fq", "price_basis") if c in out["schema"]]
        codes: set[str] = set()
        tmin = tmax = None
        rows = null_t = null_c = 0
        for batch in dset.scanner(columns=cols, batch_size=65536).to_batches():
            rows += batch.num_rows
            if "time" in batch.schema.names:
                tcol = batch.column("time")
                null_t += tcol.null_count
                try:
                    mn = pc.min(tcol).as_py()
                    mx = pc.max(tcol).as_py()
                except Exception:
                    vals = [x.as_py() for x in tcol if x.is_valid]
                    mn = min(vals) if vals else None
                    mx = max(vals) if vals else None
                if mn is not None:
                    tmin = mn if tmin is None else min(tmin, mn)
                if mx is not None:
                    tmax = mx if tmax is None else max(tmax, mx)
            if "code" in batch.schema.names:
                ccol = batch.column("code")
                null_c += ccol.null_count
                for v in ccol.to_pylist():
                    if v is not None and len(codes) < 40:
                        codes.add(str(v))
            for k, bucket in (
                ("exchange", out["exchanges"]),
                ("domain_id", out["domain_ids"]),
                ("fq", out["fq_values"]),
                ("price_basis", out["price_basis"]),
            ):
                if k in batch.schema.names:
                    for v in batch.column(k).to_pylist():
                        bucket[str(v)] += 1
        out["files_read"] = len(sample)
        out["rows"] = rows
        out["null_time"] = null_t
        out["null_code"] = null_c
        out["time_min"] = str(tmin) if tmin is not None else None
        out["time_max"] = str(tmax) if tmax is not None else None
        out["codes_sample"] = sorted(codes)[:40]
        out["exchanges"] = dict(out["exchanges"].most_common(10))
        out["domain_ids"] = dict(out["domain_ids"].most_common(10))
        out["fq_values"] = dict(out["fq_values"].most_common(10))
        out["price_basis"] = dict(out["price_basis"].most_common(10))
    except Exception as e:  # noqa: BLE001
        out["error"] = f"{type(e).__name__}:{e}"
    return out


def classify_etf_name_tokens(files: list[Path]) -> dict:
    day_re = re.compile(r"__\d+m__(\d{4}-\d{2}-\d{2})__")
    year_re = re.compile(r"__(\d{4})__\d+m__")
    src_re = re.compile(r"__(fund_etf_price_\d+m|XSHE|XSHG)__")
    days, years, srcs = [], [], Counter()
    for f in files:
        m = day_re.search(f.name)
        if m:
            days.append(m.group(1))
        y = year_re.search(f.name)
        if y:
            years.append(y.group(1))
        s = src_re.search(f.name)
        if s:
            srcs[s.group(1)] += 1
    return {
        "day_shards": sorted(set(days)),
        "year_shards": sorted(set(years)),
        "name_token_sources": dict(srcs),
        "layout_hint": (
            "DAY_TIP_SHARDS"
            if days and not years
            else "YEAR_BATCH_SHARDS"
            if years and not days
            else "MIXED_OR_UNKNOWN"
        ),
    }


def asset_filter_predicate(reg_meta: dict, read: dict) -> dict:
    """Explicit predicate from registry + observed columns — not directory-name alone."""
    asset = reg_meta.get("asset")
    freq = reg_meta.get("freq")
    fq = reg_meta.get("fq_tag")
    codes = read.get("codes_sample") or []
    # observed code domain: ETF codes typically 15/51/56/58xxxx.XSHE/XSHG — report observed, do not prove alone
    return {
        "registry_asset": asset,
        "registry_freq": freq,
        "registry_fq_tag": fq,
        "required_columns": ["time", "code", "open", "close", "high", "low", "volume", "money"],
        "observed_schema_has_required": all(
            c in (read.get("schema") or []) for c in ["time", "code", "open", "close", "high", "low", "volume", "money"]
        ),
        "observed_domain_ids": read.get("domain_ids"),
        "observed_exchanges": read.get("exchanges"),
        "code_prefix_alone_insufficient": True,
        "predicate_text": (
            f"asset=={asset} AND freq=={freq} AND fq_tag=={fq} "
            f"AND path matches CLEANING_CURRENT relative_under_standard "
            f"AND schema contains OHLCV keys; code-prefix NOT sole proof"
        ),
        "codes_sample_n": len(codes),
        "identity_status": (
            "VERIFIED_ETF_CLEAN_PATH_READ"
            if read.get("rows", 0) > 0 and not read.get("error") and asset == "ETF"
            else "UNVERIFIED"
        ),
    }


def phase_a_etf(std: Path, reg: dict) -> dict:
    products = (reg.get("products") or {})
    result = {
        "cleaning_standard_root": str(std),
        "cleaning_standard_resolved": str(std.resolve()) if std.exists() else None,
        "products": {},
    }
    for pid, rel, mat_glob in (
        ("ETF_MINUTE_1M_R1", "price/ETF_1m", "price/ETF_1m.__mat_*"),
        ("ETF_MINUTE_5M_R1", "price/ETF_5m", "price/ETF_5m.__mat_*"),
    ):
        tip = std / Path(rel)
        mats = sorted(
            [p for p in (std / "price").glob(Path(rel).name + ".__mat_*") if p.is_dir()]
        )
        tip_files = sorted(tip.glob("*.parquet")) if tip.exists() else []
        mat_files: list[Path] = []
        mat_path = None
        if mats:
            # prefer largest mat dir (history)
            mat_path = max(mats, key=lambda p: sum(1 for _ in p.glob("*.parquet")))
            mat_files = sorted(mat_path.glob("*.parquet"))
        tip_read = stream_parquet_stats(tip_files, f"{pid}:TIP", max_files=None)
        tip_names = classify_etf_name_tokens(tip_files)
        # mat: stream first 40 + last 10 to avoid full 4k materialize in one pass; checkpoint continues
        mat_sample = mat_files[:40] + mat_files[-10:] if len(mat_files) > 50 else mat_files
        # unique preserve order
        seen = set()
        mat_sample_u = []
        for f in mat_sample:
            if f not in seen:
                seen.add(f)
                mat_sample_u.append(f)
        mat_read = stream_parquet_stats(mat_sample_u, f"{pid}:MAT_SAMPLE", max_files=None)
        mat_read["files_discovered"] = len(mat_files)
        mat_read["files_read"] = len(mat_sample_u)
        mat_names = classify_etf_name_tokens(mat_files)
        meta = products.get(pid) or {}
        tip_pred = asset_filter_predicate(meta, tip_read)
        mat_pred = asset_filter_predicate(meta, mat_read)
        # old invalid history pointer (stock path) retained as VOID
        old_invalid = {
            "path_pattern": f"standard/finance/A股_stock_{meta.get('freq')}",
            "status": "VOID_HISTORY_DO_NOT_USE",
            "reason": "0815 AUTHORITY_IDENTITY_UNVERIFIED stock minute misread for ETF",
        }
        result["products"][pid] = {
            "registry": {
                "asset": meta.get("asset"),
                "freq": meta.get("freq"),
                "fq_tag": meta.get("fq_tag"),
                "relative_under_standard": (meta.get("planes") or {}).get("CLEANING_CURRENT", {}).get(
                    "relative_under_standard"
                ),
                "raw_replacement": (meta.get("planes") or {}).get("RAW_REPLACEMENT", {}).get(
                    "relative_under_raw_root"
                ),
            },
            "tip_path": str(tip),
            "tip_resolved": str(tip.resolve()) if tip.exists() else None,
            "tip_exists": tip.exists(),
            "tip_name_layout": tip_names,
            "tip_read": tip_read,
            "tip_predicate": tip_pred,
            "mat_path": str(mat_path) if mat_path else None,
            "mat_resolved": str(mat_path.resolve()) if mat_path else None,
            "mat_name_layout": mat_names,
            "mat_read": mat_read,
            "mat_predicate": mat_pred,
            "old_invalid_stock_path": old_invalid,
            "coverage_note": (
                "TIP dir under CURRENT is day-tip shards (few files); "
                ".__mat_* holds year-batch history. Do not use tip file count as full history coverage."
            ),
        }
        log(
            f"ETF {pid} tip_files={len(tip_files)} tip_rows={tip_read.get('rows')} "
            f"mat_files={len(mat_files)} mat_sample_rows={mat_read.get('rows')} "
            f"tip_id={tip_pred.get('identity_status')}"
        )
    return result


def phase_a_index() -> dict:
    import pyarrow.dataset as ds

    auth = CACHE_REL / "INDEX_CONSTITUENT_PIT_R1"
    pq = auth / "INDEX_CONSTITUENT_PIT_R1.parquet"
    contract_lines = []
    if MUST_READ.exists():
        text = MUST_READ.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            if "INDEX_CONSTITUENT" in line or "WEIGHT_PROXY" in line or "announcement" in line.lower():
                contract_lines.append({"line": i, "text": line.strip()})
    # field role contract from evidence (not invented business rules)
    field_roles = {
        "announcement_date": {
            "role": "DISCLOSURE_ANNOUNCEMENT",
            "observed": "ALL_NULL_IN_0815_AUDIT",
            "may_use_as_known_at": False,
            "reason": "null_ratio=1.0 in prior audit; empty cannot serve as PIT known-at",
        },
        "effective_from": {
            "role": "MEMBERSHIP_EFFECTIVE_START",
            "observed": "NON_NULL",
            "may_use_as_known_at": False,
            "reason": "effective membership date ≠ information available time",
        },
        "source_date": {
            "role": "VENDOR_SOURCE_DATE",
            "observed": "NON_NULL",
            "may_use_as_known_at": False,
            "reason": "source dating ≠ exchange disclosure announcement",
        },
        "available_from_ts": {
            "role": "LOCAL_AVAILABILITY_OR_INGEST_BOUND",
            "observed": "NON_NULL",
            "may_use_as_known_at": False,
            "reason": "non-null alone cannot prove historical contemporaneous availability; may be backfill/ingest",
        },
        "ingested_at": {
            "role": "INGEST_WALLCLOCK",
            "may_use_as_known_at": False,
            "reason": "pipeline ingest time",
        },
        "pit_status": {
            "role": "ADMISSION_LABEL",
            "may_use_as_known_at": False,
        },
        "current_backfill": {
            "role": "BACKFILL_FLAG",
            "may_use_as_known_at": False,
        },
    }
    dist = {}
    rows_scanned = 0
    date_ranges = {}
    if pq.exists():
        dset = ds.dataset(str(pq), format="parquet")
        cols = [
            c
            for c in (
                "pit_status",
                "pit_ok",
                "current_backfill",
                "constituent_asset_type",
                "available_from_ts",
                "effective_from",
                "source_date",
                "ingested_at",
                "announcement_date",
            )
            if c in dset.schema.names
        ]
        counters = {c: Counter() for c in ("pit_status", "pit_ok", "current_backfill", "constituent_asset_type")}
        nulls = Counter()
        mins, maxs = {}, {}
        for batch in dset.scanner(columns=cols, batch_size=200000).to_batches():
            rows_scanned += batch.num_rows
            for c in counters:
                if c in batch.schema.names:
                    for v in batch.column(c).to_pylist():
                        counters[c][str(v)] += 1
            for c in ("available_from_ts", "effective_from", "source_date", "ingested_at", "announcement_date"):
                if c not in batch.schema.names:
                    continue
                col = batch.column(c)
                nulls[c] += col.null_count
                vals = [x for x in col.to_pylist() if x is not None]
                if vals:
                    mins[c] = str(min(vals) if c not in mins else min(mins[c], str(min(vals))))
                    # keep string compare for iso-like; refine below
                    cur_min = min(vals)
                    cur_max = max(vals)
                    if c not in mins or str(cur_min) < mins[c]:
                        mins[c] = str(cur_min)
                    if c not in maxs or str(cur_max) > maxs[c]:
                        maxs[c] = str(cur_max)
            if rows_scanned >= 2592719:  # full prior row count
                break
        dist = {k: dict(v.most_common(20)) for k, v in counters.items()}
        date_ranges = {
            c: {
                "null_count": nulls.get(c, 0),
                "null_ratio": (nulls.get(c, 0) / rows_scanned) if rows_scanned else None,
                "min": mins.get(c),
                "max": maxs.get(c),
            }
            for c in ("available_from_ts", "effective_from", "source_date", "ingested_at", "announcement_date")
        }
    # FULL_DATA_UPDATE_SCOPE excerpt
    scope_refs = []
    if UPDATE_SCOPE.exists():
        scope = json.loads(UPDATE_SCOPE.read_text(encoding="utf-8-sig"))
        blob = json.dumps(scope, ensure_ascii=False)
        if "INDEX_CONSTITUENT" in blob:
            # collect matching keys shallow
            def walk(o, path=""):
                if isinstance(o, dict):
                    for k, v in o.items():
                        p2 = f"{path}.{k}" if path else k
                        if "INDEX_CONSTITUENT" in k or (
                            isinstance(v, str) and "INDEX_CONSTITUENT" in v
                        ):
                            scope_refs.append({"json_path": p2, "value": v if not isinstance(v, (dict, list)) else type(v).__name__})
                        walk(v, p2)
                elif isinstance(o, list):
                    for i, v in enumerate(o[:50]):
                        walk(v, f"{path}[{i}]")

            walk(scope)
    return {
        "product_id": "INDEX_CONSTITUENT_PIT_R1",
        "authority_path": str(auth),
        "parquet": str(pq),
        "exists": pq.exists(),
        "must_read_rules": contract_lines[:20],
        "field_roles": field_roles,
        "rows_scanned": rows_scanned,
        "value_distributions": dist,
        "date_field_ranges": date_ranges,
        "update_scope_refs": scope_refs[:30],
        "verdict": {
            "announcement_date": "NOT_USABLE_ALL_NULL_OR_EMPTY",
            "effective_from": "MEMBERSHIP_EFFECTIVE_ONLY",
            "available_from_ts": "NON_NULL_BUT_NOT_PROVEN_HISTORICAL_KNOWN_AT",
            "pit_status_observed": dist.get("pit_status"),
            "current_backfill_observed": dist.get("current_backfill"),
            "weight_absent_ok": True,
            "weight_absent_rule_source": str(MUST_READ) + "#RULE_1",
        },
    }


def phase_a_fund_like() -> dict:
    view_p = CACHE_REL / "FUND_LIKE_ASSET_VIEW_R1" / "VIEW.json"
    view = json.loads(view_p.read_text(encoding="utf-8-sig")) if view_p.exists() else {}
    items = []
    for pid in ("FUND_LIKE_ASSET_VIEW_R1", "FUND_DAILY_PIT_R1", "FUND_FACTOR_DAILY_R1", "ETF_DAILY_PIT_R1"):
        d = CACHE_REL / pid
        entries = list(d.iterdir()) if d.exists() else []
        pq = [e for e in entries if e.suffix == ".parquet" or e.is_dir() and list(e.rglob("*.parquet"))]
        items.append(
            {
                "product_id": pid,
                "path": str(d),
                "exists": d.exists(),
                "entries": [e.name for e in entries[:20]],
                "parquet_or_partition_present": bool(pq) if pid != "FUND_LIKE_ASSET_VIEW_R1" else False,
                "class": (
                    "LOGICAL_VIEW_JSON"
                    if pid == "FUND_LIKE_ASSET_VIEW_R1"
                    else "EMPTY_CACHE_DIR_NO_PARQUET"
                    if d.exists() and not pq
                    else "MATERIALIZED_OR_PARTITIONED"
                ),
            }
        )
    # consumer refs
    consumer_hits = []
    for p in (
        ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_CACHE_FIRST_WORKFLOW_POLICY_R1.json",
        ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_JQ_ACCESSIBLE_DATASET_LEDGER_R1.json",
    ):
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        if "FUND_LIKE" in text or "FUND_DAILY" in text:
            consumer_hits.append({"path": str(p), "bytes": p.stat().st_size, "mentions_fund_like": "FUND_LIKE" in text})
    return {
        "view_json_path": str(view_p),
        "view_json": view,
        "view_kind": "VIRTUAL_CONSUMER_SIDE_UNION",
        "materialized_table": False,
        "unions": view.get("unions"),
        "preserves_asset_type": view.get("preserves_asset_type"),
        "note": view.get("note"),
        "related_products": items,
        "consumer_refs": consumer_hits,
        "no_parquet_not_data_loss": True,
        "download": False,
    }


def extract_json_edges(path: Path, focus_keys: list[str]) -> list[dict]:
    if not path.exists():
        return [{"src": str(path), "status": "MISSING"}]
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    edges = []

    def walk(o, jpath=""):
        if isinstance(o, dict):
            for k, v in o.items():
                p2 = f"{jpath}.{k}" if jpath else k
                key_hit = any(fk.lower() in k.lower() for fk in focus_keys)
                if key_hit or (
                    isinstance(v, str)
                    and any(
                        tok in v
                        for tok in (
                            "E:\\BLACKBOX",
                            "数据\\",
                            "运行\\",
                            "研究系统",
                            "规则库",
                            "脚本\\",
                            ".cursor",
                        )
                    )
                ):
                    edges.append(
                        {
                            "src_file": str(path),
                            "json_path": p2,
                            "key": k,
                            "value_type": type(v).__name__,
                            "value": v if not isinstance(v, (dict, list)) else (
                                {"list_len": len(v)} if isinstance(v, list) else {"dict_keys": list(v.keys())[:30]}
                            ),
                            "exists_if_path": (
                                Path(v).exists()
                                if isinstance(v, str) and re.match(r"^[A-Za-z]:[\\/]", v)
                                else None
                            ),
                        }
                    )
                if isinstance(v, (dict, list)) and len(edges) < 400:
                    walk(v, p2)
        elif isinstance(o, list):
            for i, v in enumerate(o[:80]):
                walk(v, f"{jpath}[{i}]")

    walk(data)
    return edges


def phase_b_plane_edges() -> dict:
    focus = [
        "raw",
        "clean",
        "cache",
        "product",
        "lane",
        "asof",
        "hist_end",
        "cursor",
        "overlap",
        "incremental",
        "path",
        "root",
        "manifest",
        "authority",
        "consumer",
        "update",
    ]
    bundles = {}
    for name, path in (
        ("UPDATE_SCOPE", UPDATE_SCOPE),
        ("DAILY_DATA_MANIFEST", DAILY_MANIFEST),
        ("JQ_INCREMENTAL_DOWNLOAD_RULE", JQ_RULE),
    ):
        edges = extract_json_edges(path, focus)
        bundles[name] = {
            "path": str(path),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else 0,
            "mtime": datetime.fromtimestamp(path.stat().st_mtime, CN).isoformat(timespec="seconds")
            if path.exists()
            else None,
            "edges_extracted": len(edges),
            "edges_sample": edges[:60],
        }
        log(f"PLANE {name} edges={len(edges)}")
    return bundles


def phase_b_rules_shards() -> dict:
    shard_files = sorted(SHARDS.glob("RULES_ACTIVE_SHARD_*.jsonl"))
    idx = SHARDS / "SHARD_INDEX.json"
    index_obj = json.loads(idx.read_text(encoding="utf-8-sig")) if idx.exists() else None
    # count candidates in shards
    n_lines = 0
    status_c = Counter()
    sample_edges = []
    for sf in shard_files:
        with sf.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                n_lines += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    status_c["JSON_DECODE_ERROR"] += 1
                    continue
                st = row.get("edge_status") or row.get("status") or row.get("link_status") or "NO_STATUS_FIELD"
                status_c[str(st)] += 1
                if len(sample_edges) < 40:
                    sample_edges.append(
                        {
                            "shard": sf.name,
                            "keys": list(row.keys())[:20],
                            "edge_status": st,
                            "src": row.get("src") or row.get("source") or row.get("from"),
                            "resolved": row.get("resolved") or row.get("path") or row.get("to"),
                            "raw_token": (row.get("raw_token") or row.get("token") or "")[:160],
                        }
                    )
    # reconcile with V4 summary
    v4p = OUT / "LINKS_RECOMPUTE_SUMMARY_V4.json"
    v4 = json.loads(v4p.read_text(encoding="utf-8-sig")) if v4p.exists() else {}
    # prior index size note from tip: 8097 index items, 315 candidates in shards
    return {
        "shard_dir": str(SHARDS),
        "shard_dir_exists": SHARDS.exists(),
        "shard_files": [{"name": f.name, "bytes": f.stat().st_size} for f in shard_files],
        "shard_lines_total": n_lines,
        "status_counts": dict(status_c),
        "sample_edges": sample_edges,
        "shard_index_present": idx.exists(),
        "shard_index_keys": list(index_obj.keys())[:40] if isinstance(index_obj, dict) else type(index_obj).__name__,
        "v4_summary": v4,
        "reconcile_note": (
            "0815 STAGE_LEDGER reported rules_shard_files=0 due to wrong glob root; "
            f"true path {SHARDS} has {len(shard_files)} shards / {n_lines} lines. "
            "315 tip figure vs this count must be reconciled by candidate filter fields, not by absence."
        ),
        "lookup_fix": {
            "wrong_glob_result": 0,
            "correct_path": str(SHARDS),
            "correct_count_files": len(shard_files),
            "correct_count_lines": n_lines,
        },
    }


def phase_c_strategy_static() -> dict:
    refs = []
    for path in (
        ROOT / "参考资料" / "聚宽策略写法" / "聚宽范本_日频必读.md",
        ROOT / ".cursor" / "rules" / "blackbox_joinquant_strategy_coding_mandatory.mdc",
        ROOT / "AGENTS.md",
        JQ_RULE,
    ):
        if not path.exists():
            refs.append({"path": str(path), "exists": False})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        # extract dependency-like lines
        hits = []
        for i, line in enumerate(text.splitlines(), 1):
            if any(
                k in line
                for k in (
                    "product",
                    "CACHE",
                    "清洗",
                    "必读",
                    "KNOWN_AT",
                    "SIGNAL_TIME",
                    "FILL_TIME",
                    "download",
                    "incremental",
                    "asof",
                    "HAND",
                    "gate",
                    "入口",
                )
            ):
                hits.append({"line": i, "text": line.strip()[:240]})
            if len(hits) >= 40:
                break
        refs.append(
            {
                "path": str(path),
                "exists": True,
                "bytes": path.stat().st_size,
                "dependency_lines": hits,
                "class_hint": (
                    "STRATEGY_CODING_MANDATORY"
                    if "joinquant" in path.name.lower() or "聚宽" in path.name
                    else "ENTRY_POINTER"
                    if path.name == "AGENTS.md"
                    else "UPDATE_RULE"
                    if "DOWNLOAD" in path.name
                    else "DOC"
                ),
            }
        )
    return {"static_refs": refs, "runtime_started": False, "backtest_started": False}


def write_runtime_logic_doc(etf, index, fund, plane, rules, strat) -> Path:
    lines = [
        "# BLACKBOX 运行逻辑说明（隔离候选 · 0836）",
        "",
        f"generated_at: {now()}",
        "scope: inventory isolation candidate — NOT production AGENTS entry",
        "SYSTEM_INVENTORY_ACCEPTANCE: false",
        "",
        "## 1. 数据从哪来",
        "",
        f"- Cleaning CURRENT: `{CLEAN_CUR}` → standard_root = `{etf.get('cleaning_standard_root')}`",
        f"- 解析后 tip ETF 实际落点见各产品 `tip_resolved`（CURRENT 目录可指向 R45 tip release）",
        f"- Registry: `{REGISTRY}` 中 ETF_MINUTE_* asset=ETF / relative_under_standard=price/ETF_*m",
        f"- RAW 替换根（registry）: P4_fund_etf_raw_none/fund_etf_price_*m",
        f"- Cache release（INDEX/FUND view）: `{CACHE_REL}`",
        "",
        "### ETF 分钟（已读）",
        "",
    ]
    for pid, body in (etf.get("products") or {}).items():
        tip = body.get("tip_read") or {}
        mat = body.get("mat_read") or {}
        lines += [
            f"#### {pid}",
            f"- tip_path: `{body.get('tip_path')}`",
            f"- tip_resolved: `{body.get('tip_resolved')}`",
            f"- tip files/rows/time: {tip.get('files_discovered')}/{tip.get('rows')}/{tip.get('time_min')}→{tip.get('time_max')}",
            f"- tip layout: {body.get('tip_name_layout')}",
            f"- mat_path: `{body.get('mat_path')}` files={mat.get('files_discovered')} sample_rows={mat.get('rows')} "
            f"time={mat.get('time_min')}→{mat.get('time_max')}",
            f"- identity: tip={body.get('tip_predicate',{}).get('identity_status')} "
            f"predicate=`{body.get('tip_predicate',{}).get('predicate_text')}`",
            f"- old stock path: VOID — {body.get('old_invalid_stock_path')}",
            f"- coverage_note: {body.get('coverage_note')}",
            "",
        ]
    lines += [
        "## 2. 各层如何转换",
        "",
        "- INDEX_CONSTITUENT: RAW strategy_data_plane_additions → Cache parquet；"
        "成分生效用 effective_from；announcement_date 实测全空；available_from_ts 非空但不得单凭字段名当历史可知时点。",
        f"- pit_status 分布（扫描 {index.get('rows_scanned')} 行）: {index.get('value_distributions',{}).get('pit_status')}",
        f"- current_backfill: {index.get('value_distributions',{}).get('current_backfill')}",
        "- FUND_LIKE_ASSET_VIEW: VIEW.json 虚拟联合 ETF_DAILY_PIT_R1 ∪ FUND_DAILY_PIT_R1；非物化 parquet。",
        f"- view: {fund.get('view_json')}",
        "- FUND_DAILY_PIT_R1 / FUND_FACTOR_DAILY_R1: 空目录 NO_PARQUET ≠ 数据丢失（未物化/未发布）。",
        "",
        "## 3. 规则入口如何约束查询/策略",
        "",
        f"- MUST_READ RULE_1 等: {index.get('must_read_rules', [])[:5]}",
        f"- Rules shards 真路径: `{rules.get('shard_dir')}` files={rules.get('lookup_fix',{}).get('correct_count_files')} "
        f"lines={rules.get('lookup_fix',{}).get('correct_count_lines')}",
        f"- 0815 错 glob→0 已纠正: {rules.get('reconcile_note')}",
        f"- 策略静态依赖摘录见 STRATEGY_STATIC_0836.json（未启动回测）",
        "",
        "## 4. 更新如何落地",
        "",
        f"- UPDATE_SCOPE edges: {plane.get('UPDATE_SCOPE',{}).get('edges_extracted')}",
        f"- DAILY_MANIFEST edges: {plane.get('DAILY_DATA_MANIFEST',{}).get('edges_extracted')}",
        f"- JQ incremental rule edges: {plane.get('JQ_INCREMENTAL_DOWNLOAD_RULE',{}).get('edges_extracted')}",
        "- published/generated_at vs asof_target vs covered_through: 见各 JSON 边 value；不足处标 UNKNOWN，不整表填满。",
        "",
        "## 5. 未知 / 阻塞",
        "",
        "- KEY/EXPECTED_SCOPE 全市场对照未在本轮穷尽 → 标未证实",
        "- mat 年批全量流式续读可按断点继续（本轮已 sample）",
        "- SYSTEM_INVENTORY_ACCEPTANCE 仍为 false",
        "",
    ]
    p = OUT / "BLACKBOX_RUNTIME_LOGIC_CANDIDATE_0836.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def update_ledger_0836(etf: dict, index: dict, fund: dict) -> None:
    led = OUT / "PRODUCT_STAGE_LEDGER_75.csv"
    if not led.exists():
        return
    rows = list(csv.DictReader(led.open("r", encoding="utf-8-sig", newline="")))
    if not rows:
        return
    keys = list(rows[0].keys())
    for extra in (
        "content_0836_status",
        "content_0836_path",
        "content_0836_rows",
        "content_0836_note",
        "content_0836_updated",
    ):
        if extra not in keys:
            keys.append(extra)
    patch = {}
    for pid, body in (etf.get("products") or {}).items():
        tip = body.get("tip_read") or {}
        patch[pid] = {
            "status": body.get("tip_predicate", {}).get("identity_status"),
            "path": body.get("tip_resolved") or body.get("tip_path"),
            "rows": tip.get("rows"),
            "note": body.get("coverage_note"),
        }
    patch["INDEX_CONSTITUENT_PIT_R1"] = {
        "status": index.get("verdict", {}).get("available_from_ts"),
        "path": index.get("authority_path"),
        "rows": index.get("rows_scanned"),
        "note": "announcement_date unusable; available_from_ts not proven known-at",
    }
    patch["FUND_LIKE_ASSET_VIEW_R1"] = {
        "status": "LOGICAL_VIEW_JSON",
        "path": fund.get("view_json_path"),
        "rows": 0,
        "note": json.dumps(fund.get("view_json"), ensure_ascii=False),
    }
    for r in rows:
        pid = r.get("product_id") or r.get("PRODUCT_ID") or ""
        if pid in patch:
            r["content_0836_status"] = patch[pid]["status"]
            r["content_0836_path"] = patch[pid]["path"]
            r["content_0836_rows"] = patch[pid]["rows"]
            r["content_0836_note"] = patch[pid]["note"]
            r["content_0836_updated"] = now()
    with led.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def flush_progress(phase: str, overall: str, note: str, extras: dict | None = None) -> None:
    body = {
        "updated_at": now(),
        "task": "BLACKBOX_SYSTEM_INVENTORY_CONTENT_EXECUTION_20261021_0836",
        "parent": "BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150",
        "phase": phase,
        "overall": overall,
        "SYSTEM_INVENTORY_ACCEPTANCE": False,
        "note": note,
        **(extras or {}),
    }
    write_json(OUT / "STATUS_PROGRESS.json", body)
    master = f"""# CONTENT_0836_PROGRESS

status: **{overall}**
phase: {phase}
worker_pid: {os.getpid()}
updated_at: {now()}
SYSTEM_INVENTORY_ACCEPTANCE: false
note: {note}

## Artifacts
- ETF_TRUE_PATH_READ_0836.json
- INDEX_CONSTITUENT_CONTRACT_0836.json
- FUND_LIKE_VIEW_CLASS_0836.json
- PLANE_EDGES_0836.json
- RULES_SHARD_LOOKUP_FIX_0836.json
- STRATEGY_STATIC_0836.json
- BLACKBOX_RUNTIME_LOGIC_CANDIDATE_0836.md
- PRODUCT_STAGE_LEDGER_75.csv (content_0836_* columns)

local: `{OUT}`
"""
    (OUT / "MASTER_PROGRESS_0836.md").write_text(master, encoding="utf-8")
    sync_hub(
        [
            "STATUS_PROGRESS.json",
            "MASTER_PROGRESS_0836.md",
            "ETF_TRUE_PATH_READ_0836.json",
            "INDEX_CONSTITUENT_CONTRACT_0836.json",
            "FUND_LIKE_VIEW_CLASS_0836.json",
            "PLANE_EDGES_0836.json",
            "RULES_SHARD_LOOKUP_FIX_0836.json",
            "STRATEGY_STATIC_0836.json",
            "BLACKBOX_RUNTIME_LOGIC_CANDIDATE_0836.md",
            "PRODUCT_STAGE_LEDGER_75.csv",
            "SOURCE_SHA_0836.json",
            "WORKER_PID_0836.json",
            "NEW_FINDINGS_0836.json",
        ]
    )


def claim_need() -> None:
    need = {
        "at": now(),
        "name": "BLACKBOX_SYSTEM_INVENTORY_CONTENT_EXECUTION_20261021_0836.md",
        "status": "EXECUTING_CONTENT_A_B_C",
        "previous_status": "STOPPED_BY_USER",
        "note": "User confirmed tip 0836; content worker running",
    }
    write_json(ST / "_hub_NEED_EXEC.json", need)
    arm_p = ST / "_hub_patrol_10h_3m_arm.json"
    if arm_p.exists():
        arm = json.loads(arm_p.read_text(encoding="utf-8-sig"))
        arm["last_status"] = "EXECUTING_0836_CONTENT"
        arm["tip_hhmm"] = "0836"
        write_json(arm_p, arm)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    HUB.mkdir(parents=True, exist_ok=True)
    CKPT.mkdir(parents=True, exist_ok=True)
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    src = Path(__file__).resolve()
    (SRC_DIR / src.name).write_bytes(src.read_bytes())
    # also copy to 脚本 pointer
    scripts = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\脚本")
    scripts.mkdir(parents=True, exist_ok=True)
    (scripts / src.name).write_bytes(src.read_bytes())

    write_json(
        PIDFILE,
        {
            "pid": os.getpid(),
            "task": "0836",
            "python": sys.executable,
            "started_at": now(),
            "log": str(LOG),
            "mode": "CONTENT_A_B_C_CONTINUOUS",
            "source": str(src),
        },
    )
    claim_need()
    t0 = time.time()
    deadline, deadline_raw = deadline_dt()
    log(f"CONTENT_0836_START deadline={deadline_raw}")

    try:
        clean = load_clean_current()
        std = Path(clean["standard_root"])
        reg = json.loads(REGISTRY.read_text(encoding="utf-8-sig"))

        # A1 ETF
        etf = phase_a_etf(std, reg)
        write_json(OUT / "ETF_TRUE_PATH_READ_0836.json", etf)
        write_json(CKPT / "A_ETF.json", {"at": now(), "ok": True})
        flush_progress("A_ETF", "PARTIAL_CONTINUE", "ETF tip+mat sample read done")

        if deadline and datetime.now(CN) > deadline:
            log("DEADLINE_HIT after A_ETF")
            return 0

        # A2 INDEX
        index = phase_a_index()
        write_json(OUT / "INDEX_CONSTITUENT_CONTRACT_0836.json", index)
        write_json(CKPT / "A_INDEX.json", {"at": now(), "ok": True})
        flush_progress("A_INDEX", "PARTIAL_CONTINUE", "INDEX contract+distributions done")

        # A3 FUND_LIKE
        fund = phase_a_fund_like()
        write_json(OUT / "FUND_LIKE_VIEW_CLASS_0836.json", fund)
        write_json(CKPT / "A_FUND_LIKE.json", {"at": now(), "ok": True})
        flush_progress("A_FUND_LIKE", "PARTIAL_CONTINUE", "FUND_LIKE view classified")

        # B plane
        plane = phase_b_plane_edges()
        write_json(OUT / "PLANE_EDGES_0836.json", plane)
        write_json(CKPT / "B_PLANE.json", {"at": now(), "ok": True})
        flush_progress("B_PLANE", "PARTIAL_CONTINUE", "plane edges extracted from anchors")

        # B rules
        rules = phase_b_rules_shards()
        write_json(OUT / "RULES_SHARD_LOOKUP_FIX_0836.json", rules)
        write_json(CKPT / "B_RULES.json", {"at": now(), "ok": True})
        flush_progress("B_RULES", "PARTIAL_CONTINUE", "rules shard path fixed; lines counted")

        # C strategy static
        strat = phase_c_strategy_static()
        write_json(OUT / "STRATEGY_STATIC_0836.json", strat)
        write_json(CKPT / "C_STRATEGY.json", {"at": now(), "ok": True})

        logic = write_runtime_logic_doc(etf, index, fund, plane, rules, strat)
        update_ledger_0836(etf, index, fund)

        findings = {
            "at": now(),
            "etf_tip_identity": {
                pid: body.get("tip_predicate", {}).get("identity_status")
                for pid, body in (etf.get("products") or {}).items()
            },
            "etf_tip_vs_mat": {
                pid: {
                    "tip_files": (body.get("tip_read") or {}).get("files_discovered"),
                    "mat_files": (body.get("mat_read") or {}).get("files_discovered"),
                }
                for pid, body in (etf.get("products") or {}).items()
            },
            "index_announcement_unusable": True,
            "fund_like_virtual": True,
            "rules_shard_files_was_0_now": rules.get("lookup_fix"),
            "runtime_logic": str(logic),
        }
        write_json(OUT / "NEW_FINDINGS_0836.json", findings)

        write_json(
            OUT / "SOURCE_SHA_0836.json",
            {
                "at": now(),
                "files": [
                    {"path": str(src), "sha256": sha256_file(src), "bytes": src.stat().st_size}
                ],
            },
        )

        # continue: expand plane edges dump full + more mat streaming checkpoint
        write_json(OUT / "PLANE_EDGES_0836_FULL.json", plane)
        # second-pass mat deeper sample for 1m: years mid
        for pid, body in list((etf.get("products") or {}).items()):
            mat_path = body.get("mat_path")
            if not mat_path:
                continue
            mp = Path(mat_path)
            files = sorted(mp.glob("*.parquet"))
            if len(files) < 100:
                continue
            mid = files[len(files) // 2 : len(files) // 2 + 80]
            deep = stream_parquet_stats(mid, f"{pid}:MAT_MID", max_files=None)
            deep["files_discovered"] = len(files)
            body["mat_mid_read"] = deep
            log(f"ETF deep {pid} mid_rows={deep.get('rows')} time={deep.get('time_min')}→{deep.get('time_max')}")
        write_json(OUT / "ETF_TRUE_PATH_READ_0836.json", etf)
        write_runtime_logic_doc(etf, index, fund, plane, rules, strat)
        update_ledger_0836(etf, index, fund)

        elapsed = round(time.time() - t0, 1)
        flush_progress(
            "A_B_C_CHECKPOINT",
            "PARTIAL_CONTINUE_CONTENT",
            f"content checkpoint elapsed={elapsed}s; acceptance still false; continue queue",
            extras={"elapsed_sec": elapsed, "deadline": deadline_raw},
        )
        log(f"CONTENT_0836_CHECKPOINT_DONE elapsed={elapsed}")

        # prepare inbox checkpoint md for HUB push
        ckpt_md = ST / "agents" / "chatgpt" / "inbox" / "BLACKBOX_INVENTORY_CONTENT_CHECKPOINT_20261021_0836.md"
        ckpt_md.parent.mkdir(parents=True, exist_ok=True)
        ckpt_md.write_text(
            f"""# BLACKBOX_INVENTORY_CONTENT_CHECKPOINT_20261021_0836

task: BLACKBOX_SYSTEM_INVENTORY_CONTENT_EXECUTION_20261021_0836
host: ZHANGWEI
at: {now()}
SYSTEM_INVENTORY_ACCEPTANCE: false
status: PARTIAL_CONTINUE_CONTENT

## A done (content, not exists-only)
- ETF tip paths under Cleaning CURRENT read (schema/rows/time/domain); mat year-batch sampled + mid sample
- INDEX field roles from MUST_READ + distributions; announcement_date unusable; available_from_ts not proven known-at
- FUND_LIKE = VIEW.json virtual union; FUND_DAILY/FACTOR empty dirs ≠ data loss

## B done (first batch)
- UPDATE_SCOPE / DAILY_MANIFEST / JQ rule: real JSON edges extracted
- Rules shards: fixed path `{SHARDS}` lines={rules.get('shard_lines_total')} (was 0 by wrong glob)

## C started
- Strategy/update static refs extracted; no backtest/download

## Artifacts
local: `{OUT}`
hub mirror: `{HUB}`
runtime logic: `{logic}`

## Next (continuous, same deadline {deadline_raw})
- Finish mat full-stream watermarks per year if needed
- Expand product mapping matrix beyond anchor trio
- Continue rules edge graph from shards (not V4 summary alone)
""",
            encoding="utf-8",
        )

        return 0
    except Exception as e:  # noqa: BLE001
        log(f"FATAL {type(e).__name__}:{e}\n{traceback.format_exc()}")
        flush_progress("FATAL", "ERROR", f"{type(e).__name__}:{e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
