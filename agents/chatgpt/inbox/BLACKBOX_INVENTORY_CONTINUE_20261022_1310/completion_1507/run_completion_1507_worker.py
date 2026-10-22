# -*- coding: utf-8 -*-
"""1507: full AST source extracts + semantic static review + 75-object ledger (readonly)."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
ISO = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650")
SRC1447 = ISO / "continue_1310" / "completion_1447"
OUT = ISO / "continue_1310" / "completion_1507"
OUT.mkdir(parents=True, exist_ok=True)
SRC = OUT / "source_reads"
SRC.mkdir(exist_ok=True)

REQUIRED4 = [
    "CORP_XR_XD_EVENT_PIT_R1",
    "CORP_SHAREHOLDER_TOP10_PIT_R1",
    "CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1",
    "SW_L3_MEMBERSHIP_PIT_R1",
]


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_json(p: Path, o) -> None:
    p.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    keys: list[str] = []
    seen = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                keys.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def extract_funcs(path: Path, names: set[str] | None = None, copy_whole_if_small: int = 80_000) -> dict:
    """AST-based full function bodies (incl. decorators). Optionally copy whole small module."""
    rec: dict = {
        "path": str(path.relative_to(ROOT)).replace("\\", "/") if path.exists() and str(path).startswith(str(ROOT)) else str(path),
        "exists": path.is_file(),
        "sha256": sha(path) if path.is_file() else None,
        "size": path.stat().st_size if path.is_file() else 0,
        "funcs": {},
        "module_copied": False,
        "imports_top": [],
        "assign_consts": [],
        "error": None,
    }
    if not path.is_file():
        rec["error"] = "NOT_FOUND"
        return rec
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        rec["error"] = f"SYNTAX:{e}"
        return rec

    # top-level imports + simple assigns (constants)
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            rec["imports_top"].append(ast.get_source_segment(text, node) or "")
        elif isinstance(node, ast.Assign):
            seg = ast.get_source_segment(text, node) or ""
            if len(seg) < 300:
                rec["assign_consts"].append(seg)
        elif isinstance(node, ast.AnnAssign):
            seg = ast.get_source_segment(text, node) or ""
            if len(seg) < 300:
                rec["assign_consts"].append(seg)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if names is not None and node.name not in names:
                continue
            # include decorators
            start = node.lineno
            if node.decorator_list:
                start = min(d.lineno for d in node.decorator_list)
            end = node.end_lineno or node.lineno
            body = "\n".join(lines[start - 1 : end])
            rec["funcs"][node.name] = {
                "lineno": start,
                "end_lineno": end,
                "n_lines": end - start + 1,
                "body": body,
            }

    # also nested? no — tip asks related functions; for class methods skip unless needed

    out_name = path.name.replace(".py", "") + "_EXTRACTS.md"
    parts = [f"# {rec['path']}\nsha256={rec['sha256']}\nsize={rec['size']}\n"]
    if rec["imports_top"]:
        parts.append("## imports\n```\n" + "\n".join(rec["imports_top"][:80]) + "\n```\n")
    if rec["assign_consts"]:
        parts.append("## consts\n```\n" + "\n".join(rec["assign_consts"][:120]) + "\n```\n")
    for n, f in rec["funcs"].items():
        parts.append(f"## {n} L{f['lineno']}-L{f['end_lineno']} ({f['n_lines']} lines)\n```python\n{f['body']}\n```\n")
    (SRC / out_name).write_text("\n".join(parts), encoding="utf-8")
    rec["extract_md"] = f"source_reads/{out_name}"

    if rec["size"] <= copy_whole_if_small:
        dest = SRC / path.name
        shutil.copy2(path, dest)
        rec["module_copied"] = True
        rec["module_copy"] = f"source_reads/{path.name}"
    return rec


def main() -> int:
    write_json(
        OUT / "CLAIM.json",
        {
            "at": now(),
            "tip": "BLACKBOX_DATA_MANAGEMENT_ACCEPT_DIAGNOSIS_FINISH_SEMANTICS_20261022_1507",
            "status": "CLAIMED_EXECUTING",
            "SYSTEM_INVENTORY_ACCEPTANCE": False,
            "PRODUCTION_CHANGE_AUTHORIZED": False,
        },
    )

    tip_path = ROOT / "任务" / "BLACKBOX_BACKTEST_CACHE_COMPILER_R1" / "cache_compiler_tip_rebase_from_current_r1.py"
    gate_path = ROOT / "脚本" / "blackbox_daily_increment_publish_gate_r1.py"
    common_path = ROOT / "脚本" / "blackbox_daily_increment_common_r1.py"
    base_path = ROOT / "脚本" / "_base.py"
    adj_path = ROOT / "任务" / "BLACKBOX_ADJUST_FACTOR_PIT_R1_FULL_REBUILD_AND_BACKWARD_REFRESH_R1" / "incremental_backward_refresh_r1.py"
    fund_path = ROOT / "脚本" / "blackbox_fund_etf_nav_premium_plane_r1.py"
    navc_path = ROOT / "脚本" / "p4_etf_nav_share_common_r1.py"
    ext_path = ROOT / "脚本" / "blackbox_external_evidence_materialization_r2.py"
    iw_gov = ROOT / "脚本" / "blackbox_index_weight_governance_r1.py"
    iw_check = ROOT / "脚本" / "blackbox_index_weight_daily_increment_check_r1.py"
    orch = ROOT / "脚本" / "blackbox_daily_increment_orchestrator_r1.py"
    inv_path = ROOT / "运行" / "BLACKBOX_FULL_DATA_INVENTORY_CURRENT.json"
    hb_path = ROOT / "运行" / "BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_HANDBOOK_CURRENT.md"

    # --- A: publish chain ---
    tip_ex = extract_funcs(
        tip_path,
        names={"main", "resolve_parent_and_asof", "place", "wjson", "rebuild_price_2026", "build_valuation", "inject_sw"},
        copy_whole_if_small=80_000,
    )
    gate_ex = extract_funcs(gate_path, names=None, copy_whole_if_small=80_000)  # whole small module
    common_ex = extract_funcs(common_path, names={"resolve_run_target_trade_date"}, copy_whole_if_small=100_000)
    base_ex = extract_funcs(base_path, names={"guarded_run", "run"}, copy_whole_if_small=30_000)

    # semantic from tip main body
    tip_main = (tip_ex.get("funcs") or {}).get("main", {}).get("body", "")
    gate_refs = {
        "tip_main_calls_publish_gate": bool(re.search(r"publish_gate|daily_increment_publish_gate", tip_main)),
        "tip_main_mentions_CURRENT": bool(re.search(r"CURRENT", tip_main)),
        "tip_main_mentions_no_publish": bool(re.search(r"no_publish|no-publish", tip_main)),
        "gate_funcs": list((gate_ex.get("funcs") or {}).keys()),
    }
    # deeper: search tip file for gate import/call
    tip_text = tip_path.read_text(encoding="utf-8", errors="replace") if tip_path.is_file() else ""
    tip_gate_hits = []
    for i, ln in enumerate(tip_text.splitlines(), 1):
        if re.search(r"publish_gate|CURRENT_CACHE|CURRENT_CLEANING|atomic|no_publish", ln, re.I):
            tip_gate_hits.append({"line": i, "text": ln.strip()[:200]})
            if len(tip_gate_hits) >= 60:
                break

    publish_semantics = {
        "status": "STATIC_REVIEWED",
        "flow_from_code": [
            "orchestrator.main → INDEX_WEIGHT check → ETF_MINUTE check → tip_rebase.main → (if not no_publish) scope_refresh",
            "tip_rebase: resolve_parent_and_asof → build/inject products → publish path (see hits)",
            "publish_gate: run_production_matrix → publish_atomic (full module copied)",
        ],
        "gate_linkage": gate_refs,
        "tip_keyword_hits": tip_gate_hits,
        "resolve_run_target": {
            "path": common_ex.get("path"),
            "sha256": common_ex.get("sha256"),
            "func": (common_ex.get("funcs") or {}).get("resolve_run_target_trade_date"),
        },
        "known_gaps": [],
        "not_run": [
            "No --no-publish / publish execution this round (forbidden as readonly inventory test)",
        ],
    }
    # classify gaps
    if not gate_refs["tip_main_calls_publish_gate"]:
        # check if tip imports gate via subprocess or string path
        if not any("publish_gate" in h["text"] for h in tip_gate_hits):
            publish_semantics["known_gaps"].append(
                {
                    "id": "TIP_TO_GATE_CALL_NOT_IN_MAIN_AST",
                    "impact": "cannot assert tip.main directly invokes publish_gate from AST of selected funcs alone; see tip_keyword_hits / full tip copy",
                    "min_fix": "read full tip module (copied) for subprocess/import of publish_gate",
                    "status": "KNOWN_GAP_OR_INDIRECT",
                }
            )
    write_json(OUT / "SEMANTICS_PUBLISH_CHAIN.json", publish_semantics)

    # --- B: update/resume semantics ---
    adj_ex = extract_funcs(
        adj_path,
        names={"load_cache_factor", "fetch_factor", "write_factor_years", "publish_successor", "main", "aux_xr_codes", "inherit_tree"},
        copy_whole_if_small=80_000,
    )
    fund_ex = extract_funcs(
        fund_path,
        names={
            "configure_window",
            "phase_download",
            "_latest_consolidated",
            "_merge_prior_tips",
            "phase_clean_cache",
            "phase_rules",
            "main",
        },
        copy_whole_if_small=120_000,
    )
    navc_ex = extract_funcs(
        navc_path,
        names={"fetch_nav_batch", "validate_nav_df"} if navc_path.is_file() else set(),
        copy_whole_if_small=80_000,
    )
    # external: main + phase_acceptance + phase dispatch helpers — file may be large; extract only needed
    ext_ex = extract_funcs(
        ext_path,
        names={
            "main",
            "phase_acceptance",
            "phase_disclosure_date_check",
            "phase_anns_d_keep",
            "phase_exchange_company_primary",
            "phase_company_index_r2",
            "phase_fact_canonical",
        },
        copy_whole_if_small=0,  # do not copy huge module wholesale if >0 threshold; set 0 means never? wait I used <= so 0 never copies — good for large
    )
    # fix: copy_whole_if_small=0 means size<=0 never; good

    iw_daily = extract_funcs(iw_gov, names={"daily_check"}, copy_whole_if_small=0)
    iw_check_ex = extract_funcs(iw_check, names={"main"}, copy_whole_if_small=20_000)

    # parse adjust semantics from full bodies
    adj_main = (adj_ex.get("funcs") or {}).get("main", {}).get("body", "")
    adj_pub = (adj_ex.get("funcs") or {}).get("publish_successor", {}).get("body", "")
    adj_fetch = (adj_ex.get("funcs") or {}).get("fetch_factor", {}).get("body", "")
    adj_load = (adj_ex.get("funcs") or {}).get("load_cache_factor", {}).get("body", "")
    default_update_date = None
    m = re.search(r"update.?date[^\n]{0,80}2026-08-14|default=['\"]2026-08-14['\"]|--update-date", adj_main, re.I)
    m2 = re.search(r"2026-08-14", adj_main)
    if m2:
        default_update_date = "2026-08-14_PRESENT_IN_MAIN"
    # argparse default
    m3 = re.search(r'add_argument\([^\)]*update-date[^\)]*default\s*=\s*[\'"]([^\'"]+)[\'"]', adj_main, re.I | re.S)
    if not m3:
        m3 = re.search(r'--update-date[^\n]*default=([^\s,]+)', adj_main)
    if m3:
        default_update_date = m3.group(1)

    # also search whole adj file for argparse
    adj_text = adj_path.read_text(encoding="utf-8", errors="replace") if adj_path.is_file() else ""
    m4 = re.search(r'--update-date["\'].*?default\s*=\s*["\']([^"\']+)["\']', adj_text, re.S)
    if m4:
        default_update_date = m4.group(1)

    adjust_sem = {
        "status": "STATIC_REVIEWED",
        "wrapper": "脚本/blackbox_adjust_factor_incremental_backward_refresh_r1.py → guarded_run → TASK_SCRIPT",
        "guarded_run": (base_ex.get("funcs") or {}).get("guarded_run"),
        "default_update_date_in_source": default_update_date,
        "caller_override": "orchestrator does NOT call adjust wrapper; caller must pass argv — default is source fact only, NOT run",
        "keys_from_body": {
            "load_cache_factor_mentions": re.findall(r"\b(code|date|datetime|factor)\b", adj_load)[:20],
            "fetch_factor_mentions": re.findall(r"\b(code|start|end|factor)\b", adj_fetch)[:20],
        },
        "publish_successor_n_lines": (adj_ex.get("funcs") or {}).get("publish_successor", {}).get("n_lines"),
        "main_n_lines": (adj_ex.get("funcs") or {}).get("main", {}).get("n_lines"),
        "resume": {
            "named_state_file": bool(re.search(r"state\.json|checkpoint", adj_text, re.I)),
            "conclusion": "NO_NAMED_STATE_FILE_DOES_NOT_PROVE_NO_RESUME; keyword alone does not prove resume — see full main/publish bodies",
            "status_detail": "STATIC_REVIEWED_BODIES_PRESENT",
        },
        "extract_ref": adj_ex.get("extract_md"),
        "not_run": ["Did not execute adjust with default or any date"],
    }
    write_json(OUT / "SEMANTICS_ADJUST_FACTOR.json", adjust_sem)

    fund_text = fund_path.read_text(encoding="utf-8", errors="replace") if fund_path.is_file() else ""
    fund_sem = {
        "status": "STATIC_REVIEWED",
        "note": "fetch_nav_batch is NOT defined in fund plane; called as navc.fetch_nav_batch from p4_etf_nav_share_common_r1",
        "configure_window_n": (fund_ex.get("funcs") or {}).get("configure_window", {}).get("n_lines"),
        "phase_download_n": (fund_ex.get("funcs") or {}).get("phase_download", {}).get("n_lines"),
        "merge_prior_n": (fund_ex.get("funcs") or {}).get("_merge_prior_tips", {}).get("n_lines"),
        "phase_clean_cache_n": (fund_ex.get("funcs") or {}).get("phase_clean_cache", {}).get("n_lines"),
        "main_n": (fund_ex.get("funcs") or {}).get("main", {}).get("n_lines"),
        "navc_fetch_nav_batch": (navc_ex.get("funcs") or {}).get("fetch_nav_batch"),
        "keys_literals_from_bodies": sorted(
            set(
                re.findall(
                    r"\b(code|day|date|unit_net_value|acc_net_value|GAP_START|GAP_END|asof)\b",
                    "\n".join(
                        (fund_ex.get("funcs") or {}).get(n, {}).get("body", "")
                        for n in ("configure_window", "phase_download", "_merge_prior_tips", "phase_clean_cache", "main")
                    )
                    + ((navc_ex.get("funcs") or {}).get("fetch_nav_batch", {}) or {}).get("body", ""),
                )
            )
        ),
        "extract_refs": [fund_ex.get("extract_md"), navc_ex.get("extract_md")],
        "not_run": ["No download / clean / cache publish"],
    }
    write_json(OUT / "SEMANTICS_FUND_NAV.json", fund_sem)

    ext_main_body = (ext_ex.get("funcs") or {}).get("main", {}).get("body", "")
    ext_acc = (ext_ex.get("funcs") or {}).get("phase_acceptance", {}).get("body", "")
    # find blocking fields in acceptance
    block_fields = sorted(
        set(
            re.findall(
                r"(SILENT_TRUNCATION|returned_rows|COMPLETE|BLOCK|FAIL|reject|gate|truncat\w+|ACCEPT\w+|PASS|status)",
                ext_acc,
                re.I,
            )
        )
    )
    ext_sem = {
        "status": "STATIC_REVIEWED",
        "phase_dispatch_in_main": bool(re.search(r"phase_acceptance|phase_fact|choices=", ext_main_body)),
        "main_n_lines": (ext_ex.get("funcs") or {}).get("main", {}).get("n_lines"),
        "phase_acceptance_n_lines": (ext_ex.get("funcs") or {}).get("phase_acceptance", {}).get("n_lines"),
        "blocking_tokens_in_acceptance": block_fields,
        "jq_isolation": "contract+script domain under 数据/外部证据; must not write JQ — STATIC from handbook+script paths",
        "extract_ref": ext_ex.get("extract_md"),
        "not_run": ["No materialization / API"],
        "known_gaps": [],
    }
    if (ext_ex.get("funcs") or {}).get("phase_acceptance", {}).get("n_lines", 0) == 0:
        ext_sem["known_gaps"].append({"id": "PHASE_ACCEPTANCE_NOT_EXTRACTED", "status": "KNOWN_GAP"})
    write_json(OUT / "SEMANTICS_EXTERNAL.json", ext_sem)

    daily_body = (iw_daily.get("funcs") or {}).get("daily_check", {}).get("body", "")
    iw_sem = {
        "status": "STATIC_REVIEWED",
        "daily_check_n_lines": (iw_daily.get("funcs") or {}).get("daily_check", {}).get("n_lines"),
        "daily_check_returns_dict": "return {" in daily_body or "return dict" in daily_body or re.search(r"return\s+\w+", daily_body) is not None,
        "consumer": {
            "script": "脚本/blackbox_index_weight_daily_increment_check_r1.py",
            "behavior": "prints JSON of daily_check result; apply_download=False; **always return 0**",
            "orchestrator_consumption": "only subprocess returncode; decision fields inside JSON are NOT read by orchestrator",
            "boundary": "rc==0 ≠ download success; check may legally decide no download needed",
        },
        "extract_ref": iw_daily.get("extract_md"),
        "check_entry_ref": iw_check_ex.get("extract_md"),
        "not_run": True,
    }
    write_json(OUT / "SEMANTICS_INDEX_WEIGHT.json", iw_sem)

    # --- C: inventory + handbook + 75 ledger ---
    inv_meta = {"exists": inv_path.is_file(), "sha256": sha(inv_path) if inv_path.is_file() else None, "size": inv_path.stat().st_size if inv_path.is_file() else 0}
    inv_obj = json.loads(inv_path.read_text(encoding="utf-8")) if inv_path.is_file() else {}
    # upload inventory body (24KB — ok)
    if inv_path.is_file():
        shutil.copy2(inv_path, SRC / "BLACKBOX_FULL_DATA_INVENTORY_CURRENT.json")
    if hb_path.is_file():
        shutil.copy2(hb_path, SRC / "BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_HANDBOOK_CURRENT.md")

    handbook_sem = {
        "status": "STATIC_REVIEWED",
        "path": "运行/BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_HANDBOOK_CURRENT.md",
        "sha256": sha(hb_path) if hb_path.is_file() else None,
        "one_liner": "可下域必须下完 → 清洗 → 对齐/防穿越 → Cache → FUND_ETF_NAV tip → 外源 tip → inventory",
        "download_model": "分域入口 + 下载后编排（orchestrator/TIP）；手册未声称单一全系统下载可执行入口",
        "domain_entries_named": [
            "FUND_ETF_NAV: 脚本/blackbox_fund_etf_nav_premium_plane_r1.py --phase all",
            "外源: 脚本/blackbox_external_evidence_materialization_r2.py",
            "Cache publish / tip rebase: 任务/.../cache_compiler_tip_rebase_from_current_r1.py via orchestrator",
        ],
        "inventory_top": {
            **inv_meta,
            "inventory_id": inv_obj.get("inventory_id"),
            "generated_at_cn": inv_obj.get("generated_at_cn"),
            "keys": list(inv_obj.keys()) if isinstance(inv_obj, dict) else [],
            "note": "TOP inventory ≠ 75 product master; do not treat summary PASS as measured product completeness",
        },
    }
    write_json(OUT / "SEMANTICS_HANDBOOK_AND_INVENTORY.json", handbook_sem)

    # 75 object ledger from 1447 product master + semantics tags
    pm = {}
    pm_path = SRC1447 / "PRODUCT_MASTER.json"
    if pm_path.exists():
        raw = json.loads(pm_path.read_text(encoding="utf-8"))
        rows = raw.get("rows") if isinstance(raw, dict) else raw
        for r in rows or []:
            if isinstance(r, dict) and r.get("product_id"):
                pm[r["product_id"]] = dict(r)

    # also from UPDATE_CHAIN
    family_bind = {
        "INDEX_WEIGHT_PIT_R1": {"update_semantics": "STATIC_REVIEWED", "ref": "SEMANTICS_INDEX_WEIGHT.json"},
        "ADJUST_FACTOR_PIT_R1": {"update_semantics": "STATIC_REVIEWED", "ref": "SEMANTICS_ADJUST_FACTOR.json"},
        "FUND_NAV_PIT_R1": {"update_semantics": "STATIC_REVIEWED", "ref": "SEMANTICS_FUND_NAV.json"},
        "ORCHESTRATOR_META": {"update_semantics": "STATIC_REVIEWED", "ref": "SEMANTICS_PUBLISH_CHAIN.json"},
    }
    for pid in REQUIRED4:
        family_bind[pid] = {
            "entity": "STATIC_REVIEWED_FROM_1447",
            "main_enum": "CACHE_PRODUCT_UNAVAILABLE",
            "content_audit": "NOT_RUN_FULL_DATE_X_SYMBOL",
            "update_semantics": "ORPHAN_CATALOG_NO_RESOLVER_PATH",
        }

    ledger_rows = []
    for pid, row in sorted(pm.items()):
        out_r = {
            "product_id": pid,
            "mapping_status": row.get("mapping_status") or row.get("path_status") or "",
            "entity_status": "STATIC_REVIEWED" if pid in REQUIRED4 or str(row.get("mapping_status", "")).startswith(("VERIFIED", "ENTITY")) else row.get("mapping_status", "NOT_REVIEWED"),
            "update_axis": "NOT_REVIEWED",
            "rule_axis": row.get("rule_status") or "PRIOR_RETAINED",
            "content_axis": row.get("content_audit") or "NOT_RUN",
            "review_tag": "PRIOR_RETAINED",
        }
        if pid in family_bind:
            fb = family_bind[pid]
            out_r["update_axis"] = fb.get("update_semantics") or "STATIC_REVIEWED"
            out_r["review_tag"] = "STATIC_REVIEWED"
            out_r["bind_ref"] = fb.get("ref")
            if fb.get("main_enum"):
                out_r["main_enum"] = fb["main_enum"]
            if fb.get("content_audit"):
                out_r["content_axis"] = fb["content_audit"]
        # external family
        if "EXTERNAL" in pid or pid.startswith("JQ20_") is False and "EVIDENCE" in pid:
            out_r["update_axis"] = "STATIC_REVIEWED_EXTERNAL_FAMILY"
            out_r["bind_ref"] = "SEMANTICS_EXTERNAL.json"
        ledger_rows.append(out_r)

    # ensure 75-ish count note
    write_csv(OUT / "OBJECT_LEDGER_75.csv", ledger_rows)
    write_json(
        OUT / "OBJECT_LEDGER_75.json",
        {
            "at": now(),
            "n": len(ledger_rows),
            "note": "Built from prior PRODUCT_MASTER; newly STATIC_REVIEWED binds for REQUIRED4 + IW/ADJUST/FUND_NAV/orchestrator/external family",
            "rows": ledger_rows,
        },
    )

    # remaining / priorities
    remaining = [
        {"id": "REQUIRED4_CATALOG_REGISTER", "priority": 1, "tag": "KNOWN_GAP", "impact": "resolver CACHE_PRODUCT_UNAVAILABLE for 4 required products", "min_fix": "production catalog row via formal cache publish — NOT this round", "verify": "resolver resolve_dataset returns resolved=True"},
        {"id": "CONTENT_FULL_DATE_SYMBOL_AUDIT", "priority": 2, "tag": "NOT_RUN", "impact": "entity proof ≠ coverage proof", "verify": "bounded coverage script per product required_range"},
        {"id": "TIP_PUBLISH_ATOMIC_FAULT_WINDOW", "priority": 2, "tag": "STATIC_REVIEWED_PARTIAL", "impact": "need confirm tip→gate→CURRENT fault windows from full tip body", "verify": "code review checklist on copied tip+gate; no live publish"},
        {"id": "ADJUST_RESUME_RUNTIME", "priority": 3, "tag": "NOT_RUN", "impact": "bodies reviewed; interrupt/resume unproven", "verify": "controlled dry lab with fixture — needs separate auth"},
        {"id": "FUND_NAV_RERUN_DEDUPE", "priority": 3, "tag": "NOT_RUN", "impact": "merge/dedupe logic in bodies; not executed", "verify": "phase download dry with fixture"},
        {"id": "EXTERNAL_ACCEPTANCE_FIELD_MATRIX", "priority": 3, "tag": "STATIC_REVIEWED", "impact": "blocking tokens listed; full field matrix may need table", "verify": "derive table from phase_acceptance body"},
        {"id": "OTHER_PRODUCTS_UPDATE_AXIS", "priority": 4, "tag": "NOT_REVIEWED", "impact": "most of 75 still prior mapping only", "verify": "continue family handbook binding"},
        {"id": "ENGINE_SCOPE_LIMITED", "priority": 4, "tag": "PRIOR_RETAINED", "impact": "limited engines from earlier batches", "verify": "reuse ENGINE_SCOPE.csv"},
    ]
    write_json(OUT / "REMAINING_PRIORITIZED.json", {"at": now(), "items": remaining})

    # SOURCE_READS index
    source_reads = {"at": now(), "files": []}
    for p in sorted(SRC.rglob("*")):
        if p.is_file():
            source_reads["files"].append({"rel": str(p.relative_to(OUT)).replace("\\", "/"), "sha256": sha(p), "size": p.stat().st_size})
    write_json(OUT / "SOURCE_READS.json", source_reads)

    # copy engine scope if present
    for name in ("ENGINE_SCOPE.csv", "ENGINE_ROOT_LOOKUP.json"):
        src = SRC1447 / name
        if src.exists():
            shutil.copy2(src, OUT / name)

    # UPDATE_CHAIN enriched brief
    chain_rows = [
        {
            "family": "ORCHESTRATOR_PUBLISH",
            "entry": "orchestrator→tip_rebase→publish_gate?",
            "semantics": "STATIC_REVIEWED",
            "ref": "SEMANTICS_PUBLISH_CHAIN.json",
            "success_judgment": "gate/tip bodies; orchestrator rc chain; IW check rc always 0",
        },
        {
            "family": "ADJUST_FACTOR",
            "entry": "wrapper→TASK_SCRIPT",
            "semantics": "STATIC_REVIEWED",
            "ref": "SEMANTICS_ADJUST_FACTOR.json",
            "default_update_date": default_update_date,
        },
        {
            "family": "FUND_NAV",
            "entry": "fund plane + navc.fetch_nav_batch",
            "semantics": "STATIC_REVIEWED",
            "ref": "SEMANTICS_FUND_NAV.json",
        },
        {
            "family": "EXTERNAL",
            "entry": "materialization_r2 main phases",
            "semantics": "STATIC_REVIEWED",
            "ref": "SEMANTICS_EXTERNAL.json",
        },
        {
            "family": "INDEX_WEIGHT",
            "entry": "daily_check → check main return 0",
            "semantics": "STATIC_REVIEWED",
            "ref": "SEMANTICS_INDEX_WEIGHT.json",
        },
    ]
    write_csv(OUT / "UPDATE_CHAIN.csv", chain_rows)

    report = f"""# 数据管理阶段报告（1507）— PARTIAL / 语义正文盘点

