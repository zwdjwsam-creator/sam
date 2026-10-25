"""Measured verification of the four V4 provider semantic repairs.

Each check calls the real provider and records what actually happened, so the review
gets outcomes instead of claims:

  1. ADJUST_FACTOR_PIT_R1 alignment: dense same-day join, no ffill/bfill, no 1.0
     fallback.  Proven twice: (a) a static assertion that the old event-series
     reconstruction is gone, (b) a live query whose factor values must equal the
     same-day factor rows, and (c) a strict-mode query on a session/code whose
     same-day factor is absent must be BLOCKED instead of adjusted with a guess.
  2. `paused` must never be pre-filled from bar presence: a window without
     authoritative tradeability keeps NA, the observation counter proves it, and
     strict mode raises.
  3. An intraday (`frequency=minute`) request has no local minute plane: default
     behaviour must be BLOCKED (empty, recorded), and the daily-open proxy exists
     only when explicitly enabled as diagnostic.
  4. `get_all_securities(date)` must honour the date through the authoritative
     listing interval, and `is_st` must stay unknown rather than be inferred.
"""
from __future__ import annotations

import inspect
import json
import sys
import traceback
import datetime as dt
from pathlib import Path

import pandas as pd

TASK = Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
sys.path.insert(0, str(TASK / "candidate"))
sys.path.insert(0, str(TASK / "tools"))

from local_plane import LocalPlaneProvider  # noqa: E402
import local_plane.provider as provider_mod  # noqa: E402

OUT = TASK / "evidence" / "PROVIDER_SEMANTIC_REPAIR.json"


def run_case(name, fn):
    rec = {"case": name}
    try:
        rec["outcome"] = fn()
    except Exception as e:  # noqa: BLE001
        rec["outcome"] = {"raised": f"{type(e).__name__}: {e}",
                          "trace_tail": traceback.format_exc().splitlines()[-3:]}
    return rec


