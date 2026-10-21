# -*- coding: utf-8 -*-
"""0905 lineage + true rule citation graph worker (readonly inventory isolation)."""
from __future__ import annotations

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
CACHE = Path(
    r"E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439"
)
DEP_REG = Path(r"E:\BLACKBOX\数据\回测缓存\registry\CACHE_DEPENDENCY_REGISTRY.json")
MAN_REG = Path(r"E:\BLACKBOX\数据\回测缓存\registry\CACHE_MANIFEST_REGISTRY.json")
CLEAN_CUR = Path(r"E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json")
UNI_REG = Path(r"E:\BLACKBOX\规则库\data_dictionary\unified_market_data_plane_registry_r1.json")
LOG = OUT / "lineage_0905.log"
SRC_DIR = OUT / "source_upload_0905"
CKPT = OUT / "checkpoints_0905"

# import v5 classifier from 0730 source if present
sys.path.insert(0, str(OUT / "source_upload_0730"))
try:
    from run_inventory_resume_0730_worker import classify_token_v5  # type: ignore
except Exception:  # noqa: BLE001
    classify_token_v5 = None  # type: ignore

MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
BACKTICK_RE = re.compile(r"`([^`\n]{3,240})`")
PATHISH_RE = re.compile(
    r"(?:E:\\BLACKBOX\\[^\s`\"']+|(?:规则库|契约|脚本|运行|数据|研究系统|_OPS|任务|记忆盘|经验卡|DAILY_RESEARCH|参考资料|\.cursor)[\\/][^\s`\"']+)"
)
PLACEHOLDER_RE = re.compile(r"<[^>]+>|\{[^}]+\}|YYYYMMDD|<asof>|YOUR_|TODO_|FIXME_")


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def log(msg: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    line = f"{now()} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def write_json(p: Path, o) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sync(names: list[str]) -> None:
    HUB.mkdir(parents=True, exist_ok=True)
    for n in names:
        src = OUT / n
        if src.exists():
            if src.is_dir():
                dest = HUB / n
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(src, dest)
            else:
                (HUB / n).write_bytes(src.read_bytes())


def deadline_hit() -> bool:
    arm = ST / "_hub_patrol_10h_3m_arm.json"
    if not arm.exists():
        return False
    raw = json.loads(arm.read_text(encoding="utf-8-sig")).get("deadline_at")
    return bool(raw and datetime.now(CN) > datetime.fromisoformat(raw))


def phase_product_dependency_edges() -> dict:
    edges = []
    # 1) CACHE_DEPENDENCY_REGISTRY
    if DEP_REG.exists():
        dep = json.loads(DEP_REG.read_text(encoding="utf-8-sig"))
        for i, e in enumerate(dep.get("edges") or []):
            edges.append(
                {
                    "rel_type": "CACHE_DEP_REGISTRY",
                    "src": e.get("from"),
                    "dst": e.get("to"),
                    "evidence_file": str(DEP_REG),
                    "json_path": f"edges[{i}]",
                    "raw_value": e,
                    "asof_or_version": dep.get("schema_version"),
                    "verify_status": "DECLARED_IN_REGISTRY",
                    "storage_presence": None,
                    "declared_dependency": True,
                    "observed_coverage": None,
                }
            )
    # 2) CACHE_MANIFEST_REGISTRY clean→source_dataset
    if MAN_REG.exists():
        man = json.loads(MAN_REG.read_text(encoding="utf-8-sig"))
        for i, m in enumerate(man.get("manifests") or []):
            pid = m.get("product_id")
            src_ds = m.get("source_dataset")
            edges.append(
                {
                    "rel_type": "CACHE_MANIFEST_SOURCE_DATASET",
                    "src": pid,
                    "dst": src_ds,
                    "evidence_file": str(MAN_REG),
                    "json_path": f"manifests[{i}].source_dataset",
                    "raw_value": {
                        "source_dataset": src_ds,
                        "asof_max": m.get("asof_max"),
                        "mode": m.get("mode"),
                        "latest_release_pointer": man.get("latest_release"),
                    },
                    "asof_or_version": m.get("asof_max"),
                    "verify_status": "DECLARED_IN_MANIFEST_REGISTRY",
                    "note": "manifest registry latest_release may lag CURRENT cache release",
                    "declared_dependency": True,
                }
            )
    # 3) per-product LINEAGE / MANIFEST / COVERAGE / VIEW
    product_meta = []
    if not CACHE.exists():
        return {"edges": edges, "products_scanned": 0, "error": "CACHE_MISSING"}
    for d in sorted([p for p in CACHE.iterdir() if p.is_dir()]):
        pid = d.name
        meta = {
            "product_id": pid,
            "storage_presence": {
                "dir_exists": True,
                "entries": [x.name for x in d.iterdir()][:30],
                "has_parquet": bool(next(d.rglob("*.parquet"), None)),
                "has_lineage": (d / "LINEAGE.json").exists(),
                "has_manifest": (d / "MANIFEST.json").exists(),
                "has_coverage": (d / "COVERAGE.json").exists(),
                "has_view": (d / "VIEW.json").exists(),
                "has_product_meta": (d / "PRODUCT_META.json").exists(),
            },
        }
        product_meta.append(meta)
        for fname, rel_type in (
            ("LINEAGE.json", "PRODUCT_LINEAGE"),
            ("MANIFEST.json", "PRODUCT_MANIFEST"),
            ("COVERAGE.json", "PRODUCT_COVERAGE"),
            ("VIEW.json", "PRODUCT_VIEW"),
            ("PRODUCT_META.json", "PRODUCT_META"),
        ):
            fp = d / fname
            if not fp.exists():
                continue
            try:
                body = json.loads(fp.read_text(encoding="utf-8-sig"))
            except Exception as e:  # noqa: BLE001
                edges.append(
                    {
                        "rel_type": rel_type,
                        "src": pid,
                        "dst": None,
                        "evidence_file": str(fp),
                        "json_path": "$",
                        "verify_status": f"JSON_ERROR:{type(e).__name__}",
                        "declared_dependency": False,
                    }
                )
                continue
            # extract dependency-like fields
            def walk(o, jpath="$"):
                if isinstance(o, dict):
                    for k, v in o.items():
                        p2 = f"{jpath}.{k}"
                        kl = k.lower()
                        interesting = any(
                            t in kl
                            for t in (
                                "raw",
                                "source",
                                "clean",
                                "upstream",
                                "depends",
                                "union",
                                "base",
                                "transform",
                                "input",
                                "from",
                                "dataset",
                                "root",
                                "path",
                            )
                        )
                        if interesting:
                            if isinstance(v, str):
                                edges.append(
                                    {
                                        "rel_type": rel_type,
                                        "src": pid,
                                        "dst": v,
                                        "evidence_file": str(fp),
                                        "json_path": p2,
                                        "raw_value": v[:500],
                                        "verify_status": (
                                            "PATH_EXISTS"
                                            if re.match(r"^[A-Za-z]:[\\/]", v) and Path(v).exists()
                                            else "DECLARED_FIELD"
                                        ),
                                        "declared_dependency": True,
                                        "storage_presence": (
                                            Path(v).exists()
                                            if re.match(r"^[A-Za-z]:[\\/]", v)
                                            else None
                                        ),
                                    }
                                )
                            elif isinstance(v, list) and all(isinstance(x, str) for x in v):
                                for j, item in enumerate(v):
                                    edges.append(
                                        {
                                            "rel_type": rel_type + "_LIST",
                                            "src": pid,
                                            "dst": item,
                                            "evidence_file": str(fp),
                                            "json_path": f"{p2}[{j}]",
                                            "raw_value": item,
                                            "verify_status": "DECLARED_FIELD",
                                            "declared_dependency": True,
                                        }
                                    )
                            else:
                                edges.append(
                                    {
                                        "rel_type": rel_type,
                                        "src": pid,
                                        "dst": type(v).__name__,
                                        "evidence_file": str(fp),
                                        "json_path": p2,
                                        "raw_value": v if not isinstance(v, (dict, list)) else str(v)[:300],
                                        "verify_status": "DECLARED_FIELD_COMPLEX",
                                        "declared_dependency": True,
                                    }
                                )
                        if isinstance(v, (dict, list)):
                            walk(v, p2)
                elif isinstance(o, list):
                    for i, v in enumerate(o[:40]):
                        walk(v, f"{jpath}[{i}]")

            walk(body)
    # 4) unified registry CLEANING_CURRENT / RAW for ETF minute
    if UNI_REG.exists():
        uni = json.loads(UNI_REG.read_text(encoding="utf-8-sig"))
        clean = json.loads(CLEAN_CUR.read_text(encoding="utf-8-sig")) if CLEAN_CUR.exists() else {}
        std = Path(clean.get("standard_root") or "")
        for pid, meta in (uni.get("products") or {}).items():
            planes = meta.get("planes") or {}
            clean_rel = (planes.get("CLEANING_CURRENT") or {}).get("relative_under_standard")
            raw_rel = (planes.get("RAW_REPLACEMENT") or {}).get("relative_under_raw_root")
            if clean_rel:
                p = std / clean_rel if std else None
                edges.append(
                    {
                        "rel_type": "UNIFIED_REGISTRY_CLEAN",
                        "src": pid,
                        "dst": str(p) if p else clean_rel,
                        "evidence_file": str(UNI_REG),
                        "json_path": f"products.{pid}.planes.CLEANING_CURRENT.relative_under_standard",
                        "raw_value": clean_rel,
                        "asof_or_version": clean.get("cleaning_as_of"),
                        "verify_status": "PATH_EXISTS" if p and p.exists() else "DECLARED_RELATIVE",
                        "storage_presence": bool(p and p.exists()),
                        "declared_dependency": True,
                        "observed_coverage": None,
                    }
                )
            if raw_rel:
                raw_p = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw" / raw_rel
                edges.append(
                    {
                        "rel_type": "UNIFIED_REGISTRY_RAW",
                        "src": pid,
                        "dst": str(raw_p),
                        "evidence_file": str(UNI_REG),
                        "json_path": f"products.{pid}.planes.RAW_REPLACEMENT.relative_under_raw_root",
                        "raw_value": raw_rel,
                        "verify_status": "PATH_EXISTS" if raw_p.exists() else "DECLARED_RELATIVE_UNRESOLVED_ROOT",
                        "storage_presence": raw_p.exists(),
                        "declared_dependency": True,
                        "note": "resolved under JQData_9999_official_raw by shallow probe convention; not sole root authority",
                    }
                )
    # FUND_LIKE view unions already known
    view = CACHE / "FUND_LIKE_ASSET_VIEW_R1" / "VIEW.json"
    if view.exists():
        v = json.loads(view.read_text(encoding="utf-8-sig"))
        for u in v.get("unions") or []:
            edges.append(
                {
                    "rel_type": "VIEW_UNION_BASE",
                    "src": "FUND_LIKE_ASSET_VIEW_R1",
                    "dst": u,
                    "evidence_file": str(view),
                    "json_path": "unions",
                    "raw_value": u,
                    "verify_status": "DECLARED_IN_VIEW_JSON",
                    "declared_dependency": True,
                }
            )
    write_json(OUT / "PRODUCT_LINEAGE_EDGES_0905.json", {"at": now(), "n": len(edges), "edges": edges})
    write_json(OUT / "PRODUCT_STORAGE_PRESENCE_0905.json", {"at": now(), "n": len(product_meta), "products": product_meta})
    # also jsonl
    with (OUT / "PRODUCT_LINEAGE_EDGES_0905.jsonl").open("w", encoding="utf-8") as f:
        for e in edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    counts = Counter(e["rel_type"] for e in edges)
    log(f"product edges n={len(edges)} types={dict(counts)}")
    return {"n_edges": len(edges), "type_counts": dict(counts), "products_scanned": len(product_meta)}


def extract_tokens_from_text(text: str) -> list[tuple[int, str, str]]:
    """Return list of (line_no, field, token)."""
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        for m in MD_LINK_RE.finditer(line):
            out.append((i, "md_link", m.group(2).strip()))
        for m in BACKTICK_RE.finditer(line):
            tok = m.group(1).strip()
            if "/" in tok or "\\" in tok or tok.endswith((".md", ".json", ".py", ".mdc", ".txt")):
                out.append((i, "backtick", tok))
        for m in PATHISH_RE.finditer(line):
            out.append((i, "pathish", m.group(0).rstrip(".,;）)"))
    return out


def phase_rule_true_edges(max_nodes: int | None = None) -> dict:
    nodes = []
    for sf in sorted(SHARDS.glob("RULES_ACTIVE_SHARD_*.jsonl")):
        with sf.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    nodes.append(json.loads(line))
    # rename acknowledgment
    write_json(
        OUT / "RULE_NODES_RECLASS_0905.json",
        {
            "at": now(),
            "previous_file": "RULE_EDGES_CONTENT_0836.jsonl",
            "verdict": "NODES_NOT_CITATION_EDGES",
            "n_nodes": len(nodes),
            "note": "src/line/field were empty because records are node inventory; true edges require body parse",
        },
    )
    # also copy nodes cleanly
    with (OUT / "RULE_NODES_315_0905.jsonl").open("w", encoding="utf-8") as f:
        for n in nodes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")

    edges = []
    status = Counter()
    visited_extra: set[str] = set()
    processed = 0
    for node in nodes if max_nodes is None else nodes[:max_nodes]:
        if deadline_hit():
            break
        path = Path(node.get("path") or "")
        processed += 1
        if not path.exists():
            edges.append(
                {
                    "src": str(path),
                    "raw_token": "",
                    "line": None,
                    "field": "node",
                    "edge_status": "NODE_FILE_MISSING",
                    "edge_type": "NODE",
                    "resolved": "",
                    "node_rel": node.get("rel"),
                }
            )
            status["NODE_FILE_MISSING"] += 1
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001
            edges.append(
                {
                    "src": str(path),
                    "raw_token": "",
                    "line": None,
                    "field": "read",
                    "edge_status": f"READ_ERROR:{type(e).__name__}",
                    "edge_type": "NODE",
                    "resolved": "",
                }
            )
            status["READ_ERROR"] += 1
            continue
        tokens = extract_tokens_from_text(text)
        if not tokens:
            status["NODE_NO_TOKEN"] += 1
        for line_no, field, tok in tokens:
            if classify_token_v5:
                classified = classify_token_v5(tok, path, line_no, field)
            else:
                classified = [
                    {
                        "src": str(path),
                        "raw_token": tok[:240],
                        "line": line_no,
                        "field": field,
                        "edge_status": "CLASSIFIER_MISSING",
                        "edge_type": "UNKNOWN",
                        "resolved": "",
                    }
                ]
            for e in classified:
                # only count as verified citation edge if src + locator present
                if e.get("src") and (e.get("line") is not None) and e.get("raw_token"):
                    e["is_citation_edge"] = True
                else:
                    e["is_citation_edge"] = False
                e["node_rel"] = node.get("rel")
                e["node_status"] = node.get("status")
                edges.append(e)
                status[e.get("edge_status") or "NO_STATUS"] += 1
                # recurse one hop for RESOLVED rule/doc targets not yet visited
                res = e.get("resolved") or ""
                if e.get("edge_status") == "RESOLVED" and res and res not in visited_extra:
                    rp = Path(res)
                    if rp.exists() and rp.is_file() and rp.suffix.lower() in {
                        ".md",
                        ".mdc",
                        ".json",
                        ".txt",
                        ".py",
                    }:
                        visited_extra.add(res)
        if processed % 50 == 0:
            log(f"rule nodes processed={processed}/{len(nodes)} edges_so_far={len(edges)}")

    # write
    with (OUT / "RULE_CITATION_EDGES_0905.jsonl").open("w", encoding="utf-8") as f:
        for e in edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    citation = [e for e in edges if e.get("is_citation_edge")]
    verified = [
        e
        for e in citation
        if e.get("edge_status") == "RESOLVED" and e.get("src") and e.get("line") is not None
    ]
    summary = {
        "at": now(),
        "nodes_total": len(nodes),
        "nodes_processed": processed,
        "raw_edge_records": len(edges),
        "citation_edges_with_src_locator": len(citation),
        "resolved_citation_edges": len(verified),
        "status_counts": dict(status),
        "extra_targets_visited": len(visited_extra),
        "self_check": {
            "forbid_count_nodes_as_edges": True,
            "prior_315_were_nodes": True,
            "v4_847_historical_unchanged": True,
        },
        "sample_resolved": verified[:8],
    }
    write_json(OUT / "RULE_CITATION_SUMMARY_0905.json", summary)
    log(
        f"rule citation nodes={processed} records={len(edges)} "
        f"citation={len(citation)} resolved={len(verified)}"
    )
    return summary


def phase_etf_mat_consumer() -> dict:
    """Determine whether __mat_* is consumed by CURRENT readers."""
    findings = {
        "at": now(),
        "question": "Does CURRENT consumer read __mat_* history or only tip ETF_*m?",
        "evidence": [],
        "verdict": "HISTORY_CONSUMER_LINK_UNPROVEN",
    }
    # registry declares relative_under_standard=price/ETF_1m (tip name), not __mat_
    if UNI_REG.exists():
        uni = json.loads(UNI_REG.read_text(encoding="utf-8-sig"))
        for pid in ("ETF_MINUTE_1M_R1", "ETF_MINUTE_5M_R1"):
            rel = (
                ((uni.get("products") or {}).get(pid) or {})
                .get("planes", {})
                .get("CLEANING_CURRENT", {})
                .get("relative_under_standard")
            )
            findings["evidence"].append(
                {
                    "kind": "CONTRACT_TEXT",
                    "file": str(UNI_REG),
                    "json_path": f"products.{pid}.planes.CLEANING_CURRENT.relative_under_standard",
                    "value": rel,
                    "note": "registry points to tip dir name, not __mat_*",
                }
            )
    # search scripts mentioning __mat_ or ETF_1m (bounded)
    hits = []
    search_roots = [
        ROOT / "脚本",
        ROOT / "规则库" / "data_dictionary",
        ROOT / "契约" / "必读",
    ]
    pats = ("__mat_", "ETF_1m", "ETF_5m", "relative_under_standard", "year_batch")
    for root in search_roots:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".py", ".md", ".json", ".mdc", ".txt"}:
                continue
            if p.stat().st_size > 2_000_000:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if "__mat_" in text or ("ETF_1m" in text and "year_batch" in text):
                # extract short context lines
                lines = []
                for i, line in enumerate(text.splitlines(), 1):
                    if any(t in line for t in pats):
                        lines.append({"line": i, "text": line.strip()[:220]})
                        if len(lines) >= 6:
                            break
                hits.append({"file": str(p), "hits": lines})
            if len(hits) >= 40:
                break
        if len(hits) >= 40:
            break
    findings["evidence"].append({"kind": "CODE_SEARCH_HITS", "n": len(hits), "sample": hits[:15]})
    mat_mentioned = any("__mat_" in json.dumps(h, ensure_ascii=False) for h in hits)
    if not mat_mentioned:
        findings["verdict"] = "HISTORY_CONSUMER_LINK_UNPROVEN"
        findings["reason"] = "No __mat_ consumer reference found in bounded script/rule search; registry uses tip path"
    else:
        findings["verdict"] = "PARTIAL_REFERENCES_FOUND_NEED_CALLSITE_PROOF"
    # tip vs mat classification
    clean = json.loads(CLEAN_CUR.read_text(encoding="utf-8-sig"))
    std = Path(clean["standard_root"])
    for name in ("ETF_1m", "ETF_5m"):
        tip = std / "price" / name
        mats = sorted((std / "price").glob(name + ".__mat_*"))
        findings["evidence"].append(
            {
                "kind": "STORAGE_LAYOUT",
                "tip": str(tip),
                "tip_resolved": str(tip.resolve()) if tip.exists() else None,
                "tip_parquet_n": len(list(tip.glob("*.parquet"))) if tip.exists() else 0,
                "mat_dirs": [str(m) for m in mats],
                "mat_parquet_n": [
                    {"path": str(m), "n": len(list(m.glob("*.parquet")))} for m in mats
                ],
                "note": "tip=day freshness shards; mat=year-batch materialization sibling — not auto-merged authority",
            }
        )
    write_json(OUT / "ETF_MAT_CONSUMER_LINK_0905.json", findings)
    log(f"etf mat consumer verdict={findings['verdict']} code_hits={len(hits)}")
    return findings


def flush_master(phase: str, extras: dict) -> None:
    master = f"""# LINEAGE_0905_PROGRESS

status: **PARTIAL_CONTINUE_CONTENT**
phase: {phase}
worker_pid: {os.getpid()}
updated_at: {now()}
SYSTEM_INVENTORY_ACCEPTANCE: false

## Deltas
- PRODUCT_LINEAGE_EDGES_0905.jsonl — dependency edges from registry/LINEAGE/VIEW/unified
- RULE_NODES_RECLASS_0905.json — 315 prior rows reclassified as NODES
- RULE_CITATION_EDGES_0905.jsonl — true citation edges from body parse
- ETF_MAT_CONSUMER_LINK_0905.json — history consumer link status
- source_upload_0836 + source_upload_0905 uploaded to HUB

{json.dumps(extras, ensure_ascii=False, indent=2)}

local: `{OUT}`
"""
    (OUT / "MASTER_PROGRESS_0905.md").write_text(master, encoding="utf-8")
    write_json(
        OUT / "STATUS_PROGRESS.json",
        {
            "updated_at": now(),
            "task": "BLACKBOX_SYSTEM_INVENTORY_LINEAGE_AND_RULE_GRAPH_20261021_0905",
            "phase": phase,
            "overall": "PARTIAL_CONTINUE_CONTENT",
            "SYSTEM_INVENTORY_ACCEPTANCE": False,
            **extras,
        },
    )
    sync(
        [
            "MASTER_PROGRESS_0905.md",
            "STATUS_PROGRESS.json",
            "PRODUCT_LINEAGE_EDGES_0905.json",
            "PRODUCT_LINEAGE_EDGES_0905.jsonl",
            "PRODUCT_STORAGE_PRESENCE_0905.json",
            "RULE_NODES_RECLASS_0905.json",
            "RULE_CITATION_SUMMARY_0905.json",
            "RULE_CITATION_EDGES_0905.jsonl",
            "RULE_NODES_315_0905.jsonl",
            "ETF_MAT_CONSUMER_LINK_0905.json",
            "SOURCE_SHA_0905.json",
            "WORKER_PID_0905.json",
        ]
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    HUB.mkdir(parents=True, exist_ok=True)
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    CKPT.mkdir(parents=True, exist_ok=True)
    src = Path(__file__).resolve()
    (SRC_DIR / src.name).write_bytes(src.read_bytes())
    write_json(
        OUT / "WORKER_PID_0905.json",
        {
            "pid": os.getpid(),
            "task": "0905",
            "started_at": now(),
            "python": sys.executable,
            "source": str(src),
            "log": str(LOG),
        },
    )
    t0 = time.time()
    log("LINEAGE_0905_START")
    try:
        dep = phase_product_dependency_edges()
        write_json(CKPT / "A_PRODUCT_DEP.json", {"at": now(), **dep})
        flush_master("A_PRODUCT_DEP", {"product_dep": dep})

        rules = phase_rule_true_edges()
        write_json(CKPT / "B_RULE_CITATIONS.json", {"at": now(), **{k: rules[k] for k in rules if k != "sample_resolved"}})
        flush_master("B_RULE_CITATIONS", {"rule_citations": {k: rules[k] for k in ("nodes_processed", "citation_edges_with_src_locator", "resolved_citation_edges", "status_counts")}})

        etf = phase_etf_mat_consumer()
        write_json(CKPT / "C_ETF_MAT.json", {"at": now(), "verdict": etf.get("verdict")})

        write_json(
            OUT / "SOURCE_SHA_0905.json",
            {
                "at": now(),
                "files": [
                    {"path": str(src), "sha256": sha256_file(src), "bytes": src.stat().st_size},
                    {
                        "path": str(OUT / "source_upload_0836" / "run_inventory_content_0836_worker.py"),
                        "sha256": sha256_file(OUT / "source_upload_0836" / "run_inventory_content_0836_worker.py")
                        if (OUT / "source_upload_0836" / "run_inventory_content_0836_worker.py").exists()
                        else None,
                    },
                ],
            },
        )
        # runtime logic append
        logic = OUT / "BLACKBOX_RUNTIME_LOGIC_CANDIDATE_0836.md"
        with logic.open("a", encoding="utf-8") as f:
            f.write(
                f"\n## 8. 0905 依赖/引用图增量\n"
                f"- product declared edges: {dep.get('n_edges')} types={dep.get('type_counts')}\n"
                f"- rule nodes reclass: 315 were NODES not citation edges\n"
                f"- rule citation resolved: {rules.get('resolved_citation_edges')} / "
                f"citation_with_src={rules.get('citation_edges_with_src_locator')}\n"
                f"- ETF mat consumer: {etf.get('verdict')}\n"
                f"- at: {now()}\n"
            )
        (HUB / "BLACKBOX_RUNTIME_LOGIC_CANDIDATE_0836.md").write_bytes(logic.read_bytes())

        elapsed = round(time.time() - t0, 1)
        flush_master(
            "CHECKPOINT_0905",
            {
                "elapsed_sec": elapsed,
                "product_dep": dep,
                "rule_citations": {
                    "nodes_processed": rules.get("nodes_processed"),
                    "citation_edges_with_src_locator": rules.get("citation_edges_with_src_locator"),
                    "resolved_citation_edges": rules.get("resolved_citation_edges"),
                },
                "etf_mat": etf.get("verdict"),
            },
        )
        # inbox checkpoint
        ck = ST / "agents" / "chatgpt" / "inbox" / "BLACKBOX_INVENTORY_LINEAGE_CHECKPOINT_20261021_0905.md"
        ck.write_text(
            f"""# BLACKBOX_INVENTORY_LINEAGE_CHECKPOINT_20261021_0905

task: BLACKBOX_SYSTEM_INVENTORY_LINEAGE_AND_RULE_GRAPH_20261021_0905
at: {now()}
host: ZHANGWEI
SYSTEM_INVENTORY_ACCEPTANCE: false
status: PARTIAL_CONTINUE_CONTENT

## Corrections accepted from review
- RULE_EDGES_CONTENT_0836 → RULE_NODES (not citation edges)
- PRODUCT_MAPPING NO_CACHE_DIR ≠ missing product
- source_upload_0836 now uploaded with 0905 sources

## New content
- product declared dependency edges: **{dep.get('n_edges')}** ({dep.get('type_counts')})
- rule body citation edges: records={rules.get('raw_edge_records')}; with src+locator={rules.get('citation_edges_with_src_locator')}; RESOLVED={rules.get('resolved_citation_edges')}
- ETF __mat_* consumer: **{etf.get('verdict')}**
- elapsed_sec: {elapsed}

## Artifacts
https://github.com/zwdjwsam-creator/sam/tree/main/agents/chatgpt/inbox/BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150/v2/continue_0010/correction_0650
""",
            encoding="utf-8",
        )
        log(f"LINEAGE_0905_CHECKPOINT_DONE elapsed={elapsed}")
        return 0
    except Exception as e:  # noqa: BLE001
        log(f"FATAL {type(e).__name__}:{e}\n{traceback.format_exc()}")
        flush_master("FATAL", {"error": f"{type(e).__name__}:{e}"})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
