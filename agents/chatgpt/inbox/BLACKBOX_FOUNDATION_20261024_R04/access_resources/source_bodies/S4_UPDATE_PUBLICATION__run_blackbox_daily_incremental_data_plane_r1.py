#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BLACKBOX Daily Incremental Data Plane R1 — 六 Lane 统一数据总线（固定路径）。"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLANE = ROOT / "研究系统" / "数据平面"
PY = ROOT / ".venv" / "Scripts" / "python.exe"
CN = timezone(timedelta(hours=8))
LANES_CFG = PLANE / "CONFIG" / "daily_lanes.json"
PATH_MAP = PLANE / "CONFIG" / "DATA_PLANE_PATH_MAP.json"
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S%z")


def today_yyyymmdd() -> str:
    return datetime.now(CN).strftime("%Y%m%d")


def today_iso() -> str:
    return datetime.now(CN).strftime("%Y-%m-%d")


def load_json(p: Path) -> dict[str, Any]:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def normalize_asof(value: Any) -> str | None:
    """Normalize date to YYYY-MM-DD. Invalid/empty → None. No default invent."""
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() in {"none", "null", "nan"}:
        return None
    digits = "".join(ch for ch in s if ch.isdigit())
    if len(digits) == 8:
        return f"{digits[0:4]}-{digits[4:6]}-{digits[6:8]}"
    return None


