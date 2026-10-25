"""Deliverable 1: current dataset matrix + defensible update basis.

Measures the remaining unanswered scope from parquet footer statistics
(no full-row reads), reuses R3 identities and R10 writer bindings, and records
per-dataset observed range, coverage basis, writer/consumer, and readiness.

Not a completeness certificate: FULL_FOOTER means every file's footer was read;
STRATIFIED_SAMPLE(n/N) means only n files were read and min/max is a bound.
"""
from __future__ import annotations

import json
import os
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pyarrow.parquet as pq

TASK_ROOT = r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion"
R3_PATH = r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\ECOLOGY_REGISTRY_R3.json"
WCB_PATH = r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\r10_writer_cursor_bindings_delivery\ACQUISITION_WRITER_CURSOR_BINDINGS.json"
CACHE_RELEASE = (
    r"E:\BLACKBOX\数据\回测缓存\releases"
    r"\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439"
)
CLEAN_RELEASE = (
    r"E:\BLACKBOX\数据\清洗成品\releases"
    r"\BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439"
)

TIME_COLUMNS = [
    ("date", "EVENT_TIME"),
    ("day", "EVENT_TIME"),
    ("trade_date", "EVENT_TIME"),
    ("datetime", "EVENT_TIME"),
    ("bar_time", "EVENT_TIME"),
    ("time", "EVENT_TIME"),
    ("event_date", "EVENT_REFERENCE"),
    ("announcement_date", "EVENT_REFERENCE"),
    ("ann_date", "ANNOUNCEMENT_TIME"),
    ("call_date", "EVENT_TIME"),
    ("pub_date", "ANNOUNCEMENT_TIME"),
    ("publication_at", "AVAILABILITY_TIME"),
    ("market_available_at", "AVAILABILITY_TIME"),
    # A trading-calendar product has a date axis, but it is a calendar definition,
    # not an observation event: it must not be reported as NO_TIME_AXIS.
    ("calendar_date", "CALENDAR_AXIS"),
    ("effective_from", "EFFECTIVE_FROM"),
    ("effective_date", "EFFECTIVE_FROM"),
    # Period-end labels are contract metadata, not an availability time; keep the
    # role explicit so they are never read as "known at".
    ("end_date", "PERIOD_END_REFERENCE"),
    ("statDate", "REPORT_PERIOD"),
    ("report_date", "REPORT_PERIOD"),
    ("signal_date", "SNAPSHOT_SIGNAL"),
    ("asof_date", "SNAPSHOT_SIGNAL"),
    ("observation_date", "SNAPSHOT_SIGNAL"),
    ("start_date", "VALIDITY_START"),
]

# The R3 RAW roots are per-family directories, not per-product directories
# (e.g. P5_attributes_events holds billboard, xr_xd, shareholder_top10 ...).
# Measuring the family root and reporting it as one dataset's range is exactly the
# shared-root sample the review flagged. Resolve the product subdirectory when the
# name mapping is defensible; otherwise report the product dir as unresolved instead
# of publishing the family-wide bound.
PRODUCT_SUBDIR: Dict[str, str] = {
    "CALENDAR_CN_EXCHANGE": "calendar_cn_exchange",
    "INDUSTRY_CONCEPT": "industry_concept",
    "INDUSTRY_CONCEPT_EVENTS": "industry_concept_events",
    "BILLBOARD": "billboard",
    "XR_XD": "xr_xd",
    "SHAREHOLDER_TOP10": "shareholder_top10",
    "SHAREHOLDER_FLOATING_TOP10": "shareholder_floating_top10",
    "MTSS": "mt_total",
    "ETF_SHARE": "fund_etf_share",
    "FUND_TRACKING_INDEX_MAPPING": "fund_tracking_index_mapping",
    "INDEX_COMPONENTS": "index_constituents",
    "INDEX_WEIGHTS": "index_weights",
    "PRICE_ETF_1M": "fund_etf_price_1m",
    "PRICE_ETF_5M": "fund_etf_price_5m",
    "PRICE_ETF_30M": "fund_etf_price_30m",
    "PRICE_ETF_60M": "fund_etf_price_60m",
    "PRICE_ETF_DAILY": "fund_etf_price_daily",
    "OPEN_FUND": "open_fund",
    "QDII": "qdii",
    "FUND_OTHER": "other",
    # unambiguous product dirs inside a family root
    "TRADABLE_STATUS": "stock_limit_pause_status",
    "VALUATION": "valuation",
    "FINANCE_PIT": "financial_indicator",
}

