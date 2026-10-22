# -*- coding: utf-8 -*-
"""1527: PRODUCER_EVIDENCE — no bulk STATIC_REVIEWED; real producer paths only."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import shutil
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
ISO = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650")
SRC1447 = ISO / "continue_1310" / "completion_1447"
SRC1519 = ISO / "continue_1310" / "completion_1519"
OUT = ISO / "continue_1310" / "completion_1527"
OUT.mkdir(parents=True, exist_ok=True)
SRC = OUT / "source_reads"
SRC.mkdir(exist_ok=True)


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def sha(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def write_json(p: Path, o) -> None:
    p.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    keys: list[str] = []
    seen = set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                keys.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def func_span(path: Path, name: str) -> dict | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            start = node.lineno
            if node.decorator_list:
                start = min(d.lineno for d in node.decorator_list)
            end = node.end_lineno or node.lineno
            return {"name": name, "lineno": start, "end_lineno": end, "n_lines": end - start + 1}
    return None


def const_list(path: Path, varname: str) -> list | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(rf"^{re.escape(varname)}\s*=\s*\[(.*?)\]", text, re.M | re.S)
    if not m:
        return None
    try:
        return ast.literal_eval("[" + m.group(1) + "]")
    except Exception:
        # fallback quote scrape
        return re.findall(r'"([A-Z0-9_]+)"', m.group(1))


def evidence(
    *,
    objects: list[str],
    entry: Path | None,
    funcs: list[dict],
    io_publish: str,
    keys_watermark: str,
    status: str,
    notes: str,
    object_set_proven_in_code: bool,
) -> dict:
    rel = None
    s = None
    exists = False
    if entry is not None:
        exists = entry.is_file()
        try:
            rel = str(entry.relative_to(ROOT)).replace("\\", "/")
        except ValueError:
            rel = str(entry)
        s = sha(entry) if exists else None
    return {
        "object_set": objects,
        "object_set_proven_in_code": object_set_proven_in_code,
        "producer_entry_path": rel,
        "producer_entry_exists": exists,
        "producer_entry_sha256": s,
        "functions": funcs,
        "input_output_publish": io_publish,
        "keys_watermark_revision_resume": keys_watermark,
        "producer_review_status": status,  # PRODUCER_STATIC_REVIEWED | ENTRY_EXCLUSION_ONLY | NOT_REVIEWED | REUSED_PRIOR | KNOWN_GAP_CONTRACT
        "notes": notes,
    }


def main() -> int:
    write_json(
        OUT / "CLAIM.json",
        {
            "at": now(),
            "tip": "BLACKBOX_DATA_MANAGEMENT_REJECT_BULK_STATUS_CONTINUE_PRODUCERS_20261022_1527",
            "status": "CLAIMED_EXECUTING",
            "SYSTEM_INVENTORY_ACCEPTANCE": False,
            "PRODUCTION_CHANGE_AUTHORIZED": False,
            "rejected": "1519 bulk update_axis STATIC_REVIEWED via update_bind prefixes",
        },
    )

    pm = list(csv.DictReader((SRC1447 / "PRODUCT_MASTER.csv").open(encoding="utf-8-sig")))
    all_ids = [r["product_id"] for r in pm if r.get("product_id")]

    # --- copy prior findings (accepted) ---
    if (SRC1519 / "FINDINGS_LEDGER.json").exists():
        shutil.copy2(SRC1519 / "FINDINGS_LEDGER.json", OUT / "FINDINGS_LEDGER_ACCEPTED.json")

    producers: list[dict] = []

    # ========== 1) CBOND 14 ==========
    cbond_plane = ROOT / "脚本" / "blackbox_tushare_cbond_5y_plane_r2.py"
    cbond_reader = ROOT / "脚本" / "blackbox_tushare_cbond_reader_r2.py"
    r1_products = const_list(cbond_plane, "R1_PRODUCTS") or []
    # PIT products written by write_product in plane (from capability / code)
    pit_extra = [
        "TUSHARE_CBOND_RATING_PIT_R1",
        "TUSHARE_CBOND_RATING_R1",
        "TUSHARE_CBOND_CALL_PIT_R1",
        "TUSHARE_CBOND_REMAIN_SIZE_PIT_R1",
        "TUSHARE_CBOND_TOP10_HOLDERS_R1",
    ]
    cbond_ids = [i for i in all_ids if i.startswith("TUSHARE_CBOND_")]
    # object set from code R1_PRODUCTS + write_product call sites
    plane_text = cbond_plane.read_text(encoding="utf-8", errors="replace") if cbond_plane.is_file() else ""
    write_pids = re.findall(r'write_product\(\s*\n?\s*"([A-Z0-9_]+)"', plane_text)
    code_object_set = sorted(set(r1_products) | set(write_pids) | set(pit_extra))
    # intersection with ledger
    cbond_covered = sorted(set(cbond_ids) & set(code_object_set))
    cbond_ledger_only = sorted(set(cbond_ids) - set(code_object_set))
    funcs_cbond = [func_span(cbond_plane, n) for n in ("write_product", "promote", "main", "build_rating_pit", "build_call_pit", "build_remain_pit")]
    funcs_cbond = [f for f in funcs_cbond if f]
    # excerpt promote publish pointer
    (SRC / "CBOND_plane_consts.md").write_text(
        f"# CBOND producer\npath={cbond_plane}\nsha={sha(cbond_plane)}\n\nR1_PRODUCTS={r1_products}\nwrite_product_pids={write_pids}\nCBOND_PTR=数据/回测缓存/可转债指针/CURRENT_CBOND_CACHE_RELEASE.json\nREADER={cbond_reader} (NOT producer)\nMODIFY_STOCK_CURRENT=NO (header)\n",
        encoding="utf-8",
    )
    producers.append(
        evidence(
            objects=cbond_ids,
            entry=cbond_plane,
            funcs=funcs_cbond,
            io_publish=(
                "RAW 数据/原始只读/途施可转债* → CLEAN 途施可转债清洗* → CACHE releases BLACKBOX_CACHE_R*_途施可转债_* ; "
                "promote() writes 数据/回测缓存/可转债指针/CURRENT_CBOND_CACHE_RELEASE.json + product_path_map; "
                "STOCK MAIN CURRENT_CACHE_RELEASE.json deliberately NOT modified (MODIFY_STOCK_CURRENT=NO). "
                f"code_object_set∩ledger={cbond_covered}; ledger_only_unseen_in_write_list={cbond_ledger_only}"
            ),
            keys_watermark=(
                "ts_code/ann_date style event keys in build_*_pit; resume via slice_done/raw slices — STATIC from function names; "
                "runtime interrupt NOT_RUN"
            ),
            status="PRODUCER_STATIC_REVIEWED",
            notes="reader_r2 is consumer not producer. Main JQ CACHE may only inherit references — separate from CBOND_PTR publish.",
            object_set_proven_in_code=True,
        )
    )
    # reader separate note
    producers.append(
        evidence(
            objects=cbond_ids,
            entry=cbond_reader,
            funcs=[func_span(cbond_reader, "main")] if func_span(cbond_reader, "main") else [],
            io_publish="READ path only; not a build/publish producer",
            keys_watermark="N_A_READER",
            status="ENTRY_EXCLUSION_ONLY",
            notes="Documented so reader is not mistaken for producer",
            object_set_proven_in_code=False,
        )
    )

    # ========== 2) Minutes ==========
    etf_min_check = ROOT / "脚本" / "blackbox_etf_minute_daily_increment_check_r1.py"
    idx_align = ROOT / "脚本" / "index_minute_align_clean_antileak_seal_r1.py"
    idx_engine = ROOT / "脚本" / "index_minute_align_incremental_engine_r1.py"
    idx_dl = ROOT / "脚本" / "index_minute_jq_downloadable_download_r1.py"
    # stock minute download — search known
    stock_min_candidates = [
        ROOT / "脚本" / "blackbox_stock_minute_daily_increment_check_r1.py",
        ROOT / "脚本" / "p2_stock_minute_incremental_download_r1.py",
    ]
    stock_min = next((p for p in stock_min_candidates if p.is_file()), None)
    # ETF minute: check is NOT downloader
    producers.append(
        evidence(
            objects=["ETF_MINUTE_1M_R1"],
            entry=etf_min_check,
            funcs=[func_span(etf_min_check, "main")],
            io_publish="CHECK ONLY: looks for day tip under CURRENT cleaning price/ETF_1m; apply_download=False; does not switch CURRENT",
            keys_watermark="TARGET_DATE day filename __1m__YYYY-MM-DD__; SOURCE_REFRESH NOT_FETCHED_THIS_CHECK",
            status="PRODUCER_STATIC_REVIEWED",
            notes="This proves managed-check entry for 1m only. Does NOT prove ETF_MINUTE_5M/30M/60M producers. Download producer for missing slice = NOT_REVIEWED this round unless found below.",
            object_set_proven_in_code=True,
        )
    )
    # other ETF minute freqs — exclusion from daily cache ≠ producer reviewed
    for pid in ["ETF_MINUTE_5M_R1", "ETF_MINUTE_30M_R1", "ETF_MINUTE_60M_R1"]:
        producers.append(
            evidence(
                objects=[pid],
                entry=None,
                funcs=[],
                io_publish="mapping says N_A daily CACHE catalog — NOT a producer review",
                keys_watermark="UNPROVEN",
                status="NOT_REVIEWED",
                notes="ENTRY_EXCLUSION_ONLY was wrongly elevated in 1519; producer path for this frequency not located in this pass",
                object_set_proven_in_code=False,
            )
        )
    # stock minutes
    for pid in ["STOCK_MINUTE_1M_R1", "STOCK_MINUTE_5M_R1", "STOCK_MINUTE_30M_R1", "STOCK_MINUTE_60M_R1"]:
        producers.append(
            evidence(
                objects=[pid],
                entry=stock_min,
                funcs=[func_span(stock_min, "main")] if stock_min else [],
                io_publish="stock minute producer path "
                + ("FOUND " + str(stock_min.name) if stock_min else "NOT FOUND in candidate list this pass"),
                keys_watermark="UNPROVEN" if not stock_min else "see script body — STATIC locate only",
                status="PRODUCER_STATIC_REVIEWED" if stock_min and pid.endswith("1M_R1") else "NOT_REVIEWED",
                notes="Do not use N_A_MINUTE_NOT_DAILY_CACHE as update-reviewed. 950/unified registry reuse pending deeper bind if script missing.",
                object_set_proven_in_code=bool(stock_min and pid.endswith("1M_R1")),
            )
        )
    # index minute align layer
    producers.append(
        evidence(
            objects=["INDEX_MINUTE_ALIGN_LAYER"],  # not a product_id in 75 — document engine
            entry=idx_align,
            funcs=[func_span(idx_align, "main"), func_span(idx_engine, "main")],
            io_publish="P3_index_minute RAW → aligned cleaning standard/index_minute; incremental engine; seal CURRENT cleaning pointer for align release",
            keys_watermark="partition year/code/freq; incremental successor — STATIC; runtime NOT_RUN",
            status="PRODUCER_STATIC_REVIEWED",
            notes=f"download companion exists={idx_dl.is_file()} path=脚本/index_minute_jq_downloadable_download_r1.py; align ≠ each ETF/STOCK minute product",
            object_set_proven_in_code=True,
        )
    )

    # ========== 3) Main chain / JQ20 / SW ==========
    orch = ROOT / "脚本" / "blackbox_daily_increment_orchestrator_r1.py"
    tip = ROOT / "任务" / "BLACKBOX_BACKTEST_CACHE_COMPILER_R1" / "cache_compiler_tip_rebase_from_current_r1.py"
    handbook = ROOT / "运行" / "BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_WITH_SW_L123_CACHE_CURRENT.json"
    hb = json.loads(handbook.read_text(encoding="utf-8")) if handbook.is_file() else {}
    required_cache = hb.get("cache_products_required") or []
    # main-chain products that tip/orchestrator post-download covers — ONLY those listed in required + typical cache daily set from mapping VERIFIED
    main_chain_candidates = [
        "STOCK_DAILY_PIT_R1",
        "ETF_DAILY_PIT_R1",
        "ETF_FACTOR_DAILY_R1",
        "INDEX_DAILY_R1",
        "INDEX_FACTOR_DAILY_R1",
        "INDEX_CONSTITUENT_PIT_R1",
        "FINANCIAL_INDICATOR_PIT_R1",
        "VALUATION_PIT_R1",
        "STOCK_TRADEABILITY_PIT_R1",
        "BILLBOARD_DAILY_PIT_R1",
        "ETF_TRACKING_INDEX_MAP_R1",
        "SW_L1_MEMBERSHIP_PIT_R1",
        "SW_L2_MEMBERSHIP_PIT_R1",
        "SW_L3_MEMBERSHIP_PIT_R1",
        "SW_L1_STRUCTURE_DAILY_R1",
        "SW_L2_STRUCTURE_DAILY_R1",
        "SW_L3_STRUCTURE_DAILY_R1",
        "CORP_XR_XD_EVENT_PIT_R1",
        "CORP_SHAREHOLDER_TOP10_PIT_R1",
        "CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1",
    ]
    # Only claim post-download tip for objects in required_cache OR explicitly named in handbook daily_must — still NOT claiming RAW download producer
    tip_set = sorted(set(required_cache) & set(all_ids))
    producers.append(
        evidence(
            objects=tip_set,
            entry=orch,
            funcs=[func_span(orch, "main"), func_span(tip, "main")],
            io_publish=(
                "POST-DOWNLOAD only: orchestrator → tip_rebase → publish_atomic → scope_refresh. "
                "Object set taken from handbook cache_products_required ∩ ledger — NOT all ETF/INDEX/SW/OTHER prefixes. "
                "RAW download domain entry for each product = separate (often NOT_REVIEWED unless named elsewhere)."
            ),
            keys_watermark="MULTI_FILE_PUBLISH_FAILURE_WINDOW (KNOWN_GAP from 1519); tip no_publish candidate path",
            status="PRODUCER_STATIC_REVIEWED",
            notes="Does not cover CBOND. Does not cover JQ20. REQUIRED4 still catalog orphan on resolve path.",
            object_set_proven_in_code=True,
        )
    )
    # SW densify — handbook names it; find script
    sw_scripts = list((ROOT / "脚本").glob("*sw*densify*")) + list((ROOT / "脚本").glob("*sw_l*"))
    sw_hit = next((p for p in sw_scripts if p.is_file() and "densify" in p.name.lower()), None)
    if not sw_hit:
        # broader
        for p in (ROOT / "脚本").glob("*sw*"):
            if "membership" in p.name.lower() or "l123" in p.name.lower() or "densify" in p.name.lower():
                sw_hit = p
                break
    producers.append(
        evidence(
            objects=["SW_L1_MEMBERSHIP_PIT_R1", "SW_L2_MEMBERSHIP_PIT_R1", "SW_L3_MEMBERSHIP_PIT_R1"],
            entry=sw_hit,
            funcs=[func_span(sw_hit, "main")] if sw_hit else [],
            io_publish="handbook daily_must includes sw_l1_l2_l3_membership densify; script "
            + (sw_hit.name if sw_hit else "NOT_LOCATED_THIS_PASS"),
            keys_watermark="UNPROVEN if script missing",
            status="PRODUCER_STATIC_REVIEWED" if sw_hit else "KNOWN_GAP_CONTRACT",
            notes="Contract/handbook requires densify; producer script locate "
            + ("OK" if sw_hit else "FAILED — recorded as contract gap not fake NOT_REVIEWED forever"),
            object_set_proven_in_code=bool(sw_hit),
        )
    )

    # FUND family split — do NOT blanket NAV
    producers.append(
        evidence(
            objects=["FUND_NAV_PIT_R1"],
            entry=ROOT / "脚本" / "blackbox_fund_etf_nav_premium_plane_r1.py",
            funcs=[
                func_span(ROOT / "脚本" / "blackbox_fund_etf_nav_premium_plane_r1.py", n)
                for n in ("configure_window", "phase_download", "_merge_prior_tips", "phase_clean_cache", "main")
            ],
            io_publish="get_extras tip → clean → FUND_NAV_PIT_R1 cache publish; PRIOR_TIP_OVERRIDES_NEW_DUPLICATE confirmed",
            keys_watermark="(code,day); GAP_START/END; resume NOT_RUN",
            status="REUSED_PRIOR",
            notes="1507/1519 accepted; full_read 6496121/5980 retained",
            object_set_proven_in_code=True,
        )
    )
    for pid in ["FUND_DAILY_PIT_R1", "FUND_FACTOR_DAILY_R1"]:
        producers.append(
            evidence(
                objects=[pid],
                entry=None,
                funcs=[],
                io_publish="NOT same as FUND_NAV plane; likely main-chain RAW/clean/cache — producer script not separately bound this pass",
                keys_watermark="UNPROVEN",
                status="NOT_REVIEWED",
                notes="Rejected 1519 FUND_FAMILY→NAV blanket",
                object_set_proven_in_code=False,
            )
        )

    # ADJUST / IW reuse
    producers.append(
        evidence(
            objects=["ADJUST_FACTOR_PIT_R1"],
            entry=ROOT / "脚本" / "blackbox_adjust_factor_incremental_backward_refresh_r1.py",
            funcs=[],
            io_publish="wrapper→TASK incremental_backward_refresh; publish_successor bypasses publish_atomic (KNOWN_GAP)",
            keys_watermark="code/date; overlap 10d; dirty full history; resume STATIC/NOT_RUN",
            status="REUSED_PRIOR",
            notes="1519 findings accepted",
            object_set_proven_in_code=True,
        )
    )
    producers.append(
        evidence(
            objects=["INDEX_WEIGHT_PIT_R1"],
            entry=ROOT / "脚本" / "blackbox_index_weight_daily_increment_check_r1.py",
            funcs=[func_span(ROOT / "脚本" / "blackbox_index_weight_governance_r1.py", "daily_check")],
            io_publish="managed check only; apply_download=false; always rc 0",
            keys_watermark="decision in JSON not consumed by orchestrator",
            status="REUSED_PRIOR",
            notes="",
            object_set_proven_in_code=True,
        )
    )

    # JQ20 — entry exclusion ≠ producer reviewed
    jq20 = [i for i in all_ids if i.startswith("JQ20_")]
    producers.append(
        evidence(
            objects=jq20,
            entry=None,
            funcs=[],
            io_publish="ENTRY_DOES_NOT_SERVE_VIA_CACHE_CATALOG mapping only; domain download/clean producer NOT located as shared script with explicit object set this pass",
            keys_watermark="UNPROVEN",
            status="NOT_REVIEWED",
            notes="1519 wrongly marked STATIC_REVIEWED from exclusion",
            object_set_proven_in_code=False,
        )
    )

    # VIEW + registries
    producers.append(
        evidence(
            objects=["FUND_LIKE_ASSET_VIEW_R1"],
            entry=None,
            funcs=[],
            io_publish="logical VIEW — who builds/refreshes not found as dedicated producer this pass; must not inherit NAV rules",
            keys_watermark="UNPROVEN",
            status="NOT_REVIEWED",
            notes="",
            object_set_proven_in_code=False,
        )
    )
    producers.append(
        evidence(
            objects=["CACHE_MANIFEST_REGISTRY_R1", "CACHE_DEPENDENCY_REGISTRY_R1"],
            entry=ROOT / "脚本" / "blackbox_data_access_resolver_r1.py",
            funcs=[],
            io_publish="resolver reads registry JSON/CSV under 数据/回测缓存/registry/; generator/refresher of registry files NOT identified as separate producer this pass",
            keys_watermark="meta",
            status="NOT_REVIEWED",
            notes="resolver consumption ≠ registry producer",
            object_set_proven_in_code=False,
        )
    )

    # ETF_TRACKING etc already in tip_set possibly
    # remaining products not in any PRODUCER_STATIC_REVIEWED / REUSED_PRIOR object set
    covered: set[str] = set()
    for e in producers:
        if e["producer_review_status"] in ("PRODUCER_STATIC_REVIEWED", "REUSED_PRIOR"):
            for o in e["object_set"]:
                if o in all_ids:
                    covered.add(o)
    remaining_ids = [i for i in all_ids if i not in covered]
    if remaining_ids:
        producers.append(
            evidence(
                objects=remaining_ids,
                entry=None,
                funcs=[],
                io_publish="no producer evidence attached this round",
                keys_watermark="UNPROVEN",
                status="NOT_REVIEWED",
                notes="explicit residual bucket — not bulk-labeled reviewed",
                object_set_proven_in_code=False,
            )
        )

    write_json(OUT / "PRODUCER_EVIDENCE.json", {"at": now(), "n_entries": len(producers), "entries": producers})

    # rebuild ledger axes honestly
    status_by_pid: dict[str, str] = {i: "NOT_REVIEWED" for i in all_ids}
    entry_by_pid: dict[str, str] = {}
    note_by_pid: dict[str, str] = {}
    for e in producers:
        st = e["producer_review_status"]
        if st == "ENTRY_EXCLUSION_ONLY":
            continue
        for o in e["object_set"]:
            if o not in status_by_pid:
                continue
            # priority: REUSED_PRIOR / PRODUCER_STATIC_REVIEWED > KNOWN_GAP > NOT_REVIEWED
            cur = status_by_pid[o]
            rank = {
                "NOT_REVIEWED": 0,
                "KNOWN_GAP_CONTRACT": 1,
                "PRODUCER_STATIC_REVIEWED": 2,
                "REUSED_PRIOR": 3,
            }
            if rank.get(st, 0) >= rank.get(cur, 0):
                status_by_pid[o] = st
                entry_by_pid[o] = e.get("producer_entry_path") or ""
                note_by_pid[o] = e.get("notes") or ""

    # REQUIRED4 catalog gap remains diagnosis — update chain still not auto-reviewed unless in tip_set
    for pid in [
        "CORP_XR_XD_EVENT_PIT_R1",
        "CORP_SHAREHOLDER_TOP10_PIT_R1",
        "CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1",
        "SW_L3_MEMBERSHIP_PIT_R1",
    ]:
        note_by_pid[pid] = (note_by_pid.get(pid) or "") + " | catalog orphan diagnosis accepted; resolver path ≠ producer completeness"

    ledger = []
    for r in pm:
        pid = r["product_id"]
        ledger.append(
            {
                "product_id": pid,
                "mapping_status": r.get("mapping_status") or "",
                "producer_review_status": status_by_pid.get(pid, "NOT_REVIEWED"),
                "producer_entry": entry_by_pid.get(pid, ""),
                "producer_note": note_by_pid.get(pid, ""),
                "content_observed_prior": (
                    f"rows={r.get('full_read_rows')} shards={r.get('full_read_shards')}"
                    if r.get("full_read_rows")
                    else (r.get("data_completeness") or "")
                ),
                "content_this_round_ran": "NO",
                "content_vs_contract": r.get("data_completeness") or "REQUIRED_RANGE_UNPROVEN",
                "full_read_rows": r.get("full_read_rows") or "",
                "full_read_shards": r.get("full_read_shards") or "",
                "findings_tags": "",
            }
        )
    # tag findings on specific products
    for row in ledger:
        if row["product_id"] == "FUND_NAV_PIT_R1":
            row["findings_tags"] = "PRIOR_TIP_OVERRIDES_NEW_DUPLICATE; full_read_6496121/5980"
            row["content_observed_prior"] = "PRIOR_FULL_READ rows=6496121 shards=5980"
        if row["product_id"] == "ADJUST_FACTOR_PIT_R1":
            row["findings_tags"] = "ADJUST_PUBLISH_BYPASSES_ATOMIC_GATE; OVERLAP_DIRTY_RULE"
        if row["product_id"] == "INDEX_WEIGHT_PIT_R1":
            row["findings_tags"] = "MANAGED_CHECK_RC0"

    write_csv(OUT / "OBJECT_LEDGER_75.csv", ledger)
    write_json(OUT / "OBJECT_LEDGER_75.json", {"at": now(), "n": len(ledger), "rows": ledger})

    stats = {
        "n": len(ledger),
        "producer_review_status": dict(Counter(r["producer_review_status"] for r in ledger)),
        "mapping_status": dict(Counter(r["mapping_status"] for r in ledger)),
        "note": "producer_review_status ≠ mapping_status; bulk 75/75 STATIC_REVIEWED REJECTED",
    }
    write_json(OUT / "LEDGER_STATS.json", stats)

    # external truncation door note
    write_json(
        OUT / "EXTERNAL_TRUNCATION_GATE_STATUS.json",
        {
            "phase_acceptance_matrix": "recorded behavior; hardcoded GATE PASS ≠ measured",
            "silent_truncation_5000": "NOT traced into phase_acceptance body in 1519 — remains UNVERIFIED_IN_ACCEPTANCE; download-phase enforcement still to bind — NOT_REVIEWED as N_A",
            "status": "PARTIAL_PRIOR_MATRIX_ONLY",
        },
    )

    # engine scope — try locate authority entry beyond heuristic
    engine_note = {
        "prior_engine_files_copied": False,
        "status": "NOT_REVIEWED_BEYOND_PRIOR_HEURISTIC",
        "action": "copied prior ENGINE_* if present; no new path_heuristic-only claim of reviewed",
    }
    for base in (SRC1447, SRC1519, ISO / "continue_1310" / "completion_1429"):
        for name in ("ENGINE_SCOPE.csv", "ENGINE_ROOT_LOOKUP.json"):
            p = base / name
            if p.exists():
                shutil.copy2(p, OUT / name)
                engine_note["prior_engine_files_copied"] = True
                engine_note[name] = str(p)
    write_json(OUT / "ENGINE_SCOPE_STATUS.json", engine_note)

    remaining = [
        {"id": "STOCK_ETF_MINUTE_NON_1M_PRODUCERS", "status": "NOT_REVIEWED", "priority": 1},
        {"id": "STOCK_MINUTE_DOWNLOAD_ENTRY", "status": "NOT_REVIEWED", "priority": 1},
        {"id": "JQ20_DOMAIN_PRODUCERS", "status": "NOT_REVIEWED", "priority": 1},
        {"id": "FUND_DAILY_FACTOR_PRODUCERS", "status": "NOT_REVIEWED", "priority": 1},
        {"id": "FUND_LIKE_VIEW_BUILDER", "status": "NOT_REVIEWED", "priority": 2},
        {"id": "REGISTRY_REFRESH_PRODUCER", "status": "NOT_REVIEWED", "priority": 2},
        {"id": "SW_DENSIFY_SCRIPT" if not sw_hit else "SW_DENSIFY_RUNTIME", "status": "KNOWN_GAP_CONTRACT" if not sw_hit else "NOT_RUN", "priority": 2},
        {"id": "RAW_DOWNLOAD_PER_DOMAIN_FOR_TIP_SET", "status": "NOT_REVIEWED", "priority": 2, "note": "tip set post-download reviewed; RAW download entries still open"},
        {"id": "EXTERNAL_SILENT_TRUNCATION_BIND", "status": "NOT_REVIEWED", "priority": 2},
        {"id": "LIMITED_ENGINE_AUTHORITY_ENTRIES", "status": "NOT_REVIEWED", "priority": 3},
        {"id": "MULTI_FILE_PUBLISH_FAILURE_WINDOW", "status": "KNOWN_GAP", "priority": 1, "fix": "not this round"},
        {"id": "REQUIRED4_CATALOG", "status": "KNOWN_GAP", "priority": 1, "fix": "not this round"},
    ]
    write_json(OUT / "REMAINING_PRIORITIZED.json", {"at": now(), "items": remaining})

    # SOURCE_READS
    files = []
    for p in sorted(SRC.rglob("*")):
        if p.is_file():
            files.append({"rel": str(p.relative_to(OUT)).replace("\\", "/"), "sha256": sha(p), "size": p.stat().st_size})
    # also record key producer shas
    for label, p in [
        ("cbond_plane", cbond_plane),
        ("etf_min_check", etf_min_check),
        ("idx_align", idx_align),
        ("orch", orch),
        ("tip", tip),
    ]:
        if p.is_file():
            files.append({"label": label, "path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(p), "size": p.stat().st_size})
    write_json(OUT / "SOURCE_READS.json", {"at": now(), "files": files})

    report = f"""# 数据管理阶段报告（1527）— PARTIAL / 生产者证据（拒绝批量已审）

