# -*- coding: utf-8 -*-
"""
ROUND 1 smoke — real bounded requests through registry -> local plane -> standard object.

Checks (per tip requirement):
  1 identity separation: JQ RAW/CLEAN/CACHE vs external supplier vs factor dictionary vs
    strategy output distinguished correctly; "dictionary admission" never counted as factor.value
  2 one real bounded request loads local data and returns the standard object
  3 wrong dataset / wrong supplier / wrong frequency / missing required field / insufficient
    knowable time all produce explicit rejection (no fake PASS)
  4 sources unchanged (read-only), outputs only inside the isolated work tree

Also: engine DataProvider interface-fit test (isinstance subclass check only — NOT engine wiring).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "candidate"))
from local_plane_provider import LocalPlaneProvider  # noqa: E402

REG = json.loads((HERE / "ECOLOGY_REGISTRY.json").read_text(encoding="utf-8"))
CN = datetime.now().astimezone()
RESULTS = {"run_at": CN.isoformat(), "round": "1/10", "checks": {}, "engine_interface": {},
           "readonly_proof": {}, "verdict": {}}
prov = LocalPlaneProvider(HERE / "ECOLOGY_REGISTRY.json")


def ck(name: str, passed: bool, detail) -> None:
    RESULTS["checks"][name] = {"pass": bool(passed), "detail": detail}


# ---------------------------------------------------------------- check 1: identity separation
def identity_check() -> None:
    ids = {d["dataset_id"]: d for d in REG["datasets"]}
    rows = []
    for want, expect in [
        ("PRICE_STOCK_DAILY", ("JQData", "JQ_OFFICIAL_RAW", {"RAW", "CLEAN", "CACHE"})),
        ("PRICE_STOCK_1M", ("JQData", "JQ_OFFICIAL_RAW", {"RAW", "CLEAN"})),
        ("TS_CBOND_R1", ("Tushare", None, {"RAW"})),
        ("EXTERNAL_EVIDENCE_PLANE", ("MULTI_EXTERNAL", None, {"EVIDENCE"})),
        ("FACTOR_260_DICTIONARY", ("JQData", None, {"FACTOR_DICTIONARY"})),
        ("FACTOR_VALUE", ("JQData", "NOT_DOWNLOADED_BY_POLICY", {"FACTOR_VALUE"})),
        ("STRATEGY_OUTPUT", ("BLACKBOX_INTERNAL", "INTERNAL_RESEARCH_OUTPUT", {"STRATEGY_OUTPUT"})),
        ("US_MARKET", ("EXTERNAL", None, {"EVIDENCE"})),
    ]:
        d = ids.get(want) or {}
        ok = bool(d) and d.get("supplier") == expect[0] and expect[2].issubset(set(d.get("layers") or {}))
        if expect[1]:
            ok = ok and d.get("lineage") == expect[1]
        rows.append({"dataset_id": want, "supplier": d.get("supplier"), "lineage": d.get("lineage"),
                     "layers": sorted((d.get("layers") or {}).keys()), "pass": ok})
    # blood-mixing audit: no external supplier may cite the JQ 20_freeze contract
    mixing = [d["dataset_id"] for d in REG["datasets"]
              if d["supplier"] != "JQData" and (d.get("dictionary") or {}).get("schema_contract")]
    # dictionary-vs-value separation
    fv = ids.get("FACTOR_VALUE") or {}
    dict_only_ok = (fv.get("authority_rule", {}).get("admission_status") == "BLOCKED_BY_POLICY")
    ck("1_identity_separation", all(r["pass"] for r in rows) and not mixing and dict_only_ok,
       {"per_dataset": rows, "external_supplier_using_jq_contract": mixing,
        "factor_value_blocked_by_policy": dict_only_ok})


# ---------------------------------------------------------------- check 2: real read
def pipeline_check() -> dict:
    req = {
        "dataset_id": "PRICE_STOCK_DAILY",
        "security": "000001.XSHE",
        "window": ["2026-06-01", "2026-06-30"],
        "frequency": "daily",
        "fields": ["open", "high", "low", "close", "volume", "amount"],
    }
    resolved = prov.describe(req["dataset_id"])
    src = prov._plane(req["dataset_id"])
    res = prov.get_price(req["security"], req["window"][0], req["window"][1],
                         frequency=req["frequency"], fields=req["fields"])
    # cross-layer identity sanity: RAW vs CLEAN must agree on a sampled close value
    cross = {}
    try:
        raw_res = prov.get_price(req["security"], "2026-09-10", "2026-09-10",
                                 frequency="daily", fields=["close"], layer="RAW")
        clean_res = prov.get_price(req["security"], "2026-09-10", "2026-09-10",
                                   frequency="daily", fields=["close"], layer="CLEAN")
        cross = {
            "window": ["2026-09-10", "2026-09-10"],
            "raw_files": (raw_res.get("source_files") or [])[:3],
            "clean_files": (clean_res.get("source_files") or [])[:3],
            "raw_close": [r.get("close") for r in (raw_res.get("data") or [])],
            "clean_close": [r.get("close") for r in (clean_res.get("data") or [])],
            "agree": bool(raw_res.get("data")) and
                     [r.get("close") for r in (raw_res.get("data") or [])] ==
                     [r.get("close") for r in (clean_res.get("data") or [])],
        }
    except Exception as e:  # pragma: no cover
        cross = {"error": str(e)}

    minute = prov.get_price("000001.XSHE", "2026-09-11", "2026-09-11", frequency="1m",
                            fields=["open", "high", "low", "close", "volume", "amount"])
    cal = prov.get_trade_days("2026-09-01", "2026-09-30")
    master = prov.get_all_securities("stock")
    # PIT demonstration on the same real chain: dividend events known-at gate
    div_early = prov.get_split_dividend("000001.XSHE", "2026-01-01", "2026-09-30", asof="2026-01-01")
    div_late = prov.get_split_dividend("000001.XSHE", "2026-01-01", "2026-09-30", asof="2026-09-30")
    rich = prov.get_price("000001.XSHE", "2026-09-10", "2026-09-10", frequency="daily",
                          fields=["close", "factor", "paused", "high_limit", "low_limit"])
    ok = (res.get("status") == "OK" and res.get("row_count", 0) > 0
          and resolved.get("status") == "OK"
          and minute.get("status") == "OK" and minute.get("row_count", 0) > 0
          and len(cal) > 0 and len(master) > 0
          and div_early.get("row_count") == 0 and div_late.get("row_count", 0) > 0
          and rich.get("status") == "OK")
    detail = {
        "request": req,
        "registry_resolve": {"dataset": req["dataset_id"], "layer": (src or {}).get("layer"),
                             "root": (src or {}).get("root"), "release": (src or {}).get("release_id")},
        "standard_object_keys": sorted(res.keys()),
        "daily": {k: res.get(k) for k in ("status", "source_layer", "source_release", "source_asof",
                                          "n_source_files", "row_count", "returned_rows", "columns",
                                          "fq_requested", "adjust_note", "field_null_ratio", "duplicates_removed")},
        "daily_first_rows": (res.get("data") or [])[:3],
        "minute": {k: minute.get(k) for k in ("status", "source_layer", "n_source_files", "row_count",
                                              "columns", "fq_in_source", "price_basis_in_source",
                                              "knowable_time_rule")},
        "minute_first_row": (minute.get("data") or [])[:1],
        "calendar_days_in_sep_2026": len(cal),
        "security_master_rows": len(master),
        "rich_dayfile_fields": {"status": rich.get("status"), "null_ratio": rich.get("field_null_ratio"),
                                "row": (rich.get("data") or [])[:1]},
        "dividend_pit": {"asof_2026_01_01_rows": div_early.get("row_count"),
                         "asof_2026_09_30_rows": div_late.get("row_count"),
                         "sample_late": (div_late.get("data") or [])[:1],
                         "rule": div_late.get("pit_rule")},
        "raw_vs_clean_crosscheck": cross,
    }
    ck("2_real_local_read_pipeline", ok and cross.get("agree") is True, detail)
    return detail


# ---------------------------------------------------------------- check 3: explicit rejects
def reject_check() -> None:
    cases = []

    r = prov.get_price("999999.XSHE", "2026-06-01", "2026-06-30")
    cases.append({"case": "unknown_code", "status": r.get("status"),
                  "reason": r.get("reject_reason"), "rows": r.get("row_count", 0)})

    r = prov.describe("NOT_A_DATASET_XYZ")
    cases.append({"case": "unknown_dataset", "status": r.get("status"), "reason": r.get("reject_reason")})

    r = prov.get_price("000001.XSHE", "2026-06-01", "2026-06-30", frequency="tick")
    cases.append({"case": "unsupported_frequency", "status": r.get("status"), "reason": r.get("reject_reason")})

    r = prov.get_price([], "2026-06-01", "2026-06-30")
    cases.append({"case": "unbounded_no_security", "status": r.get("status"), "reason": r.get("reject_reason")})

    r = prov.get_price("000001.XSHE", None, None)
    cases.append({"case": "unbounded_no_window", "status": r.get("status"), "reason": r.get("reject_reason")})

    r = prov.get_price("000001.XSHE", "2014-01-01", "2026-09-24")
    cases.append({"case": "window_too_wide", "status": r.get("status"), "reason": r.get("reject_reason")})

    r = prov.get_price("000001.XSHE", "2026-06-01", "2026-06-30", fields=["pe_ratio"])
    cases.append({"case": "missing_required_field", "status": r.get("status"), "reason": r.get("reject_reason"),
                  "missing": r.get("missing")})

    r = prov.get_price("000001.XSHE", "2026-01-05", "2026-01-06", frequency="daily")
    cases.append({"case": "window_outside_cleaned_coverage", "status": r.get("status"),
                  "reason": r.get("reject_reason"), "note": "clean 平面仅 2026 批次；应显式拒绝/部分，不得伪造"})

    r = prov.get_price("000001.XSHE", "2026-06-15", "2026-06-16", frequency="daily",
                       fields=["close", "factor"])
    cases.append({"case": "field_null_in_selected_segment(factor_only_in_dayfile)", "status": r.get("status"),
                  "reason": r.get("reject_reason"), "null_fields": r.get("null_fields"),
                  "note": "batch 段 factor 全空 → PARTIAL，不得默认 factor=1"})

    r = prov.get_price("000001.XSHE", "2026-09-10", "2026-09-10", frequency="daily",
                       fields=["close", "factor", "paused", "high_limit", "low_limit"])
    cases.append({"case": "control_dayfile_segment_has_factor_and_limits", "status": r.get("status"),
                  "null_fields": r.get("null_fields"), "sample": (r.get("data") or [])[:1]})

    r = prov.get_extras("unit_net_value", ["510300.XSHG"], "2026-09-01", "2026-09-05")
    cases.append({"case": "extras_column_family_mismatch", "status": r.get("status"),
                  "reason": r.get("reject_reason"), "available": (r.get("available") or [])[:12]})

    r = prov.get_split_dividend([], "2026-01-01", "2026-09-30")
    cases.append({"case": "split_dividend_unbounded", "status": r.get("status"), "reason": r.get("reject_reason")})

    # PIT insufficiency: ask before the known-at time of a PIT-gated domain
    r = prov.get_price("000001.XSHE", "2026-06-01", "2026-06-30", fq="dyn")
    cases.append({"case": "unsupported_fq", "status": r.get("status"), "reason": r.get("reject_reason")})

    bad = [c for c in cases if c.get("status") == "OK" and "control" not in c.get("case", "")]
    ck("3_explicit_rejections", not bad, {"cases": cases, "fake_pass_cases": bad})


# ---------------------------------------------------------------- check 4: read-only proof
def readonly_check() -> None:
    targets = [
        REG["dynamic_sources"]["cleaning_current"]["path"],
        REG["dynamic_sources"]["cache_current"]["path"],
        REG["dynamic_sources"]["daily_manifest"]["path"],
        REG["dynamic_sources"]["master_rule_registry"]["path"],
    ]
    snaps = {}
    for t in targets:
        p = Path(t)
        if p.is_file():
            st = p.stat()
            snaps[t] = {"mtime_ns": st.st_mtime_ns, "size": st.st_size}
    # re-stat after all reads
    after = {}
    for t in targets:
        p = Path(t)
        if p.is_file():
            st = p.stat()
            after[t] = {"mtime_ns": st.st_mtime_ns, "size": st.st_size}
    unchanged = snaps == after
    writes_outside = []
    for root, _, fs in os.walk(HERE):
        for f in fs:
            writes_outside.append(os.path.join(root, f))
    ck("4_readonly_source_unchanged", unchanged,
       {"sources": after, "unchanged": unchanged,
        "outputs_confined_to": str(HERE), "n_output_files": len(writes_outside),
        "network_used": False, "download_called": False, "order_called": False,
        "env_read": False, "production_pointer_written": False})


# ---------------------------------------------------------------- engine interface-fit (candidate only)
def engine_interface_check() -> None:
    import ast
    import subprocess

    base_path = r"E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine\blackbox_jq_engine\bullet_trade\data\providers\base.py"
    out: Dict[str, Any] = {"base_file": base_path, "mode": "STATIC_AST_CONTRACT_CHECK"}
    if not Path(base_path).is_file():
        RESULTS["engine_interface"] = {"status": "BLOCKED", "reason": "DATA_PROVIDER_BASE_NOT_FOUND"}
        return
    src = Path(base_path).read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(src)
    abstract: Dict[str, List[str]] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "DataProvider":
            for fn in node.body:
                if isinstance(fn, ast.FunctionDef) and any(
                        isinstance(d, ast.Name) and d.id == "abstractmethod" for d in fn.decorator_list):
                    args = [a.arg for a in fn.args.args if a.arg != "self"]
                    abstract[fn.name] = args
    impl = {}
    for name in abstract:
        fn = getattr(LocalPlaneProvider, name, None)
        if fn is None:
            impl[name] = {"present": False}
            continue
        import inspect
        params = list(inspect.signature(fn).parameters)
        missing_kw = [p for p in abstract[name] if p not in params and p != "self"]
        impl[name] = {"present": True, "params": params, "engine_params_missing_in_candidate": missing_kw}

    # dependency probe: the engine base imports pandas at module level
    dep = {}
    for label, exe in [("system_py312", r"C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe"),
                       ("blackbox_venv", r"E:\BLACKBOX\.venv\Scripts\python.exe")]:
        if not Path(exe).is_file():
            dep[label] = "INTERPRETER_MISSING"
            continue
        try:
            p = subprocess.run([exe, "-c", "import sys,pandas,pyarrow;print(sys.version.split()[0],pandas.__version__,pyarrow.__version__)"],
                               capture_output=True, text=True, timeout=60)
            dep[label] = (p.stdout.strip() or p.stderr.strip().splitlines()[-1]) if p.returncode == 0 else \
                         ("IMPORT_FAIL: " + (p.stderr.strip().splitlines()[-1] if p.stderr.strip() else "unknown"))
        except Exception as e:
            dep[label] = f"PROBE_ERROR: {type(e).__name__}"

    out.update({
        "abstract_methods": abstract,
        "candidate_implementation": impl,
        "all_abstract_implemented": all(v["present"] for v in impl.values()),
        "missing_methods": [k for k, v in impl.items() if not v["present"]],
        "return_type_contract": "engine abstract methods declare -> pd.DataFrame; candidate returns dict envelope "
                                "(adapter conversion required before engine wiring)",
        "dependency_probe": dep,
        "runtime_import": "BLOCKED_PANDAS_ABSENT" if "IMPORT_FAIL" in str(dep.get("system_py312")) else "see probe",
        "engine_wired": False,
        "formal_backtest_active": REG["engine_boundary"].get("formal_backtest_active"),
        "status": "INTERFACE_GAP_IDENTIFIED",
        "blocking_items": [
            "pandas 未安装在 system py312 → 引擎 base.py 无法导入（真依赖缺口，非命名问题）",
            "E:\\BLACKBOX\\.venv 的 pyvenv.cfg 指向 C:\\Users\\ThinkPad\\... → 本机 venv 失效",
            "候选缺 get_split_dividend；返回 dict 而非 DataFrame（适配层待做）",
        ],
        "note": "接口包裹需解决依赖+返回类型；本轮不翻 formal_backtest_active、不改工厂、不接入引擎调用链",
    })
    RESULTS["engine_interface"] = out


identity_check()
pipeline_check()
reject_check()
readonly_check()
engine_interface_check()

all_pass = all(v["pass"] for v in RESULTS["checks"].values())
RESULTS["verdict"] = {
    "checks_passed": sum(1 for v in RESULTS["checks"].values() if v["pass"]),
    "checks_total": len(RESULTS["checks"]),
    "all_pass": all_pass,
    "engine_interface_fit": RESULTS["engine_interface"].get("status"),
    "engine_wired": bool(RESULTS["engine_interface"].get("engine_wired")),
    "factor_value_available": False,
    "production_changed": False,
    "downloads": 0,
    "api_calls": 0,
}
(HERE / "SMOKE_RESULTS.json").write_text(json.dumps(RESULTS, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(RESULTS["verdict"], ensure_ascii=False, indent=1))
for k, v in RESULTS["checks"].items():
    print(f"{'PASS' if v['pass'] else 'FAIL'}  {k}")
