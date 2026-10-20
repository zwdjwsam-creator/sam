# -*- coding: utf-8 -*-
"""0650 execution correction — parser v4 + deep coverage; preserves 0010 artifacts."""
from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
import time
import traceback
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
V2 = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2")
BASE = V2 / "continue_0010"
OUT = BASE / "correction_0650"
CKPT = OUT / "checkpoints"
LOG = OUT / "worker.log"
STATUS = OUT / "STATUS_PROGRESS.json"
# keep dock sync path on parent continue_0010 STATUS as well
STATUS_PARENT = BASE / "STATUS_PROGRESS.json"
HUB = Path(
    r"E:\BLACKBOX\运行\外部大脑信箱\agents\chatgpt\inbox\BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150\v2\continue_0010\correction_0650"
)
HUB_PARENT = HUB.parent
PIDFILE = OUT / "WORKER_PID.json"
PLACEHOLDER_RE = re.compile(
    r"<[^>]+>|\{[^}]+\}|YYYYMMDD|<asof>|YOUR_|TODO_|FIXME_|%\([^)]+\)s"
)
RULE_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")
FORMULA_RE = re.compile(r"(<=|>=|==|!=|<|>)|KNOWN_AT|SIGNAL_TIME|FILL_TIME")
TIME_COL_EXTRA = {
    "report_date",
    "implementation_pub_date",
    "a_xr_date",
    "publication_date",
    "announce_date",
    "info_date",
    "end_date",
    "start_date",
    "list_date",
    "delist_date",
}


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
        "task": "BLACKBOX_SYSTEM_INVENTORY_EXECUTION_CORRECTION_20261021_0650",
        "parent": "BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150",
        "supersedes_followup": "BLACKBOX_SYSTEM_INVENTORY_CONTINUE_20261021_0010",
        **kw,
    }
    text = json.dumps(body, ensure_ascii=False, indent=2)
    STATUS.write_text(text, encoding="utf-8")
    STATUS_PARENT.write_text(text, encoding="utf-8")
    HUB.mkdir(parents=True, exist_ok=True)
    HUB_PARENT.mkdir(parents=True, exist_ok=True)
    (HUB / "STATUS_PROGRESS.json").write_text(text, encoding="utf-8")
    (HUB_PARENT / "STATUS_PROGRESS.json").write_text(text, encoding="utf-8")


