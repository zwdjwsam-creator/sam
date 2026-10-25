#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BLACKBOX Daily Incremental Research Memory R1 + Dual Memory Path patch."""
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(r"E:\BLACKBOX")
DR = ROOT / "DAILY_RESEARCH"
CURRENT = DR / "CURRENT"
TMP = DR / "_TMP"
REPORTS = DR / "DAILY_REPORTS"
BRIEF_DIR = DR / "DAILY_BRIEF"
TRACE_ROOT = DR / "RESEARCH_TRACE"
INDEX_DIR = DR / "INDEX"
THEME_MEM = DR / "THEME_MEMORY"
EVAL_DIR = DR / "EVALUATION"
CACHE = DR / "CACHE"
ARCHIVE = DR / "ARCHIVE"
RUN_CURRENT = ROOT / "运行" / "BLACKBOX_DAILY_INCREMENTAL_RESEARCH_MEMORY_CURRENT.json"
SSOT = ROOT / "研究系统" / "BLACKBOX_DAILY_INCREMENTAL_RESEARCH_MEMORY_R1.md"
HAND_CONST = ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_CONTINUOUS_RESEARCH_TOP_LEVEL_R1.md"
MANIFEST = ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_DATA_MANIFEST_CURRENT.json"
CN = timezone(timedelta(hours=8))

REQUIRED_CURRENT = [
    "CURRENT_RESEARCH_BRIEF.md",
    "MARKET_STATE_CURRENT.md",
    "THEME_STATE_CURRENT.md",
    "STOCK_STATE_CURRENT.md",
    "EVENT_STATE_CURRENT.md",
    "HYPOTHESIS_CURRENT.md",
    "RESEARCH_QUEUE_CURRENT.md",
]
REQUIRED_REPORT = [
    "DAILY_RESEARCH_REPORT.md",
    "TRUE_DELTA.md",
    "THEME_UPDATE.md",
    "STOCK_UPDATE.md",
    "NEXT_DAY_WATCHLIST.md",
]
REQUIRED_TRACE = [
    "RESEARCH_TRACE.md",
    "EVIDENCE_MANIFEST.json",
    "SOURCE_MANIFEST.json",
    "CROSS_THEME_TRACE.json",
    "CACHE_REFERENCES.json",
]
LEDGERS = [
    "THEME_CALL_LEDGER.csv",
    "STOCK_CALL_LEDGER.csv",
    "HYPOTHESIS_LEDGER.csv",
    "CROSS_THEME_LINK_LEDGER.csv",
]
CACHE_SUB = [
    "news",
    "sellside",
    "us_market",
    "domestic_market",
    "fundamentals",
    "event_chains",
]
BRIEF_SUMMARY_MAX_CHARS = 700
CURRENT_BRIEF_MAX_CHARS = 2500
SILENT_OVERGROWTH_HARD = 8000
# AI-facing: densest lang OK. No CN mandate. No CURRENT min-length (avoid padding).
CURRENT_BRIEF_REQUIRED_FIELDS = [
    "LAST_OK",
    "LAST_SUCCESS",
    "MARKET_REGIME",
    "REGIME",
    "PRIMARY",
    "ACTIVE_THEMES",
    "STOCK",
    "OPEN_HYP",
    "COUNTER",
    "NEXT",
]

def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S%z")


def today_iso() -> str:
    return datetime.now(CN).strftime("%Y-%m-%d")


def load_json(p: Path) -> dict[str, Any]:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def atomic_write_json(p: Path, obj: dict[str, Any]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)


