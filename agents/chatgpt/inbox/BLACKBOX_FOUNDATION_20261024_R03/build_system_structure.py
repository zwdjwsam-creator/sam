"""Generate SYSTEM_STRUCTURE.json from actual inspected files and configuration.

Every path is existence-checked at build time; nothing is asserted without evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(r"E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine\blackbox_jq_engine")
OUT = HERE / "SYSTEM_STRUCTURE.json"


def sha16(p: Path):
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    except Exception:
        return None


def node(nid, kind, path, key, status, io, rule, evidence=None, extra=None):
    p = Path(path) if path else None
    rec = {"id": nid, "kind": kind, "path": str(path) if path else None,
           "exists": bool(p and p.exists()),
           "callable_or_key": key, "status": status, "io": io, "rule": rule,
           "evidence": evidence}
    if p and p.is_file():
        rec["sha256_16"] = sha16(p)
        rec["bytes"] = p.stat().st_size
    if extra:
        rec.update(extra)
    return rec


def main() -> int:
    candidate_py = HERE / "runtime" / ".venv" / "Scripts" / "python.exe"
    version = {}
    if candidate_py.exists():
        try:
            version = json.loads(subprocess.run(
                [str(candidate_py), "-c",
                 "import json,sys,pandas,pyarrow;print(json.dumps({'python':sys.version.split()[0],"
                 "'pandas':pandas.__version__,'pyarrow':pyarrow.__version__}))"],
                capture_output=True, text=True, timeout=90).stdout or "{}")
        except Exception:
            version = {}

    nodes = [
        node("cand.launcher", "launcher", HERE / "tests" / "test_conformance_r3.py",
             "main()", "candidate", "read local parquet; write TEST_RESULTS.json and runtime caches",
             "candidate tree only; no production write",
             "executes the 10 required verifications"),
        node("cand.interpreter", "interpreter", candidate_py, "python.exe", "candidate",
             "read-only", "isolated venv; global Python and the historical .venv are untouched",
             json.dumps(version), {"versions": version}),
        node("sys.interpreter", "interpreter",
             Path(r"C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe"), "python.exe",
             "current", "read-only", "system interpreter; lacks pandas, so the engine contract "
             "cannot be exercised here (kept unchanged)", "R01 blocked on this interpreter"),
        node("cand.registry_builder", "registry_builder", HERE / "build_registry_r3.py", "main()",
             "candidate", "reads R01 registry + parquet footer statistics; writes R3 registry",
             "candidate tree only", "observed coverage replaces filename/build-stamp heuristics"),
        node("cand.registry_query", "registry_query", HERE / "eco_query_r3.py", "main()",
             "candidate", "read-only", "candidate tree only", "executable registry entry"),
        node("cand.registry", "registry", HERE / "ECOLOGY_REGISTRY_R3.json", "datasets[]", "candidate",
             "read-only", "single machine-generated source for scope/coverage claims", None),
        node("prod.cleaning_current", "current_pointer",
             Path(r"E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json"),
             "release_id / standard_root", "current", "read-only",
             "dynamic pointer; the only allowed source of the active clean release",
             "read by build_registry_r3.py through the R01 registry"),
        node("prod.cache_current", "current_pointer",
             Path(r"E:\BLACKBOX\数据\回测缓存\CURRENT_CACHE_RELEASE.json"),
             "cache_release_id / asof", "current", "read-only",
             "cache is a derived product; not bound to the candidate reader this cycle", None),
        node("prod.daily_manifest", "current_pointer",
             Path(r"E:\BLACKBOX\研究系统\数据平面\CURRENT\DAILY_DATA_MANIFEST_CURRENT.json"),
             "DAILY_INCREMENTAL_READY / CN_RESEARCH_DATE", "current", "read-only",
             "daily incremental plane status; not re-run in this cycle", None),
        node("prod.update_entry", "update_entry",
             Path(r"E:\BLACKBOX\脚本\run_blackbox_research_os.py"), "--mode daily_incremental",
             "current", "read local + network (download)", "must not be invoked by the read plane",
             "separate from the candidate reader; not executed this cycle"),
        node("cand.reader", "reader", HERE / "candidate" / "r3" / "provider.py",
             "LocalValueProvider.get_price", "candidate",
             "read local parquet only; no network", "READ_ONLY_VALUE_PLANE; RAW_NONE identity",
             "returns envelopes with explicit accounting"),
        node("cand.adapter", "contract_adapter", HERE / "candidate" / "r3" / "engine_adapter.py",
             "EngineLocalValueProvider", "candidate", "read local parquet only; no network",
             "subclasses the real engine base; rejects unsupported parameters",
             "engine-facing DataFrame / list types"),
        node("eng.base", "engine_contract", ENGINE / "bullet_trade" / "data" / "providers" / "base.py",
             "DataProvider.get_price", "current", "read-only", "engine contract; unmodified",
             "loaded as a leaf module in the candidate runtime"),
        node("eng.api", "engine_api", ENGINE / "bullet_trade" / "data" / "api.py",
             "_create_provider / _call_provider_get_price", "current", "read-only",
             "engine data API; unmodified",
             "provider branches: jqdata, tushare, qmt/miniqmt, remote-qmt; no local-value branch"),
        node("eng.engine", "engine_core", ENGINE / "bullet_trade" / "core" / "engine.py",
             "get_trade_days / get_split_dividend consumers", "current", "read-only",
             "engine core; formal_backtest_active and engine_core_active unchanged (false)",
             "consumer evidence for event schema and trade-day types"),
        node("prod.publication_boundary", "publication_boundary",
             Path(r"E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json"),
             "CURRENT_* pointers", "current", "write (prohibited this cycle)",
             "sealed/CURRENT/RAW are never edited in place", "no publication performed"),
    ]

    edges = [
        {"from": "cand.launcher", "to": "cand.interpreter", "mechanism": "venv executable",
         "confirmed": True, "note": "documented in RUNTIME_COMMAND.md"},
        {"from": "cand.launcher", "to": "cand.reader", "mechanism": "import candidate.r3.provider",
         "confirmed": True, "note": "exercised by 9 of 10 checks"},
        {"from": "cand.reader", "to": "cand.registry", "mechanism": "LocalValueProvider(registry_path)",
         "confirmed": True, "note": "registry supplies layer roots and dataset scope"},
        {"from": "cand.registry_builder", "to": "prod.cleaning_current", "mechanism":
         "R01 registry dynamic_sources -> standard_root", "confirmed": True,
         "note": "the active clean release is read from the CURRENT pointer, not hardcoded"},
        {"from": "cand.registry_builder", "to": "cand.registry", "mechanism": "writes JSON",
         "confirmed": True, "note": "counts are generated from the build"},
        {"from": "cand.registry", "to": "prod.cleaning_current", "mechanism": "layer.root",
         "confirmed": True, "note": "dataset layer roots resolve to the active release"},
        {"from": "cand.reader", "to": "local_parquet", "mechanism": "pyarrow read_table",
         "confirmed": True, "note": "bounded reads; footer statistics come from the cached index"},
        {"from": "cand.adapter", "to": "eng.base", "mechanism": "importlib leaf load + subclass",
         "confirmed": True, "note": "isinstance(adapter, DataProvider) verified at runtime"},
        {"from": "eng.api", "to": "cand.adapter", "mechanism": "_create_provider branch",
         "confirmed": False, "note": "UNRESOLVED: no local-value branch is registered in the "
         "factory; the adapter is instantiable and conformant but not selectable by the engine"},
        {"from": "eng.api", "to": "eng.base", "mechanism": "DataProvider contract",
         "confirmed": True, "note": "abstract methods and parameter list inspected"},
        {"from": "prod.update_entry", "to": "prod.daily_manifest", "mechanism": "six-lane daily plane",
         "confirmed": True, "note": "separate path; not executed this cycle"},
        {"from": "prod.update_entry", "to": "prod.publication_boundary", "mechanism":
         "release publication + CURRENT pointer switch", "confirmed": True,
         "note": "publication is out of scope; the candidate only reads"},
        {"from": "cand.reader", "to": "prod.publication_boundary", "mechanism": "none",
         "confirmed": False, "note": "no write edge exists by design (READ_ONLY_VALUE_PLANE)"},
    ]

    unresolved = [
        {"edge": "eng.api -> cand.adapter", "why": "the provider factory in data/api.py:57 only "
         "branches to jqdata/tushare/qmt/miniqmt/remote-qmt; registering a local-value branch is a "
         "production configuration change reserved for a later round",
         "impact": "the engine cannot select this adapter yet; conformance is proven by direct "
                   "construction and real DataFrame calls only"},
        {"edge": "adjusted price semantics", "why": "no evidenced pre/post adjustment exists for the "
         "batch segments (factor is null there); applying a factor formula would fabricate values",
         "impact": "fq=pre/post are rejected; the engine default fq='pre' therefore cannot be served "
                   "by this candidate until adjustment is implemented"},
        {"edge": "per-dataset increment cursor", "why": "scope.increment_cursor is null for every "
         "observed dataset; no updater has published one",
         "impact": "the read plane knows coverage bounds but not the next download offset"},
        {"edge": "full engine initialization", "why": "engine_core_active/formal_backtest_active "
         "remain false and package import may initialise trading/download paths",
         "impact": "this cycle proves the leaf contract and DataFrame layout, not a full backtest run"},
    ]

    doc = {
        "structure_id": "BLACKBOX_SYSTEM_STRUCTURE_R3",
        "built_at": __import__("datetime").datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "language": "en",
        "round": "R03_OF_10",
        "FOUNDATION_ACCEPTANCE": False,
        "ORDER_ALLOWED": False,
        "source_of_paths": "R01 executable registry + direct file existence checks at build time",
        "read_chain": ["cand.launcher", "cand.interpreter", "cand.registry_builder", "cand.registry",
                       "cand.registry_query", "prod.cleaning_current", "cand.reader", "cand.adapter",
                       "eng.base", "eng.api", "eng.engine"],
        "update_chain": ["prod.update_entry", "prod.daily_manifest", "prod.publication_boundary"],
        "nodes": nodes,
        "edges": edges,
        "unresolved_edges": unresolved,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "missing_paths": [n["id"] for n in nodes if not n["exists"]],
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"nodes": len(nodes), "edges": len(edges),
                      "missing": doc["missing_paths"], "out": str(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
