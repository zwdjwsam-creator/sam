#!/usr/bin/env python3
"""One-shot, read-only capture of exact registered layer and dictionary metadata."""
from __future__ import annotations
import csv, hashlib, io, json, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(r"C:\LAN_SHARE_REPORT\BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1_PACKAGE")
DELIVERY = ROOT / "delivery"
ONCE = ROOT / "RUN_ONCE.json"
MAX_FILE = 8 * 1024 * 1024
MAX_TOTAL = 32 * 1024 * 1024

SESSIONS = (
    "2026-10-28","2026-10-29","2026-10-30","2026-11-02","2026-11-03",
    "2026-11-04","2026-11-05","2026-11-06","2026-11-09","2026-11-10","2026-11-11",
)

INPUTS = (
    {"id":"ecology_registry_r3","path":r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\ECOLOGY_REGISTRY_R3.json",
     "basis":"R10 DATASET_STATE.json built_from.r3_registry.path","format":"json"},
    {"id":"acquisition_writer_cursor_bindings",
     "path":r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\r10_writer_cursor_bindings_delivery\ACQUISITION_WRITER_CURSOR_BINDINGS.json",
     "basis":"R10 DATASET_STATE.json built_from.writer_cursor_bindings.path","format":"json"},
    {"id":"raw_coverage_ledger_current","path":r"E:\BLACKBOX\运行\BLACKBOX_RAW_COVERAGE_LEDGER_CURRENT.json",
     "basis":"R07 LAYER_SEARCH_AND_BINDING_LEDGER.json scope.searched_roots","format":"json"},
    {"id":"cleaning_coverage_ledger_current","path":r"E:\BLACKBOX\运行\BLACKBOX_CLEANING_COVERAGE_LEDGER_CURRENT.json",
     "basis":"R07 LAYER_SEARCH_AND_BINDING_LEDGER.json L13","format":"json"},
    {"id":"cache_coverage_ledger_current","path":r"E:\BLACKBOX\运行\BLACKBOX_CACHE_COVERAGE_LEDGER_CURRENT.json",
     "basis":"R07 LAYER_SEARCH_AND_BINDING_LEDGER.json L13","format":"json"},
    {"id":"daily_data_manifest_current","path":r"E:\BLACKBOX\研究系统\数据平面\CURRENT\DAILY_DATA_MANIFEST_CURRENT.json",
     "basis":"Owner ZHANGWEI execution baseline exact path","format":"json",
     "expected_sha256":"574842e7802be26d648d5aa2f6d91a9b4c208744e3ecf9f146e02ece41387d89",
     "sha_policy":"HISTORICAL_BASELINE_ONLY"},
    {"id":"daily_data_plane_current","path":r"E:\BLACKBOX\研究系统\数据平面\CURRENT\DAILY_DATA_PLANE_CURRENT.json",
     "basis":"Owner ZHANGWEI execution baseline exact path","format":"json",
     "expected_sha256":"8a492440257170577a5c96f66bfd81e3b93fc6dc58e547cc3acd4c7baaf3fe9b",
     "sha_policy":"HISTORICAL_BASELINE_ONLY"},
    {"id":"current_cleaning_release","path":r"E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json",
     "basis":"Retained original R15 antileak source body and P2 exact environment capture","format":"json",
     "expected_sha256":"9abad90cd952a1d623d124b794cbb0c025161cb9b80053c09980f25c0d481128",
     "sha_policy":"HISTORICAL_BASELINE_ONLY"},
    {"id":"current_cache_release","path":r"E:\BLACKBOX\数据\回测缓存\CURRENT_CACHE_RELEASE.json",
     "basis":"P2 exact environment and body capture","format":"json",
     "expected_sha256":"b2ce53f05e50e0d38c9f4232f6b5e94040d6a081066d24759e52dd60eb622564",
     "sha_policy":"HISTORICAL_BASELINE_ONLY"},
    {"id":"domain_schema_contract","path":r"E:\BLACKBOX\数据\原始只读\JQData_reference_dictionary\20_unified_data_schema_contract_freeze_full_R1\02_domain_schema\domain_schema_contract.csv",
     "basis":"P2 exact environment and normative CSV capture","format":"csv",
     "expected_sha256":"6367c574c27b7ddbb7a926e4899f59502f3febc76a4cf2b0092998d275458146",
     "sha_policy":"IMMUTABLE_PIN"},
    {"id":"pit_schema_contract","path":r"E:\BLACKBOX\数据\原始只读\JQData_reference_dictionary\20_unified_data_schema_contract_freeze_full_R1\04_pit_schema\pit_schema_contract.csv",
     "basis":"P2 exact environment and normative CSV capture","format":"csv",
     "expected_sha256":"1e62d187b6417b875f42a9b9b45fc616b3ac1d375c88f6d77116488c783e253b",
     "sha_policy":"IMMUTABLE_PIN"},
)
PATH_PREFIXES = ("E:\\BLACKBOX\\数据\\","E:\\BLACKBOX\\_OPS\\","E:\\BLACKBOX\\运行\\","E:\\BLACKBOX\\研究系统\\")

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def ptr(parent: str, token: Any) -> str:
    return parent + "/" + str(token).replace("~","~0").replace("/","~1")

