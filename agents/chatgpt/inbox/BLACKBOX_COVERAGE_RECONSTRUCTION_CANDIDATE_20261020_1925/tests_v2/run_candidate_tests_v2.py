# -*- coding: utf-8 -*-
"""Strict V2 tests for 1940 coverage candidate review fixes."""
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

CODE = Path(__file__).resolve().parents[1] / "code_v2"
ROOT = Path(r"E:\BLACKBOX")
OUT = Path(__file__).resolve().parents[1] / "TEST_RESULTS_V2.json"

sys.path = [str(CODE)] + [p for p in sys.path if Path(p).resolve() != (ROOT / "脚本").resolve()]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _write_parquet(fp: Path, dates: list[str], codes: list[str] | None = None) -> None:
    codes = codes or ["000001.XSHE"] * len(dates)
    table = pa.table({"date": dates, "code": codes, "close": [1.0] * len(dates)})
    fp.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, fp)


def _cov_ok(dates: list[str], exists: bool = True, status: str = "OK") -> dict:
    ds = sorted(dates)
    return {
        "product_id": "STOCK_DAILY_PIT_R1",
        "exists": exists,
        "coverage_mode": "FULL_HISTORY" if len(ds) >= 100 else ("INCREMENTAL_PATCH" if len(ds) == 1 else "DAILY_HISTORY_PARTIAL"),
        "min_date": ds[0] if ds else None,
        "max_date": ds[-1] if ds else None,
        "distinct_dates": len(ds),
        "coverage_extract_status": status if exists else "MISSING_PRODUCT",
        "dates": ds,
        "date_set": set(ds),
        "errors": [],
        "supported_product": True,
    }


