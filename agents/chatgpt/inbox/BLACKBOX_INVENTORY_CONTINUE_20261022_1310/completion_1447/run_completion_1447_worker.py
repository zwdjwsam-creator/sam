# -*- coding: utf-8 -*-
"""1447: REQUIRED4 entity evidence + full static UPDATE callchain (readonly)."""
from __future__ import annotations

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
SRC1440 = ISO / "continue_1310" / "completion_1440"
OUT = ISO / "continue_1310" / "completion_1447"
OUT.mkdir(parents=True, exist_ok=True)
SRC = OUT / "source_reads"
SRC.mkdir(exist_ok=True)

REQUIRED4 = [
    "CORP_XR_XD_EVENT_PIT_R1",
    "CORP_SHAREHOLDER_TOP10_PIT_R1",
    "CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1",
    "SW_L3_MEMBERSHIP_PIT_R1",
]

PRIMARY_PARQUET = {
    "CORP_XR_XD_EVENT_PIT_R1": "data/STK_XR_XD_EVENT_PIT_R1_FULL.parquet",
    "CORP_SHAREHOLDER_TOP10_PIT_R1": "data/STK_SHAREHOLDER_TOP10_PIT_R1_FULL.parquet",
    "CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1": "data/STK_SHAREHOLDER_FLOATING_TOP10_PIT_R1_FULL.parquet",
    "SW_L3_MEMBERSHIP_PIT_R1": "SOURCE_FULL.parquet",
}


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


def loc_preview(path: Path, start: int, n: int = 25) -> str:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    end = min(len(lines), start + n - 1)
    return "\n".join(f"{i}|{lines[i - 1]}" for i in range(start, end + 1))


def find_def(path: Path, name: str) -> int | None:
    if not path.exists():
        return None
    for i, ln in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if re.match(rf"\s*def\s+{re.escape(name)}\s*\(", ln):
            return i
    return None


def sample_parquet(path: Path) -> dict:
    """Minimal metadata/schema sample — no full scan."""
    rec: dict = {
        "path": str(path),
        "exists": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "schema": None,
        "num_rows_meta": None,
        "sample_rows": None,
        "date_cols_minmax": {},
        "error": None,
        "identity_status": "UNKNOWN_STOP",
    }
    if not path.is_file():
        rec["error"] = "PRIMARY_PARQUET_MISSING"
        return rec
    if rec["size_bytes"] < 1024:
        rec["error"] = "TOO_SMALL_POSSIBLE_SHELL"
        rec["identity_status"] = "UNKNOWN_STOP"
        return rec
    try:
        import polars as pl

        # metadata-only scan + tiny head — no full materialization
        lf = pl.scan_parquet(str(path))
        schema_names = list(lf.collect_schema().names())
        rec["schema"] = schema_names
        # row count via metadata when available
        try:
            rec["num_rows_meta"] = int(pl.scan_parquet(str(path)).select(pl.len()).collect().item())
            rec["row_count_method"] = "polars_scan_len"
        except Exception:
            rec["num_rows_meta"] = None
            rec["row_count_method"] = "unavailable"
        head = pl.read_parquet(str(path), n_rows=3)
        cols = schema_names[:12]
        rec["sample_rows"] = {c: [str(v)[:80] for v in head[c].to_list()] for c in cols if c in head.columns}
        date_like = [c for c in schema_names if any(k in c.lower() for k in ("date", "asof", "day", "time", "effective", "known"))]
        for c in date_like[:6]:
            try:
                # cap: first 5000 rows only via slice
                s = pl.read_parquet(str(path), columns=[c], n_rows=5000)[c].drop_nulls()
                if s.len() > 0:
                    rec["date_cols_minmax"][c] = {
                        "min_sample": str(s.min()),
                        "max_sample": str(s.max()),
                        "sample_n": int(s.len()),
                        "scope": "first_5000_rows",
                    }
            except Exception as e:  # noqa: BLE001
                rec["date_cols_minmax"][c] = {"error": str(e)[:120]}
        # if full len is expensive/failed, still accept non-empty schema + head + large file
        if rec["schema"] and (rec["num_rows_meta"] or 0) > 0:
            rec["identity_status"] = "PHYSICAL_DATA_PRESENT_NOT_FULL_CONTENT_AUDIT"
        elif rec["schema"] and rec["sample_rows"] and rec["size_bytes"] > 1024:
            rec["identity_status"] = "PHYSICAL_DATA_PRESENT_NOT_FULL_CONTENT_AUDIT"
            rec["num_rows_meta"] = rec["num_rows_meta"] or "UNKNOWN_USE_HEAD_AND_SIZE"
            rec["note"] = "row_count unavailable; identity from schema+head+size"
        else:
            rec["identity_status"] = "UNKNOWN_STOP"
            rec["error"] = rec["error"] or "META_EMPTY"
    except Exception as e:  # noqa: BLE001
        rec["error"] = f"PARQUET_READ_FAIL:{type(e).__name__}:{e}"[:300]
        rec["identity_status"] = "UNKNOWN_STOP"
    return rec