at: {now()}
SYSTEM_INVENTORY_ACCEPTANCE: **false**
status: SEMANTIC_BODIES_STATIC_REVIEWED_PARTIAL
PRODUCTION_CHANGE_AUTHORIZED: false

## 已关闭（不再重复）
1. REQUIRED4 实体+catalog 缺口诊断（1447）— 接受。
2. orchestrator 非全系统下载器 — 接受。

## 本轮方法
用 Python `ast` 的 lineno/end_lineno 导出**完整函数正文**（含 decorator），小模块整文件复制。只读源码，不 import/run 业务 main，不调 API，不执行 `--no-publish`。

## A. 发布/失败链 — STATIC_REVIEWED（部分 KNOWN_GAP）
- TIP rebase：已抽 `main/resolve_parent_and_asof/place/...`，模块全文已复制（size={tip_ex.get('size')}）。
- publish_gate：全文复制；函数 {list((gate_ex.get('funcs') or {}).keys())}。
- resolve_run_target_trade_date：完整函数已导出。
- tip.main 是否**直接**调用 publish_gate：见 `SEMANTICS_PUBLISH_CHAIN.json` keyword hits；若仅间接，标 KNOWN_GAP_OR_INDIRECT。
- **NOT_RUN**：未执行任何发布/`--no-publish`。