def classify_token_v4(tok: str, src: Path, line: int, field: str) -> list[dict]:
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
            out.extend(classify_token_v4(p.strip(), src, line, field + "+split"))
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
    if FORMULA_RE.search(tok) and not re.search(r"[\\/]", tok):
        return [
            {
                "src": str(src),
                "raw_token": tok[:240],
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
                "raw_token": tok[:240],
                "line": line,
                "field": field,
                "edge_status": "RULE_ID_OR_STATUS_UNRESOLVED",
                "edge_type": "IDENTIFIER",
                "resolved": "",
            }
        ]
    if field == "inline_code" and not re.search(r"[\\/.]", tok) and " " not in tok:
        # bare identifier in backticks — not a filesystem path
        if RULE_ID_RE.match(tok) or tok.isupper():
            return [
                {
                    "src": str(src),
                    "raw_token": tok[:240],
                    "line": line,
                    "field": field,
                    "edge_status": "RULE_ID_OR_STATUS_UNRESOLVED",
                    "edge_type": "INLINE_IDENTIFIER",
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

    # preserve leading-dot semantics; try .cursor when token lost the dot
    candidates: list[Path] = []
    if re.match(r"^[A-Za-z]:[\\/]", tok):
        candidates.append(Path(tok))
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
        candidates.append(ROOT / tok.replace("/", "\\"))
    elif tok.startswith("cursor/rules") or tok.startswith("cursor\\rules"):
        candidates.append(ROOT / (".cursor/" + tok[len("cursor/") :]).replace("/", "\\"))
        candidates.append(ROOT / tok.replace("/", "\\"))
    else:
        candidates.append(src.parent / tok.replace("/", "\\"))
        # relative to repo root if looks like project-relative
        if "/" in tok or "\\" in tok:
            candidates.append(ROOT / tok.replace("/", "\\"))

    last_resolved = ""
    for cand in candidates:
        last_resolved = str(cand)
        try:
            if cand.exists():
                return [
                    {
                        "src": str(src),
                        "raw_token": raw_keep[:240],
                        "line": line,
                        "field": field,
                        "edge_status": "RESOLVED",
                        "edge_type": "PATH_REF",
                        "resolved": str(cand),
                        "base": str(src.parent),
                    }
                ]
        except OSError:
            return [
                {
                    "src": str(src),
                    "raw_token": raw_keep[:240],
                    "line": line,
                    "field": field,
                    "edge_status": "PARSE_ERROR",
                    "edge_type": "PATH_REF",
                    "resolved": str(cand),
                    "base": str(src.parent),
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
            "resolved": last_resolved,
            "base": str(src.parent),
            "checked_candidates": [str(c) for c in candidates],
        }
    ]


def run_parser_regression_v4() -> dict:
    cases = []
    e = classify_token_v4("数据/研究报告/日增量/<asof>/", ROOT / "AGENTS.md", 1, "t")
    cases.append(("template_dynamic", e[0]["edge_status"] == "DYNAMIC_OR_PLACEHOLDER"))
    e = classify_token_v4(r"E:\BLACKBOX\经验卡;E:\BLACKBOX\记忆盘", ROOT / "AGENTS.md", 1, "t")
    cases.append(("semicolon_split", len(e) == 2))
    e = classify_token_v4(r"D:\CursorDualRouteConfig\foo", ROOT / "AGENTS.md", 1, "t")
    cases.append(("legacy_d", e[0]["edge_status"] == "LEGACY_HOST_SPECIFIC"))
    e = classify_token_v4("BACKTEST_MANDATORY_PRECHECK_R1", ROOT / "AGENTS.md", 1, "inline_code")
    cases.append(("rule_id", e[0]["edge_status"] == "RULE_ID_OR_STATUS_UNRESOLVED"))
    e = classify_token_v4("KNOWN_AT <= SIGNAL_TIME < FILL_TIME", ROOT / "AGENTS.md", 1, "inline_code")
    cases.append(("formula", e[0]["edge_status"] == "NOT_A_PATH"))
    e = classify_token_v4("cursor/rules/BLACKBOX_KERNEL_ALWAYS_APPLY.mdc", ROOT / "AGENTS.md", 1, "t")
    cases.append(("cursor_dot_recover", e[0]["edge_status"] == "RESOLVED"))
    e = classify_token_v4(".cursor/rules/BLACKBOX_KERNEL_ALWAYS_APPLY.mdc", ROOT / "AGENTS.md", 1, "t")
    cases.append(("cursor_leading_dot", e[0]["edge_status"] == "RESOLVED"))
    e = classify_token_v4("../脚本/foo.py", ROOT / "契约" / "x.md", 1, "t")
    cases.append(("relative_dotdot_kept", ".." in e[0]["raw_token"] or e[0]["edge_type"] == "PATH_REF"))
    ok = all(c[1] for c in cases)
    res = {"PASS": ok, "cases": [{"name": a, "ok": b} for a, b in cases]}
    (OUT / "parser_regression_v4.json").write_text(
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


def recompute_broken_v4() -> dict:
    # preserve v3 files; write v4 next to them
    shards = V2 / "shards"
    active = []
    for p in shards.glob("RULES_ACTIVE_SHARD_*.jsonl"):
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                active.append(json.loads(line))
    edges = []
    decode_issues = []
    md_link_re = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
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
                edges.extend(classify_token_v4(m.group(1), path, i, "inline_code"))
            for m in md_link_re.finditer(line):
                tgt = m.group(1).split("#", 1)[0].strip()
                if tgt:
                    edges.extend(classify_token_v4(tgt, path, i, "md_link"))
            for m in re.finditer(r"(E:[\\/]BLACKBOX[^\s`\"'|<>]{0,200})", line):
                edges.extend(classify_token_v4(m.group(1), path, i, "abs"))
    c = Counter(e["edge_status"] for e in edges)
    broken = [e for e in edges if e["edge_status"] == "BROKEN_CONFIRMED"]
    with (OUT / "RULE_LINKS_RECOMPUTED_V4.jsonl").open("w", encoding="utf-8") as f:
        for e in edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    with (OUT / "RULE_LINKS_BROKEN_CONFIRMED_V4.jsonl").open("w", encoding="utf-8") as f:
        for e in broken:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    # before/after vs v3
    v3_n = None
    v3p = BASE / "LINKS_RECOMPUTE_SUMMARY.json"
    if v3p.exists():
        v3_n = json.loads(v3p.read_text(encoding="utf-8")).get("broken_confirmed")
    summary = {
        "active_rules_scanned": len(active),
        "edges": len(edges),
        "status_counts": dict(c),
        "broken_confirmed": len(broken),
        "broken_confirmed_v3_preserved": v3_n,
        "decode_unverified": len(decode_issues),
        "regression": run_parser_regression_v4(),
        "note": "v3 artifacts under continue_0010 preserved; v4 is reclassify",
    }
    (OUT / "LINKS_RECOMPUTE_SUMMARY_V4.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def deep_probe(pid: str, pdir: Path, max_files: int = 80) -> dict:
    out = {
        "product_id": pid,
        "n_parquet_files_capped": 0,
        "year_parts": [],
        "date_min": "",
        "date_max": "",
        "n_rows_sampled": "",
        "n_codes": "",
        "columns": "",
        "time_fields": "",
        "null_ratio_time": "",
        "dup_pk_estimate": "",
        "validation_grain": "",
        "error": "",
        "status": "PENDING",
        "phase": "DEEP_COVERAGE",
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
            if len(files) >= max_files:
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
        import pyarrow.compute as pc

        by_year = {}
        for f in files:
            m = re.search(r"year[=_]?(\d{4})", str(f), re.I)
            y = m.group(1) if m else "NA"
            by_year.setdefault(y, f)
        sample = list(by_year.values())
        dataset = ds.dataset([str(f) for f in sample], format="parquet")
        cols = [f.name for f in dataset.schema]
        out["columns"] = ",".join(cols[:80])
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
                *TIME_COL_EXTRA,
            }
            or "date" in c.lower()
            or c.lower().endswith("_at")
        ]
        # dedupe preserve order
        seen = set()
        time_cols = [c for c in time_cols if not (c in seen or seen.add(c))]
        out["time_fields"] = ",".join(time_cols[:20])
        code_cols = [
            c
            for c in cols
            if c.lower() in {"code", "order_book_id", "security", "symbol", "stock_code"}
        ]
        if not time_cols:
            out.update(validation_grain="SCHEMA_ONLY_NO_TIME_COL_AFTER_EXPAND", status="VERIFIED_PARTIAL")
            return out
        pref = None
        for cand in (
            "date",
            "signal_date",
            "trade_date",
            "report_date",
            "publication_date",
            "implementation_pub_date",
            "a_xr_date",
            "pubDate",
            "pub_date",
            "statDate",
            "stat_date",
            "pit_available_from",
            "event_date",
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
        col = table.column(pref)
        vals = [x.as_py() for x in col if x.as_py() is not None]
        out["n_rows_sampled"] = str(table.num_rows)
        nulls = table.num_rows - len(vals)
        if table.num_rows:
            out["null_ratio_time"] = f"{nulls / table.num_rows:.4f}"
        if vals:
            out["date_min"] = str(min(vals))
            out["date_max"] = str(max(vals))
        if code_cols:
            codes = [x.as_py() for x in table.column(code_cols[0]) if x.as_py() is not None]
            out["n_codes"] = str(len(set(codes)))
            # rough dup estimate on (code, time)
            pairs = list(zip(codes, [x.as_py() for x in col if x.as_py() is not None][: len(codes)]))
            if pairs:
                out["dup_pk_estimate"] = str(len(pairs) - len(set(pairs)))
        out["validation_grain"] = (
            f"DEEP_YEAR_SAMPLE_nfiles={len(sample)}_pref={pref}_NOT_FULL_ROWSCAN"
        )
        out["status"] = "VERIFIED_PARTIAL"
    except Exception as e:  # noqa: BLE001
        out.update(
            error=f"{type(e).__name__}:{e}",
            validation_grain="FILE_LIST_ONLY",
            status="VERIFIED_PARTIAL",
        )
    return out


def load_queue_from_0010():
    qpath = BASE / "PRODUCT_QUEUE.jsonl"
    rows = []
    if qpath.exists():
        for line in qpath.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def watermark_provenance() -> list[dict]:
    rows = []
    targets = [
        ROOT / "运行" / "BLACKBOX_JQ_INCREMENTAL_DOWNLOAD_RULE_CURRENT.json",
        ROOT / "运行" / "BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json",
        ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_DATA_MANIFEST_CURRENT.json",
    ]
    for p in targets:
        if not p.exists():
            rows.append(
                {
                    "source": str(p),
                    "field": "",
                    "value": "",
                    "semantic": "MISSING_FILE",
                    "data_watermark": "UNKNOWN",
                }
            )
            continue
        try:
            body = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            rows.append(
                {
                    "source": str(p),
                    "field": "",
                    "value": "",
                    "semantic": f"JSON_ERROR:{type(e).__name__}",
                    "data_watermark": "UNKNOWN",
                }
            )
            continue
        for key in (
            "generated_at",
            "generated_at_cn",
            "published_at",
            "asof",
            "HIST_END",
            "covered_through",
            "ingest_cursor",
            "updated_at",
            "asof_target",
        ):
            if key in body:
                semantic = (
                    "PUBLISH_OR_GENERATED_AT"
                    if key in {"generated_at", "generated_at_cn", "published_at", "updated_at"}
                    else "DATA_WATERMARK_CANDIDATE"
                )
                rows.append(
                    {
                        "source": str(p),
                        "field": key,
                        "value": str(body[key])[:200],
                        "semantic": semantic,
                        "data_watermark": str(body[key])
                        if semantic == "DATA_WATERMARK_CANDIDATE"
                        else "UNKNOWN",
                    }
                )
        # datasets list
        for ds in (body.get("datasets") or [])[:40]:
            if not isinstance(ds, dict):
                continue
            rows.append(
                {
                    "source": str(p) + "#datasets",
                    "field": "dataset_id",
                    "value": str(ds.get("dataset_id")),
                    "semantic": "DATASET_ROW",
                    "data_watermark": str(
                        ds.get("asof_target")
                        or ds.get("covered_through")
                        or ds.get("ingest_cursor")
                        or "UNKNOWN"
                    ),
                    "extra_keys": ",".join(sorted(ds.keys())[:30]),
                }
            )
    return rows


def flush_hub() -> None:
    HUB.mkdir(parents=True, exist_ok=True)
    for name in (
        "STATUS_PROGRESS.json",
        "LINKS_RECOMPUTE_SUMMARY_V4.json",
        "parser_regression_v4.json",
        "DEEP_COVERAGE_PROBES.csv",
        "WATERMARK_FIELD_PROVENANCE.csv",
        "MASTER_PROGRESS_0650.md",
        "WORKER_PID.json",
        "PID_EXIT_EVIDENCE.json",
    ):
        src = OUT / name
        if src.exists():
            (HUB / name).write_bytes(src.read_bytes())
    # also mirror STATUS to parent hub for dock sync
    if STATUS_PARENT.exists():
        (HUB_PARENT / "STATUS_PROGRESS.json").write_bytes(STATUS_PARENT.read_bytes())


def pid_exit_evidence() -> dict:
    old = {}
    op = BASE / "WORKER_PID.json"
    if op.exists():
        old = json.loads(op.read_text(encoding="utf-8"))
    pid = old.get("pid")
    evidence = {
        "claimed_pid": pid,
        "checked_at": now(),
        "alive": False,
        "creation_date": None,
        "command_line": None,
        "exit_inference": "NOT_RUNNING_NOW",
        "worker_log_tail": "",
        "last_log_line": "",
    }
    if pid:
        try:
            r = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"Get-CimInstance Win32_Process -Filter \"ProcessId={pid}\" | "
                    "Select-Object ProcessId,Name,CommandLine,CreationDate | ConvertTo-Json",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if r.stdout.strip():
                evidence["alive"] = True
                evidence["raw"] = r.stdout[:2000]
                evidence["exit_inference"] = "STILL_ALIVE"
            else:
                evidence["exit_inference"] = "PROCESS_GONE_AFTER_WORKER_PASS_DONE"
        except Exception as e:  # noqa: BLE001
            evidence["exit_inference"] = f"CHECK_ERROR:{type(e).__name__}"
    wlog = BASE / "worker.log"
    if wlog.exists():
        lines = wlog.read_text(encoding="utf-8", errors="replace").splitlines()
        evidence["last_log_line"] = lines[-1] if lines else ""
        evidence["worker_log_tail"] = "\n".join(lines[-15:])
        if any("WORKER_PASS_DONE" in x for x in lines[-30:]):
            evidence["exit_inference"] = "NATURAL_END_AFTER_SINGLE_BATCH_BUDGET"
    (OUT / "PID_EXIT_EVIDENCE.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return evidence


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CKPT.mkdir(parents=True, exist_ok=True)
    HUB.mkdir(parents=True, exist_ok=True)
    PIDFILE.write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "argv": list(sys.argv),
                "python": sys.executable,
                "started_at": now(),
                "log": str(LOG),
                "task": "BLACKBOX_SYSTEM_INVENTORY_EXECUTION_CORRECTION_20261021_0650",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    t0 = time.time()
    arm_p = Path(r"E:\BLACKBOX\运行\外部大脑信箱\_hub_patrol_10h_3m_arm.json")
    deadline_arm = (
        json.loads(arm_p.read_text(encoding="utf-8")).get("deadline_at") if arm_p.exists() else None
    )
    log("CORRECTION_0650_START")
    evidence = pid_exit_evidence()
    log(f"pid39980_evidence={evidence.get('exit_inference')} alive={evidence.get('alive')}")
    reg = run_parser_regression_v4()
    log(f"parser_v4 PASS={reg.get('PASS')} cases={reg.get('cases')}")
    write_status(
        phase="PID_EVIDENCE_AND_PARSER_V4",
        parser_v4_pass=reg.get("PASS"),
        worker_pid=os.getpid(),
        deadline_arm=deadline_arm,
        pid_exit=evidence.get("exit_inference"),
    )
    link_sum = recompute_broken_v4()
    log(
        f"broken_v4={link_sum.get('broken_confirmed')} v3_was={link_sum.get('broken_confirmed_v3_preserved')} counts={link_sum.get('status_counts')}"
    )
    wm = watermark_provenance()
    with (OUT / "WATERMARK_FIELD_PROVENANCE.csv").open("w", encoding="utf-8-sig", newline="") as f:
        keys = sorted({k for r in wm for k in r.keys()})
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(wm)
    queue = load_queue_from_0010()
    # prioritize daily/financial/event products for deep pass
    priority_kw = (
        "DAILY",
        "FINANCIAL",
        "EVENT",
        "XR_XD",
        "SHAREHOLDER",
        "VALUATION",
        "TRADEABILITY",
        "STOCK_",
        "SW_L",
        "CORP_",
    )
    queue_sorted = sorted(
        queue,
        key=lambda r: (
            0 if any(k in r.get("product_id", "") for k in priority_kw) else 1,
            r.get("product_id", ""),
        ),
    )
    probes = []
    for i, item in enumerate(queue_sorted):
        if deadline_arm and datetime.now(CN) > datetime.fromisoformat(deadline_arm):
            log("ARM_DEADLINE_STOP")
            break
        # batch budget ~25 min then checkpoint continue (same process keeps going)
        pid = item["product_id"]
        ap = Path(item["authority_path"]) if item.get("authority_path") else None
        write_status(
            phase="DEEP_COVERAGE",
            current_product=pid,
            current_index=i,
            denominator_products=len(queue_sorted),
            broken_confirmed_v4=link_sum.get("broken_confirmed"),
            broken_confirmed_v3_preserved=link_sum.get("broken_confirmed_v3_preserved"),
            parser_v4_pass=reg.get("PASS"),
            worker_pid=os.getpid(),
            deadline_arm=deadline_arm,
            elapsed_sec=round(time.time() - t0, 1),
            deep_probes=len(probes),
            pid_exit=evidence.get("exit_inference"),
            overall="RUNNING",
        )
        if ap and ap.exists() and ap.is_dir() and item.get("status") not in {
            "NOT_IN_MAIN_CACHE_ROOT",
        }:
            # skip pure registry file rows
            if item.get("authority_kind") == "CACHE_REGISTRY_FILE":
                continue
            pr = deep_probe(pid, ap)
            probes.append(pr)
            log(
                f"DEEP {pid} {pr['status']} {pr.get('date_min')}..{pr.get('date_max')} grain={pr.get('validation_grain')}"
            )
        if i % 3 == 0:
            if probes:
                with (OUT / "DEEP_COVERAGE_PROBES.csv").open(
                    "w", encoding="utf-8-sig", newline=""
                ) as f:
                    keys = sorted({k for r in probes for k in r.keys()})
                    w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
                    w.writeheader()
                    w.writerows(probes)
            (CKPT / f"ckpt_{i:04d}.json").write_text(
                json.dumps({"i": i, "pid": pid, "at": now(), "n_probes": len(probes)}, ensure_ascii=False),
                encoding="utf-8",
            )
            flush_hub()
    if probes:
        with (OUT / "DEEP_COVERAGE_PROBES.csv").open("w", encoding="utf-8-sig", newline="") as f:
            keys = sorted({k for r in probes for k in r.keys()})
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(probes)
    sc = Counter(p.get("status") for p in probes)
    master = f"""# CORRECTION_0650_PROGRESS

status: **RUNNING_OR_CHECKPOINT**
worker_pid: {os.getpid()}
elapsed_sec: {round(time.time() - t0, 1)}
pid39980_exit: {evidence.get('exit_inference')}
parser_v4_pass: {reg.get('PASS')}
broken_confirmed_v3_preserved: {link_sum.get('broken_confirmed_v3_preserved')}
broken_confirmed_v4: {link_sum.get('broken_confirmed')}
edge_status_counts_v4: {dict(link_sum.get('status_counts') or {})}
deep_probes: {len(probes)}
deep_status_counts: {dict(sc)}
denominator_queue_objects: {len(queue_sorted)}  # NOT business-data classes

## 口径纠偏
- 75 = 队列对象分母（含 registry），不是 75 类业务数据
- VERIFIED_WITHIN_DECLARED_SCOPE 中 registry/sidecar 分开计
- 1551 BROKEN_CONFIRMED(v3) 不可当故障数；见 v4 重分类
- 统一 published/generated_at ≠ 每源数据水位（见 WATERMARK_FIELD_PROVENANCE.csv）

local: `{OUT}`
"""
    (OUT / "MASTER_PROGRESS_0650.md").write_text(master, encoding="utf-8")
    write_status(
        phase="DEEP_BATCH_CHECKPOINT",
        denominator_products=len(queue_sorted),
        status_counts=dict(sc),
        broken_confirmed_v4=link_sum.get("broken_confirmed"),
        broken_confirmed_v3_preserved=link_sum.get("broken_confirmed_v3_preserved"),
        deep_probes=len(probes),
        parser_v4_pass=reg.get("PASS"),
        worker_pid=os.getpid(),
        deadline_arm=deadline_arm,
        elapsed_sec=round(time.time() - t0, 1),
        pid_exit=evidence.get("exit_inference"),
        overall="PARTIAL_CONTINUE_WITH_CHECKPOINT",
    )
    flush_hub()
    log("CORRECTION_0650_BATCH_DONE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        log("FATAL\n" + traceback.format_exc())
        write_status(phase="FATAL", error=traceback.format_exc()[-2000:], worker_pid=os.getpid())
        raise