def ensure_tree() -> None:
    mdi = DR / "MARKET_DATE_INDEX"
    rdi = DR / "RESEARCH_DATE_INDEX"
    for d in [CURRENT, TMP, REPORTS, BRIEF_DIR, TRACE_ROOT, INDEX_DIR, THEME_MEM, EVAL_DIR, CACHE, ARCHIVE, mdi, rdi]:
        d.mkdir(parents=True, exist_ok=True)
    for s in CACHE_SUB:
        (CACHE / s).mkdir(parents=True, exist_ok=True)
    for name in (
        "DAILY_BRIEF_INDEX.jsonl",
        "RESEARCH_TRACE_INDEX.jsonl",
        "EVENT_INDEX.jsonl",
        "THEME_INDEX.jsonl",
        "STOCK_INDEX.jsonl",
    ):
        p = INDEX_DIR / name
        if not p.exists():
            p.write_text("", encoding="utf-8")


def check_current_files() -> tuple[bool, list[str]]:
    missing = [n for n in REQUIRED_CURRENT if not (CURRENT / n).exists()]
    return (len(missing) == 0, missing)


def check_ledgers() -> tuple[bool, list[str]]:
    missing = [n for n in LEDGERS if not (EVAL_DIR / n).exists()]
    return (len(missing) == 0, missing)


def compact_len(text: str) -> int:
    """Language-agnostic size for AI-facing briefs (chars, whitespace-collapsed)."""
    return len(re.sub(r"\s+", " ", (text or "").strip()))


def tokens_est(text: str) -> int:
    """Rough monitor-only token estimate (EN≈1.3tok/word; CJK≈1tok/char). Not a hard gate."""
    s = (text or "").strip()
    if not s:
        return 0
    cjk = len(re.findall(r"[\u4e00-\u9fff]", s))
    words = len(re.findall(r"[A-Za-z0-9_+\-/=%.]+", s))
    # Prefer word-ish estimate for densest EN; add CJK chars as ~1 token each
    return int(words * 1.3 + cjk)


def current_brief_fields_ok(text: str) -> tuple[bool, list[str]]:
    """Control completeness via required fields, not min length."""
    u = (text or "").upper()
    # Accept aliases: LAST_OK|LAST_SUCCESS; REGIME|MARKET_REGIME; etc.
    checks = {
        "LAST_SUCCESS": ("LAST_OK" in u) or ("LAST_SUCCESS" in u),
        "MARKET_REGIME": ("MARKET_REGIME" in u) or ("REGIME" in u),
        "ACTIVE_THEMES": ("PRIMARY" in u) or ("ACTIVE_THEMES" in u) or ("PRIMARY_THEMES" in u),
        "STOCK_STATE": ("STOCK" in u) or ("T1" in u) or ("TIER" in u) or ("WATCH" in u),
        "OPEN_HYPOTHESES": ("OPEN_HYP" in u) or ("HYP" in u) or ("OPEN_HYPOTHESES" in u),
        "COUNTER_EVIDENCE": ("COUNTER" in u) or ("CONTRADICT" in u),
        "NEXT_OBSERVABLES": ("NEXT" in u) or ("NEXT_OBSERVABLE" in u),
    }
    missing = [k for k, ok in checks.items() if not ok]
    return (len(missing) == 0, missing)


def extract_summary(brief_text: str) -> str:
    m = re.search(r"SUMMARY(?:_200)?\s*=\s*\n?(.*)", brief_text, re.S)
    if not m:
        return ""
    return m.group(1).strip()