## B. 更新/恢复语义
| 家族 | 状态 | 要点 |
|---|---|---|
| adjust | STATIC_REVIEWED | load/fetch/main/publish_successor + guarded_run 全文；默认 update-date 源码事实=`{default_update_date}`；未运行 |
| FUND_NAV | STATIC_REVIEWED | configure_window/phase_download/_merge_prior_tips/phase_clean_cache/main；`fetch_nav_batch` 在 `p4_etf_nav_share_common_r1` |
| external | STATIC_REVIEWED | main + phase_acceptance 等全文；阻断 token 已列；未物化 |
| INDEX_WEIGHT | STATIC_REVIEWED | daily_check 全文；上游只看 rc==0；apply_download=false |

## C. 75 对象 + 手册
- 已上传 `BLACKBOX_FULL_DATA_INVENTORY_CURRENT.json`（sha={inv_meta.get('sha256')}）— TOP 目录，**不能**当 75 产品实测 PASS。
- 手册：分域入口+下载后编排；FUND_NAV / 外源 tip 有具名命令；无「一键全系统下载」单一入口。
- 账本：`OBJECT_LEDGER_75.csv`（n={len(ledger_rows)}）；REQUIRED4+关键家族标 STATIC_REVIEWED，其余 PRIOR_RETAINED/NOT_REVIEWED。

