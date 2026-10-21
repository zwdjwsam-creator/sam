# -*- coding: utf-8 -*-
"""0730 resume worker — fix day/fragments/zip/dotdot/cursor guess; continuous readonly batches."""
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
OUT = Path(
    r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650"
)
HUB = Path(
    r"E:\BLACKBOX\运行\外部大脑信箱\agents\chatgpt\inbox\BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150\v2\continue_0010\correction_0650"
)
ST = Path(r"E:\BLACKBOX\运行\外部大脑信箱")
LOG = OUT / "resume_0730.log"
PIDFILE = OUT / "WORKER_PID_0730.json"
PLACEHOLDER_RE = re.compile(
    r"<[^>]+>|\{[^}]+\}|YYYYMMDD|<asof>|YOUR_|TODO_|FIXME_|%\([^)]+\)s"
)
RULE_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")
FORMULA_RE = re.compile(r"(<=|>=|==|!=|<|>)|KNOWN_AT|SIGNAL_TIME|FILL_TIME")


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
        "task": "BLACKBOX_SYSTEM_INVENTORY_ACCEPT_AND_RESUME_20261021_0730",
        "parent": "BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150",
        "confirmation": "ACCEPT_0712_CHECKPOINT",
        **kw,
    }
    text = json.dumps(body, ensure_ascii=False, indent=2)
    (OUT / "STATUS_PROGRESS.json").write_text(text, encoding="utf-8")
    HUB.mkdir(parents=True, exist_ok=True)
    (HUB / "STATUS_PROGRESS.json").write_text(text, encoding="utf-8")


def classify_token_v5(tok: str, src: Path, line: int, field: str) -> list[dict]:
    """Fixes: keep leading ./../ ; do not auto-resolve cursor→.cursor as original RESOLVED."""
    if not tok:
        return []
    raw_keep = tok
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
    parts = re.split(r"[;；]\s*(?=E:|[A-Za-z]:\\|/|规则库|记忆盘|经验卡|\.cursor)", tok)
    if len(parts) > 1:
        out: list[dict] = []
        for p in parts:
            out.extend(classify_token_v5(p.strip(), src, line, field + "+split"))
        return out
    # strip only quote/backtick wrappers, NOT leading dots
    tok = tok.strip()
    if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in "`'\"":
        tok = tok[1:-1]
    tok = tok.rstrip(".,;)）]")
    if PLACEHOLDER_RE.search(tok):
        return [
            {
                "src": str(src),
                "raw_token": raw_keep[:240],
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
                "raw_token": raw_keep[:240],
                "line": line,
                "field": field,
                "edge_status": "EXTERNAL",
                "edge_type": "URL_OR_ANCHOR",
                "resolved": tok if tok.startswith("http") else "",
            }
        ]
    if FORMULA_RE.search(tok) and not re.search(r"[\\/]", tok):
        return [
            {
                "src": str(src),
                "raw_token": raw_keep[:240],
                "line": line,
                "field": field,
                "edge_status": "NOT_A_PATH",
                "edge_type": "FORMULA_OR_CONSTRAINT",
                "resolved": "",
            }
        ]
    if RULE_ID_RE.match(tok) and "/" not in tok and "\\" not in tok and "." not in tok:
        return [
            {
                "src": str(src),
                "raw_token": raw_keep[:240],
                "line": line,
                "field": field,
                "edge_status": "RULE_ID_OR_STATUS_UNRESOLVED",
                "edge_type": "IDENTIFIER",
                "resolved": "",
            }
        ]
    if re.match(r"^[Dd]:[\\/]", tok) or "D:\\Cursor" in tok:
        return [
            {
                "src": str(src),
                "raw_token": raw_keep[:240],
                "line": line,
                "field": field,
                "edge_status": "LEGACY_HOST_SPECIFIC",
                "edge_type": "PATH_REF",
                "resolved": tok,
            }
        ]

    primary: Path | None = None
    alt: Path | None = None
    if re.match(r"^[A-Za-z]:[\\/]", tok):
        primary = Path(tok)
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
        primary = ROOT / tok.replace("/", "\\")
    elif tok.startswith("cursor/rules") or tok.startswith("cursor\\rules"):
        # original token is WITHOUT leading dot — do not mark RESOLVED via .cursor guess
        primary = ROOT / tok.replace("/", "\\")
        alt = ROOT / (".cursor/" + tok[len("cursor/") :]).replace("/", "\\")
    elif tok.startswith("../") or tok.startswith("..\\"):
        primary = (src.parent / tok.replace("/", "\\")).resolve()
    else:
        primary = src.parent / tok.replace("/", "\\")
        if "/" in tok or "\\" in tok:
            alt = ROOT / tok.replace("/", "\\")

    assert primary is not None
    try:
        exists = primary.exists()
    except OSError:
        return [
            {
                "src": str(src),
                "raw_token": raw_keep[:240],
                "line": line,
                "field": field,
                "edge_status": "PARSE_ERROR",
                "edge_type": "PATH_REF",
                "resolved": str(primary),
                "base": str(src.parent),
            }
        ]
    if exists:
        return [
            {
                "src": str(src),
                "raw_token": raw_keep[:240],
                "line": line,
                "field": field,
                "edge_status": "RESOLVED",
                "edge_type": "PATH_REF",
                "resolved": str(primary),
                "base": str(src.parent),
            }
        ]
    alt_exists = False
    if alt is not None:
        try:
            alt_exists = alt.exists()
        except OSError:
            alt_exists = False
    if alt_exists:
        return [
            {
                "src": str(src),
                "raw_token": raw_keep[:240],
                "line": line,
                "field": field,
                "edge_status": "BROKEN_CONFIRMED",
                "edge_type": "PATH_REF",
                "resolved": str(primary),
                "base": str(src.parent),
                "recovery_candidate": str(alt),
                "note": "ORIGINAL_MISSING_ALT_EXISTS_NOT_AUTO_RESOLVED",
            }
        ]
    return [
        {
            "src": str(src),
            "raw_token": raw_keep[:240],
            "line": line,
            "field": field,
            "edge_status": "BROKEN_CONFIRMED",
            "edge_type": "PATH_REF",
            "resolved": str(primary),
            "base": str(src.parent),
        }
    ]


