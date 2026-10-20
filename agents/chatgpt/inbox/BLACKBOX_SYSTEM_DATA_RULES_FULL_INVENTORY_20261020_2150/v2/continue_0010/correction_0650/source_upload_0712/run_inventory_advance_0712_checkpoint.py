# -*- coding: utf-8 -*-
"""0712 one-shot checkpoint: stage ledger + FUND_NAV fragment stats + source SHA + wait flag."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
import time
import traceback
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
BASE = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010")
OUT = BASE / "correction_0650"
HUB = Path(
    r"E:\BLACKBOX\运行\外部大脑信箱\agents\chatgpt\inbox\BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150\v2\continue_0010\correction_0650"
)
ST = Path(r"E:\BLACKBOX\运行\外部大脑信箱")
SCRIPTS = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\脚本")


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def log(msg: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    line = f"{now()} {msg}"
    print(line, flush=True)
    with (OUT / "advance_0712.log").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pid_alive(pid: int) -> dict:
    import subprocess

    out = {"pid": pid, "alive": False, "command_line": None, "creation_date": None}
    try:
        r = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"Get-CimInstance Win32_Process -Filter \"ProcessId={pid}\" | "
                "Select-Object ProcessId,CommandLine,CreationDate | ConvertTo-Json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.stdout.strip():
            out["alive"] = True
            out["raw"] = r.stdout[:1500]
    except Exception as e:  # noqa: BLE001
        out["error"] = f"{type(e).__name__}:{e}"
    return out


def load_queue():
    rows = []
    qp = BASE / "PRODUCT_QUEUE.jsonl"
    if qp.exists():
        for line in qp.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def deep_csv_index():
    p = OUT / "DEEP_COVERAGE_PROBES.csv"
    by = {}
    if not p.exists():
        return by
    with p.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            by[r["product_id"]] = r
    return by


def fragment_stats(pdir: Path, cap: int = 5000) -> dict:
    files = []
    years = set()
    try:
        for p in pdir.rglob("*.parquet"):
            files.append(p)
            m = re.search(r"year[=_]?(\d{4})", str(p), re.I)
            if m:
                years.add(m.group(1))
            if len(files) >= cap:
                break
    except OSError as e:
        return {"error": type(e).__name__, "files_discovered_capped": 0}
    return {
        "files_discovered_capped": len(files),
        "year_parts": sorted(years),
        "cap": cap,
        "hit_cap": len(files) >= cap,
    }


def fund_nav_all_years(pdir: Path) -> dict:
    """Read one sample per year partition for FUND_NAV-like product."""
    out = {
        "product_id": "FUND_NAV_OR_ETF",
        "years_read": [],
        "date_min": "",
        "date_max": "",
        "rows_actually_read": 0,
        "files_checked": 0,
        "pref": "",
        "error": "",
    }
    by_year = {}
    for p in pdir.rglob("*.parquet"):
        m = re.search(r"year[=_]?(\d{4})", str(p), re.I)
        y = m.group(1) if m else "NA"
        by_year.setdefault(y, p)
    if not by_year:
        out["error"] = "NO_PARQUET"
        return out
    try:
        import pyarrow.dataset as ds

        files = [str(by_year[y]) for y in sorted(by_year)]
        out["files_checked"] = len(files)
        out["years_read"] = sorted(by_year)
        dataset = ds.dataset(files, format="parquet")
        cols = [f.name for f in dataset.schema]
        pref = None
        for cand in ("date", "signal_date", "trade_date", "nav_date", "statDate"):
            for c in cols:
                if c.lower() == cand.lower():
                    pref = c
                    break
            if pref:
                break
        if not pref:
            out["error"] = "NO_DATE_COL"
            out["columns"] = cols[:40]
            return out
        out["pref"] = pref
        table = dataset.to_table(columns=[pref])
        vals = [x.as_py() for x in table.column(pref) if x.as_py() is not None]
        out["rows_actually_read"] = table.num_rows
        if vals:
            out["date_min"] = str(min(vals))
            out["date_max"] = str(max(vals))
    except Exception as e:  # noqa: BLE001
        out["error"] = f"{type(e).__name__}:{e}"
    return out


def main() -> int:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    HUB.mkdir(parents=True, exist_ok=True)
    log("ADVANCE_0712_CHECKPOINT_START")

    # worker evidence
    old_pid = 36544
    ev = pid_alive(old_pid)
    ev.update(
        {
            "role": "correction_0650_worker",
            "checked_at": now(),
            "last_log_line": "",
            "exit_inference": "ALIVE" if ev.get("alive") else "PROCESS_GONE_AFTER_BATCH_DONE",
        }
    )
    wlog = OUT / "worker.log"
    if wlog.exists():
        lines = wlog.read_text(encoding="utf-8", errors="replace").splitlines()
        ev["last_log_line"] = lines[-1] if lines else ""
        if any("CORRECTION_0650_BATCH_DONE" in x for x in lines[-20:]):
            ev["exit_inference"] = "NATURAL_END_CORRECTION_0650_BATCH_DONE"
    (OUT / "WORKER_36544_EXIT_EVIDENCE.json").write_text(
        json.dumps(ev, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    queue = load_queue()
    deep = deep_csv_index()
    stage_rows = []
    for q in queue:
        pid = q.get("product_id")
        d = deep.get(pid) or {}
        stage = "NOT_IN_DEEP_BATCH"
        if d:
            stage = "DEEP_YEAR_SAMPLE_DONE"
        if q.get("authority_kind") == "CACHE_REGISTRY_FILE":
            stage = "REGISTRY_FILE_SCOPED"
        if q.get("status") == "NOT_IN_MAIN_CACHE_ROOT":
            stage = "NOT_IN_MAIN_CACHE_ROOT"
        if "MINUTE" in (pid or "") and q.get("status") in {
            "VERIFIED_PARTIAL",
            "PENDING",
            "PENDING_COVERAGE",
        }:
            if stage == "NOT_IN_DEEP_BATCH":
                stage = "MINUTE_NEEDS_INDEX_OR_PLANE"
        stage_rows.append(
            {
                "product_id": pid,
                "authority_kind": q.get("authority_kind"),
                "authority_path": q.get("authority_path"),
                "queue_status_0010": q.get("queue_status") or q.get("status"),
                "deep_status": d.get("status", ""),
                "deep_grain": d.get("validation_grain", ""),
                "deep_date_min": d.get("date_min", ""),
                "deep_date_max": d.get("date_max", ""),
                "stage_0712": stage,
            }
        )
    with (OUT / "PRODUCT_STAGE_LEDGER_75.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(stage_rows[0].keys()))
        w.writeheader()
        w.writerows(stage_rows)
    sc = Counter(r["stage_0712"] for r in stage_rows)

    # FUND_NAV / ETF deeper year coverage
    fund_targets = []
    for q in queue:
        pid = q.get("product_id") or ""
        if any(k in pid for k in ("FUND_NAV", "ETF_DAILY", "FUND_DAILY", "STOCK_DAILY_PIT")):
            ap = Path(q["authority_path"]) if q.get("authority_path") else None
            if ap and ap.exists() and ap.is_dir():
                fund_targets.append((pid, ap))
    frag_rows = []
    for pid, ap in fund_targets:
        fs = fragment_stats(ap)
        deep_y = fund_nav_all_years(ap) if "NAV" in pid or "DAILY" in pid else {}
        row = {"product_id": pid, "authority_path": str(ap), **fs}
        if deep_y:
            row.update({f"read_{k}": v for k, v in deep_y.items() if k != "product_id"})
        frag_rows.append(row)
        log(f"FRAG {pid} files={fs.get('files_discovered_capped')} years={fs.get('year_parts')}")
    if frag_rows:
        keys = sorted({k for r in frag_rows for k in r})
        with (OUT / "FRAGMENT_COVERAGE_PRIORITY_0712.csv").open(
            "w", encoding="utf-8-sig", newline=""
        ) as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(frag_rows)

    # source SHA bundle
    src_files = [
        SCRIPTS / "run_inventory_correction_0650_worker.py",
        SCRIPTS / "run_inventory_continue_0010_worker.py",
        SCRIPTS / "run_inventory_advance_0712_checkpoint.py",
        OUT / "parser_regression_v4.json",
        OUT / "LINKS_RECOMPUTE_SUMMARY_V4.json",
    ]
    sha_rows = []
    for p in src_files:
        if p.exists():
            sha_rows.append(
                {
                    "path": str(p),
                    "sha256": sha256_file(p),
                    "bytes": p.stat().st_size,
                    "mtime": datetime.fromtimestamp(p.stat().st_mtime, CN).isoformat(
                        timespec="seconds"
                    ),
                }
            )
    (OUT / "SOURCE_SHA_BUNDLE_0712.json").write_text(
        json.dumps({"at": now(), "files": sha_rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    # copy sources into hub folder for upload
    src_hub = OUT / "source_upload_0712"
    src_hub.mkdir(exist_ok=True)
    for p in src_files:
        if p.exists() and p.suffix == ".py":
            (src_hub / p.name).write_bytes(p.read_bytes())

    status = {
        "updated_at": now(),
        "task": "BLACKBOX_SYSTEM_INVENTORY_REVIEW_AND_ADVANCE_20261021_0712",
        "parent": "BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150",
        "phase": "CHECKPOINT_0712_READY_WAIT_HUB_ACCEPT",
        "overall": "WAITING_HUB_ACCEPTANCE",
        "worker_36544": ev,
        "denominator_products": len(stage_rows),
        "stage_counts": dict(sc),
        "deep_probes_preserved": len(deep),
        "priority_fragments": len(frag_rows),
        "elapsed_sec": round(time.time() - t0, 1),
        "advance_pid": os.getpid(),
        "note": "Do not continue next batch until GPT/HUB accepts this checkpoint",
    }
    (OUT / "STATUS_PROGRESS.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (BASE / "STATUS_PROGRESS.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    master = f"""# ADVANCE_0712_CHECKPOINT — WAITING_HUB_ACCEPTANCE

