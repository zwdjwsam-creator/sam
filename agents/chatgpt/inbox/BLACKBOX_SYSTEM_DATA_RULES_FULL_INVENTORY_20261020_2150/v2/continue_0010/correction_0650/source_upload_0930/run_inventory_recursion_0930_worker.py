# -*- coding: utf-8 -*-
"""0930: true recursive rule worklist + semantic lineage + ETF reader call-chain (isolation only)."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import time
import traceback
from collections import Counter, deque
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
UNI_REG = ROOT / "规则库" / "data_dictionary" / "unified_market_data_plane_registry_r1.json"
DEP_REG = ROOT / "数据" / "回测缓存" / "registry" / "CACHE_DEPENDENCY_REGISTRY.json"
MAN_REG = ROOT / "数据" / "回测缓存" / "registry" / "CACHE_MANIFEST_REGISTRY.json"
CLEAN_CUR = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
LOG = OUT / "recursion_0930.log"
SRC_DIR = OUT / "source_upload_0930"
CKPT = OUT / "checkpoints_0930"
BODY_CACHE = OUT / "rule_body_cache_0930"

sys.path.insert(0, str(OUT / "source_upload_0730"))
try:
    from run_inventory_resume_0730_worker import classify_token_v5  # type: ignore
except Exception:  # noqa: BLE001
    classify_token_v5 = None  # type: ignore

MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
BACKTICK_RE = re.compile(r"`([^`\n]{2,240})`")
PATHISH_RE = re.compile(
    r"(?:E:\\BLACKBOX\\[^\s`\"']+|(?:规则库|契约|脚本|运行|数据|研究系统|_OPS|任务|记忆盘|经验卡|DAILY_RESEARCH|参考资料|\.cursor)[\\/][^\s`\"']+)"
)
RULE_ID_RE = re.compile(r"\b([A-Z][A-Z0-9_]{3,}(?:_R\d+)?)\b")
CMD_RE = re.compile(
    r"(python(?:\.exe)?|\.venv\\Scripts\\python|powershell|cmd\.exe|--mode\s+\w+)",
    re.I,
)
DOC_SUFFIX = {".md", ".mdc", ".json", ".txt", ".py", ".yml", ".yaml"}


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


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1024 * 1024), b""):
            h.update(c)
    return h.hexdigest()


def sync(names: list[str]) -> None:
    HUB.mkdir(parents=True, exist_ok=True)
    for n in names:
        src = OUT / n
        if not src.exists():
            continue
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


def strict_read(path: Path) -> dict:
    """Strict decode; record encoding failures. Cache by path+mtime."""
    BODY_CACHE.mkdir(parents=True, exist_ok=True)
    try:
        st = path.stat()
    except OSError as e:
        return {"ok": False, "error": f"STAT:{e}", "text": None, "sha256": None}
    key = sha256_bytes(f"{path}|{st.st_mtime_ns}|{st.st_size}".encode())
    cache_p = BODY_CACHE / f"{key}.json"
    if cache_p.exists():
        return json.loads(cache_p.read_text(encoding="utf-8"))
    raw = path.read_bytes()
    out = {
        "ok": False,
        "path": str(path),
        "bytes": len(raw),
        "sha256": sha256_bytes(raw),
        "encoding": None,
        "text": None,
        "error": None,
        "summary": None,
    }
    for enc in ("utf-8", "utf-8-sig"):
        try:
            text = raw.decode(enc)
            out.update(ok=True, encoding=enc, text=text, error=None)
            break
        except UnicodeDecodeError as e:
            out["error"] = f"DECODE_{enc}:{e}"
    if out["ok"] and out["text"] is not None:
        lines = out["text"].splitlines()
        out["summary"] = {
            "n_lines": len(lines),
            "head": "\n".join(lines[:8])[:500],
            "tail": "\n".join(lines[-4:])[:300],
        }
        # drop full text from cache to save space — keep hash+summary; store text file beside
        text_p = BODY_CACHE / f"{key}.txt"
        text_p.write_text(out["text"], encoding="utf-8")
        cache_body = {k: v for k, v in out.items() if k != "text"}
        cache_body["text_cache"] = str(text_p)
        cache_p.write_text(json.dumps(cache_body, ensure_ascii=False), encoding="utf-8")
        out["text_cache"] = str(text_p)
    else:
        cache_p.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def load_text_from_read(rd: dict) -> str | None:
    if rd.get("text"):
        return rd["text"]
    tc = rd.get("text_cache")
    if tc and Path(tc).exists():
        return Path(tc).read_text(encoding="utf-8")
    return None


def is_command_example(tok: str) -> bool:
    if CMD_RE.search(tok) and (" -u " in tok or " --" in tok or ".py " in tok or tok.count(" ") >= 2):
        return True
    if tok.strip().startswith(("python ", "powershell ", "E:\\BLACKBOX\\.venv")) and " " in tok.strip():
        return True
    return False


def extract_tokens(text: str) -> list[tuple[int, str, str]]:
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        for m in MD_LINK_RE.finditer(line):
            href = m.group(2).strip()
            # real href only
            if href and not href.startswith(("javascript:", "mailto:")):
                out.append((i, "md_href", href))
        for m in BACKTICK_RE.finditer(line):
            tok = m.group(1).strip()
            if not tok:
                continue
            if is_command_example(tok):
                out.append((i, "command_example", tok))
                # also extract .py paths inside command
                for pm in re.finditer(r"(E:\\BLACKBOX\\[^\s\"']+\.py|[脚本\\/][^\s\"']+\.py)", tok):
                    out.append((i, "cmd_script_path", pm.group(1)))
                continue
            if "/" in tok or "\\" in tok or tok.endswith(tuple(DOC_SUFFIX)):
                out.append((i, "backtick_path", tok))
            elif RULE_ID_RE.fullmatch(tok):
                out.append((i, "rule_id", tok))
        for m in PATHISH_RE.finditer(line):
            tok = m.group(0).rstrip(".,;)")
            if is_command_example(tok):
                out.append((i, "command_example", tok))
            else:
                out.append((i, "pathish", tok))
        # bare rule ids in plain text (not only backticks)
        if "RULE" in line or "_R1" in line or "_R2" in line or "GATE" in line or "PRECHECK" in line:
            for m in RULE_ID_RE.finditer(line):
                tok = m.group(1)
                if len(tok) >= 8:
                    out.append((i, "rule_id_plain", tok))
    return out


def build_rule_id_index(seed_nodes: list[dict]) -> dict[str, str]:
    """Map RULE_ID -> path from node titles and filenames."""
    idx = {}
    for n in seed_nodes:
        path = n.get("path") or ""
        rel = n.get("rel") or ""
        title = n.get("title_or_rule_id") or ""
        for cand in (title, Path(path).stem, Path(rel).stem):
            if RULE_ID_RE.fullmatch(cand or ""):
                idx[cand] = path
        # filename patterns BLACKBOX_HAND_..._R1.md
        stem = Path(path).stem
        m = RULE_ID_RE.search(stem)
        if m:
            idx.setdefault(m.group(1), path)
    # also scan 规则库 hand for ids
    hand = ROOT / "规则库" / "hand_hard_rules"
    if hand.exists():
        for p in hand.glob("*.md"):
            stem = p.stem
            if RULE_ID_RE.fullmatch(stem) or RULE_ID_RE.search(stem):
                key = stem if RULE_ID_RE.fullmatch(stem) else RULE_ID_RE.search(stem).group(1)
                idx.setdefault(key, str(p))
        for p in hand.glob("*.json"):
            stem = p.stem
            if RULE_ID_RE.search(stem):
                idx.setdefault(RULE_ID_RE.search(stem).group(1), str(p))
    return idx


def classify_ref(tok: str, src: Path, line: int, field: str, rule_id_index: dict) -> list[dict]:
    if field == "command_example":
        return [
            {
                "src": str(src),
                "raw_token": tok[:240],
                "line": line,
                "field": field,
                "edge_status": "COMMAND_EXAMPLE_STATIC",
                "edge_type": "COMMAND",
                "resolved": "",
                "is_citation_edge": True,
            }
        ]
    if field in {"rule_id", "rule_id_plain"}:
        target = rule_id_index.get(tok)
        if target and Path(target).exists():
            return [
                {
                    "src": str(src),
                    "raw_token": tok,
                    "line": line,
                    "field": field,
                    "edge_status": "RESOLVED",
                    "edge_type": "RULE_ID",
                    "resolved": target,
                    "is_citation_edge": True,
                }
            ]
        return [
            {
                "src": str(src),
                "raw_token": tok,
                "line": line,
                "field": field,
                "edge_status": "RULE_ID_UNRESOLVED",
                "edge_type": "RULE_ID",
                "resolved": "",
                "is_citation_edge": True,
            }
        ]
    if field == "md_href" and not re.search(r"[\\/]", tok) and not tok.startswith(("http", "#", "E:")):
        return [
            {
                "src": str(src),
                "raw_token": tok[:240],
                "line": line,
                "field": field,
                "edge_status": "UNRESOLVED_BASE",
                "edge_type": "MD_HREF",
                "resolved": "",
                "is_citation_edge": True,
                "note": "relative href without proven base",
            }
        ]
    if classify_token_v5:
        rows = classify_token_v5(tok, src, line, field)
        for r in rows:
            r["is_citation_edge"] = bool(r.get("src") and r.get("line") is not None and r.get("raw_token"))
        return rows
    return [
        {
            "src": str(src),
            "raw_token": tok[:240],
            "line": line,
            "field": field,
            "edge_status": "CLASSIFIER_MISSING",
            "edge_type": "UNKNOWN",
            "resolved": "",
            "is_citation_edge": True,
        }
    ]


def in_rule_doc_scope(path: Path) -> bool:
    try:
        s = str(path.resolve())
    except OSError:
        s = str(path)
    if not s.startswith(str(ROOT)):
        return False
    if path.suffix.lower() in DOC_SUFFIX:
        return True
    # allow extensionless under 规则库? skip
    return False


def phase_true_recursion(max_reads: int = 800) -> dict:
    seeds = []
    for sf in sorted(SHARDS.glob("RULES_ACTIVE_SHARD_*.jsonl")):
        with sf.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    seeds.append(json.loads(line))
    rule_id_index = build_rule_id_index(seeds)
    write_json(OUT / "RULE_ID_INDEX_0930.json", {"at": now(), "n": len(rule_id_index), "sample": dict(list(rule_id_index.items())[:40])})

    pending: deque[str] = deque()
    queued: set[str] = set()
    read_state: dict[str, dict] = {}
    failed: list[dict] = []
    excluded: list[dict] = []
    edges: list[dict] = []
    hop_examples: list[dict] = []

    def enqueue(p: str, reason: str, from_src: str | None = None) -> None:
        if p in queued:
            return
        path = Path(p)
        if path.suffix.lower() == ".parquet" or path.suffix.lower() in {".exe", ".dll", ".pyd"}:
            excluded.append({"path": p, "reason": "NOT_RULE_BODY", "from": from_src})
            return
        if path.is_dir():
            excluded.append({"path": p, "reason": "DIRECTORY_NOT_FULL_RECURSED", "from": from_src})
            return
        if not in_rule_doc_scope(path) and path.suffix.lower() not in DOC_SUFFIX:
            excluded.append({"path": p, "reason": "OUT_OF_SCOPE", "from": from_src})
            return
        queued.add(p)
        pending.append(p)
        if from_src and len(hop_examples) < 20:
            hop_examples.append({"from": from_src, "to": p, "reason": reason})

    for n in seeds:
        p = n.get("path")
        if p:
            enqueue(p, "seed_315")

    reads = 0
    while pending and reads < max_reads:
        if deadline_hit():
            break
        cur = pending.popleft()
        path = Path(cur)
        if cur in read_state and read_state[cur].get("read_ok") is not None:
            continue
        if not path.exists():
            read_state[cur] = {"read_ok": False, "error": "MISSING"}
            failed.append({"path": cur, "error": "MISSING"})
            continue
        rd = strict_read(path)
        reads += 1
        text = load_text_from_read(rd) if rd.get("ok") else None
        read_state[cur] = {
            "read_ok": bool(rd.get("ok")),
            "encoding": rd.get("encoding"),
            "sha256": rd.get("sha256"),
            "bytes": rd.get("bytes"),
            "error": rd.get("error"),
            "summary": rd.get("summary"),
            "read_at": now(),
        }
        if not text:
            failed.append({"path": cur, "error": rd.get("error") or "NO_TEXT"})
            continue
        for line_no, field, tok in extract_tokens(text):
            for e in classify_ref(tok, path, line_no, field, rule_id_index):
                e["hop_src_read"] = True
                edges.append(e)
                res = e.get("resolved") or ""
                if e.get("edge_status") == "RESOLVED" and res:
                    enqueue(res, "citation_resolved", from_src=cur)
        if reads % 50 == 0:
            log(f"recursion reads={reads} pending={len(pending)} queued={len(queued)} edges={len(edges)}")
            # checkpoint worklist
            write_json(
                CKPT / "recursion_worklist.json",
                {
                    "at": now(),
                    "reads": reads,
                    "pending_n": len(pending),
                    "queued_n": len(queued),
                    "pending_head": list(pending)[:30],
                },
            )

    # dedupe edges
    uniq = {}
    dups = 0
    for e in edges:
        key = (e.get("src"), e.get("line"), e.get("raw_token"), e.get("resolved"))
        if key in uniq:
            dups += 1
            continue
        uniq[key] = e
    deduped = list(uniq.values())
    status = Counter(e.get("edge_status") for e in deduped)
    broken_class = Counter()
    for e in deduped:
        if e.get("edge_status") == "BROKEN_CONFIRMED":
            tok = e.get("raw_token") or ""
            if is_command_example(tok):
                broken_class["SHOULD_BE_COMMAND_EXAMPLE"] += 1
            else:
                broken_class["PATH_BROKEN_CANDIDATE"] += 1

    # write outputs
    with (OUT / "RULE_CITATION_EDGES_DEDUP_0930.jsonl").open("w", encoding="utf-8") as f:
        for e in deduped:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    summary = {
        "at": now(),
        "seed_nodes": len(seeds),
        "discovered_queued": len(queued),
        "read_ok": sum(1 for v in read_state.values() if v.get("read_ok")),
        "read_failed": len(failed),
        "excluded": len(excluded),
        "pending_remaining": len(pending),
        "raw_edge_records": len(edges),
        "dedup_edge_records": len(deduped),
        "duplicate_extractor_hits": dups,
        "status_counts_dedup": dict(status),
        "broken_reclass_hint": dict(broken_class),
        "targets_discovered_vs_read": {
            "queued": len(queued),
            "read": sum(1 for v in read_state.values() if v.get("read_ok")),
            "note": "queued includes seeds; recursion READ bodies of enqueued targets",
        },
        "hop_examples": hop_examples,
        "rule_id_index_size": len(rule_id_index),
        "self_check": {
            "visited_not_substitute_for_read": True,
            "extra_targets_visited_0905_was_discovered_only": True,
            "RESOLVED_means_path_located_not_semantic_pass": True,
            "NODE_NO_TOKEN_not_in_edge_status": True,
        },
    }
    write_json(OUT / "RULE_RECURSION_SUMMARY_0930.json", summary)
    write_json(OUT / "RULE_READ_STATE_0930.json", {"at": now(), "n": len(read_state), "files": read_state})
    write_json(OUT / "RULE_FAILED_EXCLUDED_0930.json", {"failed": failed[:200], "excluded": excluded[:200]})
    log(
        f"recursion done read_ok={summary['read_ok']} queued={summary['discovered_queued']} "
        f"dedup_edges={summary['dedup_edge_records']} pending={summary['pending_remaining']}"
    )
    return summary


def phase_semantic_lineage() -> dict:
    raw_path = OUT / "PRODUCT_LINEAGE_EDGES_0905.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {"edges": []}
    entity_edges = []
    attributes = []
    unresolved_struct = []
    for e in raw.get("edges") or []:
        dst = e.get("dst")
        src = e.get("src")
        rel = e.get("rel_type") or ""
        jp = e.get("json_path") or ""
        # type-name junk
        if isinstance(dst, str) and dst in {"list", "dict", "NoneType", "str", "int", "float", "bool"}:
            unresolved_struct.append({**e, "reason": "UNRESOLVED_STRUCTURE_TYPE_NAME"})
            continue
        # metadata attributes
        jl = jp.lower()
        if any(t in jl for t in ("asof", "version", "transform", "formula", "created_at", "mode", "lookback")) or (
            isinstance(dst, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", dst or "")
        ):
            attributes.append(
                {
                    "entity": src,
                    "attr_key": jp,
                    "attr_value": dst,
                    "evidence_file": e.get("evidence_file"),
                    "rel_type": rel,
                }
            )
            continue
        # entity dependency
        direction = "upstream->product"
        if rel in {"VIEW_UNION_BASE", "PRODUCT_VIEW_LIST"}:
            direction = "view->base"
            relation = "unions"
        elif rel in {"CACHE_DEP_REGISTRY"}:
            direction = "from->to"
            relation = "depends_on"
        elif rel in {"CACHE_MANIFEST_SOURCE_DATASET", "UNIFIED_REGISTRY_CLEAN", "UNIFIED_REGISTRY_RAW", "PRODUCT_LINEAGE"}:
            relation = "sourced_from"
        else:
            relation = "declared_field"
        entity_edges.append(
            {
                "src": src,
                "dst": dst,
                "relation": relation,
                "direction": direction,
                "rel_type_raw": rel,
                "evidence_file": e.get("evidence_file"),
                "json_path": jp,
                "raw_value": e.get("raw_value"),
                "verify_status": e.get("verify_status"),
                "path_exists": e.get("storage_presence"),
                "dependency_usable": None,  # PATH_EXISTS != USABLE
                "entity_types": {
                    "src": "product_or_logical",
                    "dst": "path_or_product_or_dataset",
                },
            }
        )
    # ensure registry from/to normalized
    if DEP_REG.exists():
        dep = json.loads(DEP_REG.read_text(encoding="utf-8-sig"))
        for i, ed in enumerate(dep.get("edges") or []):
            entity_edges.append(
                {
                    "src": ed.get("from"),
                    "dst": ed.get("to"),
                    "relation": "depends_on",
                    "direction": "from->to",
                    "rel_type_raw": "CACHE_DEP_REGISTRY_NORM",
                    "evidence_file": str(DEP_REG),
                    "json_path": f"edges[{i}]",
                    "raw_value": ed,
                    "verify_status": "DECLARED_IN_REGISTRY",
                    "dependency_usable": None,
                    "lookback": ed.get("lookback"),
                    "status": ed.get("status"),
                }
            )
    write_json(
        OUT / "PRODUCT_ENTITY_DEPENDENCY_EDGES_0930.json",
        {"at": now(), "n": len(entity_edges), "edges": entity_edges},
    )
    write_json(
        OUT / "PRODUCT_LINEAGE_ATTRIBUTES_0930.json",
        {"at": now(), "n": len(attributes), "attributes": attributes[:500]},
    )
    write_json(
        OUT / "PRODUCT_LINEAGE_UNRESOLVED_STRUCTURE_0930.json",
        {"at": now(), "n": len(unresolved_struct), "items": unresolved_struct},
    )
    with (OUT / "PRODUCT_ENTITY_DEPENDENCY_EDGES_0930.jsonl").open("w", encoding="utf-8") as f:
        for e in entity_edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    summary = {
        "raw_field_records_0905": len(raw.get("edges") or []),
        "entity_dependency_edges": len(entity_edges),
        "attributes": len(attributes),
        "unresolved_structure": len(unresolved_struct),
        "note": "PATH_EXISTS != DEPENDENCY_USABLE",
    }
    log(f"semantic lineage entity={summary['entity_dependency_edges']} attr={summary['attributes']} struct={summary['unresolved_structure']}")
    return summary


def phase_etf_callchain() -> dict:
    """Follow registry keys into code, not __mat_ literals."""
    keys = [
        "relative_under_standard",
        "RAW_REPLACEMENT",
        "year_batch_regex",
        "day_name_regex",
        "CLEANING_CURRENT",
        "ETF_MINUTE_1M_R1",
        "resolve_product",
        "unified_market_data_plane",
    ]
    roots = [
        ROOT / "脚本",
        ROOT / "规则库" / "data_dictionary",
        ROOT / "中间层",
        ROOT / "工具",
    ]
    hits = []
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in {".py", ".json", ".md", ".mdc"}:
                continue
            if p.stat().st_size > 1_500_000:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="strict")
            except Exception:
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")
                    enc = "replace"
                except Exception:
                    continue
            else:
                enc = "strict"
            if not any(k in text for k in keys):
                continue
            lines = []
            for i, line in enumerate(text.splitlines(), 1):
                if any(k in line for k in keys):
                    lines.append({"line": i, "text": line.strip()[:240]})
                    if len(lines) >= 8:
                        break
            # function names nearby
            funcs = re.findall(r"^\s*def\s+(\w+)", text, re.M)[:20]
            hits.append(
                {
                    "file": str(p),
                    "encoding": enc,
                    "funcs_sample": funcs,
                    "lines": lines,
                    "has_mat_literal": "__mat_" in text,
                    "has_year_batch_regex": "year_batch_regex" in text,
                    "has_relative_under_standard": "relative_under_standard" in text,
                }
            )
            if len(hits) >= 60:
                break
        if len(hits) >= 60:
            break
    # classify callchain status
    reader_hits = [h for h in hits if h.get("has_relative_under_standard") or h.get("has_year_batch_regex")]
    verdict = (
        "CALLCHAIN_CANDIDATES_FOUND_NEED_FRAGMENT_SELECT_PROOF"
        if reader_hits
        else "HISTORY_CONSUMER_LINK_UNPROVEN"
    )
    out = {
        "at": now(),
        "search_keys": keys,
        "files_hit": len(hits),
        "reader_like_hits": len(reader_hits),
        "verdict": verdict,
        "sample_reader_like": reader_hits[:15],
        "sample_other": [h for h in hits if h not in reader_hits][:10],
        "note": "Does not merge __mat_ into authority; tip path remains registry CLEANING_CURRENT",
    }
    write_json(OUT / "ETF_READER_CALLCHAIN_0930.json", out)
    log(f"etf callchain verdict={verdict} hits={len(hits)} reader_like={len(reader_hits)}")
    return out


def flush(phase: str, extras: dict) -> None:
    master = f"""# RECURSION_0930_PROGRESS

