# -*- coding: utf-8 -*-
"""Strict V3 tests — resolver coverage_ready + FULL_HISTORY evidence (1950)."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import traceback
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

CODE = Path(__file__).resolve().parents[1] / "code_v3"
ROOT = Path(r"E:\BLACKBOX")
OUT = Path(__file__).resolve().parents[1] / "TEST_RESULTS_V3.json"
sys.path = [str(CODE)] + [p for p in sys.path if Path(p).resolve() != (ROOT / "脚本").resolve()]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _write_parquet(fp: Path, dates: list[str]) -> None:
    table = pa.table({"date": dates, "code": ["000001.XSHE"] * len(dates), "close": [1.0] * len(dates)})
    fp.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, fp)


def main() -> int:
    results: dict = {
        "task_id": "BLACKBOX_COVERAGE_V2_REVIEW_20261020_1950",
        "parent": "BLACKBOX_COVERAGE_RECONSTRUCTION_CANDIDATE_20261020_1925",
        "python": sys.version,
        "code_dir": str(CODE),
        "tests": {},
        "status": "RUNNING",
    }
    try:
        import blackbox_data_coverage_common_r1 as common
        import blackbox_cache_coverage_non_regression_gate_r1 as gate_mod
        import blackbox_data_access_resolver_r1 as resolver

        results["loaded"] = {
            "common_file": common.__file__,
            "gate_file": gate_mod.__file__,
            "resolver_file": resolver.__file__,
            "common_sha256": sha256(Path(common.__file__)),
            "gate_sha256": sha256(Path(gate_mod.__file__)),
            "resolver_sha256": sha256(Path(resolver.__file__)),
            "in_code_v3": "code_v3" in str(common.__file__).replace("\\", "/"),
        }
        assert results["loaded"]["in_code_v3"]

        # --- retain V2 date-loss gate ---
        def facts(ds):
            return {
                "exists": True,
                "coverage_extract_status": "OK",
                "errors": [],
                "dates": ds,
                "date_set": set(ds),
                "distinct_dates": len(ds),
                "min_date": min(ds),
                "max_date": max(ds),
                "year_slices": ["year=2026"],
                "supported_product": True,
                "coverage_mode": "DAILY_HISTORY",
            }

        with patch.object(gate_mod, "_product_cov", side_effect=[facts(["2026-09-01", "2026-09-02"]), facts(["2026-09-01"])]):
            g = gate_mod.gate("p", "c", ["STOCK_DAILY_PIT_R1"])
        results["tests"]["gate_date_loss_still_rejects"] = {
            "PASS": g["CACHE_RELEASE_PUBLISHABLE"] is False,
            "lost_count": g["details"]["STOCK_DAILY_PIT_R1"].get("lost_count"),
        }

        # --- bad partition extract ---
        with tempfile.TemporaryDirectory() as td:
            prod = Path(td) / "STOCK_DAILY_PIT_R1"
            _write_parquet(prod / "year=2026" / "good.parquet", ["2026-09-01", "2026-09-02"])
            (prod / "year=2026" / "bad.parquet").write_bytes(b"not-parquet")
            cov = common.product_date_coverage(prod, "STOCK_DAILY_PIT_R1")
            results["tests"]["extract_bad_partition_unverifiable"] = {
                "PASS": cov["coverage_extract_status"] == "UNVERIFIABLE",
                "status": cov["coverage_extract_status"],
            }

        # --- sparse 100 dates across years ≠ FULL_HISTORY ---
        sparse = {
            "exists": True,
            "coverage_extract_status": "OK",
            "errors": [],
            "distinct_dates": 100,
            "min_date": "2014-01-02",
            "max_date": "2026-09-24",
            "year_slices": ["year=2014", "year=2026"],
            "dates": [f"2014-01-{(i%20)+1:02d}" for i in range(50)] + [f"2026-09-{(i%20)+1:02d}" for i in range(50)],
        }
        mode_sparse = common.infer_mode_for_product("STOCK_DAILY_PIT_R1", sparse)
        results["tests"]["sparse_100_not_full_history"] = {
            "PASS": mode_sparse != "FULL_HISTORY",
            "mode": mode_sparse,
        }

        # --- resolver A: UNVERIFIABLE + subset covering window → coverage_ready false ---
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pid = "STOCK_DAILY_PIT_R1"
            (root / pid).mkdir()
            fake_cov = {
                "exists": True,
                "coverage_extract_status": "UNVERIFIABLE",
                "errors": ["bad.parquet:OSError"],
                "dates": ["2026-09-01", "2026-09-02"],
                "distinct_dates": 2,
                "min_date": "2026-09-01",
                "max_date": "2026-09-02",
                "year_slices": ["year=2026"],
                "supported_product": True,
            }
            currents = {
                "catalog": pd.DataFrame([{"product_id": pid, "asset_type": "STOCK", "description": "t"}]),
                "cache_release_root": str(root),
                "_request_start_date": "2026-09-01",
                "_request_end_date": "2026-09-02",
            }
            with patch.object(common, "product_date_coverage", return_value=fake_cov), patch.object(
                common, "load_trade_calendar", return_value=[date(2026, 9, 1), date(2026, 9, 2)]
            ), patch.object(common, "infer_mode_for_product", return_value="UNKNOWN_STOP"):
                # force local import to see patched module attributes
                import importlib

                importlib.reload(common)
                # re-patch after reload
                with patch.object(common, "product_date_coverage", return_value=fake_cov), patch.object(
                    common, "load_trade_calendar", return_value=[date(2026, 9, 1), date(2026, 9, 2)]
                ):
                    # ensure resolver imports from CODE
                    sys.path.insert(0, str(CODE))
                    r = resolver.resolve_product(pid, None, None, currents)
            results["tests"]["resolver_unverifiable_not_ready"] = {
                "PASS": r.get("coverage_ready") is False and r.get("coverage_mode") == "UNKNOWN_STOP",
                "coverage_ready": r.get("coverage_ready"),
                "coverage_mode": r.get("coverage_mode"),
                "result_status": r.get("result_status"),
                "resolved": r.get("resolved"),
            }

        # --- resolver B: unsupported CORP no window → coverage_ready false ---
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pid = "CORP_SHAREHOLDER_TOP10_PIT_R1"
            (root / pid).mkdir()
            currents = {
                "catalog": pd.DataFrame([{"product_id": pid, "asset_type": "STOCK", "description": "t"}]),
                "cache_release_root": str(root),
            }
            r = resolver.resolve_product(pid, None, None, currents)
            results["tests"]["resolver_unsupported_no_window_not_ready"] = {
                "PASS": r.get("coverage_ready") is False and r.get("coverage_mode") == "UNKNOWN_STOP",
                "coverage_ready": r.get("coverage_ready"),
                "coverage_mode": r.get("coverage_mode"),
                "resolved": r.get("resolved"),
                "extract": currents.get("_coverage_extract_status"),
            }

        # --- real resolve windows (must not treat exception as PASS) ---
        currents = resolver.read_currents()
        assert currents.get("authority_ready"), currents.get("errors")

        currents["_request_start_date"] = "2026-09-01"
        currents["_request_end_date"] = "2026-09-10"
        r_gap = resolver.resolve_product("STOCK_DAILY_PIT_R1", currents.get("cache_asof"), None, currents)
        results["tests"]["resolver_window_0901_0910_not_complete"] = {
            "PASS": (
                currents.get("_coverage_error") is None
                and r_gap.get("coverage_extract_status", currents.get("_coverage_extract_status")) in (None, "OK")
                or currents.get("_coverage_extract_status") == "OK"
            )
            and r_gap.get("coverage_ready") is False
            and "2026-09-01" in (r_gap.get("missing_trade_days") or []),
            "coverage_ready": r_gap.get("coverage_ready"),
            "coverage_mode": r_gap.get("coverage_mode"),
            "missing": r_gap.get("missing_trade_days"),
            "extract_status": currents.get("_coverage_extract_status"),
            "error": currents.get("_coverage_error"),
        }
        # tighten PASS: extract OK + not ready + missing 09-01
        results["tests"]["resolver_window_0901_0910_not_complete"]["PASS"] = (
            currents.get("_coverage_extract_status") == "OK"
            and not currents.get("_coverage_error")
            and r_gap.get("coverage_ready") is False
            and "2026-09-01" in (r_gap.get("missing_trade_days") or [])
        )

        currents2 = resolver.read_currents()
        currents2["_request_start_date"] = "2026-09-02"
        currents2["_request_end_date"] = "2026-09-10"
        r_ok = resolver.resolve_product("STOCK_DAILY_PIT_R1", currents2.get("cache_asof"), None, currents2)
        results["tests"]["resolver_window_0902_0910_ready"] = {
            "PASS": (
                currents2.get("_coverage_extract_status") == "OK"
                and not currents2.get("_coverage_error")
                and r_ok.get("coverage_ready") is True
                and r_ok.get("coverage_mode") in ("FULL_HISTORY", "DAILY_HISTORY")
                and (r_ok.get("missing_trade_days") in ([], None))
            ),
            "coverage_ready": r_ok.get("coverage_ready"),
            "coverage_mode": r_ok.get("coverage_mode"),
            "missing": r_ok.get("missing_trade_days"),
            "extract_status": currents2.get("_coverage_extract_status"),
            "error": currents2.get("_coverage_error"),
        }

        # cross-year 3 years middle
        raw = common.raw_stock_daily_dates("2023-12-20", "2025-01-10")
        results["tests"]["cross_year_three_years"] = {
            "PASS": set(raw.get("years_scanned") or []) >= {2023, 2024, 2025},
            "years_scanned": raw.get("years_scanned"),
            "status": raw.get("status"),
        }

        # calendar authority: must match CURRENT asof or ledger — not silent failure
        cal = common.find_calendar_trade_days()
        asof = str(common.cache_current().get("asof") or "").replace("-", "")[:8]
        results["tests"]["calendar_authority_explicit"] = {
            "PASS": asof in str(cal) or "CALENDAR_TRADE_DAYS" in str(cal),
            "path": str(cal),
            "cache_asof": asof,
        }

        # NEVER unknown+ready
        results["tests"]["invariant_no_unknown_with_ready"] = {
            "PASS": not (
                r_gap.get("coverage_mode") == "UNKNOWN_STOP" and r_gap.get("coverage_ready") is True
            )
            and not (r.get("coverage_mode") == "UNKNOWN_STOP" and r.get("coverage_ready") is True),
        }

        fails = [k for k, v in results["tests"].items() if not v.get("PASS")]
        results["failed"] = fails
        results["all_pass"] = not fails
        results["status"] = "CANDIDATE_V3_READY_FOR_REVIEW" if not fails else "BLOCKED_WITH_SPECIFIC_GAP"
        results["review_points"] = {
            "1_resolver_ready_gate": results["tests"]["resolver_unverifiable_not_ready"]["PASS"]
            and results["tests"]["resolver_unsupported_no_window_not_ready"]["PASS"],
            "2_full_history_evidence": results["tests"]["sparse_100_not_full_history"]["PASS"],
            "3_real_windows": results["tests"]["resolver_window_0901_0910_not_complete"]["PASS"]
            and results["tests"]["resolver_window_0902_0910_ready"]["PASS"],
        }
    except Exception as exc:  # noqa: BLE001
        results["status"] = "BLOCKED_WITH_SPECIFIC_GAP"
        results["error"] = f"{type(exc).__name__}: {exc}"
        results["traceback"] = traceback.format_exc()
        results["all_pass"] = False

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: results.get(k) for k in ("status", "all_pass", "failed", "loaded", "review_points", "error")}, ensure_ascii=False, indent=2, default=str))
    print(f"WROTE {OUT}")
    return 0 if results.get("all_pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
