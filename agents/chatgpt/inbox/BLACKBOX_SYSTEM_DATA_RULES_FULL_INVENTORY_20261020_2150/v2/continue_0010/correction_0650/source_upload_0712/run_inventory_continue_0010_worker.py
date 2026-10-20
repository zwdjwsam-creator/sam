# -*- coding: utf-8 -*-
"""0010 continue worker — readonly inventory queue + parser v3 + STATUS_PROGRESS."""
from __future__ import annotations

import csv
import json
import os
import re
import time
import traceback
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
V2 = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2")
OUT = V2 / "continue_0010"
CKPT = OUT / "checkpoints"
LOG = OUT / "worker.log"
STATUS = OUT / "STATUS_PROGRESS.json"
QUEUE = OUT / "PRODUCT_QUEUE.jsonl"
HUB = Path(
    r"E:\BLACKBOX\运行\外部大脑信箱\agents\chatgpt\inbox\BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150\v2\continue_0010"
)
PIDFILE = OUT / "WORKER_PID.json"
PLACEHOLDER_RE = re.compile(
    r"<[^>]+>|\{[^}]+\}|YYYYMMDD|<asof>|YOUR_|TODO_|FIXME_|%\([^)]+\)s"
)


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def log(msg: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    line = f"{now()} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def write_status(**kw) -> None:
    body = {
        "updated_at": now(),
        "task": "BLACKBOX_SYSTEM_INVENTORY_CONTINUE_20261021_0010",
        "parent": "BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150",
        **kw,
    }
    STATUS.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
    HUB.mkdir(parents=True, exist_ok=True)
    (HUB / "STATUS_PROGRESS.json").write_text(
        STATUS.read_text(encoding="utf-8"), encoding="utf-8"
    )


def classify_token_v3(tok: str, src: Path, line: int, field: str) -> list[dict]:
    if not tok:
        return []
    if "\n" in tok or "\r" in tok:
        return [
            {
                "src": str(src),
                "raw_token": tok[:80],
                "line": line,
                "field": field,
                "edge_status": "NOT_A_PATH",
                "edge_type": "MULTILINE",
                "resolved": "",
            }
        ]
    parts = re.split(r"[;；]\s*(?=E:|[A-Za-z]:\\|/|规则库|记忆盘|经验卡)", tok)
    if len(parts) > 1:
        out: list[dict] = []
        for p in parts:
            out.extend(classify_token_v3(p.strip(), src, line, field + "+split"))
        return out
    tok = tok.strip().strip("`'\".,;)）]")
    if PLACEHOLDER_RE.search(tok):
        return [
            {
                "src": str(src),
                "raw_token": tok[:240],
                "line": line,
                "field": field,
                "edge_status": "DYNAMIC_OR_PLACEHOLDER",
                "edge_type": "PATH_TEMPLATE",
                "resolved": "",
            }
        ]
    if tok.startswith(("http://", "https://", "#")):
        return [
            {
                "src": str(src),
                "raw_token": tok[:240],
                "line": line,
                "field": field,
                "edge_status": "EXTERNAL",
                "edge_type": "URL_OR_ANCHOR",
                "resolved": tok if tok.startswith("http") else "",
            }
        ]
    if "|" in tok or tok.startswith("##"):
        return [
            {
                "src": str(src),
                "raw_token": tok[:120],
                "line": line,
                "field": field,
                "edge_status": "NOT_A_PATH",
                "edge_type": "PROSE_OR_TABLE",
                "resolved": "",
            }
        ]
    if re.match(r"^[Dd]:[\\/]", tok) or "D:\\Cursor" in tok or "D:/Cursor" in tok:
        return [
            {
                "src": str(src),
                "raw_token": tok[:240],
                "line": line,
                "field": field,
                "edge_status": "LEGACY_HOST_SPECIFIC",
                "edge_type": "PATH_REF",
                "resolved": tok,
            }
        ]
    if "secrets" in tok.lower() or "github_hub_token" in tok.lower():
        return [
            {
                "src": str(src),
                "raw_token": tok[:240],
                "line": line,
                "field": field,
                "edge_status": "SECRET_PATH_REF_NOT_READ",
                "edge_type": "PATH_REF",
                "resolved": "",
            }
        ]
    if re.match(r"^[A-Za-z]:[\\/]", tok):
        cand = Path(tok)
    elif tok.startswith(
        (
            "规则库",
            "契约",
            "脚本",
            "运行",
            "数据",
            "研究系统",
            "_OPS",
            "任务",
            "记忆盘",
            "经验卡",
            "DAILY_RESEARCH",
            "参考资料",
            ".cursor",
        )
    ):
        cand = ROOT / tok.replace("/", "\\")
    else:
        cand = src.parent / tok.replace("/", "\\")
    try:
        exists = cand.exists()
    except OSError:
        return [
            {
                "src": str(src),
                "raw_token": tok[:240],
                "line": line,
                "field": field,
                "edge_status": "PARSE_ERROR",
                "edge_type": "PATH_REF",
                "resolved": str(cand),
            }
        ]
    return [
        {
            "src": str(src),
            "raw_token": tok[:240],
            "line": line,
            "field": field,
            "edge_status": "RESOLVED" if exists else "BROKEN_CONFIRMED",
            "edge_type": "PATH_REF",
            "resolved": str(cand),
        }
    ]


def run_parser_regression_v3() -> dict:
    tests = []
    e1 = classify_token_v3("数据/研究报告/日增量/<asof>/", ROOT / "AGENTS.md", 1, "t")
    tests.append(("template_dynamic", e1[0]["edge_status"] == "DYNAMIC_OR_PLACEHOLDER"))
    e2 = classify_token_v3(r"E:\BLACKBOX\经验卡;E:\BLACKBOX\记忆盘", ROOT / "AGENTS.md", 1, "t")
    tests.append(("semicolon_split", len(e2) == 2))
    e3 = classify_token_v3(r"D:\CursorDualRouteConfig\foo", ROOT / "AGENTS.md", 1, "t")
    tests.append(("legacy_d", e3[0]["edge_status"] == "LEGACY_HOST_SPECIFIC"))
    ok = all(t[1] for t in tests)
    res = {"PASS": ok, "cases": [{"name": a, "ok": b} for a, b in tests]}
    (OUT / "parser_regression_v3.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return res


def strict_read_text(p: Path):
    raw = p.read_bytes()
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        try:
            return raw.decode("utf-8-sig"), "utf-8-sig"
        except UnicodeDecodeError as e:
            return None, f"DECODE_UNVERIFIED:{e}"


def load_authorities():
    cache = json.loads(
        (ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json").read_text(encoding="utf-8")
    )
    clean = json.loads(
        (ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json").read_text(encoding="utf-8")
    )
    side_p = ROOT / "运行" / "BLACKBOX_SIDECAR_CACHE_PRODUCTS_CURRENT.json"
    sidecar = json.loads(side_p.read_text(encoding="utf-8")) if side_p.exists() else {"products": {}}
    catalog = {}
    with (ROOT / "数据" / "回测缓存" / "registry" / "CACHE_PRODUCT_CATALOG.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for r in csv.DictReader(f):
            catalog[r["product_id"]] = r
    uni = json.loads(
        (
            ROOT
            / "规则库"
            / "data_dictionary"
            / "unified_market_data_plane_registry_r1.json"
        ).read_text(encoding="utf-8")
    )
    return cache, clean, sidecar, catalog, uni


def resolve_product_authority(pid, cache, clean, sidecar, catalog, uni):
    main_root = Path(cache["release_root"])
    main_path = main_root / pid
    row = {
        "product_id": pid,
        "authority_kind": "",
        "authority_path": "",
        "exists": False,
        "status": "PENDING",
        "reason": "",
        "in_main_cache_catalog": pid in catalog,
    }
    if "REGISTRY" in pid:
        reg = ROOT / "数据" / "回测缓存" / "registry"
        for p in reg.iterdir():
            nu = p.name.upper()
            if "MANIFEST" in pid and "MANIFEST" in nu:
                row.update(
                    authority_kind="CACHE_REGISTRY_FILE",
                    authority_path=str(p),
                    exists=True,
                    status="VERIFIED_WITHIN_DECLARED_SCOPE",
                    reason="registry_file_not_main_cache_subdir",
                )
                return row
            if "DEPENDENCY" in pid and "DEPENDENCY" in nu:
                row.update(
                    authority_kind="CACHE_REGISTRY_FILE",
                    authority_path=str(p),
                    exists=True,
                    status="VERIFIED_WITHIN_DECLARED_SCOPE",
                    reason="registry_file_not_main_cache_subdir",
                )
                return row
        row.update(
            authority_kind="REGISTRY_EXPECTED",
            authority_path=str(reg),
            exists=False,
            status="NOT_IN_MAIN_CACHE_ROOT",
            reason="registry_product_not_a_cache_subdir",
        )
        return row
    sp = (sidecar.get("products") or {}).get(pid)
    if sp and sp.get("cache_product_path"):
        p = Path(sp["cache_product_path"])
        row.update(
            authority_kind="SIDECAR_CACHE",
            authority_path=str(p),
            exists=p.exists(),
            status="VERIFIED_WITHIN_DECLARED_SCOPE" if p.exists() else "BLOCKED",
            reason="sidecar_CURRENT",
        )
        return row
    if main_path.exists():
        row.update(
            authority_kind="MAIN_CACHE_RELEASE",
            authority_path=str(main_path),
            exists=True,
            status="PENDING_COVERAGE",
            reason="main_cache_dir",
        )
        return row
    if "MINUTE" in pid:
        products = uni.get("products") or {}
        meta = products.get(pid) if isinstance(products, dict) else None
        if isinstance(meta, dict):
            for k in ("clean_path", "clean", "raw_root", "raw", "source_path", "path"):
                if meta.get(k) and Path(str(meta[k])).exists():
                    row.update(
                        authority_kind="MINUTE_PLANE_REGISTRY",
                        authority_path=str(meta[k]),
                        exists=True,
                        status="VERIFIED_PARTIAL",
                        reason=f"unified_registry.{k}",
                    )
                    return row
        std = Path(clean.get("standard_root") or "")
        if std.exists():
            for pattern in ("**/A股_stock_1m", "**/A股_stock_5m", "**/ETF_1m", "**/ETF_5m"):
                for p in std.glob(pattern):
                    pl = str(p).lower()
                    if (
                        ("1M" in pid and "1m" in pl)
                        or ("5M" in pid and "5m" in pl)
                        or ("30M" in pid and "30m" in pl)
                        or ("60M" in pid and "60m" in pl)
                    ):
                        row.update(
                            authority_kind="CLEANING_MINUTE_PLANE",
                            authority_path=str(p),
                            exists=True,
                            status="VERIFIED_PARTIAL",
                            reason="cleaning_standard_minute_dir",
                        )
                        return row
        row.update(
            authority_kind="MINUTE_NOT_IN_MAIN_CACHE",
            authority_path=str(main_path),
            exists=False,
            status="NOT_IN_MAIN_CACHE_ROOT",
            reason="minute_lives_on_clean_or_raw_plane",
        )
        return row
    if "CBOND" in pid or pid.startswith("TUSHARE_"):
        for c in list((ROOT / "运行").glob("*CBOND*CURRENT*"))[:30]:
            if c.is_file():
                row.update(
                    authority_kind="CBOND_CURRENT_OR_EXTERNAL",
                    authority_path=str(c),
                    exists=True,
                    status="VERIFIED_PARTIAL",
                    reason="cbond_sidecar_or_current",
                )
                return row
        ext = ROOT / "数据" / "外部证据"
        row.update(
            authority_kind="EXTERNAL_EVIDENCE_ROOT",
            authority_path=str(ext),
            exists=ext.exists(),
            status="NOT_IN_MAIN_CACHE_ROOT",
            reason="cbond_under_external_plane_not_main_cache",
        )
        return row
    row.update(
        authority_kind="UNKNOWN",
        authority_path=str(main_path),
        exists=False,
        status="NOT_IN_MAIN_CACHE_ROOT",
        reason="absent_from_main_cache_root",
    )
    return row


def probe_all_partitions(pid: str, pdir: Path) -> dict:
    out = {
        "product_id": pid,
        "n_parquet_files_capped": 0,
        "year_parts": [],
        "date_min": "",
        "date_max": "",
        "n_codes": "",
        "columns": "",
        "time_fields": "",
        "validation_grain": "",
        "error": "",
        "status": "PENDING",
    }
    if not pdir.exists():
        out.update(status="BLOCKED", error="MISSING_DIR")
        return out
    files = []
    years = set()
    try:
        for p in pdir.rglob("*.parquet"):
            files.append(p)
            m = re.search(r"year[=_]?(\d{4})", str(p), re.I)
            if m:
                years.add(m.group(1))
            if len(files) >= 400:
                break
    except OSError as e:
        out.update(status="BLOCKED", error=type(e).__name__)
        return out
    out["n_parquet_files_capped"] = len(files)
    out["year_parts"] = sorted(years)
    if not files:
        out.update(status="VERIFIED_PARTIAL", validation_grain="NO_PARQUET")
        return out
    try:
        import pyarrow.dataset as ds

        by_year = {}
        for f in files:
            m = re.search(r"year[=_]?(\d{4})", str(f), re.I)
            y = m.group(1) if m else "NA"
            by_year.setdefault(y, f)
        sample = list(by_year.values())
        dataset = ds.dataset([str(f) for f in sample], format="parquet")
        cols = [f.name for f in dataset.schema]
        out["columns"] = ",".join(cols[:50])
        time_cols = [
            c
            for c in cols
            if c.lower()
            in {
                "date",
                "signal_date",
                "trade_date",
                "day",
                "asof",
                "pubdate",
                "pub_date",
                "statdate",
                "stat_date",
                "pit_available_from",
                "known_at",
                "event_date",
                "announcement_date",
            }
        ]
        out["time_fields"] = ",".join(time_cols)
        code_cols = [
            c
            for c in cols
            if c.lower() in {"code", "order_book_id", "security", "symbol", "stock_code"}
        ]
        if time_cols:
            pref = None
            for cand in (
                "date",
                "signal_date",
                "trade_date",
                "pubDate",
                "pub_date",
                "statDate",
                "stat_date",
                "pit_available_from",
            ):
                for c in time_cols:
                    if c.lower() == cand.lower() or c == cand:
                        pref = c
                        break
                if pref:
                    break
            pref = pref or time_cols[0]
            cols_read = [pref] + (code_cols[:1] if code_cols else [])
            table = dataset.to_table(columns=cols_read)
            vals = [x.as_py() for x in table.column(pref) if x.as_py() is not None]
            if vals:
                out["date_min"] = str(min(vals))
                out["date_max"] = str(max(vals))
            if code_cols:
                out["n_codes"] = str(
                    len({x.as_py() for x in table.column(code_cols[0]) if x.as_py() is not None})
                )
            out["validation_grain"] = (
                f"ALL_YEAR_PARTS_SAMPLED_nfiles={len(sample)}_NOT_FULL_ROWSCAN"
            )
            out["status"] = "VERIFIED_PARTIAL"
        else:
            out.update(validation_grain="SCHEMA_ONLY_NO_TIME_COL", status="VERIFIED_PARTIAL")
    except Exception as e:  # noqa: BLE001
        out.update(
            error=f"{type(e).__name__}:{e}",
            validation_grain="FILE_LIST_ONLY",
            status="VERIFIED_PARTIAL",
        )
    return out


def recompute_broken() -> dict:
    shards = V2 / "shards"
    active = []
    for p in shards.glob("RULES_ACTIVE_SHARD_*.jsonl"):
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                active.append(json.loads(line))
    edges = []
    decode_issues = []
    for r in active:
        path = Path(r["path"])
        if not path.exists():
            continue
        text, enc = strict_read_text(path)
        if text is None:
            decode_issues.append({"path": str(path), "status": enc})
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for m in re.finditer(r"`([^`\n]{3,240})`", line):
                edges.extend(classify_token_v3(m.group(1), path, i, "inline_code"))
            for m in re.finditer(r"(E:[\\/]BLACKBOX[^\s`\"'|<>]{0,200})", line):
                edges.extend(classify_token_v3(m.group(1), path, i, "abs"))
    c = Counter(e["edge_status"] for e in edges)
    broken = [e for e in edges if e["edge_status"] == "BROKEN_CONFIRMED"]
    with (OUT / "RULE_LINKS_RECOMPUTED_V3.jsonl").open("w", encoding="utf-8") as f:
        for e in edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    with (OUT / "RULE_LINKS_BROKEN_CONFIRMED_V3.jsonl").open("w", encoding="utf-8") as f:
        for e in broken:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    summary = {
        "active_rules_scanned": len(active),
        "edges": len(edges),
        "status_counts": dict(c),
        "broken_confirmed": len(broken),
        "decode_unverified": len(decode_issues),
        "regression": run_parser_regression_v3(),
    }
    (OUT / "LINKS_RECOMPUTE_SUMMARY.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def build_queue(cache, clean, sidecar, catalog, uni):
    pids = set(catalog.keys())
    main = Path(cache["release_root"])
    if main.exists():
        pids |= {p.name for p in main.iterdir() if p.is_dir()}
    pids |= set((sidecar.get("products") or {}).keys())
    up = uni.get("products") or {}
    if isinstance(up, dict):
        pids |= set(up.keys())
    return [
        {
            **resolve_product_authority(pid, cache, clean, sidecar, catalog, uni),
            "queue_status": "PENDING",
            "updated_at": now(),
        }
        for pid in sorted(pids)
    ]


def save_queue(queue) -> None:
    with QUEUE.open("w", encoding="utf-8") as f:
        for r in queue:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def flush_hub() -> None:
    HUB.mkdir(parents=True, exist_ok=True)
    for name in (
        "STATUS_PROGRESS.json",
        "LINKS_RECOMPUTE_SUMMARY.json",
        "parser_regression_v3.json",
        "PRODUCT_QUEUE.jsonl",
        "PRODUCT_AUTHORITY_MAP.csv",
        "PRODUCT_COVERAGE_PROBES_V2.csv",
        "RULE_LINKS_BROKEN_CONFIRMED_V3.jsonl",
        "WORKER_PID.json",
        "MASTER_PROGRESS_0010.md",
        "STRATEGIES_STATIC_V2.csv",
        "UPDATE_SOURCES_STATIC_V2.csv",
    ):
        src = OUT / name
        if src.exists():
            (HUB / name).write_bytes(src.read_bytes())


def deepen_static():
    strategies = []
    scripts = ROOT / "脚本"
    if scripts.exists():
        for p in scripts.glob("*.py"):
            name = p.name.lower()
            if any(k in name for k in ("backtest", "strategy", "live", "autorun", "research_os", "dual_pool")):
                text, enc = strict_read_text(p)
                strategies.append(
                    {
                        "strategy_id": p.stem,
                        "kind": "SCRIPT_ENTRY",
                        "entry": str(p),
                        "decode": enc,
                        "required_products": "STOCK_DAILY_PIT_R1"
                        if text and "STOCK_DAILY" in text
                        else "UNKNOWN",
                        "status": "STATIC_PARSED_HEAD",
                    }
                )
    updates = []
    inc = json.loads(
        (ROOT / "运行" / "BLACKBOX_JQ_INCREMENTAL_DOWNLOAD_RULE_CURRENT.json").read_text(
            encoding="utf-8"
        )
    )
    for ds in inc.get("datasets") or []:
        updates.append(
            {
                "source_id": ds.get("dataset_id"),
                "increment_class": ds.get("increment_class"),
                "raw_rel": ds.get("raw_rel"),
                "clean_product": ds.get("clean_product"),
                "cache_product": ds.get("cache_product"),
                "watermark": ds.get("asof_target")
                or inc.get("generated_at_cn")
                or "RULE_GENERATED_AT_ONLY",
                "code_ref": "运行/BLACKBOX_JQ_INCREMENTAL_DOWNLOAD_RULE_CURRENT.json",
                "status": "CONTRACT_WATERMARK_AS_STATED",
            }
        )
    return strategies, updates


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CKPT.mkdir(parents=True, exist_ok=True)
    HUB.mkdir(parents=True, exist_ok=True)
    PIDFILE.write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "argv": list(__import__("sys").argv),
                "python": __import__("sys").executable,
                "started_at": now(),
                "log": str(LOG),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (HUB / "WORKER_PID.json").write_bytes(PIDFILE.read_bytes())
    t0 = time.time()
    arm_p = Path(r"E:\BLACKBOX\运行\外部大脑信箱\_hub_patrol_10h_3m_arm.json")
    deadline_arm = (
        json.loads(arm_p.read_text(encoding="utf-8")).get("deadline_at") if arm_p.exists() else None
    )
    log("WORKER_START")
    reg = run_parser_regression_v3()
    log(f"parser_v3 PASS={reg.get('PASS')}")
    link_sum = recompute_broken()
    log(f"broken_v3={link_sum.get('broken_confirmed')} counts={link_sum.get('status_counts')}")
    cache, clean, sidecar, catalog, uni = load_authorities()
    queue = build_queue(cache, clean, sidecar, catalog, uni)
    save_queue(queue)
    strategies, updates = deepen_static()
    with (OUT / "STRATEGIES_STATIC_V2.csv").open("w", encoding="utf-8-sig", newline="") as f:
        if strategies:
            w = csv.DictWriter(f, fieldnames=list(strategies[0].keys()))
            w.writeheader()
            w.writerows(strategies)
    with (OUT / "UPDATE_SOURCES_STATIC_V2.csv").open("w", encoding="utf-8-sig", newline="") as f:
        if updates:
            w = csv.DictWriter(f, fieldnames=list(updates[0].keys()))
            w.writeheader()
            w.writerows(updates)
    with (OUT / "PRODUCT_AUTHORITY_MAP.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(queue[0].keys()), extrasaction="ignore")
        w.writeheader()
        w.writerows(queue)
    write_status(
        phase="AUTHORITY_MAPPED_LINKS_RECOMPUTED",
        denominator_products=len(queue),
        status_counts=dict(Counter(q["status"] for q in queue)),
        broken_confirmed_v3=link_sum.get("broken_confirmed"),
        parser_v3_pass=reg.get("PASS"),
        worker_pid=os.getpid(),
        deadline_arm=deadline_arm,
    )
    flush_hub()
    probes = []
    for i, item in enumerate(queue):
        if deadline_arm and datetime.now(CN) > datetime.fromisoformat(deadline_arm):
            log("ARM_DEADLINE_STOP")
            break
        pid = item["product_id"]
        write_status(
            phase="PRODUCT_COVERAGE_PROBE",
            denominator_products=len(queue),
            status_counts=dict(
                Counter(q.get("queue_status") or q.get("status") for q in queue)
            ),
            broken_confirmed_v3=link_sum.get("broken_confirmed"),
            worker_pid=os.getpid(),
            deadline_arm=deadline_arm,
            current_product=pid,
            current_index=i,
            elapsed_sec=round(time.time() - t0, 1),
        )
        ap = Path(item["authority_path"]) if item.get("authority_path") else None
        if (
            ap
            and ap.exists()
            and ap.is_dir()
            and item.get("status") in {"PENDING_COVERAGE", "VERIFIED_PARTIAL", "PENDING"}
        ):
            item["queue_status"] = "RUNNING"
            pr = probe_all_partitions(pid, ap)
            probes.append(pr)
            item["queue_status"] = pr["status"]
            item["probe_date_min"] = pr.get("date_min")
            item["probe_date_max"] = pr.get("date_max")
            item["probe_grain"] = pr.get("validation_grain")
            item["updated_at"] = now()
            log(
                f"PROBED {pid} {pr['status']} {pr.get('date_min')}..{pr.get('date_max')} years={pr.get('year_parts')}"
            )
        else:
            item["queue_status"] = item.get("status") or "BLOCKED"
            item["updated_at"] = now()
        if i % 5 == 0:
            save_queue(queue)
            if probes:
                with (OUT / "PRODUCT_COVERAGE_PROBES_V2.csv").open(
                    "w", encoding="utf-8-sig", newline=""
                ) as f:
                    w = csv.DictWriter(f, fieldnames=list(probes[0].keys()))
                    w.writeheader()
                    w.writerows(probes)
            (CKPT / f"ckpt_{i:04d}.json").write_text(
                json.dumps({"i": i, "pid": pid, "at": now()}, ensure_ascii=False),
                encoding="utf-8",
            )
            flush_hub()
    save_queue(queue)
    if probes:
        with (OUT / "PRODUCT_COVERAGE_PROBES_V2.csv").open(
            "w", encoding="utf-8-sig", newline=""
        ) as f:
            w = csv.DictWriter(f, fieldnames=list(probes[0].keys()))
            w.writeheader()
            w.writerows(probes)
    with (OUT / "PRODUCT_AUTHORITY_MAP.csv").open("w", encoding="utf-8-sig", newline="") as f:
        keys = sorted({k for r in queue for k in r.keys()})
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(queue)
    sc = Counter(q.get("queue_status") or q.get("status") for q in queue)
    master = f"""# CONTINUE_0010_PROGRESS

status: **PARTIAL_CONTINUE_WITH_CHECKPOINT**
worker_pid: {os.getpid()}
elapsed_sec: {round(time.time() - t0, 1)}
parser_v3_pass: {reg.get("PASS")}
broken_confirmed_v3: {link_sum.get("broken_confirmed")}
edge_status_counts: {dict(link_sum.get("status_counts") or {})}
products_denominator: {len(queue)}
queue_status_counts: {dict(sc)}
probes_written: {len(probes)}

## 口径
- 主 Cache 缺失 ≠ 丢数据（NOT_IN_MAIN_CACHE_ROOT / sidecar / clean）
- DYNAMIC/<asof> 不进 BROKEN_CONFIRMED
- 日线按 year 分区抽样

local: `{OUT}`
"""
    (OUT / "MASTER_PROGRESS_0010.md").write_text(master, encoding="utf-8")
    write_status(
        phase="BATCH_PASS_COMPLETE_OR_BUDGET",
        denominator_products=len(queue),
        status_counts=dict(sc),
        broken_confirmed_v3=link_sum.get("broken_confirmed"),
        probes=len(probes),
        worker_pid=os.getpid(),
        deadline_arm=deadline_arm,
        elapsed_sec=round(time.time() - t0, 1),
        overall="PARTIAL_CONTINUE_WITH_CHECKPOINT",
    )
    flush_hub()
    log("WORKER_PASS_DONE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        log("FATAL\n" + traceback.format_exc())
        write_status(phase="FATAL", error=traceback.format_exc()[-2000:], worker_pid=os.getpid())
        raise
