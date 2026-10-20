# -*- coding: utf-8 -*-
"""Strict V4 tests — bounded query + no self-proof FULL_HISTORY (2005)."""
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

CODE = Path(__file__).resolve().parents[1] / "code_v4"
ROOT = Path(r"E:\BLACKBOX")
OUT = Path(__file__).resolve().parents[1] / "TEST_RESULTS_V4.json"
sys.path = [str(CODE)] + [p for p in sys.path if Path(p).resolve() != (ROOT / "脚本").resolve()]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _write_parquet(fp: Path, dates: list[str]) -> None:
    table = pa.table({"date": dates, "code": ["000001.XSHE"] * len(dates), "close": [1.0] * len(dates)})
    fp.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, fp)


def main() -> int:
    results: dict = {
        "task_id": "BLACKBOX_COVERAGE_BOUNDED_QUERY_REVIEW_20261020_2005",
        "parent": "BLACKBOX_COVERAGE_V2_REVIEW_20261020_1950",
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
            "in_code_v4": "code_v4" in str(common.__file__).replace("\\", "/"),
        }
        assert results["loaded"]["in_code_v4"]

        # --- gate self_test (all items must PASS; do not drop) ---
        st = gate_mod.self_test()
        results["tests"]["gate_self_test_all"] = {
            "PASS": all(v.get("PASS") for v in st.values()),
            "items": {k: v.get("PASS") for k, v in st.items()},
            "detail": st,
        }

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

        with patch.object(
            gate_mod,
            "_product_cov",
            side_effect=[facts(["2026-09-01", "2026-09-02"]), facts(["2026-09-01"])],
        ):
            g = gate_mod.gate("p", "c", ["STOCK_DAILY_PIT_R1"])
        results["tests"]["gate_date_loss_still_rejects"] = {
            "PASS": g["CACHE_RELEASE_PUBLISHABLE"] is False,
            "lost_count": g["details"]["STOCK_DAILY_PIT_R1"].get("lost_count"),
        }

        # set retention OK but FULL unproven → not publishable
        with patch.object(
            gate_mod,
            "_product_cov",
            side_effect=[
                facts(["2026-09-01", "2026-09-02"]),
                facts(["2026-09-01", "2026-09-02"]),
            ],
        ):
            g2 = gate_mod.gate("p", "c", ["STOCK_DAILY_PIT_R1"])
        results["tests"]["gate_set_ok_full_unproven_not_publishable"] = {
            "PASS": (
                g2.get("SET_RETENTION_OK") is True
                and g2.get("CACHE_RELEASE_PUBLISHABLE") is False
                and "STOCK_DAILY_PIT_R1" in (g2.get("FULL_HISTORY_UNPROVEN") or [])
            ),
            "SET_RETENTION_OK": g2.get("SET_RETENTION_OK"),
            "CACHE_RELEASE_PUBLISHABLE": g2.get("CACHE_RELEASE_PUBLISHABLE"),
            "FULL_HISTORY_UNPROVEN": g2.get("FULL_HISTORY_UNPROVEN"),
            "GATE_STATUS": g2.get("GATE_STATUS"),
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

        # --- two days self-window complete ≠ FULL_HISTORY ---
        common.set_expected_range_authority("STOCK_DAILY_PIT_R1", None)
        two = {
            "exists": True,
            "coverage_extract_status": "OK",
            "errors": [],
            "distinct_dates": 2,
            "min_date": "2026-09-01",
            "max_date": "2026-09-02",
            "year_slices": ["year=2026"],
            "dates": ["2026-09-01", "2026-09-02"],
        }
        with patch.object(
            common, "load_trade_calendar", return_value=[date(2026, 9, 1), date(2026, 9, 2)]
        ):
            mode_two = common.infer_mode_for_product("STOCK_DAILY_PIT_R1", two)
        results["tests"]["two_days_self_window_not_full_history"] = {
            "PASS": mode_two != "FULL_HISTORY",
            "mode": mode_two,
        }

        # --- ROOT_REPRO: calendar OSError no window → not ready ---
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pid = "STOCK_DAILY_PIT_R1"
            (root / pid).mkdir()
            good = {
                "exists": True,
                "coverage_extract_status": "OK",
                "errors": [],
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
            }
            with patch.object(common, "product_date_coverage", return_value=good), patch.object(
                common, "load_trade_calendar", side_effect=OSError("calendar unavailable")
            ):
                # Without authority, infer returns DAILY_HISTORY without calling calendar.
                # Force authority so calendar path is exercised → UNKNOWN_STOP.
                common.set_expected_range_authority(
                    pid,
                    {
                        "product_id": pid,
                        "expected_start": "2026-09-01",
                        "expected_end": "2026-09-02",
                        "source": "test_fixture",
                        "version_or_asof": "V4",
                    },
                )
                r_cal = resolver.resolve_product(pid, None, None, currents)
            common.set_expected_range_authority(pid, None)
            results["tests"]["calendar_fail_no_window_not_ready"] = {
                "PASS": (
                    r_cal.get("coverage_ready") is False
                    and r_cal.get("historical_ready") is False
                    and r_cal.get("coverage_mode") == "UNKNOWN_STOP"
                    and bool(currents.get("_coverage_error"))
                ),
                "coverage_ready": r_cal.get("coverage_ready"),
                "historical_ready": r_cal.get("historical_ready"),
                "coverage_mode": r_cal.get("coverage_mode"),
                "coverage_error": currents.get("_coverage_error"),
            }

        # --- no window, no authority: DAILY_HISTORY must not be ready ---
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pid = "STOCK_DAILY_PIT_R1"
            (root / pid).mkdir()
            good = {
                "exists": True,
                "coverage_extract_status": "OK",
                "errors": [],
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
            }
            with patch.object(common, "product_date_coverage", return_value=good):
                r_nw = resolver.resolve_product(pid, None, None, currents)
            results["tests"]["no_window_daily_history_not_ready"] = {
                "PASS": (
                    r_nw.get("coverage_ready") is False
                    and r_nw.get("historical_ready") is False
                    and r_nw.get("coverage_mode") == "DAILY_HISTORY"
                    and r_nw.get("full_history_status") == "UNPROVEN"
                ),
                "coverage_ready": r_nw.get("coverage_ready"),
                "historical_ready": r_nw.get("historical_ready"),
                "coverage_mode": r_nw.get("coverage_mode"),
                "full_history_status": r_nw.get("full_history_status"),
                "coverage_scope": r_nw.get("coverage_scope"),
            }

        # --- one endpoint only ---
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pid = "STOCK_DAILY_PIT_R1"
            (root / pid).mkdir()
            good = {
                "exists": True,
                "coverage_extract_status": "OK",
                "errors": [],
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
            }
            with patch.object(common, "product_date_coverage", return_value=good):
                r_one = resolver.resolve_product(pid, None, None, currents)
            results["tests"]["one_endpoint_rejected"] = {
                "PASS": (
                    r_one.get("coverage_ready") is False
                    and currents.get("_coverage_error") == "BOUNDED_WINDOW_REQUIRES_BOTH_ENDPOINTS"
                ),
                "coverage_ready": r_one.get("coverage_ready"),
                "error": currents.get("_coverage_error"),
            }

        # --- bounded fixture window ready + scope note ---
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pid = "STOCK_DAILY_PIT_R1"
            (root / pid).mkdir()
            good = {
                "exists": True,
                "coverage_extract_status": "OK",
                "errors": [],
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
            with patch.object(common, "product_date_coverage", return_value=good), patch.object(
                common, "load_trade_calendar", return_value=[date(2026, 9, 1), date(2026, 9, 2)]
            ):
                r_b = resolver.resolve_product(pid, None, None, currents)
            results["tests"]["bounded_window_ready_with_scope"] = {
                "PASS": (
                    r_b.get("coverage_ready") is True
                    and r_b.get("coverage_scope") == "BOUNDED_WINDOW_VERIFIED"
                    and "非全历史" in str(r_b.get("coverage_scope_note") or "")
                    and r_b.get("historical_ready") is False
                ),
                "coverage_ready": r_b.get("coverage_ready"),
                "coverage_scope": r_b.get("coverage_scope"),
                "coverage_scope_note": r_b.get("coverage_scope_note"),
                "historical_ready": r_b.get("historical_ready"),
            }

        # --- calendar fail with window → not ready + error ---
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pid = "STOCK_DAILY_PIT_R1"
            (root / pid).mkdir()
            good = {
                "exists": True,
                "coverage_extract_status": "OK",
                "errors": [],
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
            with patch.object(common, "product_date_coverage", return_value=good), patch.object(
                common, "load_trade_calendar", side_effect=OSError("calendar unavailable")
            ):
                r_cw = resolver.resolve_product(pid, None, None, currents)
            results["tests"]["calendar_fail_with_window_not_ready"] = {
                "PASS": (
                    r_cw.get("coverage_ready") is False
                    and bool(currents.get("_coverage_error"))
                ),
                "coverage_ready": r_cw.get("coverage_ready"),
                "coverage_error": currents.get("_coverage_error"),
                "coverage_mode": r_cw.get("coverage_mode"),
            }

        # --- UNVERIFIABLE not ready ---
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
            ):
                r_u = resolver.resolve_product(pid, None, None, currents)
            results["tests"]["resolver_unverifiable_not_ready"] = {
                "PASS": r_u.get("coverage_ready") is False and r_u.get("coverage_mode") == "UNKNOWN_STOP",
                "coverage_ready": r_u.get("coverage_ready"),
                "coverage_mode": r_u.get("coverage_mode"),
            }

        # --- unsupported ---
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pid = "CORP_SHAREHOLDER_TOP10_PIT_R1"
            (root / pid).mkdir()
            currents = {
                "catalog": pd.DataFrame([{"product_id": pid, "asset_type": "STOCK", "description": "t"}]),
                "cache_release_root": str(root),
            }
            r_uns = resolver.resolve_product(pid, None, None, currents)
            results["tests"]["resolver_unsupported_no_window_not_ready"] = {
                "PASS": r_uns.get("coverage_ready") is False and r_uns.get("coverage_mode") == "UNKNOWN_STOP",
                "coverage_ready": r_uns.get("coverage_ready"),
                "coverage_mode": r_uns.get("coverage_mode"),
            }

        # --- real Windows windows (bounded capability) ---
        currents = resolver.read_currents()
        assert currents.get("authority_ready"), currents.get("errors")

        currents["_request_start_date"] = "2026-09-01"
        currents["_request_end_date"] = "2026-09-10"
        r_gap = resolver.resolve_product("STOCK_DAILY_PIT_R1", currents.get("cache_asof"), None, currents)
        results["tests"]["resolver_window_0901_0910_not_complete"] = {
            "PASS": (
                currents.get("_coverage_extract_status") == "OK"
                and not currents.get("_coverage_error")
                and r_gap.get("coverage_ready") is False
                and "2026-09-01" in (r_gap.get("missing_trade_days") or [])
            ),
            "coverage_ready": r_gap.get("coverage_ready"),
            "coverage_mode": r_gap.get("coverage_mode"),
            "missing": r_gap.get("missing_trade_days"),
            "extract_status": currents.get("_coverage_extract_status"),
            "error": currents.get("_coverage_error"),
        }

        currents2 = resolver.read_currents()
        currents2["_request_start_date"] = "2026-09-02"
        currents2["_request_end_date"] = "2026-09-10"
        r_ok = resolver.resolve_product("STOCK_DAILY_PIT_R1", currents2.get("cache_asof"), None, currents2)
        results["tests"]["resolver_window_0902_0910_ready"] = {
            "PASS": (
                currents2.get("_coverage_extract_status") == "OK"
                and not currents2.get("_coverage_error")
                and r_ok.get("coverage_ready") is True
                and r_ok.get("coverage_scope") == "BOUNDED_WINDOW_VERIFIED"
                and r_ok.get("historical_ready") is False
                and (r_ok.get("missing_trade_days") in ([], None))
            ),
            "coverage_ready": r_ok.get("coverage_ready"),
            "coverage_mode": r_ok.get("coverage_mode"),
            "coverage_scope": r_ok.get("coverage_scope"),
            "historical_ready": r_ok.get("historical_ready"),
            "missing": r_ok.get("missing_trade_days"),
            "extract_status": currents2.get("_coverage_extract_status"),
            "error": currents2.get("_coverage_error"),
        }

        # external authority fixture positive (not production ledger)
        auth_dates = ["2026-09-01", "2026-09-02"]
        common.set_expected_range_authority(
            "STOCK_DAILY_PIT_R1",
            {
                "product_id": "STOCK_DAILY_PIT_R1",
                "expected_start": "2026-09-01",
                "expected_end": "2026-09-02",
                "source": "external_temp_fixture",
                "version_or_asof": "V4_TEST",
            },
        )
        cov_auth = {
            "exists": True,
            "coverage_extract_status": "OK",
            "errors": [],
            "distinct_dates": 2,
            "min_date": "2026-09-01",
            "max_date": "2026-09-02",
            "year_slices": ["year=2026"],
            "dates": auth_dates,
        }
        with patch.object(
            common, "load_trade_calendar", return_value=[date(2026, 9, 1), date(2026, 9, 2)]
        ):
            mode_auth = common.infer_mode_for_product("STOCK_DAILY_PIT_R1", cov_auth)
        common.set_expected_range_authority("STOCK_DAILY_PIT_R1", None)
        results["tests"]["authority_fixture_can_prove_full_history"] = {
            "PASS": mode_auth == "FULL_HISTORY" and cov_auth.get("_full_history_status") == "PROVEN",
            "mode": mode_auth,
            "status": cov_auth.get("_full_history_status"),
        }

        fails = [k for k, v in results["tests"].items() if not v.get("PASS")]
        results["failed"] = fails
        results["all_pass"] = not fails
        results["status"] = (
            "CANDIDATE_V4_BOUNDED_QUERY_READY_FOR_REVIEW" if not fails else "BLOCKED_WITH_SPECIFIC_GAP"
        )
        results["review_points"] = {
            "A_no_self_proof_full_history": results["tests"]["two_days_self_window_not_full_history"]["PASS"],
            "B_full_unproven_explicit": results["tests"]["no_window_daily_history_not_ready"]["PASS"],
            "C_no_window_needs_range_proof": results["tests"]["no_window_daily_history_not_ready"]["PASS"],
            "D_bounded_window_ok": results["tests"]["bounded_window_ready_with_scope"]["PASS"]
            and results["tests"]["resolver_window_0902_0910_ready"]["PASS"],
            "E_calendar_errors_propagate": results["tests"]["calendar_fail_no_window_not_ready"]["PASS"]
            and results["tests"]["calendar_fail_with_window_not_ready"]["PASS"],
            "F_gate_set_vs_publishable": results["tests"]["gate_set_ok_full_unproven_not_publishable"]["PASS"],
            "self_test": results["tests"]["gate_self_test_all"]["PASS"],
        }
    except Exception as exc:  # noqa: BLE001
        results["status"] = "BLOCKED_WITH_SPECIFIC_GAP"
        results["error"] = f"{type(exc).__name__}: {exc}"
        results["traceback"] = traceback.format_exc()
        results["all_pass"] = False

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {k: results.get(k) for k in ("status", "all_pass", "failed", "loaded", "review_points", "error")},
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )
    print(f"WROTE {OUT}")
    return 0 if results.get("all_pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