def main() -> int:
    results: dict = {
        "task_id": "BLACKBOX_COVERAGE_CANDIDATE_REVIEW_20261020_1940",
        "parent": "BLACKBOX_COVERAGE_RECONSTRUCTION_CANDIDATE_20261020_1925",
        "python": sys.version,
        "code_dir": str(CODE),
        "tests": {},
        "review_points": {},
        "status": "RUNNING",
    }
    try:
        import blackbox_data_coverage_common_r1 as common
        import blackbox_cache_coverage_non_regression_gate_r1 as gate_mod

        results["loaded"] = {
            "common_file": common.__file__,
            "gate_file": gate_mod.__file__,
            "common_sha256": sha256(Path(common.__file__)),
            "gate_sha256": sha256(Path(gate_mod.__file__)),
            "in_code_v2": "code_v2" in str(common.__file__).replace("\\", "/"),
        }
        assert results["loaded"]["in_code_v2"]

        # --- R1 gate set semantics ---
        parent100 = [f"2026-01-{i:02d}" for i in range(1, 101)]
        # invalid calendar-ish strings ok for set logic unit test
        parent100 = [f"2020-01-{(i%28)+1:02d}" if i > 28 else f"2020-01-{i:02d}" for i in range(1, 101)]
        # simpler unique
        parent100 = [f"2018-{(i//28)+1:02d}-{(i%28)+1:02d}" for i in range(100)]
        child60 = parent100[:60]
        same_count_swap = parent100.copy()
        same_count_swap[50] = "2099-01-01"  # replace one internal date; count same

        cases = {
            "lost_40_must_reject": (_cov_ok(parent100), _cov_ok(child60), False),
            "same_count_changed_date_reject": (_cov_ok(parent100), _cov_ok(same_count_swap), False),
            "no_loss_allow": (_cov_ok(parent100), _cov_ok(parent100 + ["2021-06-01"]), True),
            "parent_missing_reject": (_cov_ok([], exists=False, status="MISSING_PRODUCT"), _cov_ok(parent100), False),
            "both_missing_reject": (
                _cov_ok([], exists=False, status="MISSING_PRODUCT"),
                _cov_ok([], exists=False, status="MISSING_PRODUCT"),
                False,
            ),
            "empty_products_reject": None,
        }
        for label, payload in cases.items():
            if label == "empty_products_reject":
                res = gate_mod.gate("p", "c", [])
                ok = res["CACHE_RELEASE_PUBLISHABLE"] is False
            else:
                p, c, expect_pub = payload
                with patch.object(gate_mod, "_product_cov", side_effect=[p, c]):
                    res = gate_mod.gate("p", "c", ["STOCK_DAILY_PIT_R1"])
                ok = res["CACHE_RELEASE_PUBLISHABLE"] is expect_pub
            results["tests"][f"gate_{label}"] = {
                "PASS": ok,
                "publishable": res.get("CACHE_RELEASE_PUBLISHABLE"),
                "status": res.get("GATE_STATUS"),
                "lost_count": (res.get("details") or {}).get("STOCK_DAILY_PIT_R1", {}).get("lost_count"),
                "reason": (res.get("details") or {}).get("STOCK_DAILY_PIT_R1", {}).get("reason"),
            }

        # --- R2 partition failure fixture (real small parquet + unreadable sibling) ---
        with tempfile.TemporaryDirectory() as td:
            prod = Path(td) / "STOCK_DAILY_PIT_R1"
            y = prod / "year=2026"
            _write_parquet(y / "good.parquet", ["2026-09-01", "2026-09-02"])
            bad = y / "bad.parquet"
            bad.write_bytes(b"not-a-parquet")
            cov = common.product_date_coverage(prod, "STOCK_DAILY_PIT_R1")
            mode = common.infer_mode_for_product("STOCK_DAILY_PIT_R1", cov)
            results["tests"]["extract_bad_partition_unverifiable"] = {
                "PASS": cov.get("coverage_extract_status") == "UNVERIFIABLE" and mode == "UNKNOWN_STOP" and bool(cov.get("errors")),
                "status": cov.get("coverage_extract_status"),
                "mode": mode,
                "errors": cov.get("errors"),
            }
            # gate must reject unverifiable child vs fat parent
            parent_dates = ["2026-09-01", "2026-09-02"]
            with patch.object(
                gate_mod,
                "_product_cov",
                side_effect=[_cov_ok(parent_dates), {**cov, "date_set": set(cov.get("dates") or []), "supported_product": True, "coverage_mode": mode}],
            ):
                gres = gate_mod.gate("p", "c", ["STOCK_DAILY_PIT_R1"])
            results["tests"]["gate_rejects_unverifiable_child"] = {
                "PASS": gres["CACHE_RELEASE_PUBLISHABLE"] is False,
                "status": gres.get("GATE_STATUS"),
                "reason": gres["details"]["STOCK_DAILY_PIT_R1"].get("reason"),
            }

        # --- R3 mode contract ---
        two = {
            "exists": True,
            "distinct_dates": 2,
            "min_date": "2026-09-01",
            "max_date": "2026-09-02",
            "year_slices": ["year=2026"],
            "coverage_extract_status": "OK",
            "errors": [],
            "dates": ["2026-09-01", "2026-09-02"],
        }
        results["tests"]["two_dates_not_full_history"] = {
            "PASS": common.infer_mode_for_product("STOCK_DAILY_PIT_R1", two) != "FULL_HISTORY",
            "mode": common.infer_mode_for_product("STOCK_DAILY_PIT_R1", two),
        }
        results["tests"]["unsupported_product_unknown_stop"] = {
            "PASS": common.infer_mode_for_product(
                "CORP_SHAREHOLDER_TOP10_PIT_R1",
                {"exists": True, "distinct_dates": 50, "coverage_extract_status": "OK", "errors": [], "dates": ["2020-01-01"]},
            )
            == "UNKNOWN_STOP",
            "mode": common.infer_mode_for_product(
                "CORP_SHAREHOLDER_TOP10_PIT_R1",
                {"exists": True, "distinct_dates": 50, "coverage_extract_status": "OK", "errors": []},
            ),
        }
        # unsupported product_date_coverage
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "CORP_SHAREHOLDER_TOP10_PIT_R1"
            _write_parquet(p / "year=2020" / "x.parquet", ["2020-01-02"])
            cov = common.product_date_coverage(p, "CORP_SHAREHOLDER_TOP10_PIT_R1")
            results["tests"]["unsupported_product_extract_refused"] = {
                "PASS": cov.get("coverage_extract_status") == "UNSUPPORTED_PRODUCT",
                "status": cov.get("coverage_extract_status"),
            }

        st = gate_mod.self_test()
        results["tests"]["self_test_modes"] = {
            "PASS": all(v.get("PASS") for v in st.values()),
            "body": st,
        }

        # --- R4 classify consumer structure ---
        diag = common.classify_stock_daily("2026-09-01", "2026-09-10")
        has_nest = isinstance(diag.get("cache"), dict) and isinstance(diag["cache"].get("coverage"), dict)
        # write_reports access pattern
        try:
            _ = diag["cache"]["coverage"].get("min_date")
            _ = diag["cache"]["coverage"].get("max_date")
            _ = diag["cache"]["coverage"].get("distinct_dates")
            _ = diag["cache"]["coverage"].get("row_count")
            _ = diag.get("coverage_mode")
            nest_ok = True
        except Exception:
            nest_ok = False
        results["tests"]["classify_consumer_structure"] = {
            "PASS": has_nest and nest_ok and "coverage_mode" in diag,
            "has_cache_key": "cache" in diag,
            "has_coverage_mode": "coverage_mode" in diag,
            "root_cause": diag.get("root_cause"),
            "download_required": diag.get("download_required"),
        }
        results["tests"]["no_true_miss_download_auth"] = {
            "PASS": diag.get("root_cause") != "TRUE_MISS_AFTER_ALL_PLANES" and diag.get("download_required") is False,
            "root_cause": diag.get("root_cause"),
            "download_required": diag.get("download_required"),
        }

        # cross-year years_scanned
        raw = common.raw_stock_daily_dates("2024-12-20", "2025-01-10")
        years = raw.get("years_scanned") or []
        results["tests"]["cross_year_scan"] = {
            "PASS": years == [2024, 2025] or set(years) >= {2024, 2025},
            "years_scanned": years,
            "status": raw.get("status"),
        }

        # --- R5 resolver actual call ---
        import blackbox_data_access_resolver_r1 as resolver

        currents = resolver.read_currents()
        currents["_request_start_date"] = "2026-09-01"
        currents["_request_end_date"] = "2026-09-10"
        # ensure coverage import uses code_v2: resolver inserts its parent (code_v2) first
        resolved = resolver.resolve_product("STOCK_DAILY_PIT_R1", currents.get("cache_asof"), None, currents)
        cov_ready = resolved.get("coverage_ready")
        cov_mode = resolved.get("coverage_mode")
        # Must not READY-wash unverifiable; if window has gaps, coverage_ready False
        results["tests"]["resolver_resolve_product_call"] = {
            "PASS": resolved.get("resolved") is True and cov_mode not in (None,) and (
                cov_ready is False or cov_mode == "FULL_HISTORY"
            ),
            "result_status": resolved.get("result_status"),
            "coverage_ready": cov_ready,
            "coverage_mode": cov_mode,
            "missing_trade_days": resolved.get("missing_trade_days"),
            "coverage_error": currents.get("_coverage_error"),
            "resolver_file": resolver.__file__,
        }
        # If coverage_mode UNKNOWN_STOP due to import of stub — fail hard
        if "code_v2" not in str(resolver.__file__).replace("\\", "/"):
            results["tests"]["resolver_resolve_product_call"]["PASS"] = False
            results["tests"]["resolver_resolve_product_call"]["error"] = "resolver not loaded from code_v2"

        # --- R6 calendar ---
        cal_path = common.find_calendar_trade_days()
        results["tests"]["calendar_authority_versioned"] = {
            "PASS": "calendar_cn_exchange_v2_asof_" in str(cal_path).replace("\\", "/"),
            "path": str(cal_path),
        }
        # pure weekend window inside coverage → empty list OK
        weekend = common.load_trade_calendar("2026-06-06", "2026-06-07")  # Sat-Sun
        results["tests"]["calendar_pure_weekend_empty_ok"] = {
            "PASS": weekend == [],
            "days": [str(d) for d in weekend],
        }
        # outside coverage must raise
        outside_ok = False
        try:
            common.load_trade_calendar("1990-01-01", "1990-01-05")
        except Exception:
            outside_ok = True
        results["tests"]["calendar_outside_coverage_refuse"] = {"PASS": outside_ok}

        # real fat/thin if present
        fat = ROOT / "数据" / "回测缓存" / "releases" / "BLACKBOX_CACHE_R1_ASOF_20260810_20260811_020021"
        thin = ROOT / "数据" / "回测缓存" / "releases" / "BLACKBOX_CACHE_R1_INDEX_DAILY_732_ASOF_20260811_20260812_123050"
        if fat.exists() and thin.exists():
            g_thin = gate_mod.gate(fat, thin, ["STOCK_DAILY_PIT_R1"])
            results["tests"]["real_fat_vs_thin"] = {
                "PASS": g_thin.get("CACHE_RELEASE_PUBLISHABLE") is False,
                "lost_count": g_thin["details"]["STOCK_DAILY_PIT_R1"].get("lost_count"),
                "reason": g_thin["details"]["STOCK_DAILY_PIT_R1"].get("reason"),
            }
        else:
            results["tests"]["real_fat_vs_thin"] = {"PASS": False, "error": "releases missing"}

        # sample read typed dates
        cur = common.cache_current()
        stock_path = Path(cur["standard_root"]) / "STOCK_DAILY_PIT_R1"
        fp = stock_path / "year=2026" / "part_2026.parquet"
        sample = pd.DataFrame()
        if fp.exists():
            df = pd.read_parquet(fp, columns=["date", "code", "close", "known_at"])
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            lo, hi = pd.Timestamp("2026-09-01"), pd.Timestamp("2026-09-10")
            sample = df[(df["code"] == "000001.XSHE") & (df["date"] >= lo) & (df["date"] <= hi)].sort_values("date")
        results["tests"]["sample_typed_date_filter"] = {
            "PASS": len(sample) >= 1,
            "n_rows": int(len(sample)),
            "dates": [pd.Timestamp(x).strftime("%Y-%m-%d") for x in sample["date"].head(7).tolist()] if len(sample) else [],
        }

        fails = [k for k, v in results["tests"].items() if not v.get("PASS")]
        results["failed"] = fails
        results["review_points"] = {
            "1_gate_set_semantics": all(results["tests"][k]["PASS"] for k in results["tests"] if k.startswith("gate_")),
            "2_extract_failure_propagation": results["tests"]["extract_bad_partition_unverifiable"]["PASS"]
            and results["tests"]["gate_rejects_unverifiable_child"]["PASS"],
            "3_mode_contract": results["tests"]["two_dates_not_full_history"]["PASS"]
            and results["tests"]["unsupported_product_unknown_stop"]["PASS"],
            "4_classify_consumer": results["tests"]["classify_consumer_structure"]["PASS"]
            and results["tests"]["no_true_miss_download_auth"]["PASS"],
            "5_strict_resolver_test": results["tests"]["resolver_resolve_product_call"]["PASS"],
            "6_calendar_boundaries": results["tests"]["calendar_pure_weekend_empty_ok"]["PASS"]
            and results["tests"]["calendar_outside_coverage_refuse"]["PASS"],
        }
        results["all_pass"] = not fails
        results["status"] = "CANDIDATE_V2_READY_FOR_REVIEW" if not fails else "BLOCKED_WITH_SPECIFIC_GAP"
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