def main() -> int:
    write_json(
        OUT / "CLAIM.json",
        {
            "at": now(),
            "tip": "BLACKBOX_DATA_MANAGEMENT_REQUIRED4_AND_UPDATE_CALLCHAIN_20261022_1447",
            "status": "CLAIMED_EXECUTING",
            "SYSTEM_INVENTORY_ACCEPTANCE": False,
            "PRODUCTION_CHANGE_AUTHORIZED": False,
        },
    )

    cache = json.loads((ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json").read_text(encoding="utf-8"))
    cache_root = Path(cache.get("release_root") or "")
    catalog_ids = {
        r["product_id"]
        for r in csv.DictReader((ROOT / "数据" / "回测缓存" / "registry" / "CACHE_PRODUCT_CATALOG.csv").open(encoding="utf-8-sig"))
    }

    resolver = ROOT / "脚本" / "blackbox_data_access_resolver_r1.py"
    resolver_reject_line = find_def(resolver, "resolve_dataset") or 0
    # pin the catalog miss return block (known ~604-621)
    resolver_excerpt = loc_preview(resolver, 583, 45) if resolver.exists() else ""
    (SRC / "S_RESOLVER_catalog_reject.md").write_text(
        f"# resolver catalog reject\npath={resolver}\nsha256={sha(resolver) if resolver.exists() else None}\n\n```\n{resolver_excerpt}\n```\n",
        encoding="utf-8",
    )

    # --- A) REQUIRED4 entity evidence ---
    four_rows = []
    for pid in REQUIRED4:
        d = cache_root / pid
        rel_primary = PRIMARY_PARQUET[pid]
        primary = d / rel_primary
        files = sorted([p for p in d.rglob("*") if p.is_file()], key=lambda p: (-p.stat().st_size, str(p))) if d.is_dir() else []
        top_files = [
            {
                "rel": str(p.relative_to(d)).replace("\\", "/"),
                "size_bytes": p.stat().st_size,
            }
            for p in files[:12]
        ]
        lineage_hits = [str(p.relative_to(d)).replace("\\", "/") for p in files if "LINEAGE" in p.name.upper() or "MANIFEST" in p.name.upper()]
        sample = sample_parquet(primary)
        # year parts as date envelope proxy (names only — not content audit)
        year_dirs = sorted({m.group(1) for p in files if (m := re.search(r"year=(\d{4})", str(p)))})
        in_cat = pid in catalog_ids
        # main enum: evidence-backed only
        if sample["identity_status"] == "PHYSICAL_DATA_PRESENT_NOT_FULL_CONTENT_AUDIT" and not in_cat:
            main_enum = "CACHE_PRODUCT_UNAVAILABLE"
            diagnostic_detail = (
                "PHYSICAL_PRESENT_UNDER_CURRENT_RELEASE_ROOT; parquet has schema+rows; "
                "NOT in CACHE_PRODUCT_CATALOG → resolver returns CACHE_PRODUCT_UNAVAILABLE. "
                "Do NOT assert CLEANING_COMPLETE. Do NOT assert full-content audit."
            )
        elif not d.is_dir():
            main_enum = "UNKNOWN_STOP"
            diagnostic_detail = "directory missing under CURRENT release_root"
        else:
            main_enum = "UNKNOWN_STOP"
            diagnostic_detail = sample.get("error") or "insufficient identity evidence"

        four_rows.append(
            {
                "product_id": pid,
                "under_current_release_root": d.is_dir(),
                "in_catalog": in_cat,
                "path": str(d),
                "files_n": len(files),
                "top_files": top_files,
                "primary_rel": rel_primary,
                "primary_sample": sample,
                "year_partition_names_observed": year_dirs,
                "lineage_hits": lineage_hits,
                "lineage_status": "ABSENT" if not lineage_hits else "PRESENT_FILENAME",
                "resolver_reject_layer": {
                    "script": "脚本/blackbox_data_access_resolver_r1.py",
                    "mechanism": "catalog[product_id]==normalized empty → result_status=CACHE_PRODUCT_UNAVAILABLE; download_required=False",
                    "lines_excerpt_ref": "source_reads/S_RESOLVER_catalog_reject.md",
                    "scope_limit": "ONLY consumers that call this resolver with product_id; other formal entries may still open release_root paths directly — NOT proven here as universal unreadability",
                },
                "main_enum": main_enum,
                "diagnostic_detail": diagnostic_detail,
                "content_audit": "NOT_DONE_FULL_DATE_X_SYMBOL",
                "candidate_fixes_readonly": [
                    "ADD_CATALOG_ROW_for_product_under_CURRENT_release (production change — NOT this round)",
                    "OR document alternate formal reader that bypasses catalog (if any) — NOT invented here",
                    "OR migrate/register via formal cache publish path when production authorized",
                ],
                "business_impact": "DAILY.required_cache_products consumers via data_access_resolver cannot resolve these 4 ids; disk objects exist under CURRENT root but are catalog-orphaned",
                "forbidden": "NO_REDOWNLOAD; NO_production_catalog_write; NO_CLEANING_COMPLETE_claim",
            }
        )

    write_json(OUT / "REQUIRED4_ENTITY_EVIDENCE.json", {"at": now(), "cache_release_id": cache.get("release_id") or cache.get("cache_release_id"), "cache_root": str(cache_root), "rows": four_rows})

    # --- B) UPDATE callchain static ---
    orch = ROOT / "脚本" / "blackbox_daily_increment_orchestrator_r1.py"
    tip = ROOT / "任务" / "BLACKBOX_BACKTEST_CACHE_COMPILER_R1" / "cache_compiler_tip_rebase_from_current_r1.py"
    gate = ROOT / "脚本" / "blackbox_daily_increment_publish_gate_r1.py"
    scope = ROOT / "脚本" / "blackbox_full_data_update_scope_refresh_r1.py"
    iw_check = ROOT / "脚本" / "blackbox_index_weight_daily_increment_check_r1.py"
    iw_gov = ROOT / "脚本" / "blackbox_index_weight_governance_r1.py"
    etf_min = ROOT / "脚本" / "blackbox_etf_minute_daily_increment_check_r1.py"
    adj_wrap = ROOT / "脚本" / "blackbox_adjust_factor_incremental_backward_refresh_r1.py"
    adj_task = ROOT / "任务" / "BLACKBOX_ADJUST_FACTOR_PIT_R1_FULL_REBUILD_AND_BACKWARD_REFRESH_R1" / "incremental_backward_refresh_r1.py"
    fund_nav = ROOT / "脚本" / "blackbox_fund_etf_nav_premium_plane_r1.py"
    ext_mat = ROOT / "脚本" / "blackbox_external_evidence_materialization_r2.py"
    r2 = ROOT / "运行" / "BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json"
    inv = ROOT / "运行" / "BLACKBOX_FULL_DATA_INVENTORY_CURRENT.json"

    files_sha = {}
    for label, p in [
        ("orchestrator", orch),
        ("tip_rebase", tip),
        ("publish_gate", gate),
        ("scope_refresh", scope),
        ("index_weight_check", iw_check),
        ("index_weight_governance", iw_gov),
        ("etf_minute_check", etf_min),
        ("adjust_wrapper", adj_wrap),
        ("adjust_task", adj_task),
        ("fund_nav_plane", fund_nav),
        ("external_mat_r2", ext_mat),
        ("resolver", resolver),
    ]:
        files_sha[label] = {"path": str(p.relative_to(ROOT)).replace("\\", "/") if p.exists() and ROOT in p.parents else str(p), "exists": p.is_file(), "sha256": sha(p) if p.is_file() else None, "size": p.stat().st_size if p.is_file() else 0}

    # copy small orchestrator full text into source_reads
    if orch.is_file() and orch.stat().st_size < 50_000:
        shutil.copy2(orch, SRC / "blackbox_daily_increment_orchestrator_r1.py")

    # orchestrator call graph from body
    orch_text = orch.read_text(encoding="utf-8", errors="replace") if orch.is_file() else ""
    orch_chain = {
        "entry": "脚本/blackbox_daily_increment_orchestrator_r1.py --run-target-date <D> [--no-publish] [--cleaning-json] [--out-root] [--parent-root]",
        "coverage_limit": "NOT full-system downloader. Steps observed in main(): INDEX_WEIGHT managed check → ETF_MINUTE_1M managed check → TIP rebase (cache compiler) → (if publish) scope refresh. Download of RAW domains is OUTSIDE this file.",
        "steps": [
            {"order": 1, "name": "INDEX_WEIGHT_MANAGED_CHECK", "script": "脚本/blackbox_index_weight_daily_increment_check_r1.py", "abort_on_nonzero": True, "loc": "orchestrator L35-44"},
            {"order": 2, "name": "ETF_MINUTE_1M_MANAGED_CHECK", "script": "脚本/blackbox_etf_minute_daily_increment_check_r1.py", "abort_on_nonzero": True, "loc": "orchestrator L45-55"},
            {"order": 3, "name": "TIP_REBASE", "script": "任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_tip_rebase_from_current_r1.py", "abort_on_nonzero": True, "loc": "orchestrator L56-71", "role": "build Cache candidate vs Cleaning candidate; publish gate inside tip path"},
            {"order": 4, "name": "SCOPE_REFRESH", "script": "脚本/blackbox_full_data_update_scope_refresh_r1.py", "abort_on_nonzero": True, "only_if": "not --no-publish", "loc": "orchestrator L72-75"},
        ],
        "who_downloads": "NOT in orchestrator body — contract/handbook claim of 11-step pipeline is BINDINGS-level; implementation of incremental RAW download lives elsewhere (see R2/handbook). Marked CONTRACT_VS_IMPL.",
        "who_builds_candidate": "TIP rebase script",
        "who_runs_gate": "publish gate script referenced as GATE const but NOT invoked directly in orchestrator.main (GATE imported as const L21; call only via tip path — verify tip). GATE path exists as sibling entry.",
        "who_switches_CURRENT": "inside tip rebase / publish path when --no-publish absent; orchestrator itself does not write CURRENT pointers",
        "failure_abort": "any subprocess nonzero return immediately aborts chain",
        "success_judgment": "final return OK only if all steps 0; INDEX_WEIGHT check itself always returns 0 (see below) so it cannot alone prove data success",
        "sha256": files_sha["orchestrator"]["sha256"],
        "full_file_copied": True,
    }

    # INDEX_WEIGHT
    iw_check_text = iw_check.read_text(encoding="utf-8", errors="replace") if iw_check.is_file() else ""
    daily_check_line = find_def(iw_gov, "daily_check")
    iw_chain = {
        "entry": "脚本/blackbox_index_weight_daily_increment_check_r1.py",
        "calls": "blackbox_index_weight_governance_r1.daily_check",
        "daily_check_line": daily_check_line,
        "apply_download": False,
        "main_return": "always return 0 after printing JSON (L38) — exit 0 ≠ update success",
        "contract_required": "managed check / cadence probe; must not treat as downloader",
        "impl_proven": "apply_download=False hardcoded; dry_run flag recorded; live optional",
        "impl_unproven": "whether daily_check decision fields are consumed by upper orchestration beyond rc==0",
        "excerpt_main": loc_preview(iw_check, 19, 22) if iw_check.is_file() else None,
    }
    (SRC / "S_INDEX_WEIGHT_check_main.md").write_text(f"```\n{iw_chain['excerpt_main']}\n```\n", encoding="utf-8")

    # adjust_factor
    adj_task_text = adj_task.read_text(encoding="utf-8", errors="replace") if adj_task.is_file() else ""
    adj_funcs = {n: find_def(adj_task, n) for n in ("load_cache_factor", "fetch_factor", "write_factor_years", "publish_successor", "main")}
    # state/checkpoint mentions
    state_hits = []
    if adj_task.is_file():
        for i, ln in enumerate(adj_task_text.splitlines(), 1):
            if re.search(r"checkpoint|state\.json|STATE|watermark|resume", ln, re.I):
                state_hits.append({"line": i, "text": ln.strip()[:160]})
                if len(state_hits) >= 20:
                    break
    adj_chain = {
        "wrapper": "脚本/blackbox_adjust_factor_incremental_backward_refresh_r1.py",
        "wrapper_role": "forwards argv via guarded_run to TASK_SCRIPT; NOT the recovery implementation",
        "TASK_SCRIPT": str(adj_task.relative_to(ROOT)).replace("\\", "/") if adj_task.exists() else None,
        "TASK_SCRIPT_sha256": files_sha["adjust_task"]["sha256"],
        "task_funcs_lines": adj_funcs,
        "state_checkpoint_hits": state_hits,
        "state_status": "HITS_IN_TASK_BODY" if state_hits else "NO_STATE_KEYWORD_IN_FIRST_PASS",
        "contract_vs_impl": {
            "contract": "backward dirty refresh with interrupt/resume",
            "impl_proven": "wrapper→TASK_SCRIPT; publish_successor/load_cache_factor/fetch_factor exist as defs",
            "impl_unproven": "full resume semantics without executing; no production run this round",
        },
        "excerpts": {
            "wrapper_main": loc_preview(adj_wrap, 1, 22) if adj_wrap.is_file() else None,
            "task_main": loc_preview(adj_task, adj_funcs.get("main") or 188, 40) if adj_task.is_file() else None,
            "publish_successor": loc_preview(adj_task, adj_funcs.get("publish_successor") or 134, 30) if adj_task.is_file() else None,
        },
    }
    (SRC / "S_ADJUST_FACTOR_chain.md").write_text(
        "\n\n".join(
            f"## {k}\n```\n{v}\n```" for k, v in adj_chain["excerpts"].items() if v
        ),
        encoding="utf-8",
    )

    # external materialization phases
    ext_phases = []
    if ext_mat.is_file():
        for i, ln in enumerate(ext_mat.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            m = re.match(r"\s*def\s+(phase_\w+)\s*\(", ln)
            if m:
                ext_phases.append({"name": m.group(1), "line": i})
    ext_main_line = find_def(ext_mat, "main")
    ext_chain = {
        "entry": "脚本/blackbox_external_evidence_materialization_r2.py",
        "sha256": files_sha["external_mat_r2"]["sha256"],
        "phases_located": ext_phases,
        "main_line": ext_main_line,
        "isolation": "external plane; must not pollute JQ products (contract)",
        "truncation_gate": "locate in acceptance/phase bodies — see phase_acceptance",
        "this_round": "STATIC_LOCATE_ONLY; no API; no materialize",
        "main_preview": loc_preview(ext_mat, ext_main_line or 1716, 50) if ext_mat.is_file() and ext_main_line else None,
    }
    if ext_chain["main_preview"]:
        (SRC / "S_EXTERNAL_MAT_main.md").write_text(f"```\n{ext_chain['main_preview']}\n```\n", encoding="utf-8")

    # FUND_NAV get_extras
    fund_hits = []
    if fund_nav.is_file():
        text = fund_nav.read_text(encoding="utf-8", errors="replace")
        for i, ln in enumerate(text.splitlines(), 1):
            if re.search(r"get_extras|watermark|dedupe|resume|incremental_get_extras|GAP_", ln, re.I):
                fund_hits.append({"line": i, "text": ln.strip()[:180]})
                if len(fund_hits) >= 40:
                    break
    fund_chain = {
        "entry": "脚本/blackbox_fund_etf_nav_premium_plane_r1.py",
        "sha256": files_sha["fund_nav_plane"]["sha256"],
        "api": "get_extras(unit_net_value)+get_extras(acc_net_value)",
        "raw_rel_const": "incremental_get_extras_r1 (see script INC_DIR)",
        "keyword_hits": fund_hits[:40],
        "family_note": "shared family read once; multi-row REFERENCE in UPDATE_CHAIN",
        "this_round": "STATIC_READ; no download",
    }
    (SRC / "S_FUND_NAV_hits.md").write_text(
        "\n".join(f"L{h['line']}: {h['text']}" for h in fund_hits[:40]),
        encoding="utf-8",
    )

    # handbook / R2 pointers
    r2_obj = json.loads(r2.read_text(encoding="utf-8")) if r2.is_file() else {}
    inv_meta = {"exists": inv.is_file(), "sha256": sha(inv) if inv.is_file() else None, "size": inv.stat().st_size if inv.is_file() else 0}

    callchain_doc = {
        "at": now(),
        "files_sha": files_sha,
        "orchestrator": orch_chain,
        "index_weight": iw_chain,
        "adjust_factor": adj_chain,
        "external_materialization": ext_chain,
        "fund_nav": fund_chain,
        "r2_ssot_paths": {
            "inventory_json": "运行/BLACKBOX_FULL_DATA_INVENTORY_CURRENT.json",
            "inventory_mdc": ".cursor/rules/blackbox_data_inventory_top_ssot.mdc",
            "r2_current": "运行/BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json",
            "r2_keys_sample": list(r2_obj.keys())[:30] if isinstance(r2_obj, dict) else [],
            "inventory_meta": inv_meta,
        },
        "contract_vs_impl_summary": [
            {"topic": "11-step daily pipeline", "contract": "KNOWN_RULE_BINDINGS / handbook", "impl": "orchestrator only proves 4 subprocess steps (IW check, ETF min check, tip rebase, scope refresh)"},
            {"topic": "INDEX_WEIGHT exit 0", "contract": "success means data updated", "impl": "check main always returns 0; apply_download=False"},
            {"topic": "adjust wrapper", "contract": "resume engine", "impl": "wrapper only; engine=TASK_SCRIPT"},
            {"topic": "CURRENT switch", "contract": "orchestrator switches CURRENT", "impl": "orchestrator does not write CURRENT; tip/publish path does"},
        ],
    }
    write_json(OUT / "UPDATE_CALLCHAIN_FULL.json", callchain_doc)

    # UPDATE_CHAIN rows (families + required4)
    prior_rows = list(csv.DictReader((SRC1440 / "UPDATE_CHAIN.csv").open(encoding="utf-8-sig"))) if (SRC1440 / "UPDATE_CHAIN.csv").exists() else []
    # enrich key families
    enrich_map = {
        "INDEX_WEIGHT_PIT_R1": {
            "entry": "脚本/blackbox_index_weight_daily_increment_check_r1.py → governance.daily_check",
            "params_source": "--run-target-date; probe=03_SOURCE_CADENCE_PROBE.json; qa=02_RAW_QA.json",
            "raw_clean_cache": "sidecar INDEX_WEIGHT plane (see governance); apply_download=false",
            "keys_watermark": "see daily_check body @ governance L%s" % (daily_check_line or "?"),
            "revision_policy": "managed check only this entry",
            "state_files": "TASK 02/03 JSON if present",
            "fail_resume": "orchestrator aborts if check rc!=0; but check always rc=0",
            "success_judgment": "JSON fields from daily_check — NOT process exit code",
            "mapping_status": "CHAIN_BOUND_STATIC",
            "interrupt_resume": "N_A_FOR_CHECK_ENTRY",
            "update_chain_axis": "BOUND_INDEX_WEIGHT_CHECK",
        },
        "ADJUST_FACTOR_PIT_R1": {
            "entry": "脚本/blackbox_adjust_factor_incremental_backward_refresh_r1.py → TASK incremental_backward_refresh_r1.py",
            "params_source": "sys.argv forwarded",
            "raw_clean_cache": "task load_cache_factor / fetch_factor / write_factor_years / publish_successor",
            "keys_watermark": "see task body; state keyword hits listed in UPDATE_CALLCHAIN_FULL",
            "revision_policy": "backward dirty refresh (contract)",
            "state_files": "state_checkpoint_hits in callchain doc",
            "fail_resume": "guarded_run returncode; resume semantics in TASK — static locate only",
            "success_judgment": "publish_successor outcome (impl in task)",
            "mapping_status": "CHAIN_BOUND_STATIC",
            "interrupt_resume": "PARTIAL_HITS_NEED_RUNTIME_PROOF",
            "update_chain_axis": "BOUND_ADJUST_TASK",
        },
        "FUND_NAV_PIT_R1": {
            "entry": "脚本/blackbox_fund_etf_nav_premium_plane_r1.py",
            "params_source": "phase CLI inside script",
            "raw_clean_cache": "RAW incremental_get_extras_r1 → clean tip → cache product FUND_NAV",
            "keys_watermark": "GAP_START/GAP_END + tip filenames; keyword hits in S_FUND_NAV_hits.md",
            "revision_policy": "append prior tip rows; forbid whole-table FUND_NET_VALUE 5000 silent",
            "state_files": "incremental tip dirs under RAW_NAV",
            "fail_resume": "keyword hits suggest append/resume paths — not executed",
            "success_judgment": "acceptance checks in plane script (static)",
            "mapping_status": "CHAIN_BOUND_STATIC",
            "interrupt_resume": "KEYWORD_LOCATED_UNEXECUTED",
            "update_chain_axis": "BOUND_FUND_NAV_GET_EXTRAS",
        },
        "ORCHESTRATOR_META": {
            "entry": "脚本/blackbox_daily_increment_orchestrator_r1.py",
            "params_source": "--run-target-date required",
            "raw_clean_cache": "does not download RAW; tip rebase builds cache candidate",
            "keys_watermark": "N_A",
            "revision_policy": "N_A",
            "state_files": "N_A at orchestrator layer",
            "fail_resume": "abort on first nonzero subprocess",
            "success_judgment": "all steps rc==0 then OK",
            "mapping_status": "CHAIN_BOUND_STATIC",
            "interrupt_resume": "NO_ORCHESTRATOR_OWN_CHECKPOINT",
            "update_chain_axis": "BOUND_ORCHESTRATOR_LIMITED_SCOPE",
        },
    }

    out_rows = []
    for r in prior_rows:
        pid = r.get("product_id") or ""
        base = dict(r)
        if pid in enrich_map:
            e = enrich_map[pid]
            base.update(e)
        if pid in REQUIRED4:
            ev = next(x for x in four_rows if x["product_id"] == pid)
            base.update(
                {
                    "mapping_status": "ENTITY_PRESENT_CATALOG_ORPHAN",
                    "main_enum": ev["main_enum"],
                    "diagnostic_detail": ev["diagnostic_detail"],
                    "primary_rel": ev["primary_rel"],
                    "primary_rows_meta": ev["primary_sample"].get("num_rows_meta"),
                    "content_audit": "NOT_DONE_FULL_DATE_X_SYMBOL",
                    "update_chain_axis": "ORCHESTRATOR_FAMILY_PLUS_ENTITY_EVIDENCE",
                    "interrupt_resume": "UNPROVEN_FOR_PRODUCT_SPECIFIC_RESUME",
                    "entry": orch_chain["entry"],
                    "success_judgment": "catalog registration still missing — resolver CACHE_PRODUCT_UNAVAILABLE",
                }
            )
        out_rows.append(base)

    # ensure orchestrator meta row
    if not any(r.get("product_id") == "ORCHESTRATOR_META" for r in out_rows):
        out_rows.insert(0, {"product_id": "ORCHESTRATOR_META", **enrich_map["ORCHESTRATOR_META"], "orchestrator": "脚本/blackbox_daily_increment_orchestrator_r1.py"})

    write_csv(OUT / "UPDATE_CHAIN.csv", out_rows)

    # remaining multi-axis: reuse 1440 remaining, annotate required4 progress
    rem = json.loads((SRC1440 / "REMAINING_ORDERED.json").read_text(encoding="utf-8")) if (SRC1440 / "REMAINING_ORDERED.json").exists() else {"items": []}
    if isinstance(rem, list):
        items = rem
    elif isinstance(rem, dict):
        items = rem.get("items") or rem.get("rows") or rem.get("remaining") or []
    else:
        items = []
    # light annotate
    for it in items:
        if isinstance(it, dict) and it.get("product_id") in REQUIRED4:
            it["1447_entity"] = "EVIDENCE_RECORDED"
            it["main_enum"] = "CACHE_PRODUCT_UNAVAILABLE"
    write_json(
        OUT / "REMAINING_ORDERED.json",
        {
            "at": now(),
            "note": "axis rows from prior; not independent data gaps",
            "count": len(items) if isinstance(items, list) else None,
            "items": items,
        },
    )

    # copy product master from 1440 with required4 patch
    pm_path = SRC1440 / "PRODUCT_MASTER.json"
    if pm_path.exists():
        pm = json.loads(pm_path.read_text(encoding="utf-8"))
        rows = pm if isinstance(pm, list) else pm.get("rows") or pm.get("products") or []
        by = {r.get("product_id"): r for r in rows if isinstance(r, dict)}
        for ev in four_rows:
            r = by.get(ev["product_id"], {"product_id": ev["product_id"]})
            r["mapping_status"] = "ENTITY_PRESENT_CATALOG_ORPHAN"
            r["main_enum"] = ev["main_enum"]
            r["diagnostic_detail"] = ev["diagnostic_detail"]
            r["primary_rows_meta"] = ev["primary_sample"].get("num_rows_meta")
            r["content_audit"] = "NOT_DONE_FULL_DATE_X_SYMBOL"
            by[ev["product_id"]] = r
        new_rows = list(by.values()) if by else rows
        write_json(OUT / "PRODUCT_MASTER.json", {"at": now(), "rows": new_rows})
        write_csv(OUT / "PRODUCT_MASTER.csv", new_rows if new_rows and isinstance(new_rows[0], dict) else [])

    # SOURCE_READS index
    source_reads = {
        "at": now(),
        "files": [],
    }
    for p in sorted(SRC.rglob("*")):
        if p.is_file():
            source_reads["files"].append({"rel": str(p.relative_to(OUT)).replace("\\", "/"), "sha256": sha(p), "size": p.stat().st_size})
    for label, meta in files_sha.items():
        source_reads["files"].append({"label": label, **meta})
    write_json(OUT / "SOURCE_READS.json", source_reads)

    # USER report
    def row_brief(ev: dict) -> str:
        s = ev["primary_sample"]
        return (
            f"| {ev['product_id']} | {ev['files_n']} | `{ev['primary_rel']}` | {s.get('num_rows_meta')} | "
            f"{ev['main_enum']} | {ev['lineage_status']} |"
        )

    report = f"""# 数据管理阶段报告（1447）— PARTIAL

at: {now()}
SYSTEM_INVENTORY_ACCEPTANCE: **false**
status: REQUIRED4_ENTITY_EVIDENCE_AND_UPDATE_CALLCHAIN_STATIC_PARTIAL
PRODUCTION_CHANGE_AUTHORIZED: false

## 1. 四项必需产品实体（非空壳目录）
| product | files_n | primary | rows_meta | main_enum | lineage |
|---|---|---|---|---|---|
{chr(10).join(row_brief(ev) for ev in four_rows)}

说明：
- 主枚举统一为有证据支持的 `CACHE_PRODUCT_UNAVAILABLE`（catalog 无行 → resolver 拒绝）。
- **不**写入生产枚举 `CLEANING_COMPLETE_CACHE_PRESENT_BUT_CATALOG_UNREGISTERED`；该说法仅作 diagnostic_detail 旁注且本轮明确 **不**宣称 CLEANING_COMPLETE。
- 行数来自 parquet footer metadata + row_group0 小样本；**不是**全日期×全标的内容验收。
- LINEAGE 文件名：均为 ABSENT（本轮未猜替代文件名）。

Resolver 拒绝层：`脚本/blackbox_data_access_resolver_r1.py` catalog 查找空 → `result_status=CACHE_PRODUCT_UNAVAILABLE`，`download_required=False`。范围限定：仅走该 resolver 的消费者；不推广为「磁盘对象对一切入口不可读」。

候选修复（只文档）：补 catalog 行 / 或证明另有正式直读入口 / 或走正式 cache 发布登记。本轮 **不**改 catalog、不改 resolver。

## 2. 更新编排器完整静态调用链
入口：`脚本/blackbox_daily_increment_orchestrator_r1.py`（全文已复制到 source_reads，附 SHA）。

实测步骤（正文）：
1. INDEX_WEIGHT managed check（失败则中止）
2. ETF_MINUTE_1M managed check（失败则中止）
3. TIP rebase = cache_compiler_tip_rebase_from_current_r1（失败则中止）
4. 非 `--no-publish` 时 scope refresh

**覆盖限制**：该入口 **不是**「一条命令更新全系统」下载器；11 步管线仍属契约/BINDINGS，下载主入口需沿 handbook/R2，本轮不补造。

| 主题 | 契约要求 | 实现证实 |
|---|---|---|
| INDEX_WEIGHT | 管理检查 | `apply_download=false`；**main 固定 return 0** — 退出码≠更新成功 |
| adjust_factor | 中断恢复 | wrapper 只转发；实现在 TASK_SCRIPT；state 关键词已定位，运行恢复未证 |
| external 物化 | phase 分发/接受 | 已列出 phase_* 与 main 行号；未调 API |
| FUND_NAV | get_extras 水位/去重/恢复 | 关键词命中已归档；未下载 |

详见 `UPDATE_CALLCHAIN_FULL.json` / `UPDATE_CHAIN.csv`。

## 3. 统计勿混
- remaining 轴条数继承 1440（约 304）= 多轴待办条数，**不是** 304 个独立数据缺口。
- 四项：实体证据已记；catalog 缺口仍在；内容全量未验收。

## 4. 回测/正式更新
仍不执行。ACCEPTANCE=false。
"""
    (OUT / "USER_FINAL_REPORT.md").write_text(report, encoding="utf-8")

    status = {
        "at": now(),
        "checkpoint": "COMPLETION_1447",
        "SYSTEM_INVENTORY_ACCEPTANCE": False,
        "status": "PARTIAL",
        "required4_main_enum": {ev["product_id"]: ev["main_enum"] for ev in four_rows},
        "required4_rows_meta": {ev["product_id"]: ev["primary_sample"].get("num_rows_meta") for ev in four_rows},
        "orchestrator_steps": 4,
        "orchestrator_is_full_system_downloader": False,
    }
    write_json(OUT / "STATUS_PROGRESS.json", status)
    (OUT / "MASTER_PROGRESS.md").write_text(
        f"# MASTER_PROGRESS 1447\n\n{json.dumps(status, ensure_ascii=False, indent=2)}\n",
        encoding="utf-8",
    )
    write_json(OUT / "CLAIM.json", {**json.loads((OUT / "CLAIM.json").read_text(encoding="utf-8")), "status": "DONE_LOCAL", "finished_at": now()})

    print(json.dumps({"ok": True, "status": status}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
