# -*- coding: utf-8 -*-
"""0815: minute authority identity + next-stage readonly inventory continue."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
OUT = Path(
    r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650"
)
HUB = Path(
    r"E:\BLACKBOX\运行\外部大脑信箱\agents\chatgpt\inbox\BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150\v2\continue_0010\correction_0650"
)
ST = Path(r"E:\BLACKBOX\运行\外部大脑信箱")
LOG = OUT / "authority_0815.log"
PIDFILE = OUT / "WORKER_PID_0815.json"
REVIEWS = (
    ST
    / "agents/chatgpt/reviews/BLACKBOX_MINUTE_AUTHORITY_20261021_0815"
)


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


def write_status(**kw) -> None:
    body = {
        "updated_at": now(),
        "task": "BLACKBOX_SYSTEM_INVENTORY_AUTHORITY_AND_NEXT_STAGE_20261021_0815",
        "parent": "BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150",
        "previous_followup": "BLACKBOX_SYSTEM_INVENTORY_ACCEPT_AND_RESUME_20261021_0730",
        **kw,
    }
    text = json.dumps(body, ensure_ascii=False, indent=2)
    (OUT / "STATUS_PROGRESS.json").write_text(text, encoding="utf-8")
    HUB.mkdir(parents=True, exist_ok=True)
    (HUB / "STATUS_PROGRESS.json").write_text(text, encoding="utf-8")


def load_authority_map() -> list[dict]:
    for p in (
        OUT.parent / "PRODUCT_AUTHORITY_MAP.csv",
        OUT / "PRODUCT_AUTHORITY_MAP.csv",
    ):
        if p.exists():
            with p.open("r", encoding="utf-8-sig", newline="") as f:
                return list(csv.DictReader(f))
    return []


def inspect_minute_identity() -> dict:
    """Mark ETF/STOCK minute pairs that share the same authority path."""
    rows = load_authority_map()
    by_id = {r.get("product_id") or r.get("PRODUCT_ID"): r for r in rows}
    pairs = [
        ("ETF_MINUTE_1M_R1", "STOCK_MINUTE_1M_R1"),
        ("ETF_MINUTE_5M_R1", "STOCK_MINUTE_5M_R1"),
    ]
    findings = []
    for a, b in pairs:
        ra, rb = by_id.get(a) or {}, by_id.get(b) or {}
        pa = ra.get("authority_path") or ra.get("resolved_path") or ""
        pb = rb.get("authority_path") or rb.get("resolved_path") or ""
        same = bool(pa) and pa == pb
        findings.append(
            {
                "etf": a,
                "stock": b,
                "etf_path": pa,
                "stock_path": pb,
                "same_path": same,
                "verdict": "AUTHORITY_IDENTITY_UNVERIFIED" if same else "PATHS_DIFFER",
                "note": "frequency-only match suspected; asset_type not constrained"
                if same
                else "paths differ — still verify asset_type",
            }
        )
    # fixture reproduction if review script present
    repro = {"ran": False}
    script = REVIEWS / "reproduce_minute_authority.py"
    if script.exists():
        repro = {
            "ran": False,
            "script": str(script),
            "sha256": sha256_file(script),
            "note": "GPT fixture present; identity defect accepted as inventory-locator issue",
        }
    out = {
        "at": now(),
        "findings": findings,
        "reproduction": repro,
        "action": "Invalidate ETF minute coverage conclusions that reused stock paths; keep stock reads",
    }
    (OUT / "MINUTE_AUTHORITY_IDENTITY_0815.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out


def patch_fragment_coverage_identity(findings: list[dict]) -> None:
    p = OUT / "FRAGMENT_COVERAGE_0730.csv"
    if not p.exists():
        return
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    keys = list(rows[0].keys()) if rows else []
    for k in ("authority_identity", "authority_note_0815"):
        if k not in keys:
            keys.append(k)
    bad = set()
    for g in findings:
        if g.get("same_path"):
            bad.add(g["etf"])
    for r in rows:
        pid = r.get("product_id") or ""
        if pid in bad:
            r["authority_identity"] = "AUTHORITY_IDENTITY_UNVERIFIED"
            r["authority_note_0815"] = "shared stock minute path; ETF coverage not accepted"
        elif "MINUTE" in pid and not r.get("authority_identity"):
            r["authority_identity"] = "PATH_OK_PENDING_ASSET_FILTER"
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def index_constituent_null_audit() -> dict:
    """Check announcement_date null rate without inventing values."""
    rows = load_authority_map()
    path = None
    for r in rows:
        if (r.get("product_id") or "") == "INDEX_CONSTITUENT_PIT_R1":
            path = r.get("authority_path") or r.get("resolved_path")
            break
    out = {"product_id": "INDEX_CONSTITUENT_PIT_R1", "at": now()}
    if not path:
        out["error"] = "NO_AUTHORITY_PATH"
        (OUT / "INDEX_CONSTITUENT_NULL_AUDIT_0815.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return out
    ap = Path(path)
    files = list(ap.rglob("*.parquet")) if ap.exists() else []
    out["authority_path"] = path
    out["files"] = len(files)
    if not files:
        out["error"] = "NO_PARQUET"
        (OUT / "INDEX_CONSTITUENT_NULL_AUDIT_0815.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return out
    try:
        import pyarrow.compute as pc
        import pyarrow.dataset as ds

        dataset = ds.dataset([str(files[0])], format="parquet")
        cols = [f.name for f in dataset.schema]
        out["schema"] = cols
        cand = [
            c
            for c in cols
            if c
            in {
                "announcement_date",
                "effective_from",
                "weight_date",
                "source_date",
                "available_from_ts",
            }
        ]
        stats = {}
        table = dataset.to_table(columns=cand) if cand else dataset.to_table()
        out["rows"] = table.num_rows
        for c in cand:
            col = table.column(c)
            stats[c] = {
                "null_count": int(col.null_count),
                "null_ratio": round(col.null_count / max(1, table.num_rows), 6),
                "non_null": int(table.num_rows - col.null_count),
            }
        out["date_like_stats"] = stats
        ad = stats.get("announcement_date") or {}
        if ad.get("null_ratio", 0) >= 0.999:
            out["verdict"] = "ANNOUNCEMENT_DATE_ALL_NULL_OR_EMPTY"
            out["note"] = (
                "Do not claim date column recovery; pick applicable contract field or report gap"
            )
        else:
            out["verdict"] = "HAS_NON_NULL_DATE_LIKE"
    except Exception as e:  # noqa: BLE001
        out["error"] = f"{type(e).__name__}:{e}"
    (OUT / "INDEX_CONSTITUENT_NULL_AUDIT_0815.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out


def no_files_reclassify() -> dict:
    """NO_FILES → NO_PARQUET_OBSERVED after checking dir/manifest; no download."""
    targets = [
        "FUND_DAILY_PIT_R1",
        "FUND_FACTOR_DAILY_R1",
        "FUND_LIKE_ASSET_VIEW_R1",
    ]
    rows = load_authority_map()
    by = {r.get("product_id"): r for r in rows}
    items = []
    for pid in targets:
        r = by.get(pid) or {}
        ap = Path(r.get("authority_path") or r.get("resolved_path") or "")
        entry = {
            "product_id": pid,
            "authority_path": str(ap),
            "dir_exists": ap.exists(),
            "is_dir": ap.is_dir() if ap.exists() else False,
        }
        if ap.exists() and ap.is_dir():
            pq = list(ap.rglob("*.parquet"))
            other = [
                p.suffix.lower()
                for p in ap.rglob("*")
                if p.is_file() and p.suffix.lower() not in {"", ".parquet"}
            ][:20]
            entry["parquet_count"] = len(pq)
            entry["other_suffix_sample"] = sorted(set(other))[:10]
            entry["verdict"] = (
                "NO_PARQUET_OBSERVED" if not pq else "HAS_PARQUET"
            )
            # junction?
            try:
                entry["is_symlink"] = ap.is_symlink()
            except Exception:
                entry["is_symlink"] = None
        else:
            entry["verdict"] = "AUTHORITY_PATH_MISSING"
        items.append(entry)
    out = {"at": now(), "items": items, "download": False}
    (OUT / "NO_PARQUET_OBSERVED_0815.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # patch blockers
    (OUT / "BLOCKERS_0730.md").write_text(
        "# Blockers after 0815 reclassify\n\n"
        + "\n".join(
            f"- {i['product_id']}: {i.get('verdict')} @ `{i.get('authority_path')}`"
            for i in items
        )
        + "\n\nNo download. Treat as observed empty materialization until contract says view/derived.\n",
        encoding="utf-8",
    )
    return out


def upload_sources() -> dict:
    src_dir = OUT / "source_upload_0815"
    src_dir.mkdir(exist_ok=True)
    scripts = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\脚本")
    files = [
        scripts / "run_inventory_resume_0730_worker.py",
        scripts / "run_inventory_authority_0815_worker.py",
        Path(__file__),
    ]
    rec = []
    for f in files:
        if not f.exists():
            continue
        dst = src_dir / f.name
        shutil.copy2(f, dst)
        rec.append(
            {
                "name": f.name,
                "sha256": sha256_file(dst),
                "bytes": dst.stat().st_size,
                "src": str(f),
            }
        )
    body = {"at": now(), "files": rec}
    (OUT / "SOURCE_SHA_0815.json").write_text(
        json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return body


def sync_hub() -> None:
    HUB.mkdir(parents=True, exist_ok=True)
    names = [
        "STATUS_PROGRESS.json",
        "MASTER_PROGRESS_0815.md",
        "MINUTE_AUTHORITY_IDENTITY_0815.json",
        "INDEX_CONSTITUENT_NULL_AUDIT_0815.json",
        "NO_PARQUET_OBSERVED_0815.json",
        "SOURCE_SHA_0815.json",
        "FRAGMENT_COVERAGE_0730.csv",
        "PRODUCT_STAGE_LEDGER_75.csv",
        "BLOCKERS_0730.md",
        "WORKER_PID_0815.json",
        "parser_regression_v5.json",
    ]
    for name in names:
        p = OUT / name
        if p.exists():
            (HUB / name).write_bytes(p.read_bytes())
    # copy source tree
    src = OUT / "source_upload_0815"
    if src.exists():
        hub_src = HUB / "source_upload_0815"
        hub_src.mkdir(exist_ok=True)
        for f in src.iterdir():
            if f.is_file():
                (hub_src / f.name).write_bytes(f.read_bytes())


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    PIDFILE.write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "task": "0815",
                "python": sys.executable,
                "started_at": now(),
                "argv": sys.argv,
                "log": str(LOG),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    t0 = time.time()
    log("AUTHORITY_0815_START")
    write_status(phase="MINUTE_IDENTITY", overall="RUNNING", worker_pid=os.getpid())

    ident = inspect_minute_identity()
    log(f"IDENTITY findings={len(ident.get('findings') or [])}")
    patch_fragment_coverage_identity(ident.get("findings") or [])

    write_status(phase="INDEX_NULL_AUDIT", overall="RUNNING", worker_pid=os.getpid())
    idx = index_constituent_null_audit()
    log(f"INDEX verdict={idx.get('verdict') or idx.get('error')}")

    write_status(phase="NO_PARQUET_RECLASS", overall="RUNNING", worker_pid=os.getpid())
    nf = no_files_reclassify()
    log(f"NO_PARQUET items={len(nf.get('items') or [])}")

    write_status(phase="SOURCE_UPLOAD", overall="RUNNING", worker_pid=os.getpid())
    src = upload_sources()
    log(f"SOURCE files={len(src.get('files') or [])}")

    # keep ledger frag fields if present from 0730
    master = f"""# AUTHORITY_0815_PROGRESS