def summarize_json(obj: Any) -> dict:
    products, releases, layers, hits, paths = set(), set(), set(), [], []
    session_set = set(SESSIONS)
    def walk(v: Any, p: str = "") -> None:
        if isinstance(v, dict):
            for k, x in v.items():
                q = ptr(p,k)
                if k in ("dataset_id","product_id") and isinstance(x,str): products.add(x)
                if k in ("release_id","seal_id","generation_id","cache_release_id") and isinstance(x,str): releases.add(x)
                if k in ("RAW","CLEAN","CACHE","HISTORY","SHARD","VIEW","LAYER") and isinstance(x,(dict,list)): layers.add(q)
                if isinstance(x,str):
                    for d in session_set:
                        if d in x: hits.append({"date":d,"pointer":q,"value":x[:256]})
                    if k in ("path","root","measured_root","source_path","ledger_path","manifest_path") and x.startswith(PATH_PREFIXES):
                        paths.append({"pointer":q,"value":x[:512]})
                walk(x,q)
        elif isinstance(v,list):
            for i,x in enumerate(v): walk(x,ptr(p,i))
    walk(obj)
    hits.sort(key=lambda x:(x["date"],x["pointer"]))
    paths.sort(key=lambda x:(x["pointer"],x["value"]))
    return {"top_level_keys":sorted(obj) if isinstance(obj,dict) else [],
            "product_ids":sorted(products),"release_ids":sorted(releases),
            "layer_pointers":sorted(layers),"candidate_session_literal_hits":hits,
            "registered_path_references":paths,
            "interpretation_limit":"Literal metadata references only; no row-level or source-absence conclusion."}

def summarize_csv(data: bytes) -> dict:
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    rows = list(reader)
    return {"header":reader.fieldnames or [],"row_count":len(rows),"rows":rows,
            "interpretation_limit":"Normative CSV rows captured verbatim; no unit or PIT semantics are inferred beyond explicit cells."}

def reparse_problem(path: Path) -> str | None:
    for p in reversed([path,*path.parents]):
        st = p.lstat()
        if p.is_symlink() or (getattr(st,"st_file_attributes",0) & 0x400):
            return f"REPARSE_COMPONENT_BLOCKED:{p}"
    return None