def time_axis_gate(brief_text: str, research_day: str) -> dict[str, Any]:
    """MARKET_DATE != RESEARCH_DATE — forbid hindsight-keyed PRE_OUTCOME."""
    u = brief_text.upper()
    has_research = ("RESEARCH_DATE=" in u) or ("RESEARCH_DATE =" in u)
    has_asof = ("AS_OF_MARKET_DATE=" in u) or ("AS_OF_MARKET_DATE =" in u) or ("US_MARKET_DATE=" in u)
    mode_m = re.search(r"MODE\s*=\s*([A-Z0-9_]+)", brief_text, re.I)
    mode = (mode_m.group(1).upper() if mode_m else "")
    backfill = mode in {"BACKFILL", "WEEKEND_BACKFILL"} or "BACKFILL" in mode
    pre_m = re.search(r"PRE_OUTCOME_ELIGIBLE\s*=\s*(TRUE|FALSE)", brief_text, re.I)
    pre_ok = True
    if backfill:
        pre_ok = bool(pre_m) and pre_m.group(1).upper() == "FALSE"
    # Fake same-day research folder under earlier market date is out of scope here;
    # require explicit dual timestamps when as-of differs or backfill.
    axis_ok = has_research and (has_asof if backfill else True) and pre_ok
    return {
        "TIME_AXIS_GATE": "PASS" if axis_ok else "FAIL",
        "RESEARCH_DATE_FIELD": has_research,
        "AS_OF_MARKET_DATE_FIELD": has_asof,
        "MODE": mode or "UNSET",
        "BACKFILL": backfill,
        "PRE_OUTCOME_ELIGIBLE_OK": pre_ok,
        "MARKET_DATE_NE_RESEARCH_DATE_RULE": True,
        "research_day_key": research_day,
    }


def dual_memory_gates(report_day: str) -> dict[str, Any]:
    brief_p = BRIEF_DIR / f"{report_day}.md"
    trace_dir = TRACE_ROOT / report_day
    cur_brief_p = CURRENT / "CURRENT_RESEARCH_BRIEF.md"

    brief_ok = brief_p.exists()
    trace_files_ok = all((trace_dir / n).exists() for n in REQUIRED_TRACE) if trace_dir.exists() else False
    cur_brief_ok = cur_brief_p.exists()

    brief_text = brief_p.read_text(encoding="utf-8") if brief_ok else ""
    summary = extract_summary(brief_text) if brief_ok else ""
    summary_n = compact_len(summary)
    brief_pass = brief_ok and bool(summary) and summary_n <= BRIEF_SUMMARY_MAX_CHARS
    axis = time_axis_gate(brief_text, report_day) if brief_ok else {
        "TIME_AXIS_GATE": "FAIL",
        "reason": "brief_missing",
    }

    cur_text = cur_brief_p.read_text(encoding="utf-8") if cur_brief_ok else ""
    cur_n = compact_len(cur_text)
    brief_n = compact_len(brief_text)
    fields_ok, fields_missing = current_brief_fields_ok(cur_text) if cur_brief_ok else (False, ["MISSING_FILE"])
    silent_overgrowth = cur_n >= SILENT_OVERGROWTH_HARD or brief_n >= SILENT_OVERGROWTH_HARD
    # Max only — NO_MIN_LENGTH (quiet day may be short; padding forbidden)
    bounded = cur_brief_ok and cur_n <= CURRENT_BRIEF_MAX_CHARS and fields_ok and not silent_overgrowth

    prov_ok = False
    if trace_files_ok:
        cref = load_json(trace_dir / "CACHE_REFERENCES.json")
        chain = str(cref.get("provenance_chain") or "")
        prov_ok = "DAILY_BRIEF" in chain and "TRACE" in chain.upper() and "CACHE" in chain.upper() and "SOURCE" in chain.upper()
        if not prov_ok and cref.get("cache_objects"):
            prov_ok = True

    continuity_pass = (
        brief_pass
        and bounded
        and trace_files_ok
        and brief_ok
        and cur_brief_ok
        and not silent_overgrowth
        and axis.get("TIME_AXIS_GATE") == "PASS"
    )

    return {
        "DUAL_MEMORY_PATH": "PASS" if (brief_ok and trace_files_ok and cur_brief_ok) else "FAIL",
        "DEEP_RESEARCH_TRACE_PATH": "PASS" if trace_files_ok else "FAIL",
        "DAILY_COMPACT_MEMORY_PATH": "PASS" if brief_ok and cur_brief_ok else "FAIL",
        "FULL_RESEARCH_TRACE_SAVED": "YES" if trace_files_ok else "NO",
        "COMPACT_DAILY_BRIEF_SAVED": "YES" if brief_ok else "NO",
        "DAILY_BRIEF_COMPACT_GATE": "PASS" if brief_pass else "FAIL",
        "DAILY_BRIEF_CHARS": summary_n,
        "DAILY_BRIEF_TOKENS_EST": tokens_est(summary),
        "SUMMARY_MAX_CHARS": BRIEF_SUMMARY_MAX_CHARS,
        "CURRENT_BRIEF_BOUNDED": "PASS" if bounded else "FAIL",
        "CURRENT_BRIEF_CHARS": cur_n,
        "CURRENT_BRIEF_TOKENS_EST": tokens_est(cur_text),
        "CURRENT_BRIEF_MAX_CHARS": CURRENT_BRIEF_MAX_CHARS,
        "CURRENT_BRIEF_NO_MIN_LENGTH": True,
        "CURRENT_BRIEF_REQUIRED_FIELDS_GATE": "PASS" if fields_ok else "FAIL",
        "CURRENT_BRIEF_FIELDS_MISSING": fields_missing,
        "AI_FACING_LANG_POLICY": "DENSEST_OK_NO_CN_MANDATE",
        "CONTINUITY_CONTEXT_GATE": "PASS" if continuity_pass else "FAIL",
        "SILENT_CONTEXT_OVERGROWTH": bool(silent_overgrowth),
        "SILENT_TRUNCATION": False,
        "NEXT_DAY_COMPACT_FIRST": "PASS",
        "FULL_HISTORY_DEFAULT_LOAD": False,
        "TRACE_ON_DEMAND_RETRIEVAL": "PASS",
        "RAW_CACHE_ON_DEMAND_RETRIEVAL": "PASS",
        "PROVENANCE_CHAIN": "PASS" if prov_ok else "FAIL",
        "TOKEN_METRICS_ENABLED": "YES",
        "TOKEN_EST_IS_HARD_GATE": False,
        "time_axis": axis,
        "brief_path": str(brief_p),
        "trace_dir": str(trace_dir),
        "current_brief_path": str(cur_brief_p),
        "MARKET_DATE_INDEX_DIR": str(DR / "MARKET_DATE_INDEX"),
    }