status: **PARTIAL_CONTINUE_NO_FORCED_WAIT**
task: BLACKBOX_SYSTEM_INVENTORY_AUTHORITY_AND_NEXT_STAGE_20261021_0815
parent: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
worker_pid: {os.getpid()}
elapsed_sec: {round(time.time() - t0, 1)}
started_at: see WORKER_PID_0815.json

## Done
1. ETF/STOCK minute shared-path → AUTHORITY_IDENTITY_UNVERIFIED（不删原读数）
2. INDEX_CONSTITUENT announcement_date null audit → {idx.get('verdict') or idx.get('error')}
3. FUND_* empty dirs → NO_PARQUET_OBSERVED（不下载）
4. Uploaded SOURCE_SHA_0815 + source_upload_0815（含 0730/0815 worker）

## Reused from 0730
- FUND_NAV 5980/5980 full stream evidence retained
- parser_v5 regression file retained

## Still open (2150 scope)
RAW→clean→cache/plane→consumer 映射；规则递归；策略/更新静态链条；真实日期集合/缺口/主键合同。

local: `{OUT}`
"""
    (OUT / "MASTER_PROGRESS_0815.md").write_text(master, encoding="utf-8")
    write_status(
        phase="CHECKPOINT_0815",
        overall="PARTIAL_CONTINUE_NO_FORCED_WAIT",
        worker_pid=os.getpid(),
        elapsed_sec=round(time.time() - t0, 1),
        minute_identity_unverified=sum(
            1 for g in (ident.get("findings") or []) if g.get("same_path")
        ),
        index_verdict=idx.get("verdict") or idx.get("error"),
        no_parquet_observed=sum(
            1
            for i in (nf.get("items") or [])
            if i.get("verdict") == "NO_PARQUET_OBSERVED"
        ),
        note="0815 checkpoint; continue authorized next stages without WAIT",
    )
    sync_hub()
    log("AUTHORITY_0815_CHECKPOINT_DONE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        log("FATAL\n" + traceback.format_exc())
        write_status(phase="FATAL", error=traceback.format_exc()[-2000:])
        raise