# PRODUCT_SUBDIR applies only where the subdirectory is unambiguous. When the
# resolved path does not exist the layer is reported as unresolved, not measured.

# Product-specific CACHE mapping (the R3 CACHE root is the whole release).
CACHE_PRODUCTS: Dict[str, List[str]] = {
    "PRICE_STOCK_DAILY": ["STOCK_DAILY_PIT_R1", "STOCK_DAILY_RAW_PIT_R1"],
    "PRICE_ETF_DAILY": ["ETF_DAILY_PIT_R1", "FUND_DAILY_PIT_R1"],
    "PRICE_INDEX_DAILY": ["INDEX_DAILY_R1"],
    "ADJUST_FACTOR": ["ADJUST_FACTOR_PIT_R1"],
    "TRADABLE_STATUS": ["STOCK_TRADEABILITY_PIT_R1"],
    "VALUATION": ["VALUATION_PIT_R1"],
    "FINANCE_PIT": ["FINANCIAL_INDICATOR_PIT_R1"],
    "BILLBOARD": ["BILLBOARD_DAILY_PIT_R1"],
    "XR_XD": ["CORP_XR_XD_EVENT_PIT_R1"],
    "SHAREHOLDER_TOP10": ["CORP_SHAREHOLDER_TOP10_PIT_R1"],
    "SHAREHOLDER_FLOATING_TOP10": ["CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1"],
    "INDEX_COMPONENTS": ["INDEX_CONSTITUENT_PIT_R1"],
    "INDEX_WEIGHTS": ["INDEX_WEIGHT_PIT_R1"],
    "SECURITY_MASTER": ["SECURITY_MASTER_SNAPSHOT_R1"],
    "FUND_ETF_NAV": ["FUND_NAV_PIT_R1"],
    "INDUSTRY_CONCEPT": ["SW_L1_MEMBERSHIP_PIT_R1", "SW_L2_MEMBERSHIP_PIT_R1", "SW_L3_MEMBERSHIP_PIT_R1"],
}