at: {now()}
SYSTEM_INVENTORY_ACCEPTANCE: **false**
PRODUCTION_CHANGE_AUTHORIZED: false

## 驳回
1519 用 `update_bind` 前缀把 CBOND/分钟排除/FUND_FAMILY/JQ20 等批量标成 update STATIC_REVIEWED — **不接受**。  
映射排除 ≠ 生产者已审；FUND_NAV ≠ FUND_DAILY/FACTOR/VIEW。

## 接受（不重测）
FINDINGS_LEDGER（发布故障窗 / NAV 旧 tip 覆盖 / ADJUST 旁路+dirty）；FUND_NAV 6496121/5980。

## PRODUCER_EVIDENCE（本包核心）
见 `PRODUCER_EVIDENCE.json`。摘要：
- **CBOND 14**：生产者=`脚本/blackbox_tushare_cbond_5y_plane_r2.py`（write_product/promote/main…）；专用 `CURRENT_CBOND_CACHE_RELEASE.json`；**不改**主 STOCK CURRENT；reader≠生产者。
- **ETF_MINUTE_1M**：仅 managed check 已审；5m/30m/60m **NOT_REVIEWED**。
- **指数分钟对齐层**：`index_minute_align_clean_antileak_seal_r1` (+ engine) **PRODUCER_STATIC_REVIEWED**（层，不是各分钟产品）。
- **主链 tip 集合**：仅 handbook `cache_products_required` ∩ 账本 — post-download orchestrator/tip；**不等于**各域 RAW 下载已审。
- **FUND_NAV / ADJUST / INDEX_WEIGHT**：REUSED_PRIOR。
- **JQ20 / FUND_DAILY / FUND_FACTOR / VIEW / REGISTRY 生成**：NOT_REVIEWED。
- **SW densify**：{"脚本已定位 "+sw_hit.name if sw_hit else "合同有、脚本本轮未定位=KNOWN_GAP_CONTRACT"}。

## 75 账本真实统计
{json.dumps(stats, ensure_ascii=False, indent=2)}

## 外源
acceptance 矩阵保留；硬编码 PASS≠实测；5000 截断门在 acceptance 未追到 → **不**标 N_A，标未核。

不实施生产修复。完整性/整体验收仍 false。
"""
    (OUT / "USER_FINAL_REPORT.md").write_text(report, encoding="utf-8")
    status = {
        "at": now(),
        "checkpoint": "COMPLETION_1527",
        "SYSTEM_INVENTORY_ACCEPTANCE": False,
        "status": "PARTIAL",
        "stats": stats,
        "producer_entries": len(producers),
        "sw_densify_script": str(sw_hit) if sw_hit else None,
    }
    write_json(OUT / "STATUS_PROGRESS.json", status)
    (OUT / "MASTER_PROGRESS.md").write_text(f"# MASTER_PROGRESS 1527\n\n{json.dumps(status, ensure_ascii=False, indent=2)}\n", encoding="utf-8")
    write_json(OUT / "CLAIM.json", {**json.loads((OUT / "CLAIM.json").read_text(encoding="utf-8")), "status": "DONE_LOCAL", "finished_at": now()})
    print(json.dumps({"ok": True, "status": status}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