at: {now()}
task: BLACKBOX_SYSTEM_INVENTORY_REVIEW_AND_ADVANCE_20261021_0712
status: **WAITING_HUB_ACCEPTANCE**

## Worker evidence
- pid 36544 alive={ev.get('alive')} inference={ev.get('exit_inference')}
- last_log: `{ev.get('last_log_line')}`

## 75-object stage ledger
- file: `PRODUCT_STAGE_LEDGER_75.csv`
- counts: {dict(sc)}
- deep_probes preserved: {len(deep)} (not re-run shallow 55)

## Priority fragment advance
- file: `FRAGMENT_COVERAGE_PRIORITY_0712.csv`
- products: {len(frag_rows)}

## Source SHA
- `SOURCE_SHA_BUNDLE_0712.json` + `source_upload_0712/*.py`

## Next
Cursor **stops auto-continue** until HUB outbox newer tip / explicit ACCEPT.
"""
    (OUT / "MASTER_PROGRESS_0712_CHECKPOINT.md").write_text(master, encoding="utf-8")

    # flush hub local
    for name in (
        "STATUS_PROGRESS.json",
        "MASTER_PROGRESS_0712_CHECKPOINT.md",
        "PRODUCT_STAGE_LEDGER_75.csv",
        "FRAGMENT_COVERAGE_PRIORITY_0712.csv",
        "SOURCE_SHA_BUNDLE_0712.json",
        "WORKER_36544_EXIT_EVIDENCE.json",
        "parser_regression_v4.json",
        "LINKS_RECOMPUTE_SUMMARY_V4.json",
    ):
        src = OUT / name
        if src.exists():
            (HUB / name).write_bytes(src.read_bytes())
    hub_src = HUB / "source_upload_0712"
    hub_src.mkdir(exist_ok=True)
    for p in (OUT / "source_upload_0712").glob("*.py"):
        (hub_src / p.name).write_bytes(p.read_bytes())

    # wait flag for dock
    wait = {
        "status": "WAITING_HUB_ACCEPTANCE",
        "at": now(),
        "after_task": "BLACKBOX_SYSTEM_INVENTORY_REVIEW_AND_ADVANCE_20261021_0712",
        "resume_only_when": "outbox tip newer than 20261021_0712 OR explicit ACCEPT in outbox",
        "checkpoint_local": str(OUT),
    }
    (ST / "_hub_WAIT_ACCEPTANCE.json").write_text(
        json.dumps(wait, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log("ADVANCE_0712_CHECKPOINT_DONE WAITING_HUB_ACCEPTANCE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        log("FATAL\n" + traceback.format_exc())
        raise