# dataset -> (writer row_id, note)
WRITER_MAP: Dict[str, Tuple[str, str]] = {
    "PRICE_STOCK_DAILY": ("A_STOCK_ETF_INDEX_DAILY", "stock daily writer"),
    "PRICE_ETF_DAILY": ("A_STOCK_ETF_INDEX_DAILY", "ETF daily writer"),
    "PRICE_INDEX_DAILY": ("A_STOCK_ETF_INDEX_DAILY", "index daily writer"),
    "ADJUST_FACTOR": ("B_ADJUSTMENT_FACTOR", "factor writer"),
    "TRADABLE_STATUS": ("C_RAW_NONE_MINUTE", "tradeability rides the same daily downloader body; no separate writer"),
    "PRICE_STOCK_1M": ("C_RAW_NONE_MINUTE", "stock minute writer"),
    "PRICE_STOCK_5M": ("C_RAW_NONE_MINUTE", "stock minute writer"),
    "PRICE_STOCK_30M": ("C_RAW_NONE_MINUTE", "stock minute writer"),
    "PRICE_STOCK_60M": ("C_RAW_NONE_MINUTE", "stock minute writer"),
    "PRICE_ETF_1M": ("C_RAW_NONE_MINUTE", "ETF minute writer"),
    "PRICE_ETF_5M": ("C_RAW_NONE_MINUTE", "ETF minute writer"),
    "PRICE_ETF_30M": ("C_RAW_NONE_MINUTE", "ETF minute writer"),
    "PRICE_ETF_60M": ("C_RAW_NONE_MINUTE", "ETF minute writer"),
    "PRICE_INDEX_MINUTE": ("C_RAW_NONE_MINUTE", "index minute writer"),
    "VALUATION": ("D_FINANCE_EVENT_REFERENCE", "valuation PIT refresh"),
    "FINANCE_PIT": ("D_FINANCE_EVENT_REFERENCE", "finance PIT refresh"),
    "BILLBOARD": ("D_FINANCE_EVENT_REFERENCE", "event/reference refresh"),
    "XR_XD": ("D_FINANCE_EVENT_REFERENCE", "event/reference refresh"),
    "CORPORATE_REFERENCE": ("D_FINANCE_EVENT_REFERENCE", "event/reference refresh"),
    "SHAREHOLDER_TOP10": ("D_FINANCE_EVENT_REFERENCE", "event/reference refresh"),
    "SHAREHOLDER_FLOATING_TOP10": ("D_FINANCE_EVENT_REFERENCE", "event/reference refresh"),
    "INDUSTRY_CONCEPT": ("D_FINANCE_EVENT_REFERENCE", "industry/concept refresh"),
    "INDUSTRY_CONCEPT_EVENTS": ("D_FINANCE_EVENT_REFERENCE", "industry event refresh"),
    "MTSS": ("D_FINANCE_EVENT_REFERENCE", "margin/security lending refresh"),
    "SECURITY_MASTER": ("A_STOCK_ETF_INDEX_DAILY", "security master snapshot written by the daily universe writer"),
    "INDEX_COMPONENTS": ("A_STOCK_ETF_INDEX_DAILY", "index constituent refresh"),
    "INDEX_WEIGHTS": ("A_STOCK_ETF_INDEX_DAILY", "index weight refresh"),
    "CALENDAR_CN_EXCHANGE": ("A_STOCK_ETF_INDEX_DAILY", "exchange calendar refresh"),
    "EXTERNAL_EVIDENCE_PLANE": ("E_EXTERNAL_EVIDENCE", "external evidence materialization"),
    "EXTERNAL_DICT_EVIDENCE": ("E_EXTERNAL_EVIDENCE", "external evidence materialization"),
    "US_MARKET": ("E_EXTERNAL_EVIDENCE", "external evidence materialization"),
    "TUSHARE_INDEX_WEIGHT_ADAPTER": ("E_EXTERNAL_EVIDENCE", "external adapter output"),
    "FUND_ETF_NAV": ("D_FINANCE_EVENT_REFERENCE", "fund NAV refresh (no retained production fund writer bound)"),
    "ETF_SHARE": ("D_FINANCE_EVENT_REFERENCE", "fund share refresh (no retained production fund writer bound)"),
    "OPEN_FUND": ("D_FINANCE_EVENT_REFERENCE", "open fund refresh (no retained production fund writer bound)"),
    "QDII": ("D_FINANCE_EVENT_REFERENCE", "QDII refresh (no retained production fund writer bound)"),
    "FUND_OTHER": ("D_FINANCE_EVENT_REFERENCE", "other fund refresh (no retained production fund writer bound)"),
    "FUND_TRACKING_INDEX_MAPPING": ("D_FINANCE_EVENT_REFERENCE", "fund-index mapping refresh"),
    "TS_CBOND_R1": ("D_FINANCE_EVENT_REFERENCE", "TS convertible bond raw; writer not retained"),
    "TS_CBOND_R2": ("D_FINANCE_EVENT_REFERENCE", "TS convertible bond raw; writer not retained"),
}