def capture(specs, root: Path, delivery: Path, max_file=MAX_FILE, max_total=MAX_TOTAL):
    once = root / "RUN_ONCE.json"
    if once.exists() or delivery.exists():
        return 4, {"status":"STOP_EXISTING_ONCE_OR_DELIVERY_ROOT"}
    root.mkdir(parents=True,exist_ok=True)
    try:
        with once.open("x",encoding="utf-8") as f:
            f.write(json.dumps({"task_id":"BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1",
                                "created_at_utc":now(),"replay_allowed":False},indent=2))
    except FileExistsError:
        return 4, {"status":"STOP_RUN_ONCE_ALREADY_EXISTS"}
    delivery.mkdir()
    cap = delivery / "capture_001"; cap.mkdir()
    rows, total, partial = [], 0, False
    for spec in specs:
        src = Path(spec["path"])
        row = {"id":spec["id"],"source_path":spec["path"],"basis":spec["basis"],
               "format":spec["format"],"expected_sha256":spec.get("expected_sha256"),
               "sha_policy":spec.get("sha_policy")}
        try:
            try: before = src.lstat()
            except FileNotFoundError:
                row["status"]="NOT_FOUND_AT_EXACT_PATH"; partial=True; rows.append(row); continue
            problem = reparse_problem(src)
            if problem:
                row.update(status="BLOCKED_PATH_COMPONENT",detail=problem); partial=True; rows.append(row); continue
            if not src.is_file():
                row["status"]="NOT_A_REGULAR_FILE"; partial=True; rows.append(row); continue
            if before.st_size > max_file:
                row.update(status="SIZE_CAP_EXCEEDED",bytes=before.st_size); partial=True; rows.append(row); continue
            if total + before.st_size > max_total:
                row.update(status="TOTAL_SIZE_CAP_EXCEEDED",bytes=before.st_size); partial=True; rows.append(row); continue
            data = src.read_bytes(); after = src.lstat()
            if data != src.read_bytes() or before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
                row["status"]="UNSTABLE_SOURCE_DURING_READ"; partial=True; rows.append(row); continue
            digest = sha(data)
            if row["expected_sha256"]:
                match = digest == row["expected_sha256"]
                row["pin_status"] = "MATCH" if match else "MISMATCH"
                if not match and row["sha_policy"] == "IMMUTABLE_PIN": partial = True
                if not match and row["sha_policy"] == "HISTORICAL_BASELINE_ONLY":
                    row["pin_status"] = "CHANGED_SINCE_HISTORICAL_BASELINE"
            dst = cap / (spec["id"] + (".csv" if spec["format"]=="csv" else ".json"))
            dst.write_bytes(data)
            row.update(status="CAPTURED",bytes=len(data),sha256=digest,mtime_ns=after.st_mtime_ns,
                       captured_path=str(dst),readback_bytes=dst.stat().st_size,
                       readback_sha256=sha(dst.read_bytes()),source_unchanged_during_capture=True)
            try:
                row["summary"] = summarize_json(json.loads(data.decode("utf-8-sig"))) if spec["format"]=="json" else summarize_csv(data)
                row["parse_status"]="PARSED"
            except Exception as e:
                row.update(parse_status="PARSE_FAILED",parse_error=f"{type(e).__name__}:{e}"); partial=True
            if row["readback_bytes"] != len(data) or row["readback_sha256"] != digest:
                row["status"]="CAPTURE_READBACK_MISMATCH"; partial=True
            total += len(data); rows.append(row)
        except FileNotFoundError:
            row["status"]="NOT_FOUND_AT_EXACT_PATH"; partial=True; rows.append(row)
        except Exception as e:
            row.update(status="CAPTURE_ERROR",error=f"{type(e).__name__}:{e}"); partial=True; rows.append(row)

    manifest = {
        "schema":"BLACKBOX_POST_20261027_LAYER_METADATA_CAPTURE_R1",
        "task_id":"BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1",
        "execution_host":"ZHANGWEI","created_at_utc":now(),
        "candidate_exchange_sessions":list(SESSIONS),
        "calendar_basis":{"sources":[
            "https://www.sse.com.cn/disclosure/announcement/general/c/c_20251222_10802507.shtml",
            "https://www.szse.cn/English/services/trading/calendar/"],
            "classification":"OFFICIAL_EXCHANGE_SCHEDULE_OBSERVATION_NOT_P1_EXTENSION",
            "p1_policy":"UNCHANGED_FROZEN_THROUGH_2026-10-27"},
        "limits":{"read_only_E":True,"exact_allowlist_only":True,"recursive_scan":False,
            "parquet_read":False,"supplier_calls":False,"credential_reads":False,"network_calls":False,
            "source_writes":False,"cleaning":False,"current_switch":False,"release":False,
            "source_absence_claim":False,"replay_allowed":False},
        "total_captured_bytes":total,"partial":partial,"inputs":rows}
    (delivery/"CAPTURE_MANIFEST.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    summary={"task_id":manifest["task_id"],"status":"PARTIAL_METADATA_CAPTURE" if partial else "METADATA_CAPTURE_COMPLETE",
        "input_count":len(rows),"captured_count":sum(r.get("status")=="CAPTURED" for r in rows),
        "immutable_pin_mismatch_count":sum(r.get("pin_status")=="MISMATCH" for r in rows),
        "candidate_date_literal_hit_count":sum(len((r.get("summary") or {}).get("candidate_session_literal_hits",[])) for r in rows),
        "no_source_absence_claim":True}
    (delivery/"SUMMARY.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    (delivery/"REPORT.md").write_text(
        "# Post-2026-10-27 Registered Layer and Dictionary Metadata Capture\n\n"
        f"- Task: {manifest['task_id']}\n- Status: {summary['status']}\n"
        f"- Captured: {summary['captured_count']}/{summary['input_count']} exact allowlisted files\n"
        f"- Candidate-session literal hits: {summary['candidate_date_literal_hit_count']}\n"
        "- JSON indexes and normative CSVs only; no Parquet reads or source-absence conclusion.\n"
        "- P1 remains frozen through 2026-10-27. No supplier calls, credentials, network, E: writes, Cleaning, CURRENT or release.\n",
        encoding="utf-8")
    return (2 if partial else 0), manifest

def main():
    code, result = capture(INPUTS, ROOT, DELIVERY)
    print(json.dumps({"task_id":"BLACKBOX_POST_20261027_LAYER_RECONCILIATION_20261112_R1",
                      "status":result.get("status","CAPTURE_FINISHED"),"exit":code,
                      "delivery_root":str(DELIVERY)},ensure_ascii=False))
    return code

if __name__ == "__main__":
    raise SystemExit(main())