def read_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Strict JSON object load. Returns (obj, reason_code). Never default-true."""
    if not path.exists():
        return None, "MISSING_FILE"
    try:
        raw = path.read_text(encoding="utf-8")
        obj = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, "INVALID_JSON"
    if not isinstance(obj, dict):
        return None, "INVALID_JSON"
    return obj, None


def evaluate_lane_a_asof_gate(
    *,
    scope_path: Path,
    cleaning_path: Path,
    cache_path: Path,
) -> dict[str, Any]:
    """P0-A gate: cleaning_as_of only; SOURCE==CLEAN==CACHE required for PASS.

    AUTHORIZED: no asof/data_asof fallback for cleaning. Fail → STATUS=NO.
    """
    fixed = {
        "scope": str(scope_path),
        "cleaning": str(cleaning_path),
        "cache": str(cache_path),
    }
    out: dict[str, Any] = {
        "SOURCE_ASOF": None,
        "CLEAN_ASOF": None,
        "CACHE_ASOF": None,
        "PIT_PASS": False,
        "STATUS": "NO",
        "reason_code": None,
        "FIXED_PATHS": fixed,
    }

    scope, err = read_json_object(scope_path)
    if err:
        out["reason_code"] = f"SCOPE_{err}"
        return out
    clean, err = read_json_object(cleaning_path)
    if err:
        out["reason_code"] = f"CLEANING_{err}"
        return out
    cache, err = read_json_object(cache_path)
    if err:
        out["reason_code"] = f"CACHE_{err}"
        return out

    assert scope is not None and clean is not None and cache is not None

    # Cleaning: formal key only. Forbidden silent fallback to asof/data_asof.
    if "cleaning_as_of" not in clean:
        if "asof" in clean and "data_asof" not in clean:
            out["reason_code"] = "CLEANING_ONLY_HAS_asof"
        elif "data_asof" in clean and "asof" not in clean:
            out["reason_code"] = "CLEANING_ONLY_HAS_data_asof"
        elif "asof" in clean or "data_asof" in clean:
            out["reason_code"] = "CLEANING_FORBIDDEN_FALLBACK_KEYS_WITHOUT_cleaning_as_of"
        else:
            out["reason_code"] = "CLEAN_ASOF_NULL"
        return out

    source_asof = normalize_asof(scope.get("data_asof"))
    clean_asof = normalize_asof(clean.get("cleaning_as_of"))
    # Cache formal key is asof on CURRENT_CACHE_RELEASE (not cleaning fallback).
    cache_asof = normalize_asof(cache.get("asof"))
    pit_ok = scope.get("operational_readiness") == "PASS"

    out["SOURCE_ASOF"] = source_asof
    out["CLEAN_ASOF"] = clean_asof
    out["CACHE_ASOF"] = cache_asof
    out["PIT_PASS"] = bool(pit_ok)

    if source_asof is None:
        out["reason_code"] = "SOURCE_NULL"
        return out
    if clean_asof is None:
        out["reason_code"] = "CLEAN_ASOF_NULL"
        return out
    if cache_asof is None:
        out["reason_code"] = "CACHE_NULL"
        return out

    if source_asof != clean_asof and source_asof != cache_asof and clean_asof != cache_asof:
        out["reason_code"] = "ALL_MISMATCH"
        return out
    # Distinguish outlier for fixture contract (transitive equality ⇒ at most one outlier).
    if source_asof != clean_asof and source_asof == cache_asof:
        out["reason_code"] = "CLEAN_CACHE_MISMATCH"  # clean disagrees with source(=cache)
        return out
    if source_asof != cache_asof and source_asof == clean_asof:
        out["reason_code"] = "SOURCE_CACHE_MISMATCH"
        return out
    if source_asof != clean_asof and clean_asof == cache_asof:
        out["reason_code"] = "SOURCE_CLEAN_MISMATCH"
        return out
    if source_asof != clean_asof:
        out["reason_code"] = "SOURCE_CLEAN_MISMATCH"
        return out
    if source_asof != cache_asof:
        out["reason_code"] = "SOURCE_CACHE_MISMATCH"
        return out
    if clean_asof != cache_asof:
        out["reason_code"] = "CLEAN_CACHE_MISMATCH"
        return out

    if not pit_ok:
        out["reason_code"] = "PIT_NOT_PASS"
        return out

    out["STATUS"] = "PASS"
    out["reason_code"] = "ALL_EQUAL"
    return out


def atomic_write_json(p: Path, obj: dict[str, Any]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)


def heartbeat(module: str, state: str, done: int, total: int, *, note: str = "") -> None:
    print(f"[HEARTBEAT] MODULE={module} STATE={state} ITEMS_DONE={done} ITEMS_TOTAL={total} {note}", flush=True)


def run_cmd(script: Path, extra: list[str] | None = None) -> int:
    if not script.exists():
        print(f"[SKIP] missing {script}", flush=True)
        return 1
    cmd = [str(PY), "-u", str(script)] + (extra or [])
    print(f"[RUN] {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, cwd=str(ROOT)).returncode


def scan_screenshots(folder: Path) -> list[str]:
    if not folder.exists():
        return []
    return sorted(str(p) for p in folder.rglob("*") if p.suffix.lower() in IMG_EXT)


def sellside_already_done_today(lane: dict, cn_iso: str) -> bool:
    last = load_json(Path(lane["last_success"]))
    cur = load_json(Path(lane["current"]))
    return last.get("last_successful_date") == cn_iso and last.get("status") == "PASS" and cur.get("asof") == cn_iso


def collect_lane_a(lane: dict, *, ingest: bool) -> dict[str, Any]:
    if ingest:
        run_cmd(Path(lane["scope_refresh_script"]))
    else:
        print("[DATA][JQ] VERIFY_ONLY already_updated=YES skip_ingest=YES", flush=True)
    gate = evaluate_lane_a_asof_gate(
        scope_path=Path(lane["scope_current"]),
        cleaning_path=Path(lane["cleaning_current"]),
        cache_path=Path(lane["cache_current"]),
    )
    body = {
        "lane": "A_JQ_INCREMENTAL",
        "MODE": "INGEST" if ingest else "VERIFY_ONLY",
        "SOURCE_ASOF": gate["SOURCE_ASOF"],
        "CLEAN_ASOF": gate["CLEAN_ASOF"],
        "CACHE_ASOF": gate["CACHE_ASOF"],
        "PIT_PASS": gate["PIT_PASS"],
        "STATUS": gate["STATUS"],
        "reason_code": gate["reason_code"],
        "FIXED_PATHS": gate["FIXED_PATHS"],
    }
    atomic_write_json(PLANE / lane["state_file"], {**body, "updated_at_cn": now_cn()})
    print(
        f"[DATA][JQ] source={body['SOURCE_ASOF']} clean={body['CLEAN_ASOF']} "
        f"cache={body['CACHE_ASOF']} mode={body['MODE']} status={body['STATUS']} "
        f"reason_code={body['reason_code']}",
        flush=True,
    )
    return body


def collect_lane_b(lane: dict, *, ingest: bool, asof: str) -> dict[str, Any]:
    if ingest:
        mat = Path(lane["materialization_script"])
        run_cmd(mat, ["--phase", "asof_align", "--asof", asof])
        run_cmd(mat, ["--phase", "acceptance", "--asof", asof])
    else:
        print("[DATA][T_EXTERNAL] VERIFY_ONLY already_updated=YES skip_ingest=YES", flush=True)
    align = load_json(Path(lane["asof_align_current"]))
    final = load_json(Path(lane["final_current"]))
    align_pass = align.get("status") == "PASS"
    final_st = final.get("FINAL_STATUS", "UNKNOWN")
    st = "PASS" if align_pass and final_st != "EXTERNAL_EVIDENCE_MATERIALIZATION_FAIL" else "DEGRADED"
    body = {
        "lane": "B_T_EXTERNAL_INCREMENTAL",
        "MODE": "INGEST" if ingest else "VERIFY_ONLY",
        "SOURCE_ASOF": align.get("hist_end") or align.get("aligned_to_jq_asof_yyyymmdd"),
        "ALIGN_PASS": align_pass,
        "STATUS": st,
        "FINAL_STATUS": final_st,
        "FIXED_PATHS": {"root": lane["product_root"], "final": lane["final_current"]},
        "JQ_CANONICAL_IMMUTABLE_FROM_T": True,
    }
    atomic_write_json(PLANE / lane["state_file"], {**body, "updated_at_cn": now_cn()})
    print(f"[DATA][T_EXTERNAL] mode={body['MODE']} align={align_pass} status={st}", flush=True)
    return body


def collect_lane_c(lane: dict, *, ingest: bool, cn_iso: str) -> dict[str, Any]:
    if ingest and not sellside_already_done_today(lane, cn_iso):
        run_cmd(Path(lane["script"]))
    elif not ingest:
        print("[DATA][SELLSIDE] VERIFY_ONLY skip_ingest=YES", flush=True)
    else:
        print(f"[DATA][SELLSIDE] SKIP_INGEST last_success={cn_iso} already PASS", flush=True)
    cur = load_json(Path(lane["current"]))
    asof = cur.get("asof")
    new_n = int(cur.get("NEW_REPORT_COUNT") or 0) + int(cur.get("NEW_METADATA_OR_EXTERNAL_SUMMARY_COUNT") or 0)
    failed = int(cur.get("FAILED_COUNT") or 0)
    st = "PASS" if asof and failed == 0 else ("DEGRADED" if asof else "NO")
    by_firm = {x.get("institution"): x.get("ingest_status") for x in cur.get("by_institution_status", [])}
    body = {
        "lane": "C_GLOBAL_SELLSIDE_INCREMENTAL",
        "MODE": "SKIP_ALREADY_DONE" if sellside_already_done_today(lane, cn_iso) and not ingest else ("INGEST" if ingest else "VERIFY_ONLY"),
        "DISCOVERY_ASOF": asof,
        "NEW_REPORTS": new_n,
        "MS_STATUS": by_firm.get("MORGAN_STANLEY"),
        "GS_STATUS": by_firm.get("GOLDMAN_SACHS"),
        "CLSA_STATUS": by_firm.get("CLSA"),
        "STATUS": st,
        "FIXED_PATHS": {
            "product_root": lane["product_root"],
            "raw_ms": lane["raw_ms"],
            "raw_gs": lane["raw_gs"],
            "raw_clsa": lane["raw_clsa"],
            "daily_incremental": lane["daily_incremental"],
            "current": lane["current"],
        },
    }
    atomic_write_json(PLANE / lane["state_file"], {**body, "updated_at_cn": now_cn()})
    print(f"[DATA][SELLSIDE] MS/GS/CLSA asof={asof} new={new_n} mode={body['MODE']} status={st}", flush=True)
    return body


def collect_lane_d(lane: dict, *, ingest: bool, cn_iso: str, cn_folder: str) -> dict[str, Any]:
    ds_root = Path(lane["domestic_sellside_root"])
    dn_root = Path(lane["domestic_news_root"])
    ds_daily = ds_root / "日增量" / cn_folder
    dn_daily = dn_root / "日增量" / cn_folder
    ds_daily.mkdir(parents=True, exist_ok=True)
    dn_daily.mkdir(parents=True, exist_ok=True)

    ledger_src = Path(lane["observer_ledger_fallback"])
    ledger_dst = ds_daily / "DOMESTIC_SELLSIDE_LEDGER.csv"
    if ledger_src.exists() and ledger_src.stat().st_size > 0:
        shutil.copy2(ledger_src, ledger_dst)
        print(f"[DATA][DOMESTIC] synced ledger → {ledger_dst}", flush=True)

    if ingest:
        ns = Path(lane.get("news_script", ""))
        if ns.exists():
            run_cmd(ns)

    ds_cur_p = Path(lane["domestic_sellside_current"])
    dn_cur_p = Path(lane["domestic_news_current"])
    n_ledger = 0
    if ledger_dst.exists():
        n_ledger = max(0, sum(1 for _ in ledger_dst.read_text(encoding="utf-8", errors="replace").splitlines()) - 1)

    ds_cur = {
        "schema_version": "1.0.0",
        "BUILD_TIME": now_cn(),
        "DISCOVERY_ASOF": cn_iso,
        "INGEST_TIME": now_cn(),
        "STATUS": "PASS" if n_ledger > 0 else "DEGRADED",
        "SOURCE_PATH": str(ledger_dst if ledger_dst.exists() else ds_root),
        "N_ROWS": n_ledger,
        "FIXED_ROOT": str(ds_root),
        "note": "国内卖方固定目录；observer ledger 同步为起点",
    }
    atomic_write_json(ds_cur_p, ds_cur)

    obs_news = load_json(Path(lane["news_obs_current"]))
    n_headlines = int(obs_news.get("n_headlines") or obs_news.get("headline_count") or 0)
    news_daily_json = dn_daily / "DOMESTIC_NEWS_SLICE.json"
    atomic_write_json(news_daily_json, obs_news)

    dn_cur = {
        "schema_version": "1.0.0",
        "BUILD_TIME": now_cn(),
        "DISCOVERY_ASOF": obs_news.get("asof") or cn_iso,
        "INGEST_TIME": now_cn(),
        "STATUS": "PASS" if n_headlines > 0 else "DEGRADED",
        "HEADLINE_COUNT": n_headlines,
        "FIXED_ROOT": str(dn_root),
        "daily_slice": str(dn_daily),
        "source_obs": lane["news_obs_current"],
    }
    atomic_write_json(dn_cur_p, dn_cur)

    st = "PASS" if ds_cur["STATUS"] == "PASS" and dn_cur["STATUS"] == "PASS" else "DEGRADED"
    if ds_cur["STATUS"] == "PASS" or dn_cur["STATUS"] == "PASS":
        st = "PASS" if (ds_cur["STATUS"] == "PASS" and dn_cur["STATUS"] == "PASS") else "DEGRADED"
    body = {
        "lane": "D_DOMESTIC_RESEARCH_NEWS_INCREMENTAL",
        "DISCOVERY_ASOF": cn_iso,
        "NEW_REPORTS": n_ledger,
        "NEW_EVENTS": dn_cur.get("HEADLINE_COUNT"),
        "STATUS": st,
        "FIXED_PATHS": {
            "domestic_sellside": str(ds_root),
            "domestic_news": str(dn_root),
            "sellside_current": str(ds_cur_p),
            "news_current": str(dn_cur_p),
        },
    }
    atomic_write_json(PLANE / lane["state_file"], {**body, "updated_at_cn": now_cn()})
    print(f"[DATA][DOMESTIC] sellside_rows={n_ledger} news={dn_cur['STATUS']} status={st}", flush=True)
    return body


_US_COLLECTOR_RAN = False


def run_us_l1_collector(lane_e: dict, *, ingest: bool, cn_iso: str) -> None:
    global _US_COLLECTOR_RAN
    if _US_COLLECTOR_RAN or not ingest:
        return
    script = Path(lane_e.get("collector_script", ROOT / "脚本" / "run_blackbox_us_l1_news_open_close_collector_r1.py"))
    run_cmd(script, ["--phase", "bootstrap", "--cn-date", cn_iso])
    _US_COLLECTOR_RAN = True


def collect_lane_e(lane: dict, *, ingest: bool, cn_iso: str, cn_folder: str) -> dict[str, Any]:
    run_us_l1_collector(lane, ingest=ingest, cn_iso=cn_iso)
    root = Path(lane["product_root"])
    cur_p = Path(lane["current"])
    cur = load_json(cur_p)
    if not cur:
        shot_dir = root / "抓屏" / cn_folder
        shots = scan_screenshots(shot_dir)
        st = "DEGRADED"
        body = {
            "lane": "E_US_NEWS_INCREMENTAL",
            "DISCOVERY_ASOF": cn_iso,
            "NEW_EVENTS": len(shots),
            "STATUS": st,
            "ACQUISITION_MODE": "SCREENSHOT" if shots else "AWAITING_CAPTURE_OR_FETCH",
            "FIXED_PATHS": {"root": str(root), "current": str(cur_p), "screenshot": str(shot_dir)},
        }
    else:
        st = cur.get("STATUS", "PARTIAL")
        if st not in ("PASS", "READY", "READY_WAITING_SESSION"):
            st = "PASS" if cur.get("NEW_EVENTS", 0) > 0 else "PARTIAL"
        body = {
            "lane": "E_US_NEWS_INCREMENTAL",
            "DISCOVERY_ASOF": cn_iso,
            "US_MARKET_DATE": cur.get("US_MARKET_DATE"),
            "CN_RESEARCH_DATE": cur.get("CN_RESEARCH_DATE"),
            "NEW_EVENTS": cur.get("NEW_EVENTS", 0),
            "DOMAIN_COUNTS": cur.get("DOMAIN_COUNTS", {}),
            "STATUS": st,
            "ACQUISITION_MODE": cur.get("ACQUISITION_MODE", "RSS_API"),
            "PRODUCT": "US_L1_IMPORTANT_NEWS",
            "FIXED_PATHS": {
                "root": str(root),
                "current": str(cur_p),
                "important_news_csv": lane.get("important_news_csv"),
                "taxonomy": lane.get("taxonomy"),
            },
        }
    atomic_write_json(PLANE / lane["state_file"], {**body, "updated_at_cn": now_cn()})
    dc = body.get("DOMAIN_COUNTS") or {}
    print(
        f"[DATA][US_NEWS] new_events={body.get('NEW_EVENTS')} "
        f"AI={dc.get('L1_AI_TECH_INFRA',0)} ENERGY={dc.get('L1_ENERGY_POWER',0)} status={body['STATUS']}",
        flush=True,
    )
    return body


def collect_lane_f(lane: dict, *, ingest: bool, cn_iso: str, cn_folder: str) -> dict[str, Any]:
    cfg = load_json(LANES_CFG)
    run_us_l1_collector(cfg["lanes"]["E_US_NEWS_INCREMENTAL"], ingest=ingest, cn_iso=cn_iso)
    fine_status = "NOT_RUN"
    fine_st = "SKIPPED"
    fine_paths: dict[str, Any] = {}
    if ingest and lane.get("fine_grained_script"):
        fg_script = Path(lane["fine_grained_script"])
        rc = run_cmd(fg_script, ["--phase", "daily", "--cn-date", cn_iso])
        fine_cur = load_json(Path(lane.get("fine_grained_current", ROOT / "运行" / "BLACKBOX_US_MARKET_FINE_GRAINED_FLOW_PROFIT_POOL_CURRENT.json")))
        fine_st = fine_cur.get("STATUS", "DEGRADED" if rc else "PARTIAL")
        if rc != 0:
            fine_st = "DEGRADED"
        fine_status = fine_st
        fine_paths = {
            "fine_grained_current": lane.get("fine_grained_current"),
            "fine_grained_root": lane.get("fine_grained_root"),
            "snapshot_current": str(Path(lane.get("fine_grained_root", "")) / "CURRENT" / "US_FINE_GRAINED_SNAPSHOT_CURRENT.json") if lane.get("fine_grained_root") else None,
            "mapping_prior_current": str(Path(lane.get("fine_grained_root", "")) / "CURRENT" / "A_SHARE_MAPPING_PRIOR_CURRENT.json") if lane.get("fine_grained_root") else None,
        }
    root = Path(lane["product_root"])
    cur_p = Path(lane["current"])
    snap = load_json(cur_p)
    align_p = Path(lane["session_alignment"])

    if not snap:
        shot_dir = root / "抓屏" / cn_folder
        shots = scan_screenshots(shot_dir)
        us_date = (datetime.now(CN) - timedelta(days=1)).strftime("%Y-%m-%d")
        st = "DEGRADED"
        close_ready = any("close" in Path(s).name.lower() for s in shots)
        open_ready = any("open" in Path(s).name.lower() for s in shots)
    else:
        us_date = snap.get("US_MARKET_DATE", cn_iso)
        st = snap.get("STATUS", "PARTIAL")
        if snap.get("SESSION_STATE") == "WAIT_FOR_US_OPEN":
            st = "READY_WAITING_SESSION" if snap.get("US_CLOSE_STATE") == "READY" else st
        elif snap.get("US_CLOSE_STATE") == "READY":
            st = "PASS"
        close_ready = snap.get("US_CLOSE_STATE") == "READY"
        open_ready = snap.get("US_OPEN_STATE") in ("READY", "WAITING")

    body = {
        "lane": "F_US_MARKET_STATE_INCREMENTAL",
        "US_MARKET_DATE": us_date,
        "CN_RESEARCH_DATE": snap.get("CN_RESEARCH_DATE", cn_iso),
        "SESSION_STATE": snap.get("SESSION_STATE"),
        "OPEN_READY": open_ready,
        "CLOSE_READY": close_ready,
        "STATUS": st,
        "ACQUISITION_MODE": snap.get("ACQUISITION_MODE", "YFINANCE_API"),
        "PRODUCTS": lane.get("products", ["US_OPEN_STATE", "US_CLOSE_STATE"]),
        "US_FINE_GRAINED_STATUS": fine_status,
        "A_SHARE_MAPPING_PRIOR_STATUS": fine_st,
        "FIXED_PATHS": {
            "root": str(root),
            "current": str(cur_p),
            "open_current": lane.get("open_current"),
            "close_current": lane.get("close_current"),
            "alignment": str(align_p),
            **fine_paths,
        },
    }
    atomic_write_json(PLANE / lane["state_file"], {**body, "updated_at_cn": now_cn()})
    print(
        f"[DATA][US_MARKET] us_date={us_date} session={body.get('SESSION_STATE')} "
        f"open={body['OPEN_READY']} close={body['CLOSE_READY']} status={body['STATUS']}",
        flush=True,
    )
    return body


def build_manifest(cn_iso: str, lanes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    degraded = [k for k, v in lanes.items() if v.get("STATUS") not in ("PASS", "READY", "READY_WAITING_SESSION")]
    ready = "YES" if not degraded else ("DEGRADED" if all(v.get("STATUS") != "NO" for v in lanes.values()) else "NO")
    raw = {
        "schema_version": "1.0.0",
        "manifest_id": f"DAILY_DATA_MANIFEST_{cn_iso.replace('-', '')}",
        "CN_RESEARCH_DATE": cn_iso,
        "BUILD_TIME": now_cn(),
        "PATH_MAP": str(PATH_MAP),
        "JQ": lanes.get("A", {}),
        "T_EXTERNAL": lanes.get("B", {}),
        "GLOBAL_SELLSIDE": lanes.get("C", {}),
        "DOMESTIC_RESEARCH": lanes.get("D", {}),
        "US_NEWS": lanes.get("E", {}),
        "US_MARKET": lanes.get("F", {}),
        "ALL_LANES_READY": ready,
        "DEGRADED_LANES": degraded,
        "DAILY_INCREMENTAL_READY": ready,
    }
    # DATA_GENERATION_ID issued by Data Plane (semantic hash; excludes BUILD_TIME / DG1 itself)
    from blackbox_run_identity_r1 import attach_data_generation_to_manifest

    return attach_data_generation_to_manifest(raw)


def build_input_pack(manifest: dict[str, Any], cfg: dict) -> dict[str, Any]:
    L = cfg["lanes"]
    raw = {
        "schema_version": "1.0.0",
        "BUILD_TIME": now_cn(),
        "DATA_MANIFEST_ID": manifest["manifest_id"],
        "CN_RESEARCH_DATE": manifest["CN_RESEARCH_DATE"],
        "DAILY_INCREMENTAL_READY": manifest["DAILY_INCREMENTAL_READY"],
        "FIXED_PATHS": {
            "GLOBAL_SELLSIDE": L["C_GLOBAL_SELLSIDE_INCREMENTAL"]["current"],
            "DOMESTIC_SELLSIDE": L["D_DOMESTIC_RESEARCH_NEWS_INCREMENTAL"]["domestic_sellside_current"],
            "DOMESTIC_NEWS": L["D_DOMESTIC_RESEARCH_NEWS_INCREMENTAL"]["domestic_news_current"],
            "US_NEWS": L["E_US_NEWS_INCREMENTAL"]["current"],
            "US_MARKET": L["F_US_MARKET_STATE_INCREMENTAL"]["current"],
            "US_FINE_GRAINED": L["F_US_MARKET_STATE_INCREMENTAL"].get("fine_grained_current"),
            "A_SHARE_MAPPING_PRIOR": str(Path(L["F_US_MARKET_STATE_INCREMENTAL"].get("fine_grained_root", "")) / "CURRENT" / "A_SHARE_MAPPING_PRIOR_CURRENT.json") if L["F_US_MARKET_STATE_INCREMENTAL"].get("fine_grained_root") else None,
            "JQ_SCOPE": L["A_JQ_INCREMENTAL"]["scope_current"],
            "T_EXTERNAL": L["B_T_EXTERNAL_INCREMENTAL"]["final_current"],
        },
    }
    from blackbox_run_identity_r1 import attach_data_generation_to_input_pack

    if manifest.get("DATA_GENERATION_ID"):
        return attach_data_generation_to_input_pack(raw, manifest)
    return raw


def build_temp_identity_manifest_from_lanes(cn_iso: str, lanes: dict[str, dict[str, Any]], cfg: dict) -> tuple[dict[str, Any], dict[str, Any]]:
    """Production builder functions without writing CURRENT. For TEMPORARY_REALDATA_IDENTITY_DRYRUN."""
    manifest = build_manifest(cn_iso, lanes)
    pack = build_input_pack(manifest, cfg)
    return manifest, pack


def archive_daily(cn_date: str, manifest: dict[str, Any], lanes: dict[str, dict]) -> None:
    d = PLANE / "DAILY" / cn_date
    d.mkdir(parents=True, exist_ok=True)
    atomic_write_json(d / "08_MANIFEST.json", manifest)
    names = ["01_JQ_DELTA", "02_T_EXTERNAL_DELTA", "03_GLOBAL_SELLSIDE_DELTA", "04_DOMESTIC_RESEARCH_DELTA", "05_US_NEWS_DELTA", "06_US_MARKET_STATE"]
    for key, name in zip(["A", "B", "C", "D", "E", "F"], names):
        atomic_write_json(d / f"{name}.json", lanes.get(key, {}))


def print_data_precheck(manifest: dict[str, Any]) -> None:
    print("=" * 40)
    print("BLACKBOX RESEARCH DATA PRECHECK")
    print("=" * 40)
    print(f"CN_RESEARCH_DATE = {manifest.get('CN_RESEARCH_DATE')}")
    jq = manifest.get("JQ") or {}
    print(
        f"JQ_ASOF = source={jq.get('SOURCE_ASOF')} clean={jq.get('CLEAN_ASOF')} "
        f"cache={jq.get('CACHE_ASOF')} mode={jq.get('MODE')} status={jq.get('STATUS')} "
        f"reason_code={jq.get('reason_code')}"
    )
    print(f"T_EXTERNAL = {manifest['T_EXTERNAL'].get('STATUS')} mode={manifest['T_EXTERNAL'].get('MODE')}")
    print(f"MS/GS/CLSA = {manifest['GLOBAL_SELLSIDE'].get('DISCOVERY_ASOF')} mode={manifest['GLOBAL_SELLSIDE'].get('MODE')}")
    print(f"DOMESTIC = {manifest['DOMESTIC_RESEARCH'].get('STATUS')}")
    print(f"US_NEWS = {manifest['US_NEWS'].get('STATUS')} acquisition={manifest['US_NEWS'].get('ACQUISITION_MODE')}")
    print(f"US_MARKET = {manifest['US_MARKET'].get('STATUS')} close={manifest['US_MARKET'].get('CLOSE_READY')}")
    print(f"DEGRADED_LANES = {manifest.get('DEGRADED_LANES')}")
    print(f"DAILY_INCREMENTAL_READY = {manifest.get('DAILY_INCREMENTAL_READY')}")
    print("=" * 40)


def publish_current(manifest: dict[str, Any], pack: dict[str, Any]) -> None:
    cur_dir = PLANE / "CURRENT"
    cur_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(cur_dir / "DAILY_DATA_MANIFEST_CURRENT.json", manifest)
    atomic_write_json(
        cur_dir / "DAILY_DATA_PLANE_CURRENT.json",
        {
            "schema_version": "1.0.0",
            "BUILD_TIME": now_cn(),
            "CN_RESEARCH_DATE": manifest["CN_RESEARCH_DATE"],
            "DAILY_INCREMENTAL_READY": manifest["DAILY_INCREMENTAL_READY"],
            "PATH_MAP": str(PATH_MAP),
            "manifest_current": str(cur_dir / "DAILY_DATA_MANIFEST_CURRENT.json"),
            "input_pack_current": str(cur_dir / "DAILY_RESEARCH_INPUT_PACK_CURRENT.json"),
            # Pointer shell only — DG1 lives on Manifest + Input Pack (same generation binding)
            "DATA_GENERATION_ID": manifest.get("DATA_GENERATION_ID"),
            "DATA_MANIFEST_ID": manifest.get("manifest_id"),
        },
    )
    atomic_write_json(cur_dir / "DAILY_RESEARCH_INPUT_PACK_CURRENT.json", pack)


def _rollback_data_plane_current(backup_dir: Path) -> None:
    cur = PLANE / "CURRENT"
    for name in (
        "DAILY_DATA_MANIFEST_CURRENT.json",
        "DAILY_DATA_PLANE_CURRENT.json",
        "DAILY_RESEARCH_INPUT_PACK_CURRENT.json",
    ):
        src = Path(backup_dir) / name
        if not src.is_file():
            raise RuntimeError(f"ROLLBACK_MISSING_BACKUP:{src}")
        shutil.copy2(src, cur / name)


def publish_identity_generation_no_collect(*, backup_dir: Path | str) -> dict[str, Any]:
    """Batch7: publish/seal DATA_GENERATION_ID without collectors/download/DB.

    Keeps CURRENT lane snapshot bytes for semantic stability; live-checks P0-A FIXED_PATHS.
    On any hard-gate failure: restore three CURRENT files from backup_dir.
    """
    from blackbox_run_identity_r1 import (
        attach_data_generation_to_manifest,
        verify_manifest_generation_stable,
    )

    backup_dir = Path(backup_dir)
    cur = PLANE / "CURRENT"
    man_path = cur / "DAILY_DATA_MANIFEST_CURRENT.json"
    pack_path = cur / "DAILY_RESEARCH_INPUT_PACK_CURRENT.json"
    result: dict[str, Any] = {
        "ok": False,
        "mode": "publish_identity",
        "collectors_started": False,
        "download": False,
        "database_writes": False,
        "rolled_back": False,
    }
    try:
        man = load_json(man_path)
        if not man:
            raise RuntimeError("MANIFEST_CURRENT_MISSING_OR_EMPTY")
        cfg = load_json(LANES_CFG)
        L = cfg["lanes"]["A_JQ_INCREMENTAL"]
        live_a = evaluate_lane_a_asof_gate(
            scope_path=Path(L["scope_current"]),
            cleaning_path=Path(L["cleaning_current"]),
            cache_path=Path(L["cache_current"]),
        )
        if live_a.get("STATUS") != "PASS" or live_a.get("reason_code") != "ALL_EQUAL":
            raise RuntimeError(f"P0A_GATE_FAIL:{live_a.get('reason_code')}")
        if not (
            live_a.get("SOURCE_ASOF")
            and live_a.get("SOURCE_ASOF") == live_a.get("CLEAN_ASOF") == live_a.get("CACHE_ASOF")
        ):
            raise RuntimeError("P0A_ASOF_NOT_EQUAL")

        jq_prev = man.get("JQ") or {}
        for k in ("SOURCE_ASOF", "CLEAN_ASOF", "CACHE_ASOF"):
            if normalize_asof(jq_prev.get(k)) != normalize_asof(live_a.get(k)):
                raise RuntimeError(f"LIVE_VS_CURRENT_ASOF_MISMATCH:{k}")
        if jq_prev.get("STATUS") != "PASS":
            raise RuntimeError("CURRENT_JQ_STATUS_NOT_PASS")
        if man.get("DAILY_INCREMENTAL_READY") != "YES":
            raise RuntimeError(f"DAILY_INCREMENTAL_READY_NOT_YES:{man.get('DAILY_INCREMENTAL_READY')}")

        # Preserve lane semantics; only refresh BUILD_TIME then re-issue DG1 (stable excludes).
        core = dict(man)
        core["BUILD_TIME"] = now_cn()
        new_man = attach_data_generation_to_manifest(core)
        if not new_man.get("DATA_GENERATION_ID"):
            raise RuntimeError("DATA_GENERATION_ID_MISSING_AFTER_BUILD")
        stab = verify_manifest_generation_stable(new_man)
        if not stab.get("ok"):
            raise RuntimeError(f"DG1_RECOMPUTE_FAIL:{stab.get('reason')}")
        prev_dg1 = man.get("DATA_GENERATION_ID")
        if prev_dg1 and prev_dg1 != new_man.get("DATA_GENERATION_ID"):
            raise RuntimeError(
                f"DG1_DRIFT_ON_SEAL:prev={prev_dg1}:new={new_man.get('DATA_GENERATION_ID')}"
            )

        cfg_full = load_json(LANES_CFG)
        new_pack = build_input_pack(new_man, cfg_full)
        if new_pack.get("DATA_GENERATION_ID") != new_man.get("DATA_GENERATION_ID"):
            raise RuntimeError("MANIFEST_INPUT_PACK_GENERATION_MISMATCH")
        if new_pack.get("DATA_MANIFEST_ID") != new_man.get("manifest_id"):
            raise RuntimeError("INPUT_PACK_MANIFEST_ID_MISMATCH")
        if new_pack.get("MANIFEST_SEMANTIC_SHA256") != new_man.get("MANIFEST_SEMANTIC_SHA256"):
            raise RuntimeError("INPUT_PACK_SEMANTIC_SHA_MISMATCH")

        publish_current(new_man, new_pack)
        man2 = load_json(man_path)
        pack2 = load_json(pack_path)
        plane2 = load_json(cur / "DAILY_DATA_PLANE_CURRENT.json")
        if man2.get("DATA_GENERATION_ID") != pack2.get("DATA_GENERATION_ID"):
            raise RuntimeError("POST_PUBLISH_BINDING_FAIL")
        if not verify_manifest_generation_stable(man2).get("ok"):
            raise RuntimeError("POST_PUBLISH_DG1_UNSTABLE")
        result.update(
            {
                "ok": True,
                "DATA_GENERATION_ID": man2.get("DATA_GENERATION_ID"),
                "manifest_id": man2.get("manifest_id"),
                "MANIFEST_SEMANTIC_SHA256": man2.get("MANIFEST_SEMANTIC_SHA256"),
                "SOURCE_ASOF": (man2.get("JQ") or {}).get("SOURCE_ASOF"),
                "CLEAN_ASOF": (man2.get("JQ") or {}).get("CLEAN_ASOF"),
                "CACHE_ASOF": (man2.get("JQ") or {}).get("CACHE_ASOF"),
                "DAILY_INCREMENTAL_READY": man2.get("DAILY_INCREMENTAL_READY"),
                "JQ_STATUS": (man2.get("JQ") or {}).get("STATUS"),
                "plane_pointer_generation": plane2.get("DATA_GENERATION_ID"),
                "previous_generation": prev_dg1,
            }
        )
        print(json.dumps({"publish_identity": result}, ensure_ascii=False, indent=2), flush=True)
        return result
    except Exception as e:
        result["error"] = str(e)
        try:
            _rollback_data_plane_current(backup_dir)
            result["rolled_back"] = True
        except Exception as rb:
            result["rollback_error"] = str(rb)
        print(json.dumps({"publish_identity": result}, ensure_ascii=False, indent=2), flush=True)
        return result


def p0a_selftest() -> int:
    """Isolated tempfile fixtures for P0-A. Does not touch CURRENT/Manifest production paths."""
    import tempfile

    results: list[tuple[str, bool, str]] = []

    def write(p: Path, obj: Any) -> None:
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(obj, str):
            p.write_text(obj, encoding="utf-8")
        else:
            p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def run_case(
        name: str,
        *,
        expect_status: str,
        expect_reason: str,
        scope: Any = None,
        clean: Any = None,
        cache: Any = None,
        omit_clean_file: bool = False,
        omit_scope_file: bool = False,
        omit_cache_file: bool = False,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="p0a_fix_") as td:
            root = Path(td)
            sp, cp, kp = root / "scope.json", root / "clean.json", root / "cache.json"
            if not omit_scope_file and scope is not None:
                write(sp, scope)
            if not omit_clean_file and clean is not None:
                write(cp, clean)
            if not omit_cache_file and cache is not None:
                write(kp, cache)
            gate = evaluate_lane_a_asof_gate(scope_path=sp, cleaning_path=cp, cache_path=kp)
            lanes = {"A": {**gate, "lane": "A_JQ_INCREMENTAL"}}
            for k in ("B", "C", "D", "E", "F"):
                lanes[k] = {"STATUS": "PASS"}
            man = build_manifest("2099-01-01", lanes)
            ready = man["DAILY_INCREMENTAL_READY"]
            expect_ready = "YES" if expect_status == "PASS" else "NO"
            exit_code = 0 if ready != "NO" else 1
            ok = (
                gate["STATUS"] == expect_status
                and gate["reason_code"] == expect_reason
                and ready == expect_ready
                and ((exit_code == 0) if expect_status == "PASS" else (exit_code != 0))
            )
            # Prove forbidden fallback never used
            if name in {"CLEANING_ONLY_HAS_asof", "CLEANING_ONLY_HAS_data_asof"}:
                ok = ok and gate["CLEAN_ASOF"] is None
            note = (
                f"status={gate['STATUS']} reason={gate['reason_code']} ready={ready} "
                f"exit={exit_code} src={gate['SOURCE_ASOF']} clean={gate['CLEAN_ASOF']} cache={gate['CACHE_ASOF']}"
            )
            results.append((name, ok, note))
            print(f"FIXTURE {name} = {'PASS' if ok else 'FAIL'}  {note}", flush=True)

    base_scope = {"data_asof": "2026-08-31", "operational_readiness": "PASS"}
    base_clean = {"cleaning_as_of": "2026-08-31"}
    base_cache = {"asof": "2026-08-31"}

    run_case("ALL_EQUAL", scope=base_scope, clean=base_clean, cache=base_cache, expect_status="PASS", expect_reason="ALL_EQUAL")
    run_case(
        "CLEAN_NULL",
        scope=base_scope,
        clean={"cleaning_as_of": None},
        cache=base_cache,
        expect_status="NO",
        expect_reason="CLEAN_ASOF_NULL",
    )
    run_case(
        "CACHE_NULL",
        scope=base_scope,
        clean=base_clean,
        cache={"asof": None},
        expect_status="NO",
        expect_reason="CACHE_NULL",
    )
    run_case(
        "SOURCE_NULL",
        scope={"data_asof": None, "operational_readiness": "PASS"},
        clean=base_clean,
        cache=base_cache,
        expect_status="NO",
        expect_reason="SOURCE_NULL",
    )
    run_case(
        "SOURCE_CLEAN_MISMATCH",
        scope=base_scope,
        clean={"cleaning_as_of": "2026-08-30"},
        cache={"asof": "2026-08-30"},
        expect_status="NO",
        expect_reason="SOURCE_CLEAN_MISMATCH",
    )
    run_case(
        "SOURCE_CACHE_MISMATCH",
        scope=base_scope,
        clean=base_clean,
        cache={"asof": "2026-08-30"},
        expect_status="NO",
        expect_reason="SOURCE_CACHE_MISMATCH",
    )
    run_case(
        "CLEAN_CACHE_MISMATCH",
        scope=base_scope,
        clean={"cleaning_as_of": "2026-08-30"},
        cache=base_cache,
        expect_status="NO",
        expect_reason="CLEAN_CACHE_MISMATCH",
    )
    run_case(
        "MISSING_FILE",
        scope=base_scope,
        clean=base_clean,
        cache=base_cache,
        omit_clean_file=True,
        expect_status="NO",
        expect_reason="CLEANING_MISSING_FILE",
    )
    run_case(
        "INVALID_JSON",
        scope=base_scope,
        clean="{not-json",
        cache=base_cache,
        expect_status="NO",
        expect_reason="CLEANING_INVALID_JSON",
    )
    run_case(
        "CLEANING_ONLY_HAS_asof",
        scope=base_scope,
        clean={"asof": "2026-08-31"},
        cache=base_cache,
        expect_status="NO",
        expect_reason="CLEANING_ONLY_HAS_asof",
    )
    run_case(
        "CLEANING_ONLY_HAS_data_asof",
        scope=base_scope,
        clean={"data_asof": "2026-08-31"},
        cache=base_cache,
        expect_status="NO",
        expect_reason="CLEANING_ONLY_HAS_data_asof",
    )

    failed = [n for n, ok, _ in results if not ok]
    print(f"P0A_SELFTEST_TOTAL={len(results)} PASS={len(results)-len(failed)} FAIL={len(failed)}", flush=True)
    if failed:
        print(f"P0A_SELFTEST_FAILED={failed}", flush=True)
        return 1
    print("P0A_SELFTEST=PASS", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="BLACKBOX Daily Incremental Data Plane R1")
    ap.add_argument(
        "--mode",
        default="status",
        choices=["run", "status", "resume", "publish_identity"],
    )
    ap.add_argument("--date", default=None)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--lane", default=None)
    ap.add_argument("--skip-jq", action="store_true", help="JQ already updated → verify only")
    ap.add_argument("--skip-t-external", action="store_true", help="T外源已更新 → verify only")
    ap.add_argument("--skip-sellside-if-done", action="store_true", help="三大行今日已成功则跳过重跑")
    ap.add_argument(
        "--p0a-selftest",
        action="store_true",
        help="P0-A isolated tempfile fixtures only; does not write production CURRENT",
    )
    ap.add_argument(
        "--identity-backup-dir",
        default=None,
        help="Required for --mode publish_identity: directory with three CURRENT backups for rollback",
    )
    args = ap.parse_args()
    if args.p0a_selftest:
        return p0a_selftest()
    if args.mode == "publish_identity":
        if not args.identity_backup_dir:
            print("FAIL: --identity-backup-dir required for publish_identity", flush=True)
            return 2
        r = publish_identity_generation_no_collect(backup_dir=args.identity_backup_dir)
        return 0 if r.get("ok") else 1
    mode = "run" if args.run else args.mode
    cn_date = args.date or today_yyyymmdd()
    cn_iso = f"{cn_date[:4]}-{cn_date[4:6]}-{cn_date[6:8]}"
    cn_folder = cn_iso

    cfg = load_json(LANES_CFG)
    scope = load_json(Path(cfg["lanes"]["A_JQ_INCREMENTAL"]["scope_current"]))
    jq_asof = scope.get("data_asof") or cn_iso

    ingest_jq = mode == "run" and not args.skip_jq
    ingest_t = mode == "run" and not args.skip_t_external
    ingest_c = mode == "run"
    ingest_d = mode == "run"

    L = cfg["lanes"]
    collectors = {
        "A": lambda: collect_lane_a(L["A_JQ_INCREMENTAL"], ingest=ingest_jq),
        "B": lambda: collect_lane_b(L["B_T_EXTERNAL_INCREMENTAL"], ingest=ingest_t, asof=jq_asof),
        "C": lambda: collect_lane_c(L["C_GLOBAL_SELLSIDE_INCREMENTAL"], ingest=ingest_c and not args.skip_sellside_if_done, cn_iso=cn_iso),
        "D": lambda: collect_lane_d(L["D_DOMESTIC_RESEARCH_NEWS_INCREMENTAL"], ingest=ingest_d, cn_iso=cn_iso, cn_folder=cn_folder),
        "E": lambda: collect_lane_e(L["E_US_NEWS_INCREMENTAL"], ingest=mode == "run", cn_iso=cn_iso, cn_folder=cn_folder),
        "F": lambda: collect_lane_f(L["F_US_MARKET_STATE_INCREMENTAL"], ingest=mode == "run", cn_iso=cn_iso, cn_folder=cn_folder),
    }
    order = [args.lane.upper()] if args.lane else ["A", "B", "C", "D", "E", "F"]
    lanes: dict[str, dict] = {}
    t0 = time.time()
    for i, key in enumerate(order):
        heartbeat(key, "COLLECT", i + 1, len(order))
        lanes[key] = collectors[key]()

    manifest = build_manifest(cn_iso, lanes)
    pack = build_input_pack(manifest, cfg)
    archive_daily(cn_date, manifest, lanes)
    publish_current(manifest, pack)
    print_data_precheck(manifest)
    print(f"[DATA][PLANE] elapsed={int(time.time()-t0)}s", flush=True)
    return 0 if manifest["DAILY_INCREMENTAL_READY"] != "NO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