NOT_APPLICABLE = {
    "FACTOR_260_DICTIONARY": "FACTOR_DICTIONARY contract: formula/semantics/pit rules are static references, not temporal datasets",
    "FACTOR_260_SEMANTICS": "FACTOR_DICTIONARY contract: static reference",
    "FACTOR_260_FORMULA": "FACTOR_DICTIONARY contract: static reference",
    "FACTOR_260_PIT_RULES": "FACTOR_DICTIONARY contract: static reference",
    "FACTOR_260_CLEANING_RULES": "FACTOR_DICTIONARY contract: static reference",
    "FACTOR_260_ENGINE_MAPPING": "FACTOR_DICTIONARY contract: static reference",
    "STRATEGY_OUTPUT": "STRATEGY_OUTPUT is a generated result plane, not an acquired dataset",
    "LEGACY_JQ_RAW_CN": "read-only legacy RAW archive; explicitly not an incremental target",
    "EXPERIMENTAL_WINDOW_RAW": "experimental window archive; explicitly not an incremental target",
    "STRATEGY_DATA_PLANE_ADDITIONS": "read-only strategy data plane additions archive",
    "FORENSIC_CANARY": "forensic canary archive; read-only",
    "EXPERIMENT_CANARY": "experiment canary archive; read-only",
}

# Not "contractually inapplicable": these need a real resolution before they can be
# called either way. Absence of an admitted product is a measured fact, not a
# contract that permits exclusion; an undefined scope is unresolved by definition.
BLOCKED_PLANE = {
    "FACTOR_VALUE": {
        "status": "BLOCKED_NO_ADMITTED_PRODUCT",
        "predicate": (
            "no admitted FACTOR_VALUE product exists in the mounted CACHE release and no "
            "retained factor-value writer/batch is bound; ROOT_ABSENT is an absence fact, "
            "not a contract permitting NOT_APPLICABLE"
        ),
        "required_input": "an admitted FACTOR_VALUE product (or an explicit contract permitting exclusion)",
    },
    "UNDETERMINED_SCOPE": {
        "status": "UNRESOLVED_SCOPE",
        "predicate": (
            "no layers, no identity and no controlling definition; scope stays unresolved "
            "and is excluded from the increment plan pending an actual definition"
        ),
        "required_input": "a controlling identity/scope definition",
    },
}


def list_parquet(root: str) -> List[str]:
    out = []
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            if f.endswith(".parquet"):
                out.append(os.path.join(dp, f))
    return out


def pick_time_column(names: List[str]) -> Tuple[Optional[str], str]:
    for col, role in TIME_COLUMNS:
        if col in names:
            return col, role
    return None, "NO_TIME_AXIS"


