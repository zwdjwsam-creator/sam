# -*- coding: utf-8 -*-
"""BLACKBOX Data Coverage Diagnose CLI R1.

Usage:
  python blackbox_data_coverage_diagnose_r1.py --dataset STOCK_MINUTE_1M --start-date 2026-08-03 --end-date 2026-08-12
  python blackbox_data_coverage_diagnose_r1.py --dataset STOCK_DAILY --start-date 2026-06-01 --end-date 2026-08-11
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

CN_TZ = timezone(timedelta(hours=8))
MISSING_ENUM = [
    "OK_MULTI_PLANE",
    "PARTIAL_WINDOW_GAP",
    "TRUE_MISS_AFTER_ALL_PLANES",
    "ENVELOPE_REVIEW",
    "UNIFIED_PLANE_DIAGNOSE_FAIL",
    "UNKNOWN_STOP",
    "STOCK_DAILY_CLASSIFIER_UNAVAILABLE",
]


def now_cn() -> str:
    return datetime.now(CN_TZ).isoformat()


def main() -> int:
    ap = argparse.ArgumentParser(description="BLACKBOX DATA COVERAGE DIAGNOSIS R1")
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--start-date", required=True)
    ap.add_argument("--end-date", required=True)
    args = ap.parse_args()

    ds = args.dataset.strip().upper().replace("STOCK_DAILY_PIT_R1", "STOCK_DAILY")
    if ds in ("STOCK_DAILY", "STOCK_PRICE", "PRICE", "股票日线"):
        try:
            from blackbox_data_coverage_common_r1 import classify_stock_daily  # noqa: WPS433

            body = classify_stock_daily(args.start_date, args.end_date)
        except Exception as exc:  # noqa: BLE001
            body = {
                "dataset": args.dataset,
                "requested_start": args.start_date,
                "requested_end": args.end_date,
                "root_cause": "STOCK_DAILY_CLASSIFIER_UNAVAILABLE",
                "download_required": False,
                "action": "STOP_RESTORE_COVERAGE_COMMON_OR_USE_CACHE_RESOLVER",
                "authority_ready": False,
                "error": str(exc),
            }
    else:
        try:
            from blackbox_unified_market_data_plane_r1 import (  # noqa: WPS433
                diagnose as umdp_diagnose,
                normalize_product_id,
            )

            normalize_product_id(args.dataset)
            body = umdp_diagnose(args.dataset, args.start_date, args.end_date)
            body["authority_ready"] = True
            body["reader_status"] = "UNIFIED_MARKET_DATA_PLANE_R1"
        except KeyError:
            body = {
                "dataset": args.dataset,
                "requested_start": args.start_date,
                "requested_end": args.end_date,
                "root_cause": "UNKNOWN_STOP",
                "download_required": False,
                "action": "STOP_EXTEND_DIAGNOSER",
                "authority_ready": True,
                "note": "Use UNIFIED registry products or STOCK_DAILY.",
            }
        except Exception as exc:  # noqa: BLE001
            body = {
                "dataset": args.dataset,
                "requested_start": args.start_date,
                "requested_end": args.end_date,
                "root_cause": "UNIFIED_PLANE_DIAGNOSE_FAIL",
                "download_required": False,
                "action": "STOP_FIX_UNIFIED_PLANE",
                "authority_ready": False,
                "error": str(exc),
            }

    out = {
        "DATA_COVERAGE_DIAGNOSIS": True,
        "generated_at": now_cn(),
        "missing_enum_version": "R1",
        "allowed_root_causes": MISSING_ENUM,
        **body,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