status: **PARTIAL_CONTINUE_CONTENT**
phase: {phase}
worker_pid: {os.getpid()}
updated_at: {now()}
SYSTEM_INVENTORY_ACCEPTANCE: false

{json.dumps(extras, ensure_ascii=False, indent=2)}

local: `{OUT}`
"""
    (OUT / "MASTER_PROGRESS_0930.md").write_text(master, encoding="utf-8")
    write_json(
        OUT / "STATUS_PROGRESS.json",
        {
            "updated_at": now(),
            "task": "BLACKBOX_SYSTEM_INVENTORY_RECURSION_AND_SEMANTICS_20261021_0930",
            "phase": phase,
            "overall": "PARTIAL_CONTINUE_CONTENT",
            "SYSTEM_INVENTORY_ACCEPTANCE": False,
            **extras,
        },
    )
    sync(
        [
            "MASTER_PROGRESS_0930.md",
            "STATUS_PROGRESS.json",
            "RULE_RECURSION_SUMMARY_0930.json",
            "RULE_CITATION_EDGES_DEDUP_0930.jsonl",
            "RULE_ID_INDEX_0930.json",
            "RULE_FAILED_EXCLUDED_0930.json",
            "PRODUCT_ENTITY_DEPENDENCY_EDGES_0930.json",
            "PRODUCT_ENTITY_DEPENDENCY_EDGES_0930.jsonl",
            "PRODUCT_LINEAGE_ATTRIBUTES_0930.json",
            "PRODUCT_LINEAGE_UNRESOLVED_STRUCTURE_0930.json",
            "ETF_READER_CALLCHAIN_0930.json",
            "SOURCE_SHA_0930.json",
            "WORKER_PID_0930.json",
        ]
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    CKPT.mkdir(parents=True, exist_ok=True)
    src = Path(__file__).resolve()
    (SRC_DIR / src.name).write_bytes(src.read_bytes())
    write_json(
        OUT / "WORKER_PID_0930.json",
        {"pid": os.getpid(), "task": "0930", "started_at": now(), "source": str(src), "log": str(LOG)},
    )
    t0 = time.time()
    log("RECURSION_0930_START")
    try:
        # also dedupe prior 2327 quickly for reconcile
        prior = OUT / "RULE_CITATION_EDGES_0905.jsonl"
        if prior.exists():
            seen = set()
            n = 0
            d = 0
            with prior.open(encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    n += 1
                    e = json.loads(line)
                    k = (e.get("src"), e.get("line"), e.get("raw_token"), e.get("resolved"))
                    if k in seen:
                        d += 1
                    else:
                        seen.add(k)
            write_json(
                OUT / "RULE_0905_DEDUP_RECONCILE.json",
                {"raw": n, "unique": len(seen), "dups": d, "review_expected_unique": 1846},
            )

        sem = phase_semantic_lineage()
        flush("A_SEMANTIC_LINEAGE", {"semantic": sem})

        rec = phase_true_recursion(max_reads=900)
        flush("B_TRUE_RECURSION", {"recursion": {k: rec[k] for k in rec if k != "hop_examples"}})

        etf = phase_etf_callchain()
        flush("C_ETF_CALLCHAIN", {"etf": {"verdict": etf["verdict"], "files_hit": etf["files_hit"], "reader_like": etf["reader_like_hits"]}})

        write_json(
            OUT / "SOURCE_SHA_0930.json",
            {
                "at": now(),
                "files": [{"path": str(src), "sha256": sha256_file(src), "bytes": src.stat().st_size}],
            },
        )
        elapsed = round(time.time() - t0, 1)
        extras = {
            "elapsed_sec": elapsed,
            "semantic": sem,
            "recursion": {
                "read_ok": rec.get("read_ok"),
                "queued": rec.get("discovered_queued"),
                "dedup_edges": rec.get("dedup_edge_records"),
                "pending": rec.get("pending_remaining"),
                "status_counts_dedup": rec.get("status_counts_dedup"),
            },
            "etf": etf.get("verdict"),
        }
        flush("CHECKPOINT_0930", extras)
        ck = ST / "agents" / "chatgpt" / "inbox" / "BLACKBOX_INVENTORY_RECURSION_CHECKPOINT_20261021_0930.md"
        ck.write_text(
            f"""# BLACKBOX_INVENTORY_RECURSION_CHECKPOINT_20261021_0930