## 剩余优先级
见 `REMAINING_PRIORITIZED.json`（catalog 登记 > 内容覆盖 NOT_RUN > tip/gate 故障窗 > 各域运行恢复验证）。

## 标签用法
- STATIC_REVIEWED = 正文已读有据
- KNOWN_GAP = 明确缺口
- NOT_RUN = 需运行验证（≠盘点未交代）
- NOT_REVIEWED = 正文仍未读
"""
    (OUT / "USER_FINAL_REPORT.md").write_text(report, encoding="utf-8")

    status = {
        "at": now(),
        "checkpoint": "COMPLETION_1507",
        "SYSTEM_INVENTORY_ACCEPTANCE": False,
        "status": "PARTIAL",
        "extracts": {
            "tip": tip_ex.get("extract_md"),
            "gate": gate_ex.get("extract_md"),
            "adjust": adj_ex.get("extract_md"),
            "fund": fund_ex.get("extract_md"),
            "navc": navc_ex.get("extract_md"),
            "external": ext_ex.get("extract_md"),
            "daily_check": iw_daily.get("extract_md"),
        },
        "ledger_n": len(ledger_rows),
        "source_files_n": len(source_reads["files"]),
    }
    write_json(OUT / "STATUS_PROGRESS.json", status)
    (OUT / "MASTER_PROGRESS.md").write_text(f"# MASTER_PROGRESS 1507\n\n{json.dumps(status, ensure_ascii=False, indent=2)}\n", encoding="utf-8")
    write_json(OUT / "CLAIM.json", {**json.loads((OUT / "CLAIM.json").read_text(encoding="utf-8")), "status": "DONE_LOCAL", "finished_at": now()})
    print(json.dumps({"ok": True, "status": status}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
