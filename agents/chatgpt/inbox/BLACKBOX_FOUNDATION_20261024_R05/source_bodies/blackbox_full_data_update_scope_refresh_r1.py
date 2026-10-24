# -*- coding: utf-8 -*-
"""Refresh BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json from live CURRENT only.

Summary is control-plane metadata. It is not data-readiness authority.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _base import ROOT, OK  # noqa: E402
from blackbox_daily_increment_common_r1 import (  # noqa: E402
    CACHE_PTR,
    CLEAN_PTR,
    FACTS,
    OPS,
    SCOPE,
    now_cn,
    summary_stale_gate,
    wjson,
)


def refresh_scope_from_live() -> dict:
    live_cache = json.loads(CACHE_PTR.read_text(encoding="utf-8"))
    live_clean = json.loads(CLEAN_PTR.read_text(encoding="utf-8"))
    facts = json.loads(FACTS.read_text(encoding="utf-8")) if FACTS.exists() else {}
    ops = json.loads(OPS.read_text(encoding="utf-8")) if OPS.exists() else {}
    idx = Path(r"E:\BLACKBOX\数据\清洗成品\CURRENT_INDEX_MINUTE_ALIGN_RELEASE.json")
    idx_id = json.loads(idx.read_text(encoding="utf-8")).get("release_id") if idx.exists() else None
    old = json.loads(SCOPE.read_text(encoding="utf-8")) if SCOPE.exists() else {}
    asof = str(live_cache.get("asof") or live_clean.get("cleaning_as_of") or "")
    new = dict(old)
    r2 = json.loads((ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_FULL_DATA_UPDATE_SCOPE_R2.json").read_text(encoding="utf-8"))
    new["pipeline"] = r2.get("pipeline") or new.get("pipeline")
    new.update({
        "system_generation_id": live_cache.get("cache_release_id"),
        "cleaning_release": live_clean.get("release_id"),
        "current_cleaning_release_id": live_clean.get("release_id"),
        "cache_release": live_cache.get("cache_release_id"),
        "cache_release_id": live_cache.get("cache_release_id"),
        "source_cleaning_release": live_cache.get("source_cleaning_release"),
        "data_asof": asof,
        "operational_readiness": ops.get("R20_20260817_OPERATIONAL_READINESS") or ops.get("operational_readiness"),
        "capability_generation_id": facts.get("SYSTEM_GENERATION_ID"),
        "index_minute_align_release_id": idx_id,
        "INDEX_DAILY_R1": live_cache.get("INDEX_DAILY_R1") or "NON_BLOCKING_KNOWN_EXCEPTION",
        "summary_derived_from": "LIVE_CURRENT",
        "NOT_AUTHORITY_FOR_DATA_READINESS": False,
        "generated_at_cn": now_cn(),
        "summary_refresh_rule": "blackbox_full_data_update_scope_refresh_r1.py",
    })
    gate = summary_stale_gate(new, live_cache, live_clean)
    new["SUMMARY_STALE"] = gate["SUMMARY_STALE"]
    new["NOT_AUTHORITY_FOR_DATA_READINESS"] = gate["NOT_AUTHORITY_FOR_DATA_READINESS"]
    wjson(SCOPE, new)
    child = ROOT / "运行" / "BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_WITH_SW_L123_CACHE_CURRENT.json"
    if child.exists():
        cj = json.loads(child.read_text(encoding="utf-8"))
        cj["asof"] = asof
        cj["current_cleaning_release_id"] = live_clean.get("release_id")
        cj["cache_release_id"] = live_cache.get("cache_release_id")
        cj["source_cleaning_release"] = live_cache.get("source_cleaning_release")
        cj["generated_at_cn"] = now_cn()
        wjson(child, cj)
    return new


def main() -> int:
    out = refresh_scope_from_live()
    print(json.dumps({
        "cleaning_release": out.get("cleaning_release"),
        "cache_release": out.get("cache_release"),
        "data_asof": out.get("data_asof"),
        "SUMMARY_STALE": out.get("SUMMARY_STALE"),
        "operational_readiness": out.get("operational_readiness"),
    }, ensure_ascii=False, indent=2))
    return OK


if __name__ == "__main__":
    raise SystemExit(main())