def regression_v5() -> dict:
    cases = []
    e = classify_token_v5("../脚本/foo.py", ROOT / "契约" / "x.md", 1, "t")
    resolved = Path(e[0]["resolved"])
    expect = (ROOT / "脚本" / "foo.py")
    cases.append(
        (
            "relative_dotdot_target",
            ".." in e[0]["raw_token"] and str(resolved).replace("/", "\\").endswith(
                str(expect).replace("/", "\\")
            )
            or str(resolved) == str(expect.resolve()),
        )
    )
    e = classify_token_v5("cursor/rules/gate.mdc", ROOT / "AGENTS.md", 1, "t")
    cases.append(
        (
            "cursor_no_autoresolve",
            e[0]["edge_status"] != "RESOLVED"
            or "recovery_candidate" in e[0]
            or not Path(e[0].get("resolved") or "").exists(),
        )
    )
    # if .cursor exists for real kernel file, original cursor/ without dot still not RESOLVED via guess alone
    e = classify_token_v5(
        "cursor/rules/BLACKBOX_KERNEL_ALWAYS_APPLY.mdc", ROOT / "AGENTS.md", 1, "t"
    )
    cases.append(
        (
            "cursor_original_broken_even_if_dot_exists",
            e[0]["edge_status"] == "BROKEN_CONFIRMED"
            and e[0].get("recovery_candidate"),
        )
    )
    e = classify_token_v5(".cursor/rules/BLACKBOX_KERNEL_ALWAYS_APPLY.mdc", ROOT / "AGENTS.md", 1, "t")
    cases.append(("dot_cursor_ok", e[0]["edge_status"] == "RESOLVED"))
    ok = all(c[1] for c in cases)
    res = {"PASS": ok, "cases": [{"name": a, "ok": b} for a, b in cases]}
    (OUT / "parser_regression_v5.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return res


def list_fragments(pdir: Path, cap_discover: int = 200000) -> list[Path]:
    files: list[Path] = []
    for p in pdir.rglob("*.parquet"):
        files.append(p)
        if len(files) >= cap_discover:
            break
    return files


def _pick_date_col(cols: list[str]) -> str | None:
    for cand in (
        "day",
        "date",
        "signal_date",
        "trade_date",
        "nav_date",
        "report_date",
        "publication_date",
        "pubDate",
        "pub_date",
        "statDate",
        "stat_date",
        "event_date",
        "time",
        "datetime",
        "announcement_date",
        "effective_from",
        "weight_date",
        "source_date",
        "start_date",
        "end_date",
    ):
        for c in cols:
            if c.lower() == cand.lower() or c == cand:
                return c
    return None


def read_fragment_dates(
    files: list[Path],
    max_files: int = 80,
    *,
    stream_all: bool = False,
    chunk_files: int = 200,
    deadline: datetime | None = None,
    progress_cb=None,
) -> dict:
    """Read fragments with day/date columns; optional streaming over all files."""
    out = {
        "files_checked": 0,
        "rows_actually_read": 0,
        "date_min": "",
        "date_max": "",
        "pref": "",
        "null_code": 0,
        "null_time": 0,
        "dup_pk_candidate": "",
        "error": "",
        "years_in_paths": [],
        "stream_all": stream_all,
        "files_total": len(files),
    }
    if not files:
        out["error"] = "NO_FILES"
        return out
    years = sorted(
        {
            m.group(1)
            for f in files
            if (m := re.search(r"year[=_]?(\d{4})", str(f), re.I))
        }
    )
    out["years_in_paths"] = years
    sample = files if stream_all else files[:max_files]
    try:
        import pyarrow.compute as pc
        import pyarrow.dataset as ds

        dmin = None
        dmax = None
        rows = 0
        null_time = 0
        null_code = 0
        pref = None
        code_col = None
        # pk uniqueness only on first chunk (memory bound); mark KEY_UNVERIFIED if stream_all
        dup_pk = ""
        for i in range(0, len(sample), chunk_files):
            if deadline and datetime.now(CN) > deadline:
                out["error"] = (out.get("error") or "") + "|ARM_DEADLINE_STOP"
                break
            batch_files = sample[i : i + chunk_files]
            dataset = ds.dataset([str(f) for f in batch_files], format="parquet")
            cols = [f.name for f in dataset.schema]
            if pref is None:
                pref = _pick_date_col(cols)
                if not pref:
                    out["error"] = "NO_DATE_COL"
                    out["schema_sample"] = cols[:40]
                    out["files_checked"] = len(batch_files)
                    return out
                out["pref"] = pref
                for c in cols:
                    if c.lower() in {
                        "code",
                        "order_book_id",
                        "security",
                        "symbol",
                        "stock_code",
                    }:
                        code_col = c
                        break
            cols_read = [pref] + ([code_col] if code_col else [])
            # stream batches — avoid materializing entire product
            scanner = dataset.scanner(columns=cols_read, batch_size=65536)
            for rb in scanner.to_batches():
                rows += rb.num_rows
                tcol = rb.column(pref)
                null_time += tcol.null_count
                try:
                    mn = pc.min(tcol).as_py()
                    mx = pc.max(tcol).as_py()
                except Exception:
                    vals = [x.as_py() for x in tcol if x.is_valid]
                    mn = min(vals) if vals else None
                    mx = max(vals) if vals else None
                if mn is not None:
                    dmin = mn if dmin is None else min(dmin, mn)
                if mx is not None:
                    dmax = mx if dmax is None else max(dmax, mx)
                if code_col and code_col in rb.schema.names:
                    null_code += rb.column(code_col).null_count
            out["files_checked"] = min(len(sample), i + len(batch_files))
            if progress_cb:
                progress_cb(out["files_checked"], len(sample), rows)
            # light dup estimate only first chunk
            if i == 0 and code_col and not stream_all:
                table = dataset.to_table(columns=cols_read)
                times = [x.as_py() for x in table.column(pref)]
                codes = [x.as_py() for x in table.column(code_col)]
                pairs = [
                    (c, t)
                    for c, t in zip(codes, times)
                    if c is not None and t is not None
                ]
                if pairs:
                    dup_pk = str(len(pairs) - len(set(pairs)))
                    out["dup_note"] = "ROW_ALIGNED_CANDIDATE_NOT_CONTRACT_PK"
        out["rows_actually_read"] = rows
        out["null_time"] = null_time
        out["null_code"] = null_code
        if dmin is not None:
            out["date_min"] = str(dmin)
        if dmax is not None:
            out["date_max"] = str(dmax)
        if stream_all:
            out["dup_pk_candidate"] = "KEY_UNVERIFIED_STREAM"
            out["dup_note"] = "FULL_STREAM_NO_GLOBAL_PK_MATERIALIZE"
        else:
            out["dup_pk_candidate"] = dup_pk
    except Exception as e:  # noqa: BLE001
        out["error"] = f"{type(e).__name__}:{e}"
    return out


def load_queue():
    rows = []
    qp = OUT.parent / "PRODUCT_QUEUE.jsonl"
    if not qp.exists():
        qp = Path(
            r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\PRODUCT_QUEUE.jsonl"
        )
    if qp.exists():
        for line in qp.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_prior_coverage() -> dict[str, dict]:
    p = OUT / "FRAGMENT_COVERAGE_0730.csv"
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return {r["product_id"]: r for r in csv.DictReader(f) if r.get("product_id")}


def _write_coverage(frag_rows: list[dict]) -> None:
    if not frag_rows:
        return
    with (OUT / "FRAGMENT_COVERAGE_0730.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        keys = sorted({k for r in frag_rows for k in r})
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(frag_rows)
    HUB.mkdir(parents=True, exist_ok=True)
    (HUB / "FRAGMENT_COVERAGE_0730.csv").write_bytes(
        (OUT / "FRAGMENT_COVERAGE_0730.csv").read_bytes()
    )


def _sync_hub_artifacts() -> None:
    for name in (
        "MASTER_PROGRESS_0730.md",
        "FRAGMENT_COVERAGE_0730.csv",
        "parser_regression_v5.json",
        "SOURCE_SHA_0730.json",
        "WORKER_PID_0730.json",
        "STATUS_PROGRESS.json",
        "PRODUCT_STAGE_LEDGER_75.csv",
    ):
        p = OUT / name
        if p.exists():
            (HUB / name).write_bytes(p.read_bytes())


def _update_ledger(frag_by_pid: dict[str, dict]) -> None:
    led = OUT / "PRODUCT_STAGE_LEDGER_75.csv"
    if not led.exists():
        return
    rows = list(csv.DictReader(led.open("r", encoding="utf-8-sig", newline="")))
    if not rows:
        return
    keys = list(rows[0].keys())
    for extra in (
        "frag_0730_checked",
        "frag_0730_discovered",
        "frag_0730_date_min",
        "frag_0730_date_max",
        "frag_0730_error",
        "frag_0730_updated",
    ):
        if extra not in keys:
            keys.append(extra)
    for r in rows:
        pid = r.get("product_id") or r.get("PRODUCT_ID") or ""
        fr = frag_by_pid.get(pid)
        if not fr:
            continue
        r["frag_0730_checked"] = fr.get("read_files_checked", "")
        r["frag_0730_discovered"] = fr.get("files_discovered", "")
        r["frag_0730_date_min"] = fr.get("read_date_min", "")
        r["frag_0730_date_max"] = fr.get("read_date_max", "")
        r["frag_0730_error"] = fr.get("read_error", "")
        r["frag_0730_updated"] = now()
    with led.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    HUB.mkdir(parents=True, exist_ok=True)
    PIDFILE.write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "task": "0730",
                "python": sys.executable,
                "started_at": now(),
                "log": str(LOG),
                "mode": "CONTINUOUS_UNTIL_DEADLINE",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    t0 = time.time()
    arm_p = ST / "_hub_patrol_10h_3m_arm.json"
    if not arm_p.exists():
        arm_p = ST / "_hub_AUTOMATION_CURRENT.json"
    deadline_raw = None
    if arm_p.exists():
        deadline_raw = json.loads(arm_p.read_text(encoding="utf-8-sig")).get(
            "deadline_at"
        )
    deadline = datetime.fromisoformat(deadline_raw) if deadline_raw else None
    log("RESUME_0730_START continuous=1")
    reg = regression_v5()
    log(f"parser_v5 PASS={reg.get('PASS')} {reg.get('cases')}")

    queue = load_queue()

    def prio(pid: str) -> int:
        if "FUND_NAV" in pid:
            return 0
        if any(
            k in pid
            for k in ("STOCK_DAILY", "ETF_DAILY", "CORP_", "FINANCIAL", "EVENT")
        ):
            return 1
        return 2

    queue = sorted(
        queue, key=lambda r: (prio(r.get("product_id") or ""), r.get("product_id") or "")
    )
    prior = _load_prior_coverage()
    frag_map: dict[str, dict] = dict(prior)
    ckpt_dir = OUT / "checkpoints_0730"
    ckpt_dir.mkdir(exist_ok=True)

    def deadline_hit() -> bool:
        return bool(deadline and datetime.now(CN) > deadline)

    def flush_master(phase: str, overall: str, note: str) -> None:
        rows = list(frag_map.values())
        _write_coverage(rows)
        _update_ledger(frag_map)
        src = Path(__file__)
        (OUT / "SOURCE_SHA_0730.json").write_text(
            json.dumps(
                {
                    "at": now(),
                    "files": [
                        {
                            "path": str(src),
                            "sha256": sha256_file(src),
                            "bytes": src.stat().st_size,
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (OUT / "source_upload_0730").mkdir(exist_ok=True)
        (OUT / "source_upload_0730" / src.name).write_bytes(src.read_bytes())
        incomplete = [
            r
            for r in rows
            if int(float(r.get("read_files_checked") or 0))
            < int(float(r.get("files_discovered") or 0))
            or (r.get("read_error") or "")
            in {"NO_DATE_COL", "NO_FILES"}
        ]
        master = f"""# RESUME_0730_PROGRESS

status: **{overall}**
phase: {phase}
worker_pid: {os.getpid()}
elapsed_sec: {round(time.time() - t0, 1)}
parser_v5_pass: {reg.get('PASS')}
fragments_products: {len(rows)}
incomplete_or_partial: {len(incomplete)}
deadline: {deadline_raw}
note: {note}

## Fixes applied this worker
1. date candidates include `day`
2. all fragments listed (not year-first-only)
3. row-aligned / stream KEY_UNVERIFIED (no false PK)
4. classify_token_v5 keeps ../ and does not strip leading dots
5. cursor/rules without dot NOT auto-RESOLVED via .cursor

local: `{OUT}`
"""
        (OUT / "MASTER_PROGRESS_0730.md").write_text(master, encoding="utf-8")
        write_status(
            phase=phase,
            overall=overall,
            worker_pid=os.getpid(),
            fragments_products=len(rows),
            incomplete_or_partial=len(incomplete),
            parser_v5_pass=reg.get("PASS"),
            elapsed_sec=round(time.time() - t0, 1),
            deadline_arm=deadline_raw,
            note=note,
        )
        _sync_hub_artifacts()

    # ---- Pass A: quick coverage for any missing products ----
    for i, item in enumerate(queue):
        if deadline_hit():
            log("ARM_DEADLINE_STOP passA")
            break
        pid = item.get("product_id") or ""
        ap = Path(item["authority_path"]) if item.get("authority_path") else None
        if not ap or not ap.exists() or not ap.is_dir():
            continue
        if item.get("authority_kind") == "CACHE_REGISTRY_FILE":
            continue
        if pid in frag_map and int(float(frag_map[pid].get("read_files_checked") or 0)) > 0:
            continue
        write_status(
            phase="FRAGMENT_COVERAGE_0730",
            current_product=pid,
            current_index=i,
            worker_pid=os.getpid(),
            overall="RUNNING",
            parser_v5_pass=reg.get("PASS"),
            elapsed_sec=round(time.time() - t0, 1),
            deadline_arm=deadline_raw,
        )
        files = list_fragments(ap)
        stats = read_fragment_dates(
            files, max_files=min(120, max(1, len(files))), deadline=deadline
        )
        row = {
            "product_id": pid,
            "files_discovered": len(files),
            "hit_discover_cap": len(files) >= 200000,
            **{f"read_{k}": v for k, v in stats.items()},
        }
        frag_map[pid] = row
        log(
            f"FRAG {pid} discovered={len(files)} checked={stats.get('files_checked')} "
            f"{stats.get('date_min')}..{stats.get('date_max')} err={stats.get('error')}"
        )
        if i % 3 == 0:
            flush_master(
                "FRAGMENT_COVERAGE_0730",
                "RUNNING",
                f"passA checkpoint {pid}",
            )

    flush_master(
        "DEEPEN_START_0730",
        "RUNNING",
        "passA done; start deepen incomplete (FUND_NAV first)",
    )

    # ---- Pass B: deepen incomplete — FUND_NAV full stream, others raise cap ----
    deepen_targets = []
    for item in queue:
        pid = item.get("product_id") or ""
        row = frag_map.get(pid) or {}
        disc = int(float(row.get("files_discovered") or 0))
        chk = int(float(row.get("read_files_checked") or 0))
        err = row.get("read_error") or ""
        if disc > chk or err in {"NO_DATE_COL", "NO_FILES"} or "FUND_NAV" in pid:
            deepen_targets.append(item)
    deepen_targets = sorted(
        deepen_targets,
        key=lambda r: (prio(r.get("product_id") or ""), r.get("product_id") or ""),
    )

    for i, item in enumerate(deepen_targets):
        if deadline_hit():
            log("ARM_DEADLINE_STOP passB")
            break
        pid = item.get("product_id") or ""
        ap = Path(item["authority_path"]) if item.get("authority_path") else None
        if not ap or not ap.exists() or not ap.is_dir():
            continue
        if item.get("authority_kind") == "CACHE_REGISTRY_FILE":
            continue
        write_status(
            phase="FRAGMENT_DEEPEN_0730",
            current_product=pid,
            current_index=i,
            worker_pid=os.getpid(),
            overall="RUNNING",
            parser_v5_pass=reg.get("PASS"),
            elapsed_sec=round(time.time() - t0, 1),
            deadline_arm=deadline_raw,
        )
        files = list_fragments(ap)
        stream_all = "FUND_NAV" in pid or len(files) <= 400
        max_files = len(files) if stream_all else min(800, len(files))

        def _cb(checked: int, total: int, rows: int, _pid=pid) -> None:
            if checked % 400 == 0 or checked == total:
                log(f"DEEPEN {_pid} files={checked}/{total} rows={rows}")
                write_status(
                    phase="FRAGMENT_DEEPEN_0730",
                    current_product=_pid,
                    deepen_files=f"{checked}/{total}",
                    deepen_rows=rows,
                    worker_pid=os.getpid(),
                    overall="RUNNING",
                    elapsed_sec=round(time.time() - t0, 1),
                    deadline_arm=deadline_raw,
                )

        stats = read_fragment_dates(
            files,
            max_files=max_files,
            stream_all=stream_all,
            chunk_files=150 if "FUND_NAV" in pid else 80,
            deadline=deadline,
            progress_cb=_cb,
        )
        row = {
            "product_id": pid,
            "files_discovered": len(files),
            "hit_discover_cap": len(files) >= 200000,
            **{f"read_{k}": v for k, v in stats.items()},
        }
        frag_map[pid] = row
        log(
            f"DEEPEN_DONE {pid} discovered={len(files)} checked={stats.get('files_checked')} "
            f"rows={stats.get('rows_actually_read')} "
            f"{stats.get('date_min')}..{stats.get('date_max')} err={stats.get('error')}"
        )
        (ckpt_dir / f"deepen_{i:04d}_{pid}.json").write_text(
            json.dumps(row, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        flush_master(
            "FRAGMENT_DEEPEN_0730",
            "RUNNING",
            f"deepened {pid} checked={stats.get('files_checked')}/{len(files)}",
        )

    rows = list(frag_map.values())
    incomplete = [
        r
        for r in rows
        if int(float(r.get("read_files_checked") or 0))
        < int(float(r.get("files_discovered") or 0))
        or (r.get("read_error") or "") in {"NO_DATE_COL", "NO_FILES"}
    ]
    if deadline_hit():
        overall = "PARTIAL_DEADLINE_STOP"
        note = "stopped at arm deadline; resume from FRAGMENT_COVERAGE_0730 + checkpoints"
    elif not incomplete:
        overall = "FRAGMENT_PASS_COMPLETE"
        note = "all queued products fragment-checked (stream/full where required)"
    else:
        overall = "PARTIAL_CONTINUE_NO_FORCED_WAIT"
        note = f"remaining incomplete={len(incomplete)}; no WAIT barrier"
    flush_master("BATCH_CHECKPOINT_0730", overall, note)
    log(f"RESUME_0730_BATCH_DONE overall={overall} incomplete={len(incomplete)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        log("FATAL\n" + traceback.format_exc())
        write_status(phase="FATAL", error=traceback.format_exc()[-2000:], worker_pid=os.getpid())
        raise
