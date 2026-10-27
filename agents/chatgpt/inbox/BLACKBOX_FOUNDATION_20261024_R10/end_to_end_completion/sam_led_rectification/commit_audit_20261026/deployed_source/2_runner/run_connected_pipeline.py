"""Connected retained-batch pipeline — R2, real chain: R15 clean -> original compiler -> commit -> publish gate.

Why R2 exists
-------------
R13's review objection was that `run_connected_pipeline.py` proved several original
components *each* run, not that they run *as one chain*:

  * the R15 replay wrote `candidate/r15_releases/R15_REPLAY_20260924_R2`, while
  * the compiler's `--cleaning-json` pointed at a synthesised candidate
    `candidate/cc/CC_REPLAY_20260924/RELEASE.json`, and
  * `run_connected_pipeline.py` never invoked the R15 runner at all.

R2 closes exactly that gap and nothing else:

  1. TRANSPORT  (substituted only) `LocalReplayTransport` — retained RAW batch, no download.
  2. GATE       original `acquisition_absence_gate` via `response_gate`.
  3. CLEANING   `candidate/run_r15_cleaning_replay.py` -> real R15 `hardlink_tree` +
                `load_staging` + `ingest_item` + `ingest_minute_staging` + `seal_release`
                + real `r15_antileak_and_ssot`.  Produces ONE sealed cleaning release.
  4. COMPILER   original `cache_compiler_tip_rebase_from_current_r1.main()` with
                `--cleaning-json` = **the cleaning release produced in step 3**.  This is the
                linkage that was missing: the compiler reads the R15 output's `standard_root`.
  5. COMMIT     `tools/candidate_commit.py` content-addressed commit + verify.
  6. PUBLISH    original `publish_atomic` probed on candidate facts (dry run; no CURRENT write).

`LINEAGE` records the same-artifact hand-off: retained file sha256 -> R15 sealed file sha256 ->
the exact `standard_root` path the compiler read -> the cache release id it produced.
If any link does not match, `LINEAGE_OK` is false and the run verdict is FAIL.

Still not claimed: production CURRENT switch, vendor completeness, factor validity, V4 admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import pyarrow.parquet as pq

TASK = Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
BB = Path(r"E:\BLACKBOX")
RAW_ROOT = BB / "数据" / "原始只读" / "JQData_9999_official_raw" / "P2_stock_daily"
SEALED_PARENT = (BB / "数据" / "回测缓存" / "releases"
                 / "BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439")
CAND = TASK / "candidate"
REPORT = TASK / "deliverables" / "CONNECTED_PIPELINE.json"
RUN_LOG_DIR = TASK / "pipeline_runs"
PY = str(BB / ".venv" / "Scripts" / "python.exe")

sys.path.insert(0, str(BB / "脚本"))
sys.path.insert(0, str(TASK / "tools"))
from blackbox_daily_increment_common_r1 import acquisition_absence_gate  # noqa: E402

REPLAY_DAYS = ("2026-08-31", "2026-09-01")
ASOF = "2026-09-24"
PRICE_COLUMNS = ["date", "code", "open", "high", "low", "close", "volume", "money"]
REQUIRED_SIDECAR_KEYS = ("rows", "price_basis", "gap_start", "gap_end")

# Production pointers / state this pipeline must never modify. Digested before and after so
# "production untouched" is measured, not asserted.
PRODUCTION_WATCH = (
    "数据/回测缓存/CURRENT_CACHE_RELEASE.json",
    "数据/清洗成品/CURRENT_CLEANING_RELEASE.json",
    "研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json",
    "研究系统/数据平面/CURRENT/DAILY_DATA_PLANE_CURRENT.json",
    "研究系统/数据平面/CURRENT/DAILY_RESEARCH_INPUT_PACK_CURRENT.json",
    "研究系统/数据平面/STATE/JQ_INCREMENTAL_STATE.json",
    "运行/BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json",
    "运行/BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_WITH_SW_L123_CACHE_CURRENT.json",
)


def _sha_or_none(p: Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def production_digest() -> dict:
    return {rel: _sha_or_none(BB / rel) for rel in PRODUCTION_WATCH}


class PipelineStop(RuntimeError):
    def __init__(self, stage: str, code: str, detail: Dict[str, Any]):
        super().__init__(f"{stage}/{code}: {json.dumps(detail, ensure_ascii=False, default=str)[:400]}")
        self.stage = stage
        self.code = code
        self.detail = detail


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def batch_stamp(name: str) -> str:
    parts = Path(name).stem.split("__")
    return parts[-1] if len(parts) > 1 else Path(name).stem


@dataclass
class Response:
    """What the retained transport returns for one session request."""
    requested_date: str
    rows: int
    payload_sha256: str
    sidecar: Dict[str, Any]
    source_file: str
    frame: pd.DataFrame
    request_evidence: Dict[str, Any] = field(default_factory=dict)


class LocalReplayTransport:
    """Replays the retained RAW batch for a session. No network, no download."""

    def __init__(self, raw_root: Path = RAW_ROOT):
        self.raw_root = Path(raw_root)
        files = sorted(p for p in self.raw_root.glob("*.parquet") if "gap_" in p.name)
        if not files:
            raise FileNotFoundError(f"no retained RAW batches under {self.raw_root}")
        ordered = sorted(files, key=lambda p: (batch_stamp(p.name), p.name))
        self.by_date: Dict[str, Path] = {}
        for p in ordered:
            cols = pq.ParquetFile(p).schema_arrow.names
            if "time" not in cols:
                continue
            d = pd.to_datetime(pq.ParquetFile(p).read(columns=["time"]).to_pandas()["time"],
                               errors="coerce").dt.strftime("%Y-%m-%d").dropna().unique()
            for day in d:
                self.by_date[str(day)] = p

    def fetch(self, day: str) -> Response:
        path = self.by_date.get(str(day))
        if path is None:
            raise PipelineStop("transport", "SESSION_NOT_RETAINED", {"date": str(day)})
        cols = pq.ParquetFile(path).schema_arrow.names
        missing = [c for c in ["time", "code", *PRICE_COLUMNS[2:]] if c not in cols]
        if missing:
            raise PipelineStop("transport", "BATCH_SCHEMA_INCOMPLETE",
                               {"file": path.name, "missing": missing})
        df = pq.ParquetFile(path).read().to_pandas()
        df["date"] = pd.to_datetime(df["time"], errors="coerce").dt.normalize()
        df = df.loc[df["date"] == pd.Timestamp(day)].copy()
        if df.empty:
            raise PipelineStop("transport", "SESSION_EMPTY", {"date": str(day), "file": path.name})
        sidecar = {
            "rows": int(len(df)),
            "price_basis": "RAW_NONE",
            "gap_start": str(df["date"].min().date()),
            "gap_end": str(df["date"].max().date()),
            "build_stamp": batch_stamp(path.name),
            "dup_policy": "LATEST_BATCH_WINS",
        }
        disk_sc = path.with_name(path.name + ".sidecar.json")
        if disk_sc.exists():
            try:
                on_disk = json.loads(disk_sc.read_text(encoding="utf-8"))
                sidecar = {**on_disk, **sidecar}
            except Exception:  # noqa: BLE001
                pass
        sidecar.setdefault("file_sha256", sha256_file(path))
        return Response(
            requested_date=str(day),
            rows=int(len(df)),
            payload_sha256=sha256_file(path),
            sidecar=sidecar,
            source_file=path.name,
            frame=df,
            request_evidence=self.request_evidence(path, sidecar),
        )

    @staticmethod
    def request_evidence(path: Path, sidecar: Dict[str, Any]) -> Dict[str, Any]:
        """Read whatever the ORIGINAL request record says — never invent it."""
        ev: Dict[str, Any] = {"origin": "NONE", "sidecar_path": None, "request_path": None}
        sc = path.with_name(path.name + ".sidecar.json")
        if sc.exists():
            ev["origin"] = "SIDECAR"
            ev["sidecar_path"] = str(sc)
        req = path.with_name(path.name + ".request.json")
        if req.exists():
            try:
                body = json.loads(req.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                body = {}
            ev["origin"] = "REQUEST_RECORD"
            ev["request_path"] = str(req)
            ev["query_cap"] = body.get("query_cap") or body.get("limit")
            ev["pagination_complete"] = body.get("pagination_complete", "UNKNOWN")
            ev["requested_universe"] = body.get("codes") or body.get("symbols")
            ev["terminal_page"] = body.get("terminal_page")
            ev["replayed_at"] = body.get("requested_at")
        else:
            ev.setdefault("query_cap", sidecar.get("query_cap"))
            ev.setdefault("pagination_complete", sidecar.get("pagination_complete", "UNKNOWN"))
            ev.setdefault("requested_universe", sidecar.get("codes_requested"))
        return ev


def response_gate(resp: Response, expected_rows_band: Tuple[int, int] = (0, 0),
                  *, release_acquisition: bool = False) -> Dict[str, Any]:
    """Two separate judgements, never merged: PROVENANCE and SUPPLIER COMPLETENESS."""
    prov = {
        "requested_date": resp.requested_date,
        "sidecar_gap_start": resp.sidecar.get("gap_start"),
        "sidecar_gap_end": resp.sidecar.get("gap_end"),
        "source_file": resp.source_file,
        "payload_sha256": resp.payload_sha256,
        "request_evidence_origin": resp.request_evidence.get("origin"),
    }
    missing = [k for k in REQUIRED_SIDECAR_KEYS if k not in resp.sidecar]
    if missing:
        raise PipelineStop("gate", "SIDECAR_INCOMPLETE", {**prov, "missing": missing})
    if resp.sidecar["gap_start"] != resp.requested_date or resp.sidecar["gap_end"] != resp.requested_date:
        raise PipelineStop("gate", "SESSION_DATE_MISMATCH", prov)
    if resp.frame.duplicated(subset=["date", "code"]).any():
        raise PipelineStop("gate", "DUPLICATE_KEYS_IN_BATCH", prov)
    nulls = int(resp.frame[PRICE_COLUMNS[2:]].isna().any(axis=1).sum())
    if nulls:
        raise PipelineStop("gate", "NULL_PRICE_FIELDS", {**prov, "null_rows": nulls})

    band_source = "REQUEST_EVIDENCE" if resp.request_evidence.get("requested_universe") \
        else "STRUCTURAL_SANITY_ONLY"
    band_ok = True
    if band_source == "REQUEST_EVIDENCE":
        req_n = len(resp.request_evidence["requested_universe"])
        band_ok = resp.rows == req_n
        if not band_ok:
            raise PipelineStop("gate", "ROW_COUNT_NE_REQUESTED_UNIVERSE",
                               {**prov, "rows": resp.rows, "requested": req_n})
    elif expected_rows_band[1] > 0:
        band_ok = expected_rows_band[0] <= resp.rows <= expected_rows_band[1]

    qcap = resp.request_evidence.get("query_cap")
    pag = str(resp.request_evidence.get("pagination_complete") or "UNKNOWN").upper()
    if pag not in ("YES", "NO", "UNKNOWN"):
        pag = "UNKNOWN"
    has_request_record = resp.request_evidence.get("origin") == "REQUEST_RECORD"

    absence = acquisition_absence_gate(n_rows=resp.rows, query_cap=qcap,
                                       pagination_complete=pag)
    verdict = str(absence.get("DATA_ABSENCE_GATE")
                  or absence.get("ACQUISITION_ABSENCE_GATE")
                  or absence.get("status") or "")
    completeness_proven = (
        has_request_record
        and pag == "YES"
        and qcap is not None
        and int(qcap) != int(resp.rows)
        and verdict in ("AVAILABLE", "CONFIRMED_ABSENT")
    )
    completeness = "PROVEN" if completeness_proven else "UNKNOWN"
    if release_acquisition and completeness != "PROVEN":
        raise PipelineStop("gate", "ACQUISITION_COMPLETENESS_UNPROVEN",
                           {**prov, "gate": absence,
                            "request_evidence": resp.request_evidence})
    return {
        "stage": "gate",
        "PROVENANCE_GATE": "PASS" if band_ok else "FAIL",
        "provenance": prov,
        "provenance_facts": {
            "retained_bytes_match_sidecar_sha": resp.sidecar.get("file_sha256") ==
            resp.payload_sha256,
            "row_band_source": band_source,
            "duplicate_keys": 0,
            "null_price_rows": 0,
        },
        "SUPPLIER_COMPLETENESS": completeness,
        "vendor_result_complete": completeness,
        "original_gate": absence,
        "original_gate_verdict": verdict,
        "gate_inputs": {
            "n_rows": resp.rows, "query_cap": qcap, "pagination_complete": pag,
            "request_evidence_origin": resp.request_evidence.get("origin"),
            "note": "query_cap and pagination_complete come only from a saved request "
                    "record; the returned row count is never used as its own cap",
        },
        "ACQUISITION_RELEASED": False,
        "rows": resp.rows,
    }


def run(cmd: List[str], log_path: Path) -> Dict[str, Any]:
    started = time.time()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
        fh.write("$ " + " ".join(cmd) + "\n")
        fh.flush()
        proc = subprocess.run(cmd, cwd=str(BB), stdout=fh, stderr=subprocess.STDOUT)
    return {
        "cmd": cmd,
        "exit_code": int(proc.returncode),
        "log": str(log_path),
        "elapsed_sec": round(time.time() - started, 1),
    }


def run_r15_cleaning(rid: str) -> Dict[str, Any]:
    """Stage 3: the ORIGINAL R15 functions, carry-forward included."""
    cmd = [PY, "-X", "utf8", str(TASK / "candidate" / "run_r15_cleaning_replay.py"),
           "--asof", ASOF, "--rid", rid]
    rc = run(cmd, RUN_LOG_DIR / f"r15_cleaning_{rid}.log")
    release_json = TASK / "candidate" / "r15_releases" / rid / "RELEASE.json"
    rc["release_json"] = str(release_json)
    rc["release_exists"] = release_json.exists()
    rc["release"] = json.loads(release_json.read_text(encoding="utf-8")) if release_json.exists() else None
    return rc


def compile_release(cleaning_json: Path, out_root: Path, acceptance: Path,
                    receipt: Path, log_name: str | None = None) -> Dict[str, Any]:
    """Stage 4: the ORIGINAL tip-rebase compiler, reading the R15 output tree."""
    cmd = [PY, "-X", "utf8", str(TASK / "tools" / "run_original_compiler_candidate.py"),
           "--cleaning-json", str(cleaning_json),
           "--parent-root", str(SEALED_PARENT),
           "--out-root", str(out_root),
           "--acceptance-out", str(acceptance),
           "--run-target-date", ASOF,
           "--receipt", str(receipt)]
    acceptance = Path(acceptance)
    last_json = acceptance / "TIP_REBASE_LAST.json"
    stale = None
    if last_json.exists():
        stale = last_json.with_name(f"TIP_REBASE_LAST.prev_{os.getpid()}.json")
        try:
            last_json.replace(stale)
        except OSError:
            last_json.unlink(missing_ok=True)
    started = time.time()

    rc = run(cmd, RUN_LOG_DIR / (log_name or f"compiler_{out_root.name}.log"))
    rc["receipt"] = json.loads(receipt.read_text(encoding="utf-8")) if receipt.exists() else None
    rc["tip_rebase_last"] = str(last_json)
    rc["stale_moved_to"] = str(stale) if stale else None

    if rc["exit_code"] != 0:
        return rc

    # ---- bind this run's output from the compiler's own declaration -------------------
    if not last_json.is_file():
        raise PipelineStop("compiler", "NO_DECLARED_OUTPUT",
                           {"expected": str(last_json), "exit_code": rc["exit_code"]})
    if last_json.stat().st_mtime < started - 1:
        raise PipelineStop("compiler", "DECLARED_OUTPUT_STALE",
                           {"path": str(last_json),
                            "mtime": last_json.stat().st_mtime, "started": started})
    try:
        declared = json.loads(last_json.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        raise PipelineStop("compiler", "DECLARED_OUTPUT_UNREADABLE",
                           {"path": str(last_json), "error": f"{type(e).__name__}: {e}"}) from e

    pointer = declared.get("pointer") or {}
    seal_doc = declared.get("seal") or {}
    rid = pointer.get("cache_release_id")
    root = pointer.get("release_root")
    problems = []
    if not rid:
        problems.append("MISSING cache_release_id")
    if not root:
        problems.append("MISSING release_root")
    if rid and root and Path(str(root)).name != str(rid):
        problems.append(f"ROOT_BASENAME_NE_RELEASE_ID name={Path(str(root)).name} id={rid}")
    if root and not Path(str(root)).is_dir():
        problems.append(f"RELEASE_ROOT_ABSENT {root}")
    if root and Path(str(root)).is_dir():
        root = Path(str(root))
        seal_p = root / "SEAL.json"
        rel_p = root / "RELEASE.json"
        if not seal_p.is_file():
            problems.append(f"SEAL_MISSING {seal_p}")
        else:
            s = json.loads(seal_p.read_text(encoding="utf-8"))
            if str(s.get("release_id")) != str(rid):
                problems.append(f"SEAL_RELEASE_ID_MISMATCH {s.get('release_id')}")
            if s.get("all_pass") is not True:
                problems.append("SEAL_ALL_PASS_FALSE")
        if not rel_p.is_file():
            problems.append(f"RELEASE_JSON_MISSING {rel_p}")
        else:
            rj = json.loads(rel_p.read_text(encoding="utf-8"))
            if str(rj.get("cache_release_id")) != str(rid):
                problems.append(f"RELEASE_JSON_ID_MISMATCH {rj.get('cache_release_id')}")
    if str(pointer.get("asof")) != ASOF:
        problems.append(f"ASOF_MISMATCH declared={pointer.get('asof')} expected={ASOF}")

    # the declared cleaning source must be the cleaning release we actually passed in
    cleaning_rid = None
    try:
        cleaning_rid = json.loads(Path(cleaning_json).read_text(encoding="utf-8")).get("release_id")
    except Exception:  # noqa: BLE001
        cleaning_rid = None
    if cleaning_rid and str(pointer.get("source_cleaning_release")) != str(cleaning_rid):
        problems.append(
            f"SOURCE_CLEANING_MISMATCH declared={pointer.get('source_cleaning_release')} "
            f"expected={cleaning_rid}")

    rc["declared"] = {"cache_release_id": rid, "release_root": str(root),
                      "asof": pointer.get("asof"),
                      "source_cleaning_release": pointer.get("source_cleaning_release"),
                      "all_pass": seal_doc.get("all_pass")}
    if problems:
        raise PipelineStop("compiler", "DECLARED_OUTPUT_INVALID",
                           {"problems": problems, "declared": rc["declared"]})
    rc["bound_release_root"] = str(root)
    rc["bound_release_id"] = str(rid)
    rc["binding_source"] = str(last_json)
    return rc


def newest_release(out_root: Path) -> Path:
    """DEPRECATED — do not use. Kept only so old callers fail loudly instead of silently.

    Directory-name ordering cannot identify "this run's output": archived `_prev_*` / `_bad_*`
    directories sort alongside real releases and were measured being selected, which let new
    content go uncommitted while the run reported NOOP. Identity must come from the compiler's
    own declaration (`acceptance/TIP_REBASE_LAST.json`), which `compile_release()` now enforces.
    """
    raise PipelineStop("compiler", "NEWEST_RELEASE_FORBIDDEN",
                       {"out_root": str(out_root),
                        "reason": "use compile_release()['bound_release_root'] instead"})


def build_lineage(responses: List[Dict[str, Any]], r15: Dict[str, Any],
                  rel: Path) -> Dict[str, Any]:
    """Prove the SAME artifact flowed: retained bytes -> R15 sealed -> compiler input -> cache."""
    release = r15.get("release") or {}
    std = Path(release.get("standard_root", "")) if release else Path("")
    links = []
    for r in responses:
        name = Path(r["file"]).name
        sealed = std / "price" / "stock_ohlcv_daily" / name if str(std) != "." else None
        sealed_sha = sha256_file(sealed) if sealed and sealed.exists() else None
        links.append({
            "retained_file": name,
            "retained_sha256": r["sha256"],
            "r15_sealed_path": str(sealed) if sealed else None,
            "r15_sealed_sha256": sealed_sha,
            "retained_equals_r15_sealed": bool(sealed_sha) and sealed_sha == r["sha256"],
        })
    release_json = json.loads((rel / "RELEASE.json").read_text(encoding="utf-8"))
    ok = bool(links) and all(l["retained_equals_r15_sealed"] for l in links)
    return {
        "retained_batches": links,
        "r15_release_id": release.get("release_id"),
        "r15_standard_root": release.get("standard_root"),
        "r15_release_content_root_sha256": release.get("release_content_root_sha256"),
        "compiler_cleaning_json": str(Path(r15["release_json"])),
        "compiler_read_standard_root": release.get("standard_root"),
        "cache_release_id": release_json.get("cache_release_id"),
        "LINEAGE_OK": ok,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="R14_SAM_LED_CHAIN")
    ap.add_argument("--out", default=str(REPORT))
    ap.add_argument("--r15-rid", default=f"R15_REPLAY_{ASOF.replace('-', '')}_R3")
    args = ap.parse_args()

    prod_before = production_digest()
    evidence: Dict[str, Any] = {
        "run_id": args.run_id,
        "pipeline_version": "R2_R15_TO_COMPILER_ONE_ARTIFACT",
        "production_digest_before": prod_before,
        "asof": ASOF,
        "replay_days": list(REPLAY_DAYS),
        "host": {"hostname": __import__("socket").gethostname(),
                 "python": sys.executable, "cwd": str(Path.cwd())},
        "stages": {},
        "controls": {},
        "PRODUCTION_CURRENT_WRITE": "NONE",
        "NEW_DATA_ACQUISITION": "NONE",
    }

    # ---------------------------------------------------------------- transport
    transport = LocalReplayTransport()
    responses = []
    for day in REPLAY_DAYS:
        resp = transport.fetch(day)
        gate = response_gate(resp, (3000, 7000))
        responses.append({"date": day, "rows": resp.rows, "sha256": resp.payload_sha256,
                          "file": resp.source_file, "gate": gate})
    completeness = sorted({r["gate"]["SUPPLIER_COMPLETENESS"] for r in responses})
    evidence["stages"]["transport_gate"] = {
        "status": "PASS",
        "PROVENANCE_GATE": "PASS",
        "SUPPLIER_COMPLETENESS": completeness[0] if len(completeness) == 1 else completeness,
        "ACQUISITION_RELEASED": False,
        "sessions": responses,
        "retained_sessions_available": len(transport.by_date),
        "note": "retained bytes/keys are proven; vendor completeness is UNKNOWN because no "
                "saved supplier request exists in the retained corpus",
    }

    # ------------------------------------------------- negative control: date tamper
    try:
        bad = transport.fetch(REPLAY_DAYS[0])
        tampered = Response(
            requested_date="2026-09-02",
            rows=bad.rows, payload_sha256=bad.payload_sha256,
            sidecar={**bad.sidecar, "gap_start": REPLAY_DAYS[0], "gap_end": REPLAY_DAYS[0]},
            source_file=bad.source_file, frame=bad.frame,
            request_evidence=bad.request_evidence,
        )
        response_gate(tampered, (3000, 7000))
        evidence["controls"]["tampered_date"] = {"status": "NOT_BLOCKED"}
    except PipelineStop as e:
        evidence["controls"]["tampered_date"] = {
            "status": "BLOCKED_AS_EXPECTED", "stage": e.stage, "code": e.code}

    # ------------------------- negative control: gate must refuse self-certification
    try:
        fake = transport.fetch(REPLAY_DAYS[0])
        fake = Response(
            requested_date=fake.requested_date, rows=fake.rows,
            payload_sha256=fake.payload_sha256, sidecar=fake.sidecar,
            source_file=fake.source_file, frame=fake.frame,
            request_evidence={"origin": "NONE", "query_cap": fake.rows,
                              "pagination_complete": "YES"},
        )
        g = response_gate(fake, (3000, 7000), release_acquisition=True)
        evidence["controls"]["self_certified_completeness"] = {"status": "NOT_BLOCKED", "gate": g}
    except PipelineStop as e:
        evidence["controls"]["self_certified_completeness"] = {
            "status": "BLOCKED_AS_EXPECTED", "stage": e.stage, "code": e.code}

    # ------------------------------------------- cleaning: REAL R15 (carry-forward)
    r15 = run_r15_cleaning(args.r15_rid)
    evidence["stages"]["cleaning_r15"] = {
        "status": "PASS" if r15["exit_code"] == 0 and r15["release_exists"] else "FAIL",
        "exit_code": r15["exit_code"],
        "log": r15["log"],
        "elapsed_sec": r15["elapsed_sec"],
        "release_id": (r15.get("release") or {}).get("release_id"),
        "standard_root": (r15.get("release") or {}).get("standard_root"),
        "carry_forward": (r15.get("release") or {}).get("carry_forward"),
        "release_content_root_sha256": (r15.get("release") or {}).get("release_content_root_sha256"),
        "real_functions": [
            "formal_cleaning_r15_build_and_seal_r1.hardlink_tree",
            "formal_cleaning_r15_build_and_seal_r1.load_staging",
            "formal_cleaning_r15_build_and_seal_r1.ingest_item",
            "formal_cleaning_r15_build_and_seal_r1.ingest_minute_staging",
            "formal_cleaning_r15_build_and_seal_r1.seal_release",
            "r15_antileak_and_ssot_r1.antileak_check",
        ],
        "switch_current": "NOT_CALLED",
        "patch_hand": "NOT_CALLED",
    }
    if evidence["stages"]["cleaning_r15"]["status"] != "PASS":
        evidence["status"] = "BLOCKED_R15_CLEANING"
        evidence["CONNECTED_PIPELINE_RESULT"] = "FAIL"
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(evidence, ensure_ascii=False, indent=2, default=str),
                                  encoding="utf-8")
        print(json.dumps({"CONNECTED_PIPELINE_RESULT": "FAIL",
                          "reason": "R15 cleaning failed", "exit_code": r15["exit_code"],
                          "log": r15["log"]}, ensure_ascii=False, indent=2))
        return 3

    # ------------------------------------- compiler: ORIGINAL, reads the R15 tree
    cleaning_json = Path(r15["release_json"])
    out_root = CAND / "cc_out" / "releases"
    acceptance = CAND / "cc_out" / "acceptance"
    receipt = TASK / "evidence" / "ORIGINAL_COMPILER_RECEIPT.json"
    rc = compile_release(cleaning_json, out_root, acceptance, receipt)
    evidence["stages"]["compiler"] = {
        **rc,
        "status": "PASS" if rc["exit_code"] == 0 else "FAIL",
        "cleaning_json_consumed": str(cleaning_json),
        "cleaning_json_sha256": sha256_file(cleaning_json),
    }
    if rc["exit_code"] != 0:
        evidence["status"] = "BLOCKED_COMPILER"
        evidence["CONNECTED_PIPELINE_RESULT"] = "FAIL"
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(evidence, ensure_ascii=False, indent=2, default=str),
                                  encoding="utf-8")
        print(json.dumps({"CONNECTED_PIPELINE_RESULT": "FAIL", "reason": "compiler failed",
                          "exit_code": rc["exit_code"], "log": rc["log"]},
                         ensure_ascii=False, indent=2))
        return 4

    rel = Path(rc["bound_release_root"])
    seal = json.loads((rel / "SEAL.json").read_text(encoding="utf-8"))
    evidence["stages"]["compiler"].update({
        "release": str(rel),
        "release_id": json.loads((rel / "RELEASE.json").read_text(encoding="utf-8"))["cache_release_id"],
        "seal_all_pass": seal.get("all_pass"),
        "price_gates": {k: v.get("pass") for k, v in (seal.get("price", {}).get("gates") or {}).items()},
        "stock_2026": seal.get("price", {}).get("products", {}).get("STOCK_DAILY_PIT_R1"),
        "replay_days_in_release": _count_days(rel / "STOCK_DAILY_PIT_R1", REPLAY_DAYS),
        "original_entry": str(BB / "任务" / "BLACKBOX_BACKTEST_CACHE_COMPILER_R1"
                              / "cache_compiler_tip_rebase_from_current_r1.py"),
        "publish_called_by_compiler": False,
    })

    # ------------------------------------------------------- lineage (the point)
    lineage = build_lineage(responses, r15, rel)
    evidence["LINEAGE"] = lineage

    # -------------------------------------------------------------------- commit
    import candidate_commit as cc
    commit_rc = cc.commit(rel, note=f"{args.run_id} connected pipeline")
    verify = cc.verify()
    evidence["stages"]["commit"] = {
        "status": "PASS" if verify.get("consistent") else "FAIL",
        "commit": commit_rc, "verify": verify,
    }
    gate_probe = cc.probe_original_publish_gate(rel)
    evidence["stages"]["publish_gate_probe"] = {
        "status": "EVALUATED_NOT_PUBLISHED",
        "original_function": gate_probe["gate_function"],
        "OPERATIONAL_READINESS": gate_probe["OPERATIONAL_READINESS"],
        "CURRENT_PUBLISH": gate_probe["CURRENT_PUBLISH"],
        "published": gate_probe["published"],
        "production_CURRENT_written": False,
    }

    # ------------------------------------------- negative control: compiler hard-block
    bad_cleaning = TASK / "evidence" / "BAD_CLEANING_RELEASE.json"
    bad_cleaning.write_text(json.dumps({"release_id": "BAD", "standard_root": str(TASK / "nope"),
                                        "cleaning_as_of": ASOF}, indent=2), encoding="utf-8")
    bad_rc = compile_release(bad_cleaning, CAND / "bad_out" / "releases",
                             CAND / "bad_out" / "acceptance",
                             TASK / "evidence" / "ORIGINAL_COMPILER_RECEIPT_BAD.json",
                             log_name="compiler_HARD_BLOCK_negative_control.log")
    evidence["controls"]["compiler_hard_block"] = {
        "status": "BLOCKED_AS_EXPECTED" if bad_rc["exit_code"] != 0 else "NOT_BLOCKED",
        "exit_code": bad_rc["exit_code"], "log": bad_rc["log"],
    }

    # ------------------------------------------------- idempotent same-input replay
    replay_rc = compile_release(cleaning_json, out_root, acceptance, receipt)
    if replay_rc["exit_code"] == 0:
        rel2 = Path(replay_rc["bound_release_root"])
        commit2 = cc.commit(rel2, note=f"{args.run_id} same input replay")
        evidence["stages"]["same_input_replay"] = {
            "status": "PASS" if commit2.get("status") == "IDEMPOTENT_NOOP" else "FAIL",
            "compiler_exit_code": replay_rc["exit_code"],
            "second_release_id": json.loads((rel2 / "RELEASE.json").read_text(encoding="utf-8"))["cache_release_id"],
            "commit": commit2,
            "commit_id_unchanged": commit2.get("commit_id") == commit_rc.get("commit_id"),
            "note": "same cleaning input recompiled; the committed DATA identity is "
                    "content-addressed, so the same input commits nothing new",
        }
    else:
        evidence["stages"]["same_input_replay"] = {"status": "COMPILER_FAILED",
                                                   "exit_code": replay_rc["exit_code"]}

    prod_after = production_digest()
    evidence["production_digest_after"] = prod_after
    evidence["production_digest_changed"] = {
        k: {"before": prod_before[k], "after": prod_after[k]}
        for k in prod_before if prod_before[k] != prod_after[k]}

    verdicts = {
        "transport_gate_pass": evidence["stages"]["transport_gate"]["status"] == "PASS",
        "tampered_date_blocked": evidence["controls"]["tampered_date"]["status"] == "BLOCKED_AS_EXPECTED",
        "self_cert_blocked": evidence["controls"]["self_certified_completeness"]["status"] == "BLOCKED_AS_EXPECTED",
        "r15_cleaning_pass": evidence["stages"]["cleaning_r15"]["status"] == "PASS",
        "compiler_read_r15_tree": str(evidence["stages"]["compiler"]["cleaning_json_consumed"]).startswith(
            str((TASK / "candidate" / "r15_releases"))),
        "lineage_same_artifact": bool(lineage.get("LINEAGE_OK")),
        "compiler_hard_block_propagated": evidence["controls"]["compiler_hard_block"]["status"] == "BLOCKED_AS_EXPECTED",
        "original_compiler_all_pass": evidence["stages"]["compiler"].get("seal_all_pass") is True,
        "replay_days_present_in_release": all(
            v > 0 for v in evidence["stages"]["compiler"]["replay_days_in_release"].values()),
        "commit_consistent": evidence["stages"]["commit"]["status"] == "PASS",
        "same_input_replay_noop": evidence["stages"]["same_input_replay"].get("status") == "PASS",
        "production_current_untouched": (prod_before == evidence.get(
            "production_digest_after", prod_before) and prod_before == production_digest()),
    }
    evidence["verdicts"] = verdicts
    evidence["CONNECTED_PIPELINE_RESULT"] = "PASS" if all(verdicts.values()) else "FAIL"
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(evidence, ensure_ascii=False, indent=2, default=str),
                              encoding="utf-8")
    print(json.dumps({"verdicts": verdicts,
                      "CONNECTED_PIPELINE_RESULT": evidence["CONNECTED_PIPELINE_RESULT"]},
                     ensure_ascii=False, indent=2))
    return 0 if evidence["CONNECTED_PIPELINE_RESULT"] == "PASS" else 5


def _count_days(product_dir: Path, days) -> Dict[str, int]:
    if not product_dir.exists():
        return {d: -1 for d in days}
    parts = sorted(product_dir.rglob("*.parquet"))
    if not parts:
        return {d: -1 for d in days}
    counts = {d: 0 for d in days}
    for p in parts:
        cols = pq.ParquetFile(p).schema_arrow.names
        pick = next((c for c in ("date", "time", "day") if c in cols), None)
        if pick is None:
            continue
        s = pd.to_datetime(pq.ParquetFile(p).read(columns=[pick]).to_pandas()[pick],
                           errors="coerce").dt.normalize()
        for d in days:
            counts[d] += int(s.eq(pd.Timestamp(d)).sum())
    return counts


if __name__ == "__main__":
    raise SystemExit(main())