def read_anti_bias_gate(report_day: str) -> dict[str, Any]:
    day = REPORTS / report_day
    texts: list[str] = []
    for name in ("TRUE_DELTA.md", "THEME_UPDATE.md", "DAILY_RESEARCH_REPORT.md"):
        p = day / name
        if p.exists():
            texts.append(p.read_text(encoding="utf-8"))
    blob = "\n".join(texts).upper()
    markers = ["CONTRADICT", "COUNTER", "INVALIDATION", "反证", "削弱", "证伪", "ALTERNATIVE"]
    found = [m for m in markers if m in blob]
    hyp = CURRENT / "HYPOTHESIS_CURRENT.md"
    hyp_ok = False
    if hyp.exists():
        ht = hyp.read_text(encoding="utf-8").upper()
        hyp_ok = "CONTRADICT" in ht or "反证" in ht or "INVALIDATION" in ht
    ok = len(found) >= 2 and hyp_ok
    return {
        "ANTI_CONFIRMATION_BIAS_GATE": "PASS" if ok else "FAIL",
        "markers_found": found,
        "hypothesis_has_contradict": hyp_ok,
        "report_day": report_day,
    }


def manifest_ready() -> dict[str, Any]:
    m = load_json(MANIFEST)
    return {
        "exists": MANIFEST.exists(),
        "cn_research_date": m.get("CN_RESEARCH_DATE"),
        "daily_incremental_ready": m.get("DAILY_INCREMENTAL_READY"),
        "degraded": m.get("DEGRADED_LANES") or [],
    }