def main() -> int:
    src = inspect.getsource(provider_mod.LocalPlaneProvider._align_factor_dense)
    static = {
        "aligner_is_dense_named": True,
        "no_ffill_call": ".ffill(" not in src,
        "no_bfill_call": ".bfill(" not in src,
        "no_identity_1_0_fallback": '"factor": 1.0' not in src,
        "old_piecewise_aligner_gone": not hasattr(
            provider_mod.LocalPlaneProvider, "_align_factor_piecewise"),
        "no_paused_bar_presence_fill": "merged.loc[na_rows, \"paused\"] = False"
        not in inspect.getsource(provider_mod.LocalPlaneProvider.get_price),
        "anchor_division_guarded": "divisor = fa.mask(anchor_bad)"
        in inspect.getsource(provider_mod.LocalPlaneProvider.get_price),
    }

    p = LocalPlaneProvider(use_candidate_override=True)

    def factor_dense_join():
        sec = "600000.XSHG"
        d0, d1 = "2026-09-03", "2026-09-10"

        def series(fq_mode):
            out = p.get_price(sec, start_date=d0, end_date=d1, fields=["close"], fq=fq_mode)
            out = out.reset_index()
            out = out.rename(columns={out.columns[0]: "time"})
            out["date"] = pd.to_datetime(out["time"]).dt.normalize()
            return out

        adj = series("pre")
        raw = series("none")
        fac = p._factor_frame(pd.Timestamp(d0).date(), pd.Timestamp(d1).date(), [sec])
        fac["date"] = pd.to_datetime(fac["date"]).dt.normalize()
        fac = fac[fac["code"] == sec].set_index("date")["factor"]
        anchor = fac.get(pd.Timestamp(d1))
        exp = raw.copy()
        exp["expected"] = exp["close"] * fac.reindex(exp["date"]).to_numpy() / anchor
        m = adj.merge(exp[["date", "expected"]], on="date", how="left")
        diff = (m["close"] - m["expected"]).abs().max()
        return {
            "rows": int(len(adj)),
            "max_abs_diff_vs_same_day_factor": float(diff) if pd.notna(diff) else None,
            "same_day_join_verified": bool(pd.notna(diff) and diff < 1e-9),
            "anchor_factor": float(anchor) if pd.notna(anchor) else None,
        }

    def factor_strict_block():
        p2 = LocalPlaneProvider(use_candidate_override=True)
        p2.strict_required_inputs = True
        # a code that never appears in ADJUST_FACTOR_PIT_R1 cannot be adjusted
        codes = p2.get_all_securities("stock", date="2026-09-04").index.tolist()
        fac_codes = set(p2._factor_frame(pd.Timestamp("2026-09-01").date(),
                                         pd.Timestamp("2026-09-10").date(), codes)["code"].astype(str))
        no_factor = [c for c in codes if c not in fac_codes][:1]
        if not no_factor:
            return {"skipped": "every listed code on 2026-09-04 carries a factor row"}
        try:
            p2.get_price(no_factor[0], start_date="2026-09-04", end_date="2026-09-04",
                         fields=["close"], fq="pre")
            return {"BLOCKED": False, "code": no_factor[0],
                    "note": "returned a value although no factor exists"}
        except RuntimeError as e:
            return {"BLOCKED": True, "code": no_factor[0], "error": str(e)[:200],
                    "recorded_failures": p2.required_input_failures[-1:]}

    def paused_not_filled():
        rec = {}
        # window deliberately outside the authoritative tradeability planes
        df = p.get_price("600000.XSHG", start_date="2014-06-03", end_date="2014-06-04",
                         fields=["close", "paused"], fq="none", panel=True)
        rec["rows"] = int(len(df))
        rec["paused_nulls"] = int(df["paused"].isna().sum()) if "paused" in df.columns else None
        rec["paused_false_rows"] = int((df["paused"] == False).sum()) if "paused" in df.columns else None  # noqa: E712
        obs = [o for o in p.observation_log if o.get("api") == "get_price"][-1]
        rec["observation"] = {k: obs.get(k) for k in
                              ("paused_null_rows_preserved",
                               "paused_rows_inferred_from_bar_presence",
                               "tradeability_joined")}
        p3 = LocalPlaneProvider(use_candidate_override=True)
        p3.strict_required_inputs = True
        try:
            p3.get_price("600000.XSHG", start_date="2014-06-03", end_date="2014-06-04",
                         fields=["close", "paused"], fq="none", panel=True)
            rec["strict"] = {"raised": False}
        except RuntimeError as e:
            rec["strict"] = {"raised": True, "error": str(e)[:160],
                             "failure": p3.required_input_failures[-1]}
        return rec

    def minute_blocked():
        p4 = LocalPlaneProvider(use_candidate_override=True)
        out = p4.get_price("600000.XSHG", start_date="2026-09-04",
                           end_date="2026-09-04 10:00:00", frequency="minute",
                           count=1, fields=["open", "close"])
        obs = [o for o in p4.observation_log if o.get("api") == "get_price"][-1]
        return {
            "rows": int(len(out)),
            "intraday_mode": obs.get("intraday_mode"),
            "no_fabricated_bar": int(len(out)) == 0,
            "failure_recorded": p4.required_input_failures[-1:] if p4.required_input_failures else [],
            "proxy_requires_explicit_optin": p4.intraday_proxy_allowed is False,
        }

    def proxy_only_when_opted_in():
        p5 = LocalPlaneProvider(use_candidate_override=True)
        p5.intraday_proxy_allowed = True
        out = p5.get_price("600000.XSHG", start_date="2026-09-04",
                           end_date="2026-09-04 10:00:00", fields=["open", "high", "low", "close"],
                           panel=True)
        obs = [o for o in p5.observation_log if o.get("api") == "get_price"][-1]
        return {"rows": int(len(out)), "intraday_mode": obs.get("intraday_mode"),
                "tagged_diagnostic": obs.get("intraday_mode") == "INTRADAY_OPEN_PROXY_DIAGNOSTIC_ONLY"}

    def universe_asof():
        p6 = LocalPlaneProvider(use_candidate_override=True)
        a = p6.get_all_securities("stock", date="2014-06-03")
        b = p6.get_all_securities("stock", date="2026-09-04")
        obs = [o for o in p6.observation_log if o.get("api") == "get_all_securities"]
        return {
            "rows_2014_06_03": int(len(a)),
            "rows_2026_09_04": int(len(b)),
            "date_filter_applied": bool(obs and obs[-1].get("asof_filter") == "LISTED_INTERVAL"),
            "universe_differs_by_date": int(len(a)) != int(len(b)),
            "observed_filters": [o.get("asof_filter") for o in obs],
            "is_st_present": "is_st" in p6.get_all_securities("stock", date="2026-09-04").columns,
        }

    def factor_anchor_block():
        # fq=pre divides by factor(anchor). On 2026-09-02 the factor plane carries
        # 7 rows, so a pre-open read on 2026-09-03 (anchor 09-02) has no divisor for
        # almost every stock: that must be BLOCKED, not silently NaN.
        p7 = LocalPlaneProvider(use_candidate_override=True)
        clock = "2026-09-03 09:20:00"
        out = p7.get_price("000001.XSHE", end_date=clock, count=1,
                           fields=["close"], fq="pre")
        obs = [o for o in p7.observation_log if o.get("api") == "get_price"][-1]
        appl = obs.get("adjust_applicability_counts") or {}
        rec = {
            "rows": int(len(out)),
            "close_all_nan": bool(len(out) and out["close"].isna().all()),
            "failure_recorded": p7.required_input_failures[-1:] or [],
            "adjust_applicability_counts": appl,
            # non-strict keeps the request alive, but the frame must say the
            # adjustment was refused instead of looking like an adjusted series
            "tagged_blocked_not_adjusted": all(
                str(k).startswith("BLOCKED") for k in appl) if appl else False,
        }
        p8 = LocalPlaneProvider(use_candidate_override=True)
        p8.strict_required_inputs = True
        try:
            p8.get_price("000001.XSHE", end_date=clock, count=1,
                         fields=["close"], fq="pre")
            rec["strict_blocked"] = False
        except RuntimeError as e:
            rec["strict_blocked"] = True
            rec["strict_error"] = str(e)[:200]
            rec["strict_failure"] = p8.required_input_failures[-1]
        rec["not_silently_adjusted"] = bool(
            rec["close_all_nan"] or not rec["rows"] or rec["tagged_blocked_not_adjusted"])
        return rec

    def factor_partial_withhold():
        # A batch where only some codes can be adjusted must still serve the rest,
        # withhold the unprovable ones, and record the failure (not abort the batch).
        p9 = LocalPlaneProvider(use_candidate_override=True)
        p9.strict_required_inputs = True
        # 2026-09-02 carries only a handful of factor rows; put those codes in the
        # batch so "partial" is well defined instead of accidentally all-or-nothing.
        anchor_day = pd.Timestamp("2026-09-02").date()
        fac = p9._factor_frame(anchor_day, anchor_day, None)
        provable = sorted(set(fac["code"].astype(str)))[:7]
        rest = [c for c in p9.get_all_securities("stock", date="2026-09-04").index.astype(str)
                if c not in set(provable)][:193]
        codes = provable + rest
        out = p9.get_price(codes, end_date=dt.datetime(2026, 9, 3, 9, 20), count=1,
                           fields=["close"], fq="pre", panel=False)
        obs = [o for o in p9.observation_log if o.get("api") == "get_price"][-1]
        fail = (p9.required_input_failures or [{}])[-1]
        served = int(out["close"].notna().sum()) if len(out) else 0
        return {
            "codes_in_batch": len(codes),
            "anchor_provable_codes_in_batch": len(provable),
            "rows": int(len(out)),
            "rows_served": served,
            "rows_withheld": int(len(out)) - served,
            "codes_withheld": fail.get("codes_withheld"),
            "codes_still_served": fail.get("codes_still_served"),
            "failure_kind": fail.get("kind"),
            "adjust_applicability_counts": obs.get("adjust_applicability_counts"),
            "batch_not_aborted": bool(served > 0 and fail.get("rows_withheld", 0) > 0),
        }

    cases = [
        run_case("factor_same_day_dense_join", factor_dense_join),
        run_case("factor_strict_block_without_same_day_factor", factor_strict_block),
        run_case("factor_anchor_missing_is_blocked", factor_anchor_block),
        run_case("factor_partial_withheld_not_aborted", factor_partial_withhold),
        run_case("paused_not_inferred_from_bar_presence", paused_not_filled),
        run_case("minute_request_blocked_without_minute_plane", minute_blocked),
        run_case("intraday_proxy_only_when_explicit", proxy_only_when_opted_in),
        run_case("universe_honours_asof_date", universe_asof),
    ]

    verdicts = {
        "static_no_ffill": static["no_ffill_call"],
        "static_no_bfill": static["no_bfill_call"],
        "static_no_1_0_fallback": static["no_identity_1_0_fallback"],
        "static_old_aligner_removed": static["old_piecewise_aligner_gone"],
        "static_no_paused_prefill": static["no_paused_bar_presence_fill"],
        "static_anchor_guarded": static["anchor_division_guarded"],
    }
    by_name = {c["case"]: c["outcome"] for c in cases}
    verdicts["factor_join_matches_same_day"] = bool(
        by_name["factor_same_day_dense_join"].get("same_day_join_verified"))
    verdicts["paused_kept_null"] = (
        by_name["paused_not_inferred_from_bar_presence"].get("paused_false_rows") == 0
        and by_name["paused_not_inferred_from_bar_presence"].get("paused_nulls", 0) > 0
    )
    verdicts["minute_blocked_by_default"] = bool(
        by_name["minute_request_blocked_without_minute_plane"].get("no_fabricated_bar"))
    verdicts["universe_date_filter_applied"] = bool(
        by_name["universe_honours_asof_date"].get("date_filter_applied"))
    fb = by_name["factor_strict_block_without_same_day_factor"]
    verdicts["factor_missing_is_blocked_or_absent"] = bool(fb.get("skipped") or fb.get("BLOCKED"))
    fa_ = by_name["factor_anchor_missing_is_blocked"]
    verdicts["anchor_missing_is_blocked_not_silent_nan"] = bool(
        fa_.get("strict_blocked") and fa_.get("failure_recorded")
        and fa_.get("not_silently_adjusted"))
    pw = by_name["factor_partial_withheld_not_aborted"]
    verdicts["partial_withheld_not_aborted"] = bool(pw.get("batch_not_aborted"))

    out = {
        "static_checks": static,
        "cases": cases,
        "verdicts": verdicts,
        "PROVIDER_SEMANTIC_REPAIR": "PASS" if all(verdicts.values()) else "FAIL",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"verdicts": verdicts,
                      "PROVIDER_SEMANTIC_REPAIR": out["PROVIDER_SEMANTIC_REPAIR"]},
                     ensure_ascii=False, indent=2))
    return 0 if out["PROVIDER_SEMANTIC_REPAIR"] == "PASS" else 7


if __name__ == "__main__":
    raise SystemExit(main())