def scan_files(files: List[str], cap: int = 400) -> Dict[str, Any]:
    total = len(files)
    if total == 0:
        return {"mode": "EMPTY", "n_files_total": 0, "n_files_measured": 0}
    if total <= 2500:
        chosen = files
        mode = "FULL_FOOTER"
    else:
        by_dir: Dict[str, List[str]] = {}
        for f in files:
            by_dir.setdefault(os.path.dirname(f), []).append(f)
        chosen = []
        dirs = sorted(by_dir)
        per_dir = max(2, cap // max(1, len(dirs)))
        for d in dirs:
            grp = sorted(by_dir[d])
            take = grp if len(grp) <= per_dir else grp[: per_dir // 2] + grp[-(per_dir - per_dir // 2):]
            chosen.extend(take)
        if len(chosen) > cap:
            step = max(1, len(chosen) // cap)
            chosen = chosen[::step][:cap]
        mode = f"STRATIFIED_SAMPLE({len(chosen)}/{total})"

    tmin = tmax = None
    rows_measured = 0
    stats_missing = 0
    time_col = None
    time_role = "NO_TIME_AXIS"
    columns: List[str] = []
    cols_union: List[str] = []
    non_time_base: List[str] = []
    for f in chosen:
        try:
            pf = pq.ParquetFile(f)
        except Exception:
            stats_missing += 1
            continue
        md = pf.metadata
        if md is None:
            stats_missing += 1
            continue
        rows_measured += md.num_rows
        names = list(pf.schema_arrow.names)
        for c in names:
            if c not in cols_union:
                cols_union.append(c)
        if not columns:
            columns = names
        # Resolve the time column from the union of sampled schemas, not from the
        # first file only: a mixed family root used to lose its axis entirely.
        if time_col is None:
            time_col, time_role = pick_time_column(cols_union)
        if not time_col:
            continue
        idx = None
        for i in range(md.num_columns):
            if md.schema.column(i).name == time_col:
                idx = i
                break
        if idx is None:
            continue
        found = False
        for rg in range(md.num_row_groups):
            try:
                st = md.row_group(rg).column(idx).statistics
            except Exception:
                st = None
            if st is None or not st.has_min_max:
                continue
            found = True
            lo, hi = st.min, st.max
            try:
                tmin = lo if tmin is None or lo < tmin else tmin
                tmax = hi if tmax is None or hi > tmax else tmax
            except TypeError:
                pass
        if not found:
            stats_missing += 1
    return {
        "mode": mode,
        "n_files_total": total,
        "n_files_measured": len(chosen),
        "rows_measured": rows_measured,
        "time_column": time_col,
        "time_role": time_role,
        "min": _fmt(tmin),
        "max": _fmt(tmax),
        "stats_missing_files": stats_missing,
        "columns_sample": columns[:24],
        "columns_union_n": len(cols_union),
        "range_basis": (
            "FOOTER_MIN_MAX_OUTER_BOUND_NOT_COMPLETENESS"
            if tmin is not None
            else "NO_TIME_COLUMN_IN_SAMPLED_SCHEMAS"
        ),
    }


def _fmt(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return s


def main() -> None:
    t0 = time.time()
    r3 = json.loads(open(R3_PATH, encoding="utf-8").read())
    wcb = json.loads(open(WCB_PATH, encoding="utf-8").read())
    wcb_rows = {r["row_id"]: r for r in wcb["rows"]}

    datasets = []
    for d in r3["datasets"]:
        ds_id = d["dataset_id"]
        entry: Dict[str, Any] = {
            "dataset_id": ds_id,
            "title_en": d.get("title_en"),
            "supplier": d.get("supplier"),
            "lineage": d.get("lineage"),
            "source_identity": d.get("source_identity"),
            "read_plane_role": d.get("read_plane_role"),
            "authority_rule": d.get("authority_rule"),
            "r3_scope": d.get("scope"),
            "layers": {},
        }

        measured_layers = {}
        for layer_name, layer in (d.get("layers") or {}).items():
            root = (layer or {}).get("root")
            rec: Dict[str, Any] = {
                "root": root,
                "declared_n_parquet": (layer or {}).get("n_parquet"),
                "kind": (layer or {}).get("kind"),
                "release_id": (layer or {}).get("release_id"),
                "asof": (layer or {}).get("asof"),
            }
            if not root or not os.path.exists(root):
                rec.update({"status": "ROOT_ABSENT", "measurement": None})
                measured_layers[layer_name] = rec
                continue

            # A shared family root is not this dataset's product directory. Measure
            # the resolved product subdir when it exists; otherwise say so instead of
            # publishing family-wide bounds as this dataset's observed range.
            measure_root = root
            sub = PRODUCT_SUBDIR.get(ds_id)
            if sub:
                candidate_sub = os.path.join(root, sub)
                if os.path.isdir(candidate_sub):
                    measure_root = candidate_sub
                    rec["product_dir"] = candidate_sub
                    rec["product_dir_resolved"] = True
                else:
                    rec["product_dir_expected"] = candidate_sub
                    rec["product_dir_resolved"] = False
            family_dirs = [
                name
                for name in (
                    os.listdir(root) if os.path.isdir(root) else []
                )
                if os.path.isdir(os.path.join(root, name))
            ]
            shared_family = len(family_dirs) > 1 and layer_name != "CACHE"
            # history/ + tip/ are one product's internal layout, not a product family.
            if set(family_dirs) <= {"history", "tip"}:
                shared_family = False
            # A plane-shaped dataset (evidence plane, archive, canary, strategy output)
            # IS the union of its sources; measuring the root is correct for it, and the
            # scope is labelled instead of being called a product-specific bound.
            plane_shaped = (
                layer_name == "EVIDENCE"
                or ds_id in {
                    "STRATEGY_OUTPUT",
                    "LEGACY_JQ_RAW_CN",
                    "EXPERIMENTAL_WINDOW_RAW",
                    "STRATEGY_DATA_PLANE_ADDITIONS",
                    "FORENSIC_CANARY",
                    "EXPERIMENT_CANARY",
                }
            )
            if plane_shaped:
                shared_family = False
            rec["shared_family_root"] = bool(shared_family)
            if shared_family and not rec.get("product_dir_resolved"):
                rec["status"] = "PRODUCT_DIR_UNRESOLVED"
                rec["measurement"] = {
                    "mode": "NOT_MEASURED_AMBIGUOUS_FAMILY_ROOT",
                    "family_dirs": family_dirs,
                    "note": (
                        "the R3 root is a multi-product family directory; no defensible "
                        "product subdirectory was resolved, so no product-specific range "
                        "is claimed"
                    ),
                }
                measured_layers[layer_name] = rec
                continue

            files = list_parquet(measure_root)
            rec["n_parquet_now"] = len(files)
            rec["measured_root"] = measure_root
            if len(files) == 0:
                rec["status"] = "EMPTY_DIRECTORY"
                rec["measurement"] = {"mode": "EMPTY", "n_files_total": 0}
            else:
                rec["status"] = "MEASURED"
                rec["measurement"] = scan_files(files)
                if plane_shaped and len(family_dirs) > 1:
                    rec["measurement"] = dict(
                        rec["measurement"],
                        scope="WHOLE_PLANE_UNION",
                        scope_note=(
                            "this dataset's identity is the plane itself; the range is the "
                            "union over its source subdirectories, not a single product bound"
                        ),
                    )
            # The R3 CACHE root is the whole release, so measuring it per dataset
            # yields the same total for every dataset. Keep the number but mark the
            # scope; the authoritative per-dataset figure is `cache_products`.
            if (
                layer_name == "CACHE"
                and root
                and os.path.normcase(os.path.abspath(root)) == os.path.normcase(os.path.abspath(CACHE_RELEASE))
            ):
                rec["status"] = "MEASURED_RELEASE_ROOT_ONLY"
                rec["measurement"] = dict(
                    rec.get("measurement") or {},
                    scope="ENTIRE_CACHE_RELEASE",
                    scope_note=(
                        "not a per-dataset figure: every dataset sharing the release root reports the same "
                        "total; read cache_products for this dataset's own rows/range"
                    ),
                )
            measured_layers[layer_name] = rec

        # product-level CACHE measurement where the registry points at a release root
        if ds_id in CACHE_PRODUCTS:
            prod_recs = []
            for prod in CACHE_PRODUCTS[ds_id]:
                proot = os.path.join(CACHE_RELEASE, prod)
                if not os.path.isdir(proot):
                    prod_recs.append({"product": prod, "status": "PRODUCT_DIR_ABSENT"})
                    continue
                pfiles = list_parquet(proot)
                m = scan_files(pfiles) if pfiles else {"mode": "EMPTY", "n_files_total": 0}
                prod_recs.append({"product": prod, "n_parquet": len(pfiles), "measurement": m})
            entry["cache_products"] = prod_recs

        # clean product-level measurement for price families
        if ds_id in ("PRICE_STOCK_DAILY",):
            croot = os.path.join(CLEAN_RELEASE, "standard", "price", "stock_ohlcv_daily")
            if os.path.isdir(croot):
                cfiles = list_parquet(croot)
                entry["clean_products"] = [
                    {"product": "stock_ohlcv_daily", "n_parquet": len(cfiles),
                     "measurement": scan_files(cfiles) if cfiles else {"mode": "EMPTY"}}
                ]

        entry["layers"] = measured_layers

        # writer / update basis
        if ds_id in BLOCKED_PLANE:
            bp = BLOCKED_PLANE[ds_id]
            entry["update_basis"] = {
                "status": bp["status"],
                "predicate": bp["predicate"],
                "required_input": bp["required_input"],
                "cursor": "UNRESOLVED",
            }
            entry["readiness"] = bp["status"]
        elif ds_id in NOT_APPLICABLE:
            entry["update_basis"] = {
                "status": "NOT_APPLICABLE",
                "contract": NOT_APPLICABLE[ds_id],
                "cursor": "NOT_APPLICABLE",
            }
            entry["readiness"] = "NOT_APPLICABLE_WITH_CONTRACT"
        else:
            row_id, note = WRITER_MAP.get(ds_id, (None, "no writer row bound for this dataset identity"))
            row = wcb_rows.get(row_id or "", {})
            entry["update_basis"] = build_update_basis(entry, row, row_id, note)
            entry["readiness"] = readiness_of(entry)

        entry["accepted_evidence_refs"] = refs_for(ds_id)
        datasets.append(entry)

    out = {
        "artifact": "DATASET_STATE",
        "task_id": "BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025",
        "generated_at_cn": datetime.now().astimezone().isoformat(),
        "built_from": {
            "r3_registry": {"path": R3_PATH, "n_datasets": len(r3["datasets"])},
            "writer_cursor_bindings": {"path": WCB_PATH, "artifact": wcb.get("artifact")},
            "cache_release": CACHE_RELEASE,
            "clean_release": CLEAN_RELEASE,
        },
        "measurement_policy": {
            "full_footer": "every parquet footer in the layer root was read; min/max is exact for the measured column",
            "stratified_sample": "only the sampled files were read; min/max is an outer bound, not completeness",
            "min_max_is_not_completeness": True,
            "no_filename_date_inference": True,
            "product_specific_over_shared_root": (
                "where the R3 root is a multi-product family directory, only the resolved "
                "product subdir is measured; unresolved products report PRODUCT_DIR_UNRESOLVED "
                "instead of the family-wide bound"
            ),
            "time_column_union": (
                "the time column is resolved from the union of sampled schemas, so a mixed "
                "family root does not lose its date axis"
            ),
            "time_role_separation": (
                "CALENDAR_AXIS / PERIOD_END_REFERENCE / ANNOUNCEMENT_TIME / AVAILABILITY_TIME are "
                "not EVENT_TIME; only an EVENT_TIME or CALENDAR_AXIS range is reported as an "
                "observed date range"
            ),
            "completeness_claim_allowed": False,
        },
        "counts": {
            "datasets": len(datasets),
            "measured_layers": sum(
                1
                for d in datasets
                for l in d["layers"].values()
                if str(l.get("status", "")).startswith("MEASURED")
            ),
            "product_dir_unresolved_layers": sum(
                1
                for d in datasets
                for l in d["layers"].values()
                if str(l.get("status", "")) == "PRODUCT_DIR_UNRESOLVED"
            ),
            "not_applicable": sum(1 for d in datasets if d["readiness"] == "NOT_APPLICABLE_WITH_CONTRACT"),
            "blocked": sum(1 for d in datasets if d["readiness"].startswith("BLOCKED")),
            "unresolved_scope": sum(1 for d in datasets if d["readiness"] == "UNRESOLVED_SCOPE"),
            "cursor_blocked": sum(1 for d in datasets if d["readiness"] == "PARTIAL_READABLE_CURSOR_BLOCKED"),
        },
        "datasets": datasets,
        "elapsed_seconds": round(time.time() - t0, 1),
    }
    out_dir = os.path.join(TASK_ROOT, "deliverables")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "DATASET_STATE.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(json.dumps(out["counts"], ensure_ascii=False), "elapsed", out["elapsed_seconds"])


def build_update_basis(entry: Dict[str, Any], row: Dict[str, Any], row_id: Optional[str], note: str) -> Dict[str, Any]:
    observed = None
    non_event_axes: List[Dict[str, Any]] = []
    for layer_name in ("CACHE", "CLEAN", "RAW"):
        layer = entry["layers"].get(layer_name) or {}
        m = layer.get("measurement") or {}
        role = str(m.get("time_role") or "")
        if m.get("max") and role in ("EVENT_TIME", "CALENDAR_AXIS"):
            if observed is None:
                observed = {
                    "layer": layer_name,
                    "max": m["max"],
                    "min": m.get("min"),
                    "basis": m.get("mode"),
                    "time_column": m.get("time_column"),
                    "time_role": role,
                    "range_basis": "FOOTER_MIN_MAX_OUTER_BOUND_NOT_COMPLETENESS",
                }
        elif m.get("max"):
            # Period-end / announcement / validity axes are metadata columns. Report
            # them under their own role so they are never read as an observed range.
            non_event_axes.append(
                {
                    "layer": layer_name,
                    "time_column": m.get("time_column"),
                    "time_role": role,
                    "min": m.get("min"),
                    "max": m.get("max"),
                }
            )
    checkpoint = (row or {}).get("checkpoint") or {}
    consumer = (row or {}).get("downstream_consumer") or {}
    cursor_status = "NOT_BOUND"
    if checkpoint.get("writer") == "NOT_APPLICABLE_BY_CONSTRUCTION":
        cursor_status = "NOT_APPLICABLE"
    boundary = None
    cache_current = r"E:\BLACKBOX\数据\回测缓存\CURRENT_CACHE_RELEASE.json"
    if os.path.exists(cache_current):
        try:
            cur = json.loads(open(cache_current, encoding="utf-8").read())
            boundary = f"CACHE release asof {cur.get('asof')} ({cur.get('release_id')})"
        except Exception:
            boundary = None
    return {
        "status": "PARTIAL_BINDING",
        "writer_row_id": row_id,
        "writer_note": note,
        "writer_callable": (row or {}).get("callable"),
        "writer_output": (row or {}).get("output"),
        "downstream_consumer": consumer,
        "observed_max": observed,
        "non_event_axes": non_event_axes,
        "last_demonstrated_complete_unit": None,
        "downstream_processed_boundary": boundary,
        "cursor": cursor_status,
        "blocked_predicate": (
            "no retained entry invokes the writer; no checkpoint/file/content cursor is emitted by the writer body"
            if cursor_status == "NOT_BOUND"
            else None
        ),
        "required_input": (
            "an authorised per-dataset start date plus a validated overlap window, or a writer that emits a content-identity cursor"
            if cursor_status == "NOT_BOUND"
            else None
        ),
        "no_common_start_20260924": True,
    }


def readiness_of(entry: Dict[str, Any]) -> str:
    layers = entry["layers"]
    any_measured = any(str(l.get("status", "")).startswith("MEASURED") for l in layers.values()) or any(
        (p.get("measurement") or {}).get("mode", "").startswith(("FULL_FOOTER", "STRATIFIED"))
        for p in (entry.get("cache_products") or [])
    )
    if not any_measured:
        return "BLOCKED_NO_LAYER_MEASURED"
    basis = entry.get("update_basis") or {}
    if basis.get("cursor") == "NOT_BOUND":
        return "PARTIAL_READABLE_CURSOR_BLOCKED"
    return "READABLE_CURSOR_NOT_APPLICABLE"


def refs_for(ds_id: str) -> List[str]:
    refs = ["ECOLOGY_REGISTRY_R3.json"]
    if ds_id in ("PRICE_STOCK_DAILY", "PRICE_STOCK_1M", "TRADABLE_STATUS", "ADJUST_FACTOR"):
        refs.append("candidate_releases/R06/R06_TWO_DAY_RECOVERY_20261024 (2026-08-31/09-01 price recovery)")
        refs.append("candidate_releases/R08/R08_OBSERVED_STOCK_DERIVED_RECOVERY_20261024 (factor/market structure)")
    refs.append("r10_writer_cursor_bindings_delivery/ACQUISITION_WRITER_CURSOR_BINDINGS.json")
    refs.append("RESTART_READINESS_REVIEW_20261024 (ENVIRONMENT_PROBE/GATE_PROBE)")
    return refs


if __name__ == "__main__":
    main()