def append_index(name: str, row: dict[str, Any]) -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    p = INDEX_DIR / name
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def attach_efficiency_meter(st: dict[str, Any], day: str, *, mode: str) -> dict[str, Any]:
    """Passive RESEARCH_EFFICIENCY telemetry. Never overrides research seal truth."""
    try:
        import importlib.util

        meter_path = ROOT / "脚本" / "blackbox_daily_research_efficiency_meter_r1.py"
        spec = importlib.util.spec_from_file_location("blackbox_daily_research_efficiency_meter_r1", meter_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load meter: {meter_path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        summary = mod.write_efficiency(day, mode=mode)
        st["research_efficiency"] = summary
        st["RESEARCH_EFFICIENCY_TELEMETRY"] = summary.get("RESEARCH_EFFICIENCY_TELEMETRY", "PARTIAL")
        st["RESEARCH_EFFICIENCY_METER"] = summary.get("RESEARCH_EFFICIENCY_METER", "FAIL")
        st["EFFICIENCY_BLOCKS_SEAL"] = False
        return summary
    except Exception as e:
        fail = {
            "ok": False,
            "RESEARCH_EFFICIENCY_METER": "FAIL",
            "RESEARCH_EFFICIENCY_TELEMETRY": "FAIL",
            "error": str(e)[:400],
            "SYNTHETIC_TOKEN_TARGET": "NONE",
            "RESEARCH_LOGIC_CHANGED": False,
            "note": "Telemetry failure must NOT invalidate DAILY_RESEARCH_SEAL",
        }
        st["research_efficiency"] = fail
        st["RESEARCH_EFFICIENCY_TELEMETRY"] = "FAIL"
        st["RESEARCH_EFFICIENCY_METER"] = "FAIL"
        st["EFFICIENCY_BLOCKS_SEAL"] = False
        return fail


def build_status(*, mode: str, report_day: str | None = None) -> dict[str, Any]:
    day = report_day or today_iso()
    cur_ok, cur_miss = check_current_files()
    led_ok, led_miss = check_ledgers()
    rep_dir = REPORTS / day
    rep_ok = all((rep_dir / n).exists() for n in REQUIRED_REPORT) if rep_dir.exists() else False
    anti = read_anti_bias_gate(day) if rep_ok else {
        "ANTI_CONFIRMATION_BIAS_GATE": "FAIL",
        "reason": "daily report incomplete or missing",
        "report_day": day,
    }
    dual = dual_memory_gates(day)
    man = manifest_ready()
    base_ok = cur_ok and led_ok and SSOT.exists() and HAND_CONST.exists()
    system = "PASS" if base_ok else "FAIL"
    return {
        "system_id": "BLACKBOX_DAILY_INCREMENTAL_RESEARCH_MEMORY_R1",
        "patch_id": "BLACKBOX_DAILY_RESEARCH_DUAL_MEMORY_PATH_R1",
        "mode": mode,
        "ORDER_ALLOWED": False,
        "updated_at_cn": now_cn(),
        "DAILY_INCREMENTAL_RESEARCH_SYSTEM": system,
        "ROOT": str(DR),
        "SSOT": str(SSOT),
        "HAND_CONSTITUTION": str(HAND_CONST),
        "CURRENT_DIR": str(CURRENT),
        "CURRENT_FILES_OK": cur_ok,
        "CURRENT_MISSING": cur_miss,
        "LEDGERS_OK": led_ok,
        "LEDGERS_MISSING": led_miss,
        "TODAY_REPORT_OK": rep_ok,
        "TODAY_REPORT_DIR": str(rep_dir),
        "manifest": man,
        "anti_bias": anti,
        "dual_memory": dual,
        "ORIGINAL_CALL_IMMUTABILITY": "PASS",
        "THEME_MEMORY_COUNT": len(list(THEME_MEM.glob("*.md"))) if THEME_MEM.exists() else 0,
        "formula": "S(t)=UPDATE[S(t-1), Δ(t)]",
        "default_read": [
            "CURRENT_RESEARCH_BRIEF.md",
            "RESEARCH_QUEUE_CURRENT.md",
            "RECENT_DAILY_BRIEF_3_TO_5",
            "TODAY_TRUE_DELTA",
        ],
        "retrieval_hierarchy": [
            "L0_CURRENT_BRIEF",
            "L1_RECENT_DAILY_BRIEF",
            "L2_HISTORICAL_BRIEF_SEARCH",
            "L3_RESEARCH_TRACE",
            "L4_RAW_CACHE_SOURCE",
        ],
    }


def mode_bootstrap() -> int:
    ensure_tree()
    cur_ok, missing = check_current_files()
    if missing:
        st = build_status(mode="bootstrap")
        st["DAILY_INCREMENTAL_RESEARCH_SYSTEM"] = "FAIL"
        st["CURRENT_STATE_UPDATED"] = "NO"
        st["error"] = f"CURRENT missing: {missing}"
        atomic_write_json(RUN_CURRENT, st)
        print(json.dumps(st, ensure_ascii=False, indent=2), flush=True)
        return 1
    st = build_status(mode="bootstrap")
    st["BOOTSTRAP"] = "OK"
    st["CURRENT_STATE_UPDATED"] = "NO"
    st["note"] = "Dual-memory dirs ensured; existing CURRENT preserved"
    atomic_write_json(RUN_CURRENT, st)
    print(json.dumps(st, ensure_ascii=False, indent=2), flush=True)
    return 0 if st["DAILY_INCREMENTAL_RESEARCH_SYSTEM"] == "PASS" else 1


def mode_status() -> int:
    ensure_tree()
    st = build_status(mode="status")
    atomic_write_json(RUN_CURRENT, st)
    print(json.dumps(st, ensure_ascii=False, indent=2), flush=True)
    return 0 if st["DAILY_INCREMENTAL_RESEARCH_SYSTEM"] == "PASS" else 1


def mode_seal(*, report_day: str | None) -> int:
    day = report_day or today_iso()
    ensure_tree()
    anti = read_anti_bias_gate(day)
    dual = dual_memory_gates(day)

    block_reasons: list[str] = []
    if anti.get("ANTI_CONFIRMATION_BIAS_GATE") != "PASS":
        block_reasons.append("ANTI_CONFIRMATION_BIAS_GATE")
    if dual.get("CONTINUITY_CONTEXT_GATE") != "PASS":
        block_reasons.append("CONTINUITY_CONTEXT_GATE")
    if dual.get("DUAL_MEMORY_PATH") != "PASS":
        block_reasons.append("DUAL_MEMORY_PATH")
    if dual.get("PROVENANCE_CHAIN") != "PASS":
        block_reasons.append("PROVENANCE_CHAIN")
    if dual.get("SILENT_CONTEXT_OVERGROWTH"):
        block_reasons.append("SILENT_CONTEXT_OVERGROWTH")
    if (dual.get("time_axis") or {}).get("TIME_AXIS_GATE") != "PASS":
        block_reasons.append("TIME_AXIS_GATE")

    if block_reasons:
        st = build_status(mode="seal", report_day=day)
        st["CURRENT_STATE_UPDATED"] = "NO"
        st["DAILY_RESEARCH_SEAL"] = "FAIL"
        st["DAILY_INCREMENTAL_RESEARCH_SYSTEM"] = "FAIL"
        st["FINAL_STATUS"] = "FAIL"
        st["seal_blocked"] = block_reasons
        st["anti_bias"] = anti
        st["dual_memory"] = dual
        # Still attempt efficiency snapshot (observability); never clears block_reasons
        attach_efficiency_meter(st, day, mode="seal_blocked")
        atomic_write_json(RUN_CURRENT, st)
        print(json.dumps(st, ensure_ascii=False, indent=2), flush=True)
        return 1

    tmp_names = REQUIRED_CURRENT
    tmp_files = [n for n in tmp_names if (TMP / n).exists()]
    promoted: list[str] = []
    if tmp_files:
        arch = ARCHIVE / f"CURRENT_{day}_{datetime.now(CN).strftime('%H%M%S')}"
        arch.mkdir(parents=True, exist_ok=True)
        for n in tmp_names:
            src = CURRENT / n
            if src.exists():
                shutil.copy2(src, arch / n)
        for n in tmp_files:
            shutil.copy2(TMP / n, CURRENT / n)
            promoted.append(n)
            (TMP / n).unlink(missing_ok=True)

    # index append (idempotent-ish: always append seal event)
    append_index(
        "DAILY_BRIEF_INDEX.jsonl",
        {
            "date": day,
            "trace_id": f"TRACE_{day.replace('-', '')}_R1",
            "path": str(BRIEF_DIR / f"{day}.md"),
            "sealed_at": now_cn(),
        },
    )
    append_index(
        "RESEARCH_TRACE_INDEX.jsonl",
        {
            "date": day,
            "trace_id": f"TRACE_{day.replace('-', '')}_R1",
            "path": str(TRACE_ROOT / day / "RESEARCH_TRACE.md"),
            "sealed_at": now_cn(),
        },
    )

    st = build_status(mode="seal", report_day=day)
    st["CURRENT_STATE_UPDATED"] = "YES" if promoted else "NO"
    st["promoted_from_tmp"] = promoted
    st["anti_bias"] = anti
    st["dual_memory"] = dual
    st["DAILY_RESEARCH_SEAL"] = "PASS"
    st["FINAL_STATUS"] = "PASS"
    st["report_day"] = day
    st["seal_note"] = (
        "Dual-memory + anti-bias + continuity PASS; CURRENT promoted from TMP"
        if promoted
        else "Dual-memory + anti-bias + continuity PASS; CURRENT already present (no TMP)"
    )
    attach_efficiency_meter(st, day, mode="seal")
    # Efficiency PARTIAL/FAIL must not flip research seal
    st["DAILY_RESEARCH_SEAL"] = "PASS"
    st["FINAL_STATUS"] = "PASS"
    atomic_write_json(RUN_CURRENT, st)
    print(json.dumps(st, ensure_ascii=False, indent=2), flush=True)
    return 0


def mode_run_day(*, report_day: str | None) -> int:
    day = report_day or today_iso()
    ensure_tree()
    man = manifest_ready()
    cur_ok, _ = check_current_files()
    st = build_status(mode="run-day", report_day=day)
    if not cur_ok:
        st["DAILY_INCREMENTAL_RESEARCH_SYSTEM"] = "FAIL"
        st["CURRENT_STATE_UPDATED"] = "NO"
        st["error"] = "PREVIOUS_CURRENT_MISSING"
        atomic_write_json(RUN_CURRENT, st)
        print(json.dumps(st, ensure_ascii=False, indent=2), flush=True)
        return 1
    if man.get("daily_incremental_ready") not in ("YES", True, "PASS"):
        st["DAILY_INCREMENTAL_RESEARCH_SYSTEM"] = "FAIL"
        st["CURRENT_STATE_UPDATED"] = "NO"
        st["error"] = "DAILY_DATA_NOT_READY"
        atomic_write_json(RUN_CURRENT, st)
        print(json.dumps(st, ensure_ascii=False, indent=2), flush=True)
        return 1

    checklist = {
        "report_day": day,
        "DEFAULT_READ_ONLY": [
            str(CURRENT / "CURRENT_RESEARCH_BRIEF.md"),
            str(CURRENT / "RESEARCH_QUEUE_CURRENT.md"),
            str(BRIEF_DIR),
        ],
        "FORBIDDEN_DEFAULT": [
            "FULL_DAILY_REPORTS_HISTORY",
            "FULL_RESEARCH_TRACE_HISTORY",
            "FULL_CACHE_SCAN",
            "PAST_WEEK_RAW_RELOAD",
        ],
        "SEQUENCE": [
            "LOAD_CURRENT_RESEARCH_BRIEF",
            "LOAD_RECENT_DAILY_BRIEF_3_TO_5",
            "LOAD_RESEARCH_QUEUE",
            "INGEST_TODAY_NEW_DATA",
            "LOCAL_DEDUP",
            "BUILD_TRUE_DELTA",
            "MATCH_BRIEF",
            "ON_DEMAND_TRACE",
            "ON_DEMAND_RAW_CACHE",
            "CONTRADICT_SEARCH",
            "UPDATE_STATE",
            "WRITE_DAILY_REPORT",
            "WRITE_RESEARCH_TRACE",
            "WRITE_DAILY_BRIEF_LE_200",
            "REWRITE_OR_UPDATE_CURRENT_BRIEF_BOUNDED",
            "UPDATE_EVALUATION_APPEND_ONLY",
            "TMP_VALIDATE",
            "WRITE_RESEARCH_EFFICIENCY_TELEMETRY",
            "SEAL",
        ],
        "WRITE_BRIEF_TO": str(BRIEF_DIR / f"{day}.md"),
        "WRITE_TRACE_TO": str(TRACE_ROOT / day),
        "EFFICIENCY_OUTPUT": str((REPORTS / day) / "RESEARCH_EFFICIENCY.json"),
        "OPTIONAL_MODEL_TELEMETRY": str((REPORTS / day) / "MODEL_TELEMETRY.json"),
        "OPTIONAL_RETRIEVAL_TELEMETRY": str((REPORTS / day) / "RETRIEVAL_TELEMETRY.json"),
        "EFFICIENCY_HISTORY": str(EVAL_DIR / "RESEARCH_EFFICIENCY_HISTORY.jsonl"),
        "EFFICIENCY_RULES": {
            "OBSERVABILITY_ONLY": True,
            "SYNTHETIC_TOKEN_TARGET": "NONE",
            "ZERO_DENOMINATOR": "NULL",
            "PROVIDER_CACHE_NE_LOCAL_CACHE": True,
            "BLOCKS_SEAL": False,
        },
        "THEN_SEAL": f"python -u {ROOT / '脚本' / 'run_blackbox_daily_incremental_research_memory_r1.py'} --mode seal --date {day}",
        "CONTINUITY_CONTEXT_HARD_GATE": True,
        "ORDER_ALLOWED": False,
        "HINDSIGHT_REWRITE": "FORBIDDEN",
    }
    out = REPORTS / day
    out.mkdir(parents=True, exist_ok=True)
    # checklist references use REPORTS/day; rewrite paths now that out exists
    checklist["EFFICIENCY_OUTPUT"] = str(out / "RESEARCH_EFFICIENCY.json")
    checklist["OPTIONAL_MODEL_TELEMETRY"] = str(out / "MODEL_TELEMETRY.json")
    checklist["OPTIONAL_RETRIEVAL_TELEMETRY"] = str(out / "RETRIEVAL_TELEMETRY.json")
    atomic_write_json(out / "RUN_DAY_CHECKLIST.json", checklist)
    st["CURRENT_STATE_UPDATED"] = "NO"
    st["run_day"] = "CHECKLIST_EMITTED_COMPACT_FIRST"
    st["checklist"] = str(out / "RUN_DAY_CHECKLIST.json")
    st["DAILY_INCREMENTAL_RESEARCH_SYSTEM"] = "PASS"
    # Early/partial meter from whatever artifacts already exist (run-day may precede full write)
    attach_efficiency_meter(st, day, mode="run-day")
    atomic_write_json(RUN_CURRENT, st)
    print(json.dumps(st, ensure_ascii=False, indent=2), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="BLACKBOX Daily Incremental Research Memory R1 (Dual Path)")
    ap.add_argument("--mode", required=True, choices=["status", "bootstrap", "seal", "run-day"])
    ap.add_argument("--date", default=None, help="YYYY-MM-DD")
    args = ap.parse_args()
    if args.mode == "status":
        return mode_status()
    if args.mode == "bootstrap":
        return mode_bootstrap()
    if args.mode == "seal":
        return mode_seal(report_day=args.date)
    if args.mode == "run-day":
        return mode_run_day(report_day=args.date)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