task: BLACKBOX_SYSTEM_INVENTORY_RECURSION_AND_SEMANTICS_20261021_0930
at: {now()}
host: ZHANGWEI
SYSTEM_INVENTORY_ACCEPTANCE: false
status: PARTIAL_CONTINUE_CONTENT
elapsed_sec: {elapsed}

## Corrections applied
- 0905 edges dedup reconcile (expect ~1846 unique)
- True worklist recursion: enqueue+read targets (not visited-only)
- Rule ID index + bare ID tokens
- COMMAND_EXAMPLE_STATIC separation
- Lineage split: entity deps vs attributes vs unresolved structure
- ETF callchain via registry keys (not only __mat_ literal)

## Numbers
- semantic entity edges: {sem.get('entity_dependency_edges')} (attrs={sem.get('attributes')}, unresolved_struct={sem.get('unresolved_structure')})
- recursion: queued={rec.get('discovered_queued')} read_ok={rec.get('read_ok')} dedup_edges={rec.get('dedup_edge_records')} pending={rec.get('pending_remaining')}
- ETF: {etf.get('verdict')} (reader_like_files={etf.get('reader_like_hits')})

## Artifacts
local: `{OUT}`
hub tree: correction_0650/
""",
            encoding="utf-8",
        )
        log(f"RECURSION_0930_DONE elapsed={elapsed}")
        return 0
    except Exception as e:  # noqa: BLE001
        log(f"FATAL {type(e).__name__}:{e}\n{traceback.format_exc()}")
        flush("FATAL", {"error": f"{type(e).__name__}:{e}"})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
